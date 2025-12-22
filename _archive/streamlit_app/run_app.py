#!/usr/bin/env python
"""
Quick launcher for NormCode Orchestrator Streamlit App
Checks dependencies and launches the app
"""

import sys
import subprocess
import os

def check_streamlit():
    """Check if streamlit is installed"""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def install_streamlit():
    """Offer to install streamlit"""
    print("⚠️  Streamlit is not installed.")
    print("\nThis app requires streamlit. Would you like to install it?")
    response = input("Install streamlit? [y/N]: ").strip().lower()
    
    if response in ['y', 'yes']:
        print("\n🔧 Installing streamlit...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
            print("✅ Streamlit installed successfully!")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install streamlit.")
            print("\nPlease install manually:")
            print("  pip install streamlit")
            return False
    else:
        print("\nℹ️  Please install streamlit manually:")
        print("  pip install streamlit")
        return False

def main():
    """Main launcher function"""
    print("="*60)
    print("🧠 NormCode Orchestrator - Streamlit App")
    print("="*60)
    print()
    
    # Check if streamlit is installed
    if not check_streamlit():
        if not install_streamlit():
            sys.exit(1)
    
    # Check if app.py exists (in the same directory as this script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(script_dir, "app.py")
    if not os.path.exists(app_path):
        print("❌ Error: app.py not found!")
        print(f"   Expected at: {app_path}")
        sys.exit(1)
    
    # Launch streamlit
    print("\n🚀 Launching Streamlit app...")
    print("   The app will open in your browser at http://localhost:8501")
    print("   Press Ctrl+C to stop the server\n")
    print("-"*60)
    print()
    
    try:
        subprocess.run(["streamlit", "run", app_path])
    except KeyboardInterrupt:
        print("\n\n👋 App stopped by user")
    except FileNotFoundError:
        print("\n❌ Error: streamlit command not found")
        print("   Try running directly: streamlit run app.py")
        sys.exit(1)

if __name__ == "__main__":
    main()

