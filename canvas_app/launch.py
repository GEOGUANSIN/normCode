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
import socket
import urllib.request
import urllib.error
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR / "backend"
FRONTEND_DIR = SCRIPT_DIR / "frontend"
PROJECT_ROOT = SCRIPT_DIR.parent  # normCode root

# Required Python packages (from requirements.txt)
REQUIRED_PACKAGES = [
    "fastapi",
    "uvicorn",
    "websockets",
    "pydantic",
    "pydantic_settings",
    "python_multipart",
    # Infra module dependencies
    "openai",
    "yaml",  # pyyaml
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
            print("  [OK] Python dependencies installed successfully")
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
            print("  [OK] npm dependencies installed successfully")
            return True
        else:
            print(f"  ERROR: npm install failed:\n{result.stderr}")
            return False
    except Exception as e:
        print(f"  ERROR: Failed to install npm dependencies: {e}")
        return False


def check_infra_module() -> tuple[bool, str]:
    """Check if the infra module can be imported (required for backend)."""
    try:
        # Add project root to path temporarily
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        
        from infra._constants import PROJECT_ROOT as _
        return True, ""
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def check_settings_yaml() -> tuple[bool, str]:
    """Check if settings.yaml exists in project root."""
    settings_path = PROJECT_ROOT / "settings.yaml"
    if settings_path.exists():
        return True, str(settings_path)
    return False, str(settings_path)


def check_port_available(port: int) -> bool:
    """Check if a port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result != 0  # Port is available if connect fails
    except Exception:
        return True  # Assume available if we can't check


def kill_process_on_port(port: int) -> bool:
    """Kill any process using a specific port (Windows only)."""
    if sys.platform != "win32":
        return False
    
    try:
        # Find PID using netstat
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        pids_to_kill = set()
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if parts:
                    try:
                        pid = int(parts[-1])
                        if pid > 0:
                            pids_to_kill.add(pid)
                    except ValueError:
                        pass
        
        if not pids_to_kill:
            return True  # No process found, port is free
        
        # Kill each PID
        for pid in pids_to_kill:
            print(f"   Killing process {pid} on port {port}...")
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(pid)],
                capture_output=True,
                timeout=10
            )
        
        # Give time for port to be released
        time.sleep(1)
        return check_port_available(port)
    except Exception as e:
        print(f"   Error killing process on port {port}: {e}")
        return False


def wait_for_backend(port: int = 8000, timeout: int = 15) -> bool:
    """Wait for backend to start responding."""
    start_time = time.time()
    url = f"http://127.0.0.1:{port}/api/execution/config"
    
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except urllib.error.URLError:
            pass
        except Exception:
            pass
        time.sleep(0.5)
    
    return False


def verify_backend_can_start() -> tuple[bool, str]:
    """Verify the backend can be imported without errors."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", 
             "import sys; sys.path.insert(0, r'" + str(PROJECT_ROOT) + "'); "
             "from main import app; print('OK')"],
            capture_output=True,
            text=True,
            cwd=BACKEND_DIR,
            timeout=30
        )
        
        if result.returncode == 0 and "OK" in result.stdout:
            return True, ""
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            return False, error_msg
    except subprocess.TimeoutExpired:
        return False, "Import check timed out"
    except Exception as e:
        return False, str(e)


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
    print("\n[*] Backend (Python):")
    backend_ok, missing_packages = check_backend_dependencies()
    
    if backend_ok and not force_install:
        print("  [OK] All Python dependencies installed")
    else:
        if force_install:
            print("  → Force reinstalling Python dependencies...")
        else:
            print(f"  [FAIL] Missing packages: {', '.join(missing_packages)}")
        
        if not install_backend_dependencies():
            all_ready = False
    
    # Check infra module (required for backend to work)
    print("\n[*] NormCode Infra Module:")
    infra_ok, infra_error = check_infra_module()
    if infra_ok:
        print("  [OK] infra module available")
    else:
        print("  [FAIL] infra module not found")
        print(f"    Error: {infra_error}")
        print("    Make sure you're running from the normCode project directory")
        all_ready = False
    
    # Check settings.yaml
    print("\n[*] LLM Configuration:")
    settings_ok, settings_path = check_settings_yaml()
    if settings_ok:
        print(f"  [OK] settings.yaml found at {settings_path}")
    else:
        print(f"  ⚠ settings.yaml not found at {settings_path}")
        print("    LLM features will be limited to 'demo' mode")
        print("    See canvas_app/settings.yaml.example for template")
        # This is a warning, not a failure
    
    # Verify backend can actually start
    if all_ready:
        print("\n[*] Backend Import Check:")
        can_start, error = verify_backend_can_start()
        if can_start:
            print("  [OK] Backend imports successfully")
        else:
            print("  [FAIL] Backend failed to import")
            print(f"    Error: {error[:500]}...")  # Truncate long errors
            all_ready = False
    
    # Check frontend dependencies
    print("\n[*] Frontend (Node.js):")
    
    # First check if Node.js and npm are available
    if not check_node_available():
        print("  [FAIL] Node.js is not installed or not in PATH")
        print("    Please install Node.js from https://nodejs.org/")
        all_ready = False
    elif not check_npm_available():
        print("  [FAIL] npm is not available in PATH")
        print("    Please ensure npm is installed with Node.js")
        all_ready = False
    else:
        frontend_ok = check_frontend_dependencies()
        
        if frontend_ok and not force_install:
            print("  [OK] All npm dependencies installed")
        else:
            if force_install:
                print("  → Force reinstalling npm dependencies...")
            else:
                print("  [FAIL] node_modules not found or incomplete")
            
            if not install_frontend_dependencies():
                all_ready = False
    
    if all_ready:
        print("\n[OK] All dependencies ready!")
    else:
        print("\n[FAIL] Some dependencies failed to install. Please fix the errors above.")
    
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
  python launch.py --kill       # Kill existing servers before starting
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
    parser.add_argument("--kill", action="store_true", 
                        help="Kill any existing servers on ports 8000/5173 before starting")
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
        print("\n[ERROR] Cannot start: dependency installation failed")
        print("   Try running: pip install -r canvas_app/backend/requirements.txt")
        print("   And: cd canvas_app/frontend && npm install")
        sys.exit(1)
    
    processes = []
    
    try:
        print_header(f"Starting NormCode Canvas ({'DEV' if dev_mode else 'PROD'})")
        
        # Kill existing servers if --kill flag is used
        if args.kill:
            print("\n🔪 Killing existing servers...")
            if not args.frontend_only and not check_port_available(8000):
                kill_process_on_port(8000)
            if not args.backend_only and not check_port_available(5173):
                kill_process_on_port(5173)
            time.sleep(1)
        
        # Check if port 8000 is already in use
        if not args.frontend_only:
            if not check_port_available(8000):
                print("\n⚠ Port 8000 is already in use!")
                print("   Another backend may be running.")
                if sys.platform == "win32":
                    print("   Use --kill flag to automatically kill existing servers:")
                    print(f"   python {Path(__file__).name} --kill")
                else:
                    print("   Kill it manually or use a different port.")
                    print("   You can check with: lsof -i :8000")
                sys.exit(1)
        
        # Check if port 5173 is already in use
        if not args.backend_only:
            if not check_port_available(5173):
                print("\n⚠ Port 5173 is already in use!")
                print("   Another frontend may be running.")
                if sys.platform == "win32":
                    print("   Use --kill flag to automatically kill existing servers:")
                    print(f"   python {Path(__file__).name} --kill")
                else:
                    print("   Kill it manually or use a different port.")
                sys.exit(1)
        
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
        
        # Wait for backend to be ready (with health check)
        if not args.frontend_only:
            print("         Waiting for backend to start...", end="", flush=True)
            
            # First check if process died immediately
            time.sleep(1)
            if backend_process.poll() is not None:
                print(" FAILED!")
                print(f"\n[ERROR] Backend process exited with code {backend_process.returncode}")
                print("   Run the backend manually to see the error:")
                print(f"   cd {BACKEND_DIR}")
                print(f"   {sys.executable} -m uvicorn main:app --port 8000")
                sys.exit(1)
            
            # Wait for backend to respond
            if wait_for_backend(port=8000, timeout=15):
                print(" OK!")
            else:
                print(" TIMEOUT!")
                print("\n⚠ Backend started but is not responding on port 8000")
                print("   Check for errors in the backend terminal output above")
                # Don't exit - backend might just be slow, let user see the output
        
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
            print("\n  [URL] Frontend:    http://localhost:5173")
        if not args.frontend_only:
            print("  [API] Backend API: http://localhost:8000/docs")
            print("  [WS]  WebSocket:   ws://localhost:8000/ws/events")
        
        if dev_mode:
            print("\n  [DEV] Development Mode:")
            print("     - Backend auto-reloads on .py file changes")
            print("     - Frontend hot-reloads on .tsx/.ts/.css changes")
        
        print("\n  [STOP] Press Ctrl+C to stop all servers...")
        print("=" * 60)
        
        # Wait for processes
        while True:
            for name, p in processes:
                if p.poll() is not None:
                    print(f"\n[WARN] {name} process (PID {p.pid}) exited with code {p.returncode}")
                    # If one process dies, stop all
                    if p.returncode != 0:
                        raise KeyboardInterrupt()
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n[STOP] Shutting down...")
    finally:
        # Terminate all processes - use taskkill on Windows to kill process trees
        for name, p in processes:
            try:
                print(f"   Stopping {name} (PID {p.pid})...")
                if sys.platform == "win32":
                    # Use taskkill with /T to kill entire process tree
                    # /T = kill child processes, /F = force
                    subprocess.run(
                        ["taskkill", "/T", "/F", "/PID", str(p.pid)],
                        capture_output=True,
                        timeout=10
                    )
                else:
                    os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            except Exception as e:
                print(f"   Error terminating {name}: {e}")
        
        # Give processes a moment to terminate
        time.sleep(1)
        
        # Double-check processes are dead
        for name, p in processes:
            try:
                if p.poll() is None:
                    print(f"   Force killing {name}...")
                    p.kill()
                    p.wait(timeout=3)
            except Exception:
                pass
        
        print("\n[OK] All servers stopped.")


if __name__ == "__main__":
    main()
