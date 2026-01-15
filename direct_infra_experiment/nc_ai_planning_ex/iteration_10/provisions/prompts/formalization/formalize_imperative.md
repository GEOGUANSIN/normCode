# Formalize Imperative Concept

Transform a natural language action into formal imperative `::()` syntax.

## Input

You are given a parsed concept line from an `.ncds` file that has been judged as **imperative** type:

```json
$input_1
```

The input includes:
- `flow_index`: The hierarchical address for this step (e.g., "1.1", "2.3.1")
- `content`: The full line including marker (e.g., `"<= return the completed .ncd output"`)
- `depth`: Indentation level
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<=` for functional concepts)
- `concept_type`: May be null (you're adding it)
- `concept_name`: May be null

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For imperatives:

1. **Extract the action** - Strip the `<=` marker from content to get the action description
2. **Wrap in `::()` syntax** - Mark as imperative action
3. **Add flow index** - Use the `flow_index` from input
4. **Add sequence type** - `?{sequence}: imperative`

**Transformation**:
```
Input content:  "<= parse .ncds file into JSON list"
                 ↓ strip "<= "
Action:         "parse .ncds file into JSON list"
                 ↓ wrap in ::()
Imperative:     "::(parse .ncds file into JSON list)"
                 ↓ add marker and annotations
Output:         "<= ::(parse .ncds file into JSON list) | ?{flow_index}: 1.1 | ?{sequence}: imperative"
```

**Note**: Paradigms, provisions, and resource paths are added later in Post-Formalization (Phase 3). Do NOT add those here.

## Imperative Syntax

### Format
```
<= ::(action description) | ?{flow_index}: X.X.X | ?{sequence}: imperative
```

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| `<=` | Functional concept marker | Already in input |
| `::(...)` | Imperative wrapper | `::(parse file)` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.2.1` |
| `?{sequence}:` | Sequence type | `?{sequence}: imperative` |

## Examples

**Input:**
```json
{
  "flow_index": "1.1",
  "content": "<= parse .ncds file into JSON list of lines",
  "depth": 1,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= ::(parse .ncds file into JSON list of lines) | ?{flow_index}: 1.1 | ?{sequence}: imperative
```

**Explanation**: Strip `<=` from content, wrap action in `::()`, add annotations.

---

**Input:**
```json
{
  "flow_index": "1.2.1",
  "content": "<= filter out comment lines from parsed lines",
  "depth": 2,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= ::(filter out comment lines from parsed lines) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
```

---

**Input:**
```json
{
  "flow_index": "2.3.1",
  "content": "<= append formalized line to current content",
  "depth": 3,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= ::(append formalized line to current content) | ?{flow_index}: 2.3.1 | ?{sequence}: imperative
```

---

**Input:**
```json
{
  "flow_index": "1.1",
  "content": "<= return the completed .ncd output",
  "depth": 1,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= ::(return the completed .ncd output) | ?{flow_index}: 1.1 | ?{sequence}: imperative
```

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) what action was extracted from content, 2) the flow index from input",
  "result": "<= ::(action description) | ?{flow_index}: X.X.X | ?{sequence}: imperative"
}
```

**Important**: The `result` must be the complete formalized line as a single string, ready to be written to the `.ncd` file.
