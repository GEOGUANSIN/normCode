# Compilation Section

**The 5-phase pipeline that transforms natural language ideas into executable NormCode plans.**

---

## 🎯 Purpose

This section documents how NormCode plans are compiled—from initial natural language intent through progressive formalization stages to final executable JSON repositories that the Orchestrator can run.

**Key Questions Answered:**
- How does natural language become structured `.ncd` syntax?
- What happens during formalization?
- How are norms and resources assigned?
- How do `.ncd` files become executable repositories?
- How do I use the editor and format tools?

---

## 📚 Documents in This Section

### 1. [Overview](overview.md)
**High-level view of the compilation pipeline**

Learn about:
- The 5 compilation phases
- Progressive formalization philosophy
- Design principles
- Format ecosystem

**Start here if**: You want to understand the big picture of compilation.

**Time**: 15 minutes

---

### 2. [Derivation](derivation.md)
**Phase 1: Natural Language → Structure**

Learn about:
- Transforming unstructured intent into hierarchical inferences
- Identifying concepts and operations
- Creating `.ncds` (draft straightforward) format
- Extraction of value and functional concepts

**Start here if**: You want to understand how natural language becomes structure.

**Time**: 20 minutes

---

### 3. [Formalization](formalization.md)
**Phase 2: Adding Flow and Sequence Types**

Learn about:
- Assigning unique flow indices (`1.2.3`)
- Determining sequence types (`imperative`, `grouping`, `timing`, etc.)
- Resolving concept identity and value bindings
- Transforming `.ncds` to formal `.ncd`

**Start here if**: You want to understand how structure becomes rigorous syntax.

**Time**: 25 minutes

---

### 4. [Post-Formalization](post_formalization.md)
**Phase 3: Enriching with Context and Configuration**

Learn about:
- **Re-composition**: Mapping to normative context (paradigms, body faculties, perception norms)
- **Provision**: Linking to concrete resources (file paths, prompts)
- **Syntax Re-confirmation**: Ensuring tensor coherence (axes, shape, element type)
- Annotation injection

**Start here if**: You want to understand how syntax becomes executable.

**Time**: 30 minutes

---

### 5. [Activation](activation.md)
**Phase 4: Generating Executable Repositories**

Learn about:
- Transforming enriched `.ncd` to JSON repositories
- `concept_repo.json` structure and extraction
- `inference_repo.json` structure and working_interpretation
- Syntax mapping for each sequence type
- Ground concept identification

**Start here if**: You want to understand the final compilation output.

**Time**: 35 minutes

---

### 6. [Editor and Tools](editor.md)
**Using the NormCode Editor and Format Tools**

Learn about:
- Interactive inline editor (Streamlit)
- Format conversion between `.ncd`, `.ncn`, `.ncdn`, `.nc.json`, `.nci.json`
- Validation and batch processing
- Mixed view editing (NCD/NCN toggle)
- Pure text mode vs line-by-line mode

**Start here if**: You want to use the editor and conversion tools.

**Time**: 20 minutes

---

## 🗺️ Reading Paths

### For New Users
1. [Overview](overview.md) - Understand the pipeline
2. [Derivation](derivation.md) - See how structure emerges
3. [Formalization](formalization.md) - Understand rigor
4. [Editor](editor.md) - Start using the tools

### For Plan Writers
1. [Overview](overview.md) - Pipeline overview
2. [Editor](editor.md) - Use the tools
3. [Post-Formalization](post_formalization.md) - Understand annotations
4. [Activation](activation.md) - See the final output

### For Compiler Developers
1. [Overview](overview.md) - Architecture
2. [Derivation](derivation.md) - Phase 1 logic
3. [Formalization](formalization.md) - Phase 2 logic
4. [Post-Formalization](post_formalization.md) - Phase 3 logic
5. [Activation](activation.md) - Phase 4 logic

### For Debugging
1. [Formalization](formalization.md) - Check flow indices
2. [Post-Formalization](post_formalization.md) - Check annotations
3. [Activation](activation.md) - Check working_interpretation
4. [Editor](editor.md) - Use validation tools

---

## 🔑 Key Concepts

### The Compilation Pipeline

```
Natural Language
      ↓
Phase 1: Derivation
      ↓
   .ncds (draft straightforward)
      ↓
Phase 2: Formalization
      ↓
   .ncd (with flow indices and sequences)
      ↓
Phase 3: Post-Formalization
      ↓
   .ncd (enriched with annotations)
      ↓
Phase 4: Activation
      ↓
   .concept.json + .inference.json
      ↓
   Orchestrator Execution
```

### Progressive Formalization

NormCode compilation follows a **progressive formalization** philosophy:

1. **Start loose** - Natural language intent
2. **Add structure** - Hierarchical concepts and operations
3. **Add rigor** - Flow indices, sequence types, bindings
4. **Add context** - Norms, resources, configurations
5. **Make executable** - JSON repositories

Each phase adds specificity while preserving semantic intent.

---

## 💡 The Big Picture

### What Each Phase Does

| Phase | Question Answered | Input | Output |
|-------|-------------------|-------|--------|
| **Derivation** | *What* are we trying to do? | Natural language | `.ncds` structure |
| **Formalization** | *In what order* and *which sequence*? | `.ncds` | `.ncd` (formal) |
| **Post-Formalization** | *How* and *with what resources*? | `.ncd` (formal) | `.ncd` (enriched) |
| **Activation** | *What does the Orchestrator need*? | `.ncd` (enriched) | JSON repositories |

### The Format Ecosystem

| Format | Purpose | Created By |
|--------|---------|------------|
| **`.ncds`** | Draft (easiest to write) | You or LLM |
| **`.ncd`** | Formal syntax | Compiler |
| **`.ncn`** | Natural language companion | Compiler |
| **`.ncdn`** | Hybrid (NCD + NCN together) | Editor tools |
| **`.nc.json`** | Structured JSON | Editor tools |
| **`.nci.json`** | Inference structure | Compiler |
| **`.concept.json`** | Concept repository | Activation |
| **`.inference.json`** | Inference repository | Activation |

---

## 📖 Common Questions

**Q: Do I need to understand the entire pipeline?**  
A: No. If you're just writing plans, read Overview and Editor. The detailed phases are for compiler developers.

**Q: What's the difference between formalization and post-formalization?**  
A: Formalization adds syntactic rigor (flow, sequences). Post-formalization adds execution context (norms, resources).

**Q: Can I write `.ncd` by hand?**  
A: You can, but it's easier to start with `.ncds` (draft) and let the compiler formalize it. Or use the editor.

**Q: What are annotations in post-formalization?**  
A: Comment lines starting with `//`, `|`, or `|%{...}` that tell the orchestrator how to execute each operation.

**Q: How do I convert between formats?**  
A: Use the `update_format.py` tool. See [Editor](editor.md) for details.

**Q: What is working_interpretation?**  
A: A dict in `inference_repo.json` that each sequence's IWI step reads to understand how to execute.

**Q: Where do paradigm names come from?**  
A: From the paradigm registry in `infra/_agent/_models/_paradigms/`. See [Post-Formalization](post_formalization.md).

---

## 🎓 Understanding Levels

### Level 1: Basic Understanding
**Goal**: Understand what compilation does

**Learn**:
- [Overview](overview.md) - Pipeline overview
- [Editor](editor.md) - Use the tools

**You can**: Write and edit plans, understand compiler output.

---

### Level 2: Plan Optimization
**Goal**: Write efficient plans and debug compilation issues

**Learn**:
- [Derivation](derivation.md) - Structure extraction
- [Formalization](formalization.md) - Flow and sequences
- [Post-Formalization](post_formalization.md) - Annotations

**You can**: Optimize plans, debug formalization issues, understand annotations.

---

### Level 3: Compiler Development
**Goal**: Extend or modify the compiler

**Learn**:
- All documents in detail
- [Activation](activation.md) - Repository generation
- Source code in `infra/_compilation/`

**You can**: Extend compiler, add new sequences, modify activation logic.

---

## 🚀 Quick Start Examples

### Example 1: Write and Compile a Simple Plan

**Step 1: Write draft (.ncds)**
```ncds
<- result
    <= calculate the sum
    <- number A
    <- number B
```

**Step 2: Compile to .ncd**
```bash
python compiler.py formalize draft.ncds
```

**Step 3: Generate repositories**
```bash
python compiler.py activate draft.ncd
```

**Result**: `draft.concept.json` and `draft.inference.json` ready for orchestrator.

---

### Example 2: Use the Editor

**Start editor:**
```bash
cd streamlit_app/examples
python launch_demo.py
```

**In browser:**
1. Load your `.ncd` file
2. Edit inline
3. Export to any format
4. Validate with tools

---

### Example 3: Convert Between Formats

**Convert .ncd to .ncdn:**
```bash
python update_format.py convert plan.ncd --to ncdn
```

**Validate:**
```bash
python update_format.py validate plan.ncd
```

**Batch convert directory:**
```bash
python update_format.py batch-convert ./plans --from ncd --to ncdn
```

---

## 🔗 External Resources

### Previous Sections
- **[Introduction](../1_intro/README.md)** - What is NormCode?
- **[Grammar](../2_grammar/README.md)** - The `.ncd` syntax
- **[Execution](../3_execution/README.md)** - How plans run

### Next Section
- **[Tools](../5_tools/README.md)** *(Coming Soon)* - CLI, APIs, integrations

### Source Code
- `infra/_compilation/` - Compiler implementation *(if exists)*
- `streamlit_app/examples/` - Editor and format tools
- `infra/_agent/_models/_paradigms/` - Paradigm registry

---

## 📊 Document Status

| Document | Status | Content Coverage |
|----------|--------|------------------|
| **Overview** | ✅ Complete | Pipeline, philosophy, design principles |
| **Derivation** | ✅ Complete | Natural language → structure |
| **Formalization** | ✅ Complete | Flow indices, sequence types |
| **Post-Formalization** | ✅ Complete | Re-composition, provision, syntax confirmation |
| **Activation** | ✅ Complete | JSON repositories, working_interpretation |
| **Editor** | ✅ Complete | Tools, conversion, validation |

---

## 🎯 Next Sections

After mastering compilation:

- **[5. Tools](../5_tools/README.md)** *(Coming Soon)* - User-facing tools and APIs
- Return to **[Execution](../3_execution/README.md)** - See how compiled plans run

---

## 💡 Key Takeaways

### The Compilation Promise

**NormCode's compilation transforms intent into executable structure while maintaining auditability**:

1. **Progressive formalization**: Each phase adds specificity without losing meaning
2. **Multiple representations**: Different formats for different audiences
3. **Explicit configuration**: All norms and resources are declared
4. **Auditable output**: Every decision is traceable in the JSON repositories
5. **Round-trip consistency**: Can go from JSON back to `.ncd`

### Design Philosophy

```
Flexibility → Structure → Rigor → Configuration → Execution

Each phase answers a specific question about WHAT, HOW, WHEN, and WITH WHAT.
```

---

**Ready to dive in?** Start with [Overview](overview.md) to understand the pipeline, then explore each phase in detail.
