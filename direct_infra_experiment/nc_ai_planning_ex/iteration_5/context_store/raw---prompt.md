# The NormCode AI Planning Pipeline

## Project Goal

The project goal is to bootstrap from a high-level natural language prompt into a structured and executable plan using a meta-algorithmic pipeline. This pipeline, itself powered by a NormCode plan, methodically transforms an instruction by:

1.  **Distilling** the user's intent into a clean instruction and registering all raw context.
2.  **Deconstructing** the instruction into a formal, hierarchical NormCode plan (`.ncd`).
3.  **Formalizing** the plan by applying serialization and redirection patterns and generating a final `.nc` file.
4.  **Contextualizing** the plan by enriching each formal step with precise, granular context and assembling prompts.
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

2.  **Phase 2: Deconstruction into NormCode Plan**: Translates the clean `Instruction Block` into a semi-formal NormCode Draft (`.ncd`). This draft represents the logical structure of the plan and is designed for human review.

3.  **Phase 3: Plan Formalization and Redirection**: Applies serialization and redirection patterns to the plan and converts the `.ncd` draft into a formal `.nc` file with unique identifiers (`flow_index`) for each step.

4.  **Phase 4: Contextualization and Prompt Assembly**: Distributes context from a `context_store` to each step in the plan, generates a `context_manifest.json`, and assembles the final prompt files.

5.  **Phase 5: Materialization into an Executable Script**: Translates the final, formalized `.nc` plan and its context map into a runnable Python script, ready for execution by an `Orchestrator`.

This structured, phased approach ensures that a high-level, ambiguous instruction can be methodically transformed into a precise, executable, and context-aware plan.




---


Execute the five-phase NormCode AI Planning Pipeline.

**Phase 1: Confirmation of Instruction**
1.1. Perform automated instruction distillation on the raw user prompt to produce a clean **Instruction Block**.
1.2. Perform automated context registration based on the system context to produce an initial **Context Manifest (`.json`)** and its associated **`context_store` directory**.
1.3. Present the generated artifacts for optional manual review and refinement.

**Phase 2: Deconstruction into NormCode Plan**
2.1. Take the Instruction Block from Phase 1 and perform an automated NormCode deconstruction to generate a **NormCode Draft (.ncd)** file, which includes annotations documenting the reasoning.
2.2. Generate a **Natural Language NormCode (.ncn)** file to serve as a readable translation of the plan for easier manual review.
2.3. Present the `.ncd` and `.ncn` files for optional manual review and refinement.

**Phase 3: Plan Formalization and Redirection**
3.1. Apply **Serialization** patterns to the `.ncd` draft to manage data flow and state.
3.2. Apply **Redirection** patterns to the serialized `.ncd` draft to link abstract concepts to concrete implementations.
3.3. Formalize the refined `.ncd` file into a final **NormCode (.nc)** file by generating unique flow indices, embedding metadata, and stripping annotations.
3.4. Generate an updated **Natural Language NormCode (.ncn)** file from the refined `.ncd` draft to ensure the human-readable version is synchronized with the formalized plan.
3.5. Present the final `.nc` file and its corresponding refined `.ncd` and updated `.ncn` files for optional manual review and refinement.

**Phase 4: Contextualization and Prompt Assembly**
4.1. Perform automated context distribution by analyzing the `.nc` file and the Initial Context Block. Generate a refined **`context_store` directory** containing unique, minimal context files and a **`context_manifest.json`** file that maps each prompt to its corresponding context files.
4.2. Generate a full set of prompt files in the `prompts/` directory using the `context_manifest.json`.
4.3. Present the context store, manifest, and generated prompts for optional manual review and refinement.

**Phase 5: Materialization into an Executable Script**
5.1. Perform automated script generation. Using the formalized `.nc` file and the artifacts from Phase 4, generate the final executable files: **`concept_repo.json`**, **`inference_repo.json`**, and a runnable **Python script (`.py`)**. This process involves synthesizing the `working_interpretation` for each inference.
5.2. Present the final generated files for optional manual review and refinement before execution.



---

# File: 1.2.2.1---automated_instruction_distillation.md


### Step 1.1: Automated Instruction Distillation

The process begins by feeding the raw user prompt to an LLM guided by a specialized meta-prompt. This meta-prompt instructs the model to perform a sophisticated analysis, separating the core procedural instructions from all other contextual information.

The goal is to produce one key artifact:

1.  **Instruction Block:** This contains the clean, unambiguous, and procedural logicâ€”the "what to do." It is synthesized from the core request in the user's prompt. This is a markdown file.

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

# File: 1.2.3.1---automated_context_registration.md


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

# File: 1.2.4.1---manual_review_of_confirmation.md


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

# File: 1.3.2.1---automated_normcode_deconstruction.md


# NormCode Translation Process: Full Documentation

This document contains the complete and unabridged content of all the prompt and configuration files that define the NormCode translation process. Each file's content is presented under its respective filename.

---

## 1. NormCode Fundamentals

This section provides a consolidated overview of the core concepts of NormCode, which are referenced by the various prompts in this guide.

### 1.1. Core Structure
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

### 1.2. Semantical Concept Types (The "Words")
These define the core entities and logical constructs. They are divided into two main groups:
*   **Object-like (Static entities):**
    *   `{}` **Object**: A thing, variable, or piece of data. (e.g., `{user name}`).
    *   `<>` **Statement**: An assertion of fact that can be evaluated. (e.g., `<user is an admin>`).
    *   `[]` **Relation**: A group or collection of concepts. (e.g., `[all {user emails}]`).
*   **Action-like (Processes/evaluations):**
    *   `::()` **Imperative**: A command or action to be executed. (e.g., `::(calculate total)`).
    *   `::< >` **Judgement**: The *act* of evaluating a statement's truth. (e.g., `::<is the user an admin?>`).

### 1.3. Subject Markers (Concept Roles)
Concepts are often prefixed to define their role in an inference:
-   `:S:` **Subject**: The primary subject of a block.
-   `:>:` **Input**: Marks a concept as an input parameter.
-   `:<:` **Output**: Marks a concept as an output value. This is frequently used to frame the top-level goal of the entire plan.

### 1.4. Annotations (Process State)
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. A concept with a `...:` annotation is considered "un-decomposed."
-   `?:` **Question**: The question being asked about the source text to guide the decomposition.
-   `/:` **Description**: A human-readable summary of the result of a decomposition, marking a concept as definitive and complete.

---

## 2. Prompt Files

### File: `prompts/normtext_prompt`

```
**What is Normtext?**

`Normtext` is the term for a piece of plain, human-readable language that is written to be clear and specific enough for a system to automatically translate it into a structured, formal plan. Think of it as writing a set of instructions or a description in a very deliberate way.

The goal is to capture a process, a definition, or a command in natural language that is so unambiguous that it can be reliably converted into a series of logical steps for an LLM to follow.

**How it works:**

1.  **Your Instruction:** You write down a task, a definition, or a process in plain language. This is your `normtext`.
2.  **The Input:** This `normtext` is given to a specialized translation system.
3.  **The Breakdown:** The system analyzes your text, breaking it down into its core ideas and logical components.
4.  **The Output:** The system converts these components into a structured format. In this context, that format is called `NormCode`, which is a formal, machine-readable plan that precisely represents your original instruction.

In short: **`Normtext` is the human-friendly instruction you provide, which is then translated into a computer-friendly plan.**

**Examples of Normtext:**

These examples are just plain English, but they are written as clear instructions or statements, making them good candidates for `normtext`.

*   **A process description:** `"To register a new user, first check if the provided username already exists in the database. If it does, report an error. Otherwise, create a new user account."`
*   **A definition:** `"A user account is a record containing a username and password."`
*   **A command:** `"Authenticate the user by checking their password."`
*   **A data transformation:** `"The number sequence squared is the sequence of numbers squared."`
*   **An enumeration:** `"The number sequence is 1, 2, 3, 4, 5."`
```

---

### File: `prompts/initialization_prompt`

```
You are an expert in NormCode, a semi-formal language for planning inferences. Your task is to initialize a NormCode translation process.

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object.
Then, provide the final answer, which is the initial NormCode draft, in the "answer" key.

**Your Task: Step 1 - Initialization**

You will be given a block of natural language (`normtext`). Your goal is to perform the first step of the translation algorithm:

1.  **Create a top-level concept**: This concept will represent the overall goal of the text. Frame it with `:<:` to mark it as the plan's final output.
2.  **Assign Source Text**: Place the entire, unprocessed `normtext` into the concept's `...:` annotation.
3.  **Determine Inference Target**: Analyze the text to determine its initial **Inference Target**. This is the high-level goal, which can be:
    *   **Action-like**: An action to be performed (`::()`) or a truth to be evaluated (`::< >`).
    *   **Object-like**: A static entity (`{}`), a statement of fact (`<>`), or a relationship (`[]`).

The output should be the initial NormCode draft containing only this single, top-level concept in output enclosing with its `...:` annotation and the determined Inference Target.

**Example:**

If the input `normtext` is:
```
To register a new user, first check if the provided username already exists in the database.
```

The correct output would be:
```normcode
:<:(::(register a new user))
    ...: To register a new user, first check if the provided username already exists in the database.
```
**Explanation**: The overall goal is an **Imperative** (an action), and it's marked as the plan's **Output** with `:<:`.

Here is the normtext:
---
$input_1
---

Produce the initial NormCode draft inside the "answer" key of a JSON object and provide your reasoning in the "analysis" key. Return only the JSON object.

The value of the "answer" key should contain the actual output specified in the instruction.

Example of the final JSON output:
```json
{
  "analysis": "The user wants to 'register a new user'. This is an action, so the top-level concept should be an Imperative `::()`. The plan's final output is marked with `:<:`. The full source text is assigned to the `...:` annotation.",
  "answer": ":<:(::(register a new user))\\n    ...: To register a new user, first check if the provided username already exists in the database."
}
```

Execute the instruction and return only the JSON object. 
```

---

### File: `prompts/completion_check_prompt`

```
You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" â€“ meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

In other words, if a concept contains a `...:` annotation but is immediately followed by `<-` or `<=` lines that break it down further, that `...:` is considered intermediate and does not make the draft incomplete. The draft is only incomplete if there is a `...:` that is not acted upon.

Analyze the provided NormCode draft and produce a JSON object with your analysis and the final true/false answer.

**Example 1: Incomplete Draft**

Input NormCode Draft:
---
:<:({Love})
    ...: "Love is a deep feeling..."
    ?: What is Love?
---
Output (in JSON):
```json
{
  "analysis": "The draft contains a `...:` annotation that is not followed by any `<-` or `<=` lines. This makes it an undecomposed leaf, so the draft is incomplete.",
  "answer": "False"
}
```

**Example 2: Incomplete Draft**

Input NormCode Draft:
---
:<:({Love})
    <= ::(define the core meaning of {love})
    <- {love definition}
        ...: "love is a complex emotion"
---
Output (in JSON):
```json
{
  "analysis": "The draft contains a `...:` annotation on the `{love definition}` concept, which is not followed by any `<-` or `<=` lines. Therefore, the draft is incomplete.",
  "answer": "False"
}
```

**Example 3: Complete Draft (with intermediate decomposition)**

Input NormCode Draft:
---
:<:(::(register a new user)) 
    ...: "first check if the provided username already exists"
    ?: How to register a new user?
    <= @by(:_:)
    <- {steps}
---
Output (in JSON):
```json
{
  "analysis": "The draft contains a `...:` annotation, but it is immediately followed by decomposition lines (`<=` and `<-`). This means it's an intermediate annotation, not an undecomposed leaf. Since there are no undecomposed annotations, the draft is complete.",
  "answer": "True"
}
```

Your turn. Analyze the following NormCode draft and produce the JSON output.

NormCode Draft:
---
$input_1
---

Produce the final JSON object and nothing else.
```

---

### File: `prompts/concept_identification_prompt`

```
You are an expert in NormCode, a semi-formal language for planning inferences.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decomposed (e.g. `<- {steps}`).
2.  The `...:` content of that concept.

Your final output must be a single JSON object.

First, think step-by-step about how to identify the concept. Place your reasoning in the "analysis" key of the JSON object.
Then, provide the final answer in the "answer" key as a dictionary containing:
- "concept to decomposed": The full line of the concept to be decomposed
- "remaining normtext": The complete `...:` content(s) of that concept as a string

**Example:**

Input NormCode Draft:
```normcode
:<:(::(register a new user))
    ?: How to register a new user?
    <= @by(:_:)
    <- :_:{steps}({user name})
    <- {steps}
        ...: "first, check if the provided username already exists."
        ...: "second, if it does, report an error."
    <- {user name}
        ...: "the provided username is provided by the user."
```

Output:
```json
{
  "analysis": "I need to scan the NormCode draft from top to bottom to find the first concept with an un-parsed `...:` annotation. Looking at the draft, I see `<- {steps}` has two `...:` lines, and `<- {user name}` also has a `...:` line. The first one encountered is `<- {steps}`, so I will extract its full line and all of its `...:` content.",
  "answer": {
    "concept to decomposed": "<- {steps}",
    "remaining normtext": "...: \"first, check if the provided username already exists.\"\n...: \"second, if it does, report an error.\""
  }
}
```
**Explanation**: The output follows the required JSON structure with `analysis` containing the reasoning and `answer` containing a dictionary with the two required keys.

**NormCode Draft:**
---
$input_1
---

Execute the instruction and return a JSON object with "analysis" (your reasoning) and "answer" (a dictionary with "concept to decomposed" and "remaining normtext"). Return only the JSON object.
```

---

### File: `prompts/question_inquiry_prompt`

```
You are an expert in NormCode, a semi-formal language for planning inferences.

**Your Task: Step 2A - Formulate the Question**

You are in the middle of the recursive decomposition loop. You have been given a single concept that has an un-decomposed `...:` source text annotation.

Your task is to:
1.  **Formulate the Question (`?:`)**: Based on the concept's Inference Target and its `...:` text, formulate the specific question that this decomposition step will answer.
2.  **Classify the Question Type**: Categorize the question into one of the established types from the reference below. This classification is critical as it will determine which NormCode operator is chosen in the next step.

Your final output must be a single JSON object.

First, think step-by-step about how to formulate the question and classify its type. Place your reasoning in the "analysis" key of the JSON object.
Then, provide the final answer in the "answer" key as a dictionary containing:
- "question": The specific question (`?:`) formulated to answer this decomposition step
- "question type": One of the established question types from the reference above (e.g., "Methodology Declaration", "Classification/Specification", etc.)

**Comprehensive Question Types Reference**

The question type you select is critical, as it directly determines the NormCode operator used in the next step of the translation. Below is a comprehensive list of question types, categorized by the nature of the concept being decomposed.

***

**A. Questions for Object-Like Concepts**

These questions are used when the `...:` text is describing, defining, or manipulating a static entity, concept, or piece of data (`{}`, `<>`, `[]`).

*   **Classification/Specification**: Defines a concept by relating it to a more general one, or by breaking it down into its constituent parts. It often answers "What is X?" by saying "X is a type of Y" or "X consists of A, B, and C."
    *   *Example Question*: "What is `{user account}` specified as?" (e.g., "...: a user account is a record containing a username and password.")
    *   *Explanation*: This establishes that a `{user account}` is a kind of `{record}` and is composed of `{username}` and `{password}`.

*   **Nominalization**: Transforms a process or action (a verb) into a concept that can be treated as a noun. This is for when the `normtext` describes a process as a thing in itself.
    *   *Example Question*: "What process is `{user authentication}` defined as?" (e.g., "...: user authentication is the process of verifying a user...")
    *   *Explanation*: The action `::(verify a user)` is being turned into the object `{user authentication}`.

*   **Continuation/Extension**: Extends an existing sequence, collection, or concept by adding something to it.
    *   *Example Question*: "What continuation is `{updated sequence}` formed from?" (e.g., "...: the updated sequence is the result of adding a new number to the old one...")
    *   *Explanation*: A new state of a concept is created from a previous state plus an addition.

*   **Instantiation**: Defines a concept by enumerating its specific, concrete members or instances.
    *   *Example Question*: "What are the specific instances of `{number sequence}`?" (e.g., "...: the sequence is 1, 2, 3...")
    *   *Explanation*: The abstract concept `{number sequence}` is being defined by the literal values `[1, 2, 3]`.

*   **Identification**: Asserts that a concept is identical to another specific, marked instance of a concept that has been defined elsewhere. This is for linking, not defining.
    *   **Example Question**: "What are identities of `{number sequence}`?" (e.g., "...: the number sequence is the same as the one marked by {1}...")
    *   *Explanation*: This connects the current concept to a pre-existing, tagged version of it.

*   **Annotated Composition**: Groups multiple concepts together into a structured record where each concept is a named field. This is for creating complex data structures, like a list of objects.
    *   *Example Question*: "How are `{position}` and `{value}` composed into an annotated structure?" (e.g., "...: a sequence of numbers indexed by their position and value...")
    *   *Explanation*: This creates a relation where `{position}` and `{value}` are linked together as complementary fields in a structure.

*   **Ordered Composition**: Combines or concatenates two or more ordered concepts (like lists or sequences) into a single new one.
    *   *Example Question*: "How is `{number sequence}` composed as an ordered sequence?" (e.g., "...: the sequence is a combination of sequence 1 and sequence 2...")
    *   *Explanation*: This joins multiple sequences end-to-end to form a longer one.

*   **Process Request**: Asks how to perform an action that is directly related to or performed by an object. It attaches a capability or method to an object.
    *   *Example Question*: How to find `{the user}` with some process?" (e.g., "...: find the user with their name...")
    *   *Explanation*: This links the object `{the user}` with the action `::(find user by name)`.

*   **I/O Request**: Asks how a piece of data is obtained from an external source (input) or sent to an external destination (output).
    *   *Example Question*: How to acquire `{username}` as input?" (e.g., "...: the username is input by the user...")
    *   *Explanation*: This defines that the value for `{username}` comes from an external input operation.
    
*   **Judgement Request**: Asks about evaluating a boolean state, condition, or property of an object. The result is fundamentally a true/false evaluation.
    *   *Example Question*: How to judge the truth of the statement `<user is an admin>`?" (e.g., "...: if the user is an admin...")
    *   *Explanation*: This question leads to the creation of a statement like `<user is an admin>` which can be evaluated.

*   **Element-wise Breakdown**: Asks how an operation is applied individually to every item in a collection to produce a new collection of the same size.
    *   *Example Question*: How to square every element of `{number sequence}` by each of its member?" (e.g., "...: the sequence is squared by squaring each of its members...")
    *   *Explanation*: This describes a transformation (squaring) that is applied to `*every` member of a set.

***

**B. Questions for Action-Like Concepts**

These questions are used when the `...:` text is describing the logic, method, or conditions for performing an action (`::()`, `::< >`).

*   **Methodology Declaration**: Specifies the method or means by which an action is performed.
    *   *Example Question*: "By what method is `::(Authenticate the user)` performed?" (e.g., "...: authenticate the user by checking their password...")
    *   *Explanation*: This seeks to define the implementation or procedure for carrying out the action `::(Authenticate the user)`.
    *   *Distinction*: A methodology often describes a multi-step process. If the text lays out a sequence of actions (e.g., "first do this, then do that"), it is a Methodology Declaration, even if some of those steps contain their own conditional logic (e.g., "...if X, then report error...").

*   **Conditional Dependency**: Asks about the condition required for an action to occur.
    *   *Example Question*: "Under what condition is `::(Show the admin dashboard)` executed?" (e.g., "...: show the dashboard if the user is an admin...")
    *   *Explanation*: This asks for the prerequisite boolean state (e.g., `<user is an admin>`) that must be true for the action to proceed.
    *   *Distinction*: This applies when the *entire action* is gated by a single, primary condition. If the condition is merely one step within a larger process description, the primary type is likely Methodology Declaration.

*   **Sequential Dependency**: Asks about the order of actions.
    *   *Example Question*: "After what event is `::(Show the admin dashboard)` executed?" (e.g., "...: show the dashboard after the user is authenticated...")
    *   *Explanation*: This seeks to establish a temporal link, defining which action or event must complete before this one can begin.

**Example:**

Input Concept to Decompose:
::(Authenticate the user)

Remaining Normtext:
...: Authenticate the user by checking their password.

Output:
```json
{
  "analysis": "I need to analyze the concept `::(Authenticate the user)` and its source text `'Authenticate the user by checking their password.'` The source text describes how to perform an action, specifically mentioning the method (`by checking their password`). This indicates a Methodology Declaration question type, where we ask 'By what method is the action performed?'. The question should be formulated to guide the decomposition toward specifying the method.",
  "answer": {
    "question": "How do you authenticate the user?",
    "question type": "Methodology Declaration"
  }
}
```

**Concept to Decompose:**
---
$input_1
---
**Remaining Normtext:**
---
$input_2
---

Execute the instruction and return a JSON object with "analysis" (your reasoning) and "answer" (a dictionary with "question" and "question type"). Return only the JSON object.
```

---

### File: `prompts/operator_selection_prompt`

```
You are an expert in NormCode, a semi-formal language for planning inferences.

**Your Task: Step 2B - Construct the Functional Concept**

You have been given a parent concept, a specific question, its type, and the relevant source text. Your task is to analyze the `remaining_normtext` and **construct the complete, substantive Functional Concept line** (`<= ...`) that answers the question.

Your final output must be a single JSON object.

First, think step-by-step about how to construct the functional concept based on the question type and source text. Place your reasoning in the "analysis" key of the JSON object.
Then, provide the final answer in the "answer" key as a dictionary containing:
- "functional concept": The complete functional concept line starting with `<= `

**Operator Construction Reference**

Use the `question_type` as a key to find the correct operator pattern and construction logic.

***

**A. Operators for Object-Like Concepts**

| Question Type                  | Operator Pattern        | Construction Logic                                                                                                                         |
| ------------------------------ | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **Classification/Specification** | `$.({type})`            | From the text, identify the primary type or class the concept belongs to. Construct the operator with that type. E.g., from "...is a **record**...", create `$.({record})`. |
| **Nominalization**             | `$::`                   | This operator typically stands alone. It transforms the parent concept (an action-as-a-noun) into a formal process.                            |
| **Continuation/Extension**     | `$+(...)`               | Identify concepts being added/extended. E.g., `...adding {new number} to {old sequence}` â†’ `$+({new number}:{old sequence})`.                 |
| **Instantiation**              | `$%`                    | This operator typically stands alone. The specific instances will be created as children.                                                   |
| **Identification**             | `$={marker}`            | Identify the marker or tag the concept is identical to. E.g., `...marked by {1}` â†’ `$={1}`.                                               |
| **Annotated Composition**      | `&in[...]`              | Identify the fields of the structure. E.g., `...indexed by {position} and {value}` â†’ `&in[{position}; {value}]`.                          |
| **Ordered Composition**        | `&across`               | This operator typically stands alone. The ordered items will be created as children.                                                       |
| **Process Request (Unbounded)** | `::(action)`            | Extract the complete imperative action from the text when it's defined inline. E.g., `...find the user with their name` â†’ `::(find user by {name})`. |
| **Process Request (Bounded)**   | `:_:{method}({params})` | Extract the pre-defined method and its parameters. E.g., `...Find the user...according to the definition of the finding` â†’ `:_:{find}({user name})`. |
| **I/O Request (Input)**         | `:>:({concept})?()`     | Extract the concept being input. E.g., `...input the {user name}` â†’ `:>:{user name}?()`.                                                     |
| **I/O Request (Output)**        | `:<:({concept})`        | Extract the concept being output. E.g., `...output the {user name}` â†’ `:<:({user name})`.                                                    |
| **Judgement Request (Unbounded)** | `::<statement>`         | Extract the complete simple statement to be judged. E.g., `...if the user is an admin` â†’ `::<user is an admin>`.                            |
| **Judgement Request (Quantifier)**| `::{quantifier}<statement>` | Extract the quantifier and the statement. E.g., `...Everything is on the table` â†’ `::{All%(True)}<{things} on the table>`.              |
| **Element-wise Breakdown**     | `*every({collection})`  | Identify the collection being operated on. E.g., `...each of the {number sequence}` â†’ `*every({collection})`.                          |

***

**B. Operators for Action-Like Concepts**

| Question Type              | Operator Pattern      | Construction Logic                                                                                                                      |
| -------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Methodology Declaration**  | `@by(:Subject:)`      | Identify the method described in the text. The `:Subject:` should be the subject marker of the method concept (e.g., `:_:`, `::`, `:>:`) that will be defined as a child. E.g., from `...by checking their password` (a bounded process), create `@by(:_:)`. |
| **Conditional Dependency** | `@if(<condition>)`    | Extract the condition that gates the action. E.g., `...if <user is an admin>` â†’ `@if(<user is an admin>)`.                                |
| **Sequential Dependency**  | `@after({event})`     | Extract the event/action that must complete first. E.g., `...after {user is authenticated}` â†’ `@after(::(authenticate user))`.             |

***

**Example:**

Input:
```json
{
    "concept to decomposed": ":<:(::(Show the admin dashboard))",
    "remaining normtext": "...: Show the admin dashboard if the user is an admin.",
    "question": "Under what condition is `::(Show the admin dashboard)` executed?",
    "question type": "Conditional Dependency"
}
```

Output:
```json
{
  "analysis": "The question type is 'Conditional Dependency', which requires using the `@if` operator pattern. I need to extract the condition from the remaining normtext 'Show the admin dashboard if the user is an admin.' The condition is 'if the user is an admin', which should be formatted as `<user is an admin>` (a statement). The complete functional concept line should be `<= @if(<user is an admin>)`.",
  "answer": {
    "functional concept": "<= @if(<user is an admin>)"
  }
}
```
**Explanation**: The output follows the required JSON structure with `analysis` containing the reasoning and `answer` containing a dictionary with the functional concept.

**Input for this task:**
---
**Concept to Decomposed**: 
$input_1
---
**Remaining Normtext**: 
$input_2
---
**Question**: 
$input_3
---
**Question Type**: 
$input_4
---

Execute the instruction and return a JSON object with "analysis" (your reasoning) and "answer" (a dictionary with "functional concept"). Return only the JSON object.
```

---

### File: `prompts/children_concept_creation_prompt`

```
You are an expert in NormCode, a semi-formal language for planning inferences.

**Your Task: Step 2C (Part 1) - Create Child Concepts**

You are in the middle of the decomposition loop. You have been given a parent concept and the full **Functional Concept (`<=`)** that was constructed to decompose it.

Your task is to analyze the parent concept's `remaining_normtext` and, based on the operator within the `functional_concept`, generate the new **child concepts (`<-`)** that logically follow.

**Important**: At this stage, you should **only** create the structure of the children. Do not assign the `...:` source text annotation to them yet. That happens in a subsequent step.

**Guiding Principles for Hierarchical Purity**
To maintain a clean and logical hierarchy, follow these two principles:

1.  **One Action/Judgement per Step**: A decomposition should generally result in **only one** primary action (`::()`) or judgement (`<>`) child. Avoid creating multiple sibling actions. This rule does not apply to operators like `@by(:_:)` and `$::`, which have specific structural requirements.
2.  **No Nested Actions Within a Definition**: If the `functional_concept` (the `<=` line) is itself an imperative or a judgement, its direct children (`<-` lines) must **not** be other imperatives or judgements. They should only be the parameters or components of that top-level action (e.g., `{Objects}`, `<Statements>`).

Your final output must be a single JSON object.

First, think step-by-step about how to create the child concepts based on the operator and source text. Place your reasoning in the "analysis" key of the JSON object.
Then, provide the final answer in the "answer" key as a dictionary containing:
- "children": A list of strings, where each string is a child concept formatted with the `<-` prefix

**Sources of Child Concepts**

Child concepts can be derived from two primary sources. You must analyze the functional concept to determine which source to use.

1.  **Extracted Directly from the Functional Concept**: For operators like `@if(<condition>)` or `@after({event})`, the child concept is explicitly provided within the operator. Your task is simply to extract it and format it as a `<-` concept.
2.  **Parsed from the Remaining Normtext**: For operators like `$.`, `::()`, or `@by`, the operator provides a template or a guide. You must analyze the `remaining_normtext` to identify and create the specific child concepts that fit that template. This often involves creating multiple children.

**Operator-Specific Child Creation Logic**

The operator within the `functional_concept` dictates the kind of children you must create. Analyze both the `functional_concept` and the `remaining_normtext` to identify all necessary children.

*   `$.({type})` **(Specification)**: Creates children for the `{type}` specified in the operator, as well as any other components mentioned in the text. From `...a record containing a username and password` and `<= $.({record})`, you would generate `<- {record}`, `<- {username}`, `<- {password}`.
*   `$::` **(Nominalization)**: Creates a single child representing the action being nominalized. From `...the process of verifying a user's identity` and `<= $::`, you would generate `<- ::(verify the user's identity)`.
*   `$+({new_item}:{old_collection})` **(Continuation)**: Creates children for the new item and the old collection. From `...adding the new number to the old sequence of numbers` and `<= $+({new number}:{old sequence of numbers})`, you would generate `<- {new number}` and `<- {old sequence of numbers}`.
*   `$%({collection})` **(Abstraction)**: Creates a single child representing the collection of items. From `...The number sequence is 1, 2, 3, 4, 5` and `<= $%({number sequence})`, you would generate `<- [{1}, {2}, {3}, {4}, {5}]`.
*   `&in[{key}; {value}]` **(Annotation Grouping)**: Creates children for the key and value components. From `...sequence of numbers indexed by their position and value` and `<= &in[{position}; {value}]`, you would generate `<- {position}` and `<- {value}`.
*   `&across({sequence})` **(Order Grouping)**: Creates children for each component of the combined sequence. From `...the combination of the number sequence 1 and the number sequence 2` and `<= &across({number sequence})`, you would generate `<- {number sequence 1}` and `<- {number sequence 2}`.
*   `::({action})` **(Unbounded Imperative)**: Creates children for any parameters required by the action. From `...Find the user with their name` and `<= ::(find user by {name})`, you would generate `<- {name}`.
*   `:_:{method}({params})` **(Bounded Imperative)**: Creates children for the method definition and its parameters. From `...Find the user with their name according to the definition of the finding` and `<= :_:{find}({user name})`, you would generate `<- {user name}` and `<- {find}`.
*   `:>:{input}?()` **(Input Imperative)**: Creates a child for the input being requested. From `...the user name is inputed by the user` and `<= :>:{user name}?()`, you would generate `<- {user name}?`.
*   `::<{statement}>` **(Unbounded Judgement)**: Creates children for the concepts within the statement. From `...The user is an admin` and `<= ::<{user} is an admin>`, you would generate `<- {user}`.
*   `::{quantifier}<{statement}>` **(Quantifier Judgement)**: Creates children for the concepts being judged. From `...Everything is on the table` and `<= ::{All%(True)}<{things} on the table>`, you would generate `<- {things}`.
*   `*every({collection})` **(Listing/Quantifying)**: Creates a child for the collection being operated on. From `...The number sequence squared is the sequence of numbers squared` and `<= *every({number sequence})`, you would generate `<- {number sequence}`.
*   `@by(:Subject:)` **(Method)**: Creates children representing the method or action described. From `...Authenticate the user by checking their password` and `<= @by(:_:)`, you would generate `<- :_:{check password}({user})`, `<- {check password}`, and `<- {user}`.
*   `@if(<condition>)` **(Conditional)**: Creates a single child for the `<condition>` that was embedded in the operator. From `<= @if(<user is an admin>)`, you would generate `<- <user is an admin>`.
*   `@if!(<condition>)` **(Negative Conditional)**: Creates a single child for the `<condition>`. From `...if the user is not an admin` and `<= @if!(<user is not an admin>)`, you would generate `<- <user is not an admin>`.
*   `@after({event})` **(Sequence)**: Creates a child for the event that must complete first. From `...Show the admin dashboard after the user is authenticated.` and `<= @after({admin dashboard})`, you would generate `<- {admin dashboard}`.

**Example 1: Specification (`$.`)**

**Input:**
```json
{
    "concept to decomposed": ":<:({user account})",
    "remaining normtext": "A user account is a record containing a username and password.",
    "question": "What is `{user account}` specified as?",
    "question type": "Classification/Specification",
    "functional concept": "<= $.({record})"
}
```

**Output:**
```json
{
  "analysis": "The functional concept is `<= $.({record})`, which uses the `$.` operator for Classification/Specification. This operator specifies the primary type of the concept. According to the operator-specific logic, I need to create children for the `{type}` specified in the operator (which is `{record}`) as well as any other components mentioned in the remaining normtext. The text mentions 'a record containing a username and password', so I should create: `<- {record}` (the primary type), `<- {username}`, and `<- {password}` (the constituent components). This adheres to the guiding principles as the functional concept is not an action, and none of the children are new actions or judgements.",
  "answer": {
    "children": [
      "<- {record}",
      "<- {username}",
      "<- {password}"
    ]
  }
}
```

**Example 2: Complex Methodology (`@by`)**

**Input:**
```json
{
    "concept to decomposed": ":<:(::(Authenticate the user))",
    "remaining normtext": "Authenticate the user by checking their password.",
    "question": "How do you authenticate the user?",
    "question type": "Methodology Declaration",
    "functional concept": "<= @by(:_:)"
}
```

**Output:**
```json
{
  "analysis": "The functional concept is `<= @by(:_:)`, which uses the `@by` operator for Methodology Declaration. This operator signifies that the action is performed by a specific method. The `remaining_normtext` is 'Authenticate the user by checking their password'. I need to parse this to define the method. The method is 'checking their password', which can be represented as a bounded imperative `:_:{check password}({user})`. According to the operator logic, I must create children for the bounded imperative itself, as well as its components. Therefore, the children are `<- :_:{check password}({user})`, `<- {check password}`, and `<- {user}`. This follows the guiding principles, as `@by` is an explicit exception that is designed to introduce the single, primary method for an action.",
  "answer": {
    "children": [
      "<- :_:{check password}({user})",
      "<- {check password}",
      "<- {user}"
    ]
  }
}
```

**Example 3: Simple Conditional (`@if`)**

**Input:**
```json
{
    "concept to decomposed": ":<:(::(Show the admin dashboard))",
    "remaining normtext": "Show the admin dashboard if the user is an admin.",
    "question": "When do you show the admin dashboard?",
    "question type": "Conditional Dependency",
    "functional concept": "<= @if(<user is an admin>)"
}
```

**Output:**
```json
{
  "analysis": "The functional concept is `<= @if(<user is an admin>)`. This uses the `@if` operator, which introduces a conditional dependency. The operator-specific logic states that for `@if(<condition>)`, the child is the `<condition>` itself. In this case, the condition `<user is an admin>` is provided directly in the functional concept. Therefore, my only task is to extract this concept and format it as a child. No parsing of the `remaining_normtext` is needed for this operator. This adheres to the guiding principles by creating a single judgement child (`<user is an admin>`) which serves as a parameter for the conditional operator.",
  "answer": {
    "children": [
      "<- <user is an admin>"
    ]
  }
}
```

**Explanation**: The output follows the required JSON structure with `analysis` containing the reasoning and `answer` containing a dictionary with the children list.

---
**INPUTS:**

**Concept to Decomposed:**
$input_1

**Remaining Normtext:**
$input_2

**Question:**
$input_3

**Question Type:**
$input_4

**Functional Concept:**
$input_5
---

Execute the instruction and return a JSON object with "analysis" (your reasoning) and "answer" (a dictionary with "children"). Return only the JSON object.
```

---

### File: `prompts/normtext_distribution_prompt`

```
You are an expert in NormCode, a semi-formal language for planning inferences.

**Your Task: Step 2C (Part 2) - Generate Full Inference**

You have been given the `concept_to_decomposed`, its `functional_concept` (`<=`), a set of new `child_concepts` (`<-`), and the parent's `source_text` (`...:`). Your task is to generate the **complete, annotated inference**.

This involves deciding for **both** the functional concept and all child concepts whether they are **definitive** (`/:`) or require **further decomposition** (`...:`).

1.  `...:` **(Source Text)**: Assign a snippet of the parent's text. This signifies the concept is **not fully resolved** and requires another decomposition loop.
2.  `/:` **(Description)**: Assign a concise description. This signifies the concept is **definitive** in the current context.

Your final output must be a single JSON object.

First, think step-by-step about how to distribute the source text and assign annotations. Place your reasoning in the "analysis" key of the JSON object.
Then, provide the final answer in the "answer" key as a dictionary containing:
- "new inference": The complete, annotated inference as a single string, with proper indentation and newline characters (`\n`)

**Guiding Principles for Annotation**

1.  **Functional Concept (`<=`)**:
    *   Assign `...:` if the parent text contains conditions or clauses that apply to the operation itself. (e.g., `"...if the feeling is mutual"`).
    *   Assign `/:` if the operation is straightforward and fully described by its children (the common case).

2.  **Child Concepts (`<-`)**:
    *   Assign `/:` (making it **definitive**) for I/O operations, self-contained concepts (like a nominalized action), or pre-defined concepts.
    *   Assign `...:` if the child is complex and has its own descriptive text within the parent's source that needs to be broken down further.

**Examples**

**Example 1: Definitive Child and Functional Description**

**Input:**
```json
{
    "concept to decomposed": ":<:({User Authentication})",
    "functional concept": "<= $::",
    "child concepts": [
        "<- ::(verify the user's identity)"
    ],
    "parent source text": "User authentication is the process of verifying a user's identity."
}
```

**Output:**
```json
{
  "analysis": "I need to analyze the parent source text 'User authentication is the process of verifying a user's identity.' The functional concept is `<= $::` (nominalization), and there's one child concept `<- ::(verify the user's identity)`. The parent text fully explains the nominalization without adding any conditions or clauses that need further decomposition. Therefore, both the functional concept and child concept should be assigned `/:` (definitive descriptions). The functional concept gets a description explaining it's a process, and the child gets a description of the action.",
  "answer": {
    "new inference": ":<:({User Authentication})\n    <= $::\n        /: It is defined as a process.\n    <- ::(verify the user's identity)\n        /: The action is to verify a user's identity."
  }
}
```

**Explanation**: The output follows the required JSON structure with `analysis` containing the reasoning and `answer` containing a dictionary with the complete inference.

**Example 2: Functional Source Text (`...:`)**

**Input:**
```json
{
    "concept to decomposed": ":<:({love})",
    "functional concept": "<= $.({deep feeling})",
    "child concepts": [
        "<- {deep feeling}"
    ],
    "parent source text": "love is a deep feeling, (if) the feeling is mutual."
}
```

**Output:**
```json
{
  "analysis": "I need to analyze the parent source text 'love is a deep feeling, (if) the feeling is mutual.' The functional concept is `<= $.({deep feeling})` (specification), and there's one child concept `<- {deep feeling}`. The parent text contains a conditional clause 'if the feeling is mutual' that applies to the operation itself (the specification is conditional). According to the guiding principles, when the parent text contains conditions that apply to the operation, I should assign `...:` to the functional concept. The child `{deep feeling}` is straightforward and should get a definitive description (`/:`).",
  "answer": {
    "new inference": ":<:({love})\n    <= $.({deep feeling})\n        ...: if the feeling is mutual.\n    <- {deep feeling}\n        /: love is a deep feeling."
  }
}
```

**Explanation**: The output follows the required JSON structure with `analysis` containing the reasoning and `answer` containing a dictionary with the complete inference.

---
**INPUTS:**

**Concept to Decomposed:**
$input_1

**Functional Concept (`<=`):**
$input_2

**Child Concepts (a list of strings):**
$input_3

**Parent's `...:` text to distribute:**
$input_4
---

Execute the instruction and return a JSON object with "analysis" (your reasoning) and "answer" (a dictionary with "new inference"). Return only the JSON object.
```

---

### File: `prompts/normcode_draft_update_prompt`

```
You are an expert in NormCode, a semi-formal language for planning inferences.

**Your Task: Update the Main Draft**

You have just finished a full decomposition cycle. You have been given:
1.  The **Main NormCode Draft**, which still contains the original, un-decomposed concept.
2.  The **New Decomposed Snippet**, which is the complete, structured block that should replace the original concept.

Your task is to update the main draft by finding the original concept (the one that was just decomposed) and replacing it entirely with the new, decomposed snippet.

Your final output must be a single JSON object.

First, think step-by-step about how to identify the part of the draft to replace and how to perform the replacement. Place your reasoning in the "analysis" key of the JSON object.
Then, provide the final, complete, updated draft as a single string in the "answer" key.

**Example:**

**Input:**
*   **Main NormCode Draft:**
    ```normcode
    :<:(::(register a new user))
        <= @by(:_:)
        <- {steps}
            ...: "first, check... second, if it does..."
        <- {user name}
            ...: "the provided username is provided by the user."
    ```
*   **New Decomposed Snippet:**
    ```normcode
    <- {steps}
        ?: How are the steps composed?
        <= &across
        <- {step 1}
            ...: "first, check if the provided username already exists."
        <- {step 2}
            ...: "second, if it does, report an error."
    ```

**Output (JSON):**
```json
{
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with the new, more detailed snippet provided, while preserving the indentation and the surrounding concepts like `<- {user name}`.",
  "answer": ":<:(::(register a new user))\n    <= @by(:_:)\n    <- {steps}\n        ?: How are the steps composed?\n        <= &across\n            /: The steps are composed as an ordered sequence.\\n        <- {step 1}\\n            ...: \"first, check if the provided username already exists.\"\\n        <- {step 2}\\n            ...: \"second, if it does, report an error.\""
}
```

---
**INPUTS:**

**Main NormCode Draft:**
$input_1

**New Decomposed Snippet:**
$input_2
---

Execute the instruction and return only the JSON object.
```

---

### File: `prompts/decomposition_step_prompt`

```
You are an expert in NormCode, a semi-formal language for planning inferences. Your task is to perform a complete decomposition step in a single operation.

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object.
Then, provide the final answer (the updated NormCode draft) in the "answer" key.

**Your Task: Complete Decomposition Step**

You will be given a NormCode draft. Your task is to:

1. **Identify the Next Concept**: Find the first concept (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).
2. **Formulate the Question**: Based on the concept's Inference Target and its `...:` text, formulate the specific question (`?:`) and classify its type.
3. **Construct the Functional Concept**: Build the complete `<= ...` functional concept line that answers the question.
4. **Create Child Concepts**: Generate the new child concepts (`<-`) that logically follow from the functional concept.
5. **Distribute Source Text**: Assign `...:` or `/:` annotations to the functional concept and all child concepts.
6. **Update the Draft**: Replace the original concept with the new, decomposed inference block.

---

**STEP 1: Question Type Classification**

The question type you select directly determines the NormCode operator used. Below is a comprehensive list:

**A. Questions for Object-Like Concepts** (`{}`, `<>`, `[]`):

* **Classification/Specification**: Defines a concept by relating it to a more general one, or by breaking it down into constituent parts.
    * Example: "What is `{user account}` specified as?" (e.g., "...: a user account is a record containing a username and password.")
    * Operator: `$.({type})`

* **Nominalization**: Transforms a process or action (a verb) into a concept that can be treated as a noun.
    * Example: "What process is `{user authentication}` defined as?" (e.g., "...: user authentication is the process of verifying a user...")
    * Operator: `$::`

* **Continuation/Extension**: Extends an existing sequence, collection, or concept by adding something to it.
    * Example: "What continuation is `{updated sequence}` formed from?" (e.g., "...: the updated sequence is the result of adding a new number to the old one...")
    * Operator: `$+({new_item}:{old_collection})`

* **Instantiation**: Defines a concept by enumerating its specific, concrete members or instances.
    * Example: "What are the specific instances of `{number sequence}`?" (e.g., "...: the sequence is 1, 2, 3...")
    * Operator: `$%`

* **Identification**: Asserts that a concept is identical to another specific, marked instance.
    * Example: "What are identities of `{number sequence}`?" (e.g., "...: the number sequence is the same as the one marked by {1}...")
    * Operator: `$={marker}`

* **Annotated Composition**: Groups multiple concepts together into a structured record where each concept is a named field.
    * Example: "How are `{position}` and `{value}` composed into an annotated structure?" (e.g., "...: a sequence of numbers indexed by their position and value...")
    * Operator: `&in[{field1}; {field2}]`

* **Ordered Composition**: Combines or concatenates two or more ordered concepts (like lists or sequences) into a single new one.
    * Example: "How is `{number sequence}` composed as an ordered sequence?" (e.g., "...: the sequence is a combination of sequence 1 and sequence 2...")
    * Operator: `&across`

* **Process Request**: Asks how to perform an action that is directly related to or performed by an object.
    * Example: "How to find `{the user}` with some process?" (e.g., "...: find the user with their name...")
    * Operators: `::(action)` (unbounded) or `:_:{method}({params})` (bounded)

* **I/O Request**: Asks how a piece of data is obtained from an external source (input) or sent to an external destination (output).
    * Example: "How to acquire `{username}` as input?" (e.g., "...: the username is input by the user...")
    * Operators: `:>:{concept}?()` (input) or `:<:({concept})` (output)

* **Judgement Request**: Asks about evaluating a boolean state, condition, or property of an object.
    * Example: "How to judge the truth of the statement `<user is an admin>`?" (e.g., "...: if the user is an admin...")
    * Operators: `::<statement>` (unbounded) or `::{quantifier}<statement>` (quantifier)

* **Element-wise Breakdown**: Asks how an operation is applied individually to every item in a collection.
    * Example: "How to square every element of `{number sequence}` by each of its member?" (e.g., "...: the sequence is squared by squaring each of its members...")
    * Operator: `*every({collection})`

**B. Questions for Action-Like Concepts** (`::()`, `::< >`):

* **Methodology Declaration**: Specifies the method or means by which an action is performed.
    * Example: "By what method is `::(Authenticate the user)` performed?" (e.g., "...: authenticate the user by checking their password...")
    * Operator: `@by(:Subject:)`

* **Conditional Dependency**: Asks about the condition required for an action to occur.
    * Example: "Under what condition is `::(Show the admin dashboard)` executed?" (e.g., "...: show the dashboard if the user is an admin...")
    * Operator: `@if(<condition>)` or `@if!(<condition>)`

* **Sequential Dependency**: Asks about the order of actions.
    * Example: "After what event is `::(Show the admin dashboard)` executed?" (e.g., "...: show the dashboard after the user is authenticated...")
    * Operator: `@after({event})`

---

**STEP 2: Operator Construction Reference**

| Question Type | Operator Pattern | Construction Logic |
|--------------|-----------------|-------------------|
| **Classification/Specification** | `$.({type})` | Identify the primary type or class. E.g., "...is a **record**..." â†’ `$.({record})`. |
| **Nominalization** | `$::` | Stands alone. Transforms action-as-a-noun into a formal process. |
| **Continuation/Extension** | `$+({new_item}:{old_collection})` | Identify concepts being added/extended. |
| **Instantiation** | `$%` | Stands alone. Specific instances created as children. |
| **Identification** | `$={marker}` | Identify the marker or tag. E.g., `...marked by {1}` â†’ `$={1}`. |
| **Annotated Composition** | `&in[{field1}; {field2}]` | Identify the fields of the structure. |
| **Ordered Composition** | `&across` | Stands alone. Ordered items created as children. |
| **Process Request (Unbounded)** | `::(action)` | Extract the complete imperative action. |
| **Process Request (Bounded)** | `:_:{method}({params})` | Extract the pre-defined method and parameters. |
| **I/O Request (Input)** | `:>:({concept})?()` | Extract the concept being input. |
| **I/O Request (Output)** | `:<:({concept})` | Extract the concept being output. |
| **Judgement Request (Unbounded)** | `::<statement>` | Extract the complete simple statement. |
| **Judgement Request (Quantifier)** | `::{quantifier}<statement>` | Extract the quantifier and statement. |
| **Element-wise Breakdown** | `*every({collection})` | Identify the collection being operated on. |
| **Methodology Declaration** | `@by(:Subject:)` | Identify the method described. Use appropriate subject marker. |
| **Conditional Dependency** | `@if(<condition>)` | Extract the condition that gates the action. |
| **Sequential Dependency** | `@after({event})` | Extract the event/action that must complete first. |

---

**STEP 3: Child Concept Creation Logic**

The operator within the functional concept dictates the kind of children you must create:

* `$.({type})` **(Specification)**: Create children for the `{type}` and any other components mentioned.
* `$::` **(Nominalization)**: Create a single child representing the action being nominalized.
* `$+({new_item}:{old_collection})` **(Continuation)**: Create children for the new item and old collection.
* `$%` **(Instantiation)**: Create a single child representing the collection of items.
* `&in[{key}; {value}]` **(Annotation Grouping)**: Create children for key and value components.
* `&across` **(Order Grouping)**: Create children for each component of the combined sequence.
* `::({action})` **(Unbounded Imperative)**: Create children for any parameters required.
* `:_:{method}({params})` **(Bounded Imperative)**: Create children for method definition and parameters.
* `:>:{input}?()` **(Input Imperative)**: Create a child for the input being requested.
* `::<{statement}>` **(Unbounded Judgement)**: Create children for concepts within the statement.
* `::{quantifier}<{statement}>` **(Quantifier Judgement)**: Create children for concepts being judged.
* `*every({collection})` **(Element-wise)**: Create a child for the collection being operated on.
* `@by(:Subject:)` **(Method)**: Create children representing the method or action described.
* `@if(<condition>)` **(Conditional)**: Create a single child for the embedded condition.
* `@after({event})` **(Sequence)**: Create a child for the event that must complete first.

---

**STEP 4: Annotation Assignment (Source Text Distribution)**

For both the functional concept and all child concepts, decide whether they are:
1. `...:` **(Source Text)**: Assign if the concept requires further decomposition (has complex conditions, clauses, or descriptive text).
2. `/:` **(Description)**: Assign if the concept is definitive in the current context (self-contained, I/O operations, pre-defined).

**Guiding Principles:**
- **Functional Concept (`<=`)**: Assign `...:` if parent text contains conditions/clauses that apply to the operation itself. Assign `/:` if straightforward and fully described by children.
- **Child Concepts (`<-`)**: Assign `/:` for I/O operations, self-contained concepts, or pre-defined concepts. Assign `...:` if complex with its own descriptive text needing further breakdown.

---

**Execution Steps:**

1. Find the first concept with un-parsed `...:` annotation (reading top to bottom).
2. Extract its full line and `...:` content.
3. Determine the question type based on the concept type and source text.
4. Formulate the question (`?:`).
5. Construct the functional concept (`<= ...`) based on question type.
6. Create all necessary child concepts (`<- ...`).
7. Assign `...:` or `/:` annotations to functional and child concepts.
8. Construct the complete inference block with proper indentation.
9. Replace the original concept in the draft with the new inference block.
10. Return the updated draft.

---

**Example:**

**Input NormCode Draft:**
```normcode
:<:(::(register a new user))
    ...: To register a new user, first check if the provided username already exists in the database.
    <= @by(:_:)
    <- {steps}
        ...: "first, check if the provided username already exists."
        ...: "second, if it does, report an error."
```

**Step-by-step execution:**
1. Find first concept with `...:`: `<- {steps}` (has two `...:` lines)
2. Extract: concept is `<- {steps}`, source text is the two `...:` lines
3. Question type: **Ordered Composition** (multiple steps in sequence)
4. Question: "How are `{steps}` composed as an ordered sequence?"
5. Functional concept: `<= &across`
6. Child concepts: `<- {step 1}` and `<- {step 2}`
7. Annotations: Functional gets `/:`, children get `...:` with their respective texts
8. Construct inference block
9. Replace `<- {steps}` with new block
10. Return updated draft

**Output (in JSON):**
```json
{
  "analysis": "Found `<- {steps}` with two source text lines. This represents an ordered composition of sequential steps. Used `&across` operator. Created two child steps, each with their respective source text for further decomposition.",
  "answer": ":<:(::(register a new user))\\n    ...: To register a new user, first check if the provided username already exists in the database.\\n    <= @by(:_:)\\n    <- {steps}\\n        ?: How are the steps composed as an ordered sequence?\\n        <= &across\\n            /: The steps are composed as an ordered sequence.\\n        <- {step 1}\\n            ...: \"first, check if the provided username already exists.\"\\n        <- {step 2}\\n            ...: \"second, if it does, report an error.\""
}
```

---

**Your Turn:**

**NormCode Draft:**
---
$input_1
---

Execute all steps and return a JSON object with "analysis" (your reasoning) and "answer" (the updated NormCode draft). Return only the JSON object.

---

## 3. The Meta-Plan

### File: `v1_manual.ncd`

```normcode
:<:({normcode draft}) 1. assignment

    <= $.({normcode draft})

    <- {normtext}<$={1}> | 1.1. imperative
        <= :>:({prompt}<:{normtext}>)
        <- {normtext}?<:{prompt}>
            |%{prompt_location}: normtext_prompt

    <- {normcode draft}<$={1}> | 1.2. imperative
        <= ::{%(direct)}({prompt}<$({initialization prompt})%>: {1}<$({normtext})%>)
        <- {initialization prompt}<:{prompt}>
            |%{prompt_location}: initialization_prompt
        <- {normtext}<$={1}><:{1}>

    <- [all {normcode draft}] | 1.3. grouping
        <= &across({normcode draft})
        <- {normcode draft}<$={1}>
    
    <- {normcode draft}<$={5}> | 1.4. quantifying
        <= *every([all {normcode draft}]) | 1.4.1. assignment

            <= $.({normcode draft}<$={#}>)

            <- <current normcode draft is complete> | 1.4.1.1. judgement
                <= ::{%(direct)}<{prompt}<$(completion check prompt)%>: {1}<$({current normcode draft})%> is a complete>
                <- {completion check prompt}<:{prompt}>
                    |%{prompt_location}: completion_check_prompt
                <- [all {normcode draft}]*1<:{1}>

            <- {normcode draft}<$={2}>  | 1.4.1.2. assignment
                <= $.([all {normcode draft}]*1) | 1.4.1.2.1. timing
                    <= @if(<current normcode draft is complete>)
                    <- <current normcode draft is complete>
                <- [all {normcode draft}]*1

            <- {normcode draft}<$={3}> | 1.4.1.3. assignment
                <= $.({normcode draft}<$={4}>) | 1.4.1.3.1. timing
                    <= @if!(<{normcode draft} is complete>)
                    <- <{normcode draft} is complete>
                <- [{concept to decomposed} and {remaining normtext}] | 1.4.1.3.2. imperative
                    <= ::{%(direct)}<{prompt}<$(concept identification prompt)%>: {1}<$({normcode draft})%>>
                    <- {concept identification prompt}<:{prompt}>
                        |%{prompt_location}: concept_identification_prompt
                    <- [all {normcode draft}]*1<:{2}>

                <- [{question} and {question type}] | 1.4.1.3.3. imperative
                    <= ::{%(direct)}<{prompt}<$(question inquiry prompt)%>: {1}<$({concept to decomposed})%>, {2}<$({remaining normtext})%>>
                    <- {question inquiry prompt}<:{prompt}>
                        |%{prompt_location}: question_inquiry_prompt
                    <- [{concept to decomposed}<:{1}> and {remaining normtext}<:{2}>]
                    
                <- {functional concept} | 1.4.1.3.4. imperative
                    <= ::{%(direct)}<{prompt}<$(operator selection prompt)%>: {1}<$({question})%>, {2}<$({concept to decomposed})%>, {3}<$({question type})%>, {4}<$({remaining normtext})%>>
                    <- {operator selection prompt}<:{prompt}>
                        |%{prompt_location}: operator_selection_prompt
                    <- [{concept to decomposed}<:{1}> and {remaining normtext}<:{2}>]
                    <- [{question}<:{1}> and {question type}<:{2}>]

                <- {children concepts} | 1.4.1.3.5. imperative
                    <= ::{%(direct)}<{prompt}<$(children concept creation prompt)%>: {1}<$({functional concept})%>, {2}<$({question})%>, {3}<$({concept to decomposed})%>, {4}<$({question type})%>, {5}<$({remaining normtext})%>>
                    <- {children concept creation prompt}<:{prompt}>
                        |%{prompt_location}: children_concept_creation_prompt
                    <- {functional concept}<:{1}>
                    <- [{concept to decomposed}<:{3}> and {remaining normtext}<:{5}>]
                    <- [{question}<:{2}> and {question type}<:{4}>]
    
                <- {new inference} | 1.4.1.3.6. imperative
                    <= ::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: {1}<$({functional concept})%>, {2}<$({children concepts})%>, {3}<$({concept to decomposed})%>, {4}<$({remaining normtext})%>>
                    <- {normtext distribution prompt}
                        |%{prompt_location}: normtext_distribution_prompt
                    <- {functional concept}<:{1}>
                    <- {children concepts}<:{2}>
                    <- [{concept to decomposed}<:{3}> and {remaining normtext}<:{4}>]

                <- {normcode draft}<$={4}> | 1.4.1.3.7. imperative
                    <= ::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: {1}<$({normcode draft})%>, {2}<$({new inference})%>>
                    <- {normcode draft update prompt}
                        |%{prompt_location}: normcode_draft_update_prompt
                    <- [all {normcode draft}]*1<:{1}>
                    <- {new inference}<:{2}>

            <- [all {normcode draft}] | 1.4.1.4. grouping
                <= &across({normcode draft})
                <- {normcode draft}<$={2}>
                <- {normcode draft}<$={3}>

        <- [all {normcode draft}]
```



---

# File: 1.3.3.1---generate_natural_language_translation.md


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

# File: 1.3.4.1---manual_review_of_deconstruction.md


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

# File: 1.4.2.1---apply_serialization_patterns.md


## Step 3.1: Apply Serialization Patterns

The initial phase focused on cleaning up the raw plan and giving it a consistent structure.

-   **Cleanup**: Removed all informal notation lines (`/:`, `?:`, `...:`).
-   **Serialization**: The core pattern applied was to reframe each step as an *output* being generated by an *imperative*. This established a clear "effect <= cause" relationship throughout the plan.

For example, a step was structured as:

```normcode
<- {output_file.ext}
    <= ::(imperative describing the action)
```

This created a foundation where each generated artifact was explicitly linked to the action that created it.



---

# File: 1.4.3.1---apply_redirection_patterns.md


## Step 3.2: Apply Redirection Patterns

This step was crucial for making the data flow of the pipeline explicit. The goal was to define the precise inputs for every imperative.

-   **Explicit Inputs**: Each imperative was detailed to show its dependencies, which were categorized as:
    -   **Prompts**: Inputs sourced from a prompt file, identified with a `<:{prompt}>` tag and a `%{prompt_location}` annotation.
    -   **Inherited Outputs**: Inputs that were the direct result of a previous step in the pipeline.
    -   **File Inputs**: Inputs sourced directly from files on disk, which can be static (like the original prompt) or discovered dynamically.

An example of a redirected imperative that dynamically discovers context files:

```normcode
<- {1.1_instruction_block.md}
    <= ::{%(direct)}({prompt}<$({instruction distillation prompt})%>: {1}<$({input files})%>)
    <- {instruction distillation prompt}<:{prompt}>
        |%{prompt_location}: 1.1_instruction_distillation.md
    <- {input files}<:{1}>
        <= &in
        <- {original prompt}
            |%{file_location}: prompts/0_original_prompt.md
        <- {other input files}
            <= :>:{%(file_location)}({prompt}<$({location of related files prompt})%>)
            <- {location of related files}<:{prompt}>
                |%{prompt_location}: location_of_related_files_prompt.md
```

This process made the plan's dependencies transparent and prepared it for formalization.



---

# File: 1.4.4.1---plan_formalization.md


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

# File: 1.5.2.1---automated_context_distribution.md


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
    â”œâ”€â”€ raw---prompt.txt
    â””â”€â”€ raw---system_context.json
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
    â”œâ”€â”€ 1.2.2---check_username_existence.txt
    â”œâ”€â”€ raw---prompt.txt
    â”œâ”€â”€ raw---system_context.json
    â””â”€â”€ shared---database_connection.txt
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

# File: 1.5.3.1---automated_prompt_generation.md


# Step 4.2: Automated Prompt Generation

**Objective:** To assemble the final, executable prompt files by combining the specific context required for each prompt-driven inference. This is a deterministic assembly step, not an LLM generation step.

**Process:**

This step is an automated script that takes one key input:

1.  **The final Context Manifest (`4.1_context_manifest.json`):** This file provides the complete mapping between each prompt and its required context files.

The script performs the following actions:

1.  **Reads the Manifest:** It parses the `4.1_context_manifest.json` file.
2.  **Iterates Through Prompts:** It loops through each key-value pair in the `context_mapping` object. Each key represents a unique prompt file to be generated.
3.  **Assembles Content:** For each prompt, it reads the array of file paths from the `context_files` field. It then opens and concatenates the content of each of these files in the specified order. The general convention is to list shared context files first, followed by more specific, step-related files.
4.  **Writes Prompt Files:** The concatenated content is written to a new file within the `prompts/` directory. The name of the file is taken directly from the key in the manifest (e.g., `[1.2.2.2.]1.1_instruction_distillation.md`).

---

### Example Walkthrough

This example demonstrates how a single prompt file is assembled.

**1. Input (`4.1_context_manifest.json` snippet):**

The manifest provides the "recipe" for building the prompt.

```json
{
  "context_mapping": {
    "[1.2.2.2.]1.1_instruction_distillation.md": {
      "used_by_inference": "1.2.2.1.imperative|<= ::{%(direct)}(...)",
      "context_files": [
        "./context_store/shared---pipeline_goal_and_structure.md",
        "./context_store/1.2.2.1---automated_instruction_distillation.md"
      ]
    },
    // ... other prompt mappings
  }
}
```

**2. Assembly Process:**

The script identifies the entry for `[1.2.2.2.]1.1_instruction_distillation.md`. It then:
1.  Reads the content of `./context_store/shared---pipeline_goal_and_structure.md`.
2.  Reads the content of `./context_store/1.2.2.1---automated_instruction_distillation.md`.
3.  Concatenates these two pieces of content together.
4.  Creates a new file named `prompts/[1.2.2.2.]1.1_instruction_distillation.md`.
5.  Writes the concatenated content into this new file.

**3. Output (A new file in `prompts/`):**

The result is a complete, self-contained prompt file ready to be used by the corresponding imperative (`1.2.2.1.imperative`). The content of `prompts/[1.2.2.2.]1.1_instruction_distillation.md` would look like this:

```markdown
<Content of shared---pipeline_goal_and_structure.md>
---
<Content of 1.2.2.1---automated_instruction_distillation.md>
```

This process is repeated for every entry in the manifest, resulting in a fully populated `prompts/` directory.



---

# File: 1.5.4.1---manual_review_of_contextualization.md


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

# File: 1.6.2.1---automated_script_generation.md


## Step 5.1: Automated Script Generation

**Objective**: Your task is to transform a formalized NormCode plan (`.nc`) and its associated context into a set of executable Python artifacts: `concept_repo.json`, `inference_repo.json`, and a main runner script (`.py`).

**Core Inputs**:
- The formalized NormCode plan (`.nc` file).
- The final Context Manifest (`.json` file).
- The `context_store` directory.

### Procedure

The generation process follows a structured procedure to translate the abstract NormCode plan into concrete, executable repository objects. This should be approached as a design-first process before implementation.

#### 0. Design the Repositories (Pre-computation step)
Before generating any JSON, first sketch out the repository design.
-   **Concept List**: Enumerate every concept from the `.nc` file. For each, decide if it is ground, final, or intermediate. Plan its `reference_data` and `reference_axis_names`.
-   **Inference List**: For each inference in the `.nc` file, design the corresponding `InferenceEntry`. Choose the `inference_sequence`, map all the concept connections, and, most importantly, design the full `working_interpretation` JSON object.

#### 1. Identify All Concepts and Operators from the NormCode Plan

First, perform a full parse of the `.nc` file to identify every unique concept. Each concept must be classified by its type and behavior.

-   **Semantical object concepts (`{...}`)**: e.g., `{normcode draft}`, `{functional concept}`.
-   **Semantical statement concepts (`<...>`**) e.g., `<current normcode draft is complete>`.
-   **Semantical relation concepts (`[...]`)**: e.g., `[all {normcode draft}]`.
-   **Syntactical operator concepts**: The operators that define the plan's logic, such as `*every(...)`, `&across(...)`, `$.(...)`, `$+(...)`, `@if`, `@if!`, `@after`.
-   **Functional concepts**: The imperative `::(...)` and judgement `:%(...)` blocks that represent actions or decisions.

#### 2. Generate `ConceptEntry` Objects

For each unique concept identified, create a corresponding `ConceptEntry` object. The attributes of this object are determined by the concept's role in the plan.

**2.1. Classify Concept Behavior**

-   **Final outputs**: These are the ultimate goals of the plan. Mark them with `is_final_concept=True`.
-   **Ground concepts**: These are the initial inputs, prompts, or fixed operators. Mark them with `is_ground_concept=True` and populate their `reference_data` and `reference_axis_names`. For nested data, use a nested list in `reference_data`.
-   **Intermediate concepts**: These are temporary variables or loop items that exist only during the run.
-   **Functional / operator concepts**: These represent the plan's syntax (e.g., `*every`, `$.`, `@if`, `::({})`). They are typically ground concepts (`is_ground_concept=True`).

**2.2. Map NormCode Types to `ConceptEntry` Attributes**

-   **Objects (`{...}`)**: `type` = `"{}"`. `axis_name` should describe the semantic axis (e.g., `"normcode draft"`).
-   **Statements (`<...>`**) `type` = `"<>"`. Typically have no `reference_data` unless they are ground-truth judgements.
-   **Relations (`[...]`)**: `type` = `"[]"`. `axis_name` should describe the collection (e.g., `"all unit place value of numbers"`).
-   **Operators and Functions**: The `type` attribute should encode the operator class (e.g., `"*every"`, `"$.`, `"::({})"`). The `concept_name` should be the full textual form of the operator from the `.nc` file.

#### 3. Generate `InferenceEntry` Objects

For each inference block in the `.nc` plan, create a corresponding `InferenceEntry` object. This object makes the plan's execution logic explicit for the orchestrator.

**3.1. Map Core Fields**

-   **`flow_info`**: Set `flow_info={'flow_index': '...'}` from the NormCode sequence label (e.g., `1.`, `1.1.2`).
-   **`inference_sequence`**: Map the role annotation from the `.nc` file (e.g., `quantifying`, `assigning`, `imperative`). This determines which agent sequence will execute the step.
-   **`concept_to_infer`**: The concept being defined on the left side of the inference.
-   **`function_concept`**: The operator on the right side of the `<=` in the NormCode.
-   **`value_concepts` and `context_concepts`**: The concepts listed under the `"<-"` lines in the NormCode block.

**3.2. Synthesize `working_interpretation`**

This is the most critical part of the translation. The `working_interpretation` JSON object encodes the implicit syntax of the NormCode into an explicit structure the orchestrator can understand. Below are templates for different inference sequences.

-   **For `quantifying` (`*every`) inferences**:
    -   **Purpose**: Describe a loop's structure.
    -   **Shape**:
        ```json
        {
            "syntax": {
                "marker": "every",
                "quantifier_index": 1,
                "LoopBaseConcept": "{number pair}",
                "CurrentLoopBaseConcept": "{number pair}*1",
                "group_base": "number pair",
                "InLoopConcept": { "{carry-over number}*1": 1 },
                "ConceptToInfer": ["{new number pair}"]
            }
        }
        ```

-   **For `grouping` (`&across`) inferences**:
    -   **Purpose**: Describe a grouping operation.
    -   **Shape**:
        ```json
        {
            "syntax": {
                "marker": "across",
                "by_axis_concepts": "{number pair}*1"
            }
        }
        ```

-   **For `assigning` (`$.` or `$`) inferences**:
    -   **Purpose**: Describe data movement or updates.
    -   **Shape**:
        ```json
        {
            "syntax": {
                "marker": ".", // or "+" for append
                "assign_source": "{remainder}",
                "assign_destination": "*every(...)"
            }
        }
        ```

-   **For `timing` (`@if`, `@if!`, `@after`) inferences**:
    -   **Purpose**: Describe conditional execution.
    -   **Shape**:
        ```json
        {
            "syntax": {
                "marker": "if", // or "if!" or "after"
                "condition": "<current normcode draft is complete>"
            }
        }
        ```

-   **For `imperative` or `judgement` inferences**:
    -   **Purpose**: Describe a call to a tool, LLM, or script.
    -   **Complex Shape (with value selectors)**: When an imperative needs to extract specific parts of a relation concept, use `value_selectors`:
        ```json
        {
            "is_relation_output": true,
            "with_thinking": true,
            "prompt_location": "name_of_prompt_file",
            "value_order": { ... },
            "value_selectors": {
              "relation_part_1": {
                  "source_concept": "[{concept to decomposed} and {remaining normtext}]",
                  "index": 0,
                  "key": "concept to decomposed"
              },
              "relation_part_2": {
                  "source_concept": "[{concept to decomposed} and {remaining normtext}]",
                  "index": 0,
                  "key": "remaining normtext"
              }
            }
        }
        ```
    -   The `value_order` map is crucial for binding the `value_concepts` to the positional placeholders (`{1}`, `{2}`) in the functional concept's text.

#### 4. Generate Repository Files

-   Serialize the complete list of `ConceptEntry` objects into `concept_repo.json`.
-   Serialize the complete list of `InferenceEntry` objects into `inference_repo.json`.

#### 5. Generate the Runner Script (`.py`)

Finally, generate a Python script that uses the repository files to execute the plan. The script should follow this template and include any necessary file system preparation (e.g., creating a `prompts/` directory if the plan requires it).

```python
from infra._orchest._repo import ConceptRepo, InferenceRepo
from infra._orchest._orchestrator import Orchestrator
from infra._agent._body import Body
import os
import json

def create_repositories_from_files():
    with open('concept_repo.json', 'r') as f:
        concept_data = json.load(f)
    concept_repo = ConceptRepo.from_json_list(concept_data)

    with open('inference_repo.json', 'r') as f:
        inference_data = json.load(f)
    inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)
    
    return concept_repo, inference_repo

if __name__ == "__main__":
    # 1. Build repositories from the generated JSON files
    concept_repo, inference_repo = create_repositories_from_files()

    # 2. Construct a Body for imperatives/judgements
    body = Body(llm_name="qwen-plus") # Or other appropriate configuration

    # 3. Construct and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        body=body,
        max_cycles=300,
    )
    final_concepts = orchestrator.run()

    # 4. Inspect and log final concepts
    for final_concept_entry in final_concepts:
        if final_concept_entry and final_concept_entry.concept.reference:
            ref_tensor = final_concept_entry.concept.reference.tensor
            print(f"Final concept '{final_concept_entry.concept_name}': {ref_tensor}")
        else:
            print(f"No reference found for final concept '{final_concept_entry.concept_name}'.")

```



---

# File: 1.6.3.1---manual_review_of_materialization.md


### Step 4.2: Manual Review of Materialization

**Objective:** Review the final, executable scripts generated by the automated process to ensure they are correct, efficient, and ready for deployment.

**Procedure:**

1.  **Examine the Generated Scripts (e.g., `.py`, `.sh` files):**
    *   Perform a thorough code review to check for correctness, adherence to coding standards, and efficiency.
    *   Verify that the scripts accurately implement the logic defined in the NormCode plan.
    *   Manually execute the scripts in a safe, isolated test environment to confirm they run without errors and produce the expected output.

**Outcome:** A fully validated and deployment-ready set of executable scripts that fulfill the original high-level instruction.

