from __future__ import annotations
from typing import Any, Dict

# Import spec dataclasses and runner with fallback for direct script execution
try:
	from .model_state import (
		AffordanceSpecLite,
		ToolSpecLite,
		ModelEnvSpecLite,
		ModelStepSpecLite,
		ModelSequenceSpecLite,
		MetaValue,
		AffordanceValue,
	)
	from ._model_runner import ModelEnv, ModelSequenceRunner
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	sys.path.insert(0, str(here))
	from model_state import (  # type: ignore
		AffordanceSpecLite,
		ToolSpecLite,
		ModelEnvSpecLite,
		ModelStepSpecLite,
		ModelSequenceSpecLite,
		MetaValue,
		AffordanceValue,
	)
	from _model_runner import ModelEnv, ModelSequenceRunner  # type: ignore


# ---- Mock tools and states ---------------------------------------------------
class MockPrompt:
	def __init__(self) -> None:
		self._templates: Dict[str, str] = {
			"translation": "Translate concept to natural name: {output}",
			"instruction_with_buffer_record": "Use record '{record}' to act on imperative: {impmerative}",
		}

	def load(self, prompt_name: str) -> str:
		return self._templates[prompt_name]

	def substitute(self, prompt_template: str, **variables: Any) -> str:
		try:
			return prompt_template.format(**variables)
		except Exception:
			inner = variables.get("variables", {})
			return prompt_template.format(**inner)


class MockLLM:
	def generate(self, prompt: str) -> str:
		return f"GENERATED[{prompt}]"

	def create_generation_function(self, prompt_template: str):
		def _generate_with(vars: Dict[str, Any] | None = None) -> str:
			vars = vars or {}
			return prompt_template.format(**vars) if vars else prompt_template
		return _generate_with

	def expand_generation_function(self, base_generation_function, expansion_function, expansion_params: Dict[str, Any] | None = None):
		expansion_params = dict(expansion_params or {})
		def _expanded(vars: Dict[str, Any] | None = None) -> Any:
			base_out = base_generation_function(vars or {})
			params = {**expansion_params, "new_record": base_out}
			return expansion_function(params)
		return _expanded


class MockBuffer:
	def __init__(self) -> None:
		self._store: Dict[str, Any] = {}

	def write(self, record_name: str, new_record: Any) -> Any:
		self._store[record_name] = new_record
		return new_record

	def read(self, record_name: str) -> Any:
		return self._store.get(record_name)


class MockStates:
	class Function:
		class Concept:
			def __init__(self) -> None:
				self.name = "ConceptX"
		def __init__(self) -> None:
			self.concept = MockStates.Function.Concept()
			self.buffer_record_name = "rec1"

	class Body:
		def __init__(self) -> None:
			self.prompt = MockPrompt()
			self.llm = MockLLM()
			self.buffer = MockBuffer()

	def __init__(self) -> None:
		self.body = MockStates.Body()
		self.function = MockStates.Function()


# ---- Build env spec and sequence --------------------------------------------

env_spec = ModelEnvSpecLite(
	model=ToolSpecLite(
		tool_name="llm",
		affordances=[
			AffordanceSpecLite(
				affordance_name="generate",
				call_code="result = tool.generate(params['prompt'])",
			),
			AffordanceSpecLite(
				affordance_name="create_generation_function",
				call_code="result = tool.create_generation_function(params['prompt_template'])",
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
				affordance_name="load",
				call_code="result = tool.load(params['prompt_name'])",
			),
			AffordanceSpecLite(
				affordance_name="substitute",
				call_code="result = tool.substitute(params['prompt_template'], **params.get('variables', {}))",
			),
		]
	),
	tools=[
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
		)
	]
)

sequence_spec = ModelSequenceSpecLite(
	env=env_spec,
	steps=[
		ModelStepSpecLite(
			step_index=1,
			affordance="prompt.load",
			params={"prompt_name": "translation"},
			result_key="translation_prompt_template",
		),
		ModelStepSpecLite(
			step_index=2,
			affordance="prompt.substitute",
			params={
				"prompt_template": MetaValue("translation_prompt_template"),
				"variables": {"output": MetaValue("states.function.concept.name")},
			},
			result_key="translation_prompt",
		),
		ModelStepSpecLite(
			step_index=3,
			affordance="llm.generate",
			params={"prompt": MetaValue("translation_prompt")},
			result_key="natural_concept_name",
		),
		ModelStepSpecLite(
			step_index=4,
			affordance="prompt.load",
			params={"prompt_name": "instruction_with_buffer_record"},
			result_key="instruction_prompt_template",
		),
		ModelStepSpecLite(
			step_index=5,
			affordance="buffer.write",
			params={"record_name": MetaValue("states.function.buffer_record_name"), "new_record": "seed"},
			result_key=None,
		),
		ModelStepSpecLite(
			step_index=6,
			affordance="buffer.read",
			params={"record_name": MetaValue("states.function.buffer_record_name")},
			result_key="buffer_record",
		),
		ModelStepSpecLite(
			step_index=7,
			affordance="prompt.substitute",
			params={
				"prompt_template": MetaValue("instruction_prompt_template"),
				"variables": {"record": MetaValue("buffer_record"), "impmerative": MetaValue("natural_concept_name")},
			},
			result_key="instruction_prompt_lambda_template",
		),
		ModelStepSpecLite(
			step_index=8,
			affordance="llm.create_generation_function",
			params={"prompt_template": MetaValue("instruction_prompt_lambda_template")},
			result_key="mere_generation_function",
		),
		ModelStepSpecLite(
			step_index=9,
			affordance="llm.expand_generation_function",
			params={
				"base_generation_function": MetaValue("mere_generation_function"),
				"expansion_function": AffordanceValue("buffer.write"),
				"expansion_params": {"record_name": MetaValue("states.function.buffer_record_name")},
			},
			result_key="expanded_generation_function",
		),
	]
)


def run_demo() -> None:
	states = MockStates()
	runner = ModelSequenceRunner(states, sequence_spec)
	meta = runner.run()

	print("Meta store after run:")
	for k, v in meta.items():
		preview = v
		if callable(v):
			preview = f"<callable {v.__name__ if hasattr(v, '__name__') else 'fn'}>"
		print(f"- {k}: {preview}")

	# Use the generation functions
	gen_fn = meta["mere_generation_function"]
	print("gen_fn():", gen_fn({}))
	expanded_fn = meta["expanded_generation_function"]
	print("expanded_fn():", expanded_fn({}))
	# Verify buffer write happened
	print("buffer out:", runner.env.execute("buffer.read", {"record_name": states.function.buffer_record_name}))


if __name__ == "__main__":
	run_demo() 