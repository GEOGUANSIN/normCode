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


def _build_specs_for_python_execution(config: Dict[str, Any]) -> tuple[ModelEnvSpecLite, ModelSequenceSpecLite]:
    """
    Builds the specs to create the dynamic python execution function.
    """
    prompt_key = config.get("prompt_key", "prompt_location")
    script_key = config.get("script_key", "script_location")
    with_thinking = config.get("with_thinking", False)

    call_code = (
        "result = tool.create_python_generate_and_run_function("
        "prompt_key=params['prompt_key'], "
        "script_key=params['script_key'], "
        "with_thinking=params['with_thinking']"
        ")"
    )

    env_spec = ModelEnvSpecLite(
        model=ToolSpecLite(
            tool_name="llm",
            affordances=[
                AffordanceSpecLite(
                    affordance_name="create_python_generate_and_run_function",
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
                affordance="llm.create_python_generate_and_run_function",
                params={
                    "prompt_key": prompt_key,
                    "script_key": script_key,
                    "with_thinking": with_thinking,
                },
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
    IWI step for imperative_python.
    Builds and saves the specs for creating the dynamic python execution function.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Running IWI for imperative_python: Building specs for python execution.")

    states.body = body
    
    config = working_interpretation or {}

    # Build and save the specs for MFP to execute
    env_spec, sequence_spec = _build_specs_for_python_execution(config)
    states.mfp_env_spec = env_spec
    states.mfp_sequence_spec = sequence_spec
    
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

    # Seed lists with empty records for each step's output
    for step in ["MFP"]:
        states.function.append(ReferenceRecordLite(step_name=step))
    for step in ["MVP"]:
        states.values.append(ReferenceRecordLite(step_name=step))
    for step in ["TIP", "MIA"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    logger.info("Built and stored specs for creating a generic direct instruction function.")
    
    states.set_current_step("IWI")
    return states 