#!/usr/bin/env python3
"""
NormCode Website Dev Server Launcher
Simple Python launcher for the development server
"""

import os
import sys
import subprocess
from pathlib import Path
import shutil

def find_npm():
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

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    print()
    print("=" * 50)
    print("   NormCode Website - Dev Mode")
    print("=" * 50)
    print()
    
    # Try to find npm
    npm_cmd = find_npm()
    
    if not npm_cmd:
        print("❌ Error: npm not found!")
        print()
        print("Node.js doesn't appear to be installed or is not in your PATH.")
        print()
        print("Please do ONE of the following:")
        print()
        print("  Option 1 (Recommended):")
        print("    • Download and install Node.js from: https://nodejs.org/")
        print("    • Restart your computer after installation")
        print("    • Run this launcher again")
        print()
        print("  Option 2 (Quick fix):")
        print("    • Open a NEW Command Prompt or PowerShell window")
        print("    • Navigate to the website folder")
        print("    • Run: npm run dev")
        print()
        print("  Option 3 (Use different launcher):")
        print("    • Double-click: launch_dev.bat")
        print("    • Or: launch_dev_gui_silent.vbs")
        print()
        input("Press Enter to exit...")
        sys.exit(1)
    
    print(f"Found npm at: {npm_cmd}")
    print()
    print("Starting development server...")
    print()
    
    # Change to the website directory
    os.chdir(script_dir)
    
    try:
        # Run npm dev server with the found npm command
        if npm_cmd.endswith('.cmd'):
            # On Windows, use shell=True for .cmd files
            subprocess.run(f'"{npm_cmd}" run dev', shell=True, check=True)
        else:
            subprocess.run([npm_cmd, "run", "dev"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error: Failed to start dev server (exit code: {e.returncode})")
        print()
        print("This might be because:")
        print("  • Dependencies are not installed (run: npm install)")
        print("  • Port 5173 is already in use")
        print("  • There's an error in the project configuration")
        print()
        input("Press Enter to exit...")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✓ Dev server stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()

