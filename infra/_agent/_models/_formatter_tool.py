"""
This module contains the FormatterTool, a collection of methods for various
data formatting, parsing, and extraction tasks used within the agent's
compositional framework.
"""
from typing import Any, Dict, Callable
from string import Template
import json
import uuid
import re

class FormatterTool:
    """A tool with methods for various data formatting and extraction tasks."""
    def create_template_function(self, template: str) -> Callable[[Dict[str, Any]], str]:
        """
        Factory method that takes a template string and returns a substitution function
        with that template 'baked in'.
        """
        def substitute_fn(vars: Dict[str, Any]) -> str:
            """Substitutes variables into the baked-in template string."""
            return Template(template).safe_substitute(vars)
        return substitute_fn
        
    def create_substitute_function(self, template_key: str) -> Callable[[Dict[str, Any]], str]:
        """
        Factory method that returns a substitute function bound to a specific template key.
        This mirrors how `create_generation_function_...` in the real implementation
        is configured with a `template_key`.
        """
        def substitute_fn(vars: Dict[str, Any]) -> str:
            """Substitutes variables into a template string passed within the vars."""
            if template_key not in vars:
                raise ValueError(f"'{template_key}' not found in vars")
            prompt_template = vars[template_key]
            substitution_vars = {k: v for k, v in vars.items() if k != template_key}
            return Template(str(prompt_template)).safe_substitute(substitution_vars)
        return substitute_fn

    def parse(self, raw_response: str) -> Dict[str, Any]:
        """
        Parses a JSON string into a Python dictionary.
        Handles errors gracefully if the input is not valid JSON.
        """
        if not isinstance(raw_response, str) or not raw_response.strip():
            return {"error": "Invalid input: received empty or non-string response for JSON parsing."}
        
        # Attempt to fix common LLM errors like escaping single quotes
        cleaned_response = raw_response.replace(r"\'", "'")
        
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            return {
                "raw_response": raw_response, # Log the original for debugging
                "error": "Failed to parse JSON response"
            }

    def get(self, dictionary: Dict, key: str, default: Any = None) -> Any:
        """Gets a value from a dictionary by key."""
        return dictionary.get(key, default)

    def wrap(self, data: Any, type: str | None = None) -> str:
        """Wraps the data in the normcode format %xxx() or %{type}xxx()."""
        unique_code = uuid.uuid4().hex[:3]
        if type:
            wrapped_data = f"%{{{type}}}{unique_code}({data})"
        else:
            wrapped_data = f"%{unique_code}({data})"
        print(f">>> MIA step: Wrapped data -> {wrapped_data}")
        return wrapped_data

    def wrap_list(self, data_list: list | tuple, type: str | None = None) -> list[str]:
        """Wraps each item in a list or tuple using the wrap method."""
        if not isinstance(data_list, (list, tuple)):
            # Return as is or raise an error if the input is not a list or tuple
            return data_list
        return [self.wrap(item, type) for item in data_list]

    def collect_script_inputs(self, all_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collects all key-value pairs from a dictionary where the key starts
        with the prefix 'input_'.
        """
        if not isinstance(all_inputs, dict):
            return {}
        
        script_inputs = {}
        for key, value in all_inputs.items():
            if key.startswith("input_"):
                script_inputs[key] = value
        return script_inputs

    def clean_code(self, raw_code: str) -> str:
        """Extracts code from a markdown block for python or json."""
        if not isinstance(raw_code, str):
            return ""
        # Use re.DOTALL to make '.' match newlines
        # Look for python, py, or json blocks
        code_blocks = re.findall(r"```(?:python|py|json)?\n(.*?)\n```", raw_code, re.DOTALL)
        if code_blocks:
            return code_blocks[0].strip()
        
        # If no markdown block is found, assume the whole thing is the code
        return raw_code.strip()
