#!/usr/bin/env python3
"""
NormCode Deployment Client

Minimal client to interact with the NormCode Deployment Server.

Usage:
    python client.py plans                     # List all plans
    python client.py plans <plan_id>           # Get plan details
    python client.py run <plan_id>             # Start a run
    python client.py status <run_id>           # Check run status
    python client.py result <run_id>           # Get run result
    python client.py watch <run_id>            # Watch run via WebSocket
"""

import sys
import io
import json
import argparse
import time
from typing import Optional, Dict, Any
from pathlib import Path

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

try:
    import websocket
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False


class NormCodeClient:
    """Client for interacting with NormCode Deployment Server."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api"
    
    # =========================================================================
    # Health & Info
    # =========================================================================
    
    def health(self) -> Dict[str, Any]:
        """Check server health."""
        resp = requests.get(f"{self.base_url}/health")
        resp.raise_for_status()
        return resp.json()
    
    def info(self) -> Dict[str, Any]:
        """Get server info."""
        resp = requests.get(f"{self.base_url}/info")
        resp.raise_for_status()
        return resp.json()
    
    # =========================================================================
    # Plans
    # =========================================================================
    
    def list_plans(self) -> list:
        """List all available plans."""
        resp = requests.get(f"{self.api_url}/plans")
        resp.raise_for_status()
        return resp.json()
    
    def get_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get details for a specific plan."""
        resp = requests.get(f"{self.api_url}/plans/{plan_id}")
        resp.raise_for_status()
        return resp.json()
    
    # =========================================================================
    # Runs
    # =========================================================================
    
    def start_run(
        self,
        plan_id: str,
        run_id: Optional[str] = None,
        llm_model: Optional[str] = None,
        max_cycles: Optional[int] = None,
        ground_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Start a new plan execution."""
        payload = {"plan_id": plan_id}
        if run_id:
            payload["run_id"] = run_id
        if llm_model:
            payload["llm_model"] = llm_model
        if max_cycles:
            payload["max_cycles"] = max_cycles
        if ground_inputs:
            payload["ground_inputs"] = ground_inputs
        
        resp = requests.post(f"{self.api_url}/runs", json=payload)
        resp.raise_for_status()
        return resp.json()
    
    def list_runs(self) -> list:
        """List all runs."""
        resp = requests.get(f"{self.api_url}/runs")
        resp.raise_for_status()
        return resp.json()
    
    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Get status of a specific run."""
        resp = requests.get(f"{self.api_url}/runs/{run_id}")
        resp.raise_for_status()
        return resp.json()
    
    def get_result(self, run_id: str) -> Dict[str, Any]:
        """Get the result of a completed run."""
        resp = requests.get(f"{self.api_url}/runs/{run_id}/result")
        resp.raise_for_status()
        return resp.json()
    
    def stop_run(self, run_id: str) -> Dict[str, Any]:
        """Stop a running execution."""
        resp = requests.post(f"{self.api_url}/runs/{run_id}/stop")
        resp.raise_for_status()
        return resp.json()
    
    # =========================================================================
    # Polling Helper
    # =========================================================================
    
    def wait_for_completion(
        self,
        run_id: str,
        poll_interval: float = 2.0,
        timeout: float = 300.0,
        callback=None
    ) -> Dict[str, Any]:
        """
        Poll until run completes or fails.
        
        Args:
            run_id: Run to wait for
            poll_interval: Seconds between polls
            timeout: Maximum seconds to wait
            callback: Optional function called with status on each poll
        
        Returns:
            Final run status
        """
        start_time = time.time()
        
        while True:
            status = self.get_run(run_id)
            
            if callback:
                callback(status)
            
            if status["status"] in ("completed", "failed", "stopped"):
                return status
            
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Run {run_id} did not complete within {timeout}s")
            
            time.sleep(poll_interval)
    
    # =========================================================================
    # WebSocket
    # =========================================================================
    
    def watch_run(self, run_id: str, on_event=None):
        """
        Watch a run via WebSocket.
        
        Args:
            run_id: Run to watch
            on_event: Callback for each event (receives dict)
        """
        if not HAS_WEBSOCKET:
            print("websocket-client not installed. Run: pip install websocket-client")
            return
        
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ws/runs/{run_id}"
        
        def on_message(ws, message):
            if message == "ping":
                ws.send("pong")
                return
            try:
                event = json.loads(message)
                if on_event:
                    on_event(event)
                else:
                    print(f"Event: {json.dumps(event, indent=2)}")
            except json.JSONDecodeError:
                print(f"Message: {message}")
        
        def on_error(ws, error):
            print(f"WebSocket error: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket closed: {close_status_code} {close_msg}")
        
        def on_open(ws):
            print(f"Connected to run {run_id}")
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        print(f"Watching run {run_id} at {ws_url}")
        print("Press Ctrl+C to stop")
        
        try:
            ws.run_forever()
        except KeyboardInterrupt:
            print("\nStopped watching")


# =============================================================================
# CLI
# =============================================================================

def print_json(data, indent=2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def cmd_health(client: NormCodeClient, args):
    """Health check command."""
    result = client.health()
    print_json(result)


def cmd_info(client: NormCodeClient, args):
    """Server info command."""
    result = client.info()
    print_json(result)


def cmd_plans(client: NormCodeClient, args):
    """List or get plans."""
    if args.plan_id:
        result = client.get_plan(args.plan_id)
    else:
        result = client.list_plans()
    print_json(result)


def cmd_run(client: NormCodeClient, args):
    """Start a run."""
    result = client.start_run(
        plan_id=args.plan_id,
        run_id=args.run_id,
        llm_model=args.llm,
        max_cycles=args.max_cycles
    )
    print_json(result)
    
    if args.wait:
        print("\nWaiting for completion...")
        
        def on_status(status):
            print(f"  Status: {status['status']}")
        
        try:
            final = client.wait_for_completion(
                result["run_id"],
                poll_interval=2.0,
                callback=on_status
            )
            print("\nFinal status:")
            print_json(final)
            
            if final["status"] == "completed":
                print("\nResult:")
                result = client.get_result(final["run_id"])
                print_json(result)
        except TimeoutError as e:
            print(f"\nTimeout: {e}")


def cmd_status(client: NormCodeClient, args):
    """Get run status."""
    result = client.get_run(args.run_id)
    print_json(result)


def cmd_result(client: NormCodeClient, args):
    """Get run result."""
    result = client.get_result(args.run_id)
    print_json(result)


def cmd_runs(client: NormCodeClient, args):
    """List all runs."""
    result = client.list_runs()
    print_json(result)


def cmd_stop(client: NormCodeClient, args):
    """Stop a run."""
    result = client.stop_run(args.run_id)
    print_json(result)


def cmd_watch(client: NormCodeClient, args):
    """Watch a run via WebSocket."""
    client.watch_run(args.run_id)


def main():
    parser = argparse.ArgumentParser(
        description="NormCode Deployment Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python client.py health                    # Check server health
  python client.py info                      # Get server info
  python client.py plans                     # List all plans
  python client.py plans b1fdfd5b            # Get plan details
  python client.py run b1fdfd5b              # Start a run
  python client.py run b1fdfd5b --wait       # Start and wait for completion
  python client.py run b1fdfd5b --llm demo   # Start with specific LLM
  python client.py runs                      # List all runs
  python client.py status <run_id>           # Check run status
  python client.py result <run_id>           # Get run result
  python client.py stop <run_id>             # Stop a run
  python client.py watch <run_id>            # Watch run via WebSocket
        """
    )
    
    parser.add_argument(
        "--server",
        type=str,
        default="http://localhost:8080",
        help="Server URL (default: http://localhost:8080)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # health
    subparsers.add_parser("health", help="Check server health")
    
    # info
    subparsers.add_parser("info", help="Get server info")
    
    # plans
    plans_parser = subparsers.add_parser("plans", help="List or get plans")
    plans_parser.add_argument("plan_id", nargs="?", help="Plan ID (optional)")
    
    # run
    run_parser = subparsers.add_parser("run", help="Start a run")
    run_parser.add_argument("plan_id", help="Plan ID to run")
    run_parser.add_argument("--run-id", help="Custom run ID")
    run_parser.add_argument("--llm", help="LLM model to use")
    run_parser.add_argument("--max-cycles", type=int, help="Maximum cycles")
    run_parser.add_argument("--wait", action="store_true", help="Wait for completion")
    
    # runs
    subparsers.add_parser("runs", help="List all runs")
    
    # status
    status_parser = subparsers.add_parser("status", help="Get run status")
    status_parser.add_argument("run_id", help="Run ID")
    
    # result
    result_parser = subparsers.add_parser("result", help="Get run result")
    result_parser.add_argument("run_id", help="Run ID")
    
    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop a run")
    stop_parser.add_argument("run_id", help="Run ID")
    
    # watch
    watch_parser = subparsers.add_parser("watch", help="Watch run via WebSocket")
    watch_parser.add_argument("run_id", help="Run ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    client = NormCodeClient(args.server)
    
    commands = {
        "health": cmd_health,
        "info": cmd_info,
        "plans": cmd_plans,
        "run": cmd_run,
        "runs": cmd_runs,
        "status": cmd_status,
        "result": cmd_result,
        "stop": cmd_stop,
        "watch": cmd_watch,
    }
    
    try:
        commands[args.command](client, args)
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to server at {args.server}", file=sys.stderr)
        print("Is the server running? Start it with: python deployment/server.py", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}", file=sys.stderr)
        if e.response is not None:
            try:
                print(f"  Detail: {e.response.json()}", file=sys.stderr)
            except Exception:
                print(f"  Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

