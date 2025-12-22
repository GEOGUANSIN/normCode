# The `.ncn` Translation Process

**Understanding how formal NormCode (`.ncd`) is translated into natural language narratives (`.ncn`) for human review.**

---

## Overview

The `.ncn` (NormCode Narrative) format is a **natural language companion** to the formal `.ncd` syntax. It is **not** authored directly. Instead, it is **translated** (compiled) from the `.ncd` file to provide a readable, verifiable description of the plan's logic for non-technical stakeholders.

While `.ncd` provides the *near-mathematical* truth of the plan (types, bindings, indices), `.ncn` provides the *semantic* truth—a readable story of what happens.

---

## Translation Principles

The translation follows three core principles:

1. **Grammatical Correctness**: Use proper verb forms (gerunds after "by", infinitives after "to").
2. **Minimal Redundancy**: Don't repeat information already conveyed by tags.
3. **Contextual Linking**: Adapt phrasing based on number and type of inputs.

---

## Translation Logic

The compiler generates `.ncn` by traversing the `.ncd` tree and applying **transformation rules** to concepts, markers, and operators.

### 1. Concept Markers → Narrative Tags

The formal markers that define the role of a concept are translated into explicit semantic tags:

| `.ncd` Marker | Role | `.ncn` Tag | Narrative Template |
| :--- | :--- | :--- | :--- |
| `:<:` | Root Output | `(OUTPUT)` | `_Name_` |
| `<-` | Value Input | `(VALUE)` | `_Name_` |
| `<=` | Functional | `(ACTION)` | `is obtained by _Operation_` |
| `<*` | Context (general) | `(CONTEXT)` | `given _Name_` |
| `<*` | Context (in loop) | `(CONTEXT)` | `for each _Name_ in the iteration` |

> **Note**: The `(OUTPUT)` tag itself conveys "final result" semantics, so "to be outputted" is redundant and omitted.

### 2. Semantic Concepts → Action Descriptions

Functional concepts are translated based on their type, using **gerund verb forms** for grammatical correctness:

| Concept Type | `.ncd` Syntax | `.ncn` Translation |
| :--- | :--- | :--- |
| **Imperative** | `::(_action_)` | `is obtained by _action-gerund_ [inputs]` |
| **Judgement** | `::(_check_)<_assertion_>` | `is evaluated by checking whether _check_ (_assertion_)` |
| **External Input** | `:>:(_name_)` | `is provided as external input` |

**Gerund Conversion**: The action verb should be converted to gerund form:
- `summarize` → `summarizing`
- `extract` → `extracting`
- `calculate` → `calculating`

**Input Linking Patterns** (choose based on context):

| Scenario | Pattern | Example |
| :--- | :--- | :--- |
| **Single input** | `...ing the _input_` | `by summarizing the document` |
| **Multiple inputs** | `...ing the following:` | `by combining the following:` |
| **Named inputs** | `...ing _A_ with _B_` | `by comparing A with B` |

### 3. Syntactic Operators → Action Descriptions

Cryptic operators are expanded into full sentences describing their data manipulation logic:

| Operator | Symbol | `.ncn` Translation |
| :--- | :--- | :--- |
| **Identity** | `$=` | `is aliased to _Source_` |
| **Abstraction** | `$%` | `is defined as the literal value _Value_` |
| **Specification** | `$.` | `is obtained by selecting _Target_` |
| **Continuation** | `$+` | `is obtained by appending _Item_ to _Base_ along _Axis_` |
| **Selection** | `$-` | `is obtained by extracting from _Source_` |
| **Grouping (flatten)** | `&[#]` | `is obtained by collecting and flattening the following:` |
| **Grouping (labeled)** | `&[{}]` | `is obtained by bundling the following into a labeled group:` |
| **Looping** | `*.` | `is obtained by iterating over _Collection_, where each iteration yields:` |
| **Timing (conditional)** | `@:'` | `(only when _Condition_ is true)` |
| **Timing (negated)** | `@:!` | `(only when _Condition_ is false)` |
| **Timing (sequencing)** | `@.` | `(after _Dependency_ completes)` |

### 4. Semantic Bindings → Parameter Descriptions

Positional or named bindings in functional concepts are translated into readable parameter assignments:

| Binding Type | `.ncd` Syntax | `.ncn` Translation |
| :--- | :--- | :--- |
| **Positional (1st)** | `<:{1}>` | `as the first input` |
| **Positional (2nd)** | `<:{2}>` | `as the second input` |
| **Positional (Nth)** | `<:{N}>` | `as input #N` |
| **Named** | `<:{param_name}>` | `as the _param_name_` |
| **Instance** | `<$({Type})%>` | `(treated as a _Type_)` |

### 5. Special Annotations → Inline Descriptions

Inline markers are translated into parenthetical clarifications:

| Annotation | `.ncd` Syntax | `.ncn` Translation |
| :--- | :--- | :--- |
| **Loop Reference** | `{item}*1` | `_item_ (current element in loop 1)` |
| **Previous Iteration** | `{item}*-1` | `_item_ (from previous iteration)` |
| **Initial Value** | `{item}*0` | `_item_ (initial value)` |
| **Identification** | `{output}<$(<cond>)=>` | `_output_ (identified by _cond_)` |
| **Truth Assertion** | `<FOR EACH X AND ALL Y IS TRUE>` | `(true for each X when all Y conditions hold)` |
| **Axis Protection** | `<$!{axis}>` | `(preserving the _axis_ dimension)` |

---

## Translation Example

### Source: Formal `.ncd`

```ncd
:<:([all {phase 1 output}]) | ?{flow_index}: 1
    <= &[#] %>({Phase 1 output}) %: ({Phase 1 output})
    <- {Phase 1 output} | ?{flow_index}: 1.2
        <= ::{paradigm}({prompt}<$({PromptTemplate})%>; {1}<$({Input})%>)
        <- {analysis prompt}<:{prompt}>
        <- {input files}<:{1}>
```

### Translated: Narrative `.ncn`

```ncn
(OUTPUT) all phase 1 outputs
    (ACTION) is obtained by collecting and flattening the following:
    (VALUE) Phase 1 output
        (ACTION) is obtained by running the model paradigm with a prompt template
        (VALUE) analysis prompt — as the prompt
        (VALUE) input files — as the first input
```

### Step-by-Step Translation

1.  **Root**: `:<:` becomes `(OUTPUT)`. The name follows directly (no redundant "to be outputted").
2.  **Grouping**: `&[#]` translates to "is obtained by collecting and flattening the following:".
3.  **Value**: `{Phase 1 output}` is listed as `(VALUE) Phase 1 output`.
4.  **Imperative**: The paradigm invocation becomes "is obtained by running the model paradigm...".
5.  **Bindings**: Use em-dash (`—`) for inline role descriptions:
    *   `{analysis prompt}<:{prompt}>` → `analysis prompt — as the prompt`
    *   `{input files}<:{1}>` → `input files — as the first input`

---

## More Examples

### 1. Simple Linear Plan

**Source (.ncd):**
```ncd
:<:{document summary}
    <= ::(summarize the text)
    <- {clean text}
        <= ::(extract main content, removing headers)
        <- {raw document}
            <= :>:({raw document})
```

**Translated (.ncn):**
```ncn
(OUTPUT) document summary
    (ACTION) is obtained by summarizing the following:
    (VALUE) clean text
        (ACTION) is obtained by extracting main content (removing headers) from the following:
        (VALUE) raw document
            (ACTION) is provided as external input
```

### 2. Looping with Operators

**Source (.ncd):**
```ncd
:<:([all {summaries}])
    <= *. %>({documents}) %<({summary}) %:({document}) %@(1)
        <= $. %>({summary})
        <- {summary}
            <= ::(summarize this document)
            <- {document}*1
    <- {documents}
    <* {document}<$({documents})*>
```

**Translated (.ncn):**
```ncn
(OUTPUT) all summaries
    (ACTION) is obtained by iterating over documents, where each iteration yields:
        (ACTION) is obtained by selecting summary
        (VALUE) summary
            (ACTION) is obtained by summarizing this document
            (VALUE) document (current element in loop 1)
    (VALUE) documents
    (CONTEXT) for each document in the iteration
```

### 3. Grouping (Labeled)

**Source (.ncd):**
```ncd
:<:({analysis results})
    <= &[{}] %>[{sentiment}, {entities}, {topics}]
    <- {sentiment}
        <= ::(analyze sentiment)
        <- {text}
    <- {entities}
        <= ::(extract entities)
        <- {text}
    <- {topics}
        <= ::(classify topics)
        <- {text}
```

**Translated (.ncn):**
```ncn
(OUTPUT) analysis results
    (ACTION) is obtained by bundling the following into a labeled group:
    (VALUE) sentiment
        (ACTION) is obtained by analyzing sentiment of the text
        (VALUE) text
    (VALUE) entities
        (ACTION) is obtained by extracting entities from the text
        (VALUE) text
    (VALUE) topics
        (ACTION) is obtained by classifying topics in the text
        (VALUE) text
```

### 4. Conditional with Judgement

**Source (.ncd):**
```ncd
:<:({draft output}<$(<validation passed>)=>) | ?{flow_index}: 1
    <= $. %>({draft output}) | ?{flow_index}: 1.1 | ?{sequence}: assigning
        <= @:'(<validation passed>) | ?{flow_index}: 1.1.1 | ?{sequence}: timing
        <* <validation passed>
    <- <validation passed> | ?{flow_index}: 1.2
        <= ::(meets requirements)<FOR EACH {draft output} AND ALL {requirements} IS TRUE> | ?{flow_index}: 1.2.1 | ?{sequence}: judgement
        <- {draft output} | ?{flow_index}: 1.2.2
        <- {requirements} | ?{flow_index}: 1.2.3
    <- {draft output} | ?{flow_index}: 1.3
```

**Translated (.ncn):**
```ncn
(OUTPUT) draft output (identified by validation passed)
    (ACTION) is obtained by selecting draft output
        (ACTION) (only when validation passed is true)
        (CONTEXT) given validation passed
    (VALUE) validation passed
        (ACTION) is evaluated by checking whether it meets requirements (true for each draft output when all requirements hold)
        (VALUE) draft output
        (VALUE) requirements
    (VALUE) draft output
```

---

## Formatting Guidelines

### Indentation
Preserve the hierarchical structure of the `.ncd` file. Each level of nesting represents a dependency relationship.

### Punctuation
- Use **em-dash** (`—`) for inline role descriptions: `analysis prompt — as the prompt`
- Use **colon** (`:`) before listing multiple inputs: `the following:`
- Use **parentheses** for clarifying annotations: `(from loop 1)`, `(only when X is true)`

### Verb Agreement
- **Singular subjects**: `summary is obtained by...`
- **Plural subjects**: `all summaries are obtained by...`

---

## Why This Matters

The `.ncn` format bridges the gap between **execution reliability** and **human trust**:

1.  **Verification**: A lawyer or doctor can read the `.ncn` to verify the logic without understanding code.
2.  **Debugging**: If the narrative sounds wrong ("is obtained by iterating" when it should be "collecting"), the logic is likely wrong.
3.  **Auditing**: The `.ncn` serves as a readable log of the intended plan structure.
4.  **Communication**: Stakeholders can review and approve workflows before execution.
