#!/usr/bin/env python3
"""
NormCode Plan Packager

Creates self-contained deployment packages (.zip) from NormCode projects.

Usage:
    python pack.py ./test_ncs/testproject.normcode-canvas.json
    python pack.py ./test_ncs/testproject.normcode-canvas.json --output my-plan.zip
"""

import sys
import json
import zipfile
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def extract_ground_concepts(concept_repo_path: Path) -> Dict[str, Dict[str, Any]]:
    """Extract ground concept definitions for manifest.inputs"""
    with open(concept_repo_path, 'r', encoding='utf-8') as f:
        concepts = json.load(f)
    
    inputs = {}
    for concept in concepts:
        if concept.get('is_ground_concept', False):
            name = concept.get('concept_name', '')
            inputs[name] = {
                "type": "any",  # Could be inferred from reference_data
                "required": True,
                "description": f"Ground concept: {name}"
            }
    return inputs


def extract_final_concepts(concept_repo_path: Path) -> Dict[str, Dict[str, Any]]:
    """Extract final concept definitions for manifest.outputs"""
    with open(concept_repo_path, 'r', encoding='utf-8') as f:
        concepts = json.load(f)
    
    outputs = {}
    for concept in concepts:
        if concept.get('is_final_concept', False):
            name = concept.get('concept_name', '')
            outputs[name] = {
                "type": "object",
                "description": f"Output concept: {name}"
            }
    return outputs


def collect_provisions(project_dir: Path, paradigm_dir: Optional[Path]) -> List[Path]:
    """Find all provision files to include."""
    provisions = []
    
    # Check for provision directory
    provision_dir = project_dir / 'provision'
    if provision_dir.exists():
        for item in provision_dir.rglob('*'):
            if item.is_file() and not item.name.startswith('.'):
                # Skip __pycache__
                if '__pycache__' not in str(item):
                    provisions.append(item)
    
    # Also check paradigm_dir if different
    if paradigm_dir and paradigm_dir.exists() and paradigm_dir != provision_dir / 'paradigm':
        for item in paradigm_dir.rglob('*'):
            if item.is_file() and not item.name.startswith('.'):
                if '__pycache__' not in str(item):
                    provisions.append(item)
    
    return provisions


def create_manifest(
    config_path: Path,
    concept_repo_path: Path,
    inference_repo_path: Path
) -> Dict[str, Any]:
    """Create a deployment manifest from a canvas config."""
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    name = config.get('name', config_path.stem)
    
    manifest = {
        "name": name,
        "version": "1.0.0",
        "description": config.get('description') or f"NormCode plan: {name}",
        "created_at": datetime.now().isoformat(),
        "source_config": config_path.name,
        
        "entry": {
            "concepts": "concept_repo.json",
            "inferences": "inference_repo.json"
        },
        
        "inputs": extract_ground_concepts(concept_repo_path),
        "outputs": extract_final_concepts(concept_repo_path),
        
        "execution": {
            "default_llm": config.get('execution', {}).get('llm_model', 'demo'),
            "max_cycles": config.get('execution', {}).get('max_cycles', 100)
        }
    }
    
    return manifest


def pack_plan(
    config_path: Path,
    output_path: Optional[Path] = None,
    verbose: bool = True
) -> Path:
    """
    Package a NormCode project into a deployment .zip file.
    
    Args:
        config_path: Path to .normcode-canvas.json
        output_path: Output .zip path (default: {name}.normcode.zip)
        verbose: Print progress
    
    Returns:
        Path to created .zip file
    """
    config_path = config_path.resolve()
    project_dir = config_path.parent
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Resolve repository paths
    repos = config.get('repositories', {})
    concept_path_str = repos.get('concepts')
    inference_path_str = repos.get('inferences')
    
    if not concept_path_str or not inference_path_str:
        raise ValueError("Config must specify concepts and inferences repositories")
    
    concept_path = Path(concept_path_str)
    if not concept_path.is_absolute():
        concept_path = (project_dir / concept_path).resolve()
    
    inference_path = Path(inference_path_str)
    if not inference_path.is_absolute():
        inference_path = (project_dir / inference_path).resolve()
    
    # Resolve paradigm dir
    paradigm_dir_str = config.get('execution', {}).get('paradigm_dir')
    paradigm_dir = None
    if paradigm_dir_str:
        paradigm_dir = Path(paradigm_dir_str)
        if not paradigm_dir.is_absolute():
            paradigm_dir = (project_dir / paradigm_dir).resolve()
    
    # Determine output path
    name = config.get('name', 'plan').replace(' ', '-').lower()
    if not output_path:
        output_path = project_dir / f"{name}.normcode.zip"
    
    if verbose:
        print(f"Packaging plan: {config.get('name', 'unnamed')}")
        print(f"  Config: {config_path}")
        print(f"  Concepts: {concept_path}")
        print(f"  Inferences: {inference_path}")
        print(f"  Output: {output_path}")
    
    # Create manifest
    manifest = create_manifest(config_path, concept_path, inference_path)
    
    # Collect provisions
    provisions = collect_provisions(project_dir, paradigm_dir)
    if verbose:
        print(f"  Provisions: {len(provisions)} files")
    
    # Create zip
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add manifest
        zf.writestr('manifest.json', json.dumps(manifest, indent=2, ensure_ascii=False))
        
        # Add repositories
        zf.write(concept_path, 'concept_repo.json')
        zf.write(inference_path, 'inference_repo.json')
        
        # Add provisions
        for provision_file in provisions:
            # Calculate relative path from project_dir
            try:
                rel_path = provision_file.relative_to(project_dir)
                # Normalize to provisions/ prefix
                if str(rel_path).startswith('provision'):
                    arc_path = 'provisions' + str(rel_path)[len('provision'):]
                else:
                    arc_path = f"provisions/{rel_path}"
                zf.write(provision_file, arc_path.replace('\\', '/'))
            except ValueError:
                # File is outside project_dir (e.g., absolute paradigm_dir)
                arc_path = f"provisions/paradigms/{provision_file.name}"
                zf.write(provision_file, arc_path)
    
    if verbose:
        size_kb = output_path.stat().st_size / 1024
        print(f"  Created: {output_path.name} ({size_kb:.1f} KB)")
        print(f"  Contents:")
        with zipfile.ZipFile(output_path, 'r') as zf:
            for info in zf.infolist():
                print(f"    - {info.filename} ({info.file_size} bytes)")
    
    return output_path


def unpack_plan(
    zip_path: Path,
    output_dir: Optional[Path] = None,
    verbose: bool = True
) -> Path:
    """
    Unpack a deployment .zip into a directory.
    
    Args:
        zip_path: Path to .normcode.zip
        output_dir: Output directory (default: same name as zip)
        verbose: Print progress
    
    Returns:
        Path to unpacked directory
    """
    zip_path = zip_path.resolve()
    
    if not output_dir:
        output_dir = zip_path.parent / zip_path.stem.replace('.normcode', '')
    
    if verbose:
        print(f"Unpacking: {zip_path}")
        print(f"  To: {output_dir}")
    
    # Extract
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(output_dir)
    
    if verbose:
        print(f"  Extracted {len(list(output_dir.rglob('*')))} files")
    
    return output_dir


def main():
    parser = argparse.ArgumentParser(
        description="NormCode Plan Packager - Create deployment packages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Pack a project:
    python pack.py ./test_ncs/testproject.normcode-canvas.json
    python pack.py ./test_ncs/testproject.normcode-canvas.json -o my-plan.zip
  
  Unpack a package:
    python pack.py --unpack my-plan.normcode.zip
    python pack.py --unpack my-plan.normcode.zip -o ./unpacked/
        """
    )
    
    parser.add_argument(
        'input',
        type=Path,
        help='Path to .normcode-canvas.json (pack) or .normcode.zip (unpack)'
    )
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output path (default: auto-generated)'
    )
    parser.add_argument(
        '--unpack',
        action='store_true',
        help='Unpack a .zip instead of packing'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress output'
    )
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: Input not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    try:
        if args.unpack:
            result = unpack_plan(args.input, args.output, verbose=not args.quiet)
            if not args.quiet:
                print(f"\nUnpacked to: {result}")
        else:
            result = pack_plan(args.input, args.output, verbose=not args.quiet)
            if not args.quiet:
                print(f"\nPackage created: {result}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

