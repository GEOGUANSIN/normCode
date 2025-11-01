# Imperative Input Sequence

## Purpose

The `imperative_input` sequence provides a specialized method for collecting user input interactively. It is a variation of the `imperative` sequence that replaces the language model call with direct user interaction. This makes it ideal for scenarios where the system needs to request information from the user during the execution of a NormCode plan.

## Methodology

This sequence follows the same general pattern as `imperative_direct`, but replaces the LLM execution step with a user input prompt. The key difference is in the `TVA` (Tool Value Actuation) step, which prompts the user instead of calling a language model.

### Key Feature: Direct User Input

The sequence extracts a prompt text from the input values and uses it to directly request input from the user via Python's `input()` function.

### Workflow

1.  **`IWI` (Input Working Interpretation - `_iwi.py`)**
    -   Acts as a planner. It reads the agent's configuration.
    -   It builds a "plan" (the `env_spec` and `sequence_spec`) that defines how to create a user input function using the `user_input` tool affordance.
    -   It saves this plan to the agent's state without executing it.
    -   Sets up `value_order` and pre-populates values if provided in the configuration.

2.  **`IR` (Input References - `_ir.py`)**
    -   Populates references and concept information from the inference instance.
    -   Extracts the function concept, concept to infer, and value concepts.

3.  **`MFP` (Model Function Perception - `_mfp.py`)**
    -   Executes the plan created by `IWI`.
    -   It runs a `ModelSequenceRunner` which calls the `create_input_function` affordance on the `user_input` tool.
    -   This creates a function that expects its prompt text to be supplied at runtime.
    -   The input function is saved to the agent's state.

4.  **`MVP` (Memory Value Perception - `_mvp.py`)**
    -   Orders and extracts value references based on the working configuration.
    -   Strips wrappers (like `%(...)`) from reference elements.
    -   Performs a cross-product to get all combinations of values.
    -   Converts the result to a dictionary format where:
        -   The first value becomes `prompt_text` (the question/prompt for the user)
        -   Remaining values become `context_1`, `context_2`, etc. (additional context to display)

5.  **`TVA` (Tool Value Actuation - `_tva.py`)**
    -   **This is the key step**: Applies the input function created by `MFP` to the values prepared by `MVP`.
    -   Takes the input function from `MFP` and the values dictionary from `MVP`.
    -   Calls the function with the values, which prompts the user and returns their response.
    -   Stores the response in the inference state.

6.  **`TIP` (Tool Inference Perception - `_tip.py`)**
    -   Pass-through step that copies the result from TVA.

7.  **`MIA` (Memory Inference Actuation - `_mia.py`)**
    -   Wraps the user's response in the NormCode wrapper format `%{unique_code}({response})`.

8.  **`OR` (Output Reference - `_or.py`)**
    -   Finalizes the output reference by copying from MIA.

9.  **`OWI` (Output Working Interpretation - `_owi.py`)**
    -   Finalization step (no-op for this sequence).

## Usage Example

### NormCode Structure

```normcode
<- {user response} | imperative_input
    <= ::(ask the user {1}<$({prompt text})%_> to get {2}?<$({response})%_>)
    <- {prompt text}<:{1}>
    <- {response}?<:{2}>
```

### Working Interpretation

```json
{
    "value_order": {
        "{prompt text}": 1,
        "{response}?": 2
    }
}
```

### Expected Behavior

1. The `IWI` step builds specs for creating an input function.
2. The `MFP` step creates the input function using the `user_input.create_input_function` affordance.
3. The `MVP` step extracts `{prompt text}` as the `prompt_text` and prepares it as a dictionary.
4. The `TVA` step calls the input function with the prepared values, which prompts the user and waits for input.
5. The user's response is stored in `{response}?` and wrapped appropriately.
6. The final result is available in `{user response}`.

## Differences from `imperative` and `imperative_direct`

-   **No LLM Required**: Unlike `imperative`, this sequence doesn't call a language model. It uses the `user_input` tool instead.
-   **Uses Affordance System**: Similar to `imperative_direct`, it uses the affordance system to create a reusable input function in `MFP`.
-   **Consistent Architecture**: Follows the same pattern as `imperative_direct` but with user input instead of LLM generation.
-   **Interactive**: The sequence will block execution and wait for user input, making it suitable for interactive workflows.

## Considerations

-   The sequence will block execution while waiting for user input.
-   For non-interactive environments (e.g., automated scripts), consider using `imperative` or `imperative_direct` with pre-provided values instead.
-   The prompt text should be clear and specific to help the user understand what input is expected.
