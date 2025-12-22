# The NormCode AI Planning Pipeline

This document provides a detailed, practical walkthrough of a methodology for bootstrapping from a high-level natural language prompt into a structured and executable NormCode plan.

## Project Goal

To bootstrap from a high-level natural language prompt into a structured and executable NormCode plan, powered by a NormCode plan itself, creating a meta-algorithm that allows the system to understand, decompose, and act upon complex instructions.

---

## Illustrative Example Scenario

**Initial Input:**

This consists of two parts: the raw, conversational prompt from the user, and the relevant technical context from the system.

1.  **User's Raw Prompt:**
    ```
    "Hey, can you set up the user registration flow for me? Basically, when a new user signs up, we need to make sure their username isn't already taken. If it is, just tell them it's unavailable. If it's free, go ahead and create their account. Oh, and for the username check, it shouldn't matter if it's 'John' or 'john', you know? Just treat them the same. For the password, just make something up that's secure."
    ```

2.  **System Context:**
    ```json
    {
      "database": {
        "type": "PostgreSQL",
        "user_table": "users",
        "username_column": "username"
      },
      "mcp_tools_available": [
        {
          "tool_name": "database_query",
          "description": "Executes a SQL query against the PostgreSQL database.",
          "parameters": ["sql_query"]
        },
        {
          "tool_name": "generate_secure_password",
          "description": "Generates a cryptographically secure password.",
          "parameters": []
        }
      ]
    }
    ```

---

## The Four-Phase Pipeline

## **Phase 1: Confirmation of Instruction**

This phase transforms the initial, often conversational, user prompt into a set of clean, structured inputs ready for the NormCode translation pipeline. It leverages a powerful LLM-driven process to distill the user's intent and provides a crucial checkpoint for manual refinement.

### **Step 1.1: Automated Instruction Distillation**

The process begins by feeding the raw user prompt and any available system context to an LLM guided by a specialized meta-prompt. This meta-prompt instructs the model to perform a sophisticated analysis, separating the core procedural instructions from all other contextual information.

The goal is to produce two key artifacts:

1.  **Instruction Block:** This contains the clean, unambiguous, and procedural logic—the "what to do." It is synthesized from the core request in the user's prompt.
2.  **Initial Context Block:** This is a comprehensive, initial collection of all non-procedural information that underpins the user's request. Its goal is to preserve the original prompt's context as faithfully as possible, while also enriching it with implicit information critical for accurate interpretation. This includes:
    *   **Original Context:** All details from the user's prompt, including the original procedural descriptions, constraints, examples, and formatting requirements.
    *   **Implicit Context:** Additional information gathered by the system, such as past user interactions, system environment details, user profile information, and the reasoning behind how the core instruction was extracted.
    
    This unified block serves as the complete, raw contextual input for the later phases of the pipeline. The distribution of this context to specific NormCode nodes happens in Phase 3.

### **Example Scenarios**

Below are a few examples demonstrating how the distillation process handles different types of prompts.

#### **Scenario 1: Simple & Casual Request**

-   **Input (Raw Prompt):** `"hey can you just get me the latest sales report and email it to me and Sarah? sarah@example.com"`
-   **Input (System Context):** `{"tools": [{"tool_name": "generate_sales_report"}, {"tool_name": "send_email"}], "user_info": {"name": "Analyst", "email": "analyst@example.com"}}`
-   **LLM Process:** The model identifies the core actions and consolidates all remaining information—original and system-provided—into a single context block.
-   **Output:**
    -   **Instruction Block:** `"Generate the latest sales report. Then, send an email with the report attached to analyst@example.com and sarah@example.com."`
    -   **Initial Context Block:** `"The user's name is 'Analyst' and their email is 'analyst@example.com'. System environment includes the following available tools: {\"tools\": [{\"tool_name\": \"generate_sales_report\"}, {\"tool_name\": \"send_email\"}]}."`

#### **Scenario 2: Complex & Technical Request (with Markdown)**

-   **Input (Raw Prompt):**
    ```markdown
    Okay, here's the workflow for deploying the new feature.
    1.  Run the migration script on the staging database.
    2.  If it succeeds, deploy the `feature-branch` to the staging environment.
    3.  Notify the #dev-ops channel on Slack with the results.
    
    Make sure the deployment only happens outside of peak hours (9am-5pm PST).
    ```
-   **LLM Process:** The model parses the procedural steps for the instruction block and captures the explicit constraint from the prompt in the context.
-   **Output:**
    -   **Instruction Block:** `"Run the migration script on the staging database. If the migration is successful, deploy the feature-branch to the staging environment and send a Slack message to the #dev-ops channel with the results."`
    -   **Initial Context Block:** `"Constraint from prompt: The deployment must only occur outside of peak hours (9am-5pm PST)."`

#### **Scenario 3: Implicit Intent**

-   **Input (Raw Prompt):** `"We need to archive old user accounts. Anyone who hasn't logged in for over a year and doesn't have an active subscription should be backed up to S3 and then deleted."`
-   **Input (System Context):** `{"database": "production", "s3_bucket": "user-archives"}`
-   **LLM Process:** The model synthesizes the high-level goal into a concrete procedure and captures the system information in the context block, preserving its original structure.
-   **Output:**
    -   **Instruction Block:** `"Find all users who have not logged in for more than one year and do not have an active subscription. For each of these users, back up their account data to S3, and then delete their record from the database."`
    -   **Initial Context Block:** `"System environment details: {\"database\": \"production\", \"s3_bucket\": \"user-archives\"}."`

### **Step 1.2: Manual Review and Refinement (Optional)**

After the automated distillation, the generated **Instruction Block** and **Context Blocks** are presented for human review. This is a critical step that ensures the accuracy and completeness of the distilled information before it is passed to the next phase.

During this step, a developer can:
-   Correct any misinterpretations made by the LLM.
-   Refine the wording of the instruction for greater clarity.
-   Add, remove, or modify context to ensure the subsequent NormCode generation is precise and correct.

This intervention point is key to iteratively improving the system and handling complex or ambiguous prompts that automated systems might struggle with.

---
## **Phase 2: Deconstruction into NormCode Plan**

This phase takes the clean `Instruction Block` from Phase 1 and translates it into a first-pass structural representation in NormCode (`.ncd` file). This process is driven by an LLM guided by a meta-prompt that embodies the formal translation algorithm.

### **Step 2.1: Automated NormCode Deconstruction**

The core of this phase is an automated translation process. The `Instruction Block` is provided to an LLM that has been given a specialized meta-prompt, instructing it to act as a NormCode translation engine.

The LLM applies the recursive decomposition algorithm from the `comprehensive_normcode_translation_guide.md`. It systematically analyzes the instruction, asking questions to break down the logic, selecting the appropriate NormCode operators (e.g., `@by`, `&across`, `$::`, `@if`), and structuring the result into a hierarchical NormCode draft.

-   **Input:** The `Instruction Block` generated in Phase 1.
-   **LLM Process:** The model recursively deconstructs the instruction, identifying the top-level goal and breaking it down into a sequence of logically connected inferences.
-   **Output:** A **NormCode Draft (`.ncd`)**. This file represents the skeletal structure of the procedure, derived purely from the `Instruction Block`. It often includes annotations (`?:`, `/:`) that document the LLM's reasoning during the decomposition process.

**Example Output (`.ncd`):**
```normcode
:<:(::(register a new user))
    ?: How to register a new user?
    <= @by(:_:)
        /: The registration is requesting another process to be executed.
    <- :_:{steps}({user name})
    <- {steps}
        ?: How are the steps composed?
        <= &across
            /: The steps are an ordered sequence of actions.
        <- {step 1: check existence}
            <= $::.<username exists>
            <- ::<username exists?>
                <- {user name}
        <- {step 2: report error}
            <= $::.{error}
            <- ::(report error)
                <= @if(::<username exists?>)
        <- {step 3: create account}
            <= $::.{new user account}
            <- ::(create new user account)
                <= @if!(::<username exists?>)
                <- {user name}
                <- {password}
    <- {user name}
        <= :>:{user name}?()
    <- {password}
        <= ::(securely generate a password)
```

**Note on `.ncd` vs. `.nc` vs. `.ncn` Files:**

- The **NormCode Draft (`.ncd`)** file is the primary output of this deconstruction phase. It is a semi-formal representation that is rich with annotations (`?:`, `/:`) documenting the translation process, making it ideal for human review and debugging.

- The **NormCode Natural (`.ncn`)** file is a hybrid, line-by-line translation of the `.ncd` designed for maximum readability. It maintains the exact hierarchical structure of the original plan and preserves the ` <= ` and ` <- ` operators, but translates the NormCode concepts on those lines into clear, natural language. Annotations (`?:`, `/:`) are omitted for clarity.

- In contrast, a **NormCode (`.nc`)** file represents the final, formally parsable plan ready for execution. This version is created in a later phase by stripping the descriptive annotations from the `.ncd` file and adding execution-critical information, such as flow indices.

**Example `.ncn` Translation:**

Here is the natural language equivalent of the example `.ncd` file shown above, following the hybrid format:

```ncn
:<:(::(register a new user))
    <= This is accomplished by a defined method.
    <- The method is a series of steps that takes a user name as input.
    <- The method is a composition of steps.
        <= They are composed as a sequence of actions, one after the other.
        <- The first step is to check for the existence of the username.
            <= This step is defined as the action of checking if the username exists.
            <- The action itself is to determine if the username exists.
                <- This check requires the user name as input.
        <- The second step is to report an error.
            <= This step is defined as the action of reporting an error.
            <- The action itself is to report an error.
                <= This action is only performed if the username already exists.
        <- The third step is to create an account.
            <= This step is defined as the action of creating a new user account.
            <- The action itself is to create a new user account.
                <= This action is only performed if the username does not already exist.
                <- Creating the account requires the user name.
                <- Creating the account also requires a password.
    <- The overall method requires a user name.
        <= This user name is provided as a primitive input to the system.
    <- The overall method also requires a password.
        <= The password is created by securely generating one.
```

### **Step 2.2: Manual Review and Refinement (Optional)**

Following the automated deconstruction, the generated `.ncd` file is presented for human review. This step is crucial for verifying the logical integrity of the generated plan. A developer can examine the draft, correct any structural errors, refine the decomposition, and ensure the plan accurately reflects the intent of the original instruction before it proceeds to the contextualization phase.

---
## **Phase 3: Contextualization and Plan Formalization**

This phase takes the semi-formal `.ncd` plan, enriches it with the necessary context, and formalizes it into a preliminary `.nc` file. It transforms the comprehensive `Initial Context Block` into focused, local contexts and links them to uniquely identified inferences in the plan.

### **Step 3.1: Plan Formalization**

Before context can be distributed, the plan itself must be formalized. This step converts the annotated **NormCode Draft (`.ncd`)** into a preliminary, parsable **NormCode (`.nc`)** file. This involves two actions:

1.  **Generating Flow Indices:** The system parses the hierarchical structure of the `.ncd` file and assigns a unique, dot-delimited `flow_index` (e.g., `1.1`, `1.1.2`) to each inference.
2.  **Stripping Annotations:** All descriptive annotations (`?:`, `/:`) are removed, leaving a clean, machine-readable structure.

The output is a preliminary `.nc` file where every inference can be uniquely identified by the combination of its `flow_index` and its functional concept.

### **Step 3.2: Automated Context Distribution**

With a formalized plan, the system can now accurately distribute the context. It feeds two artifacts to an LLM guided by a specialized meta-prompt:

1.  The newly created **NormCode (`.nc`)** file.
2.  The **Initial Context Block** from Phase 1.

The LLM's task is to act as a context-aware analyst. It iterates through each inference in the `.nc` file and determines which specific pieces of the `Initial Context Block` are necessary and sufficient for that inference to be executed correctly. A key part of this process is identifying when multiple inferences require the exact same local context. When such an overlap is found, the LLM creates a single, shared context file to be referenced by all relevant inferences, thus avoiding redundancy.

-   **Input:** The `.nc` file and the `Initial Context Block`.
-   **LLM Process:** For each inference, the model selects only the relevant details from the `Initial Context Block`, creating a tailored, minimal-but-complete local context. It then de-duplicates these local contexts to create a set of unique context files, some of which may be shared.
-   **Output:** A **`context_store` directory** and a **`context_manifest.json`** file.
       - The `context_store` directory contains a separate `.txt` file for each unique local context. Files used by only one inference are named after their inference ID. Files shared by multiple inferences follow a distinct naming pattern (e.g., `shared---<description>.txt`).
       - The `context_manifest.json` file acts as an index, mapping the full inference ID to the file path of its corresponding context file. Multiple inferences can point to the same shared context file.

**Example:**

-   **Input (`.nc` snippet):**
    ```normcode
    ...
    3.1 ::(log validation success)
        <= ...
    ...
    3.2 ::(log validation failure)
        <= ...
    ...
    4.1 ::(create user account)
        <= ...
    ...
    ```
-   **Input (`Initial Context Block`):**
    `"All logging should be sent to the 'audit-log' service via the 'log_event' tool. The user account creation should be done against the 'users' table in the PostgreSQL database."`
-   **Output (Directory Structure & File Contents):**
 
   - **`context_store/`**
     - **`shared---logging_details.txt`**
       ```
       All logging should be sent to the 'audit-log' service via the 'log_event' tool.
       ```
     - **`4.1---create_user_account.txt`**
       ```
       The user account creation should be done against the 'users' table in the PostgreSQL database.
       ```
 
   - **`context_manifest.json`**
     ```json
     {
       "context_mapping": {
         "3.1 ::(log validation success)": "./context_store/shared---logging_details.txt",
         "3.2 ::(log validation failure)": "./context_store/shared---logging_details.txt",
         "4.1 ::(create user account)": "./context_store/4.1---create_user_account.txt"
       }
     }
     ```

### **Step 3.3: Manual Review and Refinement (Optional)**

After the automated distribution, the generated `context_store` directory and its manifest are available for review. A developer can inspect the individual context files and the mapping to ensure that each inference has received the correct context—nothing more, nothing less. This step allows for fine-tuning that can be critical for the final materialization phase.

---
## **Phase 4: Materialization into an Executable Script**

This final phase translates the formalized `.nc` plan and its distributed context into a complete, tangible, and runnable Python script. This is where the abstract plan is materialized into executable code that the `Orchestrator` can run.

### **Step 4.1: Automated Script Generation**

The core of this phase is an automated "NormCode-to-Python" compilation process, driven by an LLM guided by a specialized meta-prompt.

-   **Input:**
    1.  The formalized **NormCode (`.nc`)** file from Phase 3.
    2.  The **`context_store` directory** and **`context_manifest.json`** from Phase 3.

-   **LLM Process:** The LLM iterates through the `.nc` plan and its associated context to generate a Python script. For each concept and inference, it generates the corresponding `ConceptEntry` and `InferenceEntry` Python object.

    The most critical task in this step is synthesizing the `working_interpretation` for each `InferenceEntry`. The LLM combines the semantic meaning of the inference (from the `.nc` file) with its specific local context (from the `context_store`) to generate a precise set of instructions for the `Orchestrator`. This could be a direct tool call, a prompt for another LLM, or other structured commands.

-   **Output:**
    - **Repository JSON files (`concept_repo.json`, `inference_repo.json`):** These files contain the structured definitions for all `ConceptEntry` and `InferenceEntry` objects in the plan.
    - **An Executable Python Script (`.py`):** This script is now a lightweight runner. It contains the necessary boilerplate to load the repository JSON files, initialize the `Orchestrator`, and execute the plan.

### **Example of Generated Files**

Below are snippets of the files that would be generated for our user registration example.

**1. `concept_repo.json` (Snippet)**

This file defines all the concepts used in the plan.

```json
[
  {
    "id": "...",
    "concept_name": "{user name}",
    "type": "{}",
    "description": "The username provided for registration."
  },
  {
    "id": "...",
    "concept_name": "::<username exists?>",
    "type": "<{}>",
    "description": "A judgement to check if the username is already in the database."
  }
]
```

**2. `inference_repo.json` (Snippet)**

This file defines all the inferences, including their `working_interpretation` which was synthesized from the local context.

```json
[
  {
    "id": "...",
    "inference_sequence": "judgement_direct",
    "concept_to_infer": "::<username exists?>",
    "function_concept": "::<username exists?>",
    "value_concepts": ["{user name}"],
    "flow_info": {"flow_index": "1.1.2.1"},
    "working_interpretation": {
        "tool_name": "database_query",
        "parameters": {
            "sql_query": "SELECT EXISTS(SELECT 1 FROM users WHERE username ILIKE '{1}')"
        },
        "value_order": {
            "{user name}": 1
        }
    }
  }
]
```

**3. Executable Python Script (`run_plan.py`)**

This script loads the repositories and runs the plan.

```python
from infra import Orchestrator, ConceptRepo, InferenceRepo

# Load the repositories from the generated JSON files
concept_repo = ConceptRepo.from_json("concept_repo.json")
inference_repo = InferenceRepo.from_json("inference_repo.json")

# Initialize and run the orchestrator
orchestrator = Orchestrator(
    concept_repo=concept_repo,
    inference_repo=inference_repo,
    # ... other configurations ...
)
final_concepts = orchestrator.run()

print("Plan execution complete.")
```

### **Step 4.2: Manual Review and Refinement (Optional)**

The final generated files (`.py`, `.json`) are available for human review. This allows a developer to inspect the repository definitions and the runner script—particularly the synthesized `working_interpretation` for each inference in the `inference_repo.json`—to ensure correctness and safety before execution.
