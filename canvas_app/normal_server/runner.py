#!/usr/bin/env python3
"""
NormCode Deployment Runner

A standalone CLI to execute NormCode plans without Canvas App.
Reads .normcode-canvas.json project configs or manifest.json from plan packages.

Uses deployment-local tools when available, falling back to infra tools.

Usage:
    python runner.py ./test_ncs/testproject.normcode-canvas.json
    python runner.py ./test_ncs/testproject.normcode-canvas.json --resume
    python runner.py ./test_ncs/testproject.normcode-canvas.json --llm gpt-4o
    python runner.py ./test_ncs/testproject.normcode-canvas.json --use-deployment-tools
"""

import sys
import json
import logging
import argparse
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Runner directory (where this file is located)
RUNNER_DIR = Path(__file__).resolve().parent

# Detect if running from built package or source
# Built package: runner.py is in root with infra/ and tools/ subdirs
# Source: runner.py is in deployment/deploy_operators/
IS_BUILT_PACKAGE = (RUNNER_DIR / "infra").exists() and (RUNNER_DIR / "tools").exists()

if IS_BUILT_PACKAGE:
    # Running from built package - add runner dir to path
    if str(RUNNER_DIR) not in sys.path:
        sys.path.insert(0, str(RUNNER_DIR))
    PROJECT_ROOT = RUNNER_DIR
    DEPLOYMENT_ROOT = RUNNER_DIR
    DEPLOYMENT_DIR = RUNNER_DIR
else:
    # Running from source - use traditional paths
    PROJECT_ROOT = RUNNER_DIR.parents[1]  # Go up to normCode root
    DEPLOYMENT_ROOT = RUNNER_DIR.parent   # deployment/
    DEPLOYMENT_DIR = RUNNER_DIR           # deploy_operators/
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    if str(DEPLOYMENT_ROOT) not in sys.path:
        sys.path.insert(0, str(DEPLOYMENT_ROOT))


class PlanConfig:
    """Configuration loaded from .normcode-canvas.json or manifest.json"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path.resolve()
        self.project_dir = self.config_path.parent
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.raw = json.load(f)
        
        # Determine format (canvas config vs deployment manifest)
        if 'repositories' in self.raw:
            self._load_canvas_format()
        elif 'entry' in self.raw:
            self._load_manifest_format()
        else:
            raise ValueError(f"Unknown config format: {config_path}")
    
    def _resolve_path(self, path_str: Optional[str]) -> Optional[Path]:
        """Resolve a path relative to project directory."""
        if not path_str:
            return None
        path = Path(path_str)
        if path.is_absolute():
            return path
        return (self.project_dir / path).resolve()
    
    def _load_canvas_format(self):
        """Load from .normcode-canvas.json format"""
        self.id = self.raw.get('id', str(uuid.uuid4())[:8])
        self.name = self.raw.get('name', 'unnamed')
        self.description = self.raw.get('description')
        
        repos = self.raw.get('repositories', {})
        self.concept_repo_path = self._resolve_path(repos.get('concepts'))
        self.inference_repo_path = self._resolve_path(repos.get('inferences'))
        
        exec_config = self.raw.get('execution', {})
        self.max_cycles = exec_config.get('max_cycles', 100)
        self.db_path = self._resolve_path(exec_config.get('db_path')) or (self.project_dir / 'orchestration.db')
        
        # Agent-centric: load llm_model, base_dir, paradigm_dir from agent config
        agent_config_ref = exec_config.get('agent_config')
        agent_data = self._load_agent_config(agent_config_ref)
        
        self.llm_model = agent_data.get('llm_model', 'qwen-plus')
        self.base_dir = self._resolve_path(agent_data.get('base_dir')) or self.project_dir
        self.paradigm_dir = self._resolve_path(agent_data.get('paradigm_dir'))
        
        # Infer prompts, scripts, data directories from paradigm_dir parent
        if self.paradigm_dir and self.paradigm_dir.exists():
            provisions_root = self.paradigm_dir.parent
            self.prompts_dir = provisions_root / 'prompts'
            self.scripts_dir = provisions_root / 'scripts'
            self.data_dir = provisions_root / 'data'
        else:
            self.prompts_dir = self.project_dir / 'prompts'
            self.scripts_dir = self.project_dir / 'scripts'
            self.data_dir = self.project_dir / 'data'
        
        self.breakpoints = self.raw.get('breakpoints', [])
    
    def _load_agent_config(self, agent_config_ref: Optional[str]) -> Dict[str, Any]:
        """
        Load LLM model, base_dir, and paradigm_dir from the agent config file.
        
        Supports both new tool-centric structure and legacy flat structure.
        """
        result = {
            'llm_model': 'qwen-plus',
            'base_dir': None,
            'paradigm_dir': None,
        }
        
        if not agent_config_ref:
            return result
        
        agent_config_path = self.project_dir / agent_config_ref
        if not agent_config_path.exists():
            return result
        
        try:
            with open(agent_config_path, 'r', encoding='utf-8') as f:
                agent_data = json.load(f)
            
            agents = agent_data.get('agents', [])
            default_agent_id = agent_data.get('default_agent', 'default')
            
            # Find default agent
            agent = None
            for a in agents:
                if a.get('id') == default_agent_id:
                    agent = a
                    break
            
            # Fallback to first agent
            if not agent and agents:
                agent = agents[0]
            
            if agent:
                # New tool-centric structure
                tools = agent.get('tools', {})
                
                # LLM model
                llm = tools.get('llm', {})
                if llm.get('model'):
                    result['llm_model'] = llm['model']
                elif agent.get('llm_model'):  # Legacy
                    result['llm_model'] = agent['llm_model']
                
                # Paradigm dir
                paradigm = tools.get('paradigm', {})
                if paradigm.get('dir'):
                    result['paradigm_dir'] = paradigm['dir']
                elif agent.get('paradigm_dir'):  # Legacy
                    result['paradigm_dir'] = agent['paradigm_dir']
                
                # Base dir (from file_system tool)
                file_system = tools.get('file_system', {})
                if file_system.get('base_dir'):
                    result['base_dir'] = file_system['base_dir']
                elif agent.get('base_dir'):  # Legacy
                    result['base_dir'] = agent['base_dir']
                    
        except Exception as e:
            logging.warning(f"Failed to load agent config {agent_config_ref}: {e}")
        
        return result
    
    def _load_manifest_format(self):
        """Load from manifest.json (deployment package) format"""
        import logging
        logging.info(f"[PlanConfig] Loading manifest format from: {self.config_path}")
        logging.info(f"[PlanConfig] project_dir: {self.project_dir}")
        
        self.id = self.raw.get('name', str(uuid.uuid4())[:8])
        self.name = self.raw.get('name', 'unnamed')
        self.description = self.raw.get('description')
        
        entry = self.raw.get('entry', {})
        self.concept_repo_path = self._resolve_path(entry.get('concepts'))
        self.inference_repo_path = self._resolve_path(entry.get('inferences'))
        
        self.llm_model = self.raw.get('default_agent', 'qwen-plus')
        self.max_cycles = 100
        self.db_path = self.project_dir / 'orchestration.db'
        self.base_dir = self.project_dir
        
        # Load provisions paths from manifest
        provisions = self.raw.get('provisions', {})
        logging.info(f"[PlanConfig] provisions from manifest: {provisions}")
        
        # Paradigm directory
        if provisions.get('paradigms'):
            self.paradigm_dir = self._resolve_path(provisions['paradigms'])
        else:
            self.paradigm_dir = self.project_dir / 'provisions' / 'paradigms'
        
        # Prompts directory
        if provisions.get('prompts'):
            self.prompts_dir = self._resolve_path(provisions['prompts'])
        else:
            self.prompts_dir = self.project_dir / 'provisions' / 'prompts'
        
        # Scripts directory
        if provisions.get('scripts'):
            self.scripts_dir = self._resolve_path(provisions['scripts'])
        else:
            self.scripts_dir = self.project_dir / 'provisions' / 'scripts'
        
        # Data directory
        if provisions.get('data'):
            self.data_dir = self._resolve_path(provisions['data'])
        else:
            self.data_dir = self.project_dir / 'provisions' / 'data'
        
        logging.info(f"[PlanConfig] base_dir: {self.base_dir}")
        logging.info(f"[PlanConfig] paradigm_dir: {self.paradigm_dir} (exists: {self.paradigm_dir.exists() if self.paradigm_dir else 'N/A'})")
        logging.info(f"[PlanConfig] prompts_dir: {self.prompts_dir} (exists: {self.prompts_dir.exists() if self.prompts_dir else 'N/A'})")
        logging.info(f"[PlanConfig] scripts_dir: {self.scripts_dir} (exists: {self.scripts_dir.exists() if self.scripts_dir else 'N/A'})")
        logging.info(f"[PlanConfig] data_dir: {self.data_dir} (exists: {self.data_dir.exists() if self.data_dir else 'N/A'})")
        
        self.breakpoints = []
    
    def __repr__(self):
        return f"PlanConfig(name={self.name}, concepts={self.concept_repo_path})"


class CustomParadigmTool:
    """Paradigm tool that loads from a custom directory."""
    
    def __init__(self, paradigm_dir: Path):
        self.paradigm_dir = paradigm_dir
        
        # Try to load custom _paradigm.py if it exists
        paradigm_py = paradigm_dir / "_paradigm.py"
        if paradigm_py.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("_paradigm", paradigm_py)
            paradigm_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(paradigm_module)
            self._Paradigm = paradigm_module.Paradigm
            paradigm_module.PARADIGMS_DIR = paradigm_dir
        else:
            # Fall back to infra's Paradigm
            from infra._agent._models._paradigms import Paradigm
            self._Paradigm = Paradigm
    
    def load(self, paradigm_name: str):
        """Load a paradigm by name."""
        # First try local directory
        local_path = self.paradigm_dir / f"{paradigm_name}.json"
        if local_path.exists():
            return self._Paradigm.load(paradigm_name)
        
        # Fall back to built-in paradigms
        from infra._agent._models._paradigms import Paradigm
        return Paradigm.load(paradigm_name)
    
    def list_manifest(self) -> str:
        """List all available paradigms."""
        import os
        manifest = []
        for filename in os.listdir(self.paradigm_dir):
            if filename.endswith(".json"):
                name = filename[:-5]
                try:
                    with open(self.paradigm_dir / filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata = data.get('metadata', {})
                        desc = metadata.get('description', 'No description')
                        manifest.append(f"  - {name}: {desc}")
                except Exception as e:
                    manifest.append(f"  - {name}: (error: {e})")
        return "\n".join(manifest) if manifest else "  (none)"


def setup_logging(log_dir: Path, run_id: str) -> str:
    """Setup logging to both console and file."""
    import io
    
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"run_{run_id[:8]}_{timestamp}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with UTF-8 support for Windows
    # Wrap stdout to handle Unicode properly on Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter('%(levelname)s | %(message)s'))
    root_logger.addHandler(console)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
    root_logger.addHandler(file_handler)
    
    return str(log_file)


def load_repositories(config: PlanConfig):
    """Load concept and inference repositories from config."""
    from infra._orchest._repo import ConceptRepo, InferenceRepo
    
    if not config.concept_repo_path or not config.concept_repo_path.exists():
        raise FileNotFoundError(f"Concept repository not found: {config.concept_repo_path}")
    
    if not config.inference_repo_path or not config.inference_repo_path.exists():
        raise FileNotFoundError(f"Inference repository not found: {config.inference_repo_path}")
    
    with open(config.concept_repo_path, 'r', encoding='utf-8') as f:
        concept_data = json.load(f)
    concept_repo = ConceptRepo.from_json_list(concept_data)
    
    with open(config.inference_repo_path, 'r', encoding='utf-8') as f:
        inference_data = json.load(f)
    inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)
    
    return concept_repo, inference_repo


def create_body(config: PlanConfig, llm_override: Optional[str] = None, use_deployment_tools: bool = False):
    """Create a Body instance from config."""
    from infra._agent._body import Body
    
    llm_name = llm_override or config.llm_model
    
    # Create paradigm tool if custom paradigm dir exists
    paradigm_tool = None
    if config.paradigm_dir and config.paradigm_dir.exists():
        paradigm_tool = CustomParadigmTool(config.paradigm_dir)
        logging.info(f"Using custom paradigms from: {config.paradigm_dir}")
    
    if use_deployment_tools:
        # Use deployment-local tools instead of infra defaults
        logging.info("Using deployment tools")
        body = create_body_with_deployment_tools(config, llm_name, paradigm_tool)
    else:
        # Use standard infra body
        body = Body(
            llm_name=llm_name,
            base_dir=str(config.base_dir),
            new_user_input_tool=True,
            paradigm_tool=paradigm_tool
        )
    
    return body


def create_body_with_deployment_tools(config: PlanConfig, llm_name: str, paradigm_tool=None):
    """Create a Body instance using deployment-local tools."""
    from infra._agent._body import Body
    
    # Import deployment tools
    from tools.llm_tool import DeploymentLLMTool
    from tools.file_system_tool import DeploymentFileSystemTool
    from tools.prompt_tool import DeploymentPromptTool
    from tools.python_interpreter_tool import DeploymentPythonInterpreterTool
    from tools.formatter_tool import DeploymentFormatterTool
    from tools.composition_tool import DeploymentCompositionTool
    from tools.user_input_tool import DeploymentUserInputTool
    
    # Settings path for LLM - check multiple locations
    settings_path = None
    for candidate in [
        DEPLOYMENT_DIR / "data" / "config" / "settings.yaml",  # Built package
        DEPLOYMENT_DIR / "settings.yaml",                       # Same directory
        DEPLOYMENT_ROOT / "tools" / "settings.yaml",            # Source location
    ]:
        if candidate.exists():
            settings_path = candidate
            break
    
    logging.info(f"  LLM settings: {settings_path}")
    
    # Create deployment tools
    llm = DeploymentLLMTool(
        model_name=llm_name,
        settings_path=str(settings_path) if settings_path else None,
    )
    
    # File system tool - use base_dir but also configure data path
    logging.info(f"[Runner] Creating FileSystemTool with base_dir: {config.base_dir}")
    file_system = DeploymentFileSystemTool(
        base_dir=str(config.base_dir),
    )
    
    # Register provision paths with file system tool if it supports it
    if hasattr(file_system, 'register_path'):
        # Find the provisions root directory
        provisions_root = None
        
        logging.info(f"[Runner] config.data_dir = {getattr(config, 'data_dir', 'NOT SET')}")
        logging.info(f"[Runner] config.scripts_dir = {getattr(config, 'scripts_dir', 'NOT SET')}")
        logging.info(f"[Runner] config.prompts_dir = {getattr(config, 'prompts_dir', 'NOT SET')}")
        logging.info(f"[Runner] config.paradigm_dir = {getattr(config, 'paradigm_dir', 'NOT SET')}")
        logging.info(f"[Runner] config.project_dir = {getattr(config, 'project_dir', 'NOT SET')}")
        
        # Register individual provision directories
        if hasattr(config, 'data_dir') and config.data_dir and config.data_dir.exists():
            file_system.register_path('data', str(config.data_dir))
            logging.info(f"[Runner] Registered 'data' path: {config.data_dir}")
            provisions_root = config.data_dir.parent
        else:
            logging.warning(f"[Runner] data_dir not registered! data_dir={getattr(config, 'data_dir', None)}, exists={config.data_dir.exists() if hasattr(config, 'data_dir') and config.data_dir else 'N/A'}")
            
        if hasattr(config, 'scripts_dir') and config.scripts_dir and config.scripts_dir.exists():
            file_system.register_path('scripts', str(config.scripts_dir))
            logging.info(f"  Scripts dir: {config.scripts_dir}")
            provisions_root = config.scripts_dir.parent
            
            # Also register script variants (e.g., scripts_chinese)
            for variant_dir in provisions_root.iterdir():
                if variant_dir.is_dir() and variant_dir.name.startswith('scripts_'):
                    file_system.register_path(variant_dir.name, str(variant_dir))
                    logging.info(f"  Added script variant: {variant_dir.name}")
            
            # Also register data variants (e.g., data_chinese)
            for variant_dir in provisions_root.iterdir():
                if variant_dir.is_dir() and variant_dir.name.startswith('data_'):
                    file_system.register_path(variant_dir.name, str(variant_dir))
                    logging.info(f"  Added data variant: {variant_dir.name}")
        
        # Set the provisions base directory for resolving paths like 'provision/scripts/...'
        if provisions_root and hasattr(file_system, 'set_provisions_base'):
            file_system.set_provisions_base(str(provisions_root))
            logging.info(f"  Provisions base: {provisions_root}")
    
    # Prompts directory - use the explicitly set prompts_dir
    prompt_dir = getattr(config, 'prompts_dir', None)
    if not prompt_dir or not prompt_dir.exists():
        # Fallback: try paradigm_dir parent
        prompt_dir = config.paradigm_dir.parent / "prompts" if config.paradigm_dir else config.project_dir / "prompts"
    
    prompt_tool = DeploymentPromptTool(
        base_dir=str(prompt_dir) if prompt_dir and prompt_dir.exists() else None,
    )
    
    # Set project_dir for resolving provision paths like 'provision/prompts/file.md'
    if hasattr(prompt_tool, 'set_project_dir'):
        prompt_tool.set_project_dir(str(config.project_dir))
        logging.info(f"  Prompt project dir: {config.project_dir}")
    
    if prompt_dir and prompt_dir.exists():
        logging.info(f"  Prompts dir: {prompt_dir}")
        
        # Add language variant directories if they exist (e.g., prompts_chinese)
        provisions_root = prompt_dir.parent
        for variant_dir in provisions_root.iterdir():
            if variant_dir.is_dir() and variant_dir.name.startswith('prompts_'):
                prompt_tool.add_search_directory(str(variant_dir))
                logging.info(f"  Added prompt variant: {variant_dir.name}")
    
    python_interpreter = DeploymentPythonInterpreterTool()
    
    formatter = DeploymentFormatterTool()
    
    composition = DeploymentCompositionTool()
    
    user_input = DeploymentUserInputTool(
        interactive=True,  # CLI mode
    )
    
    # Create body with deployment tools
    body = Body(
        llm_name=llm_name,
        base_dir=str(config.base_dir),
        new_user_input_tool=True,
        paradigm_tool=paradigm_tool
    )
    
    # Replace body.llm with deployment LLM tool
    # This is critical - without this, Body uses its own infra LanguageModel
    body.llm = llm
    
    # Also override other tools for consistency
    body.file_system = file_system
    body.prompt_tool = prompt_tool
    body.prompt = prompt_tool  # backwards-compatible alias
    body.python_interpreter = python_interpreter
    body.formatter = formatter
    body.composition = composition
    body.user_input = user_input
    
    # Store references for debugging/introspection
    body._deployment_tools = {
        "llm": llm,
        "file_system": file_system,
        "prompt_tool": prompt_tool,
        "python_interpreter": python_interpreter,
        "formatter": formatter,
        "composition": composition,
        "user_input": user_input,
    }
    
    # Set body reference on python interpreter for script access
    python_interpreter.set_body(body)
    
    logging.info(f"  Deployment LLM: {llm_name} (mock={llm.is_mock_mode})")
    logging.info(f"  File system base: {config.base_dir}")
    
    return body


def run_plan(
    config: PlanConfig,
    resume: bool = False,
    run_id: Optional[str] = None,
    llm_override: Optional[str] = None,
    max_cycles_override: Optional[int] = None,
    mode: str = "PATCH",
    dev_mode: bool = False,
    use_deployment_tools: bool = False
) -> Dict[str, Any]:
    """
    Execute a NormCode plan.
    
    Returns:
        Dict with run_id, status, final_concepts, duration, etc.
    """
    from infra._orchest._orchestrator import Orchestrator
    from infra._core._reference import set_dev_mode
    
    # Setup
    max_cycles = max_cycles_override or config.max_cycles
    
    if dev_mode:
        set_dev_mode(True)
        logging.warning("DEV MODE: Exceptions will raise instead of becoming skip values")
    
    # Load repositories
    logging.info(f"Loading repositories for plan: {config.name}")
    concept_repo, inference_repo = load_repositories(config)
    logging.info(f"  Concepts: {len(concept_repo.get_all_concepts())} loaded")
    logging.info(f"  Inferences: {len(inference_repo.get_all_inferences())} loaded")
    
    # Create body
    body = create_body(config, llm_override, use_deployment_tools=use_deployment_tools)
    logging.info(f"  LLM: {llm_override or config.llm_model}")
    
    # Create or resume orchestrator
    start_time = datetime.now()
    
    if resume:
        logging.info(f"Resuming from checkpoint: {config.db_path}")
        orchestrator = Orchestrator.load_checkpoint(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            db_path=str(config.db_path),
            body=body,
            max_cycles=max_cycles,
            run_id=run_id,
            mode=mode,
            validate_compatibility=True
        )
        logging.info(f"Resumed run: {orchestrator.run_id}")
    else:
        orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            body=body,
            max_cycles=max_cycles,
            db_path=str(config.db_path)
        )
        logging.info(f"Started fresh run: {orchestrator.run_id}")
    
    # Execute
    logging.info("=" * 60)
    logging.info("Starting execution...")
    logging.info("=" * 60)
    
    final_concepts = orchestrator.run()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Collect results
    results = {
        "run_id": orchestrator.run_id,
        "plan_id": config.id,
        "plan_name": config.name,
        "status": "completed",
        "duration_seconds": duration,
        "final_concepts": [],
        "db_path": str(config.db_path)
    }
    
    logging.info("=" * 60)
    logging.info(f"Execution completed in {duration:.2f}s")
    logging.info("=" * 60)
    logging.info("Final Concepts:")
    
    completed = 0
    for fc in final_concepts:
        concept_result = {
            "name": fc.concept_name,
            "has_value": False,
            "shape": None,
            "preview": None
        }
        
        if fc and fc.concept and fc.concept.reference:
            completed += 1
            ref = fc.concept.reference
            concept_result["has_value"] = True
            concept_result["shape"] = list(ref.shape)
            concept_result["axes"] = ref.axes
            
            # Preview (truncated)
            data_str = str(ref.tensor)
            if len(data_str) > 200:
                data_str = data_str[:197] + "..."
            concept_result["preview"] = data_str
            
            logging.info(f"  ✓ {fc.concept_name}")
            logging.info(f"    Shape: {ref.shape}, Axes: {ref.axes}")
            logging.info(f"    Data: {data_str}")
        else:
            logging.info(f"  ✗ {fc.concept_name}: No value")
        
        results["final_concepts"].append(concept_result)
    
    results["completed_count"] = completed
    results["total_count"] = len(final_concepts)
    
    logging.info("=" * 60)
    logging.info(f"Completed: {completed}/{len(final_concepts)} concepts")
    logging.info(f"Run ID: {orchestrator.run_id}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="NormCode Deployment Runner - Execute plans without Canvas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python runner.py ./test_ncs/testproject.normcode-canvas.json
  python runner.py ./test_ncs/testproject.normcode-canvas.json --resume
  python runner.py ./test_ncs/testproject.normcode-canvas.json --llm gpt-4o --max-cycles 50
        """
    )
    
    parser.add_argument(
        'config',
        type=Path,
        help='Path to .normcode-canvas.json or manifest.json'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint'
    )
    parser.add_argument(
        '--run-id',
        type=str,
        help='Specific run ID to resume (default: latest)'
    )
    parser.add_argument(
        '--llm',
        type=str,
        help='Override LLM model (e.g., gpt-4o, qwen-plus, demo)'
    )
    parser.add_argument(
        '--max-cycles',
        type=int,
        help='Override maximum execution cycles'
    )
    parser.add_argument(
        '--mode',
        choices=['PATCH', 'OVERWRITE', 'FILL_GAPS'],
        default='PATCH',
        help='Checkpoint reconciliation mode (default: PATCH)'
    )
    parser.add_argument(
        '--dev-mode',
        action='store_true',
        help='Enable dev mode (raise exceptions instead of skip values)'
    )
    parser.add_argument(
        '--use-deployment-tools',
        action='store_true',
        help='Use deployment-local tools instead of infra defaults'
    )
    parser.add_argument(
        '--output-json',
        type=Path,
        help='Write results to JSON file'
    )
    
    args = parser.parse_args()
    
    # Validate config exists
    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    
    # Load config
    try:
        config = PlanConfig(args.config)
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Setup logging
    log_dir = config.project_dir / "logs"
    run_id = args.run_id or str(uuid.uuid4())
    log_file = setup_logging(log_dir, run_id)
    
    logging.info("=" * 60)
    logging.info("NormCode Deployment Runner")
    logging.info("=" * 60)
    logging.info(f"Config: {args.config}")
    logging.info(f"Plan: {config.name} ({config.id})")
    logging.info(f"Log file: {log_file}")
    
    # Run
    try:
        results = run_plan(
            config=config,
            resume=args.resume,
            run_id=args.run_id,
            llm_override=args.llm,
            max_cycles_override=args.max_cycles,
            mode=args.mode,
            dev_mode=args.dev_mode,
            use_deployment_tools=args.use_deployment_tools
        )
        
        # Output JSON if requested
        if args.output_json:
            with open(args.output_json, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logging.info(f"Results written to: {args.output_json}")
        
        logging.info("=" * 60)
        logging.info("Runner completed successfully")
        logging.info("=" * 60)
        
    except KeyboardInterrupt:
        logging.warning("Execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logging.exception(f"Execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

