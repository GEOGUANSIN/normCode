import os
import json
from typing import List, Optional
from fastapi import HTTPException

from schemas.repository_schemas import RepositorySetSchema, RepositorySetData
from .concept_service import ConceptService
from .inference_service import InferenceService


class RepositoryService:
    """Service class for managing repository sets."""

    def __init__(self, storage_dir: str, concept_service: ConceptService, inference_service: InferenceService):
        self.storage_dir = storage_dir
        self.concept_service = concept_service
        self.inference_service = inference_service
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_filepath(self, name: str) -> str:
        """Helper to get the full path for a repository set file."""
        # Security: Prevent path traversal attacks
        if ".." in name or name.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid repository set name.")
        return os.path.join(self.storage_dir, f"{name}.json")

    def get_all_repository_sets(self) -> List[RepositorySetSchema]:
        """Lists all available repository sets."""
        repo_sets = []
        for filename in os.listdir(self.storage_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.storage_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    repo_sets.append(RepositorySetSchema(**data))
                except Exception as e:
                    # Optionally log the error or handle it more gracefully
                    print(f"Error loading repository set from {filename}: {e}")
        return repo_sets

    def get_repository_set(self, name: str) -> RepositorySetSchema:
        """Retrieves a single repository set by name."""
        filepath = self._get_filepath(name)
        if not os.path.isfile(filepath):
            raise HTTPException(status_code=404, detail=f"Repository set not found: {name}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return RepositorySetSchema(**data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading repository set {name}: {e}")

    def get_repository_set_data(self, name: str) -> RepositorySetData:
        """Retrieves the full data for a repository set, including concepts and inferences."""
        repo_set_definition = self.get_repository_set(name)
        
        # In a real application, you might want to be more efficient here,
        # but for simplicity, we'll load all and then filter.
        all_concepts = self.concept_service.get_concepts(name)
        all_inferences = self.inference_service.get_inferences(name)

        concepts = [c for c in all_concepts if c.id in repo_set_definition.concepts]
        inferences = [i for i in all_inferences if i.id in repo_set_definition.inferences]

        return RepositorySetData(
            name=name,
            concepts=concepts,
            inferences=inferences
        )

    def create_repository_set(self, repo_set: RepositorySetSchema) -> RepositorySetSchema:
        """Creates a new repository set."""
        filepath = self._get_filepath(repo_set.name)
        if os.path.exists(filepath):
            raise HTTPException(status_code=409, detail=f"Repository set with name '{repo_set.name}' already exists.")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(repo_set.dict(), f, indent=4)
            # Also create empty concept and inference files
            self.concept_service._save_concepts(repo_set.name, [])
            self.inference_service._save_inferences(repo_set.name, [])
            return repo_set
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error creating repository set {repo_set.name}: {e}")

    def delete_repository_set(self, name: str):
        """Deletes a repository set and its associated concepts and inferences."""
        filepath = self._get_filepath(name)
        if not os.path.isfile(filepath):
            raise HTTPException(status_code=404, detail=f"Repository set not found: {name}")
        try:
            os.remove(filepath)
            # Delete associated concepts and inferences files
            concept_filepath = self.concept_service._get_filepath(name)
            if os.path.exists(concept_filepath):
                os.remove(concept_filepath)
            
            inference_filepath = self.inference_service._get_filepath(name)
            if os.path.exists(inference_filepath):
                os.remove(inference_filepath)
                
            return {"status": "success", "detail": f"Repository set '{name}' deleted."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting repository set {name}: {e}")
    
    def get_flow(self, name: str):
        """Retrieves the flow data for a specific repository set."""
        import json
        flow_file_path = os.path.join(self.storage_dir, f"{name}_flow.json")
        
        # Return empty flow if file doesn't exist
        if not os.path.exists(flow_file_path):
            return {"nodes": [], "edges": []}
        
        try:
            with open(flow_file_path, 'r') as f:
                flow_data = json.load(f)
            return flow_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading flow data: {e}")
    
    def save_flow(self, name: str, flow_data):
        """Saves the flow data for a specific repository set."""
        import json
        
        # Verify repository exists
        repo_file_path = os.path.join(self.storage_dir, f"{name}.json")
        if not os.path.exists(repo_file_path):
            raise HTTPException(status_code=404, detail=f"Repository set '{name}' not found")
        
        flow_file_path = os.path.join(self.storage_dir, f"{name}_flow.json")
        
        try:
            # Convert Pydantic model to dict if needed
            if hasattr(flow_data, 'dict'):
                flow_dict = flow_data.dict()
            else:
                flow_dict = flow_data
            
            with open(flow_file_path, 'w') as f:
                json.dump(flow_dict, f, indent=2)
            
            return flow_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving flow data: {e}")