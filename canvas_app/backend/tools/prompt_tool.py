"""
Canvas-native prompt tool for NormCode orchestration.

This tool wraps the standard PromptTool but adds WebSocket event
emission for prompt operations, allowing the UI to show real-time
template loading and rendering.
"""

import logging
import time
from pathlib import Path
from string import Template
from typing import Optional, Any, Callable, Dict

logger = logging.getLogger(__name__)


class CanvasPromptTool:
    """
    A Prompt tool that emits WebSocket events for template operations.
    
    This tool proxies the standard PromptTool functionality while
    adding event emission for UI monitoring. It tracks:
    - Template loading
    - Variable substitution
    - Rendered output previews
    """
    
    def __init__(
        self,
        base_dir: Optional[str] = None,
        encoding: str = "utf-8",
        emit_callback: Optional[Callable[[str, Dict], None]] = None
    ):
        """
        Initialize the Canvas prompt tool.
        
        Args:
            base_dir: Base directory for prompt templates
            encoding: File encoding for templates
            emit_callback: Callback to emit WebSocket events
        """
        self.base_dir = base_dir
        self.encoding = encoding
        self._emit_callback = emit_callback
        self._cache: Dict[str, Template] = {}
        self._operation_count = 0
        
        # Default inline templates as fallback
        self._defaults: Dict[str, str] = {
            "translation": "Translate concept to natural name: ${output}",
            "instruction_with_buffer_record": "Use record '${record}' to act on imperative: ${impmerative}",
        }
        
        # Try to import and create the underlying PromptTool
        try:
            from infra._agent._models._prompt import PromptTool
            self._tool = PromptTool(base_dir=base_dir, encoding=encoding)
        except ImportError:
            logger.warning("Could not import PromptTool from infra, using fallback")
            self._tool = None
    
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
    
    def _get_base_dir(self) -> Path:
        """Determines the base directory for prompt operations."""
        if self.base_dir:
            return Path(self.base_dir)
        else:
            # Fallback to the 'prompts' directory relative to this file's parent
            this_dir = Path(__file__).parent
            return this_dir / "prompts"
    
    def read(self, template_name: str) -> Template:
        """
        Load a template by name and cache it.
        
        Args:
            template_name: Name of the template file or path
            
        Returns:
            A string.Template object
        """
        self._operation_count += 1
        start_time = time.time()
        
        self._emit("prompt:read_started", {
            "template_name": template_name,
            "timestamp": time.time(),
        })
        
        try:
            if self._tool:
                result = self._tool.read(template_name)
                self._cache[template_name] = result
            else:
                result = self._read_fallback(template_name)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._emit("prompt:read_completed", {
                "template_name": template_name,
                "template_length": len(result.template) if hasattr(result, 'template') else 0,
                "duration_ms": duration_ms,
                "timestamp": time.time(),
            })
            
            return result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._emit("prompt:read_failed", {
                "template_name": template_name,
                "error": str(e),
                "duration_ms": duration_ms,
                "timestamp": time.time(),
            })
            raise
    
    def _read_fallback(self, template_name: str) -> Template:
        """Fallback read implementation."""
        base_path = self._get_base_dir()
        file_path = Path(template_name) if Path(template_name).is_absolute() else base_path / template_name
        
        if file_path.exists():
            with open(file_path, "r", encoding=self.encoding) as f:
                content = f.read()
            tmpl = Template(content)
            self._cache[template_name] = tmpl
            return tmpl
        
        # Fallback to default inline template if available
        default_content = self._defaults.get(template_name)
        if default_content is not None:
            tmpl = Template(default_content)
            self._cache[template_name] = tmpl
            return tmpl
        
        raise FileNotFoundError(
            f"Template file '{template_name}' not found at path: {file_path}"
        )
    
    def substitute(self, template_name: str, variables: Dict[str, Any]) -> Template:
        """
        Apply variables to a template and cache the result.
        
        Args:
            template_name: Name of the template
            variables: Variables to substitute
            
        Returns:
            Updated Template object
        """
        self._operation_count += 1
        
        self._emit("prompt:substitute", {
            "template_name": template_name,
            "variables": list(variables.keys()),
            "timestamp": time.time(),
        })
        
        if self._tool:
            result = self._tool.substitute(template_name, variables)
            self._cache[template_name] = result
            return result
        
        # Fallback
        tmpl = self._cache.get(template_name)
        if tmpl is None:
            tmpl = self.read(template_name)
        rendered = tmpl.safe_substitute(variables)
        updated = Template(rendered)
        self._cache[template_name] = updated
        return updated
    
    def render(self, template_name: str, variables: Dict[str, Any]) -> str:
        """
        Render a template with variables (does not mutate cache).
        
        Args:
            template_name: Name of the template
            variables: Variables to substitute
            
        Returns:
            Rendered string
        """
        self._operation_count += 1
        start_time = time.time()
        
        self._emit("prompt:render_started", {
            "template_name": template_name,
            "variables": list(variables.keys()),
            "timestamp": time.time(),
        })
        
        try:
            if self._tool:
                result = self._tool.render(template_name, variables)
            else:
                # Fallback
                tmpl = self._cache.get(template_name)
                if tmpl is None:
                    tmpl = self.read(template_name)
                result = str(tmpl.safe_substitute(variables))
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._emit("prompt:render_completed", {
                "template_name": template_name,
                "result_length": len(result),
                "result_preview": result[:500] + "..." if len(result) > 500 else result,
                "duration_ms": duration_ms,
                "timestamp": time.time(),
            })
            
            return result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._emit("prompt:render_failed", {
                "template_name": template_name,
                "error": str(e),
                "duration_ms": duration_ms,
                "timestamp": time.time(),
            })
            raise
    
    def create_template_function(self, template: Template) -> Callable:
        """
        Create a function that fills the template with provided variables.
        
        Used by paradigms to create a callable function for template rendering.
        
        Args:
            template: The Template object to wrap
            
        Returns:
            A callable that renders the template with given variables
        """
        if self._tool:
            return self._tool.create_template_function(template)
        
        def template_fn(*args, **kwargs):
            # If called with a positional argument (dict), use it as the variables
            if args:
                if len(args) == 1 and isinstance(args[0], dict):
                    variables = args[0]
                else:
                    raise ValueError(f"template_fn expects a single dict as positional arg")
            else:
                variables = kwargs
            return str(template.safe_substitute(variables))
        
        return template_fn
    
    def clear_cache(self) -> None:
        """Clear all cached templates."""
        self._cache.clear()
        if self._tool:
            self._tool.clear_cache()
        
        self._emit("prompt:cache_cleared", {
            "timestamp": time.time(),
        })
    
    def drop(self, template_name: str) -> None:
        """Remove a specific template from cache."""
        self._cache.pop(template_name, None)
        if self._tool:
            self._tool.drop(template_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "operation_count": self._operation_count,
            "cached_templates": list(self._cache.keys()),
            "has_infra_tool": self._tool is not None,
        }
