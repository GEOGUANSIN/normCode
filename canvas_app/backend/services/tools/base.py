"""
Base Tool Interface.

All tools that can be injected into an agent's body should implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ToolMetadata:
    """Metadata about a tool."""
    name: str
    description: str
    version: str = "1.0.0"
    author: str = "normcode"
    tags: list = field(default_factory=list)


class BaseTool(ABC):
    """
    Base interface for all injectable tools.
    
    Tools are independent components that can be:
    - Configured with settings
    - Injected into an agent's body
    - Monitored for their execution
    """
    
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Return tool metadata."""
        pass
    
    @property
    @abstractmethod
    def is_enabled(self) -> bool:
        """Whether this tool is enabled."""
        pass
    
    @abstractmethod
    def configure(self, settings: Dict[str, Any]) -> None:
        """
        Configure the tool with settings.
        
        This is called before the tool is injected into the body.
        Settings come from the agent's tool configuration.
        """
        pass
    
    def validate_settings(self, settings: Dict[str, Any]) -> Optional[str]:
        """
        Validate settings before applying them.
        
        Returns None if valid, or an error message if invalid.
        """
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize tool state to dict (for persistence/debugging)."""
        return {
            "name": self.metadata.name,
            "enabled": self.is_enabled,
        }

