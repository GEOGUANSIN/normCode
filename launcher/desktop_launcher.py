"""
NormCode Canvas - Windows Desktop Launcher
===========================================

A Windows GUI launcher that:
- Starts the FastAPI backend server
- Serves pre-built frontend static files
- Shows a small window with the access URL
- Provides one-click browser opening

This is the entry point for PyInstaller packaging.
"""

import sys
import os
import threading
import webbrowser
import socket
import time
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Explicit imports for PyInstaller to detect
# These are imported at top-level so PyInstaller's static analysis finds them
import uvicorn
import uvicorn.config
import uvicorn.main
import uvicorn.lifespan
import uvicorn.lifespan.on
import fastapi
import starlette
import starlette.staticfiles
import starlette.responses
import pydantic
import pydantic_settings
import websockets
import anyio
import yaml

# Detect if running as frozen executable (PyInstaller)
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BUNDLE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(sys.executable).parent
    IS_FROZEN = True
else:
    # Running as script
    BUNDLE_DIR = Path(__file__).parent.parent
    APP_DIR = BUNDLE_DIR
    IS_FROZEN = False

# Paths
BACKEND_DIR = BUNDLE_DIR / "canvas_app" / "backend" if not IS_FROZEN else BUNDLE_DIR / "backend"
FRONTEND_DIST = BUNDLE_DIR / "canvas_app" / "frontend" / "dist" if not IS_FROZEN else BUNDLE_DIR / "frontend" / "dist"
PROJECT_ROOT = BUNDLE_DIR if not IS_FROZEN else APP_DIR

# Add paths for imports
if not IS_FROZEN:
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(BACKEND_DIR))


def find_free_port(start_port: int = 8000, max_tries: int = 100) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find a free port in range {start_port}-{start_port + max_tries}")


def check_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('127.0.0.1', port))
            return result == 0
    except Exception:
        return False


class NormCodeLauncher:
    """Main launcher application."""
    
    def __init__(self):
        self.port = 8000
        self.url = f"http://localhost:{self.port}"
        self.server_thread = None
        self.server = None
        self.running = False
        self.root = None
        self.status_label = None
        self.url_label = None
        self.open_button = None
        
    def find_available_port(self):
        """Find an available port for the server."""
        if check_port_in_use(self.port):
            self.port = find_free_port(8001)
        self.url = f"http://localhost:{self.port}"
        
    def start_server(self):
        """Start the FastAPI backend server."""
        try:
            import uvicorn
            
            # Setup paths for backend imports
            if IS_FROZEN:
                # In frozen mode, backend is in BUNDLE_DIR/backend
                backend_dir = BUNDLE_DIR / "backend"
                sys.path.insert(0, str(backend_dir))
                sys.path.insert(0, str(BUNDLE_DIR))
                
                # Change working directory to app directory for relative paths
                os.chdir(APP_DIR)
                print(f"  Working Directory: {os.getcwd()}")
                print(f"  Backend Dir: {backend_dir}")
            
            # Import the app
            from main import app
            
            # Configure uvicorn
            config = uvicorn.Config(
                app, 
                host="127.0.0.1", 
                port=self.port, 
                log_level="info",  # More verbose for debugging
                access_log=False
            )
            self.server = uvicorn.Server(config)
            self.running = True
            
            # Update UI
            if self.root:
                self.root.after(0, self._update_status_running)
            
            # Run server (blocking)
            self.server.run()
            
        except Exception as e:
            self.running = False
            import traceback
            error_details = traceback.format_exc()
            error_msg = f"Failed to start server: {e}"
            print(error_msg)
            print(error_details)
            if self.root:
                self.root.after(0, lambda: self._show_error(f"{error_msg}\n\n详细信息请查看控制台输出"))
    
    def _update_status_running(self):
        """Update UI to show server is running."""
        if self.status_label:
            self.status_label.config(text="✅ 服务器运行中", foreground="#22c55e")
        if self.url_label:
            self.url_label.config(text=self.url)
        if self.open_button:
            self.open_button.config(state="normal")
    
    def _show_error(self, message: str):
        """Show error in UI."""
        if self.status_label:
            self.status_label.config(text="❌ 启动失败", foreground="#ef4444")
        messagebox.showerror("启动错误", message)
    
    def open_browser(self):
        """Open the default browser to the app URL."""
        webbrowser.open(self.url)
    
    def copy_url(self):
        """Copy URL to clipboard."""
        if self.root:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.url)
            # Show feedback
            if hasattr(self, 'copy_button'):
                original_text = self.copy_button.cget('text')
                self.copy_button.config(text="✓ 已复制")
                self.root.after(1500, lambda: self.copy_button.config(text=original_text))
    
    def create_window(self):
        """Create the main launcher window."""
        self.root = tk.Tk()
        self.root.title("NormCode Canvas")
        self.root.geometry("420x280")
        self.root.resizable(False, False)
        
        # Try to set icon
        try:
            icon_path = APP_DIR / "resources" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass
        
        # Configure style
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Status.TLabel", font=("Segoe UI", 11))
        style.configure("URL.TLabel", font=("Consolas", 12))
        style.configure("Action.TButton", font=("Segoe UI", 11), padding=10)
        
        # Main frame with padding
        main_frame = ttk.Frame(self.root, padding=25)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="✨ NormCode Canvas",
            style="Title.TLabel"
        )
        title_label.pack(pady=(0, 15))
        
        # Status
        self.status_label = ttk.Label(
            main_frame,
            text="⏳ 正在启动服务器...",
            style="Status.TLabel",
            foreground="#f59e0b"
        )
        self.status_label.pack(pady=5)
        
        # URL display
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(pady=15, fill=tk.X)
        
        ttk.Label(url_frame, text="访问地址：", style="Status.TLabel").pack(side=tk.LEFT)
        self.url_label = ttk.Label(
            url_frame,
            text="等待中...",
            style="URL.TLabel",
            foreground="#3b82f6"
        )
        self.url_label.pack(side=tk.LEFT, padx=5)
        
        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        # Open browser button
        self.open_button = ttk.Button(
            btn_frame,
            text="🌐 打开浏览器",
            command=self.open_browser,
            style="Action.TButton",
            state="disabled"
        )
        self.open_button.pack(side=tk.LEFT, padx=5)
        
        # Copy URL button
        self.copy_button = ttk.Button(
            btn_frame,
            text="📋 复制链接",
            command=self.copy_url,
            style="Action.TButton"
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)
        
        # Footer
        footer_label = ttk.Label(
            main_frame,
            text="关闭此窗口将停止服务器",
            font=("Segoe UI", 9),
            foreground="#6b7280"
        )
        footer_label.pack(side=tk.BOTTOM, pady=(20, 0))
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Center window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")
    
    def on_close(self):
        """Handle window close event."""
        if self.running and self.server:
            self.server.should_exit = True
        self.root.destroy()
        # Force exit after a short delay
        threading.Timer(1.0, lambda: os._exit(0)).start()
    
    def run(self):
        """Main entry point - start the launcher."""
        # Find available port
        self.find_available_port()
        
        # Create window first
        self.create_window()
        
        # Start server in background thread
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()
        
        # Wait a bit then try to auto-open browser
        def auto_open():
            time.sleep(2)
            if self.running:
                self.root.after(0, self.open_browser)
        
        threading.Thread(target=auto_open, daemon=True).start()
        
        # Run the GUI event loop
        self.root.mainloop()


def main():
    """Entry point for the launcher."""
    print("=" * 50)
    print("  NormCode Canvas Desktop Launcher")
    print("=" * 50)
    print(f"  Bundle Dir: {BUNDLE_DIR}")
    print(f"  App Dir: {APP_DIR}")
    print(f"  Frozen: {IS_FROZEN}")
    print()
    
    try:
        launcher = NormCodeLauncher()
        launcher.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()

