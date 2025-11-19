# The NormCode AI Planning Pipeline

## Project Goal

The project goal is to bootstrap from a high-level natural language prompt into a structured and executable plan using a meta-algorithmic pipeline. This pipeline, itself powered by a NormCode plan, methodically transforms an instruction by:

1.  **Distilling** the user's intent into a clean instruction and registering all raw context.
2.  **Deconstruction** the instruction into a formal, hierarchical NormCode plan (`.ncd`).
3.  **Formalizing** the draft by applying redirection and serialization patterns to create a machine-readable NormCode script (`.nc`).
4.  **Assembling Prompts** by mapping granular context to each step and generating a full set of executable prompts.
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

2.  **Phase 2: Deconstruction into NormCode Plan**: Takes the clean `Instruction Block` and generates a semi-formal **NormCode Draft (`.ncd`)**. This draft captures the core logic and includes reasoning annotations. A human-readable **Natural Language NormCode (`.ncn`)** version is also created for easier review.

3.  **Phase 3: Plan Formalization and Redirection**: Refines the `.ncd` draft by first applying **Serialization** patterns to manage data flow, followed by **Redirection** patterns to link abstract concepts to concrete implementations. The refined plan is then formalized into a machine-readable script and an updated human-readable translation is generated.

4.  **Phase 4: Contextualization and Prompt Assembly**: Enriches the formalized plan by mapping each step to specific, granular context files from the `context_store`. This process generates a detailed **Context Manifest** (`.json`) that links prompts in the plan to their required context. Finally, it uses this manifest to generate a full set of prompt files, making the plan ready for materialization.

5.  **Phase 5: Materialization into an Executable Script**: Translates the final, formalized `.nc` plan and its associated prompts and context map into a runnable Python script, ready for execution by an `Orchestrator`.

This structured, phased approach ensures that a high-level, ambiguous instruction can be methodically transformed into a precise, executable, and context-aware plan.





# Combined Prompt and methodology

# File: 1.3.2.2---automated_instruction_distillation.md
---

### Step 1.1: Automated Instruction Distillation

The process begins by feeding the raw user prompt to an LLM guided by a specialized meta-prompt. This meta-prompt instructs the model to perform a sophisticated analysis, separating the core procedural instructions from all other contextual information.

The goal is to produce one key artifact:

1.  **Instruction Block:** This contains the clean, unambiguous, and procedural logic—the "what to do." It is synthesized from the core request in the user's prompt. This is a markdown file.

---
*From raw--prompt.md:*

#### **Example: Simple & Casual Request**

-   **Input (Raw Prompt):** `"hey can you just get me the latest sales report and email it to me and Sarah? sarah@example.com"`
-   **Output (Instruction Block):** `"Generate the latest sales report. Then, send an email with the report attached to analyst@example.com and sarah@example.com."`

#### **Example: Complex & Technical Request**

-   **Input (Raw Prompt):**
    ```markdown
    Okay, here's the workflow for deploying the new feature.
    1.  Run the migration script on the staging database.
    2.  If it succeeds, deploy the `feature-branch` to the staging environment.
    3.  Notify the #dev-ops channel on Slack with the results.
    
    Make sure the deployment only happens outside of peak hours (9am-5pm PST).
    ```
-   **Output (Instruction Block):**
    ```markdown
    Run the migration script on the staging database. If the migration is successful, deploy the feature-branch to the staging environment and send a Slack message to the #dev-ops channel with the results.
    ```


---
# File: 1.3.2.3---automated_context_registration.md
---

### Step 1.2: Automated Context Registration

Following the distillation of the instruction, the system identifies and registers all non-procedural information required for the plan. This "world knowledge" can come from various sources, including system context, constraints mentioned in the prompt, or a set of pre-existing authoritative documents.

The goal is to produce a structured and self-contained registration of this knowledge. This consists of two components:

1.  **`context_store` Directory:** A directory is created to hold copies of all raw, authoritative source documents (e.g., technical guides, original prompts, background information). This ensures the context is portable and complete.
2.  **Context Manifest File (e.g., `.json`):** A structured file that acts as a high-level summary and an index to the files in the `context_store`. It provides a machine-readable map of the available context.

---
*From Project Context:*

#### **Example: Registering Authoritative Documents**

In many cases, the context is not a small piece of information but a collection of detailed documents that provide foundational knowledge. The registration process involves identifying references to these documents within the user prompt or system context, and then creating a manifest that catalogs them.

-   **Input (User Prompt):** "Please execute the meta-pipeline as described in `prompt.md`. Use the `normcode_terminology_guide.md` for definitions and `file_formats_guide.md` for file specifications."

-   **LLM Process:** The model is instructed to analyze the prompt, identify all mentioned file references, and create a manifest that summarizes the purpose of each document and provides a file reference for the `context_store`.

-   **Output:**
    1.  The `context_store` is populated with copies of the referenced files (`raw--prompt.md`, `raw--context_normcode_terminology_guide.md`, etc.).
    2.  A **Context Manifest File** is generated:
    ```json
    {
      "summary": "This context block provides the high-level summary and references for the NormCode AI Planning Pipeline...",
      "sections": [
        {
          "title": "Core Methodology and Examples",
          "description": "A complete, practical walkthrough of this pipeline...is provided in raw--prompt.md.",
          "file_reference": "./context_store/raw--prompt.md"
        },
        {
          "title": "Technical Language Specification",
          "description": "The complete technical reference for the language...is detailed in raw--normcode_terminology_guide.md.",
          "file_reference": "./context_store/raw--normcode_terminology_guide.md"
        },
        {
          "title": "File Format Specifications",
          "description": "The specifications for the various file formats...are detailed in raw--file_formats_guide.md.",
          "file_reference": "./context_store/raw--file_formats_guide.md"
        }
      ]
    }
    ```


---
# File: 1.3.2.4---manual_review_of_distillation.md
---

### Step 1.3: Manual Review of Instruction and Context

**Objective:** To meticulously review and refine the outputs of the automated instruction distillation and context registration steps, ensuring they are accurate, complete, and logically sound before proceeding to the deconstruction phase.

**Procedure:**

1.  **Examine `1.1_instruction_block.md`:**
    *   **Clarity and Accuracy:** Verify that the distilled instruction is clear, unambiguous, and faithfully represents the core procedural intent of the original user prompt.
    *   **Completeness:** Ensure that all critical procedural steps from the original prompt have been captured. For example, a multi-step workflow should be fully represented.
    *   **Exclusion of Non-Procedural Information:** Confirm that conversational filler, metadata, and non-procedural constraints (e.g., "only happens outside of peak hours") have been correctly excluded from the instruction block. This information should be registered as context instead.
    *   **Corrections:** Edit the file directly to correct any misinterpretations, add necessary clarifications, or improve the logical flow.

2.  **Examine `1.2_initial_context_registerd.json`:** (This is a JSON file that contains the context manifest)
    *   **Manifest Completeness:** Confirm that all authoritative documents and key contextual details mentioned in the original prompt are registered in the JSON manifest.
    *   **File References:** Check that each `file_reference` points to the correct file within the `context_store` and that all referenced files exist.
    *   **Description Accuracy:** Ensure that the `title` and `description` for each entry accurately summarize the purpose and content of the referenced document.
    *   **Context Store Integrity:** Briefly check the `context_store` directory to ensure it contains copies of all the documents listed in the manifest.

**Outcome:** A validated and refined instruction block and context manifest that together provide a solid and accurate foundation for the subsequent deconstruction phase.


---
# File: 1.3.3.3---generate_natural_language_translation.md
---

### Step 2.2: Automated Natural Language Translation

**Objective:** To translate the annotated and structured `deconstruction_draft.ncd` into a clean, human-readable `natural_translation.ncn` format. This step makes the plan accessible for manual review by stripping away machine-focused annotations and presenting the core logic in plain language.

The translation is guided by the specifications in the `shared---file_formats_guide.md` and the full set of NormCode syntax and terminology guides.

---
### Example Walkthrough

This example shows how the formal, annotated deconstruction of "Phase 1" is translated into a clear, natural language summary.

**1. Input (`2.1_deconstruction_draft.ncd` snippet):**

This is the machine-focused draft, rich with annotations (`?:`, `/:`) that explain the AI's reasoning during the deconstruction process.

```normcode
<- {Phase 1: Confirmation of Instruction}
    ?: How is {Phase 1} specified?
    <= &across
        /: This phase is specified as a series of steps.
    <- {step 1.1: Automated Instruction Distillation}
        ...: 1.1. Given a raw user prompt and system context...
    <- {step 1.2: Automated Context Registration}
        ...: 1.2. Following the distillation of the instruction...
    <- {step 1.3: Manual Review of Confirmation}
        ...: 1.3. To meticulously review and refine the outputs...
```

**2. LLM Translation Process:**

An LLM parses the `.ncd` snippet, focusing on the core concepts (`{...}`) while ignoring the reasoning annotations (`?:`, `/:`) and unprocessed source text (`...:`). It then rephrases the hierarchical structure into a readable, indented list.

**3. Output (`2.2_natural_translation.ncn` snippet):**

This is the human-readable output, which preserves the plan's structure but presents its logic in clear, natural language.

```ncn
The first phase is Confirmation of Instruction.
    <= This phase is specified as a series of steps.
    <- The first step is Automated Instruction Distillation.
    <- The second step is Automated Context Registration.
    <- The third step is Manual Review of Confirmation.
```


---
# File: 1.3.4.2---automated_context_distribution.md
---

### Step 3.2: Automated Context Distribution

With a formalized plan, the system can now accurately distribute context. This process feeds two artifacts to an LLM guided by a specialized meta-prompt:

1.  The formalized **NormCode (`.nc`)** file from Phase 2.
2.  The **Initial Context Manifest (`.json`)** and its associated `context_store` directory from Phase 1.

The LLM's task is to act as a context-aware analyst. It parses the raw documents (e.g., `raw---prompt.txt`, `raw---system_context.json`) in the `context_store` and, for each inference in the `.nc` plan, creates new, tailored context files. These are saved back to the `context_store` with specific naming conventions:

-   `{flow_index}---{description}.txt`: For contexts specific to a single inference.
-   `shared---{description}.txt`: For contexts used by multiple inferences.

The primary outputs are these newly generated context files and the updated `3.2_context_manifest.json` that maps inferences to them.

---

### Example Walkthrough

To illustrate, consider a user registration plan.

**1. Inputs:**

-   **Formalized Plan (`.nc` snippet):**
    ```normcode
    1.output|:<:(::(register a new user))
    1.1.grouping| &across[{1},{2},{3}]
    1.2.object| {step 1: check existence}<:{1}>
    1.2.1.assigning| $::.<username exists>
    1.2.2.judgement| ::<username exists?>
    1.2.2.1.object| {user name}
    1.3.object| {step 2: report error}<:{2}>
    1.3.1.assigning| $::.{error}
    1.3.2.imperative| ::(report error)
    1.3.2.1.timing| @if(<username exists?>)
    1.4.object| {step 3: create account}<:{3}>
    1.4.1.assigning| $::.{new user account}
    1.4.2.imperative| ::(create new user account)
    1.4.2.1.timing| @if!(<username exists?>)
    ```

-   **Initial `context_store`:**
    ```
    context_store/
    ├── raw---prompt.txt
    └── raw---system_context.json
    ```

**2. LLM Analysis and Context Creation:**

The LLM processes each inference:

-   **For inference `1.1.1` (`::<username exists?>`):**
    -   It identifies the need for database details and the case-insensitivity requirement.
    -   It extracts "database type: PostgreSQL, user_table: 'users', username_column: 'username'" from `raw---system_context.json`.
    -   It extracts "username check should be case-insensitive" from `raw---prompt.txt`.
    -   It synthesizes this into a new file: `context_store/1.2.2---check_username_existence.txt`.

-   **Shared Context Identification:**
    -   The LLM notices that multiple steps will interact with the database.
    -   It creates a shared context file: `context_store/shared---database_connection.txt`, containing the PostgreSQL connection details. This avoids duplicating this information for every database-related step.

**3. Outputs:**

-   **Updated `context_store`:**
    ```
    context_store/
    ├── 1.2.2---check_username_existence.txt
    ├── raw---prompt.txt
    ├── raw---system_context.json
    └── shared---database_connection.txt
    ```

-   **Updated Context Manifest (`3.2_context_manifest.json` snippet):**
    ```json
    {
      "context_mapping": {
        "1.2.2.object| ::<username exists?>": [
          "./context_store/1.2.2---check_username_existence.txt",
          "./context_store/shared---database_connection.txt"
        ],
        // ... other mappings
      }
    }
    ```


---
# File: 1.3.3.4.---plan_formalization.md
---

### Step 2.3: Plan Formalization

**Objective:** To convert the annotated and semi-formal **NormCode Draft (`.ncd`)** into a clean, parsable **NormCode (`.nc`)** file. This is a critical preparatory step for context distribution and final script generation.

**Process:**

The formalization is an automated script that performs two key actions:

1.  **Stripping Annotations:** It removes all human-centric annotations (`?:`, `/:`, `...:`), which are essential for debugging the deconstruction but are noise for the execution engine.
2.  **Generating Flow Indices:** It walks the hierarchical structure of the plan and assigns a unique, dot-delimited `flow_index` (e.g., `1.3.2.2`) and an `agent sequence type` (e.g., `object`) to each line. This makes every single inference in the plan uniquely addressable.

---
### Example Walkthrough

This example shows how the annotated deconstruction of "Phase 1" is formalized into a machine-readable plan.

**1. Input (`2.1_deconstruction_draft.ncd` snippet):**

This is the version designed for human review, with questions, descriptions, and source text.

```normcode
<- {Phase 1: Confirmation of Instruction}
    ?: How is {Phase 1} specified?
    <= &across
        /: This phase is specified as a series of steps.
    <- {step 1.1: Automated Instruction Distillation}
    <- {step 1.2: Automated Context Registration}
    <- {step 1.3: Manual Review of Confirmation}
```

**2. Formalization Script:**

The script processes the `.ncd` file, stripping the annotations and adding the `flow_index` and `agent sequence type` to each line.

**3. Output (`2.3_deconstruction.nc` snippet):**

This is the final, parsable output. Every line is now uniquely identified and ready to be mapped to a specific context.

```normcode
1.3.2.object| {Phase 1: Confirmation of Instruction}<:{1}>
1.3.2.1.grouping| &across[{1}, {2}, {3}]
1.3.2.2.object| {step 1.1: Automated Instruction Distillation}<:{1}>
1.3.2.3.object| {step 1.2: Automated Context Registration}<:{2}>
1.3.2.4.object| {step 1.3: Manual Review of Confirmation}<:{3}>
```


---
# File: 1.3.3.5---manual_review_of_deconstruction.md
---

### Step 2.4: Manual Review of Deconstruction

**Objective:** Review and validate the logical structure of the NormCode plan generated from the instruction block.

**Procedure:**

1.  **Examine `2.1_deconstruction_draft.ncd`:**
    *   Trace the flow of inferences (`<-`) to ensure they logically connect.
    *   Review the annotations (`/:` and `?:`) to confirm that the reasoning behind the structure is sound.
    *   Verify that all requirements from the instruction block have been captured.

2.  **Examine `2.2_natural_translation.ncn`:**
    *   Read the plain-text version of the plan to ensure its intent is clear and matches the requirements.
    *   Use this file as a high-level guide to understanding the more formal `.ncd` file.

3.  **Examine `2.3_deconstruction.nc`:**
    *   Review the formalized plan to ensure it accurately reflects the structure of the `.ncd` and is ready for contextualization.

**Outcome:** A logically sound and validated plan structure, ready for the contextualization phase.


---
# File: 1.3.4.3---manual_review_of_contextualization.md
---

### Step 3.2: Manual Review of Contextualization

**Objective:** To meticulously validate the context mapping, ensuring every inference in the plan is linked to a set of precise, minimal, and sufficient context files, ready for the final script generation phase. This step is critical for refining the automated output and guaranteeing high-quality materialization.

**Procedure:**

1.  **Examine `3.2_context_manifest.json` for Correctness and Precision:**
    *   **No Raw Files**: The primary check is to confirm that **no inference maps directly to a `raw---*.md` guide**. All raw knowledge must be deconstructed into targeted `shared---*.md` or step-specific files. The presence of a `raw---` mapping indicates an incomplete contextualization.
    *   **Relevance Check**: For each inference (e.g., `"1.3.3.2.object| {step 2.1...}"`), review its list of mapped context files. Ask: "Is every file in this list strictly necessary for this specific step?" Remove any that are irrelevant.
    *   **Sufficiency Check**: Conversely, ask: "Is the provided context sufficient for this step to be executed without ambiguity?" As we saw with `step 2.2`, some steps may require additional context files (e.g., syntax guides) to be fully defined. Add any missing, relevant context files.

2.  **Examine the `context_store` for Quality:**
    *   **Review `shared---*.md` Files**: Open the shared context files. Verify that each one is focused on a single, coherent topic (e.g., `shared---normcode_core_syntax.md` should only contain syntax). If a file covers too many topics, it should be broken down further.
    *   **Review Step-Specific Files (`{index}---*.md`)**: Check any step-specific context files. Ensure they contain information that is genuinely unique to that step. If the content could apply to other steps, refactor it into a new shared file.

**Outcome:** A validated and refined context manifest where every inference is linked to the precise, necessary, and sufficient context it needs. This provides a solid and reliable foundation for the automated script generation in Phase 4.


---
# File: 1.3.5.2---automated_script_generation.md
---

### Step 4.1: Automated Script Generation

The core of this phase is an automated "NormCode-to-Python" compilation process, driven by an LLM guided by a specialized meta-prompt.

-   **Input:**
    1.  The formalized **NormCode (`.nc`)** file from Phase 3.
    2.  The **`context_store` directory** and **`context_manifest.json`** from Phase 3.

-   **LLM Process:** The LLM iterates through the `.nc` plan and its associated context to generate a Python script. For each concept and inference, it generates the corresponding `ConceptEntry` and `InferenceEntry` Python object.

    The most critical task in this step is synthesizing the `working_interpretation` for each `InferenceEntry`. The LLM combines the semantic meaning of the inference (from the `.nc` file) with its specific local context (from the `context_store`) to generate a precise set of instructions for the `Orchestrator`. This could be a direct tool call, a prompt for another LLM, or other structured commands.

-   **Output:**
    - **Repository JSON files (`concept_repo.json`, `inference_repo.json`):** These files contain the structured definitions for all `ConceptEntry` and `InferenceEntry` objects in the plan.
    - **An Executable Python Script (`.py`):** This script is now a lightweight runner. It contains the necessary boilerplate to load the repository JSON files, initialize the `Orchestrator`, and execute the plan.

---
*From raw_context_normcode_terminology_guide.txt:*

#\ NormCode Guide

## 1. Introduction

NormCode is a semi-formal language used to construct a **plan of inferences**. It is designed to represent complex reasoning and data processing tasks not as a single, monolithic script, but as a structured combination of multiple, distinct inferences. It is considered semi-formal because the concepts are not merely placeholders; their semantic meaning is important to the functioning of the NormCode, particularly when an inference's logic is executed by a language model.

Each **inference** within the plan is a self-contained logical operation. The entire Normcode script orchestrates how these individual inferences connect and flow to achieve a larger goal.

## 2. Core Syntax: Concepts, and Inferences

The fundamental unit of a Normcode plan is the **inference**. An inference is defined by a functional concept and its associated value concepts.

-   **Functional Concept (`<=`)**: This is the cornerstone of an inference. It "pins down" the inference by defining its core logic, function, or operation. Crucially, the functional concept is responsible for **invoking an agent's sequence** (e.g., `quantifying`, `imperative`), which is the underlying engine that executes the inference's logic.

-   **Value Concept (`<-`)**: This concept provides the concrete data for the inference. It specifies the inputs, outputs, parameters, or results that the functional concept operates on or produces.

The entire plan is represented in a hierarchical, vertical format. An inference begins with a root concept, followed by an indented functional concept (`<=`) that defines the operation. The value concepts (`<-`) are then supplied at the same or a more deeply nested level.

A line in Normcode can also have optional annotations for clarity and control:

`_concept_definition_ | _annotation_ // _comment_`

-   **`_concept_definition_`**: The core functional (`<=`) or value (`<-`) statement.
-   **`_annotation_`**: Optional metadata following the `|` symbol. This can be a **flow index** (e.g., `1.1.2`), an intended **data reference**, or the name of the invoked **agent's sequence**.
-   **`// _comment_`**: Human-readable comments.


**Example Structure of an Inference:**
```Normcode
_concept_to_infer_ // The overall goal of this inference
    <= _functional_concept_defining_the_operation_ | 
    quantifying // This invokes the 'quantifying' agent's sequence
    <- _input_value_concept_1_ // This is an input for the 
    operation
    <- _input_value_concept_2_
```

**Example of a Concrete Inference:**

The following snippet from an addition algorithm shows an `imperative` inference.

```Normcode
<- {digit sum} | 1.1.2. imperative
    <= ::(sum {1}<$([all {unit place value} of numbers])%_> and {2}<$({carry-over number}*1)%_> to get {3}?<$({sum})%_>)
    <- [all {unit place value} of numbers]<:{1}>
    <- {carry-over number}*1<:{2}>
    <- {sum}?<:{3}>
```
- **Goal**: The overall goal is to produce a `{digit sum}`.
- **Functional Concept (`<=`)**: The core of the inference is the `::` (imperative) concept, which defines a command to sum two numbers. This invokes the `imperative` agent's sequence.
- **Value Concepts (`<-`)**: It takes two inputs (`[all {unit place value} of numbers]` and `{carry-over number}*1`) and specifies one output (`{sum}`).

## 3. Concept Types

Concepts are the building blocks of NormCode and are divided into two major classes: **Semantical** and **Syntactical**. The core inference operators (`<=` and `<-`) are explained in the Core Syntax section above.

### 3.1. Semantical Concept Types

Semantical concepts define the core entities and logical constructs of the domain. They can be subdivided into typically non-functional and functional types.

#### 3.1.1. Typically Non-Functional Concept Types
These concepts represent entities, their relationships, or their roles in the inference.

| Symbol                | Name                      | Description                                                                 |
| --------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `{}`                  | Object                    | Represents a generic object or entity.                                      |
| `<>`                  | Statement                 | Represents a proposition or a state of affairs (non-functional).            |
| `[]`                  | Relation                  | Represents a relationship between two or more concepts.                     |
| `:S:`                 | Subject                   | Marks the subject of a relation or statement.                               |
| `:>:`                 | Input                     | A special type of Subject that marks a concept as an input parameter.       |
| `:<:`                 | Output                    | A special type of Subject that marks a concept as an output value.          |

**Examples:**
- **Object (`{}`):** `{new number pair}` declares a concept that will hold the state of the two numbers as they are processed.
- **Statement (`<>`):** `<all number is 0>` represents a condition that can be evaluated. The `judgement` agent's sequence will determine if this statement is true or false.
- **Relation (`[]`):** `[all {unit place value} of numbers]` defines a collection that will hold the digits from a specific place value of the numbers being added.

#### 3.1.2. Typically Functional Concept Types
These concepts define operations or evaluations that often initiate an inference.

| Symbol                | Name                      | Description                                                                 |
| --------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `({})` or `::()`      | Imperative                | Represents a command or an action to be executed.                           |
| `<{}>` or `<...>`     | Judgement                 | Represents an evaluation that results in a boolean-like assessment.         |

**Examples:**
- **Imperative (`::()`):** `::(get the {1}?<$({remainder})%_> of {2}<$({digit sum})%_> divided by 10)` issues a command to a tool or model to perform a calculation. This is the heart of an `imperative` inference.
- **Judgement (`<...>`):** `<= :%(True):<{1}<$({carry-over number})%_> is 0>` evaluates whether the carry-over is zero. This is the core of a `judgement` inference. Note the use of `<...>` as a common syntax variant for a judgement.

### 3.2. Syntactical Concept Types

Syntactical concepts are operators that control the logic, flow, and manipulation of data within the plan of inferences. They are grouped by their function.

#### 3.2.1. Assigning Operators

| Symbol | Name           | Description                                                        |
| ------ | -------------- | ------------------------------------------------------------------ |
| `$=`   | Identity     | Assigns a value to a concept, often used for state updates.          |
| `$.`   | Specification  | Specifies or isolates a particular property of a concept.          |
| `$%`   | Abstraction    | Creates a general template from a concrete instance for reuse.     |
| `$+`   | Continuation   | Appends or adds to a concept, often used in loops to update state. |

**Examples:**
- **Identity (`$=`):** `<- {number pair}<$={1}>` is used to give a stable identity (`1`) to the `{number pair}` concept across multiple steps of the algorithm.
- **Specification (`$.`):** `<= $.({remainder})` specifies that this part of the inference is focused solely on defining the `{remainder}`.
- **Abstraction (`$%`):** `<$([all {unit place value} of numbers])%_>` takes the concrete list of digits and abstracts it as an input parameter for the `sum` imperative.
- **Continuation (`$+`):** `<= $+({number pair to append}:{number pair})` defines an operation that updates the `{number pair}` for the next iteration of a loop.

#### 3.2.2. Timing (Sequencing) Operators

| Symbol     | Name      | Description                               |
| ---------- | --------- | ----------------------------------------- |
| `@if`      | If        | Executes if a condition is true.          |
| `@if!`     | If Not    | Executes if a condition is false.         |
| `@after`   | After     | Executes after a preceding step is complete. |

**Examples:**
- **If / If Not (`