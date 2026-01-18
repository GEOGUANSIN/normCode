#!/usr/bin/env python3
"""
NormCode Deployment Client GUI

Minimal Tkinter GUI for interacting with the NormCode Deployment Server.

Usage:
    python client_gui.py
    python client_gui.py --server http://localhost:8080
"""

import sys
import io
import json
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional, Dict, Any, List
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

# Add parent directory to path for imports
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import the client class
try:
    from deployment.client import NormCodeClient
except ImportError:
    # Fallback for running from deployment directory
    from client import NormCodeClient


class NormCodeClientGUI:
    """Minimal GUI for NormCode Deployment Client."""
    
    def __init__(self, server_url: str = "http://localhost:8080"):
        self.server_url = server_url
        self.client: Optional[NormCodeClient] = None
        self.plans: Dict[str, Dict] = {}
        self.runs: Dict[str, Dict] = {}
        self.polling = False
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("NormCode Client")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        self.style.configure("Status.TLabel", font=("Segoe UI", 10))
        self.style.configure("Success.TLabel", foreground="green")
        self.style.configure("Error.TLabel", foreground="red")
        
        self._build_ui()
        self._connect_to_server()
    
    def _build_ui(self):
        """Build the main UI."""
        # Main container
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        # =====================================================================
        # Header / Connection
        # =====================================================================
        header_frame = ttk.Frame(main)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="NormCode Client", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Server URL
        self.server_var = tk.StringVar(value=self.server_url)
        ttk.Label(header_frame, text="Server:").pack(side=tk.LEFT, padx=(20, 5))
        self.server_entry = ttk.Entry(header_frame, textvariable=self.server_var, width=30)
        self.server_entry.pack(side=tk.LEFT)
        
        ttk.Button(header_frame, text="Connect", command=self._connect_to_server).pack(side=tk.LEFT, padx=5)
        
        # Status indicator
        self.status_var = tk.StringVar(value="Disconnected")
        self.status_label = ttk.Label(header_frame, textvariable=self.status_var, style="Status.TLabel")
        self.status_label.pack(side=tk.RIGHT)
        
        # =====================================================================
        # Main content - PanedWindow
        # =====================================================================
        paned = ttk.PanedWindow(main, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Plans
        left_panel = ttk.Frame(paned, padding=5)
        paned.add(left_panel, weight=1)
        
        ttk.Label(left_panel, text="Plans", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        
        # Plans list
        plans_frame = ttk.Frame(left_panel)
        plans_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.plans_tree = ttk.Treeview(plans_frame, columns=("name",), show="tree headings", height=8)
        self.plans_tree.heading("#0", text="ID")
        self.plans_tree.heading("name", text="Name")
        self.plans_tree.column("#0", width=100)
        self.plans_tree.column("name", width=150)
        self.plans_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        plans_scroll = ttk.Scrollbar(plans_frame, orient=tk.VERTICAL, command=self.plans_tree.yview)
        plans_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.plans_tree.configure(yscrollcommand=plans_scroll.set)
        
        # Run button
        run_frame = ttk.Frame(left_panel)
        run_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(run_frame, text="LLM:").pack(side=tk.LEFT)
        self.llm_var = tk.StringVar(value="qwen-plus")
        self.llm_combo = ttk.Combobox(run_frame, textvariable=self.llm_var, width=15,
                                       values=["qwen-plus", "qwen-turbo-latest", "demo", "gpt-4o"])
        self.llm_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(run_frame, text="▶ Run Selected", command=self._start_run).pack(side=tk.LEFT, padx=5)
        ttk.Button(run_frame, text="↻ Refresh", command=self._refresh_plans).pack(side=tk.RIGHT)
        
        # Right panel - Runs
        right_panel = ttk.Frame(paned, padding=5)
        paned.add(right_panel, weight=2)
        
        ttk.Label(right_panel, text="Runs", font=("Segoe UI", 11, "bold")).pack(anchor=tk.W)
        
        # Runs list
        runs_frame = ttk.Frame(right_panel)
        runs_frame.pack(fill=tk.X, pady=5)
        
        self.runs_tree = ttk.Treeview(runs_frame, columns=("plan", "status", "time"), show="headings", height=6)
        self.runs_tree.heading("plan", text="Plan")
        self.runs_tree.heading("status", text="Status")
        self.runs_tree.heading("time", text="Time")
        self.runs_tree.column("plan", width=120)
        self.runs_tree.column("status", width=80)
        self.runs_tree.column("time", width=150)
        self.runs_tree.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        runs_scroll = ttk.Scrollbar(runs_frame, orient=tk.VERTICAL, command=self.runs_tree.yview)
        runs_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.runs_tree.configure(yscrollcommand=runs_scroll.set)
        
        self.runs_tree.bind("<<TreeviewSelect>>", self._on_run_selected)
        
        # Run controls
        run_controls = ttk.Frame(right_panel)
        run_controls.pack(fill=tk.X, pady=5)
        
        ttk.Button(run_controls, text="Get Result", command=self._get_result).pack(side=tk.LEFT)
        ttk.Button(run_controls, text="Stop", command=self._stop_run).pack(side=tk.LEFT, padx=5)
        ttk.Button(run_controls, text="↻ Refresh", command=self._refresh_runs).pack(side=tk.RIGHT)
        
        # Result display
        ttk.Label(right_panel, text="Result / Details", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        self.result_text = scrolledtext.ScrolledText(right_panel, height=15, font=("Consolas", 9))
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # =====================================================================
        # Status bar
        # =====================================================================
        status_bar = ttk.Frame(main)
        status_bar.pack(fill=tk.X, pady=(10, 0))
        
        self.info_var = tk.StringVar(value="")
        ttk.Label(status_bar, textvariable=self.info_var, style="Status.TLabel").pack(side=tk.LEFT)
        
        ttk.Button(status_bar, text="Clear Log", command=self._clear_result).pack(side=tk.RIGHT)
    
    def _log(self, message: str):
        """Add message to result text."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.result_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.result_text.see(tk.END)
    
    def _clear_result(self):
        """Clear result text."""
        self.result_text.delete("1.0", tk.END)
    
    def _set_status(self, status: str, is_error: bool = False):
        """Update status indicator."""
        self.status_var.set(status)
        if is_error:
            self.status_label.configure(style="Error.TLabel")
        else:
            self.status_label.configure(style="Success.TLabel" if "Connected" in status else "Status.TLabel")
    
    def _connect_to_server(self):
        """Connect to the server."""
        self.server_url = self.server_var.get().strip()
        self._set_status("Connecting...")
        
        def connect():
            try:
                self.client = NormCodeClient(self.server_url)
                health = self.client.health()
                info = self.client.info()
                
                self.root.after(0, lambda: self._on_connected(info))
            except Exception as e:
                self.root.after(0, lambda: self._on_connect_error(str(e)))
        
        threading.Thread(target=connect, daemon=True).start()
    
    def _on_connected(self, info: Dict):
        """Handle successful connection."""
        self._set_status(f"Connected ({info.get('plans_count', 0)} plans)")
        self.info_var.set(f"Plans: {info.get('plans_dir', 'N/A')}")
        self._log(f"Connected to {self.server_url}")
        self._refresh_plans()
        self._refresh_runs()
    
    def _on_connect_error(self, error: str):
        """Handle connection error."""
        self._set_status("Disconnected", is_error=True)
        self._log(f"Connection failed: {error}")
        messagebox.showerror("Connection Error", f"Could not connect to server:\n{error}")
    
    def _refresh_plans(self):
        """Refresh plans list."""
        if not self.client:
            return
        
        def fetch():
            try:
                plans = self.client.list_plans()
                self.root.after(0, lambda: self._update_plans_list(plans))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Error fetching plans: {e}"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _update_plans_list(self, plans: List[Dict]):
        """Update the plans treeview."""
        self.plans_tree.delete(*self.plans_tree.get_children())
        self.plans = {}
        
        for plan in plans:
            plan_id = plan.get("id", "")
            name = plan.get("name", "Unknown")
            self.plans[plan_id] = plan
            self.plans_tree.insert("", tk.END, iid=plan_id, text=plan_id[:8], values=(name,))
        
        self._log(f"Loaded {len(plans)} plans")
    
    def _refresh_runs(self):
        """Refresh runs list."""
        if not self.client:
            return
        
        def fetch():
            try:
                runs = self.client.list_runs()
                self.root.after(0, lambda: self._update_runs_list(runs))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Error fetching runs: {e}"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _update_runs_list(self, runs: List[Dict]):
        """Update the runs treeview."""
        self.runs_tree.delete(*self.runs_tree.get_children())
        self.runs = {}
        
        for run in runs:
            run_id = run.get("run_id", "")
            plan_id = run.get("plan_id", "")
            status = run.get("status", "unknown")
            started = run.get("started_at", "")
            if started:
                try:
                    dt = datetime.fromisoformat(started)
                    started = dt.strftime("%H:%M:%S")
                except:
                    pass
            
            self.runs[run_id] = run
            
            # Get plan name
            plan_name = self.plans.get(plan_id, {}).get("name", plan_id[:8])
            
            self.runs_tree.insert("", 0, iid=run_id, values=(plan_name, status, started))
    
    def _start_run(self):
        """Start a new run for selected plan."""
        if not self.client:
            messagebox.showwarning("Not Connected", "Please connect to a server first.")
            return
        
        selection = self.plans_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a plan to run.")
            return
        
        plan_id = selection[0]
        llm = self.llm_var.get()
        
        self._log(f"Starting run for plan {plan_id} with LLM: {llm}")
        
        def start():
            try:
                result = self.client.start_run(plan_id, llm_model=llm)
                run_id = result.get("run_id", "")
                self.root.after(0, lambda: self._on_run_started(run_id))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Error starting run: {e}"))
        
        threading.Thread(target=start, daemon=True).start()
    
    def _on_run_started(self, run_id: str):
        """Handle run started."""
        self._log(f"Run started: {run_id}")
        self._refresh_runs()
        
        # Start polling for status
        self._poll_run_status(run_id)
    
    def _poll_run_status(self, run_id: str):
        """Poll run status until complete."""
        def poll():
            try:
                status = self.client.get_run(run_id)
                current_status = status.get("status", "unknown")
                
                self.root.after(0, lambda: self._update_run_status(run_id, current_status))
                
                if current_status in ("pending", "running"):
                    # Continue polling
                    self.root.after(2000, lambda: threading.Thread(target=poll, daemon=True).start())
                else:
                    self.root.after(0, lambda: self._on_run_complete(run_id, status))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Polling error: {e}"))
        
        threading.Thread(target=poll, daemon=True).start()
    
    def _update_run_status(self, run_id: str, status: str):
        """Update run status in tree."""
        try:
            values = self.runs_tree.item(run_id, "values")
            if values:
                self.runs_tree.item(run_id, values=(values[0], status, values[2]))
        except:
            pass
    
    def _on_run_complete(self, run_id: str, status: Dict):
        """Handle run completion."""
        final_status = status.get("status", "unknown")
        self._log(f"Run {run_id[:8]}... {final_status}")
        self._refresh_runs()
        
        if final_status == "completed":
            self._get_result_for_run(run_id)
    
    def _on_run_selected(self, event):
        """Handle run selection."""
        selection = self.runs_tree.selection()
        if selection:
            run_id = selection[0]
            run = self.runs.get(run_id, {})
            self._display_json(run)
    
    def _get_result(self):
        """Get result for selected run."""
        selection = self.runs_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a run.")
            return
        
        run_id = selection[0]
        self._get_result_for_run(run_id)
    
    def _get_result_for_run(self, run_id: str):
        """Fetch and display result for a run."""
        if not self.client:
            return
        
        def fetch():
            try:
                result = self.client.get_result(run_id)
                self.root.after(0, lambda: self._display_json(result))
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Error getting result: {e}"))
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def _display_json(self, data: Dict):
        """Display JSON data in result text."""
        self._clear_result()
        try:
            formatted = json.dumps(data, indent=2, ensure_ascii=False)
            self.result_text.insert("1.0", formatted)
        except Exception as e:
            self.result_text.insert("1.0", str(data))
    
    def _stop_run(self):
        """Stop selected run."""
        selection = self.runs_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a run to stop.")
            return
        
        run_id = selection[0]
        
        def stop():
            try:
                result = self.client.stop_run(run_id)
                self.root.after(0, lambda: self._log(f"Run stopped: {run_id[:8]}..."))
                self.root.after(0, self._refresh_runs)
            except Exception as e:
                self.root.after(0, lambda: self._log(f"Error stopping run: {e}"))
        
        threading.Thread(target=stop, daemon=True).start()
    
    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="NormCode Client GUI")
    parser.add_argument("--server", type=str, default="http://localhost:8080", help="Server URL")
    args = parser.parse_args()
    
    app = NormCodeClientGUI(args.server)
    app.run()


if __name__ == "__main__":
    main()

