#!/usr/bin/env python3
"""
NormCode Canvas - macOS Build Script
=====================================

This script automates the build process for creating a macOS application.
It is fully self-contained and will install required dependencies automatically.

Steps:
1. Installs required Python packages (PyInstaller, etc.)
2. Installs backend Python dependencies
3. Builds the frontend (npm run build)
4. Packages everything with PyInstaller into a .app bundle
5. Optionally creates a DMG for distribution

Usage:
    python build_macos.py              # Full build
    python build_macos.py --skip-frontend  # Skip frontend build
    python build_macos.py --dmg        # Also create DMG installer
    python build_macos.py --clean      # Clean build artifacts first
    python build_macos.py --portable   # Create portable ZIP

Requirements:
    - macOS 10.15+ (Catalina or later recommended)
    - Python 3.10+
    - Node.js 18+ with npm
    - Xcode Command Line Tools (for codesigning, optional)
"""

import subprocess
import sys
import shutil
import argparse
import platform
from pathlib import Path

# Verify we're on macOS
if platform.system() != "Darwin":
    print("[ERROR] This script is for macOS only.")
    print("        Use build_windows.py for Windows.")
    sys.exit(1)

# Paths
BUILD_DIR = Path(__file__).parent
PROJECT_ROOT = BUILD_DIR.parent
CANVAS_APP = PROJECT_ROOT / "canvas_app"
FRONTEND_DIR = CANVAS_APP / "frontend"
BACKEND_DIR = CANVAS_APP / "backend"
DIST_DIR = BUILD_DIR / "dist"
WORK_DIR = BUILD_DIR / "build"

# App info
APP_NAME = "NormCodeCanvas"
APP_BUNDLE_ID = "com.normcode.canvas"
APP_VERSION = "1.0.0"

# Required Python packages for building
BUILD_REQUIREMENTS = [
    "pyinstaller",
    "pillow",  # For icon conversion if needed
]

# Required icon sizes for macOS (standard + retina)
ICON_SIZES = [16, 32, 64, 128, 256, 512, 1024]


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
    try:
        __import__(package_name.replace("-", "_").split("[")[0])
        return True
    except ImportError:
        return False


def install_build_requirements():
    """Install required Python packages for building."""
    print_step("Checking/Installing build requirements...")
    
    missing = []
    for pkg in BUILD_REQUIREMENTS:
        pkg_import = pkg.replace("-", "_").split("[")[0]
        if pkg_import == "pyinstaller":
            pkg_import = "PyInstaller"
        if not check_package_installed(pkg_import):
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
    try:
        result = subprocess.run(
            ["pkill", "-f", APP_NAME],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  Killed running {APP_NAME} instance")
            import time
            time.sleep(1)
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
    
    # Check macOS version
    mac_version = platform.mac_ver()[0]
    print(f"  macOS: {mac_version}")
    
    # Check Python version
    py_version = sys.version_info
    print(f"  Python: {py_version.major}.{py_version.minor}.{py_version.micro}")
    if py_version < (3, 8):
        errors.append("Python 3.8+ is required")
    
    # Check PyInstaller
    try:
        import PyInstaller
        print(f"  PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        errors.append("PyInstaller not available (installation may have failed)")
    
    # Check Node.js / npm
    npm_path = shutil.which("npm")
    if npm_path:
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            print(f"  npm: {result.stdout.strip()}")
        except Exception:
            errors.append("npm found but failed to get version")
    else:
        errors.append("npm not found. Install Node.js from https://nodejs.org/")
    
    # Check for codesign (optional but recommended)
    codesign_path = shutil.which("codesign")
    if codesign_path:
        print("  codesign: Available")
    else:
        warnings.append("codesign not found. App will not be signed.")
    
    # Check for hdiutil (for DMG creation)
    hdiutil_path = shutil.which("hdiutil")
    if hdiutil_path:
        print("  hdiutil: Available")
    else:
        warnings.append("hdiutil not found. DMG creation will not be available.")
    
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
    
    # Install dependencies if needed
    if not (FRONTEND_DIR / "node_modules").exists():
        print("  Installing npm dependencies...")
        if not run_command_safe(["npm", "install"], cwd=FRONTEND_DIR):
            print("  [ERROR] npm install failed")
            return False
    
    # Build
    if not run_command_safe(["npm", "run", "build"], cwd=FRONTEND_DIR):
        print("  [ERROR] npm run build failed")
        return False
    
    # Verify dist was created
    dist_path = FRONTEND_DIR / "dist"
    if not dist_path.exists() or not (dist_path / "index.html").exists():
        print(f"  [ERROR] Frontend build failed - dist/index.html not found")
        return False
    
    print("  [OK] Frontend build complete")
    return True


def verify_icns_icon(icns_path: Path) -> bool:
    """Verify that an ICNS file is valid and has required sizes."""
    try:
        # Check file size (valid ICNS should be > 1KB)
        if icns_path.stat().st_size < 1024:
            print(f"  ICNS file too small, may be corrupted")
            return False
        
        # Try to read header to verify it's a valid ICNS
        with open(icns_path, 'rb') as f:
            header = f.read(4)
            if header != b'icns':
                print(f"  Invalid ICNS header")
                return False
        
        print(f"  [OK] ICNS file appears valid")
        return True
    except Exception as e:
        print(f"  Could not verify ICNS: {e}")
        return False


def ensure_icon():
    """Ensure icon.icns exists with all required sizes."""
    print_step("Checking/Creating application icon...")
    
    resources_dir = BUILD_DIR / "resources"
    png_path = resources_dir / "Psylensai_log_raw.png"
    icns_path = resources_dir / "icon.icns"
    
    # Check if we need to regenerate the icon
    regenerate = False
    
    if not icns_path.exists():
        print("  icon.icns not found, will create from PNG")
        regenerate = True
    elif not verify_icns_icon(icns_path):
        print("  icon.icns appears invalid, will recreate")
        regenerate = True
    else:
        print(f"  [OK] Using existing icon: {icns_path}")
        return icns_path
    
    if regenerate and png_path.exists():
        print(f"  Creating icon.icns from {png_path.name}...")
        
        # Create iconset directory
        iconset_dir = resources_dir / "icon.iconset"
        if iconset_dir.exists():
            shutil.rmtree(iconset_dir)
        iconset_dir.mkdir(exist_ok=True)
        
        try:
            from PIL import Image
            
            # Open source PNG
            source = Image.open(png_path)
            
            # Convert to RGBA if needed
            if source.mode != 'RGBA':
                source = source.convert('RGBA')
            
            # Create icons at all required sizes
            for size in ICON_SIZES:
                # Standard resolution
                resized = source.resize((size, size), Image.Resampling.LANCZOS)
                resized.save(iconset_dir / f"icon_{size}x{size}.png")
                
                # Retina resolution (2x) - only for sizes up to 512
                if size <= 512:
                    retina_size = size * 2
                    resized_2x = source.resize((retina_size, retina_size), Image.Resampling.LANCZOS)
                    resized_2x.save(iconset_dir / f"icon_{size}x{size}@2x.png")
            
            # Convert iconset to icns using iconutil
            result = subprocess.run(
                ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
                capture_output=True,
                text=True
            )
            
            # Clean up iconset
            shutil.rmtree(iconset_dir)
            
            if result.returncode == 0:
                print(f"  [OK] Created icon.icns with sizes: {ICON_SIZES}")
                return icns_path
            else:
                print(f"  [ERROR] iconutil failed: {result.stderr}")
                return None
                
        except ImportError:
            print("  [WARN] Pillow not available, cannot create icon")
            if iconset_dir.exists():
                shutil.rmtree(iconset_dir)
            return None
        except Exception as e:
            print(f"  [ERROR] Failed to create icon: {e}")
            if iconset_dir.exists():
                shutil.rmtree(iconset_dir)
            return None
    elif regenerate:
        print(f"  [WARN] PNG source not found at {png_path}")
        return None
    
    return icns_path


def convert_icon_to_icns():
    """Convert PNG icon to ICNS format for macOS. (Legacy wrapper)"""
    return ensure_icon()


def create_macos_spec():
    """Create a macOS-specific PyInstaller spec file."""
    print_step("Creating macOS spec file...")
    
    icon_path = convert_icon_to_icns()
    icon_str = f"'{icon_path}'" if icon_path else "None"
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
NormCode Canvas - macOS PyInstaller Spec File
==============================================

Auto-generated spec file for macOS build.
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Paths
SPEC_DIR = Path(SPECPATH)
PROJECT_ROOT = SPEC_DIR.parent
CANVAS_APP = PROJECT_ROOT / "canvas_app"
LAUNCHER_DIR = SPEC_DIR / "launcher"
RESOURCES_DIR = SPEC_DIR / "resources"

block_cipher = None

# Hidden imports (same as Windows)
hidden_imports = [
    # FastAPI and web framework
    'uvicorn', 'uvicorn.config', 'uvicorn.main', 'uvicorn.logging',
    'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.loops.asyncio',
    'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl', 'uvicorn.protocols.http.httptools_impl',
    'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
    'uvicorn.protocols.websockets.websockets_impl',
    'uvicorn.lifespan', 'uvicorn.lifespan.on', 'uvicorn.lifespan.off',
    'uvicorn.server', 'uvicorn.supervisors',
    
    # FastAPI
    'fastapi', 'fastapi.applications', 'fastapi.routing',
    'fastapi.responses', 'fastapi.staticfiles', 'fastapi.middleware',
    'fastapi.middleware.cors',
    
    # Starlette
    'starlette', 'starlette.responses', 'starlette.staticfiles',
    'starlette.routing', 'starlette.middleware', 'starlette.middleware.cors',
    'starlette.websockets',
    
    # Pydantic
    'pydantic', 'pydantic.main', 'pydantic_settings', 'pydantic_core',
    
    # WebSocket
    'websockets', 'websockets.legacy', 'websockets.legacy.server', 'websockets.server',
    
    # HTTP
    'httptools', 'h11',
    
    # Multipart
    'multipart', 'python_multipart',
    
    # Async
    'anyio', 'anyio._core', 'anyio._backends', 'anyio._backends._asyncio', 'sniffio',
    
    # Other
    'click', 'email_validator', 'encodings', 'encodings.idna', 'yaml',
    'openai', 'httpx',
]

# Collect submodules
try:
    hidden_imports += collect_submodules('uvicorn')
    hidden_imports += collect_submodules('fastapi')
    hidden_imports += collect_submodules('starlette')
except Exception:
    pass

try:
    sys.path.insert(0, str(CANVAS_APP / "backend"))
    hidden_imports += collect_submodules('routers')
    hidden_imports += collect_submodules('services')
    hidden_imports += collect_submodules('schemas')
    hidden_imports += collect_submodules('core')
except Exception:
    pass

try:
    sys.path.insert(0, str(PROJECT_ROOT))
    hidden_imports += collect_submodules('infra')
except Exception:
    pass

# Data files
datas = [
    (str(CANVAS_APP / "frontend" / "dist"), "frontend/dist"),
    (str(CANVAS_APP / "backend"), "backend"),
    (str(PROJECT_ROOT / "infra"), "infra"),
    (str(CANVAS_APP / "settings.yaml.example"), "."),
]

# Add icon resources
if RESOURCES_DIR.exists():
    datas.append((str(RESOURCES_DIR), "resources"))

a = Analysis(
    [str(LAUNCHER_DIR / "desktop_launcher.py")],
    pathex=[
        str(PROJECT_ROOT),
        str(CANVAS_APP / "backend"),
    ],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'numpy', 'pandas', 'scipy', 'PIL', 'cv2',
        'torch', 'tensorflow', 'keras', 'sklearn',
        'jupyter', 'notebook', 'IPython', 'pytest', 'sphinx', '_pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window on macOS
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{APP_NAME}',
)

# Create macOS .app bundle
app = BUNDLE(
    coll,
    name='{APP_NAME}.app',
    icon={icon_str},
    bundle_identifier='{APP_BUNDLE_ID}',
    info_plist={{
        'CFBundleName': '{APP_NAME}',
        'CFBundleDisplayName': 'NormCode Canvas',
        'CFBundleVersion': '{APP_VERSION}',
        'CFBundleShortVersionString': '{APP_VERSION}',
        'CFBundleIdentifier': '{APP_BUNDLE_ID}',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15.0',
        'NSRequiresAquaSystemAppearance': False,  # Support dark mode
    }},
)
'''
    
    spec_file = BUILD_DIR / "normcode_macos.spec"
    spec_file.write_text(spec_content)
    print(f"  [OK] Created {spec_file}")
    return spec_file


def build_app():
    """Build the macOS .app bundle using PyInstaller."""
    print_step("Building macOS application with PyInstaller...")
    
    # Create macOS-specific spec file
    spec_file = create_macos_spec()
    
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
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        # PyInstaller might put it in a subdirectory
        app_path = DIST_DIR / APP_NAME / f"{APP_NAME}.app"
    
    if not app_path.exists():
        print(f"  [ERROR] Build failed - .app bundle not found")
        return False
    
    print(f"  [OK] Application created: {app_path}")
    return True


def codesign_app(identity: str = None):
    """Sign the application (optional but recommended for distribution)."""
    print_step("Code signing application...")
    
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        app_path = DIST_DIR / APP_NAME / f"{APP_NAME}.app"
    
    if not app_path.exists():
        print("  [ERROR] App bundle not found for signing")
        return False
    
    if identity:
        # Sign with provided identity
        cmd = [
            "codesign",
            "--force",
            "--deep",
            "--sign", identity,
            str(app_path)
        ]
    else:
        # Ad-hoc signing (no identity required, but app won't be notarized)
        cmd = [
            "codesign",
            "--force",
            "--deep",
            "--sign", "-",
            str(app_path)
        ]
        print("  [INFO] Using ad-hoc signing (app will show as 'unidentified developer')")
    
    if run_command_safe(cmd):
        print("  [OK] Application signed")
        return True
    else:
        print("  [WARN] Code signing failed - app may not run on other Macs")
        return True  # Not a fatal error


def create_dmg():
    """Create a DMG installer for distribution."""
    print_step("Creating DMG installer...")
    
    # Find the app bundle
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        app_path = DIST_DIR / APP_NAME / f"{APP_NAME}.app"
    
    if not app_path.exists():
        print("  [ERROR] App bundle not found")
        return False
    
    dmg_name = f"{APP_NAME}-{APP_VERSION}.dmg"
    dmg_path = DIST_DIR / dmg_name
    
    # Remove existing DMG
    if dmg_path.exists():
        dmg_path.unlink()
    
    # Create a temporary directory for DMG contents
    dmg_temp = DIST_DIR / "dmg_temp"
    if dmg_temp.exists():
        shutil.rmtree(dmg_temp)
    dmg_temp.mkdir()
    
    # Copy app to temp directory
    shutil.copytree(app_path, dmg_temp / f"{APP_NAME}.app", symlinks=True)
    
    # Create Applications symlink for drag-and-drop install
    applications_link = dmg_temp / "Applications"
    applications_link.symlink_to("/Applications")
    
    # Create DMG using hdiutil
    cmd = [
        "hdiutil", "create",
        "-volname", APP_NAME,
        "-srcfolder", str(dmg_temp),
        "-ov",
        "-format", "UDZO",  # Compressed
        str(dmg_path)
    ]
    
    if not run_command_safe(cmd):
        print("  [ERROR] DMG creation failed")
        shutil.rmtree(dmg_temp)
        return False
    
    # Cleanup
    shutil.rmtree(dmg_temp)
    
    print(f"  [OK] Created: {dmg_path}")
    return True


def copy_settings_example():
    """Copy settings.yaml.example to dist if needed."""
    print_step("Copying configuration files...")
    
    src = CANVAS_APP / "settings.yaml.example"
    
    # Find app bundle
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        app_path = DIST_DIR / APP_NAME / f"{APP_NAME}.app"
    
    if app_path.exists() and src.exists():
        # Copy to Resources inside app bundle
        resources_dst = app_path / "Contents" / "Resources"
        resources_dst.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, resources_dst / "settings.yaml.example")
        print(f"  [OK] Copied settings.yaml.example to app bundle")
    else:
        print(f"  [WARN] Could not copy settings.yaml.example")
    
    return True


def create_portable_zip():
    """Create a portable zip distribution."""
    print_step("Creating portable ZIP...")
    
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        app_path = DIST_DIR / APP_NAME / f"{APP_NAME}.app"
    
    if not app_path.exists():
        print("  [ERROR] App bundle not found")
        return False
    
    zip_name = DIST_DIR / f"{APP_NAME}-{APP_VERSION}-macos"
    
    # Use ditto to preserve macOS metadata and symlinks
    cmd = ["ditto", "-c", "-k", "--keepParent", str(app_path), f"{zip_name}.zip"]
    
    if not run_command_safe(cmd):
        # Fallback to shutil
        shutil.make_archive(str(zip_name), 'zip', app_path.parent, app_path.name)
    
    print(f"  [OK] Created: {zip_name}.zip")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Build NormCode Canvas for macOS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_macos.py                    # Full build
  python build_macos.py --clean            # Clean and rebuild
  python build_macos.py --dmg              # Build + create DMG
  python build_macos.py --portable         # Build + create ZIP
  python build_macos.py --skip-frontend    # Skip npm build (faster)
  python build_macos.py --skip-deps        # Skip dependency installation
  python build_macos.py --sign "Developer ID Application: Name"  # Code sign
        """
    )
    parser.add_argument("--skip-frontend", action="store_true", 
                        help="Skip frontend build (use existing dist)")
    parser.add_argument("--skip-deps", action="store_true",
                        help="Skip dependency installation")
    parser.add_argument("--dmg", action="store_true",
                        help="Create DMG installer")
    parser.add_argument("--clean", action="store_true",
                        help="Clean build artifacts before building")
    parser.add_argument("--portable", action="store_true",
                        help="Create portable ZIP distribution")
    parser.add_argument("--sign", type=str, metavar="IDENTITY",
                        help="Code signing identity (or use '-' for ad-hoc)")
    args = parser.parse_args()
    
    print_header("NormCode Canvas - macOS Build")
    print(f"  Project Root: {PROJECT_ROOT}")
    print(f"  Build Dir: {BUILD_DIR}")
    print(f"  macOS: {platform.mac_ver()[0]}")
    print(f"  Architecture: {platform.machine()}")
    
    # Clean if requested
    if args.clean:
        clean_build()
    
    # Install dependencies
    if not args.skip_deps:
        if not install_build_requirements():
            print("\n[ERROR] Failed to install build requirements")
            sys.exit(1)
        
        if not install_backend_requirements():
            print("\n[ERROR] Failed to install backend requirements")
            sys.exit(1)
    
    # Check system requirements
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
    
    # Build application
    if not build_app():
        print("\n[ERROR] Application build failed")
        sys.exit(1)
    
    # Copy additional files
    copy_settings_example()
    
    # Code sign if requested
    if args.sign:
        codesign_app(args.sign)
    else:
        # Always do ad-hoc signing
        codesign_app()
    
    # Create DMG if requested
    if args.dmg:
        create_dmg()
    
    # Create portable zip if requested
    if args.portable:
        create_portable_zip()
    
    # Summary
    print_header("Build Complete!")
    
    app_path = DIST_DIR / f"{APP_NAME}.app"
    if not app_path.exists():
        app_path = DIST_DIR / APP_NAME / f"{APP_NAME}.app"
    
    print(f"\n  Application: {app_path}")
    
    if args.portable:
        print(f"  Portable ZIP: {DIST_DIR / f'{APP_NAME}-{APP_VERSION}-macos.zip'}")
    
    if args.dmg:
        print(f"  DMG Installer: {DIST_DIR / f'{APP_NAME}-{APP_VERSION}.dmg'}")
    
    print("\n  To run: open the .app bundle or drag it to Applications")
    print("  To distribute: use the DMG or ZIP file")


if __name__ == "__main__":
    main()

