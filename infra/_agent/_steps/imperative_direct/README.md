# Imperative Direct Sequence

## Purpose

The `imperative_direct` sequence provides a highly flexible and efficient method for executing "direct instructions" where operational details (like a prompt template or file path) are supplied as part of the input data, rather than being generated through a multi-step translation process.

This approach is ideal for scenarios where the instruction is already known and the goal is to simply format it with dynamic values and execute it through a language model or another tool.

## Methodology

This sequence operates on a principle of separating planning, execution, and data gathering across its key steps. Its central feature is the ability to interpret and process special **wrappers** within the input concepts. These wrappers can dynamically load content from files, retrieve values from memory, or format instructions for later steps.

### Key Feature: The Wrapper Syntax

The sequence is triggered by special wrappers in the string values of the input concepts. The syntax is designed to be flexible and descriptive.

-   **General Syntax:** `%{wrapper_type}optional_id(content)`
    -   `wrapper_type`: The core type of the instruction (e.g., `prompt`, `file_location`).
    -   `optional_id`: An optional unique identifier for the wrapper instance. This is parsed but not currently used in the logic, serving as a placeholder for future functionality.
    -   `content`: The parameter for the wrapper, typically a file path or a memory key.

### Supported Wrappers

| Wrapper Syntax | Description |
| :--- | :--- |
| `%{prompt}id(path)` | **Reads the file** at the given `path` and designates its content as the `prompt_template` for an LLM call. |
| `%{file_location}id(path)` | **Reads the file** at the given `path` and treats its content as a **regular input value**. |
| `%{prompt_location}id(path)` | **Passes the `path` itself** as a `prompt_location` instruction for a later step to handle. |
| `%{script_location}id(path)` | **Passes the `path` itself** as a `script_location` instruction for a later step to handle. |
| `%{memorized_parameter}id(key)`| Retrieves a value from the agent's memory using the specified `key`. Requires the `FileSystemTool`. |

### Workflow

1.  **`IWI` (The Architect - `_iwi.py`)**
    -   Acts as a planner. It reads the agent's configuration.
    -   It builds a "plan" (the `env_spec` and `sequence_spec`) that defines how to create a generic, reusable generation function.
    -   It saves this plan to the agent's state without executing it.

2.  **`MFP` (The Executor - `_mfp.py`)**
    -   Executes the plan created by `IWI`.
    -   It runs a `ModelSequenceRunner` which calls the `create_generation_function_with_template_in_vars` method, creating a generic function that expects its prompt template to be supplied at runtime.
    -   This generic function is saved to the agent's state.

3.  **`MVP` (The Data Gatherer & Pre-processor - `_mvp.py`)**
    -   This step is a versatile pre-processor that gathers and transforms all data required for the next agent step.
    -   It inspects all input concepts and identifies special instructions by looking for the `%{...}` wrapper syntax.
    -   Depending on the wrapper type, it may:
        - Read content directly from a file (`%{prompt}`, `%{file_location}`).
        - Fetch values from memory (`%{memorized_parameter}`).
        - Reformat file paths as instructions for later steps (`%{prompt_location}`, `%{script_location}`).
    -   It handles complex input ordering and selection using `value_selectors`.
    -   It assembles a final dictionary containing all the prepared data (e.g., a prompt template, regular inputs, or other instructions) ready for the next step.

4.  **`TIP` (The Action - `_tip.py`)**
    -   This step performs the final execution.
    -   It takes the generic function created by `MFP`.
    -   It takes the complete data dictionary prepared by `MVP`.
    -   It calls the function with the data, which triggers the final, formatted call to the language model to get the result.

## Prompt Format and Requirements

To be compatible with the agent's execution logic, prompt templates must follow specific formatting rules for both input variables and output structure.

### 1. Input Placeholder Syntax

The prompt template **must** use the `$` prefix for variable substitution, as required by Python's `string.Template` class.

-   **Single Input:** If only one value is passed to the prompt, it will be available under the key `input`.
    -   *Example:* `Analyze the following text: $input`
-   **Multiple Inputs:** If multiple values are passed, they will be numbered sequentially as `input_1`, `input_2`, etc.
    -   *Example:* `Summarize the difference between $input_1 and $input_2`

> **Note:** Using other syntax like `{input}` or `%input_1%` will result in an error.

### 2. Output Structure for `with_thinking` Mode

When the `with_thinking: true` flag is set in the agent's configuration, the prompt **must** instruct the language model to return a single JSON object containing both its reasoning and the final answer.

#### General JSON Structure

The root JSON object **must** contain two keys:

-   `analysis` (string): The model's step-by-step reasoning on how it arrived at the answer.
-   `answer` (any): The final, structured answer, which varies depending on the task.

**Example of the general JSON output:**
```json
{
  "analysis": "Step-by-step reasoning about how to approach and solve the problem...",
  "answer": "The actual output as specified in the instruction"
}
```

#### Specific Structure for Relation Extraction

For tasks involving the extraction of relationships, the `answer` key has a more specific, required structure: a **list of dictionaries**.

-   Each dictionary in the list represents one complete relationship instance.
-   The keys of the dictionary must correspond to the output variable names specified in the instruction.

**Full JSON Example for Relation Extraction:**

Imagine the task is: "From the text 'TechCorp is based in San Francisco, and Innovate Inc. is in New York.', extract all companies and their headquarters."

The expected JSON output would be:

```json
{
  "analysis": "The user wants to extract company names and their locations. The sentence mentions two companies: TechCorp in San Francisco, and Innovate Inc. in New York. This requires creating two separate dictionaries, one for each company, and putting them in the 'answer' list.",
  "answer": [
    {"company": "TechCorp", "location": "San Francisco"},
    {"company": "Innovate Inc.", "location": "New York"}
  ]
}
```

### 3. Example Prompt Template

Here is an example of a prompt file (`prompt_with_thinking.txt`) that incorporates these requirements:

```
Instruction: $input

Execute the instruction. Your final output must be a single JSON object.

First, think step-by-step about how to solve the problem. Place your reasoning in the "analysis" key of the JSON object.
Then, provide the final answer in the "answer" key.

Example of the final JSON output:
\`\`\`json
{
  "analysis": "Step-by-step reasoning about how to approach and solve the problem...",
  "answer": "The actual output as specified in the instruction"
}
\`\`\`

Execute the instruction and return only the JSON object.
```