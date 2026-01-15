# Formalize Relation Concept

Transform a natural language collection concept into formal relation `[name]` syntax.

## Input

You are given a parsed concept line from an `.ncds` file that has been judged as **relation** type:

```json
$input_1
```

The input includes:
- `flow_index`: The hierarchical address for this step (e.g., "1.2")
- `content`: The full line including marker (e.g., `"<- parsed lines"`)
- `depth`: Indentation level
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<-` for value concepts)
- `concept_type`: May be null (you're adding it)
- `concept_name`: May be null

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For relations:

1. **Extract the concept name** - Strip the `<-` marker from content
2. **Wrap in `[]` syntax** - Mark as relation (collection/plural)
3. **Add flow index** - Use the `flow_index` from input

**Transformation**:
```
Input content:  "<- parsed lines"
                 ↓ strip "<- "
Name:           "parsed lines"
                 ↓ wrap in []
Relation:       "[parsed lines]"
                 ↓ add marker and flow index
Output:         "<- [parsed lines] | ?{flow_index}: 1.2"
```

**Note**: Reference axes, shapes, and element types are added later in Post-Formalization (Phase 3.3). Do NOT add those here.

## Relation Syntax

### Format
```
<- [concept name] | ?{flow_index}: X.X.X
```

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| `<-` | Value concept marker | Keep from input |
| `[...]` | Relation wrapper | `[documents]` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.2` |

### When to Use Relation

- **Plural nouns**: "documents", "files", "lines"
- **"all X" patterns**: "all results", "all formalized lines"
- **Collections**: "concept lines", "parsed lines"

## Examples

**Input:**
```json
{
  "flow_index": "1.2",
  "content": "<- parsed lines",
  "depth": 1,
  "type": "main",
  "inference_marker": "<-",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<- [parsed lines] | ?{flow_index}: 1.2
```

---

**Input:**
```json
{
  "flow_index": "1.3",
  "content": "<- concept lines",
  "depth": 1,
  "type": "main",
  "inference_marker": "<-",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<- [concept lines] | ?{flow_index}: 1.3
```

---

**Input:**
```json
{
  "flow_index": "2.1.1",
  "content": "<- all formalized results",
  "depth": 2,
  "type": "main",
  "inference_marker": "<-",
  "concept_type": null,
  "concept_name": null
}
```

**Output:**
```
<- [all formalized results] | ?{flow_index}: 2.1.1
```

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) what collection name was extracted, 2) why it's a relation (plural/collection)",
  "result": "<- [concept name] | ?{flow_index}: X.X.X"
}
```

**Important**: The `result` must be the complete formalized line as a single string, ready to be written to the `.ncd` file.
