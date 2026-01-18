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
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Server directory (where this file is located)
SERVER_DIR = Path(__file__).resolve().parent

# Detect if running from built package or source
IS_BUILT_PACKAGE = (SERVER_DIR / "infra").exists() and (SERVER_DIR / "tools").exists()

if IS_BUILT_PACKAGE:
    if str(SERVER_DIR) not in sys.path:
        sys.path.insert(0, str(SERVER_DIR))
else:
    PROJECT_ROOT = SERVER_DIR.parent
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError:
    print("FastAPI not installed. Run: pip install fastapi uvicorn", file=sys.stderr)
    sys.exit(1)

# Import local modules
from service import get_config, get_available_llm_models, SETTINGS_PATH
from routes import include_all_routes


# ============================================================================
# FastAPI App Lifespan
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
    logging.info("NormCode Deployment Server starting...")
    logging.info(f"  Plans directory: {cfg.plans_dir}")
    logging.info(f"  Runs directory: {cfg.runs_dir}")
    
    # Log LLM settings
    if SETTINGS_PATH and SETTINGS_PATH.exists():
        llm_models = get_available_llm_models()
        model_names = [m["id"] for m in llm_models if not m.get("is_mock")]
        logging.info(f"  LLM settings: {SETTINGS_PATH}")
        logging.info(f"  Available models: {', '.join(model_names) if model_names else 'demo only'}")
    else:
        logging.warning(f"  LLM settings not found: {SETTINGS_PATH}")
        logging.info("  Only demo (mock) mode available")
    
    # Ensure directories exist
    cfg.ensure_directories()
    
    yield
    
    # Shutdown
    logging.info("NormCode Deployment Server shutting down...")


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="NormCode Deployment Server",
    description="Execute NormCode plans via REST API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware - allows canvas_app to connect from different origin
# This is essential for RemoteProxyExecutor to communicate with this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all route modules
include_all_routes(app)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="NormCode Deployment Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind")
    
    # Determine default paths
    if IS_BUILT_PACKAGE:
        default_plans_dir = SERVER_DIR / "data" / "plans"
        default_runs_dir = SERVER_DIR / "data" / "runs"
    else:
        default_plans_dir = SERVER_DIR / "data" / "plans"
        default_runs_dir = SERVER_DIR / "data" / "runs"
    
    parser.add_argument("--plans-dir", type=Path, default=default_plans_dir, help="Plans directory")
    parser.add_argument("--runs-dir", type=Path, default=default_runs_dir, help="Runs directory")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    # Set environment variables for config (picked up by ServerConfig)
    os.environ["NORMCODE_HOST"] = args.host
    os.environ["NORMCODE_PORT"] = str(args.port)
    os.environ["NORMCODE_PLANS_DIR"] = str(args.plans_dir.resolve())
    os.environ["NORMCODE_RUNS_DIR"] = str(args.runs_dir.resolve())
    
    print("Starting NormCode Deployment Server...")
    print(f"  API: http://{args.host}:{args.port}")
    print(f"  Docs: http://{args.host}:{args.port}/docs")
    print(f"  Plans: {args.plans_dir.resolve()}")
    print(f"  Runs: {args.runs_dir.resolve()}")
    
    # Determine the correct module path for uvicorn
    if IS_BUILT_PACKAGE:
        app_path = "server:app"
    else:
        app_path = "normal_server.server:app"
    
    uvicorn.run(
        app_path,
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
