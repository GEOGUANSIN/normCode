# Judgement Direct Sequence

## Purpose

The `judgement_direct` sequence provides a highly flexible and efficient method for executing "direct judgment calls" where the prompt template is supplied as part of the input data, rather than being generated through a multi-step translation process.

This approach is ideal for scenarios where the judgment instruction is already known and the goal is to simply format it with dynamic values and execute it through a language model to evaluate a condition.

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
    -   It also stores the `condition` for later evaluation in the `TIP` step.

2.  **`MFP` (The Executor - `_mfp.py`)**
    -   Executes the plan created by `IWI`.
    -   It runs a `ModelSequenceRunner` which calls the `create_generation_function_with_template_in_vars` method, creating a generic function that expects its prompt template to be supplied at runtime.
    -   This generic function is saved to the agent's state.

3.  **`MVP` (The Data Gatherer - `_mvp.py`)**
    -   This step gathers all the data required for the final LLM call.
    -   It inspects all input concepts and identifies the prompt by looking for the `%{prompt}(location)` wrapper.
    -   It reads the prompt content from the specified file location.
    -   It assembles a dictionary containing the prompt template and all other input values, ready for the generation function.

4.  **`TVA` (The Executor - `_tva.py`)**
    -   Applies the generic function created by `MFP` to the data prepared by `MVP`.
    -   This triggers the LLM call and returns the judgment result.

5.  **`TIP` (The Condition Checker - `_tip.py`)**
    -   This step evaluates the judgment result against an optional condition.
    -   If a condition is provided and all results match it, it sets `condition_met = True` and creates a success reference.
    -   If the condition is not met, it sets `condition_met = False` and creates a failure reference.
    -   If no condition is provided, it acts as a pass-through.

6.  **`MIA`, `OR`, `OWI`** continue with wrapping, output, and finalization.

## Prompt Format

The prompt template file should be a standard text file with placeholders for substitution (e.g., `$input_1`, `$input_2`).

### With `with_thinking`

When the `with_thinking: true` flag is set in the configuration, the LLM is expected to return a JSON object containing its reasoning and the final answer. The prompt template must instruct the model to follow this structure.

**Example Prompt (`prompt_with_thinking.txt`):**
```
You are evaluating the following statement: $input_1

Your output must be a single JSON object.

First, think step-by-step about the evaluation. Place your reasoning in the "analysis" key of the JSON object.
Then, provide your judgment (true/false) in the "answer" key.

Example of the final JSON output:
```json
{
  "analysis": "Step-by-step reasoning about whether the statement is true or false...",
  "answer": true
}
```

Return only the JSON object.
```

## Comparison with `imperative_direct`

The `judgement_direct` sequence is similar to `imperative_direct` but adds:

-   **Conditional checking**: The `TIP` step can evaluate whether results match a specified condition
-   **State management**: The states include `condition` and `condition_met` fields for tracking evaluation results
-   **Use case**: Optimized for yes/no or conditional evaluations rather than general imperative commands
