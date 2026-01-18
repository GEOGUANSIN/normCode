"""
Plans API Routes

Endpoints for plan discovery, deployment, and management.
"""

import json
import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, File

from service import get_config, PlanInfo, discover_plans, get_plan_inputs_outputs, load_plan_graph

router = APIRouter()


@router.get("", response_model=List[PlanInfo])
async def list_plans():
    """List all available plans."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    result = []
    
    for plan_id, plan_config in plans.items():
        inputs, outputs = get_plan_inputs_outputs(plan_config)
        
        result.append(PlanInfo(
            id=plan_id,
            name=plan_config.name,
            description=plan_config.description,
            inputs=inputs,
            outputs=outputs
        ))
    
    return result


@router.get("/{plan_id}")
async def get_plan(plan_id: str):
    """Get details for a specific plan."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    if plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    plan_config = plans[plan_id]
    
    return {
        "id": plan_id,
        "name": plan_config.name,
        "description": plan_config.description,
        "config_path": str(plan_config.config_path),
        "concept_repo": str(plan_config.concept_repo_path),
        "inference_repo": str(plan_config.inference_repo_path),
        "llm_model": plan_config.llm_model,
        "max_cycles": plan_config.max_cycles
    }


@router.get("/{plan_id}/graph")
async def get_plan_graph(plan_id: str):
    """
    Get the full graph data (concepts + inferences) for a plan.
    
    This allows the Canvas App to load and render a remote plan's graph
    without needing local files.
    """
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    if plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    plan_config = plans[plan_id]
    return load_plan_graph(plan_config)


@router.get("/{plan_id}/files/{file_path:path}")
async def get_plan_file(plan_id: str, file_path: str):
    """
    Get a specific file from a plan's directory.
    
    Useful for fetching prompts, paradigms, or other provision files.
    Only allows access to files within the plan directory (security).
    """
    import base64
    
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    if plan_id not in plans:
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    plan_config = plans[plan_id]
    plan_dir = plan_config.project_dir
    
    # Resolve the requested file path
    requested_path = (plan_dir / file_path).resolve()
    
    # Security: ensure the path is within the plan directory
    try:
        requested_path.relative_to(plan_dir.resolve())
    except ValueError:
        raise HTTPException(403, "Access denied: path outside plan directory")
    
    if not requested_path.exists():
        raise HTTPException(404, f"File not found: {file_path}")
    
    if not requested_path.is_file():
        raise HTTPException(400, "Path is not a file")
    
    # Read and return content
    try:
        with open(requested_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {
            "path": file_path,
            "content": content,
            "size": requested_path.stat().st_size,
        }
    except UnicodeDecodeError:
        # Binary file - return base64 encoded
        with open(requested_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('ascii')
        return {
            "path": file_path,
            "content": content,
            "encoding": "base64",
            "size": requested_path.stat().st_size,
        }


@router.post("/deploy")
async def deploy_plan():
    """
    Deploy a plan package - informational endpoint.
    
    Use POST /api/plans/deploy-file with a 'plan' file upload instead.
    """
    cfg = get_config()
    
    return {
        "status": "use /api/plans/deploy-file",
        "plans_dir": str(cfg.plans_dir),
        "message": "POST to /api/plans/deploy-file with a 'plan' file field containing the zip"
    }


@router.post("/deploy-file")
async def deploy_plan_file(plan: bytes = File(...)):
    """
    Deploy a plan package (zip file) to this server.
    Accepts the zip file as the request body.
    """
    cfg = get_config()
    
    try:
        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp(prefix="normcode_upload_"))
        
        try:
            # Save and extract zip
            zip_path = temp_dir / "upload.zip"
            with open(zip_path, 'wb') as f:
                f.write(plan)
            
            # Extract
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir()
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)
            
            # Find manifest.json or .normcode-canvas.json
            manifest_path = None
            plan_dir = None
            
            for item in extract_dir.iterdir():
                if item.is_dir():
                    if (item / "manifest.json").exists():
                        manifest_path = item / "manifest.json"
                        plan_dir = item
                        break
                elif item.name == "manifest.json":
                    manifest_path = item
                    plan_dir = extract_dir
                    break
            
            # Also check for .normcode-canvas.json
            if not manifest_path:
                for config_file in extract_dir.rglob("*.normcode-canvas.json"):
                    manifest_path = config_file
                    plan_dir = config_file.parent
                    break
            
            if not manifest_path:
                raise HTTPException(400, "No manifest.json or .normcode-canvas.json found in package")
            
            # Load manifest to get plan ID
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            plan_id = manifest.get('name') or manifest.get('id') or 'unknown'
            
            # Copy to plans directory
            dest_dir = cfg.plans_dir / plan_id
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            
            shutil.copytree(plan_dir, dest_dir)
            
            logging.info(f"Deployed plan '{plan_id}' to {dest_dir}")
            
            return {
                "status": "deployed",
                "plan_id": plan_id,
                "plan_name": manifest.get('name', plan_id),
                "destination": str(dest_dir),
            }
            
        finally:
            # Cleanup temp
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    except HTTPException:
        raise
    except Exception as e:
        logging.exception(f"Deploy failed: {e}")
        raise HTTPException(500, f"Deploy failed: {e}")


@router.delete("/{plan_id}")
async def undeploy_plan(plan_id: str):
    """Remove a deployed plan."""
    cfg = get_config()
    plan_dir = cfg.plans_dir / plan_id
    
    if not plan_dir.exists():
        raise HTTPException(404, f"Plan not found: {plan_id}")
    
    try:
        shutil.rmtree(plan_dir)
        logging.info(f"Undeployed plan: {plan_id}")
        return {"status": "undeployed", "plan_id": plan_id}
    except Exception as e:
        raise HTTPException(500, f"Failed to undeploy: {e}")


@router.delete("")
async def clear_all_plans():
    """Remove ALL deployed plans from the server."""
    cfg = get_config()
    plans = discover_plans(cfg.plans_dir)
    
    removed = []
    failed = []
    
    for plan_id, plan_config in plans.items():
        try:
            plan_dir = plan_config.project_dir
            if plan_dir.exists():
                shutil.rmtree(plan_dir)
                removed.append(plan_id)
                logging.info(f"Removed plan: {plan_id}")
        except Exception as e:
            failed.append({"plan_id": plan_id, "error": str(e)})
            logging.error(f"Failed to remove plan {plan_id}: {e}")
    
    return {
        "status": "completed",
        "removed_count": len(removed),
        "removed": removed,
        "failed": failed
    }

