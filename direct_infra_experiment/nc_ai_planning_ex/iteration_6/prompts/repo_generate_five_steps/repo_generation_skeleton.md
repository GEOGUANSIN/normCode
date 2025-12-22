# NormCode to Repository Transpilation Pipeline

This process converts a raw or "stripped" NormCode plan (abstract logic) into a fully executable repository set (`concept_repo.json`, `inference_repo.json`).

**Input:** `stripped.nci.json` (Inference-Centric Intermediate) + `Context`
**Final Output:** `concept_repo.json`, `inference_repo.json`

---

## Step 1: Implementation Design (The "Architect")

**Objective:** Select the concrete tools (Paradigms and Prompts) for each abstract inference unit.
**Input:** List of Inference Units from `stripped.nci.json`, `Dynamic Paradigm Manifest` (XML-formatted list of available tools), `Context`.

**Prompt Skeleton:**
1.  **Iterate** through each Inference Unit object in the input list.
2.  **Analyze & Normalize:** Check `function_concept`. If it's a raw imperative (e.g., `::(instruction)`), judgement (`::<>`), or subject (`:xx:`), **transform** it:
    *   Rewrite function to `:%(Composition):{paradigm}(...)`.
    *   Extract the instruction text to a new `value_concept`.
3.  **Select Paradigm:** Query the `Paradigm Manifest` to find the XML entry that best matches the unit's intent. Select that filename.
4.  **Select Resources:** Identify necessary prompts/scripts for this unit.
5.  **Output:** An annotated or "Enriched" version of the Inference Unit (adding `attached_comments` with `| %{paradigm}: ...`).

---

## Step 2: Data Flow Binding (The "Plumber")

**Objective:** Define how data enters/exits the chosen paradigms (Wrappers & Paths).
**Input:** Enriched Inference Units (from Step 1), `MVP Wrapper Docs`.

**Prompt Skeleton:**
1.  **Iterate** through the Enriched Inference Units.
2.  **Bind Inputs:** For each item in `value_concepts`, determine the required wrapper:
    *   Need file content? -> `%{file_location}id(...)`
    *   Need file path string? -> `%{save_path}id(...)`
3.  **Bind Outputs:** Define attributes for `concept_to_infer` (e.g., output directory).
4.  **Generate Enriched NC:** Produce the fully annotated `.nci.json` where every concept has the correct `nc_comment` metadata attached.

---

## Step 3: Concept Extraction (The "Linker")

**Objective:** Create `concept_repo.json`.
**Constraint:** Do not infer logic. Only identify "Nouns" and "Operators".

**Prompt Skeleton:**
1.  **Input:** Enriched `.nci.json` (from Step 2).
2.  **Scan** every concept (`concept_to_infer`, `value_concepts`) across all units.
3.  **Extract** tokens enclosed in `{...}`, `[...]`, or `<...>`.
    *   *Rule:* Treat the string inside the brackets as the unique ID.
4.  **Deduplicate**: Create exactly one entry per unique token.
5.  **Classify**: Set `type`, `is_ground_concept`, etc.
6.  **Output**: A JSON list of `ConceptEntry` objects.

---

## Step 4: Inference Skeleton (The "Graph Builder")

**Objective:** Create `inference_repo.json` (Structure only).
**Constraint:** Map Flow Structure 1:1.

**Prompt Skeleton:**
1.  **Input:** Enriched `.nci.json` AND `concept_repo.json`.
2.  **Iterate** through each Inference Unit.
3.  **Map Fields**:
    *   `flow_info`: Extract from `function_concept.flow_index`.
    *   `inference_sequence`: Map based on `function_concept.nc_main` (e.g., `::` -> `imperative`).
    *   `concept_to_infer`: Map to `concept_to_infer.nc_main`.
    *   `function_concept`: Map to `function_concept.nc_main`.
    *   `value_concepts`: Map list of `nc_main` from `value_concepts`.
4.  **Output**: A JSON list of `InferenceEntry` objects (empty `working_interpretation`).

---

## Step 5: Syntax Compilation (The "Compiler")

**Objective:** Fill the `working_interpretation` field.
**Constraint:** Strict syntax parsing. No creative interpretation.

**Prompt Skeleton:**
1.  **Input:** `inference_repo.json` (Skeleton) AND Enriched `.nci.json`.
2.  **Match** each `InferenceEntry` to its source Inference Unit in `.nci.json`.
3.  **Parse Metadata**:
    *   Read `attached_comments` from `function_concept` for Paradigm.
    *   Read `attached_comments` from `value_concepts` for Wrappers/Prompts.
    *   Parse inline syntax `{1}<$({Input})%>` for `value_order`.
4.  **Output**: The fully populated `inference_repo.json`.
