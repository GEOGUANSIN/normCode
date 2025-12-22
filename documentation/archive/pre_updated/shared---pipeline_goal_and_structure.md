# The NormCode AI Planning Pipeline

## Project Goal

The project goal is to bootstrap from a high-level natural language prompt into a structured and executable plan using a meta-algorithmic pipeline. This pipeline, itself powered by a NormCode plan, methodically transforms an instruction by:

1.  **Distilling** the user's intent into a clean instruction and registering all raw context.
2.  **Deconstructing** the instruction into a formal, hierarchical NormCode plan (`.ncd`).
3.  **Formalizing** the plan by applying serialization and redirection patterns and generating a final `.nc` file.
4.  **Contextualizing** the plan by enriching each formal step with precise, granular context and assembling prompts.
5.  **Materializing** the final plan into an executable script, ready for an orchestrator.

This creates a system that can understand, decompose, contextualize, and act upon complex instructions in a transparent and repeatable manner.

## Core Inputs

Each iteration of the pipeline begins with two primary markdown files that define the scope and methodology of the task:

-   **`prompts/0_original_prompt.md`**: This file contains the high-level goal that is the target of the decomposition process. It defines the "what" that the pipeline needs to accomplish.
-   **`_meta_pipeline_prompt.md`**: This file documents the methodology used to bootstrap the entire process. It defines the "how" the decomposition and planning will be executed.

For the purpose of this project, these two files are kept synchronized and are updated dynamically through manual modifications to reflect the most current practices and understanding of the pipeline itself.

## The Five-Phase Pipeline

The pipeline is divided into five distinct phases, each with a specific objective:

1.  **Phase 1: Confirmation of Instruction**: Transforms the initial, conversational user prompt into a set of clean, structured inputs (an `Instruction Block` and a `Context Manifest`). This phase includes an opportunity for manual review to ensure accuracy.

2.  **Phase 2: Deconstruction into NormCode Plan**: Translates the clean `Instruction Block` into a semi-formal NormCode Draft (`.ncd`). This draft represents the logical structure of the plan and is designed for human review.

3.  **Phase 3: Plan Formalization and Redirection**: Applies serialization and redirection patterns to the plan and converts the `.ncd` draft into a formal `.nc` file with unique identifiers (`flow_index`) for each step.

4.  **Phase 4: Contextualization and Prompt Assembly**: Distributes context from a `context_store` to each step in the plan, generates a `context_manifest.json`, and assembles the final prompt files.

5.  **Phase 5: Materialization into an Executable Script**: Translates the final, formalized `.nc` plan and its context map into a runnable Python script, ready for execution by an `Orchestrator`.

This structured, phased approach ensures that a high-level, ambiguous instruction can be methodically transformed into a precise, executable, and context-aware plan.


