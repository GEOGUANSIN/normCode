# Canvas App API Reference

**Complete reference for the Canvas App REST API, WebSocket events, and frontend stores.**

---

## REST API

Base URL: `http://localhost:8000`

### Project Endpoints

#### `GET /api/project/current`
Get the currently open project.

**Response**:
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

#### `POST /api/project/open`
Open an existing project.

**Request**:
```json
{
  "project_path": "C:/path/to/project",
  "config_file": "gold-analysis.normcode-canvas.json",
  "project_id": null
}
```

**Response**: Same as `GET /api/project/current`

#### `POST /api/project/create`
Create a new project.

**Request**:
```json
{
  "name": "New Project",
  "directory": "C:/path/to/project",
  "description": "Description",
  "repositories": {
    "concepts": "concepts.json",
    "inferences": "inferences.json"
  },
  "execution": {
    "llm_model": "qwen-plus",
    "max_cycles": 100
  }
}
```

#### `POST /api/project/close`
Close the current project.

#### `GET /api/project/recent`
Get recent projects list.

**Response**:
```json
[
  {
    "id": "a1b2c3d4",
    "name": "Gold Analysis",
    "directory": "C:/path/to/project",
    "config_file": "gold.normcode-canvas.json",
    "last_opened": "2024-12-21T15:30:00"
  }
]
```

#### `GET /api/project/all`
Get all registered projects.

#### `POST /api/project/scan`
Scan a directory for project configs.

**Request**:
```json
{
  "directory": "C:/path/to/scan"
}
```

**Response**:
```json
{
  "directory": "C:/path/to/scan",
  "projects": [
    {
      "name": "Gold Analysis",
      "config_file": "gold.normcode-canvas.json"
    }
  ]
}
```

---

### Repository Endpoints

#### `POST /api/repositories/load`
Load repository files and create orchestrator.

**Request**:
```json
{
  "concepts_path": "C:/path/to/concepts.json",
  "inferences_path": "C:/path/to/inferences.json",
  "inputs_path": "C:/path/to/inputs.json",
  "llm_model": "qwen-plus",
  "max_cycles": 100,
  "db_path": "orchestration.db",
  "base_dir": "C:/path/to/project",
  "paradigm_dir": "provision/paradigm"
}
```

**Response**:
```json
{
  "success": true,
  "run_id": "abc123",
  "total_inferences": 25
}
```

#### `GET /api/repositories/examples`
List example repositories.

**Response**:
```json
[
  {
    "name": "add",
    "path": "streamlit_app/core/saved_repositories/add"
  }
]
```

---

### Graph Endpoints

#### `GET /api/graph`
Get current graph data.

**Response**:
```json
{
  "nodes": [
    {
      "id": "node@1.2",
      "label": "{result}",
      "category": "semantic-value",
      "node_type": "value",
      "flow_index": "1.2",
      "level": 1,
      "position": {"x": 300, "y": 100},
      "data": {
        "is_ground": false,
        "is_final": false,
        "axes": ["item"],
        "natural_name": "analysis result",
        "concept_name": "{result}"
      }
    }
  ],
  "edges": [
    {
      "id": "edge-func-1",
      "source": "node@1.1",
      "target": "node@1",
      "edge_type": "function",
      "label": "imperative",
      "flow_index": "1"
    }
  ]
}
```

#### `GET /api/graph/node/{node_id}`
Get detailed node information.

#### `GET /api/graph/stats`
Get graph statistics.

**Response**:
```json
{
  "total_nodes": 75,
  "total_edges": 77,
  "value_nodes": 54,
  "function_nodes": 21,
  "ground_concepts": 25,
  "final_concepts": 1
}
```

---

### Execution Endpoints

#### `POST /api/execution/start`
Start or resume execution.

#### `POST /api/execution/pause`
Pause execution after current inference.

#### `POST /api/execution/step`
Execute one inference then pause.

#### `POST /api/execution/stop`
Stop execution.

#### `POST /api/execution/restart`
Reset execution state.

**Response**:
```json
{
  "success": true,
  "run_id": "new-run-id",
  "node_statuses": {"1.1": "pending", "1.2": "pending"}
}
```

#### `POST /api/execution/run-to/{flow_index}`
Run until specific node.

#### `GET /api/execution/state`
Get current execution state.

**Response**:
```json
{
  "status": "running",
  "current_inference": "1.2.1",
  "completed_count": 8,
  "total_count": 25,
  "cycle_count": 3,
  "run_id": "abc123"
}
```

#### `GET /api/execution/reference/{concept_name}`
Get reference data for a concept.

**Response**:
```json
{
  "concept_name": "{result}",
  "data": [[1, 2, 3], [4, 5, 6]],
  "axes": ["row", "col"],
  "shape": [2, 3]
}
```

#### `GET /api/execution/references`
Get all reference data.

#### `POST /api/execution/breakpoint/{flow_index}`
Set a breakpoint.

#### `DELETE /api/execution/breakpoint/{flow_index}`
Clear a breakpoint.

#### `GET /api/execution/breakpoints`
List all breakpoints.

#### `GET /api/execution/logs`
Get execution logs.

**Query Parameters**:
- `flow_index`: Filter by flow index
- `level`: Filter by log level
- `limit`: Maximum entries

**Response**:
```json
{
  "logs": [
    {
      "timestamp": "2024-12-21T10:32:15.123Z",
      "flow_index": "1.2.1",
      "level": "INFO",
      "message": "Starting inference"
    }
  ]
}
```

#### `GET /api/execution/config`
Get available LLM models and defaults.

**Response**:
```json
{
  "available_models": ["qwen-plus", "gpt-4o", "claude-3"],
  "default_model": "qwen-plus",
  "default_max_cycles": 100,
  "default_db_path": "orchestration.db"
}
```

---

### Agent Endpoints

#### `GET /api/agents/`
List all registered agents.

**Response**:
```json
[
  {
    "id": "default",
    "name": "Default Agent",
    "llm_model": "qwen-plus",
    "description": ""
  }
]
```

#### `POST /api/agents/`
Create or update agent.

**Request**:
```json
{
  "id": "analyst",
  "name": "Analyst Agent",
  "llm_model": "gpt-4o",
  "llm_temperature": 0.7,
  "file_system_enabled": true,
  "python_interpreter_enabled": true,
  "paradigm_dir": "provision/paradigm"
}
```

#### `DELETE /api/agents/{agent_id}`
Delete an agent.

#### `GET /api/agents/{agent_id}/capabilities`
Get agent capabilities.

**Response**:
```json
{
  "agent_id": "default",
  "tools": [
    {
      "name": "LLM",
      "enabled": true,
      "description": "Language model",
      "methods": [".ask()", ".complete()"]
    }
  ],
  "paradigms": [
    {
      "name": "h_Data-c_PassThrough-o_Normal",
      "description": "Pass data through",
      "is_custom": true,
      "source": "provision/paradigm"
    }
  ],
  "sequences": [
    {
      "name": "imperative",
      "description": "LLM-based execution",
      "category": "llm"
    }
  ],
  "paradigm_dir": "provision/paradigm",
  "agent_frame_model": "demo"
}
```

#### `GET /api/agents/mappings/state`
Get agent mapping rules and assignments.

#### `POST /api/agents/mappings/rules`
Add a mapping rule.

**Request**:
```json
{
  "match_type": "sequence_type",
  "pattern": "imperative",
  "agent_id": "analyst",
  "priority": 0
}
```

#### `POST /api/agents/mappings/explicit/{flow_index}`
Set explicit agent assignment.

**Query Parameters**:
- `agent_id`: Agent to assign

#### `GET /api/agents/mappings/resolve/{flow_index}`
Resolve which agent handles an inference.

#### `GET /api/agents/tool-calls`
Get tool call history.

**Query Parameters**:
- `limit`: Maximum entries (default 100)

**Response**:
```json
[
  {
    "id": "call-123",
    "timestamp": "2024-12-21T10:32:15.123Z",
    "flow_index": "1.2.1",
    "agent_id": "default",
    "tool_name": "llm",
    "method": "generate",
    "inputs": {"prompt": "..."},
    "outputs": {"response": "..."},
    "duration_ms": 1234,
    "status": "completed"
  }
]
```

---

### Editor Endpoints

#### `GET /api/editor/file`
Read file content.

**Query Parameters**:
- `path`: File path

**Response**:
```json
{
  "path": "C:/project/example.ncd",
  "content": "file content here",
  "format": "ncd"
}
```

#### `POST /api/editor/file`
Save file content.

**Request**:
```json
{
  "path": "C:/project/example.ncd",
  "content": "file content here"
}
```

#### `POST /api/editor/list`
List files in directory.

**Request**:
```json
{
  "directory": "C:/project",
  "extensions": [".ncd", ".ncn", ".json"]
}
```

#### `POST /api/editor/list-tree`
List files as tree structure.

**Response**:
```json
{
  "children": [
    {
      "name": "repos",
      "type": "folder",
      "children": [
        {
          "name": "concepts.json",
          "type": "file",
          "format": "concept",
          "size": 1234
        }
      ]
    }
  ]
}
```

#### `GET /api/editor/validate`
Validate file syntax.

**Query Parameters**:
- `path`: File path

---

### Checkpoint Endpoints

#### `GET /api/checkpoints/runs`
List all runs in checkpoint database.

**Query Parameters**:
- `db_path`: Path to database

**Response**:
```json
[
  {
    "run_id": "abc123",
    "first_execution": "2024-12-21T10:00:00",
    "last_execution": "2024-12-21T10:32:00",
    "execution_count": 5,
    "max_cycle": 3
  }
]
```

#### `GET /api/checkpoints/runs/{run_id}/checkpoints`
List checkpoints for a run.

#### `POST /api/checkpoints/resume`
Resume from checkpoint.

**Request**:
```json
{
  "concepts_path": "concepts.json",
  "inferences_path": "inferences.json",
  "db_path": "orchestration.db",
  "run_id": "abc123",
  "cycle": null,
  "mode": "PATCH"
}
```

#### `POST /api/checkpoints/fork`
Fork from checkpoint with new run ID.

---

## WebSocket API

Connect to: `ws://localhost:8000/ws/events`

### Server → Client Events

#### Execution Events

| Event | Payload | Description |
|-------|---------|-------------|
| `execution:loaded` | `{run_id, total_inferences}` | Repositories loaded |
| `execution:started` | `{}` | Execution began |
| `execution:paused` | `{reason, inference}` | Execution paused |
| `execution:resumed` | `{}` | Execution resumed |
| `execution:stopped` | `{}` | Execution stopped |
| `execution:completed` | `{}` | All inferences done |
| `execution:error` | `{error}` | Fatal error |
| `execution:reset` | `{node_statuses, run_id}` | State reset |
| `execution:progress` | `{completed, total, cycle}` | Progress update |

#### Inference Events

| Event | Payload | Description |
|-------|---------|-------------|
| `inference:started` | `{flow_index}` | Inference began |
| `inference:completed` | `{flow_index}` | Inference succeeded |
| `inference:failed` | `{flow_index, error}` | Inference failed |
| `inference:retry` | `{flow_index, attempt}` | Inference retrying |

#### Breakpoint Events

| Event | Payload | Description |
|-------|---------|-------------|
| `breakpoint:hit` | `{flow_index}` | Breakpoint triggered |
| `breakpoint:set` | `{flow_index}` | Breakpoint added |
| `breakpoint:cleared` | `{flow_index}` | Breakpoint removed |

#### Log Events

| Event | Payload | Description |
|-------|---------|-------------|
| `log:entry` | `{flow_index, level, message, timestamp}` | Log message |

#### Tool Events

| Event | Payload | Description |
|-------|---------|-------------|
| `tool:call_started` | `{id, flow_index, agent_id, tool_name, method, inputs}` | Tool call began |
| `tool:call_completed` | `{id, outputs, duration_ms}` | Tool call succeeded |
| `tool:call_failed` | `{id, error}` | Tool call failed |

#### Agent Events

| Event | Payload | Description |
|-------|---------|-------------|
| `agent:registered` | `{agent_id}` | Agent added |
| `agent:updated` | `{agent_id}` | Agent modified |
| `agent:deleted` | `{agent_id}` | Agent removed |

### Client → Server Messages

| Message | Payload | Description |
|---------|---------|-------------|
| `execution:command` | `{action: "start"|"pause"|"stop"}` | Control execution |
| `breakpoint:set` | `{flow_index}` | Set breakpoint |
| `breakpoint:clear` | `{flow_index}` | Clear breakpoint |

---

## Frontend Stores

### graphStore

```typescript
interface GraphState {
  graphData: GraphData | null;
  isLoading: boolean;
  error: string | null;
  collapsedNodes: Set<string>;
  
  // Actions
  setGraphData(data: GraphData): void;
  fetchGraphData(): Promise<void>;
  toggleCollapse(nodeId: string): void;
  isCollapsed(nodeId: string): boolean;
  hasChildren(nodeId: string): boolean;
  getChildNodes(nodeId: string): string[];
  highlightBranch(nodeId: string): void;
  clearHighlight(): void;
}
```

### executionStore

```typescript
interface ExecutionState {
  status: 'idle' | 'running' | 'paused' | 'completed' | 'failed';
  nodeStatuses: Record<string, NodeStatus>;
  breakpoints: Set<string>;
  logs: LogEntry[];
  completedCount: number;
  totalCount: number;
  cycleCount: number;
  currentInference: string | null;
  runId: string | null;
  
  // Actions
  setStatus(status: ExecutionState['status']): void;
  setNodeStatus(flowIndex: string, status: NodeStatus): void;
  setNodeStatuses(statuses: Record<string, NodeStatus>): void;
  addBreakpoint(flowIndex: string): void;
  removeBreakpoint(flowIndex: string): void;
  toggleBreakpoint(flowIndex: string): void;
  addLog(entry: LogEntry): void;
  clearLogs(): void;
  setProgress(completed: number, total: number, cycle?: number): void;
  reset(): void;
}
```

### selectionStore

```typescript
interface SelectionState {
  selectedNodeId: string | null;
  selectedEdgeId: string | null;
  highlightedNodes: Set<string>;
  highlightedEdges: Set<string>;
  
  // Actions
  setSelectedNode(nodeId: string | null): void;
  setSelectedEdge(edgeId: string | null): void;
  highlightBranch(nodeId: string): void;
  clearHighlight(): void;
}
```

### projectStore

```typescript
interface ProjectState {
  currentProject: ProjectConfig | null;
  projectPath: string | null;
  projectConfigFile: string | null;
  isLoaded: boolean;
  repositoriesExist: boolean;
  isLoading: boolean;
  error: string | null;
  recentProjects: RegisteredProject[];
  allProjects: RegisteredProject[];
  projectPanelOpen: boolean;
  
  // Actions
  fetchCurrentProject(): Promise<void>;
  fetchRecentProjects(): Promise<void>;
  fetchAllProjects(): Promise<void>;
  openProject(path: string, configFile?: string, projectId?: string): Promise<void>;
  createProject(config: CreateProjectRequest): Promise<void>;
  saveProject(): Promise<void>;
  closeProject(): Promise<void>;
  loadProjectRepositories(): Promise<void>;
  updateSettings(settings: Partial<ExecutionSettings>): Promise<void>;
  setProjectPanelOpen(open: boolean): void;
}
```

### configStore

```typescript
interface ConfigState {
  llmModel: string;
  maxCycles: number;
  dbPath: string;
  baseDir: string;
  paradigmDir: string;
  availableModels: string[];
  
  // Actions
  setLlmModel(model: string): void;
  setMaxCycles(cycles: number): void;
  setDbPath(path: string): void;
  setBaseDir(dir: string): void;
  setParadigmDir(dir: string): void;
  fetchConfig(): Promise<void>;
}
```

### agentStore

```typescript
interface AgentState {
  agents: Record<string, AgentConfig>;
  rules: MappingRule[];
  explicitMappings: Record<string, string>;
  defaultAgent: string;
  toolCalls: ToolCallEvent[];
  selectedAgent: string | null;
  
  // Actions
  fetchAgents(): Promise<void>;
  addAgent(config: AgentConfig): Promise<void>;
  updateAgent(id: string, updates: Partial<AgentConfig>): Promise<void>;
  deleteAgent(id: string): Promise<void>;
  addRule(rule: MappingRule): Promise<void>;
  removeRule(index: number): Promise<void>;
  setExplicitMapping(flowIndex: string, agentId: string): Promise<void>;
  clearExplicitMapping(flowIndex: string): Promise<void>;
  addToolCall(event: ToolCallEvent): void;
  updateToolCall(id: string, updates: Partial<ToolCallEvent>): void;
  clearToolCalls(): void;
  getAgentForInference(flowIndex: string): string;
}
```

---

## Type Definitions

### Graph Types

```typescript
type NodeCategory = 'semantic-function' | 'semantic-value' | 'syntactic-function';
type NodeType = 'value' | 'function';
type EdgeType = 'function' | 'value' | 'context' | 'alias';
type NodeStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

interface GraphNode {
  id: string;
  label: string;
  category: NodeCategory;
  node_type: NodeType;
  flow_index: string | null;
  level: number;
  position: { x: number; y: number };
  data: {
    is_ground?: boolean;
    is_final?: boolean;
    axes?: string[];
    natural_name?: string;
    concept_name?: string;
    sequence?: string;
    working_interpretation?: Record<string, any>;
  };
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  edge_type: EdgeType;
  label?: string;
  flow_index: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
```

### Execution Types

```typescript
interface LogEntry {
  timestamp: string;
  flow_index: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  message: string;
}

interface ReferenceData {
  concept_name: string;
  data: any;
  axes: string[];
  shape: number[];
}
```

### Agent Types

```typescript
interface AgentConfig {
  id: string;
  name: string;
  description: string;
  llm_model: string;
  llm_temperature: number;
  llm_max_tokens: number;
  file_system_enabled: boolean;
  file_system_base_dir?: string;
  python_interpreter_enabled: boolean;
  python_interpreter_timeout: number;
  user_input_enabled: boolean;
  paradigm_dir?: string;
}

interface MappingRule {
  match_type: 'flow_index' | 'concept_name' | 'sequence_type';
  pattern: string;
  agent_id: string;
  priority: number;
}

interface ToolCallEvent {
  id: string;
  timestamp: string;
  flow_index: string;
  agent_id: string;
  tool_name: string;
  method: string;
  inputs: Record<string, any>;
  outputs?: any;
  duration_ms?: number;
  status: 'started' | 'completed' | 'failed';
  error?: string;
}
```

### Project Types

```typescript
interface ProjectConfig {
  id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  repositories: {
    concepts: string;
    inferences: string;
    inputs?: string;
  };
  execution: {
    llm_model: string;
    max_cycles: number;
    db_path: string;
    paradigm_dir?: string;
  };
  breakpoints: string[];
  ui_preferences: Record<string, any>;
}

interface RegisteredProject {
  id: string;
  name: string;
  directory: string;
  config_file: string;
  description?: string;
  created_at: string;
  last_opened: string;
}
```

---

## See Also

- **[Canvas App Overview](canvas_app_overview.md)**: Architecture and concepts
- **[User Guide](canvas_app_user_guide.md)**: Usage instructions
- **[Implementation Plan](implementation_plan.md)**: Remaining work
