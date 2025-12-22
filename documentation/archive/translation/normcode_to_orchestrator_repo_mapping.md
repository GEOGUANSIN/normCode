## NormCode → Orchestrator Repository Mapping

This note summarizes **how a concrete NormCode program is turned into `ConceptRepo` and `InferenceRepo` definitions** for the orchestrator, using:

- `infra/examples/add_examples/ex_add_complete.py`
- `infra/examples/add_examples/ex_add_complete_code.py`
- `direct_infra_experiment/translation_experiment/version_1/v1_manual.ncd`
- `direct_infra_experiment/translation_experiment/version_1/run_v1_manual.py`

The goal is not a full translation algorithm, but a **mechanical mapping pattern** you can follow when hand‑encoding a NormCode draft into repository code.

---

### 1. High‑level pipeline

- **1. Start from a fixed NormCode draft**
  - Example A: `Normcode_new_with_appending` inside the add examples encodes digit‑wise addition of `{number pair}` with carry.
  - Example B: `v1_manual.ncd` encodes a loop that **progressively refines `{normcode draft}`** via decomposition prompts.

- **2. Identify all symbol types in the NormCode**
  - **Object concepts**: `{number pair}`, `{digit sum}`, `{normcode draft}`, `{functional concept}`, etc.
  - **Statement concepts**: `<all number is 0>`, `<current normcode draft is complete>`, `<carry-over number is 0>`, etc.
  - **Relation concepts**: `[all {unit place value} of numbers]`, `[{concept to decomposed} and {remaining normtext}]`, `[all {normcode draft}]`, etc.
  - **Function / operator concepts**: `*every(...)`, `&across(...)`, `$.(...)`, `$+(...)`, `@if`, `@if!`, `@after`, and the various `::(...)` direct/indirect imperatives and judgements.

- **3. Classify how each symbol behaves**
  - **Final outputs** (e.g. `{new number pair}`, `{normcode draft}`) → marked as `is_final_concept=True`.
  - **Ground concepts** (inputs, prompts, fixed operations, initial carry, etc.) → `is_ground_concept=True`, usually with `reference_data` and `reference_axis_names`.
  - **Intermediate concepts** (loop items, temporary results) → no references; they exist only inside the run.
  - **Function concepts** (operators, quantifiers, timing) → `type` is the operator kind (e.g. `"*every"`, `"&across"`, `"$.", ":{}` for judgements), and they may be invariant.

- **4. For each NormCode inference block, create an `InferenceEntry`**
  - Map the **NormCode sequence label** (`1.`, `1.1.2.4.2.1`, etc.) to `flow_info={'flow_index': '...'}`.
  - Map the **NormCode role** to `inference_sequence`, e.g.:
    - `quantifying`, `assigning`, `grouping`, `imperative`, `judgement`, `timing`.
    - Or experiment‑specific variants: `imperative_python`, `imperative_python_indirect`, `judgement_python`, `imperative_input`, `imperative_direct`, `judgement_direct`.
  - Set `concept_to_infer` to the concept on the left of the inference.
  - Set `function_concept` to the operator after `<=`.
  - Fill `value_concepts` and `context_concepts` from the concepts appearing under the corresponding `"<-"` lines in the NormCode.
  - Use `working_interpretation` to encode **syntax/loop metadata** the orchestrator needs but which is implicit in the NormCode (e.g. loop base, current item, value ordering, conditions).

- **5. Optionally, connect to external prompts and code**
  - For direct NormCode translation (e.g. `run_v1_manual.py`), `reference_data` for prompt concepts points at **prompt files**.
  - For imperative‑Python variants (e.g. `ex_add_complete_code.py`), additional ground concepts carry:
    - script locations (`nominalized_action_sum`, `nominalized_action_get_digit`, …)
    - prompt locations (`prompt_location_sum`, `prompt_location_get_digit`, …)
  - `working_interpretation["value_order"]` specifies the order in which these are passed to the body.

---

### 2. From NormCode tokens to `ConceptEntry`

The basic rule is: **every syntactic token that needs state in the orchestrator becomes a `ConceptEntry`**.

#### 2.1 Object / statement / relation concepts

- **Objects (`{}`)**  
  - Example (add code): `{number pair}`, `{digit sum}`, `{remainder}`, `{carry-over number}`, `{sum}?`.  
  - Example (v1 manual): `{normcode draft}`, `{normcode draft}<$={1}>`, `{functional concept}`, `{children concepts}`, `{new inference}`.
  - Implementation pattern:
    - `concept_name` = the exact token (including decorations like `?` or `<$={1}>` where those are meaningful indices).
    - `type` = `"{}"` for object‑like concepts.
    - `axis_name` = semantic axis (e.g. `"number pair"`, `"digit sum"`, `"value"`).
    - `description` / `context` = short English explanation.
    - For ground objects with fixed content, supply **tensor‑like references** via `reference_data` and `reference_axis_names`.  
      - In the addition examples, `{number pair}` ground data is given as a nested list `reference_data=[["%(123)", "%(98)"]]` with `reference_axis_names=["number pair", "number"]`. This reflects the preferred style of passing **nested lists** for multi‑axis data.

- **Statements (`<>`)**  
  - Example: `<all number is 0>`, `<carry-over number is 0>`, `<current normcode draft is complete>`.  
  - Implementation pattern:
    - `type` = `"<>"`
    - Typically **no reference data** (they are computed), except for **judgement function concepts** (see below).

- **Relations (`[]`)**  
  - Example: `[all {unit place value} of numbers]`, `[all {normcode draft}]`, `[all {normcode draft}]*1`, `[{concept to decomposed} and {remaining normtext}]`.  
  - Implementation pattern:
    - `type` = `"[]"`
    - `axis_name` = name of the collection (e.g. `"all unit place value of numbers"`, `"value"`).
    - No reference data for dynamic collections; they are filled through `grouping` or `quantifying` inferences.

#### 2.2 Function / operator concepts

- **Quantifiers (`*every`)**
  - Example (addition): `*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]`, `*every({number pair}*1)%:[{number}]@(2)`, `*every({number pair}*1)%:[{number}]@(3)`.
  - Example (v1 manual): `*every([all {normcode draft}])`.
  - Implementation pattern:
    - A `ConceptEntry` with `type="*every"`, `concept_name` equal to the full textual operator.
    - Often `is_ground_concept=True` since the operator semantics are fixed.

- **Grouping (`&across`)**
  - Example: `&across({unit place value}:{number pair}*1)`, `&across({carry-over number}*1:{carry-over number}*1<--<!_>>)` and `&across({normcode draft})` in v1.
  - Implementation pattern:
    - `type="&across"`, `concept_name` equal to the operator string.
    - Grounded operator semantics (grouping) with optional `working_interpretation["syntax"]["by_axis_concepts"]`.

- **Pass‑through / assignment (`$.`)**
  - Example: `$.({digit sum})`, `$.({remainder})`, `$.({single unit place value})`, `$.({number with last digit removed})`, `$.({normcode draft}<$={#}>)`, `$.([all {normcode draft}]*1)`, `$.({normcode draft})`, `$.({normcode draft}<$={4}>)`.
  - Implementation pattern:
    - `type="$.", concept_name="$.(...)"`, usually `is_ground_concept=True`.
    - These are used as `function_concept` in assigning inferences to move values between concepts or from loop items into collectors.

- **Append (`$+`)**
  - Example: `$+({number pair to append}:{number pair})` in the addition example.
  - Implementation pattern:
    - `type="$+"`, `is_ground_concept=True`.
    - In `InferenceEntry.working_interpretation`, `"marker": "+", "assign_source": "{number pair to append}", "assign_destination": "{number pair}"`.

- **Imperatives / judgements (`::`, `<{}>` in the examples)**
  - Imperative operations are represented as **distinct function concepts**, each with a stable textual name mirroring the NormCode imperative:
    - Addition: `::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)`.
    - Digit extraction: `::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)`.
    - Division helpers: `::(find the {1}?<$({quotient})%_> of {2}<$({digit sum})%_> divided by 10)`, `::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10)`.
    - Decomposition prompts in v1: a family of `::{%(direct)}<...>` functions for initialization, completion check, concept identification, question formulation, operator selection, children creation, normtext distribution, and draft update.
  - Judgement functions are similar but given `type="<{}>"` in the addition example for zero checks:
    - `:%(True):<{1}<$({number})%_> is 0>`, `:%(True):<{1}<$({carry-over number})%_> is 0>`.
  - Implementation pattern:
    - `type` encodes the operator class (e.g. `"::({})"` or `"<{}>"`).
    - `is_ground_concept=True`, `is_invariant=True`.
    - `reference_data` is usually a **one‑element list containing the textual form**, with a matching `reference_axis_names` entry. This pins the meaning of the operator for the body.

- **Timing (`@if`, `@if!`, `@after`)**
  - Examples:
    - `@if!(<all number is 0>)`, `@if(<carry-over number is 0>)`, `@after({digit sum})`, `@after({number pair to append}<$={1}>)`.
    - In v1 manual: `@if(<current normcode draft is complete>)`, `@if!(<current normcode draft is complete>)`.
  - Implementation pattern:
    - `type="@if"`, `"@if!"`, or `"@after"`, `is_ground_concept=True`.
    - Used as `function_concept` in `timing` inferences, with `working_interpretation["syntax"]["marker"]` and `"condition"` mirroring the NormCode.

---

### 3. From NormCode inferences to `InferenceEntry`

After all needed `ConceptEntry` objects exist, **each NormCode inference line (or block) becomes one `InferenceEntry`**.

#### 3.1 Core fields

For both examples, the mapping is:

- **`inference_sequence`**  
  - Mirrors the **NormCode annotation** at the right of the line:
    - Addition: `"quantifying"`, `"assigning"`, `"grouping"`, `"imperative"`, `"judgement"`, `"timing"`, plus specialized `"imperative_python"`, `"imperative_python_indirect"`, `"judgement_python"`, `"judgement_python_indirect"`.
    - v1 manual: `"imperative_input"`, `"imperative_direct"`, `"judgement_direct"`, `"grouping"`, `"quantifying"`, `"assigning"`, `"timing"`.
  - This controls which orchestrator pipeline is used for that step.

- **`concept_to_infer`**  
  - The concept on the line being defined, e.g.:
    - `{new number pair}` for the top‑level quantifier in addition.
    - `{digit sum}`, `{remainder}`, `{carry-over number}*1`, `[all {unit place value} of numbers]`, etc. for lower‑level steps.
    - `{normcode draft}` for the final assignment in v1, `{normcode draft}<$={5}>` for the loop result, and other indexed variants within the loop.

- **`function_concept`**  
  - The operator after `<=` in NormCode:
    - Quantifiers: `*every(...)`.
    - Grouping: `&across(...)`.
    - Assignment: `$.(...)`.
    - Append: `$+(...)`.
    - Imperatives / judgements: the various `::(...)` or `::{%(direct)}<...>` definitions; `:%(True):<...>` for judgements.
    - Timing: `@if`, `@if!`, `@after`.

- **`value_concepts` and `context_concepts`**  
  - These correspond to the **children under `"<-"`** in the NormCode block:
    - Addition example:
      - For `{digit sum}`: `[all {unit place value} of numbers]`, `{carry-over number}*1`, `{sum}?`.
      - For `[all {unit place value} of numbers]`: `{unit place value}`, with context `{number pair}*1`.
      - For `{unit place value}` quantifying step: `{number pair}*1` as value, `{number pair}*1*2` as context.
      - For appending: `{number pair to append}`, `{number pair}`, `<all number is 0>`, `<carry-over number is 0>`, etc.
    - v1 manual:
      - For the top‑level `{normcode draft}`: direct assignment from `{normcode draft}<$={5}>`.
      - For initialization, completion check, and decomposition: the various prompt concepts and relation concepts defined in section 2.
  - The **ordering** of these is further specified in `working_interpretation["value_order"]` when needed, especially for imperatives that interact with prompts or external actions.

#### 3.2 `working_interpretation` as the bridge from syntax to orchestration

`working_interpretation` encodes the **implicit syntax-level information** that is present in the NormCode but needs to be explicit for the orchestrator:

- **Loop metadata** (for `quantifying` inferences)
  - Keys like `"LoopBaseConcept"`, `"CurrentLoopBaseConcept"`, `"group_base"`, `"quantifier_index"`, and `"ConceptToInfer"` mirror the `*every(...)` specification.
  - Example (addition, outer loop):
    - `"LoopBaseConcept": "{number pair}"`
    - `"CurrentLoopBaseConcept": "{number pair}*1"`
    - `"group_base": "number pair"`
    - `"InLoopConcept": {"{carry-over number}*1": 1}`

- **Assignment semantics** (for `assigning` inferences)
  - `"assign_source"` and `"assign_destination"` show which concept is being written from/to (`$.` and `$+` cases).
  - In some cases (e.g. v1 manual main loop), `"assign_source"` can be a list to reflect conditional update (e.g. pick between `{normcode draft}<$={2}>` and `{normcode draft}<$={3}>`).

- **Timing / conditions**
  - `"marker"` and `"condition"` encode `@if`, `@if!`, and `@after` semantics, tying the timing operator back to the relevant judgement or concept.

- **Prompt / body call semantics**
  - For direct LLM calls (v1 manual), `"prompt_location"` is set to the name of a prompt file (e.g. `"completion_check_prompt"`, `"concept_identification_prompt"`).
  - `"value_order"` and `"value_selectors"` specify:
    - Which concepts are passed to the body.
    - In what order.
    - How to extract elements from relation concepts (e.g. from `[{concept to decomposed} and {remaining normtext}]`).

---

### 4. Imperative‑Python vs. direct NormCode execution

The two addition files show **two modes for realizing NormCode imperatives**:

- **Direct repository‑only version (`ex_add_complete.py`)**
  - Imperatives like `::(sum ...)`, `::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)`, etc. are defined as ground `ConceptEntry` operators with simple `reference_data` strings.
  - `inference_sequence='imperative'` / `'judgement'` indicate that the body will implement their semantics internally (e.g. through a fixed handler).

- **Python‑indirect version (`ex_add_complete_code.py`)**
  - The same logical imperatives exist, but now each critical operation has **two extra ground concepts**:
    - `nominalized_action_<op>`: holds `%{script_location}(...)` pointing at a generated Python script in `generated_scripts/`.
    - `prompt_location_<op>`: holds `%{prompt_location}(...)` pointing at a prompt file in `generated_prompts/`.
  - The corresponding `InferenceEntry` uses an `inference_sequence` such as `'imperative_python_indirect'` and includes these two concepts in `value_concepts`, with their positions enforced via `value_order`.
  - This allows the orchestrator to:
    - Call an LLM to produce or refine a script.
    - Execute that script to implement the imperative step.

The v1 manual example (`run_v1_manual.py`) is structurally similar to the **direct** approach, but with a richer prompt lattice for decomposition rather than numeric operations.

---

### 5. Practical recipe for authoring new repo code from NormCode

Given a new NormCode draft you want to run through the orchestrator:

- **Step 1 – List all symbols**
  - Enumerate every `{...}`, `[...]`, `<...>`, and each operator form (`*every(...)`, `&across(...)`, `$.(...)`, `$+`, `@if`, `@if!`, `@after`, `::(...)`, `::{%(direct)}<...>`, `:%(True):<...>`, etc.).

- **Step 2 – Create `ConceptEntry` for each**
  - Decide which are:
    - **Final concepts** (mark `is_final_concept=True`).
    - **Ground concepts** (inputs, prompts, fixed carry, script/prompt locations, invariant operators). Give these `reference_data` / `reference_axis_names`, using **nested lists** for multi‑axis structured data where appropriate.
    - **Intermediate concepts** (loop variables, temporary results, relation concepts inside decompositions).

- **Step 3 – For each NormCode inference block, add an `InferenceEntry`**
  - Choose `inference_sequence` to match the NormCode role and your orchestrator pipeline naming.
  - Set `concept_to_infer`, `function_concept`, `value_concepts`, `context_concepts`.
  - Fill `flow_info['flow_index']` with the NormCode label for traceability.
  - Add `working_interpretation`:
    - Loop metadata for `*every` and `&across`.
    - Assignment markers for `$` / `$+`.
    - Conditions for `@if`, `@if!`, `@after`.
    - Prompt locations and value ordering for direct/indirect imperatives.

- **Step 4 – Wire in the body if needed**
  - For direct LLM‑driven steps (like v1 manual), create prompt concepts whose `reference_data` are `"%{prompt}(...)"` pointing at your prompt files.
  - For Python‑indirect steps, follow the pattern from `ex_add_complete_code.py` with `nominalized_action_*` and `prompt_location_*` concepts plus appropriate `inference_sequence` variants.

Following this pattern, any well‑structured NormCode example can be turned into a pair of repositories (`ConceptRepo`, `InferenceRepo`) that the orchestrator can execute while preserving the original plan’s structure and flow.


