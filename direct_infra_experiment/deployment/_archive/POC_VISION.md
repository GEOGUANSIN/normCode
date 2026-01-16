# NormCode Deployment: POC Vision

## The Core Idea

```
┌────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   Plan Author           Operator              End User                      │
│   writes .ncds   ──►    deploys plan   ──►    fills inputs   ──►   RESULT  │
│                         to server             via client                    │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

**One sentence**: A Plan Author creates structured AI workflows, an Operator deploys them to a NormCode Server, and End Users activate agents by filling open input slots.

---

## What Gets Deployed

```
my-plan.zip
├── concept_repo.json      # The plan structure
├── inference_repo.json    # Execution definitions
└── provisions/
    ├── prompts/*.md       # LLM instructions
    └── schemas/*.json     # Output formats
```

The plan is **compiled and self-contained**. No code changes at runtime.

---

## The Server

```
┌─────────────────────────────────────────┐
│           NORMCODE SERVER               │
├─────────────────────────────────────────┤
│                                         │
│  API          /api/plans   (deploy)     │
│               /api/runs    (execute)    │
│                                         │
│  Engine       Orchestrator + Body       │
│               (from infra/)             │
│                                         │
│  Storage      /data/plans/              │
│               /data/runs/               │
│                                         │
└─────────────────────────────────────────┘
```

**Single container. Everything inside.**

---

## How It Activates

The Body has **open slots**. Client fills them. Agent becomes active.

```
POST /api/runs
{
  "plan_id": "doc-analyzer",
  "inputs": {
    "document": "/path/to/file.pdf",     ← fills file_system slot
    "query": "Summarize the findings"     ← fills user_input slot
  }
}
```

**Result**: An agent instance runs specifically for this client.

---

## Four Roles

| Role | Does | Touches |
|------|------|---------|
| **Platform Dev** | Builds the system | Sequences, Body tools, built-in paradigms |
| **Plan Author** | Writes plans | .ncds files, prompts, schemas |
| **Operator** | Runs the server | Docker, config, deployments |
| **End User** | Uses the results | Client apps, fills inputs |

---

## POC Scope

### Phase 1: Minimal Server
- [ ] Single plan deployment via API
- [ ] Single run execution
- [ ] Basic REST endpoints

### Phase 2: Complete Flow
- [ ] Plan package format (.zip)
- [ ] Body's APIs (input slots)
- [ ] Real-time events (WebSocket)

### Phase 3: Production
- [ ] Docker containerization
- [ ] Multi-plan support
- [ ] Checkpoints/resume

---

## What This Enables

| Without Server | With Server |
|----------------|-------------|
| Run locally only | Run anywhere via API |
| Manual file setup | Deploy as artifact |
| Developer-only | End users can use |
| Single run | Concurrent runs |
| Lost on crash | Checkpoints persist |

---

## The Simplest Test

```bash
# 1. Start server
docker-compose up -d

# 2. Deploy a plan
curl -X POST localhost:8000/api/plans/deploy -F "plan=@my-plan.zip"

# 3. Run with inputs
curl -X POST localhost:8000/api/runs \
  -d '{"plan_id": "my-plan", "inputs": {"query": "Hello"}}'

# 4. Get result
curl localhost:8000/api/runs/{id}/result
```

**If this works, the POC is complete.**

