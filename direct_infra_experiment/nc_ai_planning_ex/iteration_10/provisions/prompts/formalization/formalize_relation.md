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
- `depth`: Indentation level (0 = root, 1 = first child, etc.)
- `type`: Line type (usually "main" for concepts)
- `inference_marker`: The marker found (`<-` for value concepts)

## What Formalization Does

**Formalization (Phase 2)** adds structural annotations to natural language. For relations:

1. **Extract the concept name** - Strip the `<-` marker from content
2. **Wrap in `[]` syntax** - Mark as relation (collection/plural)
3. **Add flow index annotation** - Use the `flow_index` from input
4. **Calculate indentation** - Use `depth × 4 spaces`

## Indentation Rule

The formalized line MUST include proper indentation based on the `depth` field:

- **Indentation = depth × 4 spaces**
- `depth: 0` → No indentation (root level)
- `depth: 1` → 4 spaces
- `depth: 2` → 8 spaces
- `depth: 3` → 12 spaces

## Relation Syntax

### Format
```
[INDENTATION]<- [concept name] | ?{flow_index}: X.X.X
```

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Indentation | Hierarchy level | 4 spaces per depth |
| `<-` | Value concept marker | Keep from input |
| `[...]` | Relation wrapper | `[documents]` |
| `?{flow_index}:` | Step address | `?{flow_index}: 1.2` |

### When to Use Relation

- **Plural nouns**: "documents", "files", "lines"
- **"all X" patterns**: "all results", "all formalized lines"
- **Collections**: "concept lines", "parsed lines"

## Examples

**Input (depth 1):**
```json
{
  "flow_index": "1.2",
  "content": "<- parsed lines",
  "depth": 1,
  "type": "main",
  "inference_marker": "<-"
}
```

**Output:**
```
    <- [parsed lines] | ?{flow_index}: 1.2
```
(4 spaces indentation for depth 1)

---

**Input (depth 1):**
```json
{
  "flow_index": "1.3",
  "content": "<- concept lines",
  "depth": 1,
  "type": "main",
  "inference_marker": "<-"
}
```

**Output:**
```
    <- [concept lines] | ?{flow_index}: 1.3
```
(4 spaces indentation for depth 1)

---

**Input (depth 2):**
```json
{
  "flow_index": "2.1.1",
  "content": "<- all formalized results",
  "depth": 2,
  "type": "main",
  "inference_marker": "<-"
}
```

**Output:**
```
        <- [all formalized results] | ?{flow_index}: 2.1.1
```
(8 spaces indentation for depth 2)

## Output

Return JSON with your reasoning and the formalized line:

```json
{
  "thinking": "Explain: 1) what collection name was extracted, 2) why it's a relation (plural/collection), 3) the indentation calculated",
  "result": "[INDENTATION]<- [concept name] | ?{flow_index}: X.X.X"
}
```

**Important**: 
- The `result` must be the complete formalized line as a single string
- Include the correct indentation (depth × 4 spaces) at the START of the line
- Include the flow_index annotation at the END of the line
