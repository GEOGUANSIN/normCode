# The Comprehensive NormCode Translation Guide

This document provides a unified, comprehensive guide to the NormCode translation algorithm. It synthesizes the formal process, core concepts, and operator examples into a single reference for translating natural language `normtext` into a structured NormCode plan.

## 1. Fundamental NormCode Concepts

Before detailing the algorithm, it's important to understand the basic building blocks of NormCode.

*   **Inference:** The core unit of NormCode. An inference is a single logical step in a plan. It consists of a **function/operation (`<=`)** which defines the operation to be performed, and the **Values (`<-`)** which are the inputs or ingredients for that action.
*   **Concepts:** These are the "words" of NormCode, representing the ideas, data, and actions in the plan. The main types are:
    *   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
    *   `<>` **Statement**: A statement that can be true or false (e.g., `<the user is an admin>`).
    *   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
    *   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

## 2. The Role of Annotations

These annotations are fundamental to managing the state of the decomposition process.

*   `...:` **Source Text Annotation**: Holds the piece of the original `normtext` currently being analyzed. A concept is considered "un-decomposed" as long as it has a `...:` annotation that has not yet been fully parsed.
*   `?:` **Question Annotation**: The question being asked about the concept, derived from the `...:` text.
*   `/:` **Description Annotation**: A human-readable description of the *result* of the decomposition for that concept.

The recursion for a branch is **complete** when the `...:` annotation has been fully consumed and a definitive `/:` annotation has been generated.

## 3. The Unified Translation Algorithm

The translation process consists of a one-time setup followed by a core recursive loop that progressively decomposes the `normtext`.

### 3.1. Step 1: Initialization

The process is initialized with two steps that occur only once:

1.  A single, top-level concept is created, and the entire, unprocessed `normtext` is placed in its source text annotation (`...:`).
2.  This top-level concept is analyzed to determine its initial **Inference Target**. This target represents the overall goal of the text and is classified into one of two main categories:
    *   **Action-like**: Represents something that is performed or evaluated.
        *   **Imperatives (`::()`):** A process, command, or action to be executed (e.g., `::(bake)`).
        *   **Judgements (`::< >`):** An inquiry that evaluates the truth of a statement (e.g., asking if a condition is true).
    *   **Object-like**: Represents a static entity, concept, or the relationship between them.
        *   **Subject Declarations (`:S:`):** Defines the primary subject of a block (e.g., :LLM:).
        *   **Statements (`<>`):** An assertion of fact (e.g., `<Kelly is beautiful>`).
        *   **Objects (`{}`):** A single entity or concept (e.g., `{user account}`).
        *   **Relations (`[]`):** Represents the relationship between concepts (e.g., [{position} and {number}]).

### 3.2. Step 2: The Core Recursive Decomposition Loop

The loop runs for any concept that has an un-parsed `...:` annotation. For each such concept, it performs the following steps:

*   **A. Formulate the Question (`?:`)**: Based on the concept's already-determined Inference Target and its `...:` text, formulate the specific question being answered (e.g., "How is this done?"). This question is classified into a type, such as **Methodology Declaration** or **Classification**.
*   **B. Select the Operator (`<=`)**: Based on the question type, select the appropriate `NormCode` operator that will structure the answer (e.g., `@by`, `$.`). The next section provides a detailed reference of all operators.
*   **C. Decompose and Prepare Children (`<-`)**: The operator is applied to the current concept, creating new child concepts. The parent's `...:` text is then partitioned and distributed to these children. Finally, for each new child, its own **Inference Target** is determined from its new `...:` snippet, preparing it for a subsequent run of the loop.

The translation is complete when no concepts with un-parsed `...:` annotations remain.

## 4. NormCode Operator Reference

This section details the available operators, the questions they answer, and provides a concrete example for each.

### 4.1. Object-Like Concept Operators

These operators are used to define, specify, and manipulate concepts that represent things or objects.

#### **`.`** (Specification)
*   **Question Type**: Classification/Specification (e.g., "What is a user account?").
*   **Description**: Defines a concept by relating it to another, more general concept.
*   **Example**:
    ```normcode
    :<:({user account})
        ...: A user account is a record containing a username and password.
        ?: What is a user account?
        <= $.({record})
            /: It is specified as a record among components.
        <- {record}
            ...: A record containing a username and password.
        <- {username}
            ...: A username for the user account.
        <- {password}
            ...: A password for the user account.
    ```

#### **`$::`** (Nominalization)
*   **Question Type**: Nominalization (e.g., "What is user authentication?").
*   **Description**: Transforms a process or action into a noun or object.
*   **Example**:
    ```normcode
    :<:({User Authentication})
        ...: User authentication is the process of verifying a user's identity.
        ?: What is user authentication?
        <= $::
            /: It is defined as a process.
        <- ::(verify the user's identity)
            ...: The action is to verify the user's identity.
    ```

#### **`$+`** (Continuation/Extension)
*   **Question Type**: Continuation/Extension (e.g., "What is the updated sequence?").
*   **Description**: Extends an existing concept or sequence.
*   **Example**:
    ```normcode
    :<:({updated sequence of numbers})
        ...: The updated sequence of numbers is the result of adding the new number to the old sequence of numbers.
        ?: What is the updated sequence of numbers?
        <= $+({new number}:{old sequence of numbers})
            /: It is the result of adding 1 to the old sequence of numbers.
        <- {new number}
            ...: The new number is the number to add to the old sequence of numbers.
        <- {old sequence of numbers}
            ...: The old sequence of numbers is the sequence of numbers before adding the new number.
    ```

#### **`$%`** (Instantiation)
*   **Question Type**: Instantiation (e.g., "What are all numbers?").
*   **Description**: Defines a concept by enumerating its specific instances.
*   **Example**:
    ```normcode
    :<:({number sequence})
        ...: The number sequence is 1, 2, 3, 4, 5.
        ?: What are all numbers?
        <= $%({number sequence})
            /: It is the abstraction of the sequence of numbers.
        <- [{1}, {2}, {3}, {4}, {5}]
            ...: The number sequence is 1, 2, 3, 4, 5.
    ```

#### **`$=`** (Identity)
*   **Question Type**: Identification (e.g., "what is the same number sequence").
*   **Description**: Asserts that a concept is identical to a specific marked instance of itself.
*   **Example**:
    ```normcode
    :<:({number sequence})
        ...: The number sequence is marked by {1}.
        ?: What is the number sequence?
        <= $={1}
            /: It is identical to itself as where marked by {1}
    ```

#### **`&in`** (Annotated Composition)
*   **Question Type**: Annotated Composition (e.g., "What is the value with position indexed?").
*   **Description**: Groups related data together, like creating a list of key-value pairs.
*   **Example**:
    ```normcode
    :<:([{value} with {position} indexed]) |ref. [{position: 1, value: 23}, {position: 2, value: 34}]
        ...: The value with position indexed is the sequence of numbers indexed by their position and value.
        ?: What is the value with position indexed?
        <= &in[{position}; {value}]
            /: It is grouped as a sequence of numbers, where position and value are complementary. 
        <- {position} |ref. [1, 2]
            ...: The position is the position of the number in the indexed number sequence.
        <- {value} |ref. [23, 34]
            ...: The value is the value of the number in the indexed number sequence.
    ```

#### **`&across`** (Ordered Composition)
*   **Question Type**: Ordered Composition (e.g., "What is the combination of two number sequences?").
*   **Description**: Concatenates or combines ordered concepts.
*   **Example**:
    ```normcode
    :<:({number sequence}) |ref. [1, 2, 3, 4, 5]
        ...: The number sequence is the combination of the number sequence 1 and the number sequence 2.
        ?: What is the number sequence?
        <= &across({number sequence})
            /: It is across the sequence of numbers.
        <- {number sequence 1} |ref. [1, 2, 3]
            ...: The number sequence 1 is 1, 2, 3.
        <- {number sequence 2} |ref. [4, 5]
            ...: The number sequence 2 is 4, 5.
    ```

#### **`::({})` or `:_:{}({})`** (Process Request)
*   **Question Type**: Process Request (e.g., "How do you find the user?").
*   **Description**: Describes a method or action that can be performed on or by an object.
*   **Unbounded Example (`::({})`)**:
    ```normcode
    :<:({the user})
        ...: Find the user with their name.
        ?: How do you find the user?
        <= ::(find user by {name})
            ...: It is done by finding the user by their name.
        <- {name}
            ...: The name of the user to be found.
    ```
*   **Bounded Example (`:_:{}({})`)**:
    ```normcode
    :<:({the user})
        ...: Find the user with their name according to the definition of the finding.
        ?: How do you find the user?
        <= :_:{find}({user name})
            ...: It is done by finding the user by their name.
        <- {user name}
            ...: The name of the user to be found.
        <- {find}
            ...: The definition of the finding.
    ```

#### **`:>:()` or `:<:()`** (I/O Request)
*   **Question Type**: I/O Request (e.g., "The user name is a primitive input?").
*   **Description**: Represents an action where data is received as input or produced as output.
*   **Input Example (`:>:()`)**:
    ```normcode
    :<:({user name})
        ...: the user name is inputed by the user.
        ?: How do you input the user name?
        <= :>:{user name}?()
            /: It is done by inputing the user name.
        <- {user name}?
            /: The definition of the user name.
    ```
*   **Output Example (`:<:()`)**:
    ```normcode
    :<:({outputing})
        ...: the user name is outputed by the user.
        ?: How do you output the user name?
        <= $::
            /: Outputing is defined as a process.
        <- :<:({user name})
            /: It is done by outputing the user name.
        <- {user name}
            ...: The user name to be outputed.
    ```

#### **`::<{}>` or `::{}({}):`** (Judgement Request)
*   **Question Type**: Judgement Request (e.g., "is a user an admin?").
*   **Description**: Represents a boolean state, condition, or quantified evaluation.
*   **Unbounded Example (`::<{}>`)**:
    ```normcode
    :<:(<user is an admin>)
        ...: The user is an admin.
        ?: What is the user?
        <= ::<{user} is an admin>
            ...: It is a judgement that the user is an admin.
        <- {user}
            ...: The user to be judged.
    ```
*   **Quantifier Example (`::{}({}):`)**:
    ```normcode
    :<:(<everything is on the table>)
        ...: Everything is on the table.
        ?: How to judge everything?
        <= ::{All%(True)}<{things} on the table>
            ...: It is done by quantifying the everything, and checking if the things are on the table.
        <- {things}
            ...: The things to be checked.
    ```

#### **`*every`** (Element-wise Breakdown)
*   **Question Type**: Element-wise Breakdown (e.g., "how to square a sequence by each of its member?").
*   **Description**: Applies an operation to each item in a collection.
*   **Example**:
    ```normcode
    :<:({number sequence squared}) |ref. [4, 9, 16, 25]
        ...: The number sequence squared is the sequence of numbers squared.
        ?: What is the number sequence squared?
        <= *every({number sequence})
            ...: It is done on each of the sequence of numbers, where the number is squared.
        <- {number sequence} |ref. [2, 3, 4, 5]
            ...: The number sequence is 2, 3, 4, 5.
    ```

### 4.2. Action-Like Concept Operators

These operators are used to define the logic, methods, and conditions related to actions.

#### **`@by`** (Methodology Declaration)
*   **Question Type**: Methodology Declaration (e.g., "How do you authenticate?").
*   **Description**: Specifies the means or method by which an action is performed.
*   **Example**:
    ```normcode
    :<:(::(Authenticate the user))
        ...: Authenticate the user by checking their password.
        ?: How do you authenticate the user?
        <= @by(:_:)
            /: It is done by a method.
        <- :_:{check password}({user})
            ...: by checking their password.
        <- {check password}
            ...: The definition of the checking password.
        <- {user}
            ...: The user to be authenticated.
    ```

#### **`@if` / `@if!`** (Conditional Dependency)
*   **Question Type**: Conditional Dependency (e.g., "When do you show the dashboard?").
*   **Description**: Executes an action only if a certain condition is true (`@if`) or false (`@if!`).
*   **Example (`@if`)**:
    ```normcode
    :<:(::(Show the admin dashboard))
        ...: Show the admin dashboard if the user is an admin.
        ?: When do you show the admin dashboard?
        <= @if(<user is an admin>)
            /: It is done only if the user is an admin.
        <- <user is an admin>
            ...: if the user is an admin.
    ```
*   **Example (`@if!`)**:
    ```normcode
    :<:(::(Show the admin dashboard))
        ...: Show the admin dashboard if the user is not an admin.
        ?: When do you show the admin dashboard?
        <= @if!(<user is not an admin>)
            /: It is done only if the user is not an admin.
        <- <user is not an admin>
            ...: if the user is not an admin.
    ```

#### **`@after`** (Sequential Dependency)
*   **Question Type**: Sequential Dependency (e.g., showing a dashboard after authentication).
*   **Description**: Specifies that an action occurs after another event or action has completed.
*   **Example**:
    ```normcode
    :<:(::(Show the admin dashboard))
        ...: Show the admin dashboard after the user is authenticated.
        ?: When do you show the admin dashboard?
        <= @after({admin dashboard})
            /: It is done after the admin dashboard is shown.
        <- {admin dashboard}
            ...: The admin dashboard to be shown.
    ```

## 5. Walkthrough: "User Registration" Example

This section provides a complete, step-by-step walkthrough of the algorithm using a practical example.

### 5.1. Initialization
*   The entire `normtext` is placed in the `...:` of a top-level concept.
*   The **Inference Target** is determined to be `::(register a new user)`.

```normcode
...: "To register a new user, first check if the provided username already exists in the database. If it does, report an error. Otherwise..."
:<:(::(register a new user))
```

### 5.2. Core Loop (Iteration 1)
The loop runs on the top-level concept.
*   **A. Question**: "How to register a new user?" (**Methodology Declaration**).
*   **B. Operator**: `@by`.
*   **C. Decompose**: The `@by` operator is applied. The `...:` text is passed to new child concepts.

```normcode
...: "first check if the provided username already exists in the database. If it does, report an error. Otherwise, create a new user account."
:<:(::(register a new user)) 
    ?: How to register a new user?
    <= @by(:_:)
        /: "The registration is requesting another process to be executed."
    <- :_:{steps}({user name})
        /: "The process is normatively bounded in steps with a given user name."
    <- {steps}
        ...: "first, check if the provided username already exists."
        ...: "second, if it does, report an error."
        ...: "third, otherwise, create a new user account."
    <- {user name}
        ...: "the provided username is provided by the user."
```

### 5.3. Iteration 2: Decomposing `{steps}`
We'll now process the `{steps}` concept.
*   **A. Question**: "How is `{steps}` composed?" (**Ordered Composition**).
*   **B. Operator**: `&across`.
*   **C. Decompose**: We apply `&across`, which breaks `{steps}` into three ordered child objects.

```normcode
:<:(::(register a new user))
    <= @by(:_:)
    <- :_:{steps}({user name})
    <- {steps}
        ?: How are the steps composed?
        <= &across
            /: "The steps are an ordered sequence of actions."
        <- {step 1}
            ...: "first, check if the provided username already exists."
        <- {step 2}
            ...: "second, if it does, report an error."
        <- {step 3}
            ...: "third, otherwise, create a new user account."
    <- {user name}
        <= :>:{user name}?()
        /: "the provided username is provided by the user."
```

### 5.4. Iteration 3: Nominalization of Steps
Now we process the new step objects. The question is "What is this step?", which calls for **Nominalization**.
*   **For `{step 1}`**: The operator is `$::`.
*   **For `{step 2}`**: The operator is `$::`.
*   **For `{step 3}`**: The operator is `$::`.

```normcode
...
    <- {steps}
        <= &across
        <- {step 1}
            ?: What is step 1?
            <= $::.<username exists>
                /: "Step 1 is nominalized as the action of checking if a username exists."
            <- ::<username exists>
                /: "The action is to check if the provided username already exists."
            <- {user name}
                /: "the provided username is provided by the user."
        <- {step 2}
            ?: What is step 2?
            <= $::.{error}
                /: "Step 2 is nominalized as the action of reporting an error."
            <- ::(report error)
                ...: "The action is to report an error, if the username already exists."
        <- {step 3}
            ?: What is step 3?
            <= $::.{new user account}
                /: "Step 3 is nominalized as the action of creating a new user account."
            <- ::(create new user account)
                ...: "The action is to create a new user account, if the username does not exist."
```

### 5.5. Iteration 4: Defining Conditional Dependencies
We now process the two actions with conditional logic. The question is "Under what condition does this happen?", which is a **Conditional Dependency**.
*   **For `::(report error)`**: The operator is `@if`.
*   **For `::(create new user account)`**: The operator is `@if!`.

This completes the decomposition. The final structure is:
```normcode
...
    <- ::(report error)
        ?: When should an error be reported?
        <= @if(::<username exists?>)
            /: "An error is reported if the username already exists."
    <- ::(create new user account)
        ?: When should a new user account be created?
        <= @if!(::<username exists?>)
            /: "A new account is created if the username does not exist."
...
```

### 5.6. Complete NormCode Draft
Here is the complete `normcode` draft, combining all decomposition steps.

```normcode
...: "first check if the provided username already exists in the database. If it does, report an error. Otherwise, create a new user account."
:<:(::(register a new user))
    ?: How to register a new user?
    <= @by(:_:)
        /: "The registration is requesting another process to be executed."
    <- :_:{steps}({user name})
        /: "The process is normatively bounded in steps with a given user name."
    <- {steps}
        ...: "first, check if the provided username already exists."
        ...: "second, if it does, report an error."
        ...: "third, otherwise, create a new user account."
        ?: How are the steps composed?
        <= &across
            /: "The steps are an ordered sequence of actions."
        <- {step 1}
            ...: "first, check if the provided username already exists."
            ?: What is step 1?
            <= $::.<username exists>
                /: "Step 1 is nominalized as the action of checking if a username exists."
            <- ::<username exists>
                /: "The action is to check if the provided username already exists."
            <- {user name}
                /: "the provided username is provided by the user."
        <- {step 2}
            ...: "second, if it does, report an error."
            ?: What is step 2?
            <= $::.{error}
                /: "Step 2 is nominalized as the action of reporting an error."
            <- ::(report error)
                ...: "The action is to report an error, if the username already exists."
                ?: When should an error be reported?
                <= @if(::<username exists>)
                    /: "An error is reported if the username already exists."
        <- {step 3}
            ...: "third, otherwise, create a new user account."
            ?: What is step 3?
            <= $::.{new user account}
                /: "Step 3 is nominalized as the action of creating a new user account."
            <- ::(create new user account)
                ...: "The action is to create a new user account, if the username does not exist."
                ?: When should a new user account be created?
                <= @if!(::<username exists>)
                    /: "A new account is created if the username does not exist."
    <- {user name}
        ...: "the provided username is provided by the user."
        <= :>:{user name}?()
        /: "the provided username is provided by the user."
```
