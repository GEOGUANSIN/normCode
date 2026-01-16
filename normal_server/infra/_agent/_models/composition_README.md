# Declarative Function Composition Mechanism

This document explains the declarative function composition mechanism used by the agent infrastructure. This system allows for the dynamic creation of complex, multi-step functions from a series of smaller, reusable tools, all orchestrated by declarative specifications.

## Core Concepts: Vertical vs. Horizontal Steps

The entire system is best understood by splitting the process into two distinct phases, which we will call **Vertical Steps** and **Horizontal Steps**.

### 1. Vertical Steps (The Setup Phase)

The "Vertical Steps" are the sequence of `ModelStepSpecLite` definitions executed by the `ModelSequenceRunner`. This phase is responsible for **setup, configuration, and resolving callable function handles**.

-   **Executor**: `ModelSequenceRunner`
-   **Goal**: To prepare the environment and gather all the necessary tools and functions.
-   **Analogy**: This is like an assembly line preparing all the parts and tools *before* starting the actual construction. The runner moves "vertically" down the `sequence_spec`, preparing one component at a time.

### 2. Horizontal Steps (The Execution Phase)

The "Horizontal Steps" are the individual steps within the **Execution Plan** that is passed to the `CompositionTool`. This phase defines the **runtime data flow and logic** of the final, composed function.

-   **Executor**: The composed function created by the `CompositionTool`.
-   **Goal**: To define how data flows from one function to the next when the final function is called.
-   **Analogy**: This is the blueprint for the actual construction. The `CompositionTool` creates a function that moves "horizontally" across the plan, passing the output of one step as the input to the next.

## Core Components

### `ModelSequenceRunner` (Executes Vertical Steps)

The `ModelSequenceRunner` is the high-level orchestrator. It executes the vertical steps to resolve affordance strings (e.g., `"llm.generate"`) into real, callable function handles, storing them in a `meta` context.

### `CompositionTool` (Builds the Horizontal Plan Executor)

The `CompositionTool` is a generic utility. Its `compose` method takes the fully resolved Execution Plan (where all functions are real handles gathered by the runner) and returns a single, new callable function. It is a pure, stateless micro-workflow engine that knows nothing about tools or affordances, only about executing a plan of callables.

## Inputs: Vertical vs. Horizontal

This two-phase model gives us two powerful ways to provide inputs to our composed function.

### Horizontal Inputs (Runtime `vars`)

This is the standard pattern. Data is provided at runtime in the `vars` dictionary when the final composed function is called. This is ideal for data that changes with every call.

In `composition_python_execution.py`, the `prompt_template` is a **horizontal input**. The final function is generic and requires the prompt to be passed in every time it's called.

```python
# The final function requires the prompt at runtime
test_vars = {
    "prompt_template": "...", 
    "script_location": "...",
    "script_inputs": {"a": 10, "b": 5}
}
final_result = instruction_fn(test_vars)
```

### Vertical Inputs (Composition-Time State Resolution)

A more advanced and powerful pattern is to provide data by referencing the `states` object that the `ModelSequenceRunner` is initialized with. This is ideal for pre-configuring a specialized function using dynamic runtime state.

In `composition_py_exec_vertical_prompt.py`, the `prompt_template` is a **vertical input** resolved from the `states` object. The paradigm's JSON specifies *where* to find the prompt (`states.inference.concept`), and the runner injects it during the Vertical (setup) phase.

```python
# The paradigm's JSON specifies a MetaValue pointing to the states object:
# "params": { "template": { "__type__": "MetaValue", "key": "states.inference.concept" } }

# The runner is initialized with a state object that has the required attribute:
class StateProxy:
    def __init__(self, body, prompt):
        self.body = body
        self.inference = SimpleNamespace(concept=prompt)

runtime_states = StateProxy(Body(), "You are a helpful assistant...")
runner = ModelSequenceRunner(runtime_states, sequence_spec)

# The final composed function is now specialized and no longer needs the prompt:
test_vars = {
    "script_location": "...",
    "script_inputs": {"x": 7, "y": 6}
}
final_result = instruction_fn(test_vars)
```

## Application in NormCode: Mapping to Inference

In the context of the NormCode project, this distinction maps directly to the concept of an "inference":

-   **Vertical Inputs** are typically specified by the **function** of the inference. They define *what kind of operation* is being built (e.g., "create a multiplication script").
-   **Horizontal Inputs** are specified by the **value** of the inference. They provide the specific data for that operation to run on (e.g., `{'x': 7, 'y': 6}`).


## The Execution Plan & Conditional Logic

The power of this system lies in the explicit, declarative **Execution Plan** (the horizontal steps). This plan is a list of dictionaries, where each dictionary represents a step in the pipeline, giving us precise control over the data flow.

Each step defines:
- `output_key`: The name to store the result of this step under.
- `function`: The function to execute (resolved from a `MetaValue` by the vertical steps).
- `params`: A dictionary mapping the function's arguments to the `output_key` of a previous horizontal step.
- `literal_params`: A dictionary of arguments to be passed as literal values.
- `condition`: An optional dictionary (`{'key': '...', 'operator': 'is_true'}`) that, if it evaluates to false, causes the step to be skipped. This enables conditional branching.

### Canonical Example with Conditional Logic

Here is how the plan in our Python execution experiment works.

First, the **Vertical Steps** gather handles for all necessary functions (`exists_fn`, `read_fn`, `generate_fn`, etc.).

Then, a final vertical step calls `composition_tool.compose` and passes it the **Horizontal Plan**. This plan now includes conditional logic.

```python
"plan": [
    # ... steps to get script_location and script_inputs ...
    
    # 1. Check if the file exists. The result is stored in 'script_exists'.
    {
        'output_key': 'script_exists',
        'function': MetaValue(key="exists_fn"),
        'params': {'__positional__': 'script_location'}
    },
    
    # --- "IF" Branch (Horizontal Steps) ---
    # These steps only run if 'script_exists' is True.
    {
        'condition': {'key': 'script_exists', 'operator': 'is_true'},
        'output_key': 'read_result',
        'function': MetaValue(key="read_fn"),
        # ...
    },
    {
        'condition': {'key': 'script_exists', 'operator': 'is_true'},
        'output_key': 'code_to_run',
        'function': MetaValue(key="dict_get_fn"),
        # ...
    },

    # --- "ELSE" Branch (Horizontal Steps) ---
    # These steps only run if 'script_exists' is False.
    {
        'condition': {'key': 'script_exists', 'operator': 'is_false'},
        'output_key': 'prompt_string',
        'function': MetaValue(key="template_fn"),
        # ...
    },
    # ... more generation steps, each with the same condition ...
    
    # --- Final Unconditional Step ---
    # This step runs regardless of the condition, using 'code_to_run' which
    # was populated by whichever branch was taken.
    {
        'output_key': 'execution_result',
        'function': MetaValue(key="function_execute_fn"),
        'params': {
            'script_code': 'code_to_run',
            'function_params': 'script_inputs'
        },
        'literal_params': { 'function_name': 'main' }
    },
],
"return_key": "execution_result"
```

This pattern demonstrates:
1.  **Pure Declarative Spec**: The spec only contains affordance strings and `MetaValue` references.
2.  **Clear Separation of Concerns**: The Vertical Steps (Runner) do the resolving; the Horizontal Steps (Plan) do the runtime execution.
3.  **Maximum Flexibility**: The plan can orchestrate complex conditional workflows, use literal values, and precisely control the final return value.

---

## Full Worked Example

Below is the full, runnable code for the `py_exec_vertical_prompt` pattern. It demonstrates all the concepts described above: loading a paradigm, simulating a `states` object, and executing the dynamically composed function.

```python
"""
This script demonstrates how to replicate the behavior of the hard-coded
`create_python_generate_and_run_function_from_prompt` method from `_language_models.py`.

This pattern shows how to create a pre-configured function where the prompt
template is provided by the runtime `states` object during the composition phase.
"""
from typing import Any, Dict
from types import SimpleNamespace
import pathlib
import sys

# --- Fix Python path to allow running as a script ---
project_root = pathlib.Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# --- Define a base directory and output filename ---
models_dir = pathlib.Path(__file__).parent
output_filename = "generated_script_from_prompt.py"

# --- Assume these imports are available from the infra ---
from infra._agent._models._model_runner import ModelSequenceRunner
from infra._agent._body import Body
from infra._agent._models._paradigms import Paradigm


# --- 1. Load the Paradigm ---
# The env_spec and sequence_spec are now loaded from a declarative JSON file.
paradigm = Paradigm.load("py_exec_vertical_prompt")
sequence_spec = paradigm.sequence_spec


# --- 2. Define the Runtime Environment and Execute ---

# In a real application, the prompt would come from a complex state object.
# We simulate that here by creating a proxy object that has the same structure
# the paradigm expects (`states.inference.concept`).
class StateProxy:
    def __init__(self, body, prompt):
        self.body = body
        self.inference = SimpleNamespace(concept=prompt)

prompt_template_from_state = (
    "You are a helpful assistant that writes simple Python code.\\n"
    "Write a Python script that defines a single function named 'main'.\\n"

    "The function should take two arguments, 'x' and 'y', and return their product.\\n"
    "Do not include any example usage or calls to the function in the script. Only provide the function definition."
)
runtime_states = StateProxy(Body(base_dir=str(models_dir)), prompt_template_from_state)

# The runner is initialized with the state object, allowing MetaValues to
# resolve keys like 'states.inference.concept'.
runner = ModelSequenceRunner(runtime_states, sequence_spec)
meta = runner.run()
instruction_fn = meta.get("instruction_fn")

# --- 3. Test the Composed Function ---
if instruction_fn:
    print(">>> Successfully composed Python execution function from a pre-set prompt.")
    print(">>> Calling the function (this will make a real API call)...")

    # The `vars` no longer need to contain the `prompt_template`.
    test_vars = {
        "script_location": output_filename,
        "script_inputs": {"x": 7, "y": 6}
    }

    final_result = instruction_fn(test_vars)

    print(f"\\n>>> Final result of composed function: {final_result}")

    if final_result == 42:
        print(f">>> Test successful: Received the correct result of 42.")
        assert final_result == 42
    elif isinstance(final_result, dict) and "error" in final_result:
        print(f">>> Test failed gracefully with error: {final_result['error']}")
    else:
        print(f">>> Test finished with an unexpected result: {final_result}")
else:
    print("!!! Failed to compose instruction_fn.")
```
