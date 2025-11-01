from typing import Any, Dict
import logging

# Forward-referencing type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from infra import Inference
    from infra._states._judgement_direct_states import States
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


def _build_specs_for_generic_function(config: Dict[str, Any], with_thinking: bool = False) -> tuple[ModelEnvSpecLite, ModelSequenceSpecLite]:
    """
    Builds the specs to create a generic generation function that expects the template in its vars.
    """
    template_key = config.get("template_key", "prompt_template")

    if with_thinking:
        affordance_name = "create_generic_generation_function_with_thinking"
        call_code = "result = tool.create_generation_function_with_template_in_vars_with_thinking(template_key=params['template_key'])"
    else:
        affordance_name = "create_generic_generation_function"
        call_code = "result = tool.create_generation_function_with_template_in_vars(template_key=params['template_key'])"

    env_spec = ModelEnvSpecLite(
        model=ToolSpecLite(
            tool_name="llm",
            affordances=[
                AffordanceSpecLite(
                    affordance_name=affordance_name,
                    call_code=call_code,
                ),
            ]
        )
    )

    sequence_spec = ModelSequenceSpecLite(
        env=env_spec,
        steps=[
            ModelStepSpecLite(
                step_index=1,
                affordance=f"llm.{affordance_name}",
                params={"template_key": template_key},
                result_key="instruction_fn"
            )
        ]
    )
    return env_spec, sequence_spec


def input_working_interpretation(
    inference: "Inference", 
    states: "States", 
    body: "Body",
    working_interpretation: Dict[str, Any] | None = None,
) -> "States":
    """
    IWI step for judgement_direct.
    Builds and saves the specs for creating a generic generation function in a later step.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Running IWI for judgement_direct: Building specs for generic function.")

    states.body = body
    
    config = working_interpretation or {}

    with_thinking = config.get("with_thinking", False)

    # Build and save the specs for MFP to execute
    env_spec, sequence_spec = _build_specs_for_generic_function(config, with_thinking=with_thinking)
    states.mfp_env_spec = env_spec
    states.mfp_sequence_spec = sequence_spec
    
    # Set value_order and initial values for MVP
    states.value_order = config.get("value_order")
    values_dict = config.get("values", {})
    for key, value in values_dict.items():
        record = ReferenceRecordLite(
            step_name="IR",  # Use "IR" to be compatible with MVP
            concept=Concept(name=key),
            reference=Reference(data=[value])
        )
        states.values.append(record)
    
    # Set condition for TIP step
    states.condition = config.get("condition")

    # Seed lists with empty records for each step's output
    for step in ["IR", "MFP"]:
        states.function.append(ReferenceRecordLite(step_name=step))
    for step in ["IR", "MVP"]:
        states.values.append(ReferenceRecordLite(step_name=step))
    for step in ["IR", "TIP", "MIA", "OR"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    logger.info("Built and stored specs for creating a generic direct judgment function.")
    
    states.set_current_step("IWI")
    return states
