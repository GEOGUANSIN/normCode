# File Format: NormCode Natural (`.ncn`)

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
