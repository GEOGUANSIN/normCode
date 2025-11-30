# NormCode Orchestrator App - Architecture

This document describes the architecture of the minimal Streamlit orchestrator app.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Web App                        │
│                        (app.py)                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Execute    │  │   Results    │  │   History    │    │
│  │     Tab      │  │     Tab      │  │     Tab      │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                  │                  │            │
│         └──────────────────┴──────────────────┘            │
│                           │                                │
└───────────────────────────┼────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │       infra._orchest Module           │
        ├───────────────────────────────────────┤
        │                                       │
        │  ┌─────────────────────────────┐    │
        │  │      Orchestrator           │    │
        │  │   (Main Execution Engine)   │    │
        │  └────────┬────────────────────┘    │
        │           │                          │
        │  ┌────────▼─────────┐  ┌──────────┐ │
        │  │   ConceptRepo    │  │  Body    │ │
        │  │  InferenceRepo   │  │  (LLM)   │ │
        │  └──────────────────┘  └──────────┘ │
        │                                      │
        │  ┌────────────────┐  ┌────────────┐ │
        │  │  Blackboard    │  │  Tracker   │ │
        │  │  (State)       │  │  (Logs)    │ │
        │  └────────────────┘  └────────────┘ │
        │                                      │
        │  ┌──────────────────────────────┐  │
        │  │    CheckpointManager         │  │
        │  └────────┬─────────────────────┘  │
        └───────────┼──────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  OrchestratorDB       │
        │  (SQLite Database)    │
        │                       │
        │  - Executions         │
        │  - Logs               │
        │  - Checkpoints        │
        └───────────────────────┘
```

## Data Flow

### 1. Fresh Run

```
User Uploads Files
      │
      ├──> concepts.json ────┐
      ├──> inferences.json ──┼──> ConceptRepo / InferenceRepo
      └──> inputs.json ──────┘
                              │
                              ▼
                         Orchestrator
                              │
                              ├──> Execute Cycles
                              │
                              ├──> Update Blackboard
                              │
                              └──> Save Checkpoint ──> DB
                                         │
                                         ▼
                                  Final Concepts
                                         │
                                         ▼
                                  Results Display
```

### 2. Resume from Checkpoint

```
User Selects Resume Mode (PATCH/OVERWRITE/FILL_GAPS)
      │
      ▼
Load Checkpoint from DB
      │
      ├──> Restore Blackboard State
      ├──> Restore Tracker State
      ├──> Restore Workspace State
      └──> Restore Completed Concepts
                    │
                    ▼
         Reconcile with New Repo
                    │
         ┌──────────┴──────────┐
         │                     │
    PATCH Mode          OVERWRITE Mode
         │                     │
    Compare               Trust
    Signatures          Checkpoint
         │                     │
    Discard               Apply All
    Changed               State
    Logic
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
              Continue Execution
                    │
                    ▼
             Final Concepts
```

## Component Responsibilities

### Streamlit App (`app.py`)

**Responsibilities:**
- UI rendering and user interaction
- File upload handling
- Configuration management
- Session state management
- Results visualization

**Key Features:**
- Zero external dependencies beyond streamlit
- Uses `st.session_state` for persistence
- Responsive layout with tabs
- Real-time feedback

### Orchestrator (`infra._orchest._orchestrator.py`)

**Responsibilities:**
- Main execution loop
- Dependency resolution
- Readiness checking
- Item execution delegation
- Checkpoint coordination

**Key Methods:**
- `run()` - Main execution loop
- `_is_ready(item)` - Check if item can execute
- `_execute_item(item)` - Execute single inference
- `load_checkpoint()` - Restore from database

### ConceptRepo & InferenceRepo (`infra._orchest._repo.py`)

**Responsibilities:**
- Store concept and inference definitions
- Provide access methods
- Generate logic signatures
- Support JSON serialization

**Key Features:**
- Hash-based signature generation
- Signature comparison for change detection
- Reference management

### Blackboard (`infra._orchest._blackboard.py`)

**Responsibilities:**
- Track concept status (empty/complete)
- Track item status (pending/in_progress/completed)
- Store execution results

**State Types:**
- Concept status: `empty`, `complete`
- Item status: `pending`, `in_progress`, `completed`, `failed`

### CheckpointManager (`infra._orchest._checkpoint.py`)

**Responsibilities:**
- Save execution state to database
- Load execution state from database
- Reconcile state with new repositories
- Support multiple reconciliation modes

**Reconciliation Modes:**
- `PATCH` - Smart merge with signature checking
- `OVERWRITE` - Trust checkpoint completely
- `FILL_GAPS` - Conservative fill

### OrchestratorDB (`infra._orchest._db.py`)

**Responsibilities:**
- SQLite database wrapper
- Execution record management
- Log storage
- Checkpoint persistence

**Tables:**
- `executions` - Execution attempts
- `logs` - Detailed logs
- `checkpoints` - Saved states

## File Structure

```
normCode/
├── app.py                      # Main Streamlit app
├── run_app.py                  # Python launcher
├── run_app.bat                 # Windows batch launcher
├── run_app.ps1                 # PowerShell launcher
├── sample_inputs.json          # Example input file
├── APP_README.md               # App documentation
├── STREAMLIT_APP_GUIDE.md      # Comprehensive guide
├── QUICK_START_APP.md          # Quick start guide
├── APP_ARCHITECTURE.md         # This file
└── infra/
    └── _orchest/
        ├── _orchestrator.py    # Main engine
        ├── _repo.py            # Repositories
        ├── _blackboard.py      # State tracking
        ├── _checkpoint.py      # Persistence
        └── _db.py              # Database
```

## State Management

### Session State (Streamlit)

```python
st.session_state = {
    'last_run': {
        'run_id': str,
        'timestamp': str,
        'duration': float,
        'final_concepts': List[ConceptEntry],
        'llm_model': str,
        'max_cycles': int
    },
    'execution_log': [
        {
            'run_id': str,
            'timestamp': str,
            'status': 'success' | 'failed',
            'duration': float,
            'completed': int
        }
    ]
}
```

### Checkpoint State (Database)

```python
checkpoint_data = {
    'blackboard': {
        'concept_status': Dict[str, str],
        'item_status': Dict[str, str],
        'item_results': Dict[str, Any]
    },
    'tracker': {
        'cycle_count': int,
        'total_executions': int,
        'completion_order': List[str]
    },
    'workspace': Dict[str, Any],
    'completed_concepts': {
        'concept_name': {
            'reference_data': Any,
            'reference_axes': List[str]
        }
    },
    'signatures': {
        'concept_signatures': Dict[str, str],
        'item_signatures': Dict[str, str]
    }
}
```

## Security Considerations

### Current Implementation

- **Local execution only** - No remote access
- **Local file access** - Uses Streamlit's file upload
- **SQLite database** - Local storage only
- **No authentication** - Assumes trusted environment

### Production Considerations

If deploying publicly, add:
- User authentication
- File size limits
- Execution timeouts
- Rate limiting
- Database access controls

## Performance Characteristics

### Scalability

- **Small repositories** (<100 concepts): Instant
- **Medium repositories** (100-1000 concepts): Seconds to minutes
- **Large repositories** (>1000 concepts): Minutes to hours

### Bottlenecks

1. **LLM API calls** - Dominated by model response time
2. **Checkpoint saves** - I/O bound, ~100ms per checkpoint
3. **Signature generation** - Negligible overhead

### Optimization Strategies

1. **Intra-cycle checkpointing** - Save every N inferences
2. **Parallel execution** - Future feature (requires concurrency)
3. **Caching** - LLM response caching

## Extension Points

### Adding New Features

1. **Progress bars**: Hook into `ProcessTracker`
2. **Visualizations**: Use checkpoint data for graphs
3. **Custom sequences**: Add to `infra._agent._steps`
4. **Export formats**: Add to Results tab

### Adding New Modes

1. Define mode in `CheckpointManager.reconcile_state()`
2. Add to app's mode selector
3. Document behavior

## Error Handling

### App Level

```python
try:
    orchestrator.run()
    st.success("Execution completed!")
except Exception as e:
    st.error(f"Execution failed: {e}")
    st.exception(e)
```

### Orchestrator Level

- Graceful failure handling
- State preservation on errors
- Detailed error logging

## Testing Strategy

### Manual Testing

1. Upload valid files → Verify execution
2. Upload invalid JSON → Verify error handling
3. Resume from checkpoint → Verify state restoration
4. Different modes → Verify reconciliation

### Automated Testing

```python
# Test checkpoint reconciliation
def test_patch_mode():
    # Load old checkpoint
    # Modify repo logic
    # Resume with PATCH
    # Verify changed concepts re-run
    pass
```

## Future Enhancements

### Planned

- [ ] Real-time progress streaming (WebSocket)
- [ ] Concept dependency graph visualization
- [ ] Execution timeline viewer
- [ ] Diff viewer for PATCH mode
- [ ] Export to multiple formats (CSV, Excel)

### Potential

- [ ] Multi-user support
- [ ] Cloud storage integration
- [ ] Collaborative editing
- [ ] Version control integration

---

**Last Updated**: 2025-11-30

