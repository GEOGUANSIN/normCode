Let me explore the orchestration layer to understand how it fits into the per-user/per-run model:

[3 tools called]

Now I have a clear picture. Let me explain how `infra/_orchest/` participates in the deployment model:

---

## How `_orchest/` Participates in Deployment

### The Core Insight

You're exactly right. The relationship is:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   END USER fills inputs                                                      │
│          │                                                                   │
│          ▼                                                                   │
│   ┌───────────────────────────────────────────────────────────────────────┐ │
│   │   NEW ORCHESTRATOR INSTANCE (per run)                                  │ │
│   │   ├── run_id = "run-abc-123"        ← unique per execution            │ │
│   │   ├── Blackboard (in-memory state)  ← isolated state for this run     │ │
│   │   ├── Body (activated agent)        ← configured with user's inputs   │ │
│   │   └── db_path = "/data/runs/{run_id}/run.db"  ← per-run SQLite        │ │
│   └───────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Current Architecture (from the code)

**Per-Run Isolation via `run_id`:**

```python
# From _orchestrator.py
class Orchestrator:
    def __init__(self, 
                 concept_repo: ConceptRepo,
                 inference_repo: InferenceRepo,
                 body: Optional[Body] = None,
                 db_path: Optional[str] = None,
                 run_id: Optional[str] = None):  # ← Each run gets unique ID
        
        # Use provided run_id or generate a unique one
        self.run_id = run_id if run_id is not None else str(uuid.uuid4())
        
        # Isolated state management
        self.blackboard = Blackboard()           # ← Per-run in-memory state
        self.body = body or Body()               # ← Per-run activated agent
        
        # Per-run database (or shared DB with run_id isolation)
        if db_path:
            self.db = OrchestratorDB(db_path, run_id=self.run_id)
```

**Database Isolation:**

```python
# From _db.py
class OrchestratorDB:
    """Supports multiple orchestrator runs via run_id isolation."""
    
    # Tables use run_id as key
    CREATE TABLE checkpoints (
        run_id TEXT,              # ← Isolates checkpoints per run
        cycle INTEGER,
        inference_count INTEGER,
        state_json TEXT,
        PRIMARY KEY (run_id, cycle, inference_count)
    )
    
    CREATE TABLE executions (
        run_id TEXT,              # ← Isolates execution history per run
        cycle INTEGER,
        flow_index TEXT,
        ...
    )
```

---

### How This Maps to Deployment

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NORMCODE SERVER                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   POST /api/runs { plan_id: "doc-analyzer", inputs: {...} }                  │
│          │                                                                   │
│          ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  EXECUTION MANAGER                                                   │   │
│   │  Creates isolated execution context:                                 │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│          │                                                                   │
│          ├─── Load Plan (repos from /data/plans/{plan_id}/)                 │
│          │                                                                   │
│          ├─── Create Body (with user's inputs filled in)                    │
│          │    body = Body(llm_name="gpt-4o", base_dir=plan_dir)             │
│          │    body.user_input = user_provided_inputs                        │
│          │                                                                   │
│          ├─── Create per-run DB path                                         │
│          │    db_path = "/data/runs/{run_id}/run.db"                        │
│          │                                                                   │
│          └─── Create Orchestrator                                            │
│               orchestrator = Orchestrator(                                   │
│                   concept_repo=loaded_concepts,                              │
│                   inference_repo=loaded_inferences,                          │
│                   body=activated_body,                                       │
│                   db_path=db_path,                                          │
│                   run_id=run_id                                             │
│               )                                                              │
│                                                                              │
│          │                                                                   │
│          ▼                                                                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │  ISOLATED RUN CONTEXT                                                │   │
│   │  /data/runs/{run_id}/                                               │   │
│   │  ├── run.db                  ← Checkpoints, executions, logs        │   │
│   │  ├── artifacts/              ← Intermediate outputs                  │   │
│   │  └── outputs/                ← Final results                         │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Two Isolation Strategies

**Option A: Per-Run SQLite (Current Architecture)**

```
/data/runs/
├── run-abc-123/
│   └── run.db       ← Everything for this run
├── run-def-456/
│   └── run.db       ← Completely separate
└── run-ghi-789/
│   └── run.db
```

**Pros**: 
- Complete isolation
- Easy to export/delete a run
- Can run on different machines

**Option B: Shared DB with run_id Isolation (Also Supported)**

```
/data/orchestration.db    ← Single file, runs isolated by run_id
    ├── checkpoints      (WHERE run_id = 'abc-123')
    ├── executions       (WHERE run_id = 'abc-123')
    └── logs             (WHERE run_id = 'abc-123')
```

**Pros**:
- Easier to query across runs
- Single file to backup

---

### The Full Picture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   End User A                     End User B                     End User C   │
│       │                              │                              │        │
│       ▼                              ▼                              ▼        │
│   ┌─────────┐                   ┌─────────┐                   ┌─────────┐   │
│   │ Run 001 │                   │ Run 002 │                   │ Run 003 │   │
│   └────┬────┘                   └────┬────┘                   └────┬────┘   │
│        │                             │                              │        │
│   ┌────┴─────────────────────────────┴──────────────────────────────┴────┐  │
│   │                         NORMCODE SERVER                              │  │
│   ├──────────────────────────────────────────────────────────────────────┤  │
│   │                                                                       │  │
│   │   ┌──────────────────────────────────────────────────────────────┐   │  │
│   │   │  SHARED (read-only)                                          │   │  │
│   │   │  ├── /data/plans/{plan_id}/                                  │   │  │
│   │   │  │   ├── concept_repo.json     ◄── Same plan for all        │   │  │
│   │   │  │   ├── inference_repo.json                                 │   │  │
│   │   │  │   └── provisions/                                         │   │  │
│   │   │  └── /data/config/agents.yaml  ◄── Shared agent configs      │   │  │
│   │   └──────────────────────────────────────────────────────────────┘   │  │
│   │                                                                       │  │
│   │   ┌──────────────────────────────────────────────────────────────┐   │  │
│   │   │  PER-RUN (isolated)                                          │   │  │
│   │   │                                                               │   │  │
│   │   │  Run 001 (User A)          Run 002 (User B)                  │   │  │
│   │   │  ├── Orchestrator          ├── Orchestrator                  │   │  │
│   │   │  │   ├── run_id: "001"     │   ├── run_id: "002"            │   │  │
│   │   │  │   ├── Blackboard        │   ├── Blackboard               │   │  │
│   │   │  │   │   (state)           │   │   (state)                  │   │  │
│   │   │  │   └── Body              │   └── Body                     │   │  │
│   │   │  │       (activated        │       (activated               │   │  │
│   │   │  │        with A's         │        with B's                │   │  │
│   │   │  │        inputs)          │        inputs)                 │   │  │
│   │   │  │                         │                                 │   │  │
│   │   │  └── /data/runs/001/       └── /data/runs/002/              │   │  │
│   │   │      └── run.db                └── run.db                   │   │  │
│   │   │                                                               │   │  │
│   │   └──────────────────────────────────────────────────────────────┘   │  │
│   │                                                                       │  │
│   └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Key Components and Their Isolation

| Component | Scope | Purpose |
|-----------|-------|---------|
| **Orchestrator** | Per-run | Drives execution, manages cycles |
| **Blackboard** | Per-run (in-memory) | Tracks concept/item statuses |
| **Body** | Per-run | Activated agent with user's inputs |
| **OrchestratorDB** | Per-run (SQLite) | Checkpoints, logs, execution history |
| **ConceptRepo** | Per-plan (shared) | Static concept definitions |
| **InferenceRepo** | Per-plan (shared) | Static inference definitions |

---

### What Happens on Resume/Fork

```python
# Resume: Continue same run
orchestrator = Orchestrator.load_checkpoint(
    db_path="/data/runs/001/run.db",
    run_id="001",      # Same run_id = continue
    cycle=3            # Optional: specific checkpoint
)

# Fork: Branch from checkpoint into NEW run
orchestrator = Orchestrator.load_checkpoint(
    db_path="/data/runs/001/run.db",
    run_id="001",           # Source run
    new_run_id="001-fork",  # New run_id = fork
    cycle=3
)
# New run will write to /data/runs/001-fork/run.db
```

---

### Summary

| Question | Answer |
|----------|--------|
| **Per-user agent copies?** | Yes - each run creates its own `Orchestrator` + `Body` instance |
| **Per-user DB?** | Yes - typically `/data/runs/{run_id}/run.db` (can also share DB with `run_id` isolation) |
| **Localized DB?** | Yes - SQLite is file-based, can be anywhere the server can write |
| **Shared plan?** | Yes - repos are read-only, shared across all runs of that plan |
| **Isolated state?** | Yes - `Blackboard` and `Body` are per-run instances |

The current `infra/_orchest/` is **already designed for this multi-tenant model** — the `run_id` isolation is built into the database schema and checkpoint management.