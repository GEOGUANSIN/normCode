# NormCode Overview

**NormCode is a language for writing structured AI plans that enforce data isolation by design.**

## Core Problem Solved

When chaining multiple LLM calls, context pollution causes failures. NormCode solves this by making each step a "sealed room" - it only sees what you explicitly pass in.

## Core Idea: Plans of Inferences

NormCode lets you write **plans of inferences**—structured breakdowns of complex tasks into small, isolated steps that AI agents execute reliably.

Each inference is a self-contained unit:
- **One clear action** (what to do)
- **Explicit inputs** (what it receives)
- **One output** (what it produces)

## Two Operation Types

| Type | LLM? | Cost | Speed | Examples |
|------|------|------|-------|----------|
| **Semantic** | ✅ Yes | Tokens | Seconds | Reasoning, generating, analyzing |
| **Syntactic** | ❌ No | Free | Instant | Collecting, selecting, routing |

## File Formats

| Format | Purpose | Description |
|--------|---------|-------------|
| **`.ncds`** | Draft/authoring | Rough logic—easiest to write |
| **`.ncd`** | Formal executable | Structured with operators and annotations |
| **`.ncn`** | Natural language | Human-readable companion |
| **`.concept.json`** | Concept repository | Executable format for orchestrator |
| **`.inference.json`** | Inference repository | Executable format for orchestrator |

## Compilation Pipeline

```
.ncds (draft) → .ncd (formalized) → .nci.json (structure) → .concept.json + .inference.json
```

