# File Format: NormCode Draft (`.ncd`)

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
