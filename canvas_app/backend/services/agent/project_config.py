"""Project Agent Configuration Service.

This module provides functionality to load and save project-specific
agent configuration files (.agent.json).

These files contain:
- Agent definitions specific to a project
- Mapping rules for inference-to-agent routing
- Optional project-specific LLM provider configurations
"""

import json
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple

from .config import (
    ProjectAgentConfig,
    AgentConfig,
    AgentToolsConfig,
    LLMToolConfig,
    ParadigmToolConfig,
    MappingRule,
    LLMProviderRef,
    AGENT_CONFIG_SUFFIX,
    get_agent_config_filename,
)

logger = logging.getLogger(__name__)


class ProjectAgentConfigService:
    """
    Service for managing project-specific agent configuration files.
    
    Handles loading, saving, and discovering .agent.json files.
    """
    
    def load_config(self, config_path: Path) -> ProjectAgentConfig:
        """
        Load a project agent configuration from a file.
        
        Args:
            config_path: Path to the .agent.json file
            
        Returns:
            The loaded ProjectAgentConfig
            
        Raises:
            FileNotFoundError: If the config file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Agent config not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        config = ProjectAgentConfig.from_dict(data)
        logger.info(f"Loaded project agent config from {config_path} with {len(config.agents)} agents")
        return config
    
    def save_config(self, config: ProjectAgentConfig, config_path: Path):
        """
        Save a project agent configuration to a file.
        
        Args:
            config: The configuration to save
            config_path: Path to save to
        """
        # Update timestamp
        config.updated_at = datetime.now().isoformat()
        if not config.created_at:
            config.created_at = config.updated_at
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to file
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, indent=2)
        
        logger.info(f"Saved project agent config to {config_path}")
    
    def find_agent_configs(self, project_dir: Path) -> list[str]:
        """
        Find all agent config files in a project directory.
        
        Returns:
            List of agent config filenames
        """
        if not project_dir.exists():
            return []
        
        configs = []
        for f in project_dir.iterdir():
            if f.is_file() and f.name.endswith(AGENT_CONFIG_SUFFIX):
                configs.append(f.name)
        
        return sorted(configs)
    
    def get_agent_config_path(
        self,
        project_dir: Path,
        agent_config_ref: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Get the path to a project's agent config file.
        
        Args:
            project_dir: The project directory
            agent_config_ref: Explicit reference from ExecutionSettings.agent_config
            project_name: Project name (used to derive filename if not explicit)
            
        Returns:
            Path to the agent config file, or None if not found
        """
        # If explicitly specified, use that
        if agent_config_ref:
            path = project_dir / agent_config_ref
            if path.exists():
                return path
            logger.warning(f"Agent config not found: {path}")
        
        # Try to find by project name
        if project_name:
            filename = get_agent_config_filename(project_name)
            path = project_dir / filename
            if path.exists():
                return path
        
        # Try to find any agent config in the directory
        configs = self.find_agent_configs(project_dir)
        if configs:
            return project_dir / configs[0]
        
        return None
    
    def load_for_project(
        self,
        project_dir: Path,
        agent_config_ref: Optional[str] = None,
        project_name: Optional[str] = None,
    ) -> Tuple[Optional[ProjectAgentConfig], Optional[Path]]:
        """
        Load agent config for a project, if one exists.
        
        Args:
            project_dir: The project directory
            agent_config_ref: Explicit reference from ExecutionSettings.agent_config
            project_name: Project name (used to derive filename if not explicit)
            
        Returns:
            Tuple of (config, config_path), or (None, None) if not found
        """
        config_path = self.get_agent_config_path(
            project_dir, agent_config_ref, project_name
        )
        
        if config_path is None:
            return None, None
        
        try:
            config = self.load_config(config_path)
            return config, config_path
        except Exception as e:
            logger.error(f"Failed to load agent config {config_path}: {e}")
            return None, None
    
    def create_default_config(
        self,
        project_dir: Path,
        project_name: str,
        default_llm_model: str = "demo",
        paradigm_dir: Optional[str] = None,
    ) -> Tuple[ProjectAgentConfig, Path]:
        """
        Create a default agent config for a project.
        
        Args:
            project_dir: The project directory
            project_name: Project name
            default_llm_model: Default LLM model to use
            paradigm_dir: Optional paradigm directory
            
        Returns:
            Tuple of (config, config_path)
        """
        # Create default agent with tool-centric structure
        tools = AgentToolsConfig(
            llm=LLMToolConfig(model=default_llm_model),
            paradigm=ParadigmToolConfig(dir=paradigm_dir),
        )
        
        default_agent = AgentConfig(
            id="default",
            name=f"{project_name} Agent",
            description=f"Default agent for {project_name}",
            tools=tools,
        )
        
        config = ProjectAgentConfig(
            default_agent="default",
            agents=[default_agent],
            description=f"Agent configuration for {project_name}",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        
        filename = get_agent_config_filename(project_name)
        config_path = project_dir / filename
        
        self.save_config(config, config_path)
        
        return config, config_path
    
    def resolve_env_vars(self, value: str) -> str:
        """
        Resolve environment variable references in a string.
        
        Supports ${VAR_NAME} syntax.
        """
        import re
        
        def replace_env(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        
        return re.sub(r'\$\{([^}]+)\}', replace_env, value)
    
    def resolve_llm_provider(self, provider_ref: LLMProviderRef) -> dict:
        """
        Resolve an LLM provider reference to actual configuration.
        
        Handles:
        - Environment variable substitution for api_key
        - Global provider lookups by ID or name
        - Inline provider configurations
        
        Returns:
            Dict with resolved provider configuration
        """
        if provider_ref.provider_id or provider_ref.provider_name:
            # Look up global provider
            from .llm_providers import llm_settings_service
            
            if provider_ref.provider_id:
                global_provider = llm_settings_service.get_provider(provider_ref.provider_id)
            else:
                global_provider = llm_settings_service.get_provider_by_name(provider_ref.provider_name)
            
            if global_provider:
                return {
                    "provider": global_provider.provider.value,
                    "api_key": global_provider.api_key,
                    "base_url": global_provider.base_url,
                    "model": global_provider.model,
                    "temperature": global_provider.temperature,
                    "max_tokens": global_provider.max_tokens,
                }
            else:
                logger.warning(f"Global provider not found: {provider_ref.provider_id or provider_ref.provider_name}")
        
        # Inline provider - resolve env vars
        api_key = provider_ref.api_key
        if api_key:
            api_key = self.resolve_env_vars(api_key)
        
        return {
            "provider": provider_ref.provider_type,
            "api_key": api_key,
            "base_url": provider_ref.base_url,
            "model": provider_ref.model,
            "temperature": provider_ref.temperature,
            "max_tokens": provider_ref.max_tokens,
        }


# Global service instance
project_agent_config_service = ProjectAgentConfigService()

