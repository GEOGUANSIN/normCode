from abc import ABC, abstractmethod
from multi_agent_experiement2.love_inquiry_system.concepts import NormCodeConcept

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    """
    @abstractmethod
    def execute(self, concept: NormCodeConcept, orchestrator: 'OrchestratorAgent') -> NormCodeConcept:
        """
        Executes the agent's logic on a given concept.

        Args:
            concept: The NormCodeConcept to process.
            orchestrator: The main orchestrator instance, allowing agents to delegate tasks.

        Returns:
            The processed (potentially modified) concept.
        """
        pass
