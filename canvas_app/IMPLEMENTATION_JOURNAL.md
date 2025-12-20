# NormCode Canvas Tool - Implementation Journal

**Project Start**: December 18, 2024  
**Current Phase**: Phase 4 - Modification & Re-run  
**Status**: ✅ Phase 3 Complete (Phase 1 ✅ Phase 2 ✅ Phase 3 ✅ Phase 4 🔄 In Progress)

---

## December 20, 2024 - Restart/Reset Fix (Fresh Orchestrator)

### Problem

The reset/restart functionality was not working properly because:
1. The existing `restart()` method tried to reset the orchestrator's blackboard in-place
2. The orchestrator's internal state (SQLite database, blackboard, waitlist) was not fully resettable
3. The `blackboard.reset()` method might not exist or might not fully reset all state
4. Concept references that were computed during execution remained in memory

### Solution

Implemented a **complete orchestrator reload** on restart:
1. Store the original load configuration (`_load_config`) when `load_repositories()` is called
2. On `restart()`, call `load_repositories()` again with the same configuration
3. This creates a **completely new orchestrator** with:
   - A new `run_id` 
   - Fresh blackboard and waitlist
   - Clean concept references
   - Fresh database state
4. Preserve breakpoints across restart (they should persist)

### Files Modified

**Backend**:
- `canvas_app/backend/services/execution_service.py`:
  - Added `_load_config: Optional[Dict[str, Any]]` field to `ExecutionController`
  - Store configuration in `load_repositories()` for later use
  - Rewrote `restart()` to reload repositories completely instead of trying to reset in-place
  - Preserve breakpoints across restart
  - Emit new `run_id` in `execution:reset` event

**Frontend**:
- `canvas_app/frontend/src/hooks/useWebSocket.ts`:
  - Updated `execution:reset` handler to also update `run_id` when present
  - Clear step progress on reset for fresh start
  - Log message shows new run_id when available

### Technical Details

**Before (problematic)**:
```python
async def restart(self):
    # Tried to reset blackboard in-place
    await asyncio.to_thread(self.orchestrator.blackboard.reset)  # Often fails
    # Same orchestrator, same run_id, same database state
```

**After (fixed)**:
```python
async def restart(self):
    # Reload everything with fresh orchestrator
    result = await self.load_repositories(**self._load_config)
    # New orchestrator, new run_id, fresh state
    new_run_id = result.get("run_id", "unknown")
```

### Testing

To test the fix:
1. Load a project and run execution to completion
2. Click "Reset" button
3. Verify: New run_id is logged
4. Verify: All nodes show "pending" status
5. Click "Run" - execution should start fresh from the beginning

---

## December 20, 2024 - Canvas Performance Optimization

### What Was Implemented

**Major Performance Improvements**
Resolved significant performance issues causing laggy canvas interactions with large graphs.

**Root Causes Identified**:
1. Each node (75+) had ~10 separate Zustand store subscriptions = 750+ subscriptions
2. All nodes subscribed to entire `nodeStatuses` object - any change re-rendered ALL nodes
3. Store selector functions computed values on every render without memoization
4. CSS `transition-all` on nodes caused GPU overhead during pan/zoom

**Optimizations Applied**:

- [x] **Batched store subscriptions**: Reduced from ~10 subscriptions per node to 2 using shallow comparison
- [x] **Selective status subscription**: Nodes now only re-render when THEIR status changes, not any status
- [x] **Custom `useNodeGraphState` hook**: Batches all graph-related state for a node into one subscription
- [x] **Memoized className computation**: Prevents recalculation during pan/zoom
- [x] **Removed CSS transitions**: Eliminated `transition-all duration-200` from nodes
- [x] **Optimized GraphCanvas subscriptions**: Batched related state with shallow comparison
- [x] **React Flow performance options**: Disabled node dragging, selection box for smoother pan/zoom
- [x] **MiniMap optimization**: Disabled pannable/zoomable for reduced update frequency

### Files Modified

**Frontend**:
- `canvas_app/frontend/src/components/graph/ValueNode.tsx`:
  - Single batched execution store selector with shallow comparison
  - New `useNodeGraphState` hook for graph state
  - Memoized className computation
  - Removed CSS transitions
- `canvas_app/frontend/src/components/graph/FunctionNode.tsx`:
  - Same optimizations as ValueNode
- `canvas_app/frontend/src/components/graph/GraphCanvas.tsx`:
  - Batched store subscriptions with shallow comparison
  - Extracted store actions into single subscription
  - Added React Flow performance options
  - Optimized MiniMap settings
- `canvas_app/frontend/src/stores/graphStore.ts`:
  - New `useNodeGraphState()` custom hook for node components
  - Optimized selector pattern with shallow comparison
- `canvas_app/frontend/src/types/graph.ts`:
  - Added missing `alias` to EdgeType
  - Added `natural_name` and `concept_name` to node data interface

### Technical Details

**Before**: Each node subscribed individually:
```tsx
// 10+ subscriptions per node = 750+ total for 75 nodes
const nodeStatuses = useExecutionStore((s) => s.nodeStatuses);  // ALL statuses
const isCollapsed = useGraphStore((s) => s.isCollapsed(id));    // Computed on every render
const hasChildren = useGraphStore((s) => s.hasChildren(id));    // Iterates edges every time
// ... 7 more subscriptions
```

**After**: Batched subscriptions with shallow comparison:
```tsx
// 2 subscriptions per node with shallow comparison
const { status, hasBreakpoint } = useExecutionStore(
  useCallback((s) => ({
    status: data.flowIndex ? s.nodeStatuses[data.flowIndex] : 'pending',
    hasBreakpoint: data.flowIndex ? s.breakpoints.has(data.flowIndex) : false,
  }), [data.flowIndex]),
  shallow  // Only re-render when values actually change
);

const { isCollapsed, hasChildren, ... } = useNodeGraphState(id);  // Batched hook
```

### Performance Impact

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Subscriptions per node | ~10 | 2 | 80% reduction |
| Total subscriptions (75 nodes) | ~750 | ~150 | 80% reduction |
| Re-renders on status change | All nodes | 1 node | 98% reduction |
| CSS transitions during pan/zoom | Active | Disabled | Smoother UX |

---

## December 20, 2024 - Detail Panel UX Improvements

### What Was Implemented

**Fullscreen Detail Panel**
The node details panel can now be expanded to fullscreen for detailed inspection.

- [x] **Fullscreen toggle button**: Maximize/Minimize icons in panel header
- [x] **Two-column layout in fullscreen**: Left column for metadata, right column for data/reference
- [x] **Backdrop click to close**: Clicking outside the panel exits fullscreen
- [x] **Larger text and spacing**: Better readability in fullscreen mode

**Compact Panel Redesign**
The normal panel view has been redesigned to reduce clutter.

- [x] **Compact header**: Combined Identity + Status into single section with inline badges
- [x] **Collapsible sections**: All sections use `<details>` for expand/collapse
  - Pipeline section (shows current step in header)
  - Axes section (shows count in header)
  - Function section (shows sequence type in header)
  - Connections section (shows "X in, Y out" in header)
  - Data section (shows item count when loaded)
- [x] **Reduced spacing**: Smaller padding and margins throughout
- [x] **Inline debugging buttons**: BP and Run To buttons on same row as badges

**Enhanced Connections Section**
Connections now show more information and are navigable.

- [x] **Clickable node links**: Click any connection to navigate to that node
- [x] **Branch highlighting**: Clicking a connection highlights its branch in the graph
- [x] **Edge type badges**: Color-coded badges (fn/val/ctx/alias)
- [x] **Natural names**: Shows human-readable names when available

**Layout Button Rename**
- [x] Changed "Hierarchical" to "Compact" in layout selector

### Files Modified

**Frontend**:
- `canvas_app/frontend/src/components/panels/DetailPanel.tsx`:
  - Added fullscreen support with `isFullscreen` and `onToggleFullscreen` props
  - Redesigned to use collapsible `<details>` sections
  - Added `navigateToNode()` helper that calls both `setSelectedNode` and `highlightBranch`
  - Compact badge-based status display
  - Edge type badges in connections
- `canvas_app/frontend/src/App.tsx`:
  - Added `detailPanelFullscreen` state
  - Conditional rendering for normal vs fullscreen panel
- `canvas_app/frontend/src/components/graph/GraphCanvas.tsx`:
  - Renamed "Hierarchical" to "Compact" in layout button

### UI Flow

**Normal Mode**:
```
┌──────────────────────────────────┐
│ Node Details              [⤢][×]│
├──────────────────────────────────┤
│ signal status (信号状态)         │
│ <signal status>                  │
│ [completed][value][1.9.2][Ground]│
│ [+BP] [Run To]                   │
├──────────────────────────────────┤
│ ▶ Pipeline (grouping)            │
│ ▶ Connections (2 in, 1 out)      │
│ ▼ Data (7 items)                 │
│   [tensor viewer]                │
└──────────────────────────────────┘
```

**Fullscreen Mode**:
```
┌─────────────────────────────────────────────────────────┐
│ Node Details - <signal status>                   [⤡][×]│
├───────────────────────────┬─────────────────────────────┤
│ Identity & Status         │ Reference Data              │
│ Pipeline                  │ [Full Tensor Inspector]     │
│ Function Details          │                             │
│ Connections               │                             │
└───────────────────────────┴─────────────────────────────┘
```

---

## December 20, 2024 - Natural Name Display Enhancement

### What Was Implemented

**Natural Name Support**
Nodes now display `natural_name` from the concept repository when available, providing human-readable labels instead of technical concept names.

- [x] **Backend `graph_service.py`**: Added `natural_name` to node data for all node types (target, function, value, context)
- [x] **Frontend `GraphCanvas.tsx`**: Passes `naturalName` to node components
- [x] **Frontend `ValueNode.tsx`**:
  - Prioritizes `natural_name` as the display label
  - Shows concept name as secondary label when natural_name is used
  - Uses regular font for natural name, monospace for concept ID
  - Tooltip shows both names
- [x] **Frontend `FunctionNode.tsx`**: Same display logic as ValueNode
- [x] **Frontend `DetailPanel.tsx`**:
  - Shows "Name" with natural_name when available
  - Shows "Concept ID" with technical name as secondary
  - Maintains backwards compatibility when natural_name is absent

### Display Logic

When `natural_name` exists:
```
┌─────────────────────────┐
│  investment decision    │  ← natural_name (readable)
│  {investment_decision}  │  ← concept_name (technical, smaller)
└─────────────────────────┘
```

When only `concept_name` exists:
```
┌─────────────────────────┐
│  {investment_decision}  │  ← concept_name (monospace)
└─────────────────────────┘
```

### Files Modified

**Backend**:
- `canvas_app/backend/services/graph_service.py` - Added `natural_name` to all node data dicts

**Frontend**:
- `canvas_app/frontend/src/components/graph/GraphCanvas.tsx` - Pass naturalName in transform
- `canvas_app/frontend/src/components/graph/ValueNode.tsx` - Display natural_name first
- `canvas_app/frontend/src/components/graph/FunctionNode.tsx` - Display natural_name first
- `canvas_app/frontend/src/components/panels/DetailPanel.tsx` - Show both names in identity section

---

## Overview

This journal tracks the implementation progress of the NormCode Graph Canvas Tool - a visual, interactive environment for executing, debugging, and auditing NormCode plans.

**Reference**: See `documentation/current/updated/5_tools/implementation_plan.md` for the full implementation plan.

---

## Implementation Timeline

### December 19, 2024 - Phase 4: Editor Panel (NEW)

#### What Was Implemented

**NormCode Editor Panel**
A new integrated editor panel for editing `.ncd`, `.ncn`, `.ncdn`, and JSON files directly within the canvas app.

- [x] **View Mode Switcher**: Tab-based toggle between "Canvas" and "Editor" views
  - Canvas view: Graph visualization and execution (existing functionality)
  - Editor view: File browser and code editing
- [x] **Backend Editor Router (`/api/editor/`)**:
  - `GET /file` - Read file content
  - `POST /file` - Save file content
  - `POST /list` - List files in directory (non-recursive)
  - `POST /list-recursive` - List files recursively
  - `GET /validate` - Basic syntax validation
- [x] **EditorPanel Component**:
  - File browser sidebar with directory input
  - Search/filter files
  - Recursive directory scanning option
  - Format-specific icons (NCD, NCN, NCDN, JSON)
  - Code editor with monospace font
  - Save with Ctrl+S keyboard shortcut
  - Modification tracking (unsaved changes indicator)
  - Basic validation display
  - Line/character count status bar

#### Files Created

**Backend**:
- `canvas_app/backend/routers/editor_router.py` - Editor API endpoints

**Frontend**:
- `canvas_app/frontend/src/components/panels/EditorPanel.tsx` - Editor UI component

#### Files Modified

**Backend**:
- `canvas_app/backend/main.py` - Added editor router
- `canvas_app/backend/routers/__init__.py` - Added editor_router export

**Frontend**:
- `canvas_app/frontend/src/App.tsx`:
  - Added `viewMode` state ('canvas' | 'editor')
  - Added view mode tabs in header
  - Conditional rendering of EditorPanel vs Canvas
  - Panel toggles only shown in canvas mode

#### UI Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│  Header: [Logo] [Project] | [Canvas] [Editor] | [Panels] [Settings] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Canvas Mode:        │  Editor Mode:                                 │
│  ┌─────────────────┐ │  ┌──────────┬────────────────────────────┐   │
│  │   Graph Canvas  │ │  │ File     │  Code Editor               │   │
│  │                 │ │  │ Browser  │                            │   │
│  │  [Nodes/Edges]  │ │  │          │  [File Content]            │   │
│  │                 │ │  │  .ncd    │                            │   │
│  ├─────────────────┤ │  │  .ncn    │  ─────────────────────     │   │
│  │   Log Panel     │ │  │  .ncdn   │  Status: Lines | Chars     │   │
│  └─────────────────┘ │  └──────────┴────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Usage

1. Open a project in the canvas app
2. Click "Editor" tab in the header to switch to editor view
3. Enter a directory path in the file browser sidebar
4. Click "Load" to list NormCode files
5. Select a file to open it in the editor
6. Edit the file content
7. Press Ctrl+S or click "Save" to save changes
8. Switch back to "Canvas" tab to continue execution/debugging

---

### December 19, 2024 - Phase 3 Complete: Run To & Node Expansion

#### What Was Implemented

**"Run To" Feature (NEW)**
Run execution until a specific node is reached, then automatically pause. Perfect for debugging - run to a specific point and inspect state.

- [x] **Backend `run_to(flow_index)` method**: ExecutionController method that:
  - Validates target flow_index exists and is pending
  - Sets `_run_to_target` tracking field
  - Starts execution and auto-pauses when target is completed
  - Emits `execution:paused` event with `reason: "run_to_target_reached"`
- [x] **POST `/execution/run-to/{flow_index}` endpoint**: API endpoint for triggering run-to
- [x] **Frontend `executionApi.runTo()`**: API client method
- [x] **Run To button in DetailPanel**: 
  - Shows for pending nodes when not running
  - Loading state while executing
  - Calls API and updates UI

**Enhanced Node Expansion (NEW)**
Function nodes now show detailed working interpretation information with color-coded sections.

- [x] **Paradigm Display**: Purple box showing paradigm name (e.g., `h_Data-c_PassThrough-o_Normal`)
- [x] **Value Order Display**: Blue box showing input value mapping with concept names and positions
- [x] **Prompt Location Display**: Green box showing prompt file path when applicable
- [x] **Output Type Display**: Orange box showing expected output type
- [x] **Other Properties**: Collapsible section for any additional working interpretation fields
- [x] **Value Node Details**: Simplified view showing axes for value nodes

#### Files Modified

**Backend**:
- `canvas_app/backend/services/execution_service.py`:
  - Added `_run_to_target` field to ExecutionController
  - Added `run_to(flow_index)` async method
  - Updated `_run_cycle_with_events()` to check and pause at run-to target
  - Updated `restart()` to clear run-to target
- `canvas_app/backend/routers/execution_router.py`:
  - Added `POST /execution/run-to/{flow_index}` endpoint

**Frontend**:
- `canvas_app/frontend/src/services/api.ts`:
  - Added `runTo(flowIndex)` method to executionApi
- `canvas_app/frontend/src/components/panels/DetailPanel.tsx`:
  - Wired up Run To button with loading state
  - Added enhanced Function Details section with parsed working interpretation
  - Added color-coded displays for paradigm, value_order, prompt_location, output_type
  - Added collapsible "Other Properties" section

#### Technical Notes

**Run To Flow**:
```
User clicks "Run To" on a pending node
    ↓ handleRunTo()
executionApi.runTo(flow_index)
    ↓ POST /execution/run-to/{flow_index}
execution_controller.run_to(flow_index)
    ↓ Sets _run_to_target, starts execution
_run_loop() → _run_cycle_with_events()
    ↓ Executes inferences one by one
When flow_index == _run_to_target after completion:
    ↓ Auto-pause, emit execution:paused
UI receives event, updates to paused state
```

**Working Interpretation Display**:
The working_interpretation object typically contains:
- `paradigm`: The execution paradigm (e.g., `h_PromptTemplate-c_GenerateJson-o_List`)
- `value_order`: Mapping of input concept names to their position indices
- `prompt_location`: Path to prompt template file
- `output_type`: Expected output type (e.g., `list[dict]`, `str`)
- Additional fields specific to the paradigm

---

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
| **"Run to" feature** | ✅ Working | Run until specific node, then pause |
| **Node expansion (detailed view)** | ✅ Working | Enhanced function node details with working interpretation |
| **Editor panel** | ✅ Working | Integrated file editor for .ncd/.ncn/.ncdn files |
| **View mode switcher** | ✅ Working | Tab-based toggle between Canvas and Editor views |
| **Natural name display** | ✅ Working | Shows human-readable names from concept repo |
| **Fullscreen detail panel** | ✅ Working | Expand node details to fullscreen with two-column layout |
| **Collapsible panel sections** | ✅ Working | Compact UI with expand/collapse for each section |
| **Clickable connections** | ✅ Working | Navigate to connected nodes with branch highlighting |

### What's Not Yet Working

| Feature | Status | Phase |
| Value override | ❌ Not started | Phase 4 |
| Function modification | ❌ Not started | Phase 4 |
| Selective re-run | ❌ Not started | Phase 4 |
| Run comparison | ❌ Not started | Phase 4 |

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

### Phase 3: Debugging Features ✅ COMPLETE

**Goals**:
1. ✅ Tensor data inspection in detail panel
2. ✅ Per-node log filtering in log panel
3. ✅ Node expansion with detailed execution info
4. ✅ Reference data viewer
5. ✅ "Run to" feature

**Completed Tasks**:
- [x] Add `TensorInspector` component for multi-dimensional data viewing
- [x] Port tensor slicing utilities from Streamlit app (tensorUtils.ts)
- [x] Add log filtering by selected node
- [x] Add reference data API endpoints
- [x] Integrate TensorInspector into DetailPanel
- [x] Add "Run to" feature (run until specific node)
- [x] Add expanded node view with working interpretation details
- [x] Enhanced function node display with paradigm, value_order, prompt_location

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

### v0.6.2 (December 20, 2024) - Detail Panel UX Improvements
- **Fullscreen Detail Panel**:
  - Expand button to view node details in fullscreen overlay
  - Two-column layout: metadata on left, data/reference on right
  - Backdrop click to exit fullscreen
  - Larger text and spacing for readability
- **Compact Panel Redesign**:
  - Combined Identity + Status into single compact header with inline badges
  - All sections now collapsible using `<details>` elements
  - Reduced padding and spacing throughout
  - Inline debugging buttons (BP, Run To)
- **Enhanced Connections**:
  - Clickable node links that navigate to connected nodes
  - Branch highlighting when clicking connections
  - Color-coded edge type badges (fn/val/ctx/alias)
  - Shows natural names when available
- **Natural Name Display**:
  - Nodes show human-readable `natural_name` from concept repo
  - Technical concept ID shown as secondary label
- **Layout Rename**: "Hierarchical" → "Compact"

### v0.6.1 (December 19, 2024) - Editor Parsing & Preview
- **Parser Integration**:
  - Integrated unified_parser from streamlit_app/editor_subapp
  - Backend ParserService wrapping the parser
  - Auto-loads files from project directory on mount
- **View Mode Toggle** (Raw/Parsed/Preview):
  - Raw: Standard text editing
  - Parsed: Structured view with flow indices table
  - Preview: Multi-format preview tabs (NCD, NCN, NCDN, JSON, NCI)
- **New API Endpoints**:
  - `POST /api/editor/parse` - Parse content to structured JSON
  - `POST /api/editor/convert` - Convert between formats
  - `POST /api/editor/preview` - Get all format previews
  - `GET /api/editor/parser-status` - Check parser availability
- **New Files**:
  - `backend/services/parser_service.py` - Parser service wrapper

### v0.6.0 (December 19, 2024) - Phase 4: Editor Panel
- **Integrated Editor View**:
  - New "Editor" tab alongside "Canvas" in the header
  - View mode switcher with persistent state
  - Full file browser with directory scanning
  - Recursive file search option
  - Format-specific icons for NCD, NCN, NCDN, JSON files
- **Editor Features**:
  - Load and edit NormCode files directly
  - Save with Ctrl+S keyboard shortcut
  - Modification tracking (unsaved changes indicator)
  - Basic syntax validation
  - Line/character count in status bar
  - Search/filter files in browser
- **New API Endpoints**:
  - `GET /api/editor/file` - Read file content
  - `POST /api/editor/file` - Save file content
  - `POST /api/editor/list` - List files in directory
  - `POST /api/editor/list-recursive` - List files recursively
  - `GET /api/editor/validate` - Basic file validation
- **New Files**:
  - `backend/routers/editor_router.py` - Editor API
  - `frontend/src/components/panels/EditorPanel.tsx` - Editor UI

### v0.5.0 (December 19, 2024) - Phase 3 Complete: Run To & Node Expansion
- **"Run To" Feature**:
  - Run execution until a specific node is reached, then auto-pause
  - `POST /execution/run-to/{flow_index}` API endpoint
  - Run To button in DetailPanel for pending nodes
  - Emits `execution:paused` with `reason: "run_to_target_reached"`
- **Enhanced Node Expansion**:
  - Function nodes now show detailed working interpretation
  - Color-coded sections: Paradigm (purple), Value Order (blue), Prompt Location (green), Output Type (orange)
  - Collapsible "Other Properties" for additional fields
  - Cleaner Value Node details view
- **Phase 3 Complete**: All debugging features now implemented

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
