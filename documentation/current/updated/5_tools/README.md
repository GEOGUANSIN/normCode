# NormCode Tools

**User-facing tools and interfaces for working with NormCode plans.**

---

## Overview

This section documents the tools that enable users to create, execute, debug, and audit NormCode plans. The centerpiece is the **Graph Canvas Tool**—a unified visual interface that brings together all aspects of working with NormCode.

---

## The Vision: Graph Canvas Tool

The Graph Canvas Tool is designed around a core principle: **the inference graph IS the interface**.

### What It Does

```
┌─────────────────────────────────────────────────────────────────────────┐
│  .concept.json + .inference.json                                        │
│              ↓                                                          │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                     GRAPH CANVAS                                  │ │
│  │                                                                   │ │
│  │   ┌─────┐       ┌─────┐       ┌─────┐                           │ │
│  │   │Value│──────▶│Func │──────▶│Value│   ← Interactive nodes     │ │
│  │   └─────┘       └─────┘       └─────┘                           │ │
│  │      │             │             │                               │ │
│  │      ▼             ▼             ▼                               │ │
│  │   Tensor        Sequence      Reference    ← Expandable details │ │
│  │   Preview       Pipeline      Inspector                         │ │
│  │                                                                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│              ↓                                                          │
│  Execute • Debug • Inspect • Modify • Audit                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Visualize** | See the full inference graph with function and value nodes |
| **Execute** | Run plans with live progress on the graph |
| **Debug** | Set breakpoints, step through, inspect state |
| **Inspect** | View tensors, logs, and execution context at any node |
| **Modify** | Override values, change paradigms, retry steps |
| **Audit** | Trace data flow, export execution records |

---

## Documentation

### Planning & Architecture

| Document | Description |
|----------|-------------|
| **[Implementation Plan](implementation_plan.md)** | High-level architecture and phased implementation plan |

### Tool Documentation (Planned)

| Document | Description | Status |
|----------|-------------|--------|
| **Graph Canvas User Guide** | How to use the visual graph interface | 🚧 Planned |
| **Execution Control Guide** | Breakpoints, stepping, and debugging | 🚧 Planned |
| **Reference Inspector Guide** | Inspecting tensor data | 🚧 Planned |
| **API Reference** | Programmatic access to tool functions | 🚧 Planned |

---

## The Two Node Types

The graph displays two fundamentally different kinds of nodes:

### Value Nodes (Data)
- Contain **References** (multi-dimensional tensors)
- Show **axes**, **shape**, and **data preview**
- Represent the data flowing through the plan
- Expandable to show full tensor contents

### Function Nodes (Operations)
- Contain **sequences** (imperative, grouping, looping, etc.)
- Show **paradigm** and **working interpretation**
- Represent the operations transforming data
- Expandable to show execution pipeline status

---

## Execution Control

The graph provides direct control over execution:

### Control Actions

| Control | Description |
|---------|-------------|
| **▶ Run** | Execute all ready inferences |
| **⏸ Pause** | Stop after current inference |
| **⏭ Step** | Execute exactly one inference |
| **🎯 Run to** | Execute until selected node |
| **🔁 Re-run** | Reset and re-execute from a node |

### Breakpoints

| Type | Behavior |
|------|----------|
| **Unconditional** | Always pause at this node |
| **Conditional** | Pause when expression is true |
| **On Error** | Pause only if node fails |
| **Log Only** | Log but don't pause |

---

## Inspection Features

### Per-Node Inspection

When you select a node, you can see:
- **Status**: Current state, duration, cost
- **Data**: Tensor contents (values) or paradigm details (functions)
- **Logs**: Execution logs for this specific node
- **Context**: Exactly what the LLM saw (for semantic operations)

### Data Flow Tracing

- Click any value → "Trace Origin" → See full ancestry
- Click any function → See all inputs it received
- Visual highlighting of data lineage

---

## Relationship to Other Sections

| Section | Relationship |
|---------|--------------|
| **[2. Grammar](../2_grammar/README.md)** | Tools work with `.ncd` format (via compilation) |
| **[3. Execution](../3_execution/README.md)** | Tools integrate with Orchestrator |
| **[4. Compilation](../4_compilation/README.md)** | Tools load compiled repositories |

---

## Existing Tools (Legacy)

While the Graph Canvas Tool is in development, existing tools include:

| Tool | Location | Description |
|------|----------|-------------|
| **CLI Orchestrator** | `cli_orchestrator.py` | Command-line execution |
| **Streamlit App** | `streamlit_app/` | Web UI for execution |
| **Editor App** | `editor_app/` | React/FastAPI editor |
| **Format Tools** | `update_format.py` | Format conversion CLI |

See the [Compilation Editor docs](../4_compilation/editor.md) for current editor capabilities.

---

## Status

| Component | Status |
|-----------|--------|
| **Implementation Plan** | ✅ Complete |
| **Graph Canvas Tool** | 🚧 In Planning |
| **User Documentation** | 🚧 Planned |
| **API Documentation** | 🚧 Planned |

---

## Next Steps

1. Review and validate the [Implementation Plan](implementation_plan.md)
2. Build Phase 1 prototype (basic graph display)
3. Iterate based on user feedback
4. Complete documentation as features are implemented

---

**Ready to dive in?** Start with the [Implementation Plan](implementation_plan.md) for the full technical vision.
