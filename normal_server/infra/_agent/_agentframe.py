from typing import Optional
import logging
import sys
from infra._core import Concept
from infra._core import Reference, cross_product, element_action, cross_action
from infra._core import Inference, register_inference_sequence
from infra._agent._models import LanguageModel
from infra._agent._body import Body
from infra._agent._sequences.simple import set_up_simple_demo, configure_simple_demo
from infra._agent._sequences.imperative import set_up_imperative_demo, configure_imperative_demo
from infra._agent._sequences.grouping import set_up_grouping_demo, configure_grouping_demo
from infra._agent._sequences.quantifying import set_up_quantifying_demo, configure_quantifying_demo
from infra._agent._sequences.looping import set_up_looping_demo, configure_looping_demo
from infra._agent._sequences.assigning import set_up_assigning_demo, configure_assigning_demo
from infra._agent._sequences.timing import set_up_timing_demo, configure_timing_demo
from infra._agent._sequences.judgement import set_up_judgement_demo, configure_judgement_demo
from infra._agent._sequences.imperative_direct import set_up_imperative_direct_demo, configure_imperative_direct_demo
from infra._agent._sequences.imperative_input import set_up_imperative_input_demo, configure_imperative_input_demo
from infra._agent._sequences.judgement_direct import set_up_judgement_direct_demo, configure_judgement_direct_demo
from infra._agent._sequences.imperative_python import set_up_imperative_python_demo, configure_imperative_python_demo
from infra._agent._sequences.judgement_python import set_up_judgement_python_demo, configure_judgement_python_demo
from infra._agent._sequences.imperative_python_indirect import set_up_imperative_python_indirect_demo, configure_imperative_python_indirect_demo
from infra._agent._sequences.judgement_python_indirect import set_up_judgement_python_indirect_demo, configure_judgement_python_indirect_demo
from infra._agent._sequences.imperative_in_composition import set_up_imperative_in_composition_demo, configure_imperative_in_composition_demo
from infra._agent._sequences.judgement_in_composition import set_up_judgement_in_composition_demo, configure_judgement_in_composition_demo
from infra._states._imperative_states import States as ImperativeStates
from infra._states._grouping_states import States as GroupingStates
from infra._states._quantifying_states import States as QuantifyingStates
from infra._states._looping_states import States as LoopingStates
from infra._states._simple_states import States as SimpleStates
from infra._states._assigning_states import States as AssigningStates
from infra._agent._steps.simple import simple_methods
from infra._agent._steps.imperative import imperative_methods
from infra._agent._steps.grouping import grouping_methods
from infra._agent._steps.quantifying import quantifying_methods
from infra._agent._steps.looping import looping_methods
from infra._agent._steps.assigning import assigning_methods
from infra._agent._steps.timing import timing_methods
from infra._agent._steps.judgement import judgement_methods
from infra._agent._steps.imperative_direct import imperative_direct_methods
from infra._agent._steps.imperative_input import imperative_input_methods
from infra._agent._steps.judgement_direct import judgement_direct_methods
from infra._agent._steps.imperative_python import imperative_python_methods
from infra._agent._steps.judgement_python import judgement_python_methods
from infra._agent._steps.imperative_python_indirect import imperative_python_indirect_methods
from infra._agent._steps.judgement_python_indirect import judgement_python_indirect_methods
from infra._agent._steps.imperative_in_composition import imperative_in_composition_methods
from infra._agent._steps.judgement_in_composition import judgement_in_composition_methods


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
logger.setLevel(logging.WARNING)  # Reduced from DEBUG to reduce canvas app verbosity


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
    def __init__(self, AgentFrameModel: str, working_interpretation: Optional[dict]=None, llm: Optional[LanguageModel]=None, body: Optional[Body]=None):
        logger.info(f"Initializing AgentFrame with model: {AgentFrameModel}")
        self.AgentFrameModel = AgentFrameModel
        self.working_interpretation = working_interpretation if working_interpretation else {}
        self.body = body if body else Body()
        if llm:
            from infra._agent._models import LanguageModel as _LM
            self.body.llm = _LM(llm)
        self._sequence_setup()
        logger.info("AgentFrame initialized successfully")
    
    def _null_step(**fkwargs):return None

    def _sequence_setup(self):
        logger.debug(f"Setting up sequences for NormCode inference")
        if self.AgentFrameModel == "demo":
            logger.info("Setting up demo sequences: simple, imperative, grouping, quantifying, looping, assigning, timing")
            set_up_simple_demo(self)
            set_up_imperative_demo(self)
            set_up_grouping_demo(self)
            set_up_quantifying_demo(self)
            set_up_looping_demo(self)
            set_up_assigning_demo(self)
            set_up_timing_demo(self)
            set_up_judgement_demo(self)
            set_up_imperative_direct_demo(self)
            set_up_imperative_input_demo(self)
            set_up_judgement_direct_demo(self)
            set_up_imperative_python_demo(self)
            set_up_judgement_python_demo(self)
            set_up_imperative_python_indirect_demo(self)
            set_up_judgement_python_indirect_demo(self)
            set_up_imperative_in_composition_demo(self)
            set_up_judgement_in_composition_demo(self)
        elif self.AgentFrameModel == "composition":
            logger.info("Setting up composition sequences: simple, imperative (composition), judgement (composition), grouping, quantifying, looping, assigning, timing")
            set_up_simple_demo(self)
            set_up_imperative_in_composition_demo(self)
            set_up_judgement_in_composition_demo(self)
            set_up_grouping_demo(self)
            set_up_quantifying_demo(self)
            set_up_looping_demo(self)
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
            elif inference_sequence == "looping":
                logger.info("Configuring looping demo sequence")
                configure_looping_demo(self, inference_instance, looping_methods)
            elif inference_sequence == "simple":
                logger.info("Configuring simple demo sequence")
                configure_simple_demo(self, inference_instance, simple_methods)
            elif inference_sequence == "assigning":
                logger.info("Configuring assigning demo sequence")
                configure_assigning_demo(self, inference_instance, assigning_methods)
            elif inference_sequence == "timing":
                logger.info("Configuring timing demo sequence")
                configure_timing_demo(self, inference_instance, timing_methods)
            elif inference_sequence == "judgement":
                logger.info("Configuring judgement demo sequence")
                configure_judgement_demo(self, inference_instance, judgement_methods)
            elif inference_sequence == "imperative_direct":
                logger.info("Configuring imperative_direct demo sequence")
                configure_imperative_direct_demo(self, inference_instance, imperative_direct_methods)
            elif inference_sequence == "imperative_input":
                logger.info("Configuring imperative_input demo sequence")
                configure_imperative_input_demo(self, inference_instance, imperative_input_methods)
            elif inference_sequence == "judgement_direct":
                logger.info("Configuring judgement_direct demo sequence")
                configure_judgement_direct_demo(self, inference_instance, judgement_direct_methods)
            elif inference_sequence == "imperative_python":
                logger.info("Configuring imperative_python demo sequence")
                configure_imperative_python_demo(self, inference_instance, imperative_python_methods)
            elif inference_sequence == "judgement_python":
                logger.info("Configuring judgement_python demo sequence")
                configure_judgement_python_demo(self, inference_instance, judgement_python_methods)
            elif inference_sequence == "imperative_python_indirect":
                logger.info("Configuring imperative_python_indirect demo sequence")
                configure_imperative_python_indirect_demo(self, inference_instance, imperative_python_indirect_methods)
            elif inference_sequence == "judgement_python_indirect":
                logger.info("Configuring judgement_python_indirect demo sequence")
                configure_judgement_python_indirect_demo(self, inference_instance, judgement_python_indirect_methods)
            elif inference_sequence == "imperative_in_composition":
                logger.info("Configuring imperative_in_composition demo sequence")
                configure_imperative_in_composition_demo(self, inference_instance, imperative_in_composition_methods)
            elif inference_sequence == "judgement_in_composition":
                logger.info("Configuring judgement_in_composition demo sequence")
                configure_judgement_in_composition_demo(self, inference_instance, judgement_in_composition_methods)
            else:
                logger.warning(f"Unknown inference sequence: {inference_sequence}")
        elif self.AgentFrameModel == "composition":
            if inference_sequence == "imperative":
                logger.info("Configuring imperative sequence using composition methods")
                # Map 'imperative' request to 'imperative_in_composition' implementation
                configure_imperative_in_composition_demo(self, inference_instance, imperative_in_composition_methods)
            elif inference_sequence == "judgement":
                logger.info("Configuring judgement sequence using composition methods")
                # Map 'judgement' request to 'judgement_in_composition' implementation
                configure_judgement_in_composition_demo(self, inference_instance, judgement_in_composition_methods)
            elif inference_sequence == "grouping":
                logger.info("Configuring grouping sequence")
                configure_grouping_demo(self, inference_instance, grouping_methods)
            elif inference_sequence == "quantifying":
                logger.info("Configuring quantifying sequence")
                configure_quantifying_demo(self, inference_instance, quantifying_methods)
            elif inference_sequence == "looping":
                logger.info("Configuring looping sequence")
                configure_looping_demo(self, inference_instance, looping_methods)
            elif inference_sequence == "simple":
                logger.info("Configuring simple sequence")
                configure_simple_demo(self, inference_instance, simple_methods)
            elif inference_sequence == "assigning":
                logger.info("Configuring assigning sequence")
                configure_assigning_demo(self, inference_instance, assigning_methods)
            elif inference_sequence == "timing":
                logger.info("Configuring timing sequence")
                configure_timing_demo(self, inference_instance, timing_methods)
            else:
                 logger.warning(f"Unknown inference sequence for composition model: {inference_sequence}")
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