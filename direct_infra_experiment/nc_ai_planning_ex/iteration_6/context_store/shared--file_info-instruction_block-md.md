# File Format: Instruction Block (`.md`)

The `1.1_instruction_block.md` file is the cleaned and distilled version of the user's original, high-level prompt. It serves as the definitive, structured input for the entire NormCode AI Planning Pipeline.

**Purpose:**
This file represents the official starting point for the deconstruction process (Phase 2). After the initial, often conversational, user prompt is clarified and refined in Phase 1, the result is captured in this file. It ensures that the rest of the pipeline operates on a clear, unambiguous, and well-structured set of instructions.

**Format:**
It is a Markdown file that typically contains a structured list of tasks or phases. The format is designed for clarity and logical flow, making it easier for the deconstruction agent to parse and translate into a formal NormCode plan.

**Example Snippet:**
```markdown
Execute the five-phase NormCode AI Planning Pipeline.

**Phase 1: Confirmation of Instruction**
1.1. Perform automated instruction distillation...
1.2. Perform automated context registration...

**Phase 2: Deconstruction into NormCode Plan**
2.1. Take the Instruction Block from Phase 1 and perform...
...
```
This file acts as the "source of truth" for the user's intent throughout the pipeline's execution.
