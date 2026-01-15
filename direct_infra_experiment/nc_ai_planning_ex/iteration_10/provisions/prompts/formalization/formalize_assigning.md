# Formalize Assigning Operator

Transform a natural language selection/binding into formal assigning `$` syntax.

## Input

You are given a parsed concept line from an `.ncds` file that has been judged as **assigning** type:

```json
$input_1
```

The input includes:
- `flow_index`: The hierarchical address for this step (e.g., "1.1")
- `content`: The full line including marker (e.g., `"<= select first valid formalization result"`)
- `depth`: Indentation level
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<=` for functional concepts)
- `concept_type`: May be null (you're adding it)
- `concept_name`: May be null

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For assigning:

1. **Extract the operation** - Strip the `<=` marker from content
2. **Determine operator type** - Which `$` variant based on the action
3. **Construct operator syntax** - With appropriate modifiers
4. **Add flow index** - Use the `flow_index` from input
5. **Add sequence type** - `?{sequence}: assigning`

## Assigning Operators

| Operator | Pattern in Content | Meaning | Syntax |
|----------|-------------------|---------|--------|
| `$.` | "select", "pick", "first valid" | Specification | `$. %>({source})` |
| `$=` | "return", "pass through", "use this" | Identity | `$= %>({source})` |
| `$%` | "extract", "abstract" | Abstraction | `$% %>({source})` |
| `$+` | "append", "add to" | Continuation | `$+ %>({target}) %<({item})` |
| `$-` | "remove", "filter out" | Selection | `$- %>({source})` |

### Format
```
<= $. %>({concept}) | ?{flow_index}: X.X.X | ?{sequence}: assigning
```

## Examples

**Input (select first valid):**
```json
{
  "flow_index": "1.1",
  "content": "<= select first valid formalization result",
  "depth": 2,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= $. %>({formalization result}) | ?{flow_index}: 1.1 | ?{sequence}: assigning
```

**Explanation**: "select first valid" → `$.` (specification), source is "formalization result"

---

**Input (return/pass through):**
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
<= $= %>({completed .ncd output}) | ?{flow_index}: 1.1 | ?{sequence}: assigning
```

**Explanation**: "return" → `$=` (identity/pass through)

---

**Input (return status):**
```json
{
  "flow_index": "2.1",
  "content": "<= return .ncd file status after processing this line",
  "depth": 2,
  "type": "main",
  "inference_marker": "<=",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<= $. %>({.ncd file status}) | ?{flow_index}: 2.1 | ?{sequence}: assigning
```

**Explanation**: "return... status" suggests selecting a specific result → `$.`

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) which operator was chosen ($., $=, $%, $+, $-) and why, 2) what source concept was identified",
  "result": "<= $X %>({concept}) | ?{flow_index}: X.X.X | ?{sequence}: assigning"
}
```

**Important**: The `result` must be the complete formalized line as a single string, ready to be written to the `.ncd` file.
