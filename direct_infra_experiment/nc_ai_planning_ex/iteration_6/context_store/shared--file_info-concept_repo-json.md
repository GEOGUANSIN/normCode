# File Format: Concept Repository (`concept_repo.json`)

The `concept_repo.json` file is a core artifact generated in the final phase of the pipeline (Phase 5, Materialization). It serves as a serialized database of every concept that exists within the NormCode plan.

**Purpose:**
This file provides the `Orchestrator` with a complete, structured inventory of all the conceptual elements it will manage during execution. It defines what data exists, what its properties are, and how it is initialized. It is the "what" of the plan.

**Format:**
The file is a JSON array of `ConceptEntry` objects. Each object represents a single concept from the `.nc` plan. The key is to map every unique NormCode symbol that needs to hold state into a `ConceptEntry`.

### `ConceptEntry` Attributes by NormCode Type

#### 1. Semantical Concepts (`{}`, `[]`, `<>`)
These represent the core entities of the plan.
-   `concept_name`: The exact string from the NormCode (e.g., `{normcode draft}`, `<draft is complete>`).
-   `type`: Set to `"{}"` for objects, `"[]"` for relations, or `"<>" for statements.
-   `is_ground_concept`: `true` for initial inputs (like the first `{normcode draft}`), `false` for intermediate concepts that are computed during the run.
-   `is_final_concept`: `true` for concepts that represent the final output of the plan.
-   `reference_data`: For ground concepts, this holds their initial value. For multi-dimensional data, this should be a nested list, with `reference_axis_names` defining the axes.

#### 2. Functional & Operator Concepts
These concepts define the logic and control flow. They are almost always ground concepts, as their meaning is fixed.
-   `concept_name`: The full textual operator (e.g., `*every([all {normcode draft}])`, `::(sum {1} and {2})`).
-   `type`: A string that identifies the operator class, such as `"*every"`, `"&across"`, `"$.`, `"@if"`, `"::({})"`, or `"%:({})"`.
-   `is_ground_concept`: `true`.
-   `is_invariant`: Often `true`, as the operator's function does not change.
-   `reference_data`: For functional concepts like imperatives or judgements, this is typically a one-element list containing the textual form of the function, which pins its meaning for the execution body.

**Example Snippet (Conceptual):**
```json
[
  {
    "id": "...",
    "concept_name": "{number pair}",
    "type": "{}",
    "is_ground_concept": true,
    "is_final_concept": false,
    "reference_data": [["%(123)", "%(98)"]],
    "reference_axis_names": ["number pair", "number"]
  },
  {
    "id": "...",
    "concept_name": "*every({number pair})",
    "type": "*every",
    "is_ground_concept": true,
    "is_invariant": true
  },
  {
    "id": "...",
    "concept_name": "::(sum {1} and {2})",
    "type": "::({})",
    "is_ground_concept": true,
    "is_invariant": true,
    "reference_data": ["::(sum {1} and {2})"]
  }
]
```
This repository allows the `Orchestrator` to load the entire conceptual landscape of the plan before execution begins.
