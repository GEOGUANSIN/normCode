# Formalize Imperative Concept

Transform a natural language action into formal imperative `::()` syntax.

## Input

You are given a parsed concept line from an `.ncds` file that has been judged as **imperative** type:

```json
$input_1
```

The input includes:
- `flow_index`: The hierarchical address for this step (e.g., "1.1")
- `content`: The full line including marker (e.g., `"<= parse .ncds file into JSON"`)
- `depth`: Indentation level (0 = root, 1 = first child, etc.)
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<=` for functional concepts)

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For imperatives:

1. **Extract the action description** - Strip the `<=` marker from content
2. **Wrap in `::()` syntax** - Mark as imperative action
3. **Add flow index annotation** - Use the `flow_index` from input
4. **Add sequence type annotation** - `?{sequence}: imperative`
5. **Calculate indentation** - Use `depth × 4 spaces`

**Note**: Paradigms, provisions, and resource paths are added later in Post-Formalization (Phase 3). Do NOT add those here.

## Indentation Rule

The formalized line MUST include proper indentation based on the `depth` field:

- **Indentation = depth × 4 spaces**
- `depth: 0` → No indentation (root level)
- `depth: 1` → 4 spaces
- `depth: 2` → 8 spaces
- `depth: 3` → 12 spaces

## Imperative Syntax

### Format
```
[INDENTATION]<= ::(action description) | ?{flow_index}: X.X.X | ?{sequence}: imperative
```

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Indentation | Hierarchy level | 4 spaces per depth |
| `<=` | Functional concept marker | Already in input |
| `::(...)` | Imperative wrapper | `::(parse file)` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.2.1` |
| `?{sequence}:` | Sequence type | `?{sequence}: imperative` |

## Examples

**Input (depth 1):**
```json
{
  "flow_index": "1.1",
  "content": "<= parse .ncds file into JSON list of lines",
  "depth": 1,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
    <= ::(parse .ncds file into JSON list of lines) | ?{flow_index}: 1.1 | ?{sequence}: imperative
```
(4 spaces indentation for depth 1)

---

**Input (depth 2):**
```json
{
  "flow_index": "1.2.1",
  "content": "<= filter out comment lines from parsed lines",
  "depth": 2,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
        <= ::(filter out comment lines from parsed lines) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
```
(8 spaces indentation for depth 2)

---

**Input (depth 3):**
```json
{
  "flow_index": "2.3.1",
  "content": "<= append formalized line to current content",
  "depth": 3,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
            <= ::(append formalized line to current content) | ?{flow_index}: 2.3.1 | ?{sequence}: imperative
```
(12 spaces indentation for depth 3)

---

**Input (depth 3):**
```json
{
  "flow_index": "2.4.1",
  "content": "<= write updated .ncd to output path",
  "depth": 3,
  "type": "main",
  "inference_marker": "<="
}
```

**Output:**
```
            <= ::(write updated .ncd to output path) | ?{flow_index}: 2.4.1 | ?{sequence}: imperative
```
(12 spaces indentation for depth 3)

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) the action being wrapped, 2) the flow index used, 3) the indentation calculated",
  "result": "[INDENTATION]<= ::(action description) | ?{flow_index}: X.X.X | ?{sequence}: imperative"
}
```

**Important**: 
- The `result` must be the complete formalized line as a single string
- Include the correct indentation (depth × 4 spaces) at the START of the line
- Include BOTH `?{flow_index}:` AND `?{sequence}: imperative` annotations
