# NormCode Guide

## 1. Introduction

NormCode is a semi-formal language used to construct a **plan of inferences**. It is designed to represent complex reasoning and data processing tasks not as a single, monolithic script, but as a structured combination of multiple, distinct inferences. It is considered semi-formal because the concepts are not merely placeholders; their semantic meaning is important to the functioning of the NormCode, particularly when an inference's logic is executed by a language model.

Each **inference** within the plan is a self-contained logical operation. The entire Normcode script orchestrates how these individual inferences connect and flow to achieve a larger goal.

## 2. Core Syntax: Concepts, and Inferences

The fundamental unit of a Normcode plan is the **inference**. An inference is defined by a functional concept and its associated value concepts.

-   **Functional Concept (`<=`)**: This is the cornerstone of an inference. It "pins down" the inference by defining its core logic, function, or operation. Crucially, the functional concept is responsible for **invoking an agent's sequence** (e.g., `quantifying`, `imperative`), which is the underlying engine that executes the inference's logic.

-   **Value Concept (`<-`)**: This concept provides the concrete data for the inference. It specifies the inputs, outputs, parameters, or results that the functional concept operates on or produces.

The entire plan is represented in a hierarchical, vertical format. An inference begins with a root concept, followed by an indented functional concept (`<=`) that defines the operation. The value concepts (`<-`) are then supplied at the same or a more deeply nested level.

A line in Normcode can also have optional annotations for clarity and control:

`_concept_definition_ | _annotation_ // _comment_`

-   **`_concept_definition_`**: The core functional (`<=`) or value (`<-`) statement.
-   **`_annotation_`**: Optional metadata following the `|` symbol. This can be a **flow index** (e.g., `1.1.2`), an intended **data reference**, or the name of the invoked **agent's sequence**.
-   **`// _comment_`**: Human-readable comments.


**Example Structure of an Inference:**
```Normcode
_concept_to_infer_ // The overall goal of this inference
    <= _functional_concept_defining_the_operation_ | 
    quantifying // This invokes the 'quantifying' agent's sequence
    <- _input_value_concept_1_ // This is an input for the 
    operation
    <- _input_value_concept_2_
```

**Example of a Concrete Inference:**

The following snippet from an addition algorithm shows an `imperative` inference.

```Normcode
<- {digit sum} | 1.1.2. imperative
    <= ::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)
    <- [all {unit place value} of numbers]<:{1}>
    <- {carry-over number}*1<:{2}>
    <- {sum}?<:{3}>
```
- **Goal**: The overall goal is to produce a `{digit sum}`.
- **Functional Concept (`<=`)**: The core of the inference is the `::` (imperative) concept, which defines a command to sum two numbers. This invokes the `imperative` agent's sequence.
- **Value Concepts (`<-`)**: It takes two inputs (`[all {unit place value} of numbers]` and `{carry-over number}*1`) and specifies one output (`{sum}`).

## 3. Concept Types

Concepts are the building blocks of NormCode and are divided into two major classes: **Semantical** and **Syntactical**. The core inference operators (`<=` and `<-`) are explained in the Core Syntax section above.

### 3.1. Semantical Concept Types

Semantical concepts define the core entities and logical constructs of the domain. They can be subdivided into typically non-functional and functional types.

#### 3.1.1. Typically Non-Functional Concept Types
These concepts represent entities, their relationships, or their roles in the inference.

| Symbol                | Name                      | Description                                                                 |
| --------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `{}`                  | Object                    | Represents a generic object or entity.                                      |
| `<>`                  | Statement                 | Represents a proposition or a state of affairs (non-functional).            |
| `[]`                  | Relation                  | Represents a relationship between two or more concepts.                     |
| `:S:`                 | Subject                   | Marks the subject of a relation or statement.                               |
| `:>:`                 | Input                     | A special type of Subject that marks a concept as an input parameter.       |
| `:<:`                 | Output                    | A special type of Subject that marks a concept as an output value.          |

**Examples:**
- **Object (`{}`):** `{new number pair}` declares a concept that will hold the state of the two numbers as they are processed.
- **Statement (`<>`):** `<all number is 0>` represents a condition that can be evaluated. The `judgement` agent's sequence will determine if this statement is true or false.
- **Relation (`[]`):** `[all {unit place value} of numbers]` defines a collection that will hold the digits from a specific place value of the numbers being added.

#### 3.1.2. Typically Functional Concept Types
These concepts define operations or evaluations that often initiate an inference.

| Symbol                | Name                      | Description                                                                 |
| --------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `({})` or `::()`      | Imperative                | Represents a command or an action to be executed.                           |
| `<{}>` or `<...>`     | Judgement                 | Represents an evaluation that results in a boolean-like assessment.         |

**Examples:**
- **Imperative (`::()`):** `::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10)` issues a command to a tool or model to perform a calculation. This is the heart of an `imperative` inference.
- **Judgement (`<...>`):** `<= :%(True):<{1}<$({carry-over number})%_> is 0>` evaluates whether the carry-over is zero. This is the core of a `judgement` inference. Note the use of `<...>` as a common syntax variant for a judgement.

### 3.2. Syntactical Concept Types

Syntactical concepts are operators that control the logic, flow, and manipulation of data within the plan of inferences. They are grouped by their function.

#### 3.2.1. Assigning Operators

| Symbol | Name           | Description                                                        |
| ------ | -------------- | ------------------------------------------------------------------ |
| `$=`   | Identity     | Assigns a value to a concept, often used for state updates.          |
| `$.`   | Specification  | Specifies or isolates a particular property of a concept.          |
| `$%`   | Abstraction    | Creates a general template from a concrete instance for reuse.     |
| `$+`   | Continuation   | Appends or adds to a concept, often used in loops to update state. |

**Examples:**
- **Identity (`$=`):** `<- {number pair}<$={1}>` is used to give a stable identity (`1`) to the `{number pair}` concept across multiple steps of the algorithm.
- **Specification (`$.`):** `<= $.({remainder})` specifies that this part of the inference is focused solely on defining the `{remainder}`.
- **Abstraction (`$%`):** `<$([all {unit place value} of numbers])%_>` takes the concrete list of digits and abstracts it as an input parameter for the `sum` imperative.
- **Continuation (`$+`):** `<= $+({number pair to append}:{number pair})` defines an operation that updates the `{number pair}` for the next iteration of a loop.

#### 3.2.2. Timing (Sequencing) Operators

| Symbol     | Name      | Description                               |
| ---------- | --------- | ----------------------------------------- |
| `@if`      | If        | Executes if a condition is true.          |
| `@if!`     | If Not    | Executes if a condition is false.         |
| `@after`   | After     | Executes after a preceding step is complete. |

**Examples:**
- **If / If Not (`@if`, `@if!`):** The combination ` @if!(<all number is 0>)` and `@if(<carry-over number is 0>)` forms the termination condition for the main loop, ensuring it continues as long as there are digits to process or a carry-over exists.
- **After (`@after`):** ` <= @after({digit sum})` ensures that the remainder is only calculated *after* the `digit sum` has been computed in a prior step.

#### 3.2.3. Grouping Operators

| Symbol    | Name   | Description                                           |
| --------- | ------ | ----------------------------------------------------- |
| `&in`     | In     | Groups items contained within a larger collection.    |
| `&across` | Across | Groups items by iterating across a collection.        |

**Examples:**
- **Across (`&across`):** `<= &across({unit place value}:{number pair}*1)` is a `grouping` inference that iterates across the two numbers in the `{number pair}` and extracts the `{unit place value}` (the rightmost digit) from each, creating a new group of digits to be summed.
- **In (`&in`):** Used to create a collection from explicitly listed value concepts. The elements to be grouped are provided as `<-` concepts within the inference.
  ```Normcode
  <- [my collection] | grouping
      <= &in({item})
      <- {item A}
      <- {item B}
  ```

#### 3.2.4. Quantifying (Listing) Operators

| Symbol   | Name  | Description                                        |
| -------- | ----- | -------------------------------------------------- |
| `*every` | Every | Iterates over every item in a collection (a loop). |

**Example:**
- **Every (`*every`):** `<= *every({number pair})` defines the main loop of the addition algorithm. This functional concept invokes the `quantifying` agent's sequence, which will continue to execute its child inferences as long as the termination condition (defined with `@if` operators) is not met.

#### 3.2.5. Concept Markers
These markers can be appended to concepts to modify their meaning.

| Symbol                | Name                 | Description                                                                 |
| --------------------- | -------------------- | --------------------------------------------------------------------------- |
| `?`                   | Conception Query     | Appended to a concept to query its value or definition. E.g., `{sum}?`. |
| `<:_number_>`         | Value Position       | To link a positional placeholder for values (e.g., `<:{1}>`, `<:{2}>`).     |
| `<$(_concept_)%_>`    | Instance Marker      | Marks a concept as an instance of an "umbrella" concept. E.g. `<$({number})%_>` |
| `<$={_number_}>`      | Identity Marker      | Identifies the same concept across different occurrences. E.g. `<$={1}>`     |
| `%:[_concept_]`       | Axis Specifier       | Specifies the `by_axis` for an operation. E.g. `%:[{number pair}]`        |
| `@(_number_)`         | Quantifier Index     | Specifies the index for a quantifier (`*every`) operation. E.g. `@(1)`       |
| `*_number_`           | Quantifier Version   | Links a concept to a specific quantifier iteration. E.g. `{number pair}*1`  |

## 4. Reference of Concepts

While concepts define the structure of a NormCode plan, the actual information is stored in a **Reference**. Understanding the Reference is key to grasping how data is stored, manipulated, and flows through the plan.

A Reference is the container where the information for a concept is kept. Specifically, it is the **semantical concepts** (like `{object}`, `[]`, or `<>`) that have an associated Reference, as they represent the data-holding entities within the plan.

**Key Characteristics of a Reference:**

-   **Multi-dimensional Container**: A Reference is multi-dimensional because a concept can exist in multiple contexts. Each context can introduce a new dimension, allowing the Reference to hold different instances or elements of the concept's information in a structured way.
-   **Named Axes**: Each dimension, often corresponding to a specific context, is represented as a named **axis**. This allows for clear organization and retrieval of information. For example, a concept like `{grade}` could have a Reference with axes named `student` and `assignment`, representing the different contexts in which a grade exists.
-   **Shape**: The size of each dimension defines the `shape` of the information within the Reference.
-   **Data Manipulation**: The core logic of the **Agent's Sequences** (e.g., collecting items with `grouping` or accumulating results with `quantifying`) involves manipulating the information held within these References.

**Conceptual Example: The `{grade}` Concept**

Imagine you have a concept defined as `{grade}`. This concept represents the idea of a grade in your plan.

-   **The `Concept`**: This is the semantic declaration `{grade}`. It's abstract and doesn't hold any specific grade values on its own.

-   **The Contexts**: A grade is meaningless without context. It needs to be associated with a `student` and an `assignment`. These two contexts are what give a specific grade its identity.

-   **The `Reference`**: The `Reference` for `{grade}` is where the actual grade values are stored. Because the concept has two contexts (`student` and `assignment`), its Reference will be a two-dimensional container with two named axes:
    -   `axis`: `student`
    -   `axis`: `assignment`

    This creates a structure like a table where you can look up a specific grade by providing a value for each axis:

    |               | assignment 1 | assignment 2 |
    | :------------ | :----------: | :----------: |
    | **student A** |      95      |      88      |
    | **student B** |      72      |      91      |

    In this structure, the value `88` is the information stored in the `{grade}` concept's Reference at the intersection of `student = student A` and `assignment = assignment 2`. When an inference needs the grade for Student A on Assignment 2, it queries the `Reference` using these axes.

In short, a `Concept` gives information its meaning within the plan, while a `Reference` provides the structure to hold and organize that information.

## 5. Agent's Sequences: Operational Realization of Inferences

Agent's sequences are the **operational realization** of inferences - they are the pre-defined pipelines that execute the actual logic when a functional concept invokes them. Each agent's sequence represents a specific pattern of processing steps that transform inputs into outputs.

When a functional concept (like `*every`, `::`, or `&across`) is encountered in a NormCode script, it triggers the corresponding agent's sequence, which then executes a series of standardized processing steps to realize the inference's logic.

### 5.1. Agent's Sequence Architecture

Each agent's sequence follows a standardized pattern of processing steps, represented by acronyms that describe the operation:

- **IWI**: Input Working Interpretation - Processes the incoming working interpretation
- **IR**: Input References - Handles input data references
- **GR**: Grouping References - Groups or collects related data
- **QR**: Quantifying References - Manages quantification and iteration
- **AR**: Assigning References - Handles variable assignments and updates
- **MFP**: Model Function Perception - Perceives model functions
- **MVP**: Memory Value Perception - Perceives memory values
- **TVA**: Tool Value Actuation - Actuates tool values
- **TIP**: Tool Inference Perception - Perceives tool inferences
- **MIA**: Memory Inference Actuation - Actuates memory inferences
- **T**: Timing - Controls timing and flow
- **OR**: Output Reference - Produces output references
- **OWI**: Output Working Interpretation - Generates final working interpretation

### 5.2. Available Agent's Sequences

#### 5.2.1. Simple Agent's Sequence
**Pattern**: `(IWI-IR-OR-OWI)`
- **Purpose**: Basic data retrieval and output operations
- **Use Case**: Usually as dummy for testing
- **Steps**: Input Working Interpretation → Input References → Output Reference → Output Working Interpretation

#### 5.2.2. Grouping Agent's Sequence  
**Pattern**: `(IWI-IR-GR-OR-OWI)`
- **Purpose**: Handles data collection and grouping operations
- **Use Case**: Collecting related data items using `&across` and `&in` operators
- **Steps**: Input Working Interpretation → Input References → Grouping References → Output Reference → Output Working Interpretation

#### 5.2.3. Quantifying Agent's Sequence
**Pattern**: `(IWI-IR-GR-QR-OR-OWI)`
- **Purpose**: Manages loops and iterative operations over data collections
- **Use Case**: Iterating over collections using `*every` operator
- **Steps**: Input Working Interpretation → Input References → Grouping References → Quantifying References → Output Reference → Output Working Interpretation

#### 5.2.4. Assigning Agent's Sequence
**Pattern**: `(IWI-IR-AR-OR-OWI)`
- **Purpose**: Manages variable assignments and state updates
- **Use Case**: Variable assignment using `$=`, `$+`, `$.`, `$%` operators
- **Steps**: Input Working Interpretation → Input References → Assigning References → Output Reference → Output Working Interpretation

#### 5.2.5. Imperative Agent's Sequence
**Pattern**: `(IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI)`
- **Purpose**: Executes complex commands, often with external tools or language models
- **Use Case**: Complex operations using `::` imperative operators
- **Steps**: Input Working Interpretation → Input References → Model Function Perception → Memory Value Perception → Tool Value Actuation → Tool Inference Perception → Memory Inference Actuation → Output Reference → Output Working Interpretation

#### 5.2.6. Judgement Agent's Sequence
**Pattern**: `(IWI-IR-MFP-MVP-TVA-TIP-MIA-OR-OWI)`
- **Purpose**: Evaluates conditions and returns boolean-like assessments
- **Use Case**: Conditional evaluations using `<>` judgement operators
- **Steps**: Input Working Interpretation → Input References → Model Function Perception → Memory Value Perception → Tool Value Actuation → Tool Inference Perception → Memory Inference Actuation → Output Reference → Output Working Interpretation

#### 5.2.7. Timing Agent's Sequence
**Pattern**: `(IWI-T-OWI)`
- **Purpose**: Controls conditional execution and flow control
- **Use Case**: Conditional logic using `@if`, `@if!`, `@after` operators
- **Steps**: Input Working Interpretation → Timing → Output Working Interpretation

### 5.3. Agent's Sequence Examples

This section provides concrete examples for each agent's sequence, drawn from the multi-digit addition example (`ex_add_complete.py`). Each example includes a NormCode snippet, an explanation, and the typical `working_interpretation` that guides the sequence's execution.

#### 5.3.1. Simple Agent's Sequence

As this sequence is typically used for testing or basic data passthrough, a complete example is not present in the addition algorithm. Below is a hypothetical example.

**NormCode Example:**
```normcode
{output concept} | simple
    <= '({input concept})
    <- {input concept}
```

**Explanation:**
This inference retrieves the data from `{input concept}` and directly outputs it into `{output concept}`. The functional concept `'()` is a placeholder for a simple retrieval operation.

**Typical `working_interpretation`:**
```json
{
    "source": "{input concept}",
    "destination": "{output concept}"
}
```

**Explanation of `working_interpretation`:**
The `working_interpretation` for a simple sequence would contain the minimal information needed for a direct data transfer: the `source` concept to read from and the `destination` concept to write to.

---

#### 5.3.2. Grouping Agent's Sequence

**NormCode Example:**
```normcode
<- [all {unit place value} of numbers] | 1.1.2.4. grouping
    <= &across({unit place value}:{number pair}*1)
```

**Explanation:**
This `grouping` inference is used to collect the rightmost digit (`{unit place value}`) from each number in the current `{number pair}*1`. The `&across` operator iterates through the `{number pair}*1` collection and extracts the specified digit from each, creating a new collection named `[all {unit place value} of numbers]`.

**Typical `working_interpretation`:**
```json
{
    "syntax": {
        "marker": "across",
        "by_axis_concepts": "{number pair}*1"
    }
}
```

**Explanation of `working_interpretation`:**
- `marker`: "across" confirms that the grouping operation is an iteration across a collection.
- `by_axis_concepts`: Specifies the concept (`{number pair}*1`) that the `&across` operator will iterate over.

---

#### 5.3.3. Quantifying Agent's Sequence

**NormCode Example:**
```normcode
{new number pair} | 1. quantifying
    <= *every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]
```

**Explanation:**
This is the main loop of the addition algorithm. The `*every` operator initiates a `quantifying` sequence that iterates over `{number pair}`. The loop continues until a termination condition is met, and its ultimate purpose is to produce the `{new number pair}` (the final sum).

**Typical `working_interpretation`:**
```json
{
    "syntax": {
        "marker": "every",
        "quantifier_index": 1,
        "LoopBaseConcept": "{number pair}",
        "CurrentLoopBaseConcept": "{number pair}*1",
        "group_base": "number pair",
        "InLoopConcept": {
            "{carry-over number}*1": 1,
        },
        "ConceptToInfer": ["{new number pair}"]
    }
}
```

**Explanation of `working_interpretation`:**
- `marker`: "every" identifies the looping nature of the quantifier.
- `quantifier_index`: `1` provides a unique ID for this specific loop.
- `LoopBaseConcept`: `"{number pair}"` is the collection being iterated over.
- `CurrentLoopBaseConcept`: `"{number pair}*1"` refers to the specific instance of the collection in the current iteration.
- `InLoopConcept`: Tracks concepts that are specific to the loop's state, like `{carry-over number}*1`.
- `ConceptToInfer`: `"{new number pair}"` specifies the final output of the entire sequence.

---

#### 5.3.4. Assigning Agent's Sequence

**NormCode Example:**
```normcode
<- *every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>] | 1.1. assigning
    <= $.({remainder})
    <- {remainder}
```

**Explanation:**
This `assigning` inference takes the calculated `{remainder}` from a single digit addition and assigns it as the result for the current iteration of the main loop (identified by the complex `*every(...)` concept). The `$.` operator specifies that this is a definition or assignment.

**Typical `working_interpretation`:**
```json
{
    "syntax": {
        "marker": ".",
        "assign_source": "{remainder}",
        "assign_destination": "*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]"
    }
}
```

**Explanation of `working_interpretation`:**
- `marker`: `"."` corresponds to the `$.` (specification) operator.
- `assign_source`: `"{remainder}"` is the concept whose value is being assigned.
- `assign_destination`: The target of the assignment, which in this case is the current loop iteration's output.

---

#### 5.3.5. Imperative Agent's Sequence

**NormCode Example:**
```normcode
<- {digit sum} | 1.1.2. imperative
    <= ::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)
    <- [all {unit place value} of numbers]<:{1}>
    <- {carry-over number}*1<:{2}>
    <- {sum}?<:{3}>
```

**Explanation:**
This `imperative` inference issues a command to an external tool or model. The `::` concept contains a natural language instruction to sum the collected digits (`[all {unit place value} of numbers]`) and the current `{carry-over number}*1`. The result is expected to be placed in `{sum}`.

**Typical `working_interpretation`:**
```json
{
    "is_relation_output": false,
    "with_thinking": true,
    "value_order": {
        "[all {unit place value} of numbers]": 1,
        "{carry-over number}*1": 2,
        "{sum}?": 3
    }
}
```

**Explanation of `working_interpretation`:**
- `with_thinking`: `true` indicates that this operation may require complex reasoning (e.g., by an LLM).
- `value_order`: Maps the value concepts to the positional placeholders (`{1}`, `{2}`, `{3}`) in the imperative command string, ensuring the correct data is used for each parameter.

---

#### 5.3.6. Judgement Agent's Sequence

**NormCode Example:**
```normcode
<- <all number is 0> | 1.1.3.3. judgement
    <= :%(True):<{1}<$({number})%_> is 0>
    <- {number pair to append}<:{1}>
```

**Explanation:**
This `judgement` inference evaluates a condition. It checks if the numbers in `{number pair to append}` are all zero. The `<...>` syntax defines the condition to be evaluated. The result will be a boolean-like value (`True` or `False`) stored in the statement concept `<all number is 0>`, which can then be used by a `timing` sequence for flow control.

**Typical `working_interpretation`:**
```json
{
    "is_relation_output": false,
    "with_thinking": true,
    "value_order": {
        "{number pair to append}": 1
    },
    "condition": "True"
}
```

**Explanation of `working_interpretation`:**
- `value_order`: Links the input concept `{number pair to append}` to the `{1}` placeholder in the judgement function.
- `condition`: `True` specifies the expected outcome for the judgement to be considered successful (i.e., the function evaluates whether the condition `<... is 0>` is true).

---

#### 5.3.7. Timing Agent's Sequence

**NormCode Example:**
```normcode
<- $+({number pair to append}:{number pair}) | 1.1.3.1. timing
    <= @if!(<all number is 0>)
    <- <all number is 0>
```

**Explanation:**
This `timing` inference controls the flow of execution. It wraps an `assigning` operation (`$+`) and makes it conditional. The `@if!` operator ensures that the assignment only proceeds if the condition `<all number is 0>` is false. This is part of the main loop's termination logic.

**Typical `working_interpretation`:**
```json
{
    "syntax": {
        "marker": "if!",
        "condition": "<all number is 0>"
    }
}
```

**Explanation of `working_interpretation`:**
- `marker`: "if!" corresponds to the `@if!` operator, indicating "if not".
- `condition`: `"<all number is 0>"` is the statement concept (evaluated by a `judgement` sequence) that this timing step depends on.

### 5.4. How Agent's Sequences Work

When a functional concept is encountered in a NormCode script:

1. **Sequence Selection**: The functional concept determines which agent's sequence to invoke
2. **Step Execution**: The selected sequence executes its predefined pattern of steps
3. **State Management**: Each step processes and transforms the inference state
4. **Output Generation**: The final steps produce the desired output

For example, when `*every({number pair})` is encountered:
- It triggers the **Quantifying Agent's Sequence**
- The sequence executes: IWI → IR → GR → QR → OR → OWI
- Each step processes the iteration logic and manages the loop state
- The result is a properly executed iteration over the number pair

This architecture ensures that every inference in NormCode has a well-defined operational realization through these standardized agent's sequences.

## 6. Orchestration: Executing the Plan

While Agent's Sequences define how a *single* inference is executed, the **Orchestrator** is the component responsible for managing the execution of the *entire plan* of inferences. It ensures that inferences are run in the correct logical order based on their dependencies. The system operates on a simple but powerful principle: **an inference can only be executed when all of its inputs are ready.**

The core components of the orchestration mechanism are:

*   **`Orchestrator`**: The central conductor. It runs a loop that repeatedly checks which inferences are ready to execute and triggers them.
*   **`ConceptRepo` & `InferenceRepo`**: These repositories hold the definitions for all the concepts (the "data") and inferences (the "steps") in the plan.
*   **`Waitlist`**: A prioritized queue of all inferences, sorted by their `flow_index` (e.g., `1.1`, `1.1.2`). This defines the structural hierarchy of the plan.
*   **`Blackboard`**: The central state-tracking system. It holds the real-time status (`pending`, `in_progress`, `completed`) of every single concept and inference in the plan. This is the "single source of truth" the `Orchestrator` uses to make decisions.
*   **`ProcessTracker`**: A logger that records the entire execution flow for debugging and analysis.

### A Complete Example: Tracing the Addition Algorithm

Let's trace a simplified path through the multi-digit addition example to see how these components work together. The goal is to calculate `{digit sum}` (flow index `1.1.2`), which requires the `[all {unit place value} of numbers]` (from `1.1.2.4`).

#### 6.1. Initialization

1.  When the `Orchestrator` is initialized, it receives the `concept_repo` and `inference_repo` containing all the definitions for the plan.
2.  It creates a `Waitlist` of all inferences, sorted hierarchically by flow index.
3.  It populates the `Blackboard` with every concept and inference. Initially, all concepts that are not "ground concepts" (i.e., provided as initial inputs like `{number pair}`) and all inferences are marked as **`pending`**.

Here's the state of our key items on the `Blackboard` at the start:

| ID                                   | Type       | Status    |
| ------------------------------------ | ---------- | --------- |
| `{number pair}`                      | Concept    | `complete`  |
| `{carry-over number}*1`              | Concept    | `complete`  |
| `[all {unit place value} of numbers]`| Concept    | `pending`   |
| `{digit sum}`                        | Concept    | `pending`   |
| `1.1.2.4` (grouping)                 | Inference  | `pending`   |
| `1.1.2` (imperative)                 | Inference  | `pending`   |

#### 6.2. The Execution Loop

The `Orchestrator` now enters its main loop, which runs in cycles. In each cycle, it iterates through the `Waitlist` and checks for any `pending` items that are now ready to run based on the status of their dependencies on the `Blackboard`.

**Cycle 1: Executing the Inner Steps**

*   The orchestrator checks `1.1.2` (`::(sum ...)`). This check fails because one of its value concepts, `[all {unit place value} of numbers]`, is still `pending`.
*   It continues down the hierarchy and finds that the deepest inferences, like the one that gets a single digit, are ready because their inputs are available.
*   The `Orchestrator` executes these deep inferences. The corresponding `Agent's Sequence` runs and produces an output.
*   After execution, the `Blackboard` is updated. The concepts produced by these steps are now marked as **`complete`**.

**Cycle 2: Executing the Grouping Inference (`1.1.2.4`)**

*   The orchestrator begins a new cycle. It checks `1.1.2.4` (`&across(...)`). This time, the check succeeds because all of its supporting items (the inner loops that extract individual digits) completed in the previous cycle, marking the necessary input concepts as `complete`.
*   The `Orchestrator` executes the `1.1.2.4` inference. The `grouping` agent sequence runs, collects the digits, and populates the `[all {unit place value} of numbers]` concept.
*   The `Blackboard` is updated. The concept `[all {unit place value} of numbers]` now has a reference to the collected digits and its status is changed to **`complete`**.

**Blackboard State after Cycle 2:**

| ID                                   | Type       | Status    |
| ------------------------------------ | ---------- | --------- |
| `[all {unit place value} of numbers]`| Concept    | `complete`  |
| `{digit sum}`                        | Concept    | `pending`   |
| `1.1.2.4` (grouping)                 | Inference  | `completed` |
| `1.1.2` (imperative)                 | Inference  | `pending`   |

**Cycle 3: Executing the Imperative Inference (`1.1.2`)**

*   The orchestrator begins a new cycle and checks `1.1.2` (`::(sum ...)`). Now, the check finally **succeeds** because all its value concepts are `complete` on the `Blackboard`.
*   The `Orchestrator` executes the inference. The `imperative` sequence runs, performs the sum, and gets a result.
*   The `Blackboard` is updated. The concept `{digit sum}` now has a reference to the calculated value and its status is changed to **`complete`**.

This bottom-up, dependency-driven process continues cycle after cycle. Each time a concept is marked `complete`, it may unlock one or more higher-level inferences that depend on it, until eventually the final concept of the entire plan is completed. This ensures that every step is executed in the correct logical order, purely by observing the state of the shared `Blackboard`.

## 7. Summary

The **NormCode Guide** describes a semi-formal language designed to construct a **plan of inferences**, breaking down complex reasoning tasks into a series of small, interconnected logical operations.

*   **Core Components**: The fundamental unit is the **inference**, which is defined by a **functional concept (`<=`)** specifying the operation to be performed, and **value concepts (`<-`)** that provide the data for that operation.

*   **Concept Types**: Concepts are the building blocks and are divided into two main categories:
    *   **Semantical Concepts**: Represent the entities and logic of the domain, such as `{Objects}`, `<Statements>`, and functional commands like `::(Imperatives)` or `<Judgements>`.
    *   **Syntactical Concepts**: These are operators that control the flow and manipulate data. They include operators for **Assigning** (`$=`, `$.`), **Timing** (`@if`, `@after`), **Grouping** (`&across`, `&in`), and **Quantifying** (`*every`).

*   **Data Storage (Reference)**: The actual data for a concept is stored in a multi-dimensional container called a **Reference**. Each dimension is a named **axis**, allowing data to be structured and accessed by its context (e.g., retrieving a `{grade}` using `student` and `assignment` axes).

*   **Execution (Agent's Sequences)**: Each functional concept triggers a corresponding **Agent's Sequence**, which is a pre-defined pipeline of steps that executes the inference's logic. For example, `*every` triggers the `Quantifying` sequence to manage loops, and `::` triggers the `Imperative` sequence to execute commands, often with an external language model.

*   **Orchestration**: The entire plan is managed by an **Orchestrator**. It uses a **Blackboard** to track the real-time status (`pending`, `complete`) of every concept. The Orchestrator runs in cycles, executing inferences only when all of their required input concepts are marked as `complete` on the Blackboard, ensuring a bottom-up, dependency-driven execution of the plan.