# Canvas App Overview

**The NormCode Graph Canvas App is a visual, interactive environment for executing, debugging, and auditing NormCode plans.**

---

## Introduction

The Canvas App transforms NormCode from "run and hope" to "observe and control". Instead of executing plans blindly and inspecting results after the fact, users can:

1. **Visualize** the entire inference graph before execution
2. **Watch** execution progress in real-time
3. **Debug** with breakpoints and step-by-step execution
4. **Inspect** tensor data at any node
5. **Configure** multiple agents with different LLM models
6. **Edit** NormCode files directly within the app

---

## Core Concepts

### Project-Based Architecture

The Canvas App operates like an IDE (PyCharm, VS Code). Everything is organized around **projects**:

```
my_project/
├── gold-analysis.normcode-canvas.json    # Project config
├── concepts.json                         # Concept repository
├── inferences.json                       # Inference repository
├── inputs.json                           # Input data (optional)
└── provision/
    └── paradigm/                         # Custom paradigms
```

**Project Config** (`{name}.normcode-canvas.json`):
```json
{
  "id": "a1b2c3d4",
  "name": "Gold Analysis",
  "description": "Investment analysis project",
  "repositories": {
    "concepts": "concepts.json",
    "inferences": "inferences.json",
    "inputs": "inputs.json"
  },
  "execution": {
    "llm_model": "qwen-plus",
    "max_cycles": 100,
    "db_path": "orchestration.db",
    "paradigm_dir": "provision/paradigm"
  },
  "breakpoints": ["1.1", "2.3.1"]
}
```

### Multi-Project Support

A single directory can contain multiple project configurations:
- `gold-analysis.normcode-canvas.json`
- `gold-debug.normcode-canvas.json`
- `gold-chinese.normcode-canvas.json`

Each project has its own settings, breakpoints, and execution history while sharing the same repository files.

### Centralized Registry

All known projects are tracked in `~/.normcode-canvas/project-registry.json`:
```json
{
  "projects": [
    {
      "id": "a1b2c3d4",
      "name": "Gold Analysis",
      "directory": "C:/path/to/project",
      "config_file": "gold-analysis.normcode-canvas.json",
      "last_opened": "2024-12-21T15:30:00"
    }
  ]
}
```

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           BROWSER                                        │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  React App (Vite + TypeScript)                                    │  │
│  │  ├── Zustand Stores (state management)                            │  │
│  │  ├── React Flow (graph visualization)                             │  │
│  │  └── WebSocket Client (real-time events)                          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│              │ REST API              │ WebSocket                         │
└──────────────┼───────────────────────┼───────────────────────────────────┘
               ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND (FastAPI)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │  Routers                                                            ││
│  │  ├── project_router.py      # Project CRUD                         ││
│  │  ├── repository_router.py   # Load repositories                    ││
│  │  ├── graph_router.py        # Graph data                           ││
│  │  ├── execution_router.py    # Run/pause/step                       ││
│  │  ├── agent_router.py        # Agent configuration                  ││
│  │  ├── editor_router.py       # File editing                         ││
│  │  ├── checkpoint_router.py   # Resume/fork                          ││
│  │  └── websocket_router.py    # Event streaming                      ││
│  ├─────────────────────────────────────────────────────────────────────┤│
│  │  Services                                                           ││
│  │  ├── ExecutionController    # Orchestrator wrapper                 ││
│  │  ├── GraphService           # Graph building                       ││
│  │  ├── AgentRegistry          # Multi-agent management               ││
│  │  ├── ProjectService         # Project persistence                  ││
│  │  └── ParserService          # NormCode parsing                     ││
│  └─────────────────────────────────────────────────────────────────────┘│
│              │                                                           │
└──────────────┼───────────────────────────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      NORMCODE INFRASTRUCTURE                             │
│  ├── Orchestrator              # Execution engine                       │
│  ├── ConceptRepo               # Concept storage                        │
│  ├── InferenceRepo             # Inference storage                      │
│  ├── Body                      # Agent with tools                       │
│  └── OrchestratorDB            # Checkpoint storage                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Frontend Architecture

**State Management (Zustand Stores)**:

| Store | Purpose |
|-------|---------|
| `graphStore` | Graph nodes, edges, layout, collapse state |
| `executionStore` | Execution status, node statuses, breakpoints, logs |
| `selectionStore` | Selected node/edge, highlighted branches |
| `projectStore` | Current project, recent projects, registry |
| `configStore` | Execution settings (LLM, cycles, etc.) |
| `agentStore` | Agent configurations, mappings, tool calls |

**Component Hierarchy**:

```
App
├── ProjectPanel            # Welcome screen / project management
├── Header                  # Project info, view mode tabs, controls
├── SettingsPanel           # Execution configuration
├── ControlPanel            # Run/pause/step/stop buttons
├── CheckpointPanel         # Resume/fork from checkpoints
│
├── [Canvas Mode]
│   ├── AgentPanel          # Left: agent config + tool calls
│   ├── GraphCanvas         # Center: React Flow graph
│   │   ├── ValueNode       # Value concept nodes
│   │   ├── FunctionNode    # Function concept nodes
│   │   └── CustomEdge      # Styled edges by type
│   ├── DetailPanel         # Right: node details + tensor viewer
│   └── LogPanel            # Bottom: execution logs
│
├── [Editor Mode]
│   └── EditorPanel         # File browser + code editor
│
└── StatusBar               # Connection status, node count
```

### Backend Architecture

**Execution Controller**:

The `ExecutionController` class wraps the NormCode Orchestrator with debugging support:

```python
class ExecutionController:
    orchestrator: Orchestrator           # Core execution engine
    agent_registry: AgentRegistry        # Multi-agent management
    agent_mapping: AgentMappingService   # Per-inference agent assignment
    
    node_statuses: Dict[str, str]        # Flow index → status
    breakpoints: Set[str]                # Breakpoint flow indices
    logs: List[LogEntry]                 # Execution logs
    
    async def start()                    # Begin execution
    async def pause()                    # Pause after current inference
    async def step()                     # Execute one inference
    async def stop()                     # Stop execution
    async def run_to(flow_index)         # Run until specific node
    async def restart()                  # Reset and reload
```

**Agent Registry**:

The `AgentRegistry` manages multiple agent configurations:

```python
class AgentConfig:
    id: str                              # Unique identifier
    name: str                            # Display name
    llm_model: str                       # LLM model name
    tools: Dict[str, bool]               # Tool enable/disable
    paradigm_dir: Optional[str]          # Custom paradigm directory

class AgentRegistry:
    configs: Dict[str, AgentConfig]      # Registered agents
    bodies: Dict[str, Body]              # Cached Body instances
    
    def get_body(agent_id) -> Body       # Get/create Body
    def register(config)                 # Register agent config
```

---

## Graph Visualization

### Node Types and Categories

| Category | Examples | Color | Description |
|----------|----------|-------|-------------|
| **semantic-function** | `::(analyze)`, `:<filter>` | Purple | LLM-based operations |
| **semantic-value** | `{result}`, `<item>`, `[list]` | Blue | Data containers |
| **syntactic-function** | `$collect`, `&assign` | Gray | Deterministic operations |

### Node Status Indicators

| Status | Indicator | Description |
|--------|-----------|-------------|
| `pending` | Gray dot | Not yet executed |
| `running` | Blue pulsing dot | Currently executing |
| `completed` | Green dot | Successfully completed |
| `failed` | Red dot | Execution failed |
| `skipped` | Striped dot | Skipped (SKIP value) |

### Special Node Markers

| Marker | Visual | Meaning |
|--------|--------|---------|
| **Ground** | Double border | Input data (ground concept) |
| **Output** | Red ring | Final result (output concept) |
| **Breakpoint** | Red badge | Breakpoint set on this node |

### Edge Types

| Type | Color | Style | Description |
|------|-------|-------|-------------|
| `function` | Blue | Solid | Function → Target connection |
| `value` | Purple | Solid | Value input → Target connection |
| `context` | Green | Dashed | Context input connection |
| `alias` | Gray | Dashed | Same concept at different positions |

---

## Execution Model

### Flow Index System

Every node has a **flow index** that identifies its position in the execution DAG:

```
1           # Root concept (output)
├── 1.1     # Function concept
├── 1.2     # First value input
├── 1.3     # Second value input
│   ├── 1.3.1   # Sub-inference function
│   ├── 1.3.2   # Sub-inference value
```

Flow indices are used for:
- Node identification in the graph
- Breakpoint targeting
- Log filtering
- Execution ordering

### Execution Cycle

```
┌─────────────────────────────────────────────────────────────────┐
│  ExecutionController._run_loop()                                 │
├─────────────────────────────────────────────────────────────────┤
│  while (state == RUNNING or STEPPING):                          │
│      1. Check pause event                                        │
│      2. Get next ready inference from waitlist                  │
│      3. Check breakpoints → pause if hit                        │
│      4. Emit "inference:started" event                          │
│      5. Resolve agent for this inference                        │
│      6. Execute inference with assigned Body                    │
│      7. Emit "inference:completed" or "inference:failed"        │
│      8. Emit "execution:progress"                               │
│      9. If stepping mode → pause                                │
└─────────────────────────────────────────────────────────────────┘
```

### WebSocket Events

Real-time events streamed to the frontend:

| Event | Payload | Description |
|-------|---------|-------------|
| `execution:loaded` | `{run_id, total_inferences}` | Repositories loaded |
| `execution:started` | `{}` | Execution began |
| `execution:paused` | `{reason}` | Execution paused |
| `execution:progress` | `{completed, total}` | Progress update |
| `execution:completed` | `{}` | All inferences done |
| `inference:started` | `{flow_index}` | Inference began |
| `inference:completed` | `{flow_index}` | Inference succeeded |
| `inference:failed` | `{flow_index, error}` | Inference failed |
| `breakpoint:hit` | `{flow_index}` | Breakpoint triggered |
| `log:entry` | `{flow_index, level, message}` | Log message |
| `tool:call_started` | `{tool, method, inputs}` | Tool call began |
| `tool:call_completed` | `{tool, method, outputs}` | Tool call succeeded |

---

## Multi-Agent System

### Agent Configuration

The Agent Panel allows configuring multiple agents with different:
- LLM models (qwen-plus, gpt-4o, claude-3, etc.)
- Tool settings (file system, Python interpreter, etc.)
- Paradigm directories

### Agent Mapping

Inferences can be assigned to specific agents via:

1. **Pattern Rules**: Match by flow_index, concept_name, or sequence_type
2. **Explicit Assignment**: Direct flow_index → agent_id mapping
3. **Default Agent**: Fallback for unmatched inferences

### Tool Call Monitoring

All tool calls are captured and displayed in real-time:
- LLM calls with prompts and responses
- File system operations
- Python script executions
- User input requests

---

## Data Inspection

### TensorInspector

The TensorInspector component provides N-dimensional tensor viewing:

| Dimension | View |
|-----------|------|
| 0D (scalar) | Single value display |
| 1D | Horizontal cards or vertical list |
| 2D | Table with row/column headers |
| N-D | Axis selection + slice sliders + view mode |

**View Modes**:
- **Table**: Spreadsheet-like 2D slice view
- **List**: Expandable nested list view
- **JSON**: Raw JSON representation

### Perceptual Sign Parsing

Values in `%xxx({...})` format are automatically parsed and displayed as structured objects:

```
Input:  %c2a({'action': 'BUY', 'confidence': 0.82})
Display:
  ├── action: BUY
  └── confidence: 0.82
```

---

## File Organization

```
canvas_app/
├── backend/
│   ├── main.py                     # FastAPI entry point
│   ├── requirements.txt            # Python dependencies
│   ├── core/
│   │   ├── config.py              # App settings
│   │   └── events.py              # Event emitter
│   ├── routers/
│   │   ├── project_router.py      # Project CRUD
│   │   ├── repository_router.py   # Load repos
│   │   ├── graph_router.py        # Graph data
│   │   ├── execution_router.py    # Execution control
│   │   ├── agent_router.py        # Agent config
│   │   ├── editor_router.py       # File editing
│   │   ├── checkpoint_router.py   # Resume/fork
│   │   └── websocket_router.py    # Events
│   ├── services/
│   │   ├── execution_service.py   # ExecutionController
│   │   ├── graph_service.py       # Graph building
│   │   ├── agent_service.py       # Agent registry
│   │   ├── project_service.py     # Project management
│   │   └── parser_service.py      # NormCode parsing
│   └── schemas/
│       ├── execution_schemas.py   # Execution models
│       ├── graph_schemas.py       # Graph models
│       └── project_schemas.py     # Project models
│
├── frontend/
│   ├── package.json               # Node dependencies
│   ├── vite.config.ts             # Vite configuration
│   ├── tailwind.config.js         # Tailwind CSS config
│   └── src/
│       ├── App.tsx                # Main component
│       ├── main.tsx               # Entry point
│       ├── components/
│       │   ├── graph/
│       │   │   ├── GraphCanvas.tsx
│       │   │   ├── ValueNode.tsx
│       │   │   ├── FunctionNode.tsx
│       │   │   └── CustomEdge.tsx
│       │   └── panels/
│       │       ├── ControlPanel.tsx
│       │       ├── DetailPanel.tsx
│       │       ├── LogPanel.tsx
│       │       ├── AgentPanel.tsx
│       │       ├── EditorPanel.tsx
│       │       ├── ProjectPanel.tsx
│       │       ├── SettingsPanel.tsx
│       │       ├── CheckpointPanel.tsx
│       │       └── TensorInspector.tsx
│       ├── stores/
│       │   ├── graphStore.ts
│       │   ├── executionStore.ts
│       │   ├── selectionStore.ts
│       │   ├── projectStore.ts
│       │   ├── configStore.ts
│       │   └── agentStore.ts
│       ├── services/
│       │   ├── api.ts             # REST client
│       │   └── websocket.ts       # WebSocket client
│       ├── hooks/
│       │   └── useWebSocket.ts    # WebSocket hook
│       ├── types/
│       │   ├── graph.ts
│       │   ├── execution.ts
│       │   └── project.ts
│       └── utils/
│           └── tensorUtils.ts     # Tensor utilities
│
├── launch.py                      # Combined launcher
├── launch.ps1                     # PowerShell launcher
├── README.md                      # Quick start guide
├── IMPLEMENTATION_JOURNAL.md      # Development history
├── AGENT_PANEL_PLAN.md           # Agent feature plan
└── CHECKPOINT_FEATURE_PLAN.md    # Checkpoint feature plan
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 | UI framework |
| | TypeScript | Type safety |
| | Vite | Build tool & dev server |
| | React Flow | Graph visualization |
| | Zustand | State management |
| | TailwindCSS | Styling |
| | Lucide React | Icons |
| **Backend** | FastAPI | REST API framework |
| | Python 3.11+ | Runtime |
| | WebSockets | Real-time events |
| | Pydantic | Data validation |
| **Infrastructure** | NormCode Orchestrator | Execution engine |
| | SQLite | Checkpoint storage |

---

## See Also

- **[User Guide](canvas_app_user_guide.md)**: Detailed usage instructions
- **[API Reference](canvas_app_api_reference.md)**: REST and WebSocket API
- **[Implementation Plan](implementation_plan.md)**: Remaining work
