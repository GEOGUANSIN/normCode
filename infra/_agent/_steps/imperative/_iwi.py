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
	"""Builds the MFP environment and sequence spec, matching model_runner_real_demo.py."""
	# Determine which prompts to use based on whether the output is a relation
	if is_relation_output:
		instruction_prompt = "instruction_relation_with_thinking" if with_thinking else "inistruction_relation"
	else:
		instruction_prompt = "instruction" # Assuming a non-relation thinking prompt might exist
	
	translate_prompt = "imperative_relation_translate" if is_relation_output else "imperative_translate"
	
	# Determine which generation function to use
	generation_function_affordance = "llm.create_generation_function_thinking_json" if with_thinking else "llm.create_generation_function"


	env_spec = ModelEnvSpecLite(
		model=ToolSpecLite(
			tool_name="llm",
			affordances=[
				AffordanceSpecLite(
					affordance_name="generate",
					call_code="result = tool.generate(params['prompt'], system_message=params.get('system_message', ''))",
				),
				AffordanceSpecLite(
					affordance_name="create_generation_function",
					call_code="result = tool.create_generation_function(params['prompt_template'])",
				),
				AffordanceSpecLite(
					affordance_name="create_generation_function_thinking_json",
					call_code="result = tool.create_generation_function_thinking_json(params['prompt_template'])",
				),
				AffordanceSpecLite(
					affordance_name="expand_generation_function",
					call_code="result = tool.expand_generation_function(params['base_generation_function'], params['expansion_function'], params.get('expansion_params', {}))",
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
				AffordanceSpecLite(
					affordance_name="substitute",
					call_code="result = tool.substitute(params['template_name'], params.get('variables', {}))",
				),
			]
		),
		tools=[
			ToolSpecLite(
				tool_name="fn",
				affordances=[
					AffordanceSpecLite(
						affordance_name="invoke",
						call_code="result = tool.invoke(params['fn'], params.get('vars', {}))",
					),
				]
			),
			ToolSpecLite(
				tool_name="buffer",
				affordances=[
					AffordanceSpecLite(
						affordance_name="write",
						call_code="result = tool.write(params['record_name'], params['new_record'])",
					),
					AffordanceSpecLite(
						affordance_name="read",
						call_code="result = tool.read(params['record_name'])",
					),
				]
			),
		]
	)

	sequence_spec = ModelSequenceSpecLite(
		env=env_spec,
		steps=[
			# 1) Read and render imperative_translate with input_normcode
			ModelStepSpecLite(
				step_index=1,
				affordance="prompt.read",
				params={"template_name": translate_prompt},
				result_key="imperative_template",
			),
			ModelStepSpecLite(
				step_index=2,
				affordance="prompt.render",
				params={
					"template_name": translate_prompt,
					"variables": {
						"input_normcode": MetaValue("states.function.concept.name"),
						"output": MetaValue("states.inference.concept.name"),
					},
				},
				result_key="imperative_prompt",
			),
			# 2) Generate raw natural-language template from LLM
			ModelStepSpecLite(
				step_index=3,
				affordance="llm.generate",
				params={"prompt": MetaValue("imperative_prompt"), "system_message": ""},
				result_key="nl_normcode_raw",
			),
			# 3) Read and render instruction with the filled NL normcode
			ModelStepSpecLite(
				step_index=4,
				affordance="prompt.read",
				params={"template_name": instruction_prompt},
				result_key="instruction_template",
			),
			ModelStepSpecLite(
				step_index=5,
				affordance="prompt.render",
				params={
					"template_name": instruction_prompt,
					"variables": {"input": MetaValue("nl_normcode_raw")},
				},
				result_key="instruction_prompt",
			),
			# 4) Create generation function from instruction prompt
			ModelStepSpecLite(
				step_index=6,
				affordance=generation_function_affordance,
				params={"prompt_template": MetaValue("instruction_prompt")},
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
    """Initialize states with tools, specs, and placeholder records."""
    # Store the body containing tools
    states.body = body

    # Check for relation output and thinking flags and update state
    is_relation = (working_interpretation or {}).get("is_relation_output", False)
    with_thinking = (working_interpretation or {}).get("with_thinking", False)
    states.is_relation_output = is_relation
    # We might want to add with_thinking to states as well if other steps need it
    # states.with_thinking = with_thinking

    # Extract and store value_order directly
    ir_func_record = next((f for f in states.function if f.step_name == "IR"), None)
    func_name = ir_func_record.concept.name if ir_func_record and ir_func_record.concept else ""
    states.value_order = (working_interpretation or {}).get(func_name, {}).get("value_order", {})

    # Build and store MFP specs based on flags
    env_spec, sequence_spec = _build_mfp_env_and_sequence_from_wi(
        working_interpretation, 
        is_relation_output=is_relation,
        with_thinking=with_thinking
    )
    states.mfp_env_spec = env_spec
    states.mfp_sequence_spec = sequence_spec

    # Seed function/values/inference lists with empty records for each step
    # This ensures that set_reference has a record to populate.
    for step in ["IR", "MFP"]:
        states.function.append(ReferenceRecordLite(step_name=step))
    for step in ["IR", "MVP"]:
        states.values.append(ReferenceRecordLite(step_name=step))
    for step in ["IR", "TVA", "TIP", "MIA", "OR"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    states.set_current_step("IWI")
    logging.debug("IWI completed. State lists, tools, and MFP specs initialized.")
    return states 