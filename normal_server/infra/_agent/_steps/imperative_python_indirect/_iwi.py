from typing import Any, Dict
import logging

from infra._core._inference import Inference
from infra._states._imperative_states import States
from infra._agent._body import Body
from infra._states._common_states import ReferenceRecordLite
from infra._states._model_state import (
	AffordanceSpecLite,
	ToolSpecLite,
	ModelEnvSpecLite,
	ModelStepSpecLite,
	ModelSequenceSpecLite,
	MetaValue,
)

def _build_mfp_env_and_sequence_from_wi(
    working_interpretation: Dict[str, Any] | None = None,
    is_relation_output: bool = False,
    with_thinking: bool = False
) -> tuple[ModelEnvSpecLite, ModelSequenceSpecLite]:
	"""Builds the MFP environment and sequence spec for the indirect imperative sequence."""
	# Determine which translation prompt to use based on the flags
	if is_relation_output:
		translate_prompt = "imperative_python_relation_thinking_translate" if with_thinking else "imperative_python_relation_translate"
	else:
		translate_prompt = "imperative_python_thinking_translate" if with_thinking else "imperative_python_translate"

	generation_function_affordance = "create_python_generate_and_run_function_from_prompt"

	env_spec = ModelEnvSpecLite(
		model=ToolSpecLite(
			tool_name="llm",
			affordances=[
				AffordanceSpecLite(
					affordance_name="generate",
					call_code="result = tool.generate(params['prompt'], system_message=params.get('system_message', ''))",
				),
				AffordanceSpecLite(
					affordance_name=generation_function_affordance,
					call_code="result = tool.create_python_generate_and_run_function_from_prompt(params['prompt_template'], with_thinking=params.get('with_thinking', False))",
				),
			]
		),
		prompt=ToolSpecLite(
			tool_name="prompt",
			affordances=[
				AffordanceSpecLite(
					affordance_name="read",
					call_code="result = tool.read(params['template_name'])",
				),
				AffordanceSpecLite(
					affordance_name="render",
					call_code="result = tool.render(params['template_name'], params.get('variables', {}))",
				),
			]
		),
		tools=[]
	)

	sequence_spec = ModelSequenceSpecLite(
		env=env_spec,
		steps=[
			# 1) Read the selected translation prompt template
			ModelStepSpecLite(
				step_index=1,
				affordance="prompt.read",
				params={"template_name": translate_prompt},
				result_key="translate_template",
			),
			# 2) Render the translation prompt with the high-level instruction
			ModelStepSpecLite(
				step_index=2,
				affordance="prompt.render",
				params={
					"template_name": translate_prompt,
					"variables": {
						"input_normcode": MetaValue("states.function.concept.name"),
					},
				},
				result_key="rendered_translate_prompt",
			),
			# 3) Use the LLM to generate the detailed instruction prompt
			ModelStepSpecLite(
				step_index=3,
				affordance="llm.generate",
				params={"prompt": MetaValue("rendered_translate_prompt"), "system_message": ""},
				result_key="detailed_instruction_prompt",
			),
			# 4) Create the final 'generate_and_run' function from the detailed prompt
			ModelStepSpecLite(
				step_index=4,
				affordance=f"llm.{generation_function_affordance}",
				params={
					"prompt_template": MetaValue("detailed_instruction_prompt"),
					"with_thinking": with_thinking,
				},
				result_key="instruction_fn",
			),
		]
	)
	return env_spec, sequence_spec



def input_working_interpretation(
    inference: Inference,
    states: States,
    body: Body,
    working_interpretation: Dict[str, Any] | None = None,
) -> States:
    """Initialize states with tools, specs, and placeholder records for the indirect sequence."""
    states.body = body
    states.workspace = working_interpretation.get("workspace", {})
    flow_info = working_interpretation.get("flow_info", {})
    states.flow_index = flow_info.get("flow_index")

    is_relation = (working_interpretation or {}).get("is_relation_output", False)
    with_thinking = (working_interpretation or {}).get("with_thinking", False)
    states.is_relation_output = is_relation

    states.value_order = (working_interpretation or {}).get("value_order", None)
    states.value_selectors = (working_interpretation or {}).get("value_selectors", None)

    env_spec, sequence_spec = _build_mfp_env_and_sequence_from_wi(
        working_interpretation,
        is_relation_output=is_relation,
        with_thinking=with_thinking
    )
    states.mfp_env_spec = env_spec
    states.mfp_sequence_spec = sequence_spec

    for step in ["IR", "MFP"]:
        states.function.append(ReferenceRecordLite(step_name=step))
    for step in ["IR", "MVP"]:
        states.values.append(ReferenceRecordLite(step_name=step))
    for step in ["IR", "TVA", "TIP", "MIA", "OR"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    states.set_current_step("IWI")
    logging.debug("IWI for imperative_python_indirect completed. MFP specs initialized.")
    return states
