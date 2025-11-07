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
