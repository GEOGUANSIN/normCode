# Checkpoint/Resume/Fork Feature - Implementation Plan

**Feature Goal**: Enable users to resume execution from checkpoints instead of starting fresh every time.

**Date**: December 20, 2024  
**Status**: Planning (Updated)

---

## 1. Design Philosophy: Dedicated Checkpoint Panel

### 1.1 Key Insight

Instead of cramming checkpoint functionality into the LoadPanel or other existing panels, we create a **dedicated CheckpointPanel** that handles all checkpoint/resume/fork operations. This keeps concerns separate:

| Panel | Responsibility |
|-------|---------------|
| **LoadPanel** | Fresh loads - load repositories from files |
| **CheckpointPanel** | Resume/Fork - load from saved database checkpoints |
| **ControlPanel** | Execution control - run/pause/step/stop |

### 1.2 Why a Dedicated Panel?

1. **Simpler mental model**: "Checkpoint" is its own workflow, not a modification of "Load"
2. **Cleaner UI**: Each panel does one thing well
3. **Separate orchestrator per mode**: Fresh load creates new orchestrator, Resume/Fork loads from checkpoint
4. **Easier to extend**: Add comparison, history, etc. without cluttering other panels

---

## 2. User Flow

### 2.1 Fresh Start (Existing Flow)
```
Open Project → LoadPanel → Select repos → "Load Fresh" → New Orchestrator
```

### 2.2 Resume/Fork (New Flow)
```
Open Project → CheckpointPanel → See previous runs → "Resume" or "Fork" → Loaded Orchestrator
```

### 2.3 Switching Between Runs
```
During execution → CheckpointPanel → Select different run → Confirm switch → Load that run
```

---

## 3. CheckpointPanel Design

### 3.1 Panel Location

Add as a new collapsible panel in the left sidebar, similar to how SettingsPanel works:
- **Position**: Below ControlPanel, above LogPanel
- **Icon**: 📋 or 💾 or 🔄
- **Label**: "Checkpoints" or "Run History" or "Sessions"

### 3.2 Panel UI Mockup

```
┌─────────────────────────────────────────────────────────────┐
│ 📋 Checkpoints                                        [−][⟳] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Current: run-abc123 (12/15 complete)                        │
│                                                             │
│ ┌─ Previous Runs ───────────────────────────────────────┐   │
│ │ ● run-abc123  Today 11:45    12/15  qwen-plus  [●Active]│  │
│ │ ○ run-xyz789  Yesterday      15/15  gpt-4      ─────────│  │
│ │ ○ run-def456  Dec 18         8/15   qwen-plus  [Failed] │  │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ Selected: run-abc123                                        │
│ ┌─ Checkpoints ─────────────────────────────────────────┐   │
│ │ ● Latest (cycle 3, 12 complete)                       │   │
│ │ ○ Cycle 2 (8 complete)                                │   │
│ │ ○ Cycle 1 (3 complete)                                │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ Reconciliation: [PATCH ▼]  ℹ️ Smart merge - re-runs stale   │
│                                                             │
│ ┌────────────────────────────────────────────────────────┐  │
│ │                                                        │  │
│ │    [▶ Resume]                [🍴 Fork as New Run]      │  │
│ │                                                        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ⚠️ Resume continues the same run. Fork creates a new run.   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Panel States

| State | What User Sees |
|-------|---------------|
| **No DB** | "No checkpoint database found. Run execution to create checkpoints." |
| **Empty DB** | "No previous runs found. Start a fresh execution first." |
| **Has Runs** | Run list with Resume/Fork buttons |
| **Run Active** | Current run highlighted, can still browse history |

### 3.4 Panel Actions

| Button | Action | Result |
|--------|--------|--------|
| **Resume** | `POST /execution/resume` | Continues same run_id from checkpoint |
| **Fork** | `POST /execution/fork` | Creates NEW run_id, inherits state |
| **Refresh (⟳)** | Reload run list | Fetches latest from database |
| **Delete** | Remove a run | Deletes run from database (future) |

---

## 4. Technical Implementation

### 4.1 Backend Changes

#### 4.1.1 New Methods in ExecutionController

```python
# File: canvas_app/backend/services/execution_service.py

class ExecutionController:
    # ... existing code ...
    
    async def list_runs(self, db_path: str) -> List[Dict[str, Any]]:
        """List all runs stored in the checkpoint database."""
        from infra._orchest._db import OrchestratorDB
        
        db = OrchestratorDB(db_path)
        runs = db.list_runs()  # Returns list of run dicts
        db.close()
        return runs
    
    async def list_checkpoints(self, db_path: str, run_id: str) -> List[Dict[str, Any]]:
        """List all checkpoints for a specific run."""
        from infra._orchest._db import OrchestratorDB
        
        db = OrchestratorDB(db_path)
        checkpoints = db.list_checkpoints(run_id)
        db.close()
        return checkpoints
    
    async def resume_from_checkpoint(
        self,
        concepts_path: str,
        inferences_path: str,
        inputs_path: Optional[str],
        db_path: str,
        run_id: str,
        cycle: Optional[int] = None,  # None = latest
        mode: str = "PATCH",
        llm_model: str = "demo",
        base_dir: Optional[str] = None,
        max_cycles: int = 50,
        paradigm_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Resume execution from an existing checkpoint (same run_id)."""
        from infra._orchest._orchestrator import Orchestrator
        from infra._orchest._checkpoint import ReconciliationMode
        
        # Load repos
        await self._load_repos_internal(concepts_path, inferences_path, inputs_path)
        
        # Create body
        self._create_body(llm_model, base_dir, paradigm_dir)
        
        # Load from checkpoint
        recon_mode = ReconciliationMode[mode]
        self.orchestrator = await asyncio.to_thread(
            Orchestrator.load_checkpoint,
            db_path=db_path,
            run_id=run_id,
            cycle=cycle,
            concept_repo=self.concept_repo,
            inference_repo=self.inference_repo,
            body=self.body,
            max_cycles=max_cycles,
            mode=recon_mode
        )
        
        # Sync node statuses from blackboard
        self._sync_node_statuses_from_orchestrator()
        
        return {
            "success": True,
            "run_id": run_id,
            "mode": "resume",
            "completed_count": self.completed_count,
            "total_count": self.total_count,
        }
    
    async def fork_from_checkpoint(
        self,
        concepts_path: str,
        inferences_path: str,
        inputs_path: Optional[str],
        db_path: str,
        source_run_id: str,
        new_run_id: Optional[str] = None,
        cycle: Optional[int] = None,
        mode: str = "PATCH",
        llm_model: str = "demo",
        base_dir: Optional[str] = None,
        max_cycles: int = 50,
        paradigm_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fork from an existing checkpoint with a new run_id."""
        from infra._orchest._orchestrator import Orchestrator
        from infra._orchest._checkpoint import ReconciliationMode
        import uuid
        
        # Generate new run_id if not provided
        if new_run_id is None:
            new_run_id = f"fork-{str(uuid.uuid4())[:8]}"
        
        # Load repos
        await self._load_repos_internal(concepts_path, inferences_path, inputs_path)
        
        # Create body
        self._create_body(llm_model, base_dir, paradigm_dir)
        
        # Fork from checkpoint
        recon_mode = ReconciliationMode[mode]
        self.orchestrator = await asyncio.to_thread(
            Orchestrator.load_checkpoint,
            db_path=db_path,
            run_id=source_run_id,
            cycle=cycle,
            concept_repo=self.concept_repo,
            inference_repo=self.inference_repo,
            body=self.body,
            max_cycles=max_cycles,
            mode=recon_mode,
            new_run_id=new_run_id  # This makes it a fork
        )
        
        # Sync node statuses from blackboard
        self._sync_node_statuses_from_orchestrator()
        
        return {
            "success": True,
            "run_id": new_run_id,
            "forked_from": source_run_id,
            "mode": "fork",
            "completed_count": self.completed_count,
            "total_count": self.total_count,
        }
```

#### 4.1.2 New API Endpoints

```python
# File: canvas_app/backend/routers/checkpoint_router.py (NEW FILE)

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter()

class RunInfo(BaseModel):
    run_id: str
    first_execution: Optional[str] = None
    last_execution: Optional[str] = None
    execution_count: int = 0
    max_cycle: int = 0
    completed_count: Optional[int] = None
    total_count: Optional[int] = None

class CheckpointInfo(BaseModel):
    cycle: int
    inference_count: int
    timestamp: str

class ResumeRequest(BaseModel):
    concepts_path: str
    inferences_path: str
    inputs_path: Optional[str] = None
    db_path: str
    run_id: str
    cycle: Optional[int] = None
    mode: str = "PATCH"
    llm_model: str = "demo"
    base_dir: Optional[str] = None
    max_cycles: int = 50
    paradigm_dir: Optional[str] = None

class ForkRequest(BaseModel):
    concepts_path: str
    inferences_path: str
    inputs_path: Optional[str] = None
    db_path: str
    source_run_id: str
    new_run_id: Optional[str] = None
    cycle: Optional[int] = None
    mode: str = "PATCH"
    llm_model: str = "demo"
    base_dir: Optional[str] = None
    max_cycles: int = 50
    paradigm_dir: Optional[str] = None

@router.get("/runs")
async def list_runs(db_path: str = Query(...)) -> List[RunInfo]:
    """List all runs in the checkpoint database."""
    from services.execution_service import execution_controller
    runs = await execution_controller.list_runs(db_path)
    return [RunInfo(**r) for r in runs]

@router.get("/runs/{run_id}/checkpoints")
async def list_checkpoints(
    run_id: str, 
    db_path: str = Query(...)
) -> List[CheckpointInfo]:
    """List all checkpoints for a run."""
    from services.execution_service import execution_controller
    checkpoints = await execution_controller.list_checkpoints(db_path, run_id)
    return [CheckpointInfo(**c) for c in checkpoints]

@router.post("/resume")
async def resume_execution(request: ResumeRequest):
    """Resume execution from a checkpoint (same run_id)."""
    from services.execution_service import execution_controller
    result = await execution_controller.resume_from_checkpoint(
        concepts_path=request.concepts_path,
        inferences_path=request.inferences_path,
        inputs_path=request.inputs_path,
        db_path=request.db_path,
        run_id=request.run_id,
        cycle=request.cycle,
        mode=request.mode,
        llm_model=request.llm_model,
        base_dir=request.base_dir,
        max_cycles=request.max_cycles,
        paradigm_dir=request.paradigm_dir,
    )
    return result

@router.post("/fork")
async def fork_execution(request: ForkRequest):
    """Fork from a checkpoint with a new run_id."""
    from services.execution_service import execution_controller
    result = await execution_controller.fork_from_checkpoint(
        concepts_path=request.concepts_path,
        inferences_path=request.inferences_path,
        inputs_path=request.inputs_path,
        db_path=request.db_path,
        source_run_id=request.source_run_id,
        new_run_id=request.new_run_id,
        cycle=request.cycle,
        mode=request.mode,
        llm_model=request.llm_model,
        base_dir=request.base_dir,
        max_cycles=request.max_cycles,
        paradigm_dir=request.paradigm_dir,
    )
    return result
```

### 4.2 Frontend Changes

#### 4.2.1 New CheckpointPanel Component

```tsx
// File: canvas_app/frontend/src/components/panels/CheckpointPanel.tsx

import { useState, useEffect } from 'react';
import { RefreshCw, Play, GitBranch, Database, AlertCircle } from 'lucide-react';
import { checkpointApi } from '../../services/api';
import { useProjectStore } from '../../stores/projectStore';
import { useConfigStore } from '../../stores/configStore';

interface RunInfo {
  run_id: string;
  first_execution: string | null;
  last_execution: string | null;
  execution_count: number;
  max_cycle: number;
  completed_count?: number;
  total_count?: number;
}

interface CheckpointInfo {
  cycle: number;
  inference_count: number;
  timestamp: string;
}

export function CheckpointPanel() {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const [runs, setRuns] = useState<RunInfo[]>([]);
  const [checkpoints, setCheckpoints] = useState<CheckpointInfo[]>([]);
  const [selectedRun, setSelectedRun] = useState<string | null>(null);
  const [selectedCheckpoint, setSelectedCheckpoint] = useState<number | null>(null);
  const [reconciliationMode, setReconciliationMode] = useState<'PATCH' | 'OVERWRITE' | 'FILL_GAPS'>('PATCH');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { currentProject, projectPath } = useProjectStore();
  const { llmModel, maxCycles, dbPath, paradigmDir } = useConfigStore();
  
  // Get db path from project config
  const fullDbPath = projectPath 
    ? `${projectPath}/${currentProject?.execution?.db_path || 'orchestration.db'}`
    : null;
  
  // Load runs when panel opens or db path changes
  useEffect(() => {
    if (!isCollapsed && fullDbPath) {
      loadRuns();
    }
  }, [isCollapsed, fullDbPath]);
  
  // Load checkpoints when run is selected
  useEffect(() => {
    if (selectedRun && fullDbPath) {
      loadCheckpoints(selectedRun);
    }
  }, [selectedRun]);
  
  const loadRuns = async () => {
    if (!fullDbPath) return;
    setLoading(true);
    setError(null);
    try {
      const runList = await checkpointApi.listRuns(fullDbPath);
      setRuns(runList);
      if (runList.length > 0 && !selectedRun) {
        setSelectedRun(runList[0].run_id);
      }
    } catch (e: any) {
      setError(e.message || 'Failed to load runs');
    } finally {
      setLoading(false);
    }
  };
  
  const loadCheckpoints = async (runId: string) => {
    if (!fullDbPath) return;
    try {
      const cpList = await checkpointApi.listCheckpoints(runId, fullDbPath);
      setCheckpoints(cpList);
      if (cpList.length > 0) {
        setSelectedCheckpoint(cpList[0].cycle); // Default to latest
      }
    } catch (e: any) {
      console.error('Failed to load checkpoints:', e);
    }
  };
  
  const handleResume = async () => {
    if (!selectedRun || !fullDbPath || !currentProject) return;
    setLoading(true);
    try {
      await checkpointApi.resume({
        concepts_path: `${projectPath}/${currentProject.repositories.concepts}`,
        inferences_path: `${projectPath}/${currentProject.repositories.inferences}`,
        inputs_path: currentProject.repositories.inputs 
          ? `${projectPath}/${currentProject.repositories.inputs}` 
          : undefined,
        db_path: fullDbPath,
        run_id: selectedRun,
        cycle: selectedCheckpoint ?? undefined,
        mode: reconciliationMode,
        llm_model: llmModel,
        base_dir: projectPath || undefined,
        max_cycles: maxCycles,
        paradigm_dir: paradigmDir || undefined,
      });
      // Success! The execution:loaded event will update the UI
    } catch (e: any) {
      setError(e.message || 'Failed to resume');
    } finally {
      setLoading(false);
    }
  };
  
  const handleFork = async () => {
    if (!selectedRun || !fullDbPath || !currentProject) return;
    setLoading(true);
    try {
      await checkpointApi.fork({
        concepts_path: `${projectPath}/${currentProject.repositories.concepts}`,
        inferences_path: `${projectPath}/${currentProject.repositories.inferences}`,
        inputs_path: currentProject.repositories.inputs 
          ? `${projectPath}/${currentProject.repositories.inputs}` 
          : undefined,
        db_path: fullDbPath,
        source_run_id: selectedRun,
        new_run_id: undefined, // Auto-generate
        cycle: selectedCheckpoint ?? undefined,
        mode: reconciliationMode,
        llm_model: llmModel,
        base_dir: projectPath || undefined,
        max_cycles: maxCycles,
        paradigm_dir: paradigmDir || undefined,
      });
      // Success! Reload runs to show the new fork
      await loadRuns();
    } catch (e: any) {
      setError(e.message || 'Failed to fork');
    } finally {
      setLoading(false);
    }
  };
  
  const formatDate = (isoString: string | null) => {
    if (!isoString) return 'Unknown';
    const date = new Date(isoString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  if (!currentProject) {
    return null; // Don't show if no project loaded
  }
  
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Header */}
      <button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50"
      >
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-indigo-600" />
          <span className="font-medium text-gray-900">Checkpoints</span>
        </div>
        <span className="text-gray-400">{isCollapsed ? '▶' : '▼'}</span>
      </button>
      
      {/* Body */}
      {!isCollapsed && (
        <div className="px-4 pb-4 space-y-4">
          {/* Error display */}
          {error && (
            <div className="p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              {error}
            </div>
          )}
          
          {/* Refresh button */}
          <div className="flex justify-end">
            <button
              onClick={loadRuns}
              disabled={loading}
              className="p-1 hover:bg-gray-100 rounded"
              title="Refresh runs"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
          
          {/* No runs */}
          {runs.length === 0 && !loading && (
            <div className="text-center py-4 text-gray-500">
              <Database className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No previous runs found.</p>
              <p className="text-sm">Start a fresh execution first.</p>
            </div>
          )}
          
          {/* Run list */}
          {runs.length > 0 && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Previous Runs</label>
              <div className="border rounded max-h-32 overflow-y-auto">
                {runs.map((run) => (
                  <label
                    key={run.run_id}
                    className={`flex items-center gap-2 p-2 cursor-pointer hover:bg-gray-50 ${
                      selectedRun === run.run_id ? 'bg-indigo-50' : ''
                    }`}
                  >
                    <input
                      type="radio"
                      name="run"
                      checked={selectedRun === run.run_id}
                      onChange={() => setSelectedRun(run.run_id)}
                      className="text-indigo-600"
                    />
                    <div className="flex-1 text-sm">
                      <div className="font-mono">{run.run_id.slice(0, 12)}...</div>
                      <div className="text-xs text-gray-500">
                        {formatDate(run.last_execution)} • Cycle {run.max_cycle}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}
          
          {/* Checkpoint list */}
          {selectedRun && checkpoints.length > 0 && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Checkpoint</label>
              <select
                value={selectedCheckpoint ?? ''}
                onChange={(e) => setSelectedCheckpoint(e.target.value ? Number(e.target.value) : null)}
                className="w-full border rounded px-3 py-2 text-sm"
              >
                {checkpoints.map((cp) => (
                  <option key={cp.cycle} value={cp.cycle}>
                    Cycle {cp.cycle} ({cp.inference_count} inferences) - {formatDate(cp.timestamp)}
                  </option>
                ))}
              </select>
            </div>
          )}
          
          {/* Reconciliation mode */}
          {selectedRun && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-700">Reconciliation Mode</label>
              <select
                value={reconciliationMode}
                onChange={(e) => setReconciliationMode(e.target.value as any)}
                className="w-full border rounded px-3 py-2 text-sm"
              >
                <option value="PATCH">PATCH - Smart merge, re-run stale nodes</option>
                <option value="OVERWRITE">OVERWRITE - Trust checkpoint 100%</option>
                <option value="FILL_GAPS">FILL_GAPS - Only fill missing values</option>
              </select>
              <p className="text-xs text-gray-500">
                {reconciliationMode === 'PATCH' && 'Detects changed logic via signatures and re-runs affected nodes.'}
                {reconciliationMode === 'OVERWRITE' && 'Uses checkpoint as-is. Use when repos havent changed.'}
                {reconciliationMode === 'FILL_GAPS' && 'Only fills missing values, prefers new repo defaults.'}
              </p>
            </div>
          )}
          
          {/* Action buttons */}
          {selectedRun && (
            <div className="flex gap-2 pt-2">
              <button
                onClick={handleResume}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
              >
                <Play className="w-4 h-4" />
                Resume
              </button>
              <button
                onClick={handleFork}
                disabled={loading}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 disabled:opacity-50"
              >
                <GitBranch className="w-4 h-4" />
                Fork
              </button>
            </div>
          )}
          
          {/* Help text */}
          <p className="text-xs text-gray-500 text-center">
            <strong>Resume</strong> continues the same run. <strong>Fork</strong> creates a new run.
          </p>
        </div>
      )}
    </div>
  );
}
```

#### 4.2.2 New API Methods

```typescript
// File: canvas_app/frontend/src/services/api.ts (additions)

export const checkpointApi = {
  listRuns: async (dbPath: string): Promise<RunInfo[]> => {
    const response = await fetch(
      `/api/checkpoints/runs?db_path=${encodeURIComponent(dbPath)}`
    );
    if (!response.ok) throw new Error('Failed to list runs');
    return response.json();
  },
  
  listCheckpoints: async (runId: string, dbPath: string): Promise<CheckpointInfo[]> => {
    const response = await fetch(
      `/api/checkpoints/runs/${runId}/checkpoints?db_path=${encodeURIComponent(dbPath)}`
    );
    if (!response.ok) throw new Error('Failed to list checkpoints');
    return response.json();
  },
  
  resume: async (request: ResumeRequest): Promise<LoadResult> => {
    const response = await fetch('/api/checkpoints/resume', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error('Failed to resume');
    return response.json();
  },
  
  fork: async (request: ForkRequest): Promise<LoadResult> => {
    const response = await fetch('/api/checkpoints/fork', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!response.ok) throw new Error('Failed to fork');
    return response.json();
  },
};
```

---

## 5. Implementation Tasks

### Phase A: Backend (Day 1)

| # | Task | File | Effort |
|---|------|------|--------|
| A1 | Create `checkpoint_router.py` with schemas | `routers/checkpoint_router.py` | 1h |
| A2 | Add `list_runs()` to ExecutionController | `services/execution_service.py` | 30min |
| A3 | Add `list_checkpoints()` to ExecutionController | `services/execution_service.py` | 30min |
| A4 | Add `resume_from_checkpoint()` method | `services/execution_service.py` | 1.5h |
| A5 | Add `fork_from_checkpoint()` method | `services/execution_service.py` | 1h |
| A6 | Add helper `_sync_node_statuses_from_orchestrator()` | `services/execution_service.py` | 30min |
| A7 | Register router in `main.py` | `main.py` | 5min |

**Deliverable**: API endpoints working, testable in Swagger

### Phase B: Frontend (Day 2)

| # | Task | File | Effort |
|---|------|------|--------|
| B1 | Add types for checkpoint API | `types/execution.ts` | 20min |
| B2 | Add `checkpointApi` methods | `services/api.ts` | 30min |
| B3 | Create `CheckpointPanel.tsx` component | `components/panels/CheckpointPanel.tsx` | 2h |
| B4 | Integrate panel into App layout | `App.tsx` | 15min |
| B5 | Wire up WebSocket events for load status | `hooks/useWebSocket.ts` | 30min |

**Deliverable**: CheckpointPanel working end-to-end

### Phase C: Polish (Day 3)

| # | Task | File | Effort |
|---|------|------|--------|
| C1 | Show current run_id in ControlPanel | `ControlPanel.tsx` | 30min |
| C2 | Add "mode" indicator (Fresh/Resumed/Forked) | `ControlPanel.tsx` | 30min |
| C3 | Error handling for missing DB file | `CheckpointPanel.tsx` | 30min |
| C4 | Update IMPLEMENTATION_JOURNAL.md | `IMPLEMENTATION_JOURNAL.md` | 30min |

---

## 6. Key Differences from Original Plan

| Aspect | Original Plan | New Plan |
|--------|--------------|----------|
| **UI Location** | Integrated into LoadPanel | Dedicated CheckpointPanel |
| **Complexity** | Merged with fresh load flow | Separate, focused panel |
| **Panel Name** | "Load Panel" with mode tabs | "Checkpoints" panel |
| **Router** | Extended execution_router | New checkpoint_router |
| **User Mental Model** | "Load fresh OR resume" | "Fresh Load" vs "Checkpoint" |

---

## 7. Future Enhancements (Out of Scope for Now)

- **Run comparison view**: Side-by-side diff of two runs
- **Delete runs**: Remove old runs from database
- **Checkpoint annotations**: Add notes to checkpoints
- **Auto-detect on project open**: Show "Previous run found" dialog
- **Export/import**: Save runs to file for sharing

---

## 8. Acceptance Criteria

### Must Have
- [ ] CheckpointPanel shows list of previous runs
- [ ] Can select a run and see its checkpoints
- [ ] Resume button loads orchestrator from checkpoint (same run_id)
- [ ] Fork button creates new orchestrator with new run_id
- [ ] Node statuses sync correctly from restored checkpoint
- [ ] Execution can continue after resume/fork

### Should Have
- [ ] Reconciliation mode selector (PATCH/OVERWRITE/FILL_GAPS)
- [ ] Clear error messages for failures
- [ ] Loading states for async operations

### Nice to Have
- [ ] Current run highlighted in list
- [ ] "Mode" badge in ControlPanel (Fresh/Resumed/Forked)
- [ ] Keyboard shortcut to open panel

---

## 9. References

- Orchestrator checkpoint loading: `infra/_orchest/_orchestrator.py` → `load_checkpoint()`
- Reconciliation modes: `infra/_orchest/_checkpoint.py` → `ReconciliationMode`
- Database schema: `infra/_orchest/_db.py` → `OrchestratorDB`
- Streamlit implementation: `streamlit_app/orchestration/orchestration_runner.py`
