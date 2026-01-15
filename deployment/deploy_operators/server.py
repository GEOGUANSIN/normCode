#!/usr/bin/env python3
"""
NormCode Deployment Server

Minimal standalone FastAPI server for executing NormCode plans.
Independent from Canvas App - can run plans without the UI.

Usage:
    python server.py
    python server.py --port 9000
    python server.py --plans-dir ./my_plans
"""

import sys
import json
import uuid
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("FastAPI not installed. Run: pip install fastapi uvicorn", file=sys.stderr)
    sys.exit(1)

# Import runner components
from deployment.runner import PlanConfig, load_repositories, create_body, CustomParadigmTool

# Deployment settings path
DEPLOYMENT_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = DEPLOYMENT_DIR / "settings.yaml"


# ============================================================================
# Configuration
# ============================================================================

class ServerConfig:
    """Server configuration from environment or defaults."""
    
    def __init__(self):
        import os
        self.host = os.getenv("NORMCODE_HOST", "0.0.0.0")
        self.port = int(os.getenv("NORMCODE_PORT", "8080"))
        self.plans_dir = Path(os.getenv("NORMCODE_PLANS_DIR", "./plans"))
        self.runs_dir = Path(os.getenv("NORMCODE_RUNS_DIR", "./runs"))
        self.log_level = os.getenv("NORMCODE_LOG_LEVEL", "INFO")


# Global state (initialized in main or lifespan)
config: Optional[ServerConfig] = None
active_runs: Dict[str, "RunState"] = {}
websocket_connections: Dict[str, List[WebSocket]] = {}


def get_config() -> ServerConfig:
    """Get or create config."""
    global config
    if config is None:
        config = ServerConfig()
    return config


# ============================================================================
# Schemas
# ============================================================================

class StartRunRequest(BaseModel):
    """Request to start a new run."""
    plan_id: str = Field(..., description="Plan identifier (config filename)")
    run_id: Optional[str] = Field(None, description="Custom run ID (auto-generated if not provided)")
    llm_model: Optional[str] = Field(None, description="Override LLM model")
    max_cycles: Optional[int] = Field(None, description="Override max cycles")
    ground_inputs: Optional[Dict[str, Any]] = Field(None, description="Values for ground concepts")


class RunStatus(BaseModel):
    """Run status response."""
    run_id: str
    plan_id: str
    status: str  # pending, running, completed, failed, paused
    started_at: Optional[str]
    completed_at: Optional[str]
    progress: Optional[Dict[str, Any]]
    error: Optional[str]


class PlanInfo(BaseModel):
    """Plan information."""
    id: str
    name: str
    description: Optional[str]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]


# ============================================================================
# Run State Management
# ============================================================================

class RunState:
    """Tracks the state of an active run."""
    
    def __init__(self, run_id: str, plan_id: str, config: PlanConfig):
        self.run_id = run_id
        self.plan_id = plan_id
        self.config = config
        self.status = "pending"
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error: Optional[str] = None
        self.result: Optional[Dict[str, Any]] = None
        self.orchestrator = None
        self._task: Optional[asyncio.Task] = None
    
    def to_status(self) -> RunStatus:
        return RunStatus(
            run_id=self.run_id,
            plan_id=self.plan_id,
            status=self.status,
            started_at=self.started_at.isoformat() if self.started_at else None,
            completed_at=self.completed_at.isoformat() if self.completed_at else None,
            progress=None,  # TODO: extract from orchestrator
            error=self.error
        )


# ============================================================================
# Plan Discovery
# ============================================================================

def discover_plans(plans_dir: Path) -> Dict[str, PlanConfig]:
    """Discover all plan configs in the plans directory."""
    plans = {}
    
    if not plans_dir.exists():
        plans_dir.mkdir(parents=True, exist_ok=True)
        return plans
    
    # Find all .normcode-canvas.json files
    for config_file in plans_dir.rglob("*.normcode-canvas.json"):
        try:
            plan_config = PlanConfig(config_file)
            plans[plan_config.id] = plan_config
        except Exception as e:
            logging.warning(f"Failed to load plan config {config_file}: {e}")
    
    # Also check for manifest.json files (unpacked packages)
    for manifest_file in plans_dir.rglob("manifest.json"):
        try:
            plan_config = PlanConfig(manifest_file)
            plans[plan_config.id] = plan_config
        except Exception as e:
            logging.warning(f"Failed to load manifest {manifest_file}: {e}")
    
    return plans


# ============================================================================
# Execution
# ============================================================================

async def execute_run(run_state: RunState, llm_override: Optional[str], max_cycles_override: Optional[int]):
    """Execute a run in the background."""
    from infra._orchest._orchestrator import Orchestrator
    
    run_state.status = "running"
    run_state.started_at = datetime.now()
    
    try:
        # Load repositories
        concept_repo, inference_repo = load_repositories(run_state.config)
        
        # Create body with deployment tools for actual LLM runs
        # Uses deployment/settings.yaml for LLM configuration
        body = create_body(run_state.config, llm_override, use_deployment_tools=True)
        
        logging.info(f"Run {run_state.run_id}: Using LLM '{llm_override or run_state.config.llm_model}'")
        
        # Create orchestrator
        cfg = get_config()
        max_cycles = max_cycles_override or run_state.config.max_cycles
        run_dir = cfg.runs_dir / run_state.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        
        orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            body=body,
            max_cycles=max_cycles,
            db_path=str(run_dir / "run.db"),
            run_id=run_state.run_id
        )
        
        run_state.orchestrator = orchestrator
        
        # Run (async version)
        final_concepts = await orchestrator.run_async()
        
        # Collect results
        run_state.result = {
            "run_id": run_state.run_id,
            "plan_id": run_state.plan_id,
            "status": "completed",
            "final_concepts": []
        }
        
        for fc in final_concepts:
            concept_result = {
                "name": fc.concept_name,
                "has_value": False
            }
            if fc and fc.concept and fc.concept.reference:
                concept_result["has_value"] = True
                concept_result["shape"] = list(fc.concept.reference.shape)
                data_str = str(fc.concept.reference.tensor)
                if len(data_str) > 500:
                    data_str = data_str[:497] + "..."
                concept_result["value"] = data_str
            run_state.result["final_concepts"].append(concept_result)
        
        run_state.status = "completed"
        run_state.completed_at = datetime.now()
        
        # Notify websocket subscribers
        await broadcast_event(run_state.run_id, {
            "event": "run:completed",
            "run_id": run_state.run_id,
            "result": run_state.result
        })
        
    except Exception as e:
        logging.exception(f"Run {run_state.run_id} failed: {e}")
        run_state.status = "failed"
        run_state.error = str(e)
        run_state.completed_at = datetime.now()
        
        await broadcast_event(run_state.run_id, {
            "event": "run:failed",
            "run_id": run_state.run_id,
            "error": str(e)
        })


async def broadcast_event(run_id: str, event: Dict[str, Any]):
    """Broadcast event to all websocket subscribers for a run."""
    connections = websocket_connections.get(run_id, [])
    disconnected = []
    
    for ws in connections:
        try:
            await ws.send_json(event)
        except Exception:
            disconnected.append(ws)
    
    # Remove disconnected
    for ws in disconnected:
        connections.remove(ws)


# ============================================================================
# FastAPI App
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifespan - startup/shutdown."""
    cfg = get_config()
    
    # Startup
    logging.basicConfig(
        level=getattr(logging, cfg.log_level),
        format="%(asctime)s | %(levelname)s | %(message)s"
    )
    logging.info(f"NormCode Deployment Server starting...")
    logging.info(f"  Plans directory: {cfg.plans_dir}")
    logging.info(f"  Runs directory: {cfg.runs_dir}")
    
    # Log LLM settings
    if SETTINGS_PATH.exists():
        llm_models = get_available_llm_models()
        model_names = [m["id"] for m in llm_models if not m.get("is_mock")]
        logging.info(f"  LLM settings: {SETTINGS_PATH}")
        logging.info(f"  Available models: {', '.join(model_names) if model_names else 'demo only'}")
    else:
        logging.warning(f"  LLM settings not found: {SETTINGS_PATH}")
        logging.info(f"  Only demo (mock) mode available")
    
    # Ensure directories exist
    cfg.plans_dir.mkdir(parents=True, exist_ok=True)
    cfg.runs_dir.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Shutdown
    logging.info("NormCode Deployment Server shutting down...")


app = FastAPI(
    title="NormCode Deployment Server",
    description="Execute NormCode plans via REST API",
    version="0.1.0",
    lifespan=lifespan
)


# ============================================================================
# Health & Info
# ============================================================================

def get_available_llm_models() -> List[Dict[str, Any]]:
    """Get available LLM models from settings.yaml."""
    import yaml
    
    models = [{"id": "demo", "name": "Demo (Mock)", "is_mock": True}]
    
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings = yaml.safe_load(f) or {}
            
            base_url = settings.pop("BASE_URL", None)
            
            for model_name, config in settings.items():
                if isinstance(config, dict):
                    models.append({
                        "id": model_name,
                        "name": model_name,
                        "base_url": base_url,
                        "is_mock": False,
                    })
        except Exception as e:
            logging.warning(f"Failed to load LLM settings: {e}")
    
    return models


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/info")
async def info():
    """Server information."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    llm_models = get_available_llm_models()
    return {
        "version": "0.1.0",
        "plans_count": len(plans),
        "active_runs": len(active_runs),
        "plans_dir": str(cfg.plans_dir),
        "runs_dir": str(cfg.runs_dir),
        "llm_models": llm_models,
        "settings_path": str(SETTINGS_PATH) if SETTINGS_PATH.exists() else None
    }


@app.get("/api/models")
async def list_models():
    """List available LLM models."""
    return get_available_llm_models()


# ============================================================================
# Plans API
# ============================================================================

@app.get("/api/plans", response_model=List[PlanInfo])
async def list_plans():
    """List all available plans."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    result = []
    
    for plan_id, plan_config in plans.items():
        # Extract inputs/outputs from repo if available
        inputs = {}
        outputs = {}
        
        try:
            if plan_config.concept_repo_path and plan_config.concept_repo_path.exists():
                with open(plan_config.concept_repo_path, 'r', encoding='utf-8') as f:
                    concepts = json.load(f)
                for c in concepts:
                    if c.get('is_ground_concept'):
                        inputs[c['concept_name']] = {"type": "any", "required": True}
                    if c.get('is_final_concept'):
                        outputs[c['concept_name']] = {"type": "any"}
        except Exception:
            pass
        
        result.append(PlanInfo(
            id=plan_id,
            name=plan_config.name,
            description=plan_config.description,
            inputs=inputs,
            outputs=outputs
        ))
    
    return result


@app.get("/api/plans/{plan_id}")
async def get_plan(plan_id: str):
    """Get details for a specific plan."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    if plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    plan_config = plans[plan_id]
    
    return {
        "id": plan_id,
        "name": plan_config.name,
        "description": plan_config.description,
        "config_path": str(plan_config.config_path),
        "concept_repo": str(plan_config.concept_repo_path),
        "inference_repo": str(plan_config.inference_repo_path),
        "llm_model": plan_config.llm_model,
        "max_cycles": plan_config.max_cycles
    }


# ============================================================================
# Runs API
# ============================================================================

@app.post("/api/runs", response_model=RunStatus)
async def start_run(request: StartRunRequest, background_tasks: BackgroundTasks):
    """Start a new plan execution."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    if request.plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {request.plan_id}")
    
    plan_config = plans[request.plan_id]
    run_id = request.run_id or str(uuid.uuid4())
    
    if run_id in active_runs:
        raise HTTPException(409, f"Run already exists: {run_id}")
    
    # Create run state
    run_state = RunState(run_id, request.plan_id, plan_config)
    active_runs[run_id] = run_state
    
    # Start execution in background
    background_tasks.add_task(
        execute_run,
        run_state,
        request.llm_model,
        request.max_cycles
    )
    
    return run_state.to_status()


@app.get("/api/runs", response_model=List[RunStatus])
async def list_runs():
    """List all runs (active and recent)."""
    return [run.to_status() for run in active_runs.values()]


@app.get("/api/runs/{run_id}", response_model=RunStatus)
async def get_run(run_id: str):
    """Get status of a specific run."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    return active_runs[run_id].to_status()


@app.get("/api/runs/{run_id}/result")
async def get_run_result(run_id: str):
    """Get the result of a completed run."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    
    if run.status != "completed":
        raise HTTPException(400, f"Run not completed (status: {run.status})")
    
    return run.result


@app.post("/api/runs/{run_id}/stop")
async def stop_run(run_id: str):
    """Stop a running execution."""
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run = active_runs[run_id]
    
    if run.status != "running":
        raise HTTPException(400, f"Run not running (status: {run.status})")
    
    # TODO: Implement graceful stop via orchestrator
    run.status = "stopped"
    run.completed_at = datetime.now()
    
    return {"status": "stopped", "run_id": run_id}


# ============================================================================
# WebSocket Events
# ============================================================================

@app.websocket("/ws/runs/{run_id}")
async def websocket_run_events(websocket: WebSocket, run_id: str):
    """WebSocket for real-time run events."""
    await websocket.accept()
    
    # Register connection
    if run_id not in websocket_connections:
        websocket_connections[run_id] = []
    websocket_connections[run_id].append(websocket)
    
    try:
        # Send current status
        if run_id in active_runs:
            await websocket.send_json({
                "event": "connected",
                "run_id": run_id,
                "status": active_runs[run_id].status
            })
        
        # Keep connection alive
        while True:
            try:
                # Wait for messages (ping/pong or commands)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping to keep alive
                await websocket.send_text("ping")
    except WebSocketDisconnect:
        pass
    finally:
        # Unregister connection
        if run_id in websocket_connections:
            websocket_connections[run_id].remove(websocket)


# ============================================================================
# Main
# ============================================================================

def main():
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="NormCode Deployment Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind")
    parser.add_argument("--plans-dir", type=Path, default="./plans", help="Plans directory")
    parser.add_argument("--runs-dir", type=Path, default="./runs", help="Runs directory")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    # Set environment variables for config (picked up by ServerConfig)
    os.environ["NORMCODE_HOST"] = args.host
    os.environ["NORMCODE_PORT"] = str(args.port)
    os.environ["NORMCODE_PLANS_DIR"] = str(args.plans_dir.resolve())
    os.environ["NORMCODE_RUNS_DIR"] = str(args.runs_dir.resolve())
    
    print(f"Starting NormCode Deployment Server...")
    print(f"  API: http://{args.host}:{args.port}")
    print(f"  Docs: http://{args.host}:{args.port}/docs")
    print(f"  Plans: {args.plans_dir.resolve()}")
    print(f"  Runs: {args.runs_dir.resolve()}")
    
    uvicorn.run(
        "deployment.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()

