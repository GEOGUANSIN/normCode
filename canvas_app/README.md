# NormCode Graph Canvas Tool

A visual, interactive environment for executing, debugging, and auditing NormCode plans.

## Features

- **Graph Visualization**: Interactive React Flow-based graph showing the inference structure
- **Real-time Execution**: Watch nodes change status as the plan executes
- **Debugging**: Set breakpoints, step through inferences, inspect node data
- **Tensor Inspector**: View N-dimensional tensor data with slicing and axis selection
- **Agent Management**: Configure multiple agents with different LLM models
- **Project System**: IDE-like project management with multi-project support
- **Editor Panel**: Edit NormCode files directly within the app
- **Tool Monitoring**: Real-time view of all LLM and tool calls

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+

### Running (First Time)

The launcher automatically checks and installs dependencies on first run:

```powershell
cd canvas_app
python launch.py
```

The launcher will:
1. Check for Python dependencies (FastAPI, uvicorn, etc.)
2. Check for Node.js dependencies (React, Vite, etc.)
3. Install any missing dependencies automatically
4. Start both backend and frontend servers

### Launcher Options

```powershell
python launch.py              # Start in dev mode (default)
python launch.py --prod       # Start in production mode (no auto-reload)
python launch.py --install    # Force reinstall all dependencies
python launch.py --skip-deps  # Skip dependency checks (faster startup)
python launch.py --backend-only   # Only start the backend server
python launch.py --frontend-only  # Only start the frontend server
```

### Manual Setup (Optional)

If you prefer to install dependencies manually:

1. **Install Backend Dependencies**

```powershell
cd canvas_app/backend
pip install -r requirements.txt
```

2. **Install Frontend Dependencies**

```powershell
cd canvas_app/frontend
npm install
```

### Running Manually (Separate Terminals)

Terminal 1 (Backend):
```powershell
cd canvas_app/backend
uvicorn main:app --reload --port 8000
```

Terminal 2 (Frontend):
```powershell
cd canvas_app/frontend
npm run dev
```

### Access

- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws/events

## Usage

1. Click "Load Repository" in the top right
2. Enter paths to your `.concept.json` and `.inference.json` files
3. The graph will be displayed with nodes colored by category:
   - **Purple**: Semantic functions (imperative, judgement)
   - **Blue**: Semantic values (objects, attributes, collections)
   - **Gray**: Syntactic functions (assigning, grouping, timing, looping)
4. Click nodes to view details in the right panel
5. Use the control bar to run, pause, step through execution

## Node Indicators

- **Double border**: Ground concept (input data)
- **Red ring**: Output concept (final result)
- **Status dot colors**:
  - Gray: Pending
  - Blue (pulsing): Running
  - Green: Completed
  - Red: Failed
  - Yellow: Skipped

## Project Structure

```
canvas_app/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   ├── schemas/             # Pydantic models
│   └── core/                # Config and utilities
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main app component
│   │   ├── components/      # React components
│   │   │   ├── graph/       # Graph visualization
│   │   │   └── panels/      # UI panels
│   │   ├── stores/          # Zustand state management
│   │   ├── services/        # API and WebSocket clients
│   │   └── types/           # TypeScript types
│   └── index.html
│
├── launch.py                # Combined launcher
└── README.md
```

## API Endpoints

### Repositories
- `POST /api/repositories/load` - Load repository files
- `GET /api/repositories/examples` - List example repositories

### Graph
- `GET /api/graph` - Get graph data
- `GET /api/graph/node/{id}` - Get node details
- `GET /api/graph/stats` - Get graph statistics

### Execution
- `POST /api/execution/start` - Start execution
- `POST /api/execution/pause` - Pause execution
- `POST /api/execution/step` - Step one inference
- `POST /api/execution/stop` - Stop execution
- `GET /api/execution/state` - Get execution state

### WebSocket Events
- `inference:started` - Inference execution started
- `inference:completed` - Inference completed
- `inference:failed` - Inference failed
- `breakpoint:hit` - Breakpoint triggered
- `execution:completed` - Plan execution completed

## Technology Stack

- **Backend**: FastAPI, Python 3.11+, WebSockets
- **Frontend**: React 18, TypeScript, Vite
- **Graph**: React Flow
- **State**: Zustand
- **Styling**: TailwindCSS

## Development

### Backend Development

```powershell
cd canvas_app/backend
uvicorn main:app --reload --port 8000
```

The backend will auto-reload on file changes.

### Frontend Development

```powershell
cd canvas_app/frontend
npm run dev
```

Vite provides hot module replacement for instant updates.

## Completed Features

- ✅ Graph visualization with React Flow
- ✅ Real-time WebSocket execution events
- ✅ Breakpoints and step execution
- ✅ TensorInspector for N-D data viewing
- ✅ Log panel with per-node filtering
- ✅ Project management (multi-project, registry)
- ✅ Editor panel with file browser
- ✅ Agent panel with tool monitoring
- ✅ "Run to" feature
- ✅ Fullscreen detail panel
- ✅ Natural name display

## Next Steps (Phase 4: Modification & Re-run)

- [ ] Value override dialog (edit tensor values)
- [ ] Function modification (change paradigm, prompt)
- [ ] Selective re-run from any node
- [ ] Checkpoint resume/fork
- [ ] Keyboard shortcuts
- [ ] Export execution traces

---

**Version**: 0.7.1 (Phase 3 Complete, Phase 4 In Progress)  
**Status**: Debugging features complete, implementing modification features
