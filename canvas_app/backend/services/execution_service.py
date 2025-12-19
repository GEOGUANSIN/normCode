"""Execution control service with Orchestrator integration for Phase 2."""
import asyncio
import logging
import sys
import time
import os
import json
import importlib.util
from pathlib import Path
from typing import Optional, Dict, Any, Set, List
from dataclasses import dataclass, field

from schemas.execution_schemas import ExecutionStatus, NodeStatus
from core.events import event_emitter

# Add project root to path for infra imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class CustomParadigmTool:
    """
    Custom paradigm tool that loads paradigms from a specified directory
    instead of the default infra/_agent/_models/_paradigms location.
    
    This allows projects to define their own paradigms locally.
    Based on the pattern from direct_infra_experiment executors.
    """
    
    def __init__(self, paradigm_dir: Path):
        self.paradigm_dir = Path(paradigm_dir)
        self._Paradigm = None
        
        # Try to load the Paradigm class from the local paradigm directory
        local_paradigm_py = self.paradigm_dir / "_paradigm.py"
        if local_paradigm_py.exists():
            # Load from local _paradigm.py (allows full customization)
            spec = importlib.util.spec_from_file_location("_paradigm", local_paradigm_py)
            paradigm_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(paradigm_module)
            self._Paradigm = paradigm_module.Paradigm
            # Override PARADIGMS_DIR in the module to point to our custom dir
            paradigm_module.PARADIGMS_DIR = self.paradigm_dir
            logger.info(f"Loaded custom Paradigm class from {local_paradigm_py}")
        else:
            # Fallback: Import from infra but override the directory
            try:
                from infra._agent._models._paradigms._paradigm import Paradigm
                # Create a wrapper that loads from custom directory
                class LocalParadigm:
                    """Wrapper to load paradigms from custom directory."""
                    @classmethod
                    def load(cls, paradigm_name: str):
                        paradigm_file = paradigm_dir / f"{paradigm_name}.json"
                        if not paradigm_file.exists():
                            raise FileNotFoundError(
                                f"Paradigm '{paradigm_name}' not found at {paradigm_file}"
                            )
                        with open(paradigm_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        # Create Paradigm instance with loaded data
                        paradigm = Paradigm.__new__(Paradigm)
                        paradigm.name = paradigm_name
                        paradigm.data = data
                        paradigm.metadata = data.get('metadata', {})
                        paradigm.env_spec = data.get('env_spec', {})
                        paradigm.sequence_spec = data.get('sequence_spec', {})
                        return paradigm
                self._Paradigm = LocalParadigm
                logger.info(f"Using infra Paradigm with custom directory: {paradigm_dir}")
            except ImportError as e:
                logger.error(f"Failed to import Paradigm from infra: {e}")
                raise
    
    def load(self, paradigm_name: str):
        """Load a paradigm from the custom directory."""
        return self._Paradigm.load(paradigm_name)
    
    def list_manifest(self) -> str:
        """List all available paradigms in the custom directory."""
        manifest = []
        for filename in os.listdir(self.paradigm_dir):
            if filename.endswith(".json"):
                name = filename[:-5]  # Remove .json extension
                try:
                    with open(self.paradigm_dir / filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata = data.get('metadata', {})
                        desc = metadata.get('description', 'No description provided.')
                        manifest.append(
                            f"<paradigm name=\"{name}\">\n"
                            f"    <description>{desc}</description>\n"
                            f"</paradigm>"
                        )
                except Exception as e:
                    manifest.append(f"<error paradigm=\"{name}\">{str(e)}</error>")
        return "\n\n".join(manifest)


@dataclass
class ExecutionController:
    """Controls orchestrator execution with debugging support.
    
    This controller provides inference-by-inference execution control,
    allowing for stepping, breakpoints, and real-time status updates.
    """
    
    orchestrator: Optional[Any] = None  # Orchestrator instance
    concept_repo: Optional[Any] = None
    inference_repo: Optional[Any] = None
    body: Optional[Any] = None
    
    status: ExecutionStatus = ExecutionStatus.IDLE
    breakpoints: Set[str] = field(default_factory=set)
    current_inference: Optional[str] = None
    node_statuses: Dict[str, NodeStatus] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    # Execution tracking
    completed_count: int = 0
    total_count: int = 0
    cycle_count: int = 0
    
    _pause_event: asyncio.Event = field(default_factory=asyncio.Event)
    _stop_requested: bool = False
    _run_task: Optional[asyncio.Task] = None
    _retries: List[Any] = field(default_factory=list)  # WaitlistItem retries
    
    def __post_init__(self):
        self._pause_event.set()  # Not paused by default
    
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
        """Load repositories and create orchestrator.
        
        Args:
            concepts_path: Path to concepts.json file
            inferences_path: Path to inferences.json file
            inputs_path: Optional path to inputs.json file
            llm_model: LLM model name (e.g., "demo", "qwen-plus", "gpt-4o")
            base_dir: Base directory for file operations
            max_cycles: Maximum execution cycles (default: 50)
            db_path: Path to checkpoint database (default: base_dir/orchestration.db)
            paradigm_dir: Custom paradigm directory (e.g., provision/paradigm)
        """
        import json as json_module
        
        try:
            from infra._orchest._repo import ConceptRepo, InferenceRepo
            from infra._agent._body import Body
            from infra._orchest._orchestrator import Orchestrator
        except ImportError as e:
            logger.error(f"Failed to import infra modules: {e}")
            raise RuntimeError(f"Failed to import infra modules: {e}")
        
        # Load repository files
        with open(concepts_path, 'r', encoding='utf-8') as f:
            concepts_data = json_module.load(f)
        with open(inferences_path, 'r', encoding='utf-8') as f:
            inferences_data = json_module.load(f)
        
        # Create repositories
        self.concept_repo = ConceptRepo.from_json_list(concepts_data)
        self.inference_repo = InferenceRepo.from_json_list(inferences_data, self.concept_repo)
        
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
        
        # Create body with LLM
        if base_dir is None:
            base_dir = str(Path(concepts_path).parent)
        
        # Create custom paradigm tool if paradigm_dir is specified
        custom_paradigm_tool = None
        if paradigm_dir:
            paradigm_path = Path(paradigm_dir)
            # If relative path, resolve relative to base_dir
            if not paradigm_path.is_absolute():
                paradigm_path = Path(base_dir) / paradigm_dir
            
            if paradigm_path.exists() and paradigm_path.is_dir():
                custom_paradigm_tool = CustomParadigmTool(paradigm_path)
                logger.info(f"Using custom paradigm directory: {paradigm_path}")
                self._add_log("info", "", f"Using custom paradigms from: {paradigm_path}")
            else:
                logger.warning(f"Paradigm directory not found: {paradigm_path}")
                self._add_log("warning", "", f"Paradigm directory not found: {paradigm_path}")
        
        # Create Body with optional custom paradigm tool
        self.body = Body(
            llm_name=llm_model, 
            base_dir=base_dir,
            paradigm_tool=custom_paradigm_tool
        )
        
        # Determine database path for checkpointing
        if db_path is None:
            db_path = str(Path(base_dir) / "orchestration.db")
        
        logger.info(f"Creating orchestrator with max_cycles={max_cycles}, db_path={db_path}")
        
        # Create orchestrator with full configuration
        self.orchestrator = await asyncio.to_thread(
            Orchestrator,
            concept_repo=self.concept_repo,
            inference_repo=self.inference_repo,
            body=self.body,
            max_cycles=max_cycles,
            db_path=db_path
        )
        
        # Initialize node statuses from inference repository
        self.node_statuses = {}
        self.total_count = 0
        self.completed_count = 0
        
        for inf in inferences_data:
            flow_index = inf.get('flow_info', {}).get('flow_index', '')
            if flow_index:
                self.node_statuses[flow_index] = NodeStatus.PENDING
                self.total_count += 1
        
        # Also mark ground concepts as complete
        for concept in concepts_data:
            if concept.get('is_ground_concept', False):
                concept_name = concept.get('concept_name', '')
                # Ground concepts are already complete
                pass
        
        self.status = ExecutionStatus.IDLE
        self._retries = []
        self.cycle_count = 0
        self.logs = []
        
        await self._emit("execution:loaded", {
            "run_id": getattr(self.orchestrator, 'run_id', 'unknown'),
            "total_inferences": self.total_count,
        })
        
        self._add_log("info", "", f"Loaded {len(concepts_data)} concepts and {self.total_count} inferences")
        self._add_log("info", "", f"Config: model={llm_model}, max_cycles={max_cycles}, db={db_path}")
        
        return {
            "run_id": getattr(self.orchestrator, 'run_id', 'unknown'),
            "total_inferences": self.total_count,
            "concepts_count": len(concepts_data),
            "config": {
                "llm_model": llm_model,
                "max_cycles": max_cycles,
                "db_path": db_path,
                "base_dir": base_dir,
            }
        }
    
    async def start(self):
        """Start or resume execution."""
        if self.orchestrator is None:
            raise RuntimeError("No repositories loaded. Call load_repositories first.")
        
        if self.status == ExecutionStatus.PAUSED:
            await self.resume()
            return
        
        self.status = ExecutionStatus.RUNNING
        self._stop_requested = False
        self._pause_event.set()
        
        await self._emit("execution:started", {})
        self._add_log("info", "", "Execution started")
        
        # Start execution in background task
        self._run_task = asyncio.create_task(self._run_loop())
    
    async def pause(self):
        """Pause execution after current inference."""
        self.status = ExecutionStatus.PAUSED
        self._pause_event.clear()
        await self._emit("execution:paused", {"inference": self.current_inference})
        self._add_log("info", "", f"Execution paused at {self.current_inference or 'start'}")
    
    async def resume(self):
        """Resume from paused state."""
        self.status = ExecutionStatus.RUNNING
        self._pause_event.set()
        await self._emit("execution:resumed", {})
        self._add_log("info", "", "Execution resumed")
    
    async def step(self):
        """Execute single inference then pause."""
        if self.orchestrator is None:
            raise RuntimeError("No repositories loaded.")
        
        self.status = ExecutionStatus.STEPPING
        self._pause_event.set()
        
        if self._run_task is None or self._run_task.done():
            self._run_task = asyncio.create_task(self._run_loop())
        
        await self._emit("execution:stepping", {})
        self._add_log("info", "", "Stepping to next inference")
    
    async def stop(self):
        """Stop execution."""
        self._stop_requested = True
        self._pause_event.set()  # Unblock if paused
        
        if self._run_task and not self._run_task.done():
            self._run_task.cancel()
            try:
                await self._run_task
            except asyncio.CancelledError:
                pass
        
        self.status = ExecutionStatus.IDLE
        await self._emit("execution:stopped", {})
        self._add_log("info", "", "Execution stopped")
    
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
        }
    
    def get_logs(self, limit: int = 100, flow_index: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get execution logs, optionally filtered by flow_index."""
        logs = self.logs
        if flow_index:
            logs = [l for l in logs if l.get('flow_index') == flow_index or l.get('flow_index') == '']
        return logs[-limit:]
    
    def get_reference_data(self, concept_name: str) -> Optional[Dict[str, Any]]:
        """Get reference data for a concept from the concept repository.
        
        Returns the current reference data (tensor) for a concept, including:
        - data: The tensor data (nested lists)
        - axes: The axis names
        - shape: The tensor shape
        
        Returns None if concept not found or has no reference data.
        """
        if self.concept_repo is None:
            return None
        
        try:
            # Get the concept from the repository
            concept = self.concept_repo.get(concept_name)
            if concept is None:
                return None
            
            # Check if concept has a reference
            if not hasattr(concept, 'reference') or concept.reference is None:
                return None
            
            ref = concept.reference
            
            # Extract reference data
            result = {
                "concept_name": concept_name,
                "has_reference": True,
            }
            
            # Get tensor data
            if hasattr(ref, 'tensor'):
                result["data"] = ref.tensor
            elif hasattr(ref, 'data'):
                result["data"] = ref.data
            else:
                result["data"] = None
            
            # Get axis names
            if hasattr(ref, 'axes') and ref.axes:
                result["axes"] = [axis.name if hasattr(axis, 'name') else str(axis) for axis in ref.axes]
            else:
                result["axes"] = []
            
            # Calculate shape from tensor
            if result["data"] is not None:
                shape = []
                current = result["data"]
                while isinstance(current, list):
                    shape.append(len(current))
                    if len(current) > 0:
                        current = current[0]
                    else:
                        break
                result["shape"] = shape
            else:
                result["shape"] = []
            
            return result
            
        except Exception as e:
            logger.warning(f"Error getting reference for {concept_name}: {e}")
            return None
    
    def get_all_reference_data(self) -> Dict[str, Dict[str, Any]]:
        """Get reference data for all concepts that have references.
        
        Returns a dict mapping concept_name -> reference_data for concepts
        that have been computed or are ground concepts.
        """
        if self.concept_repo is None:
            return {}
        
        result = {}
        try:
            # Iterate through all concepts in the repo
            for concept_name in self.concept_repo.keys():
                ref_data = self.get_reference_data(concept_name)
                if ref_data and ref_data.get("has_reference"):
                    result[concept_name] = ref_data
        except Exception as e:
            logger.warning(f"Error getting all references: {e}")
        
        return result
    
    def _add_log(self, level: str, flow_index: str, message: str):
        """Add a log entry."""
        log_entry = {
            "level": level,
            "flow_index": flow_index,
            "message": message,
            "timestamp": time.time()
        }
        self.logs.append(log_entry)
        # Also emit as WebSocket event
        asyncio.create_task(self._emit("log:entry", log_entry))
    
    async def _run_loop(self):
        """Main execution loop with inference-by-inference control.
        
        This loop processes inferences one at a time, allowing for:
        - Breakpoints before execution
        - Stepping (execute one then pause)
        - Pause/resume at any point
        - Real-time status updates via WebSocket
        """
        try:
            while self.status in (ExecutionStatus.RUNNING, ExecutionStatus.STEPPING):
                if self._stop_requested:
                    break
                
                # Check if paused
                if not self._pause_event.is_set():
                    await self._pause_event.wait()
                    if self._stop_requested:
                        break
                
                # Check if there are more inferences to process
                has_pending = await asyncio.to_thread(
                    lambda: self.orchestrator.blackboard.get_all_pending_or_in_progress_items()
                )
                
                if not has_pending:
                    # All done!
                    break
                
                # Check max cycles
                if self.cycle_count >= self.orchestrator.max_cycles:
                    self._add_log("error", "", f"Maximum cycles ({self.orchestrator.max_cycles}) reached")
                    break
                
                # Run one cycle
                self.cycle_count += 1
                self._add_log("info", "", f"Starting cycle {self.cycle_count}")
                
                # Process cycle with event emission
                progress_made = await self._run_cycle_with_events()
                
                if not progress_made:
                    self._add_log("warning", "", "No progress made in cycle - possible deadlock")
                    break
                
                # If stepping, pause after this cycle completes
                if self.status == ExecutionStatus.STEPPING:
                    self.status = ExecutionStatus.PAUSED
                    self._pause_event.clear()
                    await self._emit("execution:paused", {"inference": self.current_inference})
                    break
            
            if not self._stop_requested and self.status != ExecutionStatus.PAUSED:
                self.status = ExecutionStatus.COMPLETED
                await self._emit("execution:completed", {
                    "completed_count": self.completed_count,
                    "total_count": self.total_count
                })
                self._add_log("info", "", "Execution completed")
            
        except asyncio.CancelledError:
            logger.info("Execution cancelled")
        except Exception as e:
            self.status = ExecutionStatus.FAILED
            await self._emit("execution:error", {"error": str(e)})
            self._add_log("error", "", f"Execution failed: {str(e)}")
            logger.exception("Execution failed")
    
    async def _run_cycle_with_events(self) -> bool:
        """Process one cycle with event emission for each inference.
        
        Returns True if progress was made (at least one inference executed).
        """
        cycle_executions = 0
        next_retries = []
        
        # Get items to process for this cycle
        retried_items_set = set(self._retries)
        items_to_process = self._retries + [
            item for item in self.orchestrator.waitlist.items 
            if item not in retried_items_set
        ]
        
        for item in items_to_process:
            if self._stop_requested:
                break
            
            # Check if paused
            if not self._pause_event.is_set():
                await self._pause_event.wait()
                if self._stop_requested:
                    break
            
            flow_index = item.inference_entry.flow_info['flow_index']
            
            # Check if this item is pending and ready
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
            
            # Check for breakpoint BEFORE execution
            if flow_index in self.breakpoints:
                self.status = ExecutionStatus.PAUSED
                self._pause_event.clear()
                self.current_inference = flow_index
                await self._emit("breakpoint:hit", {"flow_index": flow_index})
                self._add_log("info", flow_index, "Breakpoint hit - execution paused")
                await self._pause_event.wait()
                if self._stop_requested:
                    break
            
            # Execute this inference with events
            cycle_executions += 1
            self.current_inference = flow_index
            
            # Emit inference started
            self.node_statuses[flow_index] = NodeStatus.RUNNING
            await self._emit("inference:started", {
                "flow_index": flow_index,
                "concept_name": item.inference_entry.concept_to_infer.concept_name,
                "sequence": item.inference_entry.inference_sequence
            })
            self._add_log("info", flow_index, f"Executing: {item.inference_entry.concept_to_infer.concept_name}")
            
            try:
                # Execute the inference
                start_time = time.time()
                new_status = await asyncio.to_thread(
                    self.orchestrator._execute_item,
                    item
                )
                duration = time.time() - start_time
                
                if new_status == 'completed':
                    self.node_statuses[flow_index] = NodeStatus.COMPLETED
                    self.completed_count += 1
                    await self._emit("inference:completed", {
                        "flow_index": flow_index,
                        "duration": duration
                    })
                    self._add_log("info", flow_index, f"Completed in {duration:.2f}s")
                else:
                    # Retry needed
                    self.node_statuses[flow_index] = NodeStatus.PENDING
                    next_retries.append(item)
                    await self._emit("inference:retry", {
                        "flow_index": flow_index,
                        "status": new_status
                    })
                    self._add_log("warning", flow_index, f"Needs retry: {new_status}")
                
                # Emit progress update
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
            
            # If stepping mode, pause after first inference
            if self.status == ExecutionStatus.STEPPING:
                self.status = ExecutionStatus.PAUSED
                self._pause_event.clear()
                await self._emit("execution:paused", {"inference": flow_index})
                break
        
        # Update retries for next cycle
        self._retries = next_retries
        
        self._add_log("info", "", f"Cycle {self.cycle_count}: {cycle_executions} executions, {self.completed_count}/{self.total_count} complete")
        
        return cycle_executions > 0
    
    async def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit event through event emitter."""
        await event_emitter.emit(event_type, data)


# Global execution controller instance
execution_controller = ExecutionController()
