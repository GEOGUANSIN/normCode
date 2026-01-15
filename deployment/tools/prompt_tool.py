"""
Deployment Prompt Tool - Template management for NormCode deployment.

A standalone prompt tool that provides:
- Template loading from files
- Variable substitution
- Template caching
- Same interface as infra PromptTool
"""

import logging
from pathlib import Path
from string import Template
from typing import Optional, Any, Callable, Dict

logger = logging.getLogger(__name__)


class DeploymentPromptTool:
    """
    A prompt template tool for deployment/server execution.
    
    Loads templates from files and provides variable substitution.
    """
    
    def __init__(
        self,
        base_dir: Optional[str] = None,
        encoding: str = "utf-8",
        log_callback: Optional[Callable[[str, Dict], None]] = None,
    ):
        """
        Initialize the prompt tool.
        
        Args:
            base_dir: Base directory for template files
            encoding: File encoding
            log_callback: Optional callback for logging events
        """
        self.base_dir = base_dir
        self.encoding = encoding
        self._log_callback = log_callback
        self._cache: Dict[str, Template] = {}
        self._operation_count = 0
        
        # Default inline templates as fallback
        self._defaults: Dict[str, str] = {
            "translation": "Translate concept to natural name: ${output}",
            "instruction_with_buffer_record": "Use record '${record}' to act on imperative: ${imperative}",
        }
    
    def _log(self, event: str, data: Dict[str, Any]):
        """Log an event via callback if set."""
        if self._log_callback:
            try:
                self._log_callback(event, data)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")
    
    def _get_base_dir(self) -> Path:
        """Get the base directory for prompts."""
        if self.base_dir:
            return Path(self.base_dir)
        return Path.cwd() / "prompts"
    
    def read(self, template_name: str) -> Template:
        """
        Load a template by name and cache it.
        
        Args:
            template_name: Name of the template file or path
            
        Returns:
            A string.Template object
        """
        self._operation_count += 1
        
        # Check cache first
        if template_name in self._cache:
            return self._cache[template_name]
        
        self._log("prompt:read", {
            "template_name": template_name,
            "status": "started",
        })
        
        try:
            base_path = self._get_base_dir()
            file_path = Path(template_name) if Path(template_name).is_absolute() else base_path / template_name
            
            if file_path.exists():
                with open(file_path, "r", encoding=self.encoding) as f:
                    content = f.read()
                tmpl = Template(content)
                self._cache[template_name] = tmpl
                
                self._log("prompt:read", {
                    "template_name": template_name,
                    "status": "completed",
                    "length": len(content),
                })
                
                return tmpl
            
            # Fallback to default inline template
            default_content = self._defaults.get(template_name)
            if default_content is not None:
                tmpl = Template(default_content)
                self._cache[template_name] = tmpl
                return tmpl
            
            raise FileNotFoundError(f"Template '{template_name}' not found at: {file_path}")
            
        except Exception as e:
            self._log("prompt:read", {
                "template_name": template_name,
                "status": "failed",
                "error": str(e),
            })
            raise
    
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
        
        self._log("prompt:render", {
            "template_name": template_name,
            "variables": list(variables.keys()),
            "status": "started",
        })
        
        try:
            tmpl = self._cache.get(template_name)
            if tmpl is None:
                tmpl = self.read(template_name)
            
            result = str(tmpl.safe_substitute(variables))
            
            self._log("prompt:render", {
                "template_name": template_name,
                "status": "completed",
                "result_length": len(result),
            })
            
            return result
            
        except Exception as e:
            self._log("prompt:render", {
                "template_name": template_name,
                "status": "failed",
                "error": str(e),
            })
            raise
    
    def create_template_function(self, template: Template) -> Callable:
        """
        Create a function that fills the template with provided variables.
        
        Args:
            template: The Template object to wrap
            
        Returns:
            A callable that renders the template with given variables
        """
        def template_fn(*args, **kwargs):
            # Handle positional argument (dict)
            if args:
                if len(args) == 1 and isinstance(args[0], dict):
                    variables = args[0]
                else:
                    raise ValueError("template_fn expects a single dict as positional arg")
            else:
                variables = kwargs
            return str(template.safe_substitute(variables))
        
        return template_fn
    
    def clear_cache(self) -> None:
        """Clear all cached templates."""
        self._cache.clear()
    
    def drop(self, template_name: str) -> None:
        """Remove a specific template from cache."""
        self._cache.pop(template_name, None)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "operation_count": self._operation_count,
            "cached_templates": list(self._cache.keys()),
            "base_dir": str(self._get_base_dir()),
        }

