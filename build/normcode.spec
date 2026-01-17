# -*- mode: python ; coding: utf-8 -*-
"""
NormCode Canvas - PyInstaller Spec File
========================================

This spec file configures PyInstaller to package the NormCode Canvas 
application into a standalone Windows executable with native window support.

Build command:
    cd build
    pyinstaller normcode.spec

Output:
    build/dist/NormCodeCanvas/NormCodeCanvas.exe
"""

import sys
import os
import glob
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

# Paths
SPEC_DIR = Path(SPECPATH)
PROJECT_ROOT = SPEC_DIR.parent
CANVAS_APP = PROJECT_ROOT / "canvas_app"
# Launcher and resources are now inside build/
LAUNCHER_DIR = SPEC_DIR / "launcher"
RESOURCES_DIR = SPEC_DIR / "resources"

block_cipher = None

# Collect hidden imports for all the modules we need
hidden_imports = [
    # FastAPI and web framework - MUST include all submodules
    'uvicorn',
    'uvicorn.config',
    'uvicorn.main',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.loops.asyncio',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.http.httptools_impl',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.protocols.websockets.websockets_impl',
    'uvicorn.protocols.websockets.wsproto_impl',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',
    'uvicorn.server',
    'uvicorn.supervisors',
    'uvicorn.supervisors.multiprocess',
    'uvicorn.supervisors.statreload',
    'uvicorn.middleware',
    'uvicorn.middleware.proxy_headers',
    'uvicorn.middleware.message_logger',
    
    # FastAPI
    'fastapi',
    'fastapi.applications',
    'fastapi.routing',
    'fastapi.responses',
    'fastapi.staticfiles',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    
    # Starlette
    'starlette',
    'starlette.responses',
    'starlette.staticfiles',
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',
    'starlette.websockets',
    
    # Pydantic
    'pydantic',
    'pydantic.main',
    'pydantic_settings',
    'pydantic_core',
    
    # WebSocket support
    'websockets',
    'websockets.legacy',
    'websockets.legacy.server',
    'websockets.server',
    
    # HTTP
    'httptools',
    'h11',
    
    # Multipart
    'multipart',
    'python_multipart',
    
    # Async
    'anyio',
    'anyio._core',
    'anyio._backends',
    'anyio._backends._asyncio',
    'sniffio',
    
    # Click (uvicorn dependency)
    'click',
    
    # Email validation (pydantic)
    'email_validator',
    
    # Encoding
    'encodings',
    'encodings.idna',
    
    # XML parsing (required for pkg_resources and plistlib)
    'xml',
    'xml.parsers',
    'xml.parsers.expat',
    'pyexpat',
    'xml.etree',
    'xml.etree.ElementTree',
    'xml.dom',
    'xml.sax',
    'plistlib',
    
    # YAML for settings
    'yaml',
    
    # OpenAI (for infra)
    'openai',
    'httpx',
    
    # ===== pywebview for native desktop window =====
    'webview',
    'webview.platforms',
    'webview.platforms.edgechromium',
    'webview.platforms.winforms',
    'webview.platforms.cef',
    'webview.js',
    'webview.util',
    'webview.window',
    'webview.event',
    'webview.guilib',
    'webview.menu',
    'webview.screen',
    'webview.http',
    
    # pythonnet for Windows .NET integration (pywebview dependency)
    'clr',
    'clr_loader',
    'pythonnet',
    
    # bottle (used by pywebview internally)
    'bottle',
    
    # proxy_tools (pywebview dependency)
    'proxy_tools',
]

# Add uvicorn submodules explicitly
try:
    hidden_imports += collect_submodules('uvicorn')
except Exception:
    pass

# Add fastapi submodules
try:
    hidden_imports += collect_submodules('fastapi')
except Exception:
    pass

# Add starlette submodules
try:
    hidden_imports += collect_submodules('starlette')
except Exception:
    pass

# Add pywebview submodules
try:
    hidden_imports += collect_submodules('webview')
except Exception:
    pass

# Add clr_loader submodules for pythonnet
try:
    hidden_imports += collect_submodules('clr_loader')
except Exception:
    pass


# Collect all submodules from backend routers, services, schemas
try:
    sys.path.insert(0, str(CANVAS_APP / "backend"))
    hidden_imports += collect_submodules('routers')
    hidden_imports += collect_submodules('services')
    hidden_imports += collect_submodules('schemas')
    hidden_imports += collect_submodules('core')
except Exception:
    pass

# Collect infra module
try:
    sys.path.insert(0, str(PROJECT_ROOT))
    hidden_imports += collect_submodules('infra')
except Exception:
    pass

# Data files to include
datas = [
    # Frontend dist (pre-built static files)
    (str(CANVAS_APP / "frontend" / "dist"), "frontend/dist"),
    
    # Backend source code (needed for dynamic imports)
    (str(CANVAS_APP / "backend"), "backend"),
    
    # Infra module
    (str(PROJECT_ROOT / "infra"), "infra"),
    
    # Settings example
    (str(CANVAS_APP / "settings.yaml.example"), "."),
]

# Collect webview data files (templates, js files, etc.)
try:
    datas += collect_data_files('webview')
except Exception:
    pass

# Collect clr_loader data files
try:
    datas += collect_data_files('clr_loader')
except Exception:
    pass

# Binaries - collect native libraries
binaries = []

# CRITICAL: Include pyexpat and other core DLLs (required for XML parsing, pkg_resources, plistlib)
# This is especially important for conda environments where DLLs may be in non-standard locations
try:
    python_dir = Path(sys.executable).parent
    
    # Possible locations for Python extension modules and DLLs
    search_dirs = [
        python_dir / "DLLs",
        python_dir,
        python_dir / "Library" / "bin",  # Conda location
        python_dir / "Lib",
    ]
    
    # Critical extension modules that must be included
    critical_modules = ['pyexpat.pyd', 'pyexpat.cp311-win_amd64.pyd', '_elementtree.pyd']
    # Critical DLLs
    critical_dlls = ['libexpat.dll', 'expat.dll']
    
    found_pyexpat = False
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        # Look for .pyd files (Python extension modules)
        for module_name in critical_modules:
            module_path = search_dir / module_name
            if module_path.exists() and not found_pyexpat:
                binaries.append((str(module_path), "."))
                print(f"Including {module_name} from: {module_path}")
                if 'pyexpat' in module_name:
                    found_pyexpat = True
        
        # Also look for any pyexpat variant
        if not found_pyexpat:
            for pyd in search_dir.glob("pyexpat*.pyd"):
                binaries.append((str(pyd), "."))
                print(f"Including pyexpat from: {pyd}")
                found_pyexpat = True
                break
        
        # Look for DLLs
        for dll_name in critical_dlls:
            dll_path = search_dir / dll_name
            if dll_path.exists():
                binaries.append((str(dll_path), "."))
                print(f"Including {dll_name} from: {dll_path}")
    
    if not found_pyexpat:
        print("WARNING: pyexpat.pyd not found in any standard location!")
        print(f"  Searched: {[str(d) for d in search_dirs if d.exists()]}")
        
except Exception as e:
    print(f"Warning: Error while collecting pyexpat: {e}")

# Try to collect pythonnet runtime binaries
try:
    import clr_loader
    clr_path = Path(clr_loader.__file__).parent
    for dll in clr_path.rglob('*.dll'):
        binaries.append((str(dll), str(dll.parent.relative_to(clr_path.parent))))
except Exception:
    pass

# Add icon if exists - use absolute path for reliability
icon_path = RESOURCES_DIR / "icon.ico"
print(f"Looking for icon at: {icon_path}")
print(f"Icon exists: {icon_path.exists()}")

if icon_path.exists():
    # Include resources folder in data files
    datas.append((str(RESOURCES_DIR), "resources"))
    # Convert to absolute path string for PyInstaller
    icon_path = str(icon_path.resolve())
    print(f"Using icon: {icon_path}")
else:
    icon_path = None
    print("WARNING: icon.ico not found, building without icon")

a = Analysis(
    [str(LAUNCHER_DIR / "desktop_launcher.py")],
    pathex=[
        str(PROJECT_ROOT),
        str(CANVAS_APP / "backend"),
    ],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'torch',
        'tensorflow',
        'keras',
        'sklearn',
        'jupyter',
        'notebook',
        'IPython',
        'pytest',
        'sphinx',
        '_pytest',
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
    name='NormCodeCanvas',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # WINDOWED MODE - no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,  # Already a string or None
    version_file=str(SPEC_DIR / "version_info.txt") if (SPEC_DIR / "version_info.txt").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='NormCodeCanvas',
)
