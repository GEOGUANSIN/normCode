## New NP Sequence Comparison

This document compares four sequences available in `core/_new_np`:
- Imperative (v1) — demo
- Imperative (v2) — workspace/nested-data
- Grouping
- Quantification

### Quick matrix

| Sequence | Module(s) | How it’s wired | Step order (high-level) | Special features |
|---|---|---|---|---|
| Imperative v1 | `_agentframe.py`, `_methods/_demo.py` | Registered as `Inference.imperative` and configured by `AgentFrame('demo')` | IWC → MVP → CP → AP → PTA → ASP → MA → RR → OWC | LLM translation of imperatives; simple multi-input prompting |
| Imperative v2 | `_methods/_workspace_demo.py`, `_methods/_util_nested_list.py` | Drop-in step set for `imperative` with workspace config | IWC → MVP → CP → AP → PTA → ASP → MA → RR → OWC | Nested input combination generation; relation extraction; filter constraints; workspace context |
| Grouping | `_methods/_grouping_demo.py` | Provided via `all_grouping_demo_methods('grouping')` (demo) | IWC → MVP → FAP → SPA → MA → RR → OWC | `Grouper` ops: `and_in`, `or_across`; formal and syntactical perception |
| Quantification | `_methods/_quantification_demo.py` | Provided via `all_quantification_demo_methods('quantification')` (demo) | IWC → OWC → FAP → GP → CVP → AVP → PTA → GA → RR | Quantifier parser (`*every(...)` etc.) mapped to grouping/actuation |

Legend: IWC(Input Working Config), MVP(Memorized Values Perception), CP(Cross Perception), AP(Actuator Perception), PTA(On-Perception Tool Actuation), ASP(Action Spec Perception), MA(Memory Actuation), RR(Return Reference), OWC(Output Working Config), FAP(Formal Actuator Perception), SPA(Syntactical Perception Actuation), GP(Group Perception), CVP(Context Value Perception), AVP(Actuator Value Perception), GA(Grouping Actuation).

---

### Imperative (v1) — demo
- Files: `core/_new_np/_agentframe.py`, `core/_new_np/_methods/_demo.py`
- Wiring:
  - `AgentFrame._set_up_imperative_demo()` registers `Inference.imperative` with full 9-step pipeline.
  - `AgentFrame._configure_imperative_demo(...)` binds concrete step functions from `_methods/_demo.py`.
- Flow:
  1) IWC: select active working config
  2) MVP: fetch value concept references (with `%(... )` stripped)
  3) CP: `cross_product` of value references
  4) AP: translate NormCode imperative to NL template, prepare actuator
  5) PTA: apply actuator over crossed perception (`cross_action`)
  6) ASP: finalize action spec
  7) MA: wrap elements for storage
  8) RR: assign reference to answer concept
  9) OWC: finalize outputs
- LLM use: `imperative_translate.txt` → NL template; `instruction.txt` to generate outputs; optional validation.

### Imperative (v2) — workspace/nested-data
- Files: `core/_new_np/_methods/_workspace_demo.py`, `core/_new_np/_methods/_util_nested_list.py`
- Wiring: alternative step implementations for the same `imperative` sequence name; intended to be configured similarly to v1.
- Key differences vs v1:
  - Nested data: `_util_nested_list.get_combinations_dict_and_indices(...)` generates all input combinations from nested lists/dicts.
  - Relation extraction: optional `relation_extraction` with key guides to extract nested dict fields.
  - Filter constraints: keep sub-indices aligned across multiple inputs (e.g., `[[0,1]]`).
  - Workspace context: `_setup_workspace_context` + `_build_workspace_context` to append context/system messages per object.
  - Aggregation: multiple valued actuator prompts are concatenated before instruction generation.
- Flow remains IWC → MVP → CP → AP → PTA → ASP → MA → RR → OWC, but AP/PTA handle nested combinations and workspace.

### Grouping
- Files: `core/_new_np/_methods/_grouping_demo.py`
- Wiring: `all_grouping_demo_methods('grouping')` provides a demo sequence; can be bound to an `Inference` instance via `register_step` (not auto-wired in `AgentFrame`).
- Core capability: `Grouper` operating over `Reference` objects, implementing NormCode grouping patterns:
  - `and_in(references, slice_axes=None, template=None)`
  - `or_across(references, slice_axes=None, template=None)`
  - Utilities: flatten/annotate; bridge functions `formal_actuator_perception` and `syntatical_perception_actuation`.
- Typical flow: IWC → MVP → FAP (parse function concept into grouper op) → SPA (apply over perception refs) → MA → RR → OWC.

### Quantification
- Files: `core/_new_np/_methods/_quantification_demo.py`
- Wiring: `all_quantification_demo_methods('quantification')` provides a demo sequence; to be bound via `register_step` as needed.
- Core capability: parse NormCode quantifiers and drive grouping/actuation:
  - Parser `_parse_normcode_quantification(expr)` extracts LoopBase, ViewAxis, ConceptToInfer, LoopIndex, InLoopConcept.
  - Steps map parsed parts into value/context perception and `Grouper`-based actuation.
- Flow (demo): IWC → OWC → FAP → GP → CVP → AVP → PTA → GA → RR.

---

### When to use which
- Use Imperative v1 for straightforward imperative actions with flat inputs and simple LLM prompting.
- Use Imperative v2 when inputs are nested or dict-rich, when you need extraction/filters, or you need workspace-aware context.
- Use Grouping when composing/transforming multi-axis references with logical grouping (`and_in`, `or_across`) possibly templated.
- Use Quantification when a NormCode expression with `*every`, view axes, in-loop concepts, or carryover needs to be executed over references.

### Notes
- Only `judgement` and `imperative` are auto-registered in `AgentFrame('demo')`. Grouping and Quantification provide complete step maps but require explicit binding on an `Inference` instance or a custom `AgentFrame` variant.
- All sequences rely on `Reference`’s axis/shape semantics and tolerate irregular tensors via skip padding. 