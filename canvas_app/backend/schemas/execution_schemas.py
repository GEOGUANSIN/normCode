"""Execution-related schemas."""
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path
import os
import yaml
import logging
import sys

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_MAX_CYCLES = 50
DEFAULT_DB_PATH = "orchestration.db"


def get_available_llm_models() -> List[str]:
    """
    Dynamically read available LLM models from settings.yaml.
    Uses the same path logic as infra._agent._models._language_models.LanguageModel
    to ensure consistency.
    
    Always includes 'demo' mode for testing without an LLM.
    """
    models = ["demo"]  # Always include demo mode
    
    try:
        # Import PROJECT_ROOT from infra._constants (same as LanguageModel uses)
        # Add project root to path if needed
        project_root = Path(__file__).parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from infra._constants import PROJECT_ROOT
        settings_path = os.path.join(PROJECT_ROOT, "settings.yaml")
        
        if os.path.exists(settings_path):
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = yaml.safe_load(f) or {}
            
            # Get model names from settings (exclude BASE_URL if present)
            # This matches the logic in LanguageModel.__init__
            for key in settings.keys():
                if key != 'BASE_URL' and isinstance(settings[key], dict):
                    if key not in models:
                        models.append(key)
            
            logger.info(f"Loaded {len(models)} LLM models from {settings_path}")
        else:
            logger.warning(f"settings.yaml not found at {settings_path}, using demo mode only")
    except ImportError as e:
        logger.warning(f"Could not import infra._constants: {e}, using fallback path")
        # Fallback to relative path if infra import fails
        project_root = Path(__file__).parent.parent.parent.parent
        settings_path = project_root / "settings.yaml"
        try:
            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = yaml.safe_load(f) or {}
                for key in settings.keys():
                    if key != 'BASE_URL' and isinstance(settings[key], dict):
                        if key not in models:
                            models.append(key)
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"Failed to load settings.yaml: {e}, using demo mode only")
    
    return models


# Available LLM models (loaded dynamically from settings.yaml)
LLM_MODELS = get_available_llm_models()


class ExecutionStatus(str, Enum):
    """Overall execution status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    COMPLETED = "completed"
    FAILED = "failed"


class NodeStatus(str, Enum):
    """Individual node execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class LoadRepositoryRequest(BaseModel):
    """Request to load repository files."""
    concepts_path: str
    inferences_path: str
    inputs_path: Optional[str] = None
    llm_model: str = "demo"
    base_dir: Optional[str] = None
    max_cycles: int = Field(default=DEFAULT_MAX_CYCLES, ge=1, le=1000)
    db_path: Optional[str] = None  # Defaults to base_dir/orchestration.db
    paradigm_dir: Optional[str] = None  # Custom paradigm directory (e.g., provision/paradigm)


class ExecutionConfig(BaseModel):
    """Current execution configuration and available options."""
    llm_model: str = "demo"
    max_cycles: int = DEFAULT_MAX_CYCLES
    db_path: Optional[str] = None
    base_dir: Optional[str] = None
    paradigm_dir: Optional[str] = None  # Custom paradigm directory
    available_models: List[str] = Field(default_factory=lambda: LLM_MODELS.copy())
    default_max_cycles: int = DEFAULT_MAX_CYCLES
    default_db_path: str = DEFAULT_DB_PATH


class ExecutionState(BaseModel):
    """Current execution state."""
    status: ExecutionStatus
    current_inference: Optional[str] = None
    completed_count: int = 0
    total_count: int = 0
    cycle_count: int = 0
    node_statuses: Dict[str, NodeStatus] = {}
    breakpoints: List[str] = []


class LogEntry(BaseModel):
    """A single log entry."""
    level: str  # info, warning, error
    flow_index: str
    message: str
    timestamp: float


class LogsResponse(BaseModel):
    """Response containing execution logs."""
    logs: List[LogEntry] = []
    total_count: int = 0


class BreakpointRequest(BaseModel):
    """Request to set/clear a breakpoint."""
    flow_index: str
    enabled: bool = True


class StepRequest(BaseModel):
    """Request to step execution."""
    mode: str = "step"  # "step" | "step_over" | "run_to"
    target_flow_index: Optional[str] = None
