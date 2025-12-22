"""
NormCode Canvas - Combined Launcher

Starts both the FastAPI backend and Vite frontend dev server.
Automatically checks and installs dependencies on first run.

Usage:
    python launch.py           # Default: dev mode with auto-reload
    python launch.py --prod    # Production mode (no reload)
    python launch.py --dev     # Explicit dev mode (same as default)
    python launch.py --install # Force reinstall all dependencies
    python launch.py --skip-deps # Skip dependency checks
"""

import subprocess
import sys
import os
import time
import signal
import argparse
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR / "backend"
FRONTEND_DIR = SCRIPT_DIR / "frontend"

# Required Python packages (from requirements.txt)
REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "websockets",
    "pydantic",
    "pydantic_settings",
    "python_multipart",
]


def print_header(text: str, char: str = "="):
    """Print a formatted header."""
    print(f"\n{char * 60}")
    print(f"  {text}")
    print(f"{char * 60}")


def print_step(step: str, total: str, message: str):
    """Print a step indicator."""
    print(f"\n[{step}/{total}] {message}")


def check_python_package(package_name: str) -> bool:
    """Check if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def check_backend_dependencies() -> tuple[bool, list[str]]:
    """Check if all backend Python dependencies are installed."""
    missing = []
    for package in REQUIRED_PACKAGES:
        if not check_python_package(package):
            missing.append(package)
    return len(missing) == 0, missing


def check_frontend_dependencies() -> bool:
    """Check if frontend dependencies are installed (node_modules exists)."""
    node_modules = FRONTEND_DIR / "node_modules"
    return node_modules.exists() and (node_modules / ".package-lock.json").exists()


def check_npm_available() -> bool:
    """Check if npm is available in PATH."""
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    return shutil.which(npm_cmd) is not None


def check_node_available() -> bool:
    """Check if node is available in PATH."""
    node_cmd = "node.exe" if sys.platform == "win32" else "node"
    return shutil.which(node_cmd) is not None


def install_backend_dependencies() -> bool:
    """Install backend Python dependencies."""
    print("  Installing Python dependencies...")
    requirements_file = BACKEND_DIR / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"  ERROR: {requirements_file} not found!")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            capture_output=True,
            text=True,
            cwd=BACKEND_DIR
        )
        
        if result.returncode == 0:
            print("  ✓ Python dependencies installed successfully")
            return True
        else:
            print(f"  ERROR: pip install failed:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"  ERROR: Failed to install Python dependencies: {e}")
        return False


def install_frontend_dependencies() -> bool:
    """Install frontend npm dependencies."""
    print("  Installing npm dependencies (this may take a minute)...")
    
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    
    try:
        result = subprocess.run(
            [npm_cmd, "install"],
            capture_output=True,
            text=True,
            cwd=FRONTEND_DIR
        )
        
        if result.returncode == 0:
            print("  ✓ npm dependencies installed successfully")
            return True
        else:
            print(f"  ERROR: npm install failed:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"  ERROR: Failed to install npm dependencies: {e}")
        return False


def check_and_install_dependencies(force_install: bool = False, skip_check: bool = False) -> bool:
    """
    Check and install dependencies if needed.
    
    Args:
        force_install: Force reinstall all dependencies
        skip_check: Skip dependency checking entirely
    
    Returns:
        True if all dependencies are ready, False otherwise
    """
    if skip_check:
        print("\n⚠ Skipping dependency checks (--skip-deps)")
        return True
    
    print_header("Checking Dependencies", "-")
    
    all_ready = True
    
    # Check backend dependencies
    print("\n📦 Backend (Python):")
    backend_ok, missing_packages = check_backend_dependencies()
    
    if backend_ok and not force_install:
        print("  ✓ All Python dependencies installed")
    else:
        if force_install:
            print("  → Force reinstalling Python dependencies...")
        else:
            print(f"  ✗ Missing packages: {', '.join(missing_packages)}")
        
        if not install_backend_dependencies():
            all_ready = False
    
    # Check frontend dependencies
    print("\n📦 Frontend (Node.js):")
    
    # First check if Node.js and npm are available
    if not check_node_available():
        print("  ✗ Node.js is not installed or not in PATH")
        print("    Please install Node.js from https://nodejs.org/")
        all_ready = False
    elif not check_npm_available():
        print("  ✗ npm is not available in PATH")
        print("    Please ensure npm is installed with Node.js")
        all_ready = False
    else:
        frontend_ok = check_frontend_dependencies()
        
        if frontend_ok and not force_install:
            print("  ✓ All npm dependencies installed")
        else:
            if force_install:
                print("  → Force reinstalling npm dependencies...")
            else:
                print("  ✗ node_modules not found or incomplete")
            
            if not install_frontend_dependencies():
                all_ready = False
    
    if all_ready:
        print("\n✓ All dependencies ready!")
    else:
        print("\n✗ Some dependencies failed to install. Please fix the errors above.")
    
    return all_ready


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="NormCode Canvas Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch.py              # Start in dev mode (default)
  python launch.py --prod       # Start in production mode
  python launch.py --install    # Force reinstall all dependencies
  python launch.py --skip-deps  # Skip dependency checks
  python launch.py --backend-only   # Only start the backend
  python launch.py --frontend-only  # Only start the frontend
        """
    )
    parser.add_argument("--prod", action="store_true", 
                        help="Run in production mode (no auto-reload)")
    parser.add_argument("--dev", action="store_true", 
                        help="Run in development mode with auto-reload (default)")
    parser.add_argument("--backend-only", action="store_true", 
                        help="Only start the backend server")
    parser.add_argument("--frontend-only", action="store_true", 
                        help="Only start the frontend server")
    parser.add_argument("--install", action="store_true", 
                        help="Force reinstall all dependencies")
    parser.add_argument("--skip-deps", action="store_true", 
                        help="Skip dependency checking")
    args = parser.parse_args()
    
    # Dev mode is the default
    dev_mode = not args.prod
    
    print_header("NormCode Canvas Launcher")
    print(f"  Mode: {'DEVELOPMENT' if dev_mode else 'PRODUCTION'}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Backend: {BACKEND_DIR}")
    print(f"  Frontend: {FRONTEND_DIR}")
    
    # Check and install dependencies
    if not check_and_install_dependencies(
        force_install=args.install, 
        skip_check=args.skip_deps
    ):
        print("\n❌ Cannot start: dependency installation failed")
        print("   Try running: pip install -r canvas_app/backend/requirements.txt")
        print("   And: cd canvas_app/frontend && npm install")
        sys.exit(1)
    
    processes = []
    
    try:
        print_header(f"Starting NormCode Canvas ({'DEV' if dev_mode else 'PROD'})")
        
        # Start backend
        if not args.frontend_only:
            print_step("1", "2", "Starting FastAPI backend on http://localhost:8000")
            
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
            processes.append(("Backend", backend_process))
        
        # Wait a moment for backend to start
        if not args.frontend_only:
            time.sleep(2)
        
        # Start frontend
        if not args.backend_only:
            print_step("2", "2", "Starting Vite frontend on http://localhost:5173")
            
            # Use npm.cmd on Windows to avoid shell=True issues
            npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
            
            frontend_process = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd=FRONTEND_DIR,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
            )
            processes.append(("Frontend", frontend_process))
            print("         Hot reload: ENABLED (changes update instantly)")
        
        print_header("NormCode Canvas is Running!")
        
        if not args.backend_only:
            print("\n  🌐 Frontend:    http://localhost:5173")
        if not args.frontend_only:
            print("  📡 Backend API: http://localhost:8000/docs")
            print("  🔌 WebSocket:   ws://localhost:8000/ws/events")
        
        if dev_mode:
            print("\n  📝 Development Mode:")
            print("     • Backend auto-reloads on .py file changes")
            print("     • Frontend hot-reloads on .tsx/.ts/.css changes")
        
        print("\n  ⏹  Press Ctrl+C to stop all servers...")
        print("=" * 60)
        
        # Wait for processes
        while True:
            for name, p in processes:
                if p.poll() is not None:
                    print(f"\n⚠ {name} process (PID {p.pid}) exited with code {p.returncode}")
                    # If one process dies, stop all
                    if p.returncode != 0:
                        raise KeyboardInterrupt()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
    finally:
        # Terminate all processes
        for name, p in processes:
            try:
                print(f"   Stopping {name}...")
                if sys.platform == "win32":
                    p.terminate()
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception as e:
                print(f"   Error terminating {name}: {e}")
        
        # Wait for processes to terminate
        for name, p in processes:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"   Force killing {name}...")
                p.kill()
        
        print("\n✓ All servers stopped.")


if __name__ == "__main__":
    main()
