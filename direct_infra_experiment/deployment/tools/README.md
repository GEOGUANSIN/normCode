# Deployment Tools

Standalone tool implementations for NormCode deployment, designed to work without Canvas/WebSocket dependencies.

## Overview

These tools provide the same interfaces as Canvas tools and infra tools, but are:
- **Standalone**: No WebSocket or Canvas UI dependencies
- **Self-contained**: Can work without the full infra stack
- **Configurable**: Direct parameters or settings file
- **Production-ready**: Suitable for server-side execution

## Tools

### DeploymentLLMTool

Language Model tool with OpenAI-compatible API support.

```python
from deployment.tools import DeploymentLLMTool

# Demo mode (mock responses)
llm = DeploymentLLMTool(model_name="demo")

# With API key
llm = DeploymentLLMTool(
    model_name="qwen-plus",
    api_key="your-api-key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# From settings file
llm = DeploymentLLMTool(
    model_name="qwen-plus",
    settings_path="./settings.yaml"
)

# Generate text
response = llm.generate("Translate: hello")

# Create template-based generation function
gen_fn = llm.create_generation_function("Translate: $text")
result = gen_fn({"text": "hello"})
```

### DeploymentFileSystemTool

File operations within a sandboxed base directory.

```python
from deployment.tools import DeploymentFileSystemTool

fs = DeploymentFileSystemTool(base_dir="./my_project")

# Read file
content = fs.read("data.json")

# Write file
fs.write("output.json", '{"result": "done"}')

# List directory
files = fs.list_dir("./")

# Check existence
if fs.exists("config.json"):
    config = fs.read("config.json")
```

### DeploymentPromptTool

Template loading and variable substitution.

```python
from deployment.tools import DeploymentPromptTool

prompt = DeploymentPromptTool(base_dir="./prompts")

# Load template
template = prompt.read("instruction.md")

# Render with variables
rendered = prompt.render("instruction.md", {"task": "Analyze data"})

# Create template function
template_fn = prompt.create_template_function(template)
result = template_fn({"task": "Analyze"})
```

### DeploymentPythonInterpreterTool

Execute Python scripts in a controlled environment.

```python
from deployment.tools import DeploymentPythonInterpreterTool

python = DeploymentPythonInterpreterTool()

# Execute script
result = python.execute(
    script_code="result = x + y",
    inputs={"x": 1, "y": 2}
)
# result = 3

# Execute function
result = python.function_execute(
    script_code="def add(a, b): return a + b",
    function_name="add",
    function_params={"a": 1, "b": 2}
)
# result = 3

# Create reusable executor
executor = python.create_function_executor(script_code, "process")
result = executor({"data": my_data})
```

### DeploymentFormatterTool

Data formatting, parsing, and extraction utilities.

```python
from deployment.tools import DeploymentFormatterTool

fmt = DeploymentFormatterTool()

# Parse JSON
data = fmt.parse('{"key": "value"}')

# Parse boolean from text
is_true = fmt.parse_boolean("yes")  # True

# Wrap as perceptual sign
wrapped = fmt.wrap("hello", type="text")  # %{text}abc(hello)

# Get dict value
value = fmt.get({"key": "value"}, key="key")  # "value"

# Clean code from markdown
code = fmt.clean_code("```python\nprint('hi')\n```")  # "print('hi')"
```

### DeploymentCompositionTool

Multi-step function composition for paradigm execution.

```python
from deployment.tools import DeploymentCompositionTool

comp = DeploymentCompositionTool()

# Define execution plan
plan = [
    {
        "function": prompt_fn,
        "output_key": "prompt",
        "params": {"__positional__": "__initial_input__"}
    },
    {
        "function": llm_fn,
        "output_key": "response",
        "params": {"__positional__": "prompt"}
    },
    {
        "function": parse_fn,
        "output_key": "parsed",
        "params": {"__positional__": "response"}
    },
]

# Create composed function
composed = comp.compose(plan, return_key="parsed")

# Execute
result = composed({"input_1": user_message})
```

### DeploymentUserInputTool

CLI or API-based user input for human-in-the-loop.

```python
from deployment.tools import DeploymentUserInputTool

# CLI mode (interactive prompts)
user_input = DeploymentUserInputTool(interactive=True)

# API mode (waits for submit_response)
user_input = DeploymentUserInputTool(interactive=False)

# Create input function
input_fn = user_input.create_input_function()
response = input_fn(prompt_text="Enter your name: ")

# Confirm dialog
confirm_fn = user_input.create_interaction(interaction_type="confirm")
confirmed = confirm_fn(prompt_text="Proceed?")  # True/False

# API mode: submit response externally
user_input.submit_response(request_id, "user response")
```

## Configuration

### settings.yaml

Configure LLM providers:

```yaml
BASE_URL: https://dashscope.aliyuncs.com/compatible-mode/v1

qwen-plus:
  DASHSCOPE_API_KEY: sk-xxx

gpt-4o:
  OPENAI_API_KEY: sk-xxx

deepseek-r1:
  DEEPSEEK_API_KEY: sk-xxx
```

## Comparison to Canvas Tools

| Feature | Canvas Tools | Deployment Tools |
|---------|-------------|------------------|
| WebSocket events | ✅ | ❌ |
| UI integration | ✅ | ❌ |
| Standalone use | ❌ | ✅ |
| Server-side | ❌ | ✅ |
| CLI support | ❌ | ✅ |
| Same interface | ✅ | ✅ |

## See Also

- [Deployment README](../README.md) - Overview of deployment tools
- [Canvas Tools](../../canvas_app/backend/tools/README.md) - Canvas UI-integrated tools
- [Infra Agent](../../infra/_agent/README.md) - Core agent implementation

