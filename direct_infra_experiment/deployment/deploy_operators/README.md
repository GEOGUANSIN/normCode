# NormCode Deployment

Standalone deployment tools for executing NormCode plans without the Canvas App.

## Components

| Tool | Purpose | Usage |
|------|---------|-------|
| `runner.py` | CLI to execute plans | `python runner.py config.json` |
| `pack.py` | Create deployment packages | `python pack.py config.json` |
| `server.py` | REST API server | `python server.py` |
| `client.py` | CLI client for server | `python client.py plans` |
| `client_gui.py` | GUI client for server | `python client_gui.py` |
| `tools/` | Standalone tool implementations | Used by runner/server |

## Quick Start

### 1. Run a Plan (CLI)

```powershell
# Run with demo LLM (no API calls)
python deployment/runner.py deployment/test_ncs/testproject.normcode-canvas.json

# Run with a real LLM
python deployment/runner.py deployment/test_ncs/testproject.normcode-canvas.json --llm qwen-plus

# Resume from checkpoint
python deployment/runner.py deployment/test_ncs/testproject.normcode-canvas.json --resume

# Output results to JSON
python deployment/runner.py deployment/test_ncs/testproject.normcode-canvas.json --output-json results.json
```

### 2. Create a Deployment Package

```powershell
# Pack a project into a .zip
python deployment/pack.py deployment/test_ncs/testproject.normcode-canvas.json

# Custom output name
python deployment/pack.py deployment/test_ncs/testproject.normcode-canvas.json -o my-plan.zip

# Unpack a package
python deployment/pack.py --unpack my-plan.normcode.zip
```

### 3. Start the API Server

```powershell
# Start server
python deployment/server.py

# Custom port
python deployment/server.py --port 9000

# With specific plans directory
python deployment/server.py --plans-dir ./my_plans
```

Then use the API via client or curl:

```powershell
# Using the client
python deployment/client.py health
python deployment/client.py plans
python deployment/client.py run b1fdfd5b --llm demo --wait
python deployment/client.py status <run_id>
python deployment/client.py result <run_id>

# Or using curl
curl http://localhost:8080/api/plans
curl -X POST http://localhost:8080/api/runs -H "Content-Type: application/json" -d '{"plan_id": "b1fdfd5b"}'
curl http://localhost:8080/api/runs/{run_id}
curl http://localhost:8080/api/runs/{run_id}/result
```

### 4. Client Commands

```powershell
# Health & Info
python deployment/client.py health
python deployment/client.py info

# Plans
python deployment/client.py plans               # List all plans
python deployment/client.py plans <plan_id>     # Get plan details

# Runs
python deployment/client.py run <plan_id>                  # Start a run
python deployment/client.py run <plan_id> --llm demo       # With specific LLM
python deployment/client.py run <plan_id> --wait           # Wait for completion
python deployment/client.py runs                           # List all runs
python deployment/client.py status <run_id>                # Check status
python deployment/client.py result <run_id>                # Get result
python deployment/client.py stop <run_id>                  # Stop a run

# WebSocket
python deployment/client.py watch <run_id>                 # Watch live events
```

### 5. GUI Client

```powershell
# Launch GUI (connects to localhost:8080 by default)
python deployment/client_gui.py

# Connect to a different server
python deployment/client_gui.py --server http://myserver:9000
```

The GUI provides:
- Server connection status
- Plans list with run button
- Runs list with status polling
- Result/details viewer
- LLM model selector

## Configuration Files

### .normcode-canvas.json (Project Config)

```json
{
  "id": "unique-id",
  "name": "My Plan",
  "description": "Optional description",
  "repositories": {
    "concepts": "repos/concepts.json",
    "inferences": "repos/inferences.json"
  },
  "execution": {
    "llm_model": "qwen-plus",
    "max_cycles": 100,
    "db_path": "orchestration.db",
    "paradigm_dir": "provision/paradigm"
  }
}
```

### manifest.json (Deployment Package)

```json
{
  "name": "my-plan",
  "version": "1.0.0",
  "description": "Plan description",
  "entry": {
    "concepts": "concept_repo.json",
    "inferences": "inference_repo.json"
  },
  "inputs": {
    "{raw document}": {"type": "file", "required": true}
  },
  "outputs": {
    "{result}": {"type": "object"}
  }
}
```

## Directory Structure

```
deployment/
├── runner.py              # CLI runner
├── pack.py                # Package creator
├── server.py              # API server
├── client.py              # CLI client
├── client_gui.py          # GUI client
├── NORMCODE_DEPLOYMENT_SPEC.md  # Full spec
├── README.md              # This file
│
├── tools/                 # Standalone tool implementations
│   ├── __init__.py
│   ├── llm_tool.py        # LLM with OpenAI-compatible API
│   ├── file_system_tool.py
│   ├── prompt_tool.py     # Template management
│   ├── python_interpreter_tool.py
│   ├── formatter_tool.py  # Data formatting/parsing
│   ├── composition_tool.py # Function composition
│   ├── user_input_tool.py # CLI/API input
│   └── settings.yaml      # LLM provider config
│
├── test_ncs/              # Test project
│   ├── testproject.normcode-canvas.json
│   ├── repos/
│   │   ├── gold_chinese.concept.json
│   │   └── gold_chinese.inference.json
│   └── provision/
│       ├── data/
│       ├── paradigm/
│       ├── prompts/
│       └── scripts/
│
├── plans/                 # [Server] Deployed plans
└── runs/                  # [Server] Run state & outputs
```

## Deployment Tools

The `tools/` directory contains standalone tool implementations that work without Canvas/WebSocket dependencies:

| Tool | Description |
|------|-------------|
| `DeploymentLLMTool` | LLM with OpenAI-compatible API, mock mode support |
| `DeploymentFileSystemTool` | File operations within sandboxed directory |
| `DeploymentPromptTool` | Template loading and variable substitution |
| `DeploymentPythonInterpreterTool` | Script execution with Body injection |
| `DeploymentFormatterTool` | JSON parsing, wrapping, code extraction |
| `DeploymentCompositionTool` | Multi-step function composition for paradigms |
| `DeploymentUserInputTool` | CLI/API-based user input |

### Using Deployment Tools

```powershell
# Run with deployment tools instead of infra defaults
python deployment/runner.py deployment/test_ncs/testproject.normcode-canvas.json --use-deployment-tools

# This uses tools from deployment/tools/ instead of infra/_agent/
```

### Tool Configuration (settings.yaml)

```yaml
BASE_URL: https://dashscope.aliyuncs.com/compatible-mode/v1
qwen-plus:
  DASHSCOPE_API_KEY: your-api-key
gpt-4o:
  OPENAI_API_KEY: your-openai-key
```

### Direct Tool Usage

```python
from deployment.tools import DeploymentLLMTool, DeploymentFileSystemTool

# LLM
llm = DeploymentLLMTool(model_name="qwen-plus")
response = llm.generate("Hello, world!")

# File System
fs = DeploymentFileSystemTool(base_dir="./my_project")
content = fs.read("data.json")
fs.write("output.json", '{"result": "done"}')
```

## Server API Reference

### Plans

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/plans` | List all plans |
| GET | `/api/plans/{id}` | Get plan details |

### Runs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/runs` | Start new run |
| GET | `/api/runs` | List all runs |
| GET | `/api/runs/{id}` | Get run status |
| GET | `/api/runs/{id}/result` | Get completed result |
| POST | `/api/runs/{id}/stop` | Stop running execution |

### WebSocket

| Endpoint | Events |
|----------|--------|
| `/ws/runs/{id}` | `run:completed`, `run:failed` |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/info` | Server info |

## Comparison to Canvas App

| Feature | Canvas App | Deployment Tools |
|---------|-----------|------------------|
| Visual graph | ✅ | ❌ |
| Breakpoints | ✅ | ❌ |
| Step execution | ✅ | ❌ |
| CLI execution | ❌ | ✅ |
| REST API | Limited | ✅ Full |
| Packaging | ❌ | ✅ |
| Production-ready | ❌ Dev tool | ✅ |

## Integration with Canvas App

These tools are designed to work independently but can integrate with Canvas:

1. **Author in Canvas** → Export to `.normcode-canvas.json`
2. **Package with `pack.py`** → Creates `.normcode.zip`
3. **Deploy to server** → `POST /api/plans/deploy` (TODO)
4. **Execute via API** → `POST /api/runs`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NORMCODE_HOST` | `0.0.0.0` | Server host |
| `NORMCODE_PORT` | `8080` | Server port |
| `NORMCODE_PLANS_DIR` | `./plans` | Plans directory |
| `NORMCODE_RUNS_DIR` | `./runs` | Runs directory |
| `NORMCODE_LOG_LEVEL` | `INFO` | Log level |

## See Also

- [NORMCODE_DEPLOYMENT_SPEC.md](./NORMCODE_DEPLOYMENT_SPEC.md) - Full deployment specification
- [Canvas App README](../canvas_app/README.md) - Visual development environment
- [Infra README](../infra/README.md) - Core infrastructure

