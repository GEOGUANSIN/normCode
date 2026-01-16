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
        
        # Additional search directories (e.g., for prompts_chinese)
        self._additional_dirs: list = []
        
        # Default inline templates as fallback
        self._defaults: Dict[str, str] = {
            "translation": "Translate concept to natural name: ${output}",
            "instruction_with_buffer_record": "Use record '${record}' to act on imperative: ${imperative}",
        }
    
    def add_search_directory(self, directory: str):
        """
        Add an additional search directory for templates.
        
        Args:
            directory: Path to additional directory (e.g., prompts_chinese)
        """
        if directory and Path(directory).exists():
            self._additional_dirs.append(Path(directory))
            logger.info(f"Added prompt search directory: {directory}")
    
    def _log(self, event: str, data: Dict[str, Any]):
        """Log an event via callback if set."""
        if self._log_callback:
            try:
                self._log_callback(event, data)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")
    
    def set_project_dir(self, project_dir: str):
        """
        Set the project directory for resolving provision paths.
        
        Args:
            project_dir: The project root directory
        """
        self._project_dir = Path(project_dir)
        logger.info(f"Prompt tool project dir: {project_dir}")
    
    def _get_base_dir(self) -> Path:
        """Get the base directory for prompts."""
        if self.base_dir:
            return Path(self.base_dir)
        return Path.cwd() / "prompts"
    
    def _resolve_template_path(self, template_name: str) -> Optional[Path]:
        """
        Resolve a template path, handling provision paths.
        
        Args:
            template_name: Template name or path (may include provision/prompts/ prefix)
            
        Returns:
            Resolved Path or None if not found
        """
        template_path = Path(template_name)
        
        # If absolute path, use directly
        if template_path.is_absolute():
            return template_path if template_path.exists() else None
        
        # Check if this is a provision path like 'provision/prompts/file.md'
        parts = template_path.parts
        if len(parts) >= 2 and parts[0] in ('provision', 'provisions'):
            # Extract the provision type and remaining path
            provision_type = parts[1]  # e.g., 'prompts', 'prompts_chinese'
            
            if provision_type.startswith('prompts'):
                # Extract just the filename/remaining path
                remaining = '/'.join(parts[2:]) if len(parts) > 2 else ''
                
                if remaining:
                    # Try base_dir first
                    if self.base_dir:
                        candidate = Path(self.base_dir) / remaining
                        if candidate.exists():
                            return candidate
                    
                    # Try additional dirs (e.g., prompts_chinese)
                    for search_dir in self._additional_dirs:
                        candidate = search_dir / remaining
                        if candidate.exists():
                            return candidate
                    
                    # Try with project_dir if set
                    if hasattr(self, '_project_dir') and self._project_dir:
                        # Try both provision and provisions
                        for prefix in ['provision', 'provisions']:
                            candidate = self._project_dir / prefix / provision_type / remaining
                            if candidate.exists():
                                return candidate
                        
                        # Also try just appending the path as-is
                        candidate = self._project_dir / template_name
                        if candidate.exists():
                            return candidate
                        
                        # Try alternative prefix
                        alt_prefix = 'provisions' if parts[0] == 'provision' else 'provision'
                        candidate = self._project_dir / alt_prefix / '/'.join(parts[1:])
                        if candidate.exists():
                            return candidate
        
        # Standard resolution: base_dir / template_name
        base_path = self._get_base_dir()
        file_path = base_path / template_name
        if file_path.exists():
            return file_path
        
        # Check additional directories
        for search_dir in self._additional_dirs:
            candidate = search_dir / template_name
            if candidate.exists():
                return candidate
        
        return None
    
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
            # Use the new path resolution that handles provision paths
            found_path = self._resolve_template_path(template_name)
            
            if found_path:
                with open(found_path, "r", encoding=self.encoding) as f:
                    content = f.read()
                tmpl = Template(content)
                self._cache[template_name] = tmpl
                
                self._log("prompt:read", {
                    "template_name": template_name,
                    "status": "completed",
                    "length": len(content),
                    "path": str(found_path),
                })
                
                return tmpl
            
            # Fallback to default inline template
            default_content = self._defaults.get(template_name)
            if default_content is not None:
                tmpl = Template(default_content)
                self._cache[template_name] = tmpl
                return tmpl
            
            # Build error message with all searched paths
            base_path = self._get_base_dir()
            searched = [str(base_path / template_name)] + [str(d / template_name) for d in self._additional_dirs]
            if hasattr(self, '_project_dir') and self._project_dir:
                searched.append(str(self._project_dir / template_name))
            raise FileNotFoundError(f"Template '{template_name}' not found. Searched: {searched}")
            
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
    
    def read_now(self, template_name: str) -> Template:
        """
        Load a template immediately by name (alias for read).
        
        This method exists for compatibility with paradigm affordances.
        
        Args:
            template_name: Name of the template file or path
            
        Returns:
            A string.Template object
        """
        return self.read(template_name)
    
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

