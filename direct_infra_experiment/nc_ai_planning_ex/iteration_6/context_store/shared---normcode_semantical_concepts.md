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

## 5. From Natural Language to NormCode: A Derivation Strategy

NormCode construction is a **derivation** process: moving from a potentially ambiguous natural language idea to a rigorous, executable plan. It is not a simple translation because the final structure often contains explicit logic and values that were only implied in the original thought. The following 5-step strategy refines the "Rule of Thumb" into a formal methodology.

### Step 1: Isolation and Context Separation
Identify the core instruction block within the natural language idea. Separate the "main instructions" (the sequence of actions) from the "context" (examples, definitions, environment details).
*   *Goal*: Obtain a clean set of instructional statements.

*Example 1:*
```text
Calculate the total of the numbers in the list provided, where the numbers are multiplied by 2 and added to the total.
```

### Step 2: Structural Linkage (The Semantic Tree)
Map the sentences to a rough hierarchical structure.
*   Identify relationships: Is Sentence A a prerequisite for Sentence B? (Parent-Child). Do Sentences C and D happen in parallel?
*   Identify logic: Are there loops ("for every"), conditionals ("if"), or data aggregations?
*   *Drafting*: Formulate a rough indented list where parent sentences explain the goal and child sentences provide the data or steps.

*Example 1 Draft:*
```text
The total we want to obtain
    <= for every number in the list 
        <= we multiply the number by 2
        <= we add the number to the total
        <= we return the total
```

### Step 3: Concept Refinement (The Functional Principle)
NormCode adheres to the principle: **One functional concept per inference.**
Refine the draft by introducing non-functional concepts (Values) to link the operations. Ensure that operations are not just "listed" but are "inferred" as the means to obtain a specific value.

*Refined Draft 1:*
```text
The number we want to obtain
    <= for every number in the list 
        <= the total is specified 
        <- the number to be added to the total
            <= we multiply the number by 2
        <- the total
            <= we add the number to the total
```

### Step 4: Flow and Coherence
Ensure the logical flow of data.
*   Where does the data come from? (Inputs, Initializations).
*   Where does it go? (Outputs).
*   Add initialization steps (e.g., `total = 0`) and identify inputs (e.g., `user input`).

*Coherent Draft 1:*
```text
the total we want to obtain
    <= we select the last total as the number we want to obtain
    <- total
        <= initialize the total to 0
    <- The list of totals
        <= for every number in the list 
            <= the total is specified 
            <- the number to be added to the total
                <= we multiply the number by 2
                <- the item number in the list 
            <- the total
                <= we add the number to the total
                <- the total
        <- the list of number
            <= user input the list of numbers 
```

### Step 5: Syntax Formalization (Activation Compilation)
Apply the rigorous NormCode syntax (`:<:`, `::`, `*every`, `$.`, `{...}`) to finalize the plan. This prepares it for **activation compilation**, where repositories and working interpretations are generated.

*Final NormCode 1 (.ncd):*
```ncd
:<:({total}) | Goal: The final total is the output.
    <= $-[{total lists}:_<#-1>] | Selector: Select the last element from the list of totals.
    <- {total}
        <= ::(initialize the total to {1}<is a number>)
        <- {%(0)}<:{1}> | Input 1: The literal value 0.
    <- {total list} | Context: The collection of totals generated by the loop.
        <= *every({list of numbers})@(1) | Loop: Iterate over the list of numbers.
            <= $.({total}<${2}=>) | Specifier: We want the NEW total (state 2).
            <- {number added}
                <= ::(multiply {1}<is a number> by {2}<is a number>)
                <- {item number}*1<:{1}> | Input 1: The current item from the loop.
                <- {%(2)}<:{2}> | Input 2: The literal value 2.
            <- {total}<${2}=> | The Result: The updated total.
                <= ::(add {1}<is a number> to {2}<is a number>)
                <- {number added}<:{1}> | Input 1: The calculated product.
                <- {total}<${1}=><:{2}>  | Input 2: The carried-over total (state 1).
        <- {list of numbers}
            <= :>:({list of numbers}<is a list of numbers>) | Input: User provided list.
        <* {item number}*1<*{list of numbers}> | Loop Context: Current item definition.
        <* {total}<${1}=><*_<${2}=>> | Loop Context: State carry-over (State 2 becomes State 1 next loop).
```

---

## 6. Example 2: Data Processing Pipeline

To further illustrate the strategy, let's look at a "Filter and Save" task.

**Step 1: Isolation**
"Read the file 'data.txt', keep only the lines that contain the word 'ERROR', and save the result to 'errors.log'."

**Step 2: Structural Linkage**
```text
The Saved File
    <= Filter the content
        <= Read the original file
```

**Step 3: Concept Refinement**
```text
The Saved File Location
    <= Save the content to file
    <- The Filtered Content
        <= Filter lines by keyword 'ERROR'
        <- The Raw Content
            <= Read file 'data.txt'
```

**Step 4: Flow and Coherence**
Identify inputs (filenames, keywords) and the final output.
```text
The output file location
    <= Save {content} to {path}
    <- {content} is the Filtered Content
        <= Filter {text} keeping lines with {keyword}
        <- {text} is Raw Content
            <= Read from {source path}
            <- {source path} is 'data.txt'
        <- {keyword} is 'ERROR'
    <- {path} is 'errors.log'
```

**Step 5: Syntax Formalization**
```ncd
:<:({output file location})
    <= ::(Save {1}<$({content})%> to {2}<$({path})%>)
    <- {filtered content}<$({content})%><:{1}>
        <= ::(Filter {1}<$({text})%> by {2}<$({keyword})%>)
        <- {raw content}<$({text})%><:{1}>
            <= ::(Read file from {1}<$({path})%>)
            <- {source path}<$({path})%><:{1}>
                <= :>:({source path}) | Input: 'data.txt'
        <- {keyword}<:{2}>
             <= {%(ERROR)} | Literal: 'ERROR'
    <- {destination path}<$({path})%><:{2}>
        <= {%(errors.log)} | Literal: 'errors.log'
```

---

## 7. Example 3: Meta-Derivation

A complex example: The derivation strategy itself, written as a NormCode plan.

**Step 1: Fuzzy Instruction (Isolation)**
*Original thought:*
"I want a NormCode plan that describes how we turn a user's natural language idea into a formal plan. It basically involves taking the raw idea, isolating the instructions, linking them into a tree structure, refining the concepts to make sure there's one function per inference, ensuring the data flows correctly, and then finally formalizing the syntax."

**Step 2: Structural Linkage (Parallel Structure)**
*Mapping the steps as a parallel sequence of operations:*
```text
The Final NormCode Plan
    <= Read NL Idea
    <= Isolate Instructions
    <= Link Structurally
    <= Refine Concepts
    <= Ensure Flow and Coherence
    <= Formalize Syntax
    <= return the final normcode plan
```

**Step 3: Concept Refinement**
*Explicitly listing the intermediate values produced by each step:*
```text
The Final NormCode Plan
    <= return the final normcode plan
    <- the NL idea
        <= Read NL Idea
    <- the instruction
        <= Isolate Instructions
    <- the linked tree
        <= Link Structurally
    <- the refined concepts linked tree
        <= Refine Concepts
    <- the flow and coherence linked tree
        <= Ensure Flow and Coherence
    <- final normcode plan
        <= Formalize Syntax
```

**Step 4: Flow and Coherence**
*Explicitly tracking the transformation from input to output:*
```text
The Final NormCode Plan
    <= return the final normcode plan
    <- the NL idea
        <= input the NL Idea
    <- the instruction
        <= Isolate Instructions
        <- the NL idea
    <- the linked tree
        <= Link Structurally
        <- the instruction
        <= Refine Concepts
    <- the refined concepts linked tree
        <- the linked tree
        <= Refine Concepts
    <- the flow and coherence linked tree
        <= Ensure Flow and Coherence
    <- final normcode plan
        <= Formalize Syntax
```

**Step 5: Syntax Formalization**
```ncd
:<:({final normcode plan}) | Goal: The final normcode plan is the output.
    <= $.({final normcode plan}) | this specifies the final normcode plan as the output of this inference. 
    <- the NL idea
        <= :>:({NL Idea}) | Input: The original idea from the user.
    <- {instruction}
        <= ::(isolate the {1}?<$({instructions})%> from {2}<$({NL Idea})%>) | Input: The instructions from the NL Idea.
        <- {NL Idea}<$({NL Idea})%><:{2}>
    <- {tree}
        <= ::(link the structure of {1}<$({instructions})%>) | Input: The instructions from the NL Idea.
        <- {instructions}<$({instructions})%><:{1}>
    <- {refined concepts linked tree}
        <= ::(refine the concepts in {1}<$({tree})%> to ensure one functional concept per inference) | Input: The instructions from the NL Idea.
        <- {tree}<:{1}>
    <- {flow and coherence linked tree}
        <= ::(Ensure Flow and Coherence of {1}<$({tree})%>) | Input: The instructions from the NL Idea.
        <- {refined concepts linked tree}<:{1}>
    <- {final normcode plan}
        <= ::(Formalize the syntax of {1}<$({linked tree})%>)
        <- {flow and coherence linked tree}<:{1}>
```
