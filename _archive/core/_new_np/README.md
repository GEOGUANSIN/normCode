## NormCode New NP (Neural Processing) Framework

This module provides the new NP layer for NormCode: a compact framework for composing formal reasoning, data references, and LLM-powered actuation into executable inference sequences.

### Aims
- Provide a minimal, composable abstraction to build intelligent agent flows around NormCode syntax
- Unify three classes of concepts — syntactical, semantical, and inferential — into a consistent API
- Model data as multi-axis references that support irregular shapes and safe missing values
- Orchestrate reasoning steps (perception → actuation → memory → return) as named sequences
- Integrate LLMs via prompt templates for translation, validation, and generation
- Support grouping and quantification patterns, and robust nested-data combination generation

---

## Architecture at a glance

- Core types
  - `core/_new_np/_concept.py` → `Concept` and `CONCEPT_TYPES` (syntactical/semantical/inferential)
  - `core/_new_np/_reference.py` → `Reference` (tensor-like nested data with axes/shape/skip)
- Inference orchestration
  - `core/_new_np/_inference.py` → `Inference` class with per-instance step registry and dynamic sequence dispatch; `register_inference_sequence`
  - `core/_new_np/_agentframe.py` → `AgentFrame` wires demo sequences (`judgement`, `imperative`) and binds concrete step implementations
- Methods library (step implementations and utilities)
  - `core/_new_np/_methods/_demo.py` → imperative sequence steps (IWC/MVP/CP/AP/PTA/ASP/MA/RR/OWC)
  - `core/_new_np/_methods/_grouping_demo.py` → `Grouper` for `and_in`, `or_across`, … and formal/syntactical perception helpers
  - `core/_new_np/_methods/_quantification_demo.py` → quantification expression parser and demo flow
  - `core/_new_np/_methods/_util_nested_list.py` → nested-data combinations, extraction, filtering
- LLM integration
  - `core/_new_np/_language_models.py` → `LanguageModel` with prompt loader and chat API wrapper
  - Prompts in `core/_new_np/prompts/`: `imperative_translate.txt`, `instruction.txt`, `instruction_validation.txt`
- Public API and helpers
  - `core/_new_np/__init__.py` exposes `Concept`, `Reference`, `Inference`, `AgentFrame`, `LanguageModel`, and convenience creators

---

## Core types

### Concept
File: `core/_new_np/_concept.py`

- Encapsulates a named concept with a type and optional `Reference`
- Type classes:
  - Syntactical (e.g., `@by`, `$=`, `&in`, `*every`)
  - Semantical (e.g., `{}`, `::`, `<>`)
  - Inferential (e.g., `<=`, `<-`)
- Key API:
  - `Concept(name, context="", axis_name=None, reference=None, type="{}")`
  - `is_syntactical()`, `is_semantical()`, `get_type_class()`
  - `comprehension()` returns a dict snapshot

### Reference
File: `core/_new_np/_reference.py`

- Multi-axis, tensor-like nested data structure that tolerates irregular shapes
- Tracks `axes`, `shape`, and a `skip_value` (default `@#SKIP#@`) for padding/missing
- Highlights:
  - `Reference(axes, shape, initial_value=None, skip_value="@#SKIP#@")`
  - `Reference.from_data(data, axis_names=None)` for auto-discovery of axes/shape
  - `.tensor` property auto-pads to the maximum irregular shape
  - `.get(...)` / `.set(...)` with axis-aware indexing and skip-aware semantics
  - Utilities (imported in modules): `cross_product`, `element_action`, `cross_action`

---

## Inference orchestration

### Inference
File: `core/_new_np/_inference.py`

- An `Inference` instance binds:
  - `concept_to_infer: Concept`
  - `value_concepts: list[Concept]`
  - `function_concept: Concept`
  - Optional `context_concepts`
- Per-instance step registry through `@inference_instance.register_step("STEP")`
- `execute()` dynamically discovers and calls the method matching `sequence_name`
- Class-level sequence registrar: `@register_inference_sequence("imperative")` attaches a function as `Inference.imperative`

### AgentFrame
File: `core/_new_np/_agentframe.py`

- Wires demo sequences and assigns concrete step functions
- Demo sequences:
  - `judgement`: `(IWC-[(MVP-CP)-[PA]-MA)]-RR-OWC)`
  - `imperative`: `(IWC-[(MVP-CP)-[AP-PTA-ASP]-MA)]-RR-OWC)`
- Uses `_methods._demo.all_demo_methods("imperative")` to inject implementations for the imperative pipeline
- Utility helpers: `strip_element_wrapper`, `wrap_element_wrapper`

---

## Methods and utilities

### Imperative demo methods
File: `core/_new_np/_methods/_demo.py`

- Loads prompts using `LanguageModel`
- Translates NormCode imperatives to NL templates, fills inputs, and generates outputs
- Key internal helpers:
  - `_create_activation_function(...)` → translate imperative, then instruct/validate
  - `_create_actuator_function(...)` → multi-input generation function based on NL template
  - `_raw_element_process(...)` → robustly parse model outputs (list, code block, bracketed list, or string)

### Grouping
File: `core/_new_np/_methods/_grouping_demo.py`

- `Grouper` abstracts NormCode grouping patterns as reference operations:
  - `and_in(references, annotation_list=None, slice_axes=None, template=None)`
  - `or_across(references, slice_axes=None, template=None)`
  - Plus helpers to flatten/annotate and bridge to formal/syntactical actuation
- Works directly over `Reference` objects, supports optional templating via `string.Template`

### Quantification
File: `core/_new_np/_methods/_quantification_demo.py`

- Parses quantification expressions like:
  - `*every({loop})%:[{view_axis1};{view_axis2}].[{concept1}?;{concept2}?]@(2)^(concept<*1>)`
- Provides demonstration flows to project parsed structures onto reference operations

### Nested data processing
Files:
- `core/_new_np/_methods/_util_nested_list.py`
- `core/_new_np/_methods/README_nested_data_processing.md`

- Generates all valid combinations from nested inputs, with:
  - `get_combinations_dict_and_indices(nested_data, filter_constraints=None, extraction_guide=None)`
  - `extraction_guide` to pull values from dict elements and flatten deeply nested lists
  - `filter_constraints` like `[[0, 1]]` to keep sub-indices aligned across multiple rank-1 items

---

## LLM integration

File: `core/_new_np/_language_models.py`

- `LanguageModel(model_name, settings_path)` loads API settings and wraps a chat-completions client
- Prompt templates live in `core/_new_np/prompts/` and are loaded via `load_prompt_template(name)`
- Two main usage styles:
  - `run_prompt(template_name, **kwargs)` for template-based prompting
  - `generate(prompt, system_message=..., response_format=...)` for direct prompting

Prompts:
- `imperative_translate.txt`: map NormCode imperative to NL template using `$input_1`, `$output`, etc.
- `instruction.txt`: turns an NL template into a single executable instruction
- `instruction_validation.txt`: lightweight checker for instruction/output alignment

---

## Minimal example

```python
from core._new_np import Concept, Inference, AgentFrame, LanguageModel
from core._new_np import Reference

# Data as references
inputs_ref = Reference(axes=['X'], shape=(2,), initial_value=0)
inputs_ref.tensor = ['5', '2']

# Concepts
value_concepts = [Concept('{1}', reference=inputs_ref), Concept('{2}', reference=inputs_ref)]
function_concept = Concept('::({1}<$({number})%_> add {2}<$({number})%_>)', type='::')
concept_to_infer = Concept('{result}?', type='{}?')

# LLM and agent
llm = LanguageModel('qwen-turbo-latest')
agent = AgentFrame('demo', llm=llm)

# Inference instance and configuration
inf = Inference('imperative', concept_to_infer, value_concepts, function_concept)
agent.configure(inf, 'imperative')

# Execute
answer = inf.execute({})
print(answer.reference.get_tensor(ignore_skip=True))
```

---

## Examples

- Grouping and multi-axis demos: `core/_new_np/examples/normcode_grouping.py`
- Nested data combinations: `core/_new_np/examples/demo_nested_list.py`
- Quantifier usage: `core/_new_np/examples/example_quantifier.py` (and `core/_new_np/example_quantifier.py`)
- Contrastive math examples: `core/_new_np/example_math_contrast.py`

---

## Extending the framework

- New sequences
  - Define a function and register: `@register_inference_sequence("my_sequence")`
  - Provide step implementations via `@inference_instance.register_step("STEP")`
  - Wire inside `AgentFrame.configure(...)`

- New prompts
  - Add templates under `core/_new_np/prompts/` and load via `LanguageModel.load_prompt_template`

- New grouping/quantification patterns
  - Add methods to `Grouper` or a sibling module under `core/_new_np/_methods/`

---

## Notes and current status

- `judgement_translate.txt` exists but is intentionally empty; judgement demos focus on the step skeleton
- The module favors clarity and explicitness over brevity; debug logging is enabled by default in demos
- The `Reference` class prioritizes safe irregular-shape handling via automatic padding and a configurable skip token 