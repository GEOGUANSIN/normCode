### Step 2.3: Plan Formalization

**Objective:** To convert the annotated and semi-formal **NormCode Draft (`.ncd`)** into a clean, parsable **NormCode (`.nc`)** file. This is a critical preparatory step for context distribution and final script generation.

**Process:**

The formalization is an automated script that performs two key actions:

1.  **Stripping Annotations:** It removes all human-centric annotations (`?:`, `/:`, `...:`), which are essential for debugging the deconstruction but are noise for the execution engine.
2.  **Generating Flow Indices:** It walks the hierarchical structure of the plan and assigns a unique, dot-delimited `flow_index` (e.g., `1.3.2.2`) and an `agent sequence type` (e.g., `object`) to each line. This makes every single inference in the plan uniquely addressable.

---
### Example Walkthrough

This example shows how the annotated deconstruction of "Phase 1" is formalized into a machine-readable plan.

**1. Input (`2.1_deconstruction_draft.ncd` snippet):**

This is the version designed for human review, with questions, descriptions, and source text.

```normcode
<- {Phase 1: Confirmation of Instruction}
    ?: How is {Phase 1} specified?
    <= &across
        /: This phase is specified as a series of steps.
    <- {step 1.1: Automated Instruction Distillation}
    <- {step 1.2: Automated Context Registration}
    <- {step 1.3: Manual Review of Confirmation}
```

**2. Formalization Script:**

The script processes the `.ncd` file, stripping the annotations and adding the `flow_index` and `agent sequence type` to each line.

**3. Output (`2.3_deconstruction.nc` snippet):**

This is the final, parsable output. Every line is now uniquely identified and ready to be mapped to a specific context.

```normcode
1.3.2.object| {Phase 1: Confirmation of Instruction}<:{1}>
1.3.2.1.grouping| &across[{1}, {2}, {3}]
1.3.2.2.object| {step 1.1: Automated Instruction Distillation}<:{1}>
1.3.2.3.object| {step 1.2: Automated Context Registration}<:{2}>
1.3.2.4.object| {step 1.3: Manual Review of Confirmation}<:{3}>
```

---
# File Format: Redirected NormCode Draft (`3.2_redirected.ncd`)

The `3.2_redirected.ncd` file represents the plan after the **Redirection** pattern has been applied to the serialized draft. This is a critical step for making the data flow of the pipeline explicit.

**Purpose:**
The primary goal of this file is to define the precise inputs for every imperative (`::()`) in the plan. While the serialized draft shows *what* is created, the redirected draft shows *what is needed* to create it. It "redirects" the flow of data, making all dependencies transparent.

**Key Characteristics:**
-   **Explicit Inputs**: Each imperative is expanded to show its specific dependencies, which are categorized and nested underneath it.
-   **Input Tagging**: Inputs are clearly tagged to show their origin:
    -   `<:{prompt}>`: Indicates the input is a prompt, further annotated with a `%{prompt_location}` to link to its source file.
    -   `<:{1}>`, `<:{2}>`, etc.: Indicates the input is an inherited output from a previous step, using positional markers.
    -   `%{file_location}`: Used for inputs sourced directly from static files.
-   **Data Flow Visibility**: This format makes the entire dependency graph of the plan visible and machine-parsable, which is essential for the final formalization and execution stages.

**Example Snippet:**
```normcode
<- {1.1_instruction_block.md}
    <= ::{%(direct)}({prompt}<$({instruction distillation prompt})%>: {1}<$({input files})%>)
    <- {instruction distillation prompt}<:{prompt}>
        |%{prompt_location}: 1.1_instruction_distillation.md
    <- {input files}<:{1}>
        <= &in
        <- {original prompt}
            |%{file_location}: prompts/0_original_prompt.md
```
This redirected draft is the last step before the plan is stripped of all annotations and assigned flow indices to become the final, formal `.nc` file.

---
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

---
