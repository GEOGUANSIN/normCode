# Imperative Python Indirect Sequence

## Purpose

The `imperative_python_indirect` sequence executes Python code based on a simple, high-level natural language instruction. It works by first translating this simple instruction into a detailed, specific prompt suitable for a language model to generate code, and then executing the generated script.

This sequence is ideal for tasks where the user provides a general command, and the agent must first reason about how to turn that command into a precise, executable script.

## Methodology

The sequence follows a two-stage process that leverages configuration flags in the `working_interpretation` to select the correct translation logic:

1.  **Instruction Translation**: A simple instruction (e.g., "sum the two numbers") is combined with a specialized translation prompt and sent to a language model. The model's task is to generate a detailed, secondary prompt that contains all the necessary context for another language model to write a Python script. The selection of the translation prompt is controlled by two flags:
    -   `with_thinking` (boolean): If `true`, a prompt is used that instructs the final model to return a JSON object with both its "thinking" and "code".
    -   `is_relation_output` (boolean): If `true`, a prompt is used that is tailored for tasks requiring multiple outputs structured in a JSON object.

2.  **Code Generation and Execution**: The detailed prompt generated in the first stage is then used to create and run a Python script, following the same dynamic execution model as the `imperative_python` sequence.

### Instruction Translation Prompts

The sequence dynamically selects one of four translation prompts based on the configuration:

-   `imperative_python_translate.txt`: For simple, single-output tasks without thinking.
-   `imperative_python_thinking_translate.txt`: For simple, single-output tasks with thinking.
-   `imperative_python_relation_translate.txt`: For complex, multi-output (JSON) tasks without thinking.
-   `imperative_python_relation_thinking_translate.txt`: For complex, multi-output (JSON) tasks with thinking.

### Workflow

1.  **`IWI` (The Architect - `_iwi.py`)**
    -   Acts as a planner. It reads the `with_thinking` and `is_relation_output` flags from the `working_interpretation`.
    -   It selects the correct translation prompt from the four available options.
    -   It builds a multi-step "plan" (`env_spec` and `sequence_spec`) that first translates the simple instruction and then creates the dynamic `generate_and_run` function.
    -   It saves this plan to the agent's state.

2.  **`MFP` (The Function Factory - `_mfp.py`)**
    -   Executes the multi-step plan from `IWI`.
    -   It first calls the language model to translate the simple instruction into a detailed prompt.
    -   It then uses this detailed prompt to create the dynamic `generate_and_run` function that encapsulates all execution logic.
    -   This dynamic function is saved to the agent's state.

3.  **`MVP` (The Data Gatherer - `_mvp.py`)**
    -   Gathers and prepares all data required for execution.
    -   It resolves any `%{script_location}` or `%{memorized_parameter}` wrappers.
    -   It applies any `value_selectors` to extract specific data from complex inputs.
    -   It assembles a single dictionary containing all the necessary inputs (e.g., `script_location`, `input_1`, `input_2`) for the dynamic function.

4.  **`TVA` (The Actuator - `_tva.py`)**
    -   Performs the final execution.
    -   It takes the dynamic function created by `MFP` and the complete data dictionary prepared by `MVP`.
    -   It calls the function with the data. The function then internally decides whether to execute a pre-existing script or generate and execute a new one based on the translated prompt.

5.  **`TIP` (The Perceiver - `_tip.py`)**
    -   Perceives the outcome of the action. It takes the result returned by `TVA` and formalizes it as the output of the inference.

## Execution Logic

The execution logic for the generated script is identical to the `imperative_python` sequence. The script is either read from the path specified by `%{script_location}` if it exists, or generated and saved to that path if it does not.

-   **Input Injection**: All inputs from the `MVP` step are injected into the script's global scope.
-   **Output Requirement**: The script **must** assign its final output to a variable named `result`.

### Output Structure for `with_thinking` Mode

When the `with_thinking: true` flag is set, the initial translation step will instruct the language model to generate a prompt that, in turn, asks for a JSON object containing `thinking` and `code` keys. This ensures that the entire process preserves the step-by-step reasoning.
```