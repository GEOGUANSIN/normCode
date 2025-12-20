# Checkpoint/Resume/Fork Feature - Implementation Plan

**Feature Goal**: Enable users to resume execution from checkpoints instead of starting fresh every time.

**Date**: December 20, 2024  
**Status**: Planning

---

## 1. Background

### 1.1 Current State

The canvas app currently:
- ✅ Creates checkpoints automatically (via `Orchestrator.db_path`)
- ✅ Stores checkpoints in SQLite database
- ❌ Never loads or uses existing checkpoints
- ❌ Always starts fresh with `Orchestrator(...)`

### 1.2 Available Infrastructure (Already Implemented in `infra/`)

| Component | Location | Purpose |
|-----------|----------|---------|
| `OrchestratorDB` | `infra/_orchest/_db.py` | SQLite storage for runs, checkpoints, logs |
| `CheckpointManager` | `infra/_orchest/_checkpoint.py` | Save/load/reconcile checkpoint state |
| `Orchestrator.load_checkpoint()` | `infra/_orchest/_orchestrator.py` | Class method to create orchestrator from checkpoint |
| `Orchestrator.list_available_checkpoints()` | `infra/_orchest/_orchestrator.py` | Static method to list checkpoints |

### 1.3 Three Execution Modes

| Mode | Method | Behavior |
|------|--------|----------|
| **Fresh** | `Orchestrator(...)` | New run, new run_id, starts from scratch |
| **Resume** | `Orchestrator.load_checkpoint(run_id=X)` | Same run_id, continue history |
| **Fork** | `Orchestrator.load_checkpoint(run_id=X, new_run_id=Y)` | New run_id, inherits state, fresh history |

### 1.4 Reconciliation Modes (for Resume/Fork)

| Mode | Description | Use Case |
|------|-------------|----------|
| **PATCH** | Smart merge - detect changed logic via signatures, re-run stale nodes | Default, safest |
| **OVERWRITE** | Trust checkpoint 100%, ignore repo changes | When you know repos haven't changed |
| **FILL_GAPS** | Only fill missing values, prefer new repo defaults | Rare, for partial merges |

---

## 2. User Stories

### 2.1 Resume After Browser Close
> As a user, when I close my browser mid-execution and reopen the project,
> I want to continue from where I left off without re-running completed nodes.

**Flow**:
1. Open project with existing `orchestration.db`
2. System detects previous run(s)
3. User sees "Previous run found: X/Y nodes complete"
4. User clicks "Resume" 
5. Execution continues from last checkpoint

### 2.2 Fork to Experiment
> As a user, when I want to try a different approach,
> I want to fork from a previous run so I don't lose my work.

**Flow**:
1. User has completed run `run-001`
2. User edits a prompt or paradigm
3. User clicks "Fork" to create `run-002`
4. PATCH mode detects changed nodes, only re-runs those
5. Both runs preserved for comparison

### 2.3 Compare Runs
> As a user, after forking and running,
> I want to compare results between the original and forked run.

**Flow**:
1. User selects two runs from history
2. System shows side-by-side diff of final concepts
3. User can see which changes improved/worsened results

### 2.4 Time Travel / Rollback
> As a user, when execution went wrong at some point,
> I want to go back to an earlier checkpoint and try again.

**Flow**:
1. User sees run completed but with errors
2. User browses checkpoints: cycle 1, 2, 3...
3. User selects "Fork from cycle 2"
4. New run starts from that checkpoint state

---

## 3. Technical Design

### 3.1 Backend Changes

#### 3.1.1 ExecutionController New Methods

```python
# File: canvas_app/backend/services/execution_service.py

class ExecutionController:
    # ... existing code ...
    
    # NEW: List all runs in database
    def list_runs(self, db_path: str) -> List[Dict[str, Any]]:
        """List all runs stored in the database.
        
        Returns:
            List of run dicts with: run_id, first_execution, last_execution, 
            execution_count, max_cycle, config (if include_metadata)
        """
        pass
    
    # NEW: List checkpoints for a specific run
    def list_checkpoints(self, db_path: str, run_id: str) -> List[Dict[str, Any]]:
        """List all checkpoints for a run.
        
        Returns:
            List of checkpoint dicts with: cycle, inference_count, timestamp
        """
        pass
    
    # NEW: Get run metadata
    def get_run_metadata(self, db_path: str, run_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a run (LLM model, base_dir, etc.)."""
        pass
    
    # NEW: Resume from checkpoint
    async def resume_from_checkpoint(
        self,
        concepts_path: str,
        inferences_path: str,
        inputs_path: Optional[str],
        db_path: str,
        run_id: str,
        cycle: Optional[int] = None,  # None = latest
        inference_count: Optional[int] = None,
        mode: str = "PATCH",  # PATCH | OVERWRITE | FILL_GAPS
        llm_model: str = "demo",
        base_dir: Optional[str] = None,
        max_cycles: int = 50,
        paradigm_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Resume execution from an existing checkpoint.
        
        Uses the same run_id - continues execution history.
        """
        pass
    
    # NEW: Fork from checkpoint
    async def fork_from_checkpoint(
        self,
        concepts_path: str,
        inferences_path: str,
        inputs_path: Optional[str],
        db_path: str,
        source_run_id: str,
        new_run_id: Optional[str] = None,  # None = auto-generate
        cycle: Optional[int] = None,
        inference_count: Optional[int] = None,
        mode: str = "PATCH",
        llm_model: str = "demo",
        base_dir: Optional[str] = None,
        max_cycles: int = 50,
        paradigm_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fork from an existing checkpoint with a new run_id.
        
        Creates new run history while inheriting checkpoint state.
        """
        pass
```

#### 3.1.2 New API Endpoints

```python
# File: canvas_app/backend/routers/execution_router.py

# List all runs in database
@router.get("/runs")
async def list_runs(db_path: str = Query(...)) -> List[RunInfo]:
    """List all runs stored in the checkpoint database."""
    pass

# List checkpoints for a run
@router.get("/runs/{run_id}/checkpoints")
async def list_run_checkpoints(run_id: str, db_path: str = Query(...)) -> List[CheckpointInfo]:
    """List all checkpoints for a specific run."""
    pass

# Get run metadata
@router.get("/runs/{run_id}/metadata")
async def get_run_metadata(run_id: str, db_path: str = Query(...)) -> RunMetadata:
    """Get metadata for a run (config used, etc.)."""
    pass

# Resume from checkpoint
@router.post("/resume")
async def resume_execution(request: ResumeRequest) -> LoadResult:
    """Resume execution from an existing checkpoint."""
    pass

# Fork from checkpoint
@router.post("/fork")
async def fork_execution(request: ForkRequest) -> LoadResult:
    """Fork from an existing checkpoint with new run_id."""
    pass
```

#### 3.1.3 New Schema Definitions

```python
# File: canvas_app/backend/schemas/execution_schemas.py

class RunInfo(BaseModel):
    """Information about a stored run."""
    run_id: str
    first_execution: Optional[str]  # ISO timestamp
    last_execution: Optional[str]   # ISO timestamp
    execution_count: int
    max_cycle: int
    config: Optional[Dict[str, Any]] = None  # From run_metadata

class CheckpointInfo(BaseModel):
    """Information about a checkpoint."""
    cycle: int
    inference_count: int
    timestamp: str

class RunMetadata(BaseModel):
    """Metadata for a run."""
    run_id: str
    llm_model: Optional[str]
    base_dir: Optional[str]
    max_cycles: Optional[int]
    paradigm_dir: Optional[str]
    # ... other config fields

class ResumeRequest(BaseModel):
    """Request to resume from checkpoint."""
    concepts_path: str
    inferences_path: str
    inputs_path: Optional[str] = None
    db_path: str
    run_id: str
    cycle: Optional[int] = None  # None = latest checkpoint
    inference_count: Optional[int] = None
    mode: str = "PATCH"
    llm_model: str = "demo"
    base_dir: Optional[str] = None
    max_cycles: int = 50
    paradigm_dir: Optional[str] = None

class ForkRequest(BaseModel):
    """Request to fork from checkpoint."""
    concepts_path: str
    inferences_path: str
    inputs_path: Optional[str] = None
    db_path: str
    source_run_id: str
    new_run_id: Optional[str] = None  # Auto-generate if None
    cycle: Optional[int] = None
    inference_count: Optional[int] = None
    mode: str = "PATCH"
    llm_model: str = "demo"
    base_dir: Optional[str] = None
    max_cycles: int = 50
    paradigm_dir: Optional[str] = None
```

### 3.2 Frontend Changes

#### 3.2.1 New API Service Methods

```typescript
// File: canvas_app/frontend/src/services/api.ts

export const executionApi = {
    // ... existing methods ...
    
    // NEW: List runs
    listRuns: async (dbPath: string): Promise<RunInfo[]> => {
        const response = await fetch(`/api/execution/runs?db_path=${encodeURIComponent(dbPath)}`);
        return response.json();
    },
    
    // NEW: List checkpoints
    listCheckpoints: async (runId: string, dbPath: string): Promise<CheckpointInfo[]> => {
        const response = await fetch(`/api/execution/runs/${runId}/checkpoints?db_path=${encodeURIComponent(dbPath)}`);
        return response.json();
    },
    
    // NEW: Get run metadata
    getRunMetadata: async (runId: string, dbPath: string): Promise<RunMetadata> => {
        const response = await fetch(`/api/execution/runs/${runId}/metadata?db_path=${encodeURIComponent(dbPath)}`);
        return response.json();
    },
    
    // NEW: Resume from checkpoint
    resume: async (request: ResumeRequest): Promise<LoadResult> => {
        const response = await fetch('/api/execution/resume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });
        return response.json();
    },
    
    // NEW: Fork from checkpoint
    fork: async (request: ForkRequest): Promise<LoadResult> => {
        const response = await fetch('/api/execution/fork', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request)
        });
        return response.json();
    }
};
```

#### 3.2.2 New Types

```typescript
// File: canvas_app/frontend/src/types/execution.ts

export interface RunInfo {
    run_id: string;
    first_execution: string | null;
    last_execution: string | null;
    execution_count: number;
    max_cycle: number;
    config?: Record<string, any>;
}

export interface CheckpointInfo {
    cycle: number;
    inference_count: number;
    timestamp: string;
}

export interface RunMetadata {
    run_id: string;
    llm_model?: string;
    base_dir?: string;
    max_cycles?: number;
    paradigm_dir?: string;
}

export interface ResumeRequest {
    concepts_path: string;
    inferences_path: string;
    inputs_path?: string;
    db_path: string;
    run_id: string;
    cycle?: number;
    inference_count?: number;
    mode?: 'PATCH' | 'OVERWRITE' | 'FILL_GAPS';
    llm_model?: string;
    base_dir?: string;
    max_cycles?: number;
    paradigm_dir?: string;
}

export interface ForkRequest extends Omit<ResumeRequest, 'run_id'> {
    source_run_id: string;
    new_run_id?: string;
}
```

#### 3.2.3 New UI Components

**Option A: Integrated into LoadPanel**
- Add "Execution Mode" selector: Fresh / Resume / Fork
- When Resume/Fork selected, show run picker
- Show checkpoint picker for time-travel

**Option B: Separate RunHistoryPanel**
- New collapsible panel showing run history
- Each run shows: run_id, timestamp, progress, config
- Actions: Resume, Fork, Delete, Compare

**Recommendation**: Start with Option A (simpler), add B later if needed.

```tsx
// File: canvas_app/frontend/src/components/panels/LoadPanel.tsx (modified)

// Add to LoadPanel:
// 1. ExecutionMode selector (Fresh | Resume | Fork)
// 2. RunSelector (when mode !== Fresh)
// 3. CheckpointSelector (optional, for time-travel)
// 4. ReconciliationMode selector (PATCH | OVERWRITE | FILL_GAPS)
```

### 3.3 Project Integration

When a project is opened, the canvas app should:

1. Check if `orchestration.db` exists in project directory
2. If yes, query for existing runs
3. Show user option to Resume/Fork or Start Fresh
4. Remember user's choice in project config

```typescript
// Enhanced project loading flow:
async function loadProject(projectPath: string) {
    // 1. Load project config
    const config = await projectApi.open(projectPath);
    
    // 2. Check for existing runs
    const dbPath = config.execution?.db_path || 'orchestration.db';
    const fullDbPath = path.join(projectPath, dbPath);
    
    if (await fileExists(fullDbPath)) {
        const runs = await executionApi.listRuns(fullDbPath);
        
        if (runs.length > 0) {
            // Show "Previous run found" dialog
            const latestRun = runs[0];
            showResumeDialog(latestRun);
        }
    }
}
```

---

## 4. Implementation Order

### Phase A: Backend Foundation (Day 1)

| # | Task | File(s) | Effort |
|---|------|---------|--------|
| A1 | Add `list_runs()` method | `execution_service.py` | 30min |
| A2 | Add `list_checkpoints()` method | `execution_service.py` | 30min |
| A3 | Add `get_run_metadata()` method | `execution_service.py` | 20min |
| A4 | Add `resume_from_checkpoint()` method | `execution_service.py` | 1.5h |
| A5 | Add `fork_from_checkpoint()` method | `execution_service.py` | 1h |
| A6 | Add new schemas | `execution_schemas.py` | 30min |
| A7 | Add new API endpoints | `execution_router.py` | 1h |

**Deliverable**: Backend API complete, testable via Swagger UI

### Phase B: Frontend Integration (Day 2)

| # | Task | File(s) | Effort |
|---|------|---------|--------|
| B1 | Add new types | `types/execution.ts` | 20min |
| B2 | Add API service methods | `services/api.ts` | 30min |
| B3 | Add ExecutionMode to LoadPanel | `panels/LoadPanel.tsx` | 1h |
| B4 | Add RunSelector component | `panels/LoadPanel.tsx` | 1h |
| B5 | Add CheckpointSelector (optional) | `panels/LoadPanel.tsx` | 1h |
| B6 | Wire up resume/fork flow | `panels/LoadPanel.tsx` | 1h |
| B7 | Update ControlPanel for run info | `panels/ControlPanel.tsx` | 30min |

**Deliverable**: UI for resume/fork, end-to-end flow working

### Phase C: Project Integration (Day 2-3)

| # | Task | File(s) | Effort |
|---|------|---------|--------|
| C1 | Detect existing runs on project load | `projectStore.ts` | 1h |
| C2 | Show resume dialog on project open | `ProjectPanel.tsx` | 1h |
| C3 | Save last run_id in project config | `project_service.py` | 30min |
| C4 | Auto-suggest resume on page refresh | `App.tsx` | 1h |

**Deliverable**: Seamless resume experience on project open

### Phase D: Polish (Day 3)

| # | Task | File(s) | Effort |
|---|------|---------|--------|
| D1 | Show run history in detail panel | `DetailPanel.tsx` | 1h |
| D2 | Add run comparison (basic) | New component | 2h |
| D3 | Error handling and edge cases | Various | 1h |
| D4 | Update documentation | `IMPLEMENTATION_JOURNAL.md` | 30min |

---

## 5. API Specification

### 5.1 GET /api/execution/runs

List all runs in the checkpoint database.

**Query Parameters**:
- `db_path` (required): Path to orchestration.db

**Response**:
```json
{
    "runs": [
        {
            "run_id": "abc123",
            "first_execution": "2024-12-20T10:30:00",
            "last_execution": "2024-12-20T11:45:00",
            "execution_count": 45,
            "max_cycle": 3,
            "config": {
                "llm_model": "qwen-plus",
                "max_cycles": 50
            }
        }
    ]
}
```

### 5.2 GET /api/execution/runs/{run_id}/checkpoints

List checkpoints for a specific run.

**Path Parameters**:
- `run_id`: The run ID

**Query Parameters**:
- `db_path` (required): Path to orchestration.db

**Response**:
```json
{
    "checkpoints": [
        {"cycle": 1, "inference_count": 0, "timestamp": "2024-12-20T10:35:00"},
        {"cycle": 2, "inference_count": 0, "timestamp": "2024-12-20T10:40:00"},
        {"cycle": 3, "inference_count": 0, "timestamp": "2024-12-20T10:45:00"}
    ]
}
```

### 5.3 POST /api/execution/resume

Resume execution from a checkpoint.

**Request Body**:
```json
{
    "concepts_path": "/path/to/concepts.json",
    "inferences_path": "/path/to/inferences.json",
    "inputs_path": "/path/to/inputs.json",
    "db_path": "/path/to/orchestration.db",
    "run_id": "abc123",
    "cycle": null,
    "mode": "PATCH",
    "llm_model": "qwen-plus",
    "base_dir": "/path/to/project",
    "max_cycles": 50,
    "paradigm_dir": "provision/paradigm"
}
```

**Response**:
```json
{
    "success": true,
    "run_id": "abc123",
    "restored_from_cycle": 3,
    "completed_count": 12,
    "total_count": 15,
    "message": "Resumed from cycle 3 - 12/15 nodes already complete"
}
```

### 5.4 POST /api/execution/fork

Fork from a checkpoint with new run ID.

**Request Body**:
```json
{
    "concepts_path": "/path/to/concepts.json",
    "inferences_path": "/path/to/inferences.json",
    "inputs_path": "/path/to/inputs.json",
    "db_path": "/path/to/orchestration.db",
    "source_run_id": "abc123",
    "new_run_id": "experiment-v2",
    "cycle": 2,
    "mode": "PATCH",
    "llm_model": "qwen-plus",
    "base_dir": "/path/to/project",
    "max_cycles": 50
}
```

**Response**:
```json
{
    "success": true,
    "run_id": "experiment-v2",
    "forked_from": "abc123",
    "forked_from_cycle": 2,
    "completed_count": 8,
    "total_count": 15,
    "message": "Forked from abc123@cycle2 - 8/15 nodes carried over"
}
```

---

## 6. UI Mockups

### 6.1 LoadPanel with Execution Mode

```
┌─────────────────────────────────────────────────────────────┐
│ Load Repositories                                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Concepts:    [/path/to/concepts.json        ] [Browse]      │
│ Inferences:  [/path/to/inferences.json      ] [Browse]      │
│ Inputs:      [/path/to/inputs.json          ] [Browse]      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ Execution Mode                                              │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐                         │
│ │ ● Fresh │ │ ○ Resume│ │ ○ Fork  │                         │
│ └─────────┘ └─────────┘ └─────────┘                         │
│                                                             │
│ ┌─ Previous Runs ───────────────────────────────────────┐   │
│ │ ● run-abc123  Dec 20, 11:45  12/15 complete  qwen-plus│   │
│ │ ○ run-xyz789  Dec 19, 15:30  15/15 complete  gpt-4    │   │
│ │ ○ run-def456  Dec 19, 10:00   8/15 failed    qwen-plus│   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ Reconciliation: [PATCH ▼]                                   │
│                                                             │
│ ┌─ Checkpoint (optional) ───────────────────────────────┐   │
│ │ ● Latest (cycle 3)                                    │   │
│ │ ○ Cycle 2 - Dec 20, 10:40                             │   │
│ │ ○ Cycle 1 - Dec 20, 10:35                             │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│                    [Load & Resume]                          │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Resume Dialog on Project Open

```
┌─────────────────────────────────────────────────────────────┐
│                     Previous Run Found                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Your last execution was interrupted:                       │
│                                                             │
│   Run ID:    abc123                                          │
│   Progress:  12 / 15 nodes complete                          │
│   Last Run:  Dec 20, 2024 at 11:45 AM                        │
│   LLM:       qwen-plus                                       │
│                                                             │
│   Would you like to continue where you left off?             │
│                                                             │
│   ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│   │    Resume      │  │      Fork      │  │ Start Fresh  │  │
│   └────────────────┘  └────────────────┘  └──────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Control Panel with Run Info

```
┌─────────────────────────────────────────────────────────────┐
│ Execution Control                               Run: abc123 │
├─────────────────────────────────────────────────────────────┤
│ [▶ Run] [⏸ Pause] [⏹ Stop] [⏭ Step] [🔄 Restart]           │
│                                                             │
│ Progress: ████████████░░░ 12/15  Cycle: 3  Mode: Resumed    │
│                                                             │
│ Current: {investment decision} - imperative                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Edge Cases & Error Handling

### 7.1 Incompatible Repositories

**Scenario**: User tries to resume with modified repositories.

**Handling**:
- PATCH mode: Detect signature mismatches, show warning, re-run stale nodes
- OVERWRITE mode: Trust checkpoint, may fail if structure changed drastically
- Show clear error if ground concepts are missing data

### 7.2 Corrupted Database

**Scenario**: Database file is corrupted or incompatible version.

**Handling**:
- Catch SQLite errors gracefully
- Show "Database corrupted - start fresh?" dialog
- Option to backup and recreate

### 7.3 Missing Checkpoint

**Scenario**: Specified run_id or cycle doesn't exist.

**Handling**:
- Return 404 with helpful message
- Suggest available runs/checkpoints

### 7.4 Concurrent Execution

**Scenario**: Two browser tabs try to run the same project.

**Handling**:
- Check for active execution before resuming
- Warn user if run is already in progress
- Consider locking mechanism (future enhancement)

---

## 8. Testing Plan

### 8.1 Unit Tests

```python
# test_execution_service.py

def test_list_runs_empty_db():
    """Empty database returns empty list."""
    pass

def test_list_runs_with_data():
    """Database with runs returns correct list."""
    pass

def test_resume_latest_checkpoint():
    """Resume from latest checkpoint works correctly."""
    pass

def test_resume_specific_cycle():
    """Resume from specific cycle works correctly."""
    pass

def test_fork_creates_new_run():
    """Fork creates new run_id with inherited state."""
    pass

def test_patch_mode_detects_changes():
    """PATCH mode correctly identifies stale nodes."""
    pass
```

### 8.2 Integration Tests

1. **Fresh → Resume Flow**
   - Start fresh, run 5 inferences, stop
   - Resume, verify 5 nodes already complete
   - Run to completion

2. **Fork Flow**
   - Complete a run
   - Fork with modified prompt
   - Verify only affected nodes re-run

3. **Time Travel**
   - Run to cycle 3
   - Fork from cycle 1
   - Verify state matches cycle 1

### 8.3 Manual Testing

1. Browser close mid-execution → reopen → resume
2. Modify repository → resume with PATCH → verify re-runs
3. Multiple runs → compare results
4. Large plan (100+ nodes) → resume performance

---

## 9. Future Enhancements (Out of Scope)

- Run comparison UI with diff view
- Checkpoint annotations/tags
- Auto-checkpoint on pause
- Export/import checkpoints across projects
- Cloud sync of checkpoints
- Collaborative execution (multiple users)

---

## 10. Acceptance Criteria

### Must Have
- [ ] Can list previous runs from database
- [ ] Can resume from latest checkpoint
- [ ] Can fork from checkpoint with new run_id
- [ ] UI shows execution mode options
- [ ] Resumed execution skips completed nodes
- [ ] PATCH mode correctly handles repository changes

### Should Have
- [ ] Can select specific checkpoint (cycle) to resume from
- [ ] Project auto-detects previous runs on open
- [ ] Clear progress indication (X nodes restored)
- [ ] Error handling for corrupted/missing data

### Nice to Have
- [ ] Run comparison view
- [ ] Checkpoint browser with preview
- [ ] Export run history

---

## 11. References

- Orchestrator source: `infra/_orchest/_orchestrator.py`
- Checkpoint manager: `infra/_orchest/_checkpoint.py`
- Database: `infra/_orchest/_db.py`
- Streamlit implementation: `streamlit_app/orchestration/orchestration_runner.py`
- Current canvas execution: `canvas_app/backend/services/execution_service.py`

