# File Format: Initial Context Registered (`.json`)

The `1.2_initial_context_registerd.json` file is a crucial input generated during Phase 1. It acts as the first machine-readable inventory of all the high-level, raw context materials available to the pipeline.

**Purpose:**
This file serves as a manifest, or an index, for the unstructured knowledge contained in the `context_store/raw--*` files. It allows the system to understand what context is available before the more detailed context distribution in Phase 4. It maps human-readable descriptions of each knowledge source to its corresponding file.

**Format:**
It is a JSON object containing a `summary` and an array of `sections`. Each section object represents a single raw context file.

-   `summary`: A brief, high-level description of the overall context.
-   `sections`: An array of objects, where each object has:
    -   `title`: A human-readable title for the context document.
    -   `description`: A paragraph explaining the purpose and content of the referenced file.
    -   `file_reference`: The relative path to the raw context file within the `context_store`.

**Example Snippet:**
```json
{
  "summary": "This context block provides the high-level summary and references for the NormCode AI Planning Pipeline meta-algorithm...",
  "sections": [
    {
      "title": "Core Methodology and Examples",
      "description": "The primary methodology is a four-phase pipeline...",
      "file_reference": "./context_store/raw--prompt.txt"
    },
    {
      "title": "Technical Language Specification",
      "description": "The underlying semi-formal language used in the plan is NormCode...",
      "file_reference": "./context_store/raw--normcode_terminology_guide.txt"
    }
  ]
}
```
This file is essential for bootstrapping the pipeline's understanding of its own knowledge base.
