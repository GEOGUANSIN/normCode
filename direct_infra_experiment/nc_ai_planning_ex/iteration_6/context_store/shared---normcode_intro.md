# NormCode: A Plan of Inferences

NormCode is a language for structuring thoughts. It allows you to break down complex goals into a **Plan of Inferences**—a tree of small, distinct logical steps that AI agents can execute reliably.

While the system is built on a rigorous semi-formal logic, the way you write it is designed to be straightforward.

## 1. The "Hello World" of NormCode

Here is what a basic NormCode script looks like. We call this format **`.ncds` (NormCode Draft Straightforward)**.

```ncds
<- last date sum | object 
    <= sum the last date of these months | imperative
    <- a list of months | relation 
```

You can read this in three lines:
1.  **The Output**: We want to produce a `last date sum` (which is an `object`).
2.  **The Action**: To get it, we run the command `sum the last date of these months` (which is an `imperative` action).
3.  **The Input**: To do that action, we need `a list of months` (which is a `relation` or list).

This structure—**Output** $\leftarrow$ **Action** $\leftarrow$ **Input**—is the fundamental unit of NormCode, called an **Inference**.

## 2. Writing in `.ncds` (The Human Format)

When you write a plan, you focus on the flow of logic using just three main symbols:

### 2.1. The Symbols

*   **`<=` (The Functional Concept)**: The "Verb". It defines the operation, logic, or action (e.g., "Calculate", "Find", "Iterate").
*   **`<-` (The Value Concept)**: The "Noun". It defines the data being used as input or produced as output.
*   **`|` (The Type Hint)**: An optional comment that clarifies the concept type.
    *   For **Actions**: `imperative` (do something), `judgement` (check true/false), or `syntax` (structure only, no LLM call).
    *   For **Values**: `object` (item), `relation` (list/group), or `proposition` (state/condition).

### 2.2. The Structure

NormCode is a **tree**. You solve a big problem by breaking it into smaller inferences nested inside each other.

**Example: A Two-Step Plan**
*Goal: Get a summary of a file.*

```ncds
<- file summary | object
    <= summarize the text content | imperative
    <- file text content | object
        <= read the file from disk | imperative
        <- file path | object
```

**How to read it:**
1.  To get the `file summary`, we need to `summarize...`.
2.  But to summarize, we first need the `file text content`.
3.  To get the content, we must `read the file...` using the `file path`.

The indentation shows the dependency. You can't summarize the text until you've read it.

## 3. How It Executes

Before looking at why this is useful, it is important to understand what actually happens when you run this code.

### 3.1. The "Call" Mechanism
Every `imperative` line (like `<= summarize the text content`) represents a **distinct call to an LLM** (or an Agent).

*   The text you write ("summarize the text content") serves as the **Prompt** or **Instruction** for that specific step.
*   The system isolates this instruction and only provides it with the inputs defined in that specific inference.

### 3.2. The Flow: Child-to-Parent
Execution happens in a **Child-to-Parent** flow, driven by dependency:

1.  **Top-Down Activation**: The system sees it needs a `file summary`.
2.  **Child Execution**: It realizes it can't summarize until it has the input `file text content`. It goes down a level.
    *   It sees it needs `file text content`.
    *   It executes the child action: `read the file from disk`.
3.  **Parent Execution**: Once the child returns the text, the system goes back up and executes the parent action: `summarize the text content`.

### 3.3. The Golden Rule
**"One Inference, One Functional Concept."**
Each inference block can have only **one** action (`<=`). You cannot list two actions at the same level:
```ncds
<- output
    <= do action 1
    <= do action 2  <-- ILLEGAL
```

If you need to perform multiple steps, you have three options to structure the dependency:

**Option A: Nesting (Standard Dependency)**
Use this when Step 2 depends on the result of Step 1.
```ncds
<- final output
    <= do action 2 | using intermediate
    <- intermediate result
        <= do action 1
```

**Option B: Chaining (Explicit Flow)**
Use this to show a clear linear sequence. Note that the top-level action is just a `syntax` helper to return the result, not an LLM call.
```ncds
<- final output
    <= return result 2 | syntax
    <- result 1
        <= do action 1
    <- result 2
        <= do action 2
        <- result 1
```

**Option C: Compounding (Not Recommended)**
You *can* write a complex instruction in a single line, but this delegates all complexity to the LLM (losing reliability).
```ncds
<- output
    <= do action 1 AND then do action 2
```
*Use Option C only for quick prototyping.*

## 4. Comparison with Other Approaches

### 4.1. NormCode vs. Python
**The "Boilerplate" Problem**
In Python, writing the function name is just the start. You still have to implement the logic:
```python
# Python: You still have work to do
def get_last_date_sum(months):
    # TODO: Import date library?
    # TODO: Handle leap years?
    # TODO: Parse "Feb" vs "February"?
    pass 
```
In NormCode, **you are done**.
```ncds
<= sum the last date of these months
```
The instruction *is* the implementation. The system uses an LLM to "compile" this instruction into action at runtime. You don't need to write helper functions for semantic tasks like "extract date" or "summarize text."

### 4.2. NormCode vs. Prompt Engineering (Chain-of-Thought)
**The "Black Box" Problem**
Standard prompt engineering relies on the model to internally manage the state and logic. You dump a large prompt and hope it doesn't get lost. It's opaque and hard to debug.

**The Solution: Structured Inferences**
NormCode breaks the "Black Box" into a series of visible steps. You see exactly what went in and what came out of each step. The logic is externalized in the code, not hidden in the model's weights.

**The "Context Pollution" Problem**
In standard prompt engineering, you often feed the model a long history of conversation.
```python
# The "Polluted" Context
history = []
history.append(raw_file_content) # 10MB of text
history.append(irrelevant_step_2)
# ...
# When asking for a summary, the model is distracted by the 
# raw noise from step 1, increasing hallucination risks.
response = model.generate("Summarize", context=history) 
```

**The Solution: Data Isolation**
NormCode enforces **Strict Data Scoping**.
In our file summary example, the `summarize` action is **physically unable** to see the `file path` or how the file was read. It *only* receives the `file text content` input you explicitly gave it.

Each inference is a **sealed room**. This drastic reduction in context noise makes agents:
1.  **More Reliable**: They can't hallucinate based on irrelevant past data.
2.  **Cheaper**: You don't pay tokens for history you don't need.

### 4.3. NormCode vs. DAG Frameworks (e.g., LangGraph)
**The "Grammar" Problem**
DAGs are just boxes and arrows. They lack a **Grammar**. There is no standardized way to say "Loop over this list" or "Condition on this variable" without writing custom edge logic.
NormCode provides a **Language** for agents. Concepts like `*every` (looping) and `@if` (conditionals) are built-in grammatical primitives, not ad-hoc wiring.

**The "Readability" Problem**
Graph frameworks require you to explicit wire nodes (`Node A -> Node B`). This becomes "Spaghetti Code" visually when you have 50+ steps.
NormCode manages this via **Nesting**. You don't draw lines; you just indent. The structure of the code *is* the structure of the graph. It's cleaner to read and easier to refactor.

## 5. Advanced: The "Bytecode" (.ncd)

You might wonder: *How does the system know exactly which variable is which?*

When you write the straightforward `.ncds` format, the system **compiles** it into a rigorous format called **`.ncd` (NormCode Draft)**. This is the "Bytecode" that the Orchestrator actually executes.

### 4.1. Comparison

**What You Write (.ncds):**
```ncds
<- sum | object
    <= add two numbers | imperative
    <- number A | object
    <- number B | object
```

**What The Machine Runs (.ncd):**
```ncd
<- {sum}<$({number})%><:{1}>
    <= ::(add {1}<$({number})%> and {2}<$({number})%>)
    <- {number A}<$({number})%><:{1}>
    <- {number B}<$({number})%><:{2}>
```

### 4.2. Why the Complexity?
The `.ncd` format (Advanced) handles things you don't want to worry about:
1.  **Strict Typing**: `<$({number})%>` ensures the agent treats the data as a number, not text.
2.  **Explicit Binding**: `<:{1}>` tells the tool exactly which input goes to which argument.
3.  **Unique Addressing**: Every step gets a unique ID (e.g., `1.1.2`) for tracing.

**Key Takeaway**: As a user, you stick to **`.ncds`**. Let the compiler handle the heavy formalism of `.ncd`.
