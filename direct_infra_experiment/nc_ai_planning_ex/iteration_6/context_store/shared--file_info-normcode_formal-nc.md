# File Format: NormCode Formal (`.nc`)

The `.nc` file is the **formal, machine-readable script** that is ready for the Orchestrator to execute. It is generated during Phase 3 (Formalization) by transforming the `.ncd` file.

**Key Characteristics:**
-   **Fully Formal:** The syntax is strict, consistent, and designed to be parsed by the execution engine.
-   **No Annotations:** All descriptive annotations (`?:`, `/:`, `...:`) are removed.
-   **Execution-Critical Information:** It is enriched with information required by the Orchestrator:
    -   **Flow Indices:** Each line is assigned a unique, dot-delimited index (e.g., `1.3.2.1`) that makes every inference in the plan uniquely addressable.
    -   **Agent Sequence Types:** Each inference is tagged with the name of the agent sequence (e.g., `grouping`, `imperative`, `timing`) that should execute it.
    -   **Formalized Operators:** Operators are made more explicit for the machine, for example, by specifying the positional markers for children in a grouping (`&across[{1},{2}]`).

**Purpose:** To serve as the direct input for the later stages of the pipeline, including context distribution (Phase 4) and materialization into an executable Python script (Phase 5). It is the definitive, parsable representation of the plan.

**Example Snippet:**
```normcode
1.3.2.object| {Phase 1: Confirmation of Instruction}<:{1}>
1.3.2.1.grouping| &across[{1}, {2}]
1.3.2.2.object| {step 1.1: Automated Instruction Distillation}<:{1}>
1.3.2.3.object| {step 1.3: Manual Review of Distillation}<:{2}>
```
