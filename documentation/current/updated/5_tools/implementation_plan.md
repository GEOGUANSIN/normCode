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
| **Human-in-the-Loop Tool** | `tools/user_input_tool.py` | Threading-based blocking for user input during execution |
| **Results Display** | `tabs/results/` | Concept result visualization, tensor reuse |
| **Log Management** | `core/log_manager.py` | Structured logging infrastructure |
| **File Utilities** | `core/file_utils.py` | Repository file saving, path management |

**Key features already implemented**:
- Graphviz DOT generation with node categorization (semantic-function, semantic-value, syntactic-function)
- Interactive SVG with svg-pan-zoom library
- Tensor slicing for high-dimensional data
- Orchestrator checkpoint/resume/fork support
- Human-in-the-loop tool injection

#### Specific Implementation Details to Reuse:

**Graph with Viz.js** (`graph_view.py`):
- Uses `@viz-js/viz@3.2.4` + `svg-pan-zoom@3.6.1` (CDN loaded)
- DOT format with proper escaping
- Controls: Zoom in/out, reset, fit to view, download SVG
- No server-side Graphviz needed

**Node Styling for Ground/Final** (`graph_view.py`):
```python
# Ground concepts: double outline
shape = 'doublecircle' if category == 'semantic-function' else 'doubleoctagon'
# Final concepts: bold red border
border = '#e11d48'
style = 'bold'
```

**Tensor Utilities** (`utils.py`):
```python
def get_tensor_shape(data) -> Tuple[int, ...]:
    # Recursive shape calculation for nested lists
    
def slice_tensor(data, display_axes, slice_indices, total_dims) -> Any:
    # Extract 2D slice from N-D tensor
    
def format_cell_value(value, html=True) -> str:
    # Handles %(...)  perceptual sign syntax
```

**N-D Tensor Interactive Slicer** (`tensor_display.py`):
- Row/column axis selector dropdowns
- Sliders for non-displayed dimensions
- View modes: Table, List, JSON
- Real-time slice description

**Orchestration Modes** (`orchestration_runner.py`):
```python
# Fresh Run: New orchestrator with optional custom run_id
orchestrator = await asyncio.to_thread(Orchestrator, concept_repo, inference_repo, body, ...)

# Fork: Load checkpoint with new run_id
orchestrator = await asyncio.to_thread(Orchestrator.load_checkpoint, ..., new_run_id=fork_new_run_id)

# Resume: Continue existing run
orchestrator = await asyncio.to_thread(Orchestrator.load_checkpoint, ..., mode=reconciliation_mode)
```

**Human-in-the-Loop Pattern** (`user_input_tool.py`):
```python
# Worker thread blocks on threading.Event
st.session_state.user_input_request = {"id": request_id, "prompt": ..., "type": ...}
st.session_state.user_input_event.clear()
event.wait()  # Worker blocks here

# UI detects request, shows form, user submits
st.session_state.user_input_response = {"id": request_id, "answer": user_answer}
st.session_state.user_input_event.set()  # Unblocks worker
```

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

#### Specific Implementation Details to Reuse:

**Node Categorization** (`FlowGraphView.tsx`):
```typescript
// Semantic functions: ::({}) and <{}>
if (label.includes(':(') || label.includes(':<')) return 'semantic-function';
// Semantic values: {}, <>, []
if (label.startsWith('{') || label.startsWith('<') || label.startsWith('[')) return 'semantic-value';
// Syntactic functions: everything else
return 'syntactic-function';
```

**Node ID Format** (`graph_service.py`):
```python
node_id = f"{concept_name}@{level}"  # Allows same concept at multiple levels
```

**Level Calculation**:
```python
level = len(flow_index_tuple) - 1  # Based on flow_index depth
```

**Color Scheme** (from CSS):
| Category | Fill | Stroke |
|----------|------|--------|
| `semantic-function` | `#ede7f6` (light purple) | `#7b68ee` |
| `semantic-value` | `#dbeafe` (light blue) | `#3b82f6` |
| `syntactic-function` | `#f1f5f9` (light slate) | `#64748b` |

**Edge Types**:
- Function (`<=`): Blue `#4a90e2`
- Value (`<-`): Purple `#7b68ee`

**Layout Spacing**:
```python
horizontal_spacing = 250  # Between levels
vertical_spacing = 100    # Between nodes in same level
```

**Log Polling** (`useRepositoryRunner.ts`):
- Polls log file every 1 second
- Detects completion via markers: `"--- Normcode Execution Completed ---"` or `"--- Normcode Execution Failed ---"`
- **Upgrade path**: Replace with WebSocket for real-time updates

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
**Purpose**: Compute node positions based on tree structure

**Layout**: Tree (bottom-up) using hierarchical layout (Dagre/Sugiyama)
- Matches NormCode reading direction (dependencies at bottom, goal at top)
- Root concept at top, ground concepts at bottom
- Siblings arranged horizontally by flow index order

> **Future**: Additional layouts (force-directed, timeline) can be added later if needed.

#### 2.2 Graph Renderer
**Purpose**: Render nodes, edges, and state to canvas

**Node Rendering (Unexpanded - Default)**:
Keep nodes simple until selected. Show only essential identity + status.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  VALUE NODE (unexpanded)             FUNCTION NODE (unexpanded)         │
│  ┌─────────────────────┐            ◇───────────────────◇              │
│  │ {concept_name}  [●] │            ╱ ::(function_name) ╲              │
│  └─────────────────────┘            ◇───────────────────◇              │
│                                                                         │
│  [●] = status indicator (color: gray/blue/green/red)                   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Node Rendering (Expanded - On Selection)**:
Only the selected node(s) show full detail. Expansion reveals:
- Value nodes: axes, shape, data preview
- Function nodes: sequence type, paradigm, pipeline status

> **Rationale**: Keeping unexpanded nodes minimal reduces visual clutter and improves performance for large graphs. Detail is shown on-demand via selection.

**State Visualization**:

> **Note**: Base node colors (from existing implementation) indicate **category**:
> - Semantic values: blue (`#dbeafe` / `#3b82f6`)
> - Semantic functions: purple (`#ede7f6` / `#7b68ee`)
> - Syntactic functions: gray (`#f1f5f9` / `#64748b`)
>
> Execution **state** is shown via status indicator or border overlay:

| State | Indicator | Visual Treatment |
|-------|-----------|------------------|
| Pending | Gray dot `●` | Normal node styling |
| Running | Blue pulse `◉` | Pulsing border animation |
| Complete | Green dot `●` | Green border/glow |
| Failed | Red dot `●` | Red border, error icon |
| Skipped | Striped `◌` | Dimmed with strikethrough |
| Breakpoint | Red dot on edge | Small red circle indicator |
| Paused at | Yellow border | Yellow highlight |

**Selection Behavior** (from existing implementation):
- Selected node: Highlighted with thicker border
- Related nodes/edges: Normal visibility
- Unrelated nodes/edges: Dimmed (`opacity: 0.3`)

#### 2.3 View Modes
**Purpose**: Different ways to interpret the same graph

**Initial Implementation**: Bipartite view only
- Both Value Nodes and Function Nodes visible
- Matches the natural NormCode structure (`<- value` ← `<= function`)
- Clear visualization of inference boundaries

> **Future**: Alternative views (function-centric, value-centric) can be added if users need different perspectives on the same graph.

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
- `editor_app/backend/services/graph_service.py` → Graph model building, layout algorithm
- `editor_app/frontend/src/components/FlowGraphView.tsx` → React SVG rendering, selection, info panel
- `editor_app/frontend/src/components/FlowGraphView.css` → Color scheme, styling

**Key Patterns to Preserve**:
```python
# Node ID format (allows same concept at multiple levels)
node_id = f"{concept_name}@{level}"

# Level from flow_index
level = len(flow_index_tuple) - 1

# Layout
horizontal_spacing = 250
vertical_spacing = 100
```

**Deliverables**:
- [ ] Port `GraphService.compute_graph_from_flow()` to new context
- [ ] Port `getNodeCategory()` logic for node coloring
- [ ] Use React Flow instead of raw SVG (better pan/zoom/interaction)
- [ ] Preserve existing color scheme (purple/blue/gray)
- [ ] Adapt info panel pattern (incoming/outgoing connections)
- [ ] Add dimming behavior (`opacity: 0.3` for unrelated nodes)

**Acceptance Criteria**:
- Can load any valid `.concept.json` + `.inference.json` pair
- Graph displays with tree layout (bottom-up, root at top)
- Node colors match category (semantic-function, semantic-value, syntactic)
- Click node → info panel shows connections
- Unrelated nodes dim when one is selected

---

### Phase 2: Execution Integration
**Goal**: Execute plans with basic control

**Leverage Existing**:
- `editor_app/backend/services/normcode_execution_service.py` → Background thread execution
- `editor_app/frontend/src/hooks/useRepositoryRunner.ts` → Polling pattern
- `editor_app/frontend/src/components/LogViewer.tsx` → Auto-scroll log display
- `streamlit_app/orchestration/orchestration_runner.py` → Full Orchestrator integration

**Current Pattern** (file-based polling):
```typescript
// Polls every 1 second, detects completion via string markers
const pollInterval = setInterval(async () => {
  const content = await apiService.getLogContent(logFile);
  if (content.includes('--- Normcode Execution Completed ---')) {
    clearInterval(pollInterval);
  }
}, 1000);
```

**Upgrade to WebSocket**:
```
Server → Client events:
  inference:started {flow_index}
  inference:completed {flow_index, result}
  log:entry {flow_index, level, message}
```

**Deliverables**:
- [ ] Add WebSocket endpoint to FastAPI backend
- [ ] Hook Orchestrator to emit events on inference start/complete
- [ ] Update graph nodes in real-time based on WebSocket events
- [ ] Port `LogViewer.tsx` with per-node filtering
- [ ] Add progress bar based on completed/total inferences

**Acceptance Criteria**:
- Click "Run" → execution starts
- Nodes change color in real-time (pending → running → complete)
- Logs stream in real-time (no 1-second polling delay)
- Progress bar shows completed/total
- Can pause and resume execution

---

### Phase 3: Debugging Features
**Goal**: Full debugging capability

**Leverage Existing**:
- `streamlit_app/tabs/execute/preview/tensor_display.py` → Multi-dimensional tensor rendering
- `streamlit_app/tabs/execute/preview/utils.py` → Shape calculation, slicing, formatting
- `streamlit_app/tools/user_input_tool.py` → Human-in-the-loop pattern (for breakpoint interaction)

**Key Tensor Display Features to Port**:
```python
# From tensor_display.py - supports 0D to N-D
def render_tensor_display(concept_name, data, axes, source, is_invariant, editable):
    shape = get_tensor_shape(data)
    dims = len(shape)
    
    if dims == 0: render_scalar_value(data)
    elif dims == 1: render_1d_tensor(data, axes[0])
    elif dims == 2: render_2d_tensor(data, axes)
    else: render_interactive_tensor_viewer(data, axes, shape, viewer_key)

# N-D slicer with axis selection
def render_interactive_tensor_viewer(data, axes, shape, viewer_key):
    # Row axis selector, Column axis selector
    # Sliders for non-displayed axes
    # View modes: Table, List, JSON
```

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

## Technology Stack (Option C: New Standalone App)

### Decision: New Standalone React + FastAPI Application

**Rationale**: The existing `editor_app` and `streamlit_app` have divergent architectures. A new standalone app provides:
- Clean architecture purpose-built for graph debugging
- No legacy constraints or workarounds
- Can selectively port proven patterns from existing apps
- Clear separation of concerns

### Recommended Stack

```
┌─────────────────────────────────────────────────────────────────────┐
│  FRONTEND                                                            │
│  ─────────                                                          │
│  React 18 + TypeScript + Vite                                       │
│  React Flow (graph visualization)                                   │
│  TailwindCSS (styling)                                              │
│  Zustand (state management)                                         │
│  TanStack Query (server state)                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ REST + WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  BACKEND                                                             │
│  ───────                                                            │
│  FastAPI (REST + WebSocket)                                         │
│  Python 3.11+                                                       │
│  Existing Orchestrator (infra/)                                     │
│  SQLite (checkpoints, via existing OrchestratorDB)                 │
└─────────────────────────────────────────────────────────────────────┘
```

### Frontend Dependencies

```json
{
  "name": "normcode-canvas",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "reactflow": "^11.10.0",
    "zustand": "^4.4.7",
    "@tanstack/react-query": "^5.17.0",
    "lucide-react": "^0.303.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0"
  }
}
```

### Backend Dependencies

```
# requirements.txt
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
websockets>=12.0
pydantic>=2.5.0
python-multipart>=0.0.6

# Already available from project root:
# infra (Orchestrator, ConceptRepo, InferenceRepo, etc.)
```

### Project Structure

```
canvas_app/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── repository_router.py   # Load .concept.json + .inference.json
│   │   ├── graph_router.py        # Graph data endpoints
│   │   ├── execution_router.py    # Run/pause/step/stop
│   │   └── websocket_router.py    # Real-time events
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── graph_service.py       # Build graph model from repos
│   │   ├── execution_service.py   # Orchestrator wrapper with events
│   │   └── tensor_service.py      # Tensor shape/slice utilities
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── graph_schemas.py       # GraphNode, GraphEdge, etc.
│   │   ├── execution_schemas.py   # RunRequest, StepRequest, etc.
│   │   └── websocket_schemas.py   # Event message types
│   │
│   └── core/
│       ├── __init__.py
│       ├── config.py              # App configuration
│       └── events.py              # Event emitter for WebSocket
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   │
│   ├── src/
│   │   ├── main.tsx              # Entry point
│   │   ├── App.tsx               # Main app with layout
│   │   │
│   │   ├── components/
│   │   │   ├── graph/
│   │   │   │   ├── GraphCanvas.tsx       # React Flow canvas
│   │   │   │   ├── ValueNode.tsx         # Custom value node
│   │   │   │   ├── FunctionNode.tsx      # Custom function node
│   │   │   │   └── CustomEdge.tsx        # Custom edge styling
│   │   │   │
│   │   │   ├── panels/
│   │   │   │   ├── ControlPanel.tsx      # Run/pause/step controls
│   │   │   │   ├── DetailPanel.tsx       # Selected node details
│   │   │   │   ├── LogPanel.tsx          # Execution logs
│   │   │   │   └── TensorInspector.tsx   # N-D tensor viewer
│   │   │   │
│   │   │   └── common/
│   │   │       ├── Button.tsx
│   │   │       ├── Badge.tsx
│   │   │       └── Slider.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useGraph.ts           # Graph data fetching
│   │   │   ├── useExecution.ts       # Execution control
│   │   │   ├── useWebSocket.ts       # WebSocket connection
│   │   │   └── useTensorSlice.ts     # Tensor slicing state
│   │   │
│   │   ├── stores/
│   │   │   ├── graphStore.ts         # Graph nodes/edges state
│   │   │   ├── executionStore.ts     # Execution state
│   │   │   └── selectionStore.ts     # Selected node/edge
│   │   │
│   │   ├── services/
│   │   │   ├── api.ts                # REST API client
│   │   │   └── websocket.ts          # WebSocket client
│   │   │
│   │   ├── types/
│   │   │   ├── graph.ts              # GraphNode, GraphEdge types
│   │   │   ├── execution.ts          # ExecutionState, Breakpoint
│   │   │   └── tensor.ts             # TensorData, TensorShape
│   │   │
│   │   └── utils/
│   │       ├── tensorUtils.ts        # Shape, slice, format
│   │       ├── graphLayout.ts        # Layout helpers
│   │       └── categoryUtils.ts      # Node categorization
│   │
│   └── public/
│       └── favicon.svg
│
├── launch.py                      # Combined launcher
├── launch.ps1                     # PowerShell launcher
├── launch.bat                     # Windows batch launcher
└── README.md
```

### Key Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Graph Library** | React Flow | Best-in-class for node graphs, built-in pan/zoom/minimap, custom nodes |
| **State Management** | Zustand | Simpler than Redux, great TypeScript support, works with React Flow |
| **Server State** | TanStack Query | Handles caching, refetching, loading states automatically |
| **Styling** | TailwindCSS | Rapid development, consistent with design system |
| **Icons** | Lucide React | Lightweight, tree-shakeable, consistent style |
| **Backend** | FastAPI | Async support, WebSocket built-in, auto OpenAPI docs |
| **Real-time** | WebSocket | Bidirectional, low latency for execution events |
| **Layout** | Dagre (via reactflow) | Hierarchical layout matches inference tree structure |

---

## Implementation Details

### Backend: FastAPI Application

#### Main Entry Point (`backend/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import repository_router, graph_router, execution_router, websocket_router

app = FastAPI(
    title="NormCode Canvas API",
    version="0.1.0",
    description="Backend for NormCode Graph Canvas Tool"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repository_router.router, prefix="/api/repositories", tags=["repositories"])
app.include_router(graph_router.router, prefix="/api/graph", tags=["graph"])
app.include_router(execution_router.router, prefix="/api/execution", tags=["execution"])
app.include_router(websocket_router.router, prefix="/ws", tags=["websocket"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

#### Graph Service (`backend/services/graph_service.py`)

```python
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class GraphNode(BaseModel):
    id: str                     # f"{concept_name}@{level}"
    label: str                  # Concept name
    category: str               # "semantic-function" | "semantic-value" | "syntactic-function"
    node_type: str              # "value" | "function"
    flow_index: Optional[str]
    level: int
    position: Dict[str, float]  # {x, y}
    data: Dict[str, Any]        # Additional data for expansion

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    edge_type: str              # "function" | "value"
    label: Optional[str]        # Inference sequence
    flow_index: str

class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

def get_concept_category(concept_name: str) -> str:
    """Categorize concept by name pattern."""
    if ':(' in concept_name or ':<' in concept_name:
        return "semantic-function"
    elif ((concept_name.startswith('{') and concept_name.rstrip('?').endswith('}')) or 
          (concept_name.startswith('<') and concept_name.endswith('>')) or 
          (concept_name.startswith('[') and concept_name.endswith(']'))):
        return "semantic-value"
    else:
        return "syntactic-function"

def build_graph_from_repositories(
    concepts_data: List[Dict[str, Any]],
    inferences_data: List[Dict[str, Any]]
) -> GraphData:
    """Build graph model from concept and inference repositories."""
    nodes: Dict[str, GraphNode] = {}
    edges: List[GraphEdge] = []
    
    # Build concept lookup
    concept_attrs = {c['concept_name']: c for c in concepts_data}
    
    for inf in inferences_data:
        flow_info = inf.get('flow_info', {})
        flow_index = flow_info.get('flow_index', '0')
        level = len(flow_index.split('.')) - 1
        
        target_name = inf.get('concept_to_infer', '')
        func_name = inf.get('function_concept', '')
        value_names = inf.get('value_concepts', [])
        sequence = inf.get('inference_sequence', '')
        
        # Create target node (value)
        target_id = f"{target_name}@{level}"
        if target_id not in nodes:
            attrs = concept_attrs.get(target_name, {})
            nodes[target_id] = GraphNode(
                id=target_id,
                label=target_name,
                category=get_concept_category(target_name),
                node_type="value",
                flow_index=flow_index,
                level=level,
                position={"x": 0, "y": 0},  # Calculated by layout
                data={
                    "is_ground": attrs.get('is_ground_concept', False),
                    "is_final": attrs.get('is_final_concept', False),
                    "axes": attrs.get('reference_axis_names', []),
                }
            )
        
        input_level = level + 1
        
        # Create function node
        if func_name:
            func_id = f"{func_name}@{input_level}"
            if func_id not in nodes:
                nodes[func_id] = GraphNode(
                    id=func_id,
                    label=func_name,
                    category=get_concept_category(func_name),
                    node_type="function",
                    flow_index=flow_index,
                    level=input_level,
                    position={"x": 0, "y": 0},
                    data={"sequence": sequence}
                )
            edges.append(GraphEdge(
                id=f"edge-func-{flow_index}",
                source=func_id,
                target=target_id,
                edge_type="function",
                label=sequence,
                flow_index=flow_index
            ))
        
        # Create value input nodes
        for idx, val_name in enumerate(value_names):
            val_id = f"{val_name}@{input_level}"
            if val_id not in nodes:
                val_attrs = concept_attrs.get(val_name, {})
                nodes[val_id] = GraphNode(
                    id=val_id,
                    label=val_name,
                    category=get_concept_category(val_name),
                    node_type="value",
                    flow_index=None,
                    level=input_level,
                    position={"x": 0, "y": 0},
                    data={
                        "is_ground": val_attrs.get('is_ground_concept', False),
                        "axes": val_attrs.get('reference_axis_names', []),
                    }
                )
            edges.append(GraphEdge(
                id=f"edge-val-{flow_index}-{idx}",
                source=val_id,
                target=target_id,
                edge_type="value",
                label=None,
                flow_index=flow_index
            ))
    
    # Calculate positions using level-based layout
    node_list = list(nodes.values())
    _calculate_positions(node_list)
    
    return GraphData(nodes=node_list, edges=edges)

def _calculate_positions(nodes: List[GraphNode], h_spacing: int = 250, v_spacing: int = 100):
    """Calculate x, y positions using level-based layout."""
    level_groups: Dict[int, List[GraphNode]] = {}
    for node in nodes:
        if node.level not in level_groups:
            level_groups[node.level] = []
        level_groups[node.level].append(node)
    
    for level, level_nodes in level_groups.items():
        for idx, node in enumerate(level_nodes):
            node.position = {
                "x": level * h_spacing,
                "y": idx * v_spacing
            }
```

#### Execution Service (`backend/services/execution_service.py`)

```python
import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from enum import Enum
from dataclasses import dataclass, field

from infra import ConceptRepo, InferenceRepo, Orchestrator
from infra._agent._body import Body

logger = logging.getLogger(__name__)

class ExecutionState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ExecutionController:
    """Controls orchestrator execution with debugging support."""
    
    orchestrator: Optional[Orchestrator] = None
    state: ExecutionState = ExecutionState.IDLE
    breakpoints: set = field(default_factory=set)
    current_inference: Optional[str] = None
    event_callback: Optional[Callable] = None
    
    _pause_event: asyncio.Event = field(default_factory=asyncio.Event)
    _step_event: asyncio.Event = field(default_factory=asyncio.Event)
    
    async def load_repositories(
        self,
        concepts_path: str,
        inferences_path: str,
        inputs_path: Optional[str] = None,
        llm_model: str = "demo",
        base_dir: str = "."
    ):
        """Load repositories and create orchestrator."""
        import json
        
        with open(concepts_path) as f:
            concepts_data = json.load(f)
        with open(inferences_path) as f:
            inferences_data = json.load(f)
        
        concept_repo = ConceptRepo.from_json(concepts_data)
        inference_repo = InferenceRepo.from_json(inferences_data)
        
        if inputs_path:
            with open(inputs_path) as f:
                inputs_data = json.load(f)
            for name, value in inputs_data.items():
                if isinstance(value, dict) and 'data' in value:
                    concept_repo.add_reference(name, value['data'], axis_names=value.get('axes'))
                else:
                    concept_repo.add_reference(name, value)
        
        body = Body(llm_name=llm_model, base_dir=base_dir)
        
        self.orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            body=body,
            max_cycles=100
        )
        
        self._emit("execution:loaded", {"run_id": self.orchestrator.run_id})
    
    async def start(self):
        """Start or resume execution."""
        if self.state == ExecutionState.PAUSED:
            await self.resume()
        else:
            self.state = ExecutionState.RUNNING
            self._pause_event.set()
            self._emit("execution:started", {})
            await self._run_loop()
    
    async def pause(self):
        """Pause execution after current inference."""
        self.state = ExecutionState.PAUSED
        self._pause_event.clear()
        self._emit("execution:paused", {"inference": self.current_inference})
    
    async def resume(self):
        """Resume from paused state."""
        self.state = ExecutionState.RUNNING
        self._pause_event.set()
        self._emit("execution:resumed", {})
    
    async def step(self):
        """Execute single inference then pause."""
        self.state = ExecutionState.STEPPING
        self._step_event.set()
        self._emit("execution:stepping", {})
    
    async def stop(self):
        """Stop execution."""
        self.state = ExecutionState.IDLE
        self._pause_event.set()
        self._step_event.set()
        self._emit("execution:stopped", {})
    
    def set_breakpoint(self, flow_index: str):
        """Add breakpoint at flow_index."""
        self.breakpoints.add(flow_index)
        self._emit("breakpoint:set", {"flow_index": flow_index})
    
    def clear_breakpoint(self, flow_index: str):
        """Remove breakpoint."""
        self.breakpoints.discard(flow_index)
        self._emit("breakpoint:cleared", {"flow_index": flow_index})
    
    async def _run_loop(self):
        """Main execution loop with breakpoint/stepping support."""
        try:
            while self.state in (ExecutionState.RUNNING, ExecutionState.STEPPING):
                # Check if paused
                if self.state == ExecutionState.PAUSED:
                    await self._pause_event.wait()
                
                # Get next ready inference
                next_inference = self.orchestrator._get_next_ready_inference()
                if next_inference is None:
                    break
                
                flow_index = next_inference.flow_info.get('flow_index', '')
                self.current_inference = flow_index
                
                # Check breakpoint
                if flow_index in self.breakpoints:
                    self.state = ExecutionState.PAUSED
                    self._emit("breakpoint:hit", {"flow_index": flow_index})
                    await self._pause_event.wait()
                
                # Emit start event
                self._emit("inference:started", {"flow_index": flow_index})
                
                # Execute inference
                try:
                    await asyncio.to_thread(self.orchestrator._execute_inference, next_inference)
                    self._emit("inference:completed", {"flow_index": flow_index})
                except Exception as e:
                    self._emit("inference:failed", {"flow_index": flow_index, "error": str(e)})
                    raise
                
                # If stepping, pause after this inference
                if self.state == ExecutionState.STEPPING:
                    self.state = ExecutionState.PAUSED
                    self._emit("execution:paused", {"inference": flow_index})
                    await self._pause_event.wait()
            
            self.state = ExecutionState.COMPLETED
            self._emit("execution:completed", {})
            
        except Exception as e:
            self.state = ExecutionState.FAILED
            self._emit("execution:error", {"error": str(e)})
            logger.exception("Execution failed")
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit event to callback."""
        if self.event_callback:
            self.event_callback(event_type, data)
```

#### WebSocket Router (`backend/routers/websocket_router.py`)

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Active WebSocket connections
active_connections: Set[WebSocket] = set()

@router.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time execution events."""
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket connected. Total: {len(active_connections)}")
    
    try:
        while True:
            # Receive commands from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            event_type = message.get("type")
            payload = message.get("payload", {})
            
            # Handle client commands
            if event_type == "execution:command":
                await handle_execution_command(payload)
            elif event_type == "breakpoint:set":
                await handle_breakpoint_set(payload)
            elif event_type == "breakpoint:clear":
                await handle_breakpoint_clear(payload)
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(active_connections)}")

async def broadcast_event(event_type: str, data: Dict):
    """Broadcast event to all connected clients."""
    message = json.dumps({"type": event_type, "data": data})
    disconnected = set()
    
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except:
            disconnected.add(connection)
    
    active_connections.difference_update(disconnected)
```

---

### Frontend: React Application

#### Custom Value Node (`frontend/src/components/graph/ValueNode.tsx`)

```tsx
import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { useExecutionStore } from '../../stores/executionStore';

interface ValueNodeData {
  label: string;
  category: 'semantic-value' | 'syntactic-function';
  isGround?: boolean;
  isFinal?: boolean;
  axes?: string[];
}

const categoryStyles = {
  'semantic-value': {
    bg: 'bg-blue-50',
    border: 'border-blue-400',
    text: 'text-blue-900',
  },
  'syntactic-function': {
    bg: 'bg-slate-50',
    border: 'border-slate-400',
    text: 'text-slate-900',
  },
};

const statusStyles = {
  pending: 'opacity-50',
  running: 'ring-2 ring-blue-500 animate-pulse',
  completed: 'ring-2 ring-green-500',
  failed: 'ring-2 ring-red-500',
  skipped: 'opacity-30 line-through',
};

export const ValueNode = memo(({ data, id, selected }: NodeProps<ValueNodeData>) => {
  const status = useExecutionStore((s) => s.nodeStatus[id] || 'pending');
  const style = categoryStyles[data.category] || categoryStyles['semantic-value'];
  
  return (
    <div
      className={`
        px-4 py-2 rounded-lg border-2 min-w-[120px]
        ${style.bg} ${style.border} ${style.text}
        ${statusStyles[status]}
        ${selected ? 'ring-2 ring-offset-2 ring-indigo-500' : ''}
        ${data.isGround ? 'border-double border-4' : ''}
        ${data.isFinal ? 'border-red-500 border-2' : ''}
      `}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      
      <div className="text-center">
        <div className="font-mono text-sm truncate max-w-[150px]" title={data.label}>
          {data.label}
        </div>
        {data.axes && data.axes.length > 0 && (
          <div className="text-xs opacity-60 mt-1">
            [{data.axes.join(', ')}]
          </div>
        )}
      </div>
      
      {/* Status indicator dot */}
      <div className={`
        absolute -top-1 -right-1 w-3 h-3 rounded-full
        ${status === 'pending' ? 'bg-gray-400' : ''}
        ${status === 'running' ? 'bg-blue-500 animate-pulse' : ''}
        ${status === 'completed' ? 'bg-green-500' : ''}
        ${status === 'failed' ? 'bg-red-500' : ''}
      `} />
      
      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
});

ValueNode.displayName = 'ValueNode';
```

#### Custom Function Node (`frontend/src/components/graph/FunctionNode.tsx`)

```tsx
import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { useExecutionStore } from '../../stores/executionStore';

interface FunctionNodeData {
  label: string;
  category: 'semantic-function' | 'syntactic-function';
  sequence?: string;
}

const categoryStyles = {
  'semantic-function': {
    bg: 'bg-purple-50',
    border: 'border-purple-400',
    text: 'text-purple-900',
  },
  'syntactic-function': {
    bg: 'bg-slate-50',
    border: 'border-slate-400',
    text: 'text-slate-900',
  },
};

export const FunctionNode = memo(({ data, id, selected }: NodeProps<FunctionNodeData>) => {
  const status = useExecutionStore((s) => s.nodeStatus[id] || 'pending');
  const style = categoryStyles[data.category] || categoryStyles['semantic-function'];
  
  return (
    <div
      className={`
        px-4 py-2 min-w-[100px]
        ${style.bg} ${style.border} ${style.text}
        ${selected ? 'ring-2 ring-offset-2 ring-indigo-500' : ''}
        border-2 transform rotate-45
      `}
      style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      
      <div className="transform -rotate-45 text-center p-2">
        <div className="font-mono text-xs truncate max-w-[100px]" title={data.label}>
          {data.label}
        </div>
        {data.sequence && (
          <div className="text-xs opacity-60 mt-1">
            {data.sequence}
          </div>
        )}
      </div>
      
      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
});

FunctionNode.displayName = 'FunctionNode';
```

#### Graph Canvas (`frontend/src/components/graph/GraphCanvas.tsx`)

```tsx
import { useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  OnConnect,
  NodeTypes,
  EdgeTypes,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { ValueNode } from './ValueNode';
import { FunctionNode } from './FunctionNode';
import { CustomEdge } from './CustomEdge';
import { useGraphStore } from '../../stores/graphStore';
import { useSelectionStore } from '../../stores/selectionStore';

const nodeTypes: NodeTypes = {
  value: ValueNode,
  function: FunctionNode,
};

const edgeTypes: EdgeTypes = {
  custom: CustomEdge,
};

export function GraphCanvas() {
  const graphData = useGraphStore((s) => s.graphData);
  const setSelectedNode = useSelectionStore((s) => s.setSelectedNode);
  
  const nodes = useMemo(() => {
    if (!graphData) return [];
    return graphData.nodes.map((n) => ({
      id: n.id,
      type: n.node_type === 'value' ? 'value' : 'function',
      position: n.position,
      data: {
        label: n.label,
        category: n.category,
        ...n.data,
      },
    }));
  }, [graphData]);
  
  const edges = useMemo(() => {
    if (!graphData) return [];
    return graphData.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      type: 'custom',
      data: {
        edgeType: e.edge_type,
        label: e.label,
      },
    }));
  }, [graphData]);
  
  const [flowNodes, setNodes, onNodesChange] = useNodesState(nodes);
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState(edges);
  
  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node.id);
  }, [setSelectedNode]);
  
  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        minZoom={0.1}
        maxZoom={2}
      >
        <Background color="#e2e8f0" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            switch (node.data?.category) {
              case 'semantic-function': return '#c084fc';
              case 'semantic-value': return '#60a5fa';
              default: return '#94a3b8';
            }
          }}
        />
      </ReactFlow>
    </div>
  );
}
```

#### Execution Store (`frontend/src/stores/executionStore.ts`)

```ts
import { create } from 'zustand';

type NodeStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

interface ExecutionState {
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed';
  nodeStatus: Record<string, NodeStatus>;
  breakpoints: Set<string>;
  logs: Array<{ flowIndex: string; level: string; message: string; timestamp: Date }>;
  
  // Actions
  setStatus: (status: ExecutionState['status']) => void;
  setNodeStatus: (nodeId: string, status: NodeStatus) => void;
  addBreakpoint: (flowIndex: string) => void;
  removeBreakpoint: (flowIndex: string) => void;
  addLog: (log: ExecutionState['logs'][0]) => void;
  reset: () => void;
}

export const useExecutionStore = create<ExecutionState>((set) => ({
  status: 'idle',
  nodeStatus: {},
  breakpoints: new Set(),
  logs: [],
  
  setStatus: (status) => set({ status }),
  
  setNodeStatus: (nodeId, status) =>
    set((state) => ({
      nodeStatus: { ...state.nodeStatus, [nodeId]: status },
    })),
  
  addBreakpoint: (flowIndex) =>
    set((state) => ({
      breakpoints: new Set([...state.breakpoints, flowIndex]),
    })),
  
  removeBreakpoint: (flowIndex) =>
    set((state) => {
      const newBreakpoints = new Set(state.breakpoints);
      newBreakpoints.delete(flowIndex);
      return { breakpoints: newBreakpoints };
    }),
  
  addLog: (log) =>
    set((state) => ({
      logs: [...state.logs, log],
    })),
  
  reset: () =>
    set({
      status: 'idle',
      nodeStatus: {},
      logs: [],
    }),
}));
```

#### WebSocket Hook (`frontend/src/hooks/useWebSocket.ts`)

```ts
import { useEffect, useRef, useCallback } from 'react';
import { useExecutionStore } from '../stores/executionStore';

export function useWebSocket(url: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const setStatus = useExecutionStore((s) => s.setStatus);
  const setNodeStatus = useExecutionStore((s) => s.setNodeStatus);
  const addLog = useExecutionStore((s) => s.addLog);
  
  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;
    
    ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      const { type, data } = JSON.parse(event.data);
      
      switch (type) {
        case 'execution:started':
          setStatus('running');
          break;
        case 'execution:paused':
          setStatus('paused');
          break;
        case 'execution:completed':
          setStatus('completed');
          break;
        case 'execution:error':
          setStatus('failed');
          break;
        case 'inference:started':
          setNodeStatus(data.flow_index, 'running');
          break;
        case 'inference:completed':
          setNodeStatus(data.flow_index, 'completed');
          break;
        case 'inference:failed':
          setNodeStatus(data.flow_index, 'failed');
          break;
        case 'log:entry':
          addLog({
            flowIndex: data.flow_index,
            level: data.level,
            message: data.message,
            timestamp: new Date(),
          });
          break;
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
    
    return () => {
      ws.close();
    };
  }, [url, setStatus, setNodeStatus, addLog]);
  
  const send = useCallback((type: string, payload: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, payload }));
    }
  }, []);
  
  return { send };
}
```

---

## API Design

### REST Endpoints

```
GET  /api/repositories                    # List available repos
POST /api/repositories/load               # Load repo pair
GET  /api/graph                           # Get current graph model
GET  /api/graph/node/{node_id}            # Get node details
GET  /api/graph/node/{node_id}/data       # Get node reference data

POST /api/execution/start                 # Start execution
POST /api/execution/pause                 # Pause
POST /api/execution/resume                # Resume
POST /api/execution/stop                  # Stop
POST /api/execution/step                  # Step one inference
POST /api/execution/run-to/{flow_index}   # Run to specific node

POST /api/breakpoints                     # Set breakpoint
DELETE /api/breakpoints/{flow_index}      # Clear breakpoint
GET  /api/breakpoints                     # List breakpoints

POST /api/node/{node_id}/override         # Override value
```

### WebSocket Events

```
Server → Client:
  execution:started
  execution:paused
  execution:completed
  execution:error
  inference:started {flow_index, node_id}
  inference:completed {flow_index, node_id, duration}
  inference:failed {flow_index, node_id, error}
  breakpoint:hit {flow_index}
  log:entry {flow_index, level, message}

Client → Server:
  execution:command {action: "start" | "pause" | "step" | "stop"}
  breakpoint:set {flow_index}
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

## Getting Started (Quick Setup)

### 1. Create Project Structure

```powershell
# From normCode project root
mkdir canvas_app
mkdir canvas_app/backend
mkdir canvas_app/frontend

# Backend setup
cd canvas_app/backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install fastapi uvicorn[standard] websockets pydantic

# Frontend setup  
cd ../frontend
npm create vite@latest . -- --template react-ts
npm install reactflow zustand @tanstack/react-query lucide-react
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 2. Run Development Servers

```powershell
# Terminal 1: Backend
cd canvas_app/backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd canvas_app/frontend
npm run dev
```

### 3. Access the App

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs (Swagger UI)
- WebSocket: ws://localhost:8000/ws/events

---

## Next Steps

1. **Phase 1 (Week 1-2)**: Basic graph display
   - [ ] Create backend project structure
   - [ ] Implement `graph_service.py` with `build_graph_from_repositories()`
   - [ ] Create React Flow canvas with custom nodes
   - [ ] Test with sample `.concept.json` + `.inference.json`

2. **Phase 2 (Week 3-4)**: Execution integration
   - [ ] Implement `execution_service.py` with Orchestrator wrapper
   - [ ] Add WebSocket router for real-time events
   - [ ] Connect frontend to WebSocket for status updates
   - [ ] Implement Run/Pause/Stop controls

3. **Phase 3 (Week 5-6)**: Debugging features
   - [ ] Add breakpoint system to ExecutionController
   - [ ] Implement step/step-over execution
   - [ ] Port tensor display from Streamlit to React
   - [ ] Add log viewer with filtering

4. **Phase 4 (Week 7-8)**: Polish
   - [ ] Value override capability
   - [ ] Selective re-run
   - [ ] Keyboard shortcuts
   - [ ] Export/import

---

**Document Version**: 1.1  
**Date**: December 2024  
**Status**: Implementation Plan - Option C (New Standalone App)
