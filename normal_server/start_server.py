#!/usr/bin/env python3
"""
Start the NormCode Deployment Server.

Usage:
    python start_server.py
    python start_server.py --port 9000
    python start_server.py --host 127.0.0.1 --port 8080
"""

import sys
import os
from pathlib import Path

# Add current directory (normal_server) to path
SERVER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SERVER_DIR))

# Set default data directories
os.environ.setdefault("NORMCODE_PLANS_DIR", str(SERVER_DIR / "data" / "plans"))
os.environ.setdefault("NORMCODE_RUNS_DIR", str(SERVER_DIR / "data" / "runs"))

# Import and run
from server import main

if __name__ == "__main__":
    main()

