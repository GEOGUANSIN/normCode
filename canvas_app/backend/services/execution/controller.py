"""
ExecutionController - Core execution control with Orchestrator integration.

This is the main controller class that manages orchestrator execution with
debugging support, including stepping, breakpoints, and real-time status updates.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Set, List
from dataclasses import dataclass, field

from schemas.execution_schemas import ExecutionStatus, NodeStatus, RunMode

logger = logging.getLogger(__name__)


@dataclass
class ExecutionController:
    """
    Controls orchestrator execution with debugging support.
    
    This controller provides inference-by-inference execution control,
    allowing for stepping, breakpoints, and real-time status updates.
    
    Each ExecutionController is associated with a specific project_id,
    enabling multiple projects to execute simultaneously.
    """
    
    # Project association
    project_id: Optional[str] = None
    # Source identifier for event routing ("main" for user projects, "controller" for chat controller)
    event_source: str = "main"
    
    # Orchestrator components
    orchestrator: Optional[Any] = None
    concept_repo: Optional[Any] = None
    inference_repo: Optional[Any] = None
    body: Optional[Any] = None
    
    # Execution state
    status: ExecutionStatus = ExecutionStatus.IDLE
    breakpoints: Set[str] = field(default_factory=set)
    current_inference: Optional[str] = None
    node_statuses: Dict[str, NodeStatus] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Run mode: SLOW (one inference at a time) or FAST (all ready per cycle)
    run_mode: RunMode = RunMode.SLOW
    
    # Execution tracking
    completed_count: int = 0
    total_count: int = 0
    cycle_count: int = 0
    
    # Step tracking for current inference
    current_step: Optional[str] = None
    current_sequence_type: Optional[str] = None
    step_progress: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Verbose logging mode
    verbose_logging: bool = False
    
    # Internal state
    _pause_event: asyncio.Event = field(default_factory=asyncio.Event)
    _stop_requested: bool = False
    _run_task: Optional[asyncio.Task] = None
    _retries: List[Any] = field(default_factory=list)
    _run_to_target: Optional[str] = None
    _log_handler: Optional[Any] = None
    _attached_loggers: List[str] = field(default_factory=list)
    _inference_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    _load_config: Optional[Dict[str, Any]] = None
    _main_loop: Optional[asyncio.AbstractEventLoop] = None
    
    # Canvas tools
    user_input_tool: Optional[Any] = None
    chat_tool: Optional[Any] = None
    canvas_tool: Optional[Any] = None
    
    # Pre-built graph for visualization (built when repositories are loaded)
    graph_data: Optional[Any] = None
    
    # Cached repository data for graph swapping (avoids re-reading from disk)
    concepts_data: List[Dict[str, Any]] = field(default_factory=list)
    inferences_data: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        self._pause_event.set()  # Not paused by default
        self._attached_loggers = []
        self._inference_metadata = {}
        self._load_config = None
        self._main_loop = None
        
        # Register tool call callback for WebSocket emission
        self._setup_agent_tool_monitoring()
    
    def _setup_agent_tool_monitoring(self):
        """Set up tool call monitoring to emit events via WebSocket."""
        from services.agent_service import agent_registry, ToolCallEvent
        
        def emit_tool_event(event: ToolCallEvent):
            """Emit tool call event through WebSocket."""
            event_type = f"tool:call_{event.status}"
            self._emit_threadsafe(event_type, event.to_dict())
        
        # Register callback with agent registry
        agent_registry.register_tool_callback("execution_controller", emit_tool_event)
        logger.info("Registered tool call monitoring for WebSocket events")
    
    # =========================================================================
    # Event Emission
    # =========================================================================
    
    async def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit event through event emitter, including project_id and source."""
        from core.events import event_emitter
        
        # Include source and project_id for event routing
        data = {**data, "source": self.event_source}
        if self.project_id:
            data["project_id"] = self.project_id
        
        # Route through WorkerRegistry for panel targeting
        worker_id = self._get_worker_id()
        if worker_id:
            self._route_through_registry(worker_id, event_type, data)
        
        await event_emitter.emit(event_type, data)
    
    def _get_worker_id(self) -> Optional[str]:
        """Get the worker ID for this controller."""
        if self.project_id:
            # User project workers have "user-" prefix
            # Chat controller workers have "chat-" prefix
            if self.event_source == "controller":
                return f"chat-{self.project_id.replace('chat-', '')}"
            else:
                return f"user-{self.project_id}"
        return None
    
    def _route_through_registry(self, worker_id: str, event_type: str, data: Dict[str, Any]):
        """Route event through WorkerRegistry for panel targeting."""
        try:
            from services.execution.worker_registry import get_worker_registry
            registry = get_worker_registry()
            
            # Get routing info and add to event data
            targets = registry.get_event_targets(worker_id)
            data["target_panels"] = targets.get("panel_ids", [])
            data["target_panel_types"] = targets.get("panel_types", [])
            data["worker_id"] = worker_id
            
            # Route the event (this notifies any registry listeners)
            registry.route_event(worker_id, event_type, data)
        except Exception as e:
            logger.debug(f"Registry routing skipped: {e}")
    
    def _emit_threadsafe(self, event_type: str, data: Dict[str, Any]):
        """Emit an event in a thread-safe manner."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._emit(event_type, data))
        except RuntimeError:
            if self._main_loop and self._main_loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._emit(event_type, data),
                    self._main_loop
                )
            else:
                logger.debug(f"Could not emit event {event_type}: no event loop available")
    
    def _emit_sync(self, event_type: str, data: Dict[str, Any]):
        """Synchronous emit callback for tools like CanvasUserInputTool."""
        self._emit_threadsafe(event_type, data)
    
    # =========================================================================
    # Logging
    # =========================================================================
    
    def _add_log(self, level: str, flow_index: str, message: str):
        """Add a log entry. Thread-safe."""
        log_entry = {
            "level": level,
            "flow_index": flow_index,
            "message": message,
            "timestamp": time.time()
        }
        self.logs.append(log_entry)
        self._emit_threadsafe("log:entry", log_entry)
    
    def get_logs(self, limit: int = 100, flow_index: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get execution logs, optionally filtered by flow_index."""
        logs = self.logs
        if flow_index:
            logs = [l for l in logs if l.get('flow_index') == flow_index or l.get('flow_index') == '']
        return logs[-limit:]
    
    def set_verbose_logging(self, enabled: bool):
        """Enable or disable verbose (DEBUG level) logging."""
        self.verbose_logging = enabled
        if self._log_handler:
            self._log_handler.verbose = enabled
            log_level = logging.DEBUG if enabled else logging.INFO
            self._log_handler.setLevel(log_level)
        self._add_log("info", "", f"Verbose logging {'enabled' if enabled else 'disabled'}")
    
    # =========================================================================
    # Log Handler Attachment
    # =========================================================================
    
    def _attach_infra_log_handlers(self):
        """Attach log handler to capture orchestrator logs."""
        if self._log_handler is not None:
            return
        
        from .log_handler import attach_log_handlers
        self._log_handler = attach_log_handlers(self, verbose=self.verbose_logging)
    
    def _detach_infra_log_handlers(self):
        """Detach log handler from infra loggers."""
        if self._log_handler is None:
            return
        
        from .log_handler import detach_log_handlers
        detach_log_handlers(self._log_handler)
        self._log_handler = None
    
    # =========================================================================
    # Step Progress Tracking
    # =========================================================================
    
    def get_step_progress(self, flow_index: Optional[str] = None) -> Dict[str, Any]:
        """Get step progress for a specific flow_index or current inference."""
        target = flow_index or self.current_inference
        if target and target in self.step_progress:
            return self.step_progress[target]
        return {}
    
    def _get_current_paradigm(self) -> Optional[str]:
        """Get the paradigm name for the current inference from cached metadata."""
        if not self.current_inference:
            return None
        
        if self.current_inference in self._inference_metadata:
            return self._inference_metadata[self.current_inference].get('paradigm')
        
        if self.inference_repo:
            try:
                for inf_entry in self.inference_repo.inferences:
                    flow_idx = inf_entry.flow_info.get('flow_index', '')
                    if flow_idx == self.current_inference:
                        wi = getattr(inf_entry, 'working_interpretation', None)
                        if wi:
                            paradigm = wi.get('paradigm') if isinstance(wi, dict) else getattr(wi, 'paradigm', None)
                            self._inference_metadata[self.current_inference] = {
                                'paradigm': paradigm,
                                'sequence': inf_entry.inference_sequence,
                            }
                            return paradigm
                        break
            except Exception as e:
                logger.debug(f"Could not get paradigm for {self.current_inference}: {e}")
        
        return None
    
    def _update_step_progress(self, flow_index: str, step_name: str, step_index: int, 
                              sequence_type: str, total_steps: int, steps: List[str]):
        """Update step progress tracking for an inference."""
        if flow_index not in self.step_progress:
            self.step_progress[flow_index] = {
                "flow_index": flow_index,
                "sequence_type": sequence_type,
                "current_step": step_name,
                "current_step_index": step_index,
                "total_steps": total_steps,
                "steps": steps,
                "completed_steps": [],
            }
        else:
            progress = self.step_progress[flow_index]
            if progress.get("current_step") and progress["current_step"] not in progress["completed_steps"]:
                progress["completed_steps"].append(progress["current_step"])
            progress["current_step"] = step_name
            progress["current_step_index"] = step_index
    
    # =========================================================================
    # State Access
    # =========================================================================
    
    def get_state(self) -> Dict[str, Any]:
        """Get current execution state."""
        return {
            "status": self.status.value,
            "current_inference": self.current_inference,
            "completed_count": self.completed_count,
            "total_count": self.total_count,
            "cycle_count": self.cycle_count,
            "node_statuses": {k: v.value for k, v in self.node_statuses.items()},
            "breakpoints": list(self.breakpoints),
            "run_mode": self.run_mode.value,
        }
    
    def _sync_status_to_registry(self):
        """Sync execution status to WorkerRegistry."""
        worker_id = self._get_worker_id()
        if not worker_id:
            return
        
        try:
            from services.execution.worker_registry import get_worker_registry, WorkerStatus as RegistryStatus
            registry = get_worker_registry()
            
            # Map ExecutionStatus to RegistryStatus
            status_map = {
                ExecutionStatus.IDLE: RegistryStatus.IDLE,
                ExecutionStatus.RUNNING: RegistryStatus.RUNNING,
                ExecutionStatus.PAUSED: RegistryStatus.PAUSED,
                ExecutionStatus.STEPPING: RegistryStatus.STEPPING,
                ExecutionStatus.COMPLETED: RegistryStatus.COMPLETED,
                ExecutionStatus.FAILED: RegistryStatus.FAILED,
            }
            
            registry_status = status_map.get(self.status, RegistryStatus.IDLE)
            registry.update_status(worker_id, registry_status)
        except Exception as e:
            logger.debug(f"Registry status sync skipped: {e}")
    
    def _sync_progress_to_registry(self):
        """Sync execution progress to WorkerRegistry."""
        worker_id = self._get_worker_id()
        if not worker_id:
            return
        
        try:
            from services.execution.worker_registry import get_worker_registry
            registry = get_worker_registry()
            
            registry.update_progress(
                worker_id=worker_id,
                current_inference=self.current_inference,
                completed_count=self.completed_count,
                total_count=self.total_count,
                cycle_count=self.cycle_count,
            )
        except Exception as e:
            logger.debug(f"Registry progress sync skipped: {e}")
    
    # =========================================================================
    # Repository Loading
    # =========================================================================
    
    async def load_repositories(
        self,
        concepts_path: str,
        inferences_path: str,
        inputs_path: Optional[str] = None,
        llm_model: str = "demo",
        base_dir: Optional[str] = None,
        max_cycles: int = 50,
        db_path: Optional[str] = None,
        paradigm_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Load repositories and create orchestrator."""
        import json as json_module
        
        try:
            from infra._orchest._repo import ConceptRepo, InferenceRepo
            from infra._agent._body import Body
            from infra._orchest._orchestrator import Orchestrator
            from infra._core import set_dev_mode
            set_dev_mode(True)
            logger.info("Enabled infra dev mode for debugging")
        except ImportError as e:
            logger.error(f"Failed to import infra modules: {e}")
            raise RuntimeError(f"Failed to import infra modules: {e}")
        
        # Load repository files and cache for later use (graph swapping)
        with open(concepts_path, 'r', encoding='utf-8') as f:
            self.concepts_data = json_module.load(f)
        with open(inferences_path, 'r', encoding='utf-8') as f:
            self.inferences_data = json_module.load(f)
        
        # Create repositories
        self.concept_repo = ConceptRepo.from_json_list(self.concepts_data)
        self.inference_repo = InferenceRepo.from_json_list(self.inferences_data, self.concept_repo)
        
        # Load inputs if provided
        if inputs_path:
            with open(inputs_path, 'r', encoding='utf-8') as f:
                inputs_data = json_module.load(f)
            for name, value in inputs_data.items():
                if isinstance(value, dict) and 'data' in value:
                    self.concept_repo.add_reference(
                        name, 
                        value['data'], 
                        axis_names=value.get('axes')
                    )
                else:
                    self.concept_repo.add_reference(name, value)
        
        # Set base directory
        if base_dir is None:
            base_dir = str(Path(concepts_path).parent)
        
        # Create custom paradigm tool if specified
        from .paradigm_tool import create_paradigm_tool
        custom_paradigm_tool = create_paradigm_tool(paradigm_dir, base_dir)
        if custom_paradigm_tool:
            self._add_log("info", "", f"Using custom paradigms from: {paradigm_dir}")
        
        # Create Body
        self.body = Body(
            llm_name=llm_model, 
            base_dir=base_dir,
            paradigm_tool=custom_paradigm_tool
        )
        
        # Inject canvas tools
        from .tool_injection import inject_canvas_tools, setup_tool_monitoring
        canvas_tools = inject_canvas_tools(self.body, self._emit_sync)
        self.user_input_tool = canvas_tools.user_input_tool
        self.chat_tool = canvas_tools.chat_tool
        self.canvas_tool = canvas_tools.canvas_tool
        
        # Set up tool monitoring
        setup_tool_monitoring(
            self.body,
            lambda: self.current_inference or "",
            self._emit_threadsafe
        )
        
        # Determine database path
        if db_path is None:
            db_path = str(Path(base_dir) / "orchestration.db")
        else:
            db_path_obj = Path(db_path)
            if not db_path_obj.is_absolute():
                db_path = str(Path(base_dir) / db_path)

        logger.info(f"Creating orchestrator with max_cycles={max_cycles}, db_path={db_path}")
        
        # Create orchestrator
        self.orchestrator = await asyncio.to_thread(
            Orchestrator,
            concept_repo=self.concept_repo,
            inference_repo=self.inference_repo,
            body=self.body,
            max_cycles=max_cycles,
            db_path=db_path
        )
        
        # Initialize iteration history service and set callback for loop snapshot saving
        from .iteration_history_service import iteration_history_service
        iteration_history_service.initialize(db_path)
        self.orchestrator.set_before_reset_callback(
            iteration_history_service.save_iteration_snapshot
        )
        logger.info("Iteration history service initialized and callback registered")
        
        # Initialize node statuses
        self.node_statuses = {}
        self.total_count = 0
        self.completed_count = 0
        
        for inf in self.inferences_data:
            flow_index = inf.get('flow_info', {}).get('flow_index', '')
            if flow_index:
                self.node_statuses[flow_index] = NodeStatus.PENDING
                self.total_count += 1
        
        # Sync ground concept statuses from blackboard
        # Ground concepts are already marked 'complete' in blackboard during initialization
        self._sync_ground_concept_statuses()
        
        # Build graph for visualization (stored for when "view" is clicked)
        # This cached graph_data enables fast tab switching without disk I/O
        try:
            from services.graph_service import build_graph_from_repositories
            self.graph_data = build_graph_from_repositories(self.concepts_data, self.inferences_data)
            logger.info(f"Pre-built graph: {len(self.graph_data.nodes)} nodes, {len(self.graph_data.edges)} edges")
        except Exception as e:
            logger.warning(f"Failed to pre-build graph: {e}")
            self.graph_data = None
        
        self.status = ExecutionStatus.IDLE
        self._retries = []
        self.cycle_count = 0
        self.logs = []
        
        # Store config for restart
        self._load_config = {
            "concepts_path": concepts_path,
            "inferences_path": inferences_path,
            "inputs_path": inputs_path,
            "llm_model": llm_model,
            "base_dir": base_dir,
            "max_cycles": max_cycles,
            "db_path": db_path,
            "paradigm_dir": paradigm_dir,
        }
        
        await self._emit("execution:loaded", {
            "run_id": getattr(self.orchestrator, 'run_id', 'unknown'),
            "total_inferences": self.total_count,
            "completed_count": self.completed_count,
            "node_statuses": {k: v.value for k, v in self.node_statuses.items()},
        })
        
        self._add_log("info", "", f"Loaded {len(self.concepts_data)} concepts and {self.total_count} inferences (inputs: {self.completed_count} pre-completed)")
        self._add_log("info", "", f"Config: model={llm_model}, max_cycles={max_cycles}, db={db_path}")
        
        if self.orchestrator and self.orchestrator.checkpoint_manager:
            self._add_log("info", "", f"Checkpoint manager initialized for run: {self.orchestrator.run_id}")
        else:
            self._add_log("warning", "", "Checkpoint manager NOT initialized")
        
        return {
            "run_id": getattr(self.orchestrator, 'run_id', 'unknown'),
            "total_inferences": self.total_count,
            "concepts_count": len(self.concepts_data),
            "config": {
                "llm_model": llm_model,
                "max_cycles": max_cycles,
                "db_path": db_path,
                "base_dir": base_dir,
            }
        }
    
    # =========================================================================
    # Execution Control
    # =========================================================================
    
    async def start(self):
        """Start or resume execution."""
        if self.orchestrator is None:
            raise RuntimeError("No repositories loaded. Call load_repositories first.")

        if self.status == ExecutionStatus.PAUSED:
            await self.resume()
            return

        self._main_loop = asyncio.get_running_loop()
        self._attach_infra_log_handlers()

        self.status = ExecutionStatus.RUNNING
        self._stop_requested = False
        self._pause_event.set()
        
        # Sync to registry
        self._sync_status_to_registry()
        
        if hasattr(self, 'chat_tool') and self.chat_tool:
            self.chat_tool.set_execution_active(True)

        await self._emit("execution:started", {})
        self._add_log("info", "", "Execution started")
        
        self._run_task = asyncio.create_task(self._run_loop())
    
    async def pause(self):
        """Pause execution after current inference."""
        self.status = ExecutionStatus.PAUSED
        self._pause_event.clear()
        self._sync_status_to_registry()
        await self._emit("execution:paused", {"inference": self.current_inference})
        self._add_log("info", "", f"Execution paused at {self.current_inference or 'start'}")
    
    async def resume(self):
        """Resume from paused state."""
        self.status = ExecutionStatus.RUNNING
        self._pause_event.set()
        self._sync_status_to_registry()
        await self._emit("execution:resumed", {})
        self._add_log("info", "", "Execution resumed")
    
    async def step(self):
        """Execute single inference then pause."""
        if self.orchestrator is None:
            raise RuntimeError("No repositories loaded.")
        
        self._main_loop = asyncio.get_running_loop()
        self._attach_infra_log_handlers()
        
        self.status = ExecutionStatus.STEPPING
        self._pause_event.set()
        
        if self._run_task is None or self._run_task.done():
            self._run_task = asyncio.create_task(self._run_loop())
        
        await self._emit("execution:stepping", {})
        self._add_log("info", "", "Stepping to next inference")
    
    async def stop(self):
        """Stop execution."""
        self._stop_requested = True
        self._pause_event.set()

        if hasattr(self, 'chat_tool') and self.chat_tool:
            self.chat_tool.set_execution_active(False)
            with self.chat_tool._lock:
                pending_ids = list(self.chat_tool._pending_requests.keys())
            for req_id in pending_ids:
                self.chat_tool.cancel_request(req_id)
                logger.debug(f"Cancelled pending chat request: {req_id}")

        if self._run_task and not self._run_task.done():
            self._run_task.cancel()
            try:
                await self._run_task
            except asyncio.CancelledError:
                pass

        self._detach_infra_log_handlers()

        self.status = ExecutionStatus.IDLE
        self._sync_status_to_registry()
        await self._emit("execution:stopped", {})
        self._add_log("info", "", "Execution stopped")
    
    async def restart(self):
        """Restart execution from the beginning with a fresh orchestrator."""
        if self._load_config is None:
            raise RuntimeError("No repositories loaded. Call load_repositories first.")
        
        await self.stop()
        saved_breakpoints = self.breakpoints.copy()
        
        self._add_log("info", "", "Restarting with fresh orchestrator...")
        
        config = self._load_config
        result = await self.load_repositories(
            concepts_path=config["concepts_path"],
            inferences_path=config["inferences_path"],
            inputs_path=config.get("inputs_path"),
            llm_model=config.get("llm_model", "demo"),
            base_dir=config.get("base_dir"),
            max_cycles=config.get("max_cycles", 50),
            db_path=config.get("db_path"),
            paradigm_dir=config.get("paradigm_dir"),
        )
        
        self.breakpoints = saved_breakpoints
        
        new_run_id = result.get("run_id", "unknown")
        self._add_log("info", "", f"Fresh orchestrator created with new run_id: {new_run_id}")
        
        await self._emit("execution:reset", {
            "node_statuses": {k: v.value for k, v in self.node_statuses.items()},
            "completed_count": 0,
            "total_count": self.total_count,
            "run_id": new_run_id,
        })
        self._add_log("info", "", "Execution reset - ready to run again")
    
    async def run_to(self, target_flow_index: str):
        """Run execution until a specific flow_index is reached."""
        if self.orchestrator is None:
            raise RuntimeError("No repositories loaded. Call load_repositories first.")
        
        if target_flow_index not in self.node_statuses:
            raise ValueError(f"Unknown flow_index: {target_flow_index}")
        
        if self.node_statuses.get(target_flow_index) == NodeStatus.COMPLETED:
            raise ValueError(f"Target node {target_flow_index} is already completed")
        
        self._main_loop = asyncio.get_running_loop()
        self._attach_infra_log_handlers()

        self._run_to_target = target_flow_index
        self.status = ExecutionStatus.RUNNING
        self._stop_requested = False
        self._pause_event.set()
        
        await self._emit("execution:started", {"run_to": target_flow_index})
        self._add_log("info", "", f"Running to {target_flow_index}")
        
        self._run_task = asyncio.create_task(self._run_loop())
    
    # =========================================================================
    # Breakpoints
    # =========================================================================
    
    def set_breakpoint(self, flow_index: str):
        """Add breakpoint at flow_index."""
        self.breakpoints.add(flow_index)
        asyncio.create_task(self._emit("breakpoint:set", {"flow_index": flow_index}))
        self._add_log("info", flow_index, f"Breakpoint set")
    
    def clear_breakpoint(self, flow_index: str):
        """Remove breakpoint."""
        self.breakpoints.discard(flow_index)
        asyncio.create_task(self._emit("breakpoint:cleared", {"flow_index": flow_index}))
        self._add_log("info", flow_index, f"Breakpoint cleared")
    
    # =========================================================================
    # Run Mode
    # =========================================================================
    
    def set_run_mode(self, mode: RunMode):
        """Set the execution run mode.
        
        Args:
            mode: RunMode.SLOW (one inference at a time) or RunMode.FAST (all ready per cycle)
        """
        old_mode = self.run_mode
        self.run_mode = mode
        self._add_log("info", "", f"Run mode changed: {old_mode.value} → {mode.value}")
        asyncio.create_task(self._emit("execution:run_mode_changed", {"mode": mode.value}))
    
    # =========================================================================
    # Execution Loop
    # =========================================================================
    
    async def _run_loop(self):
        """Main execution loop with inference-by-inference control."""
        from services.agent_service import agent_registry
        from .checkpoint_service import checkpoint_service
        
        try:
            while self.status in (ExecutionStatus.RUNNING, ExecutionStatus.STEPPING):
                if self._stop_requested:
                    break
                
                if not self._pause_event.is_set():
                    await self._pause_event.wait()
                    if self._stop_requested:
                        break
                
                has_pending = await asyncio.to_thread(
                    lambda: self.orchestrator.blackboard.get_all_pending_or_in_progress_items()
                )
                
                if not has_pending:
                    break
                
                if self.cycle_count >= self.orchestrator.max_cycles:
                    self._add_log("error", "", f"Maximum cycles ({self.orchestrator.max_cycles}) reached")
                    break
                
                self.cycle_count += 1
                if hasattr(self.orchestrator, 'tracker'):
                    self.orchestrator.tracker.cycle_count = self.cycle_count
                self._add_log("info", "", f"Starting cycle {self.cycle_count}")
                
                progress_made = await self._run_cycle_with_events()
                
                if self.orchestrator and self.orchestrator.checkpoint_manager:
                    saved = await checkpoint_service.save_checkpoint(
                        self.orchestrator, self.cycle_count, 0
                    )
                    if saved:
                        self._add_log("debug", "", f"Checkpoint saved for cycle {self.cycle_count}")
                
                if not progress_made:
                    self._add_log("warning", "", "No progress made in cycle - possible deadlock")
                    break
                
                if self.status == ExecutionStatus.STEPPING:
                    self.status = ExecutionStatus.PAUSED
                    self._pause_event.clear()
                    await self._emit("execution:paused", {"inference": self.current_inference})
                    break
            
            if not self._stop_requested and self.status != ExecutionStatus.PAUSED:
                self.status = ExecutionStatus.COMPLETED
                self._sync_status_to_registry()
                self._sync_progress_to_registry()
                self._detach_infra_log_handlers()
                await self._emit("execution:completed", {
                    "completed_count": self.completed_count,
                    "total_count": self.total_count
                })
                self._add_log("info", "", "Execution completed")

        except asyncio.CancelledError:
            logger.info("Execution cancelled")
            self._detach_infra_log_handlers()
        except Exception as e:
            self.status = ExecutionStatus.FAILED
            self._sync_status_to_registry()
            self._detach_infra_log_handlers()
            await self._emit("execution:error", {"error": str(e)})
            self._add_log("error", "", f"Execution failed: {str(e)}")
            logger.exception("Execution failed")
    
    async def _run_cycle_with_events(self) -> bool:
        """Process one cycle with event emission for each inference."""
        from services.agent_service import agent_registry
        
        cycle_executions = 0
        next_retries = []
        
        retried_items_set = set(self._retries)
        items_to_process = self._retries + [
            item for item in self.orchestrator.waitlist.items 
            if item not in retried_items_set
        ]
        
        for item in items_to_process:
            if self._stop_requested:
                break
            
            if not self._pause_event.is_set():
                await self._pause_event.wait()
                if self._stop_requested:
                    break
            
            flow_index = item.inference_entry.flow_info['flow_index']
            
            item_status = await asyncio.to_thread(
                lambda: self.orchestrator.blackboard.get_item_status(flow_index)
            )
            
            if item_status != 'pending':
                continue
            
            is_ready = await asyncio.to_thread(
                lambda: self.orchestrator._is_ready(item)
            )
            
            if not is_ready:
                continue
            
            # Check breakpoint
            if flow_index in self.breakpoints:
                self.status = ExecutionStatus.PAUSED
                self._pause_event.clear()
                self.current_inference = flow_index
                await self._emit("breakpoint:hit", {"flow_index": flow_index})
                self._add_log("info", flow_index, "Breakpoint hit - execution paused")
                await self._pause_event.wait()
                if self._stop_requested:
                    break
            
            # Execute inference
            cycle_executions += 1
            self.current_inference = flow_index
            agent_registry.set_current_flow_index(flow_index)
            
            self.node_statuses[flow_index] = NodeStatus.RUNNING
            await self._emit("inference:started", {
                "flow_index": flow_index,
                "concept_name": item.inference_entry.concept_to_infer.concept_name,
                "sequence": item.inference_entry.inference_sequence
            })
            self._add_log("info", flow_index, f"Executing: {item.inference_entry.concept_to_infer.concept_name}")
            
            try:
                start_time = time.time()
                new_status = await asyncio.to_thread(
                    self.orchestrator._execute_item,
                    item
                )
                duration = time.time() - start_time
                
                if new_status == 'completed':
                    self.node_statuses[flow_index] = NodeStatus.COMPLETED
                    self.completed_count += 1
                    self._sync_progress_to_registry()
                    await self._emit("inference:completed", {
                        "flow_index": flow_index,
                        "duration": duration
                    })
                    self._add_log("info", flow_index, f"Completed in {duration:.2f}s")
                    
                    # NOTE: We intentionally do NOT propagate status to alias nodes here.
                    # Each node's status reflects whether the INFERENCE at that position has run,
                    # not just whether the underlying concept has data. Alias nodes that are
                    # inputs to other inferences should stay "pending" until those inferences run.
                    # Ground concepts (initial inputs) are handled separately by _sync_ground_concept_statuses().
                    
                    if self._run_to_target and flow_index == self._run_to_target:
                        self._run_to_target = None
                        self.status = ExecutionStatus.PAUSED
                        self._pause_event.clear()
                        await self._emit("execution:paused", {
                            "inference": flow_index,
                            "reason": "run_to_target_reached"
                        })
                        self._add_log("info", flow_index, "Run-to target reached - execution paused")
                        break
                else:
                    self.node_statuses[flow_index] = NodeStatus.PENDING
                    next_retries.append(item)
                    await self._emit("inference:retry", {
                        "flow_index": flow_index,
                        "status": new_status
                    })
                    self._add_log("warning", flow_index, f"Needs retry: {new_status}")
                
                await self._emit("execution:progress", {
                    "completed_count": self.completed_count,
                    "total_count": self.total_count,
                    "current_inference": flow_index
                })
                
            except Exception as e:
                self.node_statuses[flow_index] = NodeStatus.FAILED
                await self._emit("inference:failed", {
                    "flow_index": flow_index,
                    "error": str(e)
                })
                self._add_log("error", flow_index, f"Failed: {str(e)}")
                logger.exception(f"Inference {flow_index} failed")
            
            # STEPPING mode: pause after one inference
            if self.status == ExecutionStatus.STEPPING:
                self.status = ExecutionStatus.PAUSED
                self._pause_event.clear()
                await self._emit("execution:paused", {"inference": flow_index})
                break
            
            # SLOW run mode: execute one inference per cycle, then move to next cycle
            # This allows the UI to update between inferences while still running continuously
            if self.run_mode == RunMode.SLOW:
                break
        
        self._retries = next_retries
        
        self._add_log("info", "", f"Cycle {self.cycle_count}: {cycle_executions} executions, {self.completed_count}/{self.total_count} complete")
        
        return cycle_executions > 0
    
    # =========================================================================
    # Value Access (delegates to ValueService)
    # =========================================================================
    
    def get_reference_data(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """Get reference data for a concept."""
        from .value_service import value_service
        return value_service.get_reference_data(self.concept_repo, concept_name)
    
    def get_all_reference_data(self) -> Dict[str, Dict[str, Any]]:
        """Get reference data for all concepts that have references."""
        from .value_service import value_service
        return value_service.get_all_reference_data(self.concept_repo)
    
    def get_concept_statuses(self) -> Dict[str, str]:
        """Get concept statuses directly from the blackboard.
        
        Returns a dict mapping concept_name -> status ('complete' | 'empty' | etc.)
        This queries the infra layer directly, making it the source of truth
        for whether a concept has data.
        """
        if not self.orchestrator or not self.orchestrator.blackboard:
            return {}
        
        # Get all concept statuses from the blackboard
        return dict(self.orchestrator.blackboard.concept_statuses)
    
    def _find_dependents(self, concept_name: str) -> List[str]:
        """Find all flow_indices that depend on a concept."""
        from .value_service import value_service
        return value_service.find_dependents(self.inference_repo, concept_name)
    
    def _find_descendants(self, flow_index: str) -> List[str]:
        """Find all nodes downstream from a flow_index."""
        from .value_service import value_service
        return value_service.find_descendants(self.inference_repo, self.concept_repo, flow_index)
    
    # =========================================================================
    # Iteration History Access
    # =========================================================================
    
    def get_iteration_history(self, concept_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get historical iteration values for a concept."""
        from .iteration_history_service import iteration_history_service
        
        if not self.orchestrator:
            return []
        
        return iteration_history_service.get_iteration_history(
            run_id=self.orchestrator.run_id,
            concept_name=concept_name,
            limit=limit
        )
    
    def get_flow_iteration_history(self, flow_index: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get historical iteration values for a specific flow_index."""
        from .iteration_history_service import iteration_history_service
        
        if not self.orchestrator:
            return []
        
        return iteration_history_service.get_flow_iteration_history(
            run_id=self.orchestrator.run_id,
            flow_index=flow_index,
            limit=limit
        )
    
    # =========================================================================
    # Value Override Methods
    # =========================================================================
    
    async def override_value(
        self,
        concept_name: str,
        new_value: Any,
        rerun_dependents: bool = False
    ) -> Dict[str, Any]:
        """Override a concept's reference value."""
        if self.concept_repo is None:
            raise RuntimeError("No repositories loaded.")
        
        from .value_service import value_service
        
        try:
            result = value_service.override_value(
                self.concept_repo,
                self.inference_repo,
                concept_name,
                new_value
            )
            
            stale_nodes = result["stale_nodes"]
            
            # Mark nodes as pending
            for flow_index in stale_nodes:
                if flow_index in self.node_statuses:
                    self.node_statuses[flow_index] = NodeStatus.PENDING
            
            self._add_log("info", "", f"Overridden value for '{concept_name}', {len(stale_nodes)} nodes marked stale")
            
            await self._emit("value:overridden", {
                "concept_name": concept_name,
                "stale_nodes": stale_nodes,
            })
            
            if rerun_dependents and stale_nodes:
                await self.start()
            
            return {
                "success": True,
                "overridden": concept_name,
                "stale_nodes": stale_nodes,
            }
            
        except Exception as e:
            logger.error(f"Failed to override value for {concept_name}: {e}")
            raise
    
    # =========================================================================
    # Selective Re-run Methods
    # =========================================================================
    
    async def rerun_from(self, flow_index: str) -> Dict[str, Any]:
        """Reset and re-execute from a specific node."""
        if self.orchestrator is None:
            raise RuntimeError("No repositories loaded.")
        
        if flow_index not in self.node_statuses:
            raise ValueError(f"Unknown flow_index: {flow_index}")
        
        if self.status in (ExecutionStatus.RUNNING, ExecutionStatus.STEPPING):
            await self.stop()
        
        descendants = self._find_descendants(flow_index)
        nodes_to_reset = [flow_index] + descendants
        
        self._add_log("info", flow_index, f"Re-running from {flow_index}, resetting {len(nodes_to_reset)} nodes")
        
        # Reset node statuses
        for fi in nodes_to_reset:
            if fi in self.node_statuses:
                self.node_statuses[fi] = NodeStatus.PENDING
                self.completed_count = max(0, self.completed_count - 1)
        
        # Clear computed references
        for fi in nodes_to_reset:
            try:
                for inf_entry in self.inference_repo.inferences:
                    if inf_entry.flow_info.get('flow_index') == fi:
                        concept_name = inf_entry.concept_to_infer.concept_name
                        concept_entry = self.concept_repo.get_concept(concept_name)
                        if concept_entry:
                            concept = concept_entry.concept if hasattr(concept_entry, 'concept') else None
                            if concept and not getattr(concept, 'is_ground_concept', False):
                                concept.reference = None
                        break
            except Exception as e:
                logger.warning(f"Could not clear reference for {fi}: {e}")
        
        # Reset blackboard (status AND execution count)
        try:
            for fi in nodes_to_reset:
                if self.orchestrator.blackboard:
                    self.orchestrator.blackboard.set_item_status(fi, 'pending')
                    self.orchestrator.blackboard.reset_execution_count(fi)
        except Exception as e:
            logger.warning(f"Could not reset blackboard for some nodes: {e}")
        
        await self._emit("execution:partial_reset", {
            "reset_nodes": nodes_to_reset,
            "from_flow_index": flow_index,
        })
        
        await self.start()
        
        return {
            "success": True,
            "from_flow_index": flow_index,
            "reset_count": len(nodes_to_reset),
            "reset_nodes": nodes_to_reset,
        }
    
    # =========================================================================
    # Function Modification Methods
    # =========================================================================
    
    async def modify_function(
        self,
        flow_index: str,
        modifications: Dict[str, Any],
        retry: bool = False
    ) -> Dict[str, Any]:
        """Modify a function node's working interpretation."""
        if self.inference_repo is None:
            raise RuntimeError("No repositories loaded.")
        
        target_inference = None
        for inf_entry in self.inference_repo.inferences:
            if inf_entry.flow_info.get('flow_index') == flow_index:
                target_inference = inf_entry
                break
        
        if target_inference is None:
            raise ValueError(f"Inference not found for flow_index: {flow_index}")
        
        wi = getattr(target_inference, 'working_interpretation', {})
        if not isinstance(wi, dict):
            wi = {}
        
        modified_fields = []
        for key, value in modifications.items():
            if value is not None:
                wi[key] = value
                modified_fields.append(key)
        
        target_inference.working_interpretation = wi
        
        if flow_index in self.node_statuses:
            self.node_statuses[flow_index] = NodeStatus.PENDING
        
        self._add_log("info", flow_index, f"Modified working interpretation: {', '.join(modified_fields)}")
        
        await self._emit("function:modified", {
            "flow_index": flow_index,
            "modified_fields": modified_fields,
        })
        
        if retry:
            await self.run_to(flow_index)
        
        return {
            "success": True,
            "flow_index": flow_index,
            "modified_fields": modified_fields,
        }
    
    # =========================================================================
    # Checkpoint Management (delegates to CheckpointService)
    # =========================================================================
    
    async def list_runs(self, db_path: str) -> List[Dict[str, Any]]:
        """List all runs stored in the checkpoint database."""
        from .checkpoint_service import checkpoint_service
        return await checkpoint_service.list_runs(db_path)
    
    async def list_checkpoints(self, db_path: str, run_id: str) -> List[Dict[str, Any]]:
        """List all checkpoints for a specific run."""
        from .checkpoint_service import checkpoint_service
        return await checkpoint_service.list_checkpoints(db_path, run_id)
    
    async def get_run_metadata(self, db_path: str, run_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific run."""
        from .checkpoint_service import checkpoint_service
        return await checkpoint_service.get_run_metadata(db_path, run_id)
    
    async def delete_run(self, db_path: str, run_id: str) -> Dict[str, Any]:
        """Delete a run and all its checkpoints."""
        from .checkpoint_service import checkpoint_service
        return await checkpoint_service.delete_run(db_path, run_id)
    
    # =========================================================================
    # Checkpoint Resume/Fork
    # =========================================================================
    
    async def _load_repos_and_body(
        self,
        concepts_path: str,
        inferences_path: str,
        inputs_path: Optional[str],
        llm_model: str,
        base_dir: Optional[str],
        paradigm_dir: Optional[str]
    ):
        """Internal helper to load repositories and create body."""
        import json as json_module
        
        try:
            from infra._orchest._repo import ConceptRepo, InferenceRepo
            from infra._agent._body import Body
        except ImportError as e:
            raise RuntimeError(f"Failed to import infra modules: {e}")
        
        with open(concepts_path, 'r', encoding='utf-8') as f:
            concepts_data = json_module.load(f)
        with open(inferences_path, 'r', encoding='utf-8') as f:
            inferences_data = json_module.load(f)
        
        self.concept_repo = ConceptRepo.from_json_list(concepts_data)
        self.inference_repo = InferenceRepo.from_json_list(inferences_data, self.concept_repo)
        
        if inputs_path:
            with open(inputs_path, 'r', encoding='utf-8') as f:
                inputs_data = json_module.load(f)
            for name, value in inputs_data.items():
                if isinstance(value, dict) and 'data' in value:
                    self.concept_repo.add_reference(
                        name, 
                        value['data'], 
                        axis_names=value.get('axes')
                    )
                else:
                    self.concept_repo.add_reference(name, value)
        
        if base_dir is None:
            base_dir = str(Path(concepts_path).parent)
        
        from .paradigm_tool import create_paradigm_tool
        custom_paradigm_tool = create_paradigm_tool(paradigm_dir, base_dir)
        
        self.body = Body(
            llm_name=llm_model, 
            base_dir=base_dir,
            paradigm_tool=custom_paradigm_tool
        )
        
        from .tool_injection import inject_canvas_tools, setup_tool_monitoring
        canvas_tools = inject_canvas_tools(self.body, self._emit_sync)
        self.user_input_tool = canvas_tools.user_input_tool
        self.chat_tool = canvas_tools.chat_tool
        self.canvas_tool = canvas_tools.canvas_tool
        
        setup_tool_monitoring(
            self.body,
            lambda: self.current_inference or "",
            self._emit_threadsafe
        )
        
        return concepts_data, inferences_data, base_dir
    
    def _sync_ground_concept_statuses(self):
        """
        Sync node statuses for concepts that have actual reference data (input values).
        
        Only concepts with actual reference data should be marked as complete.
        This includes:
        - Concepts that received data from inputs.json
        - Ground VALUE concepts that have initial reference_data in concepts.json
        
        Ground FUNCTION concepts (like functional specifications) should NOT be marked
        complete just because they're "ground" - they need to be executed to produce output.
        
        This method updates the node_statuses dict to reflect that, so the UI shows
        input concept nodes as 'completed' instead of 'pending'.
        
        Note: Ground concept VALUE nodes may not have corresponding inferences,
        so we also ADD entries for flow_indices that aren't already tracked.
        """
        if not self.orchestrator or not self.orchestrator.blackboard:
            logger.debug("Cannot sync ground concept statuses: no orchestrator or blackboard")
            return
        
        if not self.concept_repo:
            logger.debug("Cannot sync ground concept statuses: no concept_repo")
            return
        
        input_concepts_synced = 0
        input_concepts_added = 0
        
        for concept_entry in self.concept_repo.get_all_concepts():
            concept_name = concept_entry.concept_name
            
            # Only mark concept as complete if it has ACTUAL reference data
            # This includes data from inputs.json or initial reference_data in concepts.json
            # Don't rely on is_ground_concept flag - only the presence of data matters
            has_reference_data = (
                concept_entry.concept is not None and 
                concept_entry.concept.reference is not None
            )
            
            if has_reference_data:
                # Mark in blackboard as complete since it has data
                self.orchestrator.blackboard.set_concept_status(concept_name, 'complete')
                
                # Mark all flow indices for this concept as completed
                flow_indices = concept_entry.flow_indices or []
                for flow_index in flow_indices:
                    if flow_index in self.node_statuses:
                        # Update existing entry
                        if self.node_statuses[flow_index] == NodeStatus.PENDING:
                            self.node_statuses[flow_index] = NodeStatus.COMPLETED
                            self.completed_count += 1
                            input_concepts_synced += 1
                    else:
                        # Add new entry for ground concept node that has no inference
                        self.node_statuses[flow_index] = NodeStatus.COMPLETED
                        input_concepts_added += 1
                
                logger.debug(f"Marked concept '{concept_name}' as complete (has reference data)")
        
        if input_concepts_synced > 0 or input_concepts_added > 0:
            logger.info(f"Input concept sync: {input_concepts_synced} updated, {input_concepts_added} added as COMPLETED")
    
    def _sync_alias_node_statuses(self, concept_name: str, new_status: NodeStatus) -> List[str]:
        """
        Propagate status to all alias nodes (twin nodes) of the same concept.
        
        When a concept is inferred at one flow_index, all other nodes representing
        the same concept (alias/twin nodes connected by ≡ edges) should also be
        updated to reflect the same status.
        
        Args:
            concept_name: The name of the concept that was completed
            new_status: The status to set for all alias nodes
            
        Returns:
            List of flow_indices that were updated (excluding the original)
        """
        if not self.concept_repo:
            return []
        
        updated_aliases = []
        
        try:
            concept_entry = self.concept_repo.get_concept(concept_name)
            if not concept_entry:
                return []
            
            # Get all flow indices where this concept appears
            flow_indices = concept_entry.flow_indices or []
            
            for flow_index in flow_indices:
                if flow_index in self.node_statuses:
                    # This flow_index is an INFERENCE TARGET - it has its own inference to run.
                    # Don't mark it as completed just because the concept has data elsewhere.
                    # Its status should only change when ITS OWN inference executes.
                    # Skip this node - the user is right that it "needs to be run again".
                    logger.debug(f"Alias sync: {concept_name}@{flow_index} SKIPPED (is inference target, needs own execution)")
                    continue
                else:
                    # This flow_index exists in the graph but isn't an inference target
                    # (e.g., it's a value concept that appears in an inference but isn't the concept_to_infer)
                    # Safe to mark as completed since it just represents "data availability"
                    self.node_statuses[flow_index] = new_status
                    updated_aliases.append(flow_index)
                    logger.debug(f"Alias sync: {concept_name}@{flow_index} (value node) -> {new_status.value}")
            
            if updated_aliases:
                logger.info(f"Alias sync for '{concept_name}': updated {len(updated_aliases)} twin nodes to {new_status.value}")
                
        except Exception as e:
            logger.warning(f"Failed to sync alias statuses for '{concept_name}': {e}")
        
        return updated_aliases
    
    def _sync_node_statuses_from_orchestrator(self):
        """Sync node statuses from orchestrator's blackboard after loading checkpoint."""
        if not self.orchestrator or not self.orchestrator.blackboard:
            return
        
        self.node_statuses = {}
        self.completed_count = 0
        self.total_count = 0
        
        for item in self.orchestrator.waitlist.items:
            flow_index = item.inference_entry.flow_info.get('flow_index', '')
            if not flow_index:
                continue
            
            self.total_count += 1
            status = self.orchestrator.blackboard.get_item_status(flow_index)
            
            if status == 'completed':
                self.node_statuses[flow_index] = NodeStatus.COMPLETED
                self.completed_count += 1
            elif status == 'in_progress':
                self.node_statuses[flow_index] = NodeStatus.RUNNING
            elif status == 'failed':
                self.node_statuses[flow_index] = NodeStatus.FAILED
            else:
                self.node_statuses[flow_index] = NodeStatus.PENDING
        
        logger.info(f"Synced node statuses: {self.completed_count}/{self.total_count} complete")
    
    async def resume_from_checkpoint(
        self,
        concepts_path: str,
        inferences_path: str,
        inputs_path: Optional[str],
        db_path: str,
        run_id: str,
        cycle: Optional[int] = None,
        mode: str = "PATCH",
        llm_model: str = "demo",
        base_dir: Optional[str] = None,
        max_cycles: int = 50,
        paradigm_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Resume execution from an existing checkpoint."""
        try:
            from infra._orchest._orchestrator import Orchestrator
        except ImportError as e:
            raise RuntimeError(f"Failed to import Orchestrator: {e}")
        
        await self.stop()
        
        concepts_data, inferences_data, base_dir = await self._load_repos_and_body(
            concepts_path, inferences_path, inputs_path,
            llm_model, base_dir, paradigm_dir
        )
        
        self._add_log("info", "", f"Resuming run {run_id} from checkpoint...")
        
        self.orchestrator = await asyncio.to_thread(
            Orchestrator.load_checkpoint,
            concept_repo=self.concept_repo,
            inference_repo=self.inference_repo,
            db_path=db_path,
            body=self.body,
            max_cycles=max_cycles,
            run_id=run_id,
            cycle=cycle,
            mode=mode
        )
        
        self._sync_node_statuses_from_orchestrator()
        # Also sync ground/input concept statuses (for concepts with initial data)
        self._sync_ground_concept_statuses()
        
        self.status = ExecutionStatus.IDLE
        self._retries = []
        self.cycle_count = self.orchestrator.tracker.cycle_count if hasattr(self.orchestrator, 'tracker') else 0
        
        self._load_config = {
            "concepts_path": concepts_path,
            "inferences_path": inferences_path,
            "inputs_path": inputs_path,
            "llm_model": llm_model,
            "base_dir": base_dir,
            "max_cycles": max_cycles,
            "db_path": db_path,
            "paradigm_dir": paradigm_dir,
        }
        
        await self._emit("execution:loaded", {
            "run_id": self.orchestrator.run_id,
            "total_inferences": self.total_count,
            "completed_count": self.completed_count,
            "node_statuses": {k: v.value for k, v in self.node_statuses.items()},
            "mode": "resume",
        })
        
        self._add_log("info", "", f"Resumed: {self.completed_count}/{self.total_count} already complete")
        
        if self.orchestrator and self.orchestrator.checkpoint_manager:
            self._add_log("debug", "", f"Checkpoint manager initialized for run: {run_id}")
        else:
            self._add_log("warning", "", "Checkpoint manager NOT initialized after resume")

        return {
            "success": True,
            "run_id": run_id,
            "mode": "resume",
            "completed_count": self.completed_count,
            "total_count": self.total_count,
            "message": f"Resumed from checkpoint - {self.completed_count}/{self.total_count} nodes already complete"
        }
    
    async def fork_from_checkpoint(
        self,
        concepts_path: str,
        inferences_path: str,
        inputs_path: Optional[str],
        db_path: str,
        source_run_id: str,
        new_run_id: Optional[str] = None,
        cycle: Optional[int] = None,
        mode: str = "PATCH",
        llm_model: str = "demo",
        base_dir: Optional[str] = None,
        max_cycles: int = 50,
        paradigm_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fork from an existing checkpoint with a new run_id."""
        import uuid as uuid_module
        
        try:
            from infra._orchest._orchestrator import Orchestrator
        except ImportError as e:
            raise RuntimeError(f"Failed to import Orchestrator: {e}")
        
        await self.stop()
        
        if new_run_id is None:
            new_run_id = f"fork-{str(uuid_module.uuid4())[:8]}"
        
        concepts_data, inferences_data, base_dir = await self._load_repos_and_body(
            concepts_path, inferences_path, inputs_path,
            llm_model, base_dir, paradigm_dir
        )
        
        self._add_log("info", "", f"Forking from {source_run_id} to new run {new_run_id}...")
        
        self.orchestrator = await asyncio.to_thread(
            Orchestrator.load_checkpoint,
            concept_repo=self.concept_repo,
            inference_repo=self.inference_repo,
            db_path=db_path,
            body=self.body,
            max_cycles=max_cycles,
            run_id=source_run_id,
            new_run_id=new_run_id,
            cycle=cycle,
            mode=mode
        )
        
        self._sync_node_statuses_from_orchestrator()
        # Also sync ground/input concept statuses (for concepts with initial data)
        self._sync_ground_concept_statuses()
        
        self.status = ExecutionStatus.IDLE
        self._retries = []
        self.cycle_count = 0
        
        self._load_config = {
            "concepts_path": concepts_path,
            "inferences_path": inferences_path,
            "inputs_path": inputs_path,
            "llm_model": llm_model,
            "base_dir": base_dir,
            "max_cycles": max_cycles,
            "db_path": db_path,
            "paradigm_dir": paradigm_dir,
        }
        
        await self._emit("execution:loaded", {
            "run_id": new_run_id,
            "total_inferences": self.total_count,
            "completed_count": self.completed_count,
            "node_statuses": {k: v.value for k, v in self.node_statuses.items()},
            "mode": "fork",
            "forked_from": source_run_id,
        })
        
        self._add_log("info", "", f"Forked: {self.completed_count}/{self.total_count} nodes carried over")
        
        if self.orchestrator and self.orchestrator.checkpoint_manager:
            self._add_log("debug", "", f"Checkpoint manager initialized for run: {new_run_id}")
        else:
            self._add_log("warning", "", "Checkpoint manager NOT initialized after fork")
        
        return {
            "success": True,
            "run_id": new_run_id,
            "forked_from": source_run_id,
            "mode": "fork",
            "completed_count": self.completed_count,
            "total_count": self.total_count,
            "message": f"Forked from {source_run_id} - {self.completed_count}/{self.total_count} nodes carried over"
        }

