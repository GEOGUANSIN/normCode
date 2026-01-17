"""
Plan Discovery and Management

Functions for discovering and loading NormCode plans.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from runner import PlanConfig


def discover_plans(plans_dir: Path) -> Dict[str, PlanConfig]:
    """Discover all plan configs in the plans directory."""
    plans = {}
    
    if not plans_dir.exists():
        plans_dir.mkdir(parents=True, exist_ok=True)
        return plans
    
    # Find all .normcode-canvas.json files
    for config_file in plans_dir.rglob("*.normcode-canvas.json"):
        try:
            plan_config = PlanConfig(config_file)
            plans[plan_config.id] = plan_config
        except Exception as e:
            logging.warning(f"Failed to load plan config {config_file}: {e}")
    
    # Also check for manifest.json files (unpacked packages)
    for manifest_file in plans_dir.rglob("manifest.json"):
        try:
            plan_config = PlanConfig(manifest_file)
            plans[plan_config.id] = plan_config
        except Exception as e:
            logging.warning(f"Failed to load manifest {manifest_file}: {e}")
    
    return plans


def get_plan_inputs_outputs(plan_config: PlanConfig) -> tuple:
    """Extract inputs and outputs from a plan config."""
    inputs = {}
    outputs = {}
    
    try:
        if plan_config.concept_repo_path and plan_config.concept_repo_path.exists():
            with open(plan_config.concept_repo_path, 'r', encoding='utf-8') as f:
                concepts = json.load(f)
            for c in concepts:
                if c.get('is_ground_concept'):
                    inputs[c['concept_name']] = {"type": "any", "required": True}
                if c.get('is_final_concept'):
                    outputs[c['concept_name']] = {"type": "any"}
    except Exception:
        pass
    
    return inputs, outputs


def load_plan_graph(plan_config: PlanConfig) -> Dict:
    """Load the full graph data (concepts + inferences) for a plan."""
    # Load concept repository
    concepts = []
    if plan_config.concept_repo_path and plan_config.concept_repo_path.exists():
        try:
            with open(plan_config.concept_repo_path, 'r', encoding='utf-8') as f:
                concepts = json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load concepts for {plan_config.id}: {e}")
    
    # Load inference repository
    inferences = []
    if plan_config.inference_repo_path and plan_config.inference_repo_path.exists():
        try:
            with open(plan_config.inference_repo_path, 'r', encoding='utf-8') as f:
                inferences = json.load(f)
        except Exception as e:
            logging.warning(f"Failed to load inferences for {plan_config.id}: {e}")
    
    # Discover provisions (paradigms, prompts, etc.)
    provisions = {}
    plan_dir = plan_config.project_dir
    provisions_dir = plan_dir / "provisions"
    if provisions_dir.exists():
        for item in provisions_dir.iterdir():
            if item.is_dir():
                provisions[item.name] = {
                    "path": str(item.relative_to(plan_dir)),
                    "files": [f.name for f in item.iterdir() if f.is_file()][:20]  # Limit
                }
    
    return {
        "plan_id": plan_config.id,
        "plan_name": plan_config.name,
        "description": plan_config.description,
        "concepts": concepts,
        "inferences": inferences,
        "provisions": provisions,
        "llm_model": plan_config.llm_model,
        "max_cycles": plan_config.max_cycles,
    }

