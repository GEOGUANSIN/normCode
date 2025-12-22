# Guide: Deriving a Multi-Agent System Architecture from a NormCode Blueprint

## 1. Core Philosophy

This document outlines a methodology for using a NormCode plan as a **design-time architectural blueprint** to engineer a bespoke, high-performance multi-agent system.

The core principle is that NormCode is not a script to be interpreted at runtime. Instead, it is a formal specification that is analyzed once to derive the complete design of a purpose-built system. The resulting system is a "hard-coded" implementation of the NormCode's logic, ensuring efficiency, reliability, and clarity.

The derivation process is systematic, translating every element of the NormCode into a concrete architectural decision.

## 2. The Three-Phase Derivation Workflow

The analysis of the NormCode blueprint is conducted in three distinct phases, each answering critical questions about the final system's design.

---

### Phase 1: Deriving the "Who" and the "What" (Worker Agents & Tools)

This initial phase defines the specialized "worker" agents that will perform the actual tasks.

*   **Objective:** To determine the number of worker agents, their distinct roles, and their specific capabilities (tools).
*   **Methodology:**
    1.  **Scan for Functional Roles:** Analyze the entire NormCode for functional concepts (`::()` for imperatives, `<>` for judgements) and explicit agent annotations (`| imperative`, `| judgement`).
    2.  **Group Similar Functions:** Group these concepts by their nature. All calculation-based imperatives suggest a `MathAgent`; all conditional checks suggest a `LogicAgent`; all data structuring operations (`&across`, `&in`) suggest a `DataAgent`.
    3.  **Define Agent Tools:** For each agent role, examine the specific text within its corresponding functional concepts. This text defines the requirements for its tools.

*   **Architectural Output:**
    *   **Agent Roles:** A definitive list of required worker agents (e.g., `JudgementAgent`, `ImperativeAgent`).
    *   **Tool Specification:** For each agent, a precise list of required tools. The NormCode's `<-` value concepts specify the exact function signatures (arguments and return types) for each tool.

**Example:**
*   A NormCode line `::(sum {A} and {B})` translates to a requirement for an `ImperativeAgent` with a tool that wraps a `sum(A, B)` function.

---

### Phase 2: Deriving the "How" (Communication & State)

This phase defines the data flow and the central entity that manages it.

*   **Objective:** To define the system's communication model and the necessary state variables.
*   **Methodology:**
    1.  **Trace Object Concepts:** Track the lifecycle of all object concepts (`{...}`) throughout the NormCode.
    2.  **Identify Data Flow:** Note where a concept is created/modified (as an output) and where it is subsequently used (as an input for another step).
    3.  **Establish the Controller:** This flow invariably reveals a **hub-and-spoke** communication pattern, proving the architectural need for a central **Controller Agent** to manage state and orchestrate the workers.

*   **Architectural Output:**
    *   **State Variables:** A complete list of all concepts that are passed between steps. These become the instance variables that the Controller Agent must manage (e.g., `self.state['carry_over']`).
    *   **Communication Model:** A clear definition of the Controller as the central orchestrator that holds state and passes data to and from the worker agents.

---

### Phase 3: Deriving the "When" and "Where" (The Controller's Logic)

This final phase translates the NormCode's structure into the procedural "brain" of the Controller Agent.

*   **Objective:** To build the Controller's internal logic, execution order, and control flow.
*   **Methodology:**
    1.  **Analyze the Flow Index:** The primary tool for this phase is the numerical flow index (e.g., `1.1.2.4`). This index is not just a comment; it is a schematic for the Controller's code.
    2.  **Map Hierarchy to Code Structure:** The nesting of the index dictates the nesting of the Controller's code. A top-level index (`1.`) is a top-level method, while a deeper index (`1.1.2.`) represents a nested block or a call to a private helper method. This maps the NormCode's structure directly to the Controller's call stack.
    3.  **Translate Structural Operators:** Convert NormCode's control flow operators directly into programming constructs within the Controller's methods:
        *   `@if` / `@if!` become `if/else` statements.
        *   `*every` becomes a `while` or `for` loop.
        *   `@after` becomes a state dependency check before executing a step.
    4.  **Pinpoint Agent Dispatch:** Each flow index location that corresponds to a functional inference is the precise point in the Controller's code where it dispatches a task to the appropriate worker agent.

*   **Architectural Output:**
    *   **A Deterministic Controller:** A complete, procedural implementation of the Controller Agent. Its logic is not self-derived; it is a direct and efficient translation of the blueprint's flow index and structural operators. The result is a highly predictable and reliable state machine.
