# Scripts Directory

Utility scripts for the NormCode Deployment Server.

## Available Scripts

### `start_server.py`

Convenience wrapper to start the NormCode Deployment Server.

**Usage:**
```bash
python scripts/start_server.py
python scripts/start_server.py --port 9000
python scripts/start_server.py --host 127.0.0.1 --port 8080
```

**Options:**
- `--host`: Host to bind (default: 0.0.0.0)
- `--port`: Port to bind (default: 8080)
- `--plans-dir`: Plans directory path
- `--runs-dir`: Runs directory path
- `--reload`: Enable auto-reload (development)

### `pack.py`

Creates self-contained deployment packages (.zip) from NormCode projects.

**Usage:**
```bash
# Pack a project
python scripts/pack.py ./test_ncs/testproject.normcode-canvas.json
python scripts/pack.py ./test_ncs/testproject.normcode-canvas.json -o my-plan.zip

# Unpack a package
python scripts/pack.py --unpack my-plan.normcode.zip
python scripts/pack.py --unpack my-plan.normcode.zip -o ./unpacked/
```

**Options:**
- `input`: Path to .normcode-canvas.json (pack) or .normcode.zip (unpack)
- `-o, --output`: Output path (default: auto-generated)
- `--unpack`: Unpack a .zip instead of packing
- `-q, --quiet`: Suppress output

## Notes

- All scripts should be run from the `normal_server/` directory or with proper path resolution
- Scripts automatically detect their location and adjust paths accordingly
- The main server entry point (`server.py`) remains in the root directory

