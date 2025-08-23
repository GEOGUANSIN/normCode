
'''
For the sake of the testing, we will make sure this script is self-contained and can be run independently.

Therefore, we will define subclass for the AgentFrame and BaseStates. Also make sequences and steps contained in the script.

We will also include the assigner in the script.

The purpose of the assigning sequence is to handle syntatical concepts like this 
- Specification: $.(_a_:_b_), which takes concept _a_'s reference and assigns it to concept _b_'s reference. This usally means that there are some value concepts being ignored.
- Continuation: $+(_a_:_b_), which takes concept _a_'s reference and adds it to concept _b_'s reference. 

'''


import os
import sys
import logging
from typing import Any, Dict, List, Optional, Tuple, Callable
import json
import random
import re
from types import SimpleNamespace

# Configure logging to show INFO messages
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the project root is in the Python path
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import core components
try:
    from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body, register_inference_sequence, log_states_progress, ConceptInfoLite, ReferenceRecordLite
    from infra._states._common_states import SequenceStepSpecLite
except Exception:
    import pathlib
    here = pathlib.Path(__file__).parent
    sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
    from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body, register_inference_sequence, log_states_progress,ConceptInfoLite, ReferenceRecordLite
    from infra._states._common_states import SequenceStepSpecLite


# --- Create Assigner Class ---

class Assigner:
    """Encapsulates the logic for assignment operations."""
    def specification(self, source_ref: Optional[Reference], dest_ref: Optional[Reference]) -> Optional[Reference]:
        """
        Performs specification (assignment).
        Returns the source reference, or the destination reference if the source is None.
        """
        if source_ref:
            return source_ref.copy()
        
        logging.warning(f"Source reference is missing for specification; using destination reference as fallback.")
        if dest_ref:
            return dest_ref.copy()
        
        # If both are None, return an empty reference
        return Reference(axes=["result"], shape=(0,))

    def continuation(self, source_ref: Optional[Reference], dest_ref: Optional[Reference]) -> Reference:
        """
        Performs continuation (addition/concatenation).
        Returns a new reference with the source's data appended to the destination's data.
        """
        source_val = source_ref.get() if source_ref else []
        dest_val = dest_ref.get() if dest_ref else []

        # Ensure both are lists for concatenation
        if not isinstance(source_val, list):
            source_val = [source_val]
        if not isinstance(dest_val, list):
            dest_val = [dest_val]

        new_val = dest_val + source_val
        return Reference.from_data(new_val)


# --- Create State Class for assigning ---

class AssigningStates(BaseStates):
    """State container for the assigning sequence."""

    def __init__(self) -> None:
        super().__init__()
        self.sequence_state.sequence = [
            SequenceStepSpecLite(step_name="IWI"),
            SequenceStepSpecLite(step_name="IR"),
            SequenceStepSpecLite(step_name="AR"),
            SequenceStepSpecLite(step_name="OR"),
            SequenceStepSpecLite(step_name="OWI"),
        ]
        self.syntax: SimpleNamespace = SimpleNamespace(
            marker=None,
            assign_source=None,
            assign_destination=None
        )


# --- Create Agent Frame for assigning ---

class AssigningAgentFrame(AgentFrame):
    def __init__(self, name: str, working_interpretation: dict, body: Body):
        super().__init__(AgentFrameModel=name, working_interpretation=working_interpretation, body=body)

    def _null_step(**fkwargs):return None

    def _sequence_setup(self):
        """Sets up the 'assigning' inference sequence."""
        logger.debug("Setting up assigning demo sequence")
        
        # Capture context for the sequence function
        working_interpretation = self.working_interpretation
        body = self.body

        @register_inference_sequence("assigning")
        def assigning(inference_instance: Inference):
            """`(IWI-IR-AR-OR-OWI)`"""
            logger.info("=====EXECUTING ASSIGNING SEQUENCE=====")
            states = AssigningStates()
            logger.info("---Step 1: Input Working Interpretation (IWI)---"); states = inference_instance.IWI(inference=inference_instance, states=states, body=body, working_interpretation=working_interpretation); log_states_progress(states, "IWI", "IWI")
            logger.info("---Step 2: Input References (IR)---"); states = inference_instance.IR(inference=inference_instance, states=states); log_states_progress(states, "IR", "IR")
            logger.info("---Step 3: Assigning References (AR)---"); states = inference_instance.AR(states=states); log_states_progress(states, "AR", "AR")
            logger.info("---Step 4: Output Reference (OR)---"); states = inference_instance.OR(states=states); log_states_progress(states, "OR", "OR")
            logger.info("---Step 5: Output Working Interpretation (OWI)---"); states = inference_instance.OWI(states=states); log_states_progress(states, "OWI", "OWI")
            logger.info("=====ASSIGNING SEQUENCE COMPLETED=====")
            return states

    def configure(self, inference_instance: Inference, inference_sequence: str):
        """Configures the steps for the 'assigning' sequence."""
        if inference_sequence != "assigning":
            logger.warning(f"AssigningAgentFrame only supports the 'assigning' sequence, not '{inference_sequence}'.")
            return

        methods = {
            "input_working_interpretation": input_working_interpretation,
            "input_references": input_references,
            "assigning_references": assigning_references,
            "output_reference": output_reference,
            "output_working_interpretation": output_working_interpretation,
        }

        logger.debug("Configuring assigning demo steps")
        @inference_instance.register_step("IWI")
        def IWI(**fkwargs): return methods.get("input_working_interpretation", self._null_step)(**fkwargs)

        @inference_instance.register_step("IR")
        def IR(**fkwargs): return methods.get("input_references", self._null_step)(**fkwargs)

        @inference_instance.register_step("AR")
        def AR(**fkwargs): return methods.get("assigning_references", self._null_step)(**fkwargs)

        @inference_instance.register_step("OR")
        def OR(**fkwargs): return methods.get("output_reference", self._null_step)(**fkwargs)

        @inference_instance.register_step("OWI")
        def OWI(**fkwargs): return methods.get("output_working_interpretation", self._null_step)(**fkwargs)


# --- Create Assigning Steps ---

def input_working_interpretation(
    inference: Inference,
    states: AssigningStates,
    body: Body,
    working_interpretation: Dict[str, Any] | None = None,
) -> AssigningStates:
    """Initialize states with syntax info and placeholder records."""
    if working_interpretation:
        syntax_info = working_interpretation.get("syntax", {})
        states.syntax.marker = syntax_info.get("marker")
        states.syntax.assign_source = syntax_info.get("assign_source")
        states.syntax.assign_destination = syntax_info.get("assign_destination")


    # Seed lists with empty records for each step
    for step in ["AR", "OR"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    states.set_current_step("IWI")
    logging.debug(f"IWI completed. Syntax marker: {states.syntax.marker}")
    return states 


def input_references(inference: Inference, states: AssigningStates) -> AssigningStates:
    """Populate references and concept info into the state from the inference instance."""
    if inference.function_concept:
        states.function.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(
                    id=inference.function_concept.id,
                    name=inference.function_concept.name,
                    type=inference.function_concept.type,
                    context=inference.function_concept.context,
                    axis_name=inference.function_concept.axis_name,
                ),
                reference=inference.function_concept.reference.copy()
                if inference.function_concept.reference
                else None,
            )
        )

    for vc in inference.value_concepts or []:
        states.values.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(
                    id=vc.id, name=vc.name, type=vc.type, context=vc.context, axis_name=vc.axis_name
                ),
                reference=vc.reference.copy() if vc.reference else None,
            )
        )

    for cc in inference.context_concepts or []:
        states.context.append(
            ReferenceRecordLite(
                step_name="IR",
                concept=ConceptInfoLite(
                    id=cc.id, name=cc.name, type=cc.type, context=cc.context, axis_name=cc.axis_name
                ),
                reference=cc.reference.copy() if cc.reference else None,
            )
        )

    states.set_current_step("IR")
    logging.debug(f"IR completed. Loaded {len(states.values)} value and {len(states.context)} context concepts.")
    return states 

def assigning_references(states: AssigningStates) -> AssigningStates:
    """Perform assignment based on syntax marker."""
    syntax_marker = states.syntax.marker
    assign_source_name = states.syntax.assign_source
    assign_destination_name = states.syntax.assign_destination

    if not assign_source_name or not assign_destination_name:
        logging.error("AR failed: 'assign_source' and 'assign_destination' must be specified in syntax.")
        states.set_current_step("AR")
        return states

    # Find the source and destination records from the values list
    value_concepts_map = {rec.concept.name: rec for rec in states.values}

    source_record = value_concepts_map.get(assign_source_name)
    dest_record = value_concepts_map.get(assign_destination_name)

    if not source_record or not dest_record:
        logging.error(f"AR failed: Could not find concepts '{assign_source_name}' or '{assign_destination_name}' in value concepts.")
        states.set_current_step("AR")
        return states

    source_ref = source_record.reference
    dest_ref = dest_record.reference
    
    assigner = Assigner()
    output_ref = None

    if syntax_marker == ".":  # Specification
        logging.info(f"Performing specification (.): Assigning '{source_record.concept.name}' reference to '{dest_record.concept.name}'.")
        output_ref = assigner.specification(source_ref, dest_ref)

    elif syntax_marker == "+":  # Continuation
        logging.info(f"Performing continuation (+): Adding '{source_record.concept.name}' reference to '{dest_record.concept.name}'.")
        output_ref = assigner.continuation(source_ref, dest_ref)

    else:
        logging.warning(f"Unknown syntax marker: {syntax_marker}. No assignment performed.")
        # If no operation, the output is just the destination's original reference
        if dest_ref:
            output_ref = dest_ref.copy()

    if output_ref:
        states.set_reference("inference", "AR", output_ref)

    states.set_current_step("AR")
    logging.debug(f"AR completed. Output reference: {output_ref.get() if output_ref else None}")
    return states


def output_reference(states: AssigningStates) -> AssigningStates:
    """Finalize the output reference."""
    ar_ref = states.get_reference("inference", "AR")
    if ar_ref:
        states.set_reference("inference", "OR", ar_ref)
    states.set_current_step("OR")
    logging.debug("OR completed.")
    return states 

def output_working_interpretation(states: AssigningStates) -> AssigningStates:
    """No-op finalization for demo."""
    states.set_current_step("OWI")
    logging.debug("OWI completed.")
    return states 


# --- Main Execution ---

def _as_list(data: Any) -> List:
    """Ensures the provided data is a list."""
    return data if isinstance(data, list) else [data]

def run_assigning_demo(marker: str, concept_a_val: Any, concept_b_val: Any, concept_c_val: Any):
    """Sets up and runs a single assigning demonstration."""
    logger.info(f"\n----- Running Demo for Syntax: {marker} -----")

    # 1. Setup concepts and working interpretation
    concept_a = Concept("a")
    concept_a.reference = Reference.from_data(_as_list(concept_a_val))

    concept_b = Concept("b")
    concept_b.reference = Reference.from_data(_as_list(concept_b_val))

    concept_c = Concept("c")
    concept_c.reference = Reference.from_data(_as_list(concept_c_val))

    working_interpretation = {
        "syntax": {
            "marker": marker,
            "assign_source": concept_a.name,
            "assign_destination": concept_b.name
        }
    }

    logger.info(f"Initial state: Concept 'a' ref: {concept_a.reference.get()}, Concept 'b' ref: {concept_b.reference.get()}, Concept 'c' ref: {concept_c.reference.get()}")

    # 2. Setup agent and inference
    body = Body()
    agent_frame = AssigningAgentFrame("demo", working_interpretation, body)
    
    assigning_concept = Concept("assigning")

    concept_target = concept_b.copy()

    inference = Inference(
        sequence_name="assigning",
        concept_to_infer=concept_target,
        function_concept=assigning_concept,
        value_concepts=[concept_a, concept_b, concept_c],
    )

    # 3. Configure and run the sequence
    agent_frame.configure(inference, "assigning")

    result_states = inference.execute()

    # 4. Log the result
    final_reference = result_states.get_reference("inference", "OR")
    if final_reference:
        logger.info(f"Final output reference: {final_reference.get()}")
    else:
        logger.warning("Sequence did not produce an output reference.")
    logger.info("----- Demo Complete -----")


if __name__ == "__main__":
    # Demo 1: Specification ($.) - Assigns a's reference to b
    run_assigning_demo(
        marker=".",
        concept_a_val=[{"id": 1, "data": "This is from A"}],
        concept_b_val=["Original value of B"],
        concept_c_val="I am irrelevant context"
    )

    # Demo 2: Continuation ($+) - Appends a's list to b's list
    run_assigning_demo(
        marker="+",
        concept_a_val=[1, 2, 3],
        concept_b_val=["x", "y", "z"],
        concept_c_val=["more", "irrelevant", "context"]
    )






