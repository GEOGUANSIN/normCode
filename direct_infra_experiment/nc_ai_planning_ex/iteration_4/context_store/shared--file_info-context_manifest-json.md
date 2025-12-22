# File Format: Context Manifest (`.json`)

The `context_manifest.json` file is a critical artifact generated during Phase 4 (Contextualization). It acts as a map, linking each prompt in the plan to both its required context files and the specific inference that uses it.

**Purpose:**
The manifest's primary role is to provide the precise list of context files needed to assemble each prompt. By also including a reference to the inference that consumes the prompt, it creates a fully traceable link between a high-level action, its instruction (the prompt), and its knowledge base (the context). This ensures every step is minimal, complete, and auditable.

**Format:**
The manifest is a JSON object. Each key uniquely identifies a prompt, and the corresponding value is an object containing details about its usage.

-   **Key**: `"[flow_index]prompt_filename.md"`
    -   `flow_index`: The unique, dot-delimited index of the prompt object from the `.nc` file (e.g., `1.2.2.2.`).
    -   `prompt_filename.md`: The filename of the prompt, as specified in the `%{prompt_location}` annotation.
-   **Value**: An object with two fields:
    -   `used_by_inference`: A string containing the full line of the inference from the `.nc` file that uses this prompt.
    -   `context_files`: An array of strings, where each string is a path to a required context file.

**Example Snippet:**
```json
{
  "[1.2.2.2.]1.1_instruction_distillation.md": {
    "used_by_inference": "1.2.2.1.imperative|<= ::{%(direct)}({prompt}<$({instruction distillation prompt})%>: {1}<$({input files})%>)",
    "context_files": [
      "./context_store/1.2.2.1---automated_instruction_distillation.md",
      "./context_store/shared---pipeline_goal_and_structure.md"
    ]
  },
  "[1.2.3.2.]1.2_context_registration.md": {
    "used_by_inference": "1.2.3.1.imperative|<= ::{%(direct)}({prompt}<$({context registration prompt})%>: {1}<$({input files})%>)",
    "context_files": [
      "./context_store/1.2.3.1---automated_context_registration.md",
      "./context_store/shared---pipeline_goal_and_structure.md"
    ]
  }
}
```
This structure provides a clear, machine-readable, and highly traceable map for the prompt assembly process.
