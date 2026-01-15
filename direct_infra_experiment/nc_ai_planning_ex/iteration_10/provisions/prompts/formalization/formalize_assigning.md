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
- `depth`: Indentation level (0 = root, 1 = first child, etc.)
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<=` for functional concepts)

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For assigning:

1. **Extract the operation** - Strip the `<=` marker from content
2. **Determine operator type** - Which `$` variant based on the action
3. **Construct operator syntax** - With appropriate modifiers
4. **Add flow index annotation** - Use the `flow_index` from input
5. **Add sequence type annotation** - `?{sequence}: assigning`
6. **Calculate indentation** - Use `depth × 4 spaces`

## Indentation Rule

The formalized line MUST include proper indentation based on the `depth` field:

- **Indentation = depth × 4 spaces**
- `depth: 0` → No indentation (root level)
- `depth: 1` → 4 spaces
- `depth: 2` → 8 spaces
- `depth: 3` → 12 spaces

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
[INDENTATION]<= $X %>({concept}) | ?{flow_index}: X.X.X | ?{sequence}: assigning
```

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Indentation | Hierarchy level | 4 spaces per depth |
| `<=` | Functional concept marker | Already in input |
| `$X` | Assigning operator | `$.`, `$=`, `$%`, `$+`, `$-` |
| `%>({...})` | Source concept | `%>({formalization result})` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.1` |
| `?{sequence}:` | Sequence type | `?{sequence}: assigning` |

## Examples

**Input (select first valid, depth 2):**
```json
{
  "flow_index": "1.1",
  "content": "<= select first valid formalization result",
  "depth": 2,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
        <= $. %>({formalization result}) | ?{flow_index}: 1.1 | ?{sequence}: assigning
```
(8 spaces indentation for depth 2)

**Explanation**: "select first valid" → `$.` (specification), source is "formalization result"

---

**Input (return/pass through, depth 1):**
```json
{
  "flow_index": "1.1",
  "content": "<= return the completed .ncd output",
  "depth": 1,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
    <= $= %>({completed .ncd output}) | ?{flow_index}: 1.1 | ?{sequence}: assigning
```
(4 spaces indentation for depth 1)

**Explanation**: "return" → `$=` (identity/pass through)

---

**Input (return status, depth 2):**
```json
{
  "flow_index": "2.1",
  "content": "<= return .ncd file status after processing this line",
  "depth": 2,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
        <= $. %>({.ncd file status}) | ?{flow_index}: 2.1 | ?{sequence}: assigning
```
(8 spaces indentation for depth 2)

**Explanation**: "return... status" suggests selecting a specific result → `$.`

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) which operator was chosen ($., $=, $%, $+, $-) and why, 2) what source concept was identified, 3) the indentation calculated",
  "result": "[INDENTATION]<= $X %>({concept}) | ?{flow_index}: X.X.X | ?{sequence}: assigning"
}
```

**Important**: 
- The `result` must be the complete formalized line as a single string
- Include the correct indentation (depth × 4 spaces) at the START of the line
- Include BOTH `?{flow_index}:` AND `?{sequence}: assigning` annotations
