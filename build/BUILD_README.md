# NormCode Canvas - Windows Build Guide

This guide explains how to build NormCode Canvas into a standalone Windows executable.

## Prerequisites

### Required
1. **Python 3.10+** with pip
2. **Node.js 18+** with npm
3. **PyInstaller** - `pip install pyinstaller`

### Optional (for installer creation)
4. **Inno Setup 6** - Download from https://jrsoftware.org/isdl.php

## Quick Build

```powershell
# 1. Install PyInstaller
pip install pyinstaller

# 2. Run build script
cd build
python build_windows.py
```

The executable will be in `build/dist/NormCodeCanvas/NormCodeCanvas.exe`

## Build Options

```powershell
# Full build (default)
python build_windows.py

# Skip frontend build (use existing dist)
python build_windows.py --skip-frontend

# Clean before building
python build_windows.py --clean

# Create portable ZIP
python build_windows.py --portable

# Create installer (requires Inno Setup)
python build_windows.py --installer
```

## Build Process

The build script performs these steps:

1. **Frontend Build** (`npm run build`)
   - Compiles React/TypeScript to static files
   - Output: `canvas_app/frontend/dist/`

2. **PyInstaller Packaging**
   - Bundles Python runtime and dependencies
   - Includes frontend dist files
   - Includes backend code
   - Output: `build/dist/NormCodeCanvas/`

3. **Installer Creation** (optional)
   - Uses Inno Setup to create installer
   - Output: `build/output/NormCodeCanvasSetup-x.x.x.exe`

## Output Structure

```
build/dist/NormCodeCanvas/
├── NormCodeCanvas.exe      # Main executable
├── _internal/              # Python runtime and dependencies
│   ├── frontend/dist/      # Built frontend
│   ├── backend/            # Backend code
│   ├── infra/              # NormCode infrastructure
│   └── ...
├── settings.yaml.example   # Configuration template
└── resources/              # Icons and assets
```

## Troubleshooting

### "Module not found" errors
Make sure all required Python packages are installed:
```bash
pip install -r canvas_app/backend/requirements.txt
```

### Frontend build fails
Make sure npm dependencies are installed:
```bash
cd canvas_app/frontend
npm install
npm run build
```

### Icon not showing
Place `icon.ico` in the `resources/` folder before building.

### Large executable size
The executable includes the full Python runtime. To reduce size:
- Use `--upx` flag (requires UPX installed)
- Exclude unnecessary packages in `normcode.spec`

## Customization

### Application Icon
1. Create `resources/icon.ico` with multiple sizes (16x16, 32x32, 48x48, 256x256)
2. Rebuild the application

### Version Info
Edit `build/installer.iss`:
```ini
#define MyAppVersion "1.0.0"
```

### Installer Branding
Place these files in `resources/`:
- `banner.bmp` (164×314 pixels)
- `wizard.bmp` (55×58 pixels)

## Distribution

### Portable Version
Share `build/dist/NormCodeCanvas-Portable.zip` - users can extract and run.

### Installer Version
Share `build/output/NormCodeCanvasSetup-x.x.x.exe` - standard Windows installer experience.

## Development vs Production

| Aspect | Development | Production (Packaged) |
|--------|-------------|----------------------|
| Frontend | Vite dev server (port 5173) | Static files served by backend |
| Backend | Separate uvicorn process | Embedded in launcher |
| Hot Reload | Yes | No |
| Console | Terminal output | GUI window only |
| Dependencies | Virtual environment | Bundled with PyInstaller |

