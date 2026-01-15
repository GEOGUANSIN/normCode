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
- `depth`: Indentation level
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<-` for value concepts, `<*` for context)
- `concept_type`: May be null (you're adding it)
- `concept_name`: May be null

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For objects:

1. **Extract the concept name** - Strip the `<-` or `<*` marker from content
2. **Wrap in `{}` syntax** - Mark as object (singular entity)
3. **Keep the original marker** - `<-` for value, `<*` for context
4. **Add flow index** - Use the `flow_index` from input

**Transformation**:
```
Input content:  "<- current .ncd content"
                 ↓ strip "<- "
Name:           "current .ncd content"
                 ↓ wrap in {}
Object:         "{current .ncd content}"
                 ↓ add marker and flow index
Output:         "<- {current .ncd content} | ?{flow_index}: 1.2"
```

**Note**: Reference axes, shapes, and element types are added later in Post-Formalization (Phase 3.3). Do NOT add those here.

## Object Syntax

### Format
```
<- {concept name} | ?{flow_index}: X.X.X
```

Or for context concepts:
```
<* {concept name} | ?{flow_index}: X.X.X
```

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| `<-` or `<*` | Value/context marker | Keep from input |
| `{...}` | Object wrapper | `{document}` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.2` |

## Examples

**Input (value concept):**
```json
{
  "flow_index": "1.2",
  "content": "<- current .ncd content",
  "depth": 2,
  "type": "main",
  "inference_marker": "<-",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<- {current .ncd content} | ?{flow_index}: 1.2
```

---

**Input:**
```json
{
  "flow_index": "2.1.1",
  "content": "<- .ncds file",
  "depth": 1,
  "type": "main",
  "inference_marker": "<-",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<- {.ncds file} | ?{flow_index}: 2.1.1
```

---

**Input:**
```json
{
  "flow_index": "1.3.2",
  "content": "<- formalized line",
  "depth": 3,
  "type": "main",
  "inference_marker": "<-",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<- {formalized line} | ?{flow_index}: 1.3.2
```

---

**Input (context concept):**
```json
{
  "flow_index": "1.4",
  "content": "<* concept line",
  "depth": 2,
  "type": "main",
  "inference_marker": "<*",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<* {concept line} | ?{flow_index}: 1.4
```

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) what concept name was extracted, 2) the marker used (<- or <*)",
  "result": "<- {concept name} | ?{flow_index}: X.X.X"
}
```

**Important**: The `result` must be the complete formalized line as a single string, ready to be written to the `.ncd` file.
