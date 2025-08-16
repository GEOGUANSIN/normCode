from this import d
from typing import Dict, Any, Callable, List, Optional
import inspect
import logging
import sys
from _concept import Concept
from _reference import Reference, cross_product, element_action, cross_action
from _inference import Inference, register_inference_sequence
from _language_models import LanguageModel


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
    def __init__(self, AgentFrameModel: str, working_interpretation: Optional[dict]=None, llm: Optional[LanguageModel]=None, **body):
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
            logger.info("Setting up demo sequences: imperative, grouping, quantifying")
            self._set_up_imperative_demo(); self._set_up_grouping_demo(); self._set_up_quantifying_demo()
        else:
            logger.warning(f"Unknown AgentFrameModel: {self.AgentFrameModel}")

    def configure(self, inference_instance: Inference, inference_sequence: str, **kwargs):
        logger.info(f"Configuring inference instance with sequence: {inference_sequence}")
        if self.AgentFrameModel == "demo":
            if inference_sequence == "imperative":
                logger.info("Configuring imperative demo sequence"); self._configure_imperative_demo(inference_instance, **demo_methods("imperative"))
            elif inference_sequence == "grouping":
                logger.info("Configuring grouping demo sequence"); self._configure_grouping_demo(inference_instance, **demo_methods("grouping"))
            elif inference_sequence == "quantifying":
                logger.info("Configuring quantifying demo sequence"); self._configure_quantifying_demo(inference_instance, **demo_methods("quantifying"))
            else:
                logger.warning(f"Unknown inference sequence: {inference_sequence}")
        else:
            logger.warning(f"Configuration not supported for model: {self.AgentFrameModel}")



    def _set_up_simple_demo(self):
        logger.debug("Setting up simple demo sequence")
        working_interpretation = self.working_interpretation #suppose that all syntatical parsing is done here.
        body = self.body

        @register_inference_sequence("simple")
        def simple(self: Inference):
            """`(IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI)`"""
            logger.info("=====EXECUTING SIMPLE SEQUENCE=====")
            states = States()
            logger.info("---Step 1: Input Working Interpretation (IWI)---"); states = self.IWI(self, states, body, working_interpretation)
            logger.info("---Step 2: Input References (IR)---"); states = self.IR(self, states)
            logger.info("---Step 3: Output Reference (OR)---"); states = self.OR(states)
            logger.info("---Step 4: Output Working Interpretation (OWI)---"); states = self.OWI(states)
            logger.info("=====SIMPLE SEQUENCE COMPLETED=====")
            return states

    def _configure_simple_demo(self, inference_instance: Inference, **methods):
        logger.debug("Configuring simple demo steps")
        @inference_instance.register_step("IWI")
        def IWI(**fkwargs): return methods.get("input_working_interpretation", self._null_step)(**fkwargs) 
        
        @inference_instance.register_step("IR")
        def IR(**fkwargs): return methods.get("input_references", self._null_step)(**fkwargs)
         
        @inference_instance.register_step("OR")
        def OR(**fkwargs): return methods.get("output_reference", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("OWI")
        def OWI(**fkwargs): return methods.get("output_working_interpretation", self._null_step)(**fkwargs)
        

    def _set_up_imperative_demo(self):
        logger.debug("Setting up imperative demo sequence")
        working_interpretation = self.working_interpretation #suppose that all syntatical parsing is done here.
        body = self.body

        @register_inference_sequence("imperative")
        def imperative(self: Inference):
            """`(IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI)`"""
            logger.info("=====EXECUTING IMPERATIVE SEQUENCE=====")
            states = States()
            logger.info("---Step 1: Input Working Interpretation (IWI)---"); states = self.IWI(self, states, body, working_interpretation)
            logger.info("---Step 2: Input References (IR)---"); states = self.IR(self, states)
            logger.info("---Step 3: Model Function Perception (MFP)---"); states = self.MFP(states)
            logger.info("---Step 4: Memory Value Perception (MVP)---"); states = self.MVP(states)
            logger.info("---Step 5: Tool Value Actuation (TVA)---"); states = self.TVA(states)
            logger.info("---Step 6: Tool Inference Perception (TIP)---"); states = self.TIP(states)
            logger.info("---Step 7: Memory Inference Actuation (MIA)---"); states = self.MIA(states)
            logger.info("---Step 8: Output Reference (OR)---"); states = self.OR(states)
            logger.info("---Step 9: Output Working Interpretation (OWI)---"); states = self.OWI(states)
            logger.info("=====IMPERATIVE SEQUENCE COMPLETED=====")
            return states

    def _configure_imperative_demo(self, inference_instance: Inference, **methods):
        logger.debug("Configuring imperative demo steps")
        @inference_instance.register_step("IWI")
        def IWI(**fkwargs): return methods.get("input_working_interpretation", self._null_step)(**fkwargs) 
        
        @inference_instance.register_step("IR")
        def IR(**fkwargs): return methods.get("input_references", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("MFP")
        def MFP(**fkwargs): return methods.get("model_function_perception", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("MVP")
        def MVP(**fkwargs): return methods.get("memory_value_perception", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("TVA")
        def TVA(**fkwargs): return methods.get("tool_value_actuation", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("TIP")
        def TIP(**fkwargs): return methods.get("tool_inference_perception", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("MIA")
        def MIA(**fkwargs): return methods.get("memory_inference_actuation", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("OR")
        def OR(**fkwargs): return methods.get("output_reference", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("OWI")
        def OWI(**fkwargs): return methods.get("output_working_interpretation", self._null_step)(**fkwargs)
        
    def _set_up_grouping_demo(self):
        logger.debug("Setting up grouping demo sequence")
        working_interpretation = self.working_interpretation #suppose that all syntatical parsing is done here.
        body = self.body

        @register_inference_sequence("grouping")
        def grouping(self: Inference, input_data: dict):
            """`(IWI-IR-GR-OR-OWI)`"""
            logger.info("Executing grouping sequence")
            states = States()
            logger.info("---Step 1: Input Working Interpretation (IWI)---"); states = self.IWI(self, states, body, working_interpretation)    
            logger.info("---Step 2: Input References (IR)---"); states = self.IR(self, states)
            logger.info("---Step 3: Grouping References (GR)---"); states = self.GR(states)
            logger.info("---Step 4: Output Reference (OR)---"); states = self.OR(states)
            logger.info("---Step 5: Output Working Interpretation (OWI)---"); states = self.OWI(states)
            logger.info("=====GROUPING SEQUENCE COMPLETED=====")
            return states

    def _configure_grouping_demo(self, inference_instance: Inference, **methods):
        logger.debug("Configuring grouping demo steps")
        @inference_instance.register_step("IWI")
        def IWI(**fkwargs): return methods.get("input_working_interpretation", self._null_step)(**fkwargs) 
        
        @inference_instance.register_step("IR")
        def IR(**fkwargs): return methods.get("input_references", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("GR")
        def GR(**fkwargs): return methods.get("grouping_references", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("OR")
        def OR(**fkwargs): return methods.get("output_reference", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("OWI")
        def OWI(**fkwargs): return methods.get("output_working_interpretation", self._null_step)(**fkwargs)

    def _set_up_quantifying_demo(self):
        logger.debug("Setting up quantifying demo sequence")
        working_interpretation = self.working_interpretation #suppose that all syntatical parsing is done here.
        body = self.body

        @register_inference_sequence("quantifying")
        def quantifying(self: Inference, input_data: dict):
            """`(IWI-IR-GR-QR-OR-OWI)`"""
            logger.info("Executing quantifying sequence")
            states = States()
            logger.info("---Step 1: Input Working Interpretation (IWI)---"); states = self.IWI(self, states, body, working_interpretation)    
            logger.info("---Step 2: Input References (IR)---"); states = self.IR(self, states)
            logger.info("---Step 3: Grouping References (GR)---"); states = self.GR(states)
            logger.info("---Step 4: Quantifying References (QR)---"); states = self.QR(states)
            logger.info("---Step 5: Output Reference (OR)---"); states = self.OR(states)
            logger.info("---Step 6: Output Working Interpretation (OWI)---"); states = self.OWI(states)
            logger.info("=====QUANTIFYING SEQUENCE COMPLETED=====")
            return states

    def _configure_quantifying_demo(self, inference_instance: Inference, **methods):
        logger.debug("Configuring quantifying demo steps")
        @inference_instance.register_step("IWI")
        def IWI(**fkwargs): return methods.get("input_working_interpretation", self._null_step)(**fkwargs) 
        
        @inference_instance.register_step("IR")
        def IR(**fkwargs): return methods.get("input_references", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("GR")
        def GR(**fkwargs): return methods.get("grouping_references", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("QR")
        def QR(**fkwargs): return methods.get("quantifying_references", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("OR")
        def OR(**fkwargs): return methods.get("output_reference", self._null_step)(**fkwargs)
        
        @inference_instance.register_step("OWI")
        def OWI(**fkwargs): return methods.get("output_working_interpretation", self._null_step)(**fkwargs)





class States:

    def __init__(self):
        pass 
    
    # The first thing is to set up the input working interpretation - and understand the attributes of the state manager
    # The state manager is a class that will be used to manage the state of the inference
    # The state manager will have the following input:
    # - working_interpretation: the working interpretation of the inference
    # - body: the body of the inference
    # - inferences: the input references of the inference


    # working interpretation will sorrounding the function concept's interpretation 
        # 
            

def input_working_interpretation(inference, states, body, working_interpretation):
    """
    Input working interpretation and set up the state manager's reference sequence.
    """
    # the working interpretation will be a dictionary of the following format:
    # {
    #     "function_concept_name": {
    #         "sequence": "IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI",
    # working interpretation will sorrounding the function concept's interpretation 
    # the first thing is to understand the steps in the sequence - and the input and output of the steps - this will be known through the interpretation
    # interpretation[inference.function_concept.name][sequence] = "IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI"
    # the next step is to understand the input and output of the steps - this will be known through the interpretation
    # states.interpretation should look like the following in dictionary format:
    '''
    suppose that the seqeunce is "IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI"
    {
        "sequence": [
        {step_name:"IWI", step_index:"1"},
        {step_name:"IR", step_index:"2"},
        {step_name:"MFP", step_index:"3"},
        {step_name:"MVP", step_index:"4"},
        {step_name:"TVA", step_index:"5"},
        {step_name:"TIP", step_index:"6"},
        {step_name:"MIA", step_index:"7"},
        {step_name:"OR", step_index:"8"},
        {step_name:"OWI", step_index:"9"}
        ],
        "current_step": "IWI",
        "current_step_index": "1",
        "function":[
            {
                "step_name": "IR",
                "step_index": "2",
                "concept_name": 
                "axis_name":
                "concept_type":
                "reference": optional
            },
            {
                "step_name": "MFP",
                "step_index": "3",
                "concept_name": mfp_reference
                "concept_axis_name":
                "concept_type":
                "value_order":
                "model": {
                    "type": "model_type",
                    "model_call": "model_call",
                    "aim": "aim_of_the_model",
                    "prompts": [
                        {
                            "prompt_name": "prompt_name",
                            "prompt_type": "prompt_type",
                            "prompt_content": "prompt_content",
                        }
                    ],
                    "tool_calls": [
                        {
                            "tool_name": "buffer",
                            "affordances": [
                                {
                                    "affordance_name": "read",
                                    "tool_call": "buffer.read",
                                    "record_name":
                                },
                                {
                                    "affordance_name": "write",
                                    "tool_call": "buffer.write",
                                    "record_name":
                                }
                            ]
                        }
                    ]
                },
                "reference": optional
            },
        ],
        "values":[
            {
                "step_name": "TVA",
                "step_index": "5",
                "concept_name": tva_reference
                "axis_name":
                "concept_type":
                "extraction":
                "quantification":
                "reference": optional
            },
            {
                "step_name": "MVP",
                "step_index": "4",
                "concept_name": mvp_reference
                "axis_name":
                "concept_type":
                "extraction":
                "quantification":
                "value_order":[
                    "value_name",
                    "value_name",
                ],
                "cross_values":
                "memory": {
                    "type": "memory_type",
                },
                "reference": optional
            },
            {
                "step_name": "IR",
                "step_index": "2",
                "concept_name":
                "axis_name":
                "concept_type":
                "extraction":
                "quantification":
            },          
            ...
        ]
        "context":[
            {
                "step_name": "IR",
                "step_index": "2",
                "concept_name":
                "axis_name":
                "concept_type":
                "extraction":
                "quantification":
                "reference": optional
            },
        ]
        "inference":[
            {
                "step_name": "TIP",
                "step_index": "6",
                "concept_name":
                "axis_name":
                "concept_type":
                "extraction":
                "quantification":
                    "tools": [
                        {
                            "tool_name": "buffer",
                            "affordances": [
                                {
                                    "affordance_name": "read",
                                    "tool_call": "buffer.read",
                                    "record_name":
                                }
                            ]
                        }
                    ]
                "reference": optional
            },
            {
                "step_name": "MIA",
                "step_index": "7",
                "concept_name":
                "axis_name":
                "concept_type":
                "extraction":
                "quantification":
            },...
        
        ]
    }
    '''
    # {function}
    return states


def demo_methods(inference_sequence: str):
    """
    Return the demo methods for the given inference sequence.
    """
    if inference_sequence == "imperative":
        return {
            "IWI": input_working_interpretation,
        }
    else:
        raise ValueError(f"Unknown inference sequence: {inference_sequence}")



    
def _log_concept_details(concept, reference=None, example_number=None, concept_name=None):
    """Helper function to log concept details in a consistent format"""
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


def create_concept_with_reference(concept_name, concept_id, reference_value, concept_type="{}", reference_axes=None, reference_shape=None, axis_name = None) -> tuple[Concept, Reference]:
    """
    Create a concept with an associated reference object.
    
    Args:
        concept_name (str): The name of the concept (e.g., "{technical_concepts}?")
        concept_id (str): The internal identifier for the concept
        reference_value (str): The value to set in the reference
        concept_type (str): The type format for the concept (default: "{}")
        reference_axes (list): List of axis names for the reference (default: [concept_id])
        reference_shape (tuple): Shape of the reference tensor (default: (1,))
    
    Returns:
        tuple: (concept, reference) - The created concept and its reference
    """
    # Set default values if not provided
    if reference_axes is None:
        reference_axes = [concept_id]
    if reference_shape is None:
        reference_shape = (1,)
    
    # Create reference
    reference = Reference(reference_axes, reference_shape)
    
    # Set the reference value
    reference.set(f"%({reference_value})", **{concept_id: 0})
    
    # Create concept
    concept = Concept(concept_name, concept_id, axis_name, reference, concept_type)
    
    return concept, reference

def create_simple_concept(concept_name, concept_id, axis_name = None, concept_type="{}") -> Concept:
    """
    Create a simple concept without a reference object.
    
    Args:
        concept_name (str): The name of the concept
        concept_id (str): The internal identifier for the concept
        axis_name (str): The name of the axis for the concept
        concept_type (str): The type format for the concept (default: "{}")
    
    Returns:
        Concept: The created concept
    """
    return Concept(concept_name, concept_id, axis_name, None, concept_type)

# Abstract usage pattern
if __name__ == "__main__":

    # Create inference instance for arithmetic calculator
    judgement_instance = Inference(
        "judgement",
        Concept("concept_to_infer", "Concept to infer", "concept_to_infer", Reference(axes=["concept_to_infer"], shape=(1,), initial_value=None)),
        [Concept("value_concept", "Value concept", "value_concept", Reference(axes=["value_concept"], shape=(1,), initial_value=None))],
        Concept("function_concept", "Function concept", "function_concept", Reference(axes=["function_concept"], shape=(1,), initial_value=None))
    )

    agent = AgentFrame("demo")

    agent.configure(judgement_instance, "judgement")
    
    judgement_instance.execute(input_data={})