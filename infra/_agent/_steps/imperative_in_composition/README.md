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

### Basic Structure

```json
{
  "paradigm": "filename_without_extension",
  "value_order": {
    "concept_name_or_alias": 0,
    "another_concept": 1
  }
}
```

-   **`paradigm`** (required): The filename of the paradigm to load.
-   **`value_order`**: A map defining the order of inputs. The keys become the input variables for the paradigm (mapped to `input_1`, `input_2`, etc. by default).

### Advanced Data Selection (`value_selectors`)

You can precise control over which data is extracted from input concepts using `value_selectors`.

```json
{
  "working_interpretation": {
    "paradigm": "my_paradigm",
    "value_order": {
      "my_custom_input": 0
    },
    "value_selectors": {
      "my_custom_input": {
        "source_concept": "{concept_name}",  // The concept to read from
        "index": 0,                          // (Optional) Select item at index 0 from a list
        "key": "some_key"                    // (Optional) Select value of "some_key" from a dict
      }
    }
  }
}
```

### Unpacking Lists

If a selected value is a list (e.g., a list of files), you can "explode" it into multiple sequential inputs (e.g., `input_2`, `input_3`, `input_4`) using unpacking flags.

#### 1. Unpack After Selection (`unpack: true`)
Use this when your selector points to a list, and you want to use the items in that list as inputs.

```json
"other_files": {
    "source_concept": "{input files}",
    "key": "{other input files}",
    "unpack": true
}
```
*Result:* The list found at `{other input files}` is exploded.

#### 2. Unpack Before Selection (`unpack_before_selection: true`)
Use this when you have a list of objects, and you want to apply the selector (e.g., `key`) to *each item* in that list individually, then use the resulting list of values.

```json
"file_contents": {
    "source_concept": "{grouped files}",
    "key": "content",
    "unpack_before_selection": true
}
```
*Result:* Iterates through the list at `{grouped files}`, extracts `content` from each item, and explodes the resulting list of contents.

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
