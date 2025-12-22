"""
Execution state management for better debugging and tracking.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status enum."""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionMetrics:
    """Metrics for tracking execution progress."""
    total_items: int = 0
    completed_items: int = 0
    in_progress_items: int = 0
    pending_items: int = 0
    failed_items: int = 0
    retry_count: int = 0
    cycle_count: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_executions == 0:
            return 0.0
        return (self.successful_executions / self.total_executions) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds."""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100


@dataclass
class ExecutionState:
    """
    Comprehensive execution state for debugging and tracking.
    """
    status: ExecutionStatus = ExecutionStatus.NOT_STARTED
    current_phase: str = ""
    run_id: Optional[str] = None
    metrics: ExecutionMetrics = field(default_factory=ExecutionMetrics)
    error_message: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    debug_info: Dict[str, Any] = field(default_factory=dict)
    
    def start(self, run_id: str):
        """Mark execution as started."""
        self.status = ExecutionStatus.RUNNING
        self.run_id = run_id
        self.metrics.start_time = datetime.now()
        logger.info(f"Execution started: {run_id}")
    
    def complete(self):
        """Mark execution as completed."""
        self.status = ExecutionStatus.COMPLETED
        self.metrics.end_time = datetime.now()
        logger.info(f"Execution completed: {self.run_id} in {self.metrics.elapsed_time:.2f}s")
    
    def fail(self, error_message: str):
        """Mark execution as failed."""
        self.status = ExecutionStatus.FAILED
        self.error_message = error_message
        self.metrics.end_time = datetime.now()
        logger.error(f"Execution failed: {self.run_id} - {error_message}")
    
    def pause(self):
        """Mark execution as paused."""
        self.status = ExecutionStatus.PAUSED
        logger.info(f"Execution paused: {self.run_id}")
    
    def set_phase(self, phase: str):
        """Update current execution phase."""
        self.current_phase = phase
        logger.debug(f"Phase changed: {phase}")
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
        logger.warning(f"Warning: {warning}")
    
    def add_debug_info(self, key: str, value: Any):
        """Add debug information."""
        self.debug_info[key] = value
        logger.debug(f"Debug info [{key}]: {value}")
    
    def update_metrics(self, **kwargs):
        """Update metrics fields."""
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)
                logger.debug(f"Metric updated [{key}]: {value}")
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get a summary of current status for debugging."""
        return {
            'status': self.status.value,
            'phase': self.current_phase,
            'run_id': self.run_id,
            'progress': f"{self.metrics.progress_percentage:.1f}%",
            'elapsed_time': f"{self.metrics.elapsed_time:.2f}s",
            'success_rate': f"{self.metrics.success_rate:.1f}%",
            'warnings_count': len(self.warnings),
            'has_error': self.error_message is not None
        }

