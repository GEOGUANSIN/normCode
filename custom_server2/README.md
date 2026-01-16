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
├── start_server.py     # Start script
├── server.py           # Main server code
├── runner.py           # Plan execution
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
- `POST /api/plans/deploy-file` - Deploy a plan (zip upload)
- `DELETE /api/plans/{plan_id}` - Remove a plan
- `DELETE /api/plans` - Remove ALL plans

### Runs
- `POST /api/runs` - Start a new run
- `GET /api/runs` - List all runs
- `GET /api/runs/{run_id}` - Get run status
- `GET /api/runs/{run_id}/result` - Get run result
- `DELETE /api/runs` - Remove ALL runs

### Server
- `GET /health` - Health check
- `GET /info` - Server information
- `GET /api/models` - Available LLM models
- `POST /api/server/reset` - Full server reset

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

## License

Part of the NormCode project.
