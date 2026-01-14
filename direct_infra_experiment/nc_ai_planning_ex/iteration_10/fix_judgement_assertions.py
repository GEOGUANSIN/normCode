"""
Script to fix judgement working_interpretations by adding assertion_condition field.
Parses <{ALL True}> from function_concept and adds proper assertion_condition structure.
"""

import json
import re
from pathlib import Path

def parse_assertion_from_function_concept(function_concept: str) -> dict | None:
    """
    Parse assertion condition from function_concept string.
    
    Examples:
        "::(check if concept type equals object)<{ALL True}>" -> {"quantifiers": {"axis": "all"}, "condition": True}
        "::(check something)<{ANY True}>" -> {"quantifiers": {"axis": "any"}, "condition": True}
        "::(check something)<{ALL False}>" -> {"quantifiers": {"axis": "all"}, "condition": False}
    """
    # Match pattern like <{ALL True}> or <{ANY True}> or <{ALL False}>
    match = re.search(r'<\{(\w+)\s+(True|False)\}>', function_concept)
    if not match:
        return None
    
    quantifier = match.group(1).lower()  # "all" or "any"
    condition = match.group(2) == "True"  # True or False
    
    return {
        "quantifiers": {
            "axis": quantifier
        },
        "condition": condition
    }


def fix_inference_repo(repo_path: str) -> None:
    """Fix all judgement_in_composition inferences by adding assertion_condition."""
    
    path = Path(repo_path)
    with open(path, 'r', encoding='utf-8') as f:
        inferences = json.load(f)
    
    updated_count = 0
    
    for inference in inferences:
        # Only process judgement_in_composition inferences
        if inference.get("inference_sequence") != "judgement_in_composition":
            continue
        
        function_concept = inference.get("function_concept", "")
        working_interp = inference.get("working_interpretation", {})
        
        # Skip if already has assertion_condition
        if "assertion_condition" in working_interp:
            print(f"Skipping {inference.get('flow_info', {}).get('flow_index', '?')}: already has assertion_condition")
            continue
        
        # Parse assertion from function_concept
        assertion = parse_assertion_from_function_concept(function_concept)
        
        if assertion:
            working_interp["assertion_condition"] = assertion
            inference["working_interpretation"] = working_interp
            flow_index = inference.get("flow_info", {}).get("flow_index", "?")
            print(f"Updated {flow_index}: added assertion_condition = {assertion}")
            updated_count += 1
        else:
            # No assertion pattern found - might be a different type of judgement
            flow_index = inference.get("flow_info", {}).get("flow_index", "?")
            print(f"No assertion pattern found for {flow_index}: {function_concept[:50]}...")
    
    # Write back
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(inferences, f, indent=2)
    
    print(f"\nDone! Updated {updated_count} judgement inferences.")


if __name__ == "__main__":
    repo_path = "direct_infra_experiment/nc_ai_planning_ex/iteration_10/repos/inference_repo.json"
    fix_inference_repo(repo_path)

