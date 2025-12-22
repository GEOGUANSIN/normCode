# NormCode Documentation Restructuring Plan

This document outlines a simplified reorganization of NormCode documentation with clear, logical sections.

---

## 📋 Table of Contents

1. [New Structure Overview](#new-structure-overview)
2. [Section Descriptions](#section-descriptions)
3. [Source File Mapping](#source-file-mapping)
4. [Implementation Approach](#implementation-approach)

---

## New Structure Overview

```
documentation/
├── README.md                          # Main entry point & navigation
│
├── 1_intro/
│   ├── overview.md                    # What is NormCode? Why use it?
│   ├── quickstart.md                  # 5-minute getting started
│   └── examples.md                    # Simple example plans
│
├── 2_grammar/
│   ├── ncd_format.md                  # The .ncd file format specification
│   ├── semantic_concepts.md           # Semantic types: {}, <>, [], :S:, etc.
│   ├── syntactic_operators.md         # Operators: $, &, @, *
│   ├── references_and_axes.md         # Reference system & tensor algebra
│   └── complete_syntax_reference.md   # Full formal grammar reference
│
├── 3_execution/
│   ├── overview.md                    # Execution model overview
│   ├── reference_system.md            # How references work at runtime
│   ├── agent_sequences.md             # Agent sequence types & behavior
│   └── orchestrator.md                # Orchestrator & execution engine
│
├── 4_compilation/
│   ├── pipeline_overview.md           # The 5-phase compilation process
│   ├── derivation.md                  # Phase 1-2: Natural language → Structure
│   ├── formalization.md               # Phase 3: Adding formal rigor
│   ├── post_formalization.md          # Phase 4: Context & configuration
│   └── activation.md                  # Phase 5: .ncd → executable repositories
│
└── 5_tools/
    ├── cli.md                         # Command-line interface
    ├── editor.md                      # Visual editor usage
    ├── streamlit_executor.md          # Streamlit execution interface
    └── api_reference.md               # Python API documentation
```

---

## Section Descriptions

### 1. Introduction
**Purpose**: Get users started quickly with minimal barriers

**Content**:
- **overview.md**: Problem statement, core value proposition, when to use NormCode
- **quickstart.md**: 5-10 minute tutorial showing a complete workflow
- **examples.md**: Gallery of simple, self-contained example plans

**Audience**: New users, evaluators, anyone wanting a quick overview

---

### 2. Grammar
**Purpose**: Complete specification of the .ncd format and syntax

**Content**:
- **ncd_format.md**: File structure, basic syntax, concept definitions
- **semantic_concepts.md**: Deep dive into `{}`, `<>`, `[]`, `:S:`, `({})`, `<{}>`
- **syntactic_operators.md**: All operators `$`, `&`, `@`, `*` with modifiers `%>`, `%<`, `%:`, `%^`, `%@`
- **references_and_axes.md**: Reference system, axis mechanics, tensor algebra
- **complete_syntax_reference.md**: Formal grammar, all syntax patterns

**Audience**: Plan writers, anyone learning to write .ncd files

---

### 3. Execution
**Purpose**: Understanding how plans run and what happens at runtime

**Content**:
- **overview.md**: High-level execution model, concept flow
- **reference_system.md**: How references store and retrieve data
- **agent_sequences.md**: All sequence types (assigning, grouping, timing, looping, imperative, judgement)
- **orchestrator.md**: Execution engine, blackboard, checkpointing, debugging

**Audience**: Advanced users, debuggers, people optimizing plans

---

### 4. Compilation
**Purpose**: Understanding how natural language becomes executable plans

**Content**:
- **pipeline_overview.md**: The 5-phase compilation process overview
- **derivation.md**: Phase 1-2 (Natural language → Structured concepts)
- **formalization.md**: Phase 3 (Adding semantic types and structure)
- **post_formalization.md**: Phase 4 (Adding paradigms, resources, context)
- **activation.md**: Phase 5 (.ncd → concept_repo.json + inference_repo.json)

**Audience**: Compiler maintainers, advanced users, contributors

---

### 5. Tools
**Purpose**: Using NormCode's user-facing tools and APIs

**Content**:
- **cli.md**: Command-line interface for compilation and execution
- **editor.md**: Visual editor for creating and editing plans
- **streamlit_executor.md**: Web interface for running plans
- **api_reference.md**: Python API for programmatic use

**Audience**: Tool users, integrators, developers building on NormCode

---

## Source File Mapping

### From Current Files → New Structure

| Current File | New Location | Notes |
|-------------|--------------|-------|
| **Introduction** |
| `shared---normcode_intro.md` | Split: `1_intro/overview.md` + `1_intro/quickstart.md` | Extract intro & tutorial |
| `Editor_EXAMPLES.md` | `1_intro/examples.md` | Simple examples for new users |
| **Grammar** |
| `shared---normcode_formalism_basic.md` | Split: `2_grammar/ncd_format.md` + `2_grammar/semantic_concepts.md` | Basic format + semantics |
| `shared---normcode_semantical_concepts.md` | Merge into: `2_grammar/semantic_concepts.md` | Consolidate semantic concepts |
| `shared---normcode_syntatical_concepts_reconstruction.md` | `2_grammar/syntactic_operators.md` | All operators & modifiers |
| `shared---normcode_reference_guide.md` + `shared---normcode_axis.md` | Merge into: `2_grammar/references_and_axes.md` | Unified reference system doc |
| (Extracted from above) | `2_grammar/complete_syntax_reference.md` | Complete formal grammar |
| **Execution** |
| (New synthesis) | `3_execution/overview.md` | High-level execution model |
| (Extracted from reference_guide) | `3_execution/reference_system.md` | Runtime reference behavior |
| `shared---normcode_agent_sequence_guide.md` | `3_execution/agent_sequences.md` | All sequence types |
| `shared---normcode_orchestrator_guide.md` | `3_execution/orchestrator.md` | Orchestrator & engine |
| **Compilation** |
| `shared---normcode_compilations.md` + `shared---pipeline_goal_and_structure.md` | Merge into: `4_compilation/pipeline_overview.md` | Complete pipeline overview |
| (Extracted from pipeline docs) | `4_compilation/derivation.md` | Phase 1-2 details |
| (Extracted from pipeline docs) | `4_compilation/formalization.md` | Phase 3 details |
| (Extracted from pipeline docs) | `4_compilation/post_formalization.md` | Phase 4 details |
| `shared---normcode_activation.md` | `4_compilation/activation.md` | Phase 5: activation spec |
| **Tools** |
| (New) | `5_tools/cli.md` | CLI documentation |
| `Editor_README.md` | `5_tools/editor.md` | Editor guide |
| `StreamlitAPP_README.md` | `5_tools/streamlit_executor.md` | Streamlit interface |
| (New/Generated) | `5_tools/api_reference.md` | Python API docs |

### Additional Files

| Current File | Status | Notes |
|-------------|--------|-------|
| `paper_draft.md` | Keep separate | Academic paper (optional reading) |

---

## Implementation Approach

### Phase 1: Create Core Structure
1. Create directory structure (`1_intro/`, `2_grammar/`, etc.)
2. Create main `README.md` with navigation
3. Set up templates for each section

### Phase 2: Intro Section (Quick Wins)
1. Extract intro content → `1_intro/overview.md`
2. Create minimal quickstart → `1_intro/quickstart.md`
3. Move examples → `1_intro/examples.md`

### Phase 3: Grammar Section (Core Documentation)
1. Write `2_grammar/ncd_format.md` - basic file format
2. Consolidate semantic concepts → `2_grammar/semantic_concepts.md`
3. Consolidate syntactic operators → `2_grammar/syntactic_operators.md`
4. Merge reference docs → `2_grammar/references_and_axes.md`
5. Create complete reference → `2_grammar/complete_syntax_reference.md`

### Phase 4: Execution Section
1. Write execution overview → `3_execution/overview.md`
2. Extract runtime reference behavior → `3_execution/reference_system.md`
3. Move agent sequences → `3_execution/agent_sequences.md`
4. Consolidate orchestrator docs → `3_execution/orchestrator.md`

### Phase 5: Compilation Section
1. Merge pipeline docs → `4_compilation/pipeline_overview.md`
2. Extract phase-specific docs → `derivation.md`, `formalization.md`, etc.
3. Simplify activation doc → `4_compilation/activation.md`

### Phase 6: Tools Section
1. Document CLI → `5_tools/cli.md`
2. Move editor guide → `5_tools/editor.md`
3. Move streamlit guide → `5_tools/streamlit_executor.md`
4. Generate/write API reference → `5_tools/api_reference.md`

### Phase 7: Polish
1. Add cross-references between sections
2. Ensure consistent terminology
3. Add diagrams where helpful
4. Review for clarity and completeness

---

## Key Principles

1. **Progressive disclosure**: Intro → Grammar → Execution → Compilation → Tools
2. **Clear separation**: Each section has a distinct purpose
3. **Self-contained documents**: Each file should be readable independently
4. **Minimal redundancy**: Information lives in one primary location
5. **Cross-references**: Link between sections when needed

---

## Next Steps

1. Review this structure with stakeholders
2. Begin Phase 1: Create directory structure
3. Start with Phase 2: Quick wins in intro section
4. Iterate section by section