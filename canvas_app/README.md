# NormCode Graph Canvas Tool

A visual, interactive environment for executing, debugging, and auditing NormCode plans.

## Features

- **Graph Visualization**: Interactive React Flow-based graph showing the inference structure
- **Real-time Execution**: Watch nodes change status as the plan executes
- **Debugging**: Set breakpoints, step through inferences, inspect node data
- **Detail Panel**: View node details, connections, and working interpretations

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm 9+

### Setup

1. **Install Backend Dependencies**

```powershell
cd canvas_app/backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. **Install Frontend Dependencies**

```powershell
cd canvas_app/frontend
npm install
```

### Running

**Option 1: Combined Launcher**

```powershell
cd canvas_app
python launch.py
```

**Option 2: Separate Terminals**

Terminal 1 (Backend):
```powershell
cd canvas_app/backend
.\venv\Scripts\Activate.ps1
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

## Next Steps (Phase 2+)

- [ ] Full WebSocket integration for real-time updates
- [ ] Tensor data inspection in detail panel
- [ ] Value override capabilities
- [ ] Selective re-run from any node
- [ ] Export execution traces
- [ ] Keyboard shortcuts

---

**Version**: 0.1.0 (Phase 1)  
**Status**: Basic graph display and structure complete
