# NormCode: Structured AI Planning That You Can Audit

**NormCode is a language for building multi-step AI workflows where you can see exactly what each step receives and produces—no hidden context, no debugging in the dark.**

---

## From Chat to Workflows

### Single prompts are easy

```
You: "Summarize this document about Q3 earnings"
AI: [reads document, produces summary]
```

This works well for one-shot tasks.

### Multi-step tasks get trickier

For more complex work, you might chain several steps:

```
Step 1: "Extract all financial figures from this document"
Step 2: "Cross-reference these figures with our database"
Step 3: "Flag any discrepancies"
Step 4: "Generate an executive summary"
```

This is a **workflow**—and it can get messy.

### What can go wrong

By Step 4, your AI might be juggling:
- The entire original document (50+ pages)
- All extracted figures (hundreds of numbers)
- Raw database query results
- Notes from earlier steps

Sometimes the AI confuses a number from page 47 with a database entry, or references something that doesn't exist. When things go wrong, it's hard to tell which input caused the issue.

Some people call this "debugging in the dark."

### How NormCode helps

In NormCode, each step only sees what you explicitly pass to it:

```ncds
<- executive summary
    <= generate summary from flagged items
    <- discrepancy flags
        <= check for mismatches
        <- extracted figures
            <= extract financial data
            <- raw document
        <- database results
```

Reading bottom-up:
- The extraction step sees only the `raw document`
- The mismatch check sees only `extracted figures` + `database results`
- The summary step sees only `discrepancy flags`

If something goes wrong at a step, you can see exactly what that step received.

---

## Bigger Picture: The Alignment Stack

NormCode fits into a three-layer approach for building AI systems that stay aligned with what users actually want:

```mermaid
flowchart TB
    A["🧭 NormCode<br/><sub>Authority Layer</sub><br/>Semi-formal contracts between humans and AI"]
    B["🛠 Shared Workspace<br/><sub>Execution Layer</sub><br/>Data, tools, and task constraints"]
    C["🧠 Foundation Models<br/><sub>Understanding Layer</sub><br/>General-purpose reasoning and generation"]

    A --> B --> C
```

By making data flow and steps explicit, NormCode helps users stay in control of what their AI agents are doing.

---

## Key Ideas

### Data isolation

```ncds
<- risk assessment
    <= evaluate legal exposure based on the extracted clauses
    <- relevant clauses
        <= extract clauses related to liability
        <- full contract
```

Here, the risk assessment step only sees the extracted clauses—not the full contract. This keeps things focused and easier to audit.

### Semantic vs. syntactic steps

| Type | LLM? | Cost | Determinism | Examples |
|------|------|------|-------------|----------|
| **Semantic** | ✅ Yes | Tokens | Non-deterministic | Reasoning, generating, analyzing |
| **Syntactic** | ❌ No | Free | 100% Deterministic | Collecting, selecting, routing |

In a typical plan, many steps are just data routing—no LLM needed. Only the "thinking" steps cost tokens.

### Three properties

| Property | What it means |
|----------|---------------|
| **Readable** | You can understand what each step does |
| **Executable** | The AI can follow the plan reliably |
| **Accountable** | Every step has a unique ID for tracing |

---

## The Ecosystem

```mermaid
graph TD
    A["Natural Language Task"] --> B["Compiler"]
    B --> C["NormCode Plan (.ncd)"]
    C <--> D["Canvas App (Visual Debugger)"]
    C --> E["Orchestrator"]
    E --> F["Execution"]
    F --> G["🧠 Foundation Models"]
    F --> H["⚙️ Tools & Data"]
    F --> I["Final Result + Audit Trail"]
```

### Main components

| Component | What it does |
|-----------|--------------|
| **`infra/`** | The execution engine (Orchestrator, Blackboard, Agent Sequences) |
| **`canvas_app/`** | Visual debugger with graph view, breakpoints, and real-time execution |
| **`cli_orchestrator.py`** | Command-line tool for running orchestrations |
| **`documentation/`** | Guides and reference docs |

---

## Quick Start

### 1. Installation

```bash
git clone https://github.com/your-username/normCode.git
cd normCode
pip install -e .
```

### 2. Launch the Canvas App (Recommended)

The **Canvas App** is a visual debugger for executing and inspecting NormCode plans:

```bash
python launch_canvas.py
```

This automatically:
- Checks and installs Python dependencies (FastAPI, uvicorn, etc.)
- Checks and installs Node.js dependencies (React, Vite, etc.)
- Starts backend (port 8000) and frontend (port 5173)

**Options:**
```bash
python launch_canvas.py --prod       # Production mode (no auto-reload)
python launch_canvas.py --skip-deps  # Skip dependency checks (faster startup)
python launch_canvas.py --help       # Show all options
```

**Prerequisites:** Python 3.11+, Node.js 18+

### 3. Run from Command Line

For headless execution, use the CLI orchestrator:

```bash
# Start a new run
python cli_orchestrator.py run --concepts path/to/concepts.json --inferences path/to/inferences.json

# Resume from checkpoint
python cli_orchestrator.py resume --run-id <UUID>

# Fork from a past state
python cli_orchestrator.py fork --from-run <UUID> --concepts new_concepts.json

# List all runs
python cli_orchestrator.py list-runs
```

### 4. Run a Basic Example

See NormCode in action with the base-X addition algorithm (achieves 100% accuracy on arbitrary-length inputs):

```bash
python infra/examples/add_examples/ex_add_complete.py
```

---

## How It Works

### A Simple Plan

```ncds
<- document summary
    <= summarize this text
    <- clean text
        <= extract main content, removing headers
        <- raw document
```

Read bottom-up:
1. Start with `raw document`
2. Run `extract main content...` → produces `clean text`
3. Run `summarize this text` → produces `document summary`

**Key insight:** The summarization step literally cannot see the raw document.

### The Compilation Pipeline

```
Natural Language → .ncds (draft) → .ncd (formal) → .concept.json + .inference.json → Execution
```

| Phase | Output | Purpose |
|-------|--------|---------|
| **Derivation** | `.ncds` | Extract structure from natural language |
| **Formalization** | `.ncd` | Add flow indices, sequence types, bindings |
| **Post-Formalization** | `.ncd` (enriched) | Add paradigms, resources, axis annotations |
| **Activation** | JSON repositories | Generate executable format for orchestrator |

### Execution Model

The Orchestrator runs plans with:
- **Dependency-driven scheduling** — inferences run only when inputs are ready
- **SQLite checkpointing** — pause, resume, or fork from any cycle
- **Full state tracking** — inspect what each step saw and produced

---

## When to Use NormCode

| Scenario | Use NormCode? | Rationale |
|----------|---------------|-----------|
| Multi-step workflow (5+ LLM calls) | ✅ Yes | Isolation and debuggability pay off |
| Auditable AI (legal, medical, finance) | ✅ Yes | You must prove what each step saw |
| Long-running, resumable workflows | ✅ Yes | Built-in checkpointing |
| Quick prototype (1-2 LLM calls) | ❌ No | Overhead exceeds benefit |
| Simple Q&A chatbot | ❌ No | Just prompt the model directly |

**Sweet spot:** Complex, multi-step workflows where you need to know exactly what happened at each step—and where a failure at step 7 shouldn't corrupt reasoning at step 12.

---

## Project Structure

```
normCode/
├── infra/                    # Core execution engine
│   ├── _agent/               # Agent framework and sequences
│   ├── _orchest/             # Orchestrator and blackboard
│   ├── _states/              # Reference system and tensors
│   └── examples/             # Working examples
├── canvas_app/               # Visual debugger (React + FastAPI)
│   ├── frontend/             # React Flow graph visualization
│   └── backend/              # Execution controller API
├── documentation/            # Comprehensive documentation
│   ├── current/              # Latest guides
│   └── paper/                # Academic paper draft
├── cli_orchestrator.py       # Command-line interface
├── launch_canvas.py          # One-command Canvas App launcher
└── settings.yaml             # LLM API configuration
```

---

## Configuration

Create `settings.yaml` in the project root (see `canvas_app/settings.yaml.example`):

```yaml
llm:
  provider: openai  # or: anthropic, dashscope
  api_key: your-api-key-here
  model: gpt-4o     # or: claude-3-opus, qwen-plus
```

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Overview](documentation/current/1_intro/overview.md) | What NormCode is and why it exists |
| [NCD Format](documentation/current/2_grammar/ncd_format.md) | The formal syntax reference |
| [Execution](documentation/current/3_execution/overview.md) | How plans run at runtime |
| [Compilation](documentation/current/4_compilation/overview.md) | The transformation pipeline |
| [Canvas App](documentation/current/5_tools/canvas_app_overview.md) | Visual debugger guide |

---

## Research

NormCode is described in the paper:

> **NormCode: A Semi-Formal Language for Context-Isolated AI Planning**
> 
> Multi-step workflows that chain LLM calls suffer from context pollution. NormCode enforces explicit data isolation as a language-level constraint, making AI workflows auditable by construction.

See [Arxiv](https://arxiv.org/abs/2512.10563) for the full draft.

---

## License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.
