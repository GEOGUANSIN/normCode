"""
Check Phase Complete Script

Checks if a specific phase is marked as complete in the progress file content.
Used by paradigm: v_ScriptLocation-h_Literal-c_Execute-o_Boolean

Function Signature Requirements (New Vision):
- Parameters named input_1, input_2, etc. matching value concept order
- Optional 'body' parameter for tool access
- Direct return value (no 'result' variable)
"""

import re
from typing import Optional


def check_phase_complete(
    input_1: str,          # progress_content (from {current progress})
    input_2: str = None,   # phase_name (from {phase_name: "phase_N"})
    body=None              # Optional Body instance
) -> bool:
    """
    Check if a phase is complete based on progress content.
    
    Args:
        input_1: Content of progress.txt file (the progress string)
        input_2: Phase name like "phase_1", "phase_2", etc.
        body: Optional Body instance (not used, but available)
    
    Returns:
        True if phase is complete, False otherwise
    
    Progress file format:
        phase_1_complete
        phase_2_complete
        ...
    """
    progress_content = input_1 or ""
    phase_name = input_2
    
    if not progress_content:
        return False
    
    # Parse progress content into lines
    lines = [line.strip().lower() for line in progress_content.strip().split('\n')]
    completed_phases = set(lines)
    
    # Build the phase marker to look for
    if phase_name:
        # Handle both "phase_1" and "phase_1_complete" formats
        marker = phase_name.lower().strip()
        if not marker.endswith('_complete'):
            marker = f"{marker}_complete"
    else:
        return False
    
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


if __name__ == "__main__":
    # Test
    test_progress = """phase_1_complete
phase_2_complete
"""
    print(f"Phase 1 complete: {check_phase_complete(test_progress, 'phase_1')}")  # True
    print(f"Phase 2 complete: {check_phase_complete(test_progress, 'phase_2')}")  # True
    print(f"Phase 3 complete: {check_phase_complete(test_progress, 'phase_3')}")  # False
