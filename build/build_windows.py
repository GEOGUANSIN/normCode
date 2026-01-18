#!/usr/bin/env python3
"""
NormCode Canvas - Windows Build Script
=======================================

This script automates the build process for creating a Windows desktop application.
It is fully self-contained and will install required dependencies automatically.

Steps:
1. Installs required Python packages (PyInstaller, pywebview, etc.)
2. Installs backend Python dependencies
3. Builds the frontend (npm run build)
4. Packages everything with PyInstaller
5. Optionally creates an installer with Inno Setup

Usage:
    python build_windows.py              # Full build (windowed mode)
    python build_windows.py --debug      # Build with console for debugging
    python build_windows.py --skip-frontend  # Skip frontend build
    python build_windows.py --installer  # Also create installer
    python build_windows.py --clean      # Clean build artifacts first
    python build_windows.py --portable   # Create portable ZIP
"""

import subprocess
import sys
import shutil
import argparse
import re
from pathlib import Path

# Paths
BUILD_DIR = Path(__file__).parent
PROJECT_ROOT = BUILD_DIR.parent
CANVAS_APP = PROJECT_ROOT / "canvas_app"
FRONTEND_DIR = CANVAS_APP / "frontend"
BACKEND_DIR = CANVAS_APP / "backend"
DIST_DIR = BUILD_DIR / "dist"
WORK_DIR = BUILD_DIR / "build"
RELEASE_DIR = BUILD_DIR / "release"

# Required Python packages for building
BUILD_REQUIREMENTS = [
    "pyinstaller",
    "pillow",           # For icon conversion if needed
    "pywebview[cef]",   # Native desktop window with CEF fallback
    "bottle",           # Used internally by pywebview
    "pythonnet",        # Windows .NET integration for pywebview EdgeChromium
    "clr-loader",       # .NET runtime loader for pythonnet
]

# Required icon sizes for Windows (all contexts: taskbar, explorer, etc.)
ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]


def print_header(text: str):
    """Print a formatted header."""
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(text: str):
    """Print a step message."""
    print(f"\n-> {text}")


def run_command(cmd: list, cwd: Path = None, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"  Running: {' '.join(str(c) for c in cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            shell=sys.platform == "win32",  # Use shell on Windows for npm
            capture_output=capture,
            text=capture
        )
        return result
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Command failed with exit code {e.returncode}")
        raise
    except Exception as e:
        print(f"  [ERROR] Error: {e}")
        raise


def run_command_safe(cmd: list, cwd: Path = None) -> bool:
    """Run a command and return success status (doesn't raise)."""
    try:
        result = run_command(cmd, cwd=cwd, check=False)
        return result.returncode == 0
    except Exception:
        return False


def pip_install(packages: list, quiet: bool = False) -> bool:
    """Install Python packages using pip."""
    cmd = [sys.executable, "-m", "pip", "install"]
    if quiet:
        cmd.append("-q")
    cmd.extend(packages)
    
    try:
        result = subprocess.run(cmd, capture_output=quiet, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"  [ERROR] pip install failed: {e}")
        return False


def check_package_installed(package_name: str) -> bool:
    """Check if a Python package is installed."""
    # Handle package names with extras like "pywebview[cef]"
    base_name = package_name.split("[")[0].replace("-", "_")
    try:
        __import__(base_name)
        return True
    except ImportError:
        # Special cases
        if base_name == "pywebview":
            try:
                __import__("webview")
                return True
            except ImportError:
                return False
        elif base_name == "clr_loader":
            try:
                __import__("clr_loader")
                return True
            except ImportError:
                return False
        return False


def install_build_requirements():
    """Install required Python packages for building."""
    print_step("Checking/Installing build requirements...")
    
    missing = []
    for pkg in BUILD_REQUIREMENTS:
        pkg_check = pkg.split("[")[0].replace("-", "_")
        if pkg_check == "pyinstaller":
            pkg_check = "PyInstaller"
        if not check_package_installed(pkg_check):
            missing.append(pkg)
    
    if missing:
        print(f"  Installing: {', '.join(missing)}")
        if not pip_install(missing):
            print("  [ERROR] Failed to install build requirements")
            return False
        print("  [OK] Build requirements installed")
    else:
        print("  [OK] All build requirements already installed")
    
    return True


def install_backend_requirements():
    """Install backend Python dependencies."""
    print_step("Checking/Installing backend requirements...")
    
    requirements_file = BACKEND_DIR / "requirements.txt"
    if not requirements_file.exists():
        print(f"  [WARN] requirements.txt not found at {requirements_file}")
        return True
    
    # Install from requirements.txt
    cmd = [sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements_file)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("  [OK] Backend requirements installed")
            return True
        else:
            print(f"  [ERROR] Failed to install backend requirements")
            print(f"  {result.stderr}")
            return False
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False


def kill_running_instances():
    """Kill any running NormCodeCanvas instances."""
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", "NormCodeCanvas.exe"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("  Killed running NormCodeCanvas instance")
                import time
                time.sleep(1)  # Wait for process to fully terminate
        except Exception:
            pass  # Process might not be running


def clean_build():
    """Clean build artifacts."""
    print_step("Cleaning build artifacts...")
    
    # Kill any running instances first
    kill_running_instances()
    
    dirs_to_clean = [
        DIST_DIR,
        WORK_DIR,
        FRONTEND_DIR / "dist",
    ]
    
    for d in dirs_to_clean:
        if d.exists():
            print(f"  Removing {d}")
            try:
                shutil.rmtree(d)
            except PermissionError as e:
                print(f"  [WARN] Could not remove {d}: {e}")
                print("  [WARN] Some files may be locked. Try closing any running instances.")
                # Try again after killing processes
                kill_running_instances()
                try:
                    shutil.rmtree(d)
                except Exception:
                    print(f"  [ERROR] Still cannot remove {d}. Please close all related programs.")
                    raise
    
    print("  [OK] Clean complete")


def check_requirements():
    """Check if required tools are available."""
    print_step("Checking system requirements...")
    
    errors = []
    warnings = []
    
    # Check Python version
    py_version = sys.version_info
    print(f"  Python: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version < (3, 8):
        errors.append("Python 3.8+ is required")
    
    # Check PyInstaller (should be installed by now)
    try:
        import PyInstaller
        print(f"  PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        errors.append("PyInstaller not available (installation may have failed)")
    
    # Check pywebview
    try:
        import webview
        # pywebview doesn't have __version__, check via pkg_resources or importlib
        try:
            from importlib.metadata import version
            wv_version = version("pywebview")
        except Exception:
            wv_version = "installed"
        print(f"  pywebview: {wv_version}")
    except ImportError:
        errors.append("pywebview not available (installation may have failed)")
    
    # Check pythonnet/clr
    try:
        import clr_loader
        print(f"  clr_loader: available")
    except ImportError:
        warnings.append("clr_loader not available - EdgeChromium may not work, will fallback to CEF")
    
    # Check Node.js / npm
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    npm_path = shutil.which(npm_cmd)
    if npm_path:
        try:
            result = subprocess.run([npm_cmd, "--version"], capture_output=True, text=True, shell=True)
            print(f"  npm: {result.stdout.strip()}")
        except Exception:
            errors.append("npm found but failed to get version")
    else:
        errors.append("npm not found. Install Node.js from https://nodejs.org/")
    
    if warnings:
        print("\n[WARN] Warnings:")
        for w in warnings:
            print(f"   - {w}")
    
    if errors:
        print("\n[ERROR] Missing requirements:")
        for e in errors:
            print(f"   - {e}")
        return False
    
    print("  [OK] All system requirements met")
    return True


def build_frontend():
    """Build the frontend using npm."""
    print_step("Building frontend...")
    
    # Check if package.json exists
    if not (FRONTEND_DIR / "package.json").exists():
        print(f"  [ERROR] package.json not found in {FRONTEND_DIR}")
        return False
    
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    
    # Install dependencies if needed
    if not (FRONTEND_DIR / "node_modules").exists():
        print("  Installing npm dependencies...")
        if not run_command_safe([npm_cmd, "install"], cwd=FRONTEND_DIR):
            print("  [ERROR] npm install failed")
            return False
    
    # Build
    if not run_command_safe([npm_cmd, "run", "build"], cwd=FRONTEND_DIR):
        print("  [ERROR] npm run build failed")
        return False
    
    # Verify dist was created
    dist_path = FRONTEND_DIR / "dist"
    if not dist_path.exists() or not (dist_path / "index.html").exists():
        print(f"  [ERROR] Frontend build failed - dist/index.html not found")
        return False
    
    print("  [OK] Frontend build complete")
    return True


def ensure_icon():
    """Ensure icon.ico exists with all required sizes."""
    print_step("Checking/Creating application icon...")
    
    resources_dir = BUILD_DIR / "resources"
    icon_path = resources_dir / "icon.ico"
    png_path = resources_dir / "Psylensai_log_raw.png"
    
    # Check if we need to regenerate the icon
    regenerate = False
    
    if not icon_path.exists():
        print("  icon.ico not found, will create from PNG")
        regenerate = True
    else:
        # Check if icon has all required sizes
        try:
            from PIL import Image
            img = Image.open(icon_path)
            # ICO files can have multiple sizes, check if we have enough
            sizes = []
            try:
                for i in range(20):  # Check up to 20 frames
                    img.seek(i)
                    sizes.append(img.size[0])
            except EOFError:
                pass
            
            missing = [s for s in ICON_SIZES if s not in sizes]
            if missing:
                print(f"  icon.ico missing sizes: {missing}")
                regenerate = True
            else:
                print(f"  [OK] icon.ico has all required sizes: {sorted(set(sizes))}")
        except Exception as e:
            print(f"  Could not verify icon: {e}")
            regenerate = True
    
    if regenerate and png_path.exists():
        print(f"  Creating icon.ico from {png_path.name}...")
        try:
            from PIL import Image
            
            # Open source PNG
            source = Image.open(png_path)
            print(f"  Source image size: {source.size[0]}x{source.size[1]}")
            
            # Convert to RGBA if needed
            if source.mode != 'RGBA':
                source = source.convert('RGBA')
            
            # Create high-quality icons at all required sizes (largest first for best quality)
            # Sort sizes descending so we resize from source for each, not chain resize
            sorted_sizes = sorted(ICON_SIZES, reverse=True)
            icons = []
            for size in sorted_sizes:
                # Always resize from the original source for best quality
                resized = source.resize((size, size), Image.Resampling.LANCZOS)
                icons.append(resized)
            
            # Save as ICO - use append_images only, NOT sizes parameter
            # The sizes parameter causes internal resizing which degrades quality
            # when we already have properly pre-resized images
            icons[0].save(
                icon_path,
                format='ICO',
                append_images=icons[1:]
            )
            
            print(f"  [OK] Created icon.ico with sizes: {sorted_sizes}")
            return True
            
        except ImportError:
            print("  [WARN] Pillow not available, cannot create icon")
            return False
        except Exception as e:
            print(f"  [ERROR] Failed to create icon: {e}")
            return False
    elif regenerate:
        print(f"  [WARN] PNG source not found at {png_path}")
        return False
    
    return True


def set_console_mode(spec_file: Path, console: bool):
    """Update the spec file to set console mode."""
    content = spec_file.read_text()
    
    # Replace console=True/False
    if console:
        content = re.sub(r'console=False', 'console=True', content)
    else:
        content = re.sub(r'console=True', 'console=False', content)
    
    spec_file.write_text(content)


def build_exe(debug: bool = False):
    """Build the executable using PyInstaller."""
    print_step("Building executable with PyInstaller...")
    
    if debug:
        print("  [DEBUG MODE] Console window will be visible for debugging")
    
    spec_file = BUILD_DIR / "normcode.spec"
    if not spec_file.exists():
        print(f"  [ERROR] Spec file not found: {spec_file}")
        return False
    
    # Set console mode based on debug flag
    set_console_mode(spec_file, console=debug)
    
    # Run PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        "--distpath", str(DIST_DIR),
        "--workpath", str(WORK_DIR),
        str(spec_file)
    ]
    
    if not run_command_safe(cmd, cwd=BUILD_DIR):
        print("  [ERROR] PyInstaller failed")
        return False
    
    # Verify output
    exe_path = DIST_DIR / "NormCodeCanvas" / "NormCodeCanvas.exe"
    if not exe_path.exists():
        print(f"  [ERROR] Build failed - executable not found at {exe_path}")
        return False
    
    print(f"  [OK] Executable created: {exe_path}")
    return True


def copy_to_release():
    """Copy the built application to the release folder."""
    print_step("Copying to release folder...")
    
    dist_folder = DIST_DIR / "NormCodeCanvas"
    if not dist_folder.exists():
        print("  [ERROR] Distribution folder not found")
        return False
    
    # Create release directory
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Copy executable to release (single-file access point)
    exe_src = dist_folder / "NormCodeCanvas.exe"
    exe_dst = RELEASE_DIR / "NormCodeCanvas.exe"
    
    if exe_dst.exists():
        exe_dst.unlink()
    
    shutil.copy2(exe_src, exe_dst)
    print(f"  [OK] Copied executable to: {exe_dst}")
    
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
    if not run_command_safe([str(iscc), str(iss_file)], cwd=BUILD_DIR):
        print("  [ERROR] Inno Setup failed")
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
    else:
        print(f"  [WARN] settings.yaml.example not found at {src}")
    
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


def check_webview2_runtime():
    """Check if WebView2 runtime is installed (for EdgeChromium)."""
    print_step("Checking WebView2 Runtime...")
    
    try:
        import winreg
        
        # Check both 32-bit and 64-bit registry locations
        paths = [
            r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
            r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
        ]
        
        for path in paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
                version, _ = winreg.QueryValueEx(key, "pv")
                winreg.CloseKey(key)
                print(f"  [OK] WebView2 Runtime found: {version}")
                return True
            except WindowsError:
                continue
        
        print("  [WARN] WebView2 Runtime not found")
        print("  [WARN] Users may need to install it from:")
        print("         https://developer.microsoft.com/en-us/microsoft-edge/webview2/")
        print("  [INFO] The app will fallback to CEF if WebView2 is not available")
        return True  # Not a fatal error, CEF will be used as fallback
        
    except Exception as e:
        print(f"  [INFO] Could not check WebView2 status: {e}")
        return True  # Continue anyway


def main():
    parser = argparse.ArgumentParser(
        description="Build NormCode Canvas Desktop Application for Windows",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_windows.py                    # Full build (windowed, no console)
  python build_windows.py --debug            # Build with console for debugging
  python build_windows.py --clean            # Clean and rebuild
  python build_windows.py --portable         # Build + create ZIP
  python build_windows.py --installer        # Build + create installer
  python build_windows.py --skip-frontend    # Skip npm build (faster)
  python build_windows.py --skip-deps        # Skip dependency installation
        """
    )
    parser.add_argument("--skip-frontend", action="store_true", 
                        help="Skip frontend build (use existing dist)")
    parser.add_argument("--skip-deps", action="store_true",
                        help="Skip dependency installation")
    parser.add_argument("--installer", action="store_true",
                        help="Create installer with Inno Setup")
    parser.add_argument("--clean", action="store_true",
                        help="Clean build artifacts before building")
    parser.add_argument("--portable", action="store_true",
                        help="Create portable ZIP distribution")
    parser.add_argument("--debug", action="store_true",
                        help="Build with console window for debugging")
    args = parser.parse_args()
    
    print_header("NormCode Canvas - Desktop App Build")
    print(f"  Project Root: {PROJECT_ROOT}")
    print(f"  Build Dir: {BUILD_DIR}")
    print(f"  Mode: {'Debug (with console)' if args.debug else 'Release (windowed)'}")
    
    # Clean if requested
    if args.clean:
        clean_build()
    
    # Install dependencies
    if not args.skip_deps:
        # Install build tools (PyInstaller, pywebview, etc.)
        if not install_build_requirements():
            print("\n[ERROR] Failed to install build requirements")
            sys.exit(1)
        
        # Install backend Python dependencies
        if not install_backend_requirements():
            print("\n[ERROR] Failed to install backend requirements")
            sys.exit(1)
    
    # Check system requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check WebView2 runtime (informational only)
    check_webview2_runtime()
    
    # Build frontend
    if not args.skip_frontend:
        if not build_frontend():
            print("\n[ERROR] Frontend build failed")
            sys.exit(1)
    else:
        print_step("Skipping frontend build (--skip-frontend)")
        if not (FRONTEND_DIR / "dist" / "index.html").exists():
            print("  [WARN] Warning: Frontend dist not found. Build may fail.")
    
    # Ensure icon exists with all sizes
    ensure_icon()
    
    # Build executable
    if not build_exe(debug=args.debug):
        print("\n[ERROR] Executable build failed")
        sys.exit(1)
    
    # Copy additional files
    copy_settings_example()
    
    # Copy to release folder
    copy_to_release()
    
    # Create installer if requested
    if args.installer:
        create_installer()
    
    # Create portable zip if requested
    if args.portable:
        create_portable_zip()
    
    # Summary
    print_header("Build Complete!")
    print(f"\n  Output: {DIST_DIR / 'NormCodeCanvas'}")
    print(f"  Executable: {DIST_DIR / 'NormCodeCanvas' / 'NormCodeCanvas.exe'}")
    print(f"  Release: {RELEASE_DIR / 'NormCodeCanvas.exe'}")
    
    if args.portable:
        print(f"  Portable ZIP: {DIST_DIR / 'NormCodeCanvas-Portable.zip'}")
    
    if args.installer:
        output_dir = BUILD_DIR / "output"
        installers = list(output_dir.glob("*.exe")) if output_dir.exists() else []
        if installers:
            print(f"  Installer: {installers[0]}")
    
    print("\n  The app will open in a native desktop window (no browser needed)!")
    if args.debug:
        print("  [DEBUG MODE] Console window will show logs for debugging.")


if __name__ == "__main__":
    main()
