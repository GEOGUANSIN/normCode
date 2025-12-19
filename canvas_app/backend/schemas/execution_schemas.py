"""Execution-related schemas."""
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel


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
