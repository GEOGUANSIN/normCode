# Formalize Proposition Concept

Transform a natural language boolean/state concept into formal proposition `<name>` syntax.

## Input

You are given a parsed concept line from an `.ncds` file that has been judged as **proposition** type:

```json
$input_1
```

The input includes:
- `flow_index`: The hierarchical address for this step (e.g., "1.2")
- `content`: The full line including marker (e.g., `"<- is object type"`)
- `depth`: Indentation level (0 = root, 1 = first child, etc.)
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<-` for value, `<*` for context)

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For propositions:

1. **Extract the concept name** - Strip the `<-` or `<*` marker from content
2. **Wrap in `<>` syntax** - Mark as proposition (truth value)
3. **Keep the original marker** - `<-` for value, `<*` for context
4. **Add flow index annotation** - Use the `flow_index` from input
5. **Calculate indentation** - Use `depth × 4 spaces`

## Indentation Rule

The formalized line MUST include proper indentation based on the `depth` field:

- **Indentation = depth × 4 spaces**
- `depth: 0` → No indentation (root level)
- `depth: 1` → 4 spaces
- `depth: 2` → 8 spaces
- `depth: 3` → 12 spaces

## Proposition Syntax

### Format
```
[INDENTATION]<- <concept name> | ?{flow_index}: X.X.X
```

Or for context concepts (in timing gates):
```
[INDENTATION]<* <concept name> | ?{flow_index}: X.X.X
```

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Indentation | Hierarchy level | 4 spaces per depth |
| `<-` or `<*` | Value/context marker | Keep from input |
| `<...>` | Proposition wrapper | `<is valid>` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.2` |

### When to Use Proposition

- **"is X" patterns**: "is object type", "is valid"
- **State phrases**: "validation passed", "file exists"
- **Boolean conditions**: "ready", "complete", "has error"

## Examples

**Input (value concept, depth 2):**
```json
{
  "flow_index": "1.2",
  "content": "<- is object type",
  "depth": 2,
  "type": "main",
  "inference_marker": "<-"
}
```

**Output:**
```
        <- <is object type> | ?{flow_index}: 1.2
```
(8 spaces indentation for depth 2)

---

**Input (depth 3):**
```json
{
  "flow_index": "2.3.1",
  "content": "<- validation passed",
  "depth": 3,
  "type": "main",
  "inference_marker": "<-"
}
```

**Output:**
```
            <- <validation passed> | ?{flow_index}: 2.3.1
```
(12 spaces indentation for depth 3)

---

**Input (context concept for timing gate, depth 2):**
```json
{
  "flow_index": "1.3",
  "content": "<* is object type",
  "depth": 2,
  "type": "main",
  "inference_marker": "<*"
}
```

**Output:**
```
        <* <is object type> | ?{flow_index}: 1.3
```
(8 spaces indentation for depth 2)

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) what boolean/state was extracted, 2) the marker used (<- or <*), 3) the indentation calculated",
  "result": "[INDENTATION]<- <concept name> | ?{flow_index}: X.X.X"
}
```

**Important**: 
- The `result` must be the complete formalized line as a single string
- Include the correct indentation (depth × 4 spaces) at the START of the line
- Include the flow_index annotation at the END of the line
