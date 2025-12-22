#!/usr/bin/env python
"""
Quick launcher for NormCode Streamlit App
Navigates to streamlit_app directory and launches the app
"""

import os
import sys
import subprocess

def main():
    # Get the directory where this script is located (project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(script_dir, "streamlit_app")
    
    # Check if streamlit_app directory exists
    if not os.path.exists(app_dir):
        print("❌ Error: streamlit_app directory not found!")
        print(f"   Expected at: {app_dir}")
        sys.exit(1)
    
    # Check if app.py exists
    app_path = os.path.join(app_dir, "app.py")
    if not os.path.exists(app_path):
        print("❌ Error: app.py not found in streamlit_app directory!")
        sys.exit(1)
    
    print("="*60)
    print("🧠 NormCode Orchestrator - Streamlit App Launcher")
    print("="*60)
    print()
    print(f"📁 App directory: {app_dir}")
    print()
    
    # Check if streamlit is installed
    try:
        import streamlit
        print("✅ Streamlit is installed")
    except ImportError:
        print("⚠️  Streamlit is not installed.")
        print("\nWould you like to install it?")
        response = input("Install streamlit? [y/N]: ").strip().lower()
        
        if response in ['y', 'yes']:
            print("\n🔧 Installing streamlit...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
                print("✅ Streamlit installed successfully!")
            except subprocess.CalledProcessError:
                print("❌ Failed to install streamlit.")
                print("\nPlease install manually:")
                print("  pip install streamlit")
                sys.exit(1)
        else:
            print("\nℹ️  Please install streamlit manually:")
            print("  pip install streamlit")
            sys.exit(1)
    
    # Launch streamlit
    print("\n🚀 Launching Streamlit app...")
    print("   The app will open in your browser at http://localhost:8501")
    print("   Press Ctrl+C to stop the server\n")
    print("-"*60)
    print()
    
    try:
        # Change to app directory and run streamlit
        os.chdir(app_dir)
        subprocess.run(["streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n\n👋 App stopped by user")
    except FileNotFoundError:
        print("\n❌ Error: streamlit command not found")
        print("   Try running directly:")
        print(f"     cd {app_dir}")
        print("     streamlit run app.py")
        sys.exit(1)

if __name__ == "__main__":
    main()

