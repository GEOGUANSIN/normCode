# Judgement Python Sequence

## Purpose

The `judgement_python` sequence provides a flexible method for executing a Python script to perform an evaluation or "judgement." It can either run a pre-existing script or dynamically generate one from a natural language prompt. The key requirement is that the script's output must be a **boolean-like value** (e.g., `True`, `False`, `0`, `1`).

This sequence is ideal for conditional logic within a NormCode plan, where an inference needs to evaluate a state of affairs and return a clear `True` or `False` assessment.

## Methodology

The sequence operates on a dynamic, just-in-time execution model. A single, powerful function is created that, at runtime, inspects its inputs to decide whether to run an existing script or generate a new one.

### Key Feature Wrappers

The `MVP` step detects special wrappers in the input concepts to gather the necessary components for execution.

-   **`%{script_location}(path/to/your_script.py)`**: **(Execute or Generate-and-Execute)** Specifies the path for a Python script.
    -   If the file exists, its content is read and executed.
    -   If the file does not exist, the sequence uses a `%{prompt_template}` to generate the script, saves it to this path, and then executes it.

-   **`%{prompt_template}(path/to/prompt.txt)`**: Provides the template for generating a Python script. This is **required** if `%{script_location}` points to a non-existent file.

-   **`%{memorized_parameter}(...)`**: Retrieves a value from a JSON file to be used as an input.

### Advanced Input Handling: `value_selectors`

For handling complex input concepts (e.g., lists or dictionaries), the `working_interpretation` can include a `value_selectors` dictionary to extract specific parts of your input data before they are passed to the Python script.

Each key in `value_selectors` corresponds to a concept name. The value specifies how to process that concept:

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
        }
    }
}
```

### Workflow

1.  **`IWI` (The Architect)**: Reads the agent's configuration and builds a "plan" to create a single, dynamic `generate_and_run` function.
2.  **`MFP` (The Function Factory)**: Executes the plan from `IWI`, creating the dynamic function that encapsulates all execution logic.
3.  **`MVP` (The Data Gatherer)**: Gathers all data for execution, resolving wrappers (`%{script_location}`, etc.) and applying `value_selectors`. It assembles a single dictionary of inputs.
4.  **`TVA` (The Actuator)**: Takes the dynamic function from `MFP` and the data dictionary from `MVP` and executes the function.
5.  **`TIP` (The Perceiver)**: Takes the result from `TVA` and formalizes it as the output of the inference.

## Execution Logic

The sequence's behavior is determined by whether a script exists at the path specified by `%{script_location}`.

### Path 1: Script Exists (Direct Execution)

If a script is found, it will be executed directly.

-   **Input Injection**: All inputs from `MVP` are injected into the script's global scope. An input passed as `input_1` will be available as a variable named `input_1`.
-   **Output Requirement**: The script **must** assign its final boolean-like output to a variable named `result`.

**Example Script (`is_zero.py`):**
```python
# input 'input_1' is injected automatically
is_zero = (input_1 == 0)

# The final output must be a boolean in the 'result' variable
result = is_zero
```

### Path 2: Script Does Not Exist (Generate-and-Execute)

If no script exists, a `%{prompt_template}` is required to generate one.

-   **Input Placeholders**: The prompt template **must** use `$`-prefix syntax (e.g., `$input_1`) for variable substitution.
-   **Saving**: The generated code is automatically saved to the `%{script_location}` path.
-   **Execution**: The new script is executed following the same rules (injected inputs, `result` variable for output).
-   **Output Requirement**: The prompt **must** instruct the language model to generate a script that assigns a boolean or boolean-like value to the `result` variable.

### Output Structure for `with_thinking` Mode

When `with_thinking: true` is set, the prompt **must** instruct the language model to return a single JSON object with two keys:

-   **`thinking` (string)**: The model's reasoning on how it will generate the code.
-   **`code` (string)**: The final, complete Python script.

**Example `with_thinking` Prompt Template:**
```
Instruction: $instruction.

Your task is to write a Python script that evaluates this instruction and returns True or False.
The script will receive inputs like 'input_1', 'input_2', etc.
The final output of the script must be a boolean value assigned to a variable named 'result'.

Respond with a single JSON object containing two keys: "thinking" and "code".
- "thinking": Explain your plan for the script.
- "code": The full Python script as a string.

Example of the final JSON output:
\`\`\`json
{
  "thinking": "The user wants to check if input_1 is zero. I will compare 'input_1' to 0 and store the boolean result in the 'result' variable.",
  "code": "result = (input_1 == 0)"
}
\`\`\`

Now, generate the script for the given instruction.
```