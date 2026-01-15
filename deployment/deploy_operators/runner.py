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

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Deployment tools directory
DEPLOYMENT_DIR = Path(__file__).resolve().parent
if str(DEPLOYMENT_DIR) not in sys.path:
    sys.path.insert(0, str(DEPLOYMENT_DIR))


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
        self.llm_model = exec_config.get('llm_model', 'demo')
        self.max_cycles = exec_config.get('max_cycles', 100)
        self.db_path = self._resolve_path(exec_config.get('db_path')) or (self.project_dir / 'orchestration.db')
        self.base_dir = self._resolve_path(exec_config.get('base_dir')) or self.project_dir
        self.paradigm_dir = self._resolve_path(exec_config.get('paradigm_dir'))
        
        self.breakpoints = self.raw.get('breakpoints', [])
    
    def _load_manifest_format(self):
        """Load from manifest.json (deployment package) format"""
        self.id = self.raw.get('name', str(uuid.uuid4())[:8])
        self.name = self.raw.get('name', 'unnamed')
        self.description = self.raw.get('description')
        
        entry = self.raw.get('entry', {})
        self.concept_repo_path = self._resolve_path(entry.get('concepts'))
        self.inference_repo_path = self._resolve_path(entry.get('inferences'))
        
        self.llm_model = self.raw.get('default_agent', 'demo')
        self.max_cycles = 100
        self.db_path = self.project_dir / 'orchestration.db'
        self.base_dir = self.project_dir
        self.paradigm_dir = self.project_dir / 'provisions' / 'paradigms'
        
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
    
    # Settings path for LLM - check both deployment/settings.yaml and deployment/tools/settings.yaml
    settings_path = DEPLOYMENT_DIR / "settings.yaml"
    if not settings_path.exists():
        settings_path = DEPLOYMENT_DIR / "tools" / "settings.yaml"
    
    logging.info(f"  LLM settings: {settings_path}")
    
    # Create deployment tools
    llm = DeploymentLLMTool(
        model_name=llm_name,
        settings_path=str(settings_path) if settings_path.exists() else None,
    )
    
    file_system = DeploymentFileSystemTool(
        base_dir=str(config.base_dir),
    )
    
    prompt_dir = config.paradigm_dir.parent / "prompts" if config.paradigm_dir else config.project_dir / "prompts"
    prompt_tool = DeploymentPromptTool(
        base_dir=str(prompt_dir) if prompt_dir.exists() else None,
    )
    
    python_interpreter = DeploymentPythonInterpreterTool()
    
    formatter = DeploymentFormatterTool()
    
    composition = DeploymentCompositionTool()
    
    user_input = DeploymentUserInputTool(
        interactive=True,  # CLI mode
    )
    
    # Create body with deployment tools
    # Body accepts tool overrides
    body = Body(
        llm_name=llm_name,
        base_dir=str(config.base_dir),
        new_user_input_tool=True,
        paradigm_tool=paradigm_tool
    )
    
    # Override with deployment tools
    # Note: The Body may use these if it supports tool injection
    # Otherwise, the tools are available for paradigm execution
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

