#!/usr/bin/env python3
"""
NormCode Canvas - Root Launcher
================================

Convenience launcher to start the NormCode Canvas app from the project root.
Simply delegates to canvas_app/launch.py with all arguments passed through.

Usage:
    python launch_canvas.py           # Start in dev mode (default)
    python launch_canvas.py --prod    # Production mode (no auto-reload)
    python launch_canvas.py --install # Force reinstall all dependencies
    python launch_canvas.py --help    # Show all options
"""

import subprocess
import sys
from pathlib import Path

# Get paths
PROJECT_ROOT = Path(__file__).parent
CANVAS_APP_DIR = PROJECT_ROOT / "canvas_app"
LAUNCH_SCRIPT = CANVAS_APP_DIR / "launch.py"


def main():
    # Verify the launch script exists
    if not LAUNCH_SCRIPT.exists():
        print(f"❌ Error: Canvas app launch script not found at:")
        print(f"   {LAUNCH_SCRIPT}")
        print(f"\n   Make sure the canvas_app directory exists.")
        sys.exit(1)
    
    # Build command: python canvas_app/launch.py [args...]
    cmd = [sys.executable, str(LAUNCH_SCRIPT)] + sys.argv[1:]
    
    print("=" * 60)
    print("  NormCode Canvas - Starting from project root")
    print("=" * 60)
    print(f"  Project Root: {PROJECT_ROOT}")
    print(f"  Delegating to: {LAUNCH_SCRIPT}")
    print()
    
    # Run the canvas launcher
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error launching canvas app: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
