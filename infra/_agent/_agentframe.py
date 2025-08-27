from typing import Optional
import logging
import sys
from infra._core import Concept
from infra._core import Reference, cross_product, element_action, cross_action
from infra._core import Inference, register_inference_sequence
from infra._agent._models import LanguageModel
from infra._agent._sequences.simple import set_up_simple_demo, configure_simple_demo
from infra._agent._sequences.imperative import set_up_imperative_demo, configure_imperative_demo
from infra._agent._sequences.grouping import set_up_grouping_demo, configure_grouping_demo
from infra._agent._sequences.quantifying import set_up_quantifying_demo, configure_quantifying_demo
from infra._agent._sequences.assigning import set_up_assigning_demo, configure_assigning_demo
from infra._agent._sequences.timing import set_up_timing_demo, configure_timing_demo
from infra._states._imperative_states import States as ImperativeStates
from infra._states._grouping_states import States as GroupingStates
from infra._states._quantifying_states import States as QuantifyingStates
from infra._states._simple_states import States as SimpleStates
from infra._states._assigning_states import States as AssigningStates
from infra._agent._steps.simple import simple_methods
from infra._agent._steps.imperative import imperative_methods
from infra._agent._steps.grouping import grouping_methods
from infra._agent._steps.quantifying import quantifying_methods
from infra._agent._steps.assigning import assigning_methods
from infra._agent._steps.timing import timing_methods


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


def strip_element_wrapper(element: str) -> str:
    """
    Strip %( and ) from a reference element.
    
    Args:
        element (str): A string that may be wrapped in %(...)
        
    Returns:
        str: The element with %( and ) removed if present
        
    Examples:
        >>> _strip_element_wrapper("%(1)")
        "1"
        >>> _strip_element_wrapper("%(::({1}<$({number})%_> add {2}<$({number})%_>))")
        "::({1}<$({number})%_> add {2}<$({number})%_>)"
        >>> _strip_element_wrapper("plain_text")
        "plain_text"
    """
    if element.startswith("%(") and element.endswith(")"):
        return element[2:-1]  # Remove first 2 chars (%() and last char ())
    return element

def wrap_element_wrapper(element: str) -> str:
    """
    Wrap an element in %(...)
    """
    return f"%({element})"


class AgentFrame():
    def __init__(self, AgentFrameModel: str, working_interpretation: Optional[dict]=None, llm: Optional[LanguageModel]=None, body: Optional[dict]=None):
        logger.info(f"Initializing AgentFrame with model: {AgentFrameModel}")
        self.AgentFrameModel = AgentFrameModel
        self.working_interpretation = working_interpretation if working_interpretation else {}
        self.body = body
        if llm:
            self.body["llm"] = llm
        self._sequence_setup()
        logger.info("AgentFrame initialized successfully")
    
    def _null_step(**fkwargs):return None

    def _sequence_setup(self):
        logger.debug(f"Setting up sequences for NormCode inference")
        if self.AgentFrameModel == "demo":
            logger.info("Setting up demo sequences: simple, imperative, grouping, quantifying, assigning, timing")
            set_up_simple_demo(self)
            set_up_imperative_demo(self)
            set_up_grouping_demo(self)
            set_up_quantifying_demo(self)
            set_up_assigning_demo(self)
            set_up_timing_demo(self)
        else:
            logger.warning(f"Unknown AgentFrameModel: {self.AgentFrameModel}")

    def configure(self, inference_instance: Inference, inference_sequence: str):
        logger.info(f"Configuring inference instance with sequence: {inference_sequence}")
        if self.AgentFrameModel == "demo":
            if inference_sequence == "imperative":
                logger.info("Configuring imperative demo sequence")
                configure_imperative_demo(self, inference_instance, imperative_methods)
            elif inference_sequence == "grouping":
                logger.info("Configuring grouping demo sequence")
                configure_grouping_demo(self, inference_instance, grouping_methods)
            elif inference_sequence == "quantifying":
                logger.info("Configuring quantifying demo sequence")
                configure_quantifying_demo(self, inference_instance, quantifying_methods)
            elif inference_sequence == "simple":
                logger.info("Configuring simple demo sequence")
                configure_simple_demo(self, inference_instance, simple_methods)
            elif inference_sequence == "assigning":
                logger.info("Configuring assigning demo sequence")
                configure_assigning_demo(self, inference_instance, assigning_methods)
            elif inference_sequence == "timing":
                logger.info("Configuring timing demo sequence")
                configure_timing_demo(self, inference_instance, timing_methods)
            else:
                logger.warning(f"Unknown inference sequence: {inference_sequence}")
        else:
            logger.warning(f"Configuration not supported for model: {self.AgentFrameModel}")



# Abstract usage pattern
if __name__ == "__main__":

    # Create inference instance for arithmetic calculator
    simple_instance = Inference(
        "simple",
        Concept("concept_to_infer", "Concept to infer", "concept_to_infer", Reference(axes=["concept_to_infer"], shape=(1,), initial_value=None)),
        [Concept("value_concept", "Value concept", "value_concept", Reference(axes=["value_concept"], shape=(1,), initial_value=None))],
        Concept("function_concept", "Function concept", "function_concept", Reference(axes=["function_concept"], shape=(1,), initial_value=None))
    )

    agent = AgentFrame("demo")

    agent.configure(simple_instance, "simple")
    
    simple_instance.execute()   