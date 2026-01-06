# Activation

**Phase 4: Generating executable JSON repositories from enriched `.ncd` files.**

---

## Overview

**Activation** is the final phase of NormCode compilation. It transforms the enriched `.ncd` file into executable JSON repositories that the Orchestrator can load and run.

**Input**: `.ncd` (enriched with post-formalization annotations)  
**Output**: `concept_repo.json` + `inference_repo.json`

**Core Task**: Extract and structure all information needed by the Orchestrator's execution engine.

### Key Sub-Tasks

| Sub-Task | Purpose | Details |
|----------|---------|---------|
| **Extraction** | Parse `.ncd` structure | Extract concepts, inferences, annotations |
| **Provision (Supply)** | Validate and resolve resources | See [Provision in Activation](provision_in_activation.md) |
| **Structuring** | Build JSON repositories | Create `working_interpretation` for each sequence |

### The Demand/Supply Model

Post-Formalization **declares demands** (resource paths as annotations). Activation **supplies resources**:

| Phase | Role | What Happens |
|-------|------|--------------|
| **Post-Formalization** | **Demand** | Annotates paths: "I need a prompt at X" |
| **Activation (Provision)** | **Supply** | Validates and resolves: "X exists and is valid" |

---

## The Activation Problem

### Why Activation Is Needed

The `.ncd` format is optimized for human readability and editability, but:
- The Orchestrator needs structured JSON
- Each sequence type expects specific `working_interpretation` fields
- References need initialization data
- Execution order needs to be determinable
- **Resource demands must be validated and resolved**

**Activation bridges the gap** between human-readable `.ncd` and machine-executable JSON.

---

## Output Structure

### Two JSON Repositories

Activation generates two separate JSON files:

| File | Purpose | Contains |
|------|---------|----------|
| **`concept_repo.json`** | Static concept definitions | All data entities with types, axes, ground values |
| **`inference_repo.json`** | Operational definitions | All inferences with `working_interpretation` |

### Why Separate?

**Design Decision**: Separating concepts from inferences allows:
- Concepts to be reused across inferences
- Independent concept initialization
- Clear separation of data (concepts) vs logic (inferences)

---

## Concept Repository

### Purpose

**`concept_repo.json`** stores static definitions of all concepts in the plan—both **value concepts** (data entities) and **function concepts** (operations).

### Structure

```json
[
  {
    "id": "c-document",
    "concept_name": "{document}",
    "type": "{}",
    "flow_indices": ["1.2", "1.3.2"],
    "description": "Input document to process",
    "is_ground_concept": true,
    "is_final_concept": false,
    "reference_data": ["%{file_location}7f2(data/input.txt)"],
    "reference_axis_names": ["_none_axis"],
    "reference_element_type": "str",
    "natural_name": "document"
  },
  {
    "id": "c-summary",
    "concept_name": "{summary}",
    "type": "{}",
    "flow_indices": ["1"],
    "description": "Final summarized output",
    "is_ground_concept": false,
    "is_final_concept": true,
    "reference_data": null,
    "reference_axis_names": ["_none_axis"],
    "reference_element_type": "str",
    "natural_name": "summary"
  },
  {
    "id": "fc-summarize-the-text",
    "concept_name": "<= ::(summarize the text)",
    "type": "({})",
    "flow_indices": ["1.1"],
    "description": "Summarize the text",
    "is_ground_concept": false,
    "is_final_concept": false,
    "reference_data": null,
    "reference_axis_names": ["_none_axis"],
    "reference_element_type": "paradigm",
    "natural_name": "summarize the text"
  }
]
```

### Two Types of Concepts

| Type | Marker | Purpose | Examples |
|------|--------|---------|----------|
| **Value Concepts** | `{}`, `[]`, `<>` | Data entities | `{document}`, `[files]`, `<is valid>` |
| **Function Concepts** | `({})`, `<{}>` | Operations | `<= ::(summarize)`, `<= $. %>({x})` |

**Important**: Function concepts MUST be included in concept_repo.json. The orchestrator looks up each `function_concept` from inference_repo in the concept_repo.

### Fields

| Field | Type | Purpose | Example |
|-------|------|---------|---------|
| `id` | string | Unique identifier for the concept | `"c-document"`, `"fc-summarize"` |
| `concept_name` | string | Full concept name with markers | `"{document}"`, `"<= ::(summarize)"` |
| `type` | string | Semantic type | `"{}"`, `"[]"`, `"<>"`, `"({})"`, `"<{}>"` |
| `flow_indices` | array | All flow indices where concept appears | `["1.2", "1.3.2"]` |
| `description` | string | Optional description | `"Input document to process"` |
| `is_ground_concept` | boolean | Pre-initialized? | `true` for inputs |
| `is_final_concept` | boolean | Final output? | `true` for root |
| `reference_data` | array or null | Initial perceptual signs | `["%{file_location}(...)"]` |
| `reference_axis_names` | array | Axis names | `["_none_axis"]`, `["signal", "date"]` |
| `reference_element_type` | string | Element data type | `"str"`, `"paradigm"`, `"operator"` |
| `natural_name` | string | Human-readable name | `"document"`, `"summarize the text"` |

### ID Prefixes

| Prefix | Concept Type | Example |
|--------|--------------|---------|
| `c-` | Value concept | `c-document`, `c-summary` |
| `fc-` | Function concept | `fc-summarize-the-text` |

### Extraction from `.ncd`

**Algorithm for Value Concepts**:

1. **Scan all value concepts** (`<-` lines) and context concepts (`<*` lines)
2. **Generate id** from concept name (e.g., `"{price data}"` → `"c-price-data"`)
3. **Extract concept name** from line
4. **Determine type** from markers (`{}`, `[]`, `<>`)
5. **Collect flow_indices**: Track all flow indices where this concept appears
6. **Check if ground**:
   - Has `:>:` marker?
   - No parent inference?
   - Has `$%` abstraction?
   - Has `|%{file_location}` annotation?
7. **Check if final**: Has `:<:` marker?
8. **Extract reference_data** from `|%{file_location}` or `$%` value
9. **Extract axes** from `|%{ref_axes}` annotation
10. **Generate natural_name** from concept name (strip markers)

**Algorithm for Function Concepts**:

1. **Scan all functional concepts** (`<=` lines)
2. **Generate id** from natural name (e.g., `"summarize the text"` → `"fc-summarize-the-text"`)
3. **Store full `nc_main`** as `concept_name` (e.g., `"<= ::(summarize the text)"`)
4. **Determine type**:
   - Judgement (contains `<{...}>`) → `"<{}>"`
   - All others (imperative, operators) → `"({})"`
5. **Collect flow_indices**: Track all flow indices where this function appears
6. **Set reference_element_type**:
   - Imperative/judgement → `"paradigm"`
   - Operators (`$`, `&`, `@`, `*`) → `"operator"`
7. **Extract natural_name** from the action description

**Why Function Concepts Are Required**:

The orchestrator's execution engine looks up each `function_concept` string from `inference_repo.json` in the `concept_repo.json`. If a function concept is missing, execution fails with:

```
'Function concept '<= ::(action name)' not found in ConceptRepo.'
```

**Example**:

**`.ncd` Input**:
```ncd
<- {price data} | ?{flow_index}: 1.2
    |%{file_location}: provision/data/prices.json
    |%{ref_axes}: [date]
    |%{ref_element}: perceptual_sign
```

**Concept Repo Entry**:
```json
{
  "id": "c-price-data",
  "concept_name": "{price data}",
  "type": "{}",
  "flow_indices": ["1.2", "1.6.2.2"],
  "description": "Price data retrieved from market sources",
  "is_ground_concept": true,
  "is_final_concept": false,
  "reference_data": ["%{file_location}price(provision/data/prices.json)"],
  "reference_axis_names": ["date"],
  "natural_name": "price data"
}
```

---

## Inference Repository

### Purpose

**`inference_repo.json`** stores operational definitions—what operations to execute and how.

### Structure

```json
[
  {
    "flow_info": {"flow_index": "1.1"},
    "inference_sequence": "imperative_in_composition",
    "concept_to_infer": "{summary}",
    "function_concept": "::(summarize the text)",
    "value_concepts": ["{clean text}"],
    "context_concepts": [],
    "working_interpretation": {
      "paradigm": "h_PromptTemplate-c_Generate-o_Text",
      "value_order": {"{clean text}": 1},
      "workspace": {},
      "flow_info": {"flow_index": "1.1"}
    }
  }
]
```

### Common Fields (All Sequences)

| Field | Type | Purpose |
|-------|------|---------|
| `flow_info` | dict | `{"flow_index": "1.2.3"}` |
| `inference_sequence` | string | Sequence type (e.g., `"imperative_in_composition"`) |
| `concept_to_infer` | string | Output concept name |
| `function_concept` | string | Operation definition |
| `value_concepts` | array | Input concept names (from `<-` lines) |
| `context_concepts` | array | Context concept names (from `<*` lines) |
| `working_interpretation` | dict | **Sequence-specific configuration** |

### The Critical Field: working_interpretation

**`working_interpretation`** is the key output of activation. It contains exactly what each sequence's IWI (Input Working Interpretation) step expects.

**Common sub-fields** (all sequences):
```json
{
  "workspace": {},
  "flow_info": {"flow_index": "1.2.3"}
}
```

**Sequence-specific fields**: Vary by sequence type (see below).

---

## Working Interpretation by Sequence Type

### 1. Imperative Sequence

**For**: `inference_sequence: "imperative_in_composition"`

**Required Fields**:
```json
{
  "paradigm": "h_PromptTemplate-c_Generate-o_Text",
  "value_order": {
    "{input 1}": 1,
    "{input 2}": 2
  },
  "workspace": {},
  "flow_info": {"flow_index": "1.1"}
}
```

**Optional Fields**:
```json
{
  "value_selectors": {
    "intermediate_key": {
      "source_concept": "{grouped_input}",
      "key": "{sub_key}",
      "index": 0,
      "branch": {"path": "NULL", "content": "file_location"}
    }
  },
  "values": {"{ground_concept}": "pre_set_value"},
  "create_axis_on_list_output": false
}
```

**Extraction**:
1. **paradigm**: From `|%{norm_input}` annotation
2. **value_order**: From `<:{N}>` bindings on value concepts
3. **value_selectors**: For concepts created by grouping (`&[{}]`)
4. **values**: For ground concepts with direct values
5. **create_axis_on_list_output**: Based on output type (`[]` → false)

### 2. Judgement Sequence

**For**: `inference_sequence: "judgement_in_composition"`

**Same as Imperative, PLUS**:
```json
{
  "assertion_condition": {
    "quantifiers": {
      "axis": "for-each",
      "concept": "{signal}"
    },
    "condition": true
  }
}
```

**Extraction**:
- **assertion_condition**: From truth assertion in functional concept
  - `<ALL True>` → `{"quantifiers": {"axis": "all"}, "condition": true}`
  - `<FOR EACH {x} True>` → `{"quantifiers": {"axis": "for-each", "concept": "{x}"}, "condition": true}`

### 3. Assigning Sequence

**For**: `inference_sequence: "assigning"`

**Required Fields**:
```json
{
  "syntax": {
    "marker": ".",
    "assign_source": "{source}",
    "assign_destination": "{destination}"
  },
  "workspace": {},
  "flow_info": {"flow_index": "1.1"}
}
```

**Marker-Specific Fields**:

| Marker | Additional Fields |
|--------|------------------|
| `"="` (identity) | `"canonical_concept"`, `"alias_concept"` |
| `"%"` (abstraction) | `"face_value"`, `"axis_names"` |
| `"."` (specification) | (none) |
| `"+"` (continuation) | `"by_axes"` |
| `"-"` (derelation) | `"selector": {"index": N}` or `{"key": "..."}` or `{"unpack": true}` |

**Extraction**:
1. **marker**: From operator symbol (`$=` → `"="`, `$.` → `"."`, etc.)
2. **assign_source**: From `%>({concept})` modifier
3. **assign_destination**: From `%<({concept})` modifier
4. **by_axes**: From `%:({axis})` modifier (for continuation)
5. **face_value**: From literal in `$% %>(...)`
6. **selector**: From `%^(<selector>)` modifier

### 4. Grouping Sequence

**For**: `inference_sequence: "grouping"`

**Required Fields**:
```json
{
  "syntax": {
    "marker": "in",
    "by_axis_concepts": ["{context_concept}"],
    "protect_axes": []
  },
  "workspace": {},
  "flow_info": {"flow_index": "1.1"}
}
```

**New Format** (per-reference collapse):
```json
{
  "syntax": {
    "marker": "across",
    "by_axes": [["axis1"], ["axis2"]],
    "create_axis": "new_axis",
    "protect_axes": []
  }
}
```

**Extraction**:
1. **marker**: From operator (`&[{}]` → `"in"`, `&[#]` → `"across"`)
2. **by_axis_concepts**: From context concepts (`<*` lines)
3. **by_axes**: From per-input axis analysis (new format)
4. **create_axis**: From `%+({axis_name})` modifier
5. **protect_axes**: From `<$!{axis}>` markers in `%:(...)` modifier

### 5. Timing Sequence

**For**: `inference_sequence: "timing"`

**Required Fields**:
```json
{
  "syntax": {
    "marker": "if",
    "condition": "<validation passed>"
  },
  "blackboard": null,
  "workspace": {},
  "flow_info": {"flow_index": "1.1"}
}
```

**Extraction**:
1. **marker**: From operator (`@:'` → `"if"`, `@:!` → `"if!"`, `@.` → `"after"`)
2. **condition**: From concept in parentheses
3. **blackboard**: Set to `null` (orchestrator provides at runtime)

### 6. Looping Sequence

**For**: `inference_sequence: "looping"` or `"quantifying"`

**Required Fields**:
```json
{
  "syntax": {
    "marker": "every",
    "loop_index": 1,
    "LoopBaseConcept": "{documents}",
    "CurrentLoopBaseConcept": "{document}*1",
    "group_base": "document",
    "InLoopConcept": {"{carry}*1": 1},
    "ConceptToInfer": ["{summary}"]
  },
  "workspace": {},
  "flow_info": {"flow_index": "1.1"}
}
```

**Extraction**:
1. **marker**: Always `"every"` (only type implemented)
2. **loop_index**: From `%@(N)` modifier
3. **LoopBaseConcept**: From `%>({base})` modifier
4. **CurrentLoopBaseConcept**: Auto-generated as `{base}*N`
5. **group_base**: From `%:({axis})` modifier (strip braces)
6. **InLoopConcept**: From context concepts with `<$*-N>` markers
7. **ConceptToInfer**: From `%<({result})` modifier

---

## Provision: The Supply Side

During activation, resource demands from Post-Formalization are validated and resolved.

**For detailed documentation, see [Provision in Activation](provision_in_activation.md).**

### Summary

| Resource Type | Demand (Post-Formalization) | Supply (Activation) |
|---------------|----------------------------|---------------------|
| **Paradigms** | `\|%{norm_input}: paradigm-id` | Load JSON, validate structure |
| **Prompts** | `\|%{v_input_provision}: path` | Validate file exists |
| **Data files** | `\|%{file_location}: path` | Validate, create perceptual signs |
| **Scripts** | Referenced by paradigm | Validate script exists |

### Key Outputs

After provision, the `working_interpretation` contains:
- Validated paradigm IDs
- Resolved prompt paths
- Ground concept `reference_data` with perceptual signs

---

## Extraction Strategy

### Meet from Both Ends

Activation uses a **bidirectional approach**:

1. **Bottom-up (Execution Requirements)**: Know what each IWI step expects
2. **Top-down (Extraction Rules)**: Parse `.ncd` syntax to produce that structure

### The Syntax Mapping Task

**Core challenge**: Transform dense `.ncd` annotations into structured `working_interpretation` dicts.

**Algorithm**:

```python
def activate_inference(ncd_inference):
    # 1. Extract basic fields
    flow_index = extract_flow_index(ncd_inference)
    sequence_type = extract_sequence_type(ncd_inference)
    concept_to_infer = extract_concept_to_infer(ncd_inference)
    function_concept = extract_function_concept(ncd_inference)
    value_concepts = extract_value_concepts(ncd_inference)
    context_concepts = extract_context_concepts(ncd_inference)
    
    # 2. Build working_interpretation based on sequence_type
    if sequence_type == "imperative_in_composition":
        wi = build_imperative_wi(ncd_inference)
    elif sequence_type == "judgement_in_composition":
        wi = build_judgement_wi(ncd_inference)
    elif sequence_type == "assigning":
        wi = build_assigning_wi(ncd_inference)
    elif sequence_type == "grouping":
        wi = build_grouping_wi(ncd_inference)
    elif sequence_type == "timing":
        wi = build_timing_wi(ncd_inference)
    elif sequence_type == "looping":
        wi = build_looping_wi(ncd_inference)
    
    # 3. Return inference entry
    return {
        "flow_info": {"flow_index": flow_index},
        "inference_sequence": sequence_type,
        "concept_to_infer": concept_to_infer,
        "function_concept": function_concept,
        "value_concepts": value_concepts,
        "context_concepts": context_concepts,
        "working_interpretation": wi
    }
```

---

## Complex Extraction: Value Selectors

### The Problem

Some `working_interpretation` dicts contain **intermediate keys** that don't appear in `value_concepts`.

**Example**:
```json
{
  "value_order": {
    "{input files}": 0,
    "input_files_as_dict": 1,
    "other_input_files": 2
  },
  "value_selectors": {
    "input_files_as_dict": {
      "source_concept": "{input files}",
      "key": "{original prompt}"
    },
    "other_input_files": {
      "source_concept": "{input files}",
      "key": "{other files}",
      "unpack": true
    }
  }
}
```

**Observation**: `"input_files_as_dict"` and `"other_input_files"` are NOT in `value_concepts`, but they ARE in `value_order`.

### Why This Happens

**Answer**: Concept provenance tracking.

When `{input files}` was created by a `&[{}]` (group-in) operation:
```ncd
<- {input files}
    <= &[{}]
    <- {original prompt}
    <- {other files}
```

The activation compiler knows:
1. `{input files}` is a dictionary with keys `"{original prompt}"` and `"{other files}"`
2. The paradigm needs these as separate inputs
3. Generate `value_selectors` to extract them

### Extraction Rules for value_selectors

**Trigger**: When a value concept was created by `&[{}]` grouping.

**Algorithm**:
1. **Trace concept provenance**: How was this concept created?
2. **If created by `&[{}]`**: Extract the sub-concept keys
3. **Generate value_selectors**: One per sub-concept
4. **Add to value_order**: Create intermediate keys

**Selector Fields**:

| Field | Purpose | Example |
|-------|---------|---------|
| `source_concept` | Which concept to extract from | `"{input files}"` |
| `key` | Dictionary key to extract | `"{original prompt}"` |
| `index` | Array index (for lists) | `0`, `-1` |
| `unpack` | Flatten/spread | `true` |
| `branch` | Perceptual sign control | `{"path": "NULL", "content": "file_location"}` |

### Branch Field

**Purpose**: Control perceptual sign transmutation.

**Example**:
```json
{
  "branch": {
    "path": "NULL",
    "content": "file_location"
  }
}
```

**Meaning**:
- `"path": "NULL"` - No path transformation
- `"content": "file_location"` - Extract file location string

**When used**: For concepts that are perceptual signs requiring transmutation.

---

## Ground Concept Identification

### What Makes a Concept "Ground"?

A concept is **ground** if it's pre-initialized (not computed by an inference).

**Criteria**:
1. Has `:>:` marker (explicit input marker)
2. Created by `$%` abstraction operator
3. Has `|%{file_location}` annotation
4. No parent inference (leaf node)
5. Marked in compilation configuration

### Extraction

**Algorithm**:
```python
def is_ground_concept(concept_ncd):
    if has_input_marker(concept_ncd):  # :>:
        return True
    if has_abstraction(concept_ncd):  # $%
        return True
    if has_file_location_annotation(concept_ncd):
        return True
    if no_parent_inference(concept_ncd):
        return True
    return False
```

**Ground concepts** get `reference_data` populated in `concept_repo.json`.

---

## Activation Validation

### Pre-Activation Checks

Before running activation, ensure:

- [ ] All inferences have flow indices
- [ ] All functional concepts have sequence types
- [ ] Paradigm annotations present (for semantic sequences)
- [ ] Axes declared (for all concepts)
- [ ] Resource paths exist (for ground concepts)

### Post-Activation Checks

After generating repositories, validate:

- [ ] All concepts in `concept_repo.json`
- [ ] All inferences in `inference_repo.json`
- [ ] All `working_interpretation` dicts complete
- [ ] All required fields present
- [ ] No orphaned references

### Common Activation Errors

| Error | Symptom | Fix |
|-------|---------|-----|
| **Missing paradigm** | No `paradigm` field in WI | Add `\|%{norm_input}` annotation |
| **Missing value_order** | Empty `value_order` dict | Add value bindings (`<:{N}>`) |
| **Invalid flow_index** | Non-hierarchical indices | Re-run formalization |
| **Missing axes** | `reference_axis_names` is null | Add `\|%{ref_axes}` annotation |
| **Wrong sequence type** | IWI expects different fields | Fix `?{sequence}:` marker |

---

## Tools and Automation

### Automated Activation

**Command** (if implemented):
```bash
python compiler.py activate enriched.ncd
```

**Output**: `enriched.concept.json` and `enriched.inference.json`

### Manual Activation

**Not recommended** - the extraction logic is complex and error-prone.

**Use automated tools** whenever possible.

### Validation Tools

**Command**:
```bash
python compiler.py validate-repos concept_repo.json inference_repo.json
```

**Checks**:
- All required fields present
- Field types correct
- References are valid
- Sequences match expectations

---

## Round-Trip: Repositories → .ncd

### Why Round-Trip Matters

Being able to go **backwards** (JSON → `.ncd`) enables:
- **Debugging**: Inspect compiled output in readable format
- **Version control**: Store as text instead of JSON
- **Modification**: Edit compiled plans
- **Validation**: Ensure compilation is lossless

### Deactivation Process

**Algorithm**:
```python
def deactivate(concept_repo, inference_repo):
    # 1. Reconstruct inference tree from flow_indices
    tree = build_tree(inference_repo)
    
    # 2. For each inference, reconstruct .ncd lines
    ncd_lines = []
    for inference in tree:
        ncd_lines.append(concept_to_ncd(inference))
        ncd_lines.append(function_to_ncd(inference))
        ncd_lines.extend(values_to_ncd(inference))
        ncd_lines.extend(contexts_to_ncd(inference))
        ncd_lines.extend(annotations_to_ncd(inference))
    
    # 3. Return formatted .ncd
    return format_ncd(ncd_lines)
```

**Challenges**:
- Reconstructing indentation from flow indices
- Determining which annotations to include
- Handling value_selectors (synthetic keys)

---

## Performance Considerations

### Activation Time

**Typical**: < 1 second for plans with 50 inferences

**Factors**:
- Number of inferences
- Complexity of value_selectors
- Paradigm lookup time

### Optimization Strategies

1. **Cache paradigm lookups**: Don't re-read paradigm files
2. **Batch concept extraction**: Process all concepts in one pass
3. **Lazy validation**: Only validate on demand

---

## Related Topics

- **[Provision in Activation](provision_in_activation.md)** - How resource demands are validated and resolved (the supply side)
- **[Post-Formalization](post_formalization.md)** - How resource demands are declared (the demand side)

## Next Steps

After activation:

- **[Execution Section](../3_execution/README.md)** - How the orchestrator runs the generated repositories
- **[Editor](editor.md)** - Tools for working with repositories

---

## Summary

### Key Takeaways

| Concept | Insight |
|---------|---------|
| **Two repositories** | Concepts (data) separated from inferences (logic) |
| **working_interpretation** | Critical field containing sequence-specific configuration |
| **Syntax mapping** | Transform `.ncd` annotations to WI dicts |
| **Value selectors** | Handle decomposition of grouped concepts |
| **Ground concepts** | Pre-initialized with reference_data |
| **Round-trip** | Can go from JSON back to `.ncd` |

### The Activation Promise

**Activation makes plans executable**:

1. Enriched `.ncd` → Structured JSON repositories
2. Each sequence gets exactly what it needs
3. Ground concepts pre-initialized
4. Ready for orchestrator loading
5. Fully auditable and traceable

**Result**: Executable repositories that the orchestrator can load and run, with complete traceability back to source `.ncd`.

---

**Ready to execute?** See the [Execution Section](../3_execution/README.md) to understand how the orchestrator runs these repositories.

**Need to edit or convert?** See [Editor](editor.md) for tools to work with all NormCode formats.
