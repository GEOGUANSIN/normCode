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

### Four Major Formats

| Format | Purpose | What You See |
|--------|---------|--------------|
| **`.ncds`** | Draft/authoring | Rough logic and concept environment—easiest to write |
| **`.ncd`** | Formal executable syntax | Structured with operators|
| **`.nci.json`** | Inference structure | Clear flow structure showing inferences and their relationships |
| **`.concept.json` + `.inference.json`** | Executable repositories | Separated concept and inference repositories for orchestrator |

**Companion formats**: `.ncn` (natural language companion to `.ncd`), `.ncdn` (hybrid editor format showing both)  
**Auxiliary formats**: `.nc.json` (JSON structure of `.ncd`)

### Why Multiple Formats?

These aren't just different file formats—they're different representations for different stages and audiences:

**`.ncds` (Draft/Authoring)**:
- First draft format—start here when creating new plans
- Rough logic and concept structure
- Easy for humans and LLMs to author
- Gets formalized into `.ncd` by the compiler

**`.ncd` (Formal/Executable)**:
- Unambiguous syntax for the compiler and orchestrator
- Machine-parsable, directly executable
- Contains all technical details (types, operators, references)
- Comes with `.ncn` companion for natural language view

**`.nci.json` (Inference Structure)**:
- JSON format showing clear inference flow structure
- Each inference explicitly shows: concept to infer, function concept, value concepts
- Intermediate format in the compilation pipeline
- Perfect for flow analysis and debugging before activation

**`.concept.json` + `.inference.json` (Executable Repositories)**:
- **`.concept.json`**: Repository of all concepts (values, functions, contexts)
- **`.inference.json`**: Repository of all inferences with working interpretations
- Separated repositories loaded by the orchestrator for execution
- Contains all syntax details and paradigm configurations

**Supporting Formats**:
- **`.ncn`**: Natural language companion to `.ncd` (not standalone—always paired)
- **`.ncdn`**: Hybrid editor format showing both `.ncd` and `.ncn` together
- **`.nc.json`**: JSON structure of `.ncd`

### Typical Workflow

1. **Author**: Write your plan in `.ncds` (draft format)
2. **Formalize**: Compiler transforms `.ncds` → `.ncd` + `.ncn` companion (adds types, operators)
3. **Review**: Use `.ncn` for stakeholder review (natural language) or `.ncdn` in the editor (hybrid view)
4. **Structure**: Compiler transforms `.ncd` → `.nci.json` (inference structure)
5. **Activate**: Compiler separates `.nci.json` → `.concept.json` + `.inference.json` (executable repositories)
6. **Execute**: Orchestrator loads the repositories and executes the plan

The compiler handles most transformations automatically. You focus on writing clear plans.

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
3. **Formalization**: Add semantic types, operators, and formal structure → `.ncd` + `.ncn` formats
4. **Post-formalization**: Add execution paradigms and resource configurations → `.nci.json`
5. **Activation**: Generate executable JSON repositories for orchestrator. Seperate concepts  `.concept.json` from inference 
`.inference.json` and add working interpretations (syntax details) to the inference repository.
The orchestrator then loads the inference structure and executes your plan step-by-step.

> For most users, phases 2-5 are automatic. You write `.ncds`, run the compiler, and get `.concept.json` and `.inference.json` for execution.

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
Start with a rough draft in `.ncds`, then incrementally refine and formalize to increase reliability.

**6. Resumable Execution**  
Built-in checkpointing and forking, allowing plans to pause, resume, and chain easily.

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
