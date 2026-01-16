# NormCode Deployment Specification

**Version**: 1.0 (Canonical)
**Status**: Draft for Implementation

This is the single source of truth for NormCode deployment architecture.

---

## Table of Contents

1. [Core Concepts](#1-core-concepts)
2. [Roles](#2-roles)
3. [Agent Architecture](#3-agent-architecture)
4. [Deployment Model](#4-deployment-model)
5. [Per-Run Isolation](#5-per-run-isolation)
6. [Plan Package Format](#6-plan-package-format)
7. [Server API](#7-server-api)
8. [Configuration](#8-configuration)
9. [Docker Deployment](#9-docker-deployment)
10. [Data Residency Options](#10-data-residency-options)
11. [Optional: MCP Integration](#11-optional-mcp-integration)

---

## 1. Core Concepts

### 1.1 What NormCode Deploys

NormCode deploys **plans**, not code. A plan is a pre-compiled inference graph with explicit data isolation.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│   Plan Author           Operator              End User                        │
│   writes .ncds   ──►    deploys plan   ──►    fills inputs   ──►   RESULT    │
│   (compile)             to server             via client                      │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Key Terms

| Term           | Definition                                                                   |
| -------------- | ---------------------------------------------------------------------------- |
| **Plan**       | Compiled inference graph (`.concept.json` + `.inference.json` + provisions)  |
| **Run**        | Single orchestrator execution; one `run_id`, may use multiple agents         |
| **Agent**      | Named body configuration (tools + settings); multiple agents per run         |
| **Body**       | Collection of tools (llm, file_system, etc.) that power an agent             |
| **LLM**        | One tool in the body; multiple agents can share the same LLM                 |
| **Checkpoint** | Saved state within a run (resumable)                                         |
| **Provisions** | Resources that configure execution (paradigms, prompts, schemas)             |

---

## 2. Roles

Four roles interact with NormCode. Each has distinct responsibilities and access.

### 2.1 Role Summary

| Role                         | Responsibility                                           | Primary Tool                 |
| ---------------------------- | -------------------------------------------------------- | ---------------------------- |
| **Platform Developer** | Builds infra (sequences, Body tools, built-in paradigms) | Code editor                  |
| **Plan Author**        | Writes plans, prompts, schemas                           | Canvas (Author mode)         |
| **Operator**           | Deploys plans, configures server, monitors               | Canvas (Deploy mode), Docker |
| **End User**           | Triggers runs, provides inputs                           | Client apps (NOT Canvas)     |

### 2.2 Role Access Matrix

| Component                     |    Platform Dev    | Plan Author |  Operator  |     End User     |
| ----------------------------- | :----------------: | :---------: | :---------: | :---------------: |
| Create sequences              |         ✅         |     ❌     |     ❌     |        ❌        |
| Create Body tools             |    (for tests)    |     ❌     |     ✅     | (via client APIs) |
| Create paradigms              | (canvas built-ins) |     ✅     |     ❌     |        ❌        |
| Write& Compile plans (.ncds) | (canvas built-ins) |     ✅     |     ❌     |        ❌        |
| Create prompts/schemas        | (canvas built-ins) |     ✅     |     ❌     |        ❌        |
| Deploy plans                  |         ❌         |     ❌     |     ✅     |        ❌        |
| Configure agents (LLM)        |         ❌         |     ❌     |     ✅     | (via client APIs) |
| Start runs                    |         ❌         | (for tests) | (for tests) |        ✅        |
| Fill Body's APIs (inputs)     |         ❌         | (for tests) | (for tests) |        ✅        |

### 2.3 Key Insight

**End Users never see Canvas.** They interact through client applications (web apps, bots, CLI, MCP) built for their specific domain.

---

## 3. Agent Architecture

### 3.1 Agent System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT SYSTEM                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SEQUENCES (How inferences execute)                                          │
│  ├── Semantic: imperative, judgement (LLM calls)                            │
│  └── Syntactic: assigning, grouping, timing, looping (free, deterministic)  │
│                                                                              │
│  BODY (Tools available to agent)                                             │
│  ├── llm              (language model interface)                            │
│  ├── prompt_tool      (prompt loading and templating)                       │
│  ├── file_system      (read/write files)                                    │
│  ├── python_interpreter (execute Python scripts)                            │
│  ├── composition_tool (compose outputs)                                     │
│  ├── formatter_tool   (format/parse data)                                   │
│  ├── user_input       (request human input)                                 │
│  └── paradigm_tool    (load paradigms)                                      │
│                                                                              │
│  PROVISIONS (Resources that configure execution)                             │
│  ├── Paradigms (HOW - execution patterns, reusable)                         │
│  └── User-Tool (WHAT - prompts, schemas, scripts, plan-specific)            │
│                                                                              │
│  ════════════════════════════ BOUNDARY ════════════════════════════════════ │
│                                                                              │
│  BODY's APIs (Open slots that clients fill to activate agent)               │
│  ├── user_input: ???   ◄── client provides: "user query text"              │
│  ├── file_system: ???  ◄── client provides: "/path/to/file.pdf"            │
│  └── llm: ???          ◄── client provides: "gpt-4o" (optional)            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Run / Agent / LLM Hierarchy

A **Run** (Orchestrator) can use multiple **Agents**, and each Agent has a **Body** with tools. The LLM is just one tool in the Body.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  RUN (Orchestrator)                                                          │
│  ├── run_id: "abc-123"                                                       │
│  ├── user_id: "user-456"                                                     │
│  └── plan_id: "document-analyzer"                                            │
│                                                                              │
│      ┌─────────────────────────────────────────────────────────────────┐    │
│      │  AGENT: "default"                                                │    │
│      │  └── Body                                                        │    │
│      │      ├── llm_tool        → gpt-4o                               │    │
│      │      ├── file_tool       → base_dir: "/data/runs/{run_id}/"     │    │
│      │      ├── user_input_tool → input_api: websocket                 │    │
│      │      └── python_tool     → sandbox: true                        │    │
│      └─────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│      ┌─────────────────────────────────────────────────────────────────┐    │
│      │  AGENT: "reviewer"  (same run, different agent)                  │    │
│      │  └── Body                                                        │    │
│      │      ├── llm_tool        → gpt-4o  (SAME LLM as "default")      │    │
│      │      ├── file_tool       → base_dir: "/data/runs/{run_id}/"     │    │
│      │      └── user_input_tool → null (no user input for this agent)  │    │
│      └─────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key distinctions**:

| Concept | Definition | Cardinality |
|---------|------------|-------------|
| **Run** | One orchestrator execution context | 1 per request |
| **Agent** | Named body configuration (tools + settings) | 1+ per run |
| **LLM** | One tool in the agent's body | Shared across agents |

### 3.3 Run Request Format

```json
POST /api/runs
{
  "user_id": "user-456",
  "plan_id": "document-analyzer",
  "run_id": "abc-123",              // optional: client-provided or server-generated
  
  "ground_inputs": {
    "{raw document}": "/uploads/report.pdf",
    "{analysis type}": "risk"
  },
  
  "agents": {
    "default": {
      "tools": {
        "llm_tool": {
          "llm_name": "gpt-4o",
          "llm_api": "openai"
        },
        "file_tool": {
          "base_dir": "/data/runs/{run_id}/",
          "save_api": "local"
        },
        "user_input_tool": {
          "input_api": "websocket"
        }
      }
    },
    "reviewer": {
      "tools": {
        "llm_tool": {
          "llm_name": "gpt-4o",       // same LLM as default agent
          "llm_api": "openai"
        },
        "file_tool": {
          "base_dir": "/data/runs/{run_id}/"
        }
        // no user_input_tool - this agent doesn't interact with user
      }
    }
  }
}
```

When the client provides agent configurations → Bodies are COMPLETE → Agents are ACTIVE for this run.

### 3.4 Provisions: Paradigms vs User-Tool

| Aspect     | Paradigms (HOW)                                | User-Tool Provisions (WHAT)                      |
| ---------- | ---------------------------------------------- | ------------------------------------------------ |
| Purpose    | Execution patterns                             | Content for tools                                |
| Examples   | `h_PromptTemplate-c_Generate-o_Text.json`    | `prompts/analyze.md`, `schemas/result.json`  |
| Created by | Platform Dev (built-ins), Plan Author (custom) | Plan Author                                      |
| Reusable   | Yes, across plans                              | No, plan-specific                                |
| Location   | `provisions/paradigms/`                      | `provisions/prompts/`, `provisions/schemas/` |

---

## 4. Deployment Model

### 4.1 Single Server Architecture

Everything deployed is contained in a single NormCode Server.

```
┌─────────────────────────────────────────────────────────────────┐
│                    NORMCODE SERVER                               │
│                    (Single Container)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API Layer                                   :8000       │   │
│  │  ├── /api/plans      Plan deployment & management       │   │
│  │  ├── /api/runs       Execution control                  │   │
│  │  ├── /api/checkpoints Resume & fork                     │   │
│  │  ├── /ws/runs/{id}   Live execution events              │   │
│  │  └── /               Canvas App UI (dev/operator only)  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Execution Engine                                        │   │
│  │  ├── Orchestrator (from infra/_orchest)                 │   │
│  │  ├── Agent Pool (configured Bodies)                     │   │
│  │  └── Tool Sandbox (file_system, python_interpreter)     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Storage                                                 │   │
│  │  ├── /data/plans/       Deployed plan packages          │   │
│  │  ├── /data/provisions/  Shared prompts, paradigms       │   │
│  │  ├── /data/runs/        Per-run state & artifacts       │   │
│  │  └── /data/config/      Server & agent configuration    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Per-Run Isolation

### 5.1 How Orchestrator Creates Isolated Runs

Each run creates its own isolated execution context with one or more agents:

```python
# For each POST /api/runs request:
run_id = request.run_id or str(uuid.uuid4())
user_id = request.user_id
run_dir = Path(f"/data/runs/{run_id}")

# Create agents from request configuration
agents = {}
for agent_name, agent_config in request.agents.items():
    agents[agent_name] = Body(
        llm_name=agent_config.tools.llm_tool.llm_name,
        llm_api=agent_config.tools.llm_tool.llm_api,
        base_dir=str(run_dir),
        file_api=agent_config.tools.file_tool.save_api,
        user_input_api=agent_config.tools.get("user_input_tool", {}).get("input_api")
    )

orchestrator = Orchestrator(
    concept_repo=loaded_concepts,      # Shared (read-only)
    inference_repo=loaded_inferences,  # Shared (read-only)
    agents=agents,                     # Per-run: multiple named agents
    db_path=str(run_dir / "run.db"),   # Per-run SQLite
    run_id=run_id,
    user_id=user_id
)
```

### 5.2 What's Shared vs Isolated

| Component         | Scope                        | Location                                      |
| ----------------- | ---------------------------- | --------------------------------------------- |
| **ConceptRepo**   | Per-plan (shared, read-only) | `/data/plans/{plan_id}/concept_repo.json`     |
| **InferenceRepo** | Per-plan (shared, read-only) | `/data/plans/{plan_id}/inference_repo.json`   |
| **Provisions**    | Per-plan (shared, read-only) | `/data/plans/{plan_id}/provisions/`           |
| **LLM Config**    | Server-wide (shared)         | `/data/config/llms.yaml`                      |
| **Orchestrator**  | Per-run (isolated)           | In-memory                                     |
| **Blackboard**    | Per-run (isolated)           | In-memory                                     |
| **Agents**        | Per-run (isolated)           | In-memory (multiple per run)                  |
| **Bodies**        | Per-agent (isolated)         | In-memory (one per agent)                     |
| **Run Database**  | Per-run (isolated)           | `/data/runs/{run_id}/run.db`                  |
| **Outputs**       | Per-run (isolated)           | `/data/runs/{run_id}/outputs/`                |

### 5.3 Database Schema (Per-Run SQLite)

```sql
-- Checkpoints (resumable state)
CREATE TABLE checkpoints (
    run_id TEXT,
    cycle INTEGER,
    inference_count INTEGER DEFAULT 0,
    state_json TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (run_id, cycle, inference_count)
);

-- Execution history
CREATE TABLE executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    cycle INTEGER,
    flow_index TEXT,
    inference_type TEXT,
    status TEXT,
    concept_inferred TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Logs
CREATE TABLE logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    execution_id INTEGER,
    log_content TEXT,
    FOREIGN KEY(execution_id) REFERENCES executions(id)
);
```

### 5.4 Resume and Fork

```python
# Resume: Continue same run from checkpoint
orchestrator = Orchestrator.load_checkpoint(
    db_path="/data/runs/{run_id}/run.db",
    run_id=run_id,
    cycle=3  # Optional: specific checkpoint
)

# Fork: Branch into new run from checkpoint
orchestrator = Orchestrator.load_checkpoint(
    db_path="/data/runs/{source_run_id}/run.db",
    run_id=source_run_id,
    new_run_id=new_run_id,  # Creates new isolated run
    cycle=3
)
```

---

## 6. Plan Package Format

### 6.1 Package Structure

A plan is deployed as a self-contained `.zip`:

```
my-plan.zip
├── manifest.json           # Plan metadata
├── concept_repo.json       # Compiled concepts
├── inference_repo.json     # Compiled inferences
└── provisions/
    ├── prompts/            # Plan-specific prompts
    │   └── analyze.md
    ├── paradigms/          # Plan-specific paradigms (optional)
    │   └── custom_flow.json
    └── schemas/            # Plan-specific schemas
        └── result.schema.json
```

### 6.2 manifest.json

```json
{
  "name": "document-analysis",
  "version": "1.0.0",
  "description": "Analyzes documents and extracts key information",
  "entry": {
    "concepts": "concept_repo.json",
    "inferences": "inference_repo.json"
  },
  "inputs": {
    "{raw document}": {
      "type": "file",
      "required": true,
      "description": "Document to analyze"
    },
    "{analysis type}": {
      "type": "string",
      "required": false,
      "default": "summary"
    }
  },
  "outputs": {
    "{document summary}": {
      "type": "object",
      "description": "Analysis result"
    }
  },
  "default_agent": "qwen-plus"
}
```

---

## 7. Server API

### 7.1 Plans

| Method     | Endpoint              | Description                                  |
| ---------- | --------------------- | -------------------------------------------- |
| `POST`   | `/api/plans/deploy` | Upload and deploy a plan package             |
| `GET`    | `/api/plans`        | List all deployed plans                      |
| `GET`    | `/api/plans/{id}`   | Get plan details (including required inputs) |
| `DELETE` | `/api/plans/{id}`   | Undeploy a plan                              |

### 7.2 Runs

| Method   | Endpoint                  | Description                     |
| -------- | ------------------------- | ------------------------------- |
| `POST` | `/api/runs`             | Start a new run                 |
| `GET`  | `/api/runs`             | List all runs                   |
| `GET`  | `/api/runs/{id}`        | Get run status                  |
| `GET`  | `/api/runs/{id}/result` | Get run result (when completed) |
| `POST` | `/api/runs/{id}/pause`  | Pause execution                 |
| `POST` | `/api/runs/{id}/resume` | Resume from pause               |
| `POST` | `/api/runs/{id}/stop`   | Stop execution                  |

### 7.3 Checkpoints

| Method   | Endpoint                             | Description                  |
| -------- | ------------------------------------ | ---------------------------- |
| `GET`  | `/api/checkpoints/{run_id}`        | List checkpoints for a run   |
| `POST` | `/api/checkpoints/{run_id}/resume` | Resume from checkpoint       |
| `POST` | `/api/checkpoints/{run_id}/fork`   | Fork new run from checkpoint |

### 7.4 WebSocket Events

| Endpoint          | Events                                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------------------------- |
| `/ws/runs/{id}` | `inference:started`, `inference:completed`, `inference:failed`, `run:completed`, `run:failed` |

### 7.5 Example: Start Run

```bash
curl -X POST http://localhost:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-456",
    "plan_id": "document-analysis",
    "ground_inputs": {
      "{raw document}": "/uploads/report.pdf",
      "{analysis type}": "risk"
    },
    "agents": {
      "default": {
        "tools": {
          "llm_tool": { "llm_name": "gpt-4o", "llm_api": "openai" },
          "file_tool": { "base_dir": "/data/runs/{run_id}/" }
        }
      }
    }
  }'
```

Response:

```json
{
  "run_id": "abc-123-def-456",
  "user_id": "user-456",
  "status": "started",
  "plan_id": "document-analysis",
  "agents": ["default"]
}
```

---

## 8. Configuration

### 8.1 Server Config (`/data/config/server.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8000

storage:
  plans_dir: "/data/plans"
  runs_dir: "/data/runs"
  provisions_dir: "/data/provisions"

execution:
  max_concurrent_runs: 10
  default_max_cycles: 100
  checkpoint_frequency: 5  # Save every N inferences (null = end of cycle only)

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "json"
```

### 8.2 LLM Config (`/data/config/llms.yaml`)

Defines available LLMs that agents can use. Multiple agents can share the same LLM.

```yaml
llms:
  qwen-plus:
    provider: dashscope
    model: qwen-plus
    api_key_env: DASHSCOPE_API_KEY

  gpt-4o:
    provider: openai
    model: gpt-4o
    api_key_env: OPENAI_API_KEY

  claude-sonnet:
    provider: anthropic
    model: claude-3-sonnet-20240229
    api_key_env: ANTHROPIC_API_KEY

  demo:
    provider: mock
    description: "Mock LLM for testing (no API calls)"

default_llm: qwen-plus
```

---

## 9. Docker Deployment

### 9.1 Container Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTAINER                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  /app/                        Application code                   │
│  ├── server/                  FastAPI backend                    │
│  ├── frontend/dist/           Built React app (static)           │
│  └── infra/                   NormCode core                      │
│                                                                  │
│  /data/                       Mounted volume (persistent)        │
│  ├── plans/                   Deployed plan packages             │
│  ├── provisions/              Shared prompts, paradigms          │
│  ├── runs/                    Per-run SQLite + artifacts         │
│  └── config/                  Server + agent configuration       │
│                                                                  │
│  Process: uvicorn server:app                                     │
│  Port: 8000                                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Dockerfile

```dockerfile
# Stage 1: Frontend Builder
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY canvas_app/frontend/package*.json ./
RUN npm ci
COPY canvas_app/frontend/ ./
RUN npm run build

# Stage 2: Python Dependencies
FROM python:3.11-slim AS python-deps
WORKDIR /deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY canvas_app/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY infra/ /tmp/infra/
COPY setup.py pyproject.toml /tmp/
WORKDIR /tmp
RUN pip install --no-cache-dir -e . || pip install --no-cache-dir .

# Stage 3: Runtime
FROM python:3.11-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=python-deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY infra/ ./infra/
COPY canvas_app/backend/ ./server/
COPY --from=frontend-builder /build/dist ./frontend/dist/

RUN mkdir -p /data/plans /data/provisions /data/runs /data/config
ENV NORMCODE_DATA_DIR=/data
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 9.3 docker-compose.yaml

```yaml
version: '3.8'

services:
  normcode:
    build:
      context: ..
      dockerfile: deployment/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - normcode-data:/data
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - NORMCODE_ENV=production
      - LOG_LEVEL=INFO
    restart: always

volumes:
  normcode-data:
```

### 9.4 Usage

```bash
# Start server
docker-compose up -d

# Deploy a plan
curl -X POST http://localhost:8000/api/plans/deploy \
  -F "plan=@my-plan.zip"

# Start execution
curl -X POST http://localhost:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"plan_id": "my-plan", "inputs": {"query": "Hello"}}'

# Open Canvas App (for operators/authors only)
open http://localhost:8000
```

---

## 10. Data Residency Options

The Orchestrator is agnostic to where it runs. The deployment choice determines data location.

### 10.1 Option A: Server-Side (Default)

All data stored on NormCode Server.

```
Client (thin)              NormCode Server
├── Sends inputs    ──►    /data/runs/{run_id}/
├── Receives results ◄──   ├── run.db      ◄── USER DATA
└── No local execution     ├── inputs/     ◄── USER DATA
                           └── outputs/    ◄── USER DATA
```

**Use case**: Team deployment, managed service
**Pros**: Simple client, centralized management
**Cons**: User data leaves their environment

### 10.2 Option B: Client-Side (Local)

All data stays on client machine.

```
Client (thick, has infra bundled)
├── infra/
├── plans/
└── runs/
    └── {run_id}/
        ├── run.db      ◄── USER DATA (never leaves)
        └── outputs/    ◄── USER DATA (never leaves)
```

**Use case**: Privacy-sensitive domains (legal, medical), air-gapped
**Pros**: Full data sovereignty
**Cons**: Heavier client, user manages updates

### 10.3 Option C: Hybrid

Plans from server, data stays local.

```
Client                         NormCode Server
├── Downloads plan once   ◄──  /api/plans/{id}/download
├── Executes locally           (plans only, no user data)
├── runs/
│   └── {run_id}/
│       └── run.db  ◄── LOCAL
└── Optional: sync status ──►  /api/runs/sync (metadata only)
```

**Use case**: Enterprise with central IT but data sovereignty requirements
**Pros**: Centralized plan management, local data
**Cons**: More complex architecture

### 10.4 Data Residency Summary

| Data Type    | Server-Side | Client-Side | Hybrid            |
| ------------ | ----------- | ----------- | ----------------- |
| Plans        | Server      | Client      | Server → Client  |
| User Inputs  | Server      | Client only | Client only       |
| Run State    | Server      | Client only | Client only       |
| Outputs      | Server      | Client only | Client only       |
| Run Metadata | Server      | Client only | Server (optional) |

---

## 11. Optional: MCP Integration

MCP (Model Context Protocol) integration is **optional** and can be added after core deployment is working.

### 11.1 Two Integration Modes

| Mode                             | Purpose                                               |
| -------------------------------- | ----------------------------------------------------- |
| **NormCode as MCP Server** | AI assistants (Claude) can trigger NormCode workflows |
| **NormCode as MCP Client** | Plan steps can call external MCP tools                |

### 11.2 NormCode as MCP Server

Exposes NormCode operations as MCP tools:

```
MCP Tools:
├── list_plans      - List deployed plans
├── start_run       - Start execution
├── get_run_status  - Check status
├── pause_run       - Pause execution
├── resume_run      - Resume from checkpoint
├── fork_run        - Branch from checkpoint
└── get_run_result  - Get completed result
```

### 11.3 NormCode as MCP Client

Body can call external MCP servers:

```python
# In Body
self.mcp = MCPClientTool()
self.mcp.configure({
    "database": {"command": "python", "args": ["db_mcp.py"]},
    "web-search": {"command": "npx", "args": ["-y", "@anthropic/mcp-server-brave-search"]}
})

# In paradigm
result = body.mcp.call_tool("database", "query", {"sql": "SELECT ..."})
```

### 11.4 NormCode vs MCP: Complementary

| Aspect    | MCP                       | NormCode                    |
| --------- | ------------------------- | --------------------------- |
| Purpose   | Give AI access to tools   | Execute structured plans    |
| Control   | AI decides what to call   | Plan defines the flow       |
| State     | Stateless                 | Fully managed (checkpoints) |
| Isolation | Context is shared         | Enforced by design          |
| Best for  | Interactive AI assistance | Auditable AI pipelines      |

**They're complementary**: MCP for the interface, NormCode for the execution engine.

---

## Implementation Phases

### Phase 1: Core (MVP)

- [ ] Restructure canvas_app → normcode_server
- [ ] Plan deployment API (`/api/plans/deploy`, `/api/plans`)
- [ ] Run execution API (`/api/runs`)
- [ ] Per-run SQLite isolation
- [ ] Docker packaging

### Phase 2: Complete Server

- [ ] Checkpoint resume/fork API
- [ ] WebSocket events
- [ ] Health check endpoints
- [ ] Agent configuration via YAML

### Phase 3: Production Hardening

- [ ] Concurrent run management
- [ ] Resource limits
- [ ] Structured logging
- [ ] Metrics

### Phase 4: Optional Enhancements

- [ ] MCP Server interface
- [ ] MCP Client in Body
- [ ] Hybrid deployment mode
- [ ] Plan versioning

---

## Key Principles

1. **Self-Contained**: One container has everything
2. **Plans as Artifacts**: Deploy plans, not code
3. **Per-Run Isolation**: Each run has its own Orchestrator, Body, and database
4. **API-First**: Everything accessible via REST/WebSocket
5. **Observable**: Canvas App built-in for debugging (dev/operator only)
6. **Resumable**: Checkpoints survive restarts
7. **Auditable**: Full execution trace for every run
8. **Data Flexible**: Server-side, client-side, or hybrid deployment

---

## Quick Reference

### Start Server

```bash
docker-compose up -d
```

### Deploy Plan

```bash
curl -X POST localhost:8000/api/plans/deploy -F "plan=@my-plan.zip"
```

### Run Plan

```bash
curl -X POST localhost:8000/api/runs \
  -d '{"plan_id": "my-plan", "inputs": {"query": "..."}}'
```

### Get Result

```bash
curl localhost:8000/api/runs/{run_id}/result
```

---

**End of Specification**
