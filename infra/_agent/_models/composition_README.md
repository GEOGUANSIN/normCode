# Declarative Function Composition Mechanism

This document explains the declarative function composition mechanism used by the agent infrastructure, as demonstrated in `composition_experiment.py` and `composition_experiment_thinking.py`. This system allows for the dynamic creation of complex, multi-step functions from a series of smaller, reusable tools, all orchestrated by declarative specifications.

## Core Components & Architectural Pattern

The system is built on a clean separation of concerns between two primary components: the `ModelSequenceRunner` and the `CompositionTool`.

### 1. `ModelSequenceRunner` (The Orchestrator & Resolver)

The `ModelSequenceRunner` acts as the high-level planner and resolver. Its responsibilities are:
- To read a `ModelSequenceSpecLite` (`sequence_spec`).
- To execute each `ModelStepSpecLite` (`step`) in the sequence.
- To manage a runtime context, storing the results of each step in a `meta` dictionary.
- **To resolve affordances into callable function handles.** This is its most critical role in this pattern. It is the bridge between the static spec and the live, runtime tool instances.

The canonical practice is to use the runner to gather *all* necessary function handles—including handles to instance methods like `language_model.generate`—before passing them to the composition tool.

### 2. `CompositionTool` (The Plan Executor)

The `CompositionTool` is a generic, low-level utility. Its `compose` method takes a fully resolved **Execution Plan** and a `return_key` and returns a single, new callable function. It is a pure, stateless micro-workflow engine.

- **Input**: A `plan` (a list of dictionaries where all `function` values are real, callable functions) and an optional `return_key`.
- **Output**: A single function that, when called with an initial dictionary of variables (`vars`), will execute the entire plan.

This separation ensures that the `CompositionTool` remains generic and reusable, while the `ModelSequenceRunner` handles the environment-specific task of resolving tools and methods.

## The Execution Plan

The power of this system lies in the explicit, declarative **Execution Plan**. This plan is a list of dictionaries, where each dictionary represents a step in the pipeline. It gives us precise control over the data flow.

Each step in the plan defines:
- `output_key`: The name to store the result of this step under.
- `function`: The function to execute. The runner resolves this from a `MetaValue` that points to a previously retrieved function handle.
- `params`: A dictionary mapping the function's keyword arguments to the `output_key` of a previous step. A special key, `__initial_input__`, refers to the dictionary the composed function was originally called with.
- `literal_params`: A dictionary of keyword arguments that should be passed to the function as literal values, not as references to previous results.

### Canonical Example (`composition_experiment_thinking.py`)

Here is how the plan in our "thinking" experiment works. This represents the canonical best practice.

First, the `ModelSequenceRunner` executes a series of simple steps to get handles to all necessary functions:
```python
# In sequence_spec.steps:
ModelStepSpecLite(..., affordance="formatter_tool.create_substitute_function", ..., result_key="template_fn"),
ModelStepSpecLite(..., affordance="language_model.generate", ..., result_key="generate_fn"),
ModelStepSpecLite(..., affordance="formatter_tool.parse", ..., result_key="parse_fn"),
# ... and so on for all other functions.
```

Then, in a final step, it calls the generic `composition_tool.compose` and passes it a plan where the `function` values are `MetaValue`s pointing to the handles it just retrieved:

```python
# In the final step's params:
"plan": [
    # 1. Get the prompt string
    {
        'output_key': 'prompt_string',
        'function': MetaValue(key="template_fn"),
        'params': {'__positional__': '__initial_input__'}
    },
    # 2. Call the LLM
    {
        'output_key': 'raw_llm_response',
        'function': MetaValue(key="generate_fn"), # Resolved handle, not a placeholder
        'params': {'__positional__': 'prompt_string'}
    },
    # ... subsequent steps for parsing, saving, wrapping, etc.
],
"return_key": "mia_result"
```

This pattern demonstrates:
1.  **Pure Declarative Spec**: The spec only contains affordance strings and `MetaValue` references, never live objects or instance methods.
2.  **Clear Separation of Concerns**: The `Runner` does the resolving; the `CompositionTool` does the executing.
3.  **Maximum Flexibility**: The plan can orchestrate any combination of resolved function handles to create incredibly flexible and powerful workflows, all defined declaratively at runtime.
