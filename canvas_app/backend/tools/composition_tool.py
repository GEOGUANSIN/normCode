"""
Canvas Composition Tool - Function composition for paradigm execution.

This tool implements the composition logic for paradigm execution:
- Takes a plan (list of steps)
- Creates a composed function that executes steps in sequence
- Handles context passing between steps
- Supports conditional execution

This is the core mechanism for TVA (Tool Value Actuation) in the
paradigm execution model.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class CanvasCompositionTool:
    """
    A tool for creating and executing multi-step function composition plans.
    
    This is the runtime engine for paradigm execution:
    1. MFP (Model Function Perception) produces functions from tool affordances
    2. Those functions are assembled into a plan
    3. CompositionTool.compose() creates a single callable from the plan
    4. TVA (Tool Value Actuation) calls that function with input values
    """
    
    def __init__(self, emit_callback: Optional[Callable[[str, Dict], None]] = None):
        """
        Initialize the composition tool.
        
        Args:
            emit_callback: Optional callback for emitting WebSocket events
        """
        self._emit_callback = emit_callback
    
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
    
    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition dictionary against the current context.
        
        Args:
            condition: Dict like {'key': 'context_key', 'operator': 'is_true'}
            context: Current execution context
            
        Returns:
            Boolean result of condition evaluation
        """
        key = condition.get('key')
        operator = condition.get('operator')
        
        if key not in context:
            raise ValueError(f"Condition key '{key}' not found in context")
        
        value = context[key]
        
        if operator == 'is_true':
            return bool(value)
        elif operator == 'is_false':
            return not bool(value)
        elif operator == 'exists':
            return value is not None
        elif operator == 'not_exists':
            return value is None
        else:
            raise ValueError(f"Unsupported condition operator: {operator}")
    
    def compose(self, plan: List[Dict[str, Any]], return_key: Optional[str] = None) -> Callable:
        """
        Take an execution plan and return a single composed callable.
        
        This is the core composition mechanism. The plan is a list of steps,
        each with:
        - function: The callable to execute (from MFP)
        - output_key: Where to store the result in context
        - params: Dict mapping param names to context keys
        - literal_params: Dict of literal values to pass
        - condition: Optional condition for conditional execution
        
        Args:
            plan: List of step dictionaries
            return_key: Optional key for the final return value
            
        Returns:
            A callable that takes initial_input dict and returns result
        """
        def _composed_function(initial_input: Any) -> Any:
            """Execute the composition plan."""
            if not isinstance(initial_input, dict):
                # Wrap non-dict inputs
                initial_input = {"__positional__": initial_input}
            
            # Initialize context with initial input
            context: Dict[str, Any] = {'__initial_input__': initial_input}
            
            # Emit start event
            self._emit("composition:started", {
                "steps": len(plan),
                "return_key": return_key,
            })
            
            logger.debug(f"Composition start: {len(plan)} steps")
            
            for i, step in enumerate(plan):
                output_key = step.get('output_key', f'step_{i}_result')
                
                # Check condition if present
                if 'condition' in step:
                    should_run = self._evaluate_condition(step['condition'], context)
                    if not should_run:
                        logger.debug(f"Skipping step {i+1} ({output_key}) - condition not met")
                        continue
                
                # Get function (may be a MetaValue reference or direct callable)
                function = step['function']
                
                # Handle MetaValue references (function stored in context)
                if isinstance(function, dict) and function.get('__type__') == 'MetaValue':
                    fn_key = function['key']
                    if fn_key not in context:
                        raise ValueError(f"Function key '{fn_key}' not found in context")
                    function = context[fn_key]
                
                # Build arguments
                params = step.get('params', {})
                literal_params = step.get('literal_params', {})
                
                args = []
                kwargs = literal_params.copy()
                
                for param_name, context_key in params.items():
                    if context_key not in context:
                        raise ValueError(
                            f"Context key '{context_key}' not found for step '{output_key}'"
                        )
                    
                    value = context[context_key]
                    
                    if param_name == '__positional__':
                        args.append(value)
                    else:
                        kwargs[param_name] = value
                
                # Execute the function
                try:
                    fn_name = getattr(function, '__name__', str(function)[:50])
                    logger.debug(f"Step {i+1}: {fn_name} -> {output_key}")
                    
                    self._emit("composition:step", {
                        "step": i + 1,
                        "output_key": output_key,
                        "function": fn_name,
                    })
                    
                    result = function(*args, **kwargs)
                    context[output_key] = result
                    
                except Exception as e:
                    logger.error(f"Step {i+1} failed: {e}")
                    self._emit("composition:step_failed", {
                        "step": i + 1,
                        "output_key": output_key,
                        "error": str(e),
                    })
                    raise
            
            # Determine return value
            if return_key:
                if return_key not in context:
                    raise ValueError(f"Return key '{return_key}' not in context")
                result = context[return_key]
            else:
                # Return last value
                result = next(reversed(context.values()), None)
            
            self._emit("composition:completed", {
                "return_key": return_key,
            })
            
            return result
        
        return _composed_function

