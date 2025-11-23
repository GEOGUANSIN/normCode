# File Format: Inference Repository (`inference_repo.json`)

The `inference_repo.json` file is a core artifact generated in the final phase of the pipeline (Phase 5, Materialization), alongside `concept_repo.json`. It is a serialized database of every inference, or logical step, defined in the NormCode plan.

**Purpose:**
This file provides the `Orchestrator` with the complete, step-by-step execution plan. While `concept_repo.json` defines *what* exists, `inference_repo.json` defines *how* and *when* concepts are computed and transformed. It is the "how" of the plan.

**Format:**
The file is a JSON array of `InferenceEntry` objects. Each object represents a single line of inference from the `.nc` file and contains the logic for that step:

-   `flow_info`: Contains the `flow_index` (e.g., `"1.2.2.1"`) from the `.nc` file, making the step traceable.
-   `inference_sequence`: The type of action to be performed (e.g., `imperative`, `grouping`, `assigning`), which determines the agent responsible for the step.
-   `concept_to_infer`: The ID of the concept that will be created or modified by this inference.
-   `function_concept`: The ID of the operator or function that drives the inference.
-   `value_concepts` / `context_concepts`: A list of IDs for the concepts that serve as inputs to this step.
-   `working_interpretation`: A critical JSON object that makes the implicit syntax of the NormCode explicit for the machine (e.g., defining loop parameters, value ordering for imperatives, or conditions for timing operators).

### The Role of `working_interpretation`

The `working_interpretation` is the bridge from the implicit syntax of NormCode to the explicit instructions needed by the Orchestrator's agents. It translates the compact NormCode notation into a detailed JSON object that clarifies the role of each concept in an inference.

-   **For `quantifying` inferences (`*every`)**: It defines the loop's structure, specifying the base collection to iterate over, the concept representing the current item, and any loop-scoped variables.
-   **For `assigning` inferences (`$.`, `$`)**: It specifies the source and destination concepts for a data transfer or state update.
-   **For `timing` inferences (`@if`, `@after`)**: It specifies the condition that must be met for the inference to proceed.
-   **For `imperative` and `judgement` inferences**: This is one of its most critical roles. It defines the interface for calling an external body (like an LLM). It maps the abstract `value_concepts` to the numbered placeholders in the imperative's text (e.g., `{1}`, `{2}`), specifies the location of a prompt file, and can even define how to select specific data from a relation concept to pass as input.

**Example Snippet (Conceptual):**
```json
[
  {
    "id": "...",
    "flow_info": { "flow_index": "1.3.2.1" },
    "inference_sequence": "imperative",
    "concept_to_infer": "id_of_{2.1_deconstruction_draft.ncd}",
    "function_concept": "id_of_::(deconstruction_imperative)",
    "value_concepts": ["id_of_{1.1_instruction_block.md}"],
    "working_interpretation": {
        "is_relation_output": false,
        "with_thinking": true,
        "prompt_location": "2.1_deconstruction.md",
        "value_order": { "id_of_{1.1_instruction_block.md}": 1 }
    }
  }
]
```