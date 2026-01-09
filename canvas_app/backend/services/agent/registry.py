"""Agent Registry - Manages agent configurations and Body instances.

This module provides AgentRegistry which:
1. Stores and manages AgentConfig instances
2. Creates Body instances with appropriate tool configuration
3. Wraps Body tools with monitoring proxies
4. Manages tool call history for debugging
5. Loads project-specific agent configurations
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List

from .config import AgentConfig, ProjectAgentConfig, MappingRule
from .monitoring import MonitoredToolProxy, ToolCallEvent

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry of agent configurations and Body instances.
    
    Manages multiple agent configurations and creates Body instances
    with the appropriate tools and settings.
    
    Usage:
        registry = AgentRegistry(default_base_dir="/path/to/project")
        registry.register(AgentConfig(id="my-agent", name="My Agent"))
        body = registry.get_body("my-agent")
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
        # Invalidate cached body if it exists
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
        
        # Create body with LLM model name
        # Note: The actual LLM configuration (API key, base_url, etc.) is resolved
        # by the Body class using llm_settings_service
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
        from services.execution.paradigm_tool import CustomParadigmTool
        
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
    
    # =========================================================================
    # Project-Specific Agent Configuration
    # =========================================================================
    
    def load_project_agents(
        self,
        project_dir: Path,
        agent_config_ref: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> Optional[ProjectAgentConfig]:
        """
        Load project-specific agent configuration.
        
        This loads agents from a .agent.json file and registers them,
        replacing any existing agents with the same IDs.
        
        Args:
            project_dir: The project directory
            agent_config_ref: Explicit path to agent config (from ExecutionSettings)
            project_name: Project name (used to find config if not explicit)
            
        Returns:
            The loaded ProjectAgentConfig, or None if not found
        """
        from .project_config import project_agent_config_service
        
        config, config_path = project_agent_config_service.load_for_project(
            project_dir, agent_config_ref, project_name
        )
        
        if config is None:
            return None
        
        # Register agents from the config
        for agent in config.agents:
            self.register(agent)
            logger.info(f"Loaded project agent: {agent.id} ({agent.name})")
        
        # Apply mappings (import mapping service here to avoid circular import)
        if config.mappings:
            from .mapping import agent_mapping
            for rule in config.mappings:
                agent_mapping.add_rule(rule)
                logger.info(f"Loaded project mapping rule: {rule.match_type}={rule.pattern} -> {rule.agent_id}")
        
        # Set default agent if specified
        if config.default_agent:
            from .mapping import agent_mapping
            agent_mapping.default_agent = config.default_agent
            logger.info(f"Set project default agent: {config.default_agent}")
        
        logger.info(f"Loaded project agent config from {config_path}")
        return config
    
    def unload_project_agents(self, project_config: ProjectAgentConfig) -> None:
        """
        Unload project-specific agents.
        
        Removes agents that were loaded from a project config,
        and clears any associated mappings.
        
        Args:
            project_config: The config that was loaded
        """
        from .mapping import agent_mapping
        
        # Unregister agents
        for agent in project_config.agents:
            if agent.id != "default":  # Never unregister default
                self.unregister(agent.id)
        
        # Clear mapping rules (we don't track which came from project, so clear all)
        # In a more sophisticated implementation, we'd track rule origins
        agent_mapping.clear_rules()
        agent_mapping.default_agent = "default"
        
        logger.info("Unloaded project agent configuration")
    
    def get_project_agent_or_default(self, agent_id: str) -> AgentConfig:
        """
        Get an agent config, falling back to default if not found.
        
        Args:
            agent_id: The agent ID to look up
            
        Returns:
            The agent config (or default if not found)
        """
        config = self.get_config(agent_id)
        if config is None:
            config = self.get_config("default")
        if config is None:
            # Create a minimal default
            config = AgentConfig(id="default", name="Default Agent")
        return config


# Global instance
agent_registry = AgentRegistry()

