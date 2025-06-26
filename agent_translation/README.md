# NormCode Agentic Translation Framework

## Overview

This framework provides an automated, agentic approach to translating natural language instructions into formal NormCode structures. The system implements the complete NormCode analysis pipeline, from initial question sequencing deconstruction through final template creation.

## Architecture

The framework consists of multiple specialized agents working in sequence:

### 1. Question Sequencing Agent
- **Purpose**: Deconstructs instructive text into question sequences
- **Input**: Natural language instructions (norm-text)
- **Output**: Structured question hierarchy with main and ensuing questions
- **Key Functions**:
  - Main question identification (what/how/when)
  - Sentence chunking and grouping
  - Question hierarchy building
  - Question type classification

### 2. In-Question Analysis Agent
- **Purpose**: Transforms questions and answers into formal NormCode structures
- **Input**: Question-answer pairs from Phase 1
- **Output**: Complete NormCode structures with templates and references
- **Key Functions**:
  - Question parsing and validation
  - Clause analysis and classification
  - Template abstraction and reference mapping
  - Logical structure preservation

### 3. NormCode Integration Agent
- **Purpose**: Combines multiple NormCode structures into unified, hierarchical representations
- **Input**: Individual NormCode structures from Phase 2
- **Output**: Integrated NormCode structures showing complete workflows and relationships
- **Key Functions**:
  - Hierarchical nesting of related structures
  - Agent-consequence relationship mapping
  - Shared reference system unification
  - Semantic flow integration
  - Modular structure composition

