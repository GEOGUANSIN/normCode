"""
Canvas-native Python interpreter tool for NormCode orchestration.

This tool wraps the standard PythonInterpreterTool but adds WebSocket event
emission for script execution, allowing the UI to show real-time
script execution progress and results.
"""

import logging
import time
import inspect
from typing import Optional, Any, Callable, Dict

logger = logging.getLogger(__name__)


class CanvasPythonInterpreterTool:
    """
    A Python interpreter tool that emits WebSocket events for script execution.
    
    This tool proxies the standard PythonInterpreterTool functionality while
    adding event emission for UI monitoring. It tracks:
    - Script code (preview)
    - Inputs provided
    - Execution results
    - Duration
    - Errors
    """
    
    def __init__(
        self,
        emit_callback: Optional[Callable[[str, Dict], None]] = None,
        body: Any = None
    ):
        """
        Initialize the Canvas Python interpreter tool.
        
        Args:
            emit_callback: Callback to emit WebSocket events
            body: Optional Body instance for script access to tools
        """
        self._emit_callback = emit_callback
        self.body = body  # Used by scripts that need access to Body tools
        self._execution_count = 0
        
        # Try to import the underlying PythonInterpreterTool
        try:
            from infra._agent._models._python_interpreter import PythonInterpreterTool
            self._tool = PythonInterpreterTool()
            # Pass body reference if available
            if body:
                self._tool.body = body
        except ImportError:
            logger.warning("Could not import PythonInterpreterTool from infra, using fallback")
            self._tool = None
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """Set the callback for emitting WebSocket events."""
        self._emit_callback = callback
    
    def set_body(self, body: Any):
        """Set the Body instance for script access."""
        self.body = body
        if self._tool:
            self._tool.body = body
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event if callback is set."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    def _get_code_preview(self, code: str, max_lines: int = 10) -> str:
        """Get a preview of the code (first N lines)."""
        lines = code.strip().split('\n')
        if len(lines) <= max_lines:
            return code
        return '\n'.join(lines[:max_lines]) + f'\n... ({len(lines) - max_lines} more lines)'
    
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
        exec_id = f"python_{self._execution_count}_{int(time.time())}"
        start_time = time.time()
        
        # Emit start event
        self._emit("python:execution_started", {
            "execution_id": exec_id,
            "code_preview": self._get_code_preview(script_code),
            "code_length": len(script_code),
            "inputs": list(inputs.keys()),
            "timestamp": time.time(),
        })
        
        try:
            if self._tool:
                result = self._tool.execute(script_code, inputs)
            else:
                # Fallback implementation
                result = self._execute_fallback(script_code, inputs)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Check if result is an error
            is_error = isinstance(result, dict) and result.get("status") == "error"
            
            if is_error:
                self._emit("python:execution_failed", {
                    "execution_id": exec_id,
                    "error": result.get("message", "Unknown error"),
                    "duration_ms": duration_ms,
                    "timestamp": time.time(),
                })
            else:
                self._emit("python:execution_completed", {
                    "execution_id": exec_id,
                    "result_type": type(result).__name__,
                    "result_preview": self._get_result_preview(result),
                    "duration_ms": duration_ms,
                    "timestamp": time.time(),
                })
            
            return result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._emit("python:execution_failed", {
                "execution_id": exec_id,
                "error": str(e),
                "duration_ms": duration_ms,
                "timestamp": time.time(),
            })
            
            return {"status": "error", "message": str(e)}
    
    def _execute_fallback(self, script_code: str, inputs: Dict[str, Any]) -> Any:
        """Fallback execution when infra tool not available."""
        try:
            execution_globals = inputs.copy()
            execution_globals["__builtins__"] = __builtins__
            
            exec(script_code, execution_globals)
            
            if "result" in execution_globals:
                return execution_globals["result"]
            else:
                return {"status": "warning", "message": "No 'result' variable found in script."}
                
        except Exception as e:
            logger.error(f"Error executing Python script: {e}")
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
        exec_id = f"python_fn_{self._execution_count}_{int(time.time())}"
        start_time = time.time()
        
        # Emit start event
        self._emit("python:function_started", {
            "execution_id": exec_id,
            "function_name": function_name,
            "code_preview": self._get_code_preview(script_code),
            "params": list(function_params.keys()) if function_params else [],
            "timestamp": time.time(),
        })
        
        try:
            if self._tool:
                result = self._tool.function_execute(script_code, function_name, function_params)
            else:
                # Fallback implementation
                result = self._function_execute_fallback(script_code, function_name, function_params)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            is_error = isinstance(result, dict) and result.get("status") == "error"
            
            if is_error:
                self._emit("python:function_failed", {
                    "execution_id": exec_id,
                    "function_name": function_name,
                    "error": result.get("message", "Unknown error"),
                    "duration_ms": duration_ms,
                    "timestamp": time.time(),
                })
            else:
                self._emit("python:function_completed", {
                    "execution_id": exec_id,
                    "function_name": function_name,
                    "result_type": type(result).__name__,
                    "result_preview": self._get_result_preview(result),
                    "duration_ms": duration_ms,
                    "timestamp": time.time(),
                })
            
            return result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            self._emit("python:function_failed", {
                "execution_id": exec_id,
                "function_name": function_name,
                "error": str(e),
                "duration_ms": duration_ms,
                "timestamp": time.time(),
            })
            
            return {"status": "error", "message": str(e)}
    
    def _function_execute_fallback(
        self,
        script_code: str,
        function_name: str,
        function_params: Dict[str, Any]
    ) -> Any:
        """Fallback function execution when infra tool not available."""
        try:
            execution_scope: Dict[str, Any] = {}
            exec(script_code, execution_scope)
            
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
            
            return function_to_call(**params)
            
        except Exception as e:
            logger.error(f"Error executing function '{function_name}': {e}")
            return {"status": "error", "message": str(e)}
    
    def create_function_executor(
        self,
        script_code: str,
        function_name: str
    ) -> Callable[[Dict[str, Any]], Any]:
        """
        Create a bound function executor for a script function.
        
        Used by paradigms to create callable functions for script execution.
        
        Args:
            script_code: The Python code containing the function
            function_name: Name of the function to create executor for
            
        Returns:
            A callable that accepts function_params dict
        """
        def executor_fn(function_params: Dict[str, Any]) -> Any:
            return self.function_execute(script_code, function_name, function_params)
        
        return executor_fn
    
    def _get_result_preview(self, result: Any, max_length: int = 500) -> str:
        """Get a preview string of the result."""
        try:
            result_str = str(result)
            if len(result_str) > max_length:
                return result_str[:max_length] + "..."
            return result_str
        except Exception:
            return f"<{type(result).__name__}>"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics."""
        return {
            "execution_count": self._execution_count,
            "has_infra_tool": self._tool is not None,
            "has_body": self.body is not None,
        }
