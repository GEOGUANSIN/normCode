"""
Repository file verification utilities for NormCode Orchestrator Streamlit App.
"""

import re
from pathlib import Path
from typing import Tuple, List

from infra import ConceptRepo, InferenceRepo


def verify_repository_files(
    concept_repo: ConceptRepo,
    inference_repo: InferenceRepo,
    base_dir: str
) -> Tuple[bool, List[str], List[str]]:
    """
    Verify that all script and prompt files referenced in the repository exist in base_dir.
    
    Args:
        concept_repo: Concept repository to verify
        inference_repo: Inference repository to verify
        base_dir: Base directory to check for files
    
    Returns:
        Tuple of (all_valid, warnings, errors)
        - all_valid: True if all files exist or no files are referenced
        - warnings: List of warning messages
        - errors: List of error messages (missing files)
    """
    warnings = []
    errors = []
    base_path = Path(base_dir)
    
    # Check for prompt files
    potential_prompt_dirs = [
        base_path / "prompts",
        base_path / "_models" / "prompts",
        base_path / "generated_prompts"
    ]
    
    prompt_dir_exists = any(d.exists() and d.is_dir() for d in potential_prompt_dirs)
    
    # Check inference sequences for custom file references
    for inference in inference_repo.get_all_inferences():
        seq = inference.inference_sequence
        
        # Check for sequences that typically generate or read files
        if "python" in seq.lower() or "script" in seq.lower():
            # Check for generated_scripts directory
            script_dirs = [
                base_path / "generated_scripts",
                base_path / "scripts"
            ]
            
            script_dir_exists = any(d.exists() and d.is_dir() for d in script_dirs)
            
            if not script_dir_exists:
                # This is just a warning - directories are created on demand
                warnings.append(
                    f"Inference '{inference.concept_to_infer.concept_name}' uses sequence '{seq}' "
                    f"which may generate scripts. Consider creating 'generated_scripts/' in base_dir."
                )
    
    # Check concepts for explicit file references in context or reference_data
    for concept in concept_repo.get_all_concepts():
        # Check if reference_data contains file paths
        if concept.reference_data:
            ref_data_str = str(concept.reference_data)
            
            # Look for NormCode file wrappers: %{type}(path/to/file.ext)
            # Examples: %{script_location}(generated_scripts/op_sum.py)
            #           %{prompt_location}(generated_prompts/op_sum_prompt.txt)
            
            # Pattern to match NormCode file references
            normcode_file_pattern = r'%\{[\w_]+\}\(([\w/\\.-]+)\)'
            normcode_matches = re.findall(normcode_file_pattern, ref_data_str)
            
            for file_path_str in normcode_matches:
                # This is a file reference wrapped in NormCode syntax
                file_path = base_path / file_path_str
                if not file_path.exists():
                    errors.append(
                        f"Concept '{concept.concept_name}' references file '{file_path_str}' "
                        f"which was not found in base_dir: {base_dir}"
                    )
            
            # Also check for plain file paths (less common, but possible)
            # Only match if it looks like a proper file path (has directory separator)
            plain_file_pattern = r'(?:[\w/\\]+/)[\w/\\.-]+\.(?:txt|py|json|prompt)'
            plain_matches = re.findall(plain_file_pattern, ref_data_str)
            
            for file_path_str in plain_matches:
                # Skip if already found in NormCode pattern
                if file_path_str not in normcode_matches:
                    file_path = base_path / file_path_str
                    if not file_path.exists():
                        errors.append(
                            f"Concept '{concept.concept_name}' references file '{file_path_str}' "
                            f"which was not found in base_dir: {base_dir}"
                        )
    
    # Check for ground concepts that need data (only semantical concepts, not syntactical operators)
    missing_ground_concepts = []
    for concept in concept_repo.get_all_concepts():
        # Only check ground concepts that are:
        # 1. Not invariant (invariants have embedded logic)
        # 2. Semantical (not syntactical operators like $., @if, etc.)
        if concept.is_ground_concept and not concept.is_invariant:
            # Skip syntactical concepts (they're operators, not data containers)
            if concept.concept and concept.concept.is_syntactical():
                continue
            
            # Check if this semantical ground concept has data
            has_data = False
            if concept.reference_data is not None:
                has_data = True
            elif concept.concept and concept.concept.reference:
                has_data = True
            
            if not has_data:
                missing_ground_concepts.append(concept.concept_name)
    
    if missing_ground_concepts:
        errors.append(
            f"Missing required input data for ground concepts: {', '.join(missing_ground_concepts)}. "
            f"Please provide an inputs.json file with these concepts."
        )
    
    # Summary
    all_valid = len(errors) == 0
    
    if all_valid and len(warnings) == 0:
        warnings.append(f"✓ Base directory structure looks good: {base_dir}")
        warnings.append(f"✓ All required ground concepts have data")
    
    return all_valid, warnings, errors

