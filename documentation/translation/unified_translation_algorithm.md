# The Unified NormCode Translation Algorithm

This document outlines a unified, recursive algorithm for translating natural language `normtext` into a structured NormCode plan. The process consists of a one-time setup followed by a core recursive loop that progressively decomposes the `normtext`.

### 1. Initialization (Setup)

The process is initialized with two steps that occur only once:

*   A single, top-level concept is created, and the entire, unprocessed `normtext` is placed in its source text annotation (`...:`).
*   This top-level concept is analyzed to determine its initial **Inference Target** (e.g., `::(register a new user)`). This concept represents the overall goal and is now the first item ready for the decomposition loop.

### 2. The Core Recursive Decomposition Loop

The loop runs for any concept that has an un-parsed `...:` annotation. For each such concept, it performs the following steps to decompose it:

*   **A. Formulate the Question**: Based on the concept's already-determined Inference Target and its `...:` text, formulate the specific question being answered (e.g., "How is this done?"). This question is classified into a type, such as **Methodology Declaration** or **Classification**.
*   **B. Select the Operator**: Based on the question type, select the appropriate `NormCode` operator (`<=`) that will structure the answer (e.g., `@by`, `$.`).
*   **C. Decompose and Prepare Children**: The operator is applied to the current concept, creating new child concepts (`<-`). The parent's `...:` text is then partitioned and distributed to these children. Finally, for each new child, its own **Inference Target** is determined from its new `...:` snippet, preparing it for a subsequent run of the loop.

The loop continues naturally, as the children prepared in Step C now have the necessary components to be processed. The translation is complete when no concepts with un-parsed `...:` annotations remain.

---

### Detailed Breakdown of Question Types and Operators

This section details the options available during the "Formulate the Question" and "Select the Operator" steps of the loop.

#### Inference Target Types
*   **Action-like**: `::()` (process), `::< >` (judgement).
*   **Object-like**: `{}` (object), `<>` (statement), `[]` (relation).

#### Question Types & Operators
*   **For Object-like Targets**:
    *   **Classification/Specification (`$.`):** "What is...?"
    *   **Composition (`&across`, `&in`):** "How is this formed?"
    *   **Judgement Request (`::<{}>`):** "Is this true?"
*   **For Action-like Targets**:
    *   **Methodology Declaration (`@by`):** "How do you...?"
    *   **Conditional Dependency (`@if`):** "When do you...?"
    *   **Sequential Dependency (`@after`):** "What happens after...?"

---

### Example: The "User Registration" Decomposition

**1. Initialization**
*   The entire `normtext` is placed in the `...:` of a top-level concept.
*   The **Inference Target** is determined to be `::(register a new user)`.

```normcode
...: "To register a new user, first check if the provided username already exists in the database. If it does, report an error. Otherwise..."
:<:(::(register a new user))
```


**2. Core Loop (Iteration 1)**
The loop runs on the top-level concept.
*   **A. Question**: "How to register a new user?" (**Methodology Declaration**).
*   **B. Operator**: `@by`.
*   **C. Decompose**: The `@by` operator is applied. Its implementation is the logic within the `...:` text, so the text is passed to a new concept representing the method. This new concept's **Inference Target** is determined to be the conditional check.

```normcode
...: "first check if the provided username already exists in the database. If it does, report an error. Otherwise..."
:<:(::(register a new user)) 
    ?: How to register a new user?
    <= @by(:_:)
        /: "The registration is requesting another process to be executed."
    <- :_:{steps}({user name})
        /: "The process is normatively bounded in steps."
    <- {steps}
        ...: "first, check if the provided username already exists..."
        ...: "second, if it does, report an error..."
        ...: "third, otherwise, create a new user account..."
    <- {user name}
        ...: "the provided username is provided by the user."
```


