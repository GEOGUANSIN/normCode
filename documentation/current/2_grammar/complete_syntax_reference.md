# Complete Syntax Reference

**Comprehensive reference for all NormCode `.ncd` syntax elements.**

---

## Overview

This document serves as a quick reference for all NormCode syntax. For detailed explanations, see the individual grammar documents:

- **[NCD Format](ncd_format.md)** - File structure and flow
- **[Semantic Concepts](semantic_concepts.md)** - Concept types
- **[Syntactic Operators](syntactic_operators.md)** - Operators
- **[References and Axes](references_and_axes.md)** - Data structures

---

## Core Markers

### Inference Markers

| Symbol | Name | Purpose | Example |
|--------|------|---------|---------|
| `<-` | Value Concept | Data (inputs/outputs) | `<- {result}` |
| `<=` | Functional Concept | Operations to execute | `<= ::(calculate)` |
| `<*` | Context Concept | In-loop/timing state/context | `<* {counter}*1` |

---

## Semantic Concepts

### Non-Functional Concepts (Entities)

| Symbol | Name | Description | Example |
|--------|------|-------------|---------|
| `{}` | Object | Generic entity/data | `{document}` |
| `<>` | Proposition | State/condition (boolean) | `<validation passed>` |
| `[]` | Relation | Collection (list/dict) | `[documents]` |
| `:S:` | Subject | Agent/actor/system | `:LLMAgent:` |

### Functional Concepts (Operations)

| Symbol | Name | Description | Example |
|--------|------|-------------|---------|
| `({})` or `::()` [DEPRECATING] | Imperative | Command/action | `::(calculate sum)` |
| `<{}>` or `::<>` [DEPRECATING] | Judgement | Evaluation (true/false) | `::({input} is good)<{ALL unsure}>` |

**Default Subject (`::`)**: In most plans, `::` represents the default agent/subject. The full form `:Subject:{norm}(...)` allows specifying a custom subject (e.g., `:LLMAgent:{paradigm}(...)`), but `::` with optional norm is the common pattern.

### Special Markers

| Symbol | Name | Purpose | Example |
|--------|------|---------|---------|
| `:>:` | Input Marker | External input | `:>:({user query})` |
| `:<:` | Output Marker | Final output/goal | `:<:({final result})` |
| `:_:` | NormCode Subject | Method call (not implemented) | `:_:{method}(inputs)` |

>**Note on `:_:`**: The norm position holds `{method}` (a NormCode plan itself), making this a call to run a NormCode plan with specific inputs.

---

## Syntactic Operators

### Assigning Operators (`$`)

| Marker | Symbol | Meaning | Pattern |
|--------|--------|---------|---------|
| **Identity** | `$=` | Merge concepts (alias) | `$= %>({source})` |
| **Abstraction** | `$%` | Literal → data | `$% %>({literal}) %:([{axes}])` |
| **Specification** | `$.` | Select first valid | `$. %>({child})` |
| **Continuation** | `$+` | Append along axis | `$+ %>({base}) %<({item}) %:({axis})` |
| **Selection** | `$-` | Extract elements | `$- %>({source}) %^(<selector>)` |
| **Nominalization** | `$::` | Nominalize an Action (not implemented) | `$:: %>(:_Subject_:__)` |


### Grouping Operators (`&`)

| Marker | Symbol | Meaning | Pattern |
|--------|--------|---------|---------|
| **Group In** | `&[{}]` | Collect with labels | `&[{}] %>[{items}] %+({axis})` ⭐ |
| **Group Across** | `&[#]` | Flatten to list | `&[#] %>[{items}] %+({axis})` ⭐ |

⭐ = Recommended syntax (legacy: `%:({axis})` also supported)

### Timing Operators (`@`)

| Marker | Symbol | Meaning | Pattern |
|--------|--------|---------|---------|
| **Conditional** | `@:'` | Execute if true (filter) | `@:' %>(<_condition_>)` or `@:' <* <condition>` |
| **Negated** | `@:!` | Execute if false (filter) | `@:! %>(<_condition_>)` |
| **Completion Check** | `@.` | After dependency | `@. %>({_dependency_})` |
| **Action Call** | `@::` | Call an Action (not implemented) | `@:: %>(:_Subject_:__)` |

**Timing as Filter Pattern**:
Timing operators are typically sequences that time/filter other inferences (especially specifications):
```ncd
<= $. %>({output})              // Specification
    <= @:'(<condition>)         // Timing operator filters the specification
    <* <condition>              // Condition as context concept
<- <condition>                  // Condition evaluation
    <= ::(check)<ALL True>
```
- The timing operator takes the condition as a context concept
- Only items where the condition is true pass through the specification
- Common pattern: conditional filtering of collections

### Looping Operator (`*`)

| Marker | Symbol | Meaning | Pattern |
|--------|--------|---------|---------|
| **Iterate** | `*.` | For each item | `*. %>({collection}) %<({result}) %:({axis}) %@({index})` |

**Usage Pattern**:
```ncd
<= *. %>({collection}) %<({result}) %:({item}) %@(1)
    <= $. %>({result})        // Specification selects loop output
    <- {result}               // Result concept
        <= ::(process)
        <- {item}*1           // Current item in loop @(1)
<- {collection}               // Base collection (value concept)
<* {item}<$({collection})*>   // Current element marker (context concept)
```

**Key Components**:
- `%>({collection})`: Source collection to iterate over
- `%<({result})`: Target concept to collect
- `%:({item})`: Axis being iterated
- `%@(N)`: Loop identifier
- `{item}<$({collection})*>`: Current element (no number = current)
- `{item}<$({collection})*N>`: Carried element from N iterations
- `{item}*N`: Reference to item in loop `@(N)`

---

## Modifier System

### Universal Modifiers

| Modifier | Name | Meaning | Usage |
|----------|------|---------|-------|
| `%>` | Source | Read from | `%>({input})` or `%>[{a}, {b}]` |
| `%<` | Target | Write to | `%<({output})` |
| `%:` | Axis | Structural dimension | `%:({axis})` or `%:([{ax1}, {ax2}])` |
| `%^` | Carry | Carried state | `%^({state}*-1)` |
| `%@` | Index | Quantifier ID | `%@(1)` |
| `%+` | Create | New axis name | `%+(axis_name)` |

### Clausal Modifiers

Inline annotations that modify or describe concepts:

| Annotation | Meaning | Example |
|------------|---------|---------|
| `<_text_>` | Clausal Comment | `{concept}<is unique>` - adds a descriptive clause |
| `<:{N}>` | Value placement | `<:{1}>`, `<:{2}>` |
| `<$!{...}>` | Grouping Protection (don't collapse) | `<$!{%(class)}>` |
| `<$({concept})*>` | Current iteration element | `{item}<$({items})*>` - current element of {items} |
| `<$({concept})*N>` | Carried iteration element | `{item}<$({items})*-1>` - element from N iterations ago |
| `*N` | Loop reference | `{document}*1` - refers to element in loop @(N) |
| `<$()%>` | Instance marker (in functional inputs) | `<$({text file})%>` |
| `<$({key})%>` | Key selection (in value inputs) | `<$({name})%>` |
| `<$*#>` | Unpack all | `<$*#>` |
| `<$({N})=>` or `<$={N}>` [DEPRECATING] | Identifier marker | `<$({1})=>` |
| `<$({condition})=>` | Identification marker | `{output}<$(<validated>)=>` - marks output as identified by condition |


>**Note**: 
>- Clausal Comments `<text>` are inline annotations attached to concepts, distinct from Proposition concepts `<proposition name>` which are standalone semantic concepts representing states/conditions.
>- Iteration markers: `<$({concept})*>` = current element (no number), `<$({concept})*N>` = carried element from N iterations

---

## Comment System

### Syntactical Comments (`?{_norm_}:`)

Structure and flow metadata. where {_norm_} is a placeholder for the comment norm:

| Comment | Purpose | Example |
|---------|---------|---------|
| `?{sequence}:` | Agent sequence | `?{sequence}: imperative` |
| `?{flow_index}:` | Step identifier | `?{flow_index}: 1.1.2` (mark on concept to infer) |
| `?{natural_language}:` | NL description | `?{natural_language}: Extract content` |

> **Note**: `?{flow_index}:` should be marked on the concept to infer (value concept). In deprecated older versions, it was sometimes marked on the functional concept instead.

### Referential Comments (`%{_norm_}:`)

Data type and location metadata. where {_norm_} is a placeholder for the comment norm:

| Comment | Purpose | Example |
|---------|---------|---------|
| `%{paradigm}:` | Execution paradigm | `%{paradigm}: python_script` |
| `%{location_string}:` | File location | `%{location_string}: data/input.txt` |

### Derivation Comments

Derivation process metadata:

| Comment | Purpose | Example |
|---------|---------|---------|
| `...:` | Source text (un-decomposed) | `...: Calculate the sum` |
| `?:` | Question guiding derivation | `?: What operation?` |
| `/:` | Description (complete) | `/: Computes total` |

---

## Flow Indices

Flow indices provide unique addresses for each step:

```ncd
:<:_concept_to_infer_ | ?{flow_index}: 1           /:Root concept (depth 0)
    <= _functional_concept_1_ | ?{flow_index}: 1.1         /:First child (depth 1)
    <- _input_value_1_ | ?{flow_index}: 1.2                /:Second child (depth 1)
        <= _functional_concept_2_ | ?{flow_index}: 1.2.1       /:First grandchild (depth 2)
        <- _nested_input_1_ | ?{flow_index}: 1.2.1.1           /:First great-grandchild (depth 3)
        <- _nested_input_2_ | ?{flow_index}: 1.2.1.2           /:Second great-grandchild (depth 3)
    <- _input_value_2_ | ?{flow_index}: 1.3                /:Third child (depth 1)
    <* _context_value_ | ?{flow_index}: 1.4                /:Fourth child (depth 1)
```

**Rules**:
- All concept lines (`:<:`, `<=`, `<-`, `<*`) act as counters and receive flow indices
- Index determined by indentation depth
- Counters increment at each depth level
- When moving to a deeper level, append a new counter (e.g., 1 → 1.1 → 1.1.1)
- When returning to or continuing at the same level, increment the last counter (e.g., 1.1 → 1.2)
- Comment lines inherit the last concept's flow index

> **Deprecated**: Older versions marked flow_index only on the functional concept (`<=`) to identify inferences. Current practice marks it on **every concept line** for complete traceability.

---

## Perceptual Signs

Format for referencing external data:

```
%{Norm}ID(Signifier)
```

**Components**:
- **Norm**: Perception method (e.g., `file_location`, `prompt_location`, `literal`)
- **ID**: Hexadecimal identifier (e.g., `a1b`)
- **Signifier**: Data pointer (e.g., `data/input.txt`)

**Examples**:
```
%{file_location}7f2(data/input.txt)
%{prompt_location}3c4(prompts/template.txt)
%{truth_value}(True)
%{_X_}(computed value) /: This is Literal(_X_)
```

> **Legacy Note**: Older documentation and paradigms may use `Normal` to refer to literal/direct values. This has been replaced by `literal` for clarity.

---

## Complete Example

> **Note**: The following examples demonstrate currently implemented syntax. Future features like `$::` (Nominalization), `@::` (Action Call), and `:_:` (NormCode Subject) are not shown as they are not yet implemented.

### Simple Plan

```ncd
:<:{document summary} | ?{flow_index}: 1 | /: Final output
    <= ::(summarize the text) | ?{flow_index}: 1.1 | ?{sequence}: imperative
    <- {clean text} | ?{flow_index}: 1.2
        <= ::(extract main content, removing headers) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
        <- {raw document} | ?{flow_index}: 1.2.1.1
            <= :>:({raw document}) | ?{flow_index}: 1.2.1.1.1 | ?{sequence}: imperative
```

**Flow**:
1. Get external input (1.2.1.1.1) `{raw document}` (1.2.1.1)
2. Extract main content (1.2.1) → `{clean text}` (1.2)
3. Summarize (1.1) → `{document summary}` (1)

---

### With Operators

```ncd
:<:([all {summaries}]) | ?{flow_index}: 1
    <= *. %>({documents}) %<({summary}) %:({document}) %@(1) | ?{flow_index}: 1.1 | ?{sequence}: looping
        <= $. %>({summary})  | ?{flow_index}: 1.1.1 | ?{sequence}: assigning
        <- {summary} | ?{flow_index}: 1.1.2
            <= ::(summarize this document) | ?{flow_index}: 1.1.2.1 | ?{sequence}: imperative
            <- {document}*1 | ?{flow_index}: 1.1.2.2
    <- {documents} | ?{flow_index}: 1.2
    <* {document}<$({documents})*> | ?{flow_index}: 1.3
```

**Key Looping Concepts**:
- **Loop operator** (1.1): `*. %>({documents}) %<({summary}) %:({document}) %@(1)`
  - Source: `{documents}` (collection to iterate over)
  - Target: `{summary}` (what gets collected each iteration)
  - Axis: `{document}` (dimension being iterated)
  - Index: `@(1)` (loop identifier)
- **Specification** (1.1.1): `$. %>({summary})` - selects summary as output for each iteration
- **Loop base** (1.2): `{documents}` - regular value concept holding the collection
- **Current element** (1.3): `{document}<$({documents})*>` - context concept marking current iteration
  - `<$({documents})*>` means "current element" (no number)
  - `<$({documents})*N>` would mean "element from N iterations ago"
- **Reference in loop body** (1.1.2.2): `{document}*1` - refers to current document in loop `@(1)`

**Flow**:
1. Iterate over `{documents}` (1.2) with loop operator (1.1)
2. For each iteration, current element is `{document}<$({documents})*>` (1.3)
3. Summarize that document (1.1.2.1) using `{document}*1` (1.1.2.2)
4. Specification (1.1.1) selects `{summary}` (1.1.2) as loop output
5. Collect all summaries → `[all {summaries}]` (1)

---

### With Grouping

**non-joining grouping**:

```ncd
:<:({analysis results}) | ?{flow_index}: 1
    <= &[{}] %>[{sentiment}, {entities}, {topics}] | ?{flow_index}: 1.1 | ?{sequence}: grouping
    <- {sentiment} | ?{flow_index}: 1.2
        <= ::(analyze sentiment) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
        <- {text} | ?{flow_index}: 1.2.1.1
    <- {entities} | ?{flow_index}: 1.3
        <= ::(extract entities) | ?{flow_index}: 1.3.1 | ?{sequence}: imperative
        <- {text} | ?{flow_index}: 1.3.1.1
    <- {topics} | ?{flow_index}: 1.4
        <= ::(classify topics) | ?{flow_index}: 1.4.1 | ?{sequence}: imperative
        <- {text} | ?{flow_index}: 1.4.1.1
```

**Flow**:
1. Run all three analyses in parallel (1.2, 1.3, 1.4)
2. Group with grouping operator (1.1) into labeled structure → `{analysis results}` (1)

**joining Grouping**:
```ncd
:<:({people}) | ?{flow_index}: 1
    <= &[#] %>[{class 1 members}, {class 2 members}, {class 3 members}] %:[({class 1 members}), ({class 2 members}), ({class 3 members})] %+({people}) | ?{flow_index}: 1.1 | ?{sequence}: grouping
    <- {class 1 members} | ?{flow_index}: 1.2
        <= ::(find class 1 members) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
    <- {class 2 members} | ?{flow_index}: 1.3
        <= ::(find class 2 members) | ?{flow_index}: 1.3.1 | ?{sequence}: imperative
    <- {class 3 members} | ?{flow_index}: 1.4
        <= ::(find class 3 members) | ?{flow_index}: 1.4.1 | ?{sequence}: imperative
```

---

### With Conditional

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

**Key Conditional Timing Concepts**:
- **Timing as filter**: The timing operator `@:'(<validation passed>)` (1.1.1) acts as a sequence that times/filters the specification
  - It takes `<validation passed>` as context (`<* <validation passed>`)
  - Only items where the condition is true pass through the filter
- **Specification with filter** (1.1): `$. %>({draft output})` selects drafts, filtered by the timing condition
- **Judgement evaluation** (1.2.1): Evaluates whether each draft meets requirements → `<validation passed>` (1.2)
- **Output with identification marker** (1): `{draft output}<$(<validation passed>)=>` 
  - Remains `{}` (Object concept type) - filtering doesn't change the concept type
  - `<$(<validation passed>)=>` is a clausal comment meaning "identified by <validation passed>"
  - This marks the output as semantically different from the original `{draft output}` (1.3) - this is the validated version

**Flow**:
1. Evaluate judgement (1.2.1): Check if `{draft output}` (1.2.2) meets `{requirements}` (1.2.3) → `<validation passed>` (1.2)
2. Timing operator (1.1.1) filters the specification based on `<validation passed>` condition
3. Specification (1.1) selects only `{draft output}` (1.3) items that passed the filter
4. Return as `{draft output}<$(<validation passed>)=>` (1) - the filtered draft, identified by the validation condition

---

## Pattern Library

### Pattern 1: Linear Workflow

```ncd
:<:{output}
    <= ::(final step)
    <- {intermediate}
        <= ::(middle step)
        <- {input}
```

**Use**: Sequential processing with dependencies.

---

### Pattern 2: Parallel Collection

```ncd
:<:{results}
    <= &[{}] %>[{result A}, {result B}, {result C}] %+(results)
    <- {result A}
        <= ::(process A)
        <- {input}
    <- {result B}
        <= ::(process B)
        <- {input}
    <- {result C}
        <= ::(process C)
        <- {input}
```

**Use**: Run multiple operations in parallel, collect results with labeled structure.

---

### Pattern 3: Iteration

```ncd
:<:[all {results}]
    <= *. %>({items}) %<({result}) %:({item}) %@(1)
        <= $. %>({result})
        <- {result}
            <= ::(process item)
            <- {item}*1
    <- {items}
    <* {item}<$({items})*>
```

**Use**: Process each item in a collection.

**Structure**:
- Loop over `{items}` collection
- Current element marked as `{item}<$({items})*>` (context concept)
- Specification `$. %>({result})` selects output for each iteration
- `{item}*1` references current item in loop `@(1)`

---

### Pattern 4: Conditional Branch (Timing as Filter)

```ncd
:<:({output}<$(<condition>)=>)
    <= $. %>({output})
        <= @:'(<condition>)
        <* <condition>
    <- <condition>
        <= ::(check something)<ALL True>
        <- {input}
    <- {output}
        <= ::(process input)
        <- {input}
```

**Use**: Filter results based on a condition. The timing operator acts as a filter on the specification.

**Structure**:
- **Timing as filter**: `@:'(<condition>)` filters the specification, only passing items where condition is true
- **Output marked by condition**: `{output}<$(<condition>)=>` 
  - Keeps original concept type `{}` (Object) - filtering doesn't change type
  - Identification marker `<$(<condition>)=>` distinguishes filtered from unfiltered version
- **Judgement**: `<ALL True>` truth assertion is **mandatory** for judgements

---

### Pattern 5: Accumulation

```ncd
:<:({result}<$({result})=>)
    <= $+ %<({result}) %>({new item}) %:({items})
    <- {result}<$({current})=>
    <- {new item}
```

**Use**: Build up results over iterations.

---

## Syntax Quick Reference Tables

### By Function

| Need | Use | Pattern |
|------|-----|---------|
| Data/entity | Object `{}` | `<- {user input}` |
| Condition | Proposition `<>` | `<validation passed>` |
| Collection | Relation `[]` | `<- [documents]` |
| Action | Imperative `::()` | `<= ::(calculate)` |
| Check | Judgement `::()\<>` | `<= ::(is valid)<ALL True>` |
| Alias concepts | Identity `$=` | `$= %>({source})` |
| Set literal | Abstraction `$%` | `$% %>([1, 2, 3])` |
| Collect labeled | Group In `&[{}]` | `&[{}] %>[{a}, {b}]` |
| Flatten | Group Across `&[#]` | `&[#] %>({source})` |
| If true | Conditional `@:'` | `@:' (<cond>)` |
| After completion | Completion Check `@.` | `@. %>({dependency})` |
| Loop | Iterate `*.` | `*. %>({items}) %<({result}) %:({item}) %@(1)` |
| Nominalize action (future) | Nominalization `$::` | `$:: %>(:Subject:___)` |
| Call action (future) | Action Call `@::` | `@:: %>(:Subject:___)` |

### By Category

**Semantic Concepts**:
```
{}     Object
<>     Proposition
[]     Relation
:S:    Subject
::()   Imperative (default subject)
::()\<>  Judgement (with mandatory truth assertion)
```

**Syntactic Operators**:
```
$=  $%  $.  $+  $-  $::        Assigning
&[{}]  &[#]                    Grouping
@:'  @:!  @.  @::              Timing
*.                             Looping
```

**Modifiers**:
```
%>  %<  %:  %^  %@  %+
```

**Comments**:
```
?{sequence}:    ?{flow_index}:    ?{natural_language}:
%{paradigm}:    %{location_string}:
...:    ?:    /:
```

---

## Formal Grammar (BNF-like)

```ebnf
Plan            ::= RootConcept Inference*
RootConcept     ::= ':<:' Concept Comment*
Inference       ::= ValueConcept | FunctionalConcept | ContextConcept
ValueConcept    ::= '<-' Concept Comment* Inference*
FunctionalConcept ::= '<=' Operation Comment* Inference*
ContextConcept  ::= '<*' Concept Comment* Inference*

Concept         ::= SemanticConcept | SyntacticOperator
SemanticConcept ::= Object | Proposition | Relation | Subject | Imperative | Judgement
Object          ::= '{' Name '}'
Proposition     ::= '<' Name '>'
Relation        ::= '[' Name ']'
Subject         ::= ':' Name ':'
Imperative      ::= '::(' FunctionalInput ')'
Judgement       ::= '::(' FunctionalInput ')' '<' TruthAssertion '>'
TruthAssertion  ::= Name  /* e.g., "ALL True", "ANY False", "true for each X" */

SyntacticOperator ::= Assigning | Grouping | Timing | Looping
Assigning       ::= ('$=' | '$%' | '$.' | '$+' | '$-' | '$::') Modifiers*
Grouping        ::= ('&[{}]' | '&[#]') Modifiers*
Timing          ::= ('@:\'' | '@:!' | '@.' | '@::') Condition?
Looping         ::= '*.' Modifiers*

Modifiers       ::= Source | Target | Axis | Carry | Index | Create
Source          ::= '%>(' Concept+ ')'
Target          ::= '%<(' Concept ')'
Axis            ::= '%:(' Concept+ ')'
Carry           ::= '%^(' Concept ')'
Index           ::= '%@(' Number ')'
Create          ::= '%+(' Name ')'

Comment         ::= '|' CommentType ':' Text
CommentType     ::= '?' | '%' | '...' | '/' | ''
```

---

## Validation Checklist

When writing `.ncd` (or reviewing compiler output):

### Structure
- [ ] Root concept has `:<:` marker
- [ ] Each inference has exactly ONE functional concept (`<=`)
- [ ] Value concepts (`<-`) and context concepts (`<*`) are properly indented
- [ ] Flow indices increment correctly

### Operators
- [ ] Syntactic operators use unified modifier syntax (`%>`, `%<`, etc.)
- [ ] Grouping specifies axes to collapse (`%:`)
- [ ] Looping includes iteration markers (`*1`, `*-1`)
- [ ] Timing has valid conditions

### Semantics
- [ ] Concept types match their content (objects are `{}`, collections are `[]`)
- [ ] Imperatives and judgements have associated sequences
- [ ] Value placements (`<:{1}>`) are sequential
- [ ] Instance markers (`<$()%>`) link to valid abstractions

### Comments
- [ ] Flow indices are present
- [ ] Sequences are annotated
- [ ] Natural language descriptions match operations

---

## Common Pitfalls

| Issue | Problem | Solution |
|-------|---------|----------|
| **Missing flow index** | Can't trace execution | Ensure all concepts have `?{flow_index}:` |
| **Ambiguous bindings** | Value order unclear | Use explicit `<:{1}>`, `<:{2}>` markers |
| **Mixed old/new syntax** | Parser confusion | Use unified modifier system consistently |
| **Unprotected axes** | Axes collapse unexpectedly | Use `<$!{axis}>` to protect |
| **Skip value propagation** | Unexpected empty results | Check for `@#SKIP#@` in operations |

---

## Next Steps

- **[NCD Format](ncd_format.md)** - Deep dive into file structure
- **[Semantic Concepts](semantic_concepts.md)** - Concept type details
- **[Syntactic Operators](syntactic_operators.md)** - Operator specifications
- **[References and Axes](references_and_axes.md)** - Data structures

- **[Execution Section](../3_execution/README.md)** - How syntax runs at runtime
- **[Compilation Section](../4_compilation/README.md)** - How syntax is generated

---

**This reference is your quick lookup guide.** Bookmark it for writing and debugging NormCode plans.
