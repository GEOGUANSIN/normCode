"""
Check Phase Complete Script

Checks if a specific phase is marked as complete in the progress file content.
Used by paradigm: v_ScriptLocation-h_Literal-c_Execute-o_Boolean

Function Signature Requirements (New Vision):
- Parameters named input_1, input_2, etc. matching value concept order
- Optional 'body' parameter for tool access
- Direct return value (no 'result' variable)

Supports two progress.txt formats:
1. Standard markers: "phase_1_complete", "phase_2_complete", etc.
2. Status dict format: {'status': 'success', 'location': '...1_refined_instruction.txt'}
   (Infers phase from checkpoint file names in the location)
"""

import re
import ast
from typing import Optional, Set


def _extract_completed_phases_from_status_dicts(content: str) -> Set[str]:
    """
    Extract completed phases from status dict format.
    
    Maps checkpoint file names to phases:
        1_refined_instruction.txt -> phase_1_complete
        2_extraction.json -> phase_2_complete
        3_classifications.json -> phase_3_complete
        4_dependency_tree.json -> phase_4_complete
        ncds_output.ncds -> phase_5_complete
    """
    completed = set()
    
    # Mapping from file patterns to phase markers
    file_to_phase = {
        '1_refined_instruction': 'phase_1_complete',
        '2_extraction': 'phase_2_complete',
        '3_classifications': 'phase_3_complete',
        '4_dependency_tree': 'phase_4_complete',
        'ncds_output': 'phase_5_complete',
    }
    
    # Process each line that looks like a status dict
    for line in content.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check if it's a status dict
        if line.startswith('{') and 'status' in line and 'success' in line:
            try:
                # Try to parse as Python dict
                status_dict = ast.literal_eval(line)
                if isinstance(status_dict, dict) and status_dict.get('status') == 'success':
                    location = status_dict.get('location', '')
                    # Check which phase this corresponds to
                    for file_pattern, phase_marker in file_to_phase.items():
                        if file_pattern in location:
                            completed.add(phase_marker)
                            break
            except (ValueError, SyntaxError):
                # Not a valid dict, skip
                pass
        else:
            # Standard marker format
            completed.add(line.lower())
    
    return completed


def check_phase_complete(
    input_1: str,          # progress_content (from {current progress})
    input_2: str = None,   # phase_name (from {phase_name: "phase_N"})
    body=None              # Optional Body instance
) -> bool:
    """
    Check if a phase is complete based on progress content.
    
    Args:
        input_1: Content of progress.txt file (supports both standard and status dict formats)
        input_2: Phase name like "phase_1", "phase_2", etc.
        body: Optional Body instance (not used, but available)
    
    Returns:
        True if phase is complete, False otherwise
    """
    progress_content = input_1 or ""
    phase_name = input_2
    
    if not progress_content:
        return False
    
    if not phase_name:
        return False
    
    # Extract completed phases (handles both formats)
    completed_phases = _extract_completed_phases_from_status_dicts(progress_content)
    
    # Build the phase marker to look for
    marker = phase_name.lower().strip()
    if not marker.endswith('_complete'):
        marker = f"{marker}_complete"
    
    return marker in completed_phases


def extract_phase_number_from_name(phase_name: str) -> Optional[int]:
    """
    Extract phase number from phase name.
    
    Examples:
        "phase_3" -> 3
        "phase_5" -> 5
    """
    match = re.search(r'phase[_\s]*(\d+)', phase_name.lower())
    if match:
        return int(match.group(1))
    return None


# Main entry point for paradigm (calls check_phase_complete)
def main(input_1: str = None, input_2: str = None, body=None, **kwargs) -> bool:
    """Main entry point for paradigm execution."""
    return check_phase_complete(input_1, input_2, body)


if __name__ == "__main__":
    # Test standard format
    print("=== Testing Standard Format ===")
    test_progress = """phase_1_complete
phase_2_complete
"""
    print(f"Phase 1 complete: {check_phase_complete(test_progress, 'phase_1')}")  # True
    print(f"Phase 2 complete: {check_phase_complete(test_progress, 'phase_2')}")  # True
    print(f"Phase 3 complete: {check_phase_complete(test_progress, 'phase_3')}")  # False
    
    # Test status dict format (current bug workaround)
    print("\n=== Testing Status Dict Format ===")
    test_status_progress = """{'status': 'success', 'location': 'C:\\\\Users\\\\ProgU\\\\...\\\\1_refined_instruction.txt'}
{'status': 'success', 'location': 'C:\\\\Users\\\\ProgU\\\\...\\\\2_extraction.json'}
"""
    print(f"Phase 1 complete: {check_phase_complete(test_status_progress, 'phase_1')}")  # True
    print(f"Phase 2 complete: {check_phase_complete(test_status_progress, 'phase_2')}")  # True
    print(f"Phase 3 complete: {check_phase_complete(test_status_progress, 'phase_3')}")  # False
    
    # Test mixed format
    print("\n=== Testing Mixed Format ===")
    test_mixed = """{'status': 'success', 'location': '1_refined_instruction.txt'}
phase_2_complete
"""
    print(f"Phase 1 complete: {check_phase_complete(test_mixed, 'phase_1')}")  # True
    print(f"Phase 2 complete: {check_phase_complete(test_mixed, 'phase_2')}")  # True
