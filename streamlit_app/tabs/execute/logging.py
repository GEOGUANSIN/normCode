"""
Logging utilities for the Execute tab.
Provides structured logging for better debugging.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


class ExecutionLogger:
    """Structured logger for execution tracking."""
    
    def __init__(self, run_id: Optional[str] = None):
        """
        Initialize execution logger.
        
        Args:
            run_id: Run ID for logging context
        """
        self.run_id = run_id
        self.log_entries = []
    
    def log_phase(self, phase: str, message: str, level: str = "INFO"):
        """Log a phase transition."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'phase',
            'run_id': self.run_id,
            'phase': phase,
            'message': message,
            'level': level
        }
        self.log_entries.append(entry)
        
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[{self.run_id}] Phase: {phase} - {message}")
    
    def log_metric(self, metric_name: str, value: Any):
        """Log a metric value."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'metric',
            'run_id': self.run_id,
            'metric': metric_name,
            'value': value
        }
        self.log_entries.append(entry)
        logger.debug(f"[{self.run_id}] Metric: {metric_name}={value}")
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """Log an error with context."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'error',
            'run_id': self.run_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        }
        self.log_entries.append(entry)
        logger.error(f"[{self.run_id}] Error: {type(error).__name__} - {str(error)}", exc_info=True)
    
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log a general event."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'event',
            'run_id': self.run_id,
            'event_type': event_type,
            'data': data
        }
        self.log_entries.append(entry)
        logger.info(f"[{self.run_id}] Event: {event_type} - {data}")
    
    def get_logs(self) -> list[Dict[str, Any]]:
        """Get all log entries."""
        return self.log_entries.copy()
    
    def get_logs_by_type(self, log_type: str) -> list[Dict[str, Any]]:
        """Get log entries filtered by type."""
        return [entry for entry in self.log_entries if entry['type'] == log_type]
    
    def export_to_dict(self) -> Dict[str, Any]:
        """Export logs to dictionary for serialization."""
        return {
            'run_id': self.run_id,
            'total_entries': len(self.log_entries),
            'entries': self.log_entries
        }


def log_execution_step(step_name: str):
    """
    Decorator to log execution steps with timing.
    
    Args:
        step_name: Name of the execution step
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.info(f"Starting: {step_name}")
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"Completed: {step_name} in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"Failed: {step_name} after {duration:.2f}s - {str(e)}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.info(f"Starting: {step_name}")
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"Completed: {step_name} in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"Failed: {step_name} after {duration:.2f}s - {str(e)}")
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def format_debug_info(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format debug information for readable logging.
    
    Args:
        data: Data to format
        indent: Indentation level
    
    Returns:
        Formatted string
    """
    import json
    try:
        return json.dumps(data, indent=indent, default=str)
    except Exception:
        return str(data)

