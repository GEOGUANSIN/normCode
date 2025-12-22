# Post-Formalization

**Phase 3: Enriching plans with execution context—norms, resources, and tensor structure.**

---

## Overview

**Post-Formalization** is the third phase of NormCode compilation. It enriches the formal `.ncd` with annotations that configure execution and ground abstract concepts to concrete resources.

**Input**: `.ncd` (formalized with flow indices and sequences)  
**Output**: `.ncd` (enriched with execution annotations)

**Core Task**: Answer "HOW and WITH WHAT RESOURCES?" for each operation.

---

## The Three Sub-Phases

Post-Formalization consists of three distinct sub-phases:

| Sub-Phase | Purpose | Adds |
|-----------|---------|------|
| **3.1 Re-composition** | Map to normative context | Paradigms, body faculties, perception norms |
| **3.2 Provision** | Link to concrete resources | File paths, prompt locations |
| **3.3 Syntax Re-confirmation** | Ensure tensor coherence | Axes, shapes, element types |

Each sub-phase adds a specific layer of configuration through **annotation lines**.

---

## Annotation Syntax

### How Annotations Work

Annotations are **comment lines** that appear after concept or functional lines, providing metadata without modifying the core syntax.

**Format**:
```ncd
<- {concept} | ?{flow_index}: 1.2
    |%{annotation_name}: value
    |%{another_annotation}: another value
```

**Key properties**:
- Start with `|%{...}:` (referential comments)
- Associated with the line above them
- Inherited by same flow index
- Multiple annotations per concept/functional line allowed

---

## Sub-Phase 3.1: Re-composition

### Purpose

**Re-composition** roots the `.ncd` into the **normative context of execution**—mapping abstract intent to available conventions and capabilities.

**Key Question**: *"Given what tools and conventions exist, which ones should this operation use?"*

### The Normative Context

The normative context consists of three components:

| Component | Location | Role |
|-----------|----------|------|
| **Body** | `infra/_agent/_body.py` | Agent's tools/faculties (file_system, llm, python_interpreter) |
| **Paradigms** | `infra/_agent/_models/_paradigms/` | **Action Norms** — composition patterns for operations |
| **PerceptionRouter** | `infra/_agent/_models/_perception_router.py` | **Perception Norms** — how signs become objects |

### Paradigms (Action Norms)

**Paradigms** are declarative JSON specifications that define how semantic operations execute.

**Naming Convention** (from `_paradigms/README.md`):
```
[inputs]-[composition]-[outputs].json

Examples:
h_PromptTemplate-c_Generate-o_Text.json
v_Prompt-h_FileData-c_LoadParse-o_Struct.json
h_PromptTemplateInputOther_SaveDir-c_GenerateThinkJson-Extract-Save-o_FileLocation.json
```

**Components**:
- `h_`: Horizontal input (runtime value)
- `v_`: Vertical input (setup metadata)
- `c_`: Composition steps
- `o_`: Output format

**Purpose**:
- Define execution logic without hardcoding
- Reusable across plans
- Configurable via JSON
- Enable vertical (setup) vs horizontal (runtime) separation

### Perception Norms

**Perception norms** define how perceptual signs are transmuted into actual data.

**Common Norms**:

| Norm | Purpose | Body Faculty | Example |
|------|---------|--------------|---------|
| `{file_location}` | Read file content | `body.file_system.read()` | `%{file_location}(data/input.txt)` |
| `{prompt_location}` | Load prompt template | `body.prompt_tool.read()` | `%{prompt_location}(prompts/sentiment.md)` |
| `{script_location}` | Python script path | `body.python_interpreter` | `%{script_location}(scripts/process.py)` |
| `{save_path}` | File write target | `body.file_system.write()` | `%{save_path}(output/result.json)` |
| `{memorized_parameter}` | Stored value | `body.file_system.read_memorized_value()` | `%{memorized_parameter}(config/threshold)` |
| `in-memory` | Direct value | N/A (no transmutation) | Used for computed concepts |

### Annotations Added by Re-composition

**On functional concepts** (`<=`):

| Annotation | Purpose | Example |
|------------|---------|---------|
| `\|%{norm_input}` | Paradigm ID to load | `h_PromptTemplate-c_Generate-o_Text` |
| `\|%{v_input_norm}` | Vertical input perception norm | `{prompt_location}` |
| `\|%{h_input_norm}` | Horizontal input perception norm | `{file_location}`, `in-memory` |
| `\|%{body_faculty}` | Body faculty to invoke | `llm`, `file_system`, `python_interpreter` |
| `\|%{o_shape}` | Output structure hint | `dict in memory`, `boolean per signal` |

### Example: Re-composition

**Before Re-composition**:
```ncd
:<:{document summary} | ?{flow_index}: 1
    <= ::(summarize this text) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {clean text} | ?{flow_index}: 1.2
```

**After Re-composition**:
```ncd
:<:{document summary} | ?{flow_index}: 1
    <= ::(summarize this text) | ?{flow_index}: 1.1 | ?{sequence}: imperative
        |%{norm_input}: h_PromptTemplate-c_GenerateThinkJson-o_Normal
        |%{v_input_norm}: {prompt_location}
        |%{h_input_norm}: in-memory
        |%{body_faculty}: llm
        |%{o_shape}: dict in memory
    <- {clean text} | ?{flow_index}: 1.2
```

**What was added**:
- **Paradigm**: `h_PromptTemplate-c_GenerateThinkJson-o_Normal` (specifies how to execute)
- **Vertical norm**: `{prompt_location}` (prompt comes from file)
- **Horizontal norm**: `in-memory` (input is already in memory)
- **Body faculty**: `llm` (uses language model)
- **Output shape**: `dict in memory` (returns structured dict)

### Re-composition Process

**Algorithm**:

1. **Identify operation type** (imperative, judgement, syntactic)
2. **For semantic operations**:
   - Determine required inputs (vertical vs horizontal)
   - Select appropriate paradigm from registry
   - Identify body faculty needed
   - Assign perception norms for inputs
3. **For syntactic operations**:
   - No paradigm needed (deterministic)
   - May need perception norms for ground concepts
4. **Inject annotations** into `.ncd`

**Paradigm Selection Heuristics**:

| Operation Pattern | Likely Paradigm | Reasoning |
|-------------------|----------------|-----------|
| "generate X" | `h_PromptTemplate-c_Generate-...` | Text generation |
| "analyze X" | `h_Data-c_ThinkJSON-...` | Structured analysis |
| "validate X" | `v_Prompt-h_Data-c_ThinkJSON-o_Normal` | Judgement |
| "execute script" | `h_ScriptLocation-c_Execute-o_Result` | Python execution |
| "load file" | `h_FileLocation-c_LoadParse-o_Struct` | File I/O |

---

## Sub-Phase 3.2: Provision

### Purpose

**Provision** fills in **concrete resources** within the normative context established by re-composition.

**Key Question**: *"Where exactly are the files, prompts, and scripts located?"*

**Relationship to Re-composition**:
- **Re-composition says**: "Use `{prompt_location}` norm with `llm` faculty"
- **Provision says**: "The prompt is at `provision/prompts/sentiment_extraction.md`"

### Annotations Added by Provision

**On value concepts** (`<-`) for ground concepts:

| Annotation | Purpose | Example |
|------------|---------|---------|
| `\|%{file_location}` | Path to data file | `provision/data/price_data.json` |
| `\|%{ref_element}: perceptual_sign` | Mark as perceptual sign | Indicates lazy loading |

**On functional concepts** (`<=`) for paradigm inputs:

| Annotation | Purpose | Example |
|------------|---------|---------|
| `\|%{v_input_provision}` | Path to prompt/script | `provision/prompts/sentiment.md` |

### Example: Provision

**Before Provision**:
```ncd
:<:{sentiment analysis} | ?{flow_index}: 1
    <= ::(analyze sentiment) | ?{flow_index}: 1.1 | ?{sequence}: imperative
        |%{norm_input}: h_PromptTemplate-c_GenerateThinkJson-o_Normal
        |%{v_input_norm}: {prompt_location}
        |%{h_input_norm}: {file_location}
    <- {customer reviews} | ?{flow_index}: 1.2
```

**After Provision**:
```ncd
:<:{sentiment analysis} | ?{flow_index}: 1
    <= ::(analyze sentiment) | ?{flow_index}: 1.1 | ?{sequence}: imperative
        |%{norm_input}: h_PromptTemplate-c_GenerateThinkJson-o_Normal
        |%{v_input_norm}: {prompt_location}
        |%{v_input_provision}: provision/prompts/sentiment_extraction.md
        |%{h_input_norm}: {file_location}
    <- {customer reviews} | ?{flow_index}: 1.2
        |%{file_location}: provision/data/reviews.json
        |%{ref_element}: perceptual_sign
```

**What was added**:
- **Prompt path**: `provision/prompts/sentiment_extraction.md`
- **Data path**: `provision/data/reviews.json`
- **Perceptual sign marker**: Indicates `{customer reviews}` is initially a pointer, not loaded data

### Provision Process

**Algorithm**:

1. **Identify ground concepts** (marked with `:>:` or no parent inference)
2. **Determine perception norm** from re-composition
3. **Resolve resource paths**:
   - Check `provision/` directory
   - Look for matching files
   - Use configuration or user input
4. **Inject path annotations**
5. **Mark as perceptual signs** if lazy loading

**Ground Concept Identification**:

A concept is **ground** if:
- Marked with `:>:` (explicit input marker)
- Created by `$%` (abstraction operator)
- Has no parent inference (leaf node with no `<=` child)
- Marked in compilation configuration

---

## Sub-Phase 3.3: Syntax Re-confirmation

### Purpose

**Syntax Re-confirmation** ensures **tensor coherence** by declaring reference structure (axes, shape, element type) for each concept.

**Key Question**: *"What is the dimensional structure of each concept's data?"*

**Why It Matters**:
- Operations need to know input dimensions
- Syntactic operators manipulate axes
- Type mismatches cause runtime errors
- Documentation for developers

### Axes of Indeterminacy

**Axes** are named dimensions that model indeterminacy in data.

**Example**:
```
"A student" has axes:
- [school]: which school?
- [class]: which class?
- [nationality]: which nationality?
```

A reference with these axes is a 3D tensor where each cell is a student.

**Axis Conventions**:

| Axis Name | Meaning | Example |
|-----------|---------|---------|
| `[_none_axis]` | Singleton (no indeterminacy) | Single value |
| `[concept_name]` | One element per concept instance | `[signal]`, `[document]` |
| `[outer_axis, inner_axis]` | Nested structure | 2D or higher dimensional |

### Element Type Conventions

| Element Type | Meaning | Example |
|--------------|---------|---------|
| `dict(key1: type1, ...)` | Structured dictionary | `dict(sentiment: str, score: float)` |
| `%{truth value}` | Boolean (from judgement) | Output of `::<>` |
| `perceptual_sign` | Pointer requiring transmutation | Ground concepts before MVP |
| `str`, `int`, `float` | Primitives | Simple values |

### Annotations Added by Syntax Re-confirmation

**On concepts** (both `<-` and `<=`):

| Annotation | Purpose | Example |
|------------|---------|---------|
| `\|%{ref_axes}` | Named axes of the reference | `[_none_axis]`, `[signal]` |
| `\|%{ref_shape}` | Tensor shape | `(1,)`, `(n_signal,)` |
| `\|%{ref_element}` | Element type/schema | `dict(...)`, `%{truth value}` |
| `\|%{ref_skip}` | Filter documentation | `filtered by <condition>` |

### Example: Syntax Re-confirmation

**Before Syntax Re-confirmation**:
```ncd
:<:{sentiment analysis} | ?{flow_index}: 1
    <= ::(analyze sentiment) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {customer reviews} | ?{flow_index}: 1.2
```

**After Syntax Re-confirmation**:
```ncd
:<:{sentiment analysis} | ?{flow_index}: 1
    |%{ref_axes}: [_none_axis]
    |%{ref_shape}: (1,)
    |%{ref_element}: dict(sentiment: str, score: float, confidence: float)
    <= ::(analyze sentiment) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {customer reviews} | ?{flow_index}: 1.2
        |%{ref_axes}: [review]
        |%{ref_shape}: (n_review,)
        |%{ref_element}: perceptual_sign
```

**What was added**:
- **Root axes**: `[_none_axis]` (single result)
- **Root shape**: `(1,)` (one element)
- **Root element**: Structured dict with schema
- **Input axes**: `[review]` (collection of reviews)
- **Input shape**: `(n_review,)` (variable number)
- **Input element**: `perceptual_sign` (not yet loaded)

### Common Restructuring Patterns

Sometimes axis analysis reveals the need to restructure the plan:

| Problem | Solution | Operator |
|---------|----------|----------|
| Need to process each element separately | Add loop | `*.` (looping) |
| Need to collapse axis into flat list | Add grouping | `&[#]` (group across) |
| Need to bundle items with labels | Add grouping | `&[{}]` (group in) |
| Need to protect an axis from collapse | Add protection | `%^<$!={axis}>` |
| Need element-wise truth mask | Adjust assertion | `<FOR EACH ... True>` |
| Need single collapsed boolean | Adjust assertion | `<ALL True>` or `<ALL False>` |

**Example Restructuring**:

**Problem**: Judgement needs to evaluate each signal separately, but current structure evaluates all at once.

**Before**:
```ncd
<- <signals valid> | ?{flow_index}: 1
    |%{ref_axes}: [_none_axis]  # WRONG: Should have [signal] axis
    <= ::(validate signals)<ALL True> | ?{flow_index}: 1.1
    <- [signals] | ?{flow_index}: 1.2
        |%{ref_axes}: [signal]
```

**After** (with loop added):
```ncd
<- [all <signal valid>] | ?{flow_index}: 1
    |%{ref_axes}: [signal]
    |%{ref_element}: %{truth value}
    <= *. %>({signals}) %<({valid}) %:({signal}) %@(1) | ?{flow_index}: 1.1 | ?{sequence}: looping
        <= $. %>({valid}) | ?{flow_index}: 1.1.1 | ?{sequence}: assigning
        <- <signal valid> | ?{flow_index}: 1.1.2
            |%{ref_axes}: [_none_axis]
            |%{ref_element}: %{truth value}
            <= ::(validate signal)<ALL True> | ?{flow_index}: 1.1.2.1 | ?{sequence}: judgement
            <- {signal}*1 | ?{flow_index}: 1.1.2.1.1
    <- [signals] | ?{flow_index}: 1.2
        |%{ref_axes}: [signal]
    <* {signal}<$({signals})*> | ?{flow_index}: 1.3
```

### Syntax Re-confirmation Process

**Algorithm**:

1. **Analyze each concept**:
   - Determine type (`{}`, `[]`, `<>`)
   - Infer axes from context (loops, groupings)
   - Determine element type from operation output
2. **Check coherence**:
   - Input axes match operation expectations?
   - Judgement assertions match axes?
   - Grouping collapses correct axes?
3. **Restructure if needed**:
   - Add loops for element-wise processing
   - Add groupings for axis manipulation
   - Adjust truth assertions
4. **Inject annotations**

---

## Complete Post-Formalization Example

### Before Post-Formalization

```ncd
:<:{investment decision} | ?{flow_index}: 1
    <= ::(synthesize recommendation) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {risk analysis} | ?{flow_index}: 1.2
        <= ::(analyze risk) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
        <- {price data} | ?{flow_index}: 1.2.2
    <- {sentiment score} | ?{flow_index}: 1.3
        <= ::(analyze sentiment) | ?{flow_index}: 1.3.1 | ?{sequence}: imperative
        <- {news articles} | ?{flow_index}: 1.3.1.1
```

### After Post-Formalization

```ncd
:<:{investment decision} | ?{flow_index}: 1
    |%{ref_axes}: [_none_axis]
    |%{ref_shape}: (1,)
    |%{ref_element}: dict(decision: str, confidence: float, reasoning: str)
    <= ::(synthesize recommendation from {1} and {2}) | ?{flow_index}: 1.1 | ?{sequence}: imperative
        |%{norm_input}: h_PromptTemplate-c_GenerateThinkJson-o_Normal
        |%{v_input_norm}: {prompt_location}
        |%{v_input_provision}: provision/prompts/investment_synthesis.md
        |%{h_input_norm}: in-memory
        |%{body_faculty}: llm
        |%{o_shape}: dict in memory
    <- {risk analysis}<:{1}> | ?{flow_index}: 1.2
        |%{ref_axes}: [_none_axis]
        |%{ref_shape}: (1,)
        |%{ref_element}: dict(risk_level: str, factors: list)
        <= ::(analyze risk based on {1}) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
            |%{norm_input}: h_PromptTemplate-c_GenerateThinkJson-o_Normal
            |%{v_input_norm}: {prompt_location}
            |%{v_input_provision}: provision/prompts/risk_analysis.md
            |%{h_input_norm}: {file_location}
        <- {price data}<:{1}> | ?{flow_index}: 1.2.2
            |%{file_location}: provision/data/price_history.json
            |%{ref_axes}: [date]
            |%{ref_shape}: (n_date,)
            |%{ref_element}: perceptual_sign
    <- {sentiment score}<:{2}> | ?{flow_index}: 1.3
        |%{ref_axes}: [_none_axis]
        |%{ref_shape}: (1,)
        |%{ref_element}: float
        <= ::(analyze sentiment) | ?{flow_index}: 1.3.1 | ?{sequence}: imperative
            |%{norm_input}: h_Data-c_ThinkJSON-o_Normal
            |%{h_input_norm}: {file_location}
            |%{body_faculty}: llm
        <- {news articles} | ?{flow_index}: 1.3.1.1
            |%{file_location}: provision/data/recent_news.json
            |%{ref_axes}: [article]
            |%{ref_shape}: (n_article,)
            |%{ref_element}: perceptual_sign
```

### What Was Added

**Re-composition**:
- Paradigm IDs for all semantic operations
- Perception norms (prompt_location, file_location, in-memory)
- Body faculties (llm)
- Output shape hints

**Provision**:
- Prompt paths (`provision/prompts/*.md`)
- Data paths (`provision/data/*.json`)
- Perceptual sign markers

**Syntax Re-confirmation**:
- Axes for all concepts (`[_none_axis]`, `[date]`, `[article]`)
- Shapes (`(1,)`, `(n_date,)`, `(n_article,)`)
- Element types (dict schemas, perceptual_sign, float)

---

## Post-Formalization Validation

### Checklist

Before moving to activation:

**Re-composition**:
- [ ] All semantic operations have paradigms
- [ ] Perception norms specified
- [ ] Body faculties assigned
- [ ] Paradigm IDs exist in registry

**Provision**:
- [ ] Ground concepts have resource paths
- [ ] File paths are valid
- [ ] Prompt paths exist
- [ ] Perceptual signs marked

**Syntax Re-confirmation**:
- [ ] All concepts have axes declared
- [ ] Shapes are consistent
- [ ] Element types match operations
- [ ] No axis mismatches

### Common Issues

| Issue | Symptom | Fix |
|-------|---------|-----|
| **Missing paradigm** | Semantic operation without `\|%{norm_input}` | Add paradigm annotation |
| **Invalid path** | File path doesn't exist | Correct path or create file |
| **Axis mismatch** | Operation expects [axis] but gets [_none_axis] | Restructure with loop or grouping |
| **Wrong element type** | Expects dict but gets perceptual_sign | Add transmutation step |
| **Missing perceptual sign marker** | Ground concept without `\|%{ref_element}: perceptual_sign` | Add marker |

---

## Tools and Automation

### Automated Post-Formalization

**Command** (if implemented):
```bash
python compiler.py post-formalize formalized.ncd
```

**What it does**:
1. Runs re-composition (paradigm selection)
2. Runs provision (path resolution)
3. Runs syntax re-confirmation (axis inference)
4. Outputs enriched `.ncd`

### Manual Post-Formalization

**Steps**:
1. **Re-composition**:
   - For each semantic operation, select paradigm
   - Assign perception norms
   - Inject annotations
2. **Provision**:
   - Identify ground concepts
   - Resolve resource paths
   - Add path annotations
3. **Syntax Re-confirmation**:
   - Analyze axes for each concept
   - Determine element types
   - Restructure if needed
   - Inject annotations

### Configuration Files

**Paradigm Registry**: `infra/_agent/_models/_paradigms/`
- Each paradigm is a JSON file
- Naming follows convention
- Can be extended

**Provision Configuration**: `provision/`
- `provision/data/` - Data files
- `provision/prompts/` - Prompt templates
- `provision/scripts/` - Python scripts

---

## Next Steps

After post-formalization, your enriched `.ncd` file moves to:

- **[Activation](activation.md)** - Transform to JSON repositories for orchestrator execution

---

## Summary

### Key Takeaways

| Concept | Insight |
|---------|---------|
| **Three sub-phases** | Re-composition, Provision, Syntax Re-confirmation |
| **Annotations** | Comment lines (`\|%{...}:`) that configure execution |
| **Normative context** | Body faculties, paradigms, perception norms |
| **Concrete resources** | File paths, prompt locations |
| **Tensor coherence** | Axes, shapes, element types |
| **Restructuring** | Sometimes needed to fix axis mismatches |

### The Post-Formalization Promise

**Post-Formalization bridges intent and execution**:

1. Abstract operations → Concrete paradigms
2. Conceptual data → File paths and resources
3. Implicit structure → Explicit axes and types
4. Ready for JSON repository generation

**Result**: A fully configured plan ready to become executable repositories.

---

**Ready to generate repositories?** Continue to [Activation](activation.md) to transform your enriched `.ncd` into JSON repositories that the orchestrator can execute.
