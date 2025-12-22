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
