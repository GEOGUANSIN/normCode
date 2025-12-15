
# NormCode Compilation Pipeline

This document describes the phases that transform a natural language idea into an executable NormCode plan.

---

## Overview

The compilation pipeline progressively formalizes intent into structure:

```
Natural Language → .ncds → .ncd (draft) → .ncd (enriched) → JSON Repos → Execution
                   ↑         ↑              ↑                ↑
               Derivation  Formalization  Post-Form.      Activation
```

Each phase adds a specific layer of rigor while preserving the semantic intent.

---

## Phase 1: Derivation

**Input**: Natural language instruction  
**Output**: `.ncds` (draft straightforward) and/or rough `.ncd`

Transforms unstructured intent into hierarchical inference structure. Identifies concepts (`<-`), operations (`<=`), and their relationships.

---

## Phase 2: Formalization

**Input**: Rough `.ncd` or `.ncds`  
**Output**: Formalized `.ncd` with flow indices and sequence types

Adds structural rigor:
- Assigns unique **flow indices** (e.g., `1.2.3`) to each step
- Determines **sequence type** for each inference (`imperative`, `grouping`, `timing`, etc.)
- Resolves concept identity and value bindings (`<:{1}>`, `<$={1}>`)

---

## Phase 3: Post-Formalization Update

**Input**: Formalized `.ncd`  
**Output**: Enriched `.ncd` with annotations (lines starting with `//`, `|`, and `|%{...}`)

Prepares the plan for execution by enriching it with configuration and grounding. Annotations are injected as comment lines associated with each concept or functional line.

### 3.1 Re-composition

Roots the `.ncd` into the **normative context of execution**. Maps abstract intent to the conventions and capabilities available in the runtime environment. Development of new norms are acceptable but not recommended, because they need to be approved by the author of the plan.

**The Normative Context consists of:**

| Component | Location | Role |
|-----------|----------|------|
| **Body** | `infra/_agent/_body.py` | Agent's faculties/tools (file_system, llm, python_interpreter, etc.) |
| **Paradigms** | `infra/_agent/_models/_paradigms/` | **Action Norms** — pre-defined composition patterns for executing operations |
| **PerceptionRouter** | `infra/_agent/_models/_perception_router.py` | **Perception Norms** — how signs are transmuted into objects |

Re-composition answers: *"Given what tools and conventions exist (with existing approvals), which ones should this operation use?"*

**Annotations injected on functional concepts (`<=`):**

| Annotation | Purpose | Example |
|------------|---------|---------|
| `%{norm_input}` | Paradigm ID (Action Norm) to load | `h_FileData-c_LoadParse-o_Struct` |
| `%{v_input_norm}` | Vertical input Perception Norm | `{prompt_location}`, `{script_location}` |
| `%{h_input_norm}` | Horizontal input Perception Norm | `{file_location}`, `in-memory` |
| `%{body_faculty}` | Body faculty to invoke | `file_system`, `llm`, `python_interpreter` |
| `%{o_shape}` | Descriptive hint about output structure | `dict in memory`, `boolean per signal` |

**Paradigm ID Naming Convention** (from `_paradigms/README.md`):
```
[inputs]-[composition]-[outputs].json
h_<HorizontalInputType>-c_<Computation>-o_<OutputType>
v_<VerticalInputType>-h_<HorizontalInputType>-c_<Computation>-o_<OutputType>
```

**Perception Norms** (from `PerceptionRouter`):
- `{file_location}` → `body.file_system.read()`
- `{prompt_location}` → `body.prompt_tool.read()` → template
- `{script_location}` → `body.python_interpreter` (deferred)
- `{save_path}` → `body.file_system.write()` target
- `{memorized_parameter}` → `body.file_system.read_memorized_value()`

### 3.2 Provision

Fills in the **concrete resources** within the normative context established by Re-composition. Links abstract concepts to actual file paths.

**Relationship to Re-composition:**
- Re-composition says: *"Use `{prompt_location}` norm with `llm` faculty"*
- Provision says: *"The prompt is at `provision/prompts/sentiment_extraction.md`"*

**Annotations injected:**

| Annotation | Where | Purpose | Example |
|------------|-------|---------|---------|
| `%{file_location}` | Value concepts (`<-`) | Path to ground data | `provision/data/price_data.json` |
| `%{v_input_provision}` | Functional concepts (`<=`) | Path to prompt/script | `provision/prompts/sentiment_extraction.md` |

Ground concepts are marked with `%{ref_element}: perceptual_sign` to indicate they are initially pointers that require transmutation (via the Perception Norm) before use.

### 3.3 Syntax Re-confirmation

Confirms reference structure (axes, shape, element type) for each concept to ensure **tensor coherence** before execution. This process often requires restructuring the plan's flow and usage of syntactical operators (and sometimes semantical concepts like assertions). 

**Why restructuring may be needed:**
- Scope correctness: Does an inference process "a signal" or "all signals"?
- Axis alignment: Do input axes match what the operation expects?
- Quantification: Does a judgement evaluate "for each" or "all at once"?

**Annotations injected on concepts:**

| Annotation | Purpose | Values |
|------------|---------|--------|
| `%{ref_axes}` | Named axes of the reference tensor | `[_none_axis]` (singleton), `[axis_name]` (collection) |
| `%{ref_shape}` | Tensor shape | `(1,)`, `(n_signal,)` |
| `%{ref_element}` | Element type/schema | `dict(...)`, `%{truth value}`, `perceptual_sign` |
| `%{ref_skip}` | Documents filter injection | `filtered by <condition_concept>` |

**Axis Conventions** (see `shared---normcode_axis.md`):
- `[_none_axis]`: Singleton value (no indeterminacy)
- `[concept_name]`: The concept provides this axis (e.g., `[signal]` means "one element per signal")
- Multiple axes: `[outer_axis, inner_axis]` for nested structures
- Axes accumulate through inference chains (output inherits input axes + may add its own)

**Common Restructuring Patterns:**

| Problem | Solution | Operator |
|---------|----------|----------|
| Need to process each element separately | Add loop | `*.` (every) |
| Need to collapse axis into flat list | Add grouping | `&[#]` (across) |
| Need to bundle items with labels | Add grouping | `&[{}]` (in) |
| Need to protect an axis from collapse | Add protection | `%^<$!={axis}>` |
| Need element-wise truth mask | Adjust assertion | `<For Each ... True>` |
| Need single collapsed boolean | Adjust assertion | `<ALL True>` or `<ALL False>` |

**Element Conventions:**
- `dict(key1: type1, ...)`: Structured dictionary
- `%{truth value}`: Truth marker (output of judgement, input to timing)
- `perceptual_sign`: Pointer requiring transmutation (ground concepts)

**Cross-reference:** For detailed syntax of operators, see `shared---normcode_syntatical_concepts_reconstruction.md`.

---

## Phase 4: Activation

**Input**: Enriched `.ncd`  
**Output**: `concept_repo.json`, `inference_repo.json`

Transforms the annotated `.ncd` into executable JSON repositories that the Orchestrator can run. Extracts:
- Concept definitions with reference structure
- Inference configurations with working interpretations
- Value orderings and paradigm bindings

---

## Design Principle

Each phase answers a specific question:

| Phase | Question Answered |
|-------|-------------------|
| Derivation | *What* are we trying to do? (structure) |
| Formalization | *In what order* and *which sequence*? (flow) |
| Post-Formalization | *How* and *with what resources*? (configuration) |
| Activation | *What does the Orchestrator need*? (execution format) |