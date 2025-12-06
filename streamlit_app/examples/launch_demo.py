"""
Minimal launcher for the NormCode Inline Editor Demo
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Launch the Streamlit demo editor."""
    script_dir = Path(__file__).parent
    demo_path = script_dir / "demo_editor.py"
    
    if not demo_path.exists():
        print(f"Error: demo_editor.py not found at {demo_path}")
        sys.exit(1)
    
    print("🚀 Launching NormCode Inline Editor Demo...")
    print(f"📁 Working directory: {script_dir}")
    print("-" * 50)
    
    # Launch streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            str(demo_path),
            "--server.port", "8502",
            "--server.headless", "false"
        ], cwd=str(script_dir))
    except KeyboardInterrupt:
        print("\n\n👋 Demo editor closed.")
    except Exception as e:
        print(f"\n❌ Error launching demo: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

