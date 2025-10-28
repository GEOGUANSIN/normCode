import logging
from .base_agent import BaseAgent
from .data_agent import DataAgent
from .imperative_agent import ImperativeAgent
from .judgement_agent import JudgementAgent
from ..execution_state import ExecutionState

logger = logging.getLogger(__name__)


class ControllerAgent(BaseAgent):
    """The central agent that orchestrates the worker agents and manages state."""

    def __init__(self):
        super().__init__("ControllerAgent")
        self.data_agent = DataAgent()
        self.imperative_agent = ImperativeAgent()
        self.judgement_agent = JudgementAgent()

    def run(self, number1: int, number2: int):
        """
        Runs the multi-agent addition algorithm and produces a structured trace.

        Args:
            number1 (int): The first number to add.
            number2 (int): The second number to add.

        Returns:
            dict: The final execution trace.
        """
        # Initialize state to trace the execution as if running NormCode
        state = ExecutionState()
        
        # Initial values
        number_pair = [number1, number2]
        carry_over = 0
        remainders = []

        # The main loop, derived from '*every({number pair})' with quantifier @(1)
        q1_cycle = 1
        while True:
            # --- Start of Loop @(1), cycle {q1_cycle} ---

            # == First Inner Loop: Get unit place values ==
            # This corresponds to '*every({number pair})' with quantifier @(2)
            unit_place_values = []
            q2_cycle = 1
            for number in number_pair:
                # Flow Index: 1.1.2.4.2.1.2
                unit_digit = self.imperative_agent.execute(
                    operation="get_single_unit_place_digit",
                    number=number
                )
                key = f"1.1.2.4.2.1.2 (q1:{q1_cycle}, q2:{q2_cycle})"
                state.set(key, "{single unit place value}", unit_digit)
                unit_place_values.append(unit_digit)
                q2_cycle += 1
            
            # This corresponds to the grouping result from Flow Index 1.1.2.4
            key = f"1.1.2.4 (q1:{q1_cycle})"
            state.set(key, "[all {unit place value} of numbers]", unit_place_values)

            # Step 1.1.2: Calculate the digit sum
            digit_sum = self.imperative_agent.execute(
                operation="sum_and_carry",
                numbers=unit_place_values,
                carry_over=carry_over
            )
            key = f"1.1.2 (q1:{q1_cycle})"
            state.set(key, "{digit sum}", digit_sum)

            # Step 1.1.4: Get the remainder
            remainder = self.imperative_agent.execute(
                operation="get_remainder",
                digit_sum=digit_sum
            )
            key = f"1.1.4 (q1:{q1_cycle})"
            state.set(key, "{remainder}", remainder)
            remainders.insert(0, remainder)

            # Step 1.1.3.4.2.2: Calculate the new carry-over for the next iteration
            carry_over = self.imperative_agent.execute(
                operation="get_carry_over",
                digit_sum=digit_sum
            )
            key = f"1.1.3.4.2.2 (q1:{q1_cycle})"
            state.set(key, "{carry-over number}", carry_over)

            # == Second Inner Loop: Get numbers for next iteration ==
            # This corresponds to '*every({number pair})' with quantifier @(3)
            next_number_pair = []
            q3_cycle = 1
            for number in number_pair:
                # Flow Index: 1.1.3.2.1.2
                new_number = self.imperative_agent.execute(
                    operation="remove_last_digit",
                    number=number
                )
                key = f"1.1.3.2.1.2 (q1:{q1_cycle}, q3:{q3_cycle})"
                state.set(key, "{number with last digit removed}", new_number)
                next_number_pair.append(new_number)
                q3_cycle += 1
            
            number_pair = next_number_pair
            # This corresponds to the assignment result from Flow Index 1.1.3.2
            key = f"1.1.3.2 (q1:{q1_cycle})"
            state.set(key, "{number pair to append}", number_pair)

            # Step 1.1.3.3 & 1.1.3.4: Check termination conditions
            are_all_zero = self.judgement_agent.execute(
                operation="are_all_zero",
                values=number_pair
            )
            key = f"1.1.3.3 (q1:{q1_cycle})"
            state.set(key, "<all number is 0>", are_all_zero)

            is_carry_zero = self.judgement_agent.execute(
                operation="is_zero",
                value=carry_over
            )
            key = f"1.1.3.4 (q1:{q1_cycle})"
            state.set(key, "<carry-over number is 0>", is_carry_zero)

            if are_all_zero and is_carry_zero:
                break
            
            q1_cycle += 1

        # Construct final result string
        if carry_over > 0:
            remainders.insert(0, carry_over)
        
        final_sum = "".join(map(str, remainders)) if remainders else "0"
        state.set("result", "{final_sum}", final_sum)

        return state.get_full_trace()

    def execute(self, **kwargs):
        """Controller agent's execute method is the 'run' method."""
        num1 = kwargs.get("number1", 0)
        num2 = kwargs.get("number2", 0)
        return self.run(num1, num2)
