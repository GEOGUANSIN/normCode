import json
import os
import sys
from pathlib import Path
import dataclasses

# Add project root to path to import infra
project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the repository creation function from imperative_input.py
sys.path.insert(0, str(Path(__file__).parent))
from imperative_input import create_repositories

def concept_to_dict(concept_entry):
    """Manually convert ConceptEntry to dictionary since it doesn't have to_dict method."""
    return {
        "id": concept_entry.id,
        "concept_name": concept_entry.concept_name,
        "type": concept_entry.type,
        "context": concept_entry.context,
        "axis_name": concept_entry.axis_name,
        "natural_name": concept_entry.natural_name,
        "description": concept_entry.description,
        "is_ground_concept": concept_entry.is_ground_concept,
        "is_final_concept": concept_entry.is_final_concept,
        "is_invariant": concept_entry.is_invariant,
        "reference_data": concept_entry.reference_data,
        "reference_axis_names": concept_entry.reference_axis_names
    }

def inference_to_dict(inference_entry):
    """Manually convert InferenceEntry to dictionary."""
    return {
        "id": inference_entry.id,
        "inference_sequence": inference_entry.inference_sequence,
        "concept_to_infer": inference_entry.concept_to_infer.concept_name,
        "flow_info": inference_entry.flow_info,
        "function_concept": inference_entry.function_concept.concept_name if inference_entry.function_concept else None,
        "value_concepts": [c.concept_name for c in inference_entry.value_concepts],
        "context_concepts": [c.concept_name for c in inference_entry.context_concepts],
        "start_without_value": inference_entry.start_without_value,
        "start_without_value_only_once": inference_entry.start_without_value_only_once,
        "start_without_function": inference_entry.start_without_function,
        "start_without_function_only_once": inference_entry.start_without_function_only_once,
        "start_with_support_reference_only": inference_entry.start_with_support_reference_only,
        "start_without_support_reference_only_once": inference_entry.start_without_support_reference_only_once,
        "working_interpretation": inference_entry.working_interpretation
    }

def extract_repos():
    print("Generating repository files...")
    concept_repo, inference_repo = create_repositories()
    
    # Convert to dictionaries
    concepts_data = [concept_to_dict(c) for c in concept_repo.get_all_concepts()]
    inferences_data = [inference_to_dict(i) for i in inference_repo.get_all_inferences()]
    
    # Save to JSON files
    output_dir = Path(__file__).parent
    
    concepts_path = output_dir / "input_concepts.json"
    with open(concepts_path, 'w') as f:
        json.dump(concepts_data, f, indent=2)
    print(f"Saved concepts to {concepts_path}")
    
    inferences_path = output_dir / "input_inferences.json"
    with open(inferences_path, 'w') as f:
        json.dump(inferences_data, f, indent=2)
    print(f"Saved inferences to {inferences_path}")

if __name__ == "__main__":
    extract_repos()
