# -*- mode: python ; coding: utf-8 -*-
"""
NormCode Canvas - PyInstaller Spec File
========================================

This spec file configures PyInstaller to package the NormCode Canvas 
application into a standalone Windows executable.

Build command:
    cd build
    pyinstaller normcode.spec

Output:
    build/dist/NormCodeCanvas/NormCodeCanvas.exe
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Paths
SPEC_DIR = Path(SPECPATH)
PROJECT_ROOT = SPEC_DIR.parent
CANVAS_APP = PROJECT_ROOT / "canvas_app"
LAUNCHER_DIR = PROJECT_ROOT / "launcher"
RESOURCES_DIR = PROJECT_ROOT / "resources"

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
    
    # YAML for settings
    'yaml',
    
    # OpenAI (for infra)
    'openai',
    'httpx',
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

# Add icon if exists
icon_path = RESOURCES_DIR / "icon.ico"
if not icon_path.exists():
    icon_path = None
else:
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
    console=True,  # Enable console for debugging (set to False for release)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path else None,
    version_file=None,
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

