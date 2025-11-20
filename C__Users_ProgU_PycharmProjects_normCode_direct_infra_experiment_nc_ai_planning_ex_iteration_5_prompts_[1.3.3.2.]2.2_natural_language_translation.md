### Step 2.2: Automated Natural Language Translation

**Objective:** To translate the annotated and structured `deconstruction_draft.ncd` into a clean, human-readable `natural_translation.ncn` format. This step makes the plan accessible for manual review by stripping away machine-focused annotations and presenting the core logic in plain language.

The translation is guided by the specifications in the `shared---file_formats_guide.md` and the full set of NormCode syntax and terminology guides.

---
### Example Walkthrough

This example shows how the formal, annotated deconstruction of "Phase 1" is translated into a clear, natural language summary.

**1. Input (`2.1_deconstruction_draft.ncd` snippet):**

This is the machine-focused draft, rich with annotations (`?:`, `/:`) that explain the AI's reasoning during the deconstruction process.

```normcode
<- {Phase 1: Confirmation of Instruction}
    ?: How is {Phase 1} specified?
    <= &across
        /: This phase is specified as a series of steps.
    <- {step 1.1: Automated Instruction Distillation}
        ...: 1.1. Given a raw user prompt and system context...
    <- {step 1.2: Automated Context Registration}
        ...: 1.2. Following the distillation of the instruction...
    <- {step 1.3: Manual Review of Confirmation}
        ...: 1.3. To meticulously review and refine the outputs...
```

**2. LLM Translation Process:**

An LLM parses the `.ncd` snippet, focusing on the core concepts (`{...}`) while ignoring the reasoning annotations (`?:`, `/:`) and unprocessed source text (`...:`). It then rephrases the hierarchical structure into a readable, indented list.

**3. Output (`2.2_natural_translation.ncn` snippet):**

This is the human-readable output, which preserves the plan's structure but presents its logic in clear, natural language.

```ncn
The first phase is Confirmation of Instruction.
    <= This phase is specified as a series of steps.
    <- The first step is Automated Instruction Distillation.
    <- The second step is Automated Context Registration.
    <- The third step is Manual Review of Confirmation.
```

---
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

---
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

---
