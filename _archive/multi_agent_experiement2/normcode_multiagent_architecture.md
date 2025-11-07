# NormCode-Driven Multi-Agent System Architecture

## 1. Overview

This document outlines an architectural plan for a multi-agent system where a **NormCode plan** serves as the central orchestration script. The system interprets the NormCode hierarchy to manage state, delegate tasks, and execute complex logic.

The core principle is to map the different types of NormCode concepts to distinct software components:
-   **Non-Functional Semantic Concepts** (data, state, entities) are represented as Python **Dataclasses**.
-   **Functional Semantic Concepts** (actions, evaluations, logic) are handled by specialized **AI Agents**, each powered by a model runner and specific prompts, as suggested by the structure in the `_models` directory.
-   **Syntactical Concepts** (operators for flow control and data manipulation) are interpreted as logic within a central **Orchestrator Agent**.

This approach allows the system to dynamically execute a plan defined in NormCode, translating its semi-formal structure into concrete computational steps.

## 2. Core Components

The system is composed of four primary components:

1.  **The NormCode Plan**: A `.normcode` or `.md` file containing the full, hierarchical plan of inferences. This is the system's "source code." Example: `love_decomposition.md`.
2.  **Data Structures (Dataclasses)**: A set of Python dataclasses that mirror the structure of NormCode's non-functional concepts. These objects hold the state of the system as it executes the plan.
3.  **Specialized Agents**: A collection of agents, each responsible for executing a specific type of functional concept (e.g., performing an action, making a judgment). Each agent is a self-contained unit with its own model, prompts, and potentially, tools.
4.  **The Orchestrator Agent**: The central coordinator. It parses the NormCode plan, instantiates the dataclasses, manages the overall state, and dispatches tasks to the appropriate specialized agents based on the plan's logic.

## 3. Mapping NormCode to System Components

### 3.1. Non-Functional Concepts as Dataclasses

Every non-functional concept in the NormCode plan will be instantiated as a Python dataclass instance. This creates an in-memory, object-oriented representation of the plan's state.

-   **Concepts**: `{Object}`, `<Statement>`, `[Relation]`, `:S: Subject`, `:>: Input`, `:<: Output`.
-   **Implementation**: A generic `NormCodeConcept` base class or dataclass can be used, with attributes to store its state.

**Pseudo-code Example:**

```python
from dataclasses import dataclass, field
from typing import Any, List, Dict

@dataclass
class NormCodeConcept:
    name: str
    concept_type: str  # e.g., 'Object', 'Statement'
    source_text: str = ""  # from ...:
    question: str = ""     # from ?:
    description: str = ""  # from /:
    value: Any = None      # The actual data/result
    children: List['NormCodeConcept'] = field(default_factory=list)
    parent: 'NormCodeConcept' = None
    
    # The Reference from the guide, holding multi-dimensional data
    reference_data: Any = None
    reference_axis_names: List[str] = field(default_factory=list)

# Example Instantiation from love_decomposition.md
deep_feeling = NormCodeConcept(
    name="{deep feeling}",
    concept_type="Object",
    source_text="a deep feeling of care and attachment...",
    question="What is this feeling?"
)

care = NormCodeConcept(
    name="{care}",
    concept_type="Input",
    source_text="care (as given by the user)."
)

deep_feeling.children.append(care)
```

### 3.2. Functional Concepts as Specialized Agents

Functional concepts trigger actions. Each type of functional concept is mapped to a specialized agent. These agents are implemented using the components found in the `_models` directory (`_model_runner.py`, `_prompt.py`, `_language_models.py`).

-   **Concepts**: `::()` (Imperative), `::< >` (Judgement).
-   **Implementation**:

    -   **Judgement Agent**:
        -   **Trigger**: Encounters a `::< >` concept.
        -   **Task**: Evaluates the statement to be true or false.
        -   **Process**: It takes the target `<Statement>` dataclass, formats a prompt (from `prompts/judgement_prompt.txt`), and uses the `ModelRunner` to query a language model. The prompt would ask for a definitive boolean evaluation based on the context provided in the `source_text` of the concept. The result is then stored in the `.value` attribute of the dataclass.

    -   **Imperative Agent**:
        -   **Trigger**: Encounters a `::()` concept.
        -   **Task**: Executes a command or action.
        -   **Process**: This is more complex. It could involve:
            1.  **Tool Use**: Parsing the imperative (e.g., `::(calculate the total)`) to call a pre-defined Python function.
            2.  **Code Generation**: Using an LLM with a specific prompt to generate and execute a small code snippet.
            3.  **State Change**: Performing an operation that modifies the `.value` of one or more concept dataclasses.

### 3.3. Syntactical Operators as Orchestrator Logic

The syntactical operators are not agents themselves but are instructions that direct the flow of execution. The **Orchestrator Agent** is responsible for interpreting this logic.

-   **Timing/Sequencing Operators (`@if`, `@if!`, `@after`)**:
    -   The Orchestrator builds a dependency graph from the NormCode plan.
    -   `@after`: A concept is not processed until its dependency is complete.
    -   `@if`/`@if!`: Before processing a concept, the Orchestrator checks the `.value` (which should be boolean) of the corresponding `<Statement>` dataclass referenced in the condition.

-   **Grouping Operators (`&in`, `&across`)**:
    -   When the Orchestrator encounters these, it knows the children concepts form a collection.
    -   `&across`: It iterates through the `source_text` and partitions it, creating a new child dataclass for each part (e.g., creating three "step" concepts from the "user registration" example).
    -   `&in`: It groups the explicitly listed child concepts into a list or collection.

-   **Assigning Operators (`$=`, `$.`, `$%`, `$+`)**:
    -   These operators instruct the Orchestrator on how to structure and link the dataclasses.
    -   `$.` (Specification): Creates a definitional link, often parent-child, between two concept dataclasses (e.g., `{Love}` is specified as `{deep feeling}`).
    -   `$=` (Identity): The Orchestrator assigns or updates the `.value` of one concept dataclass with the value of another.

-   **Quantifying Operators (`*every`)**:
    -   This instructs the Orchestrator to begin a loop. The Orchestrator will repeatedly process the child inferences of the `*every` block for each item in the target collection.

## 4. Example Execution Flow: User Registration

Let's trace a simplified execution of the "User Registration" example from the `comprehensive_normcode_translation_guide.md`.

1.  **Initialization**: The Orchestrator parses the entire NormCode plan into a tree of `NormCodeConcept` dataclasses. The root is `:<:(::(register a new user))`.

2.  **Step 1 -> {steps}**: The Orchestrator processes the root. It sees `<= @by(:_:)` and its child `:_:{steps}({user name})`. It then moves to the definition of `{steps}`.

3.  **Grouping**: It sees `<= &across` under `{steps}`. The Orchestrator's logic for `&across` is triggered. It parses the `source_text` and creates three new child dataclasses under `{steps}`: `{step 1}`, `{step 2}`, and `{step 3}`.

4.  **Nominalization & Judgement**:
    -   The Orchestrator moves to `{step 1}`. It sees `<= $::.<username exists>`. This is a nominalization.
    -   It then finds the associated functional concept `::<username exists>`.
    -   The Orchestrator dispatches this concept dataclass to the **Judgement Agent**.
    -   The Judgement Agent takes the `source_text` ("check if the provided username already exists"), the context (`{user name}`), formats its prompt, and calls the LLM.
    -   The LLM returns `True`. The Judgement Agent updates the `::<username exists>` dataclass's `.value` to `True`.

5.  **Conditional Action**:
    -   The Orchestrator moves to `{step 2}` and finds `::(report error)`.
    -   It first checks the sequencing logic: `<= @if(::<username exists>)`.
    -   The Orchestrator's `@if` logic is triggered. It looks up the `::<username exists>` dataclass, finds its `.value` is `True`. The condition passes.
    -   The Orchestrator now dispatches the `::(report error)` concept to the **Imperative Agent**.
    -   The Imperative Agent executes the action (e.g., logs an error, sets an error state).

6.  **Continuation**: The Orchestrator would then move to `{step 3}`, check its `@if!` condition (which would fail in this case), and continue until the entire plan is traversed.

This architecture creates a robust system where the logic is clearly defined by the NormCode plan, state is managed in a structured way with dataclasses, and actions are cleanly delegated to specialized agents.
