"""
Server Configuration Module

Manages server settings, paths, and environment configuration.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Server directory (normal_server root) - go up one level from service/
SERVICE_DIR = Path(__file__).resolve().parent
SERVER_DIR = SERVICE_DIR.parent

# Detect if running from built package or source
IS_BUILT_PACKAGE = (SERVER_DIR / "infra").exists() and (SERVER_DIR / "tools").exists()

if IS_BUILT_PACKAGE:
    DEPLOYMENT_ROOT = SERVER_DIR
    PROJECT_ROOT = SERVER_DIR
else:
    # When in source: canvas_app/normal_server/ → canvas_app/ → normCode/
    PROJECT_ROOT = SERVER_DIR.parents[1]  # normCode root (two levels up from normal_server)
    DEPLOYMENT_ROOT = SERVER_DIR

# Settings path - check multiple locations
SETTINGS_PATH: Optional[Path] = None
for candidate in [
    SERVER_DIR / "data" / "config" / "settings.yaml",  # Built package
    SERVER_DIR / "settings.yaml",                       # Same directory
    DEPLOYMENT_ROOT / "tools" / "settings.yaml",        # Source location
]:
    if candidate.exists():
        SETTINGS_PATH = candidate
        break

if SETTINGS_PATH is None:
    SETTINGS_PATH = SERVER_DIR / "settings.yaml"  # Default fallback


class ServerConfig:
    """Server configuration from environment or defaults."""
    
    def __init__(self):
        # Determine default paths based on whether running from built package or source
        if IS_BUILT_PACKAGE:
            default_plans_dir = SERVER_DIR / "data" / "plans"
            default_runs_dir = SERVER_DIR / "data" / "runs"
        else:
            default_plans_dir = SERVER_DIR / "data" / "plans"
            default_runs_dir = SERVER_DIR / "data" / "runs"
        
        self.host = os.getenv("NORMCODE_HOST", "0.0.0.0")
        self.port = int(os.getenv("NORMCODE_PORT", "8080"))
        
        plans_dir_str = os.getenv("NORMCODE_PLANS_DIR")
        self.plans_dir = Path(plans_dir_str) if plans_dir_str else default_plans_dir
        
        runs_dir_str = os.getenv("NORMCODE_RUNS_DIR")
        self.runs_dir = Path(runs_dir_str) if runs_dir_str else default_runs_dir
        
        self.log_level = os.getenv("NORMCODE_LOG_LEVEL", "INFO")
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        self.plans_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)


# Singleton config instance
_config: Optional[ServerConfig] = None


def get_config() -> ServerConfig:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = ServerConfig()
    return _config


def get_available_llm_models() -> List[Dict[str, Any]]:
    """Get available LLM models from settings.yaml."""
    import yaml
    
    models = [{"id": "demo", "name": "Demo (Mock)", "is_mock": True}]
    
    if SETTINGS_PATH and SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                settings = yaml.safe_load(f) or {}
            
            base_url = settings.pop("BASE_URL", None)
            
            for model_name, config in settings.items():
                if isinstance(config, dict):
                    models.append({
                        "id": model_name,
                        "name": model_name,
                        "base_url": base_url,
                        "is_mock": False,
                    })
        except Exception as e:
            logging.warning(f"Failed to load LLM settings: {e}")
    
    return models

