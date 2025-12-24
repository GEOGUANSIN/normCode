#!/usr/bin/env python3
"""
Launch script for NormCode Coming Soon website
Simple static HTML site - no build process needed
"""

import os
import sys
import webbrowser
import http.server
import socketserver
from pathlib import Path

# Configuration
PORT = 8000
SCRIPT_DIR = Path(__file__).parent.absolute()
INDEX_FILE = SCRIPT_DIR / "index.html"


def print_banner():
    """Print a nice banner"""
    print("\n" + "="*60)
    print("  🚀 NormCode - Coming Soon Website")
    print("="*60 + "\n")


def open_browser_only():
    """Just open the HTML file in the default browser"""
    print("📂 Opening index.html in your default browser...")
    
    if not INDEX_FILE.exists():
        print("❌ Error: index.html not found!")
        return False
    
    try:
        webbrowser.open(f"file://{INDEX_FILE}")
        print("✅ Website opened successfully!")
        print("\n💡 Note: This opens the file directly.")
        print("   For a local server with live reload, use option 2.")
        return True
    except Exception as e:
        print(f"❌ Error opening browser: {e}")
        return False


def start_server():
    """Start a simple HTTP server"""
    print(f"🌐 Starting local server on http://localhost:{PORT}")
    print(f"📁 Serving files from: {SCRIPT_DIR}")
    
    os.chdir(SCRIPT_DIR)
    
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"\n✅ Server running at http://localhost:{PORT}")
            print("\n🌐 Opening in browser...")
            webbrowser.open(f"http://localhost:{PORT}")
            print("\n" + "="*60)
            print("  Server is running. Press Ctrl+C to stop.")
            print("="*60 + "\n")
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
        print("✅ Goodbye!")
    except OSError as e:
        if "address already in use" in str(e).lower():
            print(f"\n❌ Error: Port {PORT} is already in use!")
            print(f"💡 Try a different port or close the application using port {PORT}")
        else:
            print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def show_menu():
    """Display menu and get user choice"""
    print("Choose an option:")
    print("  1. Open HTML file directly (no server)")
    print("  2. Start local HTTP server (recommended)")
    print("  0. Exit")
    print()
    
    while True:
        choice = input("Enter your choice (1, 2, or 0): ").strip()
        if choice in ['0', '1', '2']:
            return choice
        print("❌ Invalid choice. Please enter 0, 1, or 2.")


def main():
    """Main function"""
    print_banner()
    
    # Check if running with arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['--direct', '-d']:
            open_browser_only()
            return
        elif arg in ['--server', '-s']:
            start_server()
            return
        elif arg in ['--help', '-h']:
            print("Usage:")
            print("  python launch_dev.py           # Interactive menu")
            print("  python launch_dev.py --direct  # Open file directly")
            print("  python launch_dev.py --server  # Start HTTP server")
            print("  python launch_dev.py --help    # Show this help")
            return
    
    # Interactive mode
    choice = show_menu()
    
    if choice == '0':
        print("👋 Goodbye!")
        return
    elif choice == '1':
        open_browser_only()
        input("\nPress Enter to exit...")
    elif choice == '2':
        start_server()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)

