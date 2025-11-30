#!/usr/bin/env python3
"""
NormCode Orchestrator - Command Line Interface

A command-line tool for running NormCode orchestrations without writing custom scripts.
Equivalent functionality to the Streamlit app, but for terminal users.

Usage:
    # Fresh run
    python cli_orchestrator.py run --concepts concepts.json --inferences inferences.json
    
    # With inputs
    python cli_orchestrator.py run --concepts concepts.json --inferences inferences.json --inputs inputs.json
    
    # Resume from checkpoint
    python cli_orchestrator.py resume --concepts concepts.json --inferences inferences.json --run-id <run-id>
    
    # Fork from checkpoint
    python cli_orchestrator.py fork --concepts concepts.json --inferences inferences.json --from-run <run-id> --new-run-id <new-id>
    
    # List runs
    python cli_orchestrator.py list-runs
    
    # List checkpoints
    python cli_orchestrator.py list-checkpoints --run-id <run-id>
    
    # Export checkpoint
    python cli_orchestrator.py export --run-id <run-id> --output checkpoint.json
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from infra import ConceptRepo, InferenceRepo, Orchestrator
from infra._orchest._db import OrchestratorDB
from infra._agent._body import Body


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )


def load_repositories(concepts_file: str, inferences_file: str, inputs_file: Optional[str] = None):
    """Load concept and inference repositories from JSON files."""
    print(f"Loading repositories...")
    
    # Load concepts
    with open(concepts_file, 'r', encoding='utf-8') as f:
        concept_data = json.load(f)
    concept_repo = ConceptRepo.from_json_list(concept_data)
    print(f"  ✓ Loaded {len(concept_repo._concept_map)} concepts from {concepts_file}")
    
    # Load and inject inputs if provided
    if inputs_file:
        with open(inputs_file, 'r', encoding='utf-8') as f:
            inputs_data = json.load(f)
        for concept_name, details in inputs_data.items():
            if isinstance(details, dict) and 'data' in details:
                data = details['data']
                axes = details.get('axes')
            else:
                data = details
                axes = None
            concept_repo.add_reference(concept_name, data, axis_names=axes)
        print(f"  ✓ Injected {len(inputs_data)} input concept(s) from {inputs_file}")
    
    # Load inferences
    with open(inferences_file, 'r', encoding='utf-8') as f:
        inference_data = json.load(f)
    inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)
    print(f"  ✓ Loaded {len(inference_repo.inferences)} inferences from {inferences_file}")
    
    return concept_repo, inference_repo


def run_fresh(args):
    """Execute a fresh orchestration run."""
    print("\n" + "="*60)
    print("FRESH RUN")
    print("="*60)
    
    # Load repositories
    concept_repo, inference_repo = load_repositories(
        args.concepts, args.inferences, args.inputs
    )
    
    # Initialize Body
    base_dir = args.base_dir or os.getcwd()
    body = Body(llm_name=args.llm, base_dir=base_dir)
    print(f"  ✓ Base directory: {base_dir}")
    print(f"  ✓ LLM model: {args.llm}")
    
    # Create orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        body=body,
        max_cycles=args.max_cycles,
        db_path=args.db_path
    )
    
    print(f"\n🆕 Started fresh run: {orchestrator.run_id}")
    print(f"Database: {args.db_path}")
    
    # Execute
    print("\n⏳ Running orchestration...")
    start_time = datetime.now()
    final_concepts = orchestrator.run()
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Display results
    print_results(orchestrator, final_concepts, duration)
    
    return orchestrator.run_id


def run_resume(args):
    """Resume execution from a checkpoint."""
    print("\n" + "="*60)
    print("RESUME FROM CHECKPOINT")
    print("="*60)
    
    # Load repositories
    concept_repo, inference_repo = load_repositories(
        args.concepts, args.inferences, args.inputs
    )
    
    # Initialize Body
    base_dir = args.base_dir or os.getcwd()
    body = Body(llm_name=args.llm, base_dir=base_dir)
    
    # Load from checkpoint
    mode = args.mode or "PATCH"
    print(f"  ✓ Resuming from run: {args.run_id or 'latest'}")
    print(f"  ✓ Reconciliation mode: {mode}")
    
    orchestrator = Orchestrator.load_checkpoint(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        db_path=args.db_path,
        body=body,
        max_cycles=args.max_cycles,
        run_id=args.run_id,
        mode=mode,
        validate_compatibility=True
    )
    
    print(f"\n♻️ Resumed run: {orchestrator.run_id}")
    
    # Execute
    print("\n⏳ Running orchestration...")
    start_time = datetime.now()
    final_concepts = orchestrator.run()
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Display results
    print_results(orchestrator, final_concepts, duration)
    
    return orchestrator.run_id


def run_fork(args):
    """Fork from one checkpoint to execute with a different repository."""
    print("\n" + "="*60)
    print("FORK FROM CHECKPOINT")
    print("="*60)
    
    # Load repositories (new/different repository)
    concept_repo, inference_repo = load_repositories(
        args.concepts, args.inferences, args.inputs
    )
    
    # Initialize Body
    base_dir = args.base_dir or os.getcwd()
    body = Body(llm_name=args.llm, base_dir=base_dir)
    
    # Determine new run ID
    import uuid
    new_run_id = args.new_run_id or f"fork-{uuid.uuid4().hex[:8]}"
    mode = args.mode or "OVERWRITE"
    
    print(f"  ✓ Forking from: {args.from_run or 'latest'}")
    print(f"  ✓ New run ID: {new_run_id}")
    print(f"  ✓ Reconciliation mode: {mode}")
    
    # Load from checkpoint with new repository
    orchestrator = Orchestrator.load_checkpoint(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        db_path=args.db_path,
        body=body,
        max_cycles=args.max_cycles,
        run_id=args.from_run,
        new_run_id=new_run_id,
        mode=mode,
        validate_compatibility=True
    )
    
    print(f"\n🔱 Forked to: {orchestrator.run_id}")
    print(f"State loaded from source, starting fresh execution history")
    
    # Execute
    print("\n⏳ Running orchestration...")
    start_time = datetime.now()
    final_concepts = orchestrator.run()
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Display results
    print_results(orchestrator, final_concepts, duration)
    
    return orchestrator.run_id


def list_runs(args):
    """List all available runs in the database."""
    print("\n" + "="*60)
    print("AVAILABLE RUNS")
    print("="*60)
    
    db = OrchestratorDB(args.db_path)
    runs = db.list_runs()
    
    if runs:
        for i, run in enumerate(runs, 1):
            print(f"\n{i}. Run ID: {run['run_id']}")
            print(f"   First Execution: {run['first_execution']}")
            print(f"   Last Execution: {run['last_execution']}")
            print(f"   Execution Count: {run['execution_count']}")
            print(f"   Max Cycle: {run['max_cycle']}")
    else:
        print("\nNo runs found in database.")
    
    print()


def list_checkpoints(args):
    """List all checkpoints for a specific run."""
    print("\n" + "="*60)
    print("AVAILABLE CHECKPOINTS")
    print("="*60)
    
    checkpoints = Orchestrator.list_available_checkpoints(args.db_path, run_id=args.run_id)
    
    if checkpoints:
        print(f"\nFound {len(checkpoints)} checkpoint(s):")
        for i, cp in enumerate(checkpoints, 1):
            print(f"\n{i}. Run ID: {cp['run_id']}")
            print(f"   Cycle: {cp['cycle']}")
            print(f"   Inference Count: {cp.get('inference_count', 0)}")
            print(f"   Timestamp: {cp['timestamp']}")
    else:
        print("\nNo checkpoints found.")
        if args.run_id:
            print(f"(for run_id: {args.run_id})")
    
    print()


def export_checkpoint(args):
    """Export a checkpoint to a JSON file."""
    print("\n" + "="*60)
    print("EXPORT CHECKPOINT")
    print("="*60)
    
    db = OrchestratorDB(args.db_path, run_id=args.run_id)
    
    # Load checkpoint
    if args.cycle is not None:
        result = db.load_checkpoint_by_cycle(args.cycle, args.run_id, args.inference_count)
    else:
        result = db.load_latest_checkpoint(args.run_id)
    
    if not result:
        print(f"❌ No checkpoint found for run: {args.run_id or 'latest'}")
        return
    
    cycle, inf_count, checkpoint_data = result
    
    print(f"  ✓ Loaded checkpoint: Cycle {cycle}, Inference {inf_count}")
    print(f"  ✓ Run ID: {args.run_id or 'latest'}")
    
    # Export to file
    output_file = args.output or f"checkpoint_{args.run_id or 'latest'}_c{cycle}_i{inf_count}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, indent=2, default=str)
    
    print(f"\n✅ Exported to: {output_file}")
    print()


def print_results(orchestrator, final_concepts, duration):
    """Print execution results summary."""
    print("\n" + "="*60)
    print("EXECUTION RESULTS")
    print("="*60)
    
    print(f"\n✅ Execution completed in {duration:.2f}s")
    print(f"Run ID: {orchestrator.run_id}")
    
    # Count completed concepts
    completed = sum(1 for fc in final_concepts if fc and fc.concept and fc.concept.reference)
    print(f"Completed Concepts: {completed}/{len(final_concepts)}")
    
    # Display final concepts
    print("\nFinal Concepts:")
    for fc in final_concepts:
        if fc and fc.concept and fc.concept.reference:
            ref = fc.concept.reference
            print(f"  • {fc.concept_name}")
            print(f"    Shape: {ref.shape}, Axes: {ref.axes}")
            # Print a preview of the data
            data_str = str(ref.tensor)
            if len(data_str) > 100:
                data_str = data_str[:97] + "..."
            print(f"    Data: {data_str}")
    
    print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='NormCode Orchestrator CLI - Run orchestrations from the command line',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Global arguments
    parser.add_argument('--db-path', type=str, default='orchestration.db',
                       help='Path to checkpoint database (default: orchestration.db)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Run command (fresh execution)
    run_parser = subparsers.add_parser('run', help='Start a fresh orchestration run')
    run_parser.add_argument('--concepts', required=True, help='Concepts JSON file')
    run_parser.add_argument('--inferences', required=True, help='Inferences JSON file')
    run_parser.add_argument('--inputs', help='Inputs JSON file (optional)')
    run_parser.add_argument('--llm', default='demo', help='LLM model name (default: demo)')
    run_parser.add_argument('--base-dir', help='Base directory for Body (default: current dir)')
    run_parser.add_argument('--max-cycles', type=int, default=30, help='Maximum cycles (default: 30)')
    
    # Resume command
    resume_parser = subparsers.add_parser('resume', help='Resume from a checkpoint')
    resume_parser.add_argument('--concepts', required=True, help='Concepts JSON file')
    resume_parser.add_argument('--inferences', required=True, help='Inferences JSON file')
    resume_parser.add_argument('--inputs', help='Inputs JSON file (optional)')
    resume_parser.add_argument('--run-id', help='Run ID to resume (default: latest)')
    resume_parser.add_argument('--mode', choices=['PATCH', 'OVERWRITE', 'FILL_GAPS'], 
                               default='PATCH', help='Reconciliation mode (default: PATCH)')
    resume_parser.add_argument('--llm', default='demo', help='LLM model name (default: demo)')
    resume_parser.add_argument('--base-dir', help='Base directory for Body (default: current dir)')
    resume_parser.add_argument('--max-cycles', type=int, default=30, help='Maximum cycles (default: 30)')
    
    # Fork command
    fork_parser = subparsers.add_parser('fork', help='Fork from a checkpoint with different repository')
    fork_parser.add_argument('--concepts', required=True, help='NEW concepts JSON file')
    fork_parser.add_argument('--inferences', required=True, help='NEW inferences JSON file')
    fork_parser.add_argument('--inputs', help='NEW inputs JSON file (optional)')
    fork_parser.add_argument('--from-run', help='Source run ID to fork from (default: latest)')
    fork_parser.add_argument('--new-run-id', help='New run ID (default: auto-generate)')
    fork_parser.add_argument('--mode', choices=['PATCH', 'OVERWRITE', 'FILL_GAPS'],
                            default='OVERWRITE', help='Reconciliation mode (default: OVERWRITE)')
    fork_parser.add_argument('--llm', default='demo', help='LLM model name (default: demo)')
    fork_parser.add_argument('--base-dir', help='Base directory for Body (default: current dir)')
    fork_parser.add_argument('--max-cycles', type=int, default=30, help='Maximum cycles (default: 30)')
    
    # List runs command
    list_runs_parser = subparsers.add_parser('list-runs', help='List all available runs')
    
    # List checkpoints command
    list_cp_parser = subparsers.add_parser('list-checkpoints', help='List checkpoints for a run')
    list_cp_parser.add_argument('--run-id', help='Run ID (default: all runs)')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export a checkpoint to JSON')
    export_parser.add_argument('--run-id', help='Run ID to export (default: latest)')
    export_parser.add_argument('--cycle', type=int, help='Specific cycle number (default: latest)')
    export_parser.add_argument('--inference-count', type=int, help='Specific inference count')
    export_parser.add_argument('--output', help='Output file path (default: auto-generate)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Execute command
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'run':
            run_fresh(args)
        elif args.command == 'resume':
            run_resume(args)
        elif args.command == 'fork':
            run_fork(args)
        elif args.command == 'list-runs':
            list_runs(args)
        elif args.command == 'list-checkpoints':
            list_checkpoints(args)
        elif args.command == 'export':
            export_checkpoint(args)
        else:
            parser.print_help()
    
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == '__main__':
    main()

