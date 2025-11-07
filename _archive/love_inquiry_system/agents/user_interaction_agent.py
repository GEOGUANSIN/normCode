from .base_agent import BaseAgent

class UserInteractionAgent(BaseAgent):
    """Agent responsible for handling direct communication with the user."""

    def execute(self, state: dict) -> dict:
        # This agent might be simpler and not follow the execute model strictly
        # It could have methods like ask_question and get_input
        print("UserInteractionAgent is executing...")
        return state

    def ask_question(self, question: str) -> str:
        """Asks a question to the user and returns their response."""
        print(f"AI: {question}")
        response = input("You: ")
        return response
