"""
NormCode Canvas - Combined Launcher

Starts both the FastAPI backend and Vite frontend dev server.

Usage:
    python launch.py           # Default: dev mode with auto-reload
    python launch.py --prod    # Production mode (no reload)
    python launch.py --dev     # Explicit dev mode (same as default)
"""

import subprocess
import sys
import os
import time
import signal
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR / "backend"
FRONTEND_DIR = SCRIPT_DIR / "frontend"

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="NormCode Canvas Launcher")
    parser.add_argument("--prod", action="store_true", help="Run in production mode (no auto-reload)")
    parser.add_argument("--dev", action="store_true", help="Run in development mode with auto-reload (default)")
    parser.add_argument("--backend-only", action="store_true", help="Only start the backend server")
    parser.add_argument("--frontend-only", action="store_true", help="Only start the frontend server")
    args = parser.parse_args()
    
    # Dev mode is the default
    dev_mode = not args.prod
    
    processes = []
    
    try:
        print("=" * 60)
        print(f"Starting NormCode Canvas ({'DEV MODE' if dev_mode else 'PRODUCTION MODE'})")
        print("=" * 60)
        
        # Start backend
        if not args.frontend_only:
            print(f"\n[1/2] Starting FastAPI backend on http://localhost:8000")
            
            # Build uvicorn command
            uvicorn_cmd = [
                sys.executable, "-m", "uvicorn", "main:app",
                "--host", "127.0.0.1", "--port", "8000"
            ]
            
            if dev_mode:
                # Dev mode: enable reload and watch additional directories
                uvicorn_cmd.extend([
                    "--reload",
                    "--reload-dir", str(BACKEND_DIR),  # Watch backend directory
                ])
                print("         Auto-reload: ENABLED (changes will restart server)")
            else:
                print("         Auto-reload: DISABLED (production mode)")
            
            backend_process = subprocess.Popen(
                uvicorn_cmd,
                cwd=BACKEND_DIR,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )
            processes.append(backend_process)
        
        # Wait a moment for backend to start
        if not args.frontend_only:
            time.sleep(2)
        
        # Start frontend
        if not args.backend_only:
            print(f"\n[2/2] Starting Vite frontend on http://localhost:5173")
            
            # Use npm.cmd on Windows to avoid shell=True issues
            npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
            
            frontend_process = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd=FRONTEND_DIR,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )
            processes.append(frontend_process)
            print("         Hot reload: ENABLED (changes update instantly)")
        
        print("\n" + "=" * 60)
        print("NormCode Canvas is running!")
        print("=" * 60)
        
        if not args.backend_only:
            print("\n  Frontend: http://localhost:5173")
        if not args.frontend_only:
            print("  Backend API: http://localhost:8000/docs")
            print("  WebSocket: ws://localhost:8000/ws/events")
        
        if dev_mode:
            print("\n  [DEV MODE]")
            print("  - Backend auto-reloads on .py file changes")
            print("  - Frontend hot-reloads on .tsx/.ts/.css changes")
        
        print("\nPress Ctrl+C to stop all servers...")
        
        # Wait for processes
        while True:
            for p in processes:
                if p.poll() is not None:
                    print(f"\nProcess {p.pid} exited with code {p.returncode}")
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    finally:
        # Terminate all processes
        for p in processes:
            try:
                if sys.platform == "win32":
                    p.terminate()
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception as e:
                print(f"Error terminating process: {e}")
        
        print("All servers stopped.")


if __name__ == "__main__":
    main()
