"""
Orchestrator Log Handler - Captures and parses logs from infra modules.

This handler captures logs from orchestrator/infra modules and forwards them
to the ExecutionController's log system, enabling rich orchestrator logs
to appear in the frontend's Log Panel.

It also parses structured step events from sequence logs for step pipeline
visualization in the UI.
"""

import re
import logging
from typing import Optional, TYPE_CHECKING

from schemas.execution_schemas import SEQUENCE_STEPS, STEP_FULL_NAMES

if TYPE_CHECKING:
    from .controller import ExecutionController

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
    
    # Infra logger names to capture
    INFRA_LOGGERS = [
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


def attach_log_handlers(
    execution_controller: 'ExecutionController',
    verbose: bool = False
) -> OrchestratorLogHandler:
    """
    Attach log handler to infra loggers to capture orchestrator logs.
    
    Args:
        execution_controller: The controller to forward logs to
        verbose: Whether to enable verbose (DEBUG level) logging
        
    Returns:
        The created log handler (store for later detachment)
    """
    log_handler = OrchestratorLogHandler(execution_controller, verbose=verbose)
    log_level = logging.DEBUG if verbose else logging.INFO
    log_handler.setLevel(log_level)
    
    attached_loggers = []
    for logger_name in OrchestratorLogHandler.INFRA_LOGGERS:
        try:
            infra_logger = logging.getLogger(logger_name)
            infra_logger.addHandler(log_handler)
            attached_loggers.append(logger_name)
        except Exception as e:
            logger.warning(f"Failed to attach log handler to {logger_name}: {e}")
    
    logger.info(f"Attached log handler to {len(attached_loggers)} infra loggers")
    return log_handler


def detach_log_handlers(log_handler: OrchestratorLogHandler):
    """Detach log handler from infra loggers."""
    if log_handler is None:
        return
    
    for logger_name in OrchestratorLogHandler.INFRA_LOGGERS:
        try:
            infra_logger = logging.getLogger(logger_name)
            infra_logger.removeHandler(log_handler)
        except Exception:
            pass
    
    logger.info("Detached log handlers from infra loggers")



