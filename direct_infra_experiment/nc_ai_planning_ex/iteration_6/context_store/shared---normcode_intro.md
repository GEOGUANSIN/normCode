# NormCode: Structured Plans for AI Agents

NormCode is a language for writing **Plans of Inferences**—structured breakdowns of complex tasks into small, isolated steps that AI agents can execute reliably.

## The Problem NormCode Solves

When you chain LLM calls together, things break in frustrating ways:

```
Step 1: Read a 50-page document
Step 2: Extract key entities
Step 3: Cross-reference with a database
Step 4: Generate a summary
        ↑ Why is this hallucinating entity names that don't exist?
```

The culprit: **context pollution**. By Step 4, the model has 50 pages of document, raw database results, and intermediate extraction notes all swimming in its context. It hallucinates because it's drowning in noise.

NormCode enforces **data isolation**. Each step is a sealed room—it only sees what you explicitly pass in.

---

## 1. Your First NormCode Plan

We write plans in **`.ncds` (NormCode Draft Straightforward)**—the human-friendly format:

```ncds
<- document summary
    <= summarize this text
    <- clean text
        <= extract main content, removing headers and boilerplate
        <- raw document
```

Read it bottom-up:
1. Start with `raw document`
2. `extract main content...` to produce `clean text`
3. `summarize this text` to produce `document summary`

Each `<=` line is a **distinct LLM call**. The summarization step literally cannot see the raw document—only the clean text you passed it.

---

## 2. The Core Syntax

`.ncds` uses just two symbols to mark structure:

| Symbol | Name | Meaning |
|--------|------|---------|
| `<-` | Value Concept | "This is data" (nouns) |
| `<=` | Functional Concept | "This is an action" (verbs) |

That's it. Everything else is natural language.

```ncds
<- user sentiment
    <= determine if the user is satisfied with their experience
    <- support ticket
    <- conversation history
```

The compiler infers types from context:
- "determine if..." → judgement (returns boolean)
- "conversation history" → likely a relation (list of messages)
- "support ticket" → an object

### Optional Type Hints

If you want to be explicit (or help the compiler), you can add type hints with `|`:

```ncds
<- user sentiment | proposition
    <= determine if the user is satisfied | judgement
    <- support ticket | object
    <- conversation history | relation
```

**Value types**: `object` (single item), `relation` (list/group), `proposition` (true/false)
**Action types**: `imperative` (do something), `judgement` (check true/false)

But in most cases, you can just write naturally and let the compiler figure it out.

---

## 3. How Execution Works

### The Child-to-Parent Flow

Execution is **dependency-driven**. The system won't run a step until its inputs are ready:

```ncds
<- quarterly report
    <= compile findings into executive summary
    <- analyzed data                   # Need this first!
        <= identify trends and anomalies
        <- raw metrics                 # And this before that!
```

1. System sees it needs `quarterly report`
2. But that needs `analyzed data`, which needs `raw metrics`
3. So it fetches `raw metrics` first
4. Then runs `identify trends...` → produces `analyzed data`
5. Then runs `compile findings...` → produces `quarterly report`

### The Golden Rule: One Action Per Inference

Each inference block has exactly **one** action (`<=`). This is illegal:

```ncds
<- output
    <= do step 1
    <= do step 2  # ❌ ILLEGAL: two actions
```

If you need multiple steps, nest them:

```ncds
<- final output
    <= do step 2
    <- intermediate result
        <= do step 1
        <- input data
```

---

## 4. Why This Structure Matters

### Data Isolation in Action

Consider analyzing a sensitive document:

```ncds
<- risk assessment
    <= evaluate legal exposure based on the extracted clauses
    <- relevant clauses
        <= extract clauses related to liability and indemnification
        <- full contract
```

The risk assessment step **cannot see the full contract**. It only receives the extracted clauses. This means:

1. **Reduced hallucination**: The model can't confuse clause 3.2(a) with something from page 47
2. **Lower token costs**: You're not paying to re-read 100 pages at every step
3. **Auditable reasoning**: You can inspect exactly what each step saw and produced

### Compare to Typical Prompt Chains

**The Usual Approach:**
```python
history = []
history.append(read_file("contract.pdf"))      # 100 pages
history.append(model.extract_clauses(history)) # Now 100+ pages
history.append(model.assess_risk(history))     # Model is swimming in noise
```

**NormCode Approach:**
```
Step 1 sees: contract.pdf
Step 2 sees: ONLY the extracted clauses (not the original PDF)
Step 3 sees: ONLY the relevant clauses (not extraction metadata)
```

Each step operates on exactly what it needs—nothing more.

---

## 5. Not Every Step Needs an LLM

Here's something important: **not every operation in a NormCode plan calls an LLM**.

The system distinguishes between two types of operations:

| Type | LLM? | Cost | Determinism | What It Does |
|------|------|------|-------------|--------------|
| **Semantic** | ✅ Yes | Tokens | Non-deterministic | Thinking, reasoning, generating |
| **Syntactic** | ❌ No | Free | 100% deterministic | Collecting, selecting, routing |

**Syntactic operations** are pure data manipulation. They run instantly and predictably.

### In `.ncds`, You Just Write Natural Language

Here's the key: **you don't need special symbols in `.ncds`**. Just describe what you want in plain language, and the compiler figures out the operation type during activation compilation.

### Example: Collecting Multiple Inputs

```ncds
<- all inputs
    <= collect the following items together
    <- user query
    <- system context  
    <- retrieved documents
```

You wrote "collect the following items together." The compiler recognizes this as a **grouping** operation and compiles it to `&in` in `.ncd`. No LLM call—just data restructuring.

### Example: Selecting a Specific Output

```ncds
<- final answer
    <= select the last candidate from the following
    <- candidate A
    <- candidate B
    <- candidate C
```

"Select the best candidate" becomes an **assigning** operation (`$.`). Deterministic, instant, free.

### Example: Parallel Collection

```ncds
<- extracted features
    <= gather results from each document
    <- feature from doc A
        <= extract key features
        <- document A
    <- feature from doc B
        <= extract key features
        <- document B
```

"Gather results from each" compiles to `&across`. The LLM calls happen in the child inferences (`extract key features`), but the collection itself is syntactic.

### What the Compiler Infers

When you write natural language, the activation compiler maps it to the appropriate operation:

| You Write | Compiler Infers | Symbol in `.ncd` |
|-----------|-----------------|------------------|
| "collect these items together" | Grouping | `&in` |
| "gather results from each" | Grouping (across) | `&across` |
| "select the first valid result" | Assigning | `$.` |
| "accumulate into the list" | Continuation | `$+` |
| "if the condition is met" | Timing | `@if` |
| "after step X completes" | Timing | `@after` |
| "for every item in the list" | Looping | `*every` |
| "calculate...", "generate...", "analyze..." | Imperative | `::()` |
| "check whether...", "determine if..." | Judgement | `::<>` |

### Why This Matters

A typical plan might be 20 steps, but only 8 call an LLM. The rest are:
- **Grouping**: Collecting and structuring data
- **Assigning**: Selecting or accumulating values
- **Timing**: Controlling flow and conditions
- **Looping**: Repeating actions

This means:
1. **Lower costs**: Only semantic steps burn tokens
2. **Faster execution**: Syntactic steps are instant
3. **More reliability**: Deterministic steps don't hallucinate
4. **Easier writing**: Just describe intent, let the compiler handle formalism

---

## 6. Scaling Up: Loops and Conditions

For more complex flows, NormCode provides control structures:

### Iterating Over Collections

```ncds
<- all summaries
    <= for every document in the list
    <- document summary
        <= summarize this document
        <- document
    <* documents to process
```

"For every document in the list" tells the compiler this is a loop. It iterates through `documents to process`, produces a `document summary` for each, then collects them into `all summaries`.

### Conditional Execution

```ncds
<- final output
    <= return the final output
        <= if the draft needs review
        <* draft needs review?
    <- reviewed output
        <= perform human review
        <- draft output

```

"Return the final output" tells the compiler this is the final output. It checks the condition before executing the review branch.

---

## 7. The Compilation Pipeline

When you write `.ncds`, the system compiles it through two stages before execution.

### Stage 1: Formalization (`.ncds` → `.ncd`)

The first stage converts your natural language plan into a rigorous format (`.ncd`):

**You write:**
```ncds
<- sum
    <= add two numbers
    <- number A
    <- number B
```

**Becomes:**
```ncd
<- {sum}<$({number})%>
    <= ::(add {1}<$({number})%> and {2}<$({number})%>)
    <- {number A}<$({number})%><:{1}>
    <- {number B}<$({number})%><:{2}>
```

### Why the Formalism?

The dense `.ncd` syntax exists to solve problems that natural language can't:

| Problem | How `.ncd` Solves It |
|---------|---------------------|
| **"Which number A?"** — Same name appears in multiple places | Identity markers (`<$={1}>`) distinguish instances |
| **"What order do inputs go in?"** — "Add A and B" vs "Add B and A" matters | Value bindings (`<:{1}>`, `<:{2}>`) fix positions |
| **"What type is this?"** — Is it a list or a single item? | Type markers (`<$({number})%>`) enforce structure |
| **"Where did this fail?"** — Debugging a 50-step plan | Flow indices (`1.2.3`) give every step a unique address |
| **"Is this an LLM call?"** — Need to know for cost/timing | Operation markers (`::()` vs `&in`) are explicit |

The formalism removes ambiguity. The execution engine doesn't interpret—it follows precise instructions.

### Stage 2: Activation Compilation (`.ncd` → JSON Repos)

The second stage transforms the `.ncd` into executable JSON that the orchestrator runs:

```
.ncd file
    ↓
┌─────────────────────────────────────┐
│  Activation Compiler                │
│  - Extracts concepts → concept_repo │
│  - Extracts inferences → inference_repo │
│  - Generates working interpretations │
└─────────────────────────────────────┘
    ↓
concept_repo.json + inference_repo.json
    ↓
Orchestrator executes
```

**What gets generated:**

1. **Concept Repository** (`concept_repo.json`)
   - Every value concept becomes an entry
   - Tracks: name, type, initial reference (data), flow location

2. **Inference Repository** (`inference_repo.json`)
   - Every action becomes an entry
   - Tracks: which concept it infers, what inputs it needs, which sequence to run (imperative, grouping, etc.), and the "working interpretation"

3. **Working Interpretation**
   - The configuration that tells the agent *how* to execute
   - For LLM calls: which paradigm (prompt template, extraction logic)
   - For syntactic ops: which operation (`&in`, `$.`, etc.)
   - Value mappings: which input goes where

**Example of generated inference entry:**
```json
{
  "flow_index": "1.2",
  "concept_to_infer": "{sum}",
  "inference_sequence": "imperative",
  "function_concept": "::(add two numbers)",
  "value_concepts": ["{number A}", "{number B}"],
  "working_interpretation": {
    "paradigm": "basic_calculation",
    "value_order": {
      "{number A}": 0,
      "{number B}": 1
    }
  }
}
```

### Why Two Stages?

| Stage | Purpose | Who Cares |
|-------|---------|-----------|
| **Formalization** | Make the logic unambiguous and traceable | Humans debugging, auditors reviewing |
| **Activation** | Make it executable by the orchestrator | The execution engine |

The `.ncd` is the "source of truth" that both humans and machines can verify. The JSON repos are the "compiled binary" that actually runs.

**You focus on `.ncds`. The compiler handles both stages.**

---

## 8. When to Use NormCode

NormCode adds structure. Structure has costs. Be honest about the tradeoff:

| Scenario | NormCode? | Why |
|----------|-----------|-----|
| Multi-step workflow with 5+ LLM calls | ✅ Yes | Isolation and debuggability pay off |
| Auditable AI (legal, medical, finance) | ✅ Yes | You need to prove what each step saw |
| Long-running resumable workflows | ✅ Yes | Built-in checkpointing |
| Quick prototype with 1-2 LLM calls | ❌ No | Overhead isn't worth it |
| Simple Q&A chatbot | ❌ No | Just prompt the model directly |

**The sweet spot**: Complex, multi-step workflows where you need to know exactly what happened at each step—and where a failure in step 7 shouldn't corrupt the reasoning in step 12.

---

## 9. Next Steps

- **Agent Sequences Guide**: How the system executes each type of inference
- **Orchestrator Guide**: How the execution engine manages dependencies and checkpoints
- **Formalism Guide**: The complete `.ncd` syntax for advanced users

---

*NormCode doesn't make AI smarter. It makes AI workflows **inspectable, isolated, and debuggable**—which, for production systems, often matters more.*
