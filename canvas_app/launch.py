"""
NormCode Canvas - Combined Launcher

Starts both the FastAPI backend and Vite frontend dev server.
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR / "backend"
FRONTEND_DIR = SCRIPT_DIR / "frontend"

def main():
    processes = []
    
    try:
        print("=" * 60)
        print("Starting NormCode Canvas")
        print("=" * 60)
        
        # Start backend
        print("\n[1/2] Starting FastAPI backend on http://localhost:8000")
        backend_process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
            cwd=BACKEND_DIR,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        processes.append(backend_process)
        
        # Wait a moment for backend to start
        time.sleep(2)
        
        # Start frontend
        print("\n[2/2] Starting Vite frontend on http://localhost:5173")
        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=FRONTEND_DIR,
            shell=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        processes.append(frontend_process)
        
        print("\n" + "=" * 60)
        print("NormCode Canvas is running!")
        print("=" * 60)
        print("\n  Frontend: http://localhost:5173")
        print("  Backend API: http://localhost:8000/docs")
        print("  WebSocket: ws://localhost:8000/ws/events")
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
