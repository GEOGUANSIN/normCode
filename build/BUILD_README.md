# NormCode Canvas - Build Guide

This guide explains how to build NormCode Canvas into a standalone desktop application for Windows and macOS.

## Prerequisites

### Required (All Platforms)
1. **Python 3.10+** with pip
2. **Node.js 18+** with npm
3. **PyInstaller** - `pip install pyinstaller`

### Windows-Specific (Optional)
4. **Inno Setup 6** - Download from https://jrsoftware.org/isdl.php (for installer)

### macOS-Specific (Optional)
4. **Xcode Command Line Tools** - `xcode-select --install` (for code signing)

---

## Quick Build - Windows

```powershell
# 1. Install PyInstaller
pip install pyinstaller

# 2. Run build script
cd build
python build_windows.py
```

The executable will be in `build/dist/NormCodeCanvas/NormCodeCanvas.exe`

---

## Quick Build - macOS

```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Run build script
cd build
python build_macos.py
```

The application will be in `build/dist/NormCodeCanvas.app`

## Build Options - Windows

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

## Build Options - macOS

```bash
# Full build (default)
python build_macos.py

# Skip frontend build (use existing dist)
python build_macos.py --skip-frontend

# Clean before building
python build_macos.py --clean

# Create portable ZIP
python build_macos.py --portable

# Create DMG installer
python build_macos.py --dmg

# Code sign with identity
python build_macos.py --sign "Developer ID Application: Your Name"
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

### Windows
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

### macOS
```
build/dist/NormCodeCanvas.app/
└── Contents/
    ├── Info.plist          # App metadata
    ├── MacOS/
    │   └── NormCodeCanvas  # Main executable
    ├── Resources/
    │   ├── icon.icns       # App icon
    │   ├── frontend/dist/  # Built frontend
    │   ├── backend/        # Backend code
    │   ├── infra/          # NormCode infrastructure
    │   └── settings.yaml.example
    └── Frameworks/         # Python runtime and dependencies
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
Place `icon.ico` in the `build/resources/` folder before building.

### Large executable size
The executable includes the full Python runtime. To reduce size:
- Use `--upx` flag (requires UPX installed)
- Exclude unnecessary packages in `normcode.spec`

## Customization

### Application Icon
1. Create `build/resources/icon.ico` with multiple sizes (16x16, 32x32, 48x48, 256x256)
2. Rebuild the application

### Version Info
Edit `build/installer.iss`:
```ini
#define MyAppVersion "1.0.0"
```

### Installer Branding
Place these files in `build/resources/`:
- `banner.bmp` (164×314 pixels)
- `wizard.bmp` (55×58 pixels)

## Distribution

### Windows

| Format | File | Description |
|--------|------|-------------|
| Portable | `build/dist/NormCodeCanvas-Portable.zip` | Extract and run |
| Installer | `build/output/NormCodeCanvasSetup-x.x.x.exe` | Standard Windows installer |

### macOS

| Format | File | Description |
|--------|------|-------------|
| Portable | `build/dist/NormCodeCanvas-x.x.x-macos.zip` | Extract and run |
| DMG | `build/dist/NormCodeCanvas-x.x.x.dmg` | Drag-and-drop installer |

#### macOS Code Signing Notes

- **Ad-hoc signed** (default): App runs but shows "unidentified developer" warning
- **Developer signed**: Requires Apple Developer account and `--sign` option
- **Notarized**: Required for distribution outside App Store (additional steps needed)

## Development vs Production

| Aspect | Development | Production (Packaged) |
|--------|-------------|----------------------|
| Frontend | Vite dev server (port 5173) | Static files served by backend |
| Backend | Separate uvicorn process | Embedded in launcher |
| Hot Reload | Yes | No |
| Console | Terminal output | GUI window (Windows) / None (macOS) |
| Dependencies | Virtual environment | Bundled with PyInstaller |

## Platform-Specific Notes

### Windows
- Uses Tkinter for the launcher GUI
- Console can be enabled for debugging (`console=True` in spec)
- Inno Setup creates a standard Windows installer

### macOS
- Uses Tkinter for the launcher GUI (bundled with Python)
- Creates a native `.app` bundle
- DMG includes an Applications folder symlink for drag-and-drop install
- Ad-hoc signing is applied by default
- For distribution, consider full code signing and notarization

