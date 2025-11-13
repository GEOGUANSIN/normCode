import os
import sys
import logging
from typing import Any, Dict, List
import time

# --- Path Setup ---
# Ensure the project root is in the Python path for imports
CURRENT_DIR = os.path.dirname(__file__)
print(f"CURRENT_DIR: {CURRENT_DIR}")
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import core components
try:
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body, cross_product
except Exception:
	import sys, pathlib
	here = pathlib.Path(__file__).parent
	sys.path.insert(0, str(here.parent.parent))  # Add workspace root to path
	from infra import Inference, Concept, Reference, AgentFrame, BaseStates, Body, cross_product

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Constants for Example Files ---
EXAMPLE_SCRIPTS_DIR = os.path.join("generated_scripts")
EXAMPLE_PROMPTS_DIR = os.path.join("prompts")


def _get_and_parse_mia_result(final_ref: "Reference") -> float:
    """
    Recursively unpacks a nested Reference/list structure, parses the 
    MIA-formatted string (e.g., '%abc(25)'), and returns the numeric value.
    """
    val_to_parse = final_ref
    
    # Recursively unpack lists and Reference tensors
    while isinstance(val_to_parse, (Reference, list)):
        if not val_to_parse:
            return None
        if isinstance(val_to_parse, Reference):
            val_to_parse = val_to_parse.tensor
        else: # is a list
            val_to_parse = val_to_parse[0]

    if not isinstance(val_to_parse, str):
        return val_to_parse # Should already be a number if not a string

    # Parse the MIA string format like '%abc(25)'
    if '(' in val_to_parse and val_to_parse.endswith(')'):
        try:
            # Extract the content inside the last parenthesis
            str_val = val_to_parse.split('(', 1)[1].rstrip(')')
            # Use float() as it handles ints ('25') and floats ('56.0')
            return float(str_val)
        except (ValueError, TypeError, IndexError):
            return val_to_parse # Return raw string if parsing fails
    
    return val_to_parse


def _build_concepts(
    a_val: int,
    b_val: int,
    script_path: str,
    prompt_path: str | None = None
) -> tuple[Concept, List[Concept], Concept]:
    """Helper to build concepts for the demo."""
    # Input 1
    ref_a = Reference.from_data([a_val])
    concept_a = Concept(name="input_1", reference=ref_a)

    # Input 2
    ref_b = Reference.from_data([b_val])
    concept_b = Concept(name="input_2", reference=ref_b)
    
    # --- Create and combine wrapper concepts ---
    # Create a reference for the script path with a unique axis
    script_location_str = f"%{{script_location}}({script_path})"
    ref_script = Reference(axes=['template'], shape=(1,))
    ref_script.set(script_location_str, template=0)

    refs_to_combine = [ref_script]

    # If a prompt is provided, create a reference for it with its own unique axis
    if prompt_path:
        prompt_str = f"%{{prompt_template}}({prompt_path})"
        ref_prompt = Reference(axes=['template'], shape=(1,))
        ref_prompt.set(prompt_str, template=0)
        refs_to_combine.append(ref_prompt)

    # Create a single combined reference and a single concept for the wrappers
    combined_wrappers_ref = cross_product(refs_to_combine)
    wrappers_concept = Concept(name="wrappers", reference=combined_wrappers_ref)
    
    value_concepts = [concept_a, concept_b, wrappers_concept]

    # Concept to Infer (Output)
    concept_to_infer = Concept(name="result")
    
    # Function concept (dummy for this sequence, but needs a non-null reference)
    function_concept = Concept(
        name="imperative_python_runner",
        reference=Reference.from_data(["placeholder"])
    )

    return concept_to_infer, value_concepts, function_concept


def run_direct_execution_example():
    """Demonstrates executing a pre-existing Python script."""
    logger.info("--- Running Direct Execution Example ---")
    
    # script_path = os.path.abspath(os.path.join(PRE_EXISTING_SCRIPT_DIR, "add_numbers.py"))
    script_path = "generated_scripts/multiply_numbers.py"
    
    concept_to_infer, value_concepts, function_concept = _build_concepts(
        a_val=15,
        b_val=10,
        script_path=script_path
    )

    working_interpretation = {
        "value_order": {"input_1": 0, "input_2": 1, "wrappers": 2}
    }

    inference = Inference(
        "imperative_python",
        concept_to_infer,
        function_concept,
        value_concepts,
    )


    body = Body(base_dir=CURRENT_DIR)
    agent = AgentFrame("demo", working_interpretation=working_interpretation, body=body)
    agent.configure(inference, "imperative_python")
    states = inference.execute()

    final_ref = states.get_reference("inference", "MIA")
    result = _get_and_parse_mia_result(final_ref)
    
    logger.info(f"Direct execution result: {result}")
    assert result == 150, f"Expected 150, but got {result}"
    logger.info("Direct execution test PASSED.")


def run_generate_and_execute_example():
    """Demonstrates generating a script from a prompt and then executing it."""
    logger.info("\n--- Running Generate-and-Execute Example ---")
    
    script_path = os.path.join(EXAMPLE_SCRIPTS_DIR, "multiply_numbers.py")
    prompt_path = os.path.join(EXAMPLE_PROMPTS_DIR, "multiply_prompt.txt")

    # Ensure the script doesn't exist to trigger generation
    if os.path.exists(script_path):
        os.remove(script_path)
        logger.info(f"Removed existing script at {script_path} to ensure generation.")

    concept_to_infer, value_concepts, function_concept = _build_concepts(
        a_val=7,
        b_val=8,
        script_path=script_path,
        prompt_path=prompt_path
    )

    working_interpretation = {
        "with_thinking": True,
        "value_order": {
            "input_1": 0,
            "input_2": 1,
            "wrappers": 2
        }
    }

    inference = Inference(
        "imperative_python",
        concept_to_infer,
        function_concept,
        value_concepts,
    )
    
    try:
        # --- First Run (Generation) ---
        logger.info("First run: expecting script generation...")
        agent = AgentFrame("demo", working_interpretation=working_interpretation, body=Body(base_dir=CURRENT_DIR))
        agent.configure(inference, "imperative_python")
        states = inference.execute()

        final_ref = states.get_reference("inference", "MIA")
        result = _get_and_parse_mia_result(final_ref)

        logger.info(f"Generation run result: {result}")
        assert result == 56, f"Expected 56 on first run, but got {result}"
        # assert os.path.exists(script_path), "Script file was not created after generation."
        logger.info("Generation run test PASSED.")

        # --- Second Run (Cache/Re-use) ---
        time.sleep(1) # Give a moment for file system to settle
        logger.info("\nSecond run: expecting script re-use from file...")
        
        # We need a new inference object for a clean execution
        inference_reuse = Inference(
            "imperative_python",
            concept_to_infer,
            function_concept,
            value_concepts,
        )
        agent_reuse = AgentFrame("demo", working_interpretation=working_interpretation, body=Body(base_dir=CURRENT_DIR))
        agent_reuse.configure(inference_reuse, "imperative_python")
        states_reuse = inference_reuse.execute()

        final_ref_reuse = states_reuse.get_reference("inference", "MIA")
        result_reuse = _get_and_parse_mia_result(final_ref_reuse)

        logger.info(f"Re-use run result: {result_reuse}")
        assert result_reuse == 56, f"Expected 56 on second run, but got {result_reuse}"
        logger.info("Re-use run test PASSED.")
        
    finally:
        # Clean up the generated script
        if os.path.exists(script_path):
            # os.remove(script_path)
            # logger.info(f"Cleaned up generated script: {script_path}")
            pass


if __name__ == "__main__":
    # run_direct_execution_example()
    run_generate_and_execute_example()
