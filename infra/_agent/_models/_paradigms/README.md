# Composition Paradigms

This directory contains pre-defined, reusable composition paradigms stored in a declarative JSON format. These paradigms can be loaded by the `Paradigm` class (`infra/_agent/_models/_paradigms/_paradigm.py`) to quickly construct complex, multi-step functions without redefining the specifications each time.

## Available Paradigms

### 1. `json_output.json`

-   **Purpose**: A simple paradigm for a common LLM task: take a prompt, generate a response, and ensure the output is a valid, parsed JSON object.
-   **Key Features**:
    -   Uses a standard template substitution for the prompt.
    -   Calls the `llm.generate` method with `response_format: {"type": "json_object"}` to instruct the model to return JSON.
    -   Runs the raw response through a `parse` function.
-   **Returns**: The final, parsed dictionary.
    ```json
    "return_key": "parsed_dict"
    ```

### 2. `thinking_save_and_wrap.json`

-   **Purpose**: Replicates the original `composition_experiment.py`. It models a complex workflow where the LLM "thinks", produces an answer, the answer is saved to a file, and the file path is then wrapped in a typed string for further processing.
-   **Key Features**:
    -   Extracts a specific key (`answer`) from the LLM's JSON output.
    -   Extracts a `save_path` from the initial runtime input.
    -   Saves the extracted answer to the specified path.
    -   Wraps the resulting file path in a typed string (e.g., `%{file_location}xxx(...)`).
-   **Returns**: The final, wrapped file path string.
    ```json
    "return_key": "mia_result"
    ```

### 3. `py_exec_horizontal_prompt.json`

-   **Purpose**: A general-purpose paradigm for generating and executing Python code. It includes conditional logic to reuse previously generated code. The prompt is provided at runtime.
-   **Key Features**:
    -   **Horizontal Input**: Expects the `prompt_template` to be provided in the `vars` dictionary at runtime.
    -   **Conditional Logic**: Checks if the target script file exists. If `True`, it reads the file; if `False`, it generates, cleans, and saves the code.
    -   **Function Execution**: Uses the `python_interpreter.function_execute` method to call a specific function (named `main` by convention) within the script.
-   **Returns**: The direct result of the executed Python function.
    ```json
    "return_key": "execution_result"
    ```

### 4. `py_exec_vertical_prompt.json`

-   **Purpose**: A specialized paradigm for generating and executing Python code where the code-generation prompt is pre-configured by pulling a value from the `states` object at composition time.
-   **Key Features**:
    -   **Vertical Input**: The `prompt_template` is specified as a `MetaValue` that resolves to an attribute on the `states` object at runtime (e.g., `states.inference.concept`). This makes the paradigm reusable for different state-provided prompts.
    -   **Conditional Logic**: Same as the horizontal version, it checks for the existence of the script to avoid re-generating it.
    -   **Function Execution**: Also uses `python_interpreter.function_execute`.
-   **Returns**: The direct result of the executed Python function.
    ```json
    "return_key": "execution_result"
    ```
