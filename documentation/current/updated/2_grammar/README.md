# Grammar Section

**Complete specification of the `.ncd` format and NormCode syntax.**

---

## 🎯 Purpose

This section documents the formal syntax of NormCode plans. While you typically write in the easier `.ncds` format, understanding the `.ncd` formalism helps with:

- **Debugging**: Trace exactly what the compiler generated
- **Auditing**: Verify what each step saw and did
- **Extending**: Build custom sequences or paradigms
- **Optimizing**: Refine your plans based on compiler output

---

## 📚 Documents in This Section

### 1. [NCD Format](ncd_format.md)
**The `.ncd` file format and structure**

Learn about:
- Core building blocks (inferences, concepts, markers)
- File structure and flow indices
- Comments and metadata
- The semi-formal philosophy
- Why the formalism exists

**Start here if**: You want to understand the basic structure of `.ncd` files.

**Time**: 15 minutes

---

### 2. [Semantic Concepts](semantic_concepts.md)
**Concept types: `{}`, `<>`, `[]`, `:S:`, `({})`, `<{}>`**

Learn about:
- Non-functional concepts (entities, states, collections)
- Functional concepts (operations, evaluations)
- Subject concepts (agents and actors)
- Special markers (input/output)
- Extracting concepts from natural language

**Start here if**: You want to understand what the different brackets and symbols mean.

**Time**: 20 minutes

---

### 3. [Syntactic Operators](syntactic_operators.md)
**The `$`, `&`, `@`, `*` operators**

Learn about:
- Why syntactic operators exist (free, deterministic data flow)
- Assigning operators (`$=`, `$%`, `$.`, `$+`, `$-`)
- Grouping operators (`&[{}]`, `&[#]`)
- Timing operators (`@:'`, `@:!`, `@.`)
- Looping operator (`*.`)
- The unified modifier system (`%>`, `%<`, `%:`, `%^`, `%@`)

**Start here if**: You want to understand how data flows through plans without LLM calls.

**Time**: 30 minutes

---

### 4. [References and Axes](references_and_axes.md)
**How data is stored in multi-dimensional tensors**

Learn about:
- What references are (tensor containers)
- Perceptual signs (data pointers)
- Axes of indeterminacy (named dimensions)
- Basic operations (get, set, slice, append)
- Combining references (cross product, join, cross action)
- How operators interact with axes

**Start here if**: You want to understand the data structures underlying NormCode.

**Time**: 35 minutes

---

### 5. [Complete Syntax Reference](complete_syntax_reference.md)
**Quick reference for all syntax elements**

- All markers and operators
- Modifier system
- Comment types
- Pattern library
- Formal grammar (BNF)
- Validation checklist

**Start here if**: You need a quick lookup while writing or debugging.

**Time**: Browse as needed

---

## 🗺️ Reading Paths

### For New Users
1. [NCD Format](ncd_format.md) - Understand the basics
2. [Semantic Concepts](semantic_concepts.md) - Learn concept types
3. [Complete Syntax Reference](complete_syntax_reference.md) - Quick lookup

### For Plan Writers
1. [Semantic Concepts](semantic_concepts.md) - Concept types
2. [Syntactic Operators](syntactic_operators.md) - Operators
3. [Complete Syntax Reference](complete_syntax_reference.md) - Reference

### For System Developers
1. [NCD Format](ncd_format.md) - File structure
2. [Semantic Concepts](semantic_concepts.md) - Concept types
3. [Syntactic Operators](syntactic_operators.md) - Operators
4. [References and Axes](references_and_axes.md) - Data structures
5. [Complete Syntax Reference](complete_syntax_reference.md) - Full grammar

### For Debugging
1. [NCD Format](ncd_format.md) - Flow indices
2. [Complete Syntax Reference](complete_syntax_reference.md) - Quick lookup
3. [Syntactic Operators](syntactic_operators.md) - Operator details
4. [References and Axes](references_and_axes.md) - Data flow

---

## 🔑 Key Concepts

### The Three Markers

| Symbol | Name | Purpose |
|--------|------|---------|
| `<-` | Value Concept | Data (inputs/outputs) |
| `<=` | Functional Concept | Operations to execute |
| `<*` | Context Concept | In-loop state/context |

### Semantic Concept Types

| Symbol | Type | Examples |
|--------|------|----------|
| `{}` | Object | `{document}`, `{result}` |
| `<>` | Proposition | `<is valid>`, `<ready>` |
| `[]` | Relation | `[files]`, `[numbers]` |
| `({})` | Imperative | `::(calculate sum)` (holds **norm**) |
| `<{}>` | Judgement | `<{is complete}>` (holds **norm**) |

**Note**: Functional concepts (imperative, judgement) contain a **norm**—a paradigm that specifies the execution strategy.

### Syntactic Operator Families

| Symbol | Family | Purpose |
|--------|--------|---------|
| `$` | Assigning | Data routing and selection |
| `&` | Grouping | Collection creation |
| `@` | Timing | Execution control |
| `*` | Looping | Iteration with state |

### Modifier System

| Modifier | Meaning | Usage |
|----------|---------|-------|
| `%>` | Source (read from) | `%>({input})` |
| `%<` | Target (write to) | `%<({output})` |
| `%:` | Axis (dimension) | `%:({axis_name})` |
| `%^` | Carry (state) | `%^({state}*-1)` |
| `%@` | Index (position) | `%@(1)` |

---

## 💡 The Big Picture

### Semi-Formal Balance

NormCode sits between pure natural language and fully formal code:

| Approach | Pros | Cons |
|----------|------|------|
| **Pure NL** | Expressive, accessible | Ambiguous, hard to execute |
| **Fully Formal** | Unambiguous, executable | Rigid, hard to write |
| **Semi-Formal (NormCode)** | Structured yet readable | Requires learning syntax |

### The Two Types of Operations

```
┌────────────────────────────────────────────────┐
│  SEMANTIC (imperatives, judgements)            │
│  → CREATE information via LLM                  │
│  → Expensive (tokens), non-deterministic       │
├────────────────────────────────────────────────┤
│  SYNTACTIC ($, &, @, *)                        │
│  → RESHAPE information via tensor algebra      │
│  → Free, deterministic, auditable              │
└────────────────────────────────────────────────┘
```

**Key insight**: Syntactic operators handle data plumbing so semantic operations receive exactly what they need.

---

## 📖 Common Questions

**Q: Do I need to write `.ncd` by hand?**  
A: No. You write `.ncds` (draft format), and the compiler generates `.ncd` automatically.

**Q: Why is `.ncd` so dense?**  
A: The formalism resolves ambiguities that would break execution. Tooling handles the complexity.

**Q: What's the difference between `{}` and `[]`?**  
A: `{}` is an object (single entity), `[]` is a relation (collection of entities).

**Q: When do I use semantic vs. syntactic operations?**  
A: Use semantic (`::(...)`) when you need LLM reasoning. Use syntactic (`$`, `&`, `@`, `*`) for data manipulation.

**Q: How do axes work?**  
A: Axes are named dimensions that model indeterminacy (e.g., "a student" has axes like school, class, nationality).

**Q: What are modifiers like `%>` and `%<`?**  
A: They specify roles in operations (`%>` = source/input, `%<` = target/output, etc.).

**Q: How do I debug a `.ncd` file?**  
A: Check flow indices, verify operator syntax, trace data flow through references.

---

## 🎓 Understanding Levels

### Level 1: Basic Reading
**Goal**: Understand what a `.ncd` file is saying

**Learn**:
- [NCD Format](ncd_format.md) - File structure
- [Semantic Concepts](semantic_concepts.md) - Concept types

**You can**: Read and understand compiler output.

---

### Level 2: Syntax Mastery
**Goal**: Write optimal `.ncds` that compiles to efficient `.ncd`

**Learn**:
- [Syntactic Operators](syntactic_operators.md) - All operators
- [Complete Syntax Reference](complete_syntax_reference.md) - Quick reference

**You can**: Write plans that leverage syntactic operations effectively.

---

### Level 3: Deep Understanding
**Goal**: Extend the system and optimize execution

**Learn**:
- [References and Axes](references_and_axes.md) - Data structures
- [Execution Section](../3_execution/README.md) - Runtime behavior
- [Compilation Section](../4_compilation/README.md) - Compiler pipeline

**You can**: Build custom sequences, optimize tensor operations, extend the language.

---

## 🚀 Quick Start Examples

### Example 1: Simple Linear Plan

**`.ncds` (what you write)**:
```ncds
<- document summary
    <= summarize this text
    <- clean text
        <= extract main content
        <- raw document
```

**`.ncd` (what compiler generates)**:
```ncd
:<:{document summary} | ?{flow_index}: 1
    <= ::(summarize this text) | ?{sequence}: imperative
    <- {clean text} | ?{flow_index}: 1.1
        <= ::(extract main content) | ?{sequence}: imperative
        <- {raw document} | ?{flow_index}: 1.1.1
```

---

### Example 2: With Syntactic Operators

**`.ncds` (what you write)**:
```ncds
<- all summaries
    <= for every document
    <- document summary
        <= summarize this document
        <- document
    <* documents to process
```

**`.ncd` (what compiler generates)**:
```ncd
:<:{all summaries} | ?{flow_index}: 1
    <= *. %>({documents}*1) %<({summary}) %:({document}) %@(1) | ?{sequence}: looping
    <- {summary} | ?{flow_index}: 1.1
        <= ::(summarize this document) | ?{sequence}: imperative
        <- {document}*1 | ?{flow_index}: 1.1.1
    <* {documents} | ?{flow_index}: 1.2
```

---

## 🔗 External Resources

- **[Quickstart](../1_intro/quickstart.md)** - Write your first plan
- **[Examples](../1_intro/examples.md)** - Pattern gallery
- **[Execution Section](../3_execution/README.md)** - How plans run
- **[Compilation Section](../4_compilation/README.md)** - Compiler pipeline

---

## 📊 Document Status

| Document | Status | Content Coverage |
|----------|--------|-----------------|
| **NCD Format** | ✅ Complete | File structure, flow indices, comments |
| **Semantic Concepts** | ✅ Complete | All concept types, extraction rules |
| **Syntactic Operators** | ✅ Complete | All operators, unified modifier system |
| **References and Axes** | ✅ Complete | Reference system, axes, operations |
| **Complete Syntax Reference** | ✅ Complete | Full grammar, patterns, quick reference |

---

## 🎯 Next Sections

After mastering the grammar:

- **[3. Execution](../3_execution/README.md)** - How plans run at runtime
- **[4. Compilation](../4_compilation/README.md)** - The 5-phase compilation pipeline
- **[5. Tools](../5_tools/README.md)** - CLI, editor, and executor

---

**Ready to dive in?** Start with [NCD Format](ncd_format.md) to understand the basics.
