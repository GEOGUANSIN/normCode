"""Execution control service with Orchestrator integration for Phase 2."""
import asyncio
import logging
import sys
import time
import os
import json
import re
import importlib.util
from pathlib import Path
from typing import Optional, Dict, Any, Set, List
from dataclasses import dataclass, field

from schemas.execution_schemas import (
    ExecutionStatus, NodeStatus, 
    SEQUENCE_STEPS, STEP_FULL_NAMES
)
from core.events import event_emitter
from services.agent_service import agent_registry, agent_mapping, ToolCallEvent
from tools.user_input_tool import CanvasUserInputTool
from tools.chat_tool import CanvasChatTool
from tools.canvas_tool import CanvasDisplayTool

# Add project root to path for infra imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class OrchestratorLogHandler(logging.Handler):
    """
    Custom logging handler that captures logs from orchestrator/infra modules
    and forwards them to the ExecutionController's log system.
    
    This enables rich orchestrator logs (step execution, tensor data, etc.)
    to appear in the frontend's Log Panel.
    
    Enhanced to parse structured step events from sequence logs.
    """
    
    # Regex patterns for parsing sequence logs
    SEQUENCE_START_PATTERN = re.compile(r'=+EXECUTING\s+(\w+)\s+SEQUENCE=+', re.IGNORECASE)
    SEQUENCE_END_PATTERN = re.compile(r'=+(\w+)\s+SEQUENCE\s+COMPLETED=+', re.IGNORECASE)
    STEP_PATTERN = re.compile(r'---Step\s+(\d+):\s+([^(]+)\s*\(([^)]+)\)---', re.IGNORECASE)
    STEP_SIMPLE_PATTERN = re.compile(r'---Step\s+(\d+):\s+(\w+)---', re.IGNORECASE)
    
    def __init__(self, execution_controller: 'ExecutionController', verbose: bool = False):
        super().__init__()
        self.execution_controller = execution_controller
        self.verbose = verbose
        # Set formatter to capture just the message
        self.setFormatter(logging.Formatter('%(message)s'))
        
        # Track current sequence state for flow_index association
        self._current_sequence_type: Optional[str] = None
        self._current_step_index: int = 0
    
    def emit(self, record: logging.LogRecord):
        """Forward log record to execution controller with structured event parsing."""
        try:
            # Extract flow_index from the log message if present
            flow_index = self.execution_controller.current_inference or ''
            if hasattr(record, 'flow_index'):
                flow_index = record.flow_index
            
            # Format the message
            message = self.format(record)
            
            # Always parse for structured events (step/sequence progress)
            # This allows UI to show step pipeline even in non-verbose mode
            self._parse_structured_events(message, flow_index)
            
            # Only emit log messages to frontend if verbose mode is enabled
            # In non-verbose mode, we only care about structured events (parsed above)
            if not self.verbose:
                return
            
            # Map Python log levels to our log levels
            level_map = {
                logging.DEBUG: 'debug',
                logging.INFO: 'info',
                logging.WARNING: 'warning',
                logging.ERROR: 'error',
                logging.CRITICAL: 'error',
            }
            level = level_map.get(record.levelno, 'info')
            
            # Format the message with logger name for context
            logger_short = record.name.replace('infra.', '')
            
            # Add source prefix for clarity
            if record.name.startswith('infra.'):
                message = f"[{logger_short}] {message}"
            
            # Add to execution logs (this will also emit WebSocket event)
            self.execution_controller._add_log(level, flow_index, message)
            
        except Exception:
            # Don't let logging errors break execution
            self.handleError(record)
    
    def _parse_structured_events(self, message: str, flow_index: str):
        """Parse log messages for structured step/sequence events."""
        
        # Check for sequence start
        match = self.SEQUENCE_START_PATTERN.search(message)
        if match:
            sequence_type = match.group(1).lower()
            self._current_sequence_type = sequence_type
            self._current_step_index = 0
            
            # Get steps for this sequence type
            steps = SEQUENCE_STEPS.get(sequence_type, [])
            
            # Emit sequence started event (thread-safe)
            self.execution_controller._emit_threadsafe("sequence:started", {
                "flow_index": flow_index,
                "sequence_type": sequence_type,
                "total_steps": len(steps),
                "steps": steps,
            })
            return
        
        # Check for sequence end
        match = self.SEQUENCE_END_PATTERN.search(message)
        if match:
            sequence_type = match.group(1).lower()
            
            # Emit sequence completed event (thread-safe)
            self.execution_controller._emit_threadsafe("sequence:completed", {
                "flow_index": flow_index,
                "sequence_type": sequence_type,
            })
            
            self._current_sequence_type = None
            self._current_step_index = 0
            return
        
        # Check for step (with full name in parentheses)
        match = self.STEP_PATTERN.search(message)
        if match:
            step_num = int(match.group(1))
            step_full_name = match.group(2).strip()
            step_abbrev = match.group(3).strip()
            
            self._emit_step_event(flow_index, step_abbrev, step_num)
            return
        
        # Check for simple step format (just abbreviation)
        match = self.STEP_SIMPLE_PATTERN.search(message)
        if match:
            step_num = int(match.group(1))
            step_abbrev = match.group(2).strip()
            
            self._emit_step_event(flow_index, step_abbrev, step_num)
            return
    
    def _emit_step_event(self, flow_index: str, step_abbrev: str, step_num: int):
        """Emit a step started event. Thread-safe."""
        self._current_step_index = step_num
        
        # Get total steps if we know the sequence type
        total_steps = 0
        steps = []
        if self._current_sequence_type:
            steps = SEQUENCE_STEPS.get(self._current_sequence_type, [])
            total_steps = len(steps)
        
        # Get paradigm from current inference if available
        paradigm = None
        if self.execution_controller.current_inference:
            paradigm = self.execution_controller._get_current_paradigm()
        
        # Emit step started event (thread-safe)
        self.execution_controller._emit_threadsafe("step:started", {
            "flow_index": flow_index,
            "step_name": step_abbrev,
            "step_full_name": STEP_FULL_NAMES.get(step_abbrev, step_abbrev),
            "step_index": step_num - 1,  # 0-based
            "total_steps": total_steps,
            "sequence_type": self._current_sequence_type,
            "paradigm": paradigm,
            "steps": steps,
        })


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
            LocalParadigmClass = paradigm_module.Paradigm
            # Override PARADIGMS_DIR in the module to point to our custom dir
            paradigm_module.PARADIGMS_DIR = self.paradigm_dir
            logger.info(f"Loaded custom Paradigm class from {local_paradigm_py}")
            
            # Wrap with fallback to default paradigms
            try:
                from infra._agent._models._paradigms._paradigm import Paradigm as DefaultParadigm, PARADIGMS_DIR
                custom_dir = self.paradigm_dir
                
                class WrappedLocalParadigm:
                    """Wrapper that tries local paradigm first, then falls back to default."""
                    @classmethod
                    def load(cls, paradigm_name: str):
                        # Try local paradigm directory first
                        paradigm_file = custom_dir / f"{paradigm_name}.json"
                        if paradigm_file.exists():
                            logger.debug(f"Loading paradigm '{paradigm_name}' from custom directory")
                            return LocalParadigmClass.load(paradigm_name)
                        
                        # Fall back to default paradigms
                        default_paradigm_file = PARADIGMS_DIR / f"{paradigm_name}.json"
                        if default_paradigm_file.exists():
                            logger.info(f"Paradigm '{paradigm_name}' not in custom dir, loading from default")
                            return DefaultParadigm.load(paradigm_name)
                        
                        # Not found in either location
                        raise FileNotFoundError(
                            f"Paradigm '{paradigm_name}' not found in custom ({custom_dir}) or default ({PARADIGMS_DIR})"
                        )
                
                self._Paradigm = WrappedLocalParadigm
                logger.info(f"Wrapped local Paradigm with fallback to default paradigms")
            except ImportError as e:
                # If infra not available, just use local paradigm without fallback
                logger.warning(f"Could not import default paradigms for fallback: {e}")
                self._Paradigm = LocalParadigmClass
        else:
            # Fallback: Import from infra but check custom directory first
            try:
                from infra._agent._models._paradigms._paradigm import (
                    Paradigm, PARADIGMS_DIR, 
                    _paradigm_object_hook, _build_env_spec, _build_sequence_spec
                )
                # Create a wrapper that loads from custom directory first, then falls back to default
                class LocalParadigm:
                    """Wrapper to load paradigms from custom directory, falling back to default."""
                    @classmethod
                    def load(cls, paradigm_name: str):
                        # Try custom directory first
                        paradigm_file = paradigm_dir / f"{paradigm_name}.json"
                        if paradigm_file.exists():
                            with open(paradigm_file, 'r', encoding='utf-8') as f:
                                # Use the proper object hook to handle MetaValue etc
                                raw_spec = json.load(f, object_hook=_paradigm_object_hook)
                            
                            # Properly reconstruct spec objects (not raw dicts!)
                            env_spec_data = raw_spec.get('env_spec', {})
                            sequence_spec_data = raw_spec.get('sequence_spec', {})
                            metadata_data = raw_spec.get('metadata', {})
                            
                            env_spec = _build_env_spec(env_spec_data)
                            sequence_spec = _build_sequence_spec(sequence_spec_data, env_spec)
                            
                            # Create Paradigm instance properly
                            paradigm = Paradigm(env_spec, sequence_spec, metadata_data)
                            logger.debug(f"Loaded paradigm '{paradigm_name}' from custom directory")
                            return paradigm
                        
                        # Fall back to default paradigms directory
                        default_paradigm_file = PARADIGMS_DIR / f"{paradigm_name}.json"
                        if default_paradigm_file.exists():
                            logger.debug(f"Paradigm '{paradigm_name}' not in custom dir, loading from default")
                            return Paradigm.load(paradigm_name)
                        
                        # Not found in either location
                        raise FileNotFoundError(
                            f"Paradigm '{paradigm_name}' not found in custom ({paradigm_dir}) or default ({PARADIGMS_DIR})"
                        )
                self._Paradigm = LocalParadigm
                logger.info(f"Using infra Paradigm with custom directory fallback: {paradigm_dir}")
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
    
    Each ExecutionController is associated with a specific project_id,
    enabling multiple projects to execute simultaneously.
    """
    
    # Project association
    project_id: Optional[str] = None  # ID of the project this controller manages
    
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
    
    # Step tracking for current inference
    current_step: Optional[str] = None
    current_sequence_type: Optional[str] = None
    step_progress: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # flow_index -> step progress
    
    # Verbose logging mode (captures DEBUG level logs)
    verbose_logging: bool = False
    
    _pause_event: asyncio.Event = field(default_factory=asyncio.Event)
    _stop_requested: bool = False
    _run_task: Optional[asyncio.Task] = None
    _retries: List[Any] = field(default_factory=list)  # WaitlistItem retries
    _run_to_target: Optional[str] = None  # Target flow_index for "run to" mode
    _log_handler: Optional[OrchestratorLogHandler] = None  # Handler for capturing infra logs
    _attached_loggers: List[str] = field(default_factory=list)  # Track which loggers we attached to
    
    # Cache for inference metadata
    _inference_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Store load configuration for restart functionality
    _load_config: Optional[Dict[str, Any]] = None
    
    # User input tool for human-in-the-loop interactions
    user_input_tool: Optional[CanvasUserInputTool] = None
    
    def __post_init__(self):
        self._pause_event.set()  # Not paused by default
        self._attached_loggers = []
        self._inference_metadata = {}
        self._main_loop: Optional[asyncio.AbstractEventLoop] = None  # Store main event loop for thread-safe calls
        self._load_config = None  # Will be set in load_repositories
        
        # Register tool call callback for WebSocket emission
        self._setup_agent_tool_monitoring()
    
    def _setup_agent_tool_monitoring(self):
        """Set up tool call monitoring to emit events via WebSocket."""
        def emit_tool_event(event: ToolCallEvent):
            """Emit tool call event through WebSocket."""
            event_type = f"tool:call_{event.status}"
            self._emit_threadsafe(event_type, event.to_dict())
        
        # Register callback with agent registry
        agent_registry.register_tool_callback("execution_controller", emit_tool_event)
        logger.info("Registered tool call monitoring for WebSocket events")
    
    def _wrap_body_with_monitoring(self, body: Any) -> None:
        """
        Wrap a Body's tools with MonitoredToolProxy for real-time monitoring.
        
        This enables the Agent Panel to show tool calls during execution.
        """
        from services.agent_service import MonitoredToolProxy
        
        def get_flow_index():
            return self.current_inference or ""
        
        def emit_tool_event(event: ToolCallEvent):
            """Emit tool call event through WebSocket."""
            event_type = f"tool:call_{event.status}"
            self._emit_threadsafe(event_type, event.to_dict())
            # Also add to agent_registry history for persistence
            agent_registry.tool_call_history.append(event)
            if len(agent_registry.tool_call_history) > agent_registry.max_history:
                agent_registry.tool_call_history = agent_registry.tool_call_history[-agent_registry.max_history:]
        
        # Wrap the main tools used during execution
        if hasattr(body, 'llm') and body.llm is not None:
            body.llm = MonitoredToolProxy(
                "default", "llm", body.llm,
                emit_tool_event, get_flow_index
            )
        
        if hasattr(body, 'file_system') and body.file_system is not None:
            body.file_system = MonitoredToolProxy(
                "default", "file_system", body.file_system,
                emit_tool_event, get_flow_index
            )
        
        if hasattr(body, 'python_interpreter') and body.python_interpreter is not None:
            body.python_interpreter = MonitoredToolProxy(
                "default", "python_interpreter", body.python_interpreter,
                emit_tool_event, get_flow_index
            )
        
        if hasattr(body, 'prompt_tool') and body.prompt_tool is not None:
            body.prompt_tool = MonitoredToolProxy(
                "default", "prompt", body.prompt_tool,
                emit_tool_event, get_flow_index
            )
        
        if hasattr(body, 'user_input') and body.user_input is not None:
            body.user_input = MonitoredToolProxy(
                "default", "user_input", body.user_input,
                emit_tool_event, get_flow_index
            )

        if hasattr(body, 'paradigm_tool') and body.paradigm_tool is not None:
            body.paradigm_tool = MonitoredToolProxy(
                "default", "paradigm", body.paradigm_tool,
                emit_tool_event, get_flow_index
            )
        
        if hasattr(body, 'chat') and body.chat is not None:
            body.chat = MonitoredToolProxy(
                "default", "chat", body.chat,
                emit_tool_event, get_flow_index
            )
        
        if hasattr(body, 'canvas') and body.canvas is not None:
            body.canvas = MonitoredToolProxy(
                "default", "canvas", body.canvas,
                emit_tool_event, get_flow_index
            )
        
        # Note: formatter_tool and composition_tool are internal tools used by paradigm
        # execution. They don't benefit from monitoring as they are low-level utilities.
        
        logger.info("Wrapped body tools with monitoring proxies")
    
    def _attach_infra_log_handlers(self):
        """Attach our log handler to infra loggers to capture orchestrator logs."""
        if self._log_handler is not None:
            return  # Already attached
        
        self._log_handler = OrchestratorLogHandler(self, verbose=self.verbose_logging)
        # Set level based on verbose mode
        log_level = logging.DEBUG if self.verbose_logging else logging.INFO
        self._log_handler.setLevel(log_level)
        
        # List of infra logger names to capture
        infra_loggers = [
            'infra',
            'infra._orchest',
            'infra._orchest._orchestrator',
            'infra._core',
            'infra._core._inference',
            'infra._agent',
            'infra._agent._sequences',
            'infra._agent._sequences.imperative',
            'infra._agent._sequences.grouping',
            'infra._agent._sequences.assigning',
            'infra._loggers',
            'infra._loggers.utils',
        ]
        
        self._attached_loggers = []
        for logger_name in infra_loggers:
            try:
                infra_logger = logging.getLogger(logger_name)
                infra_logger.addHandler(self._log_handler)
                self._attached_loggers.append(logger_name)
            except Exception as e:
                logger.warning(f"Failed to attach log handler to {logger_name}: {e}")
        
        logger.info(f"Attached log handler to {len(self._attached_loggers)} infra loggers")
    
    def _detach_infra_log_handlers(self):
        """Detach our log handler from infra loggers."""
        if self._log_handler is None:
            return
        
        for logger_name in self._attached_loggers:
            try:
                infra_logger = logging.getLogger(logger_name)
                infra_logger.removeHandler(self._log_handler)
            except Exception:
                pass
        
        self._attached_loggers = []
        self._log_handler = None
        logger.info("Detached log handlers from infra loggers")
    
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
            from infra._core import set_dev_mode
            # Enable dev mode to surface exceptions in element_action/cross_action
            set_dev_mode(True)
            logger.info("Enabled infra dev mode for debugging")
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
        
        # Create and inject the canvas user input tool for human-in-the-loop interactions
        self.user_input_tool = CanvasUserInputTool(emit_callback=self._emit_sync)
        self.body.user_input = self.user_input_tool
        logger.info("Injected CanvasUserInputTool for human-in-the-loop interactions")
        
        # Create and inject chat tool for compiler chat interface
        # Create chat tool with source="execution" so frontend uses /api/execution/chat-input/
        self.chat_tool = CanvasChatTool(emit_callback=self._emit_sync, source="execution")
        self.body.chat = self.chat_tool
        logger.info("Injected CanvasChatTool for chat-driven execution (source=execution)")
        
        # Create and inject canvas display tool for canvas commands
        self.canvas_tool = CanvasDisplayTool(emit_callback=self._emit_sync)
        self.body.canvas = self.canvas_tool
        logger.info("Injected CanvasDisplayTool for canvas operations")
        
        # Note: formatter_tool and composition_tool are already created by Body
        # We don't overwrite them to preserve the perception_router injection
        
        # Wrap body tools with monitoring proxies for real-time tool call tracking
        self._wrap_body_with_monitoring(self.body)
        
        # Determine database path for checkpointing
        if db_path is None:
            db_path = str(Path(base_dir) / "orchestration.db")
        else:
            # If db_path is relative, resolve it relative to base_dir
            db_path_obj = Path(db_path)
            if not db_path_obj.is_absolute():
                db_path = str(Path(base_dir) / db_path)

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
        
        # Store configuration for restart functionality
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
        })
        
        self._add_log("info", "", f"Loaded {len(concepts_data)} concepts and {self.total_count} inferences")
        self._add_log("info", "", f"Config: model={llm_model}, max_cycles={max_cycles}, db={db_path}")
        
        # Log checkpoint_manager status for debugging
        if self.orchestrator and self.orchestrator.checkpoint_manager:
            self._add_log("info", "", f"Checkpoint manager initialized for run: {self.orchestrator.run_id}")
        else:
            self._add_log("warning", "", "Checkpoint manager NOT initialized - checkpoints will NOT be saved!")
        
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

        # Capture the main event loop for thread-safe event emission
        self._main_loop = asyncio.get_running_loop()

        # Attach log handlers to capture infra/orchestrator logs
        self._attach_infra_log_handlers()

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
        
        # Capture the main event loop for thread-safe event emission
        self._main_loop = asyncio.get_running_loop()
        
        # Attach log handlers if not already attached
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
        self._pause_event.set()  # Unblock if paused

        # Cancel any pending chat input requests to unblock waiting threads
        if hasattr(self, 'chat_tool') and self.chat_tool:
            # Get all pending request IDs and cancel them
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

        # Detach log handlers
        self._detach_infra_log_handlers()

        self.status = ExecutionStatus.IDLE
        await self._emit("execution:stopped", {})
        self._add_log("info", "", "Execution stopped")
    
    async def restart(self):
        """Restart execution from the beginning with a fresh orchestrator.
        
        This creates a completely new orchestrator instance with a new run_id,
        ensuring a clean slate for re-execution. This is more reliable than
        trying to reset the internal state of the existing orchestrator.
        """
        if self._load_config is None:
            raise RuntimeError("No repositories loaded. Call load_repositories first.")
        
        # Stop any running execution first
        await self.stop()
        
        # Store breakpoints before reload (they should persist)
        saved_breakpoints = self.breakpoints.copy()
        
        self._add_log("info", "", "Restarting with fresh orchestrator...")
        
        # Reload repositories completely - this creates a NEW orchestrator with new run_id
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
        
        # Restore breakpoints
        self.breakpoints = saved_breakpoints
        
        new_run_id = result.get("run_id", "unknown")
        self._add_log("info", "", f"Fresh orchestrator created with new run_id: {new_run_id}")
        
        # Emit reset event with updated statuses
        await self._emit("execution:reset", {
            "node_statuses": {k: v.value for k, v in self.node_statuses.items()},
            "completed_count": 0,
            "total_count": self.total_count,
            "run_id": new_run_id,
        })
        self._add_log("info", "", "Execution reset - ready to run again")
    
    async def run_to(self, target_flow_index: str):
        """Run execution until a specific flow_index is reached, then pause.
        
        This is useful for debugging - run all the way to a specific node
        and then stop so you can inspect the state.
        
        Args:
            target_flow_index: The flow_index to run to (will pause AFTER executing this)
        """
        if self.orchestrator is None:
            raise RuntimeError("No repositories loaded. Call load_repositories first.")
        
        # Validate that the target exists
        if target_flow_index not in self.node_statuses:
            raise ValueError(f"Unknown flow_index: {target_flow_index}")
        
        # Check if already completed
        if self.node_statuses.get(target_flow_index) == NodeStatus.COMPLETED:
            raise ValueError(f"Target node {target_flow_index} is already completed")
        
        # Capture the main event loop for thread-safe event emission
        self._main_loop = asyncio.get_running_loop()
        
        # Attach log handlers to capture infra/orchestrator logs
        self._attach_infra_log_handlers()

        # Set up run-to mode
        self._run_to_target = target_flow_index
        self.status = ExecutionStatus.RUNNING
        self._stop_requested = False
        self._pause_event.set()
        
        await self._emit("execution:started", {"run_to": target_flow_index})
        self._add_log("info", "", f"Running to {target_flow_index}")
        
        # Start execution in background task
        self._run_task = asyncio.create_task(self._run_loop())
    
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
    
    def set_verbose_logging(self, enabled: bool):
        """Enable or disable verbose (DEBUG level) logging."""
        self.verbose_logging = enabled
        if self._log_handler:
            self._log_handler.verbose = enabled
            log_level = logging.DEBUG if enabled else logging.INFO
            self._log_handler.setLevel(log_level)
        self._add_log("info", "", f"Verbose logging {'enabled' if enabled else 'disabled'}")
    
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
        
        # Check cache first
        if self.current_inference in self._inference_metadata:
            return self._inference_metadata[self.current_inference].get('paradigm')
        
        # Try to extract from inference repository
        if self.inference_repo:
            try:
                for inf_entry in self.inference_repo.inferences:
                    flow_idx = inf_entry.flow_info.get('flow_index', '')
                    if flow_idx == self.current_inference:
                        # Get working interpretation paradigm
                        wi = getattr(inf_entry, 'working_interpretation', None)
                        if wi:
                            paradigm = wi.get('paradigm') if isinstance(wi, dict) else getattr(wi, 'paradigm', None)
                            # Cache it
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
            # Mark previous step as completed
            if progress.get("current_step") and progress["current_step"] not in progress["completed_steps"]:
                progress["completed_steps"].append(progress["current_step"])
            progress["current_step"] = step_name
            progress["current_step_index"] = step_index
    
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
            # Get the concept entry from the repository
            concept_entry = self.concept_repo.get_concept(concept_name)
            if concept_entry is None:
                return None
            
            # Get the actual Concept object from the entry
            concept = concept_entry.concept if hasattr(concept_entry, 'concept') else None
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
            # IMPORTANT: Limit depth to number of axes to avoid treating
            # nested list VALUES as additional dimensions.
            # e.g., axes=['_none_axis'], data=[[{...}, {...}]] should give shape=[1], not [1,2]
            # The inner list [{...}, {...}] is the VALUE of cell [0], not another dimension.
            if result["data"] is not None:
                shape = []
                current = result["data"]
                axes_count = len(result["axes"]) if result["axes"] else 0
                
                # If we have axes info, use it to limit shape depth
                if axes_count > 0:
                    while isinstance(current, list) and len(shape) < axes_count:
                        shape.append(len(current))
                        if len(current) > 0:
                            current = current[0]
                        else:
                            break
                else:
                    # No axes - treat as scalar (shape=[])
                    # Even if data is a list, with no axes it's a scalar complex value
                    pass
                
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
            for concept_entry in self.concept_repo.get_all_concepts():
                concept_name = concept_entry.concept_name
                ref_data = self.get_reference_data(concept_name)
                if ref_data and ref_data.get("has_reference"):
                    result[concept_name] = ref_data
        except Exception as e:
            logger.warning(f"Error getting all references: {e}")
        
        return result
    
    def _add_log(self, level: str, flow_index: str, message: str):
        """Add a log entry. Thread-safe - can be called from any thread."""
        log_entry = {
            "level": level,
            "flow_index": flow_index,
            "message": message,
            "timestamp": time.time()
        }
        self.logs.append(log_entry)
        # Emit as WebSocket event - thread-safe
        self._emit_threadsafe("log:entry", log_entry)
    
    def _emit_threadsafe(self, event_type: str, data: Dict[str, Any]):
        """Emit an event in a thread-safe manner. Can be called from any thread."""
        try:
            # Try to get the running loop in current thread
            loop = asyncio.get_running_loop()
            # We're in an async context, use create_task directly
            asyncio.create_task(self._emit(event_type, data))
        except RuntimeError:
            # No running loop in current thread, use the stored main loop
            if self._main_loop and self._main_loop.is_running():
                # Schedule the coroutine on the main event loop
                asyncio.run_coroutine_threadsafe(
                    self._emit(event_type, data),
                    self._main_loop
                )
            else:
                # Fallback: just log without emitting (shouldn't happen often)
                logger.debug(f"Could not emit event {event_type}: no event loop available")
    
    def _emit_sync(self, event_type: str, data: Dict[str, Any]):
        """Synchronous emit callback for tools like CanvasUserInputTool.
        
        This is a wrapper around _emit_threadsafe that can be passed as a 
        callback function to synchronous code.
        """
        self._emit_threadsafe(event_type, data)
    
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
                # Sync cycle count with orchestrator tracker so execution logging uses correct cycle
                if hasattr(self.orchestrator, 'tracker'):
                    self.orchestrator.tracker.cycle_count = self.cycle_count
                self._add_log("info", "", f"Starting cycle {self.cycle_count}")
                
                # Process cycle with event emission
                progress_made = await self._run_cycle_with_events()
                
                # Save checkpoint at the end of each cycle (if checkpoint_manager is available)
                if self.orchestrator and self.orchestrator.checkpoint_manager:
                    try:
                        await asyncio.to_thread(
                            self.orchestrator.checkpoint_manager.save_state,
                            self.cycle_count,
                            self.orchestrator,
                            0  # inference_count=0 marks end of cycle
                        )
                        self._add_log("debug", "", f"Checkpoint saved for cycle {self.cycle_count}")
                    except Exception as e:
                        self._add_log("warning", "", f"Failed to save checkpoint: {e}")
                        logger.warning(f"Failed to save checkpoint: {e}")
                
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
                # Detach log handlers on completion
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
            self._detach_infra_log_handlers()
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
            
            # Update agent registry with current flow index for tool monitoring
            agent_registry.set_current_flow_index(flow_index)
            
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
                    
                    # Check if we've hit the "run to" target
                    if self._run_to_target and flow_index == self._run_to_target:
                        self._run_to_target = None  # Clear the target
                        self.status = ExecutionStatus.PAUSED
                        self._pause_event.clear()
                        await self._emit("execution:paused", {
                            "inference": flow_index,
                            "reason": "run_to_target_reached"
                        })
                        self._add_log("info", flow_index, "Run-to target reached - execution paused")
                        break
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
        """Emit event through event emitter, including project_id for multi-project support."""
        # Include project_id in all events so frontend can route them correctly
        if self.project_id:
            data = {**data, "project_id": self.project_id}
        await event_emitter.emit(event_type, data)
    
    # =========================================================================
    # Checkpoint Management Methods
    # =========================================================================
    
    async def list_runs(self, db_path: str) -> List[Dict[str, Any]]:
        """List all runs stored in the checkpoint database.
        
        Args:
            db_path: Path to the orchestration.db file
            
        Returns:
            List of run dicts with: run_id, first_execution, last_execution, 
            execution_count, max_cycle, config (if include_metadata)
        """
        from infra._orchest._db import OrchestratorDB
        
        try:
            db = OrchestratorDB(db_path)
            runs = db.list_runs(include_metadata=True)
            return runs
        except Exception as e:
            logger.error(f"Failed to list runs from {db_path}: {e}")
            return []
    
    async def list_checkpoints(self, db_path: str, run_id: str) -> List[Dict[str, Any]]:
        """List all checkpoints for a specific run.
        
        Args:
            db_path: Path to the orchestration.db file
            run_id: The run ID to list checkpoints for
            
        Returns:
            List of checkpoint dicts with: cycle, inference_count, timestamp
        """
        from infra._orchest._db import OrchestratorDB
        
        try:
            db = OrchestratorDB(db_path, run_id=run_id)
            checkpoints = db.list_checkpoints(run_id=run_id)
            # Sort by cycle descending (newest first)
            checkpoints.sort(key=lambda x: (x['cycle'], x['inference_count']), reverse=True)
            return checkpoints
        except Exception as e:
            logger.error(f"Failed to list checkpoints for run {run_id}: {e}")
            return []
    
    async def get_run_metadata(self, db_path: str, run_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific run."""
        from infra._orchest._db import OrchestratorDB

        try:
            db = OrchestratorDB(db_path, run_id=run_id)
            return db.get_run_metadata(run_id)
        except Exception as e:
            logger.error(f"Failed to get metadata for run {run_id}: {e}")
            return None

    async def delete_run(self, db_path: str, run_id: str) -> Dict[str, Any]:
        """Delete a run and all its checkpoints from the database.
        
        Args:
            db_path: Path to the orchestration database
            run_id: The run ID to delete
            
        Returns:
            Dict with success status and message
        """
        from infra._orchest._db import OrchestratorDB
        
        def _do_delete():
            db = OrchestratorDB(db_path, run_id=run_id)
            conn = db.get_connection()
            cursor = conn.cursor()
            try:
                # Delete all checkpoints for this run
                cursor.execute("DELETE FROM checkpoints WHERE run_id = ?", (run_id,))
                
                # Delete run metadata
                cursor.execute("DELETE FROM run_metadata WHERE run_id = ?", (run_id,))
                
                # Delete execution records
                cursor.execute("DELETE FROM executions WHERE run_id = ?", (run_id,))
                
                # Commit the changes
                conn.commit()
            finally:
                conn.close()
        
        try:
            await asyncio.to_thread(_do_delete)
            
            logger.info(f"Deleted run {run_id} from {db_path}")
            return {"success": True, "message": f"Run {run_id} deleted successfully"}
        except Exception as e:
            logger.error(f"Failed to delete run {run_id}: {e}")
            return {"success": False, "message": str(e)}

    async def _load_repos_and_body(
        self,
        concepts_path: str,
        inferences_path: str,
        inputs_path: Optional[str],
        llm_model: str,
        base_dir: Optional[str],
        paradigm_dir: Optional[str]
    ):
        """Internal helper to load repositories and create body.
        
        This is shared between resume_from_checkpoint and fork_from_checkpoint.
        """
        import json as json_module
        
        try:
            from infra._orchest._repo import ConceptRepo, InferenceRepo
            from infra._agent._body import Body
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
            if not paradigm_path.is_absolute():
                paradigm_path = Path(base_dir) / paradigm_dir
            
            if paradigm_path.exists() and paradigm_path.is_dir():
                custom_paradigm_tool = CustomParadigmTool(paradigm_path)
                logger.info(f"Using custom paradigm directory: {paradigm_path}")
        
        self.body = Body(
            llm_name=llm_model, 
            base_dir=base_dir,
            paradigm_tool=custom_paradigm_tool
        )
        
        # Wrap body tools with monitoring proxies for real-time tool call tracking
        self._wrap_body_with_monitoring(self.body)
        
        return concepts_data, inferences_data, base_dir
    
    def _sync_node_statuses_from_orchestrator(self):
        """Sync node statuses from orchestrator's blackboard after loading checkpoint.
        
        This updates self.node_statuses based on the actual state of the blackboard.
        """
        if not self.orchestrator or not self.orchestrator.blackboard:
            return
        
        self.node_statuses = {}
        self.completed_count = 0
        self.total_count = 0
        
        # Get all items from the waitlist
        for item in self.orchestrator.waitlist.items:
            flow_index = item.inference_entry.flow_info.get('flow_index', '')
            if not flow_index:
                continue
            
            self.total_count += 1
            
            # Check status in blackboard
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
        """Resume execution from an existing checkpoint (same run_id).
        
        This loads the checkpoint state and continues with the same run_id,
        meaning execution history is preserved and continued.
        
        Args:
            concepts_path: Path to concepts.json
            inferences_path: Path to inferences.json
            inputs_path: Optional path to inputs.json
            db_path: Path to orchestration.db
            run_id: The run ID to resume
            cycle: Optional specific cycle to resume from (None = latest)
            mode: Reconciliation mode (PATCH, OVERWRITE, FILL_GAPS)
            llm_model: LLM model name
            base_dir: Base directory for file operations
            max_cycles: Maximum execution cycles
            paradigm_dir: Custom paradigm directory
        """
        try:
            from infra._orchest._orchestrator import Orchestrator
        except ImportError as e:
            raise RuntimeError(f"Failed to import Orchestrator: {e}")
        
        # Stop any running execution first
        await self.stop()
        
        # Load repos and create body
        concepts_data, inferences_data, base_dir = await self._load_repos_and_body(
            concepts_path, inferences_path, inputs_path,
            llm_model, base_dir, paradigm_dir
        )
        
        self._add_log("info", "", f"Resuming run {run_id} from checkpoint...")
        
        # Load orchestrator from checkpoint
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
        
        # Sync node statuses from orchestrator
        self._sync_node_statuses_from_orchestrator()
        
        self.status = ExecutionStatus.IDLE
        self._retries = []
        self.cycle_count = self.orchestrator.tracker.cycle_count if hasattr(self.orchestrator, 'tracker') else 0
        
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
        
        # Emit loaded event
        await self._emit("execution:loaded", {
            "run_id": self.orchestrator.run_id,
            "total_inferences": self.total_count,
            "completed_count": self.completed_count,
            "mode": "resume",
        })
        
        self._add_log("info", "", f"Resumed: {self.completed_count}/{self.total_count} already complete")
        
        # Log checkpoint_manager status for debugging
        if self.orchestrator and self.orchestrator.checkpoint_manager:
            self._add_log("debug", "", f"Checkpoint manager initialized for run: {run_id}")
        else:
            self._add_log("warning", "", "Checkpoint manager NOT initialized after resume - checkpoints will not be saved!")

        return {
            "success": True,
            "run_id": run_id,
            "mode": "resume",
            "completed_count": self.completed_count,
            "total_count": self.total_count,
            "message": f"Resumed from checkpoint - {self.completed_count}/{self.total_count} nodes already complete"
        }
    
    # =========================================================================
    # Value Override Methods (Phase 4.1)
    # =========================================================================
    
    async def override_value(
        self,
        concept_name: str,
        new_value: Any,
        rerun_dependents: bool = False
    ) -> Dict[str, Any]:
        """Override a concept's reference value.
        
        This allows modifying the value at any node (ground or computed) and
        optionally triggering re-execution of dependent nodes.
        
        Args:
            concept_name: The name of the concept to override
            new_value: The new value to set (can be any JSON-serializable value)
            rerun_dependents: If True, mark dependents as stale and start execution
            
        Returns:
            Dict with success status, overridden concept, and stale nodes list
        """
        if self.concept_repo is None:
            raise RuntimeError("No repositories loaded. Call load_repositories first.")
        
        try:
            # Get concept from repo
            concept_entry = self.concept_repo.get_concept(concept_name)
            if concept_entry is None:
                raise ValueError(f"Concept '{concept_name}' not found in repository")
            
            concept = concept_entry.concept if hasattr(concept_entry, 'concept') else None
            if concept is None:
                raise ValueError(f"Could not access concept object for '{concept_name}'")
            
            # Get axis names from existing reference if present
            axis_names = None
            if hasattr(concept, 'reference') and concept.reference is not None:
                if hasattr(concept.reference, 'axes') and concept.reference.axes:
                    axis_names = concept.reference.axes.copy() if isinstance(concept.reference.axes, list) else list(concept.reference.axes)
            
            # Use the concept_repo.add_reference() method which handles Reference creation properly
            self.concept_repo.add_reference(concept_name, new_value, axis_names=axis_names)
            
            # Find dependent inferences (nodes that use this concept as input)
            dependents = self._find_dependents(concept_name)
            
            # Mark dependents as stale (pending)
            stale_nodes = []
            for flow_index in dependents:
                if flow_index in self.node_statuses:
                    self.node_statuses[flow_index] = NodeStatus.PENDING
                    stale_nodes.append(flow_index)
            
            self._add_log("info", "", f"Overridden value for '{concept_name}', {len(stale_nodes)} nodes marked stale")
            
            # Emit override event
            await self._emit("value:overridden", {
                "concept_name": concept_name,
                "stale_nodes": stale_nodes,
            })
            
            if rerun_dependents and stale_nodes:
                # Start execution to process stale nodes
                await self.start()
            
            return {
                "success": True,
                "overridden": concept_name,
                "stale_nodes": stale_nodes,
            }
            
        except Exception as e:
            logger.error(f"Failed to override value for {concept_name}: {e}")
            raise
    
    def _find_dependents(self, concept_name: str) -> List[str]:
        """Find all flow_indices of inferences that depend on a given concept.
        
        This finds all inferences that use the concept as:
        - concept_to_infer (the target concept)
        - function_concept
        - value_concepts
        - context_concepts
        """
        if self.inference_repo is None:
            return []
        
        dependents = []
        
        for inf_entry in self.inference_repo.inferences:
            flow_index = inf_entry.flow_info.get('flow_index', '')
            if not flow_index:
                continue
            
            # Check if this inference uses the concept
            is_dependent = False
            
            # Check value concepts
            if hasattr(inf_entry, 'value_concepts') and inf_entry.value_concepts:
                for vc in inf_entry.value_concepts:
                    vc_name = vc.concept_name if hasattr(vc, 'concept_name') else str(vc)
                    if vc_name == concept_name:
                        is_dependent = True
                        break
            
            # Check context concepts
            if not is_dependent and hasattr(inf_entry, 'context_concepts') and inf_entry.context_concepts:
                for cc in inf_entry.context_concepts:
                    cc_name = cc.concept_name if hasattr(cc, 'concept_name') else str(cc)
                    if cc_name == concept_name:
                        is_dependent = True
                        break
            
            if is_dependent:
                dependents.append(flow_index)
        
        return dependents
    
    def _find_descendants(self, flow_index: str) -> List[str]:
        """Find all nodes that are downstream from a given flow_index.
        
        This traverses the inference graph to find all nodes that directly or
        indirectly depend on the specified node.
        """
        if self.inference_repo is None or self.concept_repo is None:
            return []
        
        # Build a mapping from flow_index to concept_name
        flow_to_concept: Dict[str, str] = {}
        for inf_entry in self.inference_repo.inferences:
            fi = inf_entry.flow_info.get('flow_index', '')
            if fi and hasattr(inf_entry, 'concept_to_infer'):
                flow_to_concept[fi] = inf_entry.concept_to_infer.concept_name
        
        # Get the concept name for the starting flow_index
        start_concept = flow_to_concept.get(flow_index)
        if not start_concept:
            return []
        
        # BFS to find all descendants
        descendants = []
        visited = set()
        queue = [start_concept]
        
        while queue:
            current_concept = queue.pop(0)
            if current_concept in visited:
                continue
            visited.add(current_concept)
            
            # Find inferences that use this concept
            dependents = self._find_dependents(current_concept)
            for dep_fi in dependents:
                if dep_fi not in visited and dep_fi != flow_index:
                    descendants.append(dep_fi)
                    # Get the concept for this inference and add to queue
                    dep_concept = flow_to_concept.get(dep_fi)
                    if dep_concept and dep_concept not in visited:
                        queue.append(dep_concept)
        
        return descendants
    
    # =========================================================================
    # Selective Re-run Methods (Phase 4.3)
    # =========================================================================
    
    async def rerun_from(self, flow_index: str) -> Dict[str, Any]:
        """Reset and re-execute from a specific node.
        
        This resets the target node and all its descendants, then starts
        execution from the beginning (which will skip already-completed nodes).
        
        Args:
            flow_index: The flow_index to re-run from
            
        Returns:
            Dict with success status and reset node count
        """
        if self.orchestrator is None:
            raise RuntimeError("No repositories loaded. Call load_repositories first.")
        
        # Validate the flow_index exists
        if flow_index not in self.node_statuses:
            raise ValueError(f"Unknown flow_index: {flow_index}")
        
        # Stop any running execution first
        if self.status in (ExecutionStatus.RUNNING, ExecutionStatus.STEPPING):
            await self.stop()
        
        # Find all descendants
        descendants = self._find_descendants(flow_index)
        nodes_to_reset = [flow_index] + descendants
        
        self._add_log("info", flow_index, f"Re-running from {flow_index}, resetting {len(nodes_to_reset)} nodes")
        
        # Reset node statuses
        for fi in nodes_to_reset:
            if fi in self.node_statuses:
                self.node_statuses[fi] = NodeStatus.PENDING
                self.completed_count = max(0, self.completed_count - 1)
        
        # Clear computed references for reset nodes
        for fi in nodes_to_reset:
            try:
                # Find the concept for this flow_index
                for inf_entry in self.inference_repo.inferences:
                    if inf_entry.flow_info.get('flow_index') == fi:
                        concept_name = inf_entry.concept_to_infer.concept_name
                        concept_entry = self.concept_repo.get_concept(concept_name)
                        if concept_entry:
                            concept = concept_entry.concept if hasattr(concept_entry, 'concept') else None
                            if concept and not getattr(concept, 'is_ground_concept', False):
                                # Clear the reference for non-ground concepts
                                concept.reference = None
                        break
            except Exception as e:
                logger.warning(f"Could not clear reference for {fi}: {e}")
        
        # Reset blackboard statuses
        try:
            for fi in nodes_to_reset:
                if self.orchestrator.blackboard:
                    # Mark as pending in blackboard
                    self.orchestrator.blackboard.set_item_status(fi, 'pending')
        except Exception as e:
            logger.warning(f"Could not reset blackboard for some nodes: {e}")
        
        # Emit partial reset event
        await self._emit("execution:partial_reset", {
            "reset_nodes": nodes_to_reset,
            "from_flow_index": flow_index,
        })
        
        # Start execution
        await self.start()
        
        return {
            "success": True,
            "from_flow_index": flow_index,
            "reset_count": len(nodes_to_reset),
            "reset_nodes": nodes_to_reset,
        }
    
    # =========================================================================
    # Function Modification Methods (Phase 4.2)
    # =========================================================================
    
    async def modify_function(
        self,
        flow_index: str,
        modifications: Dict[str, Any],
        retry: bool = False
    ) -> Dict[str, Any]:
        """Modify a function node's working interpretation.
        
        This allows changing the paradigm, prompt location, output type, etc.
        for a function node before re-execution.
        
        Args:
            flow_index: The flow_index of the function node to modify
            modifications: Dict of fields to update (paradigm, prompt_location, etc.)
            retry: If True, immediately run to this node
            
        Returns:
            Dict with success status
        """
        if self.inference_repo is None:
            raise RuntimeError("No repositories loaded. Call load_repositories first.")
        
        # Find the inference
        target_inference = None
        for inf_entry in self.inference_repo.inferences:
            if inf_entry.flow_info.get('flow_index') == flow_index:
                target_inference = inf_entry
                break
        
        if target_inference is None:
            raise ValueError(f"Inference not found for flow_index: {flow_index}")
        
        # Update working interpretation
        wi = getattr(target_inference, 'working_interpretation', {})
        if not isinstance(wi, dict):
            wi = {}
        
        modified_fields = []
        for key, value in modifications.items():
            if value is not None:
                wi[key] = value
                modified_fields.append(key)
        
        target_inference.working_interpretation = wi
        
        # Reset node status to pending
        if flow_index in self.node_statuses:
            self.node_statuses[flow_index] = NodeStatus.PENDING
        
        self._add_log("info", flow_index, f"Modified working interpretation: {', '.join(modified_fields)}")
        
        # Emit modification event
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
        """Fork from an existing checkpoint with a new run_id.
        
        This loads the checkpoint state but starts a NEW run with a new run_id,
        meaning execution history starts fresh while inheriting checkpoint state.
        
        Args:
            concepts_path: Path to concepts.json
            inferences_path: Path to inferences.json
            inputs_path: Optional path to inputs.json
            db_path: Path to orchestration.db
            source_run_id: The run ID to fork from
            new_run_id: New run ID (auto-generated if None)
            cycle: Optional specific cycle to fork from (None = latest)
            mode: Reconciliation mode (PATCH, OVERWRITE, FILL_GAPS)
            llm_model: LLM model name
            base_dir: Base directory for file operations
            max_cycles: Maximum execution cycles
            paradigm_dir: Custom paradigm directory
        """
        import uuid as uuid_module
        
        try:
            from infra._orchest._orchestrator import Orchestrator
        except ImportError as e:
            raise RuntimeError(f"Failed to import Orchestrator: {e}")
        
        # Stop any running execution first
        await self.stop()
        
        # Generate new run_id if not provided
        if new_run_id is None:
            new_run_id = f"fork-{str(uuid_module.uuid4())[:8]}"
        
        # Load repos and create body
        concepts_data, inferences_data, base_dir = await self._load_repos_and_body(
            concepts_path, inferences_path, inputs_path,
            llm_model, base_dir, paradigm_dir
        )
        
        self._add_log("info", "", f"Forking from {source_run_id} to new run {new_run_id}...")
        
        # Fork orchestrator from checkpoint
        self.orchestrator = await asyncio.to_thread(
            Orchestrator.load_checkpoint,
            concept_repo=self.concept_repo,
            inference_repo=self.inference_repo,
            db_path=db_path,
            body=self.body,
            max_cycles=max_cycles,
            run_id=source_run_id,
            new_run_id=new_run_id,  # This makes it a fork
            cycle=cycle,
            mode=mode
        )
        
        # Sync node statuses from orchestrator
        self._sync_node_statuses_from_orchestrator()
        
        self.status = ExecutionStatus.IDLE
        self._retries = []
        self.cycle_count = 0  # Fresh cycle count for fork
        
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
        
        # Emit loaded event
        await self._emit("execution:loaded", {
            "run_id": new_run_id,
            "total_inferences": self.total_count,
            "completed_count": self.completed_count,
            "mode": "fork",
            "forked_from": source_run_id,
        })
        
        self._add_log("info", "", f"Forked: {self.completed_count}/{self.total_count} nodes carried over")
        
        # Log checkpoint_manager status for debugging
        if self.orchestrator and self.orchestrator.checkpoint_manager:
            self._add_log("debug", "", f"Checkpoint manager initialized for run: {new_run_id}")
        else:
            self._add_log("warning", "", "Checkpoint manager NOT initialized after fork - checkpoints will not be saved!")
        
        return {
            "success": True,
            "run_id": new_run_id,
            "forked_from": source_run_id,
            "mode": "fork",
            "completed_count": self.completed_count,
            "total_count": self.total_count,
            "message": f"Forked from {source_run_id} - {self.completed_count}/{self.total_count} nodes carried over"
        }


class ExecutionControllerRegistry:
    """
    Registry for managing multiple ExecutionController instances.
    
    Enables multiple projects to execute simultaneously, each with its own
    controller maintaining independent execution state.
    """
    
    def __init__(self):
        self._controllers: Dict[str, ExecutionController] = {}
        self._default_controller: Optional[ExecutionController] = None
        self._active_project_id: Optional[str] = None
    
    def get_controller(self, project_id: Optional[str] = None) -> ExecutionController:
        """
        Get an ExecutionController for a project.
        
        Args:
            project_id: Project ID. If None, returns the active controller.
            
        Returns:
            ExecutionController for the project
        """
        if project_id is None:
            project_id = self._active_project_id
        
        if project_id is None:
            # No project context - use/create default controller
            if self._default_controller is None:
                self._default_controller = ExecutionController()
            return self._default_controller
        
        if project_id not in self._controllers:
            # Create new controller for this project
            controller = ExecutionController(project_id=project_id)
            self._controllers[project_id] = controller
            logger.info(f"Created new ExecutionController for project {project_id}")
        
        return self._controllers[project_id]
    
    def get_or_create(self, project_id: str) -> ExecutionController:
        """Get existing controller or create a new one for the project."""
        return self.get_controller(project_id)
    
    def set_active(self, project_id: Optional[str]):
        """Set the active project for the registry."""
        self._active_project_id = project_id
        logger.info(f"Active project set to: {project_id}")
    
    def get_active_project_id(self) -> Optional[str]:
        """Get the currently active project ID."""
        return self._active_project_id
    
    def get_active_controller(self) -> ExecutionController:
        """Get the controller for the active project."""
        return self.get_controller(self._active_project_id)
    
    def has_controller(self, project_id: str) -> bool:
        """Check if a controller exists for a project."""
        return project_id in self._controllers
    
    def remove_controller(self, project_id: str) -> bool:
        """
        Remove and clean up a controller for a project.
        
        Returns True if a controller was removed.
        """
        if project_id in self._controllers:
            controller = self._controllers.pop(project_id)
            # Clean up the controller
            if controller._run_task:
                controller._run_task.cancel()
            logger.info(f"Removed ExecutionController for project {project_id}")
            return True
        return False
    
    def get_all_controllers(self) -> Dict[str, ExecutionController]:
        """Get all registered controllers."""
        return self._controllers.copy()
    
    def get_running_projects(self) -> List[str]:
        """Get list of project IDs that are currently running."""
        running = []
        for project_id, controller in self._controllers.items():
            if controller.status == ExecutionStatus.RUNNING:
                running.append(project_id)
        return running
    
    async def stop_all(self):
        """Stop execution on all controllers."""
        for project_id, controller in self._controllers.items():
            if controller.status == ExecutionStatus.RUNNING:
                await controller.stop()
                logger.info(f"Stopped execution for project {project_id}")


# Global execution controller registry
execution_controller_registry = ExecutionControllerRegistry()


def get_execution_controller(project_id: Optional[str] = None) -> ExecutionController:
    """
    Get the ExecutionController for a project.
    
    This is the primary way to access execution controllers.
    If project_id is None, returns the controller for the active project.
    
    Args:
        project_id: Project ID, or None for the active project
        
    Returns:
        ExecutionController instance for the project
    """
    return execution_controller_registry.get_controller(project_id)


# Backward compatibility: Create a proxy object that delegates to the active controller
class _ExecutionControllerProxy:
    """
    Proxy that delegates all attribute access to the active ExecutionController.
    
    This maintains backward compatibility with code that imports execution_controller
    and uses it directly without specifying a project_id.
    """
    
    def __getattr__(self, name):
        # Delegate to active controller
        controller = execution_controller_registry.get_active_controller()
        return getattr(controller, name)
    
    def __setattr__(self, name, value):
        # Delegate to active controller
        controller = execution_controller_registry.get_active_controller()
        setattr(controller, name, value)


# Backward compatibility: execution_controller is a proxy to the active controller
execution_controller = _ExecutionControllerProxy()
