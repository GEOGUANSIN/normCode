import os
import json
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from uuid import uuid4

from schemas.repository_schemas import RepositorySetSchema, RepositorySetData
from schemas.concept_schemas import ConceptEntrySchema
from schemas.inference_schemas import InferenceEntrySchema
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
        repo_dir = os.path.join(self.storage_dir, name)
        return os.path.join(repo_dir, f"{name}.json")

    def get_all_repository_sets(self) -> List[RepositorySetSchema]:
        """Lists all available repository sets."""
        repo_sets = []
        for dirname in os.listdir(self.storage_dir):
            dirpath = os.path.join(self.storage_dir, dirname)
            if os.path.isdir(dirpath):
                filepath = os.path.join(dirpath, f"{dirname}.json")
                if os.path.isfile(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        repo_sets.append(RepositorySetSchema(**data))
                    except Exception as e:
                        print(f"Error loading repository set from {filepath}: {e}")
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
        
        repo_dir = os.path.dirname(filepath)
        os.makedirs(repo_dir, exist_ok=True)

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
        import shutil

        repo_dir = os.path.join(self.storage_dir, name)
        if not os.path.isdir(repo_dir):
            raise HTTPException(status_code=404, detail=f"Repository set not found: {name}")
        
        try:
            shutil.rmtree(repo_dir)
            return {"status": "success", "detail": f"Repository set '{name}' deleted."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting repository set {name}: {e}")

    def add_global_concept_to_repository(self, name: str, global_concept_id: str,
                                         reference_data: Optional[any] = None,
                                         reference_axis_names: Optional[List[str]] = None,
                                         is_ground_concept: bool = False,
                                         is_final_concept: bool = False,
                                         is_invariant: bool = False) -> ConceptEntrySchema:
        """Adds a copy of a global concept to a repository with new reference data."""
        # 1. Get the global concept
        global_concept = self.concept_service.get_concept("_global", global_concept_id)

        # 2. Create a copy and update it
        new_concept = global_concept.copy(deep=True)
        new_concept.id = str(uuid4())  # Assign a new ID
        new_concept.reference_data = reference_data
        new_concept.reference_axis_names = reference_axis_names
        new_concept.is_ground_concept = is_ground_concept
        new_concept.is_final_concept = is_final_concept
        new_concept.is_invariant = is_invariant

        # 3. Add the new concept to the repository's concept list
        self.concept_service.add_concept(name, new_concept)

        # 4. Update the repository set to include the new concept ID
        repo_set = self.get_repository_set(name)
        if new_concept.id not in repo_set.concepts:
            repo_set.concepts.append(new_concept.id)
            filepath = self._get_filepath(name)
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(repo_set.dict(), f, indent=4)
            except Exception as e:
                # Rollback adding the concept if updating the repo set fails
                concepts = self.concept_service.get_concepts(name)
                concepts = [c for c in concepts if c.id != new_concept.id]
                self.concept_service._save_concepts(name, concepts)
                raise HTTPException(status_code=500, detail=f"Error updating repository set {name}: {e}")

        return new_concept

    def add_global_inference_to_repository(
        self,
        name: str,
        global_inference_id: str,
        flow_info: Optional[Dict[str, Any]],
        working_interpretation: Optional[Dict[str, Any]],
        start_without_value: bool,
        start_without_value_only_once: bool,
        start_without_function: bool,
        start_without_function_only_once: bool,
        start_with_support_reference_only: bool
    ) -> InferenceEntrySchema:
        """Adds a copy of a global inference to a repository with new data."""
        global_inference = self.inference_service.get_inference("_global", global_inference_id)

        new_inference = global_inference.copy(deep=True)
        new_inference.id = str(uuid4())
        new_inference.flow_info = flow_info
        new_inference.working_interpretation = working_interpretation
        new_inference.start_without_value = start_without_value
        new_inference.start_without_value_only_once = start_without_value_only_once
        new_inference.start_without_function = start_without_function
        new_inference.start_without_function_only_once = start_without_function_only_once
        new_inference.start_with_support_reference_only = start_with_support_reference_only

        self.inference_service.add_inference(name, new_inference)

        repo_set = self.get_repository_set(name)
        if new_inference.id not in repo_set.inferences:
            repo_set.inferences.append(new_inference.id)
            filepath = self._get_filepath(name)
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(repo_set.dict(), f, indent=4)
            except Exception as e:
                inferences = self.inference_service.get_inferences(name)
                inferences = [i for i in inferences if i.id != new_inference.id]
                self.inference_service._save_inferences(name, inferences)
                raise HTTPException(status_code=500, detail=f"Error updating repository set {name}: {e}")

        return new_inference

    def get_flow(self, name: str):
        """Retrieves the flow data by reconstructing it from inference objects."""
        # Verify repository exists to prevent errors on new repos
        repo_file_path = self._get_filepath(name)
        if not os.path.exists(repo_file_path):
            return {"nodes": [], "edges": []}

        all_inferences = self.inference_service.get_inferences(name)

        # Filter inferences that are part of the flow
        flow_inferences = [inf for inf in all_inferences if inf.flow_info and inf.flow_info.get('flow_index')]

        # Sort inferences based on the flow index
        def sort_key(inference):
            # Convert index string like "1.2.1" to a tuple of integers for correct sorting
            return tuple(map(int, (inference.flow_info['flow_index'].split('.'))))

        flow_inferences.sort(key=sort_key)

        # Reconstruct the nodes for the FlowData schema
        nodes = []
        for inference in flow_inferences:
            # The frontend expects a unique ID for each node in the flow editor UI
            node_id = f"inference-{inference.id}-{inference.flow_info.get('flow_index')}"
            nodes.append({
                "id": node_id,
                "type": "inference",
                "position": {"x": 0, "y": 0},  # Not used, but required by schema
                "data": inference.dict()  # Send the full inference data back
            })

        return {"nodes": nodes, "edges": []}

    def save_flow(self, name: str, flow_data):
        """Saves the flow data by merging it into the individual inference objects."""
        # Verify repository exists
        repo_file_path = self._get_filepath(name)
        if not os.path.exists(repo_file_path):
            raise HTTPException(status_code=404, detail=f"Repository set '{name}' not found")

        all_inferences = self.inference_service._load_inferences(name)
        inferences_dict = {inf.id: inf for inf in all_inferences}

        # Clear existing flow_info from all inferences for this repository
        for inf in all_inferences:
            inf.flow_info = None

        flow_nodes = flow_data.dict().get('nodes', [])

        for node in flow_nodes:
            inference_id = node.get('data', {}).get('id')
            if inference_id in inferences_dict:
                inference = inferences_dict[inference_id]
                # The frontend will now pass flow_info inside the data object
                flow_info = node.get('data', {}).get('flow_info')
                if flow_info:
                    inference.flow_info = flow_info

        # Save the updated inferences
        try:
            self.inference_service._save_inferences(name, all_inferences)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving flow data to inferences: {e}")

        # Clean up the old _flow.json file if it exists
        flow_file_path = os.path.join(self.storage_dir, f"{name}_flow.json")
        if os.path.exists(flow_file_path):
            try:
                os.remove(flow_file_path)
            except OSError as e:
                # Log this error but don't fail the request because of it
                print(f"Error removing old flow file {flow_file_path}: {e}")

        return flow_data