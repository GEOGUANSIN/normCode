# Provision in Post-Formalization and Activation (The new vision)

**The supply side: Resolving declared demands into concrete resources.**

---

## Overview

**Provision in Activation** is the step within Phase 4 (Activation) where declared resource demands from Post-Formalization are resolved into actual, executable resources.

**The Demand/Supply Model**:

| Phase | Role | What It Does |
|-------|------|--------------|
| **Post-Formalization (Phase 3.2)** | **Demand** | Declares *what* resources are needed and *where* to find them |
| **Provision in Activation (Phase 4)** | **Supply** | Validates, resolves, and includes the actual resources |

**Input**: Enriched `.ncd` with resource path annotations  
**Output**: JSON repositories with resolved resources and validated paths

---

## The Demand/Supply Distinction

### Post-Formalization: Declaring Demand

During Post-Formalization (Sub-Phase 3.2), we **declare what we need** via annotations. The key distinction is **where perception happens**.

---

### Core Principle: The Paradigm is a Continuation of MVP

**The execution flow is:**

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MVP (Memory Value Perception)                                          │
│  ─────────────────────────────                                          │
│  For each value concept:                                                │
│    • If annotation is a PERCEPTUAL SIGN (|%{file_location}: path)       │
│      → PerceptionRouter perceives it → produces LITERAL content         │
│    • If annotation is a LITERAL (|%{literal<$% ...>}: value)            │
│      → Pass value as-is → no perception                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  PARADIGM (Composed Function)                                           │
│  ────────────────────────────                                           │
│  Receives what MVP produces:                                            │
│    • h_Literal → expects literal data (MVP perceived the sign)          │
│    • h_FilePath → expects file path (MVP passed literal through)        │
│      → Paradigm's composition reads the file internally                 │
└─────────────────────────────────────────────────────────────────────────┘
```

**The critical insight:**

| What Controls MVP Behavior | Where It's Declared | Examples |
|----------------------------|---------------------|----------|
| **VALUE CONCEPT annotation** | On the `<-` line | `\|%{file_location}: path` or `\|%{literal<$% file_path>}: path` |

| Value Concept Annotation | MVP Action | Result Passed to Paradigm |
|--------------------------|------------|---------------------------|
| `\|%{file_location}: path` | **Perceives** (reads file) | Loaded file content |
| `\|%{prompt_location}: path` | **Perceives** (reads prompt) | Loaded prompt content |
| `\|%{literal<$% file_path>}: path` | **No perception** | Raw path string |
| `\|%{literal<$% template>}: text` | **No perception** | Template string as-is |

**The `h_input_norm` on the functional concept describes what the paradigm EXPECTS to receive** — it must be consistent with what MVP produces.

---

#### Pattern 1: h_Literal — Perception in MVP

```ncd
<= ::(analyze sentiment) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    |%{norm_input}: v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
    |%{v_input_norm}: prompt_location
    |%{prompt_location}: provisions/prompts/sentiment_analysis.md
    |%{h_input_norm}: Literal
<- {reviews} | ?{flow_index}: 1.2
    |%{file_location}: provisions/data/reviews.json
```

- **Vertical input**: `prompt_location` norm → paradigm resolves during MFP (setup)
- **Horizontal input**: The value concept has `|%{file_location}` (a **perceptual sign**) → **MVP perceives it** → passes loaded content to paradigm
- **h_input_norm: `Literal`** → paradigm expects to receive literal data (which MVP provides after perception)
- **Key**: The `|%{file_location}` annotation on the value concept **triggers MVP perception**

#### Pattern 2: h_FilePath — Perception in Paradigm

```ncd
<= ::(analyze sentiment) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    |%{norm_input}: v_PromptLocation-h_FilePath-c_GenerateThinkJson-o_Literal
    |%{v_input_norm}: prompt_location
    |%{prompt_location}: provisions/prompts/sentiment_analysis.md
    |%{h_input_norm}: file_path
<- {reviews} | ?{flow_index}: 1.2
    |%{literal<$% file_path>}: provisions/data/reviews.json
```

- **Vertical input**: `prompt_location` norm → paradigm resolves during MFP (setup)
- **Horizontal input**: The value concept has `|%{literal<$% file_path>}` (a **literal**) → **MVP does NOT perceive** → passes raw path string to paradigm
- **h_input_norm: `file_path`** → paradigm expects to receive a file path (which it will read internally)
- **Key**: The `|%{literal<$%...>}` annotation on the value concept **skips MVP perception** — the paradigm's composition handles the file reading

### The Key Distinction

| Value Concept Annotation | MVP Perceives? | h_input_norm | Paradigm Receives |
|--------------------------|----------------|--------------|-------------------|
| `\|%{file_location}: path` | ✅ **Yes** | `Literal` | Loaded file content |
| `\|%{literal<$% file_path>}: path` | ❌ **No** | `file_path` / `LiteralPath` | Raw file path string |

**The value concept annotation controls MVP behavior:**
- `|%{file_location}` (perceptual sign) → MVP perceives → paradigm receives **literal data**
- `|%{literal<$%...>}` (literal marker) → MVP passes through → paradigm receives **raw value**

**The h_input_norm must be consistent:**
- If value has perceptual sign → h_input_norm should be `Literal` (paradigm expects the result of perception)
- If value is literal → h_input_norm should describe the literal type (`file_path`, `LiteralPath`, etc.)

**At this point, no validation occurs.** The paths are just strings.

### Provision in Activation: Supplying Resources

During Activation, the provision step **resolves these demands**:

1. **Validate** that the requested resources exist
2. **Load** paradigm definitions from JSON files
3. **Verify** prompt and data file paths
4. **Map** through `path_mapping.json` if needed
5. **Embed** or **reference** resources in the output repositories

**After provision**, the JSON repositories contain:
- Resolved paradigm configurations
- Validated file paths
- Ready-to-execute resource references

---

## Perception Norms and the PerceptionRouter

### How Input Norms Work

The PerceptionRouter transforms perceptual signs into actual data. The key is understanding **what triggers perception**:

| Input Type | What Triggers Perception | Where Resolved | Who Resolves |
|------------|--------------------------|----------------|--------------|
| **Vertical** (`v_`) | Paradigm's vertical input spec | Inside paradigm (MFP) | Paradigm's setup phase |
| **Horizontal** | **Value concept annotation** | Depends on annotation | See below |

**For horizontal inputs, the value concept annotation determines behavior:**

| Value Annotation | MVP Action | Paradigm's h_input_norm |
|------------------|------------|-------------------------|
| `\|%{file_location}: path` | Perceives → paradigm gets content | `Literal` |
| `\|%{literal<$% file_path>}: path` | Passes through | `LiteralPath` / `file_path` (paradigm reads file) |

### Vertical Inputs: Always Resolved in Paradigm

Vertical inputs (like prompts, scripts) are resolved **during MFP** (Model Function Perception) as part of the paradigm's setup phase:

```python
# During MFP - paradigm resolves its vertical inputs
# The paradigm's setup phase calls PerceptionRouter internally
prompt_content = perception_router.perceive(
    "%{prompt_location}abc(provisions/prompts/sentiment.md)", 
    body
)
# → Paradigm now has the loaded prompt template
```

### Horizontal Inputs: Depends on the Norm

Horizontal inputs can be resolved in **two different places** depending on the paradigm's expectation:

#### Value has Perceptual Sign → MVP Perceives

When the value concept has a **perceptual sign** (like `|%{file_location}`), MVP perceives it:

```python
# During MVP - BEFORE paradigm execution
# Value concept annotation: |%{file_location}: provisions/data/reviews.json
#                           ^^^^^^^^^^^^^^^^ This is a perceptual sign

data_content = perception_router.perceive(
    "%{file_location}def(provisions/data/reviews.json)",
    body
)
# → MVP passes the loaded content to paradigm
# → Paradigm receives: {"reviews": [...], ...}  (actual data)
# → h_input_norm should be: Literal (paradigm expects the perceived result)
```

#### Value is Literal → MVP Passes Through

When the value concept has a **literal marker** (like `|%{literal<$%...>}`), MVP passes it as-is:

```python
# During MVP - value is passed as-is (no perception)
# Value concept annotation: |%{literal<$% file_path>}: provisions/data/reviews.json
#                           ^^^^^^^^^^^^^^^^^^^^^^^ This is a literal marker

# → MVP passes: "provisions/data/reviews.json"  (raw path string)
# → h_input_norm should be: file_path or LiteralPath

# During paradigm execution - paradigm's composition reads the file
# Paradigm's composition step: body.file_system.read(h.file_path)
# → Paradigm loads the file internally
```

### Common Perception Norms

**Norms resolved via PerceptionRouter** (used in value concept annotations or paradigm vertical inputs):

| Norm | Faculty Used | What It Does | Example Sign |
|------|--------------|--------------|--------------|
| `file_location` | `body.file_system.read()` | Read file content | `%{file_location}7f2(data/input.txt)` |
| `prompt_location` | `body.prompt_tool.read()` | Load prompt template | `%{prompt_location}3c4(prompts/task.md)` |
| `script_location` | Deferred to executor | Reference Python script | `%{script_location}a1b(scripts/process.py)` |
| `save_path` | `body.file_system.write()` | Target for file output | `%{save_path}9e8(output/result.json)` |
| `memorized_parameter` | `body.file_system.read_memorized_value()` | Retrieve stored value | `%{memorized_parameter}(config/threshold)` |

**Paradigm input norm naming** (the h_/v_ prefix matches the norm vocabulary):

| Input Type | Naming Pattern | Examples |
|------------|----------------|----------|
| **Perception norm** | `[Norm]` | `FileLocation`, `PromptLocation`, `ScriptLocation` |
| **Literal (generic)** | `Literal` | `h_Literal` |
| **Literal (specialized)** | `Literal[Descriptor]` | `LiteralTemplate`, `LiteralPath`, `LiteralUserPrompt`, `LiteralInputs` |

| Value Concept Annotation | MVP Perceives? | h_input_norm | What Paradigm Receives |
|--------------------------|----------------|--------------|------------------------|
| `\|%{file_location}: path` | ✅ Yes | `Literal` | Loaded file content |
| `\|%{prompt_location}: path` | ✅ Yes | `Literal` | Loaded prompt content |
| `\|%{literal<$% file_path>}: path` | ❌ No | `LiteralPath` / `file_path` | Raw file path string |
| `\|%{literal<$% template>}: text` | ❌ No | `LiteralTemplate` | Template string as-is |
| `\|%{literal<$% user_prompt>}: text` | ❌ No | `LiteralUserPrompt` | User prompt string as-is |

> **Note**: Values from previous inferences are stored as perceptual signs (e.g., `%{file_location}(path)` for saved files, or `%(data)` for literal results). MVP perceives them according to their sign type.

### Understanding the Pattern

**The value concept annotation determines MVP behavior:**

| Annotation Type | Syntax | MVP Action | Use Case |
|-----------------|--------|------------|----------|
| **Perceptual Sign** | `\|%{norm}: path` | Perceives → loads content | Data needs to be read from file, or value from previous inference |
| **Literal** | `\|%{literal<$% type>}: value` | No perception → passes as-is | Value is already the right format for paradigm to handle |

**The paradigm is a continuation of MVP:**
- MVP prepares values according to their annotations
- Paradigm's composed function receives what MVP produces
- If MVP perceived → paradigm receives literal data
- If MVP didn't perceive → paradigm receives raw value and handles it internally

### Paradigm Structure

Paradigms have three main sections:

```json
{
  "metadata": {
    "description": "What this paradigm does",
    "inputs": {
      "vertical": { /* setup-time inputs (prompts, configs) */ },
      "horizontal": { /* runtime inputs (data from value concepts) */ }
    },
    "outputs": { /* output format */ }
  },
  "env_spec": {
    "tools": [ /* tools and affordances available */ ]
  },
  "sequence_spec": {
    "steps": [
      /* Steps 1..N-1: Prepare individual morphisms (get affordance functions) */
      /* Step N: composition_tool.compose - combines morphisms into final function */
    ]
  }
}
```

**The `sequence_spec` pattern:**
1. **Steps 1 to N-1**: Prepare individual morphisms by getting affordance functions from tools
2. **Final step**: `composition_tool.compose` combines all morphisms into `instruction_fn`

The `instruction_fn` is the composed function that the orchestrator executes with horizontal inputs.

The final `composition_tool.compose` step takes a `plan` parameter that defines:
- **`output_key`**: Name for this intermediate result
- **`function`**: Which morphism to apply (references a `result_key` from earlier steps)
- **`params`**: Runtime values (from `__initial_input__` or previous outputs)
- **`literal_params`**: Static values
- **`condition`** (optional): Conditional execution based on previous outputs
- **`return_key`**: Which output to return as the final result

**The `metadata.inputs` section documents what the paradigm expects:**

```json
// v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
{
  "metadata": {
    "description": "Generate JSON using LLM with vertical prompt and horizontal literal data",
    "inputs": {
      "vertical": {
        "prompt_template": "Path to prompt file (paradigm resolves during MFP)"
      },
      "horizontal": {
        "data": "Runtime data (value concept has perceptual sign, MVP perceives it)"
      }
    },
    "outputs": {
      "type": "Literal",
      "description": "Parsed JSON result"
    }
  }
  // ... env_spec and sequence_spec follow
}
```

**Example with specialized literals**:

```json
// v_LiteralTemplate-h_LiteralPath_LiteralInputs-c_CachedPyExec-o_Literal
{
  "metadata": {
    "description": "Execute Python script with caching. If missing, generate from template.",
    "inputs": {
      "vertical": {
        "template": "Template string for script generation (sourced from states.function.concept.name)"
      },
      "horizontal": {
        "script_path": "Path to Python script (literal, paradigm handles file I/O)",
        "inputs": "Collected input_* variables passed to script"
      }
    },
    "outputs": {
      "type": "Literal",
      "description": "Script execution result"
    }
  }
  // ... env_spec and sequence_spec follow
}
```

```json
// h_LiteralUserPrompt-c_MultiFilePicker-o_ListFileLocation
{
  "metadata": {
    "description": "Open file picker dialog for user to select multiple files",
    "inputs": {
      "vertical": {
        "initial_directory": "Starting directory (from states.body.base_dir)"
      },
      "horizontal": {
        "prompt": "Prompt text to display in dialog (literal user prompt)"
      }
    },
    "outputs": {
      "type": "ListFileLocation",
      "description": "List of selected file paths as perceptual signs"
    }
  }
  // ... env_spec and sequence_spec follow
}
```

> **Note**: See [Resource Types > Paradigms](#1-paradigms) for a complete paradigm example with `env_spec` and `sequence_spec`.

**Paradigm Naming Convention**:

```
[v_Norm]-[h_Norm(s)]-[c_CompositionSteps]-[o_OutputFormat].json
```

| Prefix | Pattern | Examples |
|--------|---------|----------|
| `v_` | Perception norm or Literal variant | `v_PromptLocation`, `v_LiteralTemplate` |
| `h_` | Perception norm or Literal variant | `h_Literal`, `h_LiteralPath`, `h_LiteralUserPrompt` |
| `c_` | Action description | `c_GenerateThinkJson`, `c_CachedPyExec`, `c_MultiFilePicker` |
| `o_` | `[Collection]Type` | `o_Literal`, `o_FileLocation`, `o_ListFileLocation` |

**Key rules**:
- **Input norms match PerceptionRouter vocabulary**: `FileLocation`, `PromptLocation`, `ScriptLocation`, `SavePath`
- **Literal variants use `Literal[Descriptor]`**: `LiteralTemplate`, `LiteralPath`, `LiteralUserPrompt`, `LiteralInputs`
- **Output collections put type first**: `o_ListFileLocation` (not `o_FileLocationList`)

**Key insight**: 
- The paradigm defines the *interface* (what input types are expected)
- The provision step provides the *paths* and configures value concept annotations
- **Where perception happens depends on h_input_norm**: MVP (`h_Literal`) or paradigm (`h_FilePath`)

---

## Output Formatting: The FormatterTool

### Completing the Perception-Output Cycle

The **FormatterTool** handles output formatting using the **same vocabulary** as the PerceptionRouter:

| Direction | Tool | Operation | Example |
|-----------|------|-----------|---------|
| **Input** | PerceptionRouter | Decode sign → data | `%{file_location}abc(path)` → file content |
| **Output** | FormatterTool | Encode data → sign | data → `%{file_location}def(path)` |

This symmetry ensures that outputs from one inference can be inputs to another.

### Output Formats (`o_` prefix)

The `o_` prefix in paradigm names specifies how the FormatterTool wraps the output:

| Output Format | FormatterTool Call | Resulting Sign | Use Case |
|---------------|-------------------|----------------|----------|
| `o_Literal` | `wrap(data, "literal")` | `%abc(data)` | Raw value (no perception needed) |
| `o_FileLocation` | `wrap(path, "file_location")` | `%{file_location}abc(path)` | Single file path for later reading |
| `o_ListFileLocation` | `wrap(paths, "list_file_location")` | `[%{file_location}abc(p1), ...]` | List of file paths |
| `o_Struct` | `wrap(data, None)` | Structured dict | Complex data structures |
| `o_Boolean` | `wrap(bool, "truth_value")` | `%{truth_value}abc(True/False)` | Judgement results |

**Collection naming pattern**: `o_[Collection][ElementType]`
- `o_ListFileLocation` - list of file locations
- `o_ListLiteral` - list of literal values
- `o_DictLiteral` - dictionary of literal values

### The Literal Output

When `o_Literal` is specified, the FormatterTool wraps with **no type specifier**:

```python
# FormatterTool.wrap() with type="literal"
# Special case: "literal" means NO norm - just %id(content)
wrap("hello world", "literal")  # → "%abc(hello world)"
wrap({"key": "value"}, "literal")  # → "%def({'key': 'value'})"
```

**Why "literal"?**: The output is the raw data itself—no perception/transmutation is needed when this value is used as input to another inference.

### The File Location Output

When `o_FileLocation` is specified, the FormatterTool wraps with the `file_location` norm:

```python
wrap("/path/to/result.json", "file_location")  
# → "%{file_location}abc(/path/to/result.json)"
```

**Why this matters**: When this output becomes an input to another inference:
1. If that inference expects `h_Literal`: MVP will perceive the sign and load file content
2. If that inference expects `h_FilePath`: MVP passes the path as-is

### The Perception-Output Symmetry

```
┌─────────────────────────────────────────────────────────────────┐
│  INFERENCE A                                                    │
│  ───────────                                                    │
│  Output: FormatterTool.wrap(result, "file_location")            │
│          → %{file_location}abc(/path/to/result.json)            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  INFERENCE B (h_Literal paradigm)                               │
│  ───────────────────────────────                                │
│  Input: %{file_location}abc(/path/to/result.json)               │
│  MVP: PerceptionRouter.perceive() → loads file content          │
│  Paradigm receives: actual data from file                       │
└─────────────────────────────────────────────────────────────────┘
```

This symmetry is what makes NormCode's data isolation work—each inference explicitly controls what format its outputs take, and the next inference explicitly controls when/how perception happens.

---

## Composition Steps: Bridging Data and Tools

### The Standard Execution Flow

```
┌───────────────────────────────────────────────────────────────────────┐
│  PRE-COMPOSITION (MFP - Model Function Perception)                    │
│  ─────────────────────────────────────────────────                    │
│  1. Resolve vertical inputs (prompts, scripts, configurations)        │
│  2. Prepare morphisms (transformation functions) for horizontal data  │
│  3. Bind tools from agent's Body                                      │
│  4. Output: Composed function ready to receive horizontal data        │
└───────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────┐
│  MVP (Memory Value Perception)                                        │
│  ─────────────────────────────                                        │
│  Resolve horizontal inputs (runtime data from value concepts)         │
│  - h_Literal: PerceptionRouter resolves perceptual signs → data       │
│  - h_FilePath: Pass path as-is (paradigm will read internally)        │
└───────────────────────────────────────────────────────────────────────┘
                                    ↓
┌───────────────────────────────────────────────────────────────────────┐
│  TVA (Tool Value Actuation)                                           │
│  ─────────────────────────                                            │
│  Apply the composed function to the perceived horizontal data         │
│  - Morphisms process each h_input according to its type               │
│  - Tools execute (LLM, file system, Python interpreter, etc.)         │
│  - Output wrapped by FormatterTool according to o_ format             │
└───────────────────────────────────────────────────────────────────────┘
```

### Morphisms: General Transformations

**Morphisms** are the transformation functions prepared during pre-composition. The key principle is to keep them **as general as possible**:

| Morphism Type | What It Does | Generality |
|---------------|--------------|------------|
| `template_substitute` | Substitute variables into template | Works with any template + vars |
| `llm_generate` | Send prompt to LLM | Works with any prompt string |
| `parse_json` | Extract JSON from response | Works with any JSON-like text |
| `file_read` | Read file content | Works with any file path |
| `file_write` | Write content to file | Works with any content + path |

**The goal**: Each morphism is a reusable building block that handles one type of transformation.

### Paradigm Design Philosophy

**Paradigms should bridge data types and tools, not encode specific use cases.**

#### Good Paradigm Design

```
v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
```

This paradigm:
- Takes a prompt (vertical) and data (horizontal)
- Generates with LLM and extracts JSON
- Returns literal result

**Reusable for**: Sentiment analysis, classification, extraction, summarization, etc.—any task that needs prompt + data → structured output.

```
v_LiteralTemplate-h_LiteralPath_LiteralInputs-c_CachedPyExec-o_Literal
```

This paradigm:
- Takes a template (vertical) for script generation if needed
- Takes a script path and inputs (horizontal)
- Caches executed scripts
- Returns literal result

**Reusable for**: Any Python execution with caching—data processing, calculations, transformations.

```
h_LiteralUserPrompt-c_MultiFilePicker-o_ListFileLocation
```

This paradigm:
- Takes a user prompt (horizontal)
- Opens a file picker dialog
- Returns list of selected file paths

**Reusable for**: Any file selection task—input files, batch processing, etc.

#### Avoid: Over-Specific Paradigms

```
v_SentimentPrompt-h_Reviews-c_AnalyzeSentiment-o_SentimentScore  ❌
```

This paradigm:
- Encodes a specific use case (sentiment analysis)
- Can't be reused for other tasks
- Creates paradigm proliferation

### The Execution Steps: MFP → MVP → TVA

The orchestrator executes semantic inferences through three steps:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MFP (Model Function Perception)                                        │
│  ───────────────────────────────                                        │
│  Input: function_concept reference (instruction strings)                │
│  Process: Run paradigm's sequence_spec via ModelSequenceRunner          │
│  Output: instruction_fn (composed callable) stored in function reference│
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  MVP (Memory Value Perception)                                          │
│  ─────────────────────────────                                          │
│  Input: value_concept references with perceptual signs                  │
│  Process: PerceptionRouter.perceive() transmutes signs → data           │
│  Output: dict {"input_1": data, "input_2": data, ...} in values ref     │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  TVA (Tool Value Actuation)                                             │
│  ─────────────────────────                                              │
│  Input: instruction_fn from MFP + values dict from MVP                  │
│  Process: cross_action(instruction_fn, values_dict)                     │
│  Output: inference result stored in inference reference                 │
└─────────────────────────────────────────────────────────────────────────┘
```

#### MFP: Building the Composed Function

MFP runs the paradigm's `sequence_spec` to produce `instruction_fn`:

```python
# From _mfp.py - for each instruction in the function_concept reference:

# 1. Create a proxy state with the current instruction
proxy = _MfpStateProxy(states, instruction_name_override=instruction)

# 2. Run the paradigm's sequence_spec
meta = ModelSequenceRunner(proxy, sequence_spec).run()

# 3. Extract the composed function
instruction_fn = meta.get("instruction_fn")  # The callable that will process h_data
```

The `sequence_spec` steps (defined in the paradigm JSON):
1. **Steps 1 to N-1**: Get affordance functions from tools (e.g., `llm.generate`, `file_system.read`)
2. **Final step**: `composition_tool.compose` combines them into `instruction_fn`

#### MVP: Perceiving Value Concepts

MVP resolves perceptual signs on value concepts into actual data:

```python
# From _mvp.py:

# 1. Order inputs according to value_order from working_interpretation
ordered_refs = _get_ordered_input_references(states, body)

# 2. For each reference, apply perception
for ref in ordered_refs:
    # If value has a selector (from grouped concepts), apply derelation first
    if selector and "source_concept" in selector:
        selected_ref = element_action(derelation_fn, [ref])
        perceived_ref = element_action(perception_fn, [selected_ref])
    else:
        # Direct perception via PerceptionRouter
        perceived_ref = element_action(
            lambda e: body.perception_router.perceive(e, body), 
            [ref]
        )

# 3. Format into dict: {"input_1": data1, "input_2": data2, ...}
#    Special keys (script_location, save_path, etc.) get their own keys
dict_ref = element_action(lambda x: _format_inputs_as_dict(x, body), [crossed_ref])
```

**Key insight**: The value concept annotation (`|%{file_location}`) is what `perception_router.perceive()` acts on. If it's a perceptual sign, the content is loaded. If it's a literal, it's passed through.

#### TVA: Applying the Function to Values

TVA calls `instruction_fn` with the perceived values:

```python
# From _tva.py:

func_ref = states.get_reference("function", "MFP")  # instruction_fn from MFP
values_ref = states.get_reference("values", "MVP")  # {"input_1": ..., "input_2": ...}

# Get the callable
instruction_fn = func_ref.get(**{axis_name: 0})

# Apply function to values using cross_action
# This handles tensor broadcasting across axes
applied_ref = cross_action(instruction_fn, values_ref, new_axis_name)

# Collapse singleton result axes
final_ref = applied_ref  # (with collapsing logic)

states.set_reference("inference", "TVA", final_ref)
```

**The complete flow**:
1. **MFP** produces `instruction_fn` (the paradigm's composed morphisms)
2. **MVP** produces `{"input_1": data, ...}` (perceived values from value concepts)
3. **TVA** calls `instruction_fn({"input_1": data, ...})` → result

### Why This Matters for Provision

When provisioning paradigms, think about:

1. **What data types does this paradigm bridge?**
   - Input types (h_Literal, h_FilePath, etc.)
   - Output types (o_Literal, o_FileLocation, etc.)

2. **What tools does this paradigm use?**
   - LLM, file system, Python interpreter, etc.

3. **Is this paradigm general enough to be reused?**
   - If you're creating a paradigm for one specific task, reconsider
   - Use existing paradigms with different prompts/data instead

---

## Resource Types

### 1. Paradigms

**Demand** (Post-Formalization):
```ncd
|%{norm_input}: h_LiteralPath-c_ReadFile-o_Literal
```

**Supply** (Provision in Activation):
```json
// provisions/paradigms/file_system/h_LiteralPath-c_ReadFile-o_Literal.json
{
  "metadata": {
    "description": "Read file content as string",
    "inputs": {
      "horizontal": {
        "file_path": "Path to the file to read (literal path, paradigm reads internally)"
      }
    },
    "outputs": {
      "type": "Literal",
      "description": "The file content as a string"
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "file_system",
        "affordances": [
          {
            "affordance_name": "read",
            "call_code": "result = tool.read"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "get_fn"
      },
      {
        "step_index": 2,
        "affordance": "file_system.read",
        "params": {},
        "result_key": "read_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "wrap_fn"
      },
      {
        "step_index": 4,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "file_path",
              "function": {"__type__": "MetaValue", "key": "get_fn"},
              "params": {"dictionary": "__initial_input__"},
              "literal_params": {"key": "file_path"}
            },
            {
              "output_key": "read_result",
              "function": {"__type__": "MetaValue", "key": "read_fn"},
              "params": {"__positional__": "file_path"}
            },
            {
              "output_key": "file_content",
              "function": {"__type__": "MetaValue", "key": "get_fn"},
              "params": {"dictionary": "read_result"},
              "literal_params": {"key": "content"}
            },
            {
              "output_key": "final_result",
              "function": {"__type__": "MetaValue", "key": "wrap_fn"},
              "params": {"__positional__": "file_content"}
            }
          ],
          "return_key": "final_result"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}
```

**Key sections:**
- **`metadata`**: Description and input/output documentation
- **`env_spec`**: Tools and affordances available to this paradigm
- **`sequence_spec`**: Steps that prepare morphisms and compose them into `instruction_fn`

> **Note**: The final `result_key` is always `instruction_fn` — this is the composed function that the orchestrator will execute with horizontal inputs.

**What Provision Does**:
1. Look up paradigm ID in `path_mapping.json`
2. Load the paradigm JSON file
3. Validate required fields exist
4. Include paradigm config in `working_interpretation`

### 2. Prompts

**Demand** (Post-Formalization):
```ncd
|%{v_input_provision}: provisions/prompts/phase_1/apply_refinement_questions.md
```

**Supply** (Provision in Activation):
```markdown
# provisions/prompts/phase_1/apply_refinement_questions.md

## Task
Apply each of the 7 refinement questions to the given instruction...

## Inputs
You will receive:
- `{raw instruction content}`: The original natural language instruction  
- `{refinement questions content}`: The 7 refinement questions to apply

## Output Format
Return a JSON array of question-answer pairs:
...

## Instruction to Refine
{{raw instruction content}}

## Refinement Questions
{{refinement questions content}}
```

**What Provision Does**:
1. Validate file exists at path
2. Store path reference in `working_interpretation`
3. Orchestrator loads prompt content at runtime via perception norms

### 3. Data Files

**Demand** (Post-Formalization):
```ncd
<- {refinement questions} | ?{flow_index}: 1.5
    |%{file_location}: provisions/data/refinement_questions.txt
    |%{ref_element}: perceptual_sign
```

**Supply** (Provision in Activation):
1. Validate file exists
2. Mark as ground concept with `is_ground_concept: true`
3. Set `reference_data` to perceptual sign format:
   ```json
   "reference_data": ["%{file_location}(provisions/data/refinement_questions.txt)"]
   ```

### 4. Scripts

**Demand** (Post-Formalization):
```ncd
|%{norm_input}: h_Data-c_CheckPhaseComplete-o_Boolean
```

**Supply** (Provision in Activation):
```python
# provisions/scripts/check_phase_complete.py

def check_phase_complete(progress_data, phase_name):
    """Check if a specific phase is marked complete in progress data."""
    if not progress_data:
        return False
    return progress_data.get(phase_name, {}).get("complete", False)
```

**What Provision Does**:
1. Paradigm references script location
2. Validate script exists
3. Include script path in paradigm composition

---

## The Path Mapping System

### Purpose

**`path_mapping.json`** provides indirection between demand paths and actual file locations:

```json
{
  "_comment": "Maps inference_repo prompt_path references to actual file locations",
  "_base_dir": "provisions",
  
  "prompts": {
    "provisions/prompts/phase_1/apply_refinement_questions.md": "prompts/phase_1/apply_refinement_questions.md"
  },
  
  "paradigms": {
    "v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal": "paradigms/llm/v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal.json",
    "h_LiteralPath-c_ReadFile-o_Literal": "paradigms/file_system/h_LiteralPath-c_ReadFile-o_Literal.json"
  },
  
  "data": {
    "provisions/data/refinement_questions.txt": "data/refinement_questions.txt"
  },
  
  "scripts": {
    "scripts/check_phase_complete.py": "scripts/check_phase_complete.py"
  }
}
```

### Why Indirection?

1. **Portability**: Plans can reference logical paths; physical locations can vary
2. **Versioning**: Swap resource versions without modifying the plan
3. **Modularity**: Reuse provisions across different projects
4. **Deployment**: Different mappings for dev/staging/production

### Resolution Algorithm

```python
def resolve_resource_path(demand_path, resource_type, path_mapping, base_dir):
    """
    Resolve a demand path to an actual file location.
    
    Args:
        demand_path: Path from |%{v_input_provision} or similar
        resource_type: "prompts", "paradigms", "data", or "scripts"
        path_mapping: Contents of path_mapping.json
        base_dir: Base directory (usually "provisions")
    
    Returns:
        Resolved absolute or relative path to the resource
    """
    # Check if explicit mapping exists
    if demand_path in path_mapping.get(resource_type, {}):
        relative_path = path_mapping[resource_type][demand_path]
        return os.path.join(base_dir, relative_path)
    
    # Fall back to direct path
    return demand_path
```

---

## Provision Process

### Step-by-Step Algorithm

```python
def provision_activation(enriched_ncd, provisions_dir):
    """
    Resolve all resource demands during activation.
    
    Args:
        enriched_ncd: Post-formalized .ncd content
        provisions_dir: Directory containing provisions/
    
    Returns:
        Tuple of (concept_repo, inference_repo) with resolved resources
    """
    # 1. Load path mapping
    path_mapping = load_json(f"{provisions_dir}/path_mapping.json")
    
    # 2. Initialize repositories
    concept_repo = []
    inference_repo = []
    
    # 3. Process each inference
    for inference in parse_inferences(enriched_ncd):
        
        # 3a. Extract paradigm demand
        paradigm_id = inference.get_annotation("norm_input")
        if paradigm_id:
            # Resolve and load paradigm
            paradigm_path = resolve_resource_path(
                paradigm_id, "paradigms", path_mapping, provisions_dir
            )
            paradigm_config = load_and_validate_paradigm(paradigm_path)
            
            # Include in working_interpretation
            inference.working_interpretation["paradigm"] = paradigm_id
            inference.working_interpretation["paradigm_config"] = paradigm_config
        
        # 3b. Extract prompt demand
        prompt_path = inference.get_annotation("v_input_provision")
        if prompt_path:
            # Validate prompt exists
            resolved_path = resolve_resource_path(
                prompt_path, "prompts", path_mapping, provisions_dir
            )
            validate_file_exists(resolved_path)
            
            # Include in working_interpretation
            inference.working_interpretation["prompt_path"] = resolved_path
        
        # 3c. Process value concepts for data files
        for value_concept in inference.value_concepts:
            file_location = value_concept.get_annotation("file_location")
            if file_location:
                # Validate data file exists
                resolved_path = resolve_resource_path(
                    file_location, "data", path_mapping, provisions_dir
                )
                validate_file_exists(resolved_path)
                
                # Mark as ground concept with perceptual sign
                concept_entry = build_concept_entry(
                    value_concept,
                    is_ground_concept=True,
                    reference_data=[f"%{{file_location}}({resolved_path})"]
                )
                concept_repo.append(concept_entry)
        
        inference_repo.append(build_inference_entry(inference))
    
    return concept_repo, inference_repo
```

### Validation Rules

| Resource Type | Validation | Error on Failure |
|---------------|------------|------------------|
| **Paradigm** | File exists, valid JSON, required fields present | `ParadigmNotFoundError` |
| **Prompt** | File exists | `PromptNotFoundError` |
| **Data** | File exists (or mark as optional) | `DataFileNotFoundError` or skip |
| **Script** | File exists, valid Python | `ScriptNotFoundError` |

---

## Provisions Directory Structure

### Standard Layout

```
provisions/
├── path_mapping.json          # Resource resolution mappings
├── paradigms/
│   ├── llm/
│   │   ├── v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal.json
│   │   └── v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Boolean.json
│   ├── file_system/
│   │   ├── h_LiteralPath-c_ReadFile-o_Literal.json
│   │   ├── h_LiteralPath_LiteralContent-c_WriteFile-o_Literal.json
│   │   └── h_LiteralPath-c_ReadJsonFile-o_Struct.json
│   └── python_interpreter/
│       ├── h_Literal-c_CheckPhaseComplete-o_Boolean.json
│       └── h_Literal-c_ExtractField-o_Literal.json
├── prompts/
│   ├── phase_1/
│   │   ├── judge_instruction_vagueness.md
│   │   ├── apply_refinement_questions.md
│   │   └── synthesize_refined_instruction.md
│   ├── phase_2/
│   │   └── ...
│   └── ...
├── data/
│   ├── refinement_questions.txt
│   └── ...
└── scripts/
    ├── check_phase_complete.py
    └── ...
```

### Naming Conventions

**Paradigms**: `[v_Norm]-[h_Norm(s)]-[c_Steps]-[o_Format].json`

| Component | Pattern | Examples |
|-----------|---------|----------|
| `v_` | `v_[PerceptionNorm]` or `v_Literal[Desc]` | `v_PromptLocation`, `v_LiteralTemplate` |
| `h_` | `h_[PerceptionNorm]` or `h_Literal[Desc]` | `h_Literal`, `h_LiteralPath`, `h_LiteralUserPrompt` |
| `c_` | `c_[ActionDescription]` | `c_GenerateThinkJson`, `c_CachedPyExec` |
| `o_` | `o_[Collection][Type]` | `o_Literal`, `o_ListFileLocation` |

**Specialized Literal Descriptors**:
- `LiteralTemplate` - template string
- `LiteralPath` - file path (paradigm handles I/O)
- `LiteralUserPrompt` - user prompt string
- `LiteralInputs` - collection of input values
- `LiteralContent` - content to write

**Prompts**: `[action_name].md`
- Use descriptive names matching the operation
- Include input/output documentation in the file

**Scripts**: `[function_name].py`
- Match the paradigm's action name where possible

---

## Common Patterns

### Pattern 1: LLM Operation with Prompt

**Demand** (Post-Formalization):
```ncd
<= ::(classify operation type) | ?{sequence}: imperative
    |%{norm_input}: v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
    |%{v_input_norm}: prompt_location
    |%{v_input_provision}: provisions/prompts/phase_3/classify_operation.md
    |%{h_input_norm}: Literal
<- {operation context} | ?{flow_index}: 1.2
    |%{file_location}: (from previous inference output)
```

> **Note**: The value concept `{operation context}` has a perceptual sign from a previous inference's output. MVP perceives it, so h_input_norm is `Literal`.

**Supply** (Provision in Activation):
- Load paradigm from `paradigms/llm/v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal.json`
- Validate prompt exists at `prompts/phase_3/classify_operation.md`
- Result in `working_interpretation`:
  ```json
  {
    "paradigm": "v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal",
    "prompt_path": "provisions/prompts/phase_3/classify_operation.md"
  }
  ```

### Pattern 2: File Read Operation

**Demand** (Post-Formalization):
```ncd
<= ::(read progress from file if exists) | ?{sequence}: imperative
    |%{norm_input}: h_LiteralPath-c_ReadFileIfExists-o_Literal
    |%{h_input_norm}: literal_path
<- {progress file path} | ?{flow_index}: 1.2
    |%{literal<$% file_path>}: provisions/data/progress.json
```

**Supply** (Provision in Activation):
- Load paradigm from `paradigms/file_system/h_LiteralPath-c_ReadFileIfExists-o_Literal.json`
- Validate or skip data file (if-exists paradigm handles missing files)

### Pattern 3: Python Script Execution

**Demand** (Post-Formalization):
```ncd
<= ::(check if phase 1 already complete in progress) | ?{sequence}: imperative
    |%{norm_input}: h_Literal-c_CheckPhaseComplete-o_Boolean
    |%{h_input_norm}: Literal
<- {current progress} | ?{flow_index}: 1.2
    |%{file_location}: (from previous inference output)
```

> **Note**: The value concept `{current progress}` has a perceptual sign. MVP perceives it, so h_input_norm is `Literal`.

**Supply** (Provision in Activation):
- Load paradigm which references `scripts/check_phase_complete.py`
- Validate script exists and is valid Python
- Paradigm composition includes script call

### Pattern 4: Multi-File Selection

**Demand** (Post-Formalization):
```ncd
<= ::(select input files) | ?{sequence}: imperative
    |%{norm_input}: h_LiteralUserPrompt-c_MultiFilePicker-o_ListFileLocation
    |%{h_input_norm}: literal_user_prompt
<- {selection prompt} | ?{flow_index}: 1.2
```

**Supply** (Provision in Activation):
- Load paradigm from `paradigms/ui/h_LiteralUserPrompt-c_MultiFilePicker-o_ListFileLocation.json`
- Output is a list of file locations: `[%{file_location}(path1), %{file_location}(path2), ...]`

---

## Error Handling

### Missing Resource Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `ParadigmNotFoundError` | Paradigm ID not in path_mapping or file missing | Add paradigm to provisions/ or fix path_mapping.json |
| `PromptNotFoundError` | Prompt path doesn't resolve to existing file | Create prompt file or fix v_input_provision annotation |
| `DataFileNotFoundError` | Data file path doesn't exist | Create data file, fix path, or mark as optional |
| `InvalidParadigmError` | Paradigm JSON missing required fields | Fix paradigm JSON structure |

### Validation Warnings

| Warning | Cause | Impact |
|---------|-------|--------|
| `UnusedParadigmWarning` | Paradigm in provisions/ not referenced by plan | Cleanup opportunity |
| `UnmappedPathWarning` | Path not in path_mapping.json (using direct path) | May work, but lacks indirection benefits |

---

## Best Practices

### 1. Organize by Phase or Domain

```
provisions/prompts/
├── phase_1/          # Refinement phase prompts
├── phase_2/          # Extraction phase prompts
├── phase_3/          # Classification phase prompts
└── shared/           # Reusable across phases
```

### 2. Document Prompts Thoroughly

Include in each prompt file:
- Task description
- Input format
- Output format (especially JSON schema)
- Examples when helpful

### 3. Version Your Paradigms

When creating new paradigm variations:
```
paradigms/llm/
├── h_PromptTemplate-h_Data-c_GenerateThinkJson-o_Literal.json      # Standard
├── h_PromptTemplate-h_Data-c_GenerateThinkJson-o_Literal-v2.json   # New version
```

### 4. Validate Early

Run provision validation before full activation:
```bash
python compiler.py validate-provisions provisions/ --plan enriched.ncd
```

---

## Relationship to Other Phases

### Before: Post-Formalization (Phase 3.2)

Post-Formalization's "Provision" sub-phase **declares demands**:
- Adds `|%{v_input_provision}` annotations
- Adds `|%{file_location}` annotations
- Specifies paradigm IDs in `|%{norm_input}`

**Key distinction**: Post-Formalization writes *what* is needed; it doesn't validate or resolve.

### During: Activation (Phase 4)

Provision in Activation **supplies resources**:
- Validates all paths exist
- Loads paradigm configurations
- Resolves through path_mapping.json
- Produces executable repositories

### After: Execution

The Orchestrator **consumes provisions**:
- Loads prompts via perception norms at runtime
- Executes paradigm compositions
- Reads data files as perceptual signs

---

## Summary

| Aspect | Post-Formalization (Demand) | Provision in Activation (Supply) |
|--------|---------------------------|----------------------------------|
| **Action** | Annotate paths in .ncd | Validate and resolve paths |
| **Paradigms** | Specify ID in `\|%{norm_input}` | Load JSON, validate structure |
| **Prompts** | Specify path in `\|%{v_input_provision}` | Validate file exists |
| **Data** | Specify path in `\|%{file_location}` | Validate, create perceptual signs |
| **Output** | Enriched .ncd with annotations | JSON repos with resolved resources |
| **Validation** | None (just strings) | Full existence and format checks |

**The Provision Promise**: Every resource demand declared in Post-Formalization will be validated and resolved before execution begins. No runtime surprises from missing files.

---

## Next Steps

- **[Activation](activation.md)** - Full activation phase documentation
- **[Post-Formalization](post_formalization.md)** - How demands are declared
- **[Execution Overview](../3_execution/overview.md)** - How provisions are consumed at runtime

---

**Ready to create provisions?** Start by setting up your `provisions/` directory structure and `path_mapping.json`, then run validation to catch issues early.

