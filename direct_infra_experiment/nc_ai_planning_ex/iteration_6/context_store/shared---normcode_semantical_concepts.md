# NormCode Guide - Semantical Concepts

Semantical concepts are the "vocabulary" of NormCode. They map specific parts of natural language thoughts into rigorous, executable structures. Each concept type corresponds to a specific linguistic category and plays a distinct role in the inference plan.

## 1. Typically Non-Functional Concept Types (Entities)

These concepts represent the "nouns" and "states" of your reasoning—the things being manipulated or observed.

### 1.1. Object `{}`
**Symbol**: `{_concept_name_}`
**Reference Type**: Holds concrete data, values, or state (e.g., a String, Int, File, or Object).

*   **Definition**: Represents a generic entity, item, or distinct piece of information.
*   **Natural Language Extraction**:
    *   **Nouns & Noun Phrases**: Look for the core subjects and objects in a sentence.
    *   *Example*: "Calculate the **sum** of the **digits**." -> `{sum}`, `{digits}`.
    *   *Example*: "The **user input** is invalid." -> `{user input}`.

### 1.2. Proposition `<>`
**Symbol**: `<_concept_name_>`
**Reference Type**: Holds a boolean-like state or a descriptive statement.

*   **Definition**: Represents a state of affairs, a condition, or a fact that can be true or false. It is "static"—it describes *how things are*, not an action to change them.
*   **Natural Language Extraction**:
    *   **Declarative Clauses**: Phrases describing state using "is", "are", "have".
    *   **Conditions**: The condition part of an "if" statement.
    *   *Example*: "**The file exists**." -> `<file exists>`
    *   *Example*: "Check if **the value is greater than 10**." -> `<value is greater than 10>`

### 1.3. Relation `[]`
**Symbol**: `[_concept_name_]`
**Reference Type**: Holds a collection (List) or a mapping (Dict).

*   **Definition**: Represents a group of items or a relationship between multiple entities.
*   **Natural Language Extraction**:
    *   **Plurals**: "The **files**", "The **numbers**".
    *   **Groupings**: "A **list of** items", "The **set of** parameters".
    *   *Example*: "Iterate through all **input files**." -> `[input files]`
    *   *Example*: "The **pairs of numbers**." -> `[pairs of numbers]`

### 1.4. Subject `:S:`
**Symbol**: `:S:` or `:_Name_:`
**Reference Type**: Holds a "Body" of tools and capabilities.

*   **Definition**: The active agent or system responsible for executing the logic. It defines *who* is doing the thinking.
*   **Natural Language Extraction**:
    *   **Implicit Actor**: Often implied in imperative sentences ("(You) calculate this").
    *   **Explicit Systems**: "The **Planner** should...", "The **Python Tool** runs...".
    *   *Note*: In most simple plans, the subject is implicit (the default agent).

### 1.5. Special Subject (`:>:`, `:<:`)
These are wrappers that define the "boundary roles" of a concept within the plan.
*   **Input `:>:`**: Marks data coming *into* the plan from the outside (User, API).
    *   *NL*: "Given **X**...", "Input is **Y**...".
*   **Output `:<:`**: Marks the final goal or result to be returned.
    *   *NL*: "Return **Z**...", " The goal is to find **W**...".

---

## 2. Typically Functional Concept Types (Operations)

These concepts represent the "verbs"—the operations that transform data or evaluate states. They invoke **Agent Sequences** (paradigms) to do the work.

### 2.1. Imperative `({})`
**Symbol**: `({_concept_name_})` or `::(_concept_name_)`
**Associated Sequence**: `imperative`
**Reference Type**: Holds the *Paradigm* (the logic/code to execute).

*   **Definition**: Represents a command, action, or transformation. It changes the state of the world or produces new data from old.
*   **Natural Language Extraction**:
    *   **Active Verbs**: "Calculate", "Find", "Generate", "Extract", "Save".
    *   **Action Phrases**: "Get the result", "Run the script".
    *   *Example*: "**Sum** the two numbers." -> `::(sum the two numbers)`
    *   *Example*: "**Read** the file content." -> `::(read the file content)`

### 2.2. Judgement `<{}>`
**Symbol**: `<{_concept_name_}>` or sometimes just `<...>`
**Associated Sequence**: `judgement`
**Reference Type**: Holds the *Paradigm* plus a *Truth Assertion*.

*   **Definition**: Represents an evaluation, assessment, or check. It results in a decision (True/False) typically used to control flow (branching).
*   **Natural Language Extraction**:
    *   **Questions**: "Is the file empty?", "Does the value match?".
    *   **Evaluations**: "Check validity", "Verify format".
    *   *Example*: "**Is** the carry-over 0?" -> `<{carry-over is 0}>`
    *   *Example*: "**Check if** finished." -> `<{is finished}>`

## 3. Summary Table: From Thought to NormCode

| NLP Feature | Part of Speech | NormCode Concept | Symbol |
| :--- | :--- | :--- | :--- |
| **Entities** | Noun (Singular) | Object | `{}` |
| **States/Facts** | Clause (Static) | Proposition | `<>` |
| **Collections** | Noun (Plural) | Relation | `[]` |
| **Actions** | Verb (Imperative) | Imperative | `({})` |
| **Questions** | Verb (Interrogative) | Judgement | `<{}>` |
| **Actors** | Subject Noun | Subject | `:S:` |

---

## 4. The Role of Syntax in Semantics

While NormCode uses a variety of brackets and markers (e.g., `{}`, `[]`, `<>`), the primary purpose of this syntax is a **decorative reminder**, where formality enhances the clarity of the concept. The strict, full syntax within a semantic concept is only required to the extent that it ensures two key outcomes before the **activation compilation** for the orchestrator:

### 4.1. Identity Establishment
The system must be able to identify whether two different occurrences of a concept refer to the **same entity** or distinct instances.
*   **Same Entity**: If `{file path}` appears in Step 1 as an output and `{file path}` appears in Step 5 as an input, the Orchestrator relies on the identical concept name (extracted from the syntax) to link them and pass the reference.
*   **Distinct Entities**: Variants like `{file path}<${1}=>` and `{file path}<${2}=>` are treated as **different concepts** because their syntax implies different positions or versions in the plan. The Orchestrator will *not* link them, as they represent distinct references.

### 4.2. Working Interpretation Extraction
The system must be able to reliably strip away the syntax to extract the core **Working Interpretation**. This includes the concept type, the sequence to invoke, and necessary parameters (value order, selectors, etc.) which are provided to the inference during activation compilation.
*   **Defaults**: In simple cases like `::(Calculate Sum)`, the Orchestrator can infer default values:
    *   **Sequence**: `imperative`
    *   **Mode**: Default agent mode (composition)
    *   **Paradigm**: Default paradigm
    *   **Value Order**: Same as the order of provision in the plan.
*   **Explicit Auxiliaries**: In complex cases, auxiliaries like `{1}`, `{2}`, `<:{1}>` are strictly required to define non-default behavior. They determine value order, selection logic, or specific parameter mapping. While these auxiliaries are not part of the "core name" used for lookups, they are essential syntactic standards for the activation compilation process to correctly configure the inference.

### 4.3. Formalizing Abstraction (`<$(...)%>`)
One powerful piece of formal syntax is the **Instance Marker** (`Y<$(_X_)%>`).
*   **Meaning**: "Y, which is an instance of the abstract concept X" or "Y, whose abstract concept is X".
*   **Usage**: This explicitly links a specific, concrete concept (`Y`) to a general, reusable pattern or paradigm (`X`) during activation compilation.
*   **Example**: `{daily report file}<$({text file})%>` tells the compiler: "Treat `{daily report file}` as a `{text file}` for the purpose of tool selection (e.g., use text reading tools)."

**In Summary**: Syntax is the tool for *addressing* content and *configuring* execution. As long as the parser can successfully resolve "Who am I?" (Identity matching) and "How do I run?" (Working Interpretation extraction), the semantic concept is valid.

