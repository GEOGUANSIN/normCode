"""
Deployment service for managing deployment servers and deploying projects.

This service enables the Canvas App to:
1. Manage a list of deployment servers
2. Check server health and available LLM models
3. Package and deploy projects to remote servers
4. Start and monitor runs on remote servers
"""
import json
import logging
import uuid
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import shutil

from schemas.deployment_schemas import (
    DeploymentServer,
    RemotePlan,
    RemoteRunStatus,
    RunProgress,
    ServerHealthResponse,
    BuildServerResponse,
)
from services.project_service import project_service, get_app_data_dir
from datetime import datetime as dt_module

logger = logging.getLogger(__name__)

# Try to import requests, fall back gracefully
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not available - deployment features will be limited")


DEPLOYMENT_SERVERS_FILE = "deployment-servers.json"


class DeploymentService:
    """Service for managing deployment servers and deploying projects."""
    
    def __init__(self):
        self._servers: Dict[str, DeploymentServer] = {}
        self._load_servers()
    
    def _get_servers_file_path(self) -> Path:
        """Get path to the servers configuration file."""
        app_data = get_app_data_dir()
        return app_data / DEPLOYMENT_SERVERS_FILE
    
    def _load_servers(self):
        """Load servers from persistent storage."""
        servers_file = self._get_servers_file_path()
        if servers_file.exists():
            try:
                with open(servers_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for server_data in data.get('servers', []):
                    server = DeploymentServer(**server_data)
                    self._servers[server.id] = server
                logger.info(f"Loaded {len(self._servers)} deployment servers")
            except Exception as e:
                logger.warning(f"Failed to load deployment servers: {e}")
    
    def _save_servers(self):
        """Save servers to persistent storage."""
        servers_file = self._get_servers_file_path()
        try:
            servers_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'servers': [s.model_dump() for s in self._servers.values()]
            }
            with open(servers_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save deployment servers: {e}")
    
    # =========================================================================
    # Server Management
    # =========================================================================
    
    def get_servers(self) -> List[DeploymentServer]:
        """Get all registered deployment servers."""
        return list(self._servers.values())
    
    def get_server(self, server_id: str) -> Optional[DeploymentServer]:
        """Get a specific server by ID."""
        return self._servers.get(server_id)
    
    def get_default_server(self) -> Optional[DeploymentServer]:
        """Get the default deployment server."""
        for server in self._servers.values():
            if server.is_default:
                return server
        # Return first server if no default set
        if self._servers:
            return next(iter(self._servers.values()))
        return None
    
    def add_server(
        self, 
        name: str, 
        url: str, 
        description: Optional[str] = None,
        is_default: bool = False,
    ) -> DeploymentServer:
        """
        Add a new deployment server.
        
        Args:
            name: Display name for the server
            url: Server URL (e.g., http://localhost:8080)
            description: Optional description
            is_default: Whether this should be the default server
            
        Returns:
            The created DeploymentServer
        """
        # Normalize URL (remove trailing slash)
        url = url.rstrip('/')
        
        # Generate unique ID
        server_id = str(uuid.uuid4())[:8]
        
        # If setting as default, unset other defaults
        if is_default:
            for server in self._servers.values():
                server.is_default = False
        
        server = DeploymentServer(
            id=server_id,
            name=name,
            url=url,
            description=description,
            is_default=is_default,
            added_at=datetime.now(),
        )
        
        self._servers[server_id] = server
        self._save_servers()
        
        logger.info(f"Added deployment server '{name}' at {url}")
        return server
    
    def update_server(
        self,
        server_id: str,
        name: Optional[str] = None,
        url: Optional[str] = None,
        description: Optional[str] = None,
        is_default: Optional[bool] = None,
    ) -> DeploymentServer:
        """
        Update an existing deployment server.
        
        Args:
            server_id: Server ID to update
            name: New display name (if provided)
            url: New URL (if provided)
            description: New description (if provided)
            is_default: New default status (if provided)
            
        Returns:
            The updated DeploymentServer
            
        Raises:
            KeyError: If server_id not found
        """
        if server_id not in self._servers:
            raise KeyError(f"Server not found: {server_id}")
        
        server = self._servers[server_id]
        
        if name is not None:
            server.name = name
        if url is not None:
            server.url = url.rstrip('/')
        if description is not None:
            server.description = description
        if is_default is not None:
            if is_default:
                # Unset other defaults
                for s in self._servers.values():
                    s.is_default = False
            server.is_default = is_default
        
        self._save_servers()
        return server
    
    def remove_server(self, server_id: str):
        """Remove a deployment server."""
        if server_id in self._servers:
            del self._servers[server_id]
            self._save_servers()
            logger.info(f"Removed deployment server: {server_id}")
    
    # =========================================================================
    # Server Health & Info
    # =========================================================================
    
    def check_server_health(self, server_id: str) -> ServerHealthResponse:
        """
        Check the health of a deployment server.
        
        Args:
            server_id: Server ID to check
            
        Returns:
            ServerHealthResponse with health status and info
        """
        if not REQUESTS_AVAILABLE:
            return ServerHealthResponse(
                server_id=server_id,
                url="",
                is_healthy=False,
                status="error",
                error="requests library not installed"
            )
        
        server = self._servers.get(server_id)
        if not server:
            return ServerHealthResponse(
                server_id=server_id,
                url="",
                is_healthy=False,
                status="error",
                error="Server not found"
            )
        
        try:
            # Check /health endpoint
            health_resp = requests.get(f"{server.url}/health", timeout=5)
            if health_resp.status_code != 200:
                return ServerHealthResponse(
                    server_id=server_id,
                    url=server.url,
                    is_healthy=False,
                    status="unhealthy",
                    error=f"Health check failed: {health_resp.status_code}"
                )
            
            # Get server info
            info_resp = requests.get(f"{server.url}/info", timeout=5)
            info = info_resp.json() if info_resp.status_code == 200 else {}
            
            return ServerHealthResponse(
                server_id=server_id,
                url=server.url,
                is_healthy=True,
                status="healthy",
                plans_count=info.get('plans_count'),
                active_runs=info.get('active_runs'),
                completed_runs=info.get('completed_runs'),
                total_runs=info.get('total_runs'),
                available_models=info.get('llm_models'),
            )
        except requests.exceptions.ConnectionError:
            return ServerHealthResponse(
                server_id=server_id,
                url=server.url,
                is_healthy=False,
                status="unreachable",
                error="Connection refused - server may be offline"
            )
        except requests.exceptions.Timeout:
            return ServerHealthResponse(
                server_id=server_id,
                url=server.url,
                is_healthy=False,
                status="timeout",
                error="Connection timed out"
            )
        except Exception as e:
            return ServerHealthResponse(
                server_id=server_id,
                url=server.url,
                is_healthy=False,
                status="error",
                error=str(e)
            )
    
    # =========================================================================
    # Plan Packaging
    # =========================================================================
    
    def package_project(
        self, 
        project_id: Optional[str] = None,
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Package a project for deployment.
        
        Creates a zip file containing:
        - manifest.json: Plan metadata
        - concept_repo.json: Compiled concepts
        - inference_repo.json: Compiled inferences
        - provisions/: Prompts, paradigms, schemas
        
        Args:
            project_id: Project ID to package (uses current if not specified)
            
        Returns:
            Tuple of (path to zip file, manifest data)
            
        Raises:
            ValueError: If no project is open or project not found
            FileNotFoundError: If repository files don't exist
        """
        # Get project config
        if project_id:
            registered = project_service.get_project_by_id(project_id)
            if not registered:
                raise ValueError(f"Project not found: {project_id}")
            config, _ = project_service._config_service.open_project(
                Path(registered.directory),
                registered.config_file
            )
            project_dir = Path(registered.directory)
        else:
            if not project_service.is_project_open:
                raise ValueError("No project is currently open")
            config = project_service.current_config
            project_dir = project_service.current_project_path
        
        # Get absolute paths
        repos = config.repositories
        concepts_path = project_dir / repos.concepts
        inferences_path = project_dir / repos.inferences
        
        if not concepts_path.exists():
            raise FileNotFoundError(f"Concepts file not found: {concepts_path}")
        if not inferences_path.exists():
            raise FileNotFoundError(f"Inferences file not found: {inferences_path}")
        
        # Analyze concepts for inputs/outputs
        inputs = {}
        outputs = {}
        try:
            with open(concepts_path, 'r', encoding='utf-8') as f:
                concepts = json.load(f)
            for c in concepts:
                if c.get('is_ground_concept'):
                    inputs[c['concept_name']] = {
                        "type": "any",
                        "required": True,
                        "description": c.get('natural_name', c['concept_name'])
                    }
                if c.get('is_final_concept'):
                    outputs[c['concept_name']] = {
                        "type": "any",
                        "description": c.get('natural_name', c['concept_name'])
                    }
        except Exception as e:
            logger.warning(f"Failed to analyze concepts: {e}")
        
        # Create manifest
        manifest = {
            "name": config.name or config.id,
            "version": "1.0.0",
            "description": config.description,
            "entry": {
                "concepts": "concept_repo.json",
                "inferences": "inference_repo.json"
            },
            "inputs": inputs,
            "outputs": outputs,
            "default_agent": config.execution.llm_model,
        }
        
        # Create temp directory for packaging
        temp_dir = Path(tempfile.mkdtemp(prefix="normcode_deploy_"))
        package_dir = temp_dir / config.id
        package_dir.mkdir(parents=True)
        
        try:
            # Copy concept and inference repos
            shutil.copy2(concepts_path, package_dir / "concept_repo.json")
            shutil.copy2(inferences_path, package_dir / "inference_repo.json")
            
            # Write manifest
            with open(package_dir / "manifest.json", 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            
            # Copy provisions (paradigms, prompts, schemas, scripts, data)
            provisions_dir = package_dir / "provisions"
            provisions_dir.mkdir()
            
            # Find the provisions root directory
            # The paradigm_dir is usually something like "provision/paradigm" or "provisions/paradigms"
            # We want to copy the entire parent directory
            provisions_root = None
            if config.execution.paradigm_dir:
                paradigm_path = project_dir / config.execution.paradigm_dir
                if paradigm_path.exists():
                    # The parent of paradigm dir is the provisions root
                    provisions_root = paradigm_path.parent
                    logger.info(f"Found provisions root: {provisions_root}")
            
            if provisions_root and provisions_root.exists() and provisions_root != project_dir:
                # Copy all subdirectories from the provisions root
                for subdir in provisions_root.iterdir():
                    if subdir.is_dir() and not subdir.name.startswith('__'):
                        dest_name = subdir.name
                        # Normalize directory names (paradigm -> paradigms)
                        if dest_name == "paradigm":
                            dest_name = "paradigms"
                        dest_path = provisions_dir / dest_name
                        logger.info(f"Copying provision: {subdir.name} -> {dest_name}")
                        shutil.copytree(subdir, dest_path, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                    elif subdir.is_file():
                        # Copy files like manifest.json
                        shutil.copy2(subdir, provisions_dir / subdir.name)
            else:
                # Fallback: Copy paradigm directory if it exists
                if config.execution.paradigm_dir:
                    paradigm_path = project_dir / config.execution.paradigm_dir
                    if paradigm_path.exists():
                        paradigms_dest = provisions_dir / "paradigms"
                        shutil.copytree(paradigm_path, paradigms_dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                
                # Look for common provision directories at project level
                for subdir in ["prompts", "schemas", "scripts", "data", "provision", "provisions"]:
                    src_path = project_dir / subdir
                    if src_path.exists():
                        if subdir in ["provision", "provisions"]:
                            # Copy contents of provision(s) directory
                            for item in src_path.iterdir():
                                if item.is_dir() and not item.name.startswith('__'):
                                    dest_name = item.name
                                    if dest_name == "paradigm":
                                        dest_name = "paradigms"
                                    shutil.copytree(item, provisions_dir / dest_name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                                elif item.is_file():
                                    shutil.copy2(item, provisions_dir / item.name)
                        else:
                            shutil.copytree(src_path, provisions_dir / subdir, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            
            # Update manifest with provisions paths for tools
            manifest["provisions"] = {
                "paradigms": "provisions/paradigms" if (provisions_dir / "paradigms").exists() else None,
                "prompts": "provisions/prompts" if (provisions_dir / "prompts").exists() else None,
                "scripts": "provisions/scripts" if (provisions_dir / "scripts").exists() else None,
                "data": "provisions/data" if (provisions_dir / "data").exists() else None,
            }
            
            # Add language variant directories (e.g., prompts_chinese, scripts_chinese)
            for variant_dir in provisions_dir.iterdir():
                if variant_dir.is_dir():
                    name = variant_dir.name
                    if name.startswith('prompts_') or name.startswith('scripts_'):
                        manifest["provisions"][name] = f"provisions/{name}"
            
            # Remove None values
            manifest["provisions"] = {k: v for k, v in manifest["provisions"].items() if v is not None}
            
            # Re-write manifest with provisions info
            with open(package_dir / "manifest.json", 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            # Create zip file
            zip_path = temp_dir / f"{config.id}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file_path in package_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(package_dir)
                        zf.write(file_path, arcname)
            
            logger.info(f"Packaged project '{config.name}' to {zip_path}")
            return zip_path, manifest
            
        except Exception as e:
            # Cleanup on error
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise
    
    # =========================================================================
    # Deployment
    # =========================================================================
    
    def deploy_project(
        self,
        server_id: str,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Deploy a project to a remote server.
        
        Args:
            server_id: Target server ID
            project_id: Project ID to deploy (uses current if not specified)
            
        Returns:
            Deployment result with plan_id, status, etc.
            
        Raises:
            ValueError: If server not found or project invalid
            ConnectionError: If server is unreachable
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required for deployment")
        
        server = self._servers.get(server_id)
        if not server:
            raise ValueError(f"Server not found: {server_id}")
        
        # Package the project
        zip_path, manifest = self.package_project(project_id)
        
        try:
            # Upload to server - use deploy-file endpoint which accepts raw bytes
            with open(zip_path, 'rb') as f:
                zip_content = f.read()
            
            # Try the file upload endpoint
            response = requests.post(
                f"{server.url}/api/plans/deploy-file",
                files={'plan': (zip_path.name, zip_content, 'application/zip')},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Deployed '{manifest['name']}' to {server.name}")
                return {
                    "success": True,
                    "server_id": server_id,
                    "server_name": server.name,
                    "plan_id": result.get('plan_id', manifest['name']),
                    "plan_name": result.get('plan_name', manifest['name']),
                    "message": f"Successfully deployed to {server.name}",
                    "deployed_at": datetime.now().isoformat(),
                }
            else:
                error = response.text
                return {
                    "success": False,
                    "server_id": server_id,
                    "server_name": server.name,
                    "plan_id": manifest['name'],
                    "plan_name": manifest['name'],
                    "message": f"Deployment failed: {error}",
                }
        finally:
            # Cleanup temp files
            if zip_path.parent.exists():
                shutil.rmtree(zip_path.parent, ignore_errors=True)
    
    # =========================================================================
    # Remote Plans & Runs
    # =========================================================================
    
    def list_remote_plans(self, server_id: str) -> List[RemotePlan]:
        """List plans deployed on a remote server."""
        if not REQUESTS_AVAILABLE:
            return []
        
        server = self._servers.get(server_id)
        if not server:
            return []
        
        try:
            response = requests.get(f"{server.url}/api/plans", timeout=10)
            if response.status_code == 200:
                plans_data = response.json()
                return [RemotePlan(**p) for p in plans_data]
        except Exception as e:
            logger.warning(f"Failed to list plans from {server.name}: {e}")
        
        return []
    
    def start_remote_run(
        self,
        server_id: str,
        plan_id: str,
        llm_model: Optional[str] = None,
        ground_inputs: Optional[Dict[str, Any]] = None,
    ) -> RemoteRunStatus:
        """
        Start a run on a remote server.
        
        Args:
            server_id: Target server ID
            plan_id: Plan ID to run
            llm_model: LLM model to use (optional)
            ground_inputs: Input values for ground concepts (optional)
            
        Returns:
            RemoteRunStatus with run_id and initial status
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required")
        
        server = self._servers.get(server_id)
        if not server:
            raise ValueError(f"Server not found: {server_id}")
        
        payload = {
            "plan_id": plan_id,
        }
        if llm_model:
            payload["llm_model"] = llm_model
        if ground_inputs:
            payload["ground_inputs"] = ground_inputs
        
        response = requests.post(
            f"{server.url}/api/runs",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse progress if available
            progress = None
            if data.get('progress'):
                progress = RunProgress(
                    completed_count=data['progress'].get('completed_count', 0),
                    total_count=data['progress'].get('total_count', 0),
                    cycle_count=data['progress'].get('cycle_count', 0),
                    current_inference=data['progress'].get('current_inference'),
                )
            
            return RemoteRunStatus(
                run_id=data['run_id'],
                plan_id=data['plan_id'],
                server_id=server_id,
                status=data['status'],
                started_at=data.get('started_at'),
                progress=progress,
            )
        else:
            raise RuntimeError(f"Failed to start run: {response.text}")
    
    def get_remote_run_status(self, server_id: str, run_id: str) -> RemoteRunStatus:
        """Get status of a remote run."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required")
        
        server = self._servers.get(server_id)
        if not server:
            raise ValueError(f"Server not found: {server_id}")
        
        response = requests.get(f"{server.url}/api/runs/{run_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse progress if available
            progress = None
            if data.get('progress'):
                progress = RunProgress(
                    completed_count=data['progress'].get('completed_count', 0),
                    total_count=data['progress'].get('total_count', 0),
                    cycle_count=data['progress'].get('cycle_count', 0),
                    current_inference=data['progress'].get('current_inference'),
                )
            
            return RemoteRunStatus(
                run_id=data['run_id'],
                plan_id=data['plan_id'],
                server_id=server_id,
                status=data['status'],
                started_at=data.get('started_at'),
                completed_at=data.get('completed_at'),
                progress=progress,
                error=data.get('error'),
            )
        else:
            raise RuntimeError(f"Failed to get run status: {response.text}")
    
    def get_remote_run_result(self, server_id: str, run_id: str) -> Dict[str, Any]:
        """Get result of a completed remote run."""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required")
        
        server = self._servers.get(server_id)
        if not server:
            raise ValueError(f"Server not found: {server_id}")
        
        response = requests.get(f"{server.url}/api/runs/{run_id}/result", timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise RuntimeError(f"Failed to get run result: {response.text}")
    
    # =========================================================================
    # Server Building
    # =========================================================================
    
    def _write_text_utf8(self, path: Path, content: str):
        """Write text to file with UTF-8 encoding (Windows compatible)."""
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def _copy_directory(self, src: Path, dst: Path, exclude_patterns: list = None):
        """Copy a directory, excluding certain patterns."""
        exclude_patterns = exclude_patterns or []
        
        def should_exclude(path: Path) -> bool:
            name = path.name
            for pattern in exclude_patterns:
                if pattern in str(path) or name == pattern:
                    return True
            return False
        
        if dst.exists():
            shutil.rmtree(dst)
        
        def copy_tree(src_dir: Path, dst_dir: Path):
            dst_dir.mkdir(parents=True, exist_ok=True)
            for item in src_dir.iterdir():
                if should_exclude(item):
                    continue
                dst_item = dst_dir / item.name
                if item.is_dir():
                    copy_tree(item, dst_item)
                else:
                    shutil.copy2(item, dst_item)
        
        copy_tree(src, dst)
    
    def _create_requirements(self, output_dir: Path):
        """Create requirements.txt with necessary dependencies."""
        requirements = """# NormCode Deployment Server Requirements
# Generated by Canvas App

# Web framework
fastapi>=0.100.0
uvicorn>=0.22.0
python-multipart>=0.0.6

# LLM providers
openai>=1.0.0
dashscope>=1.14.0
anthropic>=0.18.0

# Utilities
pyyaml>=6.0
pydantic>=2.0.0
numpy>=1.24.0
"""
        self._write_text_utf8(output_dir / "requirements.txt", requirements)
    
    def _create_start_script(self, output_dir: Path):
        """Create a simple start script."""
        script = '''#!/usr/bin/env python3
"""
Start the NormCode Deployment Server.

Usage:
    python start_server.py
    python start_server.py --port 9000
    python start_server.py --host 127.0.0.1 --port 8080
"""

import sys
import os
from pathlib import Path

# Add current directory to path
SERVER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SERVER_DIR))

# Set default data directories
os.environ.setdefault("NORMCODE_PLANS_DIR", str(SERVER_DIR / "data" / "plans"))
os.environ.setdefault("NORMCODE_RUNS_DIR", str(SERVER_DIR / "data" / "runs"))

# Import and run
from server import main

if __name__ == "__main__":
    main()
'''
        start_script = output_dir / "start_server.py"
        self._write_text_utf8(start_script, script)
    
    def _create_readme(self, output_dir: Path):
        """Create README with usage instructions."""
        readme = f'''# NormCode Deployment Server

A self-contained server for executing NormCode plans.

Built: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure LLM settings (optional):
   Edit `data/config/settings.yaml` with your API keys.

3. Start the server:
   ```bash
   python start_server.py
   ```
   Or with options:
   ```bash
   python start_server.py --port 9000 --host 0.0.0.0
   ```

4. Access the API:
   - Health check: http://localhost:8080/health
   - API docs: http://localhost:8080/docs
   - Server info: http://localhost:8080/info

## Directory Structure

```
normcode-server/
├── start_server.py     # Start script
├── server.py           # Main server code
├── runner.py           # Plan execution
├── tools/              # Deployment tools
├── infra/              # Core NormCode library
├── mock_users/         # Test clients
│   ├── client.py       # CLI test client
│   └── client_gui.py   # GUI test client
├── data/
│   ├── plans/          # Deploy plans here
│   ├── runs/           # Run data (auto-created)
│   └── config/
│       └── settings.yaml  # LLM configuration
└── requirements.txt
```

## Deploying Plans

Use the Canvas App to deploy plans, or copy plan folders directly to `data/plans/`.

## API Endpoints

- `GET /health` - Health check
- `GET /info` - Server information
- `GET /api/plans` - List deployed plans
- `POST /api/plans/deploy-file` - Deploy a plan (zip upload)
- `POST /api/runs` - Start a new run
- `GET /api/runs/{{run_id}}` - Get run status
'''
        self._write_text_utf8(output_dir / "README.md", readme)
    
    def _create_default_settings(self, output_dir: Path):
        """Create default LLM settings file."""
        settings = '''# NormCode LLM Settings
# Configure your LLM providers here

# Default base URL (for DashScope/Qwen)
BASE_URL: https://dashscope.aliyuncs.com/compatible-mode/v1

# Qwen models (via DashScope)
qwen-plus:
  model: qwen-plus
  api_key: YOUR_DASHSCOPE_API_KEY_HERE

qwen-turbo:
  model: qwen-turbo
  api_key: YOUR_DASHSCOPE_API_KEY_HERE

# Demo mode (no API calls, returns mock responses)
demo:
  model: demo
  api_key: mock
'''
        config_dir = output_dir / "data" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        self._write_text_utf8(config_dir / "settings.yaml", settings)
    
    def build_server(
        self,
        output_dir: Optional[Path] = None,
        include_test_plans: bool = False,
        create_zip: bool = True,
    ) -> BuildServerResponse:
        """
        Build a self-contained deployment server package.
        
        This creates a standalone server that can be deployed anywhere
        to run NormCode plans.
        
        Args:
            output_dir: Output directory (default: deployment/dist/normcode-server)
            include_test_plans: Include test plans in the build
            create_zip: Create a zip archive of the server
            
        Returns:
            BuildServerResponse with build details
        """
        # Find the deployment server source directory
        # We're in canvas_app/backend/services/deployment_service.py
        # The deployment server source is at custom_server2/ from project root
        canvas_app_dir = Path(__file__).resolve().parents[2]
        project_root = canvas_app_dir.parent
        
        # Use custom_server2 as the primary source (the actual working deployment server)
        custom_server_dir = project_root / "custom_server2"
        
        # Fallback to direct_infra_experiment/deployment for legacy support
        legacy_deployment_dir = project_root / "direct_infra_experiment" / "deployment"
        
        # Determine which source to use
        if custom_server_dir.exists():
            server_source_dir = custom_server_dir
            tools_dir = custom_server_dir / "tools"
            mock_users_dir = custom_server_dir / "mock_users"
        elif legacy_deployment_dir.exists():
            server_source_dir = legacy_deployment_dir / "deploy_operators"
            tools_dir = legacy_deployment_dir / "tools"
            mock_users_dir = legacy_deployment_dir / "mock_users"
        else:
            raise FileNotFoundError("No deployment server source found (custom_server2 or deployment)")
        
        infra_dir = project_root / "infra"
        
        # Set default output directory
        if output_dir is None:
            output_dir = project_root / "deployment_builds" / "normcode-server"
        else:
            output_dir = Path(output_dir).resolve()
        
        logger.info(f"Building NormCode Deployment Server to {output_dir}")
        files_included = []
        
        try:
            # Clean output directory
            if output_dir.exists():
                shutil.rmtree(output_dir)
            output_dir.mkdir(parents=True)
            
            # 1. Copy deploy_operators (server.py, runner.py)
            if deploy_operators_dir.exists():
                for py_file in deploy_operators_dir.glob("*.py"):
                    if py_file.name != "__init__.py":
                        shutil.copy2(py_file, output_dir / py_file.name)
                        files_included.append(py_file.name)
                
                # Copy settings.yaml if exists
                settings_src = deploy_operators_dir / "settings.yaml"
                if settings_src.exists():
                    config_dir = output_dir / "data" / "config"
                    config_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(settings_src, config_dir / "settings.yaml")
                else:
                    self._create_default_settings(output_dir)
            else:
                raise FileNotFoundError(f"deploy_operators directory not found: {deploy_operators_dir}")
            
            # 2. Copy tools directory
            if tools_dir.exists():
                self._copy_directory(
                    tools_dir,
                    output_dir / "tools",
                    exclude_patterns=["__pycache__", ".pyc", "__init__.py"]
                )
                self._write_text_utf8(output_dir / "tools" / "__init__.py", "# Deployment tools\n")
                files_included.append("tools/")
            
            # 3. Copy infra directory
            if infra_dir.exists():
                self._copy_directory(
                    infra_dir,
                    output_dir / "infra",
                    exclude_patterns=["__pycache__", ".pyc", "*.egg-info", ".pytest_cache"]
                )
                files_included.append("infra/")
            
            # 4. Copy mock_users for testing
            if mock_users_dir.exists():
                self._copy_directory(
                    mock_users_dir,
                    output_dir / "mock_users",
                    exclude_patterns=["__pycache__", ".pyc"]
                )
                self._write_text_utf8(output_dir / "mock_users" / "__init__.py", "# Mock user clients\n")
                files_included.append("mock_users/")
            
            # 5. Create data directories
            (output_dir / "data" / "plans").mkdir(parents=True, exist_ok=True)
            (output_dir / "data" / "runs").mkdir(parents=True, exist_ok=True)
            files_included.append("data/plans/")
            files_included.append("data/runs/")
            
            # 6. Include test plans if requested
            if include_test_plans:
                test_plans_src = deployment_dir / "test_ncs" / "pre-deployment"
                if test_plans_src.exists():
                    for plan_dir in test_plans_src.iterdir():
                        if plan_dir.is_dir() and (plan_dir / "manifest.json").exists():
                            self._copy_directory(
                                plan_dir,
                                output_dir / "data" / "plans" / plan_dir.name,
                                exclude_patterns=["__pycache__", ".pyc", "runs", "logs"]
                            )
                            files_included.append(f"data/plans/{plan_dir.name}/")
            
            # 7. Create requirements.txt
            self._create_requirements(output_dir)
            files_included.append("requirements.txt")
            
            # 8. Create start script
            self._create_start_script(output_dir)
            files_included.append("start_server.py")
            
            # 9. Create README
            self._create_readme(output_dir)
            files_included.append("README.md")
            
            # 10. Create zip if requested
            zip_path = None
            if create_zip:
                zip_path = output_dir.parent / f"{output_dir.name}.zip"
                shutil.make_archive(
                    str(output_dir),
                    'zip',
                    output_dir.parent,
                    output_dir.name
                )
                zip_path = str(zip_path)
            
            logger.info(f"Build complete: {output_dir}")
            
            return BuildServerResponse(
                success=True,
                output_dir=str(output_dir),
                zip_path=zip_path,
                message=f"Server built successfully at {output_dir}",
                server_name=output_dir.name,
                files_included=files_included,
            )
            
        except Exception as e:
            logger.exception(f"Failed to build server: {e}")
            return BuildServerResponse(
                success=False,
                output_dir=str(output_dir),
                message=f"Build failed: {str(e)}",
                files_included=files_included,
            )


# Global singleton
deployment_service = DeploymentService()

