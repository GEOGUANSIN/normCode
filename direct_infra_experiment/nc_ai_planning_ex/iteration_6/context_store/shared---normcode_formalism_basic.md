# 1. Introduction

NormCode is a semi-formal language used to construct a **plan of inferences**. It is designed to represent complex reasoning and data processing tasks not as a single, monolithic script, but as a structured combination of multiple, distinct inferences. It is considered semi-formal because the concepts are not merely placeholders; their semantic meaning is important to the functioning of the NormCode, particularly when an inference's logic is executed by a language model.

Each **inference** within the plan is a self-contained logical operation. The entire Normcode script orchestrates how these individual inferences connect and flow to achieve a larger goal.

# 2. Core Syntax: Inferences and Plan Structure

The fundamental unit of a Normcode plan is the **inference**. An inference is defined by a functional concept and its associated value concepts.

-   **Functional Concept (`<=`)**: This is the cornerstone of an inference. It "pins down" the inference by defining its core logic, function, or operation. Crucially, the functional concept is responsible for **invoking an agent's sequence** (e.g., `quantifying`, `imperative`), which is the underlying engine that executes the inference's logic.

-   **Value Concept (`<-`)**: This concept provides the concrete data for the inference. It specifies the inputs, outputs, parameters, or results that the functional concept operates on or produces.

-   **Context Concept (`<*`)**: A subtype of the value concept, often used in looping structures. It designates a concept that is being updated or carried forward (in-loop state) but is not the main target of the inference.

The entire plan is represented in various formats, where the default format is `.ncd` (NormCode Draft), or the vertical format. An inference begins with a root concept, followed by an indented functional concept (`<=`) that defines the operation. The value concepts (`<-`) and context concepts (`<*`) are then supplied at the same or a more deeply nested level.

# 2.1. NormCode Draft Format

The `.ncd` (NormCode Draft) format is the standard way to represent a plan of inferences.

**Meta-variable Convention (`_xxx_`):**
Throughout NormCode documentation and templates, terms enclosed in underscores (e.g., `_concept_to_infer_`, `_comment_`) indicate **meta-variables**. These are placeholders intended to be substituted with actual concept names, values, or descriptions during the planning process.

**Example Structure of one Inference:**
```ncd
_concept_to_infer_ /: The overall goal of this inference
    <= _functional_concept_defining_the_operation_ |?{sequence}: looping /: This invokes the 'looping' agent's sequence
    <- _input_value_concept_1_ /: This is an input for the operation
    <* _context_concept_1_ /: This is an in-loop state
```

In NormCode, a concept used in one inference can become the goal (`_concept_to_infer_`) of a subsequent, child inference. This tree-like structure allows for the construction of complex plans. Additionally, a single value concept may appear multiple times if it is the subject of several distinct inferences; in such cases, the logic follows the principle that the most recently inferred instance of the concept is the one utilized by the parent inference.

**Example Structure of a Plan:**
```ncd
_concept_to_infer_ /: The overall goal of this inference
    <= _functional_concept_defining_the_operation_ |?{sequence}: looping /: This invokes the 'looping' agent's sequence, a parent inference
    <- _input_value_concept_1_ /: This is the first inference for the input value concept 1
        <- _functional_concept_2_ |?{sequence}: imperative /: This invokes the 'imperative' agent's sequence, a child inference
        <- ....
    <- _input_value_concept_1_ /: This is the second inference for the input value concept 1
        <- _functional_concept_3_ |?{sequence}: imperative /: This invokes the 'imperative' agent's sequence, a child inference
        <- ....
        <- _context_concept_1_ /: This is when the context concept is used in a child inference.
    <* _context_concept_1_ /: This is an in-loop state, where it may be updated or carried forward
```

For the first concept of the plan, we usually use the `:<:` subject marker (`:<:(_first_concept_of_the_plan_)`) to mark the concept as the top-level goal of the entire plan, also indicating that it is to be outputted (an imperative act) as the final result of the plan.


### 2.1.1. Flow Index Generation Principles

The flow index (e.g., `1.1.2`) serves as a unique address for each step in the plan. It is determined by the following rules:

1.  **Concept Lines (`:<:`, `<=`, `<-`, `<*`)**: These lines act as counters. The index is generated based on **indentation depth**. When a concept line is encountered at a specific depth, its counter at that depth is incremented, and any counters at deeper levels are reset. The resulting chain of counters forms the flow index. The first concept of the plan is always at depth 0 and, normally, there should be no other concept at depth 0.
2.  **Comment Lines**: Pure comment lines (starting with `|`, `?`, or text without concept markers) **inherit** the flow index of the **last seen concept line**. If a comment appears at the top of the file before any concept, it has no flow index (`None`). Comments on the same line as a concept (following `|`) share the **exact same flow index** as that concept.


### 2.1.2. Comments and Metadata

A line in Normcode can also have optional comments for clarity, control, and metadata:

`_concept_definition_ (optionally new line) | _comment_`

-   **`_concept_definition_`**: The core functional (`<=`), value (`<-`), or context (`<*`) statement.
-   **`_comment_`**: Optional metadata or description following the `|` symbol. Two main types of commenting norms are used:
    
    1.  **Syntactical Comments (`?{...}:`)**: These relate to the structure and flow of the NormCode.
        -   `?{sequence}:`: Specifies the invoked **agent's sequence**.
        -   `?{flow_index}:`: The unique identifier for the step (e.g., `1.1.2`).
        -   `?{natural_language}:`: A natural language description of the step.
    
    2.  **Referential Comments (`%{...}:`)**: These comment on the reference or type of data a concept holds.
        -   `%{paradigm}:`: Defines the execution paradigm or pattern.
        -   `%{location_string}:`: Specifies the location of the concept in the file.
 
    3.  **Translation Comments**: Used during the deconstruction phase in `.ncd` (NormCode Draft) files to document the translation process.
        
        *(Note: In the ideal practice, these should be unified to start with `|` to match other comments, e.g., `|...:`, but currently they may appear without it.)*

        -   `...:` (or `|...:`) **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. A concept with a `...:` comment is considered "un-decomposed."
        -   `?:` (or `|?:`) **Question**: The question being asked about the source text to guide the decomposition.
        -   `/:` (or `|/:`) **Description**: A human-readable summary of the result of a decomposition, marking a concept as definitive and complete.



## 2.2. Example of a Concrete Inference

The following snippet from an addition algorithm shows an `imperative` inference.

```ncd
<- {digit sum} | ?{flow_index}: 1.1.2 | ?{sequence}: imperative
    <= ::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)
    <- [all {unit place value} of numbers]<:{1}>
    <- {carry-over number}*1<:{2}>
    <- {sum}?<:{3}>
```
- **Goal**: The overall goal is to produce a `{digit sum}`.
- **Functional Concept (`<=`)**: The core of the inference is the `({})` (imperative) concept, which defines a command to sum two numbers. This invokes the `imperative` agent's sequence (indicated by `?{sequence}: imperative`).
- **Value Concepts (`<-`)**: It takes two inputs (`[all {unit place value} of numbers]` and `{carry-over number}*1`) and specifies one output (`{sum}`).

# 3. Concept Types

Concepts are the building blocks of NormCode and are divided into two major classes: **Semantical** and **Syntactical**. The core inference operators (`<=` and `<-`) are explained in the Core Syntax section above.

## 3.1. Semantical Concept Types and References

Semantical concepts define the core entities and logical constructs of the domain. Crucially, each semantical concept is backed by a **Reference**—a multi-dimensional tensor that holds its content. The nature of this reference defines the concept's role:

1.  **Object References (Data)**: For objects (i.e.,`{}`, `<>`, `[]`), the reference acts as a **holder of information**. It contains the concrete data, values, or state that will be retrieved and processed.
2.  **Subject References (Agent/Body)**: For subjects (`:S:`), the reference represents a **body or collection of tools**, along with the syntactical sequences required to process data within that body.
3.  **Functional References (Paradigm)**: For functional concepts (`({})`, `<{}>`), the reference serves as the **joining point** between the Object and the Subject. It typically contains a **paradigm** (or other normative directives, like a script or prompt) that configures the Subject to process the functional/value inputs and structure the resulting values.

### 3.1.1. Typically Non-Functional Concept Types
These concepts represent entities, their relationships, or their roles in the inference.

#### Objects and Special Objects

| Symbol                | Name                      | Description                                                                 |
| --------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `{}`                  | Object                    | Represents a generic object or entity. **Reference**: Holds data/state.     |
| `<>`                  | Proposition               | Represents a proposition or a state of affairs (non-functional). (In older versions: *Statement*) |
| `[]`                  | Relation                  | Represents a relationship between two or more concepts.                     |

### 3.1.2. The Subject Concept

| Symbol                | Name                      | Description                                                                 |
| --------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `:S:`                 | Subject                   | Marks the active agent or system. **Reference**: Holds tools and sequences. |

### 3.1.3. Concept Markers (Roles)
These markers wrap other concepts to define their specific role in the plan structure.

| Symbol                | Name                      | Description                                                                 |
| --------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `:>:`                 | Input Marker              | Wraps a concept to mark it as an external input parameter (e.g., `:>:{user}`). |
| `:<:`                 | Output Marker             | Wraps a concept to mark it as a final output/goal (e.g., `:<:({result})`). |
| `:_:`                 | NormCode Subject          | A special subject marker for bounded process requests or method definitions which are itself normcode plans (currently not implemented). |

**Examples:**
- **Object (`{}`):** `{new number pair}` declares a concept that will hold the state of the two numbers as they are processed.
- **Proposition (`<>`):** `<all number is 0>` represents a condition that can be evaluated.
- **Relation (`[]`):** `[all {unit place value} of numbers]` defines a collection.

**NormCode Subject (`:_:`)**, **Nominalization (`$::`)**, and **Method (`@by`)** are **non-serial concepts**.
> **Warning**: These concepts alter the standard sequential flow of the plan. They are effectively meta-instructions that restructure the logic rather than executing a direct step.
> *Note: These are **not currently implemented** in the active version of the NormCode execution engine (orchestrator) and are typically "translated away" (compiled into simpler structures) before execution.*

### 3.1.2. Typically Functional Concept Types
These concepts define operations or evaluations that often initiate an inference. It is important to note that **all functional semantical concepts need a Subject to drive them**. This Subject acts as the active agent or system responsible for executing the function.

| Symbol                | Name                      | Description                                                                 |
| --------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `({})` (`::({})` in old version)      | Imperative                | Represents a command or an action to be executed. (In older versions: *Functional Imperative*)                           |
| `<{}>` (`::<{}>` in old version)     | Judgement                 | Represents an evaluation that results in a boolean-like assessment. (In older versions: *Functional Judgement*)         |

**Structure of Functional Concepts in Formal Usage (Optional):**

1.  **Imperative Format:**
    ` :_Subject_:{_norm_}(_functional_input_with_value_placements_)`
    *   **`_Subject_`**: The entity performing the action (reference contains tools/sequences).
    *   **`_norm_`**: Specifies the **paradigm** (e.g., `sequence: imperative`, `paradigm: python_script`) stored in the functional reference.
    *   **`_functional_input_...`**: The vertical input defining the operation (e.g., the instruction text or script body).
    *   **`..._value_placements_`**: Horizontal inputs that map specific values into the operation (e.g., variables `{1}`, `{2}`).

2.  **Judgement Format:**
    ` :_Subject_:{_norm_}(_functional_input_with_value_placements_) <_truth_asserting_>`
    *   Extends the imperative format.
    *   **`<_truth_asserting_>`**: Usually a quantifier plus a condition (e.g., `ALL True`, `ANY 0`, `EXISTS`). It collapses a reference tensor's values into a single boolean-like value, which is essential for **timing operators** (like `@if`) to function.

**Examples of Functional Concepts in Use:**
- **Imperative (`({})`):** `::(get the {1}?<$({remainder})%> of {2}<$({digit sum})%> divided by 10)` issues a command to a tool or model to perform a calculation. This is the heart of an `imperative` inference.
- **Judgement (`<{}>`):** `<= :%(True):<{1}<$({carry-over number})%> is 0>` evaluates whether the carry-over is zero. This is the core of a `judgement` inference. Note the use of `<...>` as a common syntax variant for a judgement.

## 3.2. Syntactical Concept Types

Syntactical concepts are operators that control the logic, flow, and manipulation of data within the plan of inferences. They are grouped by their function.

### 3.2.1. Assigning Operators

| Symbol | Name           | Description                                                        |
| ------ | -------------- | ------------------------------------------------------------------ |
| `$=`   | Identity     | Assigns a value to a concept, often used for state updates.          |
| `$.`   | Specification  | Specifies or isolates a particular property of a concept.          |
| `$%`   | Abstraction    | Creates a general template from a concrete instance for reuse.     |
| `$+`   | Continuation   | Appends or adds to a concept, often used in loops to update state. |
| `$-`   | Selecting      | Selects or filters a subset or element from a concept.             |
| `$::`  | Nominalization | Transforms a process or action (imperative) into a concept (noun) (currently not implemented). |

**Examples:**
- **Identity (`$=`):** `<- {number pair}<$={1}>` is used to give a stable identity (`1`) to the `{number pair}` concept across multiple steps of the algorithm.
- **Specification (`$.`):** `<= $.({remainder})` specifies that this part of the inference is focused solely on defining the `{remainder}`.
- **Abstraction (`$%`):** `<$([all {unit place value} of numbers])%_>` takes the concrete list of digits and abstracts it as an input parameter for the `sum` imperative.
- **Continuation (`$+`):** `<= $+({number pair to append}:{number pair})` defines an operation that updates the `{number pair}` for the next iteration of a loop.

### 3.2.2. Timing Operators

| Symbol     | Name      | Description                               |
| ---------- | --------- | ----------------------------------------- |
| `@if`      | If        | Executes if a condition is true.          |
| `@if!`     | If Not    | Executes if a condition is false.         |
| `@after`   | After     | Executes after a preceding step is complete. |
| `@by`      | Method    | Specifies the method or means by which an action is performed (currently not implemented). |

**Examples:**
- **If / If Not (`@if`, `@if!`):** The combination ` @if!(<all number is 0>)` and `@if(<carry-over number is 0>)` forms the termination condition for the main loop, ensuring it continues as long as there are digits to process or a carry-over exists.
- **After (`@after`):** ` <= @after({digit sum})` ensures that the remainder is only calculated *after* the `digit sum` has been computed in a prior step.

### 3.2.3. Grouping Operators

| Symbol    | Name   | Description                                           |
| --------- | ------ | ----------------------------------------------------- |
| `&in`     | In     | Groups items contained within a larger collection.    |
| `&across` | Across | Groups items by iterating across a collection.        |

**Examples:**
- **Across (`&across`):** `<= &across({unit place value}:{number pair}*1)` is a `grouping` inference that iterates across the two numbers in the `{number pair}` and extracts the `{unit place value}` (the rightmost digit) from each, creating a new group of digits to be summed.
- **In (`&in`):** Used to create a collection from explicitly listed value concepts. The elements to be grouped are provided as `<-` concepts within the inference.


### 3.2.4. Looping Operators
*(Note: In older versions, this was referred to as **Quantifying** or **Listing** operators.)*

| Symbol   | Name  | Description                                        |
| -------- | ----- | -------------------------------------------------- |
| `*every` | Every | Iterates over every item in a collection (a loop). |

**Example:**
- **Every (`*every`):** `<= *every({number pair})` defines the main loop of the addition algorithm. This functional concept invokes the `looping` (previously `quantifying`) agent's sequence, which will continue to execute its child inferences as long as the termination condition (defined with `@if` operators) is not met.

### 3.2.5. Concept Markers
These markers can be appended to concepts to modify their meaning.

| Symbol                | Name                 | Description                                                                 |
| --------------------- | -------------------- | --------------------------------------------------------------------------- |
| `?`                   | Conception Query     | Appended to a concept to query its value or definition. E.g., `{sum}?`. |
| `<:_number/placeholder_>`         | Value Placement       | To link a positional placeholder for values (e.g., `<:{1}>`, `<:{2}>`).     |
| `<$(_concept_)%>`     | Instance Marker      | Marks a concept as an instance of an "umbrella" concept. E.g. `<$({number})%>` (In older versions: `<$(_concept_)%_>`) |
| `<$={_number_}>`      | Identity Marker      | Identifies the same concept across different occurrences. E.g. `<$={1}>`     |
| `%:[_concept_]`       | Axis Specifier       | Specifies the `by_axis` for an operation. E.g. `%:[{number pair}]`        |
| `@(_number_)`         | Quantifier Index     | Specifies the index for a quantifier (`*every`) operation. E.g. `@(1)`       |
| `*_number_`           | Quantifier Version   | Links a concept to a specific quantifier iteration. E.g. `{number pair}*1`  |
| `%{_norm_}(_ref_)`   | Perception Norm & Ref| Specifies the norm of perception `{_norm_}` and referred name `(_ref_)`. |
| `{%(_name_)}`         | Direct Reference     | A concept that directly references the object `%(_name_)`. |

# 4. Critique, Design Philosophy, and Usage Clarification

## 4.1. Critique and Challenges

While NormCode provides a rigorous structure for AI planning, it introduces specific challenges that define its usage profile:

1.  **High Cognitive Load (Syntax Density)**: The language relies heavily on symbolic markers (`:<:`, `<=`, `<*`, `?{...}`) and strict indentation rules. This creates a "punctuation soup" that can be difficult for humans to parse or write manually without tooling support.
2.  **Verbosity**: NormCode requires explicit definition of every logical step, subject, and value transfer. Simple operations that might take one line in Python or English can expand into multiple lines of NormCode structure. This makes it "heavy" for trivial tasks.
3.  **Fragility to Manual Editing**: The reliance on indentation for `flow_index` generation means that whitespace errors can break the logical addressability of the plan, making manual editing error-prone.
4. **Overhead vs. native LLM capabilities**: Modern LLMs are rapidly improving at chain-of-thought reasoning and tool orchestration. The question is whether NormCode's explicit structure adds enough value over letting a capable model reason natively. For high-stakes, auditable workflows? Probably yes. For routine tasks? The overhead may not justify itself.

## 4.2. Design Philosophy

NormCode is designed as a **Dual-Readability Intermediate Representation (IR)** to address these challenges. It acts as a rigorous bridge between high-level human intent and low-level agent execution.

1.  **Dual-Readability & Compiler Ecosystem**: NormCode manages its inherent complexity through a two-way compiler ecosystem, reducing the need for manual interaction:
    *   **AI-Facing (Deconstruction)**: An "Input Compiler" methodically transforms natural language prompts into rigorous NormCode plans (`.ncd`), handling the syntax generation automatically.
    *   **Human-Facing (Translation)**: An "Output Compiler" translates these plans into **NormCode Natural (`.ncn`)**, a human-readable narrative. This allows humans to verify the *logic* of the plan without needing to parse the dense syntax.

2.  **Progressive Formalization (The Semi-Formal Balance)**: By combining strict control flow (`.ncd` structure) with natural language concept definitions, NormCode enables a unique development lifecycle. Developers can start with high-level, creative, and model-reliant instructions, and then **step-by-step decompose** them into more rigorous, deterministic structures. This allows a system to evolve from "creative/probabilistic" to "robust/structured" with high intervenability.

3.  **Role in the Pipeline**: In the context of the AI Planning Pipeline, NormCode serves as the structured blueprint. While humans can read and edit it (critical for review), its primary role is to act as the rigorous bridge that compiles ambiguous natural language into a verifiable, executable Python script.

## 4.3. Example: NormCode (.ncd) vs. NormCode Natural (.ncn)

The following example demonstrates how the rigorous `.ncd` syntax translates into the readable `.ncn` format while maintaining the exact same logical structure.

**Presumed Overall Prompt:**
"The result files to be outputted are obtained across the following Phases. Phase 1: Confirmation of Instruction. This specifies the class of 1.1_instruction_block.md and 1.2_initial_context_registerd.json. 1.1_instruction_block.md is obtained by running a model paradigm that takes a prompt template to process the input and save the outcome, where the given prompt is the instruction distillation prompt, the save directory is the output dir, and the input files are provided as the first input....."

**NormCode Draft (.ncd):** The "Source Code" for the Agent.
```ncd
:<:({result files})
    <= &across
    <- {Phase 1: Confirmation of Instruction}
        <= $.([{1.1_instruction_block.md}, {1.2_initial_context_registerd.json}])
        <- {1.1_instruction_block.md}
            <= :%(Composition):{paradigm}({prompt}<$({PromptTemplateWInputOther})%>; {output}<$({SaveDir})%>; {1}<$({Input})%>)
            <- {instruction distillation prompt}<:{prompt}>
            <- {output dir}<:{output}>
            <- {input files}<:{1}>
|...(more phases)...
```

**NormCode Natural (.ncn):** The "Readable Narrative" for the Human.
```ncn
(OUTPUT) the result files to be outputted
    (ACTION) are obtained across the following
    (VALUE) Phase 1: Confirmation of Instruction
        (ACTION) specifies the class of 1.1_instruction_block.md and 1.2_initial_context_registerd.json
        (VALUE) 1.1_instruction_block.md
            (ACTION) is obtained by running a model paradigm that takes a prompt template to process the input and save the outcome
            (VALUE) where the given prompt is the instruction distillation prompt
            (VALUE) the save directory is the output dir
            (VALUE) the input files are provided as the first input
|...(more phases)...
```

This dual format allows the AI to execute the precise instructions in `.ncd` while the human verifies the intent in `.ncn`.
