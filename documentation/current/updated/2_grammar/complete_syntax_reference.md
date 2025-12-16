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
| `<*` | Context Concept | In-loop state/context | `<* {counter}*1` |

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
| `({})` or `::()` | Imperative | Command/action | `::(calculate sum)` |
| `<{}>` or `::<>` | Judgement | Evaluation (true/false) | `<{is valid}>` |

### Special Markers

| Symbol | Name | Purpose | Example |
|--------|------|---------|---------|
| `:>:` | Input Marker | External input | `:>:({user query})` |
| `:<:` | Output Marker | Final output/goal | `:<:({final result})` |
| `:_:` | NormCode Subject | Method definition (not implemented) | `:_:({method})` |

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

### Grouping Operators (`&`)

| Marker | Symbol | Meaning | Pattern |
|--------|--------|---------|---------|
| **Group In** | `&[{}]` | Collect with labels | `&[{}] %>[{items}] %+({axis})` ⭐ |
| **Group Across** | `&[#]` | Flatten to list | `&[#] %>[{items}] %+({axis})` ⭐ |

⭐ = Recommended syntax (legacy: `%:({axis})` also supported)

### Timing Operators (`@`)

| Marker | Symbol | Meaning | Pattern |
|--------|--------|---------|---------|
| **Conditional** | `@:'` | Execute if true | `@:' (<condition>)` |
| **Negated** | `@:!` | Execute if false | `@:! (<condition>)` |
| **Sequencing** | `@.` | After dependency | `@. ({dependency})` |

### Looping Operator (`*`)

| Marker | Symbol | Meaning | Pattern |
|--------|--------|---------|---------|
| **Iterate** | `*.` | For each item | `*. %>({base}*) %<({result}) %:({axis}) %^({carry}*-1) %@({index})` |

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

### Inline Annotations

| Annotation | Meaning | Example |
|------------|---------|---------|
| `<$!{...}>` | Protection (don't collapse) | `<$!{%(class)}>` |
| `<$*N>` | Iteration version | `*1`, `*-1`, `*0` |
| `<$({key})%>` | Key selection | `<$({name})%>` |
| `<$*#>` | Unpack all | `<$*#>` |
| `<:{N}>` | Value placement | `<:{1}>`, `<:{2}>` |
| `<$={N}>` | Identity marker | `<$={1}>` |
| `<$()%>` | Instance marker | `<$({text file})%>` |

---

## Comment System

### Syntactical Comments (`?{...}:`)

Structure and flow metadata:

| Comment | Purpose | Example |
|---------|---------|---------|
| `?{sequence}:` | Agent sequence | `?{sequence}: imperative` |
| `?{flow_index}:` | Step identifier | `?{flow_index}: 1.1.2` (mark on concept to infer) |
| `?{natural_language}:` | NL description | `?{natural_language}: Extract content` |

> **Note**: `?{flow_index}:` should be marked on the concept to infer (value concept). In deprecated older versions, it was sometimes marked on the functional concept instead.

### Referential Comments (`%{...}:`)

Data type and location metadata:

| Comment | Purpose | Example |
|---------|---------|---------|
| `%{paradigm}:` | Execution paradigm | `%{paradigm}: python_script` |
| `%{location_string}:` | File location | `%{location_string}: data/input.txt` |

### Translation Comments

Compilation process metadata:

| Comment | Purpose | Example |
|---------|---------|---------|
| `...:` | Source text (un-decomposed) | `...: Calculate the sum` |
| `?:` | Question guiding decomposition | `?: What operation?` |
| `/:` | Description (complete) | `/: Computes total` |

---

## Flow Indices

Flow indices provide unique addresses for each step:

```ncd
| ?{flow_index}: 1           Root concept (depth 0)
| ?{flow_index}: 1.1         First child (depth 1)
| ?{flow_index}: 1.1.1       First grandchild (depth 2)
| ?{flow_index}: 1.1.2       Second grandchild (depth 2)
| ?{flow_index}: 1.2         Second child (depth 1)
| ?{flow_index}: 1.2.1       First grandchild of second child
```

**Rules**:
- Concept lines (`<-`, `<=`, `<*`, `:<:`) act as counters
- Index determined by indentation depth
- Counters increment at each depth, reset at deeper levels
- Comment lines inherit the last concept's flow index

> **Deprecated**: Older versions marked flow_index on the functional concept (`<=`) to identify inferences. Current practice marks it on the concept to infer (`<-` or `:<:`).

---

## Perceptual Signs

Format for referencing external data:

```
%{Norm}ID(Signifier)
```

**Components**:
- **Norm**: Perception method (e.g., `file_location`, `prompt_location`)
- **ID**: Hexadecimal identifier (e.g., `a1b`)
- **Signifier**: Data pointer (e.g., `data/input.txt`)

**Examples**:
```
%{file_location}7f2(data/input.txt)
%{prompt_location}3c4(prompts/template.txt)
%{truth_value}(True)
```

---

## Complete Example

### Simple Plan

```ncd
:<:{document summary} | ?{flow_index}: 1 | /: Final output
    <= ::(summarize the text) | ?{sequence}: imperative
    <- {clean text} | ?{flow_index}: 1.1
        <= ::(extract main content, removing headers) | ?{sequence}: imperative
        <- {raw document} | ?{flow_index}: 1.1.1
            <= :>:({raw document}) | ?{sequence}: assigning
```

**Flow**:
1. Get external input `{raw document}` (1.1.1)
2. Extract main content → `{clean text}` (1.1)
3. Summarize → `{document summary}` (1)

---

### With Operators

```ncd
:<:{all summaries} | ?{flow_index}: 1
    <= *. %>({documents}<$({document})*1>) %<({summary}) %:({document}) %@(1) | ?{sequence}: looping
    <- {summary} | ?{flow_index}: 1.1
        <= ::(summarize this document) | ?{sequence}: imperative
        <- {document}*1 | ?{flow_index}: 1.1.1
    <* {documents} | ?{flow_index}: 1.2
    <* {document}*1<*{documents}> | ?{flow_index}: 1.3
```

**Flow**:
1. Loop over `{documents}` (context: 1.2)
2. For each `{document}*1` (current item: 1.3)
3. Summarize document → `{summary}` (1.1)
4. Collect all summaries → `{all summaries}` (1)

---

### With Grouping

```ncd
:<:{analysis results} | ?{flow_index}: 1
    <= &[{}] %>[{sentiment}, {entities}, {topics}] | ?{sequence}: grouping
    <- {sentiment} | ?{flow_index}: 1.1
        <= ::(analyze sentiment) | ?{sequence}: imperative
        <- {text} | ?{flow_index}: 1.1.1
    <- {entities} | ?{flow_index}: 1.2
        <= ::(extract entities) | ?{sequence}: imperative
        <- {text} | ?{flow_index}: 1.2.1
    <- {topics} | ?{flow_index}: 1.3
        <= ::(classify topics) | ?{sequence}: imperative
        <- {text} | ?{flow_index}: 1.3.1
```

**Flow**:
1. Run all three analyses in parallel (1.1, 1.2, 1.3)
2. Group into labeled structure → `{analysis results}` (1)

---

### With Conditional

```ncd
:<:{final output} | ?{flow_index}: 1
    <= @:'(<validation passed>) | ?{sequence}: timing
    <- {validated output} | ?{flow_index}: 1.1
        <= ::(validate and correct) | ?{sequence}: imperative
        <- {draft output} | ?{flow_index}: 1.1.1
        <- {requirements} | ?{flow_index}: 1.1.2
    <- <validation passed> | ?{flow_index}: 1.2
        <= <{meets requirements}> | ?{sequence}: judgement
        <- {draft output} | ?{flow_index}: 1.2.1
        <- {requirements} | ?{flow_index}: 1.2.2
```

**Flow**:
1. Check if requirements met → `<validation passed>` (1.2)
2. If true, validate and correct → `{validated output}` (1.1)
3. Return as `{final output}` (1)

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
:<:{all results}
    <= *. %>({items}*1) %<({result}) %:({item}) %@(1)
    <- {result}
        <= ::(process item)
        <- {item}*1
    <* {items}
    <* {item}*1<*{items}>
```

**Use**: Process each item in a collection.

---

### Pattern 4: Conditional Branch

```ncd
:<:{output}
    <= @:'(<condition>)
    <- {then branch}
        <= ::(do if true)
        <- {input}
    <- <condition>
        <= <{check something}>
        <- {input}
```

**Use**: Execute only if condition is true.

---

### Pattern 5: Accumulation

```ncd
{accumulated result}
    <= $+ %>({current}) %<({new item}) %:({items})
    <- {current}
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
| Action | Imperative `({})` | `<= ::(calculate)` |
| Check | Judgement `<{}>` | `<= <{is valid}>` |
| Alias concepts | Identity `$=` | `$= %>({source})` |
| Set literal | Abstraction `$%` | `$% %>([1, 2, 3])` |
| Collect labeled | Group In `&[{}]` | `&[{}] %>[{a}, {b}]` |
| Flatten | Group Across `&[#]` | `&[#] %>({source})` |
| If true | Conditional `@:'` | `@:' (<cond>)` |
| Loop | Iterate `*.` | `*. %>({items}*1)` |

### By Category

**Semantic Concepts**:
```
{}    <    []    :S:    ({})    <{}>
```

**Syntactic Operators**:
```
$=  $%  $.  $+  $-        Assigning
&[{}]  &[#]               Grouping
@:'  @:!  @.              Timing
*.                        Looping
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
Imperative      ::= '({' Name '})' | '::(' Name ')'
Judgement       ::= '<{' Name '}>' | '::<' Name '>'

SyntacticOperator ::= Assigning | Grouping | Timing | Looping
Assigning       ::= ('$=' | '$%' | '$.' | '$+' | '$-') Modifiers*
Grouping        ::= ('&[{}]' | '&[#]') Modifiers*
Timing          ::= ('@:\'' | '@:!' | '@.') Condition?
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
