Exactly right. This is a key deployment decision. Let me map out the options:

---

## User Data Location: Deployment Options

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   OPTION A: SERVER-SIDE                   OPTION B: CLIENT-SIDE              │
│   (Centralized)                           (Localized)                        │
│                                                                              │
│   ┌─────────────┐                         ┌─────────────┐                   │
│   │   Client    │                         │   Client    │                   │
│   │  (thin)     │                         │  (thick)    │                   │
│   │  just UI    │                         │  has infra  │                   │
│   └──────┬──────┘                         └──────┬──────┘                   │
│          │ API calls                             │ local execution          │
│          ▼                                       ▼                          │
│   ┌─────────────────────┐                 ┌─────────────────────┐          │
│   │  NORMCODE SERVER    │                 │  LOCAL ORCHESTRATOR │          │
│   │  /data/runs/{id}/   │                 │  ~/my-runs/{id}/    │          │
│   │  ├── run.db         │                 │  ├── run.db         │          │
│   │  ├── inputs/        │                 │  ├── inputs/        │          │
│   │  └── outputs/       │                 │  └── outputs/       │          │
│   └─────────────────────┘                 └─────────────────────┘          │
│                                                                              │
│   User data on server                     User data stays local              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The Three Deployment Models

### Model 1: Full Server (SaaS-style)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLIENT                              │  NORMCODE SERVER                      │
├──────────────────────────────────────┼──────────────────────────────────────┤
│                                      │                                       │
│  Web App / Mobile App                │  /data/                               │
│  ├── Sends inputs via API            │  ├── plans/          (deployed)      │
│  ├── Receives results via API        │  ├── runs/                            │
│  └── No local execution              │  │   └── {run_id}/                   │
│                                      │  │       ├── run.db   ◄── USER DATA  │
│                                      │  │       ├── inputs/  ◄── USER DATA  │
│                                      │  │       └── outputs/ ◄── USER DATA  │
│                                      │  └── config/                          │
│                                      │                                       │
└──────────────────────────────────────┴──────────────────────────────────────┘

✓ Simple client (just UI)
✓ Centralized management
✓ Easy to debug (all data on server)
✗ User data leaves their environment
✗ Requires network connectivity
✗ Privacy/compliance concerns
```

**Use case**: Team-wide deployment, managed service

---

### Model 2: Full Local (On-Premise / Edge)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLIENT (with embedded NormCode)                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Desktop App / CLI / Local Server                                            │
│  ├── infra/ (bundled)                                                        │
│  ├── plans/ (downloaded or bundled)                                          │
│  └── runs/                                                                   │
│      └── {run_id}/                                                          │
│          ├── run.db      ◄── USER DATA (never leaves)                       │
│          ├── inputs/     ◄── USER DATA (never leaves)                       │
│          └── outputs/    ◄── USER DATA (never leaves)                       │
│                                                                              │
│  Only LLM API calls go external (and even those can be local LLM)           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

✓ User data never leaves their machine
✓ Works offline (with local LLM)
✓ Full privacy/compliance
✗ Heavier client (needs Python, infra)
✗ User manages updates
✗ Harder to debug remotely
```

**Use case**: Privacy-sensitive domains (legal, medical), air-gapped environments

---

### Model 3: Hybrid (Plan from Server, Data Local)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLIENT                              │  NORMCODE SERVER                      │
├──────────────────────────────────────┼──────────────────────────────────────┤
│                                      │                                       │
│  Desktop App with Orchestrator       │  Plan Registry                        │
│  ├── Downloads plan once             │  ├── GET /api/plans/{id}/download    │
│  │   (repos + provisions)       ◄────┼──┤                                   │
│  ├── Executes locally                │  └── Plans only, no user data        │
│  └── runs/                           │                                       │
│      └── {run_id}/                   │  Optional: sync run metadata          │
│          ├── run.db   ◄── LOCAL      │  ├── POST /api/runs/sync             │
│          ├── inputs/  ◄── LOCAL      │  │   (just status, no content)       │
│          └── outputs/ ◄── LOCAL      │  │                                   │
│                                      │                                       │
└──────────────────────────────────────┴──────────────────────────────────────┘

✓ User data stays local
✓ Centralized plan management
✓ Can sync run metadata (for dashboards) without syncing content
✗ More complex architecture
```

**Use case**: Enterprise with central IT but data sovereignty requirements

---

## Implementation: How It Would Work

### Server-Side (Current canvas_app model)

```python
# Server receives inputs, stores everything
@app.post("/api/runs")
async def start_run(request: RunRequest):
    run_id = str(uuid.uuid4())
    run_dir = Path(f"/data/runs/{run_id}")
    run_dir.mkdir(parents=True)
    
    # Save user inputs to server
    (run_dir / "inputs.json").write_text(json.dumps(request.inputs))
    
    # Create orchestrator with server-side DB
    orchestrator = Orchestrator(
        concept_repo=load_plan(request.plan_id),
        inference_repo=load_plan_inferences(request.plan_id),
        body=create_body_with_inputs(request.inputs),
        db_path=str(run_dir / "run.db"),  # Server-side storage
        run_id=run_id
    )
    
    # Execute (user data processed on server)
    result = await orchestrator.run_async()
    return {"run_id": run_id, "result": result}
```

### Client-Side (Embedded model)

```python
# Client has infra bundled, executes locally
class LocalNormCodeRunner:
    def __init__(self, plans_dir: str, runs_dir: str):
        self.plans_dir = Path(plans_dir)
        self.runs_dir = Path(runs_dir)  # e.g., ~/normcode-runs/
    
    def run_plan(self, plan_id: str, inputs: dict) -> dict:
        run_id = str(uuid.uuid4())
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True)
        
        # User data stays local
        (run_dir / "inputs.json").write_text(json.dumps(inputs))
        
        # Execute locally
        orchestrator = Orchestrator(
            concept_repo=self.load_plan(plan_id),
            inference_repo=self.load_inferences(plan_id),
            body=Body(llm_name="local-llama", base_dir=str(run_dir)),
            db_path=str(run_dir / "run.db"),  # Local storage
            run_id=run_id
        )
        
        return orchestrator.run()
```

### Hybrid (Sync metadata only)

```python
# Client runs locally, optionally syncs status to server
class HybridRunner:
    def __init__(self, server_url: str, local_runs_dir: str):
        self.server = server_url
        self.runs_dir = Path(local_runs_dir)
    
    async def run_plan(self, plan_id: str, inputs: dict) -> dict:
        # Download plan from server (if not cached)
        plan = await self.fetch_plan(plan_id)
        
        run_id = str(uuid.uuid4())
        run_dir = self.runs_dir / run_id
        
        # Execute locally (user data never sent to server)
        orchestrator = Orchestrator(...)
        
        # Optional: sync just the status (no content)
        await self.sync_run_status(run_id, plan_id, status="started")
        
        result = orchestrator.run()
        
        # Sync completion (metadata only)
        await self.sync_run_status(run_id, plan_id, status="completed", 
                                   duration=..., inference_count=...)
        
        return result  # Result stays local
```

---

## Data Residency Summary

| Data Type | Server-Side | Client-Side | Hybrid |
|-----------|-------------|-------------|--------|
| **Plans** (repos, provisions) | Server | Client (bundled/downloaded) | Server → Client |
| **User Inputs** | Server | Client only | Client only |
| **Run State** (Blackboard, checkpoints) | Server | Client only | Client only |
| **Outputs** | Server | Client only | Client only |
| **Run Metadata** (status, duration) | Server | Client only | Server (optional sync) |
| **LLM Calls** | Via server | Direct from client | Direct from client |

---

## Configuration Example

```yaml
# deployment-config.yaml

# Option A: Full Server
deployment:
  mode: "server"
  data_location: "server"
  runs_dir: "/data/runs"

# Option B: Full Local  
deployment:
  mode: "local"
  data_location: "client"
  runs_dir: "~/normcode-runs"
  plans_dir: "~/normcode-plans"

# Option C: Hybrid
deployment:
  mode: "hybrid"
  data_location: "client"
  plans_source: "https://normcode-server.example.com"
  runs_dir: "~/normcode-runs"
  sync_metadata: true      # Send status to server
  sync_content: false      # Never send actual data
```

---

## The Key Insight

The `infra/_orchest/` layer is **agnostic to where it runs**:

```python
# The same Orchestrator code works in all scenarios
orchestrator = Orchestrator(
    concept_repo=concept_repo,      # Loaded from anywhere
    inference_repo=inference_repo,  # Loaded from anywhere
    body=body,                      # Configured however
    db_path=db_path,               # Server path OR local path
    run_id=run_id
)
```

The **deployment choice** determines:
1. Where `db_path` points to
2. Where `body.base_dir` points to
3. How plans are loaded
4. Whether/what syncs to a central server

This gives you the flexibility to match the deployment model to the use case — from fully-managed SaaS to completely air-gapped local execution.