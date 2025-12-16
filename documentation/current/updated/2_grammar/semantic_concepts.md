# Semantic Concepts

**The vocabulary of NormCode—how to represent entities, states, actions, and evaluations.**

---

## Overview

Semantical concepts are the "words" of NormCode. They map specific parts of natural language thoughts into rigorous, executable structures. Each concept type corresponds to a linguistic category and plays a distinct role in the inference plan.

**Key principle**: Each semantic concept is backed by a **Reference**—a multi-dimensional tensor that holds its content. The nature of this reference defines the concept's role.

---

## The Two Major Classes

| Class | Purpose | Examples |
|-------|---------|----------|
| **Non-Functional** | Represent entities, states, relationships | `{}`, `<>`, `[]`, `:S:` |
| **Functional** | Represent operations and evaluations | `({})`, `<{}>` |

---

## Non-Functional Concepts (Entities)

These concepts represent the "nouns" and "states" of your reasoning—the things being manipulated or observed.

### Object `{}`

**Symbol**: `{_concept_name_}`  
**Reference Type**: Holds concrete data, values, or state (e.g., String, Int, File, Object)

**Definition**: Represents a generic entity, item, or distinct piece of information.

**Natural Language Extraction**:
- **Nouns & Noun Phrases**: Look for the core subjects and objects
- *Example*: "Calculate the **sum** of the **digits**." → `{sum}`, `{digits}`
- *Example*: "The **user input** is invalid." → `{user input}`

**In Plans**:
```ncd
<- {document summary}
    <= ::(summarize the document)
    <- {document}
```

---

### Proposition `<>`

**Symbol**: `<_concept_name_>`  
**Reference Type**: Holds a boolean-like state or descriptive statement

**Definition**: Represents a state of affairs, a condition, or a fact that can be true or false. It describes *how things are*, not an action to change them.

**Natural Language Extraction**:
- **Declarative Clauses**: Phrases describing state using "is", "are", "have"
- **Conditions**: The condition part of an "if" statement
- *Example*: "**The file exists**." → `<file exists>`
- *Example*: "Check if **the value is greater than 10**." → `<value is greater than 10>`

**In Plans**:
```ncd
<- final result
    <= @:'(<validation passed>)  # Only execute if true
    <- validated output
```

**Special Elements**: Propositions use truth value elements:
- `%{truth_value}(True)`
- `%{truth_value}(False)`

---

### Relation `[]`

**Symbol**: `[_concept_name_]`  
**Reference Type**: Holds a collection (List) or a mapping (Dict)

**Definition**: Represents a group of items or a relationship between multiple entities.

**Natural Language Extraction**:
- **Plurals**: "The **files**", "The **numbers**"
- **Groupings**: "A **list of** items", "The **set of** parameters"
- *Example*: "Iterate through all **input files**." → `[input files]`
- *Example*: "The **pairs of numbers**." → `[pairs of numbers]`

**In Plans**:
```ncd
<- all summaries
    <= *.(...)  # Loop over collection
    <* [documents to process]
```

---

### Subject `:S:`

**Symbol**: `:S:` or `:_Name_:`  
**Reference Type**: Holds a "Body" of tools and capabilities

**Definition**: The active agent or system responsible for executing the logic. Defines *who* is doing the work.

**Natural Language Extraction**:
- **Implicit Actor**: Often implied in imperative sentences ("(You) calculate this")
- **Explicit Systems**: "The **Planner** should...", "The **Python Tool** runs..."
- *Note*: In most simple plans, the subject is implicit (the default agent)

**In Plans**:
```ncd
<= :LLMAgent:{paradigm}(...)  # Explicit subject with body configuration
```

---

### Special Subject Markers (`:>:`, `:<:`)

These wrappers define the "boundary roles" of a concept within the plan:

| Marker | Name | Purpose | Example |
|--------|------|---------|---------|
| `:>:` | Input Marker | Marks external input data | `:>:({user query})` |
| `:<:` | Output Marker | Marks final output/goal | `:<:({final result})` |

**Natural Language Extraction**:
- **Input**: "Given **X**...", "Input is **Y**..."
- **Output**: "Return **Z**...", "The goal is to find **W**..."

**In Plans**:
```ncd
:<:({final answer})              # This is what we output
    <= ::(process)
    <- {user query}
        <= :>:({user query})     # This comes from outside
```

---

## Functional Concepts (Operations)

These concepts represent the "verbs"—operations that transform data or evaluate states. They invoke **Agent Sequences** to do the work.

### Imperative `({})`

**Symbol**: `({_concept_name_})` or `::(_concept_name_)`  
**Associated Sequence**: `imperative`  
**Reference Type**: Holds the *Paradigm* (the logic/code to execute)

**Definition**: Represents a command, action, or transformation. It changes the state of the world or produces new data.

**Natural Language Extraction**:
- **Active Verbs**: "Calculate", "Find", "Generate", "Extract", "Save"
- **Action Phrases**: "Get the result", "Run the script"
- *Example*: "**Sum** the two numbers." → `::(sum the two numbers)`
- *Example*: "**Read** the file content." → `::(read the file content)`

**In Plans**:
```ncd
<- {result}
    <= ::(calculate sum of {1} and {2})
    <- {number A}<:{1}>
    <- {number B}<:{2}>
```

**Structure (Full Form)**:
```
:_Subject_:{_paradigm_}(_functional_input_with_value_placements_)
```

- **Subject**: The entity performing the action (holds tools/sequences)
- **Paradigm**: Execution strategy (e.g., `sequence: imperative`, `paradigm: python_script`)
- **Functional input**: The instruction or script
- **Value placements**: Variables mapped into the operation (`{1}`, `{2}`, etc.)

---

### Judgement `<{}>`

**Symbol**: `<{_concept_name_}>` or sometimes just `<...>`  
**Associated Sequence**: `judgement`  
**Reference Type**: Holds the *Paradigm* plus a *Truth Assertion*

**Definition**: Represents an evaluation, assessment, or check. Results in a decision (True/False) typically used to control flow.

**Natural Language Extraction**:
- **Questions**: "Is the file empty?", "Does the value match?"
- **Evaluations**: "Check validity", "Verify format"
- *Example*: "**Is** the carry-over 0?" → `<{carry-over is 0}>`
- *Example*: "**Check if** finished." → `<{is finished}>`

**In Plans**:
```ncd
<- should continue
    <= ::<{all items processed}>  # Evaluates to true/false
    <- [items]
```

**Structure (Full Form)**:
```
:_Subject_:{_paradigm_}(_functional_input_with_value_placements_) <_truth_asserting_>
```

Extends imperative format with:
- **Truth asserting**: Quantifier + condition (e.g., `ALL True`, `ANY 0`, `EXISTS`)
- **Collapses**: Reference tensor values into a single boolean-like value

---

## Reference Types by Concept

Understanding what each concept's Reference holds:

| Concept | Reference Holds | Role |
|---------|----------------|------|
| **Object (`{}`)** | Data/state (String, Int, File) | Information holder |
| **Proposition (`<>`)** | Boolean state | Condition indicator |
| **Relation (`[]`)** | Collection (List/Dict) | Group container |
| **Subject (`:S:`)** | Body + tools | Agent/executor |
| **Imperative (`({})`)** | Paradigm + instruction | Operation definition |
| **Judgement (`<{}>`)** | Paradigm + truth assertion | Evaluation definition |

---

## From Natural Language to NormCode

### Quick Mapping Table

| NLP Feature | Part of Speech | NormCode Concept | Symbol |
|-------------|----------------|------------------|--------|
| **Entities** | Noun (Singular) | Object | `{}` |
| **States/Facts** | Clause (Static) | Proposition | `<>` |
| **Collections** | Noun (Plural) | Relation | `[]` |
| **Actions** | Verb (Imperative) | Imperative | `({})` |
| **Questions** | Verb (Interrogative) | Judgement | `<{}>` |
| **Actors** | Subject Noun | Subject | `:S:` |

### Example Transformation

**Natural Language**:
> "Calculate the sum of the numbers in the list, then check if the sum exceeds 100."

**NormCode Concepts**:
- `{sum}` - Object (the result)
- `[numbers]` - Relation (the collection)
- `::(calculate the sum)` - Imperative (the action)
- `<{sum exceeds 100}>` - Judgement (the evaluation)

**Complete Plan**:
```ncd
:<:{final decision}
    <= <{sum exceeds 100}>
    <- {sum}
        <= ::(calculate sum of all numbers)
        <- [numbers]
```

---

## The Role of Syntax in Semantics

While NormCode uses various brackets and markers (e.g., `{}`, `[]`, `<>`), the syntax serves two key purposes before **activation compilation**:

### 1. Identity Establishment

The system must identify whether two occurrences refer to the **same entity** or distinct instances:

**Same Entity**:
- `{file path}` in Step 1 and `{file path}` in Step 5 → linked automatically
- Identical concept names resolve to the same reference

**Distinct Entities**:
- `{file path}<$={1}>` and `{file path}<$={2}>` → treated as different
- Syntax variants imply different positions/versions

### 2. Working Interpretation Extraction

The system must extract the core meaning, including:
- Concept type (object, proposition, etc.)
- Sequence to invoke (imperative, judgement, etc.)
- Parameters (value order, selectors, etc.)

**Defaults**: In simple cases like `::(Calculate Sum)`:
- **Sequence**: `imperative`
- **Mode**: Default agent mode (composition)
- **Paradigm**: Default paradigm
- **Value Order**: Same as provision order in the plan

**Explicit Auxiliaries**: In complex cases, markers like `{1}`, `{2}`, `<:{1}>` define:
- Non-default behavior
- Value order and selection logic
- Specific parameter mapping

### 3. Abstraction Formalization

The **Instance Marker** (`Y<$(_X_)%>`) explicitly links concrete to abstract:

```ncd
{daily report file}<$({text file})%>
```

**Meaning**: "Treat `{daily report file}` as a `{text file}` for tool selection."

**Usage**: Links specific concepts to general patterns/paradigms during activation.

---

## Advanced Semantic Features

### Non-Serial Concepts (Not Currently Implemented)

These alter the standard sequential flow:

| Concept | Symbol | Purpose | Status |
|---------|--------|---------|--------|
| **NormCode Subject** | `:_:` | Bounded process requests/method definitions | Not implemented |
| **Nominalization** | `$::` | Transform process into noun | Not implemented |
| **Method** | `@by` | Specify execution method | Not implemented |

> **Warning**: These are meta-instructions that restructure logic rather than executing direct steps. They are typically "translated away" during compilation.

---

## Practical Examples

### Example 1: Document Processing

```ncd
:<:{processed documents}
    <= &[#]  # Group across (syntactic)
    <- {processed document}
        <= ::(clean and format the document)  # Imperative
        <- {raw document}
    <* [documents]
```

**Concepts used**:
- `{processed documents}` - Object (final result)
- `{processed document}` - Object (single item)
- `{raw document}` - Object (input item)
- `[documents]` - Relation (collection to iterate)
- `::(clean and format...)` - Imperative (operation)

---

### Example 2: Conditional Workflow

```ncd
:<:{final output}
    <= @:'(<validation passed>)  # Conditional (syntactic)
    <- {validated output}
        <= ::(validate the draft)  # Imperative
        <- {draft output}
            <= ::(generate draft)  # Imperative
            <- {input data}
    <- <validation passed>
        <= <{output meets requirements}>  # Judgement
        <- {draft output}
        <- {requirements}
```

**Concepts used**:
- `{final output}`, `{validated output}`, `{draft output}` - Objects (data)
- `<validation passed>` - Proposition (condition)
- `<{output meets requirements}>` - Judgement (evaluation)
- `::(validate...)`, `::(generate...)` - Imperatives (actions)

---

## Summary

| Concept Type | Symbol | Role | LLM Call? |
|--------------|--------|------|-----------|
| **Object** | `{}` | Data/entity | No (holds data) |
| **Proposition** | `<>` | State/condition | No (holds bool) |
| **Relation** | `[]` | Collection | No (holds list) |
| **Subject** | `:S:` | Agent/tools | No (configuration) |
| **Imperative** | `({})` | Action/command | ✅ Yes |
| **Judgement** | `<{}>` | Evaluation | ✅ Yes |

**Key insight**: Only functional concepts (imperative, judgement) invoke LLM calls. Everything else is data structure.

---

## Next Steps

- **[Syntactic Operators](syntactic_operators.md)** - Learn the `$`, `&`, `@`, `*` operators
- **[References and Axes](references_and_axes.md)** - How data is stored in multi-dimensional tensors
- **[Complete Syntax Reference](complete_syntax_reference.md)** - Full formal grammar

---

## Quick Reference

### Concept Symbols
```
{}     Object (entity/data)
<>     Proposition (state/condition)
[]     Relation (collection)
:S:    Subject (agent/actor)
({})   Imperative (action/command)
<{}>   Judgement (evaluation/check)
```

### Special Markers
```
:>:    Input marker (external data)
:<:    Output marker (final result)
:_:    NormCode subject (not implemented)
```

### Extraction Hints
```
Nouns          → {}   Objects
Plurals        → []   Relations
"is", "are"    → <>   Propositions
Action verbs   → ({}) Imperatives
Questions      → <{}> Judgements
```

---

**Ready to learn about operators?** Continue to [Syntactic Operators](syntactic_operators.md).
