from infra._orchest._repo import ConceptRepo, InferenceRepo
from infra._orchest._orchestrator import Orchestrator
from infra._agent._body import Body
import os
import json
from pathlib import Path

def create_repositories_from_files():
    with open('concept_repo.json', 'r') as f:
        concept_data = json.load(f)
    concept_repo = ConceptRepo.from_json_list(concept_data)

    with open('inference_repo.json', 'r') as f:
        inference_data = json.load(f)
    inference_repo = InferenceRepo.from_json_list(inference_data, concept_repo)
    
    return concept_repo, inference_repo

if __name__ == "__main__":
    # 1. Prepare file system
    Path("./prompts").mkdir(exist_ok=True)

    # 2. Build repositories from the generated JSON files
    concept_repo, inference_repo = create_repositories_from_files()

    # 3. Construct a Body for imperatives/judgements
    # Assuming 'qwen-plus' is a valid LLM name in the user's environment.
    body = Body(llm_name="qwen-plus", base_dir=Path("./prompts"))

    # 4. Construct and run the orchestrator
    orchestrator = Orchestrator(
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        body=body,
        max_cycles=300,
    )
    final_concepts = orchestrator.run()

    # 5. Inspect and log final concepts
    print("Execution finished. Final concepts:")
    for final_concept_entry in final_concepts:
        if final_concept_entry and final_concept_entry.concept.reference:
            ref_tensor = final_concept_entry.concept.reference.tensor
            print(f"Final concept '{final_concept_entry.concept_name}': {ref_tensor}")
        else:
            print(f"No reference found for final concept '{final_concept_entry.concept_name}'.")
