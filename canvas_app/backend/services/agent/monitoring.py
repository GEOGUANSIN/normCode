"""Tool Call Monitoring - Proxies and Events for tool call observation.

This module provides:
- ToolCallEvent: Event emitted when a tool method is called
- MonitoredToolProxy: Wraps tools to emit monitoring events

This enables the Agent Panel to show real-time tool call activity.
"""

import time
import uuid
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolCallEvent:
    """Event emitted when a tool method is called."""
    id: str
    timestamp: str
    flow_index: str
    agent_id: str
    tool_name: str
    method: str
    inputs: Dict[str, Any]
    outputs: Optional[Any] = None
    duration_ms: Optional[float] = None
    status: str = "started"  # started, completed, failed
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "flow_index": self.flow_index,
            "agent_id": self.agent_id,
            "tool_name": self.tool_name,
            "method": self.method,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
        }


class MonitoredToolProxy:
    """
    Proxy that wraps a tool to emit monitoring events for each method call.
    
    This allows the UI to see real-time tool call activity during execution.
    
    Usage:
        monitored_llm = MonitoredToolProxy(
            agent_id="default",
            tool_name="llm",
            tool=body.llm,
            emit_callback=emit_event,
            current_flow_index_getter=lambda: current_flow
        )
    """
    
    def __init__(
        self, 
        agent_id: str, 
        tool_name: str, 
        tool: Any, 
        emit_callback: Callable[[ToolCallEvent], None],
        current_flow_index_getter: Optional[Callable[[], str]] = None
    ):
        self._agent_id = agent_id
        self._tool_name = tool_name
        self._tool = tool
        self._emit_callback = emit_callback
        self._get_flow_index = current_flow_index_getter or (lambda: "")
    
    def __getattr__(self, name: str) -> Any:
        """Intercept attribute access to wrap method calls."""
        attr = getattr(self._tool, name)
        
        if callable(attr):
            return self._create_monitored_method(name, attr)
        return attr
    
    def _create_monitored_method(self, method_name: str, method: Callable) -> Callable:
        """Create a wrapped method that emits events."""
        def monitored_method(*args, **kwargs):
            event_id = str(uuid.uuid4())[:8]
            flow_index = self._get_flow_index()
            
            # Create start event
            start_event = ToolCallEvent(
                id=event_id,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                flow_index=flow_index,
                agent_id=self._agent_id,
                tool_name=self._tool_name,
                method=method_name,
                inputs=self._sanitize_inputs(args, kwargs),
                status="started",
            )
            self._emit_callback(start_event)
            
            start_time = time.time()
            try:
                result = method(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # If the result is a callable (like from create_function_executor),
                # wrap it so we can monitor when it's actually executed
                if callable(result) and not isinstance(result, type):
                    result = self._wrap_returned_callable(method_name, result)
                
                # Create completion event
                complete_event = ToolCallEvent(
                    id=event_id,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    flow_index=flow_index,
                    agent_id=self._agent_id,
                    tool_name=self._tool_name,
                    method=method_name,
                    inputs=start_event.inputs,
                    outputs=self._sanitize_output(result),
                    duration_ms=duration_ms,
                    status="completed",
                )
                self._emit_callback(complete_event)
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Create failure event
                fail_event = ToolCallEvent(
                    id=event_id,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    flow_index=flow_index,
                    agent_id=self._agent_id,
                    tool_name=self._tool_name,
                    method=method_name,
                    inputs=start_event.inputs,
                    duration_ms=duration_ms,
                    status="failed",
                    error=str(e),
                )
                self._emit_callback(fail_event)
                raise
        
        return monitored_method
    
    def _wrap_returned_callable(self, parent_method: str, fn: Callable) -> Callable:
        """
        Wrap a callable returned by a tool method (e.g., executor from create_function_executor).
        
        This ensures that when the returned function is later called (e.g., during composition),
        we emit monitoring events for that execution as well.
        """
        def wrapped_executor(*args, **kwargs):
            event_id = str(uuid.uuid4())[:8]
            flow_index = self._get_flow_index()
            
            # Derive a method name for the executor
            executor_name = f"{parent_method}→execute"
            
            # Create start event
            start_event = ToolCallEvent(
                id=event_id,
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                flow_index=flow_index,
                agent_id=self._agent_id,
                tool_name=self._tool_name,
                method=executor_name,
                inputs=self._sanitize_inputs(args, kwargs),
                status="started",
            )
            self._emit_callback(start_event)
            
            start_time = time.time()
            try:
                result = fn(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                # Create completion event
                complete_event = ToolCallEvent(
                    id=event_id,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    flow_index=flow_index,
                    agent_id=self._agent_id,
                    tool_name=self._tool_name,
                    method=executor_name,
                    inputs=start_event.inputs,
                    outputs=self._sanitize_output(result),
                    duration_ms=duration_ms,
                    status="completed",
                )
                self._emit_callback(complete_event)
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                # Create failure event
                fail_event = ToolCallEvent(
                    id=event_id,
                    timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"),
                    flow_index=flow_index,
                    agent_id=self._agent_id,
                    tool_name=self._tool_name,
                    method=executor_name,
                    inputs=start_event.inputs,
                    duration_ms=duration_ms,
                    status="failed",
                    error=str(e),
                )
                self._emit_callback(fail_event)
                raise
        
        return wrapped_executor
    
    def _sanitize_inputs(self, args: tuple, kwargs: dict) -> Dict[str, Any]:
        """Serialize inputs for logging, preserving full structure."""
        result = {}
        
        # Serialize all args
        for i, arg in enumerate(args):
            result[f"arg{i}"] = self._serialize_value(arg)
        
        # Serialize all kwargs
        for key, value in kwargs.items():
            result[key] = self._serialize_value(value)
        
        return result
    
    def _sanitize_output(self, output: Any) -> Any:
        """Create a safe summary of output for logging."""
        return self._serialize_value(output)
    
    def _serialize_value(self, value: Any, depth: int = 0, max_depth: int = 10, max_str_len: int = 50000) -> Any:
        """
        Serialize a value for logging, preserving full structure.
        
        Args:
            value: The value to serialize
            depth: Current recursion depth
            max_depth: Maximum recursion depth
            max_str_len: Maximum string length before truncation
        """
        if depth > max_depth:
            return f"<max depth exceeded>"
        
        if value is None:
            return None
        if isinstance(value, (bool, int, float)):
            return value
        if isinstance(value, str):
            if len(value) > max_str_len:
                return value[:max_str_len] + f"... [truncated, total {len(value)} chars]"
            return value
        if isinstance(value, bytes):
            return f"<bytes: {len(value)} bytes>"
        if isinstance(value, (list, tuple)):
            # Serialize list items
            serialized = []
            for i, item in enumerate(value):
                if i >= 100:  # Limit array items
                    serialized.append(f"... and {len(value) - 100} more items")
                    break
                serialized.append(self._serialize_value(item, depth + 1, max_depth, max_str_len))
            return serialized
        if isinstance(value, dict):
            # Serialize dict items
            serialized = {}
            for i, (k, v) in enumerate(value.items()):
                if i >= 50:  # Limit dict keys
                    serialized["..."] = f"{len(value) - 50} more keys"
                    break
                key = str(k) if not isinstance(k, str) else k
                serialized[key] = self._serialize_value(v, depth + 1, max_depth, max_str_len)
            return serialized
        # For other objects, try to get a useful representation
        if hasattr(value, '__dict__'):
            serialized_dict = self._serialize_value(value.__dict__, depth + 1, max_depth, max_str_len)
            if isinstance(serialized_dict, dict):
                return {
                    "_type": type(value).__name__,
                    **serialized_dict
                }
            else:
                return {"_type": type(value).__name__, "_value": serialized_dict}
        if hasattr(value, 'to_dict'):
            try:
                return self._serialize_value(value.to_dict(), depth + 1, max_depth, max_str_len)
            except Exception:
                pass
        # Fallback: string representation
        try:
            s = str(value)
            if len(s) > max_str_len:
                return s[:max_str_len] + f"... [truncated]"
            return s
        except Exception:
            return f"<{type(value).__name__}>"

