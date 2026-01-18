# Formalize Object Concept

Transform a natural language value concept into formal object `{name}` syntax.

## Input

You are given a parsed concept line from an `.ncds` file that has been judged as **object** type:

```json
$input_1
```

The input includes:
- `flow_index`: The hierarchical address for this step (e.g., "1.2")
- `content`: The full line including marker (e.g., `"<- current .ncd content"`)
- `depth`: Indentation level (0 = root, 1 = first child, etc.)
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<-` for value concepts, `<*` for context)

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For objects:

1. **Extract the concept name** - Strip the `<-` or `<*` marker from content
2. **Wrap in `{}` syntax** - Mark as object (singular entity)
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

## Object Syntax

### Format
```
[INDENTATION]<- {concept name} | ?{flow_index}: X.X.X
```

Or for context concepts:
```
[INDENTATION]<* {concept name} | ?{flow_index}: X.X.X
```

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Indentation | Hierarchy level | 4 spaces per depth |
| `<-` or `<*` | Value/context marker | Keep from input |
| `{...}` | Object wrapper | `{document}` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.2` |

## Examples

**Input (value concept, depth 2):**
```json
{
  "flow_index": "1.2",
  "content": "<- current .ncd content",
  "depth": 2,
  "type": "main",
  "inference_marker": "<-"
}
```

**Output:**
```
        <- {current .ncd content} | ?{flow_index}: 1.2
```
(8 spaces indentation for depth 2)

---

**Input (depth 1):**
```json
{
  "flow_index": "2.1.1",
  "content": "<- .ncds file",
  "depth": 1,
  "type": "main",
  "inference_marker": "<-"
}
```

**Output:**
```
    <- {.ncds file} | ?{flow_index}: 2.1.1
```
(4 spaces indentation for depth 1)

---

**Input (depth 3):**
```json
{
  "flow_index": "1.3.2",
  "content": "<- formalized line",
  "depth": 3,
  "type": "main",
  "inference_marker": "<-"
}
```

**Output:**
```
            <- {formalized line} | ?{flow_index}: 1.3.2
```
(12 spaces indentation for depth 3)

---

**Input (context concept, depth 2):**
```json
{
  "flow_index": "1.4",
  "content": "<* concept line",
  "depth": 2,
  "type": "main",
  "inference_marker": "<*"
}
```

**Output:**
```
        <* {concept line} | ?{flow_index}: 1.4
```
(8 spaces indentation for depth 2)

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) what concept name was extracted, 2) the marker used (<- or <*), 3) the indentation calculated",
  "result": "[INDENTATION]<- {concept name} | ?{flow_index}: X.X.X"
}
```

**Important**: 
- The `result` must be the complete formalized line as a single string
- Include the correct indentation (depth × 4 spaces) at the START of the line
- Include the flow_index annotation at the END of the line
