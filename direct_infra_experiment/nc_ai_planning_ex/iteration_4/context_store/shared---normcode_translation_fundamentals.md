# NormCode Translation Fundamentals

This document provides a consolidated overview of the core concepts of NormCode that are essential for the translation process.

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
