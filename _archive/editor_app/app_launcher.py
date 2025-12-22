#!/usr/bin/env python3
"""
NormCode Editor - One-Click App Launcher

This script launches both the backend (FastAPI) and frontend (React+Vite) servers
for the NormCode Editor application.

Usage:
    python app_launcher.py
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path
import signal
import platform

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color=Colors.OKGREEN):
    """Print a colored message to the console."""
    print(f"{color}{message}{Colors.ENDC}")

def print_header(message):
    """Print a header message."""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f"  {message}", Colors.HEADER)
    print_colored(f"{'='*60}\n", Colors.HEADER)

def check_command_exists(command):
    """Check if a command exists in the system PATH."""
    try:
        # On Windows, we need shell=True to find .cmd and .bat files like npm.cmd
        subprocess.run(
            [command, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            shell=(platform.system() == "Windows")
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def setup_backend(backend_dir):
    """Set up the backend environment and install dependencies if needed."""
    print_header("Setting up Backend")
    
    venv_dir = backend_dir / "venv"
    requirements_file = backend_dir / "requirements.txt"
    
    # Check if Python is available
    if not check_command_exists("python"):
        print_colored("❌ Python not found. Please install Python 3.8+", Colors.FAIL)
        return False
    
    # Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        print_colored("📦 Creating virtual environment...", Colors.OKCYAN)
        subprocess.run(
            ["python", "-m", "venv", "venv"],
            cwd=backend_dir,
            check=True
        )
        print_colored("✓ Virtual environment created", Colors.OKGREEN)
    else:
        print_colored("✓ Virtual environment already exists", Colors.OKGREEN)
    
    # Determine the pip executable path
    if platform.system() == "Windows":
        pip_executable = venv_dir / "Scripts" / "pip.exe"
        python_executable = venv_dir / "Scripts" / "python.exe"
    else:
        pip_executable = venv_dir / "bin" / "pip"
        python_executable = venv_dir / "bin" / "python"
    
    # Install/update dependencies
    if requirements_file.exists():
        print_colored("📦 Checking/installing backend dependencies...", Colors.OKCYAN)
        subprocess.run(
            [str(pip_executable), "install", "--upgrade", "-r", "requirements.txt"],
            cwd=backend_dir,
            check=True
        )
        print_colored("✓ Backend dependencies up to date", Colors.OKGREEN)
    else:
        print_colored("⚠ requirements.txt not found", Colors.WARNING)
    
    return True

def setup_frontend(frontend_dir):
    """Set up the frontend environment and install dependencies if needed."""
    print_header("Setting up Frontend")
    
    node_modules_dir = frontend_dir / "node_modules"
    package_json = frontend_dir / "package.json"
    
    # Check if Node.js and npm are available
    if not check_command_exists("node"):
        print_colored("❌ Node.js not found. Please install Node.js 18+", Colors.FAIL)
        return False
    
    if not check_command_exists("npm"):
        print_colored("❌ npm not found. Please install npm", Colors.FAIL)
        return False
    
    # Install dependencies if node_modules doesn't exist
    if not node_modules_dir.exists():
        print_colored("📦 Installing frontend dependencies...", Colors.OKCYAN)
        subprocess.run(
            ["npm", "install"],
            cwd=frontend_dir,
            check=True,
            shell=True
        )
        print_colored("✓ Frontend dependencies installed", Colors.OKGREEN)
    else:
        print_colored("✓ Frontend dependencies already installed", Colors.OKGREEN)
    
    return True

def start_backend(backend_dir):
    """Start the backend server."""
    print_header("Starting Backend Server")
    
    if platform.system() == "Windows":
        python_executable = backend_dir / "venv" / "Scripts" / "python.exe"
    else:
        python_executable = backend_dir / "venv" / "bin" / "python"
    
    # Start uvicorn server in dev mode with --reload
    # No stdout/stderr capture - let it display in terminal
    backend_process = subprocess.Popen(
        [str(python_executable), "-m", "uvicorn", "main:app", "--reload", "--port", "8001"],
        cwd=backend_dir
    )
    
    print_colored("✓ Backend server starting on http://127.0.0.1:8001 (dev mode with --reload)", Colors.OKGREEN)
    return backend_process

def start_frontend(frontend_dir):
    """Start the frontend development server."""
    print_header("Starting Frontend Server")
    
    # Start Vite dev server in dev mode with HMR
    # No stdout/stderr capture - let it display in terminal
    frontend_process = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True
    )
    
    print_colored("✓ Frontend server starting on http://localhost:5173 (dev mode with HMR)", Colors.OKGREEN)
    return frontend_process

def wait_for_server(url, timeout=30):
    """Wait for a server to become available."""
    import urllib.request
    import urllib.error
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Try to open the URL - even a 404 means the server is up
            urllib.request.urlopen(url, timeout=1)
            return True
        except urllib.error.HTTPError:
            # Server is responding (even with an error), so it's ready
            return True
        except (urllib.error.URLError, ConnectionRefusedError, OSError):
            # Server not ready yet
            time.sleep(0.5)
        except Exception:
            # Any other error, wait a bit
            time.sleep(0.5)
    return False

def main():
    """Main function to launch the application."""
    print_colored("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║        NormCode Editor - One-Click Launcher              ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """, Colors.HEADER)
    
    # Get the script directory
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir / "backend"
    frontend_dir = script_dir / "frontend"
    
    # Validate directories exist
    if not backend_dir.exists():
        print_colored(f"❌ Backend directory not found: {backend_dir}", Colors.FAIL)
        sys.exit(1)
    
    if not frontend_dir.exists():
        print_colored(f"❌ Frontend directory not found: {frontend_dir}", Colors.FAIL)
        sys.exit(1)
    
    # Setup
    if not setup_backend(backend_dir):
        print_colored("❌ Backend setup failed", Colors.FAIL)
        sys.exit(1)
    
    if not setup_frontend(frontend_dir):
        print_colored("❌ Frontend setup failed", Colors.FAIL)
        sys.exit(1)
    
    # Start servers
    backend_process = None
    frontend_process = None
    
    try:
        backend_process = start_backend(backend_dir)
        
        # Wait for backend to be ready
        print_colored("⏳ Waiting for backend to be ready...", Colors.OKCYAN)
        if wait_for_server("http://127.0.0.1:8001", timeout=30):
            print_colored("✓ Backend is ready!", Colors.OKGREEN)
        else:
            print_colored("⚠ Backend may not be ready, but continuing...", Colors.WARNING)
        
        frontend_process = start_frontend(frontend_dir)
        time.sleep(4)  # Give frontend time to start
        
        # Print status
        print_header("Application Running")
        print_colored("🚀 Backend API:  http://127.0.0.1:8001", Colors.OKGREEN)
        print_colored("🚀 Frontend App: http://localhost:5173", Colors.OKGREEN)
        print_colored("📚 API Docs:     http://127.0.0.1:8001/docs", Colors.OKGREEN)
        print_colored("\n💡 Press Ctrl+C to stop all servers", Colors.WARNING)
        
        # Wait a bit then open browser
        time.sleep(2)
        print_colored("\n🌐 Opening browser...", Colors.OKCYAN)
        webbrowser.open("http://localhost:5173")
        
        print_colored("\n" + "="*60, Colors.HEADER)
        print_colored("📊 Dev Mode Active - Server logs will appear below", Colors.HEADER)
        print_colored("🔄 Backend: Auto-reloads on Python file changes", Colors.HEADER)
        print_colored("⚡ Frontend: Hot Module Replacement (HMR) active", Colors.HEADER)
        print_colored("\n💡 If you see connection errors, do a HARD REFRESH:", Colors.WARNING)
        print_colored("   Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)", Colors.WARNING)
        print_colored("="*60 + "\n", Colors.HEADER)
        
        # Wait for processes to complete or user interrupt
        while True:
            # Check if processes are still running
            if backend_process.poll() is not None:
                print_colored("\n⚠ Backend process stopped unexpectedly", Colors.WARNING)
                break
            if frontend_process.poll() is not None:
                print_colored("\n⚠ Frontend process stopped unexpectedly", Colors.WARNING)
                break
            time.sleep(1)
    
    except KeyboardInterrupt:
        print_colored("\n\n🛑 Shutting down servers...", Colors.WARNING)
    
    finally:
        # Cleanup
        if backend_process:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
            print_colored("✓ Backend server stopped", Colors.OKGREEN)
        
        if frontend_process:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
            print_colored("✓ Frontend server stopped", Colors.OKGREEN)
        
        print_colored("\n👋 Goodbye!\n", Colors.OKCYAN)

if __name__ == "__main__":
    main()

