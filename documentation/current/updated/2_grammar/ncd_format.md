# The `.ncd` File Format

**Learn the formal NormCode syntax that the compiler generates from your draft plans.**

---

## Overview

When you write a plan in `.ncds` (NormCode Draft Straightforward), the compiler transforms it into `.ncd` (NormCode Draft)—a rigorous, formal representation that the orchestrator can execute.

**The key difference:**
- **`.ncds`**: Natural language with minimal markers (`<-`, `<=`)
- **`.ncd`**: Fully annotated with types, bindings, flow indices, and operation markers

**Important**: You don't need to write `.ncd` by hand. The compiler handles the transformation. This guide helps you understand the formalized output for debugging, auditing, and extending the system.

---

## The Semi-Formal Philosophy

NormCode is considered **semi-formal** because concepts are not merely placeholders—their semantic meaning matters, particularly when an inference's logic is executed by a language model.

This positions NormCode between:
- **Pure natural language** (ambiguous, hard to execute)
- **Fully formal code** (rigid, hard to write)

The `.ncd` format provides just enough structure to be unambiguous and executable while remaining readable and LLM-friendly.

---

## Core Building Blocks

### Inferences: The Fundamental Unit

The fundamental unit of a NormCode plan is the **inference**. An inference is a self-contained logical operation defined by:

1. **Functional Concept (`<=`)**: Defines the core operation and invokes an agent sequence. Usually contains a **norm** that specifies the execution strategy.
2. **Value Concept (`<-`)**: Provides the input/output data
3. **Context Concept (`<*`)**: Optional in-loop state or carried data

**The Norm**: The functional concept's reference holds a **norm**—a paradigm or execution strategy (e.g., `sequence: imperative`, `paradigm: python_script`, `method: NormCode_ncd`) that configures how the agent processes the operation.

### Concept Markers

NormCode uses three primary markers to distinguish concept types:

| Symbol | Name | Meaning |
|--------|------|---------|
| `<-` | Value Concept | Data (nouns) - inputs and outputs |
| `<=` | Functional Concept | Actions (verbs) - operations to execute |
| `<*` | Context Concept | In-loop state or context data |

---

## File Structure

### Basic Inference Pattern

```ncd
_concept_to_infer_ /: Description of overall goal
    <= _functional_concept_defining_the_operation_ |?{sequence}: imperative /: Agent sequence invoked
    <- _input_value_concept_1_ /: First input
    <- _input_value_concept_2_ /: Second input
```

**Meta-variable Convention (`_xxx_`)**:
Throughout NormCode documentation, terms enclosed in underscores (e.g., `_concept_to_infer_`) indicate **meta-variables**—placeholders to be replaced with actual concept names during planning.

### Plan Structure (Multiple Inferences)

Plans are tree-like structures where child inferences provide data for parent inferences:

```ncd
_concept_to_infer_ /: The overall goal of this inference
    <= _functional_concept_defining_the_operation_ |?{sequence}: imperative
    <- _input_value_concept_1_ /: First input needs computation
        <= _functional_concept_2_ |?{sequence}: imperative
        <- _nested_input_1_
        <- _nested_input_2_
    <- _input_value_concept_2_ /: Second input (direct)
    <* _context_concept_1_ /: Context data
```

**Key principle**: A concept used as output in one inference becomes the input for a parent inference. This creates explicit data flow.

### Root Concept Marker

The first concept of a plan uses the `:<:` subject marker to indicate it's the top-level goal:

```ncd
:<:(_first_concept_of_the_plan_) /: Final output of the entire plan
    <= ...
```

This marks the concept as both:
- The top-level goal to be completed
- The final result to be outputted

---

## Flow Indices

Flow indices (e.g., `1.1.2`) serve as unique addresses for each step in the plan.

### Generation Rules

1. **Concept Lines (`:<:`, `<=`, `<-`, `<*`)**: Act as counters
   - Index determined by indentation depth
   - Counters increment at each depth level
   - Deeper levels reset when parent level increments

2. **Comment Lines**: Inherit the flow index of the last seen concept line

> **Deprecated Pattern (Old Versions)**: In some older NormCode versions, the flow index was marked on the functional concept (`<=`) instead of the value concept (`<-`). This made the functional concept's flow index serve as the inference identifier. This pattern is deprecated—current practice marks flow indices on the concept to infer (the value concept at the top of each inference).

**Example (Current)**:
```ncd
:<:{result} | ?{flow_index}: 1
    <= ::(compute) | ?{flow_index}: 1.1
    <- {input A} | ?{flow_index}: 1.2
        <= ::(process A) | ?{flow_index}: 1.2.1
        <- {raw A} | ?{flow_index}: 1.2.1.1
    <- {input B} | ?{flow_index}: 1.3
        <= ::(process B) | ?{flow_index}: 1.3.1
        <- {raw B} | ?{flow_index}: 1.3.1.1
```

**Example (Deprecated - Old Versions)**:
```ncd
:<:{result}
    <= ::(compute) | ?{flow_index}: 1 | /: DEPRECATED: flow_index on functional concept
    <- {input A}
        <= ::(process A) | ?{flow_index}: 1.1
        <- {raw A}
```

In the deprecated pattern, the inference was identified by the functional concept's flow index instead of marking the concept to infer. **Always use the current pattern** where each concept has its own flow index.

### Why Flow Indices Matter

- **Debugging**: "Step `1.3.2` failed" tells you exactly where
- **Auditing**: Trace execution through specific paths
- **Checkpointing**: Resume from specific steps
- **Cross-referencing**: Reference other steps explicitly

---

## Comments and Metadata

A line in NormCode can have optional comments for clarity, control, and metadata:

```
_concept_definition_ | _comment_
```

### Comment Types

#### 1. Syntactical Comments (`?{_comment_norm_}:`)

Relate to the structure and flow of the NormCode:

| Comment | Purpose | Example |
|---------|---------|---------|
| `?{sequence}:` | Agent sequence invoked | `?{sequence}: imperative` |
| `?{flow_index}:` | Step identifier | `?{flow_index}: 1.1.2` |
| `?{natural_language}:` | Natural language description | `?{natural_language}: Extract main content` |

#### 2. Referential Comments (`%{_comment_norm_}:`)

Comment on the reference or type of data:

| Comment | Purpose | Example |
|---------|---------|---------|
| `%{paradigm}:` | Execution paradigm | `%{paradigm}: python_script` |
| `%{location_string}:` | File location | `%{location_string}: data/input.txt` |

#### 3. Derivation Comments

Used during compilation to document the transformation process:

| Comment | Purpose | Example |
|---------|---------|---------|
| `...:` or `\|...:` | Source text being analyzed | `...: Calculate the sum of digits` |
| `?:` or `\|?:` | Question guiding decomposition | `?: What operation is being performed?` |
| `/:` or `\|/:` | Description of result | `/: This computes the final total` |

**Note**: Derivation comments mark concepts as "un-decomposed" (`...:`) or "complete" (`/:`).

---

## Concrete Example

Here's a real inference from an addition algorithm:

```ncd
<- {digit sum} | ?{flow_index}: 1.2
    <= ::(sum {1}<$([all {unit place value} of numbers])%> and {2}<$({carry-over number}*1)%> to get {3}<$({sum})%>) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
    <- [all {unit place value} of numbers]<:{1}> | ?{flow_index}: 1.2.2
    <- {carry-over number}*1<:{2}> | ?{flow_index}: 1.2.3
    <- {sum}<:{3}> | ?{flow_index}: 1.2.4
```

**Breaking it down**:
- **Goal**: Produce a `{digit sum}` (flow_index: 1.2)
- **Functional Concept** (1.2.1): Sum operation with positional bindings using instance markers `<$()%>`
- **Value Concepts** (1.2.2-1.2.4): Three inputs with explicit position markers (`<:{1}>`, `<:{2}>`, `<:{3}>`)
- **Sequence**: `imperative` (calls an LLM or tool)

---

## Three Formats for Human Review

NormCode uses three formats for different purposes:

| Format | Author | Reader | Purpose |
|--------|--------|--------|---------|
| **`.ncds`** | Humans | Compiler | Natural language, easy to author |
| **`.ncd`** | Compiler | Execution engine | Formal, unambiguous, executable |
| **`.ncn`** | Compiler | Human reviewers | Natural language for verification |

**The workflow**:
1. You write `.ncds` (natural language with `<-`/`<=` markers)
2. Compiler generates `.ncd` (formal syntax with all annotations)
3. Compiler can also generate `.ncn` (readable narrative for review)
4. Orchestrator executes from `.ncd` → JSON repositories

---

## Why This Format Exists

### Resolving Ambiguities

The formal syntax exists because natural language is ambiguous:

| Ambiguity in `.ncds` | How `.ncd` Resolves It |
|----------------------|------------------------|
| "Add A and B" — which is first? | Value bindings (`<:{1}>`, `<:{2}>`) fix positions |
| "The result" — which result? | Identification markers (`<$({condition})=>`) distinguish instances |
| "Process the data" — LLM or code? | Operation markers (`::()` vs `&[{}]`) are explicit |
| "After step 3" — which step 3? | Flow indices (`1.2.3`) are unambiguous |
| "A number" — what type exactly? | Instance markers (`<$({number})%>`) enforce structure |

### When You'll Read `.ncd`

You don't write `.ncd` by hand, but you'll interact with it when:

1. **Debugging**: Tracing which step failed and why
2. **Auditing**: Verifying exactly what data each step saw
3. **Extending**: Building custom sequences or paradigms
4. **Optimizing**: Understanding compiler output to refine your `.ncds`

---

## Example: Full Translation Chain

### You write (`.ncds`):
```ncds
<- result files
    <= gather results from each phase
    <- Phase 1 output
        <= run the analysis paradigm
        <- analysis prompt
        <- input files
```

### Compiler generates (`.ncd`):
```ncd
:<:([all {phase 1 output}]) | ?{flow_index}: 1
    <= &[#] %>({Phase 1 output}) %: ({Phase 1 output})| ?{flow_index}: 1.1 | ?{sequence}: grouping
    <- {Phase 1 output} | ?{flow_index}: 1.2
        <= ::{paradigm}({prompt}<$({PromptTemplate})%>; {1}<$({Input})%>) | ?{flow_index}: 1.2.1 | ?{sequence}: imperative
        <- {analysis prompt}<:{prompt}> | ?{flow_index}: 1.2.2
        <- {input files}<:{1}> | ?{flow_index}: 1.2.3
```

### Reviewers see (`.ncn`):
```ncn
(OUTPUT) all phase 1 outputs to be outputted
    (ACTION) are obtained by collecting across the following
    (VALUE) Phase 1 output
        (ACTION) is obtained by running a model paradigm with a prompt template
        (VALUE) where the given prompt is the analysis prompt
        (VALUE) the input files are provided as the first input
```

**Key insight**: The `.ncd` is the "source of truth" that both humans and machines can verify.

---

## Honest Assessment: Tradeoffs

The `.ncd` syntax is dense by design, but this comes with real costs:

| Challenge | Reality |
|-----------|---------|
| **Syntax Density** | The markers (`:<:`, `<$()%>`, `<:{1}>`) create "punctuation soup" |
| **Verbosity** | A one-line operation can expand to 5+ lines of structure |
| **Fragility** | Indentation errors break flow index generation |
| **Overhead** | For simple tasks, the structure may not justify itself |

**Why accept these costs?**

1. **Progressive Formalization**: Start loose (`.ncds`), tighten to production-ready (`.ncd`)
2. **Auditability**: For high-stakes workflows, you *need* to prove what each step saw with auxillary format like (`.ncn`)
3. **Tooling Absorbs Complexity**: You don't write `.ncd` by hand—tools handle it

**The honest tradeoff**: NormCode's formalism is overkill for quick prototypes but essential for reliable, auditable, multi-step AI workflows.

---

## Next Steps

- **[Semantic Concepts](semantic_concepts.md)** - Deep dive into `{}`, `<>`, `[]`, and functional types
- **[Syntactic Operators](syntactic_operators.md)** - The `$`, `&`, `@`, `*` operators
- **[References and Axes](references_and_axes.md)** - How data is stored and manipulated
- **[Complete Syntax Reference](complete_syntax_reference.md)** - Full formal grammar

---

## Quick Reference

### Basic Markers
```
<-  Value concept (data)
<=  Functional concept (operation)
<*  Context concept (loop state)
:<: Output marker (final result)
:>: Input marker (external input)
```

### Comment Types
```
|?{sequence}: imperative     # Syntactical (structure)
|%{paradigm}: python_script  # Referential (data type)
|/: This computes X          # Derivation (description)
```

### Flow Index Example
Flow indices provide unique addresses for each step:

```ncd
<- _concept_to_infer_ | ?{flow_index}: (NN).1           /:Root concept (depth 0)
    <= _functional_concept_1_ | ?{flow_index}: (NN).1.1         /:First child (depth 1)
    <- _input_value_1_ | ?{flow_index}: (NN).1.2                /:Second child (depth 1)
        <= _functional_concept_2_ | ?{flow_index}: (NN).1.2.1       /:First grandchild (depth 2)
        <- _nested_input_1_ | ?{flow_index}: (NN).1.2.1.1           /:First great-grandchild (depth 3)
        <- _nested_input_2_ | ?{flow_index}: (NN).1.2.1.2           /:Second great-grandchild (depth 3)
    <- _input_value_2_ | ?{flow_index}: (NN).1.3                /:Third child (depth 1)
    <* _context_value_ | ?{flow_index}: (NN).1.4                /:Fourth child (depth 1)
```

---

**Ready to dive deeper?** Continue to [Semantic Concepts](semantic_concepts.md) to learn about the concept types that make up NormCode plans.
