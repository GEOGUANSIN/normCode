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
import logging

logger = logging.getLogger(__name__)

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

    def create_smart_substitute_function(self, template_key: str, combine_to_key: str) -> Callable[[Dict[str, Any]], str]:
        """
        Factory method for a "smart" substitution that automatically bundles unused inputs.
        
        Args:
            template_key: Key for the template string.
            combine_to_key: The key (e.g. 'input_other') where all unused 'input_n' variables
                            will be combined.
        """
        def substitute_fn(vars: Dict[str, Any]) -> str:
            if template_key not in vars:
                raise ValueError(f"'{template_key}' not found in vars")
            
            prompt_template = str(vars[template_key])
            substitution_vars = {k: v for k, v in vars.items() if k != template_key}

            # 1. Detect used input variables in the template
            # We look for $input_n or ${input_n}
            used_vars = set(re.findall(r'\$\{?(input_\d+)\}?', prompt_template))
            
            # 2. Identify unused input variables available in the data
            # unused_inputs = []  <-- Remove this list, we'll build the combined string directly
            combined_parts = []
            
            sorted_keys = sorted([k for k in substitution_vars.keys() if k.startswith("input_")])
            
            file_counter = 1
            for k in sorted_keys:
                if k not in used_vars:
                    val = substitution_vars[k]
                    
                    # Handle dictionary input from branching
                    if isinstance(val, dict):
                        # Look for a "content-like" key to use as inner text
                        content_keys = ["content", "data", "text", "body"]
                        content_text = None
                        attrs = {}
                        
                        for key, value in val.items():
                            if key in content_keys:
                                content_text = str(value)
                            else:
                                # All other keys become XML attributes
                                attrs[key] = str(value)
                        
                        # Build attribute string
                        attr_str = "".join([f' {k}="{v}"' for k, v in attrs.items()])
                        
                        # Format based on whether we have content
                        if content_text is not None:
                            combined_parts.append(f"<file_{file_counter}{attr_str}>\n{content_text}\n</file_{file_counter}>")
                        else:
                            # No content key found, all values are attributes (self-closing tag)
                            combined_parts.append(f"<file_{file_counter}{attr_str} />")
                    else:
                        # Plain string value
                        content_text = str(val)
                        combined_parts.append(f"<file_{file_counter}>\n{content_text}\n</file_{file_counter}>")
                    
                    file_counter += 1
            
            # 3. Combine them into the special key
            if combined_parts:
                substitution_vars[combine_to_key] = "\n\n".join(combined_parts)
            else:
                # If key doesn't exist yet, initialize it as empty string
                if combine_to_key not in substitution_vars:
                    substitution_vars[combine_to_key] = ""

            return Template(prompt_template).safe_substitute(substitution_vars)
        return substitute_fn

    def parse(self, raw_response: str) -> Dict[str, Any]:
        """
        Parses a JSON or Python dict string into a Python dictionary.
        Handles errors gracefully if the input is not valid.
        """
        import ast
        
        if not isinstance(raw_response, str) or not raw_response.strip():
            return {"error": "Invalid input: received empty or non-string response for parsing."}
        
        # Attempt to fix common LLM errors like escaping single quotes
        cleaned_response = raw_response.replace(r"\'", "'")
        
        # Try JSON first (standard format)
        try:
            return json.loads(cleaned_response)
        except json.JSONDecodeError:
            pass
        
        # Try Python literal eval (handles single-quoted dicts from LLMs)
        try:
            result = ast.literal_eval(cleaned_response)
            if isinstance(result, dict):
                return result
        except (ValueError, SyntaxError):
            pass
        
        # Both failed
        return {
            "raw_response": raw_response,
            "error": "Failed to parse response as JSON or Python dict"
        }

    def get(self, dictionary: Dict, key: str, default: Any = None) -> Any:
        """Gets a value from a dictionary by key."""
        return dictionary.get(key, default)

    def wrap(self, data: Any, type: str | None = None) -> str:
        """
        Wraps the data in the normcode format %xxx() or %{type}xxx().
        Delegates to the Body's Perception faculty if available (via encode_sign).
        
        Special case: type="literal" means NO type specifier - just %id(content).
        "literal" is not a norm, it indicates raw data without a perceptual norm.
        """
        # "literal" means no type specifier
        effective_type = None if type == "literal" else type
        
        if hasattr(self, 'perception_router'):
            wrapped_data = self.perception_router.encode_sign(data, effective_type)
            logger.debug("MIA step: Encoded sign -> %s", wrapped_data)
            return wrapped_data

        # Fallback
        unique_code = uuid.uuid4().hex[:3]
        if effective_type:
            wrapped_data = f"%{{{effective_type}}}{unique_code}({data})"
        else:
            wrapped_data = f"%{unique_code}({data})"
        logger.debug("MIA step: Wrapped data -> %s", wrapped_data)
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
        with the prefix 'input_'. If a value is a JSON string, parse it.
        """
        if not isinstance(all_inputs, dict):
            return {}
        
        script_inputs = {}
        for key, value in all_inputs.items():
            if key.startswith("input_"):
                # If value is a JSON string, try to parse it
                if isinstance(value, str):
                    try:
                        parsed = json.loads(value)
                        script_inputs[key] = parsed
                    except (json.JSONDecodeError, ValueError):
                        # If not valid JSON, use as-is
                        script_inputs[key] = value
                else:
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

    @property
    def parse_boolean(self) -> Callable[[str], bool]:
        """
        Returns a function that parses a raw LLM response to extract a boolean value.
        
        The function looks for common boolean indicators in the text:
        - "true", "yes", "1", "correct", "affirmative" -> True
        - "false", "no", "0", "incorrect", "negative" -> False
        
        Used by: h_Memo-v_Prompt-c_LLMGenerate-o_Truth paradigm
        """
        def _parse_boolean_fn(raw_response: str) -> bool:
            if not isinstance(raw_response, str):
                # If already a boolean, return it directly
                if isinstance(raw_response, bool):
                    return raw_response
                return False
            
            # Normalize the response
            text = raw_response.strip().lower()
            
            # Check for explicit true indicators
            true_indicators = ['true', 'yes', '1', 'correct', 'affirmative', 'continue', 'proceed']
            for indicator in true_indicators:
                if indicator in text:
                    return True
            
            # Check for explicit false indicators
            false_indicators = ['false', 'no', '0', 'incorrect', 'negative', 'stop', 'end', 'terminate', 'quit', 'exit']
            for indicator in false_indicators:
                if indicator in text:
                    return False
            
            # Default to False if no clear indicator found
            return False
        
        return _parse_boolean_fn
