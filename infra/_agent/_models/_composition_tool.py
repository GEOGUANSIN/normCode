from typing import Callable, List, Any, Dict
import inspect

class CompositionTool:
    """
    A tool for creating and executing a multi-step function composition plan.
    """

    def compose(self, plan: List[Dict[str, Any]], return_key: str | None = None) -> Callable:
        """
        Takes an execution plan and returns a single callable function.

        The plan is a list of steps, where each step is a dictionary defining:
        - 'output_key': The key under which to store the function's result.
        - 'function': The callable to execute for this step.
        - 'params': A dictionary mapping the function's parameter names to
                    keys in the execution context.

        Args:
            plan (List[Dict[str, Any]]): The execution plan.
            return_key (str, optional): The key from the execution context to
                                       return as the final result. If None, the
                                       result of the last step is returned.
        """

        def _composed_function(initial_input: Any) -> Any:
            """
            Executes the composition plan.
            """
            if not isinstance(initial_input, dict):
                raise TypeError("The initial input for a plan-based composition must be a dictionary.")

            context: Dict[str, Any] = {'__initial_input__': initial_input}
            last_result = None

            for step in plan:
                function = step['function']
                output_key = step['output_key']
                params = step.get('params', {})
                literal_params = step.get('literal_params', {})

                args = []
                kwargs = literal_params.copy() # Start with literal values

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
                last_result = result
            
            if return_key:
                if return_key not in context:
                    raise ValueError(f"Specified return_key '{return_key}' not found in execution context.")
                return context[return_key]
            
            return last_result

        return _composed_function
