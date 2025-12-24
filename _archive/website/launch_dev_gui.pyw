#!/usr/bin/env python3
"""
NormCode Website Dev Server - GUI Launcher
Provides a simple GUI to launch and monitor the dev server
"""

import tkinter as tk
from tkinter import scrolledtext
import subprocess
import threading
import os
import sys
from pathlib import Path
import queue
import shutil

class DevServerLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("NormCode Website - Dev Server Launcher")
        self.root.geometry("700x500")
        self.root.resizable(True, True)
        
        # Server process
        self.process = None
        self.running = False
        
        # Queue for thread-safe output
        self.output_queue = queue.Queue()
        
        # Get script directory
        if getattr(sys, 'frozen', False):
            self.script_dir = Path(sys.executable).parent
        else:
            self.script_dir = Path(__file__).parent.absolute()
        
        # Find npm command
        self.npm_cmd = self.find_npm()
        
        self.setup_ui()
        self.check_output_queue()
    
    def find_npm(self):
        """Try to find npm in various common locations"""
        # First, try to find it in PATH
        npm_path = shutil.which("npm")
        if npm_path:
            return npm_path
        
        # Common Node.js installation paths on Windows
        common_paths = [
            r"C:\Program Files\nodejs\npm.cmd",
            r"C:\Program Files (x86)\nodejs\npm.cmd",
            os.path.expanduser(r"~\AppData\Roaming\npm\npm.cmd"),
            os.path.expanduser(r"~\AppData\Local\Programs\nodejs\npm.cmd"),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
        
    def setup_ui(self):
        # Header Frame
        header_frame = tk.Frame(self.root, bg="#4f46e5", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="NormCode Website",
            font=("Arial", 20, "bold"),
            bg="#4f46e5",
            fg="white"
        )
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(
            header_frame,
            text="Development Server Launcher",
            font=("Arial", 12),
            bg="#4f46e5",
            fg="white"
        )
        subtitle_label.pack()
        
        # Control Frame
        control_frame = tk.Frame(self.root, padx=10, pady=10)
        control_frame.pack(fill=tk.X)
        
        # Status
        self.status_label = tk.Label(
            control_frame,
            text="● Server Status: Stopped",
            font=("Arial", 11, "bold"),
            fg="red"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Buttons
        button_frame = tk.Frame(control_frame)
        button_frame.pack(side=tk.RIGHT)
        
        self.start_btn = tk.Button(
            button_frame,
            text="▶ Start Server",
            command=self.start_server,
            bg="#10b981",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5,
            cursor="hand2"
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(
            button_frame,
            text="■ Stop Server",
            command=self.stop_server,
            bg="#ef4444",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5,
            state=tk.DISABLED,
            cursor="hand2"
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(
            button_frame,
            text="Clear Log",
            command=self.clear_log,
            bg="#6b7280",
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5,
            cursor="hand2"
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Output Frame
        output_frame = tk.Frame(self.root, padx=10, pady=5)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        output_label = tk.Label(
            output_frame,
            text="Server Output:",
            font=("Arial", 10, "bold"),
            anchor=tk.W
        )
        output_label.pack(fill=tk.X)
        
        # Output Text
        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Footer
        footer_frame = tk.Frame(self.root, bg="#f3f4f6", height=30)
        footer_frame.pack(fill=tk.X)
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(
            footer_frame,
            text=f"Working Directory: {self.script_dir}",
            font=("Arial", 8),
            bg="#f3f4f6",
            fg="#6b7280",
            anchor=tk.W
        )
        footer_label.pack(side=tk.LEFT, padx=10)
        
        # Initial message
        if self.npm_cmd:
            self.log(f"✓ Found npm at: {self.npm_cmd}")
            self.log("Ready to start the development server.")
            self.log(f"Press '▶ Start Server' to launch.")
        else:
            self.log("❌ Warning: npm not found in PATH or common locations!", "#ef4444")
            self.log("")
            self.log("Please install Node.js from: https://nodejs.org/", "#fbbf24")
            self.log("Or open a regular Command Prompt (not from conda) and run the batch launcher.", "#fbbf24")
            self.log("")
            self.log("Tip: Try using 'launch_dev.bat' instead - it uses system PATH.", "#10b981")
    
    def log(self, message, color="#d4d4d4"):
        """Thread-safe logging"""
        self.output_queue.put(("log", message, color))
    
    def check_output_queue(self):
        """Check for messages from threads"""
        try:
            while True:
                action, *args = self.output_queue.get_nowait()
                if action == "log":
                    message, color = args
                    self.output_text.insert(tk.END, message + "\n")
                    self.output_text.see(tk.END)
                    self.output_text.update()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_output_queue)
    
    def start_server(self):
        if self.running:
            return
        
        if not self.npm_cmd:
            self.log("\n❌ Cannot start server: npm not found!", "#ef4444")
            self.log("Please install Node.js or use launch_dev.bat instead.", "#fbbf24")
            return
        
        self.log("\n" + "=" * 60)
        self.log("Starting development server...", "#10b981")
        self.log("=" * 60)
        
        self.running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="● Server Status: Running", fg="#10b981")
        
        # Start server in a separate thread
        thread = threading.Thread(target=self.run_server, daemon=True)
        thread.start()
    
    def run_server(self):
        try:
            os.chdir(self.script_dir)
            
            # Prepare the command
            if self.npm_cmd.endswith('.cmd'):
                # On Windows, .cmd files need shell=True
                cmd = f'"{self.npm_cmd}" run dev'
                use_shell = True
            else:
                cmd = [self.npm_cmd, "run", "dev"]
                use_shell = False
            
            # Start the process
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=self.script_dir,
                shell=use_shell
            )
            
            # Read output line by line
            for line in iter(self.process.stdout.readline, ''):
                if not self.running:
                    break
                self.log(line.rstrip())
            
            self.process.wait()
            
            if self.running:
                self.log("\n" + "=" * 60)
                self.log("Server stopped.", "#ef4444")
                self.log("=" * 60)
                self.output_queue.put(("reset",))
            
        except FileNotFoundError:
            self.log("\n❌ Error: npm not found. Please ensure Node.js is installed.", "#ef4444")
            self.output_queue.put(("reset",))
        except Exception as e:
            self.log(f"\n❌ Error: {str(e)}", "#ef4444")
            self.output_queue.put(("reset",))
        finally:
            if self.running:
                self.running = False
                self.root.after(0, self.reset_buttons)
    
    def stop_server(self):
        if not self.running:
            return
        
        self.log("\nStopping server...", "#ef4444")
        self.running = False
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        self.reset_buttons()
    
    def reset_buttons(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="● Server Status: Stopped", fg="red")
    
    def clear_log(self):
        self.output_text.delete(1.0, tk.END)
        self.log("Log cleared.")
    
    def on_closing(self):
        if self.running:
            self.stop_server()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = DevServerLauncher(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()

