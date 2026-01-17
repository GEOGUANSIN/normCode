"""
API Schema Definitions

Pydantic models for request/response validation.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class StartRunRequest(BaseModel):
    """Request to start a new run."""
    plan_id: str = Field(..., description="Plan identifier (config filename)")
    run_id: Optional[str] = Field(None, description="Custom run ID (auto-generated if not provided)")
    llm_model: Optional[str] = Field(None, description="Override LLM model")
    max_cycles: Optional[int] = Field(None, description="Override max cycles")
    ground_inputs: Optional[Dict[str, Any]] = Field(None, description="Values for ground concepts")


class RunStatus(BaseModel):
    """Run status response."""
    run_id: str
    plan_id: str
    status: str  # pending, running, completed, failed, paused, stepping
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    breakpoints: List[str] = Field(default_factory=list, description="Active breakpoint flow_indices")


class PlanInfo(BaseModel):
    """Plan information."""
    id: str
    name: str
    description: Optional[str] = None
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# IDE-Level Debugging Schemas
# =============================================================================

class BreakpointRequest(BaseModel):
    """Request to set or clear a breakpoint."""
    flow_index: str = Field(..., description="The flow_index to set/clear breakpoint on")
    enabled: bool = Field(True, description="True to set, False to clear")


class BreakpointResponse(BaseModel):
    """Response for breakpoint operations."""
    success: bool
    flow_index: str
    enabled: bool
    all_breakpoints: List[str] = Field(default_factory=list)


class ValueOverrideRequest(BaseModel):
    """Request to override a concept's value."""
    new_value: Any = Field(..., description="The new value to set")
    rerun_dependents: bool = Field(False, description="If True, mark dependents stale and rerun")


class ValueOverrideResponse(BaseModel):
    """Response for value override."""
    success: bool
    concept_name: str
    stale_nodes: List[str] = Field(default_factory=list)


class ReferenceDataResponse(BaseModel):
    """Response containing concept reference data."""
    concept_name: str
    has_reference: bool
    data: Optional[Any] = None
    shape: List[int] = Field(default_factory=list)
    axes: List[str] = Field(default_factory=list)


class NodeStatusesResponse(BaseModel):
    """Response containing all node statuses."""
    run_id: str
    statuses: Dict[str, str] = Field(default_factory=dict)
    current_inference: Optional[str] = None


class LogEntry(BaseModel):
    """A single log entry."""
    level: str
    flow_index: str
    message: str
    timestamp: float


class LogsResponse(BaseModel):
    """Response containing execution logs."""
    logs: List[LogEntry] = Field(default_factory=list)
    total_count: int = 0


class CommandResponse(BaseModel):
    """Generic response for execution commands."""
    success: bool
    message: str
    run_id: Optional[str] = None

