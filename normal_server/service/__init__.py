"""
Service Layer

Core business logic for the NormCode Deployment Server.
"""

from .config import get_config, get_available_llm_models, SETTINGS_PATH, ServerConfig
from .schemas import (
    StartRunRequest, RunStatus, PlanInfo,
    # IDE-level debugging schemas
    BreakpointRequest, BreakpointResponse,
    ValueOverrideRequest, ValueOverrideResponse,
    ReferenceDataResponse, NodeStatusesResponse,
    LogEntry, LogsResponse, CommandResponse,
)
from .state import RunState
from .globals import active_runs, websocket_connections, broadcast_event
from .plans import discover_plans, get_plan_inputs_outputs, load_plan_graph
from .execution import execute_run, execute_run_with_resume, setup_run_logging

__all__ = [
    # Config
    "get_config",
    "get_available_llm_models",
    "SETTINGS_PATH",
    "ServerConfig",
    # Schemas
    "StartRunRequest",
    "RunStatus",
    "PlanInfo",
    # IDE-level debugging schemas
    "BreakpointRequest",
    "BreakpointResponse",
    "ValueOverrideRequest",
    "ValueOverrideResponse",
    "ReferenceDataResponse",
    "NodeStatusesResponse",
    "LogEntry",
    "LogsResponse",
    "CommandResponse",
    # State
    "RunState",
    # Globals
    "active_runs",
    "websocket_connections",
    "broadcast_event",
    # Plans
    "discover_plans",
    "get_plan_inputs_outputs",
    "load_plan_graph",
    # Execution
    "execute_run",
    "execute_run_with_resume",
    "setup_run_logging",
]

