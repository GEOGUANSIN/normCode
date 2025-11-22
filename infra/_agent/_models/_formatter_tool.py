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
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            return {
                "raw_response": raw_response,
                "error": "Failed to parse JSON response"
            }

    def get(self, dictionary: Dict, key: str) -> Any:
        """Gets a value from a dictionary by key."""
        return dictionary.get(key)

    def wrap(self, data: Any, type: str | None = None) -> str:
        """Wraps the data in the normcode format %xxx() or %{type}xxx()."""
        unique_code = uuid.uuid4().hex[:3]
        if type:
            wrapped_data = f"%{{{type}}}{unique_code}({data})"
        else:
            wrapped_data = f"%{unique_code}({data})"
        print(f">>> MIA step: Wrapped data -> {wrapped_data}")
        return wrapped_data

    def clean_code(self, raw_code: str) -> str:
        """Extracts Python code from a markdown block."""
        if not isinstance(raw_code, str):
            return ""
        # Use re.DOTALL to make '.' match newlines
        code_blocks = re.findall(r"```(?:python|py)?\n(.*?)\n```", raw_code, re.DOTALL)
        return code_blocks[0].strip() if code_blocks else raw_code.strip()
