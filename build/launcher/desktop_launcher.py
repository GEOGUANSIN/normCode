"""
NormCode Canvas - Windows Desktop Launcher
===========================================

A self-contained desktop application that:
- Starts the FastAPI backend server
- Serves pre-built frontend static files
- Opens the app in a native desktop window (no browser needed)

This is the entry point for PyInstaller packaging.
"""

__version__ = "1.0.2-alpha"

import sys
import os
import threading
import socket
import time
from pathlib import Path

# Explicit imports for PyInstaller to detect
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

# pywebview for native desktop window
import webview

# Detect if running as frozen executable (PyInstaller)
if getattr(sys, 'frozen', False):
    BUNDLE_DIR = Path(sys._MEIPASS)
    APP_DIR = Path(sys.executable).parent
    IS_FROZEN = True
else:
    BUNDLE_DIR = Path(__file__).parent.parent.parent
    APP_DIR = BUNDLE_DIR
    IS_FROZEN = False

# Paths
BACKEND_DIR = BUNDLE_DIR / "canvas_app" / "backend" if not IS_FROZEN else BUNDLE_DIR / "backend"
PROJECT_ROOT = BUNDLE_DIR if not IS_FROZEN else APP_DIR


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
            return s.connect_ex(('127.0.0.1', port)) == 0
    except Exception:
        return False


def wait_for_server(port: int, timeout: int = 30) -> bool:
    """Wait for the server to become available."""
    start = time.time()
    while time.time() - start < timeout:
        if check_port_in_use(port):
            return True
        time.sleep(0.1)
    return False


class NormCodeApp:
    """Main desktop application using native window."""
    
    def __init__(self):
        self.port = 49821  # Use high port to avoid conflicts with common services
        self.url = f"http://localhost:{self.port}"
        self.server_thread = None
        self.server = None
        self.window = None
        self.running = False
        self._server_ready = threading.Event()
        self._server_error = None
        
    def find_available_port(self):
        """Find an available port for the server."""
        if check_port_in_use(self.port):
            self.port = find_free_port(49822)  # Start searching from next port
        self.url = f"http://localhost:{self.port}"
        
    def start_server(self):
        """Start the FastAPI backend server."""
        try:
            import uvicorn
            
            if IS_FROZEN:
                backend_dir = BUNDLE_DIR / "backend"
                sys.path.insert(0, str(backend_dir))
                sys.path.insert(0, str(BUNDLE_DIR))
                os.chdir(APP_DIR)
            else:
                # Development mode
                sys.path.insert(0, str(PROJECT_ROOT))
                sys.path.insert(0, str(BACKEND_DIR))
            
            from main import app
            
            config = uvicorn.Config(
                app, 
                host="127.0.0.1", 
                port=self.port, 
                log_level="warning",
                access_log=False
            )
            self.server = uvicorn.Server(config)
            self.running = True
            self._server_ready.set()
            self.server.run()
            
        except Exception as e:
            self.running = False
            self._server_error = str(e)
            self._server_ready.set()
            import traceback
            traceback.print_exc()
    
    def on_window_closing(self):
        """Called when the window is closing."""
        self.running = False
        if self.server:
            self.server.should_exit = True
        return True  # Allow window to close
    
    def on_window_loaded(self):
        """Called when the webview content is loaded."""
        pass
    
    def run(self):
        """Main entry point - creates native desktop window."""
        self.find_available_port()
        
        # Start server in background thread
        self.server_thread = threading.Thread(target=self.start_server, daemon=True)
        self.server_thread.start()
        
        # Wait for server to be ready
        self._server_ready.wait(timeout=30)
        
        if self._server_error:
            # Show error dialog if server failed
            webview.create_window(
                'NormCode Canvas - Error',
                html=f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                            color: #e94560;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            margin: 0;
                        }}
                        .error-box {{
                            background: rgba(233, 69, 96, 0.1);
                            border: 1px solid #e94560;
                            border-radius: 12px;
                            padding: 40px;
                            max-width: 500px;
                            text-align: center;
                        }}
                        h1 {{ margin-bottom: 20px; }}
                        pre {{
                            background: rgba(0,0,0,0.3);
                            padding: 15px;
                            border-radius: 8px;
                            text-align: left;
                            overflow-x: auto;
                            font-size: 12px;
                            color: #fff;
                        }}
                    </style>
                </head>
                <body>
                    <div class="error-box">
                        <h1>⚠️ Startup Error</h1>
                        <p>Failed to start the application server:</p>
                        <pre>{self._server_error}</pre>
                    </div>
                </body>
                </html>
                ''',
                width=600,
                height=400
            )
            webview.start()
            return
        
        # Wait a bit more for server to fully initialize
        if not wait_for_server(self.port, timeout=10):
            self._server_error = "Server failed to respond within timeout"
        
        # Get icon path if available
        icon_path = None
        if IS_FROZEN:
            icon_file = BUNDLE_DIR / "resources" / "icon.ico"
            if icon_file.exists():
                icon_path = str(icon_file)
        else:
            icon_file = Path(__file__).parent.parent / "resources" / "icon.ico"
            if icon_file.exists():
                icon_path = str(icon_file)
        
        # Create native window
        self.window = webview.create_window(
            title='NormCode Canvas',
            url=self.url,
            width=1400,
            height=900,
            min_size=(800, 600),
            resizable=True,
            frameless=False,
            easy_drag=False,
            text_select=True,
            confirm_close=False,
            background_color='#0f0f23'
        )
        
        # Set window events
        self.window.events.closing += self.on_window_closing
        self.window.events.loaded += self.on_window_loaded
        
        # Start the webview - this blocks until window is closed
        webview.start(
            debug=not IS_FROZEN,
            private_mode=False,
            storage_path=str(APP_DIR / "webview_data") if IS_FROZEN else None,
            gui='edgechromium'  # Use Edge WebView2 on Windows for best compatibility
        )
        
        # Cleanup after window closes
        self.running = False
        if self.server:
            self.server.should_exit = True


def main():
    """Entry point for the launcher."""
    try:
        app = NormCodeApp()
        app.run()
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        
        # Try to show error in a window
        try:
            webview.create_window(
                'NormCode Canvas - Critical Error',
                html=f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            background: #1a1a2e;
                            color: #e94560;
                            padding: 40px;
                        }}
                        pre {{
                            background: #0f0f23;
                            padding: 20px;
                            border-radius: 8px;
                            overflow-x: auto;
                            font-size: 11px;
                            color: #fff;
                            white-space: pre-wrap;
                        }}
                    </style>
                </head>
                <body>
                    <h1>⚠️ Critical Error</h1>
                    <p>The application encountered a fatal error:</p>
                    <pre>{error_msg}</pre>
                </body>
                </html>
                ''',
                width=700,
                height=500
            )
            webview.start()
        except Exception:
            # Fallback to console
            print(f"Critical Error: {e}")
            traceback.print_exc()
            input("Press Enter to exit...")
        
        sys.exit(1)


if __name__ == "__main__":
    main()
