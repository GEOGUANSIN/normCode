# From Prompt to Actionable Intelligence: The NormCode Translation Pipeline in Depth

This document provides a detailed, practical walkthrough of **NormCode AI Planning**: a methodology for bootsrapping from a high-level natural language prompt into a structured and executable NormCode plan. This translation process is to be uniquely **powered by a NormCode plan itself**, creating a meta-algorithm that allows the system to understand, decompose, and act upon complex instructions.

We will illustrate the pipeline using a concrete example.

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

## **Phase 1: Instruction Confirmation and Deconstruction (Steps 1-3)**

This phase is about parsing the initial prompt, confirming the core task, and creating the first-pass structural representation in NormCode.

### **Step 1: Confirm the Core Instruction from the Raw Prompt**

The first, and most critical, step is to process the raw, conversational prompt and distill it into a clear, structured, and unambiguous instruction. This involves identifying the core intent and removing conversational filler.

-   **Analysis of Raw Prompt:**
    -   "Hey, can you set up the user registration flow for me?" -> Conversational opener, ignored.
    -   "Basically, when a new user signs up..." -> Sets the context.
    -   "...we need to make sure their username isn't already taken." -> Core logic: Check for existing username.
    -   "If it is, just tell them it's unavailable." -> Core logic: Conditional error reporting.
    -   "If it's free, go ahead and create their account." -> Core logic: Conditional account creation.
    -   "Oh, and for the username check, it shouldn't matter if it's 'John' or 'john', you know? Just treat them the same." -> A specific constraint on the checking logic.
    -   "For the password, just make something up that's secure." -> Vague instruction that needs to be clarified into a specific action: "securely generate a password".

-   **Synthesized, Confirmed Instruction:**
    ```
    "To register a new user, first check if the provided username already exists in the database. If it does, report an error. Otherwise, create a new user account with the provided username and a securely generated password. The username should be considered case-insensitive during the check."
    ```
This confirmed instruction is now the clean input for the rest of the translation pipeline.

### **Step 2: Isolate the Core Logic and All Contexts**

The system now takes the *confirmed instruction* and the *system context* to separate the procedural logic from all non-procedural constraints.

-   **Instruction Block:** "To register a new user, first check if the provided username already exists in the database. If it does, report an error. Otherwise, create a new user account with the provided username and a securely generated password." (Derived from user prompt)
-   **User Context Block:** "The username should be considered case-insensitive during the check." (Derived from user prompt)
-   **System Context Block:** Information about the PostgreSQL database and the `database_query` and `generate_secure_password` tools.

This is a crucial first step. The **Instruction Block** contains the procedural logic—the "what to do"—while the **Context Block** contains non-procedural constraints and details—the "how to do it."

### **Step 3: Translate the Instruction into a NormCode Draft**

The `NormCode AI Planning` process applies the formal algorithm from the `comprehensive_normcode_translation_guide.md` to the **Instruction Block**. This is a recursive process of questioning and decomposition.

1.  **Top-Level Goal:** The overall goal is identified as an action: `::(register a new user)`.
2.  **Decomposition:** The agent asks, "How is this done?" The answer involves a sequence of steps, which are broken down using operators like `@by`, `&across`, `@if`, and `$::`.

This results in the following **NormCode Draft**. This is the skeletal structure of the procedure, derived purely from the Instruction Block.

```normcode
:<:(::(register a new user))
    <= @by(:_:)
    <- :_:{steps}({user name})
    <- {steps}
        <= &across
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

At this point, we have a logical plan, but it's missing the critical detail from the context.

---

## **Phase 2: Contextualization and NormCode Interpretation (Steps 4-5)**

This phase enriches the structural plan with the nuanced, non-procedural information required for correct execution.

### **Step 4: Identify Leftover Contexts**

The system identifies all context that hasn't been encoded in the NormCode's structure.

-   **User Context:** `{"check_constraint": "username check must be case-insensitive"}`
-   **System Context:** `{"db_type": "PostgreSQL", "user_table": "users", "username_column": "username", "tool": "database_query"}`

### **Step 5: Distribute All Context to Relevant Nodes**

The system now analyzes all context blocks and attaches them to the specific NormCode components where they apply.

-   **Node `::<username exists?>`:** Receives both user and system context, as it needs to know *how* to check (case-insensitive) and *what* to check against (the PostgreSQL database).
    -   **Local Context:**
        ```json
        {
          "user_constraint": "case-insensitive",
          "system_details": {
            "db_type": "PostgreSQL",
            "user_table": "users",
            "username_column": "username",
            "tool_to_use": "database_query"
          }
        }
        ```
-   **Node `::(securely generate a password)`:** This node only needs the relevant system context.
    -   **Local Context:** `{"system_details": {"tool_to_use": "generate_secure_password"}}`

---

## **Phase 3: Materialization into Executable Repositories (Step 6)**

This final phase translates the enriched NormCode components into the concrete data structures (`ConceptRepo` and `InferenceRepo`) required for execution by the `Orchestrator`. This is where the abstract plan becomes a tangible, runnable program.

### **Step 6: Generate Repositories and Interpretations**

The system iterates through the context-enriched NormCode graph to generate the final `ConceptEntry` and `InferenceEntry` objects. This involves creating prompt files for LLM-driven steps and defining the `working_interpretation` for each inference.

For each NormCode component, the system combines the component's semantic meaning with its attached Local Context to generate a final, self-contained prompt.

**Example 1: The Username Existence Check Judgement**

This is the most powerful example, as it combines user and system context to generate a precise, executable tool call instead of a generic prompt.

1.  **Synthesize Action:** The system analyzes the enriched node for `::<username exists?>`.
    -   **Goal:** Perform a true/false check.
    -   **User Context:** Must be case-insensitive.
    -   **System Context:** Use the `database_query` tool on a PostgreSQL database.
    -   **Conclusion:** The correct action is to generate a case-insensitive SQL query for PostgreSQL.

2.  **Generate `working_interpretation` for the `InferenceEntry`:** Instead of creating a prompt file for an LLM, the system now generates a precise `working_interpretation` that configures a direct tool call.

    ```python
    # In the InferenceEntry for the username check:
    "working_interpretation": {
        "tool_name": "database_query",
        "parameters": {
            "sql_query": "SELECT EXISTS(SELECT 1 FROM users WHERE username ILIKE '{1}')"
        },
        "value_order": {
            "{user name}": 1
        }
    }
    ```
    *Note: The system correctly chose `ILIKE` for a case-insensitive search in PostgreSQL based on the combined context.*

**Example 2: The Secure Password Generation Imperative**

1.  **Synthesize Action:** The system analyzes the `::(securely generate a password)` node.
    -   **Goal:** Generate a secure password.
    -   **System Context:** Use the `generate_secure_password` tool.

2.  **Generate `working_interpretation`:**

    ```python
    # In the InferenceEntry for password generation:
    "working_interpretation": {
        "tool_name": "generate_secure_password",
        "parameters": {}
    }
    ```

**Example 3: The Error Reporting Imperative**

1.  **Synthesize Action:** The system analyzes the `::(report error)` node.
    -   **Goal:** Report an error to the user.
    -   **User Context:** The error message should be friendly and informative.
    -   **System Context:** The error message should be in a format suitable for the LLM to understand.

2.  **Generate `working_interpretation`:**

    ```python
    # In the InferenceEntry for error reporting:
    "working_interpretation": {
        "tool_name": "LLM",
        "parameters": {
            "prompt": "I apologize, but the username '{user name}' is already in use. Please choose a different one."
        },
        "value_order": {
            "{user name}": 1
        }
    }
    ```

### **Final Result**

The final output of this phase is a complete, machine-readable, and executable plan. The `ConceptRepo` and `InferenceRepo` are now populated with entries that can directly execute tool calls with precise, context-aware parameters. The `Orchestrator` can run this plan, interacting with the defined system tools to accomplish the user's goal with no ambiguity.
