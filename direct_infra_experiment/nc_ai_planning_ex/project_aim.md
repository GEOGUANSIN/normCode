# Project Aim: NormCode AI Planning Self-Orchestration

This project aims to develop a functional NormCode script that orchestrates the **NormCode AI Planning** pipeline. The goal is to automate the process described in `NormCode_AI_planning.md`, translating a high-level natural language prompt and system context into a complete, executable NormCode plan.

The core of this experiment is a meta-algorithm: a NormCode plan that defines the very process of its own generation. It will leverage a series of specialized inferences to execute each phase of the AI Planning pipeline—from prompt deconstruction and context distribution to the final materialization of `ConceptRepo` and `InferenceRepo` entries. This approach effectively bootstraps the entire planning and code generation process using NormCode itself.

## Iterative Development

The development will follow an iterative approach. We will begin by creating a foundational NormCode script that handles a simplified version of the planning pipeline. Each subsequent version of the script will be used, along with manual refinement, to build the next, more sophisticated iteration. This strategy aims to continuously improve the accuracy and autonomy of the automated NormCode planning process.

Each iteration will produce a series of key artifacts that reflect the step-by-step nature of the AI planning pipeline:
1.  **Instruction & Context Files:** The initial confirmed instruction and parsed system context (e.g., `instruction.txt`).
2.  **NormCode Draft (`.ncd`):** The initial structural translation of the instruction into a NormCode draft, which may include annotations.
3.  **Refined NormCode (`.nc`):** A version of the NormCode plan after contextualization, without annotations of question or description but adding the flow index and seqeunce type, representing the pure logic before final code generation.
4.  **Runnable Python Script (`.py`):** The final, executable output containing the `ConceptRepo` and `InferenceRepo`, along with any generated prompts required for LLM-driven inferences. Related .json files for the repositories can be given.
