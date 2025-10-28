from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Abstract base class for all agents in the system."""

    @abstractmethod
    def execute(self, state: dict) -> dict:
        """Execute the agent's logic and return the new state."""
        pass
