# NormCode Deployment Server

A self-contained server for executing NormCode plans.

Built: 2026-01-16 15:56:09

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure LLM settings (optional):
   Edit `data/config/settings.yaml` with your API keys.

3. Start the server:
   ```bash
   python start_server.py
   ```
   Or with options:
   ```bash
   python start_server.py --port 9000 --host 0.0.0.0
   ```

4. Access the API:
   - Health check: http://localhost:8080/health
   - API docs: http://localhost:8080/docs
   - Server info: http://localhost:8080/info

## Directory Structure

```
normcode-server/
├── server.py           # Main server code
├── runner.py           # Plan execution (shared module)
├── start_server.py     # Start server script (frequently used utility)
├── scripts/            # Utility scripts
│   └── pack.py         # Plan packager
├── routes/             # API route modules
├── tools/              # Deployment tools
├── infra/              # Core NormCode library
├── mock_users/         # Test clients
│   ├── client.py       # CLI test client
│   └── client_gui.py   # GUI test client
├── data/
│   ├── plans/          # Deploy plans here
│   ├── runs/           # Run data (auto-created)
│   └── config/
│       └── settings.yaml  # LLM configuration
└── requirements.txt
```

## Test Clients

The `mock_users/` directory contains test clients:

```bash
# CLI client
python mock_users/client.py --server http://localhost:8080

# GUI client (requires tkinter)
python mock_users/client_gui.py
```

## API Endpoints

### Plans
- `GET /api/plans` - List deployed plans
- `GET /api/plans/{plan_id}` - Get plan details
- `GET /api/plans/{plan_id}/graph` - **Get full graph data (concepts + inferences)** ✨
- `GET /api/plans/{plan_id}/files/{path}` - **Get plan files (prompts, paradigms)** ✨
- `POST /api/plans/deploy-file` - Deploy a plan (zip upload)
- `DELETE /api/plans/{plan_id}` - Remove a plan
- `DELETE /api/plans` - Remove ALL plans

### Runs
- `POST /api/runs` - Start a new run
- `GET /api/runs` - List all runs (includes historical runs from disk) ✨
- `GET /api/runs/{run_id}` - Get run status (active or historical)
- `GET /api/runs/{run_id}/result` - Get run result (active or from checkpoint)
- `POST /api/runs/{run_id}/resume` - **Resume run from checkpoint** ✨
- `POST /api/runs/{run_id}/stop` - Stop a running execution
- `DELETE /api/runs` - Remove ALL runs

### Run Database Inspector ✨
These endpoints allow remote inspection of run databases for debugging and analysis:

- `GET /api/runs/{run_id}/db/overview` - Database structure and statistics
- `GET /api/runs/{run_id}/db/executions` - Execution history (with optional logs)
- `GET /api/runs/{run_id}/db/executions/{id}/logs` - Detailed logs for an execution
- `GET /api/runs/{run_id}/db/statistics` - Run statistics (status counts, cycles)
- `GET /api/runs/{run_id}/db/checkpoints` - List available checkpoints
- `GET /api/runs/{run_id}/db/checkpoints/{cycle}` - Get checkpoint state data
- `GET /api/runs/{run_id}/db/blackboard` - Blackboard summary (concept/item statuses)
- `GET /api/runs/{run_id}/db/concepts` - Completed concepts with data previews

### Server
- `GET /health` - Health check
- `GET /info` - Server information
- `GET /api/models` - Available LLM models
- `GET /api/connect` - **Connection info for remote proxy** ✨
- `POST /api/server/reset` - Full server reset

### Remote Execution Support ✨
These endpoints facilitate the RemoteProxyExecutor connection from canvas_app:

- `GET /api/connect` - Verify connectivity and get server capabilities
- `GET /api/plans/{plan_id}/manifest` - Get project manifest for tab integration
- `GET /api/runs/{run_id}/stream` - SSE stream (stays open for paused runs!)

### WebSocket
- `WS /ws/runs/{run_id}` - Real-time run events

## Deploying Plans

### Option 1: HTTP Upload
```bash
curl -X POST http://localhost:8080/api/plans/deploy-file \
  -F "plan=@my-plan.zip"
```

### Option 2: Direct Copy
Copy your plan folder directly to `data/plans/`:
```bash
cp -r ./my-plan/ ./data/plans/my-plan/
```

## Running Plans

```bash
curl -X POST http://localhost:8080/api/runs \
  -H "Content-Type: application/json" \
  -d '{"plan_id": "my-plan", "llm_model": "qwen-plus"}'
```

## LLM Configuration

Edit `data/config/settings.yaml`:

```yaml
BASE_URL: https://dashscope.aliyuncs.com/compatible-mode/v1

qwen-plus:
  model: qwen-plus
  api_key: your-api-key-here

gpt-4o:
  model: gpt-4o
  api_key: your-openai-key
  base_url: https://api.openai.com/v1
```

## Canvas App Integration

This server is designed to work with the NormCode Canvas App for remote project loading and debugging.

### Loading Remote Projects

The Canvas App can connect to this server and load projects remotely:

```bash
# Get the full graph data for a plan (concepts + inferences)
curl http://localhost:8080/api/plans/my-plan/graph
```

This returns the complete repository data needed to render the graph in Canvas.

### Inspecting Remote Runs

The DB Inspector endpoints allow Canvas to inspect run execution remotely:

```bash
# List all checkpoints for a run
curl http://localhost:8080/api/runs/{run_id}/db/checkpoints

# Get blackboard state
curl http://localhost:8080/api/runs/{run_id}/db/blackboard

# Get execution history with logs
curl "http://localhost:8080/api/runs/{run_id}/db/executions?include_logs=true"
```

### Resuming from Checkpoints

Resume a run from any checkpoint:

```bash
# Resume from latest checkpoint
curl -X POST http://localhost:8080/api/runs/{run_id}/resume

# Resume from specific cycle (creates a fork)
curl -X POST "http://localhost:8080/api/runs/{run_id}/resume?cycle=5&fork=true"
```

## RemoteProxyExecutor Integration

The server supports the canvas_app's unified remote execution architecture via the `RemoteProxyExecutor`. This allows the canvas_app to control remote runs as if they were local.

### How It Works

```
┌─────────────────┐     HTTP/SSE      ┌──────────────────┐
│   canvas_app    │◄─────────────────►│  normal_server   │
│                 │                    │                  │
│ RemoteProxy     │  POST /api/runs/X/continue  │  RunState        │
│ Executor        │────────────────────────────►│                  │
│                 │                    │                  │
│                 │  GET /api/runs/X/stream     │  (SSE events)    │
│                 │◄────────────────────────────│                  │
└─────────────────┘                    └──────────────────┘
```

### Connecting from canvas_app

1. **Verify connectivity:**
   ```bash
   curl http://localhost:8080/api/connect
   ```

2. **Get plan manifest (for tab integration):**
   ```bash
   curl http://localhost:8080/api/plans/my-plan/manifest
   ```

3. **Start a run:**
   ```bash
   curl -X POST http://localhost:8080/api/runs \
     -H "Content-Type: application/json" \
     -d '{"plan_id": "my-plan", "llm_model": "qwen-plus"}'
   ```

4. **Subscribe to SSE events:**
   ```bash
   curl http://localhost:8080/api/runs/{run_id}/stream
   ```

5. **Control execution:**
   ```bash
   # Pause
   curl -X POST http://localhost:8080/api/runs/{run_id}/pause
   
   # Resume
   curl -X POST http://localhost:8080/api/runs/{run_id}/continue
   
   # Step
   curl -X POST http://localhost:8080/api/runs/{run_id}/step
   
   # Stop
   curl -X POST http://localhost:8080/api/runs/{run_id}/stop
   ```

### SSE Event Types

The `/api/runs/{run_id}/stream` endpoint sends these events:

| Event | Description |
|-------|-------------|
| `connected` | Initial connection with full state |
| `node:statuses` | Batch node status update |
| `inference:started` | Inference execution began |
| `inference:completed` | Inference finished successfully |
| `inference:failed` | Inference failed |
| `execution:progress` | Progress update |
| `execution:paused` | Execution paused |
| `execution:resumed` | Execution resumed |
| `execution:stopped` | Execution stopped |
| `breakpoint:hit` | Breakpoint reached |
| `run:completed` | Run finished |
| `run:failed` | Run failed |

## License

Part of the NormCode project.
