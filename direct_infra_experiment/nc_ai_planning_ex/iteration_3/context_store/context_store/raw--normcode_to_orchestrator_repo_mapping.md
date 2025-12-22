## NormCode → Orchestrator Repository Mapping

This note describes a **procedure** that takes a concrete NormCode draft as input and produces:

- first, a **repository design** (lists of concepts and inferences, including their `working_interpretation`),
- then a **Python repository script** (a `.py` file that builds `ConceptRepo` and `InferenceRepo` from that design), and
- an **orchestrator entry point** that uses those repos to run the plan,
- plus optionally, a **serialized repository** (e.g. `.json`) generated from those repos.

The procedure is illustrated using:

- `infra/examples/add_examples/ex_add_complete.py`
- `infra/examples/add_examples/ex_add_complete_code.py`
- `direct_infra_experiment/translation_experiment/version_1/v1_manual.ncd`
- `direct_infra_experiment/translation_experiment/version_1/run_v1_manual.py`

The goal is a repeatable, mechanical pattern you can follow when **hand‑encoding a NormCode draft into a `.py` repository script** that the orchestrator can import and run.

---

### 0. Inputs and outputs

- **Input**: A fixed NormCode draft (e.g. a `.ncd` file or an inline `Normcode_...` string) that you want the orchestrator to execute.
- **Intermediate output**: A **repository specification** consisting of:
  - a list of **Concept definitions** (what exists, what is ground/final/intermediate), and
  - a list of **Inference definitions** (what is inferred when, plus their `working_interpretation`).
- **Final output**: A Python file that implements that specification as a `ConceptRepo` and `InferenceRepo`, plus:
  - a small **orchestrator runner** that builds the repos and calls `Orchestrator(...).run()`, and
  - optional helpers (e.g. JSON export utilities).

---

### 1. Step‑by‑step procedure from NormCode to repository design

This section is about designing the **repos themselves** (concepts, inferences, `working_interpretation`), independently of any particular `.py` implementation. Only after this design is clear do we embed it into a Python module.

- **Step 1 – Start from a fixed NormCode draft**
  - Example A: `Normcode_new_with_appending` inside the add examples encodes digit‑wise addition of `{number pair}` with carry.
  - Example B: `v1_manual.ncd` encodes a loop that **progressively refines `{normcode draft}`** via decomposition prompts.

- **Step 2 – Identify all symbol types in the NormCode**
  - **Semantical object concepts (`{}`)**: `{number pair}`, `{digit sum}`, `{normcode draft}`, `{functional concept}`, etc.
  - **Semantical statement concepts (`<>`)**: `<all number is 0>`, `<current normcode draft is complete>`, `<carry-over number is 0>`, etc.
  - **Semantical relation concepts (`[]`)**: `[all {unit place value} of numbers]`, `[{concept to decomposed} and {remaining normtext}]`, `[all {normcode draft}]`, etc.
  - **Syntactical operator concepts** (as in the NormCode Guide’s assigning / timing / grouping / quantifying categories): `*every(...)`, `&across(...)`, `$=(...)`, `$.(...)`, `$+(...)`, `@if`, `@if!`, `@after`, and the various `::(...)` imperatives and `<{}>` judgements.

- **Step 3 – Classify how each concept behaves in the run**
  - **Final outputs** (e.g. `{new number pair}`, `{normcode draft}`) → marked as `is_final_concept=True`.
  - **Ground concepts** (inputs, prompts, fixed operations, initial carry, etc.) → `is_ground_concept=True`, usually with `reference_data` and `reference_axis_names`.
  - **Intermediate concepts** (loop items, temporary results) → no references; they exist only inside the run.
  - **Functional / operator concepts** (imperatives, judgements, and syntactical operators) → `type` is the operator kind (e.g. `"*every"`, `"&across"`, `"$.", "$+", "@if", "@after", "::({})", "<{}>"`), and they may be invariant.

- **Step 4 – For each NormCode inference block, sketch the corresponding `InferenceEntry`**
  - Map the **NormCode sequence label** (`1.`, `1.1.2.4.2.1`, etc.) to `flow_info={'flow_index': '...'}`.
  - Map the **NormCode role** to `inference_sequence`, e.g.:
    - `quantifying`, `assigning`, `grouping`, `imperative`, `judgement`, `timing`.
    - Or experiment‑specific variants: `imperative_python`, `imperative_python_indirect`, `judgement_python`, `imperative_input`, `imperative_direct`, `judgement_direct`.
  - Set `concept_to_infer` to the concept on the left of the inference.
  - Set `function_concept` to the operator after `<=`.
  - Fill `value_concepts` and `context_concepts` from the concepts appearing under the corresponding `"<-"` lines in the NormCode.
  - Use `working_interpretation` to encode **syntax/loop metadata** the orchestrator needs but which is implicit in the NormCode (e.g. loop base, current item, value ordering, conditions).

- **Step 5 – Decide how imperatives/judgements are realized**
  - For direct NormCode translation (e.g. `run_v1_manual.py`), `reference_data` for prompt concepts points at **prompt files**.
  - For imperative‑Python variants (e.g. `ex_add_complete_code.py`), additional ground concepts carry:
    - script locations (`nominalized_action_sum`, `nominalized_action_get_digit`, …)
    - prompt locations (`prompt_location_sum`, `prompt_location_get_digit`, …)
  - `working_interpretation["value_order"]` specifies the order in which these are passed to the body.

At the end of Step 5 you should have, on paper or in a design file:

- a **Concept list** (names, types, axes, ground/final flags, references), and
- an **Inference list** (one entry per NormCode line/block, with `inference_sequence`, `function_concept`, `value_concepts`, `context_concepts`, `flow_info`, and a carefully specified `working_interpretation`).

Only then do you translate that repository design into a `.py` file (see Section 4).

---

### 2. From NormCode tokens to `ConceptEntry` (Python side)

The basic rule is: **every NormCode concept that needs state in the orchestrator becomes a `ConceptEntry`** inside the `.py` script’s `concept_entries` list.

#### 2.1 Semantical object / statement / relation concepts

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

#### 2.2 Syntactical operator and functional concepts

- **Quantifying operator (`*every`)**
  - Example (addition): `*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]`, `*every({number pair}*1)%:[{number}]@(2)`, `*every({number pair}*1)%:[{number}]@(3)`.
  - Example (v1 manual): `*every([all {normcode draft}])`.
  - Implementation pattern:
    - A `ConceptEntry` with `type="*every"`, `concept_name` equal to the full textual operator.
    - Often `is_ground_concept=True` since the operator semantics are fixed.

- **Grouping operator (`&across`)**
  - Example: `&across({unit place value}:{number pair}*1)`, `&across({carry-over number}*1:{carry-over number}*1<--<!_>>)` and `&across({normcode draft})` in v1.
  - Implementation pattern:
    - `type="&across"`, `concept_name` equal to the operator string.
    - Grounded operator semantics (grouping) with optional `working_interpretation["syntax"]["by_axis_concepts"]`.

- **Specification / assigning operator (`$.`)**
  - Example: `$.({digit sum})`, `$.({remainder})`, `$.({single unit place value})`, `$.({number with last digit removed})`, `$.({normcode draft}<$={#}>)`, `$.([all {normcode draft}]*1)`, `$.({normcode draft})`, `$.({normcode draft}<$={4}>)`.
  - Implementation pattern:
    - `type="$.", concept_name="$.(...)"`, usually `is_ground_concept=True`.
    - These are used as `function_concept` in **assigning** inferences (the Assigning Agent’s Sequence) to specify and move values between concepts or from loop items into collectors.

- **Continuation operator (`$+`)**
  - Example: `$+({number pair to append}:{number pair})` in the addition example.
  - Implementation pattern:
    - `type="$+"`, `is_ground_concept=True`.
    - In `InferenceEntry.working_interpretation`, `"marker": "+", "assign_source": "{number pair to append}", "assign_destination": "{number pair}"`.

- **Imperative / judgement functional concepts (`::()`, `<{}>` in the examples)**
  - Imperative operations are represented as **distinct function concepts**, each with a stable textual name mirroring the NormCode imperative:
    - Addition: `::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)`.
    - Digit extraction: `::(get {2}?<$({unit place value})%_> of {1}<$({number})%_>)`.
    - Division helpers: `::(find the {1}?<$({quotient})%_> of {2}<$({digit sum})%_> divided by 10)`, `::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10)`.
    - Decomposition prompts in v1: a family of `::{%(direct)}<...>` functions for initialization, completion check, concept identification, question formulation, operator selection, children creation, normtext distribution, and draft update.
  - Judgement functional concepts are similar but given `type="<{}>"` in the addition example for zero checks:
    - `:%(True):<{1}<$({number})%_> is 0>`, `:%(True):<{1}<$({carry-over number})%_> is 0>`.
  - Implementation pattern:
    - `type` encodes the operator class (e.g. `"::({})"` or `"<{}>"`).
    - `is_ground_concept=True`, `is_invariant=True`.
    - `reference_data` is usually a **one‑element list containing the textual form**, with a matching `reference_axis_names` entry. This pins the meaning of the operator for the body.

- **Timing operators (`@if`, `@if!`, `@after`)**
  - Examples:
    - `@if!(<all number is 0>)`, `@if(<carry-over number is 0>)`, `@after({digit sum})`, `@after({number pair to append}<$={1}>)`.
    - In v1 manual: `@if(<current normcode draft is complete>)`, `@if!(<current normcode draft is complete>)`.
  - Implementation pattern:
    - `type="@if"`, `"@if!"`, or `"@after"`, `is_ground_concept=True`.
    - Used as `function_concept` in `timing` inferences, with `working_interpretation["syntax"]["marker"]` and `"condition"` mirroring the NormCode.

---

### 3. From NormCode inferences to `InferenceEntry` (Python side)

After the conceptual **inference list** is defined, **each NormCode inference line (or block) becomes one `InferenceEntry`** in the `.py` script’s `inference_entries` list. Together they form the `InferenceRepo`, mirroring the plan of inferences described in the NormCode Guide.

#### 3.1 Core fields

For both examples, the mapping is:

- **`inference_sequence`**  
  - Mirrors the **NormCode annotation** at the right of the line:
    - Addition: `"quantifying"`, `"assigning"`, `"grouping"`, `"imperative"`, `"judgement"`, `"timing"`, plus specialized `"imperative_python"`, `"imperative_python_indirect"`, `"judgement_python"`, `"judgement_python_indirect"`.
    - v1 manual: `"imperative_input"`, `"imperative_direct"`, `"judgement_direct"`, `"grouping"`, `"quantifying"`, `"assigning"`, `"timing"`.
  - This determines which **Agent's Sequence** (grouping, quantifying, assigning, imperative, judgement, timing) is used for that step, as described in the NormCode Guide.

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

`working_interpretation` encodes the **implicit syntax-level information** that is present in the NormCode but needs to be explicit for the orchestrator. It should be designed **before** you write any Python, as part of the repository specification:

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

In practice, you can think of `working_interpretation` as the **compact, JSON‑like representation of the NormCode line**, used by the Agent’s Sequence to understand:

- what kind of step this is (loop, grouping, assignment, imperative, judgement, timing), and  
- how to map **positions** like `{1}`, `{2}`, or `*1` in the NormCode into concrete `ConceptEntry` instances at run time.

#### 3.3 Working‑interpretation templates by agent’s sequence

Below are concrete patterns, distilled from the examples, that you can **reuse when designing `working_interpretation` in your repo specification and later copying it into your `.py` file**.

- **Quantifying (`inference_sequence='quantifying'`)**
  - **Purpose**: describe a `*every(...)` loop (loop base, current item, outputs).
  - **Typical shape (addition outer loop, `{new number pair}`)**:

    ```python
    working_interpretation={
        "syntax": {
            "marker": "every",
            "quantifier_index": 1,
            "LoopBaseConcept": "{number pair}",
            "CurrentLoopBaseConcept": "{number pair}*1",
            "group_base": "number pair",
            "InLoopConcept": {
                "{carry-over number}*1": 1,
            },
            "ConceptToInfer": ["{new number pair}"],
        }
    }
    ```

  - **How to adapt for a new loop**:
    - Set `"LoopBaseConcept"` to the collection concept in your NormCode (`[all {normcode draft}]`, `{items}`, etc.).
    - Set `"CurrentLoopBaseConcept"` to the `*1` version of that concept if you use identity markers.
    - Set `"group_base"` to a human‑readable base name (e.g. `"normcode draft"`, `"number"`).
    - Fill `"InLoopConcept"` with any loop‑scoped helper concepts (`{carry-over number}*1`, loop indices, etc.).
    - List the main output concepts in `"ConceptToInfer"`.

- **Grouping (`inference_sequence='grouping'`)**
  - **Purpose**: describe an `&across` (or `&in`) grouping operation.
  - **Simple case (`[all {unit place value} of numbers]` in addition)**:

    ```python
    working_interpretation={
        "syntax": {
            "marker": "across",
            "by_axis_concepts": "{number pair}*1"
        }
    }
    ```

  - **More complex case (carry‑over grouping)**:
    - The addition code uses a list for `"by_axis_concepts"` and a `"protect_axes"` list to keep certain axes untouched.
    - When grouping over multiple helper concepts, follow that pattern:
      - `"by_axis_concepts": [<helper operator concept>, <input concept>, <output concept>?]`
      - `"protect_axes": ["carry-over number"]` or similar to preserve identity axes.

- **Assigning (`inference_sequence='assigning'`)**
  - **Purpose**: describe a `$`‑family assigning step (`$.`, `$+`) that moves/updates data.
  - **Single‑source assignment (e.g. assign `{remainder}` into current loop result)**:

    ```python
    working_interpretation={
        "syntax": {
            "marker": ".",
            "assign_source": "{remainder}",
            "assign_destination": "*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]"
        }
    }
    ```

  - **Conditional assignment in a loop (v1 manual, `{normcode draft}<$={2}>`)**:
    - When there are multiple possible sources, use a list:

      ```python
      working_interpretation={
          "syntax": {
              "marker": ".",
              "assign_source": ["{normcode draft}<$={3}>", "{normcode draft}<$={2}>"],
              "assign_destination": "*every([all {normcode draft}])"
          }
      }
      ```

    - The Agent’s Sequence (and any timing inferences) decide which source is actually used for a given iteration.

  - **Append/continuation (`$+`)**:
    - For `$+({number pair to append}:{number pair})`, set:

      ```python
      working_interpretation={
          "syntax": {
              "marker": "+",
              "assign_source": "{number pair to append}",
              "assign_destination": "{number pair}",
              "by_axes": ["number pair"]
          }
      }
      ```

- **Timing (`inference_sequence='timing'`)**
  - **Purpose**: describe `@if`, `@if!`, `@after` control steps around another function.
  - **Pattern from both examples**:

    ```python
    working_interpretation={
        "syntax": {
            "marker": "if",    # or "if!" or "after"
            "condition": "<current normcode draft is complete>"  # or "<all number is 0>", "{digit sum}", etc.
        }
    }
    ```

  - Guidelines:
    - Use `"marker": "if"` for `@if`, `"if!"` for `@if!`, `"after"` for `@after`.
    - `"condition"` always names the **concept whose completion or truth value gates the step**:
      - A statement concept for `@if` / `@if!` (e.g. `<all number is 0>`).
      - An object concept for `@after` (e.g. `{digit sum}`, `{number pair to append}`).

- **Imperative / judgement (`inference_sequence` in the imperative/judgement family)**
  - **Purpose**: describe how to call the body (LLM/tool/script) for `::()` and `<{}>` functional concepts.
  - **Core fields (seen in both examples)**:
    - `"with_thinking": True` when the call may involve non‑trivial reasoning.
    - `"is_relation_output"`:
      - `True` if the output is a relation (e.g. `[{concept to decomposed} and {remaining normtext}]`).
      - `False` if the output is a single object/statement.
    - `"value_order"`:
      - Maps each concept name to the **position index** used in the NormCode imperative (`{1}`, `{2}`, `{3}`, …).
      - This is how `{1}`, `{2}` get bound to specific `ConceptEntry` references.
    - `"condition"` (judgement only):
      - e.g. `"condition": "True"` for zero‑checks in the addition example.

  - **Example: addition imperative for `{digit sum}`**:

    ```python
    working_interpretation={
        "is_relation_output": False,
        "with_thinking": True,
        "value_order": {
            "[all {unit place value} of numbers]": 1,
            "{carry-over number}*1": 2,
            "{sum}?": 3
        }
    }
    ```

  - **Example: v1 manual direct imperative (concept identification)**:
    - Adds `"prompt_location"` and sometimes `"value_selectors"`:

    ```python
    working_interpretation={
        "is_relation_output": True,
        "with_thinking": True,
        "prompt_location": "concept_identification_prompt",
        "value_order": {
            "{concept identification prompt}": 0,
            "[all {normcode draft}]*1": 1,
        }
    }
    ```

  - **When using relation outputs with internal structure**:
    - Use `"value_selectors"` to tell the body how to **extract sub‑parts** from a relation concept into separate arguments, as v1 manual does:

      ```python
      "value_selectors": {
          "[{concept to decomposed} and {remaining normtext}]_1": {
              "source_concept": "[{concept to decomposed} and {remaining normtext}]",
              "index": 0,
              "key": "concept to decomposed"
          },
          "[{concept to decomposed} and {remaining normtext}]_2": {
              "source_concept": "[{concept to decomposed} and {remaining normtext}]",
              "index": 0,
              "key": "remaining normtext"
          }
      }
      ```

    - This allows one relation to serve as a structured container, while still exposing named pieces to the Agent’s Sequence and body.

- **Imperative‑Python variants**
  - In `ex_add_complete_code.py`, the imperative entries use the same fields as above, but with **two extra concepts** in `value_concepts` (script location and prompt location) and corresponding indices in `"value_order"`.
  - When you generate Python scripts/prompts dynamically:
    - Reserve specific indices in `"value_order"` for:
      - `"nominalized_action_<op>"` (script path),
      - `"prompt_location_<op>"` (prompt path),
    - so the imperative Python Agent’s Sequence can reliably locate and call them.

---

### 4. Turning the repository design into a `.py` script

Once the **Concept list** and **Inference list** (with `working_interpretation`) are stable, turning them into a Python module and connecting it to the orchestrator is a mostly mechanical step.

- **4.1 Implement `create_repositories()`**

At the code level, the target pattern inside your `.py` file looks like:

```python
from infra._orchest._repo import ConceptEntry, InferenceEntry, ConceptRepo, InferenceRepo
import uuid

def create_repositories():
    concept_entries = [
        # One ConceptEntry per concept from your design
        ConceptEntry(
            id=str(uuid.uuid4()),
            concept_name="{number pair}",
            type="{}",
            axis_name="number pair",
            description="The collection of number pairs.",
            reference_data=[["%(123)", "%(98)"]],
            reference_axis_names=["number pair", "number"],
            is_ground_concept=True,
        ),
        # ...
    ]
    concept_repo = ConceptRepo(concept_entries)

    inference_entries = [
        # One InferenceEntry per NormCode line/block from your design
        InferenceEntry(
            id=str(uuid.uuid4()),
            inference_sequence='quantifying',
            concept_to_infer=concept_repo.get_concept('{new number pair}'),
            function_concept=concept_repo.get_concept('*every({number pair})%:[{number pair}]@(1)^[{carry-over number}<*1>]'),
            value_concepts=[concept_repo.get_concept('{number pair}')],
            context_concepts=[
                concept_repo.get_concept('{number pair}*1'),
                concept_repo.get_concept('{carry-over number}*1'),
            ],
            flow_info={'flow_index': '1'},
            working_interpretation={  # copy from your repo specification
                "syntax": {
                    "marker": "every",
                    "quantifier_index": 1,
                    "LoopBaseConcept": "{number pair}",
                    "CurrentLoopBaseConcept": "{number pair}*1",
                    "group_base": "number pair",
                    "InLoopConcept": {"{carry-over number}*1": 1},
                    "ConceptToInfer": ["{new number pair}"],
                }
            },
            start_without_value_only_once=True,
            start_without_function_only_once=True,
            start_without_support_reference_only_once=True
        ),
        # more InferenceEntry(...) instances
    ]
    inference_repo = InferenceRepo(inference_entries)

    return concept_repo, inference_repo
```

The key point is that **all of the design choices** (what concepts exist, how inferences are wired, how `working_interpretation` is structured) are made **before** this function is written; the function simply encodes that specification in Python.

- **4.2 Orchestrator entry point and JSON export**

After `create_repositories()` is in place, you should **always** provide a minimal way to run the repos through the orchestrator, following the pattern used in `ex_add_complete.py` and `run_v1_manual.py`.

At minimum, your module should do something like:

```python
from infra._orchest._orchestrator import Orchestrator
from infra._agent._body import Body  # if you use an LLM-backed body
import os
from pathlib import Path

if __name__ == "__main__":
    # 1. Build repositories from the design
    concept_repo, inference_repo = create_repositories()

    # 2. (Optional but common) construct a Body for imperatives/judgements
    body = Body(llm_name="qwen-plus")  # or whatever model/config you use

    # 3. Construct and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        body=body,            # may be omitted for pure non-LLM examples
        max_cycles=300,       # or a problem-specific bound
    )
    final_concepts = orchestrator.run()

    # 4. Inspect/log final concepts
    for final_concept_entry in final_concepts:
        if final_concept_entry and final_concept_entry.concept.reference:
            ref_tensor = final_concept_entry.concept.reference.tensor
            print(f"Final concept '{final_concept_entry.concept_name}': {ref_tensor}")
        else:
            print(f"No reference found for final concept '{final_concept_entry.concept_name}'.")
```

This is the same structure used in the provided examples:

- `ex_add_complete.py` builds repos, constructs an `Orchestrator`, runs it, logs/prints final concepts, and then validates results.
- `run_v1_manual.py` builds repos, constructs an `Orchestrator` with a `Body`, runs it, and prints/logs the final `{normcode draft}`.

In many cases, your entry point will also need to **prepare a small file‑system layout**, mirroring the examples:

- The addition examples (`ex_add_complete.py`, `ex_add_complete_code.py`) create `generated_scripts/` and `generated_prompts/` directories before running, because ground concepts reference files inside them.
- The v1 manual example (`run_v1_manual.py`) assumes a `prompts/` directory with named prompt files that match the `reference_data` paths used in the repository design.

So, as part of the runner, make sure any directories and files referenced in `reference_data` (prompt files, generated scripts, etc.) actually exist on disk before the orchestrator is started.

On top of this standard runner and file‑system setup, you may add small helper functions that walk `concept_repo` / `inference_repo` and dump them to `.json` for tooling or debugging, but the orchestrator entry point itself is part of the normal deliverable, not optional.

---

### 4. Imperative‑Python vs. direct NormCode execution (design choice in the `.py` file)

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

### 5. Practical checklist when authoring a new `.py` repo from NormCode

Given a new NormCode draft you want to run through the orchestrator:

- **1. List all symbols**
  - Enumerate every `{...}`, `[...]`, `<...>`, and each operator form (`*every(...)`, `&across(...)`, `$.(...)`, `$+`, `@if`, `@if!`, `@after`, `::(...)`, `::{%(direct)}<...>`, `:%(True):<...>`, etc.).

- **2. Design the Concept list (future `ConceptEntry`s)**
  - Decide which concepts are:
    - **Final concepts** (mark `is_final_concept=True` in the design).
    - **Ground concepts** (inputs, prompts, fixed carry, script/prompt locations, invariant operators). Plan their `reference_data` / `reference_axis_names`, using **nested lists** for multi‑axis structured data where appropriate.
    - **Intermediate concepts** (loop variables, temporary results, relation concepts inside decompositions).

- **3. Design the Inference list (future `InferenceEntry`s)**
  - For each NormCode inference block:
    - Choose `inference_sequence` to match the NormCode role and your orchestrator pipeline naming.
    - Decide `concept_to_infer`, `function_concept`, `value_concepts`, `context_concepts`.
    - Assign `flow_info['flow_index']` from the NormCode label for traceability.
    - Design `working_interpretation`:
      - Loop metadata for `*every` and `&across`.
      - Assignment markers for `$` / `$+`.
      - Conditions for `@if`, `@if!`, `@after`.
      - Prompt locations, value ordering, and any `value_selectors` for direct/indirect imperatives.

- **4. Implement `create_repositories()` in Python**
  - Translate the Concept and Inference lists into `ConceptEntry` and `InferenceEntry` instances inside a `create_repositories()` function as in Section 4.1.

- **5. Wire in the body and optional JSON export**
  - For direct LLM‑driven steps (like v1 manual), create prompt concepts whose `reference_data` are `"%{prompt}(...)"` pointing at your prompt files.
  - For Python‑indirect steps, follow the pattern from `ex_add_complete_code.py` with `nominalized_action_*` and `prompt_location_*` concepts plus appropriate `inference_sequence` variants.
  - Optionally, add orchestrator entry points and JSON export helpers.

Following this pattern, any well‑structured NormCode example can be turned into a **repository design** and then into a **Python repository script** that builds `ConceptRepo` and `InferenceRepo`. Those repositories can then be imported by the orchestrator, optionally exported to JSON, and executed while preserving the original NormCode plan’s structure and flow.


