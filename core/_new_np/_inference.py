"""
Abstract Sequence Configuration - Demonstrates the core logic pattern
"""

from typing import Dict, Any, Callable
import inspect
import logging
import sys
from _concept import Concept
from _reference import Reference

# Configure logging
def setup_logging(level=logging.INFO, log_file=None):
    """Setup logging configuration for the inference module"""
    # Create formatter
    # formatter = logging.Formatter(
    #     '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    # )
    formatter = logging.Formatter(
        '[%(levelname)s] %(message)s - %(asctime)s - %(name)s'
    )

    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# Sequence class for executing registered steps
class Inference:
    def __init__(self, sequence_name: str, concept_to_infer: Concept, value_concepts: list[Concept], function_concept: Concept):
        logger.info(f"Initializing Inference instance with sequence: {sequence_name}")
        logger.debug(f"Concept to infer: {concept_to_infer}")
        logger.debug(f"Value concepts: {value_concepts}")
        logger.debug(f"Function concept: {function_concept}")
        
        self.concept_to_infer: Concept = concept_to_infer
        self.value_concepts: list[Concept] = value_concepts
        self.function_concept: Concept = function_concept
        self.sequence_name = sequence_name
        # Instance-specific step registry
        self._step_registry = {}
        self._initialize_steps()
        logger.info(f"Inference instance initialized successfully")

    def register_step(self, step_name: str, **metadata):
        """Instance method to register a step for this specific instance"""
        logger.debug(f"Registering step: {step_name} with metadata: {metadata}")
        def decorator(func: Callable) -> Callable:
            self._step_registry[step_name] = {
                "function": func,
                "metadata": metadata
            }
            logger.debug(f"Successfully registered step: {step_name}")
            return func
        return decorator

    @property
    def steps(self):
        """Return steps for this specific instance"""
        # Use object.__getattribute__ to avoid triggering __getattr__
        return object.__getattribute__(self, '_step_registry')

    def _initialize_steps(self):
        """Initialize step and check functions from instance registry"""
        logger.debug(f"Initializing {len(self._step_registry)} steps")
        # Replace step functions
        for step_name, step_data in self._step_registry.items():
            # Remove 'step_' prefix if present for cleaner method names
            method_name = step_name.replace('step_', '') if step_name.startswith('step_') else step_name
            setattr(self, method_name, step_data["function"])
            logger.debug(f"Initialized step method: {method_name}")
    
    def __getattr__(self, name):
        """Handle missing methods gracefully"""
        # Use object.__getattribute__ to avoid recursion
        step_registry = object.__getattribute__(self, '_step_registry')
        if name in step_registry:
            logger.debug(f"Retrieved step function: {name}")
            return step_registry[name]["function"]
        logger.warning(f"Attribute '{name}' not found in step registry")
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def _discover_sequences(self) -> Dict[str, Callable]:
        """Discover sequence methods dynamically"""
        # Get instance methods
        instance_sequences = {
            name: method for name, method in inspect.getmembers(self, inspect.ismethod)
            if name in [self.sequence_name]
        }
        
        # Get class methods (including those registered via setattr)
        class_sequences = {
            name: method for name, method in inspect.getmembers(self.__class__, inspect.isfunction)
            if name in [self.sequence_name] and not name.startswith('_')
        }
        
        # Combine both, with instance methods taking precedence
        sequences = {**class_sequences, **instance_sequences}
        logger.debug(f"Discovered sequences: {list(sequences.keys())}")
        return sequences

    def execute(self, input_data, sequence_method: str | None = None):
        """Execute the selected sequence method (default: the one matching sequence_name)"""
        method_name = sequence_method or self.sequence_name
        logger.info(f"Executing sequence method: {method_name}")
        logger.debug(f"Input data: {input_data}")
        
        # Discover sequences at execution time
        sequences = self._discover_sequences()
        
        if method_name not in sequences:
            error_msg = f"Sequence '{method_name}' not found. Available: {list(sequences.keys())}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            result = sequences[method_name](input_data)
            logger.info(f"Sequence '{method_name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing sequence '{method_name}': {str(e)}", exc_info=True)
            raise

    def judgement(self, input_data: dict):
        """placeholder for judgement sequence"""
        logger.debug("Executing judgement sequence placeholder")
        pass
    
    def imperative(self, input_data: dict):
        """placeholder for imperative sequence"""
        logger.debug("Executing imperative sequence placeholder")
        pass


def register_inference_sequence(sequence_name: str):
    """Class method decorator to register a function as a sequence method of the Inference class"""
    logger.debug(f"Registering inference sequence: {sequence_name}")
    def decorator(func: Callable) -> Callable:
        # Add the function as a method to the Inference class
        method_name = f"{sequence_name}"
        setattr(Inference, method_name, func)
        logger.debug(f"Successfully registered sequence method: {method_name}")
        return func
    return decorator