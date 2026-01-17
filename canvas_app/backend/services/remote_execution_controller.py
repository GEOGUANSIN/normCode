"""
RemoteExecutionController - Connects to a remote normal_server.

This controller proxies execution commands to a remote normal_server via HTTP
and receives real-time events via SSE (Server-Sent Events).

It maintains a local mirror of the execution state so the canvas_app frontend
can render the graph and control execution as if it were local.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Set, List

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from schemas.execution_schemas import ExecutionStatus, NodeStatus

logger = logging.getLogger(__name__)


@dataclass
class RemoteExecutionController:
    """
    Controls execution on a remote normal_server.
    
    Mirrors the ExecutionController API but proxies all commands
    to the remote server via HTTP, and receives events via SSE.
    
    This enables the canvas_app to be used as a visual debugger
    for plans running on a separate deployment server.
    """
    
    # Remote server connection
    server_url: str = "http://localhost:8080"
    run_id: Optional[str] = None
    plan_id: Optional[str] = None
    
    # Mirrored state (updated from SSE events)
    status: ExecutionStatus = ExecutionStatus.IDLE
    node_statuses: Dict[str, NodeStatus] = field(default_factory=dict)
    breakpoints: Set[str] = field(default_factory=set)
    current_inference: Optional[str] = None
    completed_count: int = 0
    total_count: int = 0
    cycle_count: int = 0
    
    # Logs (mirrored)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # SSE subscription
    _sse_task: Optional[asyncio.Task] = None
    _session: Optional["aiohttp.ClientSession"] = None
    _connected: bool = False
    _stop_sse: bool = False
    
    # Graph data (fetched on connect)
    graph_data: Optional[Dict[str, Any]] = None
    
    # Event callbacks for WebSocket emission
    _event_callback: Optional[callable] = None
    
    # =========================================================================
    # Connection Management
    # =========================================================================
    
    async def connect(
        self,
        server_url: str,
        run_id: str,
        event_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Connect to a running execution on the remote server.
        
        Args:
            server_url: Base URL of the normal_server (e.g., http://localhost:8080)
            run_id: The run ID to connect to
            event_callback: Optional async callback for emitting events locally
            
        Returns:
            Initial state including node_statuses, breakpoints, etc.
        """
        if not HAS_AIOHTTP:
            raise RuntimeError("aiohttp is required for remote connections. Install with: pip install aiohttp")
        
        self.server_url = server_url.rstrip('/')
        self.run_id = run_id
        self._event_callback = event_callback
        self._stop_sse = False
        
        # Create HTTP session
        self._session = aiohttp.ClientSession()
        
        try:
            # Fetch initial state
            await self._sync_state()
            
            # Fetch graph data
            await self._fetch_graph()
            
            # Start SSE subscription
            self._sse_task = asyncio.create_task(self._subscribe_to_events())
            
            self._connected = True
            logger.info(f"Connected to remote run: {run_id} on {server_url}")
            
            return self.get_state()
            
        except Exception as e:
            await self.disconnect()
            raise RuntimeError(f"Failed to connect to {server_url}/runs/{run_id}: {e}")
    
    async def disconnect(self):
        """Disconnect from remote server."""
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
        
        self.run_id = None
        logger.info("Disconnected from remote server")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to a remote server."""
        return self._connected and self._session is not None
    
    async def _sync_state(self):
        """Fetch current state from remote server."""
        if not self._session:
            return
        
        # Fetch run status
        async with self._session.get(f"{self.server_url}/runs/{self.run_id}") as resp:
            if resp.status != 200:
                raise RuntimeError(f"Failed to get run status: {await resp.text()}")
            data = await resp.json()
            
            self.plan_id = data.get("plan_id")
            self.status = ExecutionStatus(data["status"]) if data["status"] in [s.value for s in ExecutionStatus] else ExecutionStatus.IDLE
            self.breakpoints = set(data.get("breakpoints", []))
            
            if data.get("progress"):
                self.completed_count = data["progress"].get("completed_count", 0)
                self.total_count = data["progress"].get("total_count", 0)
                self.cycle_count = data["progress"].get("cycle_count", 0)
                self.current_inference = data["progress"].get("current_inference")
        
        # Fetch node statuses
        async with self._session.get(f"{self.server_url}/runs/{self.run_id}/node-statuses") as resp:
            if resp.status == 200:
                data = await resp.json()
                self.node_statuses = {}
                for flow_index, status in data.get("statuses", {}).items():
                    try:
                        self.node_statuses[flow_index] = NodeStatus(status)
                    except ValueError:
                        self.node_statuses[flow_index] = NodeStatus.PENDING
    
    async def _fetch_graph(self):
        """Fetch graph visualization data from remote server."""
        if not self._session:
            return
        
        try:
            async with self._session.get(f"{self.server_url}/runs/{self.run_id}/graph") as resp:
                if resp.status == 200:
                    self.graph_data = await resp.json()
                    logger.info(f"Fetched graph data: {len(self.graph_data.get('nodes', []))} nodes")
        except Exception as e:
            logger.warning(f"Failed to fetch graph data: {e}")
            self.graph_data = None
    
    async def _subscribe_to_events(self):
        """Subscribe to SSE stream for real-time updates."""
        if not self._session:
            return
        
        url = f"{self.server_url}/api/runs/{self.run_id}/stream"
        
        while not self._stop_sse:
            try:
                async with self._session.get(url) as resp:
                    if resp.status != 200:
                        logger.warning(f"SSE connection failed: {resp.status}")
                        await asyncio.sleep(2)
                        continue
                    
                    async for line in resp.content:
                        if self._stop_sse:
                            break
                        
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            try:
                                event_data = json.loads(line[6:])
                                await self._handle_event(event_data)
                            except json.JSONDecodeError:
                                continue
                        elif line.startswith(': keepalive'):
                            continue
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                if not self._stop_sse:
                    logger.warning(f"SSE connection error: {e}")
                    await asyncio.sleep(2)
    
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle incoming SSE event and update local state."""
        event_type = event.get("event")
        
        # Update local state based on event type
        if event_type == "node:statuses":
            for flow_index, status in event.get("statuses", {}).items():
                try:
                    self.node_statuses[flow_index] = NodeStatus(status)
                except ValueError:
                    self.node_statuses[flow_index] = NodeStatus.PENDING
        
        elif event_type == "inference:started":
            flow_index = event.get("flow_index")
            self.current_inference = flow_index
            if flow_index:
                self.node_statuses[flow_index] = NodeStatus.RUNNING
        
        elif event_type == "inference:completed":
            flow_index = event.get("flow_index")
            if flow_index:
                self.node_statuses[flow_index] = NodeStatus.COMPLETED
            self.completed_count += 1
        
        elif event_type == "inference:failed":
            flow_index = event.get("flow_index")
            if flow_index:
                self.node_statuses[flow_index] = NodeStatus.FAILED
        
        elif event_type == "execution:progress":
            self.completed_count = event.get("completed_count", self.completed_count)
            self.total_count = event.get("total_count", self.total_count)
            self.cycle_count = event.get("cycle_count", self.cycle_count)
            if event.get("current_inference"):
                self.current_inference = event["current_inference"]
        
        elif event_type == "execution:paused":
            self.status = ExecutionStatus.PAUSED
        
        elif event_type == "execution:resumed":
            self.status = ExecutionStatus.RUNNING
        
        elif event_type == "breakpoint:hit":
            self.status = ExecutionStatus.PAUSED
            self.current_inference = event.get("flow_index")
        
        elif event_type == "breakpoint:set":
            flow_index = event.get("flow_index")
            if flow_index:
                self.breakpoints.add(flow_index)
        
        elif event_type == "breakpoint:cleared":
            flow_index = event.get("flow_index")
            if flow_index:
                self.breakpoints.discard(flow_index)
        
        elif event_type == "run:completed":
            self.status = ExecutionStatus.COMPLETED
        
        elif event_type == "run:failed":
            self.status = ExecutionStatus.FAILED
        
        elif event_type == "execution:stopped":
            self.status = ExecutionStatus.IDLE
        
        # Add source info and emit to local WebSocket subscribers
        event["source"] = "remote"
        event["server_url"] = self.server_url
        
        if self._event_callback:
            try:
                await self._event_callback(event_type, event)
            except Exception as e:
                logger.debug(f"Event callback error: {e}")
    
    # =========================================================================
    # Command Methods (proxy to remote)
    # =========================================================================
    
    async def _post(self, endpoint: str, json_data: Dict = None) -> Dict[str, Any]:
        """Helper to POST to remote server."""
        if not self._session:
            raise RuntimeError("Not connected to remote server")
        
        url = f"{self.server_url}{endpoint}"
        async with self._session.post(url, json=json_data) as resp:
            if resp.status >= 400:
                error = await resp.text()
                raise RuntimeError(f"Remote server error: {error}")
            return await resp.json()
    
    async def _get(self, endpoint: str) -> Dict[str, Any]:
        """Helper to GET from remote server."""
        if not self._session:
            raise RuntimeError("Not connected to remote server")
        
        url = f"{self.server_url}{endpoint}"
        async with self._session.get(url) as resp:
            if resp.status >= 400:
                error = await resp.text()
                raise RuntimeError(f"Remote server error: {error}")
            return await resp.json()
    
    async def _delete(self, endpoint: str) -> Dict[str, Any]:
        """Helper to DELETE from remote server."""
        if not self._session:
            raise RuntimeError("Not connected to remote server")
        
        url = f"{self.server_url}{endpoint}"
        async with self._session.delete(url) as resp:
            if resp.status >= 400:
                error = await resp.text()
                raise RuntimeError(f"Remote server error: {error}")
            return await resp.json()
    
    async def start(self):
        """Start/resume execution on remote server."""
        result = await self._post(f"/runs/{self.run_id}/continue")
        self.status = ExecutionStatus.RUNNING
        return result
    
    async def pause(self):
        """Pause execution on remote server."""
        result = await self._post(f"/runs/{self.run_id}/pause")
        self.status = ExecutionStatus.PAUSED
        return result
    
    async def resume(self):
        """Resume execution on remote server."""
        result = await self._post(f"/runs/{self.run_id}/continue")
        self.status = ExecutionStatus.RUNNING
        return result
    
    async def step(self):
        """Step one inference on remote server."""
        result = await self._post(f"/runs/{self.run_id}/step")
        self.status = ExecutionStatus.STEPPING
        return result
    
    async def stop(self):
        """Stop execution on remote server."""
        result = await self._post(f"/runs/{self.run_id}/stop")
        self.status = ExecutionStatus.IDLE
        return result
    
    async def run_to(self, flow_index: str):
        """Run until specific node on remote server."""
        result = await self._post(f"/runs/{self.run_id}/run-to/{flow_index}")
        self.status = ExecutionStatus.RUNNING
        return result
    
    # =========================================================================
    # Breakpoints (proxy to remote)
    # =========================================================================
    
    async def set_breakpoint(self, flow_index: str):
        """Set breakpoint on remote server."""
        result = await self._post(
            f"/runs/{self.run_id}/breakpoints",
            {"flow_index": flow_index, "enabled": True}
        )
        self.breakpoints.add(flow_index)
        return result
    
    async def clear_breakpoint(self, flow_index: str):
        """Clear breakpoint on remote server."""
        result = await self._delete(f"/runs/{self.run_id}/breakpoints/{flow_index}")
        self.breakpoints.discard(flow_index)
        return result
    
    async def clear_all_breakpoints(self):
        """Clear all breakpoints on remote server."""
        result = await self._delete(f"/runs/{self.run_id}/breakpoints")
        self.breakpoints.clear()
        return result
    
    # =========================================================================
    # Value Access (fetch from remote)
    # =========================================================================
    
    async def get_reference_data(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """Fetch concept value from remote server."""
        try:
            return await self._get(f"/runs/{self.run_id}/reference/{concept_name}")
        except Exception:
            return None
    
    async def get_all_reference_data(self) -> Dict[str, Dict[str, Any]]:
        """Fetch all concept values from remote server."""
        try:
            return await self._get(f"/runs/{self.run_id}/references")
        except Exception:
            return {}
    
    async def override_value(
        self,
        concept_name: str,
        new_value: Any,
        rerun_dependents: bool = False
    ) -> Dict[str, Any]:
        """Override value on remote server."""
        return await self._post(
            f"/runs/{self.run_id}/override/{concept_name}",
            {"new_value": new_value, "rerun_dependents": rerun_dependents}
        )
    
    # =========================================================================
    # Logs (fetch from remote)
    # =========================================================================
    
    async def get_logs(self, limit: int = 100, flow_index: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch logs from remote server."""
        try:
            params = f"?limit={limit}"
            if flow_index:
                params += f"&flow_index={flow_index}"
            result = await self._get(f"/runs/{self.run_id}/logs{params}")
            return result.get("logs", [])
        except Exception:
            return []
    
    # =========================================================================
    # State Access (local mirror)
    # =========================================================================
    
    def get_state(self) -> Dict[str, Any]:
        """Get current execution state (from local mirror)."""
        return {
            "status": self.status.value,
            "current_inference": self.current_inference,
            "completed_count": self.completed_count,
            "total_count": self.total_count,
            "cycle_count": self.cycle_count,
            "node_statuses": {k: v.value for k, v in self.node_statuses.items()},
            "breakpoints": list(self.breakpoints),
            # Remote-specific fields
            "remote": True,
            "connected": self._connected,
            "server_url": self.server_url,
            "run_id": self.run_id,
            "plan_id": self.plan_id,
        }
    
    def get_graph_data(self) -> Optional[Dict[str, Any]]:
        """Get cached graph data (fetched on connect)."""
        return self.graph_data


# =============================================================================
# Factory and Registry Integration
# =============================================================================

# Global registry of remote controllers (one per remote run)
_remote_controllers: Dict[str, RemoteExecutionController] = {}


def get_remote_controller(run_id: str) -> Optional[RemoteExecutionController]:
    """Get a remote controller by run_id."""
    return _remote_controllers.get(run_id)


async def create_remote_controller(
    server_url: str,
    run_id: str,
    event_callback: Optional[callable] = None
) -> RemoteExecutionController:
    """
    Create and connect a new remote controller.
    
    Args:
        server_url: Base URL of the normal_server
        run_id: The run ID to connect to
        event_callback: Optional callback for emitting events locally
        
    Returns:
        Connected RemoteExecutionController
    """
    controller = RemoteExecutionController()
    await controller.connect(server_url, run_id, event_callback)
    _remote_controllers[run_id] = controller
    return controller


async def disconnect_remote_controller(run_id: str):
    """Disconnect and remove a remote controller."""
    if run_id in _remote_controllers:
        controller = _remote_controllers.pop(run_id)
        await controller.disconnect()


def list_remote_controllers() -> List[Dict[str, Any]]:
    """List all active remote controller connections."""
    return [
        {
            "run_id": run_id,
            "server_url": controller.server_url,
            "connected": controller.is_connected,
            "status": controller.status.value,
        }
        for run_id, controller in _remote_controllers.items()
    ]

