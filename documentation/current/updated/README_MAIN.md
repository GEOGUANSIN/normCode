# NormCode Documentation

**Complete documentation for the NormCode structured AI planning language.**

---

## 🚀 New to NormCode? Start Here

👉 **[1. Introduction](1_intro/README.md)** - What is NormCode and why use it?

- [Overview](1_intro/overview.md) - The problem, solution, and core concepts
- [Quickstart](1_intro/quickstart.md) - Write your first plan in 5 minutes  
- [Examples](1_intro/examples.md) - Gallery of common patterns

---

## 📚 Documentation Sections

### [1. Introduction](1_intro/README.md)
**What is NormCode? Why use it?**

Get started quickly with the core concepts, your first plan, and practical examples.

**Start here if**: You're new to NormCode or evaluating it.

---

### [2. Grammar](2_grammar/README.md) ✅
**The `.ncd` format and syntax specification**

Complete reference for writing NormCode plans:
- [NCD file format](2_grammar/ncd_format.md) - File structure and flow
- [Semantic concepts](2_grammar/semantic_concepts.md) - `{}`, `<>`, `[]`, `:S:`, `({})`, `<{}>`
- [Syntactic operators](2_grammar/syntactic_operators.md) - `$`, `&`, `@`, `*`
- [References and axes](2_grammar/references_and_axes.md) - Tensor data structures
- [Complete syntax reference](2_grammar/complete_syntax_reference.md) - Full grammar

**Start here if**: You're writing plans and need syntax details.

---

### [3. Execution](3_execution/README.md) *(Coming Soon)*
**How plans run at runtime**

Understanding the execution model:
- Execution overview
- Reference system
- Agent sequences (assigning, grouping, timing, looping, imperative, judgement)
- Orchestrator and checkpointing

**Start here if**: You're debugging plans or optimizing performance.

---

### [4. Compilation](4_compilation/README.md) *(Coming Soon)*
**The 5-phase compilation pipeline**

From natural language to executable code:
- Pipeline overview
- Derivation (NL → Structure)
- Formalization (Adding rigor)
- Post-formalization (Context & config)
- Activation (`.ncd` → JSON repositories)

**Start here if**: You're extending the compiler or need deep understanding.

---

### [5. Tools](5_tools/README.md) *(Coming Soon)*
**User-facing tools and APIs**

Using NormCode tools:
- CLI commands
- Visual editor
- Streamlit executor
- Python API reference

**Start here if**: You're integrating NormCode or using the tools.

---

## 🗺️ Reading Paths

### For New Users
1. [Introduction](1_intro/README.md) - Understand the concepts
2. [Quickstart](1_intro/quickstart.md) - Write your first plan
3. [Examples](1_intro/examples.md) - See common patterns
4. [Tools](5_tools/README.md) - Run your plans

### For Plan Writers
1. [Quickstart](1_intro/quickstart.md) - Basic syntax
2. [Grammar](2_grammar/README.md) - Complete syntax reference
3. [Examples](1_intro/examples.md) - Patterns and best practices
4. [Execution](3_execution/README.md) - How your plans run

### For System Developers
1. [Overview](1_intro/overview.md) - Architecture
2. [Execution](3_execution/README.md) - Runtime behavior
3. [Compilation](4_compilation/README.md) - Compiler pipeline
4. [Tools](5_tools/README.md) - APIs and integration

### For Auditors/Reviewers
1. [Overview](1_intro/overview.md) - Why data isolation matters
2. [Grammar](2_grammar/README.md) - Understanding `.ncd` files
3. [Execution](3_execution/README.md) - How steps are isolated
4. [Tools](5_tools/README.md) - Execution tracing

---

## 📖 Documentation Principles

This documentation follows these principles:

1. **Progressive disclosure**: Start simple, add complexity as needed
2. **Clear separation**: Each section has a distinct, focused purpose
3. **Self-contained docs**: Each file is readable independently
4. **Minimal redundancy**: Information lives in one primary location
5. **Cross-references**: Links between sections when needed

---

## 🎯 Quick Reference

### Core Syntax

| Symbol | Name | Meaning |
|--------|------|---------|
| `<-` | Value Concept | Data (nouns) |
| `<=` | Functional Concept | Actions (verbs) |

### Operation Types

| Type | LLM? | Cost | Deterministic | Examples |
|------|------|------|---------------|----------|
| **Semantic** | ✅ Yes | Tokens | ❌ No | Analyze, generate, reason |
| **Syntactic** | ❌ No | Free | ✅ Yes | Collect, select, loop, if/then |

### Core Formats

| Format | Purpose | Audience |
|--------|---------|----------|
| `.ncds` | Draft/authoring | Plan writers (start here) |
| `.ncd` | Formal syntax | Compiler (intermediate) |
| `.concept.json` + `.inference.json` | Executable repositories | Orchestrator (runtime) |

**Companion formats**: `.ncn` (natural language view of `.ncd`), `.ncdn` (hybrid editor format)  
**Intermediate formats**: `.nci.json` (inference structure for post-formalization)  
**Auxiliary formats**: `.nc.json` (JSON structure for tooling)

---

## 🔍 What Makes NormCode Different?

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

## 📦 Repository Structure

```
documentation/
├── current/updated/          # New documentation (you are here)
│   ├── 1_intro/             # ✅ Complete
│   ├── 2_grammar/           # ✅ Complete
│   ├── 3_execution/         # 🚧 Coming soon
│   ├── 4_compilation/       # 🚧 Coming soon
│   └── 5_tools/             # 🚧 Coming soon
│
└── current/                 # Legacy documentation (being restructured)
    ├── shared---*.md        # Original docs
    ├── Editor_*.md          # Editor docs
    └── paper_draft.md       # Academic paper
```

---

## ❓ Common Questions

**Q: Where do I start?**  
A: [Introduction](1_intro/README.md) → [Quickstart](1_intro/quickstart.md)

**Q: How do I write a plan?**  
A: Start with [Quickstart](1_intro/quickstart.md), then see [Examples](1_intro/examples.md)

**Q: How do I run a plan?**  
A: See [Tools](5_tools/README.md) (coming soon) or [legacy StreamlitAPP_README](../StreamlitAPP_README.md)

**Q: What's the difference between `.ncds`, `.ncd`, `.nci.json`, and the `.json` repositories?**  
A: `.ncds` is draft format (start here), `.ncd` is formal syntax, `.nci.json` is intermediate inference structure, and `.concept.json` + `.inference.json` are the final executable repositories loaded by the orchestrator. `.ncn` is an optional companion showing natural language. See [Overview](1_intro/overview.md#multiple-formats-one-system)

**Q: Is this for me?**  
A: If you have complex multi-step LLM workflows (5+ steps) and need debuggability/auditability, yes. For simple tasks, no.

**Q: How stable is this?**  
A: NormCode is in active development. The core execution model is stable; syntax may evolve.

---

## 🚧 Documentation Status

| Section | Status | Notes |
|---------|--------|-------|
| **1. Introduction** | ✅ Complete | Overview, quickstart, examples |
| **2. Grammar** | ✅ Complete | Format, concepts, operators, references |
| **3. Execution** | 🚧 Planned | Extracting from existing docs |
| **4. Compilation** | 🚧 Planned | Extracting from existing docs |
| **5. Tools** | 🚧 Planned | Extracting from existing docs |

---

## 🔗 External Resources

- **[Academic Paper](../paper_draft.md)** - Detailed background and formal specification
- **[Legacy Documentation](../)** - Original documentation (being restructured)

---

## 📝 Contributing

Found an error? Have suggestions? This documentation is being actively rewritten.

For now, please refer to the [Implementation Approach](README.md#implementation-approach) for the restructuring plan.

---

**Ready to start?** → [Go to Introduction](1_intro/README.md)
