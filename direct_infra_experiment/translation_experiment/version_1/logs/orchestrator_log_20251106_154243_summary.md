# Step Summary: MFP Names, MVP Values, and OR Outputs

**Extracted from orchestrator log for judgement and imperative sequences**

**Total Sequences Found**: 79

## Statistics

- **Total Sequences**: 79
- **Sequence Types**: {'IMPERATIVE INPUT': 1, 'IMPERATIVE DIRECT': 67, 'JUDGEMENT DIRECT': 11}

### Data Coverage
- **MFP Names**: 79/79 (100.0%)
- **MVP Values**: 34/79 (43.0%)
- **OR Outputs**: 78/79 (98.7%)
- **Complete** (MFP + OR): 78/79 (98.7%)

### Timeline
- **First Sequence**: 2025-11-06 15:42:44,237
- **Last Sequence**: 2025-11-06 15:57:09,447
- **Total Duration**: 865.21 seconds

---

## Sequence 1: IMPERATIVE INPUT (#1)
**Timestamp**: 2025-11-06 15:42:44,237

### MFP Step Name
```
:>:({prompt}<:{normtext}>)
```

### MVP Values
```
[
  {
    'prompt_text': """**What is Normtext?**

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
"""
  }
]
```

### OR Output
```
['%69d(To register a new user, first check if the provided username already exists in the database. If it does, report an error. Otherwise, create a new user account.)']
```

---

## Sequence 2: IMPERATIVE DIRECT (#1)
**Timestamp**: 2025-11-06 15:42:57,982

### MFP Step Name
```
::{%(direct)}({prompt}<$({initialization prompt})%>: initialize normcode draft)
```

### OR Output
```
['%3c2(:<:(::(register a new user))
    ...: To register a new user, first check if the provided username already exists in the database. If it does, report an error. Otherwise, create a new user account.)']
```

---

## Sequence 3: JUDGEMENT DIRECT (#1)
**Timestamp**: 2025-11-06 15:43:02,769

### MFP Step Name
```
::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" – meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

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

**Example 3: Complete Draft (with intermediate
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    ...: To register a new user, first check if the provided username already exists in the database. If it does, report an error. Otherwise, create a new user account."""
  }
]
```

### OR Output
```
['%6c2($(F)%)']
```

---

## Sequence 4: IMPERATIVE DIRECT (#2)
**Timestamp**: 2025-11-06 15:43:07,415

### MFP Step Name
```
::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode is a language for translating natural language into a structured plan. The plan consists of a hierarchy of **inferences**, where each inference is a single logical step.

**1. Core Structure:**
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

**2. Concept Types:**
Concepts are the "words" of NormCode. The main types are:
-   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
-   `<>` **Statement**: An assertion that can be true or false (e.g., `<the user is an admin>`).
-   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
-   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

Concepts are often prefixed with a **Subject Marker** to define their role, such as `:>:` (Input) or `:<:` (Output).

**3. Annotations:**
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. **A concept with a `...:` annotation is considered "un-decomposed."**
-   `?:` **Question**: The question being asked about the source text.
-   `/:` **Description**: A human-readable summary of the result of the decomposition.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decom
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    ...: To register a new user, first check if the provided username already exists in the database. If it does, report an error. Otherwise, create a new user account."""
  }
]
```

### OR Output
```
["%c5f({'concept to decomposed': ':<:(::(register a new user))', 'remaining normtext': '...: To register a new user, first check if the provided username already exists in the database. If it does, report an error. Otherwise, create a new user account.'})"]
```

---

## Sequence 5: IMPERATIVE DIRECT (#3)
**Timestamp**: 2025-11-06 15:43:10,409

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%5de({'question': 'By what method is ::(register a new user) performed?', 'question type': 'Methodology Declaration'})"]
```

---

## Sequence 6: IMPERATIVE DIRECT (#4)
**Timestamp**: 2025-11-06 15:43:16,287

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%667({'functional concept': '<= @by(:_:)'})"]
```

---

## Sequence 7: IMPERATIVE DIRECT (#5)
**Timestamp**: 2025-11-06 15:43:22,194

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%515({'children': ['<- :_:{check and create}(<username exists>, {create new user account})', '<- <username exists>', '<- {create new user account}']})"]
```

---

## Sequence 8: IMPERATIVE DIRECT (#6)
**Timestamp**: 2025-11-06 15:43:35,439

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%609({'new inference': ':<:(::(register a new user))\
    <= @by(:_:)\
        ...: If [the username exists], report an error; otherwise, create a new user account.\
    <- :_:{check and create}(<username exists>, {create new user account})\
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.\
    <- <username exists>\
        /: Check if the provided username already exists in the database.\
    <- {create new user account}\
        /: Create a new user account.'})"]
```

---

## Sequence 9: IMPERATIVE DIRECT (#7)
**Timestamp**: 2025-11-06 15:43:53,885

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode translates natural language into a structured plan of **inferences**. The translation process works by recursively finding a concept with un-decomposed source text (`...:`) and replacing it with a more detailed block.

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
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with th
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    ...: To register a new user, first check if the provided username already exists in the database. If it does, report an error. Otherwise, create a new user account.""",
    'input_2': "{'new inference': ':<:(::(register a new user))\
    <= @by(:_:)\
        ...: If [the username exists], report an error; otherwise, create a new user account.\
    <- :_:{check and create}(<username exists>, {create new user account})\
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.\
    <- <username exists>\
        /: Check if the provided username already exists in the database.\
    <- {create new user account}\
        /: Create a new user account.'}"
  }
]
```

### OR Output
```
['%9e7(:<:(::(register a new user))
    <= @by(:_:)
        ...: If [the username exists], report an error; otherwise, create a new user account.
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.)']
```

---

## Sequence 10: JUDGEMENT DIRECT (#2)
**Timestamp**: 2025-11-06 15:44:01,801

### MFP Step Name
```
::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" – meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

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

**Example 3: Complete Draft (with intermediate
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        ...: If [the username exists], report an error; otherwise, create a new user account.
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%bb5($(F)%)']
```

---

## Sequence 11: IMPERATIVE DIRECT (#8)
**Timestamp**: 2025-11-06 15:44:06,870

### MFP Step Name
```
::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode is a language for translating natural language into a structured plan. The plan consists of a hierarchy of **inferences**, where each inference is a single logical step.

**1. Core Structure:**
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

**2. Concept Types:**
Concepts are the "words" of NormCode. The main types are:
-   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
-   `<>` **Statement**: An assertion that can be true or false (e.g., `<the user is an admin>`).
-   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
-   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

Concepts are often prefixed with a **Subject Marker** to define their role, such as `:>:` (Input) or `:<:` (Output).

**3. Annotations:**
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. **A concept with a `...:` annotation is considered "un-decomposed."**
-   `?:` **Question**: The question being asked about the source text.
-   `/:` **Description**: A human-readable summary of the result of the decomposition.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decom
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        ...: If [the username exists], report an error; otherwise, create a new user account.
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
["%9ca({'concept to decomposed': '<= @by(:_:)', 'remaining normtext': '...: If [the username exists], report an error; otherwise, create a new user account.'})"]
```

---

## Sequence 12: IMPERATIVE DIRECT (#9)
**Timestamp**: 2025-11-06 15:44:11,469

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%1d6({'question': 'Under what condition is the creation of a new user account performed?', 'question type': 'Conditional Dependency'})"]
```

---

## Sequence 13: IMPERATIVE DIRECT (#10)
**Timestamp**: 2025-11-06 15:44:18,826

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%d74({'functional concept': '<= @if(<username does not exist>)'})"]
```

---

## Sequence 14: IMPERATIVE DIRECT (#11)
**Timestamp**: 2025-11-06 15:44:26,224

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%890({'children': ['<- <username does not exist>']})"]
```

---

## Sequence 15: IMPERATIVE DIRECT (#12)
**Timestamp**: 2025-11-06 15:44:33,585

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%e4d({'new inference': '<= @by(:_:)\
    <= @if(<username does not exist>)\
        ...: If [the username exists], report an error; otherwise, create a new user account.\
    <- <username does not exist>\
        /: The username is not already registered in the system.'})"]
```

---

## Sequence 16: IMPERATIVE DIRECT (#13)
**Timestamp**: 2025-11-06 15:44:46,835

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode translates natural language into a structured plan of **inferences**. The translation process works by recursively finding a concept with un-decomposed source text (`...:`) and replacing it with a more detailed block.

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
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with th
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        ...: If [the username exists], report an error; otherwise, create a new user account.
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.""",
    'input_2': "{'new inference': '<= @by(:_:)\
    <= @if(<username does not exist>)\
        ...: If [the username exists], report an error; otherwise, create a new user account.\
    <- <username does not exist>\
        /: The username is not already registered in the system.'}"
  }
]
```

### OR Output
```
['%839(:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
            ...: If [the username exists], report an error; otherwise, create a new user account.
        <- <username does not exist>
            /: The username is not already registered in the system.
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.)']
```

---

## Sequence 17: JUDGEMENT DIRECT (#3)
**Timestamp**: 2025-11-06 15:44:55,379

### MFP Step Name
```
::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" – meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

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

**Example 3: Complete Draft (with intermediate
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
            ...: If [the username exists], report an error; otherwise, create a new user account.
        <- <username does not exist>
            /: The username is not already registered in the system.
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%40e($(F)%)']
```

---

## Sequence 18: IMPERATIVE DIRECT (#14)
**Timestamp**: 2025-11-06 15:45:00,488

### MFP Step Name
```
::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode is a language for translating natural language into a structured plan. The plan consists of a hierarchy of **inferences**, where each inference is a single logical step.

**1. Core Structure:**
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

**2. Concept Types:**
Concepts are the "words" of NormCode. The main types are:
-   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
-   `<>` **Statement**: An assertion that can be true or false (e.g., `<the user is an admin>`).
-   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
-   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

Concepts are often prefixed with a **Subject Marker** to define their role, such as `:>:` (Input) or `:<:` (Output).

**3. Annotations:**
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. **A concept with a `...:` annotation is considered "un-decomposed."**
-   `?:` **Question**: The question being asked about the source text.
-   `/:` **Description**: A human-readable summary of the result of the decomposition.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decom
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
            ...: If [the username exists], report an error; otherwise, create a new user account.
        <- <username does not exist>
            /: The username is not already registered in the system.
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
["%ff3({'concept to decomposed': '<= @if(<username does not exist>)', 'remaining normtext': '...: If [the username exists], report an error; otherwise, create a new user account.'})"]
```

---

## Sequence 19: IMPERATIVE DIRECT (#15)
**Timestamp**: 2025-11-06 15:45:04,995

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%f90({'question': 'Under what condition should an error be reported and a new user account created?', 'question type': 'Conditional Dependency'})"]
```

---

## Sequence 20: IMPERATIVE DIRECT (#16)
**Timestamp**: 2025-11-06 15:45:14,114

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%0ba({'functional concept': '<= @if(<username does not exist>)'})"]
```

---

## Sequence 21: IMPERATIVE DIRECT (#17)
**Timestamp**: 2025-11-06 15:45:20,812

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%9a7({'children': ['<- <username does not exist>']})"]
```

---

## Sequence 22: IMPERATIVE DIRECT (#18)
**Timestamp**: 2025-11-06 15:45:29,508

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%e25({'new inference': '<= @if(<username does not exist>)\
    ...: If [the username exists], report an error; otherwise, create a new user account.\
    <- <username does not exist>\
        /: the condition where the username does not exist'})"]
```

---

## Sequence 23: IMPERATIVE DIRECT (#19)
**Timestamp**: 2025-11-06 15:45:52,775

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode translates natural language into a structured plan of **inferences**. The translation process works by recursively finding a concept with un-decomposed source text (`...:`) and replacing it with a more detailed block.

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
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with th
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
            ...: If [the username exists], report an error; otherwise, create a new user account.
        <- <username does not exist>
            /: The username is not already registered in the system.
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.""",
    'input_2': "{'new inference': '<= @if(<username does not exist>)\
    ...: If [the username exists], report an error; otherwise, create a new user account.\
    <- <username does not exist>\
        /: the condition where the username does not exist'}"
  }
]
```

### OR Output
```
['%746(:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.)']
```

---

## Sequence 24: JUDGEMENT DIRECT (#4)
**Timestamp**: 2025-11-06 15:46:02,572

### MFP Step Name
```
::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" – meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

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

**Example 3: Complete Draft (with intermediate
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%a2a($(F)%)']
```

---

## Sequence 25: IMPERATIVE DIRECT (#20)
**Timestamp**: 2025-11-06 15:46:11,253

### MFP Step Name
```
::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode is a language for translating natural language into a structured plan. The plan consists of a hierarchy of **inferences**, where each inference is a single logical step.

**1. Core Structure:**
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

**2. Concept Types:**
Concepts are the "words" of NormCode. The main types are:
-   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
-   `<>` **Statement**: An assertion that can be true or false (e.g., `<the user is an admin>`).
-   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
-   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

Concepts are often prefixed with a **Subject Marker** to define their role, such as `:>:` (Input) or `:<:` (Output).

**3. Annotations:**
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. **A concept with a `...:` annotation is considered "un-decomposed."**
-   `?:` **Question**: The question being asked about the source text.
-   `/:` **Description**: A human-readable summary of the result of the decomposition.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decom
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
["%f9a({'concept to decomposed': '<- :_:{check and create}(<username exists>, {create new user account})', 'remaining normtext': '...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.'})"]
```

---

## Sequence 26: IMPERATIVE DIRECT (#21)
**Timestamp**: 2025-11-06 15:46:18,444

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%6fd({'question': 'By what method is the input operation {check and create} performed?', 'question type': 'Methodology Declaration'})"]
```

---

## Sequence 27: IMPERATIVE DIRECT (#22)
**Timestamp**: 2025-11-06 15:46:25,127

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%3f2({'functional concept': '<= @by(:_:)'})"]
```

---

## Sequence 28: IMPERATIVE DIRECT (#23)
**Timestamp**: 2025-11-06 15:46:33,498

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%b25({'children': ['<- :_:{check}(<username exists>)', '<- :_:{report error}()', '<- :_:{create}({new user account})']})"]
```

---

## Sequence 29: IMPERATIVE DIRECT (#24)
**Timestamp**: 2025-11-06 15:46:51,119

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%5c6({'new inference': '<- :_:{check and create}(<username exists>, {create new user account})\
    <= @by(:_:)\
        ...: If it does, report an error. Otherwise, create a new user account.\
    <- :_:{check}(<username exists>)\
        ...: First check if the provided username already exists.\
    <- :_:{report error}()\
        /: Report an error if the username exists.\
    <- :_:{create}({new user account})\
        /: Create a new user account if the username does not exist.'})"]
```

---

## Sequence 30: IMPERATIVE DIRECT (#25)
**Timestamp**: 2025-11-06 15:47:14,534

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode translates natural language into a structured plan of **inferences**. The translation process works by recursively finding a concept with un-decomposed source text (`...:`) and replacing it with a more detailed block.

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
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with th
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        ...: First check if the provided username already exists. If it does, report an error. Otherwise, create a new user account.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.""",
    'input_2': "{'new inference': '<- :_:{check and create}(<username exists>, {create new user account})\
    <= @by(:_:)\
        ...: If it does, report an error. Otherwise, create a new user account.\
    <- :_:{check}(<username exists>)\
        ...: First check if the provided username already exists.\
    <- :_:{report error}()\
        /: Report an error if the username exists.\
    <- :_:{create}({new user account})\
        /: Create a new user account if the username does not exist.'}"
  }
]
```

### OR Output
```
['%aa1(:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @by(:_:)
            ...: If it does, report an error. Otherwise, create a new user account.
        <- :_:{check}(<username exists>)
            ...: First check if the provided username already exists.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.)']
```

---

## Sequence 31: JUDGEMENT DIRECT (#5)
**Timestamp**: 2025-11-06 15:47:27,707

### MFP Step Name
```
::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" – meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

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

**Example 3: Complete Draft (with intermediate
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @by(:_:)
            ...: If it does, report an error. Otherwise, create a new user account.
        <- :_:{check}(<username exists>)
            ...: First check if the provided username already exists.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%b74($(F)%)']
```

---

## Sequence 32: IMPERATIVE DIRECT (#26)
**Timestamp**: 2025-11-06 15:47:42,358

### MFP Step Name
```
::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode is a language for translating natural language into a structured plan. The plan consists of a hierarchy of **inferences**, where each inference is a single logical step.

**1. Core Structure:**
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

**2. Concept Types:**
Concepts are the "words" of NormCode. The main types are:
-   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
-   `<>` **Statement**: An assertion that can be true or false (e.g., `<the user is an admin>`).
-   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
-   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

Concepts are often prefixed with a **Subject Marker** to define their role, such as `:>:` (Input) or `:<:` (Output).

**3. Annotations:**
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. **A concept with a `...:` annotation is considered "un-decomposed."**
-   `?:` **Question**: The question being asked about the source text.
-   `/:` **Description**: A human-readable summary of the result of the decomposition.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decom
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @by(:_:)
            ...: If it does, report an error. Otherwise, create a new user account.
        <- :_:{check}(<username exists>)
            ...: First check if the provided username already exists.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
["%0bb({'concept to decomposed': '<- :_:{check}(<username exists>)', 'remaining normtext': '...: First check if the provided username already exists.'})"]
```

---

## Sequence 33: IMPERATIVE DIRECT (#27)
**Timestamp**: 2025-11-06 15:47:58,749

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%aab({'question': 'How to judge the truth of the statement <username exists>?', 'question type': 'Judgement Request'})"]
```

---

## Sequence 34: IMPERATIVE DIRECT (#28)
**Timestamp**: 2025-11-06 15:48:06,437

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%24f({'functional concept': '<= :_:{check}(<username exists>)'})"]
```

---

## Sequence 35: IMPERATIVE DIRECT (#29)
**Timestamp**: 2025-11-06 15:48:13,800

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%941({'children': ['<- {provided username}']})"]
```

---

## Sequence 36: IMPERATIVE DIRECT (#30)
**Timestamp**: 2025-11-06 15:48:24,745

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%c5e({'new inference': '<- :_:{check}(<username exists>)\
    <= :_:{check}(<username exists>)\
        ...: if the provided username already exists.\
    <- {provided username}\
        /: The username that was provided for the check.'})"]
```

---

## Sequence 37: IMPERATIVE DIRECT (#31)
**Timestamp**: 2025-11-06 15:48:34,884

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode translates natural language into a structured plan of **inferences**. The translation process works by recursively finding a concept with un-decomposed source text (`...:`) and replacing it with a more detailed block.

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
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with th
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @by(:_:)
            ...: If it does, report an error. Otherwise, create a new user account.
        <- :_:{check}(<username exists>)
            ...: First check if the provided username already exists.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.""",
    'input_2': "{'new inference': '<- :_:{check}(<username exists>)\
    <= :_:{check}(<username exists>)\
        ...: if the provided username already exists.\
    <- {provided username}\
        /: The username that was provided for the check.'}"
  }
]
```

### OR Output
```
['%2d2(:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @by(:_:)
            ...: If it does, report an error. Otherwise, create a new user account.
        <- :_:{check}(<username exists>)
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.)']
```

---

## Sequence 38: JUDGEMENT DIRECT (#6)
**Timestamp**: 2025-11-06 15:48:51,136

### MFP Step Name
```
::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" – meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

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

**Example 3: Complete Draft (with intermediate
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @by(:_:)
            ...: If it does, report an error. Otherwise, create a new user account.
        <- :_:{check}(<username exists>)
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%45e($(F)%)']
```

---

## Sequence 39: IMPERATIVE DIRECT (#32)
**Timestamp**: 2025-11-06 15:49:12,206

### MFP Step Name
```
::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode is a language for translating natural language into a structured plan. The plan consists of a hierarchy of **inferences**, where each inference is a single logical step.

**1. Core Structure:**
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

**2. Concept Types:**
Concepts are the "words" of NormCode. The main types are:
-   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
-   `<>` **Statement**: An assertion that can be true or false (e.g., `<the user is an admin>`).
-   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
-   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

Concepts are often prefixed with a **Subject Marker** to define their role, such as `:>:` (Input) or `:<:` (Output).

**3. Annotations:**
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. **A concept with a `...:` annotation is considered "un-decomposed."**
-   `?:` **Question**: The question being asked about the source text.
-   `/:` **Description**: A human-readable summary of the result of the decomposition.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decom
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @by(:_:)
            ...: If it does, report an error. Otherwise, create a new user account.
        <- :_:{check}(<username exists>)
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%5b4({\'concept to decomposed\': \'<- :_:{check and create}(<username exists>, {create new user account})\', \'remaining normtext\': \'...: "If it does, report an error. Otherwise, create a new user account."\'})']
```

---

## Sequence 40: IMPERATIVE DIRECT (#33)
**Timestamp**: 2025-11-06 15:49:28,607

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%513({'question': 'Under what condition is {create new user account} performed?', 'question type': 'Conditional Dependency'})"]
```

---

## Sequence 41: IMPERATIVE DIRECT (#34)
**Timestamp**: 2025-11-06 15:49:36,859

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%fd1({'functional concept': '<= @if(<not(username exists)>)'})"]
```

---

## Sequence 42: IMPERATIVE DIRECT (#35)
**Timestamp**: 2025-11-06 15:49:41,300

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%4b5({'children': ['<- <not(username exists)>']})"]
```

---

## Sequence 43: IMPERATIVE DIRECT (#36)
**Timestamp**: 2025-11-06 15:49:48,276

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%f74({'new inference': '<- :_:{check and create}(<username exists>, {create new user account})\
    <= @if(<not(username exists)>)\
        ...: If it does, report an error. Otherwise, create a new user account.\
    <- <not(username exists)>\
        /: The condition is that the username does not exist.'})"]
```

---

## Sequence 44: IMPERATIVE DIRECT (#37)
**Timestamp**: 2025-11-06 15:50:10,614

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode translates natural language into a structured plan of **inferences**. The translation process works by recursively finding a concept with un-decomposed source text (`...:`) and replacing it with a more detailed block.

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
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with th
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @by(:_:)
            ...: If it does, report an error. Otherwise, create a new user account.
        <- :_:{check}(<username exists>)
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.""",
    'input_2': "{'new inference': '<- :_:{check and create}(<username exists>, {create new user account})\
    <= @if(<not(username exists)>)\
        ...: If it does, report an error. Otherwise, create a new user account.\
    <- <not(username exists)>\
        /: The condition is that the username does not exist.'}"
  }
]
```

### OR Output
```
['%221(:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(<not(username exists)>)
        ...: If it does, report an error. Otherwise, create a new user account.
        <- <not(username exists)>
            /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.)']
```

---

## Sequence 45: JUDGEMENT DIRECT (#7)
**Timestamp**: 2025-11-06 15:50:27,888

### MFP Step Name
```
::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" – meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

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

**Example 3: Complete Draft (with intermediate
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(<not(username exists)>)
        ...: If it does, report an error. Otherwise, create a new user account.
        <- <not(username exists)>
            /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%7a7($(F)%)']
```

---

## Sequence 46: IMPERATIVE DIRECT (#38)
**Timestamp**: 2025-11-06 15:50:45,336

### MFP Step Name
```
::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode is a language for translating natural language into a structured plan. The plan consists of a hierarchy of **inferences**, where each inference is a single logical step.

**1. Core Structure:**
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

**2. Concept Types:**
Concepts are the "words" of NormCode. The main types are:
-   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
-   `<>` **Statement**: An assertion that can be true or false (e.g., `<the user is an admin>`).
-   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
-   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

Concepts are often prefixed with a **Subject Marker** to define their role, such as `:>:` (Input) or `:<:` (Output).

**3. Annotations:**
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. **A concept with a `...:` annotation is considered "un-decomposed."**
-   `?:` **Question**: The question being asked about the source text.
-   `/:` **Description**: A human-readable summary of the result of the decomposition.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decom
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(<not(username exists)>)
        ...: If it does, report an error. Otherwise, create a new user account.
        <- <not(username exists)>
            /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%cb8({\'concept to decomposed\': \'<- :_:{check and create}(<username exists>, {create new user account})\', \'remaining normtext\': \'...: "If it does, report an error. Otherwise, create a new user account."\'})']
```

---

## Sequence 47: IMPERATIVE DIRECT (#39)
**Timestamp**: 2025-11-06 15:50:50,356

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%5a5({'question': 'Under what condition is the new user account created?', 'question type': 'Conditional Dependency'})"]
```

---

## Sequence 48: IMPERATIVE DIRECT (#40)
**Timestamp**: 2025-11-06 15:50:59,891

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%8a1({'functional concept': '<= @if(not <username exists>)'})"]
```

---

## Sequence 49: IMPERATIVE DIRECT (#41)
**Timestamp**: 2025-11-06 15:51:04,428

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%312({'children': ['<- <not <username exists>>']})"]
```

---

## Sequence 50: IMPERATIVE DIRECT (#42)
**Timestamp**: 2025-11-06 15:51:19,128

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%4f3({'new inference': '<- :_:{check and create}(<username exists>, {create new user account})\
    <= @if(not <username exists>)\
        ...: If it does, report an error. Otherwise, create a new user account.\
    <- <not <username exists>>\
        /: The condition is that the username does not exist.'})"]
```

---

## Sequence 51: IMPERATIVE DIRECT (#43)
**Timestamp**: 2025-11-06 15:51:37,055

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode translates natural language into a structured plan of **inferences**. The translation process works by recursively finding a concept with un-decomposed source text (`...:`) and replacing it with a more detailed block.

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
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with th
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(<not(username exists)>)
        ...: If it does, report an error. Otherwise, create a new user account.
        <- <not(username exists)>
            /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.""",
    'input_2': "{'new inference': '<- :_:{check and create}(<username exists>, {create new user account})\
    <= @if(not <username exists>)\
        ...: If it does, report an error. Otherwise, create a new user account.\
    <- <not <username exists>>\
        /: The condition is that the username does not exist.'}"
  }
]
```

### OR Output
```
['%2e6(:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.)']
```

---

## Sequence 52: JUDGEMENT DIRECT (#8)
**Timestamp**: 2025-11-06 15:51:59,383

### MFP Step Name
```
::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" – meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

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

**Example 3: Complete Draft (with intermediate
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%090($(F)%)']
```

---

## Sequence 53: IMPERATIVE DIRECT (#44)
**Timestamp**: 2025-11-06 15:52:13,590

### MFP Step Name
```
::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode is a language for translating natural language into a structured plan. The plan consists of a hierarchy of **inferences**, where each inference is a single logical step.

**1. Core Structure:**
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

**2. Concept Types:**
Concepts are the "words" of NormCode. The main types are:
-   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
-   `<>` **Statement**: An assertion that can be true or false (e.g., `<the user is an admin>`).
-   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
-   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

Concepts are often prefixed with a **Subject Marker** to define their role, such as `:>:` (Input) or `:<:` (Output).

**3. Annotations:**
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. **A concept with a `...:` annotation is considered "un-decomposed."**
-   `?:` **Question**: The question being asked about the source text.
-   `/:` **Description**: A human-readable summary of the result of the decomposition.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decom
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%894({\'concept to decomposed\': \'<= :_:{check}(<username exists>)\', \'remaining normtext\': \'...: "if the provided username already exists."\'})']
```

---

## Sequence 54: IMPERATIVE DIRECT (#45)
**Timestamp**: 2025-11-06 15:52:24,523

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%bc1({'question': 'How to judge the truth of the statement <username exists>?', 'question type': 'Judgement Request'})"]
```

---

## Sequence 55: IMPERATIVE DIRECT (#46)
**Timestamp**: 2025-11-06 15:52:30,317

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%2d6({'functional concept': '<= :_:{check}(<username exists>)'})"]
```

---

## Sequence 56: IMPERATIVE DIRECT (#47)
**Timestamp**: 2025-11-06 15:52:35,846

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%c31({'children': ['<- <username exists>', '<- {check}']})"]
```

---

## Sequence 57: IMPERATIVE DIRECT (#48)
**Timestamp**: 2025-11-06 15:52:47,293

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%f0b({'new inference': '<= :_:{check}(<username exists>)\
    ...: if the provided username already exists.\
    <- <username exists>\
        ...: the provided username already exists.\
    <- {check}\
        /: The action is to perform a verification.'})"]
```

---

## Sequence 58: IMPERATIVE DIRECT (#49)
**Timestamp**: 2025-11-06 15:52:59,046

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode translates natural language into a structured plan of **inferences**. The translation process works by recursively finding a concept with un-decomposed source text (`...:`) and replacing it with a more detailed block.

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
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with th
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
        ...: if the provided username already exists.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.""",
    'input_2': "{'new inference': '<= :_:{check}(<username exists>)\
    ...: if the provided username already exists.\
    <- <username exists>\
        ...: the provided username already exists.\
    <- {check}\
        /: The action is to perform a verification.'}"
  }
]
```

### OR Output
```
['%622(:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        ...: the provided username already exists.
    <- {check}
        /: The action is to perform a verification.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.)']
```

---

## Sequence 59: JUDGEMENT DIRECT (#9)
**Timestamp**: 2025-11-06 15:53:16,178

### MFP Step Name
```
::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" – meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

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

**Example 3: Complete Draft (with intermediate
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        ...: the provided username already exists.
    <- {check}
        /: The action is to perform a verification.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%9f9($(F)%)']
```

---

## Sequence 60: IMPERATIVE DIRECT (#50)
**Timestamp**: 2025-11-06 15:53:36,072

### MFP Step Name
```
::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode is a language for translating natural language into a structured plan. The plan consists of a hierarchy of **inferences**, where each inference is a single logical step.

**1. Core Structure:**
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

**2. Concept Types:**
Concepts are the "words" of NormCode. The main types are:
-   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
-   `<>` **Statement**: An assertion that can be true or false (e.g., `<the user is an admin>`).
-   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
-   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

Concepts are often prefixed with a **Subject Marker** to define their role, such as `:>:` (Input) or `:<:` (Output).

**3. Annotations:**
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. **A concept with a `...:` annotation is considered "un-decomposed."**
-   `?:` **Question**: The question being asked about the source text.
-   `/:` **Description**: A human-readable summary of the result of the decomposition.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decom
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        ...: the provided username already exists.
    <- {check}
        /: The action is to perform a verification.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
["%ed7({'concept to decomposed': '<:>(::(register a new user))', 'remaining normtext': '...: If [the username exists], report an error; otherwise, create a new user account.'})"]
```

---

## Sequence 61: IMPERATIVE DIRECT (#51)
**Timestamp**: 2025-11-06 15:53:45,066

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%214({'question': 'Under what condition is ::(register a new user) executed?', 'question type': 'Conditional Dependency'})"]
```

---

## Sequence 62: IMPERATIVE DIRECT (#52)
**Timestamp**: 2025-11-06 15:53:53,227

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%563({'functional concept': '<= @if(<the username does not exist>)'})"]
```

---

## Sequence 63: IMPERATIVE DIRECT (#53)
**Timestamp**: 2025-11-06 15:54:01,011

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%146({'children': ['<- <the username does not exist>']})"]
```

---

## Sequence 64: IMPERATIVE DIRECT (#54)
**Timestamp**: 2025-11-06 15:54:07,208

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%a83({'new inference': '<:>(::(register a new user))\
    <= @if(<the username does not exist>)\
        ...: otherwise, create a new user account.\
    <- <the username does not exist>\
        ...: otherwise, create a new user account.'})"]
```

---

## Sequence 65: IMPERATIVE DIRECT (#55)
**Timestamp**: 2025-11-06 15:54:24,166

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode translates natural language into a structured plan of **inferences**. The translation process works by recursively finding a concept with un-decomposed source text (`...:`) and replacing it with a more detailed block.

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
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with th
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
    ...: If [the username exists], report an error; otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        ...: the provided username already exists.
    <- {check}
        /: The action is to perform a verification.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.""",
    'input_2': "{'new inference': '<:>(::(register a new user))\
    <= @if(<the username does not exist>)\
        ...: otherwise, create a new user account.\
    <- <the username does not exist>\
        ...: otherwise, create a new user account.'}"
  }
]
```

### OR Output
```
['%e67(:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
<:>(::(register a new user))
    <= @if(<the username does not exist>)
        ...: otherwise, create a new user account.
    <- <the username does not exist>
        ...: otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        ...: the provided username already exists.
    <- {check}
        /: The action is to perform a verification.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.)']
```

---

## Sequence 66: JUDGEMENT DIRECT (#10)
**Timestamp**: 2025-11-06 15:54:39,917

### MFP Step Name
```
::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" – meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

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

**Example 3: Complete Draft (with intermediate
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
<:>(::(register a new user))
    <= @if(<the username does not exist>)
        ...: otherwise, create a new user account.
    <- <the username does not exist>
        ...: otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        ...: the provided username already exists.
    <- {check}
        /: The action is to perform a verification.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%f49($(F)%)']
```

---

## Sequence 67: IMPERATIVE DIRECT (#56)
**Timestamp**: 2025-11-06 15:54:47,869

### MFP Step Name
```
::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode is a language for translating natural language into a structured plan. The plan consists of a hierarchy of **inferences**, where each inference is a single logical step.

**1. Core Structure:**
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

**2. Concept Types:**
Concepts are the "words" of NormCode. The main types are:
-   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
-   `<>` **Statement**: An assertion that can be true or false (e.g., `<the user is an admin>`).
-   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
-   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

Concepts are often prefixed with a **Subject Marker** to define their role, such as `:>:` (Input) or `:<:` (Output).

**3. Annotations:**
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. **A concept with a `...:` annotation is considered "un-decomposed."**
-   `?:` **Question**: The question being asked about the source text.
-   `/:` **Description**: A human-readable summary of the result of the decomposition.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decom
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
<:>(::(register a new user))
    <= @if(<the username does not exist>)
        ...: otherwise, create a new user account.
    <- <the username does not exist>
        ...: otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        ...: the provided username already exists.
    <- {check}
        /: The action is to perform a verification.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
["%1a3({'concept to decomposed': '<= :_:{check}(<username exists>)', 'remaining normtext': '...: if the provided username already exists.'})"]
```

---

## Sequence 68: IMPERATIVE DIRECT (#57)
**Timestamp**: 2025-11-06 15:55:00,647

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%27a({'question': 'How to judge the truth of the statement <username exists>?', 'question type': 'Judgement Request'})"]
```

---

## Sequence 69: IMPERATIVE DIRECT (#58)
**Timestamp**: 2025-11-06 15:55:08,551

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%698({'functional concept': '<= :_:{check}(<username exists>)'})"]
```

---

## Sequence 70: IMPERATIVE DIRECT (#59)
**Timestamp**: 2025-11-06 15:55:13,967

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%e5b({'children': ['<- <username exists>', '<- {username}']})"]
```

---

## Sequence 71: IMPERATIVE DIRECT (#60)
**Timestamp**: 2025-11-06 15:55:25,183

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%f90({'new inference': '<= :_:{check}(<username exists>)\
    ...: if the provided username already exists.\
    <- <username exists>\
        /: the existence of the username\
    <- {username}\
        /: the provided username'})"]
```

---

## Sequence 72: IMPERATIVE DIRECT (#61)
**Timestamp**: 2025-11-06 15:55:34,656

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode translates natural language into a structured plan of **inferences**. The translation process works by recursively finding a concept with un-decomposed source text (`...:`) and replacing it with a more detailed block.

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
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with th
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
<:>(::(register a new user))
    <= @if(<the username does not exist>)
        ...: otherwise, create a new user account.
    <- <the username does not exist>
        ...: otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        ...: the provided username already exists.
    <- {check}
        /: The action is to perform a verification.
    <- {provided username}
        /: The username that was provided for the check.
        <- :_:{report error}()
            /: Report an error if the username exists.
        <- :_:{create}({new user account})
            /: Create a new user account if the username does not exist.
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.""",
    'input_2': "{'new inference': '<= :_:{check}(<username exists>)\
    ...: if the provided username already exists.\
    <- <username exists>\
        /: the existence of the username\
    <- {username}\
        /: the provided username'}"
  }
]
```

### OR Output
```
['%960(:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
<:>(::(register a new user))
    <= @if(<the username does not exist>)
        ...: otherwise, create a new user account.
    <- <the username does not exist>
        ...: otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        /: the existence of the username
    <- {username}
        /: the provided username
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.)']
```

---

## Sequence 73: JUDGEMENT DIRECT (#11)
**Timestamp**: 2025-11-06 15:55:58,301

### MFP Step Name
```
::{%(direct)}<{prompt}<$(completion check prompt)%>: check if draft is complete>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an AI assistant specializing in NormCode, a semi-formal language for planning inferences. Your task is to determine if a given NormCode draft is "complete".

Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object. Then, provide the final answer (`True` or `False`) in the "answer" key.

A NormCode draft is considered "complete" if all of its source text (`...:`) has been decomposed into further steps. A `...:` annotation marks a draft as "incomplete" only if it is a "leaf" – meaning it is not followed by a decomposition operator (`<=`) or value concepts (`<-`) within its scope (i.e., at a greater indentation level before the next peer element).

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

**Example 3: Complete Draft (with intermediate
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
<:>(::(register a new user))
    <= @if(<the username does not exist>)
        ...: otherwise, create a new user account.
    <- <the username does not exist>
        ...: otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        /: the existence of the username
    <- {username}
        /: the provided username
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
['%8f6($(F)%)']
```

---

## Sequence 74: IMPERATIVE DIRECT (#62)
**Timestamp**: 2025-11-06 15:56:11,006

### MFP Step Name
```
::{%(direct)}<{prompt}<$(concept identification prompt)%>: identify concept to decompose>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode is a language for translating natural language into a structured plan. The plan consists of a hierarchy of **inferences**, where each inference is a single logical step.

**1. Core Structure:**
An inference starts with a concept to be defined, followed by:
-   `<=` **Functional Concept**: Defines the core operation (e.g., performing an action, specifying a value).
-   `<-` **Value Concept**: Provides the data or inputs for the operation.

**2. Concept Types:**
Concepts are the "words" of NormCode. The main types are:
-   `{}` **Object**: A thing, a variable, or a piece of data (e.g., `{user name}`).
-   `<>` **Statement**: An assertion that can be true or false (e.g., `<the user is an admin>`).
-   `::()` **Imperative**: A command or an action to be done (e.g., `::(calculate the total)`).
-   `[]` **Relation**: A group or collection of things (e.g., `[all user emails]`).

Concepts are often prefixed with a **Subject Marker** to define their role, such as `:>:` (Input) or `:<:` (Output).

**3. Annotations:**
Annotations manage the state of the translation process:
-   `...:` **Source Text**: Holds the piece of the original natural language (`normtext`) currently being analyzed. **A concept with a `...:` annotation is considered "un-decomposed."**
-   `?:` **Question**: The question being asked about the source text.
-   `/:` **Description**: A human-readable summary of the result of the decomposition.

**Your Task: Identify the Next Concept for Decomposition**

You will be given the current NormCode draft. The translation process is a recursive loop that runs for any concept that has an un-parsed `...:` annotation.

Your task is to find the **first concept** (reading from top to bottom) that still has an un-parsed source text annotation (`...:`).

From the draft below, you must extract two things:
1.  The full line of the concept to be decom
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
<:>(::(register a new user))
    <= @if(<the username does not exist>)
        ...: otherwise, create a new user account.
    <- <the username does not exist>
        ...: otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        /: the existence of the username
    <- {username}
        /: the provided username
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account."""
  }
]
```

### OR Output
```
["%0d2({'concept to decomposed': '<= :_:{check}(<username exists>)', 'remaining normtext': '...: if the provided username already exists.'})"]
```

---

## Sequence 75: IMPERATIVE DIRECT (#63)
**Timestamp**: 2025-11-06 15:56:31,678

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%858({'question': 'How to judge the truth of the statement <username exists>?', 'question type': 'Judgement Request'})"]
```

---

## Sequence 76: IMPERATIVE DIRECT (#64)
**Timestamp**: 2025-11-06 15:56:38,958

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%9f9({'functional concept': '<= :_:{check}(<username exists>)'})"]
```

---

## Sequence 77: IMPERATIVE DIRECT (#65)
**Timestamp**: 2025-11-06 15:56:47,916

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%7d3({'children': ['<- {check}', '<- <username exists>']})"]
```

---

## Sequence 78: IMPERATIVE DIRECT (#66)
**Timestamp**: 2025-11-06 15:56:59,669

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%e3f({'new inference': '<= :_:{check}(<username exists>)\
    ...: if the provided username already exists.\
    <- {check}\
        /: This refers to verifying the presence or absence.\
    <- <username exists>\
        /: This is the condition being checked regarding the username.'})"]
```

---

## Sequence 79: IMPERATIVE DIRECT (#67)
**Timestamp**: 2025-11-06 15:57:09,447

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normcode draft update prompt)%>: update normcode draft>
```

### MVP Values
```
[
  {
    'prompt_template': """You are an expert in NormCode, a semi-formal language for planning inferences.

**Background: NormCode Fundamentals**

NormCode translates natural language into a structured plan of **inferences**. The translation process works by recursively finding a concept with un-decomposed source text (`...:`) and replacing it with a more detailed block.

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
  "analysis": "The goal is to replace the `<- {steps}` block in the main draft with the new decomposed snippet. I will find the lines corresponding to `<- {steps}` and its `...:` content and replace that entire block with th
... (truncated)""",
    'input_1': """:<:(::(register a new user))
    <= @by(:_:)
        <= @if(<username does not exist>)
<:>(::(register a new user))
    <= @if(<the username does not exist>)
        ...: otherwise, create a new user account.
    <- <the username does not exist>
        ...: otherwise, create a new user account.
    <- <username does not exist>
        /: the condition where the username does not exist
    <- :_:{check and create}(<username exists>, {create new user account})
        <= @if(not <username exists>)
        ...: If it does, report an error. Otherwise, create a new user account.
    <- <not <username exists>>
        /: The condition is that the username does not exist.
    <= :_:{check}(<username exists>)
    ...: if the provided username already exists.
    <- <username exists>
        /: the existence of the username
    <- {username}
        /: the provided username
    <- <username exists>
        /: Check if the provided username already exists in the database.
    <- {create new user account}
        /: Create a new user account.""",
    'input_2': "{'new inference': '<= :_:{check}(<username exists>)\
    ...: if the provided username already exists.\
    <- {check}\
        /: This refers to verifying the presence or absence.\
    <- <username exists>\
        /: This is the condition being checked regarding the username.'}"
  }
]
```

---
