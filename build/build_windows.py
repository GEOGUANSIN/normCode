#!/usr/bin/env python3
"""
NormCode Canvas - Windows Build Script
=======================================

This script automates the build process for creating a Windows executable:
1. Builds the frontend (npm run build)
2. Packages everything with PyInstaller
3. Optionally creates an installer with Inno Setup

Usage:
    python build_windows.py              # Full build
    python build_windows.py --skip-frontend  # Skip frontend build
    python build_windows.py --installer  # Also create installer
    python build_windows.py --clean      # Clean build artifacts first
"""

import subprocess
import sys
import shutil
import argparse
from pathlib import Path

# Paths
BUILD_DIR = Path(__file__).parent
PROJECT_ROOT = BUILD_DIR.parent
CANVAS_APP = PROJECT_ROOT / "canvas_app"
FRONTEND_DIR = CANVAS_APP / "frontend"
BACKEND_DIR = CANVAS_APP / "backend"
DIST_DIR = BUILD_DIR / "dist"
WORK_DIR = BUILD_DIR / "build"


def print_header(text: str):
    """Print a formatted header."""
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(text: str):
    """Print a step message."""
    print(f"\n→ {text}")


def run_command(cmd: list, cwd: Path = None, check: bool = True) -> bool:
    """Run a command and return success status."""
    print(f"  Running: {' '.join(str(c) for c in cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            shell=sys.platform == "win32"  # Use shell on Windows for npm
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Command failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        return False


def clean_build():
    """Clean build artifacts."""
    print_step("Cleaning build artifacts...")
    
    dirs_to_clean = [
        DIST_DIR,
        WORK_DIR,
        FRONTEND_DIR / "dist",
    ]
    
    for d in dirs_to_clean:
        if d.exists():
            print(f"  Removing {d}")
            shutil.rmtree(d)
    
    print("  [OK] Clean complete")


def check_requirements():
    """Check if required tools are installed."""
    print_step("Checking requirements...")
    
    errors = []
    
    # Check Python
    print(f"  Python: {sys.version.split()[0]}")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"  PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        errors.append("PyInstaller not installed. Run: pip install pyinstaller")
    
    # Check Node.js / npm
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    if shutil.which(npm_cmd):
        result = subprocess.run([npm_cmd, "--version"], capture_output=True, text=True)
        print(f"  npm: {result.stdout.strip()}")
    else:
        errors.append("npm not found. Install Node.js from https://nodejs.org/")
    
    if errors:
        print("\n[ERROR] Missing requirements:")
        for e in errors:
            print(f"   - {e}")
        return False
    
    print("  [OK] All requirements met")
    return True


def build_frontend():
    """Build the frontend using npm."""
    print_step("Building frontend...")
    
    # Check if package.json exists
    if not (FRONTEND_DIR / "package.json").exists():
        print(f"  [ERROR] package.json not found in {FRONTEND_DIR}")
        return False
    
    # Install dependencies if needed
    if not (FRONTEND_DIR / "node_modules").exists():
        print("  Installing npm dependencies...")
        npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
        if not run_command([npm_cmd, "install"], cwd=FRONTEND_DIR):
            return False
    
    # Build
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    if not run_command([npm_cmd, "run", "build"], cwd=FRONTEND_DIR):
        return False
    
    # Verify dist was created
    dist_path = FRONTEND_DIR / "dist"
    if not dist_path.exists() or not (dist_path / "index.html").exists():
        print(f"  [ERROR] Frontend build failed - dist/index.html not found")
        return False
    
    print("  [OK] Frontend build complete")
    return True


def build_exe():
    """Build the executable using PyInstaller."""
    print_step("Building executable with PyInstaller...")
    
    spec_file = BUILD_DIR / "normcode.spec"
    if not spec_file.exists():
        print(f"  [ERROR] Spec file not found: {spec_file}")
        return False
    
    # Run PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--distpath", str(DIST_DIR),
        "--workpath", str(WORK_DIR),
        str(spec_file)
    ]
    
    if not run_command(cmd, cwd=BUILD_DIR):
        return False
    
    # Verify output
    exe_path = DIST_DIR / "NormCodeCanvas" / "NormCodeCanvas.exe"
    if not exe_path.exists():
        print(f"  [ERROR] Build failed - executable not found at {exe_path}")
        return False
    
    print(f"  [OK] Executable created: {exe_path}")
    return True


def create_installer():
    """Create installer using Inno Setup."""
    print_step("Creating installer with Inno Setup...")
    
    iss_file = BUILD_DIR / "installer.iss"
    if not iss_file.exists():
        print(f"  [ERROR] Inno Setup script not found: {iss_file}")
        return False
    
    # Find Inno Setup compiler
    iscc_paths = [
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files (x86)/Inno Setup 5/ISCC.exe"),
    ]
    
    iscc = None
    for p in iscc_paths:
        if p.exists():
            iscc = p
            break
    
    if not iscc:
        print("  [WARN] Inno Setup not found. Skipping installer creation.")
        print("    Download from: https://jrsoftware.org/isdl.php")
        return True  # Not a fatal error
    
    # Run Inno Setup
    if not run_command([str(iscc), str(iss_file)], cwd=BUILD_DIR):
        return False
    
    # Check output
    output_dir = BUILD_DIR / "output"
    installers = list(output_dir.glob("*.exe"))
    if installers:
        print(f"  [OK] Installer created: {installers[0]}")
    
    return True


def copy_settings_example():
    """Copy settings.yaml.example to dist if needed."""
    print_step("Copying configuration files...")
    
    src = CANVAS_APP / "settings.yaml.example"
    dst = DIST_DIR / "NormCodeCanvas" / "settings.yaml.example"
    
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)
        print(f"  [OK] Copied settings.yaml.example")
    
    return True


def create_portable_zip():
    """Create a portable zip distribution."""
    print_step("Creating portable ZIP...")
    
    dist_folder = DIST_DIR / "NormCodeCanvas"
    if not dist_folder.exists():
        print("  [ERROR] Distribution folder not found")
        return False
    
    zip_name = DIST_DIR / "NormCodeCanvas-Portable"
    shutil.make_archive(str(zip_name), 'zip', DIST_DIR, "NormCodeCanvas")
    
    print(f"  [OK] Created: {zip_name}.zip")
    return True


def main():
    parser = argparse.ArgumentParser(description="Build NormCode Canvas for Windows")
    parser.add_argument("--skip-frontend", action="store_true", 
                        help="Skip frontend build (use existing dist)")
    parser.add_argument("--installer", action="store_true",
                        help="Create installer with Inno Setup")
    parser.add_argument("--clean", action="store_true",
                        help="Clean build artifacts before building")
    parser.add_argument("--portable", action="store_true",
                        help="Create portable ZIP distribution")
    args = parser.parse_args()
    
    print_header("NormCode Canvas - Windows Build")
    print(f"  Project Root: {PROJECT_ROOT}")
    print(f"  Build Dir: {BUILD_DIR}")
    
    # Clean if requested
    if args.clean:
        clean_build()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Build frontend
    if not args.skip_frontend:
        if not build_frontend():
            print("\n[ERROR] Frontend build failed")
            sys.exit(1)
    else:
        print_step("Skipping frontend build (--skip-frontend)")
        if not (FRONTEND_DIR / "dist" / "index.html").exists():
            print("  [WARN] Warning: Frontend dist not found. Build may fail.")
    
    # Build executable
    if not build_exe():
        print("\n[ERROR] Executable build failed")
        sys.exit(1)
    
    # Copy additional files
    copy_settings_example()
    
    # Create installer if requested
    if args.installer:
        create_installer()
    
    # Create portable zip if requested
    if args.portable:
        create_portable_zip()
    
    print_header("Build Complete!")
    print(f"\n  Output: {DIST_DIR / 'NormCodeCanvas'}")
    print(f"  Executable: {DIST_DIR / 'NormCodeCanvas' / 'NormCodeCanvas.exe'}")
    
    if args.portable:
        print(f"  Portable ZIP: {DIST_DIR / 'NormCodeCanvas-Portable.zip'}")


if __name__ == "__main__":
    main()

