import sys
import logging
from typing import Callable, Any, Dict

logger = logging.getLogger(__name__)

class UserInputTool:
    def create_input_function(self, prompt_key: str = "prompt_text") -> Callable:
        """
        Creates a function that prompts the user for input.
        The function expects keyword arguments that will be used as the vars dictionary.
        """
        def input_fn(**kwargs: Any) -> str:
            """
            The actual function that will be called at runtime to get user input.
            """
            vars_dict = kwargs or {}
            logger.debug(f"UserInputTool.input_fn received vars: {vars_dict}")
            logger.debug(f"UserInputTool.input_fn using prompt_key: '{prompt_key}'")

            prompt_text = vars_dict.get(prompt_key, "Enter input: ")
            logger.debug(f"UserInputTool.input_fn resolved prompt: '{prompt_text.strip()}'")

            # This version checks if stdin is a TTY. If not, it returns a default.
            is_interactive = sys.stdin.isatty()
            logger.debug(f"Is interactive session (isatty): {is_interactive}")
            
            if is_interactive:
                return input(prompt_text)
            else:
                logging.warning("Non-interactive session detected. Returning default input.")
                return "Default response for non-interactive mode."
            
        return input_fn
