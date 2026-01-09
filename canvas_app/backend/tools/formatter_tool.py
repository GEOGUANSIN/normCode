"""
Canvas Formatter Tool - Data formatting and parsing utilities for paradigm composition.

This tool provides utility functions used by paradigm composition:
- Template substitution
- JSON parsing
- Dictionary access
- Data wrapping (perceptual sign encoding)
- Code extraction from markdown

These are the same utilities as infra/_agent/_models/_formatter_tool.py,
adapted for the Canvas app context.
"""

import json
import logging
import re
import uuid
from string import Template
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class CanvasFormatterTool:
    """
    A tool with methods for data formatting, parsing, and extraction.
    
    Used by paradigm composition to transform data between steps.
    Each method can be used as an affordance in paradigm JSON.
    """
    
    def __init__(self, emit_callback: Optional[Callable[[str, Dict], None]] = None):
        """
        Initialize the formatter tool.
        
        Args:
            emit_callback: Optional callback for emitting WebSocket events
        """
        self._emit_callback = emit_callback
        self.perception_router = None  # Set by Body if available
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """Set the callback for emitting WebSocket events."""
        self._emit_callback = callback
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event if callback is set."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    # =========================================================================
    # Template Functions
    # =========================================================================
    
    def create_template_function(self, template: str) -> Callable[[Dict[str, Any]], str]:
        """
        Factory method that takes a template string and returns a substitution function.
        
        Args:
            template: Template string with $variable placeholders
            
        Returns:
            A function that takes a vars dict and returns the substituted string
        """
        def substitute_fn(vars: Dict[str, Any]) -> str:
            return Template(template).safe_substitute(vars)
        return substitute_fn
    
    def create_substitute_function(self, template_key: str) -> Callable[[Dict[str, Any]], str]:
        """
        Factory method returning a substitute function bound to a template key.
        
        The template string is expected to be in vars[template_key].
        
        Args:
            template_key: Key in vars dict containing the template string
            
        Returns:
            A function that takes vars dict and returns substituted string
        """
        def substitute_fn(vars: Dict[str, Any]) -> str:
            if template_key not in vars:
                raise ValueError(f"'{template_key}' not found in vars")
            prompt_template = vars[template_key]
            substitution_vars = {k: v for k, v in vars.items() if k != template_key}
            return Template(str(prompt_template)).safe_substitute(substitution_vars)
        return substitute_fn
    
    # =========================================================================
    # Parsing Functions (affordances that return callable methods)
    # =========================================================================
    
    @property
    def parse(self) -> Callable[[str], Dict[str, Any]]:
        """
        Affordance: Return a function that parses JSON strings.
        
        Used by paradigms to parse LLM responses.
        """
        def parse_fn(raw_response: str) -> Dict[str, Any]:
            if not isinstance(raw_response, str) or not raw_response.strip():
                return {"error": "Invalid input: empty or non-string"}
            
            # Clean common LLM escaping issues
            cleaned = raw_response.replace(r"\'", "'")
            
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return {
                    "raw_response": raw_response,
                    "error": "Failed to parse JSON"
                }
        
        return parse_fn
    
    @property
    def parse_boolean(self) -> Callable[[str], bool]:
        """
        Affordance: Return a function that parses boolean values from text.
        
        Used by judgement paradigms to extract true/false.
        """
        def parse_bool_fn(raw_response: str) -> bool:
            if not isinstance(raw_response, str):
                return False
            
            text = raw_response.strip().lower()
            
            # Check for explicit true/false
            if text in ("true", "yes", "1", "correct", "valid", "confirmed"):
                return True
            if text in ("false", "no", "0", "incorrect", "invalid", "denied"):
                return False
            
            # Check for JSON boolean
            try:
                parsed = json.loads(raw_response)
                if isinstance(parsed, bool):
                    return parsed
                if isinstance(parsed, dict):
                    # Look for answer/result/value keys
                    for key in ("answer", "result", "value", "output"):
                        if key in parsed:
                            val = parsed[key]
                            if isinstance(val, bool):
                                return val
                            if isinstance(val, str):
                                return val.lower() in ("true", "yes", "1")
            except (json.JSONDecodeError, TypeError):
                pass
            
            # Default to False for ambiguous cases
            return False
        
        return parse_bool_fn
    
    @property
    def get(self) -> Callable[..., Any]:
        """
        Affordance: Return a function that gets values from dictionaries.
        
        Supports both positional and keyword arguments.
        """
        def get_fn(dictionary: Dict = None, key: str = None, default: Any = None, **kwargs) -> Any:
            # Handle keyword arguments
            d = dictionary or kwargs.get("dictionary", {})
            k = key or kwargs.get("key", "")
            dflt = default if default is not None else kwargs.get("default")
            
            if not isinstance(d, dict):
                return dflt
            return d.get(k, dflt)
        
        return get_fn
    
    @property
    def wrap(self) -> Callable[..., str]:
        """
        Affordance: Return a function that wraps data as perceptual signs.
        
        Formats data as %{type}xxx(data) for the Reference system.
        
        Special case: type="literal" means NO type specifier - just %id(content).
        "literal" is not a norm, it indicates raw data without a perceptual norm.
        """
        def wrap_fn(data: Any = None, type: str = None, **kwargs) -> str:
            # Handle keyword arguments
            d = data if data is not None else kwargs.get("__positional__", kwargs.get("data", ""))
            t = type or kwargs.get("type")
            
            # Use perception router if available
            if self.perception_router:
                # Pass None for literal type - no norm specifier
                effective_type = None if t == "literal" else t
                return self.perception_router.encode_sign(d, effective_type)
            
            # Fallback: simple wrapping
            unique_code = uuid.uuid4().hex[:3]
            # "literal" means no type specifier - just %id(content)
            if t and t != "literal":
                return f"%{{{t}}}{unique_code}({d})"
            else:
                return f"%{unique_code}({d})"
        
        return wrap_fn
    
    @property
    def clean_code(self) -> Callable[[str], str]:
        """
        Affordance: Return a function that extracts code from markdown blocks.
        """
        def clean_code_fn(raw_code: str) -> str:
            if not isinstance(raw_code, str):
                return ""
            
            # Look for markdown code blocks
            code_blocks = re.findall(
                r"```(?:python|py|json|ncd|ncds)?\n(.*?)\n```",
                raw_code,
                re.DOTALL
            )
            
            if code_blocks:
                return code_blocks[0].strip()
            
            return raw_code.strip()
        
        return clean_code_fn
    
    @property
    def wrap_list(self) -> Callable[[List, Optional[str]], List[str]]:
        """
        Affordance: Return a function that wraps each item in a list.
        """
        wrap_fn = self.wrap
        
        def wrap_list_fn(data_list: Union[list, tuple], type: str = None) -> List[str]:
            if not isinstance(data_list, (list, tuple)):
                return data_list
            return [wrap_fn(item, type) for item in data_list]
        
        return wrap_list_fn
    
    def collect_script_inputs(self, all_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect all input_N variables from a dictionary.
        
        If a value is a JSON string, parse it.
        """
        if not isinstance(all_inputs, dict):
            return {}
        
        script_inputs = {}
        for key, value in all_inputs.items():
            if key.startswith("input_"):
                if isinstance(value, str):
                    try:
                        script_inputs[key] = json.loads(value)
                    except (json.JSONDecodeError, ValueError):
                        script_inputs[key] = value
                else:
                    script_inputs[key] = value
        return script_inputs

