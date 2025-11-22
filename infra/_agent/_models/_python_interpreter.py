import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PythonInterpreterTool:
    def execute(self, script_code: str, inputs: Dict[str, Any]) -> Any:
        """
        Executes a Python script in a controlled environment.

        Args:
            script_code (str): The Python code to execute.
            inputs (Dict[str, Any]): A dictionary of inputs to be injected
                                     into the script's global scope.

        Returns:
            Any: The value of the 'result' variable from the executed script's
                 scope, or an error dictionary.
        """
        try:
            # Prepare the global scope for the execution
            execution_globals = inputs.copy()
            execution_globals['__builtins__'] = __builtins__

            logger.info(f"Executing script with inputs: {list(inputs.keys())}")
            
            # Execute the code
            exec(script_code, execution_globals)

            # Extract the result
            if 'result' in execution_globals:
                result = execution_globals['result']
                logger.info(f"Script executed successfully. Result: {result}")
                return result
            else:
                logger.warning("Script executed, but no 'result' variable was found.")
                return {"status": "warning", "message": "No 'result' variable found in script."}

        except Exception as e:
            logger.error(f"Error executing Python script: {e}")
            logger.error(f"Script that failed:\n{script_code}")
            return {"status": "error", "message": str(e)}

    def function_execute(self, script_code: str, function_name: str, function_params: Dict[str, Any]) -> Any:
        """
        Executes a specific function from a Python script string with given parameters.

        Args:
            script_code (str): The Python code containing the function definition.
            function_name (str): The name of the function to execute.
            function_params (Dict[str, Any]): A dictionary of keyword arguments to pass to the function.

        Returns:
            Any: The return value of the function, or an error dictionary.
        """
        try:
            execution_scope = {}
            exec(script_code, execution_scope)

            if function_name not in execution_scope:
                raise NameError(f"Function '{function_name}' not found in the provided script.")
            
            function_to_call = execution_scope[function_name]

            if not callable(function_to_call):
                raise TypeError(f"'{function_name}' is not a callable function.")

            logger.info(f"Executing function '{function_name}' with params: {list(function_params.keys())}")
            
            result = function_to_call(**function_params)

            logger.info(f"Function '{function_name}' executed successfully. Result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error executing function '{function_name}' from script: {e}")
            logger.error(f"Script that failed:\n{script_code}")
            return {"status": "error", "message": str(e)}
