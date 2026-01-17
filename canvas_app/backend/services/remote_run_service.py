"""
Remote Run Binding Service

This service connects to a remote NormCode server and relays execution events
to the local canvas frontend via WebSocket.

When a remote run is "bound" to the canvas:
1. We connect to the remote server's SSE stream for that run
2. We transform remote events into the format expected by the frontend
3. We emit them through the local event_emitter

This allows users to view and monitor remote runs as if they were local.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Try to import httpx for SSE streaming
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    logger.warning("httpx not available - remote run binding disabled")


@dataclass
class BoundRemoteRun:
    """Represents a remote run bound to the local canvas."""
    server_id: str
    server_url: str
    run_id: str
    plan_id: str
    plan_name: str
    is_active: bool = True
    _task: Optional[asyncio.Task] = field(default=None, repr=False)
    
    # Cached state
    node_statuses: Dict[str, str] = field(default_factory=dict)
    completed_count: int = 0
    total_count: int = 0
    cycle_count: int = 0
    status: str = "connecting"


class RemoteRunService:
    """Service for binding remote runs to the local canvas."""
    
    def __init__(self):
        self._bound_runs: Dict[str, BoundRemoteRun] = {}  # run_id -> BoundRemoteRun
        self._active_run_id: Optional[str] = None
    
    async def bind_run(
        self,
        server_id: str,
        server_url: str,
        run_id: str,
        plan_id: str,
        plan_name: str,
    ) -> bool:
        """
        Bind a remote run to the canvas.
        
        This starts streaming events from the remote server and relaying
        them to the local frontend.
        """
        if not HTTPX_AVAILABLE:
            logger.error("Cannot bind remote run: httpx not installed")
            return False
        
        # Check if already bound
        if run_id in self._bound_runs:
            existing = self._bound_runs[run_id]
            if existing.is_active:
                logger.info(f"Run {run_id} already bound")
                return True
        
        # Create bound run
        bound_run = BoundRemoteRun(
            server_id=server_id,
            server_url=server_url.rstrip('/'),
            run_id=run_id,
            plan_id=plan_id,
            plan_name=plan_name,
        )
        
        self._bound_runs[run_id] = bound_run
        self._active_run_id = run_id
        
        # Register as a worker for UI display in WorkersPanel
        await self._register_as_worker(bound_run)
        
        # Start streaming task
        bound_run._task = asyncio.create_task(
            self._stream_events(bound_run)
        )
        
        logger.info(f"Bound remote run: {run_id} from {server_url}")
        return True
    
    async def unbind_run(self, run_id: str) -> bool:
        """Unbind a remote run from the canvas."""
        if run_id not in self._bound_runs:
            return False
        
        bound_run = self._bound_runs[run_id]
        bound_run.is_active = False
        
        # Cancel streaming task
        if bound_run._task and not bound_run._task.done():
            bound_run._task.cancel()
            try:
                await bound_run._task
            except asyncio.CancelledError:
                pass
        
        # Remove from bound runs
        del self._bound_runs[run_id]
        
        if self._active_run_id == run_id:
            self._active_run_id = None
        
        # Unregister from worker registry
        await self._unregister_worker(run_id)
        
        # Emit unbind event
        from core.events import event_emitter
        await event_emitter.emit("remote:unbound", {
            "run_id": run_id,
            "server_id": bound_run.server_id,
        })
        
        logger.info(f"Unbound remote run: {run_id}")
        return True
    
    def get_bound_run(self, run_id: str) -> Optional[BoundRemoteRun]:
        """Get a bound run by ID."""
        return self._bound_runs.get(run_id)
    
    def get_active_run(self) -> Optional[BoundRemoteRun]:
        """Get the currently active bound run."""
        if self._active_run_id:
            return self._bound_runs.get(self._active_run_id)
        return None
    
    def list_bound_runs(self) -> list:
        """List all bound runs."""
        return [
            {
                "run_id": run.run_id,
                "server_id": run.server_id,
                "plan_id": run.plan_id,
                "plan_name": run.plan_name,
                "status": run.status,
                "is_active": run.run_id == self._active_run_id,
                "completed_count": run.completed_count,
                "total_count": run.total_count,
                "cycle_count": run.cycle_count,
            }
            for run in self._bound_runs.values()
        ]
    
    async def _stream_events(self, bound_run: BoundRemoteRun):
        """Stream events from remote server and relay to frontend."""
        from core.events import event_emitter
        
        stream_url = f"{bound_run.server_url}/api/runs/{bound_run.run_id}/stream"
        
        try:
            bound_run.status = "connecting"
            await event_emitter.emit("remote:connecting", {
                "run_id": bound_run.run_id,
                "server_id": bound_run.server_id,
                "plan_name": bound_run.plan_name,
            })
            
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", stream_url) as response:
                    if response.status_code != 200:
                        logger.error(f"Failed to connect to SSE stream: {response.status_code}")
                        bound_run.status = "error"
                        await event_emitter.emit("remote:error", {
                            "run_id": bound_run.run_id,
                            "error": f"HTTP {response.status_code}",
                        })
                        return
                    
                    bound_run.status = "connected"
                    await event_emitter.emit("remote:connected", {
                        "run_id": bound_run.run_id,
                        "server_id": bound_run.server_id,
                        "plan_name": bound_run.plan_name,
                    })
                    
                    # Process SSE events
                    async for line in response.aiter_lines():
                        if not bound_run.is_active:
                            break
                        
                        # SSE format: "data: {json}\n"
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])
                                await self._relay_event(bound_run, event_data)
                            except json.JSONDecodeError as e:
                                logger.warning(f"Invalid SSE JSON: {e}")
                        elif line.startswith(":"):
                            # Comment/keepalive - ignore
                            pass
            
            # Stream ended normally
            bound_run.status = "completed" if bound_run.status != "error" else bound_run.status
            
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled for run {bound_run.run_id}")
            bound_run.status = "cancelled"
            raise
        except Exception as e:
            logger.exception(f"SSE stream error for run {bound_run.run_id}: {e}")
            bound_run.status = "error"
            await event_emitter.emit("remote:error", {
                "run_id": bound_run.run_id,
                "error": str(e),
            })
    
    async def _relay_event(self, bound_run: BoundRemoteRun, event_data: Dict[str, Any]):
        """Transform and relay a remote event to the local frontend."""
        from core.events import event_emitter
        
        event_type = event_data.get("event", "unknown")
        
        # Map remote event types to local event types
        event_mapping = {
            "connected": "remote:connected",
            "run:started": "remote:run_started",
            "run:completed": "remote:run_completed",
            "run:failed": "remote:run_failed",
            "node:statuses": "remote:node_statuses",
            "inference:started": "remote:inference_started",
            "inference:completed": "remote:inference_completed",
            "inference:failed": "remote:inference_failed",
            "inference:error": "remote:inference_error",
            "inference:retry": "remote:inference_retry",
            "execution:progress": "remote:progress",
            "execution:paused": "remote:execution:paused",
            "execution:resumed": "remote:execution:resumed",
            "execution:stepping": "remote:execution:stepping",
            "execution:stopped": "remote:execution:stopped",
            "cycle:started": "remote:cycle_started",
            "cycle:completed": "remote:cycle_completed",
        }
        
        local_event_type = event_mapping.get(event_type, f"remote:{event_type}")
        
        # Update cached state
        if event_type == "node:statuses":
            statuses = event_data.get("statuses", {})
            bound_run.node_statuses.update(statuses)
            if "total_count" in event_data:
                bound_run.total_count = event_data["total_count"]
        
        elif event_type == "execution:progress":
            bound_run.completed_count = event_data.get("completed_count", bound_run.completed_count)
            bound_run.total_count = event_data.get("total_count", bound_run.total_count)
            bound_run.cycle_count = event_data.get("cycle_count", bound_run.cycle_count)
        
        elif event_type in ("run:completed", "run:failed"):
            bound_run.status = "completed" if event_type == "run:completed" else "failed"
        
        elif event_type == "run:started":
            bound_run.status = "running"
        
        elif event_type == "execution:paused":
            bound_run.status = "paused"
        
        elif event_type == "execution:resumed":
            bound_run.status = "running"
        
        elif event_type == "execution:stepping":
            bound_run.status = "stepping"
        
        elif event_type == "execution:stopped":
            bound_run.status = "stopped"
        
        # Update worker registry state
        await self._update_worker_state(bound_run)
        
        # Add bound run metadata
        relay_data = {
            **event_data,
            "server_id": bound_run.server_id,
            "plan_name": bound_run.plan_name,
            "is_remote": True,
        }
        
        # Emit to local frontend
        await event_emitter.emit(local_event_type, relay_data)


    async def _register_as_worker(self, bound_run: BoundRemoteRun):
        """Register the bound remote run as a worker for WorkersPanel display."""
        from core.events import event_emitter
        
        try:
            from services.execution.worker_registry import (
                get_worker_registry,
                WorkerCategory,
                WorkerStatus,
                PanelType,
            )
            
            registry = get_worker_registry()
            
            # Create a unique worker ID for the remote run
            worker_id = f"remote:{bound_run.run_id}"
            
            # Register with metadata indicating it's a remote run (no local controller)
            registry.register_worker(
                worker_id=worker_id,
                controller=None,  # No local controller for remote runs
                category=WorkerCategory.EPHEMERAL,
                name=f"Remote: {bound_run.plan_name}",
                project_id=None,  # Not a local project
                project_path=None,
                metadata={
                    "is_remote": True,
                    "server_id": bound_run.server_id,
                    "server_url": bound_run.server_url,
                    "run_id": bound_run.run_id,
                    "plan_id": bound_run.plan_id,
                    "plan_name": bound_run.plan_name,
                },
            )
            
            # Set initial status
            registry.update_status(worker_id, WorkerStatus.LOADING)
            
            # Bind to main panel so it shows as active
            registry.bind_panel("main_panel", PanelType.MAIN, worker_id)
            
            # Emit worker update event
            await event_emitter.emit("workers:updated", {
                "worker_id": worker_id,
                "action": "registered",
            })
            
            logger.info(f"Registered remote run as worker: {worker_id}")
            
        except ImportError:
            logger.debug("WorkerRegistry not available - skipping worker registration")
        except Exception as e:
            logger.warning(f"Failed to register remote run as worker: {e}")
    
    async def _unregister_worker(self, run_id: str):
        """Unregister the remote run worker."""
        from core.events import event_emitter
        
        try:
            from services.execution.worker_registry import get_worker_registry
            
            registry = get_worker_registry()
            worker_id = f"remote:{run_id}"
            
            # Unbind from main panel first
            registry.unbind_panel("main_panel")
            
            # Unregister worker
            registry.unregister_worker(worker_id)
            
            await event_emitter.emit("workers:updated", {
                "worker_id": worker_id,
                "action": "unregistered",
            })
            
            logger.info(f"Unregistered remote run worker: {worker_id}")
            
        except ImportError:
            logger.debug("WorkerRegistry not available")
        except Exception as e:
            logger.warning(f"Failed to unregister remote run worker: {e}")
    
    async def _update_worker_state(self, bound_run: BoundRemoteRun):
        """Update the worker's state in the registry based on run status."""
        try:
            from services.execution.worker_registry import get_worker_registry, WorkerStatus
            
            registry = get_worker_registry()
            worker_id = f"remote:{bound_run.run_id}"
            
            # Map bound run status to WorkerStatus
            status_map = {
                "connecting": WorkerStatus.LOADING,
                "connected": WorkerStatus.READY,
                "running": WorkerStatus.RUNNING,
                "paused": WorkerStatus.PAUSED,
                "stepping": WorkerStatus.STEPPING,
                "completed": WorkerStatus.COMPLETED,
                "failed": WorkerStatus.FAILED,
                "error": WorkerStatus.FAILED,
                "stopped": WorkerStatus.STOPPED,
                "cancelled": WorkerStatus.STOPPED,
            }
            
            worker_status = status_map.get(bound_run.status, WorkerStatus.IDLE)
            registry.update_status(worker_id, worker_status)
            
            # Update progress
            registry.update_progress(
                worker_id,
                completed_count=bound_run.completed_count,
                total_count=bound_run.total_count,
                cycle_count=bound_run.cycle_count,
            )
            
        except Exception as e:
            logger.debug(f"Could not update worker state: {e}")


# Global service instance
remote_run_service = RemoteRunService()

