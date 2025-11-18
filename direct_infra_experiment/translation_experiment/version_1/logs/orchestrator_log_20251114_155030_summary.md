# Step Summary: MFP Names, MVP Values, and OR Outputs

**Extracted from orchestrator log for judgement and imperative sequences**

**Total Sequences Found**: 16

## Statistics

- **Total Sequences**: 16
- **Sequence Types**: {'IMPERATIVE INPUT': 1, 'IMPERATIVE DIRECT': 13, 'JUDGEMENT DIRECT': 2}

### Data Coverage
- **MFP Names**: 16/16 (100.0%)
- **MVP Values**: 7/16 (43.8%)
- **OR Outputs**: 16/16 (100.0%)
- **Complete** (MFP + OR): 16/16 (100.0%)

### Timeline
- **First Sequence**: 2025-11-14 15:50:30,677
- **Last Sequence**: 2025-11-14 15:53:13,275
- **Total Duration**: 162.60 seconds

---

## Sequence 1: IMPERATIVE INPUT (#1)
**Timestamp**: 2025-11-14 15:50:30,677

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
['%18a(The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation. Once this concept is found, the system must extract the full line that defines the concept as well as all of the ...: text associated with it. After identifying these elements, the system returns a single JSON object. This JSON object includes an “analysis” field, which contains a step-by-step explanation of how the concept was located, and an “answer” field, which is a dictionary holding the complete concept line and the combined remaining ...: content. The system should output nothing except this JSON object.)']
```

---

## Sequence 2: IMPERATIVE DIRECT (#1)
**Timestamp**: 2025-11-14 15:50:33,997

### MFP Step Name
```
::{%(direct)}({prompt}<$({initialization prompt})%>: initialize normcode draft)
```

### OR Output
```
['%80c(:<:(::(process NormCode draft to locate first unparsed concept))
    ...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation. Once this concept is found, the system must extract the full line that defines the concept as well as all of the ...: text associated with it. After identifying these elements, the system returns a single JSON object. This JSON object includes an “analysis” field, which contains a step-by-step explanation of how the concept was located, and an “answer” field, which is a dictionary holding the complete concept line and the combined remaining ...: content. The system should output nothing except this JSON object.)']
```

---

## Sequence 3: JUDGEMENT DIRECT (#1)
**Timestamp**: 2025-11-14 15:50:48,840

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
    'input_1': """:<:(::(process NormCode draft to locate first unparsed concept))
    ...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation. Once this concept is found, the system must extract the full line that defines the concept as well as all of the ...: text associated with it. After identifying these elements, the system returns a single JSON object. This JSON object includes an “analysis” field, which contains a step-by-step explanation of how the concept was located, and an “answer” field, which is a dictionary holding the complete concept line and the combined remaining ...: content. The system should output nothing except this JSON object."""
  }
]
```

### OR Output
```
['%990($(F)%)']
```

---

## Sequence 4: IMPERATIVE DIRECT (#2)
**Timestamp**: 2025-11-14 15:50:52,977

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
    'input_1': """:<:(::(process NormCode draft to locate first unparsed concept))
    ...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation. Once this concept is found, the system must extract the full line that defines the concept as well as all of the ...: text associated with it. After identifying these elements, the system returns a single JSON object. This JSON object includes an “analysis” field, which contains a step-by-step explanation of how the concept was located, and an “answer” field, which is a dictionary holding the complete concept line and the combined remaining ...: content. The system should output nothing except this JSON object."""
  }
]
```

### OR Output
```
["%0ab({'concept to decomposed': ':<:(::(process NormCode draft to locate first unparsed concept))', 'remaining normtext': '...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation. Once this concept is found, the system must extract the full line that defines the concept as well as all of the ...: text associated with it. After identifying these elements, the system returns a single JSON object. This JSON object includes an “analysis” field, which contains a step-by-step explanation of how the concept was located, and an “answer” field, which is a dictionary holding the complete concept line and the combined remaining ...: content. The system should output nothing except this JSON object.'})"]
```

---

## Sequence 5: IMPERATIVE DIRECT (#3)
**Timestamp**: 2025-11-14 15:51:00,710

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
["%0b6({'question': 'By what method is ::(process NormCode draft to locate first unparsed concept) performed?', 'question type': 'Methodology Declaration'})"]
```

---

## Sequence 6: IMPERATIVE DIRECT (#4)
**Timestamp**: 2025-11-14 15:51:17,309

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%8f1({'functional concept': '<= @by(:_:)'})"]
```

---

## Sequence 7: IMPERATIVE DIRECT (#5)
**Timestamp**: 2025-11-14 15:51:24,679

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%d1b({'children': ['<- :_:{read and scan draft}({NormCode draft})', '<- {read and scan draft}', '<- {NormCode draft}']})"]
```

---

## Sequence 8: IMPERATIVE DIRECT (#6)
**Timestamp**: 2025-11-14 15:51:41,551

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%e17({'new inference': ':<:(::(process NormCode draft to locate first unparsed concept))\
    <= @by(:_:)\
        ...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation.\
    <- :_:{read and scan draft}({NormCode draft})\
        ...: reads it from top to bottom.\
    <- {read and scan draft}\
        ...: The system receives a NormCode draft as input and reads it from top to bottom.\
    <- {NormCode draft}\
        /: The input to the system is a NormCode draft.'})"]
```

---

## Sequence 9: IMPERATIVE DIRECT (#7)
**Timestamp**: 2025-11-14 15:52:07,260

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
    'input_1': """:<:(::(process NormCode draft to locate first unparsed concept))
    ...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation. Once this concept is found, the system must extract the full line that defines the concept as well as all of the ...: text associated with it. After identifying these elements, the system returns a single JSON object. This JSON object includes an “analysis” field, which contains a step-by-step explanation of how the concept was located, and an “answer” field, which is a dictionary holding the complete concept line and the combined remaining ...: content. The system should output nothing except this JSON object.""",
    'input_2': "{'new inference': ':<:(::(process NormCode draft to locate first unparsed concept))\
    <= @by(:_:)\
        ...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation.\
    <- :_:{read and scan draft}({NormCode draft})\
        ...: reads it from top to bottom.\
    <- {read and scan draft}\
        ...: The system receives a NormCode draft as input and reads it from top to bottom.\
    <- {NormCode draft}\
        /: The input to the system is a NormCode draft.'}"
  }
]
```

### OR Output
```
['%eb7(:<:(::(process NormCode draft to locate first unparsed concept))
    <= @by(:_:)
        ...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation.
    <- :_:{read and scan draft}({NormCode draft})
        ...: reads it from top to bottom.
    <- {read and scan draft}
        ...: The system receives a NormCode draft as input and reads it from top to bottom.
    <- {NormCode draft}
        /: The input to the system is a NormCode draft.)']
```

---

## Sequence 10: JUDGEMENT DIRECT (#2)
**Timestamp**: 2025-11-14 15:52:19,272

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
    'input_1': """:<:(::(process NormCode draft to locate first unparsed concept))
    <= @by(:_:)
        ...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation.
    <- :_:{read and scan draft}({NormCode draft})
        ...: reads it from top to bottom.
    <- {read and scan draft}
        ...: The system receives a NormCode draft as input and reads it from top to bottom.
    <- {NormCode draft}
        /: The input to the system is a NormCode draft."""
  }
]
```

### OR Output
```
['%712($(T)%)']
```

---

## Sequence 11: IMPERATIVE DIRECT (#8)
**Timestamp**: 2025-11-14 15:52:25,404

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
    'input_1': """:<:(::(process NormCode draft to locate first unparsed concept))
    <= @by(:_:)
        ...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation.
    <- :_:{read and scan draft}({NormCode draft})
        ...: reads it from top to bottom.
    <- {read and scan draft}
        ...: The system receives a NormCode draft as input and reads it from top to bottom.
    <- {NormCode draft}
        /: The input to the system is a NormCode draft."""
  }
]
```

### OR Output
```
["%c04({'concept to decomposed': '<= @by(:_:)', 'remaining normtext': '...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation.'})"]
```

---

## Sequence 12: IMPERATIVE DIRECT (#9)
**Timestamp**: 2025-11-14 15:52:31,590

### MFP Step Name
```
::{%(direct)}<{prompt}<$(question inquiry prompt)%>: formulate question for decomposition>
```

### OR Output
```
['%8cc({\'question\': "By what method is the system\'s processing of the NormCode draft performed?", \'question type\': \'Methodology Declaration\'})']
```

---

## Sequence 13: IMPERATIVE DIRECT (#10)
**Timestamp**: 2025-11-14 15:52:42,305

### MFP Step Name
```
::{%(direct)}<{prompt}<$(operator selection prompt)%>: select normcode operator>
```

### OR Output
```
["%e6d({'functional concept': '<= @by(:_:)'})"]
```

---

## Sequence 14: IMPERATIVE DIRECT (#11)
**Timestamp**: 2025-11-14 15:52:46,827

### MFP Step Name
```
::{%(direct)}<{prompt}<$(children concept creation prompt)%>: create child concepts>
```

### OR Output
```
["%cfa({'children': ['<- :_:{read from top to bottom}({NormCode draft})', '<- {read from top to bottom}', '<- {NormCode draft}']})"]
```

---

## Sequence 15: IMPERATIVE DIRECT (#12)
**Timestamp**: 2025-11-14 15:52:54,743

### MFP Step Name
```
::{%(direct)}<{prompt}<$(normtext distribution prompt)%>: distribute normtext to child concepts>
```

### OR Output
```
["%764({'new inference': '<= @by(:_:)\
    ...: Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation.\
    <- :_:{read from top to bottom}({NormCode draft})\
        /: The system reads the NormCode draft from top to bottom.\
    <- {read from top to bottom}\
        /: The reading direction is sequential from top to bottom.\
    <- {NormCode draft}\
        /: The input received is a NormCode draft.'})"]
```

---

## Sequence 16: IMPERATIVE DIRECT (#13)
**Timestamp**: 2025-11-14 15:53:13,275

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
    'input_1': """:<:(::(process NormCode draft to locate first unparsed concept))
    <= @by(:_:)
        ...: The system receives a NormCode draft as input and reads it from top to bottom. Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation.
    <- :_:{read and scan draft}({NormCode draft})
        ...: reads it from top to bottom.
    <- {read and scan draft}
        ...: The system receives a NormCode draft as input and reads it from top to bottom.
    <- {NormCode draft}
        /: The input to the system is a NormCode draft.""",
    'input_2': "{'new inference': '<= @by(:_:)\
    ...: Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation.\
    <- :_:{read from top to bottom}({NormCode draft})\
        /: The system reads the NormCode draft from top to bottom.\
    <- {read from top to bottom}\
        /: The reading direction is sequential from top to bottom.\
    <- {NormCode draft}\
        /: The input received is a NormCode draft.'}"
  }
]
```

### OR Output
```
['%993(:<:(::(process NormCode draft to locate first unparsed concept))
    <= @by(:_:)
    ...: Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation.
    <- :_:{read from top to bottom}({NormCode draft})
        /: The system reads the NormCode draft from top to bottom.
    <- {read from top to bottom}
        /: The reading direction is sequential from top to bottom.
    <- {NormCode draft}
        /: The input received is a NormCode draft.
    <- :_:{read and scan draft}({NormCode draft})
        ...: reads it from top to bottom.
    <- {read and scan draft}
        ...: The system receives a NormCode draft as input and reads it from top to bottom.
    <- {NormCode draft}
        /: The input to the system is a NormCode draft.)']
```

---

:<:(::(process NormCode draft to locate first unparsed concept))
    <= @by(:_:)
    ...: Its task is to locate the first concept in the draft that still contains an un-parsed ...: source-text annotation.
    <- :_:{read from top to bottom}({NormCode draft})
        /: The system reads the NormCode draft from top to bottom.
    <- {read from top to bottom}
        /: The reading direction is sequential from top to bottom.
        <= $::.{unparsed concept}^({normcode draft})
            /: {read from top to bottom} is a nominalized method to output the unparsed concept, and normcode draft as an input. 
        <- ::(locate the {first unparsed concept} in the {draft} that still contains an un-parsed ...: source-text annotation.)
            /: this is the functional imperative to locate the first unparsed concept in the draft that still contains an un-parsed ...: source-text annotation.
        <- {normcode draft}
            /: The input received is a NormCode draft.
    <- {NormCode draft}
        /: The input received is a NormCode draft.