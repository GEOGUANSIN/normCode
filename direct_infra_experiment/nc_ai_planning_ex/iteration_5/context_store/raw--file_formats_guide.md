# NormCode File Format Guide

This document explains the purpose and characteristics of the three primary file formats used in the NormCode AI Planning Pipeline: `.ncd`, `.ncn`, and `.nc`. Each format represents the same underlying plan but is tailored for a different stage of the process, from human-readable design to machine-executable script.

---

## 1. `.ncd` - NormCode Draft

The `.ncd` file is the **annotated blueprint** of the plan. It is the primary output of Phase 2 (Deconstruction) and is designed for human review and debugging of the translation logic.

**Key Characteristics:**
-   **Semi-Formal:** It uses formal NormCode syntax for concepts (`{}`, `::()`) and operators (`<=`, `<-`), but is not yet ready for direct execution.
-   **Rich with Annotations:** This is its most important feature. It includes:
    -   `?:` (Question): Documents the question the translator asked to guide a specific decomposition step.
    -   `/:` (Description): Provides a human-readable summary of the result or purpose of an inference.
    -   `...:` (Source Text): Contains snippets of the original natural language instruction that still need to be decomposed.
-   **Hierarchical:** It preserves the full, indented hierarchical structure of the plan's logic.

**Purpose:** To provide a transparent, human-readable record of the automated translation process. It allows developers to verify that the original instruction was deconstructed correctly and to refine the logical structure before it is formalized.

**Example Snippet:**
```normcode
<- {Phase 1: Confirmation of Instruction}
    ?: How is {Phase 1} specified?
    <= &across
        /: This phase is specified as a series of steps.
    <- {step 1.1: Automated Instruction Distillation}
        ...: 1.1. Given a raw user prompt and system context...
    <- {step 1.2: Manual Review of Distillation}
        ...: 1.2. Present the generated blocks for optional manual review...
```

---

## 2. `.ncn` - NormCode Natural

The `.ncn` file is the **readable summary** of the plan. It is a direct, line-by-line translation of the `.ncd` file, optimized for clarity and quick comprehension.

**Key Characteristics:**
-   **Natural Language Concepts:** The formal NormCode concepts (e.g., `{step 1.1: Automated...}`) are replaced with clear, descriptive sentences (e.g., "Step 1.1 is to perform Automated...").
-   **Structure Preservation:** It maintains the exact same indentation and hierarchical structure as the `.ncd` file, including the ` <= ` and ` <- ` operators, to show the logical flow.
-   **No Annotations:** All `?:`, `/:`, and `...:` annotations are stripped out to remove clutter and focus purely on the plan's intent.

**Purpose:** To provide a high-level, easily understandable version of the plan for stakeholders who may not be familiar with NormCode syntax, or for developers who need a quick overview of the plan's logic without the detailed reasoning.

**Example Snippet:**
```ncn
<- The first phase is Confirmation of Instruction.
    <= This phase is specified as a series of steps.
    <- Step 1.1 is to perform Automated Instruction Distillation.
    <- Step 1.2 is to allow for Manual Review of the Distillation.
```

---

## 3. `.nc` - NormCode (Formal)

The `.nc` file is the **formal, machine-readable script** that is ready for the Orchestrator to execute. It is generated during Phase 3 (Formalization) by transforming the `.ncd` file.

**Key Characteristics:**
-   **Fully Formal:** The syntax is strict, consistent, and designed to be parsed by the execution engine.
-   **No Annotations:** All descriptive annotations (`?:`, `/:`, `...:`) are removed.
-   **Execution-Critical Information:** It is enriched with information required by the Orchestrator:
    -   **Flow Indices:** Each line is assigned a unique, dot-delimited index (e.g., `1.3.2.1`) that makes every inference in the plan uniquely addressable.
    -   **Agent Sequence Types:** Each inference is tagged with the name of the agent sequence (e.g., `grouping`, `imperative`, `timing`) that should execute it.
    -   **Formalized Operators:** Operators are made more explicit for the machine, for example, by specifying the positional markers for children in a grouping (`&across[{1},{2}]`).

**Purpose:** To serve as the direct input for the later stages of the pipeline, including context distribution (Phase 3) and materialization into an executable Python script (Phase 4). It is the definitive, parsable representation of the plan.

**Example Snippet:**
```normcode
1.3.2.object| {Phase 1: Confirmation of Instruction}<:{1}>
1.3.2.1.grouping| &across[{1}, {2}]
1.3.2.2.object| {step 1.1: Automated Instruction Distillation}<:{1}>
1.3.2.3.object| {step 1.3: Manual Review of Distillation}<:{2}>
```
