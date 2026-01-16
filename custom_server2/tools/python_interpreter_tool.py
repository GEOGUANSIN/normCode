"""
Deployment Python Interpreter Tool - Script execution for NormCode deployment.

A standalone Python interpreter tool that provides:
- Script execution in controlled environment
- Function execution from scripts
- Body injection for tool access
- Same interface as infra PythonInterpreterTool
"""

import logging
import inspect
from typing import Optional, Any, Callable, Dict

logger = logging.getLogger(__name__)


class DeploymentPythonInterpreterTool:
    """
    A Python interpreter tool for deployment/server execution.
    
    Executes Python scripts in a controlled environment with optional
    access to Body tools.
    """
    
    def __init__(
        self,
        body: Any = None,
        log_callback: Optional[Callable[[str, Dict], None]] = None,
    ):
        """
        Initialize the Python interpreter tool.
        
        Args:
            body: Optional Body instance for script access to tools
            log_callback: Optional callback for logging events
        """
        self.body = body
        self._log_callback = log_callback
        self._execution_count = 0
    
    def set_body(self, body: Any):
        """Set the Body instance for script access."""
        self.body = body
    
    def _log(self, event: str, data: Dict[str, Any]):
        """Log an event via callback if set."""
        if self._log_callback:
            try:
                self._log_callback(event, data)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")
    
    def _get_code_preview(self, code: str, max_lines: int = 10) -> str:
        """Get a preview of the code (first N lines)."""
        lines = code.strip().split('\n')
        if len(lines) <= max_lines:
            return code
        return '\n'.join(lines[:max_lines]) + f'\n... ({len(lines) - max_lines} more lines)'
    
    def _get_result_preview(self, result: Any, max_length: int = 500) -> str:
        """Get a preview string of the result."""
        try:
            result_str = str(result)
            if len(result_str) > max_length:
                return result_str[:max_length] + "..."
            return result_str
        except Exception:
            return f"<{type(result).__name__}>"
    
    def execute(self, script_code: str, inputs: Dict[str, Any]) -> Any:
        """
        Execute a Python script in a controlled environment.
        
        Args:
            script_code: The Python code to execute
            inputs: Dictionary of inputs to inject into the script's global scope
            
        Returns:
            The value of the 'result' variable from the script, or error dict
        """
        self._execution_count += 1
        
        self._log("python:execute", {
            "execution_id": self._execution_count,
            "code_preview": self._get_code_preview(script_code),
            "inputs": list(inputs.keys()),
            "status": "started",
        })
        
        try:
            # Create execution environment
            execution_globals = inputs.copy()
            execution_globals["__builtins__"] = __builtins__
            
            # Inject body if available
            if self.body:
                execution_globals["body"] = self.body
            
            # Execute the script
            exec(script_code, execution_globals)
            
            # Get result
            if "result" in execution_globals:
                result = execution_globals["result"]
            else:
                result = {"status": "warning", "message": "No 'result' variable found in script."}
            
            self._log("python:execute", {
                "execution_id": self._execution_count,
                "result_type": type(result).__name__,
                "result_preview": self._get_result_preview(result),
                "status": "completed",
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            
            self._log("python:execute", {
                "execution_id": self._execution_count,
                "error": str(e),
                "status": "failed",
            })
            
            return {"status": "error", "message": str(e)}
    
    def function_execute(
        self,
        script_code: str,
        function_name: str,
        function_params: Dict[str, Any]
    ) -> Any:
        """
        Execute a specific function from a Python script.
        
        Args:
            script_code: The Python code containing the function definition
            function_name: Name of the function to execute
            function_params: Keyword arguments to pass to the function
            
        Returns:
            The return value of the function, or error dict
        """
        self._execution_count += 1
        
        self._log("python:function_execute", {
            "execution_id": self._execution_count,
            "function_name": function_name,
            "params": list(function_params.keys()) if function_params else [],
            "status": "started",
        })
        
        try:
            # Create execution environment
            execution_scope: Dict[str, Any] = {}
            exec(script_code, execution_scope)
            
            # Find the function
            if function_name not in execution_scope:
                raise NameError(f"Function '{function_name}' not found in script.")
            
            function_to_call = execution_scope[function_name]
            
            if not callable(function_to_call):
                raise TypeError(f"'{function_name}' is not callable.")
            
            params = dict(function_params or {})
            
            # Inject body if function accepts it
            if self.body is not None:
                sig = inspect.signature(function_to_call)
                accepts_body = (
                    "body" in sig.parameters
                    or any(
                        p.kind == inspect.Parameter.VAR_KEYWORD
                        for p in sig.parameters.values()
                    )
                )
                if accepts_body and "body" not in params:
                    params["body"] = self.body
            
            result = function_to_call(**params)
            
            self._log("python:function_execute", {
                "execution_id": self._execution_count,
                "function_name": function_name,
                "result_type": type(result).__name__,
                "status": "completed",
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Function execution failed: {e}")
            
            self._log("python:function_execute", {
                "execution_id": self._execution_count,
                "function_name": function_name,
                "error": str(e),
                "status": "failed",
            })
            
            return {"status": "error", "message": str(e)}
    
    def create_function_executor(
        self,
        script_code: str,
        function_name: str
    ) -> Callable[[Dict[str, Any]], Any]:
        """
        Create a bound function executor for a script function.
        
        Args:
            script_code: The Python code containing the function
            function_name: Name of the function to create executor for
            
        Returns:
            A callable that accepts function_params dict
        """
        def executor_fn(function_params: Dict[str, Any]) -> Any:
            return self.function_execute(script_code, function_name, function_params)
        
        return executor_fn
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "execution_count": self._execution_count,
            "has_body": self.body is not None,
        }

