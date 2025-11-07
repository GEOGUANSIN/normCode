from .base_agent import BaseAgent
from ..tools import math_tools, data_tools
from ..models.language_models import LanguageModel


class ImperativeAgent(BaseAgent):
    """Agent responsible for executing imperative commands, including calculations."""

    def __init__(self, llm: LanguageModel = None):
        super().__init__("ImperativeAgent")
        self.llm = llm

    def execute(self, operation: str, **kwargs):
        """
        Executes an imperative command.

        Args:
            operation (str): The name of the command to execute.
            **kwargs: Arguments for the command.

        Returns:
            The result of the command.
        """
        if operation == "sum_and_carry":
            # Corresponds to: ::(sum ... and {carry-over number}...)
            numbers_to_sum = kwargs.get("numbers", [])
            carry_over = kwargs.get("carry_over", 0)
            all_numbers = numbers_to_sum + [carry_over]
            return math_tools.sum_numbers(all_numbers)
        elif operation == "get_remainder":
            # Corresponds to: ::(get the {remainder} of {digit sum}...)
            digit_sum = kwargs.get("digit_sum")
            return math_tools.get_remainder(digit_sum, 10)
        elif operation == "get_carry_over":
            # Corresponds to: ::(find the {quotient} of {digit sum}...)
            digit_sum = kwargs.get("digit_sum")
            return math_tools.get_quotient(digit_sum, 10)
        elif operation == "get_single_unit_place_digit":
            # Corresponds to: ::(get {unit place value} of {number})
            number = kwargs.get("number")
            return data_tools.get_unit_place_digit(number)
        elif operation == "remove_last_digit":
            # Corresponds to: ::(output 0 if {number} is less than 10, otherwise remove...)
            number = kwargs.get("number")
            return data_tools.remove_last_digit_from_number(number)
        else:
            # Here you could use self.llm to interpret more complex natural language imperatives
            raise NotImplementedError(f"Operation '{operation}' not implemented in ImperativeAgent.")
