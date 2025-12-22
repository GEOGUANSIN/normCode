# File Format: Deconstruction Draft (`2.1_deconstruction_draft.ncd`)

The `2.1_deconstruction_draft.ncd` file is the **initial blueprint** of the plan, representing the first direct translation from the natural language `instruction_block.md` into the semi-formal NormCode structure.

**Purpose:**
This file's primary role is to act as a transparent and human-readable record of the automated deconstruction process (Phase 2). It captures not just the logical structure of the plan but also the reasoning behind each decomposition step, making it invaluable for debugging and verifying the initial translation. It is the raw, unrefined output before any formalization patterns are applied.

**Key Characteristics:**
-   **Rich with Annotations:** This is its defining feature. The file is filled with annotations that expose the "thought process" of the deconstruction agent:
    -   `?:` (Question): Documents the question the agent asked itself to break down a concept.
    -   `/:` (Description): Provides a human-readable summary of an inference's purpose.
    -   `...:` (Source Text): Contains the original natural language snippet that is being deconstructed.
-   **Hierarchical Structure:** It maintains the full, indented hierarchy of the plan as inferred from the source instructions.

**Example Snippet:**
```normcode
<- {Phase 1: Confirmation of Instruction}
    ?: How is {Phase 1} specified?
    <= &across
        /: This phase is specified as a series of steps.
    <- {step 1.1: Automated Instruction Distillation}
        ...: 1.1. Perform automated instruction distillation...
```
This file serves as the foundational draft upon which all subsequent refinement steps (Serialization, Redirection, Formalization) are built.
