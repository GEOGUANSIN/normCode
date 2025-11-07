from .base_agent import BaseAgent
from ..tools import data_tools


class DataAgent(BaseAgent):
    def __init__(self):
        super().__init__("DataAgent")

    def group_across(self, *items):
        return data_tools.group_across(*items)
