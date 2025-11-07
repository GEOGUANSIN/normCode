# Imperative Python Sequence

## Purpose

The `imperative_python` sequence provides a powerful and flexible method for executing Python code as part of an inference. It can either run a pre-existing Python script or dynamically generate, save, and execute a new script using a language model based on a natural language prompt.

This sequence is ideal for tasks that require complex logic, calculations, or interactions that are best handled by executable code rather than direct LLM generation.

## Methodology

The sequence operates on a dynamic, just-in-time execution model. A single, powerful function is created that, at runtime, inspects its inputs to decide whether to run an existing script or generate a new one.

### Key Feature Wrappers

The `MVP` step detects special wrappers in the input concepts to gather the necessary components for execution.

-   **`%{script_location}(path/to/your_script.py)`**: **(Direct Execution)** Specifies a pre-existing Python script to execute. The `MVP` step reads the content of this file and passes it directly to the interpreter. This path is for executing known, static scripts and bypasses any code generation. The location can be an absolute path or relative to `infra/_agent/_models/scripts/`.

-   **`%{generated_script_path}(path/to/your_script.py)`**: **(Generate, Save, and Execute)** Specifies the file path for a script that will be dynamically generated. The sequence checks if this file already exists.
    -   If the file exists, its content is read and executed (useful for re-running a previously generated script).
    -   If the file does not exist, the sequence uses a `%{prompt_template}` to generate the script, saves it to this path for future use, and then executes it.
    The location can be an absolute path or relative to `infra/_agent/_models/scripts/`.

-   **`%{prompt_template}(path/to/prompt.txt)`**: Provides the template for generating a Python script. This is **required** when using `%{generated_script_path}` and the target file does not yet exist. The location can be an absolute path or relative to `infra/_agent/_models/prompts/`.

-   **`%{memorized_parameter}(...)`**: Retrieves a value from a JSON file to be used as an input. It can take a simple key (for the default `memorized.json`) or a JSON object specifying a custom file and key (e.g., `{"location": "params.json", "key": "name_key"}`).

### Workflow

1.  **`IWI` (The Architect - `_iwi.py`)**
    -   Acts as a planner. It reads the agent's configuration from the `working_interpretation` (e.g., `with_thinking`, custom keys).
    -   It builds a "plan" (`env_spec` and `sequence_spec`) to create the single, dynamic `generate_and_run` function.
    -   It saves this plan to the agent's state.

2.  **`MFP` (The Executor - `_mfp.py`)**
    -   Executes the plan from `IWI`.
    -   It runs a `ModelSequenceRunner` which calls the `create_python_generate_and_run_function` method, creating the dynamic function that encapsulates all execution logic.
    -   This dynamic function is saved to the agent's state.

3.  **`MVP` (The Data Gatherer - `_mvp.py`)**
    -   Gathers all data required for execution.
    -   It resolves any `%{script_location}`, `%{generated_script_path}`, `%{prompt_template}`, and `%{memorized_parameter}` wrappers. For wrappers pointing to files, it reads their content.
    -   It assembles a single dictionary containing all the necessary inputs (e.g., `script_location`, `generated_script_path`, `prompt_template`, and other input values) for the dynamic function.

4.  **`TIP` (The Action - `_tip.py`)**
    -   Performs the final execution.
    -   It takes the dynamic function created by `MFP`.
    -   It takes the complete data dictionary prepared by `MVP`.
    -   It calls the function with the data. The function then internally decides whether to execute the provided script or generate a new one.

## Execution Paths

The sequence has two primary execution paths, determined by the wrappers provided.

### Path 1: Direct Script Execution (using `script_location`)

If a script is provided via `%{script_location}`, it will be executed directly. This is the most straightforward path, intended for running validated, pre-written scripts.

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

### Path 2: Generate-and-Execute (using `generated_script_path`)

This is the more dynamic path. When `%{generated_script_path}` is provided, the sequence first checks if the script file exists.

#### Sub-path 2a: Re-using an Existing Script
If the file at `generated_script_path` already exists, it is read and executed just like in the Direct Execution path. This allows for caching and re-use of previously generated scripts.

#### Sub-path 2b: Generating a New Script
If the file does not exist, the sequence requires a `%{prompt_template}` to generate a new script.

-   **Input Placeholders**: The prompt template **must** use `$`-prefix syntax (e.g., `$input_1`, `$input_2`) for variable substitution. The inputs gathered by `MVP` are substituted into the template before sending it to the language model.
-   **Saving**: The generated code is automatically saved to the path specified by `%{generated_script_path}` for debugging and future re-use.
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