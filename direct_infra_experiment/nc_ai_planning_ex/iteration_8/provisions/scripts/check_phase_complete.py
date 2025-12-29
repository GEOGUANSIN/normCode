"""
Check Phase Complete Script

Checks if a specific phase is marked as complete in the progress file content.
Used by paradigm: h_Data-c_CheckPhaseComplete-o_Boolean
"""

import re
from typing import Optional


def check_phase_complete(
    progress_content: str,
    phase_number: Optional[int] = None,
    phase_name: Optional[str] = None
) -> bool:
    """
    Check if a phase is complete based on progress content.
    
    Args:
        progress_content: Content of progress.txt file
        phase_number: Phase number to check (1-5)
        phase_name: Alternative: full phase name like "phase_3_complete"
    
    Returns:
        True if phase is complete, False otherwise
    
    Progress file format:
        phase_1_complete
        phase_2_complete
        ...
    """
    if not progress_content:
        return False
    
    # Parse progress content into lines
    lines = [line.strip().lower() for line in progress_content.strip().split('\n')]
    completed_phases = set(lines)
    
    # Build the phase marker to look for
    if phase_name:
        marker = phase_name.lower().strip()
    elif phase_number is not None:
        marker = f"phase_{phase_number}_complete"
    else:
        # Try to extract from calling context (would be passed by orchestrator)
        return False
    
    return marker in completed_phases


def extract_phase_number_from_context(context: str) -> Optional[int]:
    """
    Extract phase number from context string.
    
    Examples:
        "check if phase 3 already complete" -> 3
        "phase 5 already complete" -> 5
    """
    match = re.search(r'phase\s+(\d+)', context.lower())
    if match:
        return int(match.group(1))
    return None


# Entry point for orchestrator
def main(inputs: dict) -> bool:
    """
    Main entry point called by orchestrator.
    
    Args:
        inputs: Dict with 'progress_content' and optionally 'phase_number' or context
    
    Returns:
        Boolean indicating if phase is complete
    """
    progress_content = inputs.get('progress_content', '')
    phase_number = inputs.get('phase_number')
    
    # If no phase number, try to extract from context
    if phase_number is None and 'context' in inputs:
        phase_number = extract_phase_number_from_context(inputs['context'])
    
    return check_phase_complete(progress_content, phase_number)


if __name__ == "__main__":
    # Test
    test_progress = """phase_1_complete
phase_2_complete
"""
    print(f"Phase 1 complete: {check_phase_complete(test_progress, 1)}")  # True
    print(f"Phase 2 complete: {check_phase_complete(test_progress, 2)}")  # True
    print(f"Phase 3 complete: {check_phase_complete(test_progress, 3)}")  # False

