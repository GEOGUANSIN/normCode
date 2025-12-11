# NormCode: A Semi-Formal Intermediate Representation for AI Planning

**[Authors]**: _To be filled_

**[Abstract]**
_~150-250 words summarizing: problem, approach, key contributions, and (if available) results_

> **Questions for Abstract:**
> - What is the one-sentence "elevator pitch" for NormCode?
> - Do you have any quantitative results to mention (e.g., "reduced debugging time by X%", "successfully executed Y complex plans")?

---

## 1. Introduction

### 1.1 The Problem
- The gap between natural language instructions and executable AI agent plans
- Current approaches (direct prompting, chain-of-thought, tool-use frameworks) lack: auditability, debuggability, progressive refinement
- The need for a structured intermediate representation

> **Questions:**
> - What specific failures or pain points motivated NormCode? Any concrete examples of "this went wrong without structure"?
> - Are there existing systems you're positioning against (e.g., LangChain, AutoGPT, specific agent frameworks)?

### 1.2 The Solution (High-Level)
- NormCode: a semi-formal language for constructing **plans of inferences**
- Key design principles: Dual-Readability, Progressive Formalization, Inference-Based Decomposition

### 1.3 Contributions
1. A novel semi-formal IR design for AI planning with explicit inference structure
2. The dual-format paradigm (`.ncd` / `.ncn`) for machine-rigorous yet human-verifiable plans
3. A conceptual framework for progressive formalization in AI systems
4. _[If available]_ Implementation of compiler ecosystem / experimental validation

> **Questions:**
> - What would you say are the 3-4 key contributions?
> - Is there a working compiler/orchestrator? What's its status?

---

## 2. Background and Related Work

### 2.1 AI Planning and Agent Frameworks
- Traditional AI planning (STRIPS, PDDL, HTN)
- Modern LLM-based agent frameworks

> **Questions:**
> - What prior work influenced NormCode's design?
> - How does NormCode relate to classical planning languages (PDDL, HTN)?
> - Are there specific agent frameworks you see as related (ReAct, Reflexion, LangGraph, etc.)?

### 2.2 Intermediate Representations in AI/ML
- IR in compilers (LLVM IR, etc.)
- Structured reasoning in LLMs (chain-of-thought, tree-of-thought, graph-of-thought)

### 2.3 Formal Methods and Semi-Formal Approaches
- The spectrum from natural language to formal specification
- Why "semi-formal" is the right balance

> **Questions:**
> - What's the theoretical heritage? (Philosophy of language? Formal semantics? Something else?)
> - The naming suggests normative/deontic logic influences — is that intentional?

---

## 3. The NormCode Language

### 3.1 Core Syntax: Inferences and Plan Structure
- The inference as the fundamental unit
- Functional concepts (`<=`), Value concepts (`<-`), Context concepts (`<*`)
- The `.ncd` (NormCode Draft) format

### 3.2 Semantical Concept Types
- Objects (`{}`), Propositions (`<>`), Relations (`[]`)
- Subjects (`:S:`) and their role as agents
- Functional types: Imperative (`({})`), Judgement (`<{}>`)

### 3.3 Syntactical Concept Types (Operators)
- Assigning operators (`$=`, `$.`, `$%`, `$+`, `$-`)
- Timing operators (`@if`, `@if!`, `@after`)
- Grouping operators (`&in`, `&across`)
- Looping operators (`*every`)

### 3.4 The Reference System
- Object references as data holders
- Subject references as tool/sequence collections
- Functional references as paradigm specifications

> **Questions:**
> - How mature is the reference system implementation?
> - Is the "multi-dimensional tensor" backing actually implemented, or is it conceptual?
> - What does a Subject's "sequence" look like in practice?

### 3.5 Flow Index and Plan Addressability
- How flow indices are generated
- Why addressability matters for debugging/intervention

---

## 4. Design Philosophy

### 4.1 Dual-Readability: The `.ncd` / `.ncn` Paradigm
- Machine-facing: NormCode Draft (`.ncd`)
- Human-facing: NormCode Natural (`.ncn`)
- The compiler ecosystem that connects them

> **Questions:**
> - Is there a working `.ncd` → `.ncn` translator?
> - Is there a working NL → `.ncd` compiler (the "Input Compiler")?
> - What LLM/approach powers these compilers?

### 4.2 Progressive Formalization
- The lifecycle: creative/probabilistic → robust/structured
- How NormCode enables step-by-step decomposition
- Intervenability at any stage

> **Questions:**
> - Can you show an example of progressive formalization in action?
> - How does a user intervene? Is there tooling, or is it manual editing?

### 4.3 The Semi-Formal Balance
- Why full formalization is impractical for LLM-based systems
- Why pure natural language lacks structure
- NormCode as the middle ground

---

## 5. The Execution Model (Implementation)

### 5.1 The Orchestrator / Execution Engine
- How a `.ncd` plan is executed
- Agent sequences: `imperative`, `looping`, `grouping`, `judgement`, etc.

> **Questions:**
> - Is there a working orchestrator? What's it implemented in (Python?)?
> - How does it invoke LLMs or tools?
> - What agent sequences are currently implemented?

### 5.2 The Compiler Ecosystem
- NL → `.ncd` (Deconstruction / Input Compiler)
- `.ncd` → `.ncn` (Translation / Output Compiler)
- `.ncd` → Executable (if applicable)

> **Questions:**
> - What's the current state of each compiler?
> - What are the main challenges in building the NL → `.ncd` compiler?

### 5.3 Integration with External Tools and LLMs
- How Subjects connect to tools
- How paradigms configure LLM calls

> **Questions:**
> - What LLMs have you tested with?
> - What kinds of tools/APIs can NormCode orchestrate?

---

## 6. Evaluation / Case Studies

> **This section depends heavily on what you've built and tested.**

### 6.1 Case Study 1: [Name]
- Problem description
- NormCode plan structure
- Execution results

> **Questions:**
> - What's the most impressive/complete example you've run?
> - The addition algorithm in the docs — has it been executed? What were the results?
> - Any multi-step reasoning tasks?

### 6.2 Case Study 2: [Name]
_If applicable_

### 6.3 Quantitative Evaluation (if available)
- Metrics: success rate, debugging time, plan complexity, etc.
- Comparison to baselines (if any)

> **Questions:**
> - Do you have any quantitative results?
> - Any user studies or qualitative feedback?
> - Have you compared NormCode plans to direct LLM prompting?

---

## 7. Discussion

### 7.1 Strengths and When to Use NormCode
- High-stakes, auditable AI decisions
- Complex multi-step reasoning
- Human-AI collaborative planning

### 7.2 Limitations and Challenges
- Syntax density / cognitive load
- Verbosity for simple tasks
- Fragility to manual editing
- Tooling dependency

### 7.3 Lessons Learned

> **Questions:**
> - What surprised you during development?
> - What would you do differently if starting over?
> - What's the biggest remaining unsolved problem?

---

## 8. Future Work

- Compiler maturation
- Tooling (IDE support, visualization)
- Broader evaluation
- Community/ecosystem development

> **Questions:**
> - What's the roadmap?
> - Are there specific domains you want to target (legal, medical, financial)?
> - Any plans for open-sourcing?

---

## 9. Conclusion

_Summary of contributions, significance, and future directions._

---

## References

_To be populated based on related work section._

---

---

# META: Information I Need From You

To turn this skeleton into a real paper, I need you to point me to information about:

## Implementation Status
1. **Orchestrator/Executor**: Is there working code? Where is it?
2. **Compilers**: NL→`.ncd`, `.ncd`→`.ncn` — what's implemented?
3. **Reference system**: How are concepts actually stored and retrieved?

## Results / Examples
4. **Working examples**: What plans have you actually executed end-to-end?
5. **Case studies**: Any real-world or realistic tasks?
6. **Failures**: What went wrong? (Honest discussion strengthens papers)

## Context / Motivation
7. **Origin story**: What problem led to creating NormCode?
8. **Related work**: What systems influenced the design?
9. **Target users**: Who is this for?

## Theoretical Grounding
10. **Influences**: Philosophy? Linguistics? Formal methods? Where does the "Norm" in NormCode come from?

---

Please point me to files, folders, or tell me directly — and I'll integrate the information into this skeleton.

