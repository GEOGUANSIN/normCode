# NormCode Quickstart

Get started with NormCode in 5 minutes.

---

## Your First Plan

We'll write a simple document summarization plan in `.ncd` format.

### Step 1: Write the Plan

Create a file called `summarize.ncds`:

> **Note**: Start with `.ncds` (draft format). The compiler will formalize it to `.ncd` (with `.ncn` companion), structure it to `.nci.json`, and activate it to `.concept.json` + `.inference.json` for execution. You can also use `.ncdn` in the editor to see both formal and natural language together.

```ncds
<- document summary
    <= summarize this text
    <- clean text
        <= extract main content, removing headers and boilerplate
        <- raw document
```

That's it. Let's break down what this means.

### Step 2: Understand the Structure

**Read bottom-up** (execution flows from bottom to top):

1. **`<- raw document`**
   - This is your input (a value concept)
   - Marked with `<-` = "this is data"

2. **`<= extract main content...`**
   - This is an action (a functional concept)
   - Marked with `<=` = "this is an operation"
   - Takes `raw document` as input
   - Produces `clean text` as output

3. **`<- clean text`**
   - Result of the extraction (another value concept)

4. **`<= summarize this text`**
   - Another action
   - Takes `clean text` as input (NOT the raw document)
   - Produces `document summary`

5. **`<- document summary`**
   - Final output

**Key insight**: The summarization step cannot see `raw document`. It only receives `clean text`. This is data isolation in action.

---

## The Core Syntax

NormCode uses just two symbols:

| Symbol | Name | Meaning |
|--------|------|---------|
| `<-` | Value Concept | "This is data" (nouns) |
| `<=` | Functional Concept | "This is an action" (verbs) |

Everything else is natural language.

### Execution Flow: Child-to-Parent

Plans execute **dependency-driven**:

```ncds
<- quarterly report
    <= compile findings into executive summary
    <- analyzed data                   /: Need this first!
        <= identify trends and anomalies
        <- raw metrics                 /: And this before that!
```

**Execution order**:
1. System needs `quarterly report`
2. That needs `analyzed data`, which needs `raw metrics`
3. So: fetch `raw metrics` → run `identify trends...` → run `compile findings...`

---

## The Golden Rule

**Each inference has exactly ONE action (`<=`).**

This is **illegal**:

```ncds
<- output
    <= do step 1
    <= do step 2  /: ❌ ILLEGAL: two actions
```

If you need multiple steps, **nest them**:

```ncds
<- final output
    <= do step 2
    <- intermediate result
        <= do step 1
        <- input data
```

---

## Example 2: Multi-Input Operations

Actions can have multiple inputs:

```ncds
<- user sentiment
    <= determine if the user is satisfied
    <- support ticket
    <- conversation history
```

The action sees both `support ticket` AND `conversation history`—but nothing else.

---

## Example 3: Type Hints (Optional)

The compiler infers types from context, but you can be explicit:

```ncds
<- user sentiment | proposition
    <= determine if the user is satisfied | judgement
    <- support ticket | object
    <- conversation history | relation
```

**Value types**:
- `object` = single item
- `relation` = list/group
- `proposition` = true/false

**Action types**:
- `imperative` = do something
- `judgement` = check true/false

Most of the time, just write naturally and let the compiler figure it out.

---

## Example 4: Collections

### Grouping Inputs

```ncds
<- all inputs
    <= collect these items together
    <- user query
    <- system context
    <- retrieved documents
```

"Collect these items" → compiler recognizes this as a **grouping** operation.

No LLM call. Just data structuring.

### Iterating Over Lists

```ncds
<- all summaries
    <= for every document in the list return the document summary
        <= select document summary to return
        <- document summary
            <= summarize this document
            <- document to process now
    <- documents
    <* document to process now
```

"For every document" → compiler recognizes a **loop**.

It will iterate through `documents`, produce a summary for each `document to process now`, then collect results into `all summaries`.

---

## Example 5: Conditional Execution

```ncds
<- final output
    <= select reviewed output if available otherwise use draft output
    <- draft needs review?
        <= check if draft requires review
        <- draft output
    <- reviewed output
        <= perform human review
            <= if draft needs review
            <* draft needs review?
        <- draft output
    <- draft output
```

The review step only runs if `draft needs review?` is true. The timer `<= if draft needs review` and context `<* draft needs review?` are attached to the review action, not the selection.

---

## Syntactic vs. Semantic Operations

Not every step calls an LLM:

| You Write | Compiler Infers | LLM Call? |
|-----------|-----------------|-----------|
| "collect these items" | Grouping (`&in`) | ❌ No |
| "select the first valid" | Assigning (`$.`) | ❌ No |
| "if condition is met" | Timing (`@if`) | ❌ No |
| "for every item" | Looping (`*every`) | ❌ No |
| "analyze...", "generate..." | Imperative (`::`) | ✅ Yes |
| "determine if...", "check whether..." | Judgement (`::<>`) | ✅ Yes |

**Syntactic operations** (grouping, assigning, timing, looping) are:
- Free (no tokens)
- Instant
- Deterministic (never hallucinate)

**Semantic operations** (imperative, judgement) are:
- Use tokens
- Take time
- Non-deterministic (LLM reasoning)

---

## Complete Example: Risk Assessment

```ncds
<- risk assessment
    <= evaluate legal exposure based on extracted clauses
    <- relevant clauses
        <= extract clauses related to liability and indemnification
        <- full contract
```

**What happens**:
1. System receives `full contract` (input)
2. Runs `extract clauses...` (LLM call #1)
3. Produces `relevant clauses`
4. Runs `evaluate legal exposure...` (LLM call #2)
5. Produces `risk assessment` (output)

**Key point**: Step 2 cannot see the full contract. Only the extracted clauses.

Result:
- No hallucination of clause numbers
- Lower token costs
- Auditable reasoning trail

---

## Next Steps

### Run Your Plan

To actually execute a plan, you need:

1. **Author** your plan in `.ncds` (draft format)
2. **Formalize** `.ncds` → `.ncd` + `.ncn` (adds types and operators)
3. **Structure** `.ncd` → `.nci.json` (inference structure)
4. **Activate** `.nci.json` → `.concept.json` + `.inference.json` (executable repositories)
5. **Execute** orchestrator loads the repositories and runs your plan

Most of this is automated by the tooling.

See the [Tools section](../5_tools/README.md) for:
- CLI commands
- Editor usage
- Streamlit executor

### Learn More

- **[Examples](examples.md)** - More sample plans
- **[Grammar](../2_grammar/README.md)** - Complete .ncd syntax
- **[Execution](../3_execution/README.md)** - How the orchestrator works
- **[Compilation](../4_compilation/README.md)** - The compilation pipeline

---

## Common Questions

**Q: Do I have to write `.ncd` by hand?**  
A: No. Start with `.ncds` (draft format), and the compiler formalizes it to `.ncd` + `.ncn`, structures to `.nci.json`, then activates to `.concept.json` + `.inference.json`. Or use the `.ncdn` editor format to work with both views simultaneously.

**Q: How do I debug a failing step?**  
A: Inspect the step's inputs in the orchestrator. Every step has an explicit input list.

**Q: Can I use this with non-OpenAI models?**  
A: Yes. Paradigms (execution strategies) are configurable.

**Q: Is this overkill for simple tasks?**  
A: Yes. Use NormCode when you have 5+ steps and need isolation/auditability.

**Q: Can steps run in parallel?**  
A: Yes, if they have no dependencies. The orchestrator handles scheduling.

---

**You're ready to write NormCode plans!**

Start with simple linear flows, then add loops and conditions as needed.
