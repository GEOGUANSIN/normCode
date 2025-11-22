# Imperative in Composition Sequence

## Purpose

The `imperative_in_composition` sequence provides a highly flexible method for executing complex, multi-step instructions that are defined declaratively in **paradigm** files. Instead of hard-coding operational logic, this sequence loads a JSON-defined workflow and executes it.

This approach is ideal for creating reusable and complex operational patterns (e.g., prompt-LLM-parse-save) that can be selected and run at runtime with dynamic data.

## Methodology

This sequence operates by separating the definition of a complex workflow (the **paradigm**) from the execution engine (the agent sequence). The `working_interpretation` provided to the inference tells the sequence which paradigm to load and how to order the input data.

### Key Feature: Declarative Paradigms

The core of this sequence is the **Paradigm**. A paradigm is a JSON file that declaratively defines a multi-step function. It specifies:
1.  **`env_spec`**: The set of tools required for the operation (e.g., `llm`, `file_system`, `formatter_tool`).
2.  **`sequence_spec`**: The "vertical" setup steps needed to gather the tool functions.
3.  **`plan`**: The "horizontal" execution plan that defines the runtime data flow—how the output of one tool becomes the input for the next.

The sequence is configured by passing the paradigm's name in the `working_interpretation`, making the agent a generic paradigm executor.

### Workflow

1.  **`IWI` (The Planner - `_iwi.py`)**
    -   Reads the `working_interpretation` to get the specified `paradigm` name (e.g., `"thinking_save_and_wrap"`).
    -   It loads the corresponding paradigm's `env_spec` and `sequence_spec` from its JSON file.
    -   It saves this specification to the agent's state for the next step.

2.  **`IR` (Input References - `_ir.py`)**
    -   A standard step that gathers the initial data references from the input concepts.

3.  **`MFP` (The Composer - `_mfp.py`)**
    -   Executes the `sequence_spec` that `IWI` loaded from the paradigm.
    -   It runs a `ModelSequenceRunner` to resolve all the required tool affordances (e.g., `"llm.generate"`) into a single, callable, composed function. This function encapsulates the entire data-flow logic defined in the paradigm's `plan`.
    -   This newly composed function is saved to the agent's state.

4.  **`MVP` (The Data Pre-processor - `_mvp.py`)**
    -   Gathers and transforms all the data needed to execute the composed function.
    -   It uses the `value_order` from the `working_interpretation` to correctly structure the inputs.
    -   It processes special **wrappers** in the input strings to perform tasks like loading file content.
    -   It assembles a final dictionary containing all the prepared data, ready to be passed to the composed function.

5.  **`TVA` (The Executor - `_tva.py`)**
    -   This step performs the final execution.
    -   It takes the composed function created by `MFP`.
    -   It takes the complete data dictionary prepared by `MVP`.
    -   It calls the function with the data, which triggers the paradigm's entire multi-step plan (e.g., formatting a prompt, calling an LLM, cleaning and parsing the response, saving the result, etc.).

6.  **`OR` & `OWI` (Output Steps)**
    -   Standard steps to format and return the final result of the sequence.

## Configuration (`working_interpretation`)

The sequence is primarily configured through the `working_interpretation` dictionary.

**Example:**
```json
{
  "paradigm": "thinking_save_and_wrap",
  "value_order": {
    "prompt_info": 0,
    "input_1": 1,
    "input_2": 2,
    "save_path": 3
  }
}
```

-   **`paradigm`** (required): The filename (without `.json`) of the paradigm to load from the `infra/_agent/_models/_paradigms/` directory.
-   **`value_order`** (required): A dictionary that maps the names of the input concepts to a numerical order. This ensures the `MVP` step processes the data in the correct sequence before passing it to the paradigm.

## Wrapper Syntax in MVP

The `MVP` step can process special wrappers in the input concept data to perform pre-processing tasks.

-   **General Syntax:** `%{wrapper_type}optional_id(content)`

| Wrapper Syntax | Description |
| :--- | :--- |
| `%{prompt}id(path)` | **Reads the file** at `path` and designates its content as the `prompt_template` for the paradigm. |
| `%{save_path}id(path)` | Designates the `path` string as the `save_path` for the paradigm. |
| `%{file_location}id(path)` | **Reads the file** at `path` and treats its content as a **regular input value**. |
| `%{script_location}id(path)`| Designates the `path` as a `script_location` for paradigms that execute code. |

## Prompt and Paradigm Requirements

Because this sequence is a generic paradigm runner, the specific requirements for prompts and output formats are defined by the tools and logic **within the paradigm itself**.

### 1. Input Placeholder Syntax

The `FormatterTool` used in many paradigms relies on Python's `string.Template`, which requires a `$` prefix for variable substitution. When creating prompts for such paradigms, this syntax must be used.

-   **Example:** `Create a friendly greeting for $input_1 from $input_2.`

> **Note:** The names of the variables (e.g., `input_1`) are determined by the `MVP` step based on the `value_order` configuration.

### 2. Output Structure (Paradigm-Dependent)

The required output structure from an LLM is also defined by the paradigm's plan. For example, the `thinking_save_and_wrap` paradigm expects the LLM to return a single JSON object with two specific keys:

-   `thinking` (string): The model's reasoning.
-   `answer` (any): The final answer.

This is a requirement of that specific paradigm, not a general rule for the `imperative_in_composition` sequence. Always refer to the paradigm's logic to determine the expected input and output formats.