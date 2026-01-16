import sys
from pathlib import Path

# Add project root to path (go up 4 levels: gold -> iteration_6 -> nc_ai_planning_ex -> direct_infra_experiment -> normCode)
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from infra._orchest._repo import ConceptRepo, InferenceRepo
from infra._orchest._orchestrator import Orchestrator
from infra._agent._body import Body
from infra._loggers.utils import setup_orchestrator_logging
from infra._core._reference import set_dev_mode
import logging
import os
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PARADIGM_DIR = SCRIPT_DIR / 'provision' / 'paradigm'

class CustomParadigmTool:
    """Custom paradigm tool that loads from local provision/paradigm directory."""
    
    def __init__(self, paradigm_dir: Path):
        self.paradigm_dir = paradigm_dir
        # Import the Paradigm class from the local provision/paradigm directory
        import importlib.util
        spec = importlib.util.spec_from_file_location("_paradigm", paradigm_dir / "_paradigm.py")
        paradigm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(paradigm_module)
        self._Paradigm = paradigm_module.Paradigm
        # Override PARADIGMS_DIR in the module
        paradigm_module.PARADIGMS_DIR = paradigm_dir
        
    def load(self, paradigm_name: str):
        """Load a paradigm from the local directory."""
        return self._Paradigm.load(paradigm_name)
    
    def list_manifest(self) -> str:
        """List all available paradigms in the local directory."""
        manifest = []
        for filename in os.listdir(self.paradigm_dir):
            if filename.endswith(".json"):
                name = filename[:-5]
                try:
                    with open(self.paradigm_dir / filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata = data.get('metadata', {})
                        desc = metadata.get('description', 'No description provided.')
                        manifest.append(f"<paradigm name=\"{name}\">\n    <description>{desc}</description>\n</paradigm>")
                except Exception as e:
                    manifest.append(f"<error paradigm=\"{name}\">{str(e)}</error>")
        return "\n\n".join(manifest)

def create_repositories_from_files():
    with open(SCRIPT_DIR / 'repos/concept_repo.json', 'r', encoding='utf-8') as f:
        concept_data = json.load(f)
    concept_repo = ConceptRepo.from_json_list(concept_data)

    with open(SCRIPT_DIR / 'repos/inference_repo.json', 'r', encoding='utf-8') as f:
        inference_data = json.load(f)
    inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)
    
    return concept_repo, inference_repo

if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Gold Investment Decision System Executor')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--run-id', type=str, help='Specific run ID to resume (default: latest)')
    parser.add_argument('--llm', type=str, default='qwen-plus', help='LLM model name')
    parser.add_argument('--max-cycles', type=int, default=300, help='Maximum execution cycles')
    parser.add_argument('--mode', choices=['PATCH', 'OVERWRITE', 'FILL_GAPS'], 
                       default='PATCH', help='Checkpoint reconciliation mode')
    parser.add_argument('--dev-mode', action='store_true', 
                       help='Enable dev mode: raise exceptions instead of converting to skip values')
    args = parser.parse_args()
    
    # 1. Prepare file system
    (SCRIPT_DIR / "next_iteration").mkdir(exist_ok=True)

    # 2. Setup logging
    log_filename = setup_orchestrator_logging(__file__)
    if args.resume:
        logging.info(f"=== Resuming Gold Investment Decision System (Run: {args.run_id or 'latest'}) ===")
    else:
        logging.info("=== Starting Gold Investment Decision System Execution ===")
    
    # 2.5. Enable dev mode if requested
    if args.dev_mode:
        set_dev_mode(True)
        logging.warning("=" * 60)
        logging.warning("DEV MODE ENABLED: Exceptions will be raised instead of skip values")
        logging.warning("=" * 60)

    # 3. Build repositories from the generated JSON files
    concept_repo, inference_repo = create_repositories_from_files()

    # 4. Create custom paradigm tool for local paradigm directory
    logging.info(f"Using custom paradigm directory: {PARADIGM_DIR}")
    custom_paradigm_tool = CustomParadigmTool(PARADIGM_DIR)
    
    # List available paradigms
    logging.info("Available paradigms:")
    for line in custom_paradigm_tool.list_manifest().split('\n\n'):
        if line.strip():
            logging.info(f"  {line.split('<description>')[1].split('</description>')[0] if '<description>' in line else line}")

    # 5. Construct a Body with custom paradigm tool
    body = Body(
        llm_name=args.llm, 
        base_dir=SCRIPT_DIR, 
        new_user_input_tool=True,
        paradigm_tool=custom_paradigm_tool
    )

    # 6. Database path for checkpointing
    db_path = SCRIPT_DIR / "orchestration.db"
    
    # 7. Enable dev mode for Reference operations (errors will raise instead of becoming @#SKIP#@)
    logging.info("Enabling Reference dev_mode for debugging")
    set_dev_mode(True)
    
    # 8. Construct and run the orchestrator
    start_time = datetime.now()
    
    if args.resume:
        # Resume from checkpoint
        logging.info(f"Loading checkpoint from: {db_path}")
        orchestrator = Orchestrator.load_checkpoint(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            db_path=str(db_path),
            body=body,
            max_cycles=args.max_cycles,
            run_id=args.run_id,
            mode=args.mode,
            validate_compatibility=True
        )
        logging.info(f"Resumed run: {orchestrator.run_id}")
    else:
        # Fresh execution with checkpointing
        orchestrator = Orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            body=body,
            max_cycles=args.max_cycles,
            db_path=str(db_path)
        )
        logging.info(f"Started fresh run: {orchestrator.run_id}")
        logging.info(f"Checkpointing to: {db_path}")
    
    # Run orchestration
    final_concepts = orchestrator.run()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # 9. Inspect and log final concepts
    logging.info("=" * 60)
    logging.info(f"Execution completed in {duration:.2f}s")
    logging.info("=" * 60)
    logging.info("--- Final concepts: ---")
    
    completed = 0
    for final_concept_entry in final_concepts:
        if final_concept_entry and final_concept_entry.concept.reference:
            completed += 1
            ref = final_concept_entry.concept.reference
            ref_tensor = ref.tensor
            logging.info(f"✓ {final_concept_entry.concept_name}")
            logging.info(f"  Shape: {ref.shape}, Axes: {ref.axes}")
            data_str = str(ref_tensor)
            if len(data_str) > 200:
                data_str = data_str[:197] + "..."
            logging.info(f"  Data: {data_str}")
        else:
            logging.info(f"✗ {final_concept_entry.concept_name}: No reference")
    
    logging.info("=" * 60)
    logging.info(f"Completed: {completed}/{len(final_concepts)} concepts")
    logging.info(f"Run ID: {orchestrator.run_id}")
    logging.info(f"Database: {db_path}")
    logging.info(f"=== Gold Investment Decision System Complete - Log saved to {log_filename} ===")
