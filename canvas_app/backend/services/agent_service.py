"""Agent Registry and Customization Service.

This module provides:
1. AgentConfig - Configuration dataclass for agent/body customization
2. AgentRegistry - Registry of agent configurations and Body instances
3. AgentMappingService - Maps inferences to agents based on rules
4. MonitoredToolProxy - Wraps tools to emit monitoring events
"""

import re
import time
import logging
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for a single agent."""
    id: str
    name: str
    description: str = ""
    
    # LLM config
    llm_model: str = "qwen-plus"
    
    # Tool config
    file_system_enabled: bool = True
    file_system_base_dir: Optional[str] = None
    python_interpreter_enabled: bool = True
    python_interpreter_timeout: int = 30
    user_input_enabled: bool = True
    user_input_mode: str = "blocking"  # blocking, async, disabled
    
    # Paradigm config
    paradigm_dir: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "llm_model": self.llm_model,
            "file_system_enabled": self.file_system_enabled,
            "file_system_base_dir": self.file_system_base_dir,
            "python_interpreter_enabled": self.python_interpreter_enabled,
            "python_interpreter_timeout": self.python_interpreter_timeout,
            "user_input_enabled": self.user_input_enabled,
            "user_input_mode": self.user_input_mode,
            "paradigm_dir": self.paradigm_dir,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            llm_model=data.get("llm_model", "qwen-plus"),
            file_system_enabled=data.get("file_system_enabled", True),
            file_system_base_dir=data.get("file_system_base_dir"),
            python_interpreter_enabled=data.get("python_interpreter_enabled", True),
            python_interpreter_timeout=data.get("python_interpreter_timeout", 30),
            user_input_enabled=data.get("user_input_enabled", True),
            user_input_mode=data.get("user_input_mode", "blocking"),
            paradigm_dir=data.get("paradigm_dir"),
        )


@dataclass
class MappingRule:
    """Rule for mapping inferences to agents."""
    match_type: str  # 'flow_index', 'concept_name', 'sequence_type'
    pattern: str     # Regex pattern
    agent_id: str
    priority: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "match_type": self.match_type,
            "pattern": self.pattern,
            "agent_id": self.agent_id,
            "priority": self.priority,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MappingRule':
        return cls(
            match_type=data.get("match_type", "flow_index"),
            pattern=data.get("pattern", ".*"),
            agent_id=data.get("agent_id", "default"),
            priority=data.get("priority", 0),
        )


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


class AgentMappingService:
    """Maps inferences to agents based on rules."""
    
    def __init__(self):
        self.rules: List[MappingRule] = []
        self.explicit: Dict[str, str] = {}  # flow_index → agent_id
        self.default_agent: str = "default"
    
    def add_rule(self, rule: MappingRule) -> None:
        """Add a mapping rule."""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: -r.priority)
    
    def remove_rule(self, index: int) -> None:
        """Remove a rule by index."""
        if 0 <= index < len(self.rules):
            self.rules.pop(index)
    
    def clear_rules(self) -> None:
        """Clear all rules."""
        self.rules = []
    
    def set_explicit(self, flow_index: str, agent_id: str) -> None:
        """Set explicit agent assignment for an inference."""
        self.explicit[flow_index] = agent_id
    
    def clear_explicit(self, flow_index: str) -> None:
        """Remove explicit assignment."""
        self.explicit.pop(flow_index, None)
    
    def clear_all_explicit(self) -> None:
        """Clear all explicit assignments."""
        self.explicit = {}
    
    def get_agent_for_inference(
        self,
        flow_index: str,
        concept_name: Optional[str] = None,
        sequence_type: Optional[str] = None
    ) -> str:
        """Determine which agent should handle an inference."""
        
        # Check explicit assignment first
        if flow_index in self.explicit:
            return self.explicit[flow_index]
        
        # Check rules
        for rule in self.rules:
            if self._matches_rule(rule, flow_index, concept_name, sequence_type):
                return rule.agent_id
        
        return self.default_agent
    
    def _matches_rule(
        self,
        rule: MappingRule,
        flow_index: str,
        concept_name: Optional[str],
        sequence_type: Optional[str]
    ) -> bool:
        """Check if rule matches the inference."""
        value = {
            'flow_index': flow_index,
            'concept_name': concept_name or '',
            'sequence_type': sequence_type or ''
        }.get(rule.match_type, '')
        
        try:
            return bool(re.match(rule.pattern, value))
        except re.error:
            logger.warning(f"Invalid regex pattern in rule: {rule.pattern}")
            return False
    
    def get_state(self) -> Dict[str, Any]:
        """Get current mapping state."""
        return {
            "rules": [r.to_dict() for r in self.rules],
            "explicit": self.explicit.copy(),
            "default_agent": self.default_agent,
        }


class AgentRegistry:
    """
    Registry of agent configurations and Body instances.
    
    Manages multiple agent configurations and creates Body instances
    with the appropriate tools and settings.
    """
    
    def __init__(self, default_base_dir: str = "."):
        self.default_base_dir = default_base_dir
        self.configs: Dict[str, AgentConfig] = {}
        self.bodies: Dict[str, Any] = {}  # Body instances (lazy-created)
        self.tool_callbacks: Dict[str, Callable[[ToolCallEvent], None]] = {}
        self.tool_call_history: List[ToolCallEvent] = []
        self.max_history: int = 500
        
        # Flow index tracking for tool monitoring
        self._current_flow_index: str = ""
        
        # Create default agent
        self.register(AgentConfig(id="default", name="Default Agent"))
    
    def register(self, config: AgentConfig) -> None:
        """Register an agent configuration."""
        self.configs[config.id] = config
        # Invalidate cached body
        if config.id in self.bodies:
            del self.bodies[config.id]
        logger.info(f"Registered agent: {config.id} ({config.llm_model})")
    
    def unregister(self, agent_id: str) -> bool:
        """Unregister an agent. Returns True if agent was found and removed."""
        if agent_id == "default":
            logger.warning("Cannot unregister default agent")
            return False
        
        if agent_id in self.configs:
            del self.configs[agent_id]
            if agent_id in self.bodies:
                del self.bodies[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False
    
    def get_config(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID."""
        return self.configs.get(agent_id)
    
    def list_agents(self) -> List[AgentConfig]:
        """List all registered agent configurations."""
        return list(self.configs.values())
    
    def set_current_flow_index(self, flow_index: str) -> None:
        """Set the current flow index for tool call tracking."""
        self._current_flow_index = flow_index
    
    def get_body(self, agent_id: str) -> Any:
        """Get or create Body instance for agent."""
        if agent_id not in self.bodies:
            config = self.configs.get(agent_id)
            if not config:
                logger.warning(f"Unknown agent '{agent_id}', using default")
                config = self.configs.get("default")
                if not config:
                    raise ValueError("No default agent configured")
            self.bodies[agent_id] = self._create_body(config)
        return self.bodies[agent_id]
    
    def _create_body(self, config: AgentConfig) -> Any:
        """Create Body instance from config with monitored tools."""
        try:
            from infra._agent._body import Body
        except ImportError:
            logger.error("Could not import Body from infra")
            raise
        
        base_dir = config.file_system_base_dir or self.default_base_dir
        
        # Create custom paradigm tool if specified
        paradigm_tool = None
        if config.paradigm_dir:
            paradigm_tool = self._create_paradigm_tool(config.paradigm_dir, base_dir)
        
        # Create body
        body = Body(
            llm_name=config.llm_model,
            base_dir=base_dir,
            paradigm_tool=paradigm_tool
        )
        
        # Wrap tools with monitoring proxies
        def get_flow_index():
            return self._current_flow_index
        
        body.llm = MonitoredToolProxy(
            config.id, "llm", body.llm, 
            self._emit_tool_event, get_flow_index
        )
        body.file_system = MonitoredToolProxy(
            config.id, "file_system", body.file_system,
            self._emit_tool_event, get_flow_index
        )
        body.python_interpreter = MonitoredToolProxy(
            config.id, "python_interpreter", body.python_interpreter,
            self._emit_tool_event, get_flow_index
        )
        body.prompt_tool = MonitoredToolProxy(
            config.id, "prompt", body.prompt_tool,
            self._emit_tool_event, get_flow_index
        )
        
        logger.info(f"Created body for agent '{config.id}' with LLM={config.llm_model}")
        return body
    
    def _create_paradigm_tool(self, paradigm_dir: str, base_dir: str) -> Any:
        """Create a custom paradigm tool for the specified directory."""
        from services.execution_service import CustomParadigmTool
        
        paradigm_path = Path(paradigm_dir)
        if not paradigm_path.is_absolute():
            paradigm_path = Path(base_dir) / paradigm_dir
        
        if paradigm_path.exists() and paradigm_path.is_dir():
            return CustomParadigmTool(paradigm_path)
        
        logger.warning(f"Paradigm directory not found: {paradigm_path}")
        return None
    
    def _emit_tool_event(self, event: ToolCallEvent) -> None:
        """Emit tool call event to registered callbacks."""
        # Store in history
        self.tool_call_history.append(event)
        if len(self.tool_call_history) > self.max_history:
            self.tool_call_history = self.tool_call_history[-self.max_history:]
        
        # Notify all callbacks
        for callback in self.tool_callbacks.values():
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Tool event callback error: {e}")
    
    def register_tool_callback(self, callback_id: str, callback: Callable[[ToolCallEvent], None]) -> None:
        """Register callback for tool call events."""
        self.tool_callbacks[callback_id] = callback
    
    def unregister_tool_callback(self, callback_id: str) -> None:
        """Unregister a tool call callback."""
        self.tool_callbacks.pop(callback_id, None)
    
    def get_tool_call_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent tool call events."""
        return [e.to_dict() for e in self.tool_call_history[-limit:]]
    
    def clear_tool_call_history(self) -> None:
        """Clear tool call history."""
        self.tool_call_history = []
    
    def invalidate_all_bodies(self) -> None:
        """Clear all cached Body instances (force recreation on next access)."""
        self.bodies = {}
    
    def update_base_dir(self, base_dir: str) -> None:
        """Update the default base directory and invalidate all bodies."""
        self.default_base_dir = base_dir
        self.invalidate_all_bodies()


# Global instances
agent_registry = AgentRegistry()
agent_mapping = AgentMappingService()

