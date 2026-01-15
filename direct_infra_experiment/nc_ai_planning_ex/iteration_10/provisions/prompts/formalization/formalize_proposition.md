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
- `depth`: Indentation level
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<-` for value, `<*` for context)
- `concept_type`: May be null (you're adding it)
- `concept_name`: May be null

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For propositions:

1. **Extract the concept name** - Strip the `<-` or `<*` marker from content
2. **Wrap in `<>` syntax** - Mark as proposition (truth value)
3. **Keep the original marker** - `<-` for value, `<*` for context
4. **Add flow index** - Use the `flow_index` from input

**Transformation**:
```
Input content:  "<- is object type"
                 ↓ strip "<- "
Name:           "is object type"
                 ↓ wrap in <>
Proposition:    "<is object type>"
                 ↓ add marker and flow index
Output:         "<- <is object type> | ?{flow_index}: 1.2"
```

**Note**: Reference axes, shapes, and element types are added later in Post-Formalization (Phase 3.3). Do NOT add those here.

## Proposition Syntax

### Format
```
<- <concept name> | ?{flow_index}: X.X.X
```

Or for context concepts (in timing gates):
```
<* <concept name> | ?{flow_index}: X.X.X
```

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| `<-` or `<*` | Value/context marker | Keep from input |
| `<...>` | Proposition wrapper | `<is valid>` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.2` |

### When to Use Proposition

- **"is X" patterns**: "is object type", "is valid"
- **State phrases**: "validation passed", "file exists"
- **Boolean conditions**: "ready", "complete", "has error"

## Examples

**Input (value concept):**
```json
{
  "flow_index": "1.2",
  "content": "<- is object type",
  "depth": 2,
  "type": "main",
  "inference_marker": "<-",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<- <is object type> | ?{flow_index}: 1.2
```

---

**Input:**
```json
{
  "flow_index": "2.3.1",
  "content": "<- validation passed",
  "depth": 3,
  "type": "main",
  "inference_marker": "<-",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<- <validation passed> | ?{flow_index}: 2.3.1
```

---

**Input (context concept for timing gate):**
```json
{
  "flow_index": "1.3",
  "content": "<* is object type",
  "depth": 2,
  "type": "main",
  "inference_marker": "<*",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<* <is object type> | ?{flow_index}: 1.3
```

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) what boolean/state was extracted, 2) the marker used (<- or <*)",
  "result": "<- <concept name> | ?{flow_index}: X.X.X"
}
```

**Important**: The `result` must be the complete formalized line as a single string, ready to be written to the `.ncd` file.
