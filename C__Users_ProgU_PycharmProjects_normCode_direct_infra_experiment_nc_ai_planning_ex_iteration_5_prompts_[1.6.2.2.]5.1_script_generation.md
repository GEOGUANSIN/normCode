## Step 5.1: Automated Script Generation

**Objective**: Your task is to transform a formalized NormCode plan (`.nc`) and its associated context into a set of executable Python artifacts: `concept_repo.json`, `inference_repo.json`, and a main runner script (`.py`).

**Core Inputs**:
- The formalized NormCode plan (`.nc` file).
- The final Context Manifest (`.json` file).
- The `context_store` directory.

### Procedure

The generation process follows a structured procedure to translate the abstract NormCode plan into concrete, executable repository objects. This should be approached as a design-first process before implementation.

#### 0. Design the Repositories (Pre-computation step)
Before generating any JSON, first sketch out the repository design.
-   **Concept List**: Enumerate every concept from the `.nc` file. For each, decide if it is ground, final, or intermediate. Plan its `reference_data` and `reference_axis_names`.
-   **Inference List**: For each inference in the `.nc` file, design the corresponding `InferenceEntry`. Choose the `inference_sequence`, map all the concept connections, and, most importantly, design the full `working_interpretation` JSON object.

#### 1. Identify All Concepts and Operators from the NormCode Plan

First, perform a full parse of the `.nc` file to identify every unique concept. Each concept must be classified by its type and behavior.

-   **Semantical object concepts (`{...}`)**: e.g., `{normcode draft}`, `{functional concept}`.
-   **Semantical statement concepts (`<...>`**) e.g., `<current normcode draft is complete>`.
-   **Semantical relation concepts (`[...]`)**: e.g., `[all {normcode draft}]`.
-   **Syntactical operator concepts**: The operators that define the plan's logic, such as `*every(...)`, `&across(...)`, `$.(...)`, `$+(...)`, `@if`, `@if!`, `@after`.
-   **Functional concepts**: The imperative `::(...)` and judgement `:%(...)` blocks that represent actions or decisions.

#### 2. Generate `ConceptEntry` Objects

For each unique concept identified, create a corresponding `ConceptEntry` object. The attributes of this object are determined by the concept's role in the plan.

**2.1. Classify Concept Behavior**

-   **Final outputs**: These are the ultimate goals of the plan. Mark them with `is_final_concept=True`.
-   **Ground concepts**: These are the initial inputs, prompts, or fixed operators. Mark them with `is_ground_concept=True` and populate their `reference_data` and `reference_axis_names`. For nested data, use a nested list in `reference_data`.
-   **Intermediate concepts**: These are temporary variables or loop items that exist only during the run.
-   **Functional / operator concepts**: These represent the plan's syntax (e.g., `*every`, `$.`, `@if`, `::({})`). They are typically ground concepts (`is_ground_concept=True`).

**2.2. Map NormCode Types to `ConceptEntry` Attributes**

-   **Objects (`{...}`)**: `type` = `"{}"`. `axis_name` should describe the semantic axis (e.g., `"normcode draft"`).
-   **Statements (`<...>`**) `type` = `"<>"`. Typically have no `reference_data` unless they are ground-truth judgements.
-   **Relations (`[...]`)**: `type` = `"[]"`. `axis_name` should describe the collection (e.g., `"all unit place value of numbers"`).
-   **Operators and Functions**: The `type` attribute should encode the operator class (e.g., `"*every"`, `"$.`, `"::({})"`). The `concept_name` should be the full textual form of the operator from the `.nc` file.

#### 3. Generate `InferenceEntry` Objects

For each inference block in the `.nc` plan, create a corresponding `InferenceEntry` object. This object makes the plan's execution logic explicit for the orchestrator.

**3.1. Map Core Fields**

-   **`flow_info`**: Set `flow_info={'flow_index': '...'}` from the NormCode sequence label (e.g., `1.`, `1.1.2`).
-   **`inference_sequence`**: Map the role annotation from the `.nc` file (e.g., `quantifying`, `assigning`, `imperative`). This determines which agent sequence will execute the step.
-   **`concept_to_infer`**: The concept being defined on the left side of the inference.
-   **`function_concept`**: The operator on the right side of the `<=` in the NormCode.
-   **`value_concepts` and `context_concepts`**: The concepts listed under the `"<-"` lines in the NormCode block.

**3.2. Synthesize `working_interpretation`**

This is the most critical part of the translation. The `working_interpretation` JSON object encodes the implicit syntax of the NormCode into an explicit structure the orchestrator can understand. Below are templates for different inference sequences.

-   **For `quantifying` (`*every`) inferences**:
    -   **Purpose**: Describe a loop's structure.
    -   **Shape**:
        ```json
        {
            "syntax": {
                "marker": "every",
                "quantifier_index": 1,
                "LoopBaseConcept": "{number pair}",
                "CurrentLoopBaseConcept": "{number pair}*1",
                "group_base": "number pair",
                "InLoopConcept": { "{carry-over number}*1": 1 },
                "ConceptToInfer": ["{new number pair}"]
            }
        }
        ```

-   **For `grouping` (`&across`) inferences**:
    -   **Purpose**: Describe a grouping operation.
    -   **Shape**:
        ```json
        {
            "syntax": {
                "marker": "across",
                "by_axis_concepts": "{number pair}*1"
            }
        }
        ```

-   **For `assigning` (`$.` or `$`) inferences**:
    -   **Purpose**: Describe data movement or updates.
    -   **Shape**:
        ```json
        {
            "syntax": {
                "marker": ".", // or "+" for append
                "assign_source": "{remainder}",
                "assign_destination": "*every(...)"
            }
        }
        ```

-   **For `timing` (`@if`, `@if!`, `@after`) inferences**:
    -   **Purpose**: Describe conditional execution.
    -   **Shape**:
        ```json
        {
            "syntax": {
                "marker": "if", // or "if!" or "after"
                "condition": "<current normcode draft is complete>"
            }
        }
        ```

-   **For `imperative` or `judgement` inferences**:
    -   **Purpose**: Describe a call to a tool, LLM, or script.
    -   **Complex Shape (with value selectors)**: When an imperative needs to extract specific parts of a relation concept, use `value_selectors`:
        ```json
        {
            "is_relation_output": true,
            "with_thinking": true,
            "prompt_location": "name_of_prompt_file",
            "value_order": { ... },
            "value_selectors": {
              "relation_part_1": {
                  "source_concept": "[{concept to decomposed} and {remaining normtext}]",
                  "index": 0,
                  "key": "concept to decomposed"
              },
              "relation_part_2": {
                  "source_concept": "[{concept to decomposed} and {remaining normtext}]",
                  "index": 0,
                  "key": "remaining normtext"
              }
            }
        }
        ```
    -   The `value_order` map is crucial for binding the `value_concepts` to the positional placeholders (`{1}`, `{2}`) in the functional concept's text.

#### 4. Generate Repository Files

-   Serialize the complete list of `ConceptEntry` objects into `concept_repo.json`.
-   Serialize the complete list of `InferenceEntry` objects into `inference_repo.json`.

#### 5. Generate the Runner Script (`.py`)

Finally, generate a Python script that uses the repository files to execute the plan. The script should follow this template and include any necessary file system preparation (e.g., creating a `prompts/` directory if the plan requires it).

```python
from infra._orchest._repo import ConceptRepo, InferenceRepo
from infra._orchest._orchestrator import Orchestrator
from infra._agent._body import Body
import os
import json

def create_repositories_from_files():
    with open('concept_repo.json', 'r') as f:
        concept_data = json.load(f)
    concept_repo = ConceptRepo.from_json_list(concept_data)

    with open('inference_repo.json', 'r') as f:
        inference_data = json.load(f)
    inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)
    
    return concept_repo, inference_repo

if __name__ == "__main__":
    # 1. Build repositories from the generated JSON files
    concept_repo, inference_repo = create_repositories_from_files()

    # 2. Construct a Body for imperatives/judgements
    body = Body(llm_name="qwen-plus") # Or other appropriate configuration

    # 3. Construct and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        body=body,
        max_cycles=300,
    )
    final_concepts = orchestrator.run()

    # 4. Inspect and log final concepts
    for final_concept_entry in final_concepts:
        if final_concept_entry and final_concept_entry.concept.reference:
            ref_tensor = final_concept_entry.concept.reference.tensor
            print(f"Final concept '{final_concept_entry.concept_name}': {ref_tensor}")
        else:
            print(f"No reference found for final concept '{final_concept_entry.concept_name}'.")

```

---
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

---
# File Format: Concept Repository (`concept_repo.json`)

The `concept_repo.json` file is a core artifact generated in the final phase of the pipeline (Phase 5, Materialization). It serves as a serialized database of every concept that exists within the NormCode plan.

**Purpose:**
This file provides the `Orchestrator` with a complete, structured inventory of all the conceptual elements it will manage during execution. It defines what data exists, what its properties are, and how it is initialized. It is the "what" of the plan.

**Format:**
The file is a JSON array of `ConceptEntry` objects. Each object represents a single concept from the `.nc` plan. The key is to map every unique NormCode symbol that needs to hold state into a `ConceptEntry`.

### `ConceptEntry` Attributes by NormCode Type

#### 1. Semantical Concepts (`{}`, `[]`, `<>`)
These represent the core entities of the plan.
-   `concept_name`: The exact string from the NormCode (e.g., `{normcode draft}`, `<draft is complete>`).
-   `type`: Set to `"{}"` for objects, `"[]"` for relations, or `"<>" for statements.
-   `is_ground_concept`: `true` for initial inputs (like the first `{normcode draft}`), `false` for intermediate concepts that are computed during the run.
-   `is_final_concept`: `true` for concepts that represent the final output of the plan.
-   `reference_data`: For ground concepts, this holds their initial value. For multi-dimensional data, this should be a nested list, with `reference_axis_names` defining the axes.

#### 2. Functional & Operator Concepts
These concepts define the logic and control flow. They are almost always ground concepts, as their meaning is fixed.
-   `concept_name`: The full textual operator (e.g., `*every([all {normcode draft}])`, `::(sum {1} and {2})`).
-   `type`: A string that identifies the operator class, such as `"*every"`, `"&across"`, `"$.`, `"@if"`, `"::({})"`, or `"%:({})"`.
-   `is_ground_concept`: `true`.
-   `is_invariant`: Often `true`, as the operator's function does not change.
-   `reference_data`: For functional concepts like imperatives or judgements, this is typically a one-element list containing the textual form of the function, which pins its meaning for the execution body.

**Example Snippet (Conceptual):**
```json
[
  {
    "id": "...",
    "concept_name": "{number pair}",
    "type": "{}",
    "is_ground_concept": true,
    "is_final_concept": false,
    "reference_data": [["%(123)", "%(98)"]],
    "reference_axis_names": ["number pair", "number"]
  },
  {
    "id": "...",
    "concept_name": "*every({number pair})",
    "type": "*every",
    "is_ground_concept": true,
    "is_invariant": true
  },
  {
    "id": "...",
    "concept_name": "::(sum {1} and {2})",
    "type": "::({})",
    "is_ground_concept": true,
    "is_invariant": true,
    "reference_data": ["::(sum {1} and {2})"]
  }
]
```
This repository allows the `Orchestrator` to load the entire conceptual landscape of the plan before execution begins.

---
# File Format: Inference Repository (`inference_repo.json`)

The `inference_repo.json` file is a core artifact generated in the final phase of the pipeline (Phase 5, Materialization), alongside `concept_repo.json`. It is a serialized database of every inference, or logical step, defined in the NormCode plan.

**Purpose:**
This file provides the `Orchestrator` with the complete, step-by-step execution plan. While `concept_repo.json` defines *what* exists, `inference_repo.json` defines *how* and *when* concepts are computed and transformed. It is the "how" of the plan.

**Format:**
The file is a JSON array of `InferenceEntry` objects. Each object represents a single line of inference from the `.nc` file and contains the logic for that step:

-   `flow_info`: Contains the `flow_index` (e.g., `"1.2.2.1"`) from the `.nc` file, making the step traceable.
-   `inference_sequence`: The type of action to be performed (e.g., `imperative`, `grouping`, `assigning`), which determines the agent responsible for the step.
-   `concept_to_infer`: The ID of the concept that will be created or modified by this inference.
-   `function_concept`: The ID of the operator or function that drives the inference.
-   `value_concepts` / `context_concepts`: A list of IDs for the concepts that serve as inputs to this step.
-   `working_interpretation`: A critical JSON object that makes the implicit syntax of the NormCode explicit for the machine (e.g., defining loop parameters, value ordering for imperatives, or conditions for timing operators).

### The Role of `working_interpretation`

The `working_interpretation` is the bridge from the implicit syntax of NormCode to the explicit instructions needed by the Orchestrator's agents. It translates the compact NormCode notation into a detailed JSON object that clarifies the role of each concept in an inference.

-   **For `quantifying` inferences (`*every`)**: It defines the loop's structure, specifying the base collection to iterate over, the concept representing the current item, and any loop-scoped variables.
-   **For `assigning` inferences (`$.`, `$`)**: It specifies the source and destination concepts for a data transfer or state update.
-   **For `timing` inferences (`@if`, `@after`)**: It specifies the condition that must be met for the inference to proceed.
-   **For `imperative` and `judgement` inferences**: This is one of its most critical roles. It defines the interface for calling an external body (like an LLM). It maps the abstract `value_concepts` to the numbered placeholders in the imperative's text (e.g., `{1}`, `{2}`), specifies the location of a prompt file, and can even define how to select specific data from a relation concept to pass as input.

**Example Snippet (Conceptual):**
```json
[
  {
    "id": "...",
    "flow_info": { "flow_index": "1.3.2.1" },
    "inference_sequence": "imperative",
    "concept_to_infer": "id_of_{2.1_deconstruction_draft.ncd}",
    "function_concept": "id_of_::(deconstruction_imperative)",
    "value_concepts": ["id_of_{1.1_instruction_block.md}"],
    "working_interpretation": {
        "is_relation_output": false,
        "with_thinking": true,
        "prompt_location": "2.1_deconstruction.md",
        "value_order": { "id_of_{1.1_instruction_block.md}": 1 }
    }
  }
]
```
---
# File Format: Executable Script (`.py`)

The executable Python script is the final, tangible output of the entire NormCode AI Planning Pipeline, generated in Phase 5. It is a runnable script that takes the generated repositories (`concept_repo.json`, `inference_repo.json`) and executes the plan they describe.

**Purpose:**
This script is the materialization of the abstract plan. It serves as the entry point for an `Orchestrator` to run the entire logical flow, from initial inputs to final outputs. It bridges the gap between the formal plan and a concrete, executable process.

**Key Responsibilities:**
The script is a standard Python file containing a main execution block (`if __name__ == "__main__":`) that is responsible for:
1.  **File System Preparation**: Creating any necessary directories (e.g., `generated_scripts/`, `prompts/`) that ground concepts in the repositories might reference.
2.  **Loading Repositories**: Reading `concept_repo.json` and `inference_repo.json` from disk.
3.  **Instantiating Repositories**: Creating `ConceptRepo` and `InferenceRepo` objects from the loaded data.
4.  **Initializing a Body**: Setting up a `Body` object, which provides the connection to reasoning capabilities (like an LLM) needed to execute imperatives and judgements.
5.  **Initializing the Orchestrator**: Creating an `Orchestrator` instance, passing it the repositories and the body.
6.  **Running the Plan**: Calling the `orchestrator.run()` method to start the execution cycle.
7.  **Reporting Results**: Printing or logging the final concepts produced by the run.

**Example Snippet:**
```python
from infra._orchest._repo import ConceptRepo, InferenceRepo
from infra._orchest._orchestrator import Orchestrator
from infra._agent._body import Body
import json
import os
from pathlib import Path

def create_repositories_from_files():
    # ... code to load .json files ...
    concept_repo = ConceptRepo.from_json_list(...)
    inference_repo = InferenceRepo.from_json_list(...)
    return concept_repo, inference_repo

if __name__ == "__main__":
    # 1. Prepare file system
    Path("./generated_prompts").mkdir(exist_ok=True)
    
    # 2. Build repositories
    concept_repo, inference_repo = create_repositories_from_files()

    # 3. Construct a Body for imperatives/judgements
    body = Body(llm_name="qwen-plus", base_dir=Path("./generated_prompts"))

    # 4. Construct and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        body=body,
        max_cycles=300,
    )
    final_concepts = orchestrator.run()

    # ... code to print final concepts ...
```

---
