"""Execution-related schemas."""
from typing import Optional, List, Dict, Any
from enum import Enum
from pathlib import Path
import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_MAX_CYCLES = 50
DEFAULT_DB_PATH = "orchestration.db"


def get_available_llm_models() -> List[str]:
    """
    Get available LLM models from the LLM settings service.
    
    This reads from canvas_app/backend/tools/llm-settings.json,
    ensuring the canvas app is self-contained and decoupled from infra.
    
    Always includes 'demo' mode for testing without an LLM.
    """
    models = ["demo"]  # Always include demo mode
    
    try:
        from services.agent.llm_providers import LLMSettingsService
        service = LLMSettingsService()
        providers = service.get_providers()
        
        for provider in providers:
            if provider.is_enabled and provider.model:
                if provider.model not in models:
                    models.append(provider.model)
        
        logger.info(f"Loaded {len(models)} LLM models from llm-settings.json")
    except Exception as e:
        logger.warning(f"Failed to load LLM models from settings service: {e}, using demo mode only")
    
    return models


# Available LLM models (loaded dynamically from llm-settings.json)
LLM_MODELS = get_available_llm_models()


class ExecutionStatus(str, Enum):
    """Overall execution status."""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    COMPLETED = "completed"
    FAILED = "failed"


class RunMode(str, Enum):
    """Execution run mode - controls how many inferences execute per cycle."""
    SLOW = "slow"      # One inference at a time (default) - easier to follow
    FAST = "fast"      # All ready inferences per cycle - faster execution


class NodeStatus(str, Enum):
    """Individual node execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class LoadRepositoryRequest(BaseModel):
    """Request to load repository files.
    
    Agent-centric LLM configuration:
    - agent_config is the primary way to configure LLM (points to .agent.json)
    - llm_model is deprecated but kept for backward compatibility
    """
    concepts_path: str
    inferences_path: str
    inputs_path: Optional[str] = None
    llm_model: str = "demo"  # DEPRECATED: Use agent_config instead
    base_dir: Optional[str] = None
    max_cycles: int = Field(default=DEFAULT_MAX_CYCLES, ge=1, le=1000)
    db_path: Optional[str] = None  # Defaults to base_dir/orchestration.db
    paradigm_dir: Optional[str] = None  # Custom paradigm directory
    # Agent-centric config
    agent_config: Optional[str] = None  # Path to .agent.json file
    project_dir: Optional[str] = None  # Project directory for resolving paths
    project_name: Optional[str] = None  # Project name for auto-discovery


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
    run_mode: str = "slow"  # "slow" or "fast"


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


# Step names for different sequence types
SEQUENCE_STEPS = {
    "imperative": ["IWI", "IR", "MFP", "MVP", "TVA", "TIP", "MIA", "OR", "OWI"],
    "imperative_direct": ["IWI", "IR", "MFP", "MVP", "TVA", "TIP", "MIA", "OR", "OWI"],
    "imperative_input": ["IWI", "IR", "MFP", "MVP", "TVA", "TIP", "MIA", "OR", "OWI"],
    "imperative_python": ["IWI", "IR", "MFP", "MVP", "TVA", "TIP", "MIA", "OR", "OWI"],
    "imperative_python_indirect": ["IWI", "IR", "MFP", "MVP", "TVA", "TIP", "MIA", "OR", "OWI"],
    "judgement": ["IWI", "IR", "MFP", "MVP", "TVA", "TIP", "MIA", "OR", "OWI"],
    "judgement_direct": ["IWI", "IR", "MFP", "MVP", "TVA", "TIP", "MIA", "OR", "OWI"],
    "grouping": ["IWI", "IR", "GR", "OR", "OWI"],
    "assigning": ["IWI", "IR", "AR", "OR", "OWI"],
    "looping": ["IWI", "IR", "GR", "LR", "OR", "OWI"],
    "quantifying": ["IWI", "IR", "GR", "QR", "OR", "OWI"],
    "timing": ["IWI", "T", "OWI"],
    "simple": ["IWI", "IR", "OR", "OWI"],
}

# Full step names for display
STEP_FULL_NAMES = {
    "IWI": "Input Working Interpretation",
    "IR": "Input References",
    "MFP": "Model Function Perception",
    "MVP": "Memory Value Perception",
    "TVA": "Tool Value Actuation",
    "TIP": "Tool Inference Perception",
    "MIA": "Memory Inference Actuation",
    "OR": "Output Reference",
    "OWI": "Output Working Interpretation",
    "GR": "Grouping References",
    "AR": "Assigning References",
    "LR": "Looping References",
    "QR": "Quantifying References",
    "T": "Timing",
}


class StepProgress(BaseModel):
    """Progress through sequence steps for an inference."""
    flow_index: str
    sequence_type: str
    current_step: Optional[str] = None  # e.g., "TVA"
    current_step_index: int = 0
    total_steps: int = 0
    steps: List[str] = []  # All steps in sequence
    completed_steps: List[str] = []  # Steps that have completed
    paradigm: Optional[str] = None  # e.g., "h_PromptTemplate-c_GenerateJson-o_List"


class StepEvent(BaseModel):
    """Event for step-level progress."""
    event_type: str  # "step:started" | "step:completed" | "sequence:started" | "sequence:completed"
    flow_index: str
    step_name: Optional[str] = None
    sequence_type: Optional[str] = None
    paradigm: Optional[str] = None
    step_index: Optional[int] = None
    total_steps: Optional[int] = None
    message: Optional[str] = None
