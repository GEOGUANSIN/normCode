from multi_agent_experiement2.love_inquiry_system.concepts import NormCodeConcept
from multi_agent_experiement2.love_inquiry_system.agents.base_agent import BaseAgent

class InputAgent(BaseAgent):
    """
    An agent responsible for handling Input concepts (e.g., :>:{...}?).
    """
    def execute(self, concept: NormCodeConcept, orchestrator: 'OrchestratorAgent') -> NormCodeConcept:
        """
        Processes an Input concept.

        For now, this simulates getting input from a user. In a real system,
        this might involve a CLI prompt, a web form, or an API call.
        """
        print(f"    [InputAgent]: Requesting input for concept '{concept.name}'.")
        print(f"    [InputAgent]: Prompt: {concept.question}")

        # Placeholder logic: We'll use a dummy value.
        dummy_input = f"user_provided_{concept.name.strip('{}?')}"
        concept.value = dummy_input

        print(f"    [InputAgent]: Input received. Value set to: '{dummy_input}'")

        return concept
