import logging
import io
from typing import List, Union, Optional
from datetime import datetime
import pathlib

from infra._core import Reference, cross_product
from infra._states import ReferenceRecordLite, BaseStates

def setup_logging(log_file: Optional[str] = None):
    """Setup logging to both console and optionally to a file."""
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logging.info(f"Logging to file: {log_file}")

def setup_orchestrator_logging(script_path: str, log_dir_name: str = "logs", run_id: Optional[str] = None) -> str:
    """
    Setup logging for orchestrator scripts with automatic log directory creation.
    
    Args:
        script_path: Path to the script file
        log_dir_name: Name of the log directory (default: "logs")
        run_id: Optional run_id to include in log filename and metadata
    
    Returns:
        Path to the created log file
    """
    script_dir = pathlib.Path(script_path).parent
    logs_dir = script_dir / log_dir_name
    logs_dir.mkdir(exist_ok=True)  # Ensure logs directory exists
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Include run_id in filename if provided (sanitize for filesystem)
    if run_id:
        # Sanitize run_id for filesystem (remove/replace invalid characters)
        sanitized_run_id = run_id.replace(":", "_").replace("/", "_").replace("\\", "_")[:20]  # Limit length
        log_filename = str(logs_dir / f"orchestrator_log_{sanitized_run_id}_{timestamp}.txt")
    else:
        log_filename = str(logs_dir / f"orchestrator_log_{timestamp}.txt")
    
    setup_logging(log_filename)
    
    # Log run_id information at startup if provided
    if run_id:
        logging.info(f"=== Orchestrator Run ID: {run_id} ===")
    
    return log_filename

def log_states_progress(states: BaseStates, step_name: str, step_filter: str | None = None):
    logger = logging.getLogger(__name__)
    logger.info(f"\n--- States after {step_name} (Filtered by: {step_filter if step_filter else 'None'}) ---")
    logger.info(f"Current Step: {states.sequence_state.current_step}")
    
    def _log_record_list(label: str, record_list: List[ReferenceRecordLite]):
        logger.info(f"{label}:")
        filtered_records = [item for item in record_list if step_filter is None or item.step_name == step_filter]
        if not filtered_records:
            logger.info("  (Empty or no matching records for filter)")
            return
        for item in filtered_records:
            logger.info(f"  Step Name: {item.step_name}")
            if item.concept:
                logger.info(f"    Concept ID: {item.concept.id}, Name: {item.concept.name}, Type: {item.concept.type}, Context: {item.concept.context}, Axis: {item.concept.axis_name}")
            if item.reference and isinstance(item.reference, Reference):
                logger.info(f"    Reference Axes: {item.reference.axes}")
                logger.info(f"    Reference Shape: {item.reference.shape}")
                logger.info(f"    Reference Tensor: {item.reference.tensor}")
            if item.model:
                logger.info(f"    Model: {item.model}")

    _log_record_list("Function", states.function)
    _log_record_list("Values", states.values)
    _log_record_list("Context", states.context)
    _log_record_list("Inference", states.inference)

    logger.info("-----------------------------------")



def _log_concept_details(concept, reference=None, example_number=None, concept_name=None):
    """Helper function to log concept details in a consistent format"""
    logger = logging.getLogger(__name__)
    if example_number and concept_name:
        logger.info(f"{example_number}. {concept_name}:")
    
    logger.info(f"   Concept: {concept.name}")
    logger.info(f"   Type: {concept.type} ({concept.get_type_class()})")
    
    if reference and isinstance(reference, Reference):
        # Get all values from the reference using slice(None) for all axes
        slice_params = {axis: slice(None) for axis in reference.axes}
        all_values = reference.get(**slice_params)
        logger.info(f"   All values: {all_values}")
        logger.info(f"   All values without skip values: {reference.get_tensor(ignore_skip=True)}")
        logger.info(f"   Axes: {reference.axes}")

def _log_inference_result(result_concept, value_concepts, function_concept):
    """Log the inference result and related information"""
    logger = logging.getLogger(__name__)
    if result_concept.reference:
        logger.info(f"Answer concept reference: {result_concept.reference.tensor}")
        logger.info(f"Answer concept reference without skip values: {result_concept.reference.get_tensor(ignore_skip=True)}")
        logger.info(f"Answer concept axes: {result_concept.reference.axes}")
        
        # Create list of all references for cross product
        all_references = [result_concept.reference]
        if value_concepts:
            all_references.extend([concept.reference for concept in value_concepts if concept.reference])
        if function_concept and function_concept.reference:
            all_references.append(function_concept.reference)
        
        if len(all_references) > 1:
            all_info_reference = cross_product(all_references)
            logger.info(f"All info reference: {all_info_reference.tensor}")
            logger.info(f"All info reference without skip values: {all_info_reference.get_tensor(ignore_skip=True)}")
            logger.info(f"All info axes: {all_info_reference.axes}")
    else:
        logger.warning("Answer concept reference is None")

def log_workspace_details(workspace: dict, logger_instance: Optional[logging.Logger] = None):
    """Logs the detailed contents of a quantifier workspace."""
    if logger_instance is None:
        logger_instance = logging.getLogger(__name__)

    if not workspace:
        logger_instance.info("Workspace is empty.")
        return

    logger_instance.info("--- Workspace Details ---")
    for subworkspace_key, subworkspace in workspace.items():
        logger_instance.info(f"  Sub-workspace: '{subworkspace_key}'")
        if not subworkspace:
            logger_instance.info("    (Empty)")
            continue
        
        # Sort by loop index to ensure order
        sorted_loop_indices = sorted(subworkspace.keys())
        for loop_index in sorted_loop_indices:
            concepts = subworkspace[loop_index]
            logger_instance.info(f"    Loop Index: {loop_index}")
            if not concepts:
                logger_instance.info("      (No concepts)")
                continue
            
            for concept_name, reference in concepts.items():
                logger_instance.info(f"      Concept: '{concept_name}'")
                if isinstance(reference, Reference):
                    logger_instance.info(f"        Reference Axes: {reference.axes}")
                    logger_instance.info(f"        Reference Shape: {reference.shape}")
                    logger_instance.info(f"        Reference Tensor: {reference.tensor}")
                else:
                    logger_instance.info(f"        Value: {reference}")
    logger_instance.info("-------------------------")


class ExecutionLogHandler(logging.Handler):
    """
    Custom logging handler that captures logs during inference execution.
    
    This handler captures all log messages emitted during an execution and stores
    them in a buffer for later retrieval and persistence to a database.
    """
    
    def __init__(self, execution_id: Optional[int] = None, run_id: Optional[str] = None):
        """
        Initialize the execution log handler.
        
        Args:
            execution_id: Optional execution ID to associate with captured logs
            run_id: Optional run ID to include in log context
        """
        super().__init__()
        self.execution_id = execution_id
        self.run_id = run_id
        self.log_buffer = io.StringIO()
        # Use a simple formatter - we'll add run_id/execution_id in emit()
        self.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    def emit(self, record):
        """Capture log records to buffer."""
        try:
            # Build log message with run_id and execution_id context
            run_id_str = f"[run_id:{self.run_id}] " if self.run_id else ""
            exec_id_str = f"[exec_id:{self.execution_id}] " if self.execution_id else ""
            context_prefix = run_id_str + exec_id_str if (run_id_str or exec_id_str) else ""
            
            msg = self.format(record)
            if context_prefix:
                # Insert context after timestamp but before the rest
                # Format is: timestamp - name - level - message
                # We want: timestamp - [context] - name - level - message
                parts = msg.split(' - ', 1)
                if len(parts) == 2:
                    formatted_msg = f"{parts[0]} - {context_prefix}- {parts[1]}"
                else:
                    formatted_msg = f"{context_prefix}{msg}"
            else:
                formatted_msg = msg
                
            self.log_buffer.write(formatted_msg + '\n')
        except Exception:
            self.handleError(record)
    
    def get_log_content(self) -> str:
        """Get all captured log content."""
        return self.log_buffer.getvalue()
    
    def clear(self):
        """Clear the log buffer."""
        self.log_buffer.seek(0)
        self.log_buffer.truncate(0)