# NormCode Documentation Restructuring Plan

This document outlines the reorganization of NormCode documentation to improve navigation, reduce redundancy, and create clear reading paths for different audiences.

---

## 📋 Table of Contents

1. [New Structure Overview](#new-structure-overview)
2. [File Mapping: Current → New](#file-mapping-current--new)
3. [Source Files for Each New Document](#source-files-for-each-new-document)
4. [Reading Paths by Audience](#reading-paths-by-audience)
5. [Implementation Checklist](#implementation-checklist)

---

## New Structure Overview

```
documentation/
├── README.md                          # Navigation hub & entry point
├── getting_started/
│   ├── 01_quickstart.md              # 5-minute introduction
│   ├── 02_core_concepts.md            # Essential concepts overview
│   └── 03_first_plan.md              # Hands-on tutorial
├── core_concepts/
│   ├── semantics.md                  # Semantic concept types
│   ├── syntax_operators.md           # Syntactic operators ($, &, @, *)
│   ├── references_and_axes.md        # Reference system & tensor algebra
│   └── agent_sequences.md            # Agent execution pipelines
├── compilation/
│   ├── overview.md                   # Compilation pipeline high-level
│   ├── derivation.md                 # Phase 1-2: NL → Structure
│   ├── formalization.md              # Phase 3: Adding rigor
│   ├── post_formalization.md         # Phase 4: Context & configuration
│   └── activation_overview.md        # Phase 5: Overview (simplified)
├── execution/
│   ├── orchestrator.md               # Execution engine
│   ├── checkpointing.md              # State persistence
│   └── debugging.md                  # Troubleshooting guide
├── advanced/
│   ├── paradigms.md                  # Paradigm system deep dive
│   ├── multi_agent.md                # Multi-agent planning
│   └── extending_normcode.md         # How to add new features
├── reference/
│   ├── ncd_syntax_complete.md        # Full formal grammar
│   ├── activation_spec_detailed.md   # Complete activation spec (for implementers)
│   └── api_reference.md              # Python API documentation
└── paper/
    └── paper_draft.md                 # Academic paper (with cross-references)
```

---

## File Mapping: Current → New

### Current Files Status

| Current File | Status | New Location(s) | Notes |
|-------------|--------|-----------------|-------|
| `shared---normcode_intro.md` | ✅ Keep & Split | `getting_started/02_core_concepts.md` + `getting_started/03_first_plan.md` | Extract tutorial parts |
| `shared---normcode_formalism_basic.md` | ✅ Keep & Split | `core_concepts/semantics.md` + `reference/ncd_syntax_complete.md` | Split conceptual vs. reference |
| `shared---normcode_activation.md` | ✅ Split | `compilation/activation_overview.md` + `reference/activation_spec_detailed.md` | Too long (1351 lines) |
| `shared---normcode_reference_guide.md` | ✅ Merge | `core_concepts/references_and_axes.md` | Merge with axis.md |
| `shared---normcode_axis.md` | ✅ Merge | `core_concepts/references_and_axes.md` | Merge with reference_guide.md |
| `shared---normcode_agent_sequence_guide.md` | ✅ Keep | `core_concepts/agent_sequences.md` | Rename only |
| `shared---normcode_syntatical_concepts_reconstruction.md` | ✅ Keep | `core_concepts/syntax_operators.md` | Rename only |
| `shared---normcode_semantical_concepts.md` | ✅ Merge | `core_concepts/semantics.md` | Merge with formalism parts |
| `shared---normcode_orchestrator_guide.md` | ✅ Split | `execution/orchestrator.md` + `execution/checkpointing.md` | Split concerns |
| `shared---normcode_compilations.md` | ✅ Merge | `compilation/overview.md` | Merge with pipeline_goal |
| `shared---pipeline_goal_and_structure.md` | ✅ Merge | `compilation/overview.md` + `compilation/derivation.md` | Merge with compilations.md |
| `paper_draft.md` | ✅ Enhance | `paper/paper_draft.md` | Add cross-references |
| `Editor_EXAMPLES.md` | ✅ Keep | `getting_started/examples.md` | Move to getting_started |
| `Editor_README.md` | ✅ Keep | `getting_started/editor_guide.md` | Move to getting_started |
| `StreamlitAPP_README.md` | ✅ Keep | `execution/streamlit_interface.md` | Move to execution |

---

## Source Files for Each New Document

### Getting Started Section

#### `getting_started/01_quickstart.md` (NEW)
**Purpose**: 5-minute introduction to NormCode
**Source Files**:
- Extract from `shared---normcode_intro.md` (Sections 1-2: Problem & First Plan)
- Extract from `paper_draft.md` (Section 1.1: The Problem)
- **New content**: Simple "Hello World" example

#### `getting_started/02_core_concepts.md`
**Purpose**: Essential concepts overview
**Source Files**:
- `shared---normcode_intro.md` (Sections 2-5: Core Syntax, Execution, Why Structure Matters)
- `shared---normcode_semantical_concepts.md` (Summary table)
- `paper_draft.md` (Section 3.1-3.3: Core Syntax, Three Formats, Concept Types)

#### `getting_started/03_first_plan.md`
**Purpose**: Hands-on tutorial
**Source Files**:
- `shared---normcode_intro.md` (Section 1: Your First NormCode Plan)
- `Editor_EXAMPLES.md` (Simple examples)
- **New content**: Step-by-step walkthrough

#### `getting_started/examples.md`
**Purpose**: Example plans
**Source Files**:
- `Editor_EXAMPLES.md` (entire file)
- `paper_draft.md` (Appendix A: Base-X Addition)

#### `getting_started/editor_guide.md`
**Purpose**: Editor usage
**Source Files**:
- `Editor_README.md` (entire file)

---

### Core Concepts Section

#### `core_concepts/semantics.md`
**Purpose**: Semantic concept types (the "vocabulary")
**Source Files**:
- `shared---normcode_semantical_concepts.md` (entire file)
- `shared---normcode_formalism_basic.md` (Section 3.1: Semantic Concept Types)
- `shared---normcode_intro.md` (Section 2: Core Syntax, Section 3.3: Semantic Types)
- `paper_draft.md` (Section 3.3: Semantic Concept Types)

**Structure**:
1. Overview: What are semantic concepts?
2. Non-Functional Types: `{}`, `<>`, `[]`, `:S:`
3. Functional Types: `({})`, `<{}>`
4. Natural Language Extraction Guide
5. Summary Table

#### `core_concepts/syntax_operators.md`
**Purpose**: Syntactic operators ($, &, @, *)
**Source Files**:
- `shared---normcode_syntatical_concepts_reconstruction.md` (entire file)
- `shared---normcode_formalism_basic.md` (Section 3.2: Syntactical Concept Types)
- `shared---normcode_intro.md` (Section 5: Not Every Step Needs an LLM)
- `paper_draft.md` (Section 3.4: Syntactic Concept Types)

**Structure**:
1. Why Syntactic Operators? (The Intuition)
2. Unified Modifier System
3. Assigning Operators ($=, $%, $., $+, $-)
4. Grouping Operators (&[{}], &[#])
5. Timing Operators (@:', @:!, @.)
6. Looping Operators (*.)
7. How They Work Toge