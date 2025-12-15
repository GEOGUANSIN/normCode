from typing import Any, Dict
import logging

# Forward-referencing type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from infra import Inference
    from infra._states._imperative_states import States
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


def _build_specs_for_input_function(config: Dict[str, Any]) -> tuple[ModelEnvSpecLite, ModelSequenceSpecLite]:
    """
    Builds the specs to create a user input function.
    Similar to imperative_direct but for user input instead of LLM generation.
    """
    prompt_key = config.get("prompt_key", "prompt_text")

    env_spec = ModelEnvSpecLite(
        tools=[
            ToolSpecLite(
                tool_name="user_input",
                affordances=[
                    AffordanceSpecLite(
                        affordance_name="create_input_function",
                        call_code="result = tool.create_input_function(prompt_key=params.get('prompt_key', 'prompt_text'))",
                    ),
                ]
            )
        ]
    )

    sequence_spec = ModelSequenceSpecLite(
        env=env_spec,
        steps=[
            ModelStepSpecLite(
                step_index=1,
                affordance="user_input.create_input_function",
                params={"prompt_key": prompt_key},
                result_key="input_fn"
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
    IWI step for imperative_input.
    Builds and saves the specs for creating a user input function in a later step.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Running IWI for imperative_input: Building specs for user input function.")

    states.body = body
    states.workspace = working_interpretation.get("workspace", {})
    flow_info = working_interpretation.get("flow_info", {})
    states.flow_index = flow_info.get("flow_index")
    
    config = working_interpretation or {}

    # Build and save the specs for MFP to execute
    env_spec, sequence_spec = _build_specs_for_input_function(config)
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

    # Seed lists with empty records for each step's output
    for step in ["IR", "MFP"]:
        states.function.append(ReferenceRecordLite(step_name=step))
    for step in ["IR", "MVP"]:
        states.values.append(ReferenceRecordLite(step_name=step))
    for step in ["TVA", "TIP", "MIA"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    logger.info("Built and stored specs for creating a user input function.")
    
    states.set_current_step("IWI")
    return states