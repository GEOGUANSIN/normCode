# Formalize Judgement Concept

Transform a natural language evaluation into formal judgement syntax with truth assertion.

## Input

You are given a parsed concept line from an `.ncds` file that has been judged as **judgement** type:

```json
$input_1
```

The input includes:
- `flow_index`: The hierarchical address for this step (e.g., "1.2.1")
- `content`: The full line including marker (e.g., `"<= check if concept type equals object"`)
- `depth`: Indentation level
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<=` for functional concepts)
- `concept_type`: May be null (you're adding it)
- `concept_name`: May be null

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For judgements:

1. **Extract the evaluation** - Strip the `<=` marker from content
2. **Wrap in `::()` syntax** - Same as imperative
3. **Add truth assertion** - Append `<{quantifier}>` to specify how to collapse results
4. **Add flow index** - Use the `flow_index` from input
5. **Add sequence type** - `?{sequence}: judgement`

**Transformation**:
```
Input content:  "<= check if concept type equals object"
                 ↓ strip "<= "
Evaluation:     "check if concept type equals object"
                 ↓ wrap in ::() and add truth assertion
Judgement:      "::(check if concept type equals object)<{ALL True}>"
                 ↓ add marker and annotations
Output:         "<= ::(check if concept type equals object)<{ALL True}> | ?{flow_index}: 1.2.1 | ?{sequence}: judgement"
```

**Note**: Paradigms, provisions, and resource paths are added later in Post-Formalization (Phase 3). Do NOT add those here.

## Judgement Syntax

### Format
```
<= ::(evaluation description)<{truth assertion}> | ?{flow_index}: X.X.X | ?{sequence}: judgement
```

### Truth Assertions

| Assertion | Meaning | When to Use |
|-----------|---------|-------------|
| `<{ALL True}>` | All elements must be true | Single check, must fully pass |
| `<{ANY True}>` | At least one element true | Any match is enough |
| `<{ALL False}>` | All elements must be false | Negative check |

**Default**: Use `<{ALL True}>` for most single-element checks.

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| `<=` | Functional concept marker | Already in input |
| `::(...)` | Evaluation wrapper | `::(check if valid)` |
| `<{...}>` | Truth assertion | `<{ALL True}>` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.2.1` |
| `?{sequence}:` | Sequence type | `?{sequence}: judgement` |

## Examples

**Input:**
```json
{
  "flow_index": "1.2.1",
  "content": "<= check if concept type equals object",
  "depth": 2,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= ::(check if concept type equals object)<{ALL True}> | ?{flow_index}: 1.2.1 | ?{sequence}: judgement
```

---

**Input:**
```json
{
  "flow_index": "2.3.1",
  "content": "<= judge what type of concept this line is",
  "depth": 3,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= ::(judge what type of concept this line is)<{ALL True}> | ?{flow_index}: 2.3.1 | ?{sequence}: judgement
```

---

**Input:**
```json
{
  "flow_index": "1.1.2",
  "content": "<= validate input format",
  "depth": 2,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= ::(validate input format)<{ALL True}> | ?{flow_index}: 1.1.2 | ?{sequence}: judgement
```

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) what evaluation was extracted, 2) what truth assertion was chosen and why",
  "result": "<= ::(evaluation description)<{truth assertion}> | ?{flow_index}: X.X.X | ?{sequence}: judgement"
}
```

**Important**: The `result` must be the complete formalized line as a single string, ready to be written to the `.ncd` file.
