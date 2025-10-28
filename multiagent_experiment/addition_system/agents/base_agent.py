from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, **kwargs):
        """The main execution method for the agent."""
        pass
