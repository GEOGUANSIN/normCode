from .base_agent import BaseAgent


class JudgementAgent(BaseAgent):
    """Agent responsible for logical judgements and conditions."""

    def __init__(self):
        super().__init__("JudgementAgent")

    def execute(self, operation: str, **kwargs):
        """
        Executes a judgement operation.

        Args:
            operation (str): The name of the judgement to perform.
            **kwargs: Arguments for the judgement.

        Returns:
            bool: The result of the judgement.
        """
        if operation == "is_zero":
            # Corresponds to: <{...} is 0>
            value = kwargs.get("value")
            return value == 0
        elif operation == "are_all_zero":
            # Corresponds to: <all number is 0>
            values = kwargs.get("values", [])
            return all(v == 0 for v in values)
        else:
            raise NotImplementedError(f"Operation '{operation}' not implemented in JudgementAgent.")
