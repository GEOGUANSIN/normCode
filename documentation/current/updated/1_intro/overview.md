# NormCode Overview

**NormCode is a language for writing structured AI plans that enforce data isolation by design.**

## What Problem Does It Solve?

When you chain multiple LLM calls together, context pollution causes failures:

```
Step 1: Read a 50-page document
Step 2: Extract key entities  
Step 3: Cross-reference with database
Step 4: Generate summary
        ↑ Why is this hallucinating names that don't exist?
```

**The culprit**: By step 4, the model has 50 pages of document, raw database results, and extraction metadata all swimming in context. It hallucinates because it's drowning in noise.

**The NormCode solution**: Each step is a sealed room. It only sees what you explicitly pass in.

---

## Core Idea: Plans of Inferences

NormCode lets you write **plans of inferences**—structured breakdowns of complex tasks into small, isolated steps that AI agents execute reliably.

Each inference is a self-contained unit:
- **One clear action** (what to do)
- **Explicit inputs** (what it receives)
- **One output** (what it produces)

No step can peek at data from earlier steps unless you explicitly pass it through, making each inference independently auditable.

---

## A Simple Example

Here's a plan in NormCode format:

```ncds
<- document summary
    <= summarize this text
    <- clean text
        <= extract main content, removing headers
        <- raw document
```

> **Note**: This uses the core NormCode syntax. The language exists in multiple formats (`.ncd`, `.ncn`, `.ncdn`) which we'll cover later.

Read it bottom-up:
1. Start with `raw document`
2. Run `extract main content...` → produces `clean text`
3. Run `summarize this text` → produces `document summary`

**Key point**: The summarization step literally cannot see the raw document. It only receives `clean text`.

---

## Why Structure Matters

### 1. Eliminates Context Pollution

```ncds
<- risk assessment
    <= evaluate legal exposure based on the extracted clauses
    <- relevant clauses
        <= extract clauses related to liability
        <- full contract
```

The risk assessment **cannot see the full contract**. Only the extracted clauses. This means:
- No confusion between clause 3.2(a) and something on page 47
- Reduced hallucination
- Auditable: you can inspect exactly what each step saw

### 2. Reduces Token Costs

You're not re-reading 100 pages at every step. Each step only processes what it needs.

### 3. Makes Failures Debuggable

When step 7 fails, you can inspect:
- What inputs step 7 received
- What it was supposed to do
- What it actually produced

No guesswork. No reverse-engineering hidden state.

---

## Not Every Step Calls an LLM

NormCode distinguishes two operation types:

| Type | LLM? | Cost | Speed | Examples |
|------|------|------|-------|----------|
| **Semantic** | ✅ Yes | Tokens | Seconds | Reasoning, generating, analyzing |
| **Syntactic** | ❌ No | Free | Instant | Collecting, selecting, routing |

**Syntactic operations** are deterministic data manipulation. They run instantly and never hallucinate.

### Example: Collecting Inputs

```ncds
<- all inputs
    <= collect these items together
    <- user query
    <- system context
    <- retrieved documents
```

"Collect these items" is recognized as a **grouping** operation. No LLM call—just data restructuring.

### Example: Selecting First Valid Result

```ncds
<- final answer
    <= select the first valid result
    <- candidate A
    <- candidate B  
    <- candidate C
```

"Select the first valid" is an **assigning** operation. Deterministic, instant, free.

### What This Means

A typical 20-step plan might only call an LLM 8 times. The rest are:
- **Grouping**: Structuring data
- **Assigning**: Selecting values
- **Timing**: Controlling flow
- **Looping**: Iterating

Result: Lower costs, faster execution, more reliability.

---

## The Semi-Formal Philosophy

Before diving into formats and implementation, it's important to understand NormCode's design philosophy.

NormCode occupies a deliberate position between natural language and formal specification:

NormCode uses multiple formats for different purposes:

### Primary Formats: Three Views of the Same Plan

| Format | Purpose | What You See |
|--------|---------|--------------|
| **`.ncds`** | Draft/authoring format | Rough logic and concept environment—easiest to write |
| **`.ncd`** | Formal syntax | Structured with operators: `<= extract clauses related to liability` |
| **`.ncn`** | Natural language | Readable narrative: "Extract the liability-related clauses from the contract" |

**Additional formats**: `.ncdn` (hybrid editor format), `.nc.json` and `.nci.json` (used by tooling for validation and execution)

### Why Multiple Views?

These aren't just different file formats—they're different perspectives on the same plan:

**`.ncds` (Draft/Authoring)**:
- First draft format—start here when creating new plans
- Rough logic and concept structure
- Easy for humans and LLMs to author
- Gets formalized into `.ncd` by the compiler

**`.ncd` (Formal/Executable)**:
- Unambiguous syntax for the compiler and orchestrator
- Machine-parsable, directly executable
- Contains all technical details (types, operators, references)

**`.ncn` (Natural Language)**:
- Human-readable descriptions
- Explains intent in plain language
- Perfect for non-technical stakeholders to review
- Generated automatically from `.ncd`

**`.ncdn` (Hybrid Editor Format)**:
- Shows both `.ncd` and `.ncn` side-by-side
- Used by the visual editor
- Lets you edit formal structure while seeing natural language

### Typical Workflow

1. **Author**: Write your plan in `.ncds` (draft format)
2. **Formalize**: Compiler transforms `.ncds` → `.ncd` (adds types, operators)
3. **Review**: Generate `.ncn` for stakeholder review (natural language)
4. **Edit**: Use `.ncdn` format in the visual editor when you want both views
5. **Execute**: Compiler activates `.ncd` → JSON repositories for orchestrator

The tooling handles most transformations automatically. You focus on writing clear plans.

| Approach | Pros | Cons | Example |
|----------|------|------|---------|
| **Pure Natural Language** | Expressive, accessible | Ambiguous, hard to execute | "Analyze the document and extract important parts" |
| **Fully Formal** | Unambiguous, executable | Rigid, hard to write | `extract(doc, filter=lambda x: importance(x) > 0.8)` |
| **Semi-Formal (NormCode)** | Structured yet readable | Requires learning syntax | `<= extract clauses related to liability` |

### Why Semi-Formal?

**The ambiguity problem** (pure natural language): 
- "Extract important clauses" - what's important? All clauses? First 3?
- "Analyze the data and summarize" - which data? How to summarize?
- Ambiguity breaks reliable execution

**The rigidity problem** (fully formal code):
- Small syntax errors break everything
- Requires programming expertise
- Hard for LLMs to generate correctly
- Difficult for non-technical stakeholders to review

**NormCode's balance**:
- **Structural guidance**: Clear markers (`<-`, `<=`) remove ambiguity about data vs. action
- **Near-natural content**: The descriptions remain readable
- **Progressive formalization**: Start rough, refine incrementally
- **LLM-friendly**: Models can generate valid NormCode reliably
- **Human-verifiable**: Non-programmers can review the `.ncn` narrative

### The "Norm" in NormCode

The name "NormCode" references **normative reasoning**—rules and norms that agents must follow:

- **Norms as constraints**: Each step follows the norm "only see what you're explicitly given"
- **Auditable compliance**: Every step's adherence to norms is verifiable
- **Structured obligation**: The syntax enforces what must be declared (inputs, outputs)

This makes NormCode particularly suited for **high-stakes domains** (legal, medical, financial) where proving AI compliance with established rules is essential.

---

## Multiple Formats, One System

The semi-formal philosophy is implemented through multiple format views:

NormCode adds structure. Structure has costs. Be honest about the tradeoff:

| Scenario | Use NormCode? | Why |
|----------|---------------|-----|
| Multi-step workflow (5+ LLM calls) | ✅ Yes | Isolation pays off |
| Auditable AI (legal, medical, finance) | ✅ Yes | Need proof of reasoning |
| Long-running resumable workflows | ✅ Yes | Built-in checkpointing |
| Simple Q&A chatbot | ❌ No | Just prompt directly |

**Sweet spot**: Complex multi-step workflows where you need to know exactly what happened at each step—and where a failure at step 7 shouldn't corrupt reasoning at step 12.

---

## How It Works: The Pipeline

NormCode plans go through a compilation process from draft to execution:

```
1. Author (.ncds draft format)
       ↓
2. Derivation (Natural language → Structure)
       ↓
3. Formalization (Add types and operators)
       ↓
4. Post-formalization (Add paradigms and resources)
       ↓
5. Activation (Generate executable JSON repositories)
       ↓
   Orchestrator Executes
```

**What happens in each phase**:
1. **Authoring**: You write the plan in `.ncds` (draft format)—easy and flexible
2. **Derivation**: Natural language descriptions → structured concepts
3. **Formalization**: Add semantic types, operators, and formal structure → `.ncd` format
4. **Post-formalization**: Add execution paradigms and resource configurations
5. **Activation**: Generate executable repositories (`concept_repo.json` + `inference_repo.json`)

The orchestrator then loads these repositories and executes your plan step-by-step.

> For most users, phases 2-5 are automatic. You write `.ncds`, run the compiler, and get executable plans.

---

## Key Benefits Summary

Bringing it all together, NormCode provides:

**1. Data Isolation by Construction**  
Each step only sees explicitly passed inputs. No accidental context leakage.

**2. Semi-Formal Balance**  
Structured enough for reliable execution, readable enough for human review.

**3. Full Auditability**  
Every intermediate state is explicit and independently inspectable. Perfect for high-stakes domains.

**4. Cost/Reliability Tracing**  
Know exactly which steps call LLMs (expensive, non-deterministic) vs. which are free (deterministic).

**5. Progressive Development**  
Start with a rough draft with simple NormCode, then build up complexity in future versions to increase reliability.

**6. Reusable Execution**  
Built-in checkpointing and forking, allowing the chaining of multiple plans easily.

---

## Who Is This For?

**Primary users**:
- Developers building complex AI workflows
- Organizations needing auditable AI systems
- Anyone frustrated by debugging implicit context

**Ideal domains**:
- Legal document analysis
- Medical decision support
- Financial risk assessment
- Research synthesis
- Multi-stage content generation

**Not for**:
- Simple chatbots
- Single-shot Q&A


---

## Next Steps

- **[Quickstart](quickstart.md)** - Write your first plan in 5 minutes
- **[Examples](examples.md)** - See sample plans
- **[Grammar Section](../2_grammar/README.md)** - Learn the .ncd format
- **[Execution Section](../3_execution/README.md)** - Understand how plans run

---
