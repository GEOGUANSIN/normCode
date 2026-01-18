# Agent Architecture and Role Access

How NormCode's Agent system (Sequences, Body, Provisions) relates to different user roles.

---

## Agent System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT SYSTEM                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  SEQUENCES (How inferences execute)                                  │    │
│  │  ├── Semantic: imperative, judgement                                │    │
│  │  └── Syntactic: assigning, grouping, timing, looping               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  BODY (Tools available to the agent)                                │    │
│  │  ├── llm              (language model interface)                    │    │
│  │  ├── prompt_tool      (prompt loading and templating)              │    │
│  │  ├── file_system      (read/write files)          ◄─── has open API│    │
│  │  ├── python_interpreter (execute Python scripts)                   │    │
│  │  ├── composition_tool (compose outputs)                            │    │
│  │  ├── formatter_tool   (format/parse data)                          │    │
│  │  ├── user_input       (request human input)       ◄─── has open API│    │
│  │  └── paradigm_tool    (load paradigms)                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  PROVISIONS (Resources that configure execution)                    │    │
│  │  ├── Paradigms    (HOW - execution patterns)                       │    │
│  │  └── User-Tool    (WHAT - prompts, schemas, scripts)               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│  ════════════════════════════╪══════════════════════════════════════════    │
│  INTERNAL                    │  BOUNDARY                      EXTERNAL      │
│  ════════════════════════════╪══════════════════════════════════════════    │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  BODY's APIs (Open slots that clients fill to activate agent)       │    │
│  │  ├── user_input: ???   ◄── client provides: "user query text"      │    │
│  │  ├── file_system: ???  ◄── client provides: "/path/to/file.pdf"    │    │
│  │  └── llm: ???          ◄── client provides: "gpt-4o" (optional)    │    │
│  │                                                                     │    │
│  │  When filled → Body is COMPLETE → Agent is ACTIVE for this client  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Deep Dive

### 1. Sequences

Sequences define **how** an inference executes - the step-by-step flow.

| Sequence | Type | LLM Call? | Purpose |
|----------|------|-----------|---------|
| `imperative` | Semantic | ✅ Yes | Execute a command, generate output |
| `imperative_in_composition` | Semantic | ✅ Yes | Imperative with paradigm composition |
| `imperative_direct` | Semantic | ✅ Yes | Direct LLM call without paradigm |
| `imperative_python` | Semantic | ✅ Yes | Generate and execute Python |
| `imperative_input` | Semantic | ❌ No* | Request user input |
| `judgement` | Semantic | ✅ Yes | Evaluate a condition (true/false) |
| `judgement_in_composition` | Semantic | ✅ Yes | Judgement with paradigm composition |
| `judgement_direct` | Semantic | ✅ Yes | Direct LLM judgement |
| `assigning` | Syntactic | ❌ No | Route/select data |
| `grouping` | Syntactic | ❌ No | Collect items into structure |
| `timing` | Syntactic | ❌ No | Control execution flow |
| `looping` | Syntactic | ❌ No | Iterate over collections |

**Sequence Selection**: The compiler determines the sequence based on the functional concept's syntax and annotations.

### 2. Body (Tools)

The Body provides **capabilities** - what the agent can do.

```python
class Body:
    # Language Model Interface
    llm: LanguageModel              # Generate text, embeddings
    
    # Resource Access
    prompt_tool: PromptTool         # Load prompt templates
    file_system: FileSystemTool     # Read/write files
    paradigm_tool: ParadigmTool     # Load paradigm definitions
    
    # Execution
    python_interpreter: PythonInterpreterTool  # Run Python code
    composition_tool: CompositionTool          # Compose outputs
    formatter_tool: FormatterTool              # Format/parse data
    
    # Interaction
    user_input: UserInputTool       # Request human input
    
    # State
    buffer: BufferTool              # Temporary storage
    
    # Perception
    perception_router: PerceptionRouter  # Sign transmutation
```

**Body Configuration**: Operators configure which LLM provider, API keys, and base directories are used.

### 3. Provisions

Provisions are **resources** that customize execution. They divide into two categories:

#### 3.1 Paradigms (Execution Patterns)

Paradigms define **how** an inference executes - the orchestration of Body tools.

| Aspect | Description |
|--------|-------------|
| **Purpose** | Compose multiple Body tool calls into a reusable pattern |
| **Format** | `.json` files in `paradigms/` |
| **Created by** | Platform Dev (built-ins), Plan Author (custom) |
| **Selected by** | Plan Author (annotations), Operator (defaults) |
| **Used by** | Orchestrator (at runtime) |

**Paradigm Structure**:
```json
{
  "name": "h_PromptTemplate-c_GenerateThinkJson-o_Literal",
  "metadata": {
    "description": "Load prompt, generate with thinking, extract JSON",
    "inputs": {
      "vertical": {"prompt_template": "Path to prompt file"},
      "horizontal": {"input_data": "Data to include in prompt"}
    }
  },
  "composition": [
    {"step": "load_prompt", "action": "body.prompt_tool.load", ...},
    {"step": "generate", "action": "body.llm.generate", ...},
    {"step": "extract", "action": "body.formatter_tool.extract_json", ...}
  ]
}
```

**Key insight**: Paradigms reference other provisions (like prompts) but don't contain them.

#### 3.2 User-Tool-Specific Provisions (Tool Content)

These are **what** content specific Body tools consume during execution.

| Provision Type | For Tool | Format | Purpose | Example |
|----------------|----------|--------|---------|---------|
| **Prompts** | `prompt_tool` | `.md` | LLM instruction templates | `summarize.md` |
| **Schemas** | `formatter_tool` | `.json` | Output structure definitions | `analysis_result.schema.json` |
| **Scripts** | `python_interpreter` | `.py` | Python code to execute | `transform_data.py` |
| **Templates** | `file_system` | `.*` | File templates to generate | `report_template.html` |

```
┌───────────────────────────────────────────────────────────────────────────────┐
│  PARADIGMS vs USER-TOOL-SPECIFIC PROVISIONS                                    │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  PARADIGMS (HOW)                       USER-TOOL PROVISIONS (WHAT)             │
│  ──────────────────                    ─────────────────────────────           │
│                                                                                │
│  ┌─────────────────────────┐          ┌─────────────────────────┐             │
│  │ h_PromptTemplate-...    │          │ prompts/                │             │
│  │                         │   uses   │   ├── summarize.md      │             │
│  │ Step 1: load_prompt ────┼─────────►│   ├── analyze.md        │             │
│  │ Step 2: generate        │          │   └── extract.md        │             │
│  │ Step 3: extract_json ───┼───────┐  └─────────────────────────┘             │
│  └─────────────────────────┘       │                                          │
│                                    │  ┌─────────────────────────┐             │
│                                    └─►│ schemas/                │             │
│                                       │   └── result.schema.json│             │
│                                       └─────────────────────────┘             │
│                                                                                │
│  Defines: orchestration logic          Contains: actual content               │
│  Created by: Platform Dev / Author     Created by: Plan Author                │
│  Reusable across plans: ✅             Plan-specific: ✅                       │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

**Directory Structure**:
```
my-plan/
├── plan.ncds
├── provisions/
│   ├── paradigms/           ← HOW (execution patterns)
│   │   └── custom_flow.json
│   ├── prompts/             ← WHAT (for prompt_tool)
│   │   ├── summarize.md
│   │   └── analyze.md
│   ├── schemas/             ← WHAT (for formatter_tool)
│   │   └── result.schema.json
│   └── scripts/             ← WHAT (for python_interpreter)
│       └── transform.py
└── manifest.json
```

### 4. Body's APIs

Body's APIs are **open-ended input slots** that Platform Developers leave in Body tools. When a client connects to run a plan, they provide specific values for these APIs, making the Body **complete** and the agent **active for that client**.

| Body Tool | Open API | What Client Provides | Example |
|-----------|----------|---------------------|---------|
| `user_input` | User data inputs | Text, choices, confirmations | `{"name": "John", "task": "analyze"}` |
| `file_system` | File locations | Paths to read/write | `{"input_file": "/data/doc.pdf"}` |
| `python_interpreter` | Script parameters | Runtime variables | `{"threshold": 0.8}` |
| `llm` | Model override | Preferred LLM | `{"agent": "gpt-4o"}` |

**Key Concept**:
- **Body Tools** = Capabilities with open parameters (designed by Platform Dev)
- **Body's APIs** = Those open parameters that clients fill to activate an agent

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                    HOW BODY's APIs COMPLETE AN AGENT                           │
├───────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  BODY (incomplete - has open slots)          CLIENT (provides values)          │
│  ─────────────────────────────────           ─────────────────────────         │
│                                                                                │
│  ┌─────────────────────────────┐            ┌─────────────────────────┐       │
│  │ user_input                  │            │ POST /api/runs          │       │
│  │   ├── ???  ◄────────────────┼────────────┼─ "user_name": "Alice"   │       │
│  │   └── ???  ◄────────────────┼────────────┼─ "query": "summarize"   │       │
│  │                             │            │                         │       │
│  │ file_system                 │            │ {                       │       │
│  │   ├── input_path: ???  ◄────┼────────────┼─   "input": "/doc.pdf"  │       │
│  │   └── output_path: ??? ◄────┼────────────┼─   "output": "/out.md"  │       │
│  │                             │            │ }                       │       │
│  │ llm                         │            │                         │       │
│  │   └── agent: ???  ◄─────────┼────────────┼─ "agent": "claude"      │       │
│  └─────────────────────────────┘            └─────────────────────────┘       │
│                                                                                │
│  Platform Dev DESIGNS the slots             End User FILLS the slots           │
│  (what inputs are needed)                   (with their specific data)         │
│                                                                                │
│                         ═══════════════════════════                            │
│                              AGENT NOW ACTIVE                                  │
│                         ═══════════════════════════                            │
│                                                                                │
└───────────────────────────────────────────────────────────────────────────────┘
```

**How it works in a run request**:
```json
// Client connects to NormCode server and provides Body's API values
POST /api/runs
{
  "plan_id": "document-analyzer",
  
  // Body's APIs - client fills these slots to complete the agent
  "inputs": {
    "document_path": "/uploads/report.pdf",    // for file_system
    "user_query": "What are the key findings?", // for user_input
    "output_format": "markdown"                 // for formatter_tool
  },
  
  // Optional: override default agent
  "agent": "gpt-4o"
}
```

**The activation flow**:
```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│  1. PLATFORM DEV designs Body with open APIs                                  │
│     Body has tools with parameters marked as "client-provided"                │
│                                                                               │
│  2. PLAN AUTHOR writes plan that uses these tools                             │
│     Plan references: <- user query, <- input document                         │
│                                                                               │
│  3. OPERATOR deploys plan to server                                           │
│     Server knows which inputs the plan expects                                │
│                                                                               │
│  4. END USER connects and provides values                                     │
│     POST /api/runs { inputs: { user_query: "...", document: "..." } }         │
│                                                                               │
│  5. SERVER creates COMPLETE agent instance                                    │
│     Body's open slots are now filled → agent is ACTIVE for this client        │
│                                                                               │
│  6. ORCHESTRATOR executes with the complete Body                              │
│     Agent runs with client's specific inputs                                  │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Role Access Matrix

### Overview

| Component | Platform Dev | Plan Author | Operator | End User |
|-----------|-------------|-------------|----------|----------|
| **Sequences** | Create/Modify | Use (via syntax) | - | - |
| **Body Tools** | Create built-ins | Use (via paradigms) | Configure (LLM, dirs) | - |
| **Paradigms** | Create built-ins | Create custom / Select | Select defaults | - |
| **User-Tool Provisions** | Create examples | Create plan-specific | Manage shared | - |
| ↳ Prompts | - | Create | Deploy | - |
| ↳ Schemas | - | Create | Deploy | - |
| ↳ Scripts | - | Create | Deploy | - |
| **Body's APIs** | Design (open slots) | Reference (in plan) | Expose (via server) | Fill (to activate) |

---

## Detailed Access by Role

### Platform Developer

**Full access** - builds the agent infrastructure.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLATFORM DEVELOPER ACCESS                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SEQUENCES                                                                   │
│  ├── ✅ CREATE new sequence types                                           │
│  ├── ✅ MODIFY existing sequences                                           │
│  ├── ✅ ADD new steps to sequences                                          │
│  └── ✅ DEFINE step execution logic                                         │
│                                                                              │
│  BODY                                                                        │
│  ├── ✅ CREATE new tools                                                    │
│  ├── ✅ MODIFY tool implementations                                         │
│  ├── ✅ ADD new LLM providers                                               │
│  └── ✅ EXTEND perception router                                            │
│                                                                              │
│  PROVISIONS                                                                  │
│  ├── ✅ CREATE built-in paradigms                                           │
│  ├── ✅ DEFINE paradigm structure                                           │
│  └── ✅ CREATE example provisions                                           │
│                                                                              │
│  Files Modified:                                                             │
│  • infra/_agent/_sequences/*.py                                             │
│  • infra/_agent/_steps/**/*.py                                              │
│  • infra/_agent/_body.py                                                    │
│  • infra/_agent/_models/*.py                                                │
│  • infra/_agent/_models/_paradigms/*.json                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Plan Author

**Use and extend** - writes plans and creates plan-specific provisions.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLAN AUTHOR ACCESS                                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SEQUENCES                                                                   │
│  ├── ❌ Cannot create new sequences                                         │
│  ├── ✅ USE sequences via .ncds syntax                                      │
│  │      <- result                                                           │
│  │          <= analyze this document    ← triggers imperative sequence      │
│  │          <- document                                                     │
│  │                                                                          │
│  ├── ✅ CHOOSE sequence via annotations                                     │
│  │      |%{sequence}: imperative_in_composition                             │
│  │      |%{sequence}: judgement_direct                                      │
│  └── ✅ UNDERSTAND sequence behavior for debugging                          │
│                                                                              │
│  BODY                                                                        │
│  ├── ❌ Cannot create new tools                                             │
│  ├── ✅ USE tools indirectly via paradigms                                  │
│  │      Paradigm calls body.llm.generate internally                         │
│  └── ✅ REFERENCE file paths that body.file_system will access             │
│                                                                              │
│  PROVISIONS                                                                  │
│  ├── ✅ CREATE prompts for their plan                                       │
│  │      provisions/prompts/analyze_document.md                              │
│  │                                                                          │
│  ├── ✅ CREATE schemas for their plan                                       │
│  │      provisions/schemas/analysis_result.json                             │
│  │                                                                          │
│  ├── ✅ CREATE custom paradigms (advanced)                                  │
│  │      provisions/paradigms/my_custom_pattern.json                         │
│  │                                                                          │
│  ├── ✅ SELECT built-in paradigms via annotations                           │
│  │      |%{paradigm}: h_PromptTemplate-c_GenerateThinkJson-o_Literal        │
│  │                                                                          │
│  └── ✅ REFERENCE provisions in annotations                                 │
│         |%{prompt_location}: provisions/prompts/analyze.md                  │
│                                                                              │
│  Files Created:                                                              │
│  • my-plan/plan.ncds                                                        │
│  • my-plan/provisions/prompts/*.md                                          │
│  • my-plan/provisions/schemas/*.json                                        │
│  • my-plan/provisions/paradigms/*.json (optional)                           │
│  • my-plan/manifest.json                                                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Operator

**Configure, manage, and expose** - sets up agents, deploys provisions, and creates APIs for End Users.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  OPERATOR ACCESS                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SEQUENCES                                                                   │
│  ├── ❌ Cannot create or modify sequences                                   │
│  ├── ❌ Cannot choose sequences (plan determines this)                      │
│  └── ✅ VIEW which sequences a plan uses (for monitoring)                   │
│                                                                              │
│  BODY (Agent Configuration)                                                  │
│  ├── ✅ CONFIGURE which LLM providers are available                         │
│  │      agents.yaml:                                                        │
│  │        qwen-plus:                                                        │
│  │          provider: dashscope                                             │
│  │          model: qwen-plus                                                │
│  │          api_key_env: DASHSCOPE_API_KEY                                  │
│  │                                                                          │
│  ├── ✅ SET API keys (environment variables)                                │
│  │      DASHSCOPE_API_KEY=sk-xxx                                            │
│  │      OPENAI_API_KEY=sk-xxx                                               │
│  │                                                                          │
│  ├── ✅ CONFIGURE base directories                                          │
│  │      server.yaml:                                                        │
│  │        storage:                                                          │
│  │          provisions_dir: /data/provisions                                │
│  │                                                                          │
│  ├── ✅ SET default agent for plans                                         │
│  │      default_agent: qwen-plus                                            │
│  │                                                                          │
│  └── ✅ ENABLE/DISABLE tools (future)                                       │
│         tools:                                                              │
│           python_interpreter: disabled  # security concern                  │
│                                                                              │
│  PROVISIONS                                                                  │
│  ├── ✅ DEPLOY plan provisions (via plan package)                           │
│  │      POST /api/plans/deploy with my-plan.zip                             │
│  │                                                                          │
│  ├── ✅ MANAGE shared provisions                                            │
│  │      /data/provisions/prompts/  (server-wide)                            │
│  │      /data/provisions/paradigms/ (server-wide)                           │
│  │                                                                          │
│  ├── ✅ VIEW deployed provisions                                            │
│  │      GET /api/plans/{id}/provisions                                      │
│  │                                                                          │
│  └── ❌ Cannot modify plan-specific provisions (immutable once deployed)    │
│                                                                              │
│  BODY's APIs (Exposing Input Slots)                                          │
│  ├── ✅ EXPOSE which inputs a plan requires                                 │
│  │      GET /api/plans/{id} returns:                                        │
│  │        { "required_inputs": ["document_path", "user_query"] }            │
│  │                                                                          │
│  ├── ✅ CONFIGURE server endpoints                                          │
│  │      server.yaml:                                                        │
│  │        host: "0.0.0.0"                                                   │
│  │        port: 8000                                                        │
│  │                                                                          │
│  ├── ✅ SET access controls (authentication, rate limits)                   │
│  │      api.auth.type: "api_key"                                            │
│  │      api.rate_limit: 100  # requests/minute                              │
│  │                                                                          │
│  └── ✅ MONITOR which inputs clients provide                                │
│         Logs: "Run started with inputs: {document_path, user_query}"        │
│                                                                              │
│  Files Managed:                                                              │
│  • /data/config/agents.yaml                                                 │
│  • /data/config/server.yaml                                                 │
│  • /data/provisions/* (shared)                                              │
│  • /data/plans/* (deployed packages)                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### End User

**Fills Body's APIs** - provides specific values to complete the agent and activate it for their run.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  END USER ACCESS                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SEQUENCES                                                                   │
│  ├── ❌ No direct access                                                    │
│  └── ⚪ Indirectly triggered when plan runs                                 │
│                                                                              │
│  BODY TOOLS                                                                  │
│  ├── ❌ No direct access                                                    │
│  └── ⚪ Tools execute on their behalf during plan run                       │
│                                                                              │
│  PROVISIONS                                                                  │
│  ├── ❌ No direct access                                                    │
│  └── ⚪ Provisions are used internally during plan run                      │
│                                                                              │
│  BODY's APIs (What End Users FILL)  ◄── PRIMARY INTERACTION POINT           │
│  ├── ✅ DISCOVER what inputs a plan needs                                   │
│  │      GET /api/plans/{id}                                                 │
│  │      Response: { "required_inputs": ["document", "query"] }              │
│  │                                                                          │
│  ├── ✅ FILL the input slots to activate an agent                           │
│  │      POST /api/runs                                                      │
│  │      {                                                                   │
│  │        "plan_id": "doc-analyzer",                                        │
│  │        "inputs": {                                                       │
│  │          "document": "/path/to/file.pdf",  ← fills file_system slot     │
│  │          "query": "What are the key points?" ← fills user_input slot    │
│  │        }                                                                 │
│  │      }                                                                   │
│  │                                                                          │
│  ├── ✅ RECEIVE results from the activated agent                            │
│  │      GET /api/runs/{id}/result                                           │
│  │      WS /ws/runs/{id} (real-time events)                                 │
│  │                                                                          │
│  └── ✅ INTERACT during run (if plan requires)                              │
│         Agent may request additional input during execution                 │
│         Client receives: { "event": "input_required", "prompt": "..." }     │
│         Client responds: { "input": "user's answer" }                       │
│                                                                              │
│  End User Clients (that fill Body's APIs):                                  │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │  • Custom Web App (form that collects inputs)                   │        │
│  │  • Mobile App (UI that gathers user data)                       │        │
│  │  • AI Assistant (extracts inputs from conversation)             │        │
│  │  • Slack Bot (parses command arguments)                         │        │
│  │  • CLI Tool (takes flags as inputs)                             │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                              │
│  End Users COMPLETE the agent by filling its open slots.                     │
│  They don't know about Sequences, Paradigms, or Provisions.                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Provision Layering

Provisions exist at multiple levels, with clear precedence. Note how **paradigms** and **user-tool provisions** have different layering behaviors:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PROVISION LAYERS (highest priority at top)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ═══════════════════════ PARADIGMS (HOW) ═══════════════════════            │
│                                                                              │
│  Paradigms are typically REUSED, not overridden per-plan                     │
│                                                                              │
│  Priority: Plan-specific → Server-shared → Built-in                         │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Plan paradigms   │ provisions/paradigms/custom.json  │ rare     │    │
│  │ 2. Server paradigms │ /data/provisions/paradigms/       │ org-wide │    │
│  │ 3. Built-in         │ infra/_agent/_models/_paradigms/  │ standard │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ═══════════════ USER-TOOL PROVISIONS (WHAT) ═══════════════════            │
│                                                                              │
│  User-tool provisions are typically PLAN-SPECIFIC                            │
│                                                                              │
│  Priority: Plan-specific → Server-shared                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ PROMPTS (for prompt_tool)                                           │    │
│  │ 1. Plan prompts   │ provisions/prompts/analyze.md      │ common   │    │
│  │ 2. Server prompts │ /data/provisions/prompts/common.md │ shared   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ SCHEMAS (for formatter_tool)                                        │    │
│  │ 1. Plan schemas   │ provisions/schemas/result.json     │ common   │    │
│  │ 2. Server schemas │ /data/provisions/schemas/org.json  │ shared   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ SCRIPTS (for python_interpreter)                                    │    │
│  │ 1. Plan scripts   │ provisions/scripts/transform.py    │ common   │    │
│  │ 2. Server scripts │ /data/provisions/scripts/utils.py  │ shared   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Difference**:
- **Paradigms**: Usually select from built-ins; custom paradigms are rare
- **User-tool provisions**: Almost always plan-specific; that's where the work happens

```
┌────────────────────────────────────────────────────────────────────────────┐
│  WHO CREATES WHAT                                                           │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PARADIGMS                                                                  │
│  ┌────────────────┬────────────────────────────────────────────────────┐   │
│  │ Platform Dev   │ Built-in paradigms (95% of use cases)              │   │
│  │ Plan Author    │ Custom paradigms (rare, advanced use)              │   │
│  │ Operator       │ Server-shared paradigms (org-wide patterns)        │   │
│  └────────────────┴────────────────────────────────────────────────────┘   │
│                                                                             │
│  USER-TOOL PROVISIONS                                                       │
│  ┌────────────────┬────────────────────────────────────────────────────┐   │
│  │ Plan Author    │ Prompts, schemas, scripts (primary responsibility) │   │
│  │ Operator       │ Shared prompts, schemas (org standards)            │   │
│  └────────────────┴────────────────────────────────────────────────────┘   │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Configuration Flow

How an agent gets configured for a run:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│  1. OPERATOR configures agents.yaml                                          │
│     ┌──────────────────────────────────┐                                    │
│     │ agents:                          │                                    │
│     │   qwen-plus:                     │                                    │
│     │     provider: dashscope          │                                    │
│     │     model: qwen-plus             │                                    │
│     │     api_key_env: DASHSCOPE_KEY   │                                    │
│     │ default_agent: qwen-plus         │                                    │
│     └──────────────────────────────────┘                                    │
│                              │                                               │
│                              ▼                                               │
│  2. PLAN AUTHOR specifies agent preference (optional)                        │
│     ┌──────────────────────────────────┐                                    │
│     │ manifest.json:                   │                                    │
│     │   "default_agent": "gpt-4o"      │                                    │
│     └──────────────────────────────────┘                                    │
│                              │                                               │
│                              ▼                                               │
│  3. END USER (via client) can override agent (optional)                      │
│     ┌──────────────────────────────────┐                                    │
│     │ POST /api/runs                   │                                    │
│     │   {"plan_id": "X", "agent": "Y"} │                                    │
│     └──────────────────────────────────┘                                    │
│                              │                                               │
│                              ▼                                               │
│  4. SERVER resolves agent (priority: request > plan > server default)        │
│     ┌──────────────────────────────────┐                                    │
│     │ Body initialized with:           │                                    │
│     │   llm_name: "gpt-4o"             │                                    │
│     │   base_dir: "/data/plans/X/"     │                                    │
│     └──────────────────────────────────┘                                    │
│                              │                                               │
│                              ▼                                               │
│  5. ORCHESTRATOR executes plan with configured Body                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Sequence Selection Flow

How the system determines which sequence to use:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PLAN AUTHOR writes .ncds                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  <- document summary                                                         │
│      <= summarize this document                                              │
│      <- clean text                                                           │
│                                                                              │
│                              │                                               │
│                              ▼                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  COMPILER analyzes functional concept                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  "summarize this document"                                                   │
│    ├── Is it a command/action? → imperative family                          │
│    ├── Is it a yes/no evaluation? → judgement family                        │
│    ├── Is it data routing? → assigning                                      │
│    ├── Is it collecting items? → grouping                                   │
│    ├── Is it controlling flow? → timing                                     │
│    └── Is it iterating? → looping                                           │
│                                                                              │
│                              │                                               │
│                              ▼                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  COMPILER checks annotations (Plan Author may override)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  |%{sequence}: imperative_in_composition   ← explicit override              │
│  |%{paradigm}: h_PromptTemplate-c_GenerateThinkJson-o_Literal               │
│                                                                              │
│                              │                                               │
│                              ▼                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  OUTPUT in inference_repo.json                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  {                                                                           │
│    "flow_index": "1.1",                                                      │
│    "inference_sequence": "imperative_in_composition",                        │
│    "function_concept": "::(summarize this document)",                        │
│    "working_interpretation": {                                               │
│      "paradigm": "h_PromptTemplate-c_GenerateThinkJson-o_Literal",           │
│      ...                                                                     │
│    }                                                                         │
│  }                                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary: Who Does What

| Component | Platform Dev | Plan Author | Operator | End User |
|-----------|:------------:|:-----------:|:--------:|:--------:|
| **Create sequences** | ✅ | ❌ | ❌ | ❌ |
| **Use sequences (via syntax)** | ✅ | ✅ | ❌ | ❌ |
| **Override sequence (annotation)** | ✅ | ✅ | ❌ | ❌ |
| **Create Body tools** | ✅ | ❌ | ❌ | ❌ |
| **Configure LLM providers** | ✅ | ❌ | ✅ | ❌ |
| **Set API keys** | ✅ | ❌ | ✅ | ❌ |
| | | | | |
| **PARADIGMS (HOW)** | | | | |
| Create built-in paradigms | ✅ | ❌ | ❌ | ❌ |
| Create plan paradigms | ✅ | ✅ | ❌ | ❌ |
| Select/manage paradigms | ✅ | ✅ | ✅ | ❌ |
| | | | | |
| **USER-TOOL PROVISIONS (WHAT)** | | | | |
| Create prompts | ✅ | ✅ | ❌ | ❌ |
| Create schemas | ✅ | ✅ | ❌ | ❌ |
| Create scripts | ✅ | ✅ | ❌ | ❌ |
| Deploy provisions | ✅ | ❌ | ✅ | ❌ |
| Manage shared provisions | ✅ | ❌ | ✅ | ❌ |
| | | | | |
| **Design Body's APIs (open slots)** | ✅ | ❌ | ❌ | ❌ |
| **Reference Body's APIs (in plan)** | ✅ | ✅ | ❌ | ❌ |
| **Fill Body's APIs (activate agent)** | ✅ | ❌ | ✅ | ✅ |
| **Select agent for run** | ✅ | ✅* | ✅* | ✅** |

*Via manifest default  
**Via API request (if allowed)

---

## Key Insights

1. **Separation of concerns**: Each role has a clear domain
   - Platform Dev → builds capabilities (sequences, tools, built-in provisions)
   - Plan Author → uses capabilities to solve problems (plans, custom provisions)
   - Operator → configures capabilities and creates external access (config, APIs)
   - End User → benefits from capabilities via APIs (clients, integrations)

2. **Two types of provisions** serve different purposes
   - **Paradigms (HOW)**: Execution patterns that orchestrate Body tools
     - Reusable across plans, defines the flow
   - **User-Tool Provisions (WHAT)**: Content consumed by specific tools
     - Prompts → for prompt_tool
     - Schemas → for formatter_tool  
     - Scripts → for python_interpreter
     - Plan-specific, contains the actual content

3. **Body is configured, not modified** by Operators
   - Which LLM? Which API keys? Which directories?
   - Tools themselves are fixed by Platform Developers

4. **Body's APIs are open slots** that clients fill to activate agents
   - Platform Dev DESIGNS the slots (what inputs tools need)
   - Plan Author REFERENCES the slots (uses them in plans)
   - End User FILLS the slots (provides specific values to complete the agent)
   - This is how an agent becomes "active" for a specific client

5. **Sequences are invisible** to most users
   - Plan Authors use them implicitly via syntax
   - The compiler determines the right sequence
   - Advanced authors can override with annotations

6. **Clear internal/external boundary**
   - Internal: Sequences, Body Tools, Provisions → Platform Dev, Plan Author
   - External: Body's APIs → Operator (creates), End User (uses)
   - This separation enables security, scalability, and clean architecture

---

## Complete Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                               NORMCODE AGENT ARCHITECTURE                                    │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                          INTERNAL (Platform Dev + Plan Author)                         │  │
│  ├───────────────────────────────────────────────────────────────────────────────────────┤  │
│  │                                                                                        │  │
│  │   SEQUENCES              BODY TOOLS                 PROVISIONS                         │  │
│  │   ┌──────────┐          ┌──────────────┐           ┌──────────────┐                   │  │
│  │   │imperative│          │ llm          │           │ prompts/*.md │                   │  │
│  │   │judgement │   ──►    │ file_system  │    ◄──    │ paradigms/*.json                 │  │
│  │   │assigning │          │ python_interp│           │ schemas/*.json│                  │  │
│  │   │looping   │          │ user_input   │           └──────────────┘                   │  │
│  │   └──────────┘          └──────────────┘                                              │  │
│  │        │                       │                                                       │  │
│  │        └───────────┬───────────┘                                                       │  │
│  │                    ▼                                                                   │  │
│  │           ┌─────────────────┐                                                          │  │
│  │           │   ORCHESTRATOR  │  ◄── Executes plans using sequences + body + provisions  │  │
│  │           └─────────────────┘                                                          │  │
│  │                    │                                                                   │  │
│  └────────────────────┼───────────────────────────────────────────────────────────────────┘  │
│                       │                                                                      │
│  ═════════════════════╪══════════════════════════════════════════════════════════════════   │
│                       │  BOUNDARY                                                            │
│  ═════════════════════╪══════════════════════════════════════════════════════════════════   │
│                       │                                                                      │
│  ┌────────────────────┼───────────────────────────────────────────────────────────────────┐  │
│  │                    ▼             EXTERNAL (Operator + End User)                        │  │
│  ├───────────────────────────────────────────────────────────────────────────────────────┤  │
│  │                                                                                        │  │
│  │   BODY's APIs (Open Slots - designed by Platform Dev)                                  │  │
│  │   ┌────────────────────────────────────────────────────────────────────────────────┐  │  │
│  │   │  user_input: ???      file_system: ???      llm: ???                           │  │  │
│  │   │       ▲                     ▲                  ▲                               │  │  │
│  │   │       │                     │                  │                               │  │  │
│  │   └───────┼─────────────────────┼──────────────────┼───────────────────────────────┘  │  │
│  │           │                     │                  │                                  │  │
│  │           └─────────────────────┼──────────────────┘                                  │  │
│  │                                 │                                                     │  │
│  │                                 │  FILL                                               │  │
│  │                                 │                                                     │  │
│  │   END USER CLIENTS (Fill slots to activate agent)                                     │  │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                   │  │
│  │   │ Web App  │ │Mobile App│ │ AI Asst  │ │ Slack Bot│ │Dashboard │                   │  │
│  │   │ query=X  │ │ file=Y   │ │ input=Z  │ │ args=W   │ │ data=V   │                   │  │
│  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘                   │  │
│  │                                                                                       │  │
│  │   → Client provides values → Body becomes COMPLETE → Agent is ACTIVE for that run    │  │
│  │                                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Flow Summary**:
1. **Platform Dev** creates Sequences, Body Tools (with open API slots), and built-in Provisions
2. **Plan Author** writes plans (.ncds) that reference these open slots
3. **Operator** deploys plans and configures server
4. **End User** fills the open slots via their client, activating the agent for their run

