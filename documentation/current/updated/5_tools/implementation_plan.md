# NormCode Graph Canvas Tool - Implementation Plan

**A unified, graph-based interface for executing, debugging, and auditing NormCode plans.**

---

## Overview

This document outlines the high-level implementation plan for the NormCode Graph Canvas Tool—a visual, interactive environment where users can load, visualize, execute, debug, and audit NormCode plans through a unified graph interface.

### Core Concept

The tool provides a **single canvas** where:
1. The inference graph is always visible
2. The graph transforms to show different information layers (preview, execution, debug, audit)
3. Users interact directly with nodes for control and inspection
4. Both structure and state are always visible—no hidden logs or separate screens

---

## System Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           INPUT                                         │
│   .concept.json + .inference.json (from compilation)                   │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       GRAPH CONSTRUCTION                                │
│   Parse repositories → Build node/edge model → Layout graph            │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        GRAPH CANVAS                                     │
│   ┌───────────────────────────────────────────────────────────────┐    │
│   │  Visual Graph (zoomable, pannable, interactive)               │    │
│   │  - Function Nodes (sequences, paradigms)                      │    │
│   │  - Value Nodes (tensors, references)                          │    │
│   │  - Edges (data flow, control dependencies)                    │    │
│   └───────────────────────────────────────────────────────────────┘    │
│                                                                         │
│   ┌─────────────────────┐  ┌─────────────────────────────────────┐     │
│   │  Control Bar        │  │  Detail Panel                       │     │
│   │  (run, pause, step) │  │  (node inspection, logs, data)      │     │
│   └─────────────────────┘  └─────────────────────────────────────┘     │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      CONTROLLED EXECUTION                               │
│   Orchestrator integration with breakpoints, stepping, logging         │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           OUTPUT                                        │
│   Results + Execution Trace + Audit Report                             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Existing Reusable Infrastructure

Before building new components, significant infrastructure already exists that can be leveraged:

### Streamlit App (`streamlit_app/`)

| Component | Location | Reusable For |
|-----------|----------|--------------|
| **Graph Visualization** | `tabs/execute/preview/graph_view.py` | Graphviz-based graph with Viz.js, pan/zoom, node styling by category |
| **Tensor Display** | `tabs/execute/preview/tensor_display.py` | Multi-dimensional tensor rendering (0D-ND), axis selection, editing |
| **Tensor Utilities** | `tabs/execute/preview/utils.py` | Shape calculation, slicing, category detection, formatting |
| **Orchestration Runner** | `orchestration/orchestration_runner.py` | Full Orchestrator integration, fresh/resume/fork modes |
| **Results Display** | `tabs/results/` | Concept result visualization, tensor reuse |
| **Log Management** | `core/log_manager.py` | Structured logging infrastructure |
| **File Utilities** | `core/file_utils.py` | Repository file saving, path management |

**Key features already implemented**:
- Graphviz DOT generation with node categorization (semantic-function, semantic-value, syntactic-function)
- Interactive SVG with svg-pan-zoom library
- Tensor slicing for high-dimensional data
- Orchestrator checkpoint/resume/fork support
- Human-in-the-loop tool injection

### Editor App (`editor_app/`)

| Component | Location | Reusable For |
|-----------|----------|--------------|
| **React Graph View** | `frontend/src/components/FlowGraphView.tsx` | SVG-based graph with selection, info panels |
| **Graph Service** | `backend/services/graph_service.py` | Flow index parsing, node positioning, edge computation |
| **Execution Service** | `backend/services/normcode_execution_service.py` | Background execution, log streaming |
| **Log Viewer** | `frontend/src/components/LogViewer.tsx` | Real-time log display with auto-scroll |
| **Repository Management** | `backend/routers/repository_router.py` | CRUD for repository sets |
| **API Structure** | `backend/routers/` | FastAPI router patterns |

**Key features already implemented**:
- React component for SVG graph rendering
- Node selection with incoming/outgoing edge highlighting
- Level-based layout algorithm
- Background thread execution with file-based logging
- Repository set data schemas

### Core Infrastructure (`infra/`)

| Component | Location | Reusable For |
|-----------|----------|--------------|
| **Orchestrator** | `_orchest/_orchestrator.py` | Core execution engine |
| **Checkpointing DB** | `_orchest/_db.py` | SQLite checkpoint storage |
| **ConceptRepo/InferenceRepo** | `_orchest/_repo.py` | Repository data structures |
| **Reference System** | `_agent/` | Tensor/Reference implementation |
| **Agent Sequences** | `_agent/_sequences/` | Sequence execution logic |

### Reuse Strategy

| New Feature | Can Leverage |
|-------------|--------------|
| **Graph Display** | `graph_view.py` (Streamlit) or `FlowGraphView.tsx` (React) |
| **Node Styling** | `get_concept_category()`, `get_node_style()` |
| **Tensor Inspection** | `tensor_display.py`, tensor slicing utilities |
| **Execution Integration** | `orchestration_runner.py`, existing Orchestrator |
| **Log Display** | `LogViewer.tsx` or `log_manager.py` |
| **API Design** | Existing FastAPI routers as patterns |

---

## Component Architecture

### 1. Data Layer

#### 1.1 Repository Loader
**Input**: `.concept.json` + `.inference.json`  
**Output**: Unified graph model

```
ConceptRepository
├── concepts: Map<concept_name, ConceptDefinition>
│   ├── type: "{}" | "[]" | "<>" | ":S:" | ...
│   ├── is_ground_concept: boolean
│   ├── is_final_concept: boolean
│   ├── reference_axis_names: string[]
│   └── reference_data: any (for ground concepts)

InferenceRepository  
├── inferences: Map<flow_index, InferenceDefinition>
│   ├── concept_to_infer: string
│   ├── function_concept: string
│   ├── value_concepts: string[]
│   ├── context_concepts: string[]
│   ├── inference_sequence: string
│   └── working_interpretation: WorkingInterpretation
```

#### 1.2 Graph Model
**Purpose**: Abstract graph representation independent of visualization

```
GraphModel
├── nodes: Map<id, GraphNode>
│   ├── ValueNode
│   │   ├── concept_name: string
│   │   ├── reference: Reference | null
│   │   └── status: pending | complete | skipped | failed
│   └── FunctionNode
│       ├── concept_name: string
│       ├── sequence_type: string
│       ├── working_interpretation: object
│       └── execution_state: pending | running | complete | failed
│
├── edges: Edge[]
│   ├── source: node_id
│   ├── target: node_id
│   ├── type: "data_flow" | "control" | "produces"
│   └── binding: number | null (for value ordering)
│
└── inferences: Map<flow_index, Inference>
    ├── concept_to_infer: ValueNode
    ├── function_concept: FunctionNode
    └── value_concepts: ValueNode[]
```

---

### 2. Visualization Layer

#### 2.1 Graph Layout Engine
**Purpose**: Compute node positions based on selected layout

**Layout Options**:
| Layout | Algorithm | Best For |
|--------|-----------|----------|
| Tree (top-down) | Hierarchical Sugiyama | Clear execution order |
| Tree (bottom-up) | Hierarchical Sugiyama | Matches NormCode reading |
| Force-directed | D3-force / Dagre | Complex dependencies |
| Layered | Custom | Timeline view |

#### 2.2 Graph Renderer
**Purpose**: Render nodes, edges, and state to canvas

**Node Rendering**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│  VALUE NODE                          FUNCTION NODE                      │
│  ┌─────────────────────┐            ◇─────────────────────◇            │
│  │ {concept_name}      │            ╱                       ╲           │
│  │ ─────────────────── │           ╱  ::(function_name)      ╲          │
│  │ axes: [axis1, ...]  │          ◇    sequence: imperative   ◇         │
│  │ shape: (n, m)       │           ╲                         ╱          │
│  │ [status indicator]  │            ╲                       ╱           │
│  └─────────────────────┘             ◇─────────────────────◇            │
└─────────────────────────────────────────────────────────────────────────┘
```

**State Visualization**:
| State | Value Node Color | Function Node Color |
|-------|-----------------|---------------------|
| Pending | Gray | Gray |
| Running | Blue pulse | Blue pulse |
| Complete | Green | Green |
| Failed | Red | Red |
| Skipped | Striped gray | Striped gray |
| Breakpoint | Red dot indicator | Red dot indicator |
| Paused | Yellow border | Yellow border |

#### 2.3 View Modes
**Purpose**: Different ways to interpret the same graph

| View Mode | Emphasis | When to Use |
|-----------|----------|-------------|
| **Bipartite** | Both node types visible | Understanding structure |
| **Function-centric** | Functions as nodes, values as edges | Execution flow focus |
| **Value-centric** | Values as nodes, functions as edges | Data flow focus |

---

### 3. Interaction Layer

#### 3.1 Navigation
| Action | Gesture/Key | Result |
|--------|-------------|--------|
| Pan | Drag canvas | Move view |
| Zoom | Scroll / Pinch | Zoom in/out |
| Select | Click node | Show details |
| Multi-select | Shift+Click | Select multiple |
| Focus | Double-click | Center and zoom to node |
| Search | Ctrl+F | Highlight matching nodes |

#### 3.2 Node Expansion
**Purpose**: Reveal interior structure of nodes

**Value Node Expansion**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│  {extracted clauses}                                                    │
│  ═══════════════════════════════════════════════════════════════════   │
│  Reference Details:                                                     │
│  ├─ Axes: [clause_idx]                                                 │
│  ├─ Shape: (7,)                                                        │
│  ├─ Element Type: dict(text: str, page: int)                          │
│  └─ Skip Values: 2 filtered                                           │
│                                                                         │
│  Data Preview:                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ [0]: {text: "Party A shall...", page: 3}                        │   │
│  │ [1]: {text: "Liability for...", page: 5}                        │   │
│  │ [2]: @SKIP@                                                     │   │
│  │ ...                                                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  [View Full Data] [Export] [Trace Origin]                              │
└─────────────────────────────────────────────────────────────────────────┘
```

**Function Node Expansion**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│  ::(extract liability clauses)                                          │
│  ═══════════════════════════════════════════════════════════════════   │
│  Sequence: imperative                                                   │
│  Paradigm: h_PromptTemplate-c_GenerateJson-o_List                      │
│                                                                         │
│  Working Interpretation:                                                │
│  ├─ value_order: {{clean text}: 1}                                     │
│  ├─ prompt_location: provision/prompts/extract.md                      │
│  └─ output_type: list[dict]                                            │
│                                                                         │
│  Execution Pipeline:                                                    │
│  ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐   ┌─────┐                       │
│  │ IWI │ → │ IR  │ → │ MFP │ → │ MVP │ → │ TVA │ → ...                 │
│  │ ✓   │   │ ✓   │   │ ✓   │   │ ✓   │   │ 🔄  │                       │
│  └─────┘   └─────┘   └─────┘   └─────┘   └─────┘                       │
│                                                                         │
│  [View Prompt] [View Full Context] [Modify Paradigm]                   │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3.3 Context Menus
**Value Node Context Menu**:
- View Data
- Export Data
- Trace Origin
- Override Value...
- Set Breakpoint
- Copy Reference

**Function Node Context Menu**:
- View Details
- View Prompt/Script
- Retry
- Skip
- Modify Working Interpretation...
- Set Breakpoint

---

### 4. Execution Control Layer

#### 4.1 Control Bar
```
┌─────────────────────────────────────────────────────────────────────────┐
│  [▶ Run] [⏸ Pause] [⏹ Stop] [⏭ Step] [⏩ Step Over] [🔄 Restart]       │
│                                                                          │
│  [🎯 Run to Selected] [🔁 Re-run from Here]                             │
│                                                                          │
│  Breakpoints: 3    Status: Running    Progress: ████░░ 8/12            │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 4.2 Execution Engine Integration
**Purpose**: Bridge between UI and Orchestrator

```
ExecutionController
├── orchestrator: Orchestrator instance
├── breakpoints: Set<flow_index>
├── execution_mode: "run" | "step" | "paused"
│
├── methods:
│   ├── start() → Begin execution
│   ├── pause() → Pause after current inference
│   ├── step() → Execute one inference
│   ├── stepOver() → Execute branch
│   ├── resume() → Continue from pause
│   ├── stop() → Abort execution
│   ├── runTo(flow_index) → Run until specific node
│   └── rerunFrom(flow_index) → Reset and re-execute
│
└── events:
    ├── onInferenceStart(flow_index)
    ├── onInferenceComplete(flow_index, result)
    ├── onInferenceFailed(flow_index, error)
    ├── onBreakpointHit(flow_index)
    └── onExecutionComplete(results)
```

#### 4.3 Breakpoint System
**Breakpoint Types**:
| Type | Trigger |
|------|---------|
| Unconditional | Always pause |
| Conditional | Pause when expression is true |
| Error | Pause only on failure |
| Hit Count | Pause after N executions |
| Log-only | Log but don't pause |

**Breakpoint Storage**:
```
Breakpoint
├── flow_index: string
├── type: "unconditional" | "conditional" | "error" | "hit_count"
├── condition: string | null (for conditional)
├── hit_count: number | null
├── enabled: boolean
└── actions: ("pause" | "log")[]
```

---

### 5. Inspection Layer

#### 5.1 Detail Panel
**Purpose**: Show detailed information for selected node

**Sections**:
1. **Identity**: Name, type, flow index
2. **Status**: Current state, duration, cost
3. **Data**: For values—tensor contents; for functions—paradigm details
4. **Logs**: Execution logs for this node
5. **Actions**: Contextual actions (retry, skip, export, etc.)

#### 5.2 Log Viewer
**Purpose**: Show execution logs per-node and globally

```
LogViewer
├── mode: "node" | "global" | "timeline"
├── filters:
│   ├── level: Set<"error" | "warn" | "info" | "debug" | "trace">
│   ├── node: string | null
│   └── search: string
│
├── display:
│   ├── timestamp
│   ├── level
│   ├── node (flow_index)
│   ├── phase (IWI, IR, MFP, MVP, TVA, etc.)
│   └── message
│
└── actions:
    ├── export()
    ├── search(query)
    └── jumpToNode(flow_index)
```

#### 5.3 Reference Inspector
**Purpose**: Deep inspection of tensor data

```
ReferenceInspector
├── reference: Reference
│
├── views:
│   ├── Summary: axes, shape, element type, skip count
│   ├── Table: spreadsheet-like view
│   ├── Slice: view along specific axis
│   ├── Raw: JSON representation
│   └── Diff: compare with another reference
│
└── actions:
    ├── export(format: "json" | "csv" | "clipboard")
    ├── filter(predicate)
    └── traceOrigin() → highlight producing node
```

---

### 6. Modification Layer

#### 6.1 Value Override
**Purpose**: Inject or modify values at any node

```
ValueOverride
├── target_node: ValueNode
├── new_value: any
├── options:
│   ├── mark_as_ground: boolean
│   └── rerun_dependents: boolean
└── apply() → updates graph and optionally triggers re-execution
```

#### 6.2 Function Modification
**Purpose**: Modify working interpretation and retry

```
FunctionModification
├── target_node: FunctionNode
├── modifications:
│   ├── paradigm: string | null
│   ├── prompt_template: string | null
│   ├── model: string | null
│   └── parameters: object | null
└── apply() → updates and retries inference
```

#### 6.3 Re-run System
**Purpose**: Selective re-execution from any point

```
RerunController
├── from_node: flow_index
│
├── analyze():
│   ├── nodes_to_reset: flow_index[]
│   ├── nodes_preserved: flow_index[]
│   └── estimated_cost: number
│
└── execute():
    ├── reset affected nodes to pending
    ├── clear affected references
    └── resume execution from earliest ready node
```

---

## Implementation Phases

### Phase 1: Foundation (Graph Display)
**Goal**: Load repositories and display static graph

**Leverage Existing**:
- `graph_service.py` → Graph model building and layout
- `graph_view.py` → Viz.js rendering with pan/zoom (Streamlit)
- `FlowGraphView.tsx` → React SVG rendering with selection (React)
- `get_concept_category()` → Node categorization

**Deliverables**:
- [ ] Adapt existing graph service for unified model
- [ ] Choose rendering approach (Streamlit Viz.js vs React SVG vs React Flow)
- [ ] Integrate existing node styling (semantic-function, semantic-value, syntactic)
- [ ] Add node detail panel (adapt from FlowGraphView info panel)
- [ ] Connect to repository loader (already exists in both apps)

**Acceptance Criteria**:
- Can load any valid repository pair
- Graph displays all concepts and inferences with proper styling
- Can navigate the graph (pan/zoom/select)
- Clicking shows node details

---

### Phase 2: Execution Integration
**Goal**: Execute plans with basic control

**Leverage Existing**:
- `orchestration_runner.py` → Full Orchestrator integration
- `Orchestrator` class → Run, checkpoint, resume, fork
- `LogViewer.tsx` → Log display with auto-scroll
- `log_manager.py` → Structured logging

**Deliverables**:
- [ ] Adapt orchestration_runner for graph-aware execution
- [ ] Add WebSocket/polling for live status updates
- [ ] Integrate existing Run/Pause controls
- [ ] Connect log display to per-node filtering
- [ ] Add progress indicator based on blackboard state

**Acceptance Criteria**:
- Can run a plan from the graph
- Node states update in real-time
- Can pause and resume
- Logs visible during execution

---

### Phase 3: Debugging Features
**Goal**: Full debugging capability

**Leverage Existing**:
- `tensor_display.py` → Multi-dimensional tensor rendering
- `tensor slicing utilities` → Axis selection, N-D viewer
- Existing concept display components

**Deliverables**:
- [ ] Add breakpoint system to Orchestrator (new feature)
- [ ] Implement step/step-over execution modes (new feature)
- [ ] Integrate tensor_display for value node expansion
- [ ] Add function node expansion (sequence pipeline status)
- [ ] Enhance log viewer with per-node filtering

**Acceptance Criteria**:
- Can set breakpoints and execution pauses
- Can step through inference by inference
- Can inspect exact tensor data at any node
- Can see full execution logs per node

---

### Phase 4: Modification & Re-run
**Goal**: Interactive modification and retry

**Leverage Existing**:
- Editable tensor components (already in tensor_display.py)
- Orchestrator checkpoint/resume infrastructure

**Deliverables**:
- [ ] Add value override dialog (extend editable tensor components)
- [ ] Add function modification dialog (paradigm selection)
- [ ] Implement selective re-run (reset node + descendants)
- [ ] Add run comparison/diff view

**Acceptance Criteria**:
- Can inject values and see effects
- Can modify prompts/paradigms and retry
- Can selectively re-run parts of the graph
- Can compare current run with previous

---

### Phase 5: Polish & Advanced Features
**Goal**: Production-ready tool

**Deliverables**:
- [ ] Multiple view modes (bipartite, function-centric, value-centric)
- [ ] Watch expressions
- [ ] Export/import (checkpoints, reports)
- [ ] Keyboard shortcuts
- [ ] Performance optimization for large graphs
- [ ] Theme/styling

**Acceptance Criteria**:
- Handles graphs with 100+ nodes smoothly
- All major workflows possible via keyboard
- Can export audit trails
- Professional UI/UX

---

## Technology Considerations

### Existing Technology Stack

The codebase already uses:

| Layer | Current Technology | Notes |
|-------|-------------------|-------|
| **Streamlit App** | Python + Streamlit | Rapid UI, good for prototyping |
| **Editor App Frontend** | React + TypeScript + Vite | Modern SPA, component-based |
| **Editor App Backend** | FastAPI + Python | REST API, async support |
| **Graph Rendering** | Viz.js (Streamlit), Custom SVG (React) | Both functional |
| **Execution** | Python Orchestrator | Core engine, well-tested |
| **Persistence** | SQLite (checkpoints) | Simple, file-based |

### Build vs. Extend Decision

| Approach | Pros | Cons |
|----------|------|------|
| **Extend Streamlit App** | Fast iteration, Python-only, existing infrastructure | Limited interactivity, no true graph library |
| **Extend React Editor App** | Rich interactivity, component reuse, modern UX | More complex, split Python/JS |
| **New React + React Flow App** | Purpose-built, best graph UX | Restart from scratch, lose existing work |
| **Hybrid: React Flow + FastAPI** | Best graph library + existing backend | Integration work needed |

**Recommendation**: Extend the React Editor App with React Flow for graph rendering, leveraging existing FastAPI backend and Orchestrator integration.

### Specific Technology Choices

| Component | Recommendation | Rationale |
|-----------|---------------|-----------|
| **Graph Library** | React Flow | Purpose-built for node graphs, active maintenance, fits React stack |
| **Layout** | Dagre (via React Flow) | Hierarchical layout matches inference tree structure |
| **State Management** | React hooks + Context | Already used in editor_app, sufficient for this scope |
| **Real-time Updates** | WebSocket | Needed for live execution status; FastAPI supports this |
| **Tensor Display** | Port from Streamlit | `tensor_display.py` logic reusable, needs React components |
| **Logging** | Adapt LogViewer.tsx | Already exists, add filtering |

### Migration Path

1. **Phase 1**: Add React Flow to `editor_app/frontend`, port graph_service
2. **Phase 2**: Add WebSocket endpoint to backend for execution events
3. **Phase 3**: Port tensor_display logic to React components
4. **Phase 4**: Extend Orchestrator with breakpoint/stepping hooks
5. **Phase 5**: Polish and integrate all components

---

## API Design

### REST Endpoints

```
GET  /api/repositories                    # List available repos
POST /api/repositories/load               # Load repo pair
GET  /api/graph                           # Get current graph model
GET  /api/graph/node/{flow_index}         # Get node details
GET  /api/graph/node/{flow_index}/logs    # Get node logs
GET  /api/graph/node/{flow_index}/data    # Get node reference data

POST /api/execution/start                 # Start execution
POST /api/execution/pause                 # Pause
POST /api/execution/resume                # Resume
POST /api/execution/stop                  # Stop
POST /api/execution/step                  # Step one inference
POST /api/execution/run-to/{flow_index}   # Run to specific node
POST /api/execution/rerun-from/{flow_index} # Re-run from node

POST /api/breakpoints                     # Set breakpoint
DELETE /api/breakpoints/{flow_index}      # Clear breakpoint
GET  /api/breakpoints                     # List breakpoints

POST /api/node/{flow_index}/override      # Override value
POST /api/node/{flow_index}/modify        # Modify function
```

### WebSocket Events

```
Server → Client:
  execution:started
  execution:paused
  execution:completed
  execution:error
  inference:started {flow_index}
  inference:completed {flow_index, duration, cost}
  inference:failed {flow_index, error}
  breakpoint:hit {flow_index}
  log:entry {flow_index, level, message}

Client → Server:
  execution:command {action: "run" | "pause" | "step" | ...}
  breakpoint:set {flow_index, type, condition}
  breakpoint:clear {flow_index}
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| **Load time** | < 2s for 100-node graph |
| **Update latency** | < 100ms for state changes |
| **Step execution** | < 500ms UI response |
| **Large graph** | 500+ nodes without lag |
| **Debugging session** | All features work without refresh |

---

## Summary

The NormCode Graph Canvas Tool provides:

1. **Unified Visualization** — One graph, multiple views, always visible
2. **Interactive Exploration** — Expand nodes to see tensors and sequences
3. **Controlled Execution** — Breakpoints, stepping, pause/resume
4. **Deep Inspection** — Logs, references, full context at every step
5. **Live Modification** — Override values, modify functions, re-run selectively
6. **Audit Trail** — Everything visible, exportable, traceable

The tool transforms NormCode from "run and hope" to "observe and control"—making complex AI workflows debuggable, auditable, and understandable.

---

## Next Steps

1. **Validate Architecture** — Review with stakeholders
2. **Prototype Phase 1** — Basic graph display
3. **User Testing** — Validate interaction patterns
4. **Iterate** — Refine based on feedback
5. **Production Build** — Full implementation

---

**Document Version**: 1.0  
**Date**: December 2024  
**Status**: Draft - High Level Plan
