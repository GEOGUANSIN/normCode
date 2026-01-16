from typing import Any, Dict
import logging

# Forward-referencing type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from infra import Inference
    from infra._states._judgement_states import States
    from infra._agent._body import Body

from infra._states._model_state import (
	AffordanceSpecLite,
	ToolSpecLite,
	ModelEnvSpecLite,
	ModelStepSpecLite,
	ModelSequenceSpecLite,
	MetaValue,
)
from infra._states._common_states import ReferenceRecordLite
from infra._core import Reference, Concept


def input_working_interpretation(
    inference: "Inference", 
    states: "States", 
    body: "Body",
    working_interpretation: Dict[str, Any] | None = None,
) -> "States":
    """
    IWI step for imperative_direct.
    Builds and saves the specs for creating a generic generation function in a later step.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Running IWI for imperative_direct: Building specs for generic function.")

    states.body = body
    
    config = working_interpretation or {}
    # Add after states.body = body:
    states.workspace = config.get("workspace", {})
    flow_info = config.get("flow_info", {})
    states.flow_index = flow_info.get("flow_index")

    paradigm_name = config.get("paradigm")
    if not paradigm_name:
        raise ValueError("IWI for judgement_in_composition requires a 'paradigm' key in the working_interpretation.")
    
    paradigm = body.paradigm_tool.load(paradigm_name)
    logger.info(f"Loaded composition paradigm: '{paradigm_name}'")

    # Build and save the specs for MFP to execute
    states.mfp_env_spec = paradigm.env_spec
    states.mfp_sequence_spec = paradigm.sequence_spec
    
    # Store axis creation preference (default is True for backward compatibility)
    states.create_axis_on_list_output = config.get("create_axis_on_list_output", True)
    
    # Set value_order and initial values for MVP
    states.value_order = config.get("value_order")
    states.value_selectors = config.get("value_selectors", {})
    values_dict = config.get("values", {})
    for key, value in values_dict.items():
        record = ReferenceRecordLite(
            step_name="IR",  # Use "IR" to be compatible with MVP
            concept=Concept(name=key),
            reference=Reference(data=[value])
        )
        states.values.append(record)
    
    # Handle assertion_condition for TIA step
    assertion_condition = config.get("assertion_condition")
    if assertion_condition:
        states.assertion_condition = assertion_condition
        logger.info(f"Stored assertion_condition for TIA: {assertion_condition}")

    # Seed lists with empty records for each step's output
    for step in ["IR", "MFP"]:
        states.function.append(ReferenceRecordLite(step_name=step))
    for step in ["MVP"]:
        states.values.append(ReferenceRecordLite(step_name=step))
    for step in ["TVA", "TIA"]:  # Added TIA to the list
        states.inference.append(ReferenceRecordLite(step_name=step))

    logger.info("Built and stored specs for creating a generic judgement function with assertion.")
    
    states.set_current_step("IWI")
    return states 