# Provision: The New Vision

**A unified model for resource resolution in NormCode compilation and execution.**

---

## Overview

Provision is the process of connecting abstract plan operations to concrete resources. This document describes the **new vision** for how provisions work across compilation and execution.

**The Demand/Supply Model**:

| Phase | Role | What It Does |
|-------|------|--------------|
| **Post-Formalization (Phase 3.2)** | **Demand** | Declares *what* resources are needed and *where* to find them |
| **Activation (Phase 4)** | **Supply** | Validates, resolves, and includes the actual resources |

**Activation Input**: Enriched `.ncd` with resource path annotations  
**Activation Output**: JSON repositories with resolved resources and validated paths

---

# Part I: Core Concepts

## 1.1 The Demand/Supply Distinction

### Post-Formalization: Declaring Demand

During Post-Formalization (Sub-Phase 3.2), we **declare what we need** via annotations:

```ncd
<= ::(analyze sentiment) | ?{sequence}: imperative
    |%{norm_input}: v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
    |%{v_input}: provisions/prompts/sentiment_analysis.md
<- {reviews} | ?{flow_index}: 1.2
    |%{file_location}: provisions/data/reviews.json
```

**At this point, no validation occurs.** The paths are just strings.

### Activation: Supplying Resources

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

## 1.2 Perceptual Signs vs Literals

The key distinction in the new vision is **where perception happens**—controlled by the value concept annotation.

### Annotations

| Annotation Type | Syntax | MVP Action | Use Case |
|-----------------|--------|------------|----------|
| **Perceptual Sign** | `\|%{norm}: path` | Perceives → loads content | Data needs to be read from file |
| **Literal** (The special Perceptual Sign) | `\|%{literal<$% type>}: value` | No perception → passes as-is | Value is already the right format |

### The Key Distinction Table

| Value Concept Annotation | MVP Perceives? | h_input_norm | Paradigm Receives |
|--------------------------|----------------|--------------|-------------------|
| `\|%{file_location}: path` | ✅ **Yes** | `Literal` | Loaded file content |
| `\|%{prompt_location}: path` | ✅ **Yes** | `Literal` | Loaded prompt content |
| `\|%{literal<$% file_path>}: path` | ❌ **No** | `LiteralPath` | Raw file path string |
| `\|%{literal<$% template>}: text` | ❌ **No** | `LiteralTemplate` | Template string as-is |

### The Critical Rule

**The value concept annotation controls MVP behavior:**
- `|%{file_location}` (perceptual sign) → MVP perceives → paradigm receives **literal data**
- `|%{literal<$%...>}` (literal marker) → MVP passes through → paradigm receives **raw value**

**The h_input_norm must be consistent:**
- If value has perceptual sign → h_input_norm should be `Literal`
- If value is literal → h_input_norm should describe the literal type (`LiteralPath`, etc.)

---

## 1.3 The Execution Flow: MFP → MVP → TVA

The orchestrator executes semantic inferences through three steps:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MFP (Model Function Perception)                                        │
│  ───────────────────────────────                                        │
│  1. Resolve vertical inputs (prompts, scripts, configurations)          │
│  2. Run paradigm's sequence_spec via ModelSequenceRunner                │
│  3. Output: instruction_fn (composed callable)                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  MVP (Memory Value Perception)                                          │
│  ─────────────────────────────                                          │
│  1. Resolve horizontal inputs from value concepts                       │
│  2. Perceptual signs → PerceptionRouter perceives them                  │
│  3. Literals → pass through as-is                                       │
│  4. Output: {"input_1": data, "input_2": data, ...}                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  TVA (Tool Value Actuation)                                             │
│  ─────────────────────────                                              │
│  1. Apply instruction_fn to values dict                                 │
│  2. Tools execute (LLM, file system, Python interpreter, etc.)          │
│  3. Output wrapped by FormatterTool according to o_ format              │
└─────────────────────────────────────────────────────────────────────────┘
```

### The Core Principle: Paradigm is a Continuation of MVP

```
┌─────────────────────────────────────────────────────────────────────────┐
│  MVP (Memory Value Perception)                                          │
│  For each value concept:                                                │
│    • If annotation is a PERCEPTUAL SIGN (|%{file_location}: path)       │
│      → PerceptionRouter perceives it → produces LITERAL content         │
│    • If annotation is a LITERAL (|%{literal<$% ...>}: value)            │
│      → Pass value as-is → no perception                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│  PARADIGM (Composed Function)                                           │
│  Receives what MVP produces:                                            │
│    • h_Literal → expects literal data (MVP perceived the sign)          │
│    • h_FilePath → expects file path (MVP passed literal through)        │
│      → Paradigm's composition reads the file internally                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# Part II: Perception and Output

## 2.1 The PerceptionRouter

The PerceptionRouter transforms perceptual signs into actual data.

### How Input Norms Work

| Input Type | What Triggers Perception | Where Resolved |
|------------|--------------------------|----------------|
| **Vertical** (`v_`) | Paradigm's vertical input spec | Inside paradigm (MFP) |
| **Horizontal** | **Value concept annotation** | Depends on annotation (see below) |

### Vertical Inputs: Always Resolved in Paradigm

Vertical inputs (like prompts, scripts) are resolved **during MFP** (Model Function Perception):

```python
# During MFP - paradigm resolves its vertical inputs
prompt_content = perception_router.perceive(
    "%{prompt_location}abc(provisions/prompts/sentiment.md)", 
    body
)
# → Paradigm now has the loaded prompt template
```

### Horizontal Inputs: Depends on the Annotation

#### When value has Perceptual Sign → MVP Perceives

```python
# Value concept annotation: |%{file_location}: provisions/data/reviews.json
# This is a perceptual sign

data_content = perception_router.perceive(
    "%{file_location}def(provisions/data/reviews.json)",
    body
)
# → MVP passes the loaded content to paradigm
# → Paradigm receives: {"reviews": [...], ...}  (actual data)
# → h_input_norm should be: Literal
```

#### When value is Literal → MVP Passes Through

```python
# Value concept annotation: |%{literal<$% file_path>}: provisions/data/reviews.json
# This is a literal marker

# → MVP passes: "provisions/data/reviews.json"  (raw path string)
# → h_input_norm should be: LiteralPath
# → Paradigm's composition reads the file internally
```

---

## 2.2 Common Perception Norms

**Norms resolved via PerceptionRouter:**

| Norm | Faculty Used | What It Does | Example Sign |
|------|--------------|--------------|--------------|
| `file_location` | `body.file_system.read()` | Read file content | `%{file_location}7f2(data/input.txt)` |
| `prompt_location` | `body.prompt_tool.read()` | Load prompt template | `%{prompt_location}3c4(prompts/task.md)` |
| `script_location` | Deferred to executor | Reference Python script | `%{script_location}a1b(scripts/process.py)` |
| `save_path` | `body.file_system.write()` | Target for file output | `%{save_path}9e8(output/result.json)` |
| `memorized_parameter` | `body.file_system.read_memorized_value()` | Retrieve stored value | `%{memorized_parameter}(config/threshold)` |

---

## 2.3 The FormatterTool

The **FormatterTool** handles output formatting using the **same vocabulary** as the PerceptionRouter:

| Direction | Tool | Operation | Example |
|-----------|------|-----------|---------|
| **Input** | PerceptionRouter | Decode sign → data | `%{file_location}abc(path)` → file content |
| **Output** | FormatterTool | Encode data → sign | data → `%{file_location}def(path)` |

### Output Formats (`o_` prefix)

| Output Format | FormatterTool Call | Resulting Sign | Use Case |
|---------------|-------------------|----------------|----------|
| `o_Literal` | `wrap(data, "literal")` | `%abc(data)` | Raw value (no perception needed) |
| `o_FileLocation` | `wrap(path, "file_location")` | `%{file_location}abc(path)` | Single file path |
| `o_ListFileLocation` | `wrap(paths, "list_file_location")` | `[%{file_location}abc(p1), ...]` | List of file paths |
| `o_Boolean` | `wrap(bool, "truth_value")` | `%{truth_value}abc(True/False)` | Judgement results |

**Collection naming pattern**: `o_[Collection][ElementType]`
- `o_ListFileLocation` — list of file locations
- `o_ListLiteral` — list of literal values

---

## 2.4 The Perception-Output Symmetry

This symmetry is what makes NormCode's data isolation work:

```
┌─────────────────────────────────────────────────────────────────┐
│  INFERENCE A                                                    │
│  Output: FormatterTool.wrap(result, "file_location")            │
│          → %{file_location}abc(/path/to/result.json)            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  INFERENCE B (h_Literal paradigm)                               │
│  Input: %{file_location}abc(/path/to/result.json)               │
│  MVP: PerceptionRouter.perceive() → loads file content          │
│  Paradigm receives: actual data from file                       │
└─────────────────────────────────────────────────────────────────┘
```

Each inference explicitly controls what format its outputs take, and the next inference explicitly controls when/how perception happens.

---

# Part III: Paradigms

## 3.1 What is a Paradigm

**Paradigms** are declarative JSON specifications that define how semantic operations execute. They bridge data types and tools.

**Key insight**:
- The paradigm defines the *interface* (what input types are expected)
- The provision step provides the *paths* and configures value concept annotations
- **Where perception happens depends on h_input_norm**: MVP (`h_Literal`) or paradigm (`h_FilePath`)

---

## 3.2 Paradigm Structure

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
      /* Steps 1..N-1: Prepare individual morphisms */
      /* Step N: composition_tool.compose → instruction_fn */
    ]
  }
}
```

### The `sequence_spec` Pattern

1. **Steps 1 to N-1**: Prepare individual morphisms by getting affordance functions from tools
2. **Final step**: `composition_tool.compose` combines all morphisms into `instruction_fn`

The `instruction_fn` is the composed function that the orchestrator executes with horizontal inputs.

### The `composition_tool.compose` Plan

The final step's `plan` parameter defines:
- **`output_key`**: Name for this intermediate result
- **`function`**: Which morphism to apply (references a `result_key` from earlier steps)
- **`params`**: Runtime values (from `__initial_input__` or previous outputs)
- **`literal_params`**: Static values
- **`condition`** (optional): Conditional execution
- **`return_key`**: Which output to return as the final result

---

## 3.3 Paradigm Naming Convention

```
[v_Norm]-[h_Norm(s)]-[c_CompositionSteps]-[o_OutputFormat].json
```

| Prefix | Pattern | Examples |
|--------|---------|----------|
| `v_` | Perception norm or Literal variant | `v_PromptLocation`, `v_LiteralTemplate` |
| `h_` | Perception norm or Literal variant | `h_Literal`, `h_LiteralPath`, `h_LiteralUserPrompt` |
| `c_` | Action description | `c_GenerateThinkJson`, `c_CachedPyExec`, `c_MultiFilePicker` |
| `o_` | `[Collection]Type` | `o_Literal`, `o_FileLocation`, `o_ListFileLocation` |

### Input Norm Naming Patterns

| Input Type | Naming Pattern | Examples |
|------------|----------------|----------|
| **Perception norm** | `[Norm]` | `FileLocation`, `PromptLocation`, `ScriptLocation` |
| **Literal (generic)** | `Literal` | `h_Literal` |
| **Literal (specialized)** | `Literal[Descriptor]` | `LiteralTemplate`, `LiteralPath`, `LiteralUserPrompt`, `LiteralInputs` |

### Key Rules

- **Input norms match PerceptionRouter vocabulary**: `FileLocation`, `PromptLocation`, `ScriptLocation`, `SavePath`
- **Literal variants use `Literal[Descriptor]`**: `LiteralTemplate`, `LiteralPath`, `LiteralUserPrompt`, `LiteralInputs`
- **Output collections put collection first**: `o_ListFileLocation` (not `o_FileLocationList`)

---

## 3.4 Paradigm Design Philosophy

**Paradigms should bridge data types and tools, not encode specific use cases.**

### ✅ Good Paradigm Design

```
v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
```
- Takes a prompt (vertical) and data (horizontal)
- Generates with LLM and extracts JSON
- **Reusable for**: Sentiment analysis, classification, extraction, summarization, etc.

```
h_LiteralUserPrompt-c_MultiFilePicker-o_ListFileLocation
```
- Takes a user prompt (horizontal)
- Opens a file picker dialog
- **Reusable for**: Any file selection task

### ❌ Avoid: Over-Specific Paradigms

```
v_SentimentPrompt-h_Reviews-c_AnalyzeSentiment-o_SentimentScore
```
- Encodes a specific use case (sentiment analysis)
- Can't be reused for other tasks
- Creates paradigm proliferation

---

## 3.5 Retrieving Vertical Inputs in Paradigms

Vertical inputs (prompts, scripts, configurations) arrive at the paradigm wrapped in perceptual signs. The paradigm's `sequence_spec` must **extract the raw path** before using it.

### The `states.vertical` Structure

During MFP (Model Function Perception), the orchestrator populates `states.vertical` with the vertical input value. This value is a **perceptual sign** (e.g., `%{prompt_location}abc(provisions/prompts/task.md)`).

### Extracting Paths with `perception_router.strip_sign`

To get the raw path from a perceptual sign, use the `perception_router.strip_sign` function:

```json
{
  "output_key": "prompt_path",
  "function": {"__type__": "MetaValue", "key": "perception_router.strip_sign"},
  "params": {"__positional__": {"__type__": "MetaValue", "key": "states.vertical"}}
}
```

**Result**: `"provisions/prompts/task.md"` (the raw path, stripped of the sign wrapper)

### ❌ Common Mistake: Accessing Non-Existent Keys

```json
{
  "output_key": "prompt_path",
  "function": {"__type__": "MetaValue", "key": "states.function.paradigm_config.vertical.prompt_path"},
  "params": {}
}
```

**Error**: `KeyError: 'paradigm_config'`

This pattern assumes a nested structure that doesn't exist. Always use `perception_router.strip_sign` on `states.vertical`.

### Script Paradigms: Extracting Multiple Fields

For script paradigms where the vertical input contains multiple fields (script path and function name), extract each field separately:

```json
[
  {
    "output_key": "script_path",
    "function": {"__type__": "MetaValue", "key": "perception_router.strip_sign"},
    "params": {"__positional__": {"__type__": "MetaValue", "key": "states.vertical.script_path"}}
  },
  {
    "output_key": "function_name",
    "function": {"__type__": "MetaValue", "key": "perception_router.strip_sign"},
    "params": {"__positional__": {"__type__": "MetaValue", "key": "states.vertical.function_name"}}
  }
]
```

### The Pattern Summary

| Vertical Input Type | Access Pattern | Extract With |
|---------------------|----------------|--------------|
| **Prompt** (`v_PromptLocation`) | `states.vertical` | `perception_router.strip_sign(states.vertical)` |
| **Script** (`v_ScriptLocation`) | `states.vertical.script_path`, `states.vertical.function_name` | `perception_router.strip_sign(...)` on each |
| **Template** (`v_LiteralTemplate`) | `states.vertical` | Direct access (already literal) |

---

# Part IV: Resource Types & Directory Structure

## 4.1 Resource Types

### Paradigms

**Demand** (Post-Formalization):
```ncd
|%{norm_input}: h_LiteralPath-c_ReadFile-o_Literal
```

**Supply** (Activation): Load paradigm JSON, validate structure, include in `working_interpretation`.

---

### Prompts

**Demand** (Post-Formalization):
```ncd
|%{v_input_provision}: provisions/prompts/phase_1/apply_refinement_questions.md
```

**Supply** (Activation): Validate file exists, store path reference. Orchestrator loads content at runtime via perception norms.

#### Template Variable Requirements

Prompts use Python's `string.Template` syntax for variable substitution. Variables are injected based on **value concept order**.

**Variable Naming Convention**:
- `$input_1` — First value concept (by `value_order` or flow index)
- `$input_2` — Second value concept
- `$input_n` — Nth value concept
- `$input_other` — Bundle of unused inputs (for smart substitution paradigms)

**Example Prompt Template**:
```markdown
# Analyze Sentiment

## Task
Analyze the sentiment of the following reviews.

## Reviews Data
$input_1

## Classification Guidelines  
$input_2

## Output Format
Return JSON with sentiment scores...
```

**How Substitution Works** (from `FormatterTool.create_substitute_function`):

```python
# The template key (e.g., "prompt_template") contains the template string
# All other keys in vars become substitution variables
def substitute_fn(vars: Dict[str, Any]) -> str:
    prompt_template = vars[template_key]
    substitution_vars = {k: v for k, v in vars.items() if k != template_key}
    return Template(str(prompt_template)).safe_substitute(substitution_vars)
```

**Special Keys**: Some paradigms use `$input_other` for smart bundling of unused variables (see `create_smart_substitute_function`).

---

### Data Files

**Demand** (Post-Formalization):
```ncd
<- {refinement questions} | ?{flow_index}: 1.5
    |%{file_location}: provisions/data/refinement_questions.txt
    |%{ref_element}: perceptual_sign
```

**Supply** (Activation): Validate file exists, mark as ground concept, set `reference_data` to perceptual sign format.

---

### Scripts

**Demand** (Post-Formalization):
```ncd
|%{norm_input}: h_Literal-c_CheckPhaseComplete-o_Boolean
```

**Supply** (Activation): Paradigm references script location, validate script exists, include in composition.

#### Script Function Requirements

Scripts are executed via the `PythonInterpreterTool`. There are two execution modes:

**Mode 1: Script Execution** (`execute` method)
- Script sets a `result` variable
- Inputs are injected into global scope

```python
# provisions/scripts/process_data.py

# Inputs are available as globals: input_1, input_2, etc.
data = input_1
config = input_2

# Process...
processed = {"processed": data, "config": config}

# REQUIRED: Set the result variable
result = processed
```

**Mode 2: Function Execution** (`function_execute` method) — **Preferred**
- Define a named function
- Parameters passed as keyword arguments
- Optional `body` parameter for tool access

```python
# provisions/scripts/check_phase_complete.py

def check_phase_complete(input_1: dict, input_2: str = None, body=None) -> bool:
    """
    Check if a specific phase is marked complete in progress data.
    
    Args:
        input_1: The progress tracking dictionary
        input_2: Name of the phase to check (e.g., "phase_1")
        body: Optional Body instance for accessing tools
        
    Returns:
        True if phase is complete, False otherwise
    """
    if not input_1:
        return False
    return input_1.get(input_2, {}).get("complete", False)
```

**Function Signature Requirements**:
1. **Named function** — The paradigm specifies which function to call
2. **Positional-style parameters** — Use `input_1`, `input_2`, etc. to match MVP's value order
3. **Optional `body` parameter** — If declared, receives the Body instance for tool access
4. **Return value** — Directly returned (no `result` variable needed)

### The `main` Function Convention

Many paradigms are configured to call a function named `main`. When your script's primary function has a different name, **add a `main` alias**:

```python
# provisions/scripts/check_phase_complete.py

def check_phase_complete(input_1: dict, input_2: str = None, body=None) -> bool:
    """The actual implementation with a descriptive name."""
    if not input_1:
        return False
    return input_1.get(input_2, {}).get("complete", False)


# Convention: Add a main alias for paradigm compatibility
def main(input_1: dict, input_2: str = None, body=None) -> bool:
    """Alias for paradigm compatibility."""
    return check_phase_complete(input_1, input_2, body)
```

**Why this pattern?**
- **Paradigm reusability**: Generic paradigms (e.g., `v_ScriptLocation-h_Literal-c_Execute-o_Boolean`) can call `main` without knowing specific function names
- **Code clarity**: The descriptive function name (`check_phase_complete`) documents intent
- **Testability**: You can test `check_phase_complete` directly, while `main` serves as the paradigm entry point

### Parameter Naming: `input_N` Pattern

Scripts receive horizontal inputs as positional parameters named `input_1`, `input_2`, etc.:

| Parameter | Source |
|-----------|--------|
| `input_1` | First value concept (by `value_order`) |
| `input_2` | Second value concept |
| `input_N` | Nth value concept |
| `body` | Optional Body instance (injected if declared) |

```python
def main(input_1: Any, input_2: str = None, body=None) -> Any:
    """
    Args:
        input_1: The primary data to process
        input_2: Optional configuration or secondary input
        body: Optional Body instance for tool access
    """
    # Process input_1 with optional input_2 configuration
    return process(input_1, input_2)
```

**Body Injection** (from `PythonInterpreterTool`):
```python
# The tool automatically injects body if the function accepts it
sig = inspect.signature(function_to_call)
accepts_body = (
    "body" in sig.parameters
    or any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
)
if accepts_body and "body" not in params:
    params["body"] = self.body
```

**Example with Body Access**:
```python
# provisions/scripts/save_checkpoint.py

def save_checkpoint(data: dict, checkpoint_name: str, body=None) -> dict:
    """Save data to a checkpoint file using Body's file_system."""
    if body is None:
        return {"status": "error", "message": "Body not available"}
    
    path = f"checkpoints/{checkpoint_name}.json"
    result = body.file_system.write(path, json.dumps(data, indent=2))
    
    return {"status": "success", "path": path}
```

---

## 4.2 Provisions Directory Structure

```
provisions/
├── path_mapping.json          # Resource resolution mappings
├── paradigms/
│   ├── llm/
│   │   ├── v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal.json
│   │   └── v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Boolean.json
│   ├── file_system/
│   │   ├── h_LiteralPath-c_ReadFile-o_Literal.json
│   │   └── h_LiteralPath-c_ReadJsonFile-o_Struct.json
│   └── python_interpreter/
│       └── h_Literal-c_CheckPhaseComplete-o_Boolean.json
├── prompts/
│   ├── phase_1/
│   │   ├── judge_instruction_vagueness.md
│   │   └── apply_refinement_questions.md
│   ├── phase_2/
│   │   └── ...
│   └── shared/           # Reusable across phases
├── data/
│   └── refinement_questions.txt
└── scripts/
    └── check_phase_complete.py
```

### Naming Conventions

**Paradigms**: `[v_Norm]-[h_Norm(s)]-[c_Steps]-[o_Format].json`

**Prompts**: `[action_name].md` — Use descriptive names matching the operation

**Scripts**: `[function_name].py` — Match the paradigm's action name where possible

---

## 4.3 The Path Mapping System

**`path_mapping.json`** provides indirection between demand paths and actual file locations:

```json
{
  "_comment": "Maps demand paths to actual file locations",
  "_base_dir": "provisions",
  
  "prompts": {
    "provisions/prompts/phase_1/apply_refinement_questions.md": "prompts/phase_1/apply_refinement_questions.md"
  },
  
  "paradigms": {
    "v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal": "paradigms/llm/v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal.json"
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

---

# Part V: The Provision Process

## 5.1 Post-Formalization: Declaring Demand

Post-Formalization's "Provision" sub-phase **declares demands**:
- Adds `|%{v_input_provision}` annotations for prompts
- Adds `|%{file_location}` annotations for data files
- Specifies paradigm IDs in `|%{norm_input}`

**Key distinction**: Post-Formalization writes *what* is needed; it doesn't validate or resolve.

## 5.2 Activation: Supplying Resources

Provision in Activation **supplies resources**:
- Validates all paths exist
- Loads paradigm configurations
- Resolves through `path_mapping.json`
- Produces executable repositories

## 5.3 Validation Rules

| Resource Type | Validation | Error on Failure |
|---------------|------------|------------------|
| **Paradigm** | File exists, valid JSON, required fields present | `ParadigmNotFoundError` |
| **Prompt** | File exists | `PromptNotFoundError` |
| **Data** | File exists (or mark as optional) | `DataFileNotFoundError` or skip |
| **Script** | File exists, valid Python | `ScriptNotFoundError` |

---

# Part VI: Practical Guide

## 6.1 Common Patterns

### Pattern 1: LLM Operation with Prompt (h_Literal)

```ncd
<= ::(classify operation type) | ?{sequence}: imperative
    |%{norm_input}: v_PromptLocation-h_Literal-c_GenerateThinkJson-o_Literal
    |%{v_input_norm}: prompt_location
    |%{v_input_provision}: provisions/prompts/phase_3/classify_operation.md
    |%{h_input_norm}: Literal
<- {operation context} | ?{flow_index}: 1.2
    |%{file_location}: (from previous inference output)
```

**Key**: Value concept has perceptual sign → MVP perceives → h_input_norm is `Literal`.

### Pattern 2: File Read Operation (h_LiteralPath)

```ncd
<= ::(read progress from file if exists) | ?{sequence}: imperative
    |%{norm_input}: h_LiteralPath-c_ReadFileIfExists-o_Literal
    |%{h_input_norm}: literal_path
<- {progress file path} | ?{flow_index}: 1.2
    |%{literal<$% file_path>}: provisions/data/progress.json
```

**Key**: Value concept is literal → MVP passes through → paradigm reads file internally.

### Pattern 3: Python Script Execution

```ncd
<= ::(check if phase 1 already complete in progress) | ?{sequence}: imperative
    |%{norm_input}: h_Literal-c_CheckPhaseComplete-o_Boolean
    |%{h_input_norm}: Literal
<- {current progress} | ?{flow_index}: 1.2
    |%{file_location}: (from previous inference output)
```

**Key**: Value concept has perceptual sign → MVP perceives → h_input_norm is `Literal`.

### Pattern 4: Multi-File Selection

```ncd
<= ::(select input files) | ?{sequence}: imperative
    |%{norm_input}: h_LiteralUserPrompt-c_MultiFilePicker-o_ListFileLocation
    |%{h_input_norm}: literal_user_prompt
<- {selection prompt} | ?{flow_index}: 1.2
```

**Output**: List of file locations: `[%{file_location}(path1), %{file_location}(path2), ...]`

---

## 6.2 Best Practices

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

## 6.3 Error Handling

### Missing Resource Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `ParadigmNotFoundError` | Paradigm ID not in path_mapping or file missing | Add paradigm to provisions/ or fix path_mapping.json |
| `PromptNotFoundError` | Prompt path doesn't resolve to existing file | Create prompt file or fix v_input_provision annotation |
| `DataFileNotFoundError` | Data file path doesn't exist | Create data file, fix path, or mark as optional |
| `InvalidParadigmError` | Paradigm JSON missing required fields | Fix paradigm JSON structure |

### Runtime Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `KeyError: 'paradigm_config'` | Paradigm tries to access `states.function.paradigm_config.vertical.*` | Use `perception_router.strip_sign` on `states.vertical` instead (see Section 3.5) |
| `AttributeError: 'NoneType' has no attribute 'main'` | Paradigm calls `main` but script doesn't define it | Add a `main` function alias to the script (see Section 4.1) |
| `KeyError: 'input_1'` | Script expects named parameters but receives different names | Use `input_1`, `input_2`, etc. pattern in function signature |

### Validation Warnings

| Warning | Cause | Impact |
|---------|-------|--------|
| `UnusedParadigmWarning` | Paradigm in provisions/ not referenced by plan | Cleanup opportunity |
| `UnmappedPathWarning` | Path not in path_mapping.json (using direct path) | May work, but lacks indirection benefits |

---

# Summary

## The Demand/Supply Model

| Aspect | Post-Formalization (Demand) | Provision in Activation (Supply) |
|--------|---------------------------|----------------------------------|
| **Action** | Annotate paths in .ncd | Validate and resolve paths |
| **Paradigms** | Specify ID in `\|%{norm_input}` | Load JSON, validate structure |
| **Prompts** | Specify path in `\|%{v_input_provision}` | Validate file exists |
| **Data** | Specify path in `\|%{file_location}` | Validate, create perceptual signs |
| **Output** | Enriched .ncd with annotations | JSON repos with resolved resources |
| **Validation** | None (just strings) | Full existence and format checks |

## Key Takeaways

1. **Value concept annotations control MVP behavior** — `|%{file_location}` triggers perception; `|%{literal<$%...>}` passes through
2. **The paradigm is a continuation of MVP** — it receives what MVP produces
3. **The h_input_norm must be consistent** — if MVP perceives, use `Literal`; if not, describe the literal type
4. **Post-Formalization declares demands** — just string paths, no validation
5. **Activation supplies resources** — validates, resolves, embeds
6. **FormatterTool mirrors PerceptionRouter** — encode/decode symmetry for chaining inferences
7. **Vertical inputs must be stripped** — use `perception_router.strip_sign` on `states.vertical` to extract raw paths in paradigms
8. **Scripts should provide a `main` alias** — paradigms call `main`, delegate to descriptive function names

## The Provision Promise

Every resource demand declared in Post-Formalization will be validated and resolved before execution begins. No runtime surprises from missing files.

---

## Next Steps

- **[Activation](activation.md)** — Full activation phase documentation
- **[Post-Formalization](post_formalization.md)** — How demands are declared
- **[Execution Overview](../3_execution/overview.md)** — How provisions are consumed at runtime

---

**Ready to create provisions?** Start by setting up your `provisions/` directory structure and `path_mapping.json`, then run validation to catch issues early.
