# Judge Concept Type

Determine what type of concept this line represents, based on its natural language content.

## Input

You are given a parsed concept line from an `.ncds` file:

```json
$input_1
```

**Important**: `.ncds` is a draft format with natural language content. It does NOT contain formal syntax like `{}`, `[]`, `<>`, or `::()`. Your job is to analyze the natural language and determine what type it SHOULD become.

## How to Determine Type

### Step 1: Check the Inference Marker

| Marker | Meaning | Possible Types |
|--------|---------|----------------|
| `<-` | Value concept | object, relation, proposition |
| `<=` | Functional concept | imperative, judgement, OR syntactic operator |
| `<*` | Context concept | Usually object (loop variable) |

### Step 2: Analyze the Natural Language Content

**For Value Concepts (`<-`):**

| Pattern in Content | Type | Examples |
|-------------------|------|----------|
| Singular noun/thing | **object** | "document", "result", "file path", "digit sum" |
| Plural noun / "all X" / collection | **relation** | "documents", "all files", "parsed lines", "concept lines" |
| Boolean/state phrase | **proposition** | "is valid", "file exists", "validation passed", "is object type" |

**For Functional Concepts (`<=`):**

First check for syntactic operator patterns, then fall back to semantic types:

| Pattern in Content | Type | Examples |
|-------------------|------|----------|
| "for each", "iterate", "loop through" | **looping** | "for each concept line" |
| "collect", "bundle", "gather", "combine" | **grouping** | "collect all results", "bundle inputs" |
| "if", "when", "only if", "execute if" | **timing** | "if is object type", "when validation passed" |
| "select", "pick", "choose", "use this", "first valid" | **assigning** | "select first valid", "use the result" |
| "check if", "validate", "is X?", "determine if", "verify" | **judgement** | "check if type equals object", "validate input" |
| Action verb (transform/produce) | **imperative** | "parse file", "formalize line", "append to content" |

### Step 3: Priority Rules

1. **Syntactic operators first**: If a functional concept matches a syntactic pattern (looping, grouping, timing, assigning), use that
2. **Judgement vs Imperative**: If it's evaluating/checking something (returns boolean), it's judgement. If it's doing/producing something, it's imperative
3. **Relation vs Object**: Plurals and "all X" patterns are relations. Singular things are objects
4. **Proposition**: Phrases describing a state or condition that could be true/false

## Examples

### Value Concepts (`<-`)

**Object - Singular thing:**
```json
{"content": ".ncds file", "inference_marker": "<-", "depth": 1}
```
→ `object` (singular file reference)

```json
{"content": "current .ncd content", "inference_marker": "<-", "depth": 2}
```
→ `object` (singular content value)

```json
{"content": "formalized line", "inference_marker": "<-", "depth": 2}
```
→ `object` (singular line)

```json
{"content": "concept type", "inference_marker": "<-", "depth": 3}
```
→ `object` (singular type value)

**Relation - Collection/plural:**
```json
{"content": "parsed lines", "inference_marker": "<-", "depth": 1}
```
→ `relation` (plural - multiple lines)

```json
{"content": "concept lines", "inference_marker": "<-", "depth": 1}
```
→ `relation` (plural - multiple lines)

```json
{"content": "all formalized results", "inference_marker": "<-", "depth": 1}
```
→ `relation` ("all X" pattern = collection)

**Proposition - Boolean/state:**
```json
{"content": "is object type", "inference_marker": "<-", "depth": 2}
```
→ `proposition` ("is X" = boolean state)

```json
{"content": "validation passed", "inference_marker": "<-", "depth": 2}
```
→ `proposition` (state that is true/false)

```json
{"content": "file exists", "inference_marker": "<-", "depth": 2}
```
→ `proposition` (boolean condition)

### Functional Concepts (`<=`) - Semantic Types

**Imperative - Action/transformation:**
```json
{"content": "parse .ncds file into JSON list of lines", "inference_marker": "<=", "depth": 1}
```
→ `imperative` ("parse... into..." = transformation)

```json
{"content": "filter out comment lines from parsed lines", "inference_marker": "<=", "depth": 1}
```
→ `imperative` ("filter out" = action)

```json
{"content": "append formalized line to current content", "inference_marker": "<=", "depth": 2}
```
→ `imperative` ("append... to..." = action)

```json
{"content": "write updated .ncd to output path", "inference_marker": "<=", "depth": 2}
```
→ `imperative` ("write" = action)

```json
{"content": "read current .ncd file if exists", "inference_marker": "<=", "depth": 2}
```
→ `imperative` ("read" = action)

```json
{"content": "formalize according to object syntax", "inference_marker": "<=", "depth": 2}
```
→ `imperative` ("formalize" = transformation)

**Judgement - Evaluation/check:**
```json
{"content": "check if concept type equals object", "inference_marker": "<=", "depth": 2}
```
→ `judgement` ("check if" = evaluation)

```json
{"content": "judge what type of concept this line is", "inference_marker": "<=", "depth": 2}
```
→ `judgement` ("judge" = evaluation/decision)

```json
{"content": "validate input format", "inference_marker": "<=", "depth": 2}
```
→ `judgement` ("validate" = evaluation)

### Functional Concepts (`<=`) - Syntactic Operators

**Looping - Iteration:**
```json
{"content": "for each concept line in concept lines", "inference_marker": "<=", "depth": 1}
```
→ `looping` ("for each" = iteration)

```json
{"content": "iterate over parsed lines", "inference_marker": "<=", "depth": 1}
```
→ `looping` ("iterate over" = iteration)

**Grouping - Collection:**
```json
{"content": "collect all results together", "inference_marker": "<=", "depth": 1}
```
→ `grouping` ("collect all" = bundling)

```json
{"content": "bundle inputs into single structure", "inference_marker": "<=", "depth": 1}
```
→ `grouping` ("bundle" = bundling)

**Timing - Conditional execution:**
```json
{"content": "when condition holds", "inference_marker": "<=", "depth": 3}
```
→ `timing` ("when" = conditional gate)

```json
{"content": "if is object type", "inference_marker": "<=", "depth": 3}
```
→ `timing` ("if" = conditional gate)

```json
{"content": "execute only when validation passed", "inference_marker": "<=", "depth": 2}
```
→ `timing` ("only when" = conditional gate)

**Assigning - Selection:**
```json
{"content": "select first valid formalization result", "inference_marker": "<=", "depth": 2}
```
→ `assigning` ("select first valid" = specification)

```json
{"content": "return the completed .ncd output", "inference_marker": "<=", "depth": 1}
```
→ `assigning` ("return" = pass-through/identity)

```json
{"content": "return .ncd file status after processing this line", "inference_marker": "<=", "depth": 2}
```
→ `assigning` ("return... status" = specification)

### Context Concepts (`<*`)

```json
{"content": "concept line", "inference_marker": "<*", "depth": 2}
```
→ `object` (loop variable - current item being processed)

## Output

Return JSON with your reasoning and the determined type:

```json
{
  "thinking": "Explain: 1) what marker was found, 2) what pattern in the content led to this type",
  "result": "object|relation|proposition|imperative|judgement|assigning|grouping|timing|looping"
}
```
