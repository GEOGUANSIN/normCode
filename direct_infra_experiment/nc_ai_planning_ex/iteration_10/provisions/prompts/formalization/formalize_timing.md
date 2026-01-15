# Formalize Timing Operator

Transform a natural language conditional into formal timing `@` syntax.

## Input

You are given a parsed concept line from an `.ncds` file that has been judged as **timing** type:

```json
$input_1
```

The input includes:
- `flow_index`: The hierarchical address for this step (e.g., "1.1.1")
- `content`: The full line including marker (e.g., `"<= when condition holds"`)
- `depth`: Indentation level
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<=` for functional concepts)
- `concept_type`: May be null (you're adding it)
- `concept_name`: May be null

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For timing:

1. **Extract the condition** - Strip the `<=` marker and find the condition
2. **Determine operator type** - `@:'` (if true) or `@:!` (if false)
3. **Construct gate syntax** - Reference the condition proposition
4. **Add flow index** - Use the `flow_index` from input
5. **Add sequence type** - `?{sequence}: timing`

## Timing Operators

| Operator | Pattern in Content | Meaning | Syntax |
|----------|-------------------|---------|--------|
| `@:'` | "when", "if", "only if" | Execute if TRUE | `@:'(<condition>)` |
| `@:!` | "unless", "if not", "when not" | Execute if FALSE | `@:!(<condition>)` |
| `@.` | "after", "once complete" | After dependency | `@.({dependency})` |

### Format
```
<= @:'(<condition>) | ?{flow_index}: X.X.X | ?{sequence}: timing
```

## Examples

**Input (positive gate):**
```json
{
  "flow_index": "1.1.1",
  "content": "<= when condition holds",
  "depth": 3,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= @:'(<condition>) | ?{flow_index}: 1.1.1 | ?{sequence}: timing
```

**Explanation**: "when" → `@:'` (execute if true)

---

**Input (if type check):**
```json
{
  "flow_index": "2.3.1",
  "content": "<= if is object type",
  "depth": 3,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= @:'(<is object type>) | ?{flow_index}: 2.3.1 | ?{sequence}: timing
```

**Explanation**: "if is object type" → `@:'` with condition `<is object type>`

---

**Input (negative gate):**
```json
{
  "flow_index": "1.2.1",
  "content": "<= unless validation failed",
  "depth": 2,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= @:!(<validation failed>) | ?{flow_index}: 1.2.1 | ?{sequence}: timing
```

**Explanation**: "unless" → `@:!` (execute if false)

---

**Input (after dependency):**
```json
{
  "flow_index": "3.1",
  "content": "<= after parsing complete",
  "depth": 2,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= @.({parsing complete}) | ?{flow_index}: 3.1 | ?{sequence}: timing
```

**Explanation**: "after" → `@.` (sequencing dependency)

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) which operator was chosen (@:', @:!, @.) and why, 2) what condition/dependency was identified",
  "result": "<= @X(<condition>) | ?{flow_index}: X.X.X | ?{sequence}: timing"
}
```

**Important**: The `result` must be the complete formalized line as a single string, ready to be written to the `.ncd` file.
