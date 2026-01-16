# Imperative Python Sequence

## Purpose

The `imperative_python` sequence provides a powerful and flexible method for executing Python code as part of an inference. It can either run a pre-existing Python script or dynamically generate, save, and execute a new script using a language model based on a natural language prompt.

This sequence is ideal for tasks that require complex logic, calculations, or interactions that are best handled by executable code rather than direct LLM generation.

## Methodology

The sequence operates on a dynamic, just-in-time execution model. A single, powerful function is created that, at runtime, inspects its inputs to decide whether to run an existing script or generate a new one.

### Key Feature Wrappers

The `MVP` step detects special wrappers in the input concepts to gather the necessary components for execution.

-   **`%{script_location}(path/to/your_script.py)`**: **(Execute or Generate-and-Execute)** Specifies the path for a Python script. The sequence checks if this file exists.
    -   If the file exists, its content is read and executed directly.
    -   If the file does not exist, the sequence uses a `%{prompt_template}` to generate the script, saves it to this path for future use, and then executes it.
    The location can be an absolute path or relative to the `base_dir` configured in the `Body`.

-   **`%{prompt_template}(path/to/prompt.txt)`**: Provides the template for generating a Python script. This is **required** when using `%{script_location}` and the target file does not yet exist. The location can be an absolute path or relative to the `base_dir` configured in the `Body`.

-   **`%{memorized_parameter}(...)`**: Retrieves a value from a JSON file to be used as an input. It can take a simple key (for the default `memorized.json`) or a JSON object specifying a custom file and key (e.g., `{"location": "params.json", "key": "name_key"}`).

### Advanced Input Handling: `value_selectors`

For handling complex input concepts (e.g., lists or dictionaries), the `working_interpretation` can include a `value_selectors` dictionary. This allows you to extract specific parts of your input data before they are passed to the Python script.

Each key in the `value_selectors` object corresponds to a concept name defined in `value_order`. The value contains instructions for how to process that concept.

-   `source_concept`: The name of the concept to read from.
-   `index` (optional): The list index to select.
-   `key` (optional): The dictionary key to select.

**Example `working_interpretation`:**
```json
"working_interpretation": {
    "value_order": {
        "input_1": 0,
        "input_2": 1
    },
    "value_selectors": {
        "input_1": {
            "source_concept": "list_of_numbers",
            "index": 0
        },
        "input_2": {
            "source_concept": "list_of_dicts",
            "index": 0,
            "key": "value"
        }
    }
}
```
In this example, before execution:
1.  The value for `input_1` will be the element at index `0` from the `list_of_numbers` concept.
2.  The value for `input_2` will be the value associated with the `value` key from the dictionary at index `0` of the `list_of_dicts` concept.

### Workflow

1.  **`IWI` (The Architect - `_iwi.py`)**
    -   Acts as a planner. It reads the agent's configuration from the `working_interpretation` (e.g., `with_thinking`, `value_selectors`).
    -   It builds a "plan" (`env_spec` and `sequence_spec`) to create the single, dynamic `generate_and_run` function.
    -   It saves this plan to the agent's state.

2.  **`MFP` (The Function Factory - `_mfp.py`)**
    -   Executes the plan from `IWI`.
    -   It runs a `ModelSequenceRunner` which calls the `create_python_generate_and_run_function` method, creating the dynamic function that encapsulates all execution logic.
    -   This dynamic function is saved to the agent's state.

3.  **`MVP` (The Data Gatherer - `_mvp.py`)**
    -   Gathers and prepares all data required for execution.
    -   It resolves any `%{script_location}`, `%{prompt_template}`, and `%{memorized_parameter}` wrappers.
    -   It applies any `value_selectors` to extract specific data from complex inputs.
    -   It assembles a single dictionary containing all the necessary inputs (e.g., `script_location`, `prompt_template`, `input_1`, `input_2`) for the dynamic function.

4.  **`TVA` (The Actuator - `_tva.py`)**
    -   Performs the final execution.
    -   It takes the dynamic function created by `MFP` and the complete data dictionary prepared by `MVP`.
    -   It calls the function with the data. The function then internally decides whether to execute the provided script or generate and execute a new one.

5.  **`TIP` (The Perceiver - `_tip.py`)**
    -   Perceives the outcome of the action. It takes the result returned by `TVA` and formalizes it as the output of the inference.

## Execution Logic

The sequence's behavior is determined by whether a script exists at the path specified by `%{script_location}`.

### Path 1: Script Exists (Direct Execution)

If a script is found at the path provided via `%{script_location}`, it will be executed directly. This is the path for running validated, pre-written, or previously generated scripts.

-   **Input Injection**: All other inputs from the `MVP` step are injected into the script's global scope. For example, a value passed as `input_1` will be available as a variable named `input_1`.
-   **Output Requirement**: The script **must** assign its final output to a variable named `result`. The `execute` method will capture and return the value of this variable.

**Example Script (`my_script.py`):**
```python
# inputs 'input_1' and 'input_2' are injected automatically
sum_val = input_1 + input_2
product_val = input_1 * input_2

# The final output must be in the 'result' variable
result = {"sum": sum_val, "product": product_val}
```

### Path 2: Script Does Not Exist (Generate-and-Execute)

If the script file does not exist at the specified path, the sequence requires a `%{prompt_template}` to generate a new one.

-   **Input Placeholders**: The prompt template **must** use `$`-prefix syntax (e.g., `$input_1`, `$input_2`) for variable substitution. The inputs gathered by `MVP` are substituted into the template before sending it to the language model.
-   **Saving**: The generated code is automatically saved to the path specified by `%{script_location}` for debugging and future re-use.
-   **Execution**: The newly generated script is then executed following the same rules as Direct Script Execution (injected inputs, `result` variable for output).

### Output Structure for `with_thinking` Mode

When the `with_thinking: true` flag is set in the agent's configuration, the prompt **must** instruct the language model to return a single JSON object containing its reasoning and the final code.

-   **`thinking` (string)**: The model's step-by-step reasoning on how it will generate the code.
-   **`code` (string)**: The final, complete Python script to be executed.

**Example `with_thinking` Prompt Template:**
```
Instruction: $instruction.

Your task is to write a Python script to perform this instruction. The script will receive inputs in variables like 'input_1', 'input_2', etc. The final output of the script must be assigned to a variable named 'result'.

Respond with a single JSON object containing two keys: "thinking" and "code".
- "thinking": Explain your plan for the script.
- "code": The full Python script as a string.

Example of the final JSON output:
\`\`\`json
{
  "thinking": "The user wants to add two numbers. I will access the numbers from the 'input_1' and 'input_2' variables, add them together, and store the final value in the 'result' variable.",
  "code": "result = input_1 + input_2"
}
\`\`\`

Now, generate the script for the given instruction.
```