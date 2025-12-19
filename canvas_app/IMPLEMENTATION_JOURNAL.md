# NormCode Canvas Tool - Implementation Journal

**Project Start**: December 18, 2024  
**Current Phase**: Phase 3 - Debugging Features + Project-Based Architecture  
**Status**: 🚧 Phase 3 In Progress (Phase 1 ✅ Phase 2 ✅ Complete, Tensor Inspection ✅, Project System ✅)

---

## Overview

This journal tracks the implementation progress of the NormCode Graph Canvas Tool - a visual, interactive environment for executing, debugging, and auditing NormCode plans.

**Reference**: See `documentation/current/updated/5_tools/implementation_plan.md` for the full implementation plan.

---

## Implementation Timeline

### December 19, 2024 - Project-Based Canvas Architecture

#### What Was Implemented

**Project-Based Architecture (NEW)**
The canvas app now operates like an IDE (PyCharm/VS Code) - you open a project, and all configuration is stored and restored automatically.

**Project Configuration File (`normcode-canvas.json`)**
- [x] Stored in project directory
- [x] Contains:
  - Project metadata (name, description, created/updated timestamps)
  - Repository paths (concepts.json, inferences.json, inputs.json)
  - Execution settings (LLM model, max cycles, db path, paradigm dir)
  - Saved breakpoints
  - UI preferences

**Backend Project Service (`project_service.py`)**
- [x] `ProjectService` class for project CRUD operations
- [x] Recent projects tracking (stored in `~/.normcode-canvas/recent-projects.json`)
- [x] Auto-validation of project existence
- [x] Absolute path resolution for repository files

**Backend Project Router (`/api/project/`)**
- [x] `GET /current` - Get currently open project
- [x] `POST /open` - Open existing project by path
- [x] `POST /create` - Create new project
- [x] `POST /save` - Save current project state
- [x] `POST /close` - Close current project
- [x] `GET /recent` - Get recent projects list
- [x] `DELETE /recent` - Clear recent projects
- [x] `POST /load-repositories` - Load repos from project config
- [x] `GET /paths` - Get absolute repository paths
- [x] `PUT /settings` - Update execution settings

**Frontend Project Store (`projectStore.ts`)**
- [x] Zustand store for project state
- [x] `currentProject`, `projectPath`, `isLoaded`, `repositoriesExist` state
- [x] `recentProjects` list
- [x] Async actions: `openProject`, `createProject`, `saveProject`, `closeProject`
- [x] Auto-load graph data after loading repositories

**Frontend ProjectPanel Component**
- [x] **Welcome Screen**: Shown when no project is open
  - Recent projects list with one-click open
  - "Open Project" and "New Project" buttons
- [x] **Project Modal**: Tabbed interface for open/create/recent
  - Open tab: Enter project directory path
  - Create tab: Full project configuration form
  - Recent tab: List of recent projects
- [x] **Project Header Bar**: Shown when project is open
  - Project name and path display
  - Repository status (loaded/missing)
  - Quick "Load Repositories" button
  - Settings and close buttons

**App Integration**
- [x] Project state checked on startup
- [x] Welcome screen shown if no project open
- [x] Project header bar shown when project is open
- [x] "Load Different" button for loading alternative repositories
- [x] Settings persisted with project

#### Files Created

**Backend**:
- `canvas_app/backend/schemas/project_schemas.py` - Project Pydantic models
- `canvas_app/backend/services/project_service.py` - Project CRUD service
- `canvas_app/backend/routers/project_router.py` - Project API endpoints

**Frontend**:
- `canvas_app/frontend/src/types/project.ts` - Project TypeScript types
- `canvas_app/frontend/src/stores/projectStore.ts` - Project Zustand store
- `canvas_app/frontend/src/components/panels/ProjectPanel.tsx` - Project UI

#### Files Modified

**Backend**:
- `canvas_app/backend/main.py` - Added project router
- `canvas_app/backend/routers/__init__.py` - Added project_router export

**Frontend**:
- `canvas_app/frontend/src/services/api.ts` - Added projectApi methods
- `canvas_app/frontend/src/App.tsx` - Integrated ProjectPanel and project-based flow

#### Project File Example

```json
{
  "name": "Gold Investment Analysis",
  "description": "NormCode plan for analyzing gold investment decisions",
  "created_at": "2024-12-19T10:30:00",
  "updated_at": "2024-12-19T15:45:00",
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
  "breakpoints": ["1.1", "2.3.1"],
  "ui_preferences": {}
}
```

#### Usage

1. **First Launch**: Welcome screen with recent projects
2. **Create Project**: Click "New Project", enter path and name
3. **Open Project**: Click "Open Project", enter path to existing project
4. **Work with Project**: Load repositories, execute, set breakpoints
5. **Save/Close**: Settings auto-save, or click close to return to welcome

---

### December 19, 2024 - Phase 3: Debugging Features (Part 2 - Restart & Breakpoint Fixes)

#### What Was Implemented

**Restart/Reset Functionality (NEW)**
- [x] **POST /execution/restart**: New API endpoint to reset execution state
  - Resets all node statuses to PENDING
  - Clears completed count and cycle count
  - Resets orchestrator's blackboard
  - Allows re-execution after completion
- [x] **ExecutionController.restart()**: Backend method for resetting execution
  - Stops any running execution first
  - Resets all tracking state
  - Emits `execution:reset` event via WebSocket
- [x] **executionApi.restart()**: Frontend API method
- [x] **Reset button enhanced**: ControlPanel reset button now:
  - Calls restart API instead of just stop
  - Shows orange color when execution is completed/failed (indicating "can restart")
  - Properly resets frontend state via WebSocket event

**WebSocket Event Handling**
- [x] **execution:reset event**: New event type for resetting execution
  - Updates node statuses from backend
  - Resets progress counters
  - Logs reset action

**Breakpoint Button Fix**
- [x] **Improved error logging**: Added console warning when breakpoint cannot be set (no flow_index)
- [x] **Better async handling**: Ensured breakpoint toggle updates local store after API call succeeds

#### Files Modified

**Backend**:
- `canvas_app/backend/services/execution_service.py`:
  - Added `restart()` async method to ExecutionController
  - Resets node_statuses, completed_count, cycle_count
  - Attempts to reset orchestrator blackboard
  - Emits `execution:reset` WebSocket event
- `canvas_app/backend/routers/execution_router.py`:
  - Added `POST /execution/restart` endpoint

**Frontend**:
- `canvas_app/frontend/src/services/api.ts`:
  - Added `restart()` method to executionApi
- `canvas_app/frontend/src/components/panels/ControlPanel.tsx`:
  - Added `handleRestart()` function
  - Updated reset button to call restart API
  - Added visual feedback (orange color) when restart is available
- `canvas_app/frontend/src/hooks/useWebSocket.ts`:
  - Added handler for `execution:reset` event
  - Added `setNodeStatuses` and `reset` to store access
- `canvas_app/frontend/src/components/panels/DetailPanel.tsx`:
  - Added warning log when breakpoint cannot be set

#### Technical Notes

**Restart Flow**:
```
User clicks Reset button (after completion)
    ↓ handleRestart()
executionApi.restart()
    ↓ POST /execution/restart
execution_controller.restart()
    ↓
Reset node_statuses, counts, blackboard
    ↓ emit("execution:reset", {...})
WebSocket → useWebSocket hook
    ↓ setNodeStatuses(), setProgress(0, total)
UI updates: all nodes show "pending"
    ↓
User can click Run to start fresh execution
```

---

### December 19, 2024 - Phase 3: Debugging Features (Part 1)

#### What Was Implemented

**TensorInspector Component (NEW)**
- [x] **tensorUtils.ts**: Ported tensor utilities from Streamlit Python to TypeScript
  - `getTensorShape()`: Calculate shape of nested arrays
  - `sliceTensor()`: Extract 2D slices from N-D tensors
  - `formatCellValue()`: Format values for display (handles `%(...)` syntax)
  - `getSliceDescription()`: Human-readable slice descriptions
  - `detectElementType()`: Detect tensor element types
- [x] **TensorInspector.tsx**: React component for N-D tensor viewing
  - Scalar view: Single value display
  - 1D view: Horizontal cards or vertical list
  - 2D view: Table with row/column headers
  - N-D view: Axis selection + slice sliders + view modes (Table/List/JSON)
  - Collapsible mode for compact display

**Reference Data API (NEW)**
- [x] **GET /execution/reference/{concept_name}**: Get reference data for a specific concept
  - Returns tensor data, axes, shape from orchestrator's concept repo
  - Works for both ground concepts and computed values
- [x] **GET /execution/references**: Get all reference data in batch
  - Returns dict of concept_name → reference_data
- [x] **get_reference_data()** method in ExecutionController
  - Extracts tensor data from concept.reference
  - Handles axis name extraction

**Enhanced DetailPanel**
- [x] **Reference Data Section**: Shows tensor data for value nodes
  - Fetches reference data when node is selected
  - Integrates TensorInspector for visualization
  - Refresh button to reload data during execution
  - Handles loading states and errors gracefully
- [x] **Context Badge**: Shows "Context" label for context nodes
- [x] **Run To Button**: Placeholder for run-to functionality

**Per-Node Log Filtering**
- [x] **Node Filter Toggle**: Filter logs by selected node's flow_index
  - Shows only logs for selected node + global logs
  - Purple highlight for matching log entries
  - Disabled when no node selected
- [x] **Filter Indicator**: Shows active node filter in collapsed header

#### Files Created

- `canvas_app/frontend/src/utils/tensorUtils.ts` - Tensor utility functions
- `canvas_app/frontend/src/components/panels/TensorInspector.tsx` - Tensor viewer component

#### Files Modified

**Backend**:
- `canvas_app/backend/services/execution_service.py`:
  - Added `get_reference_data()` method
  - Added `get_all_reference_data()` method
- `canvas_app/backend/routers/execution_router.py`:
  - Added `/execution/reference/{concept_name}` endpoint
  - Added `/execution/references` endpoint

**Frontend**:
- `canvas_app/frontend/src/services/api.ts`:
  - Added `getReference()` method
  - Added `getAllReferences()` method
  - Added `ReferenceData` type
- `canvas_app/frontend/src/components/panels/DetailPanel.tsx`:
  - Integrated TensorInspector component
  - Added reference data fetching on node selection
  - Added refresh functionality
  - Added context and run-to UI elements
- `canvas_app/frontend/src/components/panels/LogPanel.tsx`:
  - Added node filter toggle
  - Integrated with selection store
  - Added visual highlighting for selected node logs

#### Technical Notes

**Tensor Slicing Algorithm**:
```typescript
// For N-D tensors (N > 2), user selects:
// - displayAxes: [rowAxis, colAxis] - which 2 axes to show
// - sliceIndices: {axisN: index} - fixed indices for other axes

function sliceTensor(data, displayAxes, sliceIndices, totalDims) {
  // Recursively navigate tensor
  // Keep dimensions in displayAxes (map over all elements)
  // Slice dimensions not in displayAxes (take single index)
}
```

**Reference Data Flow**:
```
DetailPanel (select node)
    ↓ useEffect
executionApi.getReference(conceptName)
    ↓ 
execution_router.py → execution_controller.get_reference_data()
    ↓
concept_repo.get(name) → concept.reference.tensor
    ↓
Return {data, axes, shape}
    ↓
TensorInspector renders the data
```

---

### December 19, 2024 - Execution Environment Enhancement

#### What Was Implemented

**Custom Paradigm Directory Support**
- [x] **Paradigm Directory field**: Added to Settings Panel for specifying custom paradigm locations
- [x] **CustomParadigmTool class**: Created in `execution_service.py` to load paradigms from non-default directories
- [x] **Relative path support**: Paradigm directory can be relative to base_dir (e.g., `provision/paradigm`)
- [x] **Logging integration**: Custom paradigm usage logged to execution logs

**Execution Configuration (Phase 2 Enhancement)**
- [x] **LLM Model selection**: Dropdown populated from `settings.yaml` via backend API
- [x] **Max Cycles configuration**: Configurable execution cycle limit (1-1000)
- [x] **Database Path**: SQLite checkpoint database path configuration
- [x] **Base Directory**: Override base directory for file operations
- [x] **Paradigm Directory**: Custom paradigm directory for project-specific paradigms

**New Components**
- [x] **SettingsPanel (`SettingsPanel.tsx`)**: Collapsible panel for all execution configuration
- [x] **ConfigStore (`configStore.ts`)**: Zustand store for execution settings state

**Backend API Enhancements**
- [x] **GET /execution/config**: Returns available LLM models and default config values
- [x] **Dynamic model loading**: Reads models from `settings.yaml` using `infra._constants.PROJECT_ROOT`

#### Files Modified

**Backend**:
- `canvas_app/backend/schemas/execution_schemas.py`:
  - Added `paradigm_dir` to `LoadRepositoryRequest` and `ExecutionConfig`
  - Added `get_available_llm_models()` for dynamic model loading
  - Added `DEFAULT_MAX_CYCLES`, `DEFAULT_DB_PATH` constants
- `canvas_app/backend/services/execution_service.py`:
  - Added `CustomParadigmTool` class
  - Updated `load_repositories()` to accept and use `paradigm_dir`
  - Body instantiation with optional custom paradigm tool
- `canvas_app/backend/routers/repository_router.py`: Pass `paradigm_dir` to controller
- `canvas_app/backend/routers/execution_router.py`: Added `/execution/config` endpoint

**Frontend**:
- `canvas_app/frontend/src/types/execution.ts`: Added `paradigm_dir` to types
- `canvas_app/frontend/src/stores/configStore.ts`: NEW - Config state management
- `canvas_app/frontend/src/services/api.ts`: Added `getConfig()` method
- `canvas_app/frontend/src/components/panels/SettingsPanel.tsx`: NEW - Settings UI
- `canvas_app/frontend/src/components/panels/LoadPanel.tsx`: Integrated config store
- `canvas_app/frontend/src/App.tsx`: Integrated SettingsPanel

#### Technical Notes

**CustomParadigmTool Pattern**:
Based on the pattern from `direct_infra_experiment/nc_ai_planning_ex/iteration_6/gold/_executor.py`:
1. CustomParadigmTool loads paradigms from a specified directory
2. Falls back to infra Paradigm class with custom directory
3. Injected into Body constructor as `paradigm_tool` parameter

**Configuration Flow**:
```
Frontend (SettingsPanel)
    ↓ useConfigStore
LoadPanel → API request with config
    ↓
repository_router → execution_service.load_repositories()
    ↓
CustomParadigmTool created if paradigm_dir specified
    ↓
Body(paradigm_tool=custom_paradigm_tool)
```

**Usage Example**:
For the gold investment example:
- Base Directory: `C:\...\direct_infra_experiment\nc_ai_planning_ex\iteration_6\gold`
- Paradigm Directory: `provision/paradigm`
- This loads paradigms from `gold/provision/paradigm/` including `h_Data-c_PassThrough-o_Normal.json`

---

### December 18, 2024 - Phase 2: Execution Integration

#### What Was Implemented

**Backend Execution Service (`execution_service.py`)**
- [x] **Inference-by-inference execution control**: Rewrote `_run_loop` and `_run_cycle_with_events` to process inferences one at a time
- [x] **Real-time WebSocket events**: Emits events for:
  - `execution:loaded`, `execution:started`, `execution:paused`, `execution:resumed`, `execution:stopped`, `execution:completed`, `execution:error`
  - `inference:started`, `inference:completed`, `inference:failed`, `inference:retry`
  - `execution:progress` with completed_count/total_count
  - `log:entry` for real-time log streaming
- [x] **Breakpoint support**: Check for breakpoints before each inference execution
- [x] **Stepping mode**: Execute one inference then pause
- [x] **Log management**: Track execution logs with timestamp, level, flow_index, message

**Updated Schemas (`execution_schemas.py`)**
- [x] Added `cycle_count` to `ExecutionState`
- [x] Added `LogEntry` model for structured log entries
- [x] Added `LogsResponse` model for log retrieval

**Updated Execution Router (`execution_router.py`)**
- [x] Added `GET /execution/logs` endpoint with filtering by flow_index

**Frontend Execution Store (`executionStore.ts`)**
- [x] Added `cycleCount` state
- [x] Updated `setProgress` to accept optional cycle parameter
- [x] Updated `reset` to clear all new fields

**Frontend WebSocket Hook (`useWebSocket.ts`)**
- [x] Handle `execution:loaded` event with run_id and total_inferences
- [x] Handle `execution:progress` event with completed/total counts
- [x] Handle `inference:retry` event
- [x] Return connection status for UI display
- [x] Added reactive connection state tracking

**Control Panel (`ControlPanel.tsx`)**
- [x] Display current inference being executed
- [x] Display cycle count
- [x] Animated spinner during execution

**Log Panel (`LogPanel.tsx`) - NEW COMPONENT**
- [x] Real-time log display with auto-scroll
- [x] Log level filtering (all, info, warning, error)
- [x] Color-coded log levels with icons
- [x] Flow index highlighting
- [x] Clear logs button
- [x] Collapsible panel

**App Layout (`App.tsx`)**
- [x] Integrated LogPanel into main layout
- [x] WebSocket connection status indicator
- [x] Execution status indicator with color coding

#### Files Modified

- `canvas_app/backend/services/execution_service.py`: Full rewrite for Phase 2
- `canvas_app/backend/schemas/execution_schemas.py`: Added LogEntry, LogsResponse
- `canvas_app/backend/routers/execution_router.py`: Added logs endpoint
- `canvas_app/frontend/src/stores/executionStore.ts`: Added cycleCount
- `canvas_app/frontend/src/hooks/useWebSocket.ts`: New events + connection state
- `canvas_app/frontend/src/components/panels/ControlPanel.tsx`: Current inference display
- `canvas_app/frontend/src/components/panels/LogPanel.tsx`: NEW FILE
- `canvas_app/frontend/src/App.tsx`: LogPanel integration, status bar

#### Technical Notes

**Execution Flow**:
1. `ExecutionController.start()` creates background `_run_loop` task
2. `_run_loop` runs cycles until completion or max_cycles
3. `_run_cycle_with_events` processes each inference with:
   - Pause/resume check via `asyncio.Event`
   - Breakpoint check before execution
   - WebSocket events for start/complete/fail
   - Stepping support (pause after one inference)
4. All execution uses `asyncio.to_thread` to run blocking Orchestrator methods

**Event Flow**:
```
Orchestrator._execute_item() 
    ↓
ExecutionController._run_cycle_with_events()
    ↓ emit("inference:started")
await asyncio.to_thread(orchestrator._execute_item)
    ↓ emit("inference:completed") or emit("inference:failed")
    ↓ emit("execution:progress")
```

---

### December 18, 2024 - Graph Layout Improvements

#### What Was Implemented

**Graph Layout & Flow Index Alignment**
- [x] **Right-to-left data flow**: Reversed graph layout so children/inputs are on the LEFT and parents/outputs are on the RIGHT
  - Updated `_calculate_positions()` in `graph_service.py` to reverse x-coordinates
  - Children (deeper flow indices) positioned at x=0 (left)
  - Root/output concepts positioned at x=max (right)
  
- [x] **Proper flow index assignment**: All concepts now get explicit flow indices following NormCode pattern
  - `concept_to_infer` gets base flow_index (e.g., "1")
  - `function_concept` gets base + ".1" (e.g., "1.1")
  - `value_concepts[0]` gets base + ".2" (e.g., "1.2")
  - `value_concepts[1]` gets base + ".3" (e.g., "1.3")
  - Continues for context_concepts
  
- [x] **Hierarchical sorting**: Nodes at same level sorted by full flow_index tuple
  - Ensures `1.1.3` appears above `1.2.1` (because parent `1.1` < `1.2`)
  - Children of earlier parents always positioned before children of later parents
  - Matches NormCode document structure exactly
  
- [x] **Duplicate node handling**: When same concept appears at multiple flow indices
  - Creates separate node instances (e.g., `node@1.2` and `node@2.3`)
  - Connects duplicates with "alias" edges (dashed gray lines)
  - Uses equivalence symbol "≡" as edge label
  
- [x] **Node ID refactoring**: Changed from `{concept_name}@{level}` to `node@{flow_index}`
  - Enables unique identification of same concept at different positions
  - Better aligns with NormCode's flow_index addressing scheme
  
- [x] **Handle position correction**: Swapped React Flow handle positions
  - Source handle (arrow start) on RIGHT side of child nodes
  - Target handle (arrow end) on LEFT side of parent nodes
  - Arrows now flow correctly: Child → Parent (LEFT to RIGHT)

**Edge Type Enhancement**
- [x] Added "alias" edge type in `CustomEdge.tsx`
  - Dashed line styling (`strokeDasharray: '5,5'`)
  - Gray color (`#9ca3af`)
  - Lower opacity (0.5)
  - Italic label styling

#### Visual Result

**Before**: 
```
[Root/Output] ──→ [Processing] ──→ [Ground/Input]
    (LEFT)                            (RIGHT)
```

**After**:
```
[Ground/Input] ──→ [Processing] ──→ [Root/Output]
    (LEFT)                             (RIGHT)
```

**Flow Index Hierarchy** (example):
```
Level 0: node@1              (x=600, rightmost)
Level 1: node@1.1            (x=300)
         node@1.2            (x=300)
Level 2: node@1.1.1          (x=0, leftmost)
         node@1.1.2          (x=0)
         node@1.2.1          (x=0)  ← Below all 1.1.x nodes
```

#### Files Modified

- `canvas_app/backend/services/graph_service.py`:
  - Rewrote `_calculate_positions()` for hierarchical left-to-right layout
  - Refactored `build_graph_from_repositories()` to assign proper flow indices
  - Added `register_concept_flow_index()` tracking function
  - Added alias edge creation for duplicate concepts

- `canvas_app/frontend/src/components/graph/ValueNode.tsx`:
  - Changed target handle from Left → Right (arrow entry)
  - Changed source handle from Right → Left → Right (arrow exit)
  
- `canvas_app/frontend/src/components/graph/FunctionNode.tsx`:
  - Changed target handle from Left → Right (arrow entry)
  - Changed source handle from Right → Left → Right (arrow exit)
  
- `canvas_app/frontend/src/components/graph/CustomEdge.tsx`:
  - Added "alias" to edge type union
  - Added dashed styling for alias edges
  - Added gray color and italic label styling

#### Technical Notes

**Layout Algorithm**:
- Groups nodes by level (depth in flow_index tree)
- Sorts each level by lexicographic flow_index order: `(1,1,3) < (1,2,1)`
- Assigns sequential y-positions within each level
- Calculates x-position as `(max_level - current_level) * h_spacing`

**Flow Index Benefits**:
- Every node has explicit position in execution DAG
- Easy to identify parent-child relationships
- Supports duplicate concepts (same concept at different execution points)
- Matches NormCode document format exactly

---

### December 18, 2024 - Phase 1 Complete

#### What Was Implemented

**Backend (FastAPI)**
- [x] Project structure created (`canvas_app/backend/`)
- [x] Main FastAPI application (`main.py`)
- [x] CORS configuration for frontend at `localhost:5173`
- [x] Core modules:
  - `core/config.py` - Application settings with pydantic-settings
  - `core/events.py` - Event emitter for WebSocket broadcasting
- [x] Schema definitions:
  - `schemas/graph_schemas.py` - GraphNode, GraphEdge, GraphData
  - `schemas/execution_schemas.py` - ExecutionStatus, NodeStatus, LoadRepositoryRequest
- [x] Services:
  - `services/graph_service.py` - Graph construction from repositories
  - `services/execution_service.py` - Orchestrator wrapper with debugging support
- [x] API Routers:
  - `routers/repository_router.py` - Load/list repositories
  - `routers/graph_router.py` - Get graph data and node details
  - `routers/execution_router.py` - Run/pause/step/stop commands
  - `routers/websocket_router.py` - Real-time event streaming

**Frontend (React + Vite)**
- [x] Project structure created (`canvas_app/frontend/`)
- [x] Vite configuration with proxy for API/WebSocket
- [x] TailwindCSS setup with custom theme colors
- [x] TypeScript types:
  - `types/graph.ts` - GraphNode, GraphEdge, NodeCategory
  - `types/execution.ts` - ExecutionStatus, NodeStatus, WebSocketEvent
- [x] Zustand stores:
  - `stores/graphStore.ts` - Graph data and loading state
  - `stores/executionStore.ts` - Execution status, node statuses, breakpoints
  - `stores/selectionStore.ts` - Selected node/edge tracking
- [x] Services:
  - `services/api.ts` - REST API client
  - `services/websocket.ts` - WebSocket client with reconnection
- [x] Hooks:
  - `hooks/useWebSocket.ts` - WebSocket connection and event handling
- [x] Components:
  - `components/graph/ValueNode.tsx` - Custom React Flow node for values
  - `components/graph/FunctionNode.tsx` - Custom React Flow node for functions
  - `components/graph/CustomEdge.tsx` - Styled edges by type
  - `components/graph/GraphCanvas.tsx` - Main React Flow canvas
  - `components/panels/ControlPanel.tsx` - Run/pause/step controls
  - `components/panels/DetailPanel.tsx` - Node inspection panel
  - `components/panels/LoadPanel.tsx` - Repository loading modal
- [x] Main App component with layout

**Launchers**
- [x] `launch.py` - Python combined launcher
- [x] `launch.ps1` - PowerShell launcher
- [x] `README.md` - Usage documentation

#### Issues Encountered & Resolved

1. **Issue**: `ConceptRepo.from_json` not found
   - **Cause**: The actual method in `infra/_orchest/_repo.py` is `from_json_list`
   - **Fix**: Updated `execution_service.py` to use correct method:
     ```python
     self.concept_repo = ConceptRepo.from_json_list(concepts_data)
     self.inference_repo = InferenceRepo.from_json_list(inferences_data, self.concept_repo)
     ```

2. **Issue**: Server reload not picking up changes
   - **Fix**: Manually restarted uvicorn server

#### Testing Results

Successfully tested with example repository `add`:
- **75 nodes** loaded (54 value, 21 function)
- **77 edges** loaded (22 function, 45 value, 10 context)
- **25 ground concepts**, **1 final concept**
- Category distribution: 53 semantic-value, 14 syntactic-function, 8 semantic-function

API endpoints verified:
- `GET /` - Returns API info ✅
- `GET /api/repositories/examples` - Lists examples ✅
- `POST /api/repositories/load` - Loads repositories ✅
- `GET /api/graph` - Returns graph data ✅
- `GET /api/graph/stats` - Returns statistics ✅

---

## Current State

### What's Working

| Feature | Status | Notes |
|---------|--------|-------|
| Backend API | ✅ Working | All endpoints responding |
| Graph loading | ✅ Working | Parses concept/inference repos |
| Graph visualization | ✅ Working | React Flow with custom nodes |
| Node styling | ✅ Working | Color-coded by category |
| Flow index assignment | ✅ Working | All concepts get proper flow indices |
| Hierarchical layout | ✅ Working | Left-to-right flow, sorted by flow_index |
| Duplicate node handling | ✅ Working | Alias edges connect same concept at different positions |
| Status indicators | ✅ Working | Pending/running/complete dots |
| Ground/output markers | ✅ Working | Double border, red ring |
| Selection | ✅ Working | Click node to select |
| Detail panel | ✅ Working | Shows node info |
| WebSocket connection | ✅ Working | Connects and reconnects |
| Control bar UI | ✅ Working | Run/Pause/Step/Stop buttons |
| Load repository modal | ✅ Working | File path input |
| **Execution start/stop** | ✅ Working | Orchestrator integration |
| **Real-time node updates** | ✅ Working | WebSocket events for inference status |
| **Log panel** | ✅ Working | Real-time log streaming with filtering |
| **Progress tracking** | ✅ Working | Completed/total count, cycle count |
| **Breakpoint support** | ✅ Working | Set breakpoints, pause on hit |
| **Step execution** | ✅ Working | Execute one inference then pause |
| **Settings Panel** | ✅ Working | LLM, max cycles, db path, base dir, paradigm dir |
| **Custom paradigm dir** | ✅ Working | Load paradigms from project-specific directories |
| **LLM model selection** | ✅ Working | Dynamic loading from settings.yaml |
| **Tensor inspection** | ✅ Working | N-D tensor viewer with axis selection and slicing |
| **Reference data API** | ✅ Working | Fetch live reference data from orchestrator |
| **Per-node log filtering** | ✅ Working | Filter logs by selected node |
| **Restart after completion** | ✅ Working | Reset button allows re-running after completion |
| **Project-based canvas** | ✅ Working | IDE-like project management with config persistence |
| **Recent projects** | ✅ Working | Quick access to recently opened projects |
| **Project welcome screen** | ✅ Working | Launch screen for opening/creating projects |

### What's Not Yet Working

| Feature | Status | Phase |
|---------|--------|-------|
| "Run to" feature | ❌ Not started | Phase 3 |
| Node expansion (detailed view) | ❌ Not started | Phase 3 |
| Value override | ❌ Not started | Phase 4 |
| Function modification | ❌ Not started | Phase 4 |
| Selective re-run | ❌ Not started | Phase 4 |

---

## Next Steps

### Phase 2: Execution Integration ✅ COMPLETE

**Completed**:
- [x] Hook Orchestrator to emit events on inference start/complete
- [x] Update graph nodes in real-time based on WebSocket events
- [x] Implement actual Run/Pause/Stop functionality
- [x] Add progress tracking
- [x] Emit WebSocket events during execution
- [x] Update `useWebSocket` hook to handle all event types
- [x] Real-time status updates on nodes
- [x] Log streaming

### Phase 3: Debugging Features 🚧 IN PROGRESS

**Goals**:
1. ✅ Tensor data inspection in detail panel
2. ✅ Per-node log filtering in log panel
3. Node expansion with detailed execution info
4. ✅ Reference data viewer

**Completed Tasks**:
- [x] Add `TensorInspector` component for multi-dimensional data viewing
- [x] Port tensor slicing utilities from Streamlit app (tensorUtils.ts)
- [x] Add log filtering by selected node
- [x] Add reference data API endpoints
- [x] Integrate TensorInspector into DetailPanel

**Remaining Tasks**:
- [ ] Add "Run to" feature (run until specific node)
- [ ] Add expanded node view with working interpretation details

**Estimated Effort**: ~1 more day for remaining tasks

### Phase 4: Modification & Re-run

**Goals**:
1. Value override capability
2. Function modification (paradigm, prompt)
3. Selective re-run from any node
4. Run comparison

**Key Tasks**:
- [ ] Value editor dialog for ground concepts
- [ ] Working interpretation editor
- [ ] Re-run dependency analysis
- [ ] Checkpoint/restore state management

**Estimated Effort**: 3-4 days

---

## Technical Notes

### Key Design Decisions

1. **Standalone App**: Created new `canvas_app` instead of extending existing `editor_app` or `streamlit_app` to have clean architecture purpose-built for graph debugging.

2. **React Flow**: Chose React Flow over raw SVG for better pan/zoom/interaction support and custom node capabilities.

3. **Zustand**: Used Zustand for state management - simpler than Redux with great TypeScript support.

4. **WebSocket for real-time**: Using WebSocket instead of polling for real-time execution updates.

5. **Flow index-based layout**: Graph layout based on complete flow_index hierarchy, preserving parent-child relationships from NormCode structure.
   - Left-to-right flow (inputs → outputs)
   - Hierarchical vertical sorting (children of earlier parents come first)
   - Duplicate nodes with alias edges for concepts appearing at multiple positions

6. **Node identification**: Using `node@{flow_index}` as node IDs instead of `{concept_name}@{level}` to support:
   - Same concept appearing at different flow indices
   - Direct mapping to NormCode's addressing scheme
   - Easier debugging and tracing

### File Locations

| Component | Path |
|-----------|------|
| Backend entry | `canvas_app/backend/main.py` |
| Graph service | `canvas_app/backend/services/graph_service.py` |
| Execution service | `canvas_app/backend/services/execution_service.py` |
| Frontend entry | `canvas_app/frontend/src/main.tsx` |
| Graph canvas | `canvas_app/frontend/src/components/graph/GraphCanvas.tsx` |
| Custom nodes | `canvas_app/frontend/src/components/graph/ValueNode.tsx` |

### Dependencies

**Backend** (`requirements.txt`):
- fastapi>=0.109.0
- uvicorn[standard]>=0.27.0
- websockets>=12.0
- pydantic>=2.5.0
- pydantic-settings>=2.1.0
- python-multipart>=0.0.6

**Frontend** (`package.json`):
- react: ^18.2.0
- reactflow: ^11.10.0
- zustand: ^4.4.7
- @tanstack/react-query: ^5.17.0
- tailwindcss: ^3.4.0
- lucide-react: ^0.303.0

---

## Running the App

### Quick Start

```powershell
# Terminal 1: Backend
cd c:\Users\ProgU\PycharmProjects\normCode\canvas_app\backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd c:\Users\ProgU\PycharmProjects\normCode\canvas_app\frontend
npm run dev
```

### URLs

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws/events

### Test Repository

```
Concepts: c:/Users/ProgU/PycharmProjects/normCode/streamlit_app/core/saved_repositories/add/concepts.json
Inferences: c:/Users/ProgU/PycharmProjects/normCode/streamlit_app/core/saved_repositories/add/inferences.json
```

---

## Changelog

### v0.4.0 (December 19, 2024) - Project-Based Canvas Architecture
- **Project Management**:
  - IDE-like project system (similar to PyCharm/VS Code)
  - `normcode-canvas.json` configuration file per project
  - Recent projects list with quick access
  - Welcome screen on startup for project selection
- **Project Configuration**:
  - Repository paths (concepts, inferences, inputs)
  - Execution settings (LLM model, max cycles, db path, paradigm dir)
  - Breakpoint persistence across sessions
  - UI preferences storage
- **New API Endpoints**:
  - `GET/POST /api/project/*` - Full project CRUD operations
  - Recent projects tracking in `~/.normcode-canvas/`
- **New Frontend Components**:
  - `ProjectPanel` - Welcome screen and project management modal
  - `projectStore` - Zustand store for project state
  - Project header bar with status and quick actions
- **Workflow Improvement**:
  - Open project → Load repositories → Execute
  - Settings automatically saved with project
  - Breakpoints preserved between sessions

### v0.3.1 (December 19, 2024) - Restart & Breakpoint Fixes
- **Restart Functionality**:
  - New `/execution/restart` API endpoint to reset execution state
  - Reset button in ControlPanel now allows re-running after completion
  - Orange visual indicator when restart is available (completed/failed state)
  - Properly resets node statuses, counters, and orchestrator blackboard
- **WebSocket Event Handling**:
  - New `execution:reset` event type for syncing reset state
  - Improved breakpoint event handling
- **Breakpoint Improvements**:
  - Better error logging when breakpoint cannot be set (missing flow_index)
  - Improved async handling for breakpoint toggle

### v0.3.0 (December 19, 2024) - Phase 3: Debugging Features
- **Tensor Inspection**:
  - New `TensorInspector` component for viewing N-D tensor data
  - Supports scalar, 1D, 2D, and higher-dimensional tensors
  - Axis selection for N-D tensors (choose row/column axes)
  - Slice sliders for non-displayed axes
  - Multiple view modes: Table, List, JSON
  - Collapsible compact mode
- **Reference Data API**:
  - GET `/execution/reference/{concept_name}` - fetch reference data for a concept
  - GET `/execution/references` - batch fetch all reference data
  - Returns tensor data, axes, and shape
- **Enhanced Detail Panel**:
  - Reference data section with TensorInspector integration
  - Auto-fetch reference data when node is selected
  - Refresh button to reload during execution
  - Context badge for context nodes
  - "Run To" button placeholder
- **Per-Node Log Filtering**:
  - Toggle to filter logs by selected node's flow_index
  - Visual highlighting for matching log entries
  - Filter indicator in collapsed header
- **New Files**:
  - `frontend/src/utils/tensorUtils.ts` - Tensor utility functions
  - `frontend/src/components/panels/TensorInspector.tsx` - Tensor viewer component

### v0.2.1 (December 19, 2024) - Execution Environment Enhancement
- **Execution Configuration**:
  - New Settings Panel for all execution configuration options
  - LLM model selection with dynamic loading from settings.yaml
  - Max cycles configuration (1-1000)
  - Database path for checkpointing
  - Base directory override
  - Custom paradigm directory support
- **Custom Paradigm Tool**:
  - CustomParadigmTool class for loading paradigms from project-specific directories
  - Relative path support (e.g., `provision/paradigm` relative to base_dir)
  - Automatic paradigm directory validation
- **Frontend**:
  - New configStore (Zustand) for execution settings state
  - SettingsPanel component with all config fields
  - LoadPanel integration with config store
  - Config summary in Load Repository modal
- **Backend API**:
  - GET /execution/config endpoint for available models and defaults
  - Dynamic LLM model discovery from settings.yaml

### v0.2.0 (December 18, 2024) - Phase 2 Complete
- **Execution Integration**:
  - Full Orchestrator integration with inference-by-inference control
  - Real-time WebSocket events for all execution states
  - Breakpoint support with pause-on-hit
  - Stepping mode (execute one inference then pause)
  - Progress tracking (completed/total count, cycle count)
- **Log Panel**: New component for real-time log viewing
  - Auto-scroll, level filtering, flow_index highlighting
  - Collapsible panel, clear logs
- **UI Enhancements**:
  - Current inference indicator in control bar
  - WebSocket connection status in status bar
  - Execution status colors

### v0.1.1 (December 18, 2024)
- **Graph Layout Improvements**:
  - Reversed flow direction: left-to-right (inputs → outputs)
  - Hierarchical vertical sorting by complete flow_index
  - Proper flow_index assignment for all concepts in each inference
  - Duplicate node support with alias edges for concepts appearing multiple times
  - Refactored node IDs from `{name}@{level}` to `node@{flow_index}`
- **Edge Enhancements**:
  - Added "alias" edge type with dashed styling
  - Fixed handle positions for correct arrow direction
- **Documentation**: Updated IMPLEMENTATION_JOURNAL.md with detailed layout changes

### v0.1.0 (December 18, 2024)
- Initial Phase 1 implementation
- Graph visualization with React Flow
- Custom nodes with status indicators
- WebSocket connection infrastructure
- Repository loading
- Detail panel for node inspection
- Control bar UI (buttons only, not wired to execution)

---

## References

- Implementation Plan: `documentation/current/updated/5_tools/implementation_plan.md`
- NormCode Documentation: `documentation/current/updated/README_MAIN.md`
- Existing Streamlit App: `streamlit_app/`
- Existing Editor App: `editor_app/`
- Orchestrator: `infra/_orchest/_orchestrator.py`
- Repository Classes: `infra/_orchest/_repo.py`
