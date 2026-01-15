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
- `depth`: Indentation level (0 = root, 1 = first child, etc.)
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<=` for functional concepts)

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For timing:

1. **Extract the condition** - Strip the `<=` marker and find the condition
2. **Determine operator type** - `@:'` (if true) or `@:!` (if false)
3. **Construct gate syntax** - Reference the condition proposition
4. **Add flow index annotation** - Use the `flow_index` from input
5. **Add sequence type annotation** - `?{sequence}: timing`
6. **Calculate indentation** - Use `depth × 4 spaces`

## Indentation Rule

The formalized line MUST include proper indentation based on the `depth` field:

- **Indentation = depth × 4 spaces**
- `depth: 0` → No indentation (root level)
- `depth: 1` → 4 spaces
- `depth: 2` → 8 spaces
- `depth: 3` → 12 spaces

## Timing Operators

| Operator | Pattern in Content | Meaning | Syntax |
|----------|-------------------|---------|--------|
| `@:'` | "when", "if", "only if" | Execute if TRUE | `@:'(<condition>)` |
| `@:!` | "unless", "if not", "when not" | Execute if FALSE | `@:!(<condition>)` |
| `@.` | "after", "once complete" | After dependency | `@.({dependency})` |

### Format
```
[INDENTATION]<= @:'(<condition>) | ?{flow_index}: X.X.X | ?{sequence}: timing
```

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Indentation | Hierarchy level | 4 spaces per depth |
| `<=` | Functional concept marker | Already in input |
| `@:'` or `@:!` or `@.` | Timing operator | Conditional or sequencing |
| `(<...>)` | Condition proposition | `(<is object type>)` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.1.1` |
| `?{sequence}:` | Sequence type | `?{sequence}: timing` |

## Examples

**Input (positive gate, depth 3):**
```json
{
  "flow_index": "1.1.1",
  "content": "<= when condition holds",
  "depth": 3,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
            <= @:'(<condition>) | ?{flow_index}: 1.1.1 | ?{sequence}: timing
```
(12 spaces indentation for depth 3)

**Explanation**: "when" → `@:'` (execute if true)

---

**Input (if type check, depth 3):**
```json
{
  "flow_index": "2.3.1",
  "content": "<= if is object type",
  "depth": 3,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
            <= @:'(<is object type>) | ?{flow_index}: 2.3.1 | ?{sequence}: timing
```
(12 spaces indentation for depth 3)

**Explanation**: "if is object type" → `@:'` with condition `<is object type>`

---

**Input (negative gate, depth 2):**
```json
{
  "flow_index": "1.2.1",
  "content": "<= unless validation failed",
  "depth": 2,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
        <= @:!(<validation failed>) | ?{flow_index}: 1.2.1 | ?{sequence}: timing
```
(8 spaces indentation for depth 2)

**Explanation**: "unless" → `@:!` (execute if false)

---

**Input (after dependency, depth 2):**
```json
{
  "flow_index": "3.1",
  "content": "<= after parsing complete",
  "depth": 2,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
        <= @.({parsing complete}) | ?{flow_index}: 3.1 | ?{sequence}: timing
```
(8 spaces indentation for depth 2)

**Explanation**: "after" → `@.` (sequencing dependency)

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) which operator was chosen (@:', @:!, @.) and why, 2) what condition/dependency was identified, 3) the indentation calculated",
  "result": "[INDENTATION]<= @X(<condition>) | ?{flow_index}: X.X.X | ?{sequence}: timing"
}
```

**Important**: 
- The `result` must be the complete formalized line as a single string
- Include the correct indentation (depth × 4 spaces) at the START of the line
- Include BOTH `?{flow_index}:` AND `?{sequence}: timing` annotations
- The condition should be wrapped in `<...>` for propositions or `{...}` for objects
