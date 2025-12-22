# Understanding orchestrator context and agent models
_Exported on 12/4/2025 at 14:25:20 GMT+8 from Cursor (2.1.32)_

---

**User**

@.cursor/chats/orchestrator_context.md understsand in particular @infra/_agent/_models/_paradigms/_paradigm.py @infra/_agent/_body.py 

---

**Cursor**

Based on the provided files and context, here is an explanation of how `_paradigm.py` and `_body.py` function within the orchestration architecture.

### High-Level Relationship

Think of these two components as the **Blueprints** and the **Toolbox**:

1.  **`_paradigm.py` (The Blueprints)**: Responsible for loading the instructions. It reads declarative JSON files that describe *what* needs to be done (the plan).
2.  **`_body.py` (The Toolbox)**: Responsible for providing the capabilities. It holds the actual Python instances of tools (LLM, FileSystem, etc.) that *do* the work.

---

### 1. `infra/_agent/_body.py`: The Agent's Body (Toolbox)

This class represents the physical capabilities of an agent. In the context of `orchestrator_context.md`, the `Body` is instantiated by the CLI and passed down through the Orchestrator to the `AgentFrame`.

**Key Responsibilities:**
*   **Centralized Tool Management:** It initializes and stores references to every tool the agent might need:
    *   `llm`: The "brain" (Language Model).
    *   `file_system`: The "hands" for disk I/O (scoped to `base_dir`).
    *   `python_interpreter`: Capability to run code.
    *   `composition_tool`: The logic to stitch other tools together.
    *   `formatter_tool`: String manipulation/templating.
*   **Context Enforcement:** It accepts a `base_dir` argument. This is critical for security and organization, ensuring that the `file_system` tool and other components only operate within a specific project directory.
*   **Self-Reflection:** It injects itself into the `python_interpreter` (`setattr(self.python_interpreter, "body", self)`). This allows Python scripts executed by the agent to access the agent's own tools (e.g., a script could ask the LLM a question).

**In Context:**
When the `cli_orchestrator.py` runs:
```python
# The body acts as the unified interface for all capabilities
body = Body(llm_name=args.llm, base_dir=base_dir)
```

### 2. `infra/_agent/_models/_paradigms/_paradigm.py`: The Blueprint Loader

This file is the bridge between the static JSON files (Paradigms) and the active Python code. The `orchestrator_context.md` mentions "Paradigms" as "Declarative JSON workflows." This file is the code that understands how to read them.

**Key Responsibilities:**
*   **Loading & Deserialization:** The `Paradigm.load(name)` method finds the corresponding JSON file in `PARADIGMS_DIR` and loads it.
*   **Structure Reconstruction:** It doesn't just load a dictionary; it converts the JSON data into structured "Spec" objects (`ModelEnvSpecLite`, `ModelSequenceSpecLite`, `ToolSpecLite`) using helper functions like `_build_env_spec` and `_build_sequence_spec`.
*   **Custom Logic:** It uses `_paradigm_object_hook` to handle special types like `MetaValue` that might exist in the JSON but need specific Python class representations.

**In Context:**
When the `imperative_in_composition` sequence runs (as described in the architecture):
1.  It identifies which paradigm to run (e.g., from `working_interpretation`).
2.  It calls `Paradigm.load("paradigm_name")`.
3.  The returned `Paradigm` object tells the system:
    *   **`env_spec`**: "I need the `llm` and `file_system` tools."
    *   **`sequence_spec`**: "Step 1: Generate text. Step 2: Save to file."

### How They Connect

The connection happens inside the `AgentFrame` during execution (specifically in the **MFP** step of the `imperative_in_composition` sequence):

1.  **Request:** The **Paradigm** says, "I need a tool called `file_system` to perform Step 5."
2.  **Fulfillment:** The system looks at the **Body**, finds `body.file_system`, and binds it to that step.
3.  **Execution:** The **Body**'s `composition_tool` is then used to compile the **Paradigm**'s `sequence_spec` into an executable Python function.

**Summary Diagram:**

```mermaid
graph TD
    A[JSON File] -->|Loaded by| B(_paradigm.py)
    B -->|Produces| C[Paradigm Object]
    C -->|Contains| D[Specs: "What to do"]
    
    E[CLI Args] -->|Configures| F(_body.py)
    F -->|Produces| G[Body Object]
    G -->|Contains| H[Tools: "How to do it"]

    D -->|Combined with| H
    H -->|Via| I[Composition Tool]
    I -->|Executes| J[Final Action]
```

```python
# The body acts as the unified interface for all capabilities
body = Body(llm_name=args.llm, base_dir=base_dir)
```

```plaintext
graph TD
    A[JSON File] -->|Loaded by| B(_paradigm.py)
    B -->|Produces| C[Paradigm Object]
    C -->|Contains| D[Specs: "What to do"]
    
    E[CLI Args] -->|Configures| F(_body.py)
    F -->|Produces| G[Body Object]
    G -->|Contains| H[Tools: "How to do it"]

    D -->|Combined with| H
    H -->|Via| I[Composition Tool]
    I -->|Executes| J[Final Action]
```

---

**User**

ok - can we customize paradigms rom where are provvided? - i..e provide paradigms by passed a special paradigm class into the body etc.

---

**Cursor**

Yes, you can absolutely customize where paradigms are loaded from by injecting a custom paradigm provider into the `Body`.

Currently, the system hardcodes the loading logic in `infra/_agent/_steps/imperative_in_composition/_iwi.py` to use the default `Paradigm.load()`. By modifying the `Body` to accept a custom tool and updating the IWI step to check for it, you can redirect this logic to your own class.

Here are the necessary changes:

### 1. Update `Body` to accept a `paradigm_tool`
Modify the `__init__` method in `infra/_agent/_body.py` to accept an optional `paradigm_tool`. This tool should implement a `load(name)` method.

```python:infra/_agent/_body.py
// ... existing code ...
class Body:
    def __init__(self, llm_name: str = "qwen-turbo-latest", base_dir: str | None = None, new_user_input_tool: bool = True, paradigm_tool: Any = None) -> None:
        self.base_dir = base_dir
        self.paradigm_tool = paradigm_tool
        self.prompt_tool = PromptTool(base_dir=base_dir)
        # Backwards-compatible alias
// ... existing code ...
```

### 2. Update the IWI Step to use the custom tool
Modify `infra/_agent/_steps/imperative_in_composition/_iwi.py` to prioritize `body.paradigm_tool` if it exists.

```python:infra/_agent/_steps/imperative_in_composition/_iwi.py
// ... existing code ...
    paradigm_name = config.get("paradigm")
    if not paradigm_name:
        raise ValueError("IWI for imperative_in_composition requires a 'paradigm' key in the working_interpretation.")
    
    if hasattr(body, "paradigm_tool") and body.paradigm_tool:
        paradigm = body.paradigm_tool.load(paradigm_name)
    else:
        paradigm = Paradigm.load(paradigm_name)
        
    logger.info(f"Loaded composition paradigm: '{paradigm_name}'")

    # Build and save the specs for MFP to execute
// ... existing code ...
```

### How to use it

You can now define a custom class that mimics the `Paradigm` class interface and pass it when creating the `Body`:

```python
class MyParadigmLoader:
    def load(self, name: str):
        # Your custom logic to load paradigm JSON/objects from database, API, etc.
        return CustomParadigm.load_from_db(name)

# When initializing the orchestrator/body:
body = Body(
    llm_name="qwen-plus", 
    base_dir="./my_project",
    paradigm_tool=MyParadigmLoader()
)
```

```python
// ... existing code ...
class Body:
    def __init__(self, llm_name: str = "qwen-turbo-latest", base_dir: str | None = None, new_user_input_tool: bool = True, paradigm_tool: Any = None) -> None:
        self.base_dir = base_dir
        self.paradigm_tool = paradigm_tool
        self.prompt_tool = PromptTool(base_dir=base_dir)
        # Backwards-compatible alias
// ... existing code ...
```

```python
// ... existing code ...
    paradigm_name = config.get("paradigm")
    if not paradigm_name:
        raise ValueError("IWI for imperative_in_composition requires a 'paradigm' key in the working_interpretation.")
    
    if hasattr(body, "paradigm_tool") and body.paradigm_tool:
        paradigm = body.paradigm_tool.load(paradigm_name)
    else:
        paradigm = Paradigm.load(paradigm_name)
        
    logger.info(f"Loaded composition paradigm: '{paradigm_name}'")

    # Build and save the specs for MFP to execute
// ... existing code ...
```

```python
class MyParadigmLoader:
    def load(self, name: str):
        # Your custom logic to load paradigm JSON/objects from database, API, etc.
        return CustomParadigm.load_from_db(name)

# When initializing the orchestrator/body:
body = Body(
    llm_name="qwen-plus", 
    base_dir="./my_project",
    paradigm_tool=MyParadigmLoader()
)
```

---

**User**

let's try this - I will test this later. just update body and iwi - when updating body let's also default the body's paradigm tool to the defaul paradigm class

---

**Cursor**


Updating `Body` to accept a `paradigm_tool` (defaulting to `Paradigm`) and updating the IWI step to use it.



Updating both files:


```python
from typing import Any, Dict, Callable
from infra._agent._models import (
    PromptTool,
    FileSystemTool,
    PythonInterpreterTool,
    FormatterTool,
    CompositionTool,
    UserInputTool,
)


class Body:
    def __init__(self, llm_name: str = "qwen-turbo-latest", base_dir: str | None = None, new_user_input_tool: bool = True, paradigm_tool: Any = None) -> None:
        self.base_dir = base_dir
        self.prompt_tool = PromptTool(base_dir=base_dir)
        # Backwards-compatible alias
        self.prompt = PromptTool(base_dir=base_dir)
        try:
            from infra._agent._models import LanguageModel as _LM
            self.llm = _LM(llm_name)
        except Exception:
            class _MockLM:
                def create_generation_function(self, prompt_template: str):
                    from string import Template as _T

                    def _fn(vars: dict | None = None) -> str:
                        return _T(prompt_template).safe_substitute(vars or {})

                    return _fn

                def generate(self, prompt: str, system_message: str = "") -> str:
                    return f"GENERATED[{prompt}]"

            self.llm = _MockLM()

        # Add buffer and fn tools to match model_runner_real_demo.py
        class _BufferTool:
            def __init__(self) -> None:
                self._store: Dict[str, Any] = {}

            def write(self, record_name: str, new_record: Any) -> Any:
                self._store[record_name] = new_record
                return new_record

            def read(self, record_name: str) -> Any:
                return self._store.get(record_name)

        class _FnTool:
            def invoke(self, fn, vars: Dict[str, Any] | None = None) -> Any:
                return fn(vars or {})

        self.buffer = _BufferTool()
        self.fn = _FnTool()

        # User input tool for imperative_input sequence
        class _UserInputTool:
            def create_input_function(self, prompt_key: str = "prompt_text") -> Callable:
                """
                Creates a function that prompts the user for input.
                The function expects a dict with 'prompt_text' and optional context keys.
                """
                from typing import Dict as _Dict, Any as _Any

                def input_fn(vars: _Dict[str, _Any] | None = None) -> str:
                    vars = vars or {}
                    prompt_text = vars.get(prompt_key, "Enter input: ")
                    context = {k: v for k, v in vars.items() if k.startswith("context_")}

                    # Build the full prompt message
                    if context:
                        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                        full_prompt = f"{prompt_text}\n{context_str}\n> "
                    else:
                        full_prompt = f"{prompt_text}\n> "

                    # Prompt the user and return their response
                    return input(full_prompt)

                return input_fn

        self.user_input = UserInputTool() if new_user_input_tool else _UserInputTool()
        self.file_system = FileSystemTool(base_dir=base_dir)
        self.python_interpreter = PythonInterpreterTool()
        # Attach a back-reference so the interpreter can inject Body into scripts when appropriate
        setattr(self.python_interpreter, "body", self)

        self.formatter_tool = FormatterTool()
        self.composition_tool = CompositionTool()

        # Pass the body's tool instances to the llm to ensure they share the same context (e.g., base_dir)
        if hasattr(self.llm, "file_tool"):
            self.llm.file_tool = self.file_system
        if hasattr(self.llm, "python_interpreter"):
            self.llm.python_interpreter = self.python_interpreter
```

```python
from typing import Any, Dict, Callable
from infra._agent._models import (
    PromptTool,
    FileSystemTool,
    PythonInterpreterTool,
    FormatterTool,
    CompositionTool,
    UserInputTool,
)


class Body:
    def __init__(self, llm_name: str = "qwen-turbo-latest", base_dir: str | None = None, new_user_input_tool: bool = True, paradigm_tool: Any = None) -> None:
        self.base_dir = base_dir
        self.prompt_tool = PromptTool(base_dir=base_dir)
        # Backwards-compatible alias
        self.prompt = PromptTool(base_dir=base_dir)
        try:
            from infra._agent._models import LanguageModel as _LM
            self.llm = _LM(llm_name)
        except Exception:
            class _MockLM:
                def create_generation_function(self, prompt_template: str):
                    from string import Template as _T

                    def _fn(vars: dict | None = None) -> str:
                        return _T(prompt_template).safe_substitute(vars or {})

                    return _fn

                def generate(self, prompt: str, system_message: str = "") -> str:
                    return f"GENERATED[{prompt}]"

            self.llm = _MockLM()

        # Add buffer and fn tools to match model_runner_real_demo.py
        class _BufferTool:
            def __init__(self) -> None:
                self._store: Dict[str, Any] = {}

            def write(self, record_name: str, new_record: Any) -> Any:
                self._store[record_name] = new_record
                return new_record

            def read(self, record_name: str) -> Any:
                return self._store.get(record_name)

        class _FnTool:
            def invoke(self, fn, vars: Dict[str, Any] | None = None) -> Any:
                return fn(vars or {})

        self.buffer = _BufferTool()
        self.fn = _FnTool()

        # User input tool for imperative_input sequence
        class _UserInputTool:
            def create_input_function(self, prompt_key: str = "prompt_text") -> Callable:
                """
                Creates a function that prompts the user for input.
                The function expects a dict with 'prompt_text' and optional context keys.
                """
                from typing import Dict as _Dict, Any as _Any

                def input_fn(vars: _Dict[str, _Any] | None = None) -> str:
                    vars = vars or {}
                    prompt_text = vars.get(prompt_key, "Enter input: ")
                    context = {k: v for k, v in vars.items() if k.startswith("context_")}

                    # Build the full prompt message
                    if context:
                        context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                        full_prompt = f"{prompt_text}\n{context_str}\n> "
                    else:
                        full_prompt = f"{prompt_text}\n> "

                    # Prompt the user and return their response
                    return input(full_prompt)

                return input_fn

        self.user_input = UserInputTool() if new_user_input_tool else _UserInputTool()
        self.file_system = FileSystemTool(base_dir=base_dir)
        self.python_interpreter = PythonInterpreterTool()
        # Attach a back-reference so the interpreter can inject Body into scripts when appropriate
        setattr(self.python_interpreter, "body", self)

        self.formatter_tool = FormatterTool()
        self.composition_tool = CompositionTool()

        # Set up paradigm tool - default to Paradigm class if not provided
        if paradigm_tool is None:
            from infra._agent._models._paradigms import Paradigm
            # Create a wrapper that provides a load method
            class _DefaultParadigmTool:
                def load(self, paradigm_name: str):
                    return Paradigm.load(paradigm_name)
            self.paradigm_tool = _DefaultParadigmTool()
        else:
            self.paradigm_tool = paradigm_tool

        # Pass the body's tool instances to the llm to ensure they share the same context (e.g., base_dir)
        if hasattr(self.llm, "file_tool"):
            self.llm.file_tool = self.file_system
        if hasattr(self.llm, "python_interpreter"):
            self.llm.python_interpreter = self.python_interpreter
```

```python
from typing import Any, Dict
import logging

# Forward-referencing type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from infra import Inference
    from infra._states._imperative_states import States
    from infra._agent._body import Body

from infra._states._model_state import (
	AffordanceSpecLite,
	ToolSpecLite,
	ModelEnvSpecLite,
	ModelStepSpecLite,
	ModelSequenceSpecLite,
	MetaValue,
)
from infra._states._common_states import ReferenceRecordLite
from infra._core import Reference, Concept


def input_working_interpretation(
    inference: "Inference", 
    states: "States", 
    body: "Body",
    working_interpretation: Dict[str, Any] | None = None,
) -> "States":
    """
    IWI step for imperative_direct.
    Builds and saves the specs for creating a generic generation function in a later step.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Running IWI for imperative_direct: Building specs for generic function.")

    states.body = body
    
    config = working_interpretation or {}

    paradigm_name = config.get("paradigm")
    if not paradigm_name:
        raise ValueError("IWI for imperative_in_composition requires a 'paradigm' key in the working_interpretation.")
    
    paradigm = body.paradigm_tool.load(paradigm_name)
    logger.info(f"Loaded composition paradigm: '{paradigm_name}'")

    # Build and save the specs for MFP to execute
    states.mfp_env_spec = paradigm.env_spec
    states.mfp_sequence_spec = paradigm.sequence_spec
    
    # Store axis creation preference (default is True for backward compatibility)
    states.create_axis_on_list_output = config.get("create_axis_on_list_output", True)
    
    # Set value_order and initial values for MVP
    states.value_order = config.get("value_order")
    states.value_selectors = config.get("value_selectors", {})
    values_dict = config.get("values", {})
    for key, value in values_dict.items():
        record = ReferenceRecordLite(
            step_name="IR",  # Use "IR" to be compatible with MVP
            concept=Concept(name=key),
            reference=Reference(data=[value])
        )
        states.values.append(record)

    # Seed lists with empty records for each step's output
    for step in ["IR", "MFP"]:
        states.function.append(ReferenceRecordLite(step_name=step))
    for step in ["MVP"]:
        states.values.append(ReferenceRecordLite(step_name=step))
    for step in ["TVA"]:
        states.inference.append(ReferenceRecordLite(step_name=step))

    logger.info("Built and stored specs for creating a generic direct instruction function.")
    
    states.set_current_step("IWI")
    return states 
```


Checking for linting errors:



## Changes Made

### 1. **Updated `infra/_agent/_body.py`**:
   - Added `paradigm_tool` parameter to `__init__` (defaults to `None`)
   - Defaults to a wrapper around the default `Paradigm` class when `paradigm_tool` is `None`
   - The wrapper provides a `load()` method that calls `Paradigm.load()`

### 2. **Updated `infra/_agent/_steps/imperative_in_composition/_iwi.py`**:
   - Removed the direct import of `Paradigm`
   - Changed `Paradigm.load(paradigm_name)` to `body.paradigm_tool.load(paradigm_name)`
   - Now uses the paradigm tool from the body

## How It Works

- **Default behavior**: If no `paradigm_tool` is provided, it uses the default `Paradigm` class (backward compatible)
- **Custom behavior**: You can pass a custom paradigm tool class/instance that implements a `load(paradigm_name)` method:

```python
class MyCustomParadigmTool:
    def load(self, paradigm_name: str):
        # Your custom loading logic (database, API, etc.)
        return custom_paradigm_object

body = Body(
    llm_name="qwen-plus",
    base_dir="./my_project",
    paradigm_tool=MyCustomParadigmTool()
)
```

The IWI step will automatically use whatever paradigm tool is provided in the body. Ready for testing.

```python
class MyCustomParadigmTool:
    def load(self, paradigm_name: str):
        # Your custom loading logic (database, API, etc.)
        return custom_paradigm_object

body = Body(
    llm_name="qwen-plus",
    base_dir="./my_project",
    paradigm_tool=MyCustomParadigmTool()
)
```

