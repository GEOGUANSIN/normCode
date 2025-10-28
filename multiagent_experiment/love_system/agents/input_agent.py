from .base_agent import BaseAgent
from ..tools import input_tools


class InputAgent(BaseAgent):
    def __init__(self):
        super().__init__("InputAgent")

    def extract_concepts(self, text: str) -> dict:
        return input_tools.extract_love_concepts(text)
