# Introduction to NormCode

Welcome to NormCode—a language for building structured, auditable AI workflows.

---

## Start Here

If you're new to NormCode, read these in order:

### 1. [Overview](overview.md)
**What is NormCode and why does it exist?**

- The context pollution problem
- How data isolation solves it
- Core concepts
- When to use (and not use) NormCode
- Three formats, one system

**Read this if**: You're evaluating NormCode or want to understand the big picture.

**Time**: 10 minutes

---

### 2. [Quickstart](quickstart.md)
**Write your first plan in 5 minutes**

- Basic syntax (`<-` and `<=`)
- Execution flow (bottom-up)
- Multi-input operations
- Loops and conditions
- Complete working examples

**Read this if**: You want to start writing plans immediately.

**Time**: 5-10 minutes

---

### 3. [Examples](examples.md)
**Gallery of common patterns**

- Document processing
- Conditional workflows
- Iteration patterns
- Data collection
- Nested workflows
- Real-world use cases

**Read this if**: You learn best by seeing examples.

**Time**: Browse as needed

---

## Quick Navigation

### Just Starting
→ [Overview](overview.md) → [Quickstart](quickstart.md) → [Examples](examples.md)

### Ready to Write Plans
→ [Quickstart](quickstart.md) → [Grammar Section](../2_grammar/README.md)

### Want to Execute Plans
→ [Tools Section](../5_tools/README.md)

### Need Deep Understanding
→ [Execution Section](../3_execution/README.md) → [Compilation Section](../4_compilation/README.md)

---

## Key Concepts (Quick Reference)

### The Two Symbols

| Symbol | Name | Meaning |
|--------|------|---------|
| `<-` | Value Concept | Data (nouns) |
| `<=` | Functional Concept | Actions (verbs) |

### Data Isolation

Each step only sees explicitly passed inputs. No accidental context leakage.

### Semi-Formal Language

NormCode balances structure with readability:
- **Not pure natural language** (which is ambiguous)
- **Not fully formal code** (which is rigid)  
- **Structured but accessible** (clear rules, readable content)

### Syntactic vs. Semantic

| Type | LLM Call? | Cost | Examples |
|------|-----------|------|----------|
| **Semantic** | ✅ Yes | Tokens | Analyze, generate, reason |
| **Syntactic** | ❌ No | Free | Collect, select, loop |

### Core Formats

| Format | Purpose | You Interact With |
|--------|---------|-------------------|
| `.ncds` | Draft/authoring | ✅ Start here |
| `.ncd` | Formal syntax | After formalization |
| `.nci.json` | Inference structure | Intermediate format |
| `.concept.json` + `.inference.json` | Executable repositories | Orchestrator loads these |

**Companion formats**: `.ncn` (natural language view of `.ncd`), `.ncdn` (hybrid editor format)  
**Auxiliary formats**: `.nc.json` (JSON structure for tooling)

---

## Common Questions

**Q: Do I need to learn formal syntax?**  
A: No. Start writing in `.ncds` (draft format). The compiler handles formalization to `.ncd` + `.ncn`, then structuring to `.nci.json`, and finally activation to `.concept.json` + `.inference.json`.

**Q: How is this different from LangChain?**  
A: NormCode enforces explicit data isolation. Each step's inputs are declared, not implicit.

**Q: Is this overkill for simple tasks?**  
A: Yes. Use NormCode when you have 5+ steps and need isolation/debuggability.

**Q: Can I use my own LLM?**  
A: Yes. Agent body (repositories of tools) and paradigms (execution strategies) are configurable.

**Q: What if a step fails?**  
A: Inspect its inputs in the orchestrator. Everything is explicit and traceable.

---

## What's Next?

After reading the intro section, continue to:

- **[Grammar](../2_grammar/README.md)** - Complete `.ncd` syntax specification
- **[Execution](../3_execution/README.md)** - How plans run at runtime
- **[Compilation](../4_compilation/README.md)** - The 5-phase compilation pipeline
- **[Tools](../5_tools/README.md)** - CLI, editor, and executor

---

## External Resources

- **[Paper Draft](../../paper_draft.md)** - Academic paper (detailed background)
- **[Editor Examples](../../Editor_EXAMPLES.md)** - Advanced editor usage patterns

---

**Ready to start?** → [Overview](overview.md)
