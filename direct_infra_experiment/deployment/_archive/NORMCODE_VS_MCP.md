# NormCode Server vs MCP Server

A comparison of NormCode Server and Model Context Protocol (MCP) Server architectures.

---

## Executive Summary

| Aspect | NormCode Server | MCP Server |
|--------|-----------------|------------|
| **Primary Purpose** | Execute structured AI workflows | Provide tools/context to AI models |
| **Core Abstraction** | Plan (DAG of inferences) | Resources + Tools + Prompts |
| **Execution Model** | Orchestrated multi-step | Single tool invocation |
| **State** | Managed (checkpoints, blackboard) | Stateless (or client-managed) |
| **Data Flow** | Explicit, isolated per step | Implicit, in model context |
| **Auditability** | Built-in (every step traced) | Depends on implementation |

**Key Insight**: They solve different problems and are **complementary**, not competing.

---

## What Each Does

### MCP Server

**Purpose**: Standardized protocol for AI assistants to access external capabilities.

```
┌─────────────────┐         ┌─────────────────┐
│  AI Assistant   │ ←─MCP─→ │   MCP Server    │
│  (Claude, etc)  │         │  (Your tools)   │
└─────────────────┘         └─────────────────┘
```

**MCP provides**:
- **Resources**: Read-only data (files, DB records, API responses)
- **Tools**: Executable functions (create file, query database, call API)
- **Prompts**: Reusable prompt templates

**Execution**: Single request → single response. The AI decides when/how to call tools.

### NormCode Server

**Purpose**: Execute pre-defined, structured AI workflows with data isolation.

```
┌─────────────────┐         ┌─────────────────┐
│  Client/Trigger │ ←─API─→ │ NormCode Server │
│                 │         │  (Orchestrator) │
└─────────────────┘         └─────────────────┘
                                    │
                            ┌───────┴───────┐
                            │   Plan (DAG)  │
                            │  Step1 → Step2 → Step3
                            └───────────────┘
```

**NormCode provides**:
- **Plans**: Structured inference graphs (what to do, in what order)
- **Orchestration**: Dependency-based execution with state management
- **Isolation**: Each step only sees explicitly passed data
- **Checkpointing**: Resume/fork execution from any point

**Execution**: Deploy plan → orchestrator executes all steps → return final result.

---

## Architecture Comparison

### MCP Server Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       MCP SERVER                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Protocol Handler (JSON-RPC over stdio/SSE/WebSocket)   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Resources  │  │   Tools     │  │   Prompts   │              │
│  │  (read)     │  │  (execute)  │  │ (templates) │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Protocol: JSON-RPC 2.0
Transport: stdio, HTTP+SSE, WebSocket
State: Stateless (each call independent)
```

### NormCode Server Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    NORMCODE SERVER                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  API Layer (REST + WebSocket)                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Orchestrator                                           │    │
│  │  ├── Waitlist (pending inferences)                      │    │
│  │  ├── Blackboard (concept states)                        │    │
│  │  └── Checkpoint Manager (persistence)                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Agent Pool (Bodies)                                    │    │
│  │  ├── LLM providers                                      │    │
│  │  ├── Tools (file_system, python_interpreter, etc.)      │    │
│  │  └── Paradigms (execution strategies)                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Storage                                                │    │
│  │  ├── Plans (deployed artifacts)                         │    │
│  │  ├── Runs (execution state)                             │    │
│  │  └── Checkpoints (resumable snapshots)                  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Protocol: REST + WebSocket
Transport: HTTP
State: Fully managed (persisted, resumable)
```

---

## Feature Comparison

| Feature | MCP Server | NormCode Server |
|---------|------------|-----------------|
| **Multi-step workflows** | ❌ Client orchestrates | ✅ Server orchestrates |
| **Data isolation** | ❌ All in context | ✅ Explicit per step |
| **Checkpointing** | ❌ Not built-in | ✅ Built-in |
| **Auditability** | ⚠️ Logging optional | ✅ Every step traced |
| **Tool execution** | ✅ Core feature | ✅ Via Body |
| **Resource access** | ✅ Core feature | ✅ Via provisions |
| **Prompt templates** | ✅ Core feature | ✅ Via paradigms |
| **Resumable execution** | ❌ Not applicable | ✅ Fork/resume |
| **Cost tracking** | ❌ Not built-in | ✅ Semantic vs syntactic |
| **Visual debugging** | ❌ Not built-in | ✅ Canvas App |
| **Protocol standard** | ✅ JSON-RPC spec | ⚠️ Custom REST |

---

## Execution Model Comparison

### MCP: Tool-Centric (AI Decides)

```
AI Model
    │
    ├── "I need to read file X"
    │       └── MCP: resources/read("X") → content
    │
    ├── "I should query the database"
    │       └── MCP: tools/call("query", {sql: "..."}) → results
    │
    └── "Let me analyze and respond"
            └── (internal reasoning)

The AI model decides:
- WHEN to call tools
- WHICH tools to call
- HOW to use results
```

### NormCode: Plan-Centric (Orchestrator Decides)

```
Plan (pre-defined DAG)
    │
    ├── Step 1.1: Read document
    │       └── Orchestrator executes, stores result
    │
    ├── Step 1.2: Extract entities (depends on 1.1)
    │       └── Orchestrator waits for 1.1, then executes
    │
    └── Step 1.3: Generate summary (depends on 1.2)
            └── Orchestrator waits for 1.2, then executes

The orchestrator decides:
- WHEN steps execute (dependency-based)
- WHICH data each step sees (explicit isolation)
- HOW to handle failures (checkpointing)
```

---

## State Management

### MCP: Stateless

```
Request 1: tools/call("create_file", {path: "a.txt", content: "..."})
    └── Response: {success: true}

Request 2: tools/call("read_file", {path: "a.txt"})
    └── Response: {content: "..."}

Each request is independent. 
The MCP server doesn't remember Request 1 when handling Request 2.
Client (AI) maintains conversation context.
```

### NormCode: Stateful

```
Run started: run_id = "abc-123"
    │
    ├── Inference 1.1 completed → Blackboard updated
    │       Checkpoint saved: cycle=1, inference=1
    │
    ├── Inference 1.2 completed → Blackboard updated
    │       Checkpoint saved: cycle=1, inference=2
    │
    └── [Server restart]
    
Resume: POST /api/runs/abc-123/resume
    └── Orchestrator reloads from checkpoint, continues from 1.3

Server maintains full execution state.
Resumable across restarts.
```

---

## When to Use Which

### Use MCP Server When:

- AI assistant needs **ad-hoc access** to tools/data
- The AI should **decide** what to do next
- Workflow is **conversational** (human-in-the-loop)
- You want **standardized integration** with AI assistants
- Simple tool exposure is sufficient

**Example**: Claude Desktop accessing your local files, databases, APIs

### Use NormCode Server When:

- Workflow is **pre-defined** and complex (5+ steps)
- **Data isolation** is critical (compliance, security)
- Execution must be **auditable** (trace every decision)
- Long-running workflows need **checkpointing**
- **Cost control** matters (minimize LLM calls)
- Visual **debugging** is needed

**Example**: Legal document analysis pipeline, financial risk assessment

---

## Complementary Usage

They can work together:

### Option 1: NormCode Exposes MCP Interface

```
┌─────────────────┐         ┌─────────────────┐
│  AI Assistant   │ ←─MCP─→ │ NormCode Server │
│  (Claude)       │         │  (as MCP server)│
└─────────────────┘         └─────────────────┘

MCP Tools exposed:
- deploy_plan(zip) → plan_id
- start_run(plan_id, inputs) → run_id  
- get_run_status(run_id) → status
- resume_run(run_id, checkpoint) → run_id
```

The AI can trigger NormCode workflows via MCP.

### Option 2: NormCode Uses MCP Tools

```
┌─────────────────┐         ┌─────────────────┐
│ NormCode Server │ ←─MCP─→ │   MCP Servers   │
│  (Orchestrator) │         │  (external)     │
└─────────────────┘         └─────────────────┘

NormCode Body could include an MCP client:
- body.mcp.call_tool("server_name", "tool_name", args)
- body.mcp.read_resource("server_name", "resource_uri")
```

NormCode steps can invoke external MCP tools.

### Option 3: Hybrid Architecture

```
┌─────────────────┐
│  AI Assistant   │
│  (Claude)       │
└────────┬────────┘
         │ MCP
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NORMCODE SERVER                               │
│                    (Implements MCP)                              │
├─────────────────────────────────────────────────────────────────┤
│  MCP Layer (for AI assistants)                                  │
│  ├── resources: list deployed plans, run results                │
│  ├── tools: deploy_plan, start_run, pause_run, resume_run       │
│  └── prompts: plan templates                                    │
├─────────────────────────────────────────────────────────────────┤
│  Orchestrator (executes plans)                                  │
│  └── Agent Pool                                                 │
│        └── Body (uses external MCP servers as tools)            │
│              ├── MCP: database-server (query tool)              │
│              ├── MCP: file-server (file operations)             │
│              └── MCP: api-server (external APIs)                │
└─────────────────────────────────────────────────────────────────┘
```

NormCode is both an MCP server (for AI assistants) and an MCP client (for external tools).

---

## Summary

| Dimension | MCP | NormCode |
|-----------|-----|----------|
| **Philosophy** | "Give AI access to tools" | "Execute structured plans" |
| **Control** | AI decides | Plan defines |
| **Granularity** | Single tool call | Multi-step workflow |
| **State** | Client-managed | Server-managed |
| **Isolation** | None (context is shared) | Enforced (by design) |
| **Resumability** | N/A | Built-in |
| **Best for** | Interactive AI assistance | Auditable AI pipelines |

**They're complementary**:
- MCP: How AI accesses capabilities
- NormCode: How AI executes structured workflows

A production system might use both: MCP for the interface, NormCode for the execution engine.

