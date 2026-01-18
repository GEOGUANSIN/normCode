"""
RemoteProxyExecutor - Relay architecture for remote execution.

This executor acts as a transparent proxy between the canvas_app frontend and a
remote normal_server. It:

1. RELAYS commands from frontend → remote server (start, stop, pause, step)
2. RELAYS events from remote server → frontend WebSocket (same format as local)
3. Maintains mirrored state for consistency

The frontend doesn't need to know if execution is local or remote - it uses the
same executionApi endpoints and receives the same WebSocket events.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Set, List, Callable

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from schemas.execution_schemas import ExecutionStatus, NodeStatus

logger = logging.getLogger(__name__)


@dataclass
class RemoteProxyExecutor:
    """
    Proxy executor for remote normal_server execution.
    
    This provides the same interface as the local ExecutionController but
    proxies all operations to a remote server and relays events back.
    
    Key difference from local: Events come via SSE from remote server,
    not generated locally. We transform them to the canonical format and
    emit through the global event_emitter so the frontend receives them
    through the same WebSocket channel as local events.
    """
    
    # Remote connection info
    server_url: str = ""
    run_id: Optional[str] = None
    plan_id: Optional[str] = None
    project_id: Optional[str] = None  # The remote project tab ID
    
    # Mirrored state (updated from SSE events)
    status: ExecutionStatus = ExecutionStatus.IDLE
    node_statuses: Dict[str, NodeStatus] = field(default_factory=dict)
    breakpoints: Set[str] = field(default_factory=set)
    current_inference: Optional[str] = None
    completed_count: int = 0
    total_count: int = 0
    cycle_count: int = 0
    
    # Run mode (mirrored from remote)
    run_mode: str = "slow"
    verbose_logging: bool = False
    
    # Logs (mirrored from remote)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # SSE connection
    _sse_task: Optional[asyncio.Task] = None
    _session: Optional["aiohttp.ClientSession"] = None
    _connected: bool = False
    _stop_sse: bool = False
    
    # Event source identifier (for routing)
    event_source: str = "remote"
    
    # =========================================================================
    # Connection Management
    # =========================================================================
    
    async def connect(
        self,
        server_url: str,
        run_id: str,
        project_id: Optional[str] = None,
    ) -> bool:
        """
        Connect to a remote run and start relaying events.
        
        Args:
            server_url: Base URL of the normal_server (e.g., http://localhost:8080)
            run_id: The run ID to connect to
            project_id: Optional project tab ID for event routing
            
        Returns:
            True if connected successfully
        """
        if not HAS_AIOHTTP:
            raise RuntimeError("aiohttp required. Install: pip install aiohttp")
        
        self.server_url = server_url.rstrip('/')
        self.run_id = run_id
        self.project_id = project_id
        self._stop_sse = False
        
        # Create HTTP session
        self._session = aiohttp.ClientSession()
        
        try:
            # Sync initial state from remote
            await self._sync_state()
            
            # Start SSE subscription for real-time events
            self._sse_task = asyncio.create_task(self._subscribe_to_events())
            
            self._connected = True
            logger.info(f"RemoteProxyExecutor connected: {run_id} on {server_url}")
            
            # Emit connected event
            await self._emit("remote:connected", {
                "run_id": run_id,
                "server_url": server_url,
                "status": self.status.value,
            })
            
            return True
            
        except Exception as e:
            await self.disconnect()
            logger.error(f"Failed to connect to remote: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from remote server and stop event streaming."""
        self._stop_sse = True
        self._connected = False
        
        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
            self._sse_task = None
        
        if self._session:
            await self._session.close()
            self._session = None
        
        logger.info(f"RemoteProxyExecutor disconnected: {self.run_id}")
        
        # Emit disconnected event
        await self._emit("remote:disconnected", {
            "run_id": self.run_id,
            "server_url": self.server_url,
        })
        
        self.run_id = None
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to a remote server."""
        return self._connected and self._session is not None
    
    # =========================================================================
    # State Synchronization
    # =========================================================================
    
    async def _sync_state(self):
        """Fetch current state from remote server."""
        if not self._session:
            return
        
        # Fetch run status
        async with self._session.get(f"{self.server_url}/api/runs/{self.run_id}") as resp:
            if resp.status != 200:
                raise RuntimeError(f"Failed to get run: {await resp.text()}")
            data = await resp.json()
            
            self.plan_id = data.get("plan_id")
            
            # Map status
            status_str = data.get("status", "idle")
            try:
                self.status = ExecutionStatus(status_str)
            except ValueError:
                self.status = ExecutionStatus.IDLE
            
            self.breakpoints = set(data.get("breakpoints", []))
            
            # Progress
            progress = data.get("progress", {})
            self.completed_count = progress.get("completed_count", 0)
            self.total_count = progress.get("total_count", 0)
            self.cycle_count = progress.get("cycle_count", 0)
            self.current_inference = progress.get("current_inference")
        
        # Fetch node statuses
        try:
            async with self._session.get(f"{self.server_url}/api/runs/{self.run_id}/node-statuses") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self.node_statuses = {}
                    for flow_index, status in data.get("statuses", {}).items():
                        try:
                            self.node_statuses[flow_index] = NodeStatus(status)
                        except ValueError:
                            self.node_statuses[flow_index] = NodeStatus.PENDING
        except Exception as e:
            logger.warning(f"Failed to fetch node statuses: {e}")
    
    # =========================================================================
    # SSE Event Streaming & Relay
    # =========================================================================
    
    async def _subscribe_to_events(self):
        """Subscribe to remote SSE stream and relay events to frontend."""
        if not self._session:
            return
        
        url = f"{self.server_url}/api/runs/{self.run_id}/stream"
        
        reconnect_delay = 1
        max_reconnect_delay = 30
        
        while not self._stop_sse:
            try:
                logger.debug(f"Connecting to SSE stream: {url}")
                
                # Use timeout to avoid hanging forever
                timeout = aiohttp.ClientTimeout(total=None, sock_read=60)
                async with self._session.get(url, timeout=timeout) as resp:
                    if resp.status == 404:
                        # Run not found - might have completed
                        logger.warning(f"SSE: Run not found (404), syncing state...")
                        await self._sync_state()
                        if self.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED):
                            logger.info(f"SSE: Run already finished ({self.status.value}), stopping stream")
                            break
                        await asyncio.sleep(reconnect_delay)
                        continue
                    
                    if resp.status != 200:
                        logger.warning(f"SSE connection failed: {resp.status}")
                        await asyncio.sleep(reconnect_delay)
                        reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                        continue
                    
                    # Connection successful, reset backoff
                    reconnect_delay = 1
                    logger.debug("SSE stream connected")
                    
                    stream_ended_normally = False
                    async for line in resp.content:
                        if self._stop_sse:
                            break
                        
                        try:
                            line = line.decode('utf-8').strip()
                        except UnicodeDecodeError:
                            continue
                        
                        if line.startswith('data: '):
                            try:
                                event_data = json.loads(line[6:])
                                await self._handle_and_relay_event(event_data)
                                
                                # Check if this was a terminal event
                                event_type = event_data.get("event", "")
                                if event_type in ("run:completed", "run:failed", "execution:stopped"):
                                    logger.info(f"SSE: Received terminal event '{event_type}', stopping stream")
                                    stream_ended_normally = True
                                    self._stop_sse = True  # Stop the reconnection loop
                                    break
                            except json.JSONDecodeError:
                                continue
                        elif line.startswith(': keepalive'):
                            continue
                    
                    # If stream ended without a terminal event, sync state before deciding to reconnect
                    if not stream_ended_normally and not self._stop_sse:
                        await self._sync_state()
                        # If run has completed/failed, stop reconnecting
                        if self.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED):
                            logger.info(f"SSE: Run finished ({self.status.value}), stopping stream")
                            break
                        # Otherwise wait before reconnecting (stream closed unexpectedly)
                        logger.debug(f"SSE: Stream ended unexpectedly, reconnecting in {reconnect_delay}s...")
                        await asyncio.sleep(reconnect_delay)
                        reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                            
            except asyncio.CancelledError:
                break
            except aiohttp.ClientError as e:
                if not self._stop_sse:
                    logger.warning(f"SSE client error: {e}, reconnecting in {reconnect_delay}s...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
            except Exception as e:
                if not self._stop_sse:
                    logger.warning(f"SSE error: {e}, reconnecting in {reconnect_delay}s...")
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
    
    async def _handle_and_relay_event(self, event: Dict[str, Any]):
        """
        Handle incoming SSE event, update local state, and relay to frontend.
        
        This is the heart of the relay architecture - we transform remote events
        to the same format used by local execution and emit them through the
        global event_emitter so the frontend receives them on the same WebSocket.
        """
        event_type = event.get("event", "")
        
        # ===== Update local mirrored state =====
        
        # Handle initial "connected" event from SSE stream - this contains full state
        if event_type == "connected":
            # Update status
            status_str = event.get("status", "running")
            try:
                self.status = ExecutionStatus(status_str)
            except ValueError:
                self.status = ExecutionStatus.RUNNING
            
            # Update node statuses
            node_statuses_data = event.get("node_statuses", {})
            for flow_index, status in node_statuses_data.items():
                try:
                    self.node_statuses[flow_index] = NodeStatus(status)
                except ValueError:
                    self.node_statuses[flow_index] = NodeStatus.PENDING
            
            # Update progress
            progress = event.get("progress", {})
            self.completed_count = progress.get("completed_count", 0)
            self.total_count = progress.get("total_count", 0)
            self.cycle_count = progress.get("cycle_count", 0)
            self.current_inference = progress.get("current_inference")
            
            # Update breakpoints
            self.breakpoints = set(event.get("breakpoints", []))
            
            # Emit execution:loaded event with full state - this triggers frontend sync
            await self._emit("execution:loaded", {
                "status": self.status.value,
                "node_statuses": {k: v.value for k, v in self.node_statuses.items()},
                "completed_count": self.completed_count,
                "total_inferences": self.total_count,
                "cycle_count": self.cycle_count,
                "current_inference": self.current_inference,
                "breakpoints": list(self.breakpoints),
            })
            
            # Also emit node statuses batch for UI update
            if node_statuses_data:
                await self._emit("node:status_batch", {
                    "statuses": {k: v.value for k, v in self.node_statuses.items()},
                })
            
            logger.info(f"SSE: Initial state synced - {self.completed_count}/{self.total_count} complete, status={self.status.value}")
        
        elif event_type == "node:statuses":
            for flow_index, status in event.get("statuses", {}).items():
                try:
                    self.node_statuses[flow_index] = NodeStatus(status)
                except ValueError:
                    self.node_statuses[flow_index] = NodeStatus.PENDING
            
            # Relay as node:status_changed (batch update)
            await self._emit("node:status_batch", {
                "statuses": event.get("statuses", {}),
            })
        
        elif event_type == "inference:started":
            flow_index = event.get("flow_index")
            self.current_inference = flow_index
            if flow_index:
                self.node_statuses[flow_index] = NodeStatus.RUNNING
            
            # Relay
            await self._emit("inference:started", {
                "flow_index": flow_index,
            })
        
        elif event_type == "inference:completed":
            flow_index = event.get("flow_index")
            if flow_index:
                self.node_statuses[flow_index] = NodeStatus.COMPLETED
            self.completed_count += 1
            
            # Relay with full data
            await self._emit("inference:completed", {
                "flow_index": flow_index,
                "result": event.get("result"),
            })
        
        elif event_type == "inference:failed":
            flow_index = event.get("flow_index")
            if flow_index:
                self.node_statuses[flow_index] = NodeStatus.FAILED
            
            await self._emit("inference:failed", {
                "flow_index": flow_index,
                "error": event.get("error"),
            })
        
        elif event_type == "execution:progress":
            self.completed_count = event.get("completed_count", self.completed_count)
            self.total_count = event.get("total_count", self.total_count)
            self.cycle_count = event.get("cycle_count", self.cycle_count)
            if event.get("current_inference"):
                self.current_inference = event["current_inference"]
            
            await self._emit("execution:progress", {
                "completed_count": self.completed_count,
                "total_count": self.total_count,
                "cycle_count": self.cycle_count,
                "current_inference": self.current_inference,
            })
        
        elif event_type == "run:started" or event_type == "execution:started":
            self.status = ExecutionStatus.RUNNING
            await self._emit("execution:started", {})
        
        elif event_type == "execution:paused":
            self.status = ExecutionStatus.PAUSED
            await self._emit("execution:paused", {})
        
        elif event_type == "execution:resumed":
            self.status = ExecutionStatus.RUNNING
            await self._emit("execution:resumed", {})
        
        elif event_type == "execution:stopped":
            self.status = ExecutionStatus.IDLE
            await self._emit("execution:stopped", {})
        
        elif event_type == "run:completed":
            self.status = ExecutionStatus.COMPLETED
            await self._emit("execution:completed", {
                "result": event.get("result"),
            })
        
        elif event_type == "run:failed":
            self.status = ExecutionStatus.FAILED
            await self._emit("execution:error", {
                "error": event.get("error"),
            })
        
        elif event_type == "breakpoint:hit":
            self.status = ExecutionStatus.PAUSED
            self.current_inference = event.get("flow_index")
            await self._emit("breakpoint:hit", {
                "flow_index": event.get("flow_index"),
            })
        
        elif event_type == "log:entry":
            # Add to local log buffer and relay
            log_entry = {
                "level": event.get("level", "info"),
                "flow_index": event.get("flow_index", ""),
                "message": event.get("message", ""),
                "timestamp": event.get("timestamp"),
            }
            self.logs.append(log_entry)
            
            await self._emit("log:entry", log_entry)
        
        elif event_type == "step:started" or event_type == "step:completed":
            # Relay step progress events
            await self._emit(event_type, event)
        
        # Catch-all: relay unknown events as-is with remote prefix
        else:
            await self._emit(f"remote:{event_type}", event)
    
    async def _emit(self, event_type: str, data: Dict[str, Any]):
        """
        Emit event through global event_emitter to WebSocket clients.
        
        This is the key - we use the SAME event system as local execution
        so the frontend doesn't need to distinguish between local and remote.
        """
        from core.events import event_emitter
        
        # Enrich with source info
        enriched_data = {
            **data,
            "source": self.event_source,
            "remote": True,
            "server_url": self.server_url,
            "run_id": self.run_id,
        }
        
        if self.project_id:
            enriched_data["project_id"] = self.project_id
        
        await event_emitter.emit(event_type, enriched_data)
    
    # =========================================================================
    # Execution Commands (Proxy to Remote)
    # =========================================================================
    
    async def start(self):
        """Start/resume execution on remote server.
        
        Note: If the run is already running, this is a no-op. The remote server's
        /continue endpoint only works for paused runs.
        """
        # If already running, no action needed
        if self.status == ExecutionStatus.RUNNING:
            return {"status": "already_running"}
        
        try:
            result = await self._post(f"/api/runs/{self.run_id}/continue")
            self.status = ExecutionStatus.RUNNING
            return result
        except RuntimeError as e:
            # If the error is because run is not paused, it's likely already running
            error_msg = str(e).lower()
            if "not paused" in error_msg or "not active" in error_msg:
                # Sync state to get current status
                await self._sync_state()
                return {"status": self.status.value, "message": "Run state synced"}
            raise
    
    async def pause(self):
        """Pause execution on remote server."""
        result = await self._post(f"/api/runs/{self.run_id}/pause")
        self.status = ExecutionStatus.PAUSED
        return result
    
    async def resume(self):
        """Resume execution on remote server."""
        result = await self._post(f"/api/runs/{self.run_id}/continue")
        self.status = ExecutionStatus.RUNNING
        return result
    
    async def step(self):
        """Step one inference on remote server."""
        result = await self._post(f"/api/runs/{self.run_id}/step")
        self.status = ExecutionStatus.STEPPING
        return result
    
    async def stop(self):
        """Stop execution on remote server."""
        result = await self._post(f"/api/runs/{self.run_id}/stop")
        self.status = ExecutionStatus.IDLE
        return result
    
    async def restart(self):
        """Restart execution - for remote, this stops and starts fresh."""
        await self.stop()
        # Remote restart requires creating a new run - not supported here
        # The frontend should handle this via deploymentApi
        logger.warning("Remote restart not fully supported - stopped execution")
    
    # =========================================================================
    # Breakpoint Management (Proxy to Remote)
    # =========================================================================
    
    async def set_breakpoint(self, flow_index: str):
        """Set breakpoint on remote server."""
        await self._post(f"/api/runs/{self.run_id}/breakpoints", {
            "flow_index": flow_index,
            "enabled": True,
        })
        self.breakpoints.add(flow_index)
    
    async def clear_breakpoint(self, flow_index: str):
        """Clear breakpoint on remote server."""
        await self._delete(f"/api/runs/{self.run_id}/breakpoints/{flow_index}")
        self.breakpoints.discard(flow_index)
    
    async def clear_all_breakpoints(self):
        """Clear all breakpoints on remote server."""
        await self._delete(f"/api/runs/{self.run_id}/breakpoints")
        self.breakpoints.clear()
    
    # =========================================================================
    # HTTP Helpers
    # =========================================================================
    
    async def _post(self, endpoint: str, json_data: Dict = None) -> Dict[str, Any]:
        """POST to remote server."""
        if not self._session:
            raise RuntimeError("Not connected to remote server")
        
        url = f"{self.server_url}{endpoint}"
        async with self._session.post(url, json=json_data) as resp:
            if resp.status >= 400:
                error = await resp.text()
                raise RuntimeError(f"Remote error: {error}")
            return await resp.json()
    
    async def _get(self, endpoint: str) -> Dict[str, Any]:
        """GET from remote server."""
        if not self._session:
            raise RuntimeError("Not connected to remote server")
        
        url = f"{self.server_url}{endpoint}"
        async with self._session.get(url) as resp:
            if resp.status >= 400:
                error = await resp.text()
                raise RuntimeError(f"Remote error: {error}")
            return await resp.json()
    
    async def _delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE on remote server."""
        if not self._session:
            raise RuntimeError("Not connected to remote server")
        
        url = f"{self.server_url}{endpoint}"
        async with self._session.delete(url) as resp:
            if resp.status >= 400:
                error = await resp.text()
                raise RuntimeError(f"Remote error: {error}")
            return await resp.json()
    
    # =========================================================================
    # State Accessors (same interface as local ExecutionController)
    # =========================================================================
    
    def get_status(self) -> ExecutionStatus:
        """Get current execution status."""
        return self.status
    
    def get_node_statuses(self) -> Dict[str, NodeStatus]:
        """Get all node statuses."""
        return self.node_statuses.copy()
    
    def get_breakpoints(self) -> Set[str]:
        """Get all breakpoints."""
        return self.breakpoints.copy()
    
    def get_progress(self) -> Dict[str, Any]:
        """Get execution progress."""
        return {
            "completed_count": self.completed_count,
            "total_count": self.total_count,
            "cycle_count": self.cycle_count,
            "current_inference": self.current_inference,
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Get full state as dict."""
        return {
            "status": self.status.value,
            "node_statuses": {k: v.value for k, v in self.node_statuses.items()},
            "breakpoints": list(self.breakpoints),
            "current_inference": self.current_inference,
            "completed_count": self.completed_count,
            "total_count": self.total_count,
            "cycle_count": self.cycle_count,
            "run_mode": self.run_mode,
            "verbose_logging": self.verbose_logging,
            "remote": True,
            "server_url": self.server_url,
            "run_id": self.run_id,
        }
    
    # =========================================================================
    # Data Access Methods (proxy to remote server)
    # =========================================================================
    
    async def get_reference_data(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """Get reference data for a concept from remote server.
        
        Returns the current tensor data for a concept including:
        - data: The tensor data
        - axes: Axis names
        - shape: Tensor shape
        
        Returns None if concept not found or has no reference.
        """
        try:
            result = await self._get(f"/api/runs/{self.run_id}/reference/{concept_name}")
            # Check if response indicates no reference
            if result and not result.get("has_reference", True):
                return None
            return result
        except Exception as e:
            logger.warning(f"Failed to get reference data for {concept_name}: {e}")
            return None
    
    async def get_all_reference_data(self) -> Dict[str, Dict[str, Any]]:
        """Get reference data for all concepts from remote server.
        
        Returns a dict mapping concept_name -> reference_data.
        """
        try:
            result = await self._get(f"/api/runs/{self.run_id}/references")
            return result if isinstance(result, dict) else {}
        except Exception as e:
            logger.warning(f"Failed to get all reference data: {e}")
            return {}
    
    async def get_concept_statuses(self) -> Dict[str, str]:
        """Get concept statuses from remote server.
        
        Returns a dict mapping concept_name -> status ('complete' | 'empty' | etc.)
        """
        try:
            result = await self._get(f"/api/runs/{self.run_id}/concept-statuses")
            # The remote endpoint may return a wrapper, extract the statuses
            if isinstance(result, dict):
                return result.get("concept_statuses", result)
            return {}
        except Exception as e:
            logger.warning(f"Failed to get concept statuses: {e}")
            return {}
    
    async def override_value(
        self,
        concept_name: str,
        new_value: Any,
        rerun_dependents: bool = False
    ) -> Dict[str, Any]:
        """Override a concept's reference value on remote server.
        
        Args:
            concept_name: The concept to override
            new_value: The new value to set
            rerun_dependents: If True, mark dependents as stale and resume
            
        Returns:
            Dict with success, overridden concept name, and stale nodes list
        """
        try:
            result = await self._post(
                f"/api/runs/{self.run_id}/override/{concept_name}",
                {"new_value": new_value, "rerun_dependents": rerun_dependents}
            )
            return result
        except Exception as e:
            logger.error(f"Failed to override value for {concept_name}: {e}")
            raise RuntimeError(f"Failed to override value: {e}")
    
    def get_logs(self, limit: int = 100, flow_index: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get logs from local cache.
        
        Note: This returns cached logs. For fresh logs, use get_logs_async.
        The SSE stream updates self.logs in real-time.
        """
        logs = self.logs
        
        # Filter by flow_index if specified
        if flow_index:
            logs = [log for log in logs if log.get("flow_index") == flow_index]
        
        # Apply limit
        return logs[-limit:] if limit else logs
    
    async def get_logs_async(
        self,
        limit: int = 100,
        flow_index: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get logs from remote server.
        
        This fetches fresh logs from the remote server.
        """
        try:
            params = f"?limit={limit}"
            if flow_index:
                params += f"&flow_index={flow_index}"
            result = await self._get(f"/api/runs/{self.run_id}/logs{params}")
            return result.get("logs", [])
        except Exception as e:
            logger.warning(f"Failed to get logs from remote: {e}")
            return self.get_logs(limit, flow_index)  # Fall back to cached logs


# =============================================================================
# Factory & Global Instance Management
# =============================================================================

# Active remote proxy (only one remote project can be active at a time)
_active_proxy: Optional[RemoteProxyExecutor] = None


def get_active_remote_proxy() -> Optional[RemoteProxyExecutor]:
    """Get the currently active remote proxy executor."""
    return _active_proxy


async def activate_remote_proxy(
    server_url: str,
    run_id: str,
    project_id: Optional[str] = None,
) -> RemoteProxyExecutor:
    """
    Activate a remote proxy for the given run.
    
    This disconnects any existing proxy and creates a new one.
    """
    global _active_proxy
    
    # Disconnect existing proxy
    if _active_proxy and _active_proxy.is_connected:
        await _active_proxy.disconnect()
    
    # Create and connect new proxy
    proxy = RemoteProxyExecutor()
    await proxy.connect(server_url, run_id, project_id)
    
    _active_proxy = proxy
    return proxy


async def deactivate_remote_proxy():
    """Deactivate and disconnect the current remote proxy."""
    global _active_proxy
    
    if _active_proxy:
        await _active_proxy.disconnect()
        _active_proxy = None

