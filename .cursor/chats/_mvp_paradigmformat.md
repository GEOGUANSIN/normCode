# Understanding and customizing agent paradigms
_Exported on 12/6/2025 at 18:03:32 GMT+8 from Cursor (2.1.32)_

---

**User**

@infra/_agent/_models/_paradigms/README.md understand paradigm in  @infra/_agent/_steps/imperative_in_composition/README.md @.cursor/chats/customize_paradigm.md 

---

**Cursor**

Based on the provided files and the code I've inspected, here is an explanation of what a **Paradigm** is, how it fits into the `imperative_in_composition` sequence, and how the recent customization changes enable flexibility.

### 1. What is a Paradigm?

A **Paradigm** is a **declarative blueprint** for a complex, multi-step function. Instead of writing Python code for every new agent capability (like "read file -> summarize -> save"), you define a JSON file that describes:

*   **`env_spec` (The Tools)**: What capabilities are needed (e.g., `llm`, `file_system`).
*   **`sequence_spec` (The Plan)**: The step-by-step data flow (e.g., "Take `input_1`, pass it to `llm.generate`, take result, pass to `file_system.write`").

**Naming Convention:**
Paradigms follow a strict naming structure to be self-documenting: `[inputs]-[logic]-[outputs].json`.
*   *Example:* `h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation.json`

### 2. The Paradigm Lifecycle (in `imperative_in_composition`)

The `imperative_in_composition` sequence is a **generic engine** that runs these blueprints.

1.  **IWI (The Planner)**:
    *   Reads the configuration (e.g., `paradigm: "thinking_save_and_wrap"`).
    *   **Loads the Paradigm**: Calls `body.paradigm_tool.load(name)`.
    *   Extracts the `env_spec` and `sequence_spec` and saves them to the state.

2.  **MFP (The Composer)**:
    *   Takes the specs from IWI.
    *   "Compiles" them into a single, executable Python function.

3.  **MVP (The Data Gatherer)**:
    *   Prepares inputs (mapping `input_1`, `input_2`...) based on the paradigm's requirements.

4.  **TVA (The Executor)**:
    *   Executes the function created by MFP.

### 3. Customization Mechanism

The files referenced in `.cursor/chats/customize_paradigm.md` (which I verified are applied in the codebase) allow you to change **where** these blueprints come from.

**Before:**
The system was hardcoded to load JSON files from the local `infra/_agent/_models/_paradigms/` directory.

**Now (The Customization):**
The system uses a **Dependency Injection** pattern in the agent's `Body`.

1.  **`infra/_agent/_body.py`**: The `Body` now accepts a `paradigm_tool`.
    ```python
    # Default behavior: Wraps the standard file-based loader
    if paradigm_tool is None:
        self.paradigm_tool = _DefaultParadigmTool() # calls Paradigm.load()
    else:
        self.paradigm_tool = paradigm_tool
    ```

2.  **`infra/_agent/_steps/imperative_in_composition/_iwi.py`**: The step no longer imports the static `Paradigm` class. Instead, it asks the `Body` for the paradigm:
    ```python
    # Uses whatever tool is injected into the body
    paradigm = body.paradigm_tool.load(paradigm_name)
    ```

**Implication:**
You can now inject a custom class that loads paradigms from a database, an API, or generates them on the fly, without changing the agent's core logic. You simply pass this custom tool when initializing the `Body`.

```python
    # Default behavior: Wraps the standard file-based loader
    if paradigm_tool is None:
        self.paradigm_tool = _DefaultParadigmTool() # calls Paradigm.load()
    else:
        self.paradigm_tool = paradigm_tool
```

```python
    # Uses whatever tool is injected into the body
    paradigm = body.paradigm_tool.load(paradigm_name)
```

---

**User**

now, let's first think about what is the best way to register and provide info for paradigm as in @direct_infra_experiment/nc_ai_planning_ex/iteration_6/prompts/repo_generate_five_steps/5.2.1_architect_step.md 

---

**Cursor**

The "Architect Step" prompt you referenced currently relies on a **static file reference** (`infra/_agent/_models/_paradigms/README.md`) to inform the LLM about available paradigms.

This is fragile: if you add a new paradigm JSON but forget to update the README, the Architect won't know about it.

The best way to handle this is to make the paradigms **self-registering** and **self-documenting**, then inject that information dynamically into the prompt.

### Recommended Design: "Self-Documenting Registry"

I propose we move the description *inside* the Paradigm JSON files and use your new `paradigm_tool` to expose them.

#### 1. The Data Source: Embed Metadata in JSON
Instead of maintaining a separate README, we add a `metadata` field to each paradigm JSON file. The loading logic (which currently ignores extra keys) will be safe, but we can update it to read this data.

**Example `h_UserPrompt-c_Ask-o_Normal.json`**:
```json
{
  "metadata": {
    "description": "Asks the user a question and returns their response.",
    "intent_keywords": ["ask", "user input", "question"],
    "inputs": {"prompt_text": "The question to display"},
    "output": "The user's typed string"
  },
  "env_spec": { ... },
  "sequence_spec": { ... }
}
```

#### 2. The Registry: `paradigm_tool.list_manifest()`
We update the `paradigm_tool` (in `_body.py`) to include a method that scans the paradigms directory (or your custom source), reads these `metadata` blocks, and returns a formatted string or list.

```python
def list_manifest(self) -> str:
    # Scans all .json files
    # Returns a string like:
    # - h_UserPrompt-c_Ask: Asks the user a question...
    # - h_PromptTemplate...: Generates a response from an LLM...
```

#### 3. The Usage: Dynamic Prompt Injection
In the Architect step, instead of pointing to a file path, you inject the result of this function.

**Updated Prompt (`5.2.1_architect_step.md`):**
```markdown
**2. Paradigms:**
Below is the library of available paradigms:
{{ body.paradigm_tool.list_manifest() }}
```

---

### Why this is better
1.  **Single Source of Truth**: The documentation lives *with* the code (the JSON).
2.  **No "Drift"**: You can't have a paradigm that exists but isn't documented (if the tool scans all files).
3.  **Flexible**: If you switch to a database loader later (using the customization we just built), `list_manifest` just queries the DB instead of the file system.

### Plan
If you agree, I can:
1.  Update `infra/_agent/_models/_paradigms/_paradigm.py` to support a `metadata` field.
2.  Update the `_DefaultParadigmTool` in `_body.py` to implement `list_manifest()`.
3.  Add `metadata` blocks to your existing key paradigm files (referencing the current README).

Shall I proceed with this implementation?

```json
{
  "metadata": {
    "description": "Asks the user a question and returns their response.",
    "intent_keywords": ["ask", "user input", "question"],
    "inputs": {"prompt_text": "The question to display"},
    "output": "The user's typed string"
  },
  "env_spec": { ... },
  "sequence_spec": { ... }
}
```

```python
def list_manifest(self) -> str:
    # Scans all .json files
    # Returns a string like:
    # - h_UserPrompt-c_Ask: Asks the user a question...
    # - h_PromptTemplate...: Generates a response from an LLM...
```

```markdown
**2. Paradigms:**
Below is the library of available paradigms:
{{ body.paradigm_tool.list_manifest() }}
```

---

**User**

ok we can do that, but make sure we distinguish vertical/function input form the horizontal/value input as mentioned in @infra/_agent/_models/composition_README.md see @infra/_agent/_models/_paradigms/v_PromptTemplate-h_ScriptLocation-c_Retrieve_or_GenerateThinkJson_ExtractPy_Execute-o_Normal.json @infra/_agent/_models/_paradigms/h_PromptTemplate_ScriptLocation-c_Retrieve_or_GenerateThinkJson_ExtractPy_ExecuteWBody-o_Normal.json . let's check if we are on the same page.

---

**Cursor**

Yes, we are exactly on the same page. The distinction is critical for the Architect because it determines **where** the data comes from in the Execution Plan:

1.  **Vertical Inputs (`v_...`)**: These are **Composition-Time Configurations**.
    *   *Source:* The `function_concept` (e.g., `states.function.concept.name`).
    *   *Mechanism:* `MetaValue` injection during the "setup" phase.
    *   *Architect's Job:* Ensure the `function_concept` definition itself contains this data (e.g., the prompt text).

2.  **Horizontal Inputs (`h_...`)**: These are **Runtime Arguments**.
    *   *Source:* The `value_concepts` (e.g., `input_1`, `save_path`).
    *   *Mechanism:* Passed in the `vars` dictionary (`__initial_input__`) during the "execution" phase.
    *   *Architect's Job:* Ensure the `value_concepts` provide these keys.

### Proposed Metadata Structure

To capture this, I will structure the `metadata` block to explicitly separate these requirements. This tells the Architect exactly how to "wire up" the Inference Unit.

**Example for `v_PromptTemplate-h_ScriptLocation...`:**

```json
"metadata": {
  "description": "Executes a Python script. If the script is missing, generates it using a prompt provided by the function definition.",
  "inputs": {
    "vertical": {
      "template": "The prompt template string (sourced from function_concept.name)."
    },
    "horizontal": {
      "script_location": "Path to the python script to execute/generate.",
      "script_inputs": "Dictionary of inputs to pass to the script."
    }
  },
  "outputs": {
    "type": "Normal",
    "description": "The return value of the executed script."
  }
}
```

### Implementation Plan

I will now provide the code changes to implement this **Self-Documenting Registry**.

#### 1. Update `infra/_agent/_models/_paradigms/_paradigm.py`
Modify the `Paradigm` class to store `metadata` and load it from the JSON.

```python:infra/_agent/_models/_paradigms/_paradigm.py
// ... existing code ...
class Paradigm:
    """
    Loads and reconstructs a full composition paradigm (environment and sequence specs)
    from a JSON file.
    """
    def __init__(self, env_spec: ModelEnvSpecLite, sequence_spec: ModelSequenceSpecLite, metadata: Dict[str, Any] | None = None):
        self.env_spec = env_spec
        self.sequence_spec = sequence_spec
        self.metadata = metadata or {}

    @classmethod
    def load(cls, paradigm_name: str) -> 'Paradigm':
// ... existing code ...
        with open(paradigm_file, 'r', encoding='utf-8') as f:
            raw_spec = json.load(f, object_hook=_paradigm_object_hook)

        env_spec_data = raw_spec['env_spec']
        sequence_spec_data = raw_spec['sequence_spec']
        metadata_data = raw_spec.get('metadata', {})

        # Reconstruct the spec objects from the loaded data
        env_spec = _build_env_spec(env_spec_data)
        sequence_spec = _build_sequence_spec(sequence_spec_data, env_spec)
        
        return cls(env_spec, sequence_spec, metadata_data)
```

#### 2. Update `infra/_agent/_body.py`
Add the `list_manifest()` method to the `_DefaultParadigmTool`. This method will scan the directory and generate the documentation string for the prompt.

```python:infra/_agent/_body.py
// ... existing code ...
        # Set up paradigm tool - default to Paradigm class if not provided
        if paradigm_tool is None:
            from infra._agent._models._paradigms import Paradigm, PARADIGMS_DIR
            import json
            import os

            # Create a wrapper that provides a load method
            class _DefaultParadigmTool:
                def load(self, paradigm_name: str):
                    return Paradigm.load(paradigm_name)
                
                def list_manifest(self) -> str:
                    """
                    Scans the paradigms directory and returns a formatted string 
                    describing all available paradigms and their inputs.
                    """
                    manifest = []
                    # List all .json files in PARADIGMS_DIR
                    for filename in os.listdir(PARADIGMS_DIR):
                        if filename.endswith(".json"):
                            name = filename[:-5] # Remove .json
                            try:
                                with open(PARADIGMS_DIR / filename, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    metadata = data.get('metadata', {})
                                    
                                    desc = metadata.get('description', 'No description provided.')
                                    v_inputs = metadata.get('inputs', {}).get('vertical', {})
                                    h_inputs = metadata.get('inputs', {}).get('horizontal', {})
                                    
                                    entry = f"- **{name}**\n  - *Description*: {desc}"
                                    if v_inputs:
                                        entry += "\n  - *Vertical Inputs (Function)*: " + ", ".join([f"`{k}`" for k in v_inputs.keys()])
                                    if h_inputs:
                                        entry += "\n  - *Horizontal Inputs (Values)*: " + ", ".join([f"`{k}`" for k in h_inputs.keys()])
                                    
                                    manifest.append(entry)
                            except Exception as e:
                                manifest.append(f"- **{name}**: Error reading metadata ({str(e)})")
                    
                    return "\n".join(manifest)

            self.paradigm_tool = _DefaultParadigmTool()
        else:
// ... existing code ...
```

#### 3. Example JSON Update
You would then update your paradigm files (e.g., `v_PromptTemplate-h_ScriptLocation...json`) to include the `metadata` block at the top level, as shown in the "Proposed Metadata Structure" section above.

**Does this plan look correct to you?** I can proceed with applying these changes if you are ready.

```json
"metadata": {
  "description": "Executes a Python script. If the script is missing, generates it using a prompt provided by the function definition.",
  "inputs": {
    "vertical": {
      "template": "The prompt template string (sourced from function_concept.name)."
    },
    "horizontal": {
      "script_location": "Path to the python script to execute/generate.",
      "script_inputs": "Dictionary of inputs to pass to the script."
    }
  },
  "outputs": {
    "type": "Normal",
    "description": "The return value of the executed script."
  }
}
```

```python
// ... existing code ...
class Paradigm:
    """
    Loads and reconstructs a full composition paradigm (environment and sequence specs)
    from a JSON file.
    """
    def __init__(self, env_spec: ModelEnvSpecLite, sequence_spec: ModelSequenceSpecLite, metadata: Dict[str, Any] | None = None):
        self.env_spec = env_spec
        self.sequence_spec = sequence_spec
        self.metadata = metadata or {}

    @classmethod
    def load(cls, paradigm_name: str) -> 'Paradigm':
// ... existing code ...
        with open(paradigm_file, 'r', encoding='utf-8') as f:
            raw_spec = json.load(f, object_hook=_paradigm_object_hook)

        env_spec_data = raw_spec['env_spec']
        sequence_spec_data = raw_spec['sequence_spec']
        metadata_data = raw_spec.get('metadata', {})

        # Reconstruct the spec objects from the loaded data
        env_spec = _build_env_spec(env_spec_data)
        sequence_spec = _build_sequence_spec(sequence_spec_data, env_spec)
        
        return cls(env_spec, sequence_spec, metadata_data)
```

```python
// ... existing code ...
        # Set up paradigm tool - default to Paradigm class if not provided
        if paradigm_tool is None:
            from infra._agent._models._paradigms import Paradigm, PARADIGMS_DIR
            import json
            import os

            # Create a wrapper that provides a load method
            class _DefaultParadigmTool:
                def load(self, paradigm_name: str):
                    return Paradigm.load(paradigm_name)
                
                def list_manifest(self) -> str:
                    """
                    Scans the paradigms directory and returns a formatted string 
                    describing all available paradigms and their inputs.
                    """
                    manifest = []
                    # List all .json files in PARADIGMS_DIR
                    for filename in os.listdir(PARADIGMS_DIR):
                        if filename.endswith(".json"):
                            name = filename[:-5] # Remove .json
                            try:
                                with open(PARADIGMS_DIR / filename, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    metadata = data.get('metadata', {})
                                    
                                    desc = metadata.get('description', 'No description provided.')
                                    v_inputs = metadata.get('inputs', {}).get('vertical', {})
                                    h_inputs = metadata.get('inputs', {}).get('horizontal', {})
                                    
                                    entry = f"- **{name}**\n  - *Description*: {desc}"
                                    if v_inputs:
                                        entry += "\n  - *Vertical Inputs (Function)*: " + ", ".join([f"`{k}`" for k in v_inputs.keys()])
                                    if h_inputs:
                                        entry += "\n  - *Horizontal Inputs (Values)*: " + ", ".join([f"`{k}`" for k in h_inputs.keys()])
                                    
                                    manifest.append(entry)
                            except Exception as e:
                                manifest.append(f"- **{name}**: Error reading metadata ({str(e)})")
                    
                    return "\n".join(manifest)

            self.paradigm_tool = _DefaultParadigmTool()
        else:
// ... existing code ...
```

---

**User**

ok let's try to provide the meta data for all of the paradigm in the paradigm dirs one by one 

---

**Cursor**

```python
import json
from pathlib import Path
from typing import Any, Dict, List

from infra._states import (
    ModelEnvSpecLite,
    ModelSequenceSpecLite,
    ModelStepSpecLite,
    ToolSpecLite,
    AffordanceSpecLite,
    MetaValue,
)

# --- Constants ---
PARADIGMS_DIR = Path(__file__).parent

# --- Custom Deserialization Hook ---

def _paradigm_object_hook(d: Dict[str, Any]) -> Any:
    """
    A custom object hook for json.load to reconstruct specific object types
    like MetaValue from a dictionary representation.
    """
    if "__type__" in d:
        if d["__type__"] == "MetaValue":
            return MetaValue(key=d["key"])
    return d

# --- Helper Functions for Reconstruction ---

def _build_affordance_spec(data: Dict[str, Any]) -> AffordanceSpecLite:
    return AffordanceSpecLite(affordance_name=data['affordance_name'], call_code=data['call_code'])

def _build_tool_spec(data: Dict[str, Any]) -> ToolSpecLite:
    return ToolSpecLite(
        tool_name=data['tool_name'],
        affordances=[_build_affordance_spec(aff) for aff in data['affordances']]
    )

def _build_env_spec(data: Dict[str, Any]) -> ModelEnvSpecLite:
    return ModelEnvSpecLite(
        tools=[_build_tool_spec(tool) for tool in data['tools']]
    )

def _build_step_spec(data: Dict[str, Any]) -> ModelStepSpecLite:
    return ModelStepSpecLite(
        step_index=data['step_index'],
        affordance=data['affordance'],
        params=data['params'],
        result_key=data['result_key']
    )

def _build_sequence_spec(data: Dict[str, Any], env_spec: ModelEnvSpecLite) -> ModelSequenceSpecLite:
    return ModelSequenceSpecLite(
        env=env_spec,
        steps=[_build_step_spec(step) for step in data['steps']]
    )

# --- Main Paradigm Class ---

class Paradigm:
    """
    Loads and reconstructs a full composition paradigm (environment and sequence specs)
    from a JSON file.
    """
    def __init__(self, env_spec: ModelEnvSpecLite, sequence_spec: ModelSequenceSpecLite, metadata: Dict[str, Any] | None = None):
        self.env_spec = env_spec
        self.sequence_spec = sequence_spec
        self.metadata = metadata or {}

    @classmethod
    def load(cls, paradigm_name: str) -> 'Paradigm':
        """
        Loads a paradigm by its name from the corresponding JSON file in this directory.

        Args:
            paradigm_name (str): The name of the paradigm (e.g., 'json_output').

        Returns:
            Paradigm: An instance containing the reconstructed env and sequence specs.
        """
        paradigm_file = PARADIGMS_DIR / f"{paradigm_name}.json"
        if not paradigm_file.exists():
            raise FileNotFoundError(f"Paradigm '{paradigm_name}' not found at {paradigm_file}")

        with open(paradigm_file, 'r', encoding='utf-8') as f:
            raw_spec = json.load(f, object_hook=_paradigm_object_hook)

        env_spec_data = raw_spec['env_spec']
        sequence_spec_data = raw_spec['sequence_spec']
        metadata_data = raw_spec.get('metadata', {})

        # Reconstruct the spec objects from the loaded data
        env_spec = _build_env_spec(env_spec_data)
        sequence_spec = _build_sequence_spec(sequence_spec_data, env_spec)
        
        return cls(env_spec, sequence_spec, metadata_data)

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
            from infra._agent._models._paradigms import Paradigm, PARADIGMS_DIR
            import json
            import os

            # Create a wrapper that provides a load method
            class _DefaultParadigmTool:
                def load(self, paradigm_name: str):
                    return Paradigm.load(paradigm_name)
                
                def list_manifest(self) -> str:
                    """
                    Scans the paradigms directory and returns a formatted string 
                    describing all available paradigms and their inputs.
                    """
                    manifest = []
                    # List all .json files in PARADIGMS_DIR
                    for filename in os.listdir(PARADIGMS_DIR):
                        if filename.endswith(".json"):
                            name = filename[:-5] # Remove .json
                            try:
                                with open(PARADIGMS_DIR / filename, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                    metadata = data.get('metadata', {})
                                    
                                    desc = metadata.get('description', 'No description provided.')
                                    v_inputs = metadata.get('inputs', {}).get('vertical', {})
                                    h_inputs = metadata.get('inputs', {}).get('horizontal', {})
                                    
                                    entry = f"- **{name}**\n  - *Description*: {desc}"
                                    if v_inputs:
                                        entry += "\n  - *Vertical Inputs (Function)*: " + ", ".join([f"`{k}`" for k in v_inputs.keys()])
                                    if h_inputs:
                                        entry += "\n  - *Horizontal Inputs (Values)*: " + ", ".join([f"`{k}`" for k in h_inputs.keys()])
                                    
                                    manifest.append(entry)
                            except Exception as e:
                                manifest.append(f"- **{name}**: Error reading metadata ({str(e)})")
                    
                    return "\n".join(manifest)

            self.paradigm_tool = _DefaultParadigmTool()
        else:
            self.paradigm_tool = paradigm_tool

        # Pass the body's tool instances to the llm to ensure they share the same context (e.g., base_dir)
        if hasattr(self.llm, "file_tool"):
            self.llm.file_tool = self.file_system
        if hasattr(self.llm, "python_interpreter"):
            self.llm.python_interpreter = self.python_interpreter
```

```json
{
  "metadata": {
    "description": "Takes a prompt template and a save path, generates a JSON response from an LLM, extracts the 'answer' from it, saves that answer to the specified path, and returns the file location.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "prompt_template": "The template string for the LLM prompt.",
        "save_path": "The file path where the extracted answer should be saved."
      }
    },
    "outputs": {
      "type": "FileLocation",
      "description": "The path to the saved file, wrapped in %{file_location}."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "llm",
        "affordances": [
          {
            "affordance_name": "generate",
            "call_code": "result = tool.generate"
          }
        ]
      },
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "create_substitute_function",
            "call_code": "result = tool.create_substitute_function(template_key=params['template_key'])"
          },
          {
            "affordance_name": "parse",
            "call_code": "result = tool.parse"
          },
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          },
          {
            "affordance_name": "clean_code",
            "call_code": "result = tool.clean_code"
          }
        ]
      },
      {
        "tool_name": "file_system",
        "affordances": [
          {
            "affordance_name": "save",
            "call_code": "result = tool.save"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.create_substitute_function",
        "params": {
          "template_key": "prompt_template"
        },
        "result_key": "template_fn"
      },
      {
        "step_index": 2,
        "affordance": "llm.generate",
        "params": {},
        "result_key": "generate_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.parse",
        "params": {},
        "result_key": "parse_fn"
      },
      {
        "step_index": 4,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "mia_fn"
      },
      {
        "step_index": 5,
        "affordance": "file_system.save",
        "params": {},
        "result_key": "save_fn"
      },
      {
        "step_index": 6,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 7,
        "affordance": "formatter_tool.clean_code",
        "params": {},
        "result_key": "clean_code_fn"
      },
      {
        "step_index": 8,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "prompt_string",
              "function": {
                "__type__": "MetaValue",
                "key": "template_fn"
              },
              "params": {
                "__positional__": "__initial_input__"
              }
            },
            {
              "output_key": "raw_llm_response",
              "function": {
                "__type__": "MetaValue",
                "key": "generate_fn"
              },
              "params": {
                "__positional__": "prompt_string"
              }
            },
            {
              "output_key": "cleaned_response",
              "function": {
                "__type__": "MetaValue",
                "key": "clean_code_fn"
              },
              "params": {
                "__positional__": "raw_llm_response"
              }
            },
            {
              "output_key": "parsed_dict",
              "function": {
                "__type__": "MetaValue",
                "key": "parse_fn"
              },
              "params": {
                "__positional__": "cleaned_response"
              }
            },
            {
              "output_key": "final_answer",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "parsed_dict"
              },
              "literal_params": {
                "key": "answer"
              }
            },
            {
              "output_key": "save_path_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "save_path"
              }
            },
            {
              "output_key": "save_confirmation",
              "function": {
                "__type__": "MetaValue",
                "key": "save_fn"
              },
              "params": {
                "content": "final_answer",
                "location": "save_path_from_vars"
              }
            },
            {
              "output_key": "saved_location",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "save_confirmation"
              },
              "literal_params": {
                "key": "location"
              }
            },
            {
              "output_key": "mia_result",
              "function": {
                "__type__": "MetaValue",
                "key": "mia_fn"
              },
              "params": {
                "__positional__": "saved_location"
              },
              "literal_params": {
                "type": "file_location"
              }
            }
          ],
          "return_key": "mia_result"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}

```

```json
{
  "metadata": {
    "description": "Similar to the standard prompt-and-save, but bundles all unused inputs into an '$input_other' variable for the prompt. Saves the result to a directory.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "prompt_template": "The template string for the LLM prompt (must include $input_other).",
        "save_dir": "The directory where the result file should be saved.",
        "input_other": "Any other inputs provided will be bundled here."
      }
    },
    "outputs": {
      "type": "FileLocation",
      "description": "The path to the saved file, wrapped in %{file_location}."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "llm",
        "affordances": [
          {
            "affordance_name": "generate",
            "call_code": "result = tool.generate"
          }
        ]
      },
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "create_substitute_function",
            "call_code": "result = tool.create_substitute_function(template_key=params['template_key'])"
          },
          {
            "affordance_name": "create_smart_substitute_function",
            "call_code": "result = tool.create_smart_substitute_function(template_key=params['template_key'], combine_to_key=params['combine_to_key'])"
          },
          {
            "affordance_name": "parse",
            "call_code": "result = tool.parse"
          },
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          },
          {
            "affordance_name": "clean_code",
            "call_code": "result = tool.clean_code"
          }
        ]
      },
      {
        "tool_name": "file_system",
        "affordances": [
          {
            "affordance_name": "save",
            "call_code": "result = tool.save"
          },
          {
            "affordance_name": "save_from_dict",
            "call_code": "result = tool.save_from_dict"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.create_smart_substitute_function",
        "params": {
          "template_key": "prompt_template",
          "combine_to_key": "input_other"
        },
        "result_key": "template_fn"
      },
      {
        "step_index": 2,
        "affordance": "llm.generate",
        "params": {},
        "result_key": "generate_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.parse",
        "params": {},
        "result_key": "parse_fn"
      },
      {
        "step_index": 4,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "mia_fn"
      },
      {
        "step_index": 5,
        "affordance": "file_system.save",
        "params": {},
        "result_key": "save_fn"
      },
      {
        "step_index": 6,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 7,
        "affordance": "formatter_tool.clean_code",
        "params": {},
        "result_key": "clean_code_fn"
      },
      {
        "step_index": 8,
        "affordance": "file_system.save_from_dict",
        "params": {},
        "result_key": "save_dict_fn"
      },
      {
        "step_index": 9,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "prompt_string",
              "function": {
                "__type__": "MetaValue",
                "key": "template_fn"
              },
              "params": {
                "__positional__": "__initial_input__"
              }
            },
            {
              "output_key": "raw_llm_response",
              "function": {
                "__type__": "MetaValue",
                "key": "generate_fn"
              },
              "params": {
                "__positional__": "prompt_string"
              }
            },
            {
              "output_key": "cleaned_response",
              "function": {
                "__type__": "MetaValue",
                "key": "clean_code_fn"
              },
              "params": {
                "__positional__": "raw_llm_response"
              }
            },
            {
              "output_key": "parsed_dict",
              "function": {
                "__type__": "MetaValue",
                "key": "parse_fn"
              },
              "params": {
                "__positional__": "cleaned_response"
              }
            },
            {
              "output_key": "final_answer",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "parsed_dict"
              },
              "literal_params": {
                "key": "answer"
              }
            },
            {
              "output_key": "save_dir_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "save_dir"
              }
            },
            {
              "output_key": "save_confirmation",
              "function": {
                "__type__": "MetaValue",
                "key": "save_dict_fn"
              },
              "params": {
                "content_dict": "final_answer",
                "directory": "save_dir_from_vars"
              }
            },
            {
              "output_key": "saved_location",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "save_confirmation"
              },
              "literal_params": {
                "key": "saved_location"
              }
            },
            {
              "output_key": "mia_result",
              "function": {
                "__type__": "MetaValue",
                "key": "mia_fn"
              },
              "params": {
                "__positional__": "saved_location"
              },
              "literal_params": {
                "type": "file_location"
              }
            }
          ],
          "return_key": "mia_result"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}

```

```json
{
  "metadata": {
    "description": "Executes a Python script. If the script does not exist, generates it using the provided prompt template. Inputs for the script are collected from the horizontal inputs.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "prompt_template": "The template string to generate the script if it is missing.",
        "script_location": "The path to the python script to execute/generate.",
        "script_inputs": "Any other inputs provided will be passed to the script as variables."
      }
    },
    "outputs": {
      "type": "Normal",
      "description": "The return value of the executed script."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "llm",
        "affordances": [
          {
            "affordance_name": "generate",
            "call_code": "result = tool.generate"
          }
        ]
      },
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "create_substitute_function",
            "call_code": "result = tool.create_substitute_function(template_key=params['template_key'])"
          },
          {
            "affordance_name": "clean_code",
            "call_code": "result = tool.clean_code"
          },
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "identity",
            "call_code": "result = lambda x: x"
          },
          {
            "affordance_name": "collect_script_inputs",
            "call_code": "result = tool.collect_script_inputs"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          },
          {
            "affordance_name": "parse_json",
            "call_code": "import json\nresult = json.loads"
          }
        ]
      },
      {
        "tool_name": "file_system",
        "affordances": [
          {
            "affordance_name": "save",
            "call_code": "result = tool.save"
          },
          {
            "affordance_name": "read",
            "call_code": "result = tool.read"
          },
          {
            "affordance_name": "exists",
            "call_code": "result = tool.exists"
          }
        ]
      },
      {
        "tool_name": "python_interpreter",
        "affordances": [
          {
            "affordance_name": "function_execute",
            "call_code": "result = tool.function_execute"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.create_substitute_function",
        "params": {
          "template_key": "prompt_template"
        },
        "result_key": "template_fn"
      },
      {
        "step_index": 2,
        "affordance": "llm.generate",
        "params": {},
        "result_key": "generate_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.clean_code",
        "params": {},
        "result_key": "clean_code_fn"
      },
      {
        "step_index": 4,
        "affordance": "file_system.save",
        "params": {},
        "result_key": "save_fn"
      },
      {
        "step_index": 5,
        "affordance": "python_interpreter.function_execute",
        "params": {},
        "result_key": "function_execute_fn"
      },
      {
        "step_index": 6,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 7,
        "affordance": "file_system.read",
        "params": {},
        "result_key": "read_fn"
      },
      {
        "step_index": 8,
        "affordance": "file_system.exists",
        "params": {},
        "result_key": "exists_fn"
      },
      {
        "step_index": 9,
        "affordance": "formatter_tool.identity",
        "params": {},
        "result_key": "identity_fn"
      },
      {
        "step_index": 10,
        "affordance": "formatter_tool.collect_script_inputs",
        "params": {},
        "result_key": "collect_inputs_fn"
      },
      {
        "step_index": 11,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "wrap_fn"
      },
      {
        "step_index": 12,
        "affordance": "formatter_tool.parse_json",
        "params": {},
        "result_key": "parse_json_fn"
      },
      {
        "step_index": 13,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "script_location",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "script_location"
              }
            },
            {
              "output_key": "script_inputs",
              "function": {
                "__type__": "MetaValue",
                "key": "collect_inputs_fn"
              },
              "params": {
                "all_inputs": "__initial_input__"
              }
            },
            {
              "output_key": "script_exists",
              "function": {
                "__type__": "MetaValue",
                "key": "exists_fn"
              },
              "params": {
                "__positional__": "script_location"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_true"
              },
              "output_key": "read_result",
              "function": {
                "__type__": "MetaValue",
                "key": "read_fn"
              },
              "params": {
                "__positional__": "script_location"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_true"
              },
              "output_key": "code_to_run",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "read_result"
              },
              "literal_params": {
                "key": "content"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "prompt_string",
              "function": {
                "__type__": "MetaValue",
                "key": "template_fn"
              },
              "params": {
                "__positional__": "__initial_input__"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "raw_llm_response",
              "function": {
                "__type__": "MetaValue",
                "key": "generate_fn"
              },
              "params": {
                "__positional__": "prompt_string"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "clean_code",
              "function": {
                "__type__": "MetaValue",
                "key": "clean_code_fn"
              },
              "params": {
                "__positional__": "raw_llm_response"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "parsed_llm_json",
              "function": {
                "__type__": "MetaValue",
                "key": "parse_json_fn"
              },
              "params": {
                "__positional__": "clean_code"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "code_to_run",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "parsed_llm_json"
              },
              "literal_params": {
                "key": "answer"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "save_confirmation",
              "function": {
                "__type__": "MetaValue",
                "key": "save_fn"
              },
              "params": {
                "content": "code_to_run",
                "location": "script_location"
              }
            },
            {
              "output_key": "execution_result",
              "function": {
                "__type__": "MetaValue",
                "key": "function_execute_fn"
              },
              "params": {
                "script_code": "code_to_run",
                "function_params": "script_inputs"
              },
              "literal_params": {
                "function_name": "main"
              }
            },
            {
              "output_key": "final_wrapped_result",
              "function": {
                "__type__": "MetaValue",
                "key": "wrap_fn"
              },
              "params": {
                "__positional__": "execution_result"
              }
            }
          ],
          "return_key": "final_wrapped_result"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}

```

```json
{
  "metadata": {
    "description": "Executes a Python script. If the script is missing, generates it using a prompt provided by the function definition (Vertical Input).",
    "inputs": {
      "vertical": {
        "template": "The prompt template string (sourced from function_concept.name)."
      },
      "horizontal": {
        "script_location": "Path to the python script to execute/generate.",
        "script_inputs": "Any other inputs provided will be passed to the script as variables."
      }
    },
    "outputs": {
      "type": "Normal",
      "description": "The return value of the executed script."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "llm",
        "affordances": [
          {
            "affordance_name": "generate",
            "call_code": "result = tool.generate"
          }
        ]
      },
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "create_template_function",
            "call_code": "result = tool.create_template_function(template=params['template'])"
          },
          {
            "affordance_name": "clean_code",
            "call_code": "result = tool.clean_code"
          },
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "identity",
            "call_code": "result = lambda x: x"
          },
          {
            "affordance_name": "collect_script_inputs",
            "call_code": "result = tool.collect_script_inputs"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          },
          {
            "affordance_name": "parse_json",
            "call_code": "import json\nresult = json.loads"
          }
        ]
      },
      {
        "tool_name": "file_system",
        "affordances": [
          {
            "affordance_name": "save",
            "call_code": "result = tool.save"
          },
          {
            "affordance_name": "read",
            "call_code": "result = tool.read"
          },
          {
            "affordance_name": "exists",
            "call_code": "result = tool.exists"
          }
        ]
      },
      {
        "tool_name": "python_interpreter",
        "affordances": [
          {
            "affordance_name": "function_execute",
            "call_code": "result = tool.function_execute"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.create_template_function",
        "params": {
          "template": {
            "__type__": "MetaValue",
            "key": "states.function.concept.name"
          }
        },
        "result_key": "template_fn"
      },
      {
        "step_index": 2,
        "affordance": "llm.generate",
        "params": {},
        "result_key": "generate_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.clean_code",
        "params": {},
        "result_key": "clean_code_fn"
      },
      {
        "step_index": 4,
        "affordance": "file_system.save",
        "params": {},
        "result_key": "save_fn"
      },
      {
        "step_index": 5,
        "affordance": "python_interpreter.function_execute",
        "params": {},
        "result_key": "function_execute_fn"
      },
      {
        "step_index": 6,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 7,
        "affordance": "file_system.read",
        "params": {},
        "result_key": "read_fn"
      },
      {
        "step_index": 8,
        "affordance": "file_system.exists",
        "params": {},
        "result_key": "exists_fn"
      },
      {
        "step_index": 9,
        "affordance": "formatter_tool.identity",
        "params": {},
        "result_key": "identity_fn"
      },
      {
        "step_index": 10,
        "affordance": "formatter_tool.collect_script_inputs",
        "params": {},
        "result_key": "collect_inputs_fn"
      },
      {
        "step_index": 11,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "wrap_fn"
      },
      {
        "step_index": 12,
        "affordance": "formatter_tool.parse_json",
        "params": {},
        "result_key": "parse_json_fn"
      },
      {
        "step_index": 13,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "script_location",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "script_location"
              }
            },
            {
              "output_key": "script_inputs",
              "function": {
                "__type__": "MetaValue",
                "key": "collect_inputs_fn"
              },
              "params": {
                "all_inputs": "__initial_input__"
              }
            },
            {
              "output_key": "script_exists",
              "function": {
                "__type__": "MetaValue",
                "key": "exists_fn"
              },
              "params": {
                "__positional__": "script_location"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_true"
              },
              "output_key": "read_result",
              "function": {
                "__type__": "MetaValue",
                "key": "read_fn"
              },
              "params": {
                "__positional__": "script_location"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_true"
              },
              "output_key": "code_to_run",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "read_result"
              },
              "literal_params": {
                "key": "content"
              }
            },
            {
              "output_key": "prompt_string",
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "function": {
                "__type__": "MetaValue",
                "key": "template_fn"
              },
              "params": {
                "__positional__": "script_inputs"
              }
            },
            {
              "output_key": "raw_llm_response",
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "function": {
                "__type__": "MetaValue",
                "key": "generate_fn"
              },
              "params": {
                "__positional__": "prompt_string"
              }
            },
            {
              "output_key": "clean_code",
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "function": {
                "__type__": "MetaValue",
                "key": "clean_code_fn"
              },
              "params": {
                "__positional__": "raw_llm_response"
              }
            },
            {
              "output_key": "parsed_llm_json",
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "function": {
                "__type__": "MetaValue",
                "key": "parse_json_fn"
              },
              "params": {
                "__positional__": "clean_code"
              }
            },
            {
              "output_key": "code_to_run",
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "parsed_llm_json"
              },
              "literal_params": {
                "key": "answer"
              }
            },
            {
              "output_key": "save_confirmation",
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "function": {
                "__type__": "MetaValue",
                "key": "save_fn"
              },
              "params": {
                "content": "code_to_run",
                "location": "script_location"
              }
            },
            {
              "output_key": "execution_result",
              "function": {
                "__type__": "MetaValue",
                "key": "function_execute_fn"
              },
              "params": {
                "script_code": "code_to_run",
                "function_params": "script_inputs"
              },
              "literal_params": {
                "function_name": "main"
              }
            },
            {
              "output_key": "final_wrapped_result",
              "function": {
                "__type__": "MetaValue",
                "key": "wrap_fn"
              },
              "params": {
                "__positional__": "execution_result"
              }
            }
          ],
          "return_key": "final_wrapped_result"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}

```

```json
{
  "metadata": {
    "description": "Opens a text editor GUI with initial text. The user modifies it, and the result is saved to a specific path.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "input_1": "The instruction/prompt to display to the user.",
        "input_2": "The initial text to populate the editor with.",
        "save_path": "The path where the modified text will be saved."
      }
    },
    "outputs": {
      "type": "FileLocation",
      "description": "The path to the saved file."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          }
        ]
      },
      {
        "tool_name": "user_input",
        "affordances": [
          {
            "affordance_name": "create_text_editor_function",
            "call_code": "result = tool.create_text_editor_function()"
          }
        ]
      },
      {
        "tool_name": "file_system",
        "affordances": [
          {
            "affordance_name": "save",
            "call_code": "result = tool.save"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 2,
        "affordance": "user_input.create_text_editor_function",
        "params": {},
        "result_key": "text_editor_fn"
      },
      {
        "step_index": 3,
        "affordance": "file_system.save",
        "params": {},
        "result_key": "save_fn"
      },
      {
        "step_index": 4,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "wrap_fn"
      },
      {
        "step_index": 5,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "prompt_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "input_1"
              }
            },
            {
              "output_key": "initial_text_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "input_2"
              }
            },
            {
              "output_key": "save_path_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "save_path"
              }
            },
            {
              "output_key": "modified_text",
              "function": {
                "__type__": "MetaValue",
                "key": "text_editor_fn"
              },
              "params": {
                "prompt_text": "prompt_from_vars",
                "initial_text": "initial_text_from_vars"
              }
            },
            {
              "output_key": "save_result",
              "function": {
                "__type__": "MetaValue",
                "key": "save_fn"
              },
              "params": {
                "content": "modified_text",
                "location": "save_path_from_vars"
              }
            },
            {
              "output_key": "wrapped_file_location",
              "function": {
                "__type__": "MetaValue",
                "key": "wrap_fn"
              },
              "params": {
                "data": "save_path_from_vars"
              },
              "literal_params": {
                "type": "file_location"
              }
            }
          ],
          "return_key": "wrapped_file_location"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}


```

```json
{
  "metadata": {
    "description": "Opens a text editor GUI with initial text. The user modifies it, and the result is returned as a string.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "input_1": "The instruction/prompt to display to the user.",
        "input_2": "The initial text to populate the editor with."
      }
    },
    "outputs": {
      "type": "Normal",
      "description": "The modified text string."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          }
        ]
      },
      {
        "tool_name": "user_input",
        "affordances": [
          {
            "affordance_name": "create_text_editor_function",
            "call_code": "result = tool.create_text_editor_function()"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 2,
        "affordance": "user_input.create_text_editor_function",
        "params": {},
        "result_key": "text_editor_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "wrap_fn"
      },
      {
        "step_index": 4,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "prompt_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "input_1"
              }
            },
            {
              "output_key": "initial_text_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "input_2"
              }
            },
            {
              "output_key": "modified_text",
              "function": {
                "__type__": "MetaValue",
                "key": "text_editor_fn"
              },
              "params": {
                "prompt_text": "prompt_from_vars",
                "initial_text": "initial_text_from_vars"
              }
            },
            {
              "output_key": "wrapped_result",
              "function": {
                "__type__": "MetaValue",
                "key": "wrap_fn"
              },
              "params": {
                "data": "modified_text"
              },
              "literal_params": {
                "type": "normal"
              }
            }
          ],
          "return_key": "wrapped_result"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}


```

```json
{
  "metadata": {
    "description": "Generates a JSON response (thinking/answer), extracts the answer (which must be a dictionary), and saves it to a directory.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "prompt_template": "The template string for the LLM prompt.",
        "save_dir": "The directory where the dictionary result should be saved."
      }
    },
    "outputs": {
      "type": "FileLocation",
      "description": "The location where the file was saved."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "llm",
        "affordances": [
          {
            "affordance_name": "generate",
            "call_code": "result = tool.generate"
          }
        ]
      },
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "create_substitute_function",
            "call_code": "result = tool.create_substitute_function(template_key=params['template_key'])"
          },
          {
            "affordance_name": "parse",
            "call_code": "result = tool.parse"
          },
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          },
          {
            "affordance_name": "clean_code",
            "call_code": "result = tool.clean_code"
          }
        ]
      },
      {
        "tool_name": "file_system",
        "affordances": [
          {
            "affordance_name": "save",
            "call_code": "result = tool.save"
          },
          {
            "affordance_name": "save_from_dict",
            "call_code": "result = tool.save_from_dict"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.create_substitute_function",
        "params": {
          "template_key": "prompt_template"
        },
        "result_key": "template_fn"
      },
      {
        "step_index": 2,
        "affordance": "llm.generate",
        "params": {},
        "result_key": "generate_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.parse",
        "params": {},
        "result_key": "parse_fn"
      },
      {
        "step_index": 4,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "mia_fn"
      },
      {
        "step_index": 5,
        "affordance": "file_system.save",
        "params": {},
        "result_key": "save_fn"
      },
      {
        "step_index": 6,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 7,
        "affordance": "formatter_tool.clean_code",
        "params": {},
        "result_key": "clean_code_fn"
      },
      {
        "step_index": 8,
        "affordance": "file_system.save_from_dict",
        "params": {},
        "result_key": "save_dict_fn"
      },
      {
        "step_index": 9,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "prompt_string",
              "function": {
                "__type__": "MetaValue",
                "key": "template_fn"
              },
              "params": {
                "__positional__": "__initial_input__"
              }
            },
            {
              "output_key": "raw_llm_response",
              "function": {
                "__type__": "MetaValue",
                "key": "generate_fn"
              },
              "params": {
                "__positional__": "prompt_string"
              }
            },
            {
              "output_key": "cleaned_response",
              "function": {
                "__type__": "MetaValue",
                "key": "clean_code_fn"
              },
              "params": {
                "__positional__": "raw_llm_response"
              }
            },
            {
              "output_key": "parsed_dict",
              "function": {
                "__type__": "MetaValue",
                "key": "parse_fn"
              },
              "params": {
                "__positional__": "cleaned_response"
              }
            },
            {
              "output_key": "final_answer",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "parsed_dict"
              },
              "literal_params": {
                "key": "answer"
              }
            },
            {
              "output_key": "save_dir_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "save_dir"
              }
            },
            {
              "output_key": "save_confirmation",
              "function": {
                "__type__": "MetaValue",
                "key": "save_dict_fn"
              },
              "params": {
                "content_dict": "final_answer",
                "directory": "save_dir_from_vars"
              }
            },
            {
              "output_key": "saved_location",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "save_confirmation"
              },
              "literal_params": {
                "key": "saved_location"
              }
            },
            {
              "output_key": "mia_result",
              "function": {
                "__type__": "MetaValue",
                "key": "mia_fn"
              },
              "params": {
                "__positional__": "saved_location"
              },
              "literal_params": {
                "type": "file_location"
              }
            }
          ],
          "return_key": "mia_result"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}

```

```json
{
  "metadata": {
    "description": "Executes a Python script (generating it if missing). The script is injected with the agent's Body, allowing it to call other tools. Expects a list of file locations as output.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "prompt_template": "The template string to generate the script if it is missing.",
        "script_location": "The path to the python script to execute/generate.",
        "script_inputs": "Inputs passed to the script."
      }
    },
    "outputs": {
      "type": "FileLocationList",
      "description": "A list of file paths returned by the script."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "llm",
        "affordances": [
          {
            "affordance_name": "generate",
            "call_code": "result = tool.generate"
          }
        ]
      },
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "create_substitute_function",
            "call_code": "result = tool.create_substitute_function(template_key=params['template_key'])"
          },
          {
            "affordance_name": "clean_code",
            "call_code": "result = tool.clean_code"
          },
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "identity",
            "call_code": "result = lambda x: x"
          },
          {
            "affordance_name": "collect_script_inputs",
            "call_code": "result = tool.collect_script_inputs"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          },
          {
            "affordance_name": "wrap_list",
            "call_code": "result = tool.wrap_list"
          },
          {
            "affordance_name": "parse_json",
            "call_code": "import json\nresult = json.loads"
          }
        ]
      },
      {
        "tool_name": "file_system",
        "affordances": [
          {
            "affordance_name": "save",
            "call_code": "result = tool.save"
          },
          {
            "affordance_name": "read",
            "call_code": "result = tool.read"
          },
          {
            "affordance_name": "exists",
            "call_code": "result = tool.exists"
          }
        ]
      },
      {
        "tool_name": "python_interpreter",
        "affordances": [
          {
            "affordance_name": "function_execute",
            "call_code": "result = tool.function_execute"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.create_substitute_function",
        "params": {
          "template_key": "prompt_template"
        },
        "result_key": "template_fn"
      },
      {
        "step_index": 2,
        "affordance": "llm.generate",
        "params": {},
        "result_key": "generate_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.clean_code",
        "params": {},
        "result_key": "clean_code_fn"
      },
      {
        "step_index": 4,
        "affordance": "file_system.save",
        "params": {},
        "result_key": "save_fn"
      },
      {
        "step_index": 5,
        "affordance": "python_interpreter.function_execute",
        "params": {},
        "result_key": "function_execute_fn"
      },
      {
        "step_index": 6,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 7,
        "affordance": "file_system.read",
        "params": {},
        "result_key": "read_fn"
      },
      {
        "step_index": 8,
        "affordance": "file_system.exists",
        "params": {},
        "result_key": "exists_fn"
      },
      {
        "step_index": 9,
        "affordance": "formatter_tool.identity",
        "params": {},
        "result_key": "identity_fn"
      },
      {
        "step_index": 10,
        "affordance": "formatter_tool.collect_script_inputs",
        "params": {},
        "result_key": "collect_inputs_fn"
      },
      {
        "step_index": 11,
        "affordance": "formatter_tool.wrap_list",
        "params": {},
        "result_key": "wrap_list_fn"
      },
      {
        "step_index": 12,
        "affordance": "formatter_tool.parse_json",
        "params": {},
        "result_key": "parse_json_fn"
      },
      {
        "step_index": 13,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "script_location",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "script_location"
              }
            },
            {
              "output_key": "script_inputs",
              "function": {
                "__type__": "MetaValue",
                "key": "collect_inputs_fn"
              },
              "params": {
                "all_inputs": "__initial_input__"
              }
            },
            {
              "output_key": "script_exists",
              "function": {
                "__type__": "MetaValue",
                "key": "exists_fn"
              },
              "params": {
                "__positional__": "script_location"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_true"
              },
              "output_key": "read_result",
              "function": {
                "__type__": "MetaValue",
                "key": "read_fn"
              },
              "params": {
                "__positional__": "script_location"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_true"
              },
              "output_key": "code_to_run",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "read_result"
              },
              "literal_params": {
                "key": "content"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "prompt_string",
              "function": {
                "__type__": "MetaValue",
                "key": "template_fn"
              },
              "params": {
                "__positional__": "__initial_input__"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "raw_llm_response",
              "function": {
                "__type__": "MetaValue",
                "key": "generate_fn"
              },
              "params": {
                "__positional__": "prompt_string"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "clean_code",
              "function": {
                "__type__": "MetaValue",
                "key": "clean_code_fn"
              },
              "params": {
                "__positional__": "raw_llm_response"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "parsed_llm_json",
              "function": {
                "__type__": "MetaValue",
                "key": "parse_json_fn"
              },
              "params": {
                "__positional__": "clean_code"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "code_to_run",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "parsed_llm_json"
              },
              "literal_params": {
                "key": "answer"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "save_confirmation",
              "function": {
                "__type__": "MetaValue",
                "key": "save_fn"
              },
              "params": {
                "content": "code_to_run",
                "location": "script_location"
              }
            },
            {
              "output_key": "execution_result",
              "function": {
                "__type__": "MetaValue",
                "key": "function_execute_fn"
              },
              "params": {
                "script_code": "code_to_run",
                "function_params": "script_inputs"
              },
              "literal_params": {
                "function_name": "main"
              }
            },
            {
              "output_key": "final_wrapped_result",
              "function": {
                "__type__": "MetaValue",
                "key": "wrap_list_fn"
              },
              "params": {
                "__positional__": "execution_result"
              },
              "literal_params": {
                "type": "file_location"
              }
            }
          ],
          "return_key": "final_wrapped_result"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}


```

```json
{
  "metadata": {
    "description": "Executes a Python script (generating it if missing). The script is injected with the agent's Body, allowing it to call other tools. Returns the raw result.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "prompt_template": "The template string to generate the script if it is missing.",
        "script_location": "The path to the python script to execute/generate.",
        "script_inputs": "Inputs passed to the script."
      }
    },
    "outputs": {
      "type": "Normal",
      "description": "The raw return value of the script."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "llm",
        "affordances": [
          {
            "affordance_name": "generate",
            "call_code": "result = tool.generate"
          }
        ]
      },
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "create_substitute_function",
            "call_code": "result = tool.create_substitute_function(template_key=params['template_key'])"
          },
          {
            "affordance_name": "clean_code",
            "call_code": "result = tool.clean_code"
          },
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "identity",
            "call_code": "result = lambda x: x"
          },
          {
            "affordance_name": "collect_script_inputs",
            "call_code": "result = tool.collect_script_inputs"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          },
          {
            "affordance_name": "parse_json",
            "call_code": "import json\nresult = json.loads"
          }
        ]
      },
      {
        "tool_name": "file_system",
        "affordances": [
          {
            "affordance_name": "save",
            "call_code": "result = tool.save"
          },
          {
            "affordance_name": "read",
            "call_code": "result = tool.read"
          },
          {
            "affordance_name": "exists",
            "call_code": "result = tool.exists"
          }
        ]
      },
      {
        "tool_name": "python_interpreter",
        "affordances": [
          {
            "affordance_name": "function_execute",
            "call_code": "result = tool.function_execute"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.create_substitute_function",
        "params": {
          "template_key": "prompt_template"
        },
        "result_key": "template_fn"
      },
      {
        "step_index": 2,
        "affordance": "llm.generate",
        "params": {},
        "result_key": "generate_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.clean_code",
        "params": {},
        "result_key": "clean_code_fn"
      },
      {
        "step_index": 4,
        "affordance": "file_system.save",
        "params": {},
        "result_key": "save_fn"
      },
      {
        "step_index": 5,
        "affordance": "python_interpreter.function_execute",
        "params": {},
        "result_key": "function_execute_fn"
      },
      {
        "step_index": 6,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 7,
        "affordance": "file_system.read",
        "params": {},
        "result_key": "read_fn"
      },
      {
        "step_index": 8,
        "affordance": "file_system.exists",
        "params": {},
        "result_key": "exists_fn"
      },
      {
        "step_index": 9,
        "affordance": "formatter_tool.identity",
        "params": {},
        "result_key": "identity_fn"
      },
      {
        "step_index": 10,
        "affordance": "formatter_tool.collect_script_inputs",
        "params": {},
        "result_key": "collect_inputs_fn"
      },
      {
        "step_index": 11,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "wrap_fn"
      },
      {
        "step_index": 12,
        "affordance": "formatter_tool.parse_json",
        "params": {},
        "result_key": "parse_json_fn"
      },
      {
        "step_index": 13,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "script_location",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "script_location"
              }
            },
            {
              "output_key": "script_inputs",
              "function": {
                "__type__": "MetaValue",
                "key": "collect_inputs_fn"
              },
              "params": {
                "all_inputs": "__initial_input__"
              }
            },
            {
              "output_key": "script_exists",
              "function": {
                "__type__": "MetaValue",
                "key": "exists_fn"
              },
              "params": {
                "__positional__": "script_location"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_true"
              },
              "output_key": "read_result",
              "function": {
                "__type__": "MetaValue",
                "key": "read_fn"
              },
              "params": {
                "__positional__": "script_location"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_true"
              },
              "output_key": "code_to_run",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "read_result"
              },
              "literal_params": {
                "key": "content"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "prompt_string",
              "function": {
                "__type__": "MetaValue",
                "key": "template_fn"
              },
              "params": {
                "__positional__": "__initial_input__"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "raw_llm_response",
              "function": {
                "__type__": "MetaValue",
                "key": "generate_fn"
              },
              "params": {
                "__positional__": "prompt_string"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "clean_code",
              "function": {
                "__type__": "MetaValue",
                "key": "clean_code_fn"
              },
              "params": {
                "__positional__": "raw_llm_response"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "parsed_llm_json",
              "function": {
                "__type__": "MetaValue",
                "key": "parse_json_fn"
              },
              "params": {
                "__positional__": "clean_code"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "code_to_run",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "parsed_llm_json"
              },
              "literal_params": {
                "key": "answer"
              }
            },
            {
              "condition": {
                "key": "script_exists",
                "operator": "is_false"
              },
              "output_key": "save_confirmation",
              "function": {
                "__type__": "MetaValue",
                "key": "save_fn"
              },
              "params": {
                "content": "code_to_run",
                "location": "script_location"
              }
            },
            {
              "output_key": "execution_result",
              "function": {
                "__type__": "MetaValue",
                "key": "function_execute_fn"
              },
              "params": {
                "script_code": "code_to_run",
                "function_params": "script_inputs"
              },
              "literal_params": {
                "function_name": "main"
              }
            },
            {
              "output_key": "final_wrapped_result",
              "function": {
                "__type__": "MetaValue",
                "key": "wrap_fn"
              },
              "params": {
                "__positional__": "execution_result"
              }
            }
          ],
          "return_key": "final_wrapped_result"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}

```

```json
{
  "metadata": {
    "description": "Bundles unused inputs into '$input_other', prompts LLM for a JSON list of files, saves them to a directory, and returns the list of file paths.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "prompt_template": "The template string for the LLM prompt.",
        "save_dir": "The directory where results should be saved.",
        "input_other": "Bundled unused inputs."
      }
    },
    "outputs": {
      "type": "FileLocationList",
      "description": "A list of paths to the saved files."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "llm",
        "affordances": [
          {
            "affordance_name": "generate",
            "call_code": "result = tool.generate"
          }
        ]
      },
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "create_substitute_function",
            "call_code": "result = tool.create_substitute_function(template_key=params['template_key'])"
          },
          {
            "affordance_name": "create_smart_substitute_function",
            "call_code": "result = tool.create_smart_substitute_function(template_key=params['template_key'], combine_to_key=params['combine_to_key'])"
          },
          {
            "affordance_name": "parse",
            "call_code": "result = tool.parse"
          },
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          },
          {
            "affordance_name": "wrap_list",
            "call_code": "result = tool.wrap_list"
          },
          {
            "affordance_name": "clean_code",
            "call_code": "result = tool.clean_code"
          }
        ]
      },
      {
        "tool_name": "file_system",
        "affordances": [
          {
            "affordance_name": "save",
            "call_code": "result = tool.save"
          },
          {
            "affordance_name": "save_from_dict",
            "call_code": "result = tool.save_from_dict"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.create_smart_substitute_function",
        "params": {
          "template_key": "prompt_template",
          "combine_to_key": "input_other"
        },
        "result_key": "template_fn"
      },
      {
        "step_index": 2,
        "affordance": "llm.generate",
        "params": {},
        "result_key": "generate_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.parse",
        "params": {},
        "result_key": "parse_fn"
      },
      {
        "step_index": 4,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "mia_fn"
      },
      {
        "step_index": 5,
        "affordance": "file_system.save",
        "params": {},
        "result_key": "save_fn"
      },
      {
        "step_index": 6,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 7,
        "affordance": "formatter_tool.clean_code",
        "params": {},
        "result_key": "clean_code_fn"
      },
      {
        "step_index": 8,
        "affordance": "file_system.save_from_dict",
        "params": {},
        "result_key": "save_dict_fn"
      },
      {
        "step_index": 9,
        "affordance": "formatter_tool.wrap_list",
        "params": {},
        "result_key": "wrap_list_fn"
      },
      {
        "step_index": 10,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "prompt_string",
              "function": {
                "__type__": "MetaValue",
                "key": "template_fn"
              },
              "params": {
                "__positional__": "__initial_input__"
              }
            },
            {
              "output_key": "raw_llm_response",
              "function": {
                "__type__": "MetaValue",
                "key": "generate_fn"
              },
              "params": {
                "__positional__": "prompt_string"
              }
            },
            {
              "output_key": "cleaned_response",
              "function": {
                "__type__": "MetaValue",
                "key": "clean_code_fn"
              },
              "params": {
                "__positional__": "raw_llm_response"
              }
            },
            {
              "output_key": "parsed_dict",
              "function": {
                "__type__": "MetaValue",
                "key": "parse_fn"
              },
              "params": {
                "__positional__": "cleaned_response"
              }
            },
            {
              "output_key": "final_answer",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "parsed_dict"
              },
              "literal_params": {
                "key": "answer"
              }
            },
            {
              "output_key": "save_dir_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "save_dir"
              }
            },
            {
              "output_key": "save_confirmation",
              "function": {
                "__type__": "MetaValue",
                "key": "save_dict_fn"
              },
              "params": {
                "content_dict": "final_answer",
                "directory": "save_dir_from_vars"
              }
            },
            {
              "output_key": "all_saved_locations",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "save_confirmation"
              },
              "literal_params": {
                "key": "saved_locations"
              }
            },
            {
              "output_key": "mia_result",
              "function": {
                "__type__": "MetaValue",
                "key": "wrap_list_fn"
              },
              "params": {
                "__positional__": "all_saved_locations"
              },
              "literal_params": {
                "type": "file_location"
              }
            }
          ],
          "return_key": "mia_result"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}


```

```json
{
  "metadata": {
    "description": "Bundles unused inputs into '$input_other', prompts LLM for a JSON list of files, saves them to a directory, and returns the list of file paths. (Variant)",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "prompt_template": "The template string for the LLM prompt.",
        "save_dir": "The directory where results should be saved.",
        "input_other": "Bundled unused inputs."
      }
    },
    "outputs": {
      "type": "FileLocationList",
      "description": "A list of paths to the saved files."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "llm",
        "affordances": [
          {
            "affordance_name": "generate",
            "call_code": "result = tool.generate"
          }
        ]
      },
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "create_substitute_function",
            "call_code": "result = tool.create_substitute_function(template_key=params['template_key'])"
          },
          {
            "affordance_name": "create_smart_substitute_function",
            "call_code": "result = tool.create_smart_substitute_function(template_key=params['template_key'], combine_to_key=params['combine_to_key'])"
          },
          {
            "affordance_name": "parse",
            "call_code": "result = tool.parse"
          },
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          },
          {
            "affordance_name": "wrap_list",
            "call_code": "result = tool.wrap_list"
          },
          {
            "affordance_name": "clean_code",
            "call_code": "result = tool.clean_code"
          }
        ]
      },
      {
        "tool_name": "file_system",
        "affordances": [
          {
            "affordance_name": "save",
            "call_code": "result = tool.save"
          },
          {
            "affordance_name": "save_from_dict",
            "call_code": "result = tool.save_from_dict"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.create_smart_substitute_function",
        "params": {
          "template_key": "prompt_template",
          "combine_to_key": "input_other"
        },
        "result_key": "template_fn"
      },
      {
        "step_index": 2,
        "affordance": "llm.generate",
        "params": {},
        "result_key": "generate_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.parse",
        "params": {},
        "result_key": "parse_fn"
      },
      {
        "step_index": 4,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "mia_fn"
      },
      {
        "step_index": 5,
        "affordance": "file_system.save",
        "params": {},
        "result_key": "save_fn"
      },
      {
        "step_index": 6,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 7,
        "affordance": "formatter_tool.clean_code",
        "params": {},
        "result_key": "clean_code_fn"
      },
      {
        "step_index": 8,
        "affordance": "file_system.save_from_dict",
        "params": {},
        "result_key": "save_dict_fn"
      },
      {
        "step_index": 9,
        "affordance": "formatter_tool.wrap_list",
        "params": {},
        "result_key": "wrap_list_fn"
      },
      {
        "step_index": 10,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "prompt_string",
              "function": {
                "__type__": "MetaValue",
                "key": "template_fn"
              },
              "params": {
                "__positional__": "__initial_input__"
              }
            },
            {
              "output_key": "raw_llm_response",
              "function": {
                "__type__": "MetaValue",
                "key": "generate_fn"
              },
              "params": {
                "__positional__": "prompt_string"
              }
            },
            {
              "output_key": "cleaned_response",
              "function": {
                "__type__": "MetaValue",
                "key": "clean_code_fn"
              },
              "params": {
                "__positional__": "raw_llm_response"
              }
            },
            {
              "output_key": "parsed_dict",
              "function": {
                "__type__": "MetaValue",
                "key": "parse_fn"
              },
              "params": {
                "__positional__": "cleaned_response"
              }
            },
            {
              "output_key": "final_answer",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "parsed_dict"
              },
              "literal_params": {
                "key": "answer"
              }
            },
            {
              "output_key": "save_dir_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "save_dir"
              }
            },
            {
              "output_key": "save_confirmation",
              "function": {
                "__type__": "MetaValue",
                "key": "save_dict_fn"
              },
              "params": {
                "content_dict": "final_answer",
                "directory": "save_dir_from_vars"
              }
            },
            {
              "output_key": "all_saved_locations",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "save_confirmation"
              },
              "literal_params": {
                "key": "saved_locations"
              }
            },
            {
              "output_key": "mia_result",
              "function": {
                "__type__": "MetaValue",
                "key": "wrap_list_fn"
              },
              "params": {
                "__positional__": "all_saved_locations"
              },
              "literal_params": {
                "type": "file_location"
              }
            }
          ],
          "return_key": "mia_result"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}


```

```json
{
  "metadata": {
    "description": "Prompts the user for input and returns the raw string response.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "input_1": "The question/prompt to display to the user."
      }
    },
    "outputs": {
      "type": "Normal",
      "description": "The user's response string."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          }
        ]
      },
      {
        "tool_name": "user_input",
        "affordances": [
          {
            "affordance_name": "create_input_function",
            "call_code": "result = tool.create_input_function()"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 2,
        "affordance": "user_input.create_input_function",
        "params": {},
        "result_key": "user_input_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "wrap_fn"
      },
      {
        "step_index": 4,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "prompt_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "input_1"
              }
            },
            {
              "output_key": "user_response",
              "function": {
                "__type__": "MetaValue",
                "key": "user_input_fn"
              },
              "params": {
                "prompt_text": "prompt_from_vars"
              }
            },
            {
              "output_key": "wrapped_response",
              "function": {
                "__type__": "MetaValue",
                "key": "wrap_fn"
              },
              "params": {
                "__positional__": "user_response"
              }
            }
          ],
          "return_key": "wrapped_response"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}

```

```json
{
  "metadata": {
    "description": "Asks the user a Yes/No question and returns a boolean.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "input_1": "The question/prompt to display to the user."
      }
    },
    "outputs": {
      "type": "Boolean",
      "description": "True for Yes, False for No."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          }
        ]
      },
      {
        "tool_name": "user_input",
        "affordances": [
          {
            "affordance_name": "create_interaction",
            "call_code": "result = tool.create_interaction(**params)"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 2,
        "affordance": "user_input.create_interaction",
        "params": {
          "interaction_type": "confirm",
          "default": true
        },
        "result_key": "user_confirm_fn"
      },
      {
        "step_index": 3,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "prompt_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "input_1"
              }
            },
            {
              "output_key": "user_confirmation",
              "function": {
                "__type__": "MetaValue",
                "key": "user_confirm_fn"
              },
              "params": {
                "prompt_text": "prompt_from_vars"
              }
            }
          ],
          "return_key": "user_confirmation"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}

```

```json
{
  "metadata": {
    "description": "Asks the user to provide a file path. Returns the path wrapped as a FileLocation.",
    "inputs": {
      "vertical": {},
      "horizontal": {
        "input_1": "The prompt to display to the user."
      }
    },
    "outputs": {
      "type": "FileLocation",
      "description": "The file path provided by the user."
    }
  },
  "env_spec": {
    "tools": [
      {
        "tool_name": "composition_tool",
        "affordances": [
          {
            "affordance_name": "compose",
            "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
          }
        ]
      },
      {
        "tool_name": "formatter_tool",
        "affordances": [
          {
            "affordance_name": "get",
            "call_code": "result = tool.get"
          },
          {
            "affordance_name": "wrap",
            "call_code": "result = tool.wrap"
          }
        ]
      },
      {
        "tool_name": "user_input",
        "affordances": [
          {
            "affordance_name": "create_input_function",
            "call_code": "result = tool.create_input_function()"
          }
        ]
      }
    ]
  },
  "sequence_spec": {
    "steps": [
      {
        "step_index": 1,
        "affordance": "formatter_tool.get",
        "params": {},
        "result_key": "dict_get_fn"
      },
      {
        "step_index": 2,
        "affordance": "user_input.create_input_function",
        "params": {},
        "result_key": "user_input_fn"
      },
      {
        "step_index": 3,
        "affordance": "formatter_tool.wrap",
        "params": {},
        "result_key": "wrap_fn"
      },
      {
        "step_index": 4,
        "affordance": "composition_tool.compose",
        "params": {
          "plan": [
            {
              "output_key": "prompt_from_vars",
              "function": {
                "__type__": "MetaValue",
                "key": "dict_get_fn"
              },
              "params": {
                "dictionary": "__initial_input__"
              },
              "literal_params": {
                "key": "input_1"
              }
            },
            {
              "output_key": "user_response_path",
              "function": {
                "__type__": "MetaValue",
                "key": "user_input_fn"
              },
              "params": {
                "prompt_text": "prompt_from_vars"
              }
            },
            {
              "output_key": "wrapped_file_location",
              "function": {
                "__type__": "MetaValue",
                "key": "wrap_fn"
              },
              "params": {
                "data": "user_response_path"
              },
              "literal_params": {
                "type": "file_location"
              }
            }
          ],
          "return_key": "wrapped_file_location"
        },
        "result_key": "instruction_fn"
      }
    ]
  }
}

```

```json

{
  "metadata": {
    "description": "Opens a file selection dialog allowing the user to select multiple files. Returns a list of FileLocations.",
    "inputs": {
      "vertical": {
        "initial_directory": "The starting directory for the file picker (defaults to agent base_dir)."
      },
      "horizontal": {
        "prompt_template": "The prompt to display in the dialog."
      }
    },
    "outputs": {
      "type": "FileLocationList",
      "description": "A list of selected file paths."
    }
  },
  "env_spec": {
    "tools": [
        {
          "tool_name": "composition_tool",
          "affordances": [
            {
              "affordance_name": "compose",
              "call_code": "result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
            }
          ]
        },
        {
          "tool_name": "formatter_tool",
          "affordances": [
            {
              "affordance_name": "get",
              "call_code": "result = tool.get"
            },
            {
              "affordance_name": "wrap_list",
              "call_code": "result = tool.wrap_list"
            }
          ]
        },
        {
          "tool_name": "user_input",
          "affordances": [
            {
              "affordance_name": "create_interaction",
              "call_code": "result = tool.create_interaction(**params)"
            }
          ]
        }
      ]
    },
    "sequence_spec": {
      "steps": [
        {
          "step_index": 1,
          "affordance": "formatter_tool.get",
          "params": {},
          "result_key": "dict_get_fn"
        },
        {
          "step_index": 2,
          "affordance": "user_input.create_interaction",
          "params": {
            "interaction_type": "multi_file_input",
            "initial_directory": {
              "__type__": "MetaValue",
              "key": "states.body.base_dir"
            }
          },
          "result_key": "user_files_fn"
        },
        {
          "step_index": 3,
          "affordance": "formatter_tool.wrap_list",
          "params": {},
          "result_key": "wrap_list_fn"
        },
        {
          "step_index": 4,
          "affordance": "composition_tool.compose",
          "params": {
            "plan": [
              {
                "output_key": "prompt_from_vars",
                "function": {
                  "__type__": "MetaValue",
                  "key": "dict_get_fn"
                },
                "params": {
                  "dictionary": "__initial_input__"
                },
                "literal_params": {
                  "key": "prompt_template"
                }
              },
              {
                "output_key": "user_file_list",
                "function": {
                  "__type__": "MetaValue",
                  "key": "user_files_fn"
                },
                "params": {
                  "prompt_text": "prompt_from_vars"
                }
              },
              {
                "output_key": "wrapped_file_list",
                "function": {
                  "__type__": "MetaValue",
                  "key": "wrap_list_fn"
                },
                "params": {
                  "data_list": "user_file_list"
                },
                "literal_params": {
                  "type": "file_location"
                }
              }
            ],
            "return_key": "wrapped_file_list"
          },
          "result_key": "instruction_fn"
        }
      ]
    }
  }
  
```

```python
"""
This module provides a loader for retrieving declarative composition paradigms
from JSON specifications.
"""
from ._paradigm import Paradigm, PARADIGMS_DIR

__all__ = ["Paradigm", "PARADIGMS_DIR"]

```

The updates are complete.

1.  **Registry Mechanism**: I've implemented a self-documenting registry.
    *   **`_paradigm.py`**: Updated to load and store a `metadata` field from the JSON files.
    *   **`_body.py`**: Updated the `_DefaultParadigmTool` to include a `list_manifest()` method. This method scans the `paradigms` directory and generates a formatted markdown list of all available paradigms, including their descriptions and input requirements.
    *   **`__init__.py`**: Exported `PARADIGMS_DIR` so the body tool can locate the files.

2.  **Data Migration**: I have iterated through all 15 paradigm JSON files in `infra/_agent/_models/_paradigms/` and injected the `metadata` block.
    *   Each block explicitly distinguishes between **Vertical Inputs** (configuration from the function concept) and **Horizontal Inputs** (runtime values from input concepts).

### Verification

You can now use this in your Architect Step prompt (`5.2.1_architect_step.md`) by injecting the manifest dynamically (if you are using a templating engine that supports python evaluation, like Jinja2 with the agent's body context):

```markdown
**2. Paradigms:**
Below is the library of available paradigms:
{{ body.paradigm_tool.list_manifest() }}
```

Or, if you simply want to see the output to verify it works, I can run a quick script to print the manifest for you.

Would you like me to run a verification script to display the generated manifest?

```markdown
**2. Paradigms:**
Below is the library of available paradigms:
{{ body.paradigm_tool.list_manifest() }}
```

---

**User**

a side action I we need to do - you see that the paradigms especially @infra/_agent/_models/_formatter_tool.py and the @infra/_agent/_steps/imperative_in_composition/_mvp.py talks with each other in wrappers - can we create a specialize element_typing script under _models and then pass that into the body to eliminate problems with incosistent element typing? 

---

**Cursor**

Yes, unifying the wrapper logic into a dedicated "Type System" module is an excellent idea. Currently, the logic for creating wrappers (`formatter_tool.wrap`) and parsing them (`_mvp._resolve_wrapper_string`) is scattered, leading to potential "drift" where one side might update a format (like adding an ID) while the other side doesn't expect it.

I recommend creating `infra/_agent/_models/_element_typing.py`.

### Proposed Architecture

1.  **`ElementType` (Enum/Constants)**: Define standard types like `FileLocation`, `ScriptLocation`, `PromptTemplate`, `Normal`.
2.  **`Wrapper` (Class)**: Handles the creation and parsing of the `%type_id(content)` syntax.
    *   `wrap(content, type_name)`: Returns the string.
    *   `parse(wrapped_string)`: Returns a `ParsedWrapper` object (type, id, content).
    *   `is_wrapped(string)`: Boolean check.
3.  **Tool Integration**:
    *   Inject this `Wrapper` class (or an instance) into the `Body`.
    *   Update `FormatterTool` to use `body.element_type.wrap(...)`.
    *   Update `MVP` to use `body.element_type.parse(...)`.

### Proposed Code: `infra/_agent/_models/_element_typing.py`

```python
import uuid
import re
from typing import NamedTuple, Any, Optional

class ParsedElement(NamedTuple):
    type_name: Optional[str]
    unique_id: str
    content: str

class ElementTyping:
    """
    Centralized handler for the agent's element typing system (wrappers).
    Format: %{type_name}unique_id(content) or %unique_id(content) for typeless.
    """
    
    # Regex for parsing: matches %{type}id(content) or %id(content)
    # Group 1: Optional type name inside {}
    # Group 2: ID (alphanumeric)
    # Group 3: Content inside ()
    _PATTERN = re.compile(r"^%(\{([a-zA-Z0-9_]+)\})?([a-zA-Z0-9]*)\((.*)\)$", re.DOTALL)

    def wrap(self, content: Any, type_name: str | None = None) -> str:
        """Wraps data into the standard agent format."""
        unique_id = uuid.uuid4().hex[:3]
        str_content = str(content)
        
        if type_name:
            return f"%{{{type_name}}}{unique_id}({str_content})"
        else:
            return f"%{unique_id}({str_content})"

    def parse(self, value: str) -> ParsedElement | None:
        """
        Parses a string to see if it's a wrapped element.
        Returns ParsedElement if it is, None otherwise.
        """
        if not isinstance(value, str) or not value.startswith("%"):
            return None
            
        match = self._PATTERN.match(value)
        if not match:
            return None
            
        # match.groups() structure:
        # 1: "{type}" or None
        # 2: "type" or None (inner group)
        # 3: "id"
        # 4: "content"
        
        type_name = match.group(2) # The inner group without braces
        unique_id = match.group(3)
        content = match.group(4)
        
        return ParsedElement(type_name=type_name, unique_id=unique_id, content=content)

    def is_wrapped(self, value: Any) -> bool:
        """Fast check if a value looks like a wrapper."""
        return isinstance(value, str) and value.startswith("%") and value.endswith(")")
```

### Next Steps
1.  **Create** this file.
2.  **Update `Body`** to initialize this tool.
3.  **Refactor `FormatterTool`** to delegate to `body.element_typing.wrap`.
4.  **Refactor `MVP`** to delegate to `body.element_typing.parse`.

Would you like me to proceed with creating the file and updating the Body first component references?

```python
import uuid
import re
from typing import NamedTuple, Any, Optional

class ParsedElement(NamedTuple):
    type_name: Optional[str]
    unique_id: str
    content: str

class ElementTyping:
    """
    Centralized handler for the agent's element typing system (wrappers).
    Format: %{type_name}unique_id(content) or %unique_id(content) for typeless.
    """
    
    # Regex for parsing: matches %{type}id(content) or %id(content)
    # Group 1: Optional type name inside {}
    # Group 2: ID (alphanumeric)
    # Group 3: Content inside ()
    _PATTERN = re.compile(r"^%(\{([a-zA-Z0-9_]+)\})?([a-zA-Z0-9]*)\((.*)\)$", re.DOTALL)

    def wrap(self, content: Any, type_name: str | None = None) -> str:
        """Wraps data into the standard agent format."""
        unique_id = uuid.uuid4().hex[:3]
        str_content = str(content)
        
        if type_name:
            return f"%{{{type_name}}}{unique_id}({str_content})"
        else:
            return f"%{unique_id}({str_content})"

    def parse(self, value: str) -> ParsedElement | None:
        """
        Parses a string to see if it's a wrapped element.
        Returns ParsedElement if it is, None otherwise.
        """
        if not isinstance(value, str) or not value.startswith("%"):
            return None
            
        match = self._PATTERN.match(value)
        if not match:
            return None
            
        # match.groups() structure:
        # 1: "{type}" or None
        # 2: "type" or None (inner group)
        # 3: "id"
        # 4: "content"
        
        type_name = match.group(2) # The inner group without braces
        unique_id = match.group(3)
        content = match.group(4)
        
        return ParsedElement(type_name=type_name, unique_id=unique_id, content=content)

    def is_wrapped(self, value: Any) -> bool:
        """Fast check if a value looks like a wrapper."""
        return isinstance(value, str) and value.startswith("%") and value.endswith(")")
```

