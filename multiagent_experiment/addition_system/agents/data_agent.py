from .base_agent import BaseAgent


class DataAgent(BaseAgent):
    """
    Agent responsible for data structuring and manipulation.
    In this system, the grouping operations (&across) are interpreted as
    control flow instructions for the ControllerAgent, which performs the loops.
    """

    def __init__(self):
        super().__init__("DataAgent")

    def execute(self, operation: str, **kwargs):
        """
        Executes a data manipulation operation.
        Note: For this specific NormCode, looping is handled by the Controller.
        """
        # The controller now handles the iteration implied by '&across'
        # This agent could be used for more complex data transformations.
        raise NotImplementedError(f"Operation '{operation}' is handled by the Controller's loops.")
