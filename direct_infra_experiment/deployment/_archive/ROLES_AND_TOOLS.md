# Roles, Tools, and Data Strategy

How different users interact with NormCode, and what tools/data support each role.

---

## Overview: The NormCode Ecosystem

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│   │   Platform   │    │     Plan     │    │   Operator   │    │   End    │  │
│   │   Developer  │    │    Author    │    │   / Admin    │    │   User   │  │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    └────┬─────┘  │
│          │                   │                   │                  │        │
│          ▼                   ▼                   ▼                  ▼        │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│   │    Code      │    │   Author     │    │   Deploy     │    │   Run    │  │
│   │    Editor    │    │   Canvas     │    │   Canvas     │    │   API    │  │
│   │   (Cursor)   │    │              │    │              │    │   / UI   │  │
│   └──────────────┘    └──────────────┘    └──────────────┘    └──────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Role Definitions

### 1. Platform Developer

**Who**: Engineers building NormCode itself (infra, Canvas App, server)

**Responsibilities**:
- Develop core infrastructure (`infra/`)
- Build and maintain Canvas App
- Create new paradigms, sequences, tools
- Fix bugs, optimize performance

**Tools**:
| Tool | Purpose |
|------|---------|
| Code Editor (Cursor/VSCode) | Develop Python/TypeScript code |
| Git | Version control |
| pytest | Testing |
| Docker (dev mode) | Local server testing |

**Artifacts Created**:
- `infra/` package updates
- `canvas_app/` updates
- New paradigms in `_paradigms/`
- Documentation

---

### 2. Plan Author

**Who**: Domain experts, AI engineers who design NormCode workflows

**Responsibilities**:
- Write `.ncds` drafts (plan logic)
- Create provisions (prompts, schemas)
- Test and debug plans locally
- Iterate on plan design

**Tools**:
| Tool | Purpose |
|------|---------|
| **Author Canvas** | Write and test .ncds plans |
| Code Editor | Edit prompts, schemas |
| Local Server (dev mode) | Test execution |
| Compiler | .ncds → .ncd → repositories |

**Artifacts Created**:
- `.ncds` draft files
- `.ncd` formalized plans
- Provisions (prompts, paradigms, schemas)
- Plan packages (`.zip`)

**Author Canvas Features Needed**:
- `.ncds` editor with syntax highlighting
- Compile button (run derivation + formalization)
- Test run with sample inputs
- View execution graph
- Debug breakpoints

---

### 3. Operator / Admin

**Who**: DevOps, platform admins who manage NormCode Server

**Responsibilities**:
- Deploy and configure server
- Deploy/undeploy plans
- Monitor server health
- Manage agents (LLM configs)
- View logs, troubleshoot issues

**Tools**:
| Tool | Purpose |
|------|---------|
| **Deploy Canvas** | Deploy plans, manage server |
| Docker/Kubernetes | Run server |
| CLI | Server management |
| Monitoring (Grafana, etc.) | Metrics, alerts |

**Artifacts Managed**:
- Deployed plan packages
- Server configuration
- Agent configurations
- Run history, logs

**Deploy Canvas Features Needed**:
- Plan registry (list, deploy, undeploy)
- Server status dashboard
- Agent configuration UI
- Log viewer
- Run history browser

---

### 4. End User

**Who**: Business users, applications that trigger plan execution

**Responsibilities**:
- Trigger plan runs
- Provide inputs
- View results
- Monitor run progress

**Tools** (provided by client's environment, NOT Canvas):
| Tool | Built By | Example |
|------|----------|---------|
| **Custom Frontend** | Client's dev team | React dashboard for their domain |
| **AI Assistant** | Via MCP | Claude triggering plans |
| **CLI** | NormCode team | `normcode run --plan X` |
| **API Integration** | Client's dev team | Backend calling REST API |
| **Chatbot** | Client's dev team | Slack/Teams bot |

**Interactions with NormCode Server**:
- `POST /api/runs` - Start execution with inputs
- `GET /api/runs/{id}` - Check status
- `WS /ws/runs/{id}` - Live updates
- `GET /api/runs/{id}/result` - Get final output

**Key Point**: End users never see Canvas. They interact through clients designed for their specific domain and workflow.

---

## Canvas Strategy: Two Modes (Developer Tool)

The Canvas App is a **developer/operator tool**, not an end-user tool.

End users interact with the **deployed NormCode Server** through their own clients.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│   DEVELOPMENT SIDE                         DEPLOYMENT SIDE                   │
│   (Canvas App)                             (NormCode Server)                 │
│                                                                              │
│   ┌─────────────────────────────┐          ┌─────────────────────────────┐  │
│   │        CANVAS APP           │          │      NORMCODE SERVER        │  │
│   │         (Two Modes)         │          │                             │  │
│   ├─────────────┬───────────────┤          │  ┌─────────────────────┐    │  │
│   │ AUTHOR MODE │ DEPLOY MODE   │──.zip──→ │  │   Deployed Plans    │    │  │
│   │             │               │          │  └──────────┬──────────┘    │  │
│   │ • Edit .ncds│ • Plan list   │          │             │               │  │
│   │ • Compile   │ • Deploy/undep│          │  ┌──────────┴──────────┐    │  │
│   │ • Test run  │ • Agent config│          │  │     REST API        │    │  │
│   │ • Debug     │ • Server stats│          │  │     WebSocket       │    │  │
│   │ • Breakpoint│ • Log viewer  │          │  │     MCP Interface   │    │  │
│   │             │               │          │  └──────────┬──────────┘    │  │
│   │[Plan Author]│ [Operator]    │          │             │               │  │
│   └─────────────┴───────────────┘          └─────────────┼───────────────┘  │
│                                                          │                   │
│                                            ┌─────────────┴───────────────┐  │
│                                            │       CLIENT LAYER          │  │
│                                            ├─────────────────────────────┤  │
│                                            │  • Custom Frontend (React)  │  │
│                                            │  • MCP / AI Assistant       │  │
│                                            │  • CLI Tool                 │  │
│                                            │  • Direct API Calls         │  │
│                                            │  • Webhooks / Integrations  │  │
│                                            │  • Mobile App               │  │
│                                            └─────────────┬───────────────┘  │
│                                                          │                   │
│                                            ┌─────────────┴───────────────┐  │
│                                            │         END USERS           │  │
│                                            │   (in client's environment) │  │
│                                            └─────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Canvas Mode Switching

```yaml
# Canvas App config (development tool)
canvas:
  modes:
    author: true      # Enable for plan authors
    deploy: true      # Enable for operators
  
  default_mode: "author"
  
  # Optional: role-based access
  auth:
    author_roles: ["author", "admin"]
    deploy_roles: ["operator", "admin"]
```

### Client Layer (End Users)

End users don't use Canvas - they use clients built for their specific needs:

| Client Type | Use Case | Example |
|-------------|----------|---------|
| **Custom Frontend** | Branded UI for specific workflows | React app calling NormCode API |
| **MCP Integration** | AI assistants trigger plans | Claude Desktop with NormCode MCP |
| **CLI** | Automation, scripting | `normcode run --plan doc-analysis` |
| **Direct API** | System-to-system integration | Backend service calling REST API |
| **Webhooks** | Event-driven triggers | Slack bot, GitHub Actions |
| **Mobile App** | On-the-go access | Flutter/React Native app |

The NormCode Server exposes a **universal API** that all clients consume.

---

## Database Strategy

### Current State

```
Per-run SQLite database (orchestration.db)
├── checkpoints table
├── executions table
└── logs table
```

### Proposed: Split Database Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATABASE ARCHITECTURE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────┐                                │
│  │  SERVER DATABASE (PostgreSQL/SQLite)    │  ← Shared across runs          │
│  │                                         │                                 │
│  │  • plans (registry)                     │                                 │
│  │  • runs (history)                       │                                 │
│  │  • agents (configurations)              │                                 │
│  │  • users (optional auth)                │                                 │
│  │  • audit_log (all operations)           │                                 │
│  └─────────────────────────────────────────┘                                │
│                                                                              │
│  ┌─────────────────────────────────────────┐                                │
│  │  RUN DATABASE (SQLite per run)          │  ← Isolated per run            │
│  │                                         │                                 │
│  │  /data/runs/{run_id}/                   │                                 │
│  │  ├── run.db                             │                                 │
│  │  │   ├── checkpoints                    │                                 │
│  │  │   ├── executions                     │                                 │
│  │  │   ├── logs                           │                                 │
│  │  │   └── iteration_history              │                                 │
│  │  └── artifacts/                         │                                 │
│  │      ├── outputs/                       │                                 │
│  │      └── intermediate/                  │                                 │
│  └─────────────────────────────────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Why This Split?

| Database | Type | Why |
|----------|------|-----|
| **Server DB** | PostgreSQL (prod) or SQLite (dev) | Shared state, needs queries across all runs |
| **Run DB** | SQLite (always) | Isolated, portable, can export entire run |

### Server Database Schema

```sql
-- plans: deployed plan registry
CREATE TABLE plans (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    description TEXT,
    manifest JSON NOT NULL,
    deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deployed_by TEXT,
    status TEXT DEFAULT 'active',  -- active, deprecated, disabled
    package_path TEXT NOT NULL
);

-- runs: execution history
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL REFERENCES plans(id),
    status TEXT NOT NULL,  -- pending, running, paused, completed, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    inputs JSON,
    outputs JSON,
    agent TEXT,
    error TEXT,
    run_db_path TEXT NOT NULL
);

-- agents: LLM configurations
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    api_key_env TEXT,
    config JSON,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- audit_log: all operations
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operation TEXT NOT NULL,  -- plan.deploy, run.start, agent.update, etc.
    actor TEXT,               -- user or system
    resource_type TEXT,       -- plan, run, agent
    resource_id TEXT,
    details JSON
);
```

### Run Database Schema (existing + additions)

```sql
-- Already exists in orchestration.db:
-- checkpoints, executions, logs

-- New: iteration_history (for loop debugging)
CREATE TABLE iteration_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    flow_index TEXT NOT NULL,
    concept_name TEXT NOT NULL,
    iteration_index INTEGER NOT NULL,
    cycle INTEGER NOT NULL,
    reference_snapshot JSON,  -- serialized Reference
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- New: tool_calls (for Agent Panel monitoring)
CREATE TABLE tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    execution_id INTEGER,
    flow_index TEXT,
    tool_name TEXT NOT NULL,
    method TEXT NOT NULL,
    inputs JSON,
    outputs JSON,
    duration_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Data Flow by Role

### Plan Author Workflow

```
┌──────────────────────────────────────────────────────────────────────────┐
│  PLAN AUTHOR WORKFLOW                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  1. AUTHOR                                                                │
│     ┌─────────────┐                                                       │
│     │ Write .ncds │  ← Author Canvas (editor mode)                        │
│     │ + prompts   │                                                       │
│     └──────┬──────┘                                                       │
│            ▼                                                              │
│  2. COMPILE                                                               │
│     ┌─────────────┐                                                       │
│     │  Derivation │  → .ncd + .ncn                                        │
│     │Formalization│  → concept_repo.json + inference_repo.json            │
│     │  Activation │                                                       │
│     └──────┬──────┘                                                       │
│            ▼                                                              │
│  3. TEST                                                                  │
│     ┌─────────────┐                                                       │
│     │  Test Run   │  ← Author Canvas (debug mode)                         │
│     │ Breakpoints │                                                       │
│     │  Inspect    │                                                       │
│     └──────┬──────┘                                                       │
│            ▼                                                              │
│  4. PACKAGE                                                               │
│     ┌─────────────┐                                                       │
│     │ Create .zip │  → my-plan.zip                                        │
│     │  manifest   │                                                       │
│     └─────────────┘                                                       │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### Operator Workflow

```
┌──────────────────────────────────────────────────────────────────────────┐
│  OPERATOR WORKFLOW                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  1. DEPLOY SERVER                                                         │
│     ┌─────────────┐                                                       │
│     │ docker-comp │  ← docker-compose up                                  │
│     │ ose up      │                                                       │
│     └──────┬──────┘                                                       │
│            ▼                                                              │
│  2. CONFIGURE                                                             │
│     ┌─────────────┐                                                       │
│     │ Set agents  │  ← Deploy Canvas / API                                │
│     │ API keys    │                                                       │
│     └──────┬──────┘                                                       │
│            ▼                                                              │
│  3. DEPLOY PLANS                                                          │
│     ┌─────────────┐                                                       │
│     │ Upload .zip │  ← Deploy Canvas / POST /api/plans/deploy             │
│     │ Validate    │                                                       │
│     └──────┬──────┘                                                       │
│            ▼                                                              │
│  4. MONITOR                                                               │
│     ┌─────────────┐                                                       │
│     │ View runs   │  ← Deploy Canvas (dashboard)                          │
│     │ View logs   │                                                       │
│     │ Health check│                                                       │
│     └─────────────┘                                                       │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### End User Workflow (via Client App)

```
┌──────────────────────────────────────────────────────────────────────────┐
│  END USER WORKFLOW                                                        │
│  (in client's environment - NOT Canvas)                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  1. ACCESS CLIENT APP                                                     │
│     ┌─────────────┐                                                       │
│     │ Open client │  ← Custom React app, Slack bot, CLI, etc.             │
│     │ application │                                                       │
│     └──────┬──────┘                                                       │
│            ▼                                                              │
│  2. PROVIDE INPUTS                                                        │
│     ┌─────────────┐                                                       │
│     │ Fill form   │  ← Client's UI designed for their domain              │
│     │ Upload files│     (calls POST /api/runs internally)                 │
│     └──────┬──────┘                                                       │
│            ▼                                                              │
│  3. RUN                                                                   │
│     ┌─────────────┐                                                       │
│     │ Start run   │  ← Client shows progress                              │
│     │ Watch prog  │     (via WebSocket /ws/runs/{id})                     │
│     └──────┬──────┘                                                       │
│            ▼                                                              │
│  4. GET RESULTS                                                           │
│     ┌─────────────┐                                                       │
│     │ View output │  ← Client displays results in domain-specific format  │
│     │ Take action │     (GET /api/runs/{id}/result internally)            │
│     └─────────────┘                                                       │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Tool Matrix

| Role | Tool | Access | Features |
|------|------|--------|----------|
| **Platform Developer** | Code Editor | Local | Full codebase access |
| | Git | Local/Remote | Version control |
| | pytest | Local | Testing |
| | Docker (dev) | Local | Development server |
| **Plan Author** | Author Canvas | Local/Server | .ncds editing, compile, test, debug |
| | Code Editor | Local | Prompts, schemas |
| | Compiler CLI | Local | Batch compilation |
| **Operator** | Deploy Canvas | Server | Plan deployment, monitoring |
| | CLI | Server | Server management |
| | Docker | Server | Container management |
| **End User** | Client App | Client's env | Custom UI for their domain |
| | MCP/AI | Client's env | AI assistant integration |
| | CLI | Client's env | Command-line access |
| | API | Client's env | Direct integration |

---

## Canvas UI Wireframes (Two Modes)

Canvas App is for **developers and operators only**. End users use their own client apps.

### Author Mode

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Author] [Deploy]                                  [Settings] [User]   │
├──────────────────────┬──────────────────────────────────────────────────┤
│                      │                                                   │
│  PROJECT BROWSER     │  EDITOR                                          │
│  ──────────────      │  ──────────────────────────────────────────      │
│  📁 my-plan/         │  /: Document Analysis Plan                        │
│  ├── plan.ncds ●     │                                                   │
│  ├── prompts/        │  <- document summary                              │
│  │   └── analyze.md  │      <= summarize the document                    │
│  └── manifest.json   │      <- clean text                                │
│                      │          <= extract main content                  │
│  ──────────────      │          <- raw document                          │
│  [Compile] [Test]    │                                                   │
│  [Package .zip]      │                                                   │
│                      │                                                   │
├──────────────────────┴───────────────────────────────┬──────────────────┤
│                                                       │                  │
│  EXECUTION GRAPH                                      │  NODE DETAILS    │
│  ────────────────────────────────────────────────    │  ────────────    │
│                                                       │                  │
│    [summary] ← [summarize] ← [clean] ← [extract] ←   │  {clean text}    │
│                                          [raw doc]    │  Type: object    │
│                                                       │  Status: ●       │
│  ──────────────────────────────────────────────────  │  Value: ...      │
│  [▶ Run] [⏸ Pause] [⏭ Step] [⏹ Stop]   Cycle: 3/10  │                  │
│                                                       │                  │
└───────────────────────────────────────────────────────┴──────────────────┘
```

### Deploy Mode

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [Author] [Deploy]                                  [Settings] [User]   │
├──────────────────────┬──────────────────────────────────────────────────┤
│                      │                                                   │
│  DEPLOYED PLANS      │  PLAN DETAILS                                    │
│  ──────────────      │  ────────────────────────────────────────────    │
│  📦 doc-analysis     │                                                   │
│     v1.2.0 ●         │  Name: document-analysis                          │
│  📦 data-pipeline    │  Version: 1.2.0                                   │
│     v2.0.1 ●         │  Deployed: 2026-01-15 10:30                       │
│  📦 risk-assessment  │  Status: Active                                   │
│     v1.0.0 ○         │                                                   │
│                      │  Inputs:                                          │
│  ──────────────      │  - {raw document}: file (required)                │
│  [+ Deploy New]      │  - {analysis type}: string (optional)             │
│                      │                                                   │
│                      │  [Undeploy] [View Manifest] [View Runs]           │
│                      │                                                   │
├──────────────────────┴──────────────────────────────────────────────────┤
│                                                                          │
│  SERVER STATUS                    │  RECENT RUNS                         │
│  ────────────────────────────────│  ────────────────────────────────    │
│  Health: ● Healthy                │  run-abc123  doc-analysis  ✓ 2m ago  │
│  Plans: 3 active                  │  run-def456  data-pipeline ● running │
│  Active Runs: 1                   │  run-ghi789  risk-assess   ✗ 1h ago  │
│  Agents: qwen-plus (default)      │                                      │
│                                   │                                      │
└───────────────────────────────────┴──────────────────────────────────────┘
```

### Client Apps (End User Examples)

End users access deployed plans through **client applications** in their environment:

```
EXAMPLE 1: Custom Web Dashboard (for legal document analysis)
┌─────────────────────────────────────────────────────────────────────────┐
│  ACME Legal - Document Analyzer                     [Profile] [Logout]  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Upload Contract for Analysis                                            │
│  ────────────────────────────────────────────────────────────────────   │
│  [Drag & Drop PDF here]                                                  │
│                                                                          │
│  Analysis Type: [Risk Assessment ▼]                                      │
│                                                                          │
│  [Analyze Contract]                                                      │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
(Internally calls NormCode API: POST /api/runs with plan_id: "contract-analysis")

EXAMPLE 2: Slack Bot
┌─────────────────────────────────────────────────────────────────────────┐
│  #legal-team                                                             │
├─────────────────────────────────────────────────────────────────────────┤
│  @analyst-bot analyze this contract: [contract.pdf]                      │
│                                                                          │
│  🤖 analyst-bot: Analyzing contract... (35% complete)                    │
│                                                                          │
│  🤖 analyst-bot: Analysis complete!                                      │
│     Risk Level: Medium                                                   │
│     Key Clauses: 3 flagged                                               │
│     [View Full Report]                                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
(Bot calls NormCode API behind the scenes)

EXAMPLE 3: CLI Tool
┌─────────────────────────────────────────────────────────────────────────┐
│  $ normcode run contract-analysis --input contract.pdf                   │
│  Starting run: run-abc123                                                │
│  Progress: ████████████████████████████████████████ 100%                 │
│  Result saved to: ./analysis-result.json                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: Core (Current canvas_app + Database)

| Component | Priority | Effort |
|-----------|----------|--------|
| Server DB schema | High | Medium |
| Health endpoints | High | Low |
| Mode switching (Author/Deploy) | Medium | Medium |

### Phase 2: Author Experience

| Component | Priority | Effort |
|-----------|----------|--------|
| .ncds editor in Canvas | High | High |
| Compile button | High | Medium |
| Test run with debug | High | Medium (exists) |
| Package .zip button | Medium | Low |

### Phase 3: Operator Experience (Deploy Mode)

| Component | Priority | Effort |
|-----------|----------|--------|
| Plan deployment API | High | Medium |
| Plan registry UI | High | Medium |
| Server dashboard | Medium | Medium |
| Run history viewer | Medium | Medium |

### Phase 4: Client Enablement (for End Users)

| Component | Priority | Effort |
|-----------|----------|--------|
| Clean REST API docs | High | Low |
| OpenAPI/Swagger spec | High | Low |
| Example client code | Medium | Medium |
| CLI tool | Medium | Medium |
| MCP server interface | Medium | High |

*Note: End User UI is built by clients, not by us. We provide the API and examples.*

---

## Summary

### Tools by Role

| Role | Primary Tool | Database Access | Environment |
|------|-------------|-----------------|-------------|
| Platform Developer | Code Editor | Full (dev) | Local development |
| Plan Author | Author Canvas | Run DB (test) | Canvas (Author mode) |
| Operator | Deploy Canvas | Server DB + Run DBs | Canvas (Deploy mode) |
| End User | Client App | Run DB (read-only via API) | Client's environment |

### The Clean Separation

```
┌────────────────────────────┐     ┌────────────────────────────┐
│     DEVELOPMENT SIDE       │     │     DEPLOYMENT SIDE        │
│                            │     │                            │
│  Canvas App (Two Modes)    │     │  NormCode Server           │
│  ├── Author Mode           │────→│  ├── Deployed Plans        │
│  └── Deploy Mode           │     │  ├── REST API              │
│                            │     │  ├── WebSocket             │
│  [Plan Authors]            │     │  └── MCP Interface         │
│  [Operators]               │     │           │                │
│                            │     │           ▼                │
└────────────────────────────┘     │  Client Applications       │
                                   │  ├── Custom Frontend       │
                                   │  ├── AI/MCP Integration    │
                                   │  ├── CLI                   │
                                   │  └── API Integrations      │
                                   │           │                │
                                   │           ▼                │
                                   │      [End Users]           │
                                   └────────────────────────────┘
```

**Canvas is a developer tool.** End users never see it - they use clients designed for their specific needs.

