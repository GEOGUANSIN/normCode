import os
import sys
import logging
from typing import Any, Dict, List, Optional, Callable
from types import SimpleNamespace

# Ensure the project root is in the Python path so we can import from infra
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)  # Go up one level to project root
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from infra._core._inference import Inference, register_inference_sequence, setup_logging
from infra._core._concept import Concept
from dataclasses import dataclass, field
from infra._core._reference import Reference, cross_product, cross_action, element_action
from infra._states._imperative_states import States
from infra._states._common_states import BaseStates, SequenceStepSpecLite, SequenceSpecLite, ConceptInfoLite, ReferenceRecordLite

# MFP-related imports from _syntax
from infra._agent._models._model_runner import ModelSequenceRunner
from infra._states._model_state import (
    ModelEnvSpecLite,
    ModelSequenceSpecLite,
    ModelStepSpecLite,
    ToolSpecLite,
    AffordanceSpecLite,
    MetaValue,
)
from infra._agent._models._prompt import PromptTool

# Directly import imperative steps from their files
from infra._agent._steps.imperative._iwi import input_working_interpretation as IWI
from infra._agent._steps.imperative._ir import input_references as IR
from infra._agent._steps.imperative._mfp import model_function_perception as MFP
from infra._agent._steps.imperative._mvp import memory_value_perception as MVP
from infra._agent._steps.imperative._tva import tool_value_actuation as TVA
from infra._agent._steps.imperative._tip import tool_inference_perception as TIP
from infra._agent._steps.imperative._mia import memory_inference_actuation as MIA
from infra._agent._steps.imperative._or import output_reference as OR
from infra._agent._steps.imperative._owi import output_working_interpretation as OWI


# --- New Body Class for Tools ---
class Body:
	def __init__(self) -> None:
		self.prompt = PromptTool()
		try:
			from infra._agent._models import LanguageModel as _LM
			self.llm = _LM("qwen-turbo-latest")
		except Exception:
			class _MockLM:
				def create_generation_function(self, prompt_template: str):
					from string import Template as _T
					def _fn(vars: dict | None = None) -> str:
						return _T(prompt_template).safe_substitute(vars or {})
					return _fn
				def generate(self, prompt: str, system_message: str = "") -> str:
					return f"GENERATED[{prompt}]"
			self.llm = _MockLM()
		
		# Add buffer and fn tools to match model_runner_real_demo.py
		class _BufferTool:
			def __init__(self) -> None:
				self._store: Dict[str, Any] = {}

			def write(self, record_name: str, new_record: Any) -> Any:
				self._store[record_name] = new_record
				return new_record

			def read(self, record_name: str) -> Any:
				return self._store.get(record_name)
		
		class _FnTool:
			def invoke(self, fn, vars: Dict[str, Any] | None = None) -> Any:
				return fn(vars or {})
		
		self.buffer = _BufferTool()
		self.fn = _FnTool()


# --- State Models (based on simple_sequence_runner.py) ---

# The States class is now imported directly from _states.imperative_states
# class States(BaseStates):
#     """State container for the imperative sequence."""
#     def __init__(self) -> None:
#         super().__init__()
#         self.sequence_state.sequence = [
#                 SequenceStepSpecLite(step_name="IWI"),
#                 SequenceStepSpecLite(step_name="IR"),
#                 SequenceStepSpecLite(step_name="MFP"),
#                 SequenceStepSpecLite(step_name="MVP"),
#                 SequenceStepSpecLite(step_name="TVA"),
#                 SequenceStepSpecLite(step_name="TIP"),
#                 SequenceStepSpecLite(step_name="MIA"),
#                 SequenceStepSpecLite(step_name="OR"),
#                 SequenceStepSpecLite(step_name="OWI"),
#             ]
#         self.body: Body | None = None
#         self.mfp_env_spec: ModelEnvSpecLite | None = None
#         self.mfp_sequence_spec: ModelSequenceSpecLite | None = None
#         self.value_order: Dict[str, Any] = field(default_factory=dict)

#     def set_current_step(self, name: str) -> None:
#         self.sequence_state.current_step = name

#     def get_reference(self, category: str, step_name: str) -> Reference | None:
#         """Helper to get a reference from a specific category and step."""
#         cat_list = getattr(self, category, [])
#         for record in cat_list:
#             if record.step_name == step_name:
#                 return record.reference
#         return None

#     def set_reference(self, category: str, step_name: str, ref: Reference) -> None:
#         """Helper to set a reference in a specific category and step."""
#         cat_list = getattr(self, category, [])
#         for record in cat_list:
#             if record.step_name == step_name:
#                 record.reference = ref.copy()
#                 return
#         # If not found, append a new record
#         cat_list.append(ReferenceRecordLite(step_name=step_name, reference=ref.copy())) 


# --- Imperative Step Implementations ---

def input_working_interpretation(
	inference: Inference, 
	states: States, 
	body: Body, 
	working_interpretation: Dict[str, Any] | None = None
) -> States:
	"""Initialize states with tools, specs, and placeholder records."""
	# Store the body containing tools
	states.body = body
	
	# Extract and store value_order directly
	ir_func_record = next((f for f in states.function if f.step_name == "IR"), None)
	func_name = ir_func_record.concept.name if ir_func_record and ir_func_record.concept else ""
	states.value_order = (working_interpretation or {}).get(func_name, {}).get("value_order", {})

	# Build and store MFP specs
	env_spec, sequence_spec = _build_mfp_env_and_sequence_from_wi(working_interpretation)
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


def input_references(inference: Inference, states: States) -> States:
	"""Populate references and concept info into the state from the inference instance."""
	# Simplified from simple_sequence_runner, as we just need the raw concepts for now.
	# The working_interpretation will drive which concepts are used where.
	if inference.function_concept:
		states.function[0].concept = ConceptInfoLite(
			id=inference.function_concept.id, name=inference.function_concept.name, type=inference.function_concept.type,
			context=inference.function_concept.context, axis_name=inference.function_concept.axis_name
		)
		states.function[0].reference = inference.function_concept.reference.copy()
	
	# Store the concept_to_infer in the 'inference' record for the IR step.
	if inference.concept_to_infer:
		ir_inference_record = next((r for r in states.inference if r.step_name == "IR"), None)
		if ir_inference_record:
			ir_inference_record.concept = ConceptInfoLite(id=inference.concept_to_infer.id,name=inference.concept_to_infer.name,type=inference.concept_to_infer.type,context=inference.concept_to_infer.context,axis_name=inference.concept_to_infer.axis_name)

	for vc in inference.value_concepts or []:
		states.values.append(
			ReferenceRecordLite(
				step_name="IR",
				concept=ConceptInfoLite(id=vc.id, name=vc.name, type=vc.type, context=vc.context, axis_name=vc.axis_name),
				reference=vc.reference.copy()
			)
		)
	
	states.set_current_step("IR")
	logging.debug(f"IR completed. Function state: {states.function}")
	logging.debug(f"IR completed. Values state: {states.values}")
	return states


def model_function_perception(states: States) -> States:
	"""Execute a model sequence to derive a function."""
	# Specs and body are now retrieved from the states object, prepared during IWI.
	sequence_spec = states.mfp_sequence_spec
	
	# The `ModelSequenceRunner` needs an object with `body` and `function` attributes.
	# We create a temporary proxy that pulls these from our `States` object for clarity.
	class _MfpStateProxy:
		def __init__(self, s: States):
			self.body = s.body
			
			ir_func_record = next((f for f in s.function if f.step_name == "IR"), None)
			ir_func_concept = ir_func_record.concept if ir_func_record else None
			self.function = SimpleNamespace(concept=ir_func_concept)

			ir_inference_record = next((r for r in s.inference if r.step_name == "IR"), None)
			ir_inference_concept = ir_inference_record.concept if ir_inference_record else None
			self.inference = SimpleNamespace(concept=ir_inference_concept)

	mfp_states_proxy = _MfpStateProxy(states)
	
	# Run the sequence
	if sequence_spec:
		meta = ModelSequenceRunner(mfp_states_proxy, sequence_spec).run()
		# The result of MFP is a callable function. We wrap it in a Reference.
		instruction_fn = meta.get("instruction_fn") # This key comes from your sequence spec
		if instruction_fn:
			ref = Reference(axes=["f"], shape=(1,))
			ref.set(instruction_fn, f=0)
			states.set_reference("function", "MFP", ref)

	states.set_current_step("MFP")
	logging.debug(f"MFP completed. Function state after model run: {states.function}")
	return states


def memory_value_perception(states: States) -> States:
	"""Order and cross-product value references based on working_configuration."""
	
	ir_func_record = next((f for f in states.function if f.step_name == "IR"), None)
	func_name = ir_func_record.concept.name if ir_func_record and ir_func_record.concept else ""
	
	value_order = states.value_order
	
	name_to_ref: Dict[str, Reference] = {
		v.concept.name: v.reference
		for v in states.values
		if v.step_name == "IR" and v.concept and v.reference
	}
	
	ordered_refs: List[Reference] = []
	ordered_names: List[str] = []
	if value_order:
		sorted_items = sorted(value_order.items(), key=lambda item: item[1])
		for name, _ in sorted_items:
			if name in name_to_ref:
				ordered_refs.append(name_to_ref[name])
				ordered_names.append(name)
	else:
		# Fallback if no order is specified
		for name, ref in name_to_ref.items():
			ordered_refs.append(ref)
			ordered_names.append(name)

	if ordered_refs:
		# Step 1: Cross product to get lists of values.
		crossed_ref = cross_product(ordered_refs)
		
		# Step 2: Use element_action to convert lists to dicts with generic keys.
		# The keys "input_1", "input_2", etc. match the prompt templates.
		def list_to_dict(values_list: List[Any]) -> Dict[str, Any]:
			"""Creates a dict with keys like 'input_1', 'input_2'."""
			return {f"input_{i+1}": val for i, val in enumerate(values_list)}

		dict_ref = element_action(list_to_dict, [crossed_ref])
		states.set_reference("values", "MVP", dict_ref)

	states.set_current_step("MVP")
	logging.debug(f"MVP completed. Values state after cross-product and dict conversion: {states.values}")
	return states


def tool_value_actuation(states: States) -> States:
	"""Apply the function from MFP to the values from MVP."""
	func_ref = states.get_reference("function", "MFP")
	values_ref = states.get_reference("values", "MVP")

	if func_ref and values_ref:
		# The function is stored as a callable in the reference tensor
		func_callable = func_ref.get(f=0)
		if func_callable and isinstance(func_callable, Callable):
			# Wrap the generation function to ensure its output is a list,
			# as required by the `cross_action` function.
			def _list_wrapper_fn(*args, **kwargs):
				result = func_callable(*args, **kwargs)
				return result if isinstance(result, list) else [result]

			# Create a new reference for the wrapped function to avoid side effects.
			wrapped_func_ref = func_ref.copy()
			wrapped_func_ref.set(_list_wrapper_fn, f=0)

			applied_ref = cross_action(wrapped_func_ref, values_ref, "result")
			states.set_reference("inference", "TVA", applied_ref)
	
	states.set_current_step("TVA")
	logging.debug(f"TVA completed. Inference state after actuation: {states.inference}")
	return states


def tool_inference_perception(states: States) -> States:
	"""Pass-through from TVA for this demo."""
	tva_ref = states.get_reference("inference", "TVA")
	if tva_ref:
		states.set_reference("inference", "TIP", tva_ref)
	states.set_current_step("TIP")
	logging.debug(f"TIP completed. Inference state: {states.inference}")
	return states


def memory_inference_actuation(states: States) -> States:
	"""Wrap the result in the normcode wrapper %()."""
	tip_ref = states.get_reference("inference", "TIP")
	if tip_ref:
		def wrap_element(element: Any) -> Any:
			# The element from cross_action is a list; we want to wrap the first item.
			value_to_wrap = element[0] if isinstance(element, list) and element else element
			return f"%({value_to_wrap})"
		
		wrapped_ref = element_action(wrap_element, [tip_ref])
		states.set_reference("inference", "MIA", wrapped_ref)

	states.set_current_step("MIA")
	logging.debug(f"MIA completed. Inference state after wrapping: {states.inference}")
	return states


def output_reference(states: States) -> States:
	"""Finalize the output reference."""
	mia_ref = states.get_reference("inference", "MIA")
	if mia_ref:
		states.set_reference("inference", "OR", mia_ref)
	states.set_current_step("OR")
	logging.debug(f"OR completed. Final inference state: {states.inference}")
	return states


def output_working_interpretation(states: States) -> States:
	"""No-op finalization for demo."""
	states.set_current_step("OWI")
	logging.debug("OWI completed.")
	return states

# --- New Logging Function ---
def log_states_progress(states: States, step_name: str, step_filter: str | None = None):
    logger = logging.getLogger(__name__)
    logger.info(f"\n--- States after {step_name} (Filtered by: {step_filter if step_filter else 'None'}) ---")
    logger.info(f"Current Step: {states.sequence_state.current_step}")
    
    def _log_record_list(label: str, record_list: List[ReferenceRecordLite]):
        logger.info(f"{label}:")
        filtered_records = [item for item in record_list if step_filter is None or item.step_name == step_filter]
        if not filtered_records:
            logger.info("  (Empty or no matching records for filter)")
            return
        for item in filtered_records:
            logger.info(f"  Step Name: {item.step_name}")
            if item.concept:
                logger.info(f"    Concept ID: {item.concept.id}, Name: {item.concept.name}, Type: {item.concept.type}, Context: {item.concept.context}, Axis: {item.concept.axis_name}")
            if item.reference and isinstance(item.reference, Reference):
                logger.info(f"    Reference Axes: {item.reference.axes}")
                logger.info(f"    Reference Shape: {item.reference.shape}")
                logger.info(f"    Reference Tensor: {item.reference.tensor}")
            if item.model:
                logger.info(f"    Model: {item.model}")

    _log_record_list("Function", states.function)
    _log_record_list("Values", states.values)
    _log_record_list("Context", states.context)
    _log_record_list("Inference", states.inference)

    logger.info("-----------------------------------")


# --- MFP Env/Sequence Builder ---

def _build_mfp_env_and_sequence_from_wi(working_interpretation: Dict[str, Any] | None = None) -> tuple[ModelEnvSpecLite, ModelSequenceSpecLite]:
	"""Builds the MFP environment and sequence spec, matching model_runner_real_demo.py."""
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
				params={"template_name": "imperative_translate"},
				result_key="imperative_template",
			),
			ModelStepSpecLite(
				step_index=2,
				affordance="prompt.render",
				params={
					"template_name": "imperative_translate",
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
				params={"template_name": "instruction"},
				result_key="instruction_template",
			),
			ModelStepSpecLite(
				step_index=5,
				affordance="prompt.render",
				params={
					"template_name": "instruction",
					"variables": {"input": MetaValue("nl_normcode_raw")},
				},
				result_key="instruction_prompt",
			),
			# 4) Create generation function from instruction prompt
			ModelStepSpecLite(
				step_index=6,
				affordance="llm.create_generation_function",
				params={"prompt_template": MetaValue("instruction_prompt")},
				result_key="instruction_fn",
			),
		]
	)
	return env_spec, sequence_spec


# --- Imperative Sequence Runner ---

@register_inference_sequence("imperative_v2")
def imperative_v2(self: Inference, input_data: Dict[str, Any] | None = None) -> States:
    """New imperative sequence runner."""
    states = States()
    working_interpretation = (input_data or {}).get("working_interpretation")
    body = Body()  # Create tools body before the sequence

    # IWI
    states = IWI(
        self, states, body=body, working_interpretation=working_interpretation
    )
    log_states_progress(states, "IWI", "IWI")
    # IR
    states = IR(self, states)
    log_states_progress(states, "IR", "IR")
    # MFP
    states = MFP(states)
    log_states_progress(states, "MFP", "MFP")
    # MVP
    states = MVP(states)
    log_states_progress(states, "MVP", "MVP")
    # TVA
    states = TVA(states)
    log_states_progress(states, "TVA", "TVA")
    # TIP
    states = TIP(states)
    log_states_progress(states, "TIP", "TIP")
    # MIA
    states = MIA(states)
    log_states_progress(states, "MIA", "MIA")
    # OR
    states = OR(states)
    log_states_progress(states, "OR", "OR")  # Show only OR reference
    # OWI
    states = OWI(states)
    log_states_progress(states, "OWI", "OWI")

    return states


# --- Demo Setup ---

def _build_demo_concepts() -> tuple[Concept, List[Concept], Concept]:
    logger = logging.getLogger(__name__)
    logger.info("Building demo concepts")

    ref_a = Reference(axes=["a"], shape=(1,))
    ref_a.set(2, a=0)
    logger.info(f"ref_a: {ref_a.tensor}")
    concept_a = Concept(name="A", context="a", reference=ref_a, type="{}")

    ref_b = Reference(axes=["b"], shape=(1,))
    ref_b.set(3, b=0)
    logger.info(f"ref_b: {ref_b.tensor}")
    concept_b = Concept(name="B", context="b", reference=ref_b, type="{}")

    # Function concept is now just a placeholder for the normcode string
    ref_f = Reference(axes=["f"], shape=(1,))
    ref_f.set("::({1}<$({number})%_> add {2}<$({number})%_>)", f=0)
    function_concept = Concept(name="::({1}<$({number})%_> add {2}<$({number})%_>)", context="adding number 1 and 2", type="::", reference=ref_f)
    logger.info(f"ref_f: {ref_f.tensor}")

    concept_to_infer = Concept(name="result", context="result", type="{}")
    return concept_to_infer, [concept_a, concept_b], function_concept


def _build_demo_working_interpretation() -> Dict[str, Any]:
	return {
		"sum": {
			"value_order": {"A": 0, "B": 1}
		}
	}


# --- Main Execution ---

def run_imperative_sequence() -> States:
	setup_logging(logging.DEBUG)

	concept_to_infer, value_concepts, function_concept = _build_demo_concepts()

	inference = Inference(
		"imperative_v2",
		concept_to_infer,
		value_concepts,
		function_concept,
	)

	# The new runner is self-contained and doesn't need explicit step registration here.
	
	states = inference.execute(input_data={
		"working_interpretation": _build_demo_working_interpretation()
	})

	final_ref = states.get_reference("inference", "OR")
	if isinstance(final_ref, Reference):
		logging.getLogger(__name__).info("Final Output (OR):")
		logging.getLogger(__name__).info(f"\tAxes: {final_ref.axes}")
		logging.getLogger(__name__).info(f"\tShape: {final_ref.shape}")
		logging.getLogger(__name__).info(f"\tTensor: {final_ref.tensor}")
		# Also print to be sure we see it
		print("--- Final Output (OR) ---")
		print(f"Axes: {final_ref.axes}")
		print(f"Shape: {final_ref.shape}")
		print(f"Tensor: {final_ref.tensor}")
	
	return states


if __name__ == "__main__":
	run_imperative_sequence() 