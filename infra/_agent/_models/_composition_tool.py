from typing import Callable, List, Any, Dict
import inspect

class CompositionTool:
    """
    A tool for creating and executing a multi-step function composition plan
    where each step can have a `condition` to determine if it runs.
    """

    def _evaluate_condition(self, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """
        Evaluates a condition dictionary against the current context.
        
        Args:
            condition (Dict[str, Any]): A dict like {'key': 'context_key', 'operator': 'is_true'}.
            context (Dict[str, Any]): The current execution context.

        Returns:
            bool: The result of the condition evaluation.
        """
        key = condition.get('key')
        operator = condition.get('operator')

        if key not in context:
            raise ValueError(f"Condition failed: Key '{key}' not found in context.")
            
        value = context[key]

        if operator == 'is_true':
            return bool(value)
        elif operator == 'is_false':
            return not bool(value)
        else:
            raise ValueError(f"Unsupported operator in condition: {operator}")

    def compose(self, plan: List[Dict[str, Any]], return_key: str | None = None) -> Callable:
        """
        Takes an execution plan and returns a single callable function.
        """
        def _composed_function(initial_input: Any) -> Any:
            """
            Executes the composition plan.
            """
            if not isinstance(initial_input, dict):
                raise TypeError("The initial input for a plan-based composition must be a dictionary.")

            context: Dict[str, Any] = {'__initial_input__': initial_input}
            
            for step in plan:
                # Check if a condition exists and if it evaluates to false
                if 'condition' in step:
                    if not self._evaluate_condition(step['condition'], context):
                        continue # Skip this step

                # --- Execute the step (standard function call) ---
                function = step['function']
                output_key = step['output_key']
                params = step.get('params', {})
                literal_params = step.get('literal_params', {})

                args = []
                kwargs = literal_params.copy()

                for param_name, context_key in params.items():
                    if context_key not in context:
                        raise ValueError(f"Execution failed: Key '{context_key}' not found in context for step producing '{output_key}'.")
                    
                    value = context[context_key]
                    if param_name == '__positional__':
                        args.append(value)
                    else:
                        kwargs[param_name] = value
                
                result = function(*args, **kwargs)
                context[output_key] = result
            
            last_result = next(reversed(context.values()), None)

            if return_key:
                if return_key not in context:
                    raise ValueError(f"Specified return_key '{return_key}' not found in execution context.")
                return context[return_key]
            
            return last_result

        return _composed_function
