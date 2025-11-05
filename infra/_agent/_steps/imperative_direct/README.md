# Imperative Direct Sequence

## Purpose

The `imperative_direct` sequence provides a highly flexible and efficient method for executing "direct instructions" where the prompt template is supplied as part of the input data, rather than being generated through a multi-step translation process.

This approach is ideal for scenarios where the instruction is already known and the goal is to simply format it with dynamic values and execute it through a language model.

## Methodology

This sequence operates on a principle of separating planning, execution, and data gathering across its key steps. The central feature is the ability to dynamically load a prompt template from a file path specified directly within an input concept.

### Key Feature: The `%{prompt}(location)` Wrapper

The sequence is triggered by a special wrapper in one of the input concepts' string values.

-   **Syntax:** `%{prompt}(path/to/prompt.txt)`
-   **Function:** The `MVP` step detects this wrapper. The `location` can be an absolute path or a relative path from the `infra/_agent/_models/prompts/` directory. The content of this file is then used as the prompt template for the LLM call.

### Workflow

1.  **`IWI` (The Architect - `_iwi.py`)**
    -   Acts as a planner. It reads the agent's configuration.
    -   It builds a "plan" (the `env_spec` and `sequence_spec`) that defines how to create a generic, reusable generation function.
    -   It saves this plan to the agent's state without executing it.

2.  **`MFP` (The Executor - `_mfp.py`)**
    -   Executes the plan created by `IWI`.
    -   It runs a `ModelSequenceRunner` which calls the `create_generation_function_with_template_in_vars` method, creating a generic function that expects its prompt template to be supplied at runtime.
    -   This generic function is saved to the agent's state.

3.  **`MVP` (The Data Gatherer - `_mvp.py`)**
    -   This step gathers all the data required for the final LLM call.
    -   It inspects all input concepts and identifies the prompt by looking for the `%{prompt}(location)` wrapper.
    -   It reads the prompt content from the specified file location.
    -   It assembles a dictionary containing the prompt template and all other input values, ready for the generation function.

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