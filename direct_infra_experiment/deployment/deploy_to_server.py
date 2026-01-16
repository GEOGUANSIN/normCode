#!/usr/bin/env python3
"""
NormCode Plan Deployer

Packs a NormCode project and deploys it to a server.

Supports:
- HTTP deployment (to remote server)
- Local deployment (direct copy to server's plans directory)

Usage:
    # Deploy to remote server via HTTP
    python deploy_to_server.py ./project.normcode-canvas.json --server http://localhost:8080
    
    # Deploy to local server directory
    python deploy_to_server.py ./project.normcode-canvas.json --local ./custom_server/data/plans
    
    # Just pack without deploying
    python deploy_to_server.py ./project.normcode-canvas.json --pack-only -o ./my-plan.zip

Examples:
    python deploy_to_server.py deployment/test_ncs/pre-deployment/gold/testproject.normcode-canvas.json --server http://localhost:9090
    python deploy_to_server.py deployment/test_ncs/pre-deployment/gold/testproject.normcode-canvas.json --local ./custom_server/data/plans
"""

import sys
import json
import shutil
import argparse
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Ensure deployment directory is in path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def write_text_utf8(path: Path, content: str):
    """Write text to file with UTF-8 encoding."""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load project configuration."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def resolve_path(base_dir: Path, path_str: Optional[str]) -> Optional[Path]:
    """Resolve a path relative to base directory."""
    if not path_str:
        return None
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def create_manifest(config: Dict[str, Any], project_dir: Path) -> Dict[str, Any]:
    """Create manifest.json from project config."""
    
    # Get plan name/id
    plan_name = config.get('name', config.get('id', 'unnamed'))
    
    manifest = {
        "name": plan_name,
        "version": "1.0.0",
        "description": config.get('description', f"Deployed from {plan_name}"),
        "entry": {
            "concepts": "concept_repo.json",
            "inferences": "inference_repo.json"
        },
        "default_agent": config.get('execution', {}).get('llm_model', 'qwen-plus'),
        "provisions": {}
    }
    
    # Detect provision directories
    exec_config = config.get('execution', {})
    paradigm_dir = exec_config.get('paradigm_dir')
    
    if paradigm_dir:
        paradigm_path = resolve_path(project_dir, paradigm_dir)
        if paradigm_path and paradigm_path.exists():
            provisions_root = paradigm_path.parent
            
            # Check for standard provision subdirectories
            for subdir in ['paradigms', 'paradigm', 'prompts', 'scripts', 'data']:
                subdir_path = provisions_root / subdir
                if subdir_path.exists():
                    # Normalize paradigm -> paradigms
                    key = 'paradigms' if subdir == 'paradigm' else subdir
                    manifest['provisions'][key] = f"provisions/{key}"
            
            # Check for language variants
            for item in provisions_root.iterdir():
                if item.is_dir() and ('_' in item.name):
                    base, variant = item.name.rsplit('_', 1)
                    if base in ['prompts', 'scripts', 'data']:
                        manifest['provisions'][item.name] = f"provisions/{item.name}"
    
    return manifest


def pack_project(config_path: Path, output_zip: Optional[Path] = None) -> Path:
    """
    Pack a NormCode project into a deployable zip.
    
    Returns path to the created zip file.
    """
    config_path = config_path.resolve()
    project_dir = config_path.parent
    
    print(f"Packing project: {config_path.name}")
    print(f"  Project dir: {project_dir}")
    
    # Load config
    config = load_config(config_path)
    plan_name = config.get('name', config.get('id', 'unnamed'))
    
    # Determine output path
    if output_zip is None:
        output_zip = project_dir / f"{plan_name}.normcode.zip"
    output_zip = output_zip.resolve()
    
    # Create temp directory for packaging
    with tempfile.TemporaryDirectory(prefix="normcode_pack_") as temp_dir:
        temp_path = Path(temp_dir)
        package_dir = temp_path / plan_name
        package_dir.mkdir()
        
        # 1. Copy concept repo
        repos = config.get('repositories', {})
        concept_src = resolve_path(project_dir, repos.get('concepts'))
        if concept_src and concept_src.exists():
            shutil.copy2(concept_src, package_dir / "concept_repo.json")
            print(f"  Added: concept_repo.json")
        else:
            raise FileNotFoundError(f"Concept repo not found: {repos.get('concepts')}")
        
        # 2. Copy inference repo
        inference_src = resolve_path(project_dir, repos.get('inferences'))
        if inference_src and inference_src.exists():
            shutil.copy2(inference_src, package_dir / "inference_repo.json")
            print(f"  Added: inference_repo.json")
        else:
            raise FileNotFoundError(f"Inference repo not found: {repos.get('inferences')}")
        
        # 3. Copy provisions
        exec_config = config.get('execution', {})
        paradigm_dir_str = exec_config.get('paradigm_dir')
        
        if paradigm_dir_str:
            paradigm_path = resolve_path(project_dir, paradigm_dir_str)
            if paradigm_path and paradigm_path.exists():
                provisions_root = paradigm_path.parent
                provisions_dest = package_dir / "provisions"
                provisions_dest.mkdir()
                
                # Copy all provision directories
                for item in provisions_root.iterdir():
                    if item.is_dir() and not item.name.startswith('__'):
                        # Normalize 'paradigm' to 'paradigms'
                        dest_name = 'paradigms' if item.name == 'paradigm' else item.name
                        dest_path = provisions_dest / dest_name
                        
                        # Copy directory, excluding __pycache__
                        shutil.copytree(
                            item, 
                            dest_path,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git')
                        )
                        print(f"  Added: provisions/{dest_name}/")
        
        # 4. Create manifest
        manifest = create_manifest(config, project_dir)
        manifest_path = package_dir / "manifest.json"
        write_text_utf8(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
        print(f"  Created: manifest.json")
        
        # 5. Create zip
        print(f"  Creating zip archive...")
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in package_dir.rglob('*'):
                if file_path.is_file():
                    arc_name = file_path.relative_to(temp_path)
                    zf.write(file_path, arc_name)
    
    print(f"  Output: {output_zip}")
    return output_zip


def deploy_http(zip_path: Path, server_url: str) -> Dict[str, Any]:
    """Deploy a plan to a server via HTTP."""
    import urllib.request
    import urllib.error
    
    # Ensure URL ends without slash
    server_url = server_url.rstrip('/')
    deploy_url = f"{server_url}/api/plans/deploy-file"
    
    print(f"Deploying to: {deploy_url}")
    
    # Read zip file
    with open(zip_path, 'rb') as f:
        zip_data = f.read()
    
    # Create multipart form data
    boundary = '----NormCodeDeployBoundary'
    
    body = []
    body.append(f'--{boundary}'.encode())
    body.append(b'Content-Disposition: form-data; name="plan"; filename="plan.zip"')
    body.append(b'Content-Type: application/zip')
    body.append(b'')
    body.append(zip_data)
    body.append(f'--{boundary}--'.encode())
    body.append(b'')
    
    body_bytes = b'\r\n'.join(body)
    
    # Make request
    req = urllib.request.Request(
        deploy_url,
        data=body_bytes,
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body_bytes))
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"  Status: {result.get('status', 'unknown')}")
            print(f"  Plan ID: {result.get('plan_id', 'unknown')}")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        print(f"  Error: HTTP {e.code}")
        print(f"  {error_body}")
        raise
    except urllib.error.URLError as e:
        print(f"  Error: {e.reason}")
        raise


def deploy_local(zip_path: Path, plans_dir: Path) -> Dict[str, Any]:
    """Deploy a plan by extracting directly to the plans directory."""
    
    plans_dir = plans_dir.resolve()
    plans_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Deploying to: {plans_dir}")
    
    # Extract zip
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Get the root folder name from the zip
        namelist = zf.namelist()
        if namelist:
            root_folder = namelist[0].split('/')[0]
        else:
            raise ValueError("Empty zip file")
        
        # Check if plan already exists
        dest_dir = plans_dir / root_folder
        if dest_dir.exists():
            print(f"  Removing existing: {root_folder}")
            shutil.rmtree(dest_dir)
        
        # Extract
        zf.extractall(plans_dir)
        print(f"  Extracted: {root_folder}/")
    
    # Load manifest to get plan info
    manifest_path = dest_dir / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        plan_id = manifest.get('name', root_folder)
    else:
        plan_id = root_folder
    
    result = {
        "status": "deployed",
        "plan_id": plan_id,
        "destination": str(dest_dir)
    }
    
    print(f"  Status: deployed")
    print(f"  Plan ID: {plan_id}")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Pack and deploy a NormCode project to a server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy to remote server
  python deploy_to_server.py ./project.normcode-canvas.json --server http://localhost:8080
  
  # Deploy to local server directory
  python deploy_to_server.py ./project.normcode-canvas.json --local ./custom_server/data/plans
  
  # Just pack without deploying
  python deploy_to_server.py ./project.normcode-canvas.json --pack-only
        """
    )
    
    parser.add_argument(
        'config',
        type=Path,
        help='Path to .normcode-canvas.json or manifest.json'
    )
    
    # Deployment targets (mutually exclusive)
    target_group = parser.add_mutually_exclusive_group()
    target_group.add_argument(
        '--server',
        type=str,
        help='Server URL for HTTP deployment (e.g., http://localhost:8080)'
    )
    target_group.add_argument(
        '--local',
        type=Path,
        help='Local plans directory for direct deployment'
    )
    target_group.add_argument(
        '--pack-only',
        action='store_true',
        help='Only pack, do not deploy'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output zip file path (for --pack-only)'
    )
    
    parser.add_argument(
        '--keep-zip',
        action='store_true',
        help='Keep the zip file after deployment'
    )
    
    args = parser.parse_args()
    
    # Validate config exists
    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 60)
    print("NormCode Plan Deployer")
    print("=" * 60)
    
    try:
        # Step 1: Pack
        zip_path = pack_project(args.config, args.output)
        
        if args.pack_only:
            print("\n[OK] Pack complete!")
            print(f"  Output: {zip_path}")
            return
        
        # Step 2: Deploy
        print()
        if args.server:
            result = deploy_http(zip_path, args.server)
        elif args.local:
            result = deploy_local(zip_path, args.local)
        else:
            print("No deployment target specified. Use --server, --local, or --pack-only")
            print(f"  Zip created: {zip_path}")
            return
        
        # Cleanup
        if not args.keep_zip and not args.pack_only:
            zip_path.unlink()
            print(f"  Cleaned up: {zip_path.name}")
        
        print("\n[OK] Deployment complete!")
        
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

