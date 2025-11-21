"""
This script demonstrates how to use the ModelSequenceRunner to compose a sequence of 
functions declaratively.

It replicates the behavior of the hard-coded `create_generation_function_with_template_in_vars_with_thinking`
function by breaking it down into four distinct, granular functions and then composing
them using a spec.
"""
from typing import Any, Dict, Callable
import json
from unittest.mock import patch
import tempfile
import os
import inspect
import uuid

# --- Fix Python path to allow running as a script ---
import sys
import pathlib
project_root = pathlib.Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


# --- Assume these imports are available from the infra ---
from infra._states import (
    ModelEnvSpecLite,
    ModelSequenceSpecLite,
    ModelStepSpecLite,
    ToolSpecLite,
    AffordanceSpecLite,
    MetaValue,
)
from infra._agent._models._model_runner import ModelSequenceRunner
# --- Import the REAL tools from the codebase ---
from infra._agent._models._language_models import LanguageModel, GENERATE_METHOD_PLACEHOLDER
from infra._agent._models._composition_tool import CompositionTool
from infra._agent._models._file_system import FileSystemTool
from infra._agent._models._formatter_tool import FormatterTool

# --- 1. Define Tools and Adapters ---

# All formatter tools are now consolidated in the FormatterTool class in its own file.

# --- 2. Define the Tools and their Affordances in a Spec ---

# This spec now includes the language_model with a direct 'generate' affordance,
# and also the generic CompositionTool.
env_spec = ModelEnvSpecLite(
    tools=[
        ToolSpecLite(
            tool_name="language_model",
            affordances=[
                # This simple affordance just provides a handle to the generate method.
                AffordanceSpecLite(
                    affordance_name="generate",
                    call_code="result = tool.generate"
                )
            ]
        ),
        ToolSpecLite(
            tool_name="composition_tool",
            affordances=[
                AffordanceSpecLite(
                    affordance_name="compose",
                    call_code="result = tool.compose(plan=params['plan'], return_key=params.get('return_key'))"
                )
            ]
        ),
        ToolSpecLite(
            tool_name="formatter_tool",
            affordances=[
                AffordanceSpecLite(affordance_name="create_substitute_function", call_code="result = tool.create_substitute_function(template_key=params['template_key'])"),
                AffordanceSpecLite(affordance_name="parse", call_code="result = tool.parse"),
                AffordanceSpecLite(affordance_name="get", call_code="result = tool.get"),
                AffordanceSpecLite(affordance_name="wrap", call_code="result = tool.wrap"),
            ]
        ),
        ToolSpecLite(
            tool_name="file_system_tool",
            affordances=[AffordanceSpecLite(
                affordance_name="save",
                call_code="result = tool.save"
            )]
        ),
    ]
)

# --- 3. Define the Model Sequence Spec for Composition ---

# This sequence now uses the high-level factory to create the composed function.
sequence_spec = ModelSequenceSpecLite(
    env=env_spec,
    steps=[
        # Get handles to all component functions, including the LLM's generate method.
        ModelStepSpecLite(step_index=1, affordance="formatter_tool.create_substitute_function", params={"template_key": "prompt_template"}, result_key="template_fn"),
        ModelStepSpecLite(step_index=2, affordance="language_model.generate", params={}, result_key="generate_fn"),
        ModelStepSpecLite(step_index=3, affordance="formatter_tool.parse", params={}, result_key="parse_fn"),
        ModelStepSpecLite(step_index=4, affordance="formatter_tool.wrap", params={}, result_key="mia_fn"),
        ModelStepSpecLite(step_index=5, affordance="file_system_tool.save", params={}, result_key="save_fn"),
        ModelStepSpecLite(step_index=6, affordance="formatter_tool.get", params={}, result_key="dict_get_fn"),

        # Create the final composed function by calling the generic CompositionTool directly.
        ModelStepSpecLite(
            step_index=7,
            affordance="composition_tool.compose", # We call the generic tool.
            params={
                "plan": [
                    {
                        'output_key': 'prompt_string',
                        'function': MetaValue(key="template_fn"),
                        'params': {'__positional__': '__initial_input__'}
                    },
                    {
                        'output_key': 'raw_llm_response',
                        # We now use a MetaValue to reference the handle we retrieved.
                        'function': MetaValue(key="generate_fn"),
                        'params': {'__positional__': 'prompt_string'}
                    },
                    {
                        'output_key': 'parsed_dict',
                        'function': MetaValue(key="parse_fn"),
                        'params': {'__positional__': 'raw_llm_response'}
                    },
                    {
                        'output_key': 'final_answer',
                        'function': MetaValue(key="dict_get_fn"),
                        'params': {'dictionary': 'parsed_dict'},
                        'literal_params': {'key': 'answer'}
                    },
                    # Explicitly extract the save_path from the initial input.
                    {
                        'output_key': 'save_path_from_vars',
                        'function': MetaValue(key="dict_get_fn"),
                        'params': {
                            'dictionary': '__initial_input__',
                        },
                        'literal_params': {
                            'key': 'save_path'
                        }
                    },
                    # Save the unwrapped answer first.
                    {
                        'output_key': 'save_confirmation',
                        'function': MetaValue(key="save_fn"),
                        'params': {
                            'content': 'final_answer',
                            'location': 'save_path_from_vars'
                        }
                    },
                    # Extract the saved location from the confirmation dictionary.
                    {
                        'output_key': 'saved_location',
                        'function': MetaValue(key="dict_get_fn"),
                        'params': {'dictionary': 'save_confirmation'},
                        'literal_params': {'key': 'location'}
                    },
                    # Then wrap the saved location for the final return value.
                    {
                        'output_key': 'mia_result',
                        'function': MetaValue(key="mia_fn"),
                        'params': {'__positional__': 'saved_location'},
                        'literal_params': {'type': 'file_location'}
                    },
                ],
                "return_key": "mia_result" # The final result is the wrapped location.
            },
            result_key="instruction_fn"
        )
    ]
)

# --- 4. Define the Runtime Environment using REAL Tools ---

class RealToolProvider:
    """
    This class now provides all the tools needed for the declarative sequence.
    """
    language_model = LanguageModel("qwen-turbo-latest")
    composition_tool = CompositionTool()
    formatter_tool = FormatterTool()
    file_system_tool = FileSystemTool()

# We need a mock `states` object to pass to the runner.
mock_states = type("States", (), {"body": RealToolProvider()})()

# --- 5. Execute and Test the Composed Function ---

# Initialize the runner with our spec and mock environment
runner = ModelSequenceRunner(mock_states, sequence_spec)

# Run the sequence to get the composed function.
meta = runner.run()
instruction_fn = meta.get("instruction_fn")

# --- 6. Test the Composed `instruction_fn` with a REAL LLM CALL ---

if instruction_fn:
    print(">>> Successfully composed instruction_fn.")
    print(">>> Calling the function with sample vars (this will make a real API call)...")

    prompt_template = (
        "You are a helpful assistant that provides answers in JSON format.\n"
        "What is the capital of ${country}?\n"
        "Respond with a JSON object containing the key 'thinking' and 'answer' with the capital of the country."
    )
    
    # Use a temporary file for the output
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt", encoding="utf-8")
    temp_file.close() # Close it so our tool can write to it

    test_vars = {
        "prompt_template": prompt_template,
        "country": "France",
        "save_path": temp_file.name
    }

    # This call will now go through the real LanguageModel and make an API call.
    # Make sure your settings.yaml is configured with an API key for 'qwen-turbo-latest'.
    final_result = instruction_fn(test_vars)

    print(f"\n>>> Final result of composed function: {final_result}")

    # Verify the file was written with the UNWRAPPED content
    with open(temp_file.name, 'r', encoding='utf-8') as f:
        file_content = f.read()
    print(f">>> Content of saved file: {file_content}")
    # The final result should be the WRAPPED file path.
    assert temp_file.name in final_result
    # The saved content should be a non-empty string.
    assert isinstance(file_content, str) and file_content

    # Clean up the temporary file
    os.remove(temp_file.name)
    print(f">>> Cleaned up temporary file: {temp_file.name}")


    # Since we now expect a typed wrapped string, we'll check for that.
    import re
    if isinstance(final_result, str) and re.match(r"%\{file_location\}[a-f0-9]{3}\(.*\)", final_result):
        print(">>> Test successful: Received a correctly formatted wrapped string.")
    elif isinstance(final_result, dict) and "error" in final_result:
        print(f">>> Test failed gracefully with error: {final_result['error']}")
    else:
        print(f">>> Test finished with an unexpected result type: {type(final_result)}")

else:
    print("!!! Failed to compose instruction_fn.")

"""
Expected Output (will vary based on LLM response):

>>> Successfully composed instruction_fn.
>>> Calling the function with sample vars (this will make a real API call)...
>>> Adapter successfully saved content to C:/Users/.../Temp/tmpxxxxxxx.txt
>>> MIA step: Wrapped data -> %{file_location}xxx(C:/Users/.../Temp/tmpxxxxxxx.txt)

>>> Final result of composed function: %{file_location}xxx(C:/Users/.../Temp/tmpxxxxxxx.txt)
>>> Content of saved file: Paris
>>> Cleaned up temporary file: C:/Users/.../Temp/tmpxxxxxxx.txt
>>> Test successful: Received a correctly formatted wrapped string.
"""
