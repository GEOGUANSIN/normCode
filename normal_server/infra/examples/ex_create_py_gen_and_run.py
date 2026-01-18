import os
import sys

# Add project root to path to allow imports from infra
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(PROJECT_ROOT)

from infra._agent._models._language_models import LanguageModel
from infra._agent._body import Body

def run_example():
    """
    This example demonstrates the reusable script generation functionality of 
    the `create_python_generate_and_run_function`.
    """
    print("Initializing example for reusable script generation...")

    # Define paths for our reusable scripts (store them under this examples directory)
    example_script_dir = os.path.join(os.path.dirname(__file__), "generated_scripts")
    os.makedirs(example_script_dir, exist_ok=True)

    body = Body(llm_name="qwen-turbo-latest", base_dir=example_script_dir) 
    language_model = body.llm


    uppercase_script_path = os.path.join(example_script_dir, "uppercase_string.py")
    multiply_script_path = os.path.join(example_script_dir, "multiply_numbers.py")
    file_io_script_path = os.path.join(example_script_dir, "file_io_uppercase.py") # New script path
    
    # Define paths for file I/O test
    input_file_path = os.path.join(example_script_dir, "input.txt")
    output_file_path = os.path.join(example_script_dir, "output.txt")


    # Clean up any leftover scripts from previous runs
    if os.path.exists(uppercase_script_path):
        os.remove(uppercase_script_path)
    if os.path.exists(multiply_script_path):
        os.remove(multiply_script_path)
    if os.path.exists(file_io_script_path):
        os.remove(file_io_script_path)
    if os.path.exists(input_file_path):
        os.remove(input_file_path)
    if os.path.exists(output_file_path):
        os.remove(output_file_path)

    if language_model.mock_mode:
        print("\n" + "="*80)
        print("WARNING: LanguageModel is in MOCK MODE. Generation tests will be skipped.")
        print("Please configure 'settings.yaml' to run the full example.")
        print("="*80 + "\n")
        return

    # --- Test Case 1: Generate and run a script for the first time ---
    print("\n--- TEST CASE 1: Generate and Execute 'uppercase_string.py' ---")
    generate_and_run = language_model.create_python_generate_and_run_function(
        file_tool=body.file_system, python_interpreter=body.python_interpreter
    )
    
    vars_for_generation = {
        "prompt_template": "Create a python script that uppercases a string provided in the 'data_input' variable. Do NOT redeclare 'data_input'. The final output must be in a variable named 'result'. IMPORTANT: Respond with only the raw Python code.",
        "script_location": uppercase_script_path,
        "data_input": "first run"
    }
    result1 = generate_and_run(vars_for_generation)
    print(f"\nResult from first run: {result1}")
    assert result1 == "FIRST RUN"
    assert os.path.exists(uppercase_script_path)
    print("--> Script generated and executed successfully.")

    # --- Test Case 2: Reuse the same script with different data ---
    print("\n--- TEST CASE 2: Reuse 'uppercase_string.py' with new data ---")
    
    # Note: We do not provide the 'prompt_template' this time.
    # The function should find and execute the script from Test Case 1.
    vars_for_reuse = {
        "script_location": uppercase_script_path,
        "data_input": "second run"
    }
    result2 = generate_and_run(vars_for_reuse)
    print(f"\nResult from reused script: {result2}")
    assert result2 == "SECOND RUN"
    print("--> Script reused successfully without calling the LLM.")

    # --- Test Case 3: Generate a second script with 'thinking' ---
    print("\n--- TEST CASE 3: Generate and Execute 'multiply_numbers.py' with thinking ---")
    generate_and_run_thinking = language_model.create_python_generate_and_run_function(
        with_thinking=True, file_tool=body.file_system, python_interpreter=body.python_interpreter
    )
    vars_for_thinking = {
        "prompt_template": "Instruction: create a python script that multiplies 'input_a' and 'input_b'. Do NOT redeclare these variables. The final output must be in a variable named 'result'. IMPORTANT: Respond with a JSON object containing 'thinking' and 'code' keys.",
        "script_location": multiply_script_path,
        "input_a": 11,
        "input_b": 12
    }
    result3 = generate_and_run_thinking(vars_for_thinking)
    print(f"\nResult from thinking script: {result3}")
    assert result3 == 132
    assert os.path.exists(multiply_script_path)
    print("--> 'Thinking' script generated and executed successfully.")

    # --- Test Case 4: Generate a script that performs file I/O ---
    print("\n--- TEST CASE 4: Generate and Execute 'file_io_uppercase.py' ---")
    
    # 1. Create a source file for the script to read
    input_content = "hello file system"
    body.file_system.save(location=input_file_path, content=input_content)
    print(f"Created input file: '{input_file_path}' with content: '{input_content}'")

    # 2. Define prompt and variables for the generation
    vars_for_file_io = {
        "prompt_template": (
            "Create a python script that reads content from the file specified in 'input_path', "
            "converts it to uppercase, and writes the result to the file specified in 'output_path'. "
            "Do NOT redeclare 'input_path' or 'output_path'. The script should not produce any return value."
            "IMPORTANT: Respond with only the raw Python code."
        ),
        "script_location": file_io_script_path,
        "input_path": input_file_path,
        "output_path": output_file_path
    }
    
    # 3. Generate and run the script
    # This function call won't return a direct result, as the script's output is file-based
    generate_and_run(vars_for_file_io)

    # 4. Verify the result
    assert os.path.exists(file_io_script_path)
    print(f"--> File I/O script generated successfully at: {file_io_script_path}")
    
    read_result = body.file_system.read(location=output_file_path)
    output_content = read_result.get("content")
    print(f"Read from output file: '{output_file_path}' with content: '{output_content}'")
    
    assert output_content == input_content.upper()
    print("--> File I/O script executed and verified successfully.")


    # # --- Cleanup ---
    # print("\n--- Cleaning up generated script files ---")
    # os.remove(uppercase_script_path)
    # os.remove(multiply_script_path)
    # os.remove(file_io_script_path)
    # os.remove(input_file_path)
    # os.remove(output_file_path)
    # print("--> Cleanup complete.")

if __name__ == "__main__":
    run_example()
