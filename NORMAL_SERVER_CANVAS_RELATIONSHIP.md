# Relationship Between `normal_server` and `canvas_app`

## Overview

`normal_server` and `canvas_app` are two separate components that work together to enable **remote execution and visualization** of NormCode plans. The relationship is built around a **proxy/relay architecture** that allows `canvas_app` to control and monitor runs executing on `normal_server` as if they were local.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        canvas_app                               │
│  ┌──────────────┐         ┌──────────────────────────────┐    │
│  │   Frontend   │◄───────►│      Backend (FastAPI)       │    │
│  │  (React/Vite)│  WS     │  ┌────────────────────────┐  │    │
│  └──────────────┘          │  │ RemoteProxyExecutor   │  │    │
│                            │  │  - Connects to remote │  │    │
│                            │  │  - Relays commands    │  │    │
│                            │  │  - Relays events      │  │    │
│                            │  └────────────────────────┘  │    │
│                            └──────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/SSE
                              │ Commands: POST /api/runs/{id}/continue
                              │ Events: GET /api/runs/{id}/stream
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      normal_server                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         FastAPI Server (Port 8080)                       │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  RunState Manager                                  │  │  │
│  │  │  - Manages active runs                             │  │  │
│  │  │  - Executes plans via runner.py                   │  │  │
│  │  │  - Emits events to SSE subscribers                 │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  Routes:                                                  │  │
│  │  - POST /api/runs (start run)                           │  │
│  │  - GET /api/runs/{id}/stream (SSE events)              │  │
│  │  - POST /api/runs/{id}/continue (resume)               │  │
│  │  - POST /api/runs/{id}/pause (pause)                   │  │
│  │  - POST /api/runs/{id}/step (step)                      │  │
│  │  - GET /api/plans/{id}/graph (get graph data)          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. **normal_server** (Deployment Server)

**Purpose**: Standalone server for executing NormCode plans independently of the UI.

**Key Files**:
- `normal_server/server.py` - Main FastAPI server
- `normal_server/routes/runs.py` - Run execution endpoints
- `normal_server/routes/streaming.py` - SSE event streaming
- `normal_server/routes/health.py` - Connection info endpoint (`/api/connect`)
- `normal_server/runner.py` - Plan execution engine

**Key Features**:
- Executes plans via `runner.py`
- Manages active runs in memory (`active_runs` dict)
- Streams events via SSE (`/api/runs/{run_id}/stream`)
- Accepts control commands (pause, resume, step, stop)
- Can run independently without `canvas_app`

**Default Port**: `8080`

### 2. **canvas_app** (Visual Debugger)

**Purpose**: Visual IDE for debugging and monitoring NormCode plans, with support for both local and remote execution.

**Key Files**:
- `canvas_app/backend/services/execution/remote_proxy_executor.py` - **The Proxy**
- `canvas_app/backend/routers/execution_router.py` - Unified execution API
- `canvas_app/backend/routers/deployment_router.py` - Remote server management
- `canvas_app/frontend/src/stores/deploymentStore.ts` - Frontend state

**Key Features**:
- Visual graph rendering (React Flow)
- Real-time execution monitoring
- Breakpoints and step debugging
- Can execute locally OR connect to remote `normal_server`
- Unified API - frontend doesn't know if execution is local or remote

**Default Ports**: 
- Backend: `8000`
- Frontend: `5173`

## How They Connect: RemoteProxyExecutor

The `RemoteProxyExecutor` is the **heart of the connection**. It acts as a transparent relay:

### Connection Flow

1. **User loads remote project in canvas_app**:
   - Frontend calls `POST /api/deployment/servers/{server_id}/plans/{plan_id}/load`
   - Backend fetches graph data from `normal_server` via `GET /api/plans/{plan_id}/graph`
   - Graph is displayed in canvas

2. **User starts execution**:
   - Frontend calls `POST /api/execution/start`
   - Backend detects remote project and:
     - Starts run on `normal_server`: `POST {server_url}/api/runs`
     - Activates `RemoteProxyExecutor` to connect to the run
     - Proxy connects to SSE stream: `GET {server_url}/api/runs/{run_id}/stream`

3. **Proxy relays events**:
   - `normal_server` emits SSE events (node statuses, progress, logs)
   - `RemoteProxyExecutor` receives events via SSE
   - Proxy transforms events to canonical format
   - Proxy emits events through `canvas_app`'s WebSocket to frontend
   - Frontend receives events as if execution were local

4. **User controls execution**:
   - Frontend calls `POST /api/execution/pause` (or step, resume, stop)
   - `execution_router.py` routes command to `RemoteProxyExecutor`
   - Proxy forwards command to `normal_server`: `POST {server_url}/api/runs/{run_id}/pause`
   - `normal_server` pauses execution and emits event
   - Event flows back through proxy to frontend

## Communication Protocol

### Commands (canvas_app → normal_server)

All commands are HTTP POST requests:

```
POST {server_url}/api/runs/{run_id}/continue  - Resume execution
POST {server_url}/api/runs/{run_id}/pause     - Pause execution
POST {server_url}/api/runs/{run_id}/step      - Step one inference
POST {server_url}/api/runs/{run_id}/stop      - Stop execution
POST {server_url}/api/runs/{run_id}/breakpoints - Set breakpoint
DELETE {server_url}/api/runs/{run_id}/breakpoints/{flow_index} - Clear breakpoint
```

### Events (normal_server → canvas_app)

Events are streamed via **Server-Sent Events (SSE)**:

```
GET {server_url}/api/runs/{run_id}/stream
```

**Event Types**:
- `connected` - Initial connection with full state
- `node:statuses` - Batch node status update
- `inference:started` - Inference execution began
- `inference:completed` - Inference finished
- `inference:failed` - Inference failed
- `execution:progress` - Progress update
- `execution:paused` - Execution paused
- `execution:resumed` - Execution resumed
- `execution:stopped` - Execution stopped
- `breakpoint:hit` - Breakpoint reached
- `run:completed` - Run finished
- `run:failed` - Run failed
- `log:entry` - Log message

### Data Fetching

```
GET {server_url}/api/plans/{plan_id}/graph          - Get full graph (concepts + inferences)
GET {server_url}/api/runs/{run_id}                  - Get run status
GET {server_url}/api/runs/{run_id}/node-statuses    - Get all node statuses
GET {server_url}/api/connect                        - Verify connectivity
```

## Unified Execution API

The `canvas_app` backend provides a **unified execution API** that routes commands to either:
- **Local ExecutionController** (for local projects)
- **RemoteProxyExecutor** (for remote projects)

The routing happens in `execution_router.py` via `_get_active_executor()`:

```python
def _get_active_executor():
    # Check if there's an active remote proxy
    remote_proxy = get_active_remote_proxy()
    if remote_proxy and remote_proxy.is_connected:
        return remote_proxy, True
    
    # Default to local execution controller
    return execution_controller, False
```

This means the frontend uses the **same endpoints** regardless of execution location:
- `POST /api/execution/start`
- `POST /api/execution/pause`
- `POST /api/execution/step`
- `POST /api/execution/stop`
- `GET /api/execution/state`

## State Synchronization

The `RemoteProxyExecutor` maintains a **mirrored state** that stays in sync with the remote server:

1. **Initial Sync**: On connect, fetches full state from `normal_server`
2. **Event Updates**: Updates local state as events arrive via SSE
3. **Command Responses**: Updates state based on command responses

This ensures the canvas UI always shows accurate status even though execution is remote.

## Key Differences: Local vs Remote

| Aspect | Local Execution | Remote Execution |
|--------|----------------|------------------|
| **Executor** | `ExecutionController` | `RemoteProxyExecutor` |
| **Event Source** | Generated locally | SSE from `normal_server` |
| **Command Target** | Local orchestrator | HTTP to `normal_server` |
| **State Storage** | Local in-memory | Mirrored from remote |
| **Graph Data** | Loaded from files | Fetched via API |
| **Project Type** | Local file-based | Remote server-based |

## Common Issues & Debugging

### Issue: Remote proxy not connecting

**Symptoms**: 
- Events not appearing in canvas
- Commands not working
- "No active executor" errors

**Debug Steps**:
1. Check `normal_server` is running: `curl http://localhost:8080/health`
2. Check connectivity: `curl http://localhost:8080/api/connect`
3. Verify run exists: `curl http://localhost:8080/api/runs/{run_id}`
4. Check SSE stream: `curl http://localhost:8080/api/runs/{run_id}/stream`
5. Check `canvas_app` backend logs for proxy connection errors

### Issue: Events not flowing

**Symptoms**:
- Graph not updating
- Node statuses stuck
- No progress updates

**Debug Steps**:
1. Verify SSE connection is active (check `RemoteProxyExecutor._sse_task`)
2. Check `normal_server` is emitting events (check `RunState` event subscribers)
3. Verify event transformation in `_handle_and_relay_event()`
4. Check WebSocket connection from frontend to `canvas_app` backend

### Issue: Commands not working

**Symptoms**:
- Pause/resume/step buttons don't work
- Commands timeout or return errors

**Debug Steps**:
1. Verify routing: Check `_get_active_executor()` returns proxy
2. Check command forwarding: Verify HTTP requests reach `normal_server`
3. Check `normal_server` logs for command processing errors
4. Verify run state: Check if run is in correct state for command (e.g., paused for resume)

## File Locations Summary

### normal_server
- `normal_server/server.py` - Main server entry point
- `normal_server/routes/runs.py` - Run execution endpoints
- `normal_server/routes/streaming.py` - SSE streaming endpoint
- `normal_server/routes/health.py` - Health and connection info
- `normal_server/service.py` - Run state management
- `normal_server/runner.py` - Plan execution engine

### canvas_app
- `canvas_app/backend/services/execution/remote_proxy_executor.py` - **The Proxy**
- `canvas_app/backend/routers/execution_router.py` - Unified execution API
- `canvas_app/backend/routers/deployment_router.py` - Remote server management
- `canvas_app/backend/services/deployment_service.py` - Server communication
- `canvas_app/frontend/src/stores/deploymentStore.ts` - Frontend state
- `canvas_app/frontend/src/services/api.ts` - API client

## Summary

The relationship is:
- **normal_server**: Executes plans independently, streams events via SSE
- **canvas_app**: Visual debugger that can connect to `normal_server` via `RemoteProxyExecutor`
- **RemoteProxyExecutor**: Transparent relay that makes remote execution look local
- **Unified API**: Frontend uses same endpoints for local and remote execution

The architecture enables:
- ✅ Running plans on remote servers while debugging locally
- ✅ Visual monitoring of remote executions
- ✅ Full debugging capabilities (breakpoints, step, pause) for remote runs
- ✅ Seamless switching between local and remote execution

