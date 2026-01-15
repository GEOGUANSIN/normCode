# NormCode Deployment Vision

## Core Principle

**Everything deployed is contained in a single server.**

The NormCode Server is the deployment target. Plans are artifacts deployed into it.

---

## The Deployment Model

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   Author Plans  ───→  Package Plans  ───→  Deploy to Server     │
│   (.ncds → .ncd)      (.zip artifact)      (POST /api/plans)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| Concept | Description |
|---------|-------------|
| **NormCode Server** | Self-contained execution environment |
| **Plan Package** | Deployable artifact (repos + provisions) |
| **Run** | Single execution of a deployed plan |
| **Checkpoint** | Resumable state within a run |

---

## Server Architecture

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
│  │  ├── /ws/events      Live execution events              │   │
│  │  └── /               Canvas App UI                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Execution Engine                                        │   │
│  │  ├── Orchestrator (from infra)                          │   │
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

## Plan Package Format

A plan is deployed as a self-contained `.zip`:

```
my-plan.zip
├── manifest.json           # Plan metadata
├── concept_repo.json       # Compiled concepts
├── inference_repo.json     # Compiled inferences
└── provisions/
    ├── prompts/            # Plan-specific prompts
    ├── paradigms/          # Plan-specific paradigms
    └── schemas/            # Plan-specific schemas
```

**manifest.json:**
```json
{
  "name": "document-analysis",
  "version": "1.0.0",
  "entry": {
    "concepts": "concept_repo.json",
    "inferences": "inference_repo.json"
  },
  "inputs": {
    "{raw document}": {"type": "file", "required": true}
  },
  "default_agent": "qwen-plus"
}
```

---

## API Contract

### Plans

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/plans/deploy` | Upload and deploy a plan package |
| `GET` | `/api/plans` | List all deployed plans |
| `GET` | `/api/plans/{id}` | Get plan details |
| `DELETE` | `/api/plans/{id}` | Undeploy a plan |

### Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/runs` | Start a new run |
| `GET` | `/api/runs` | List all runs |
| `GET` | `/api/runs/{id}` | Get run status |
| `POST` | `/api/runs/{id}/pause` | Pause execution |
| `POST` | `/api/runs/{id}/resume` | Resume from pause |
| `POST` | `/api/runs/{id}/stop` | Stop execution |

### Checkpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/checkpoints/{run_id}` | List checkpoints for a run |
| `POST` | `/api/checkpoints/{run_id}/resume` | Resume from checkpoint |
| `POST` | `/api/checkpoints/{run_id}/fork` | Fork new run from checkpoint |

### Events (WebSocket)

| Endpoint | Events |
|----------|--------|
| `/ws/runs/{id}` | `inference:started`, `inference:completed`, `inference:failed`, `run:completed` |

---

## Configuration

### Server Config (`/data/config/server.yaml`)

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
  checkpoint_frequency: 5
```

### Agent Config (`/data/config/agents.yaml`)

```yaml
agents:
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

default_agent: qwen-plus
```

---

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN cd frontend && npm ci && npm run build

EXPOSE 8000
ENV NORMCODE_DATA_DIR=/data

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yaml

```yaml
version: '3.8'

services:
  normcode:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - normcode-data:/data
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    restart: unless-stopped

volumes:
  normcode-data:
```

### Usage

```bash
# Start server
docker-compose up -d

# Deploy a plan
curl -X POST http://localhost:8000/api/plans/deploy \
  -F "plan=@my-plan.zip"

# Start execution
curl -X POST http://localhost:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"plan_id": "my-plan", "inputs": {"raw_document": "data:text/plain;base64,..."}}'

# Open Canvas App
open http://localhost:8000
```

---

## Evolution Path

The server evolves from the existing `canvas_app`:

| Current (canvas_app) | Server Addition |
|---------------------|-----------------|
| Projects with local paths | Plan packages (self-contained) |
| Manual file loading | Plan deployment API |
| Single project focus | Multi-plan registry |
| Development mode | Production Docker |
| `launch.py` | `docker-compose up` |

### Phase 1: Foundation
- [ ] Restructure canvas_app → normcode_server
- [ ] Add Dockerfile
- [ ] Environment-based configuration

### Phase 2: Plan Deployment
- [ ] Plan package format (.zip)
- [ ] Deploy/undeploy endpoints
- [ ] Plan registry

### Phase 3: Production Hardening
- [ ] Concurrent run management
- [ ] Resource limits
- [ ] Health checks
- [ ] Logging/metrics

---

## Key Principles

1. **Self-Contained**: One container has everything
2. **Plans as Artifacts**: Deploy plans, not code
3. **API-First**: Everything accessible via REST/WebSocket
4. **Observable**: Canvas App built-in for debugging
5. **Resumable**: Checkpoints survive restarts
6. **Auditable**: Full execution trace for every run

---

## What This Enables

- **Deploy once, run many**: One server handles multiple plans
- **Remote execution**: Trigger runs from anywhere via API
- **Team debugging**: Shared Canvas App for investigation
- **Portable**: Docker runs anywhere
- **Reproducible**: Same server + same plan = same behavior

