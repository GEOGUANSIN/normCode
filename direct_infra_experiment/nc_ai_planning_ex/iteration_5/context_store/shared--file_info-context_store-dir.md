# Directory Guide: context_store

The `context_store` is a directory that holds the "knowledge base" for the pipeline. It contains a variety of files, primarily Markdown (`.md`) but also plain text (`.txt`), which provide the necessary information and guidance for the AI to execute the steps of the NormCode plan.

**Purpose:**
The context store holds the "knowledge base" for the pipeline. Each file contains a specific piece of context—a procedure, a guide, a data format explanation, or a principle—that is required by one or more prompts during the plan's execution. This modular approach allows for precise context distribution, ensuring that each prompt receives only the information it needs.

**File Categories:**
The files within the directory are categorized by a naming prefix, which indicates their role. The full inventory of these files is referenced in `1.2_initial_context_registerd.json` (for raw context) and `4.1_context_manifest.json` (for refined, task-specific context). The categories are:

-   `shared--*.md`: These files contain context that is potentially relevant to many different steps across the pipeline (e.g., `shared---pipeline_goal_and_structure.md`).
-   `[flow_index]---*.md`: These files contain context that is highly specific to a single step in the plan, identified by its unique `flow_index` (e.g., `1.6.2.1---automated_script_generation.md`).
-   `raw--*.(md|txt)`: These files represent initial, unprocessed context registered at the beginning of the pipeline. They are intended to be analyzed or transformed into more refined context files, but are kept intact as a record of the original state.

**Role in the Pipeline:**
During Phase 4 (Contextualization), the system analyzes the plan and generates a `context_manifest.json` file. This manifest explicitly maps which files from the `context_store` are required for each prompt, enabling the final assembly of targeted, context-aware prompts.
