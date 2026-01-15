# Judge Concept Type

Determine what type of concept this line represents, based on its natural language content.

## Input

You are given a parsed concept line from an `.ncds` file:

```json
$input_1
```

The input includes:
- `flow_index`: The hierarchical address for this step (e.g., "1.2.1")
- `content`: The full line including marker (e.g., `"<- current .ncd content"`)
- `depth`: Indentation level (0 = root, 1 = first child, etc.)
- `type`: Line type ("main" for concepts, "comment" for comments)
- `inference_marker`: The marker found (`<-`, `<=`, `<*`, or null)

**Important**: `.ncds` is a draft format with natural language content. It does NOT contain formal syntax like `{}`, `[]`, `<>`, or `::()`. Your job is to analyze the natural language and determine what type it SHOULD become.

## How to Determine Type

### Step 1: Check the Inference Marker

| Marker | Meaning | Possible Types |
|--------|---------|----------------|
| `<-` | Value concept | object, relation, proposition |
| `<=` | Functional concept | imperative, judgement, OR syntactic operator |
| `<*` | Context concept | Usually object (loop variable) |

### Step 2: Analyze the Natural Language Content

**For Value Concepts (`<-` or `<*`):**

| Pattern in Content | Type | Examples |
|-------------------|------|----------|
| Singular noun/thing | **object** | "document", "result", "file path", "digit sum", "current line" |
| Plural noun / "all X" / collection | **relation** | "documents", "all files", "parsed lines", "concept lines" |
| Boolean/state phrase ("is X", "has X", "X passed") | **proposition** | "is valid", "file exists", "validation passed", "is object type" |

**For Functional Concepts (`<=`):**

First check for syntactic operator patterns, then fall back to semantic types:

| Pattern in Content | Type | Examples |
|-------------------|------|----------|
| "for each", "iterate", "loop through" | **looping** | "for each concept line in lines" |
| "collect", "bundle", "gather", "combine" | **grouping** | "collect all results", "bundle inputs" |
| "if", "when", "only if", "execute if" | **timing** | "if is object type", "when validation passed" |
| "select", "pick", "choose", "return", "first valid" | **assigning** | "select first valid", "return the result" |
| "check if", "validate", "is X?", "determine if", "verify", "judge" | **judgement** | "check if type equals object", "validate input", "judge what type" |
| Action verb (transform/produce/parse/filter/append/write) | **imperative** | "parse file", "filter lines", "append to content", "write to file" |

### Step 3: Priority Rules

1. **Syntactic operators first**: If a functional concept matches a syntactic pattern (looping, grouping, timing, assigning), use that
2. **Judgement vs Imperative**: If it's evaluating/checking something (returns boolean), it's judgement. If it's doing/producing something, it's imperative
3. **Relation vs Object**: Plurals and "all X" patterns are relations. Singular things are objects
4. **Proposition**: Phrases describing a state or condition that could be true/false (often starts with "is", "has", or ends with "passed", "valid", "complete")

## Examples

**Input**: `{"content": "<- parsed lines", "inference_marker": "<-", "depth": 1}`
- Marker `<-` = value concept
- "parsed lines" = plural noun
- **Result**: `relation`

**Input**: `{"content": "<= parse .ncds file into JSON list of lines", "inference_marker": "<=", "depth": 1}`
- Marker `<=` = functional concept
- "parse... into..." = action verb (transforming)
- **Result**: `imperative`

**Input**: `{"content": "<= for each concept line in concept lines", "inference_marker": "<=", "depth": 1}`
- Marker `<=` = functional concept
- "for each" = iteration pattern
- **Result**: `looping`

**Input**: `{"content": "<= check if concept type equals object", "inference_marker": "<=", "depth": 2}`
- Marker `<=` = functional concept
- "check if" = evaluation pattern
- **Result**: `judgement`

**Input**: `{"content": "<- is object type", "inference_marker": "<-", "depth": 2}`
- Marker `<-` = value concept
- "is object type" = boolean state
- **Result**: `proposition`

**Input**: `{"content": "<= return the completed .ncd output", "inference_marker": "<=", "depth": 1}`
- Marker `<=` = functional concept
- "return" = assigning pattern
- **Result**: `assigning`

**Input**: `{"content": "<* concept line", "inference_marker": "<*", "depth": 2}`
- Marker `<*` = context concept (loop variable)
- "concept line" = singular noun
- **Result**: `object`

## Output

Return JSON with your reasoning and the determined type:

```json
{
  "thinking": "Explain: 1) what marker was found, 2) what pattern in the content led to this type",
  "result": "object|relation|proposition|imperative|judgement|assigning|grouping|timing|looping"
}
```

**Important**: The `result` must be exactly one of these 9 type strings.
