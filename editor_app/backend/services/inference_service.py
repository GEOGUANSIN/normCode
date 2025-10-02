import os
import json
from typing import List, Optional
from fastapi import HTTPException

from schemas.repository_schemas import InferenceEntrySchema, InferenceFileSchema


class InferenceService:
    """Service class for managing inferences."""

    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_filepath(self, name: str) -> str:
        """Helper to get the full path for an inference file."""
        if ".." in name or name.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid name.")
        return os.path.join(self.storage_dir, f"{name}.json")

    def _load_inferences(self, name: str) -> List[InferenceEntrySchema]:
        """Loads a list of inferences from a JSON file."""
        filepath = self._get_filepath(name)
        if not os.path.isfile(filepath):
            return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return InferenceFileSchema(**data).inferences
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading inferences for {name}: {e}")

    def _save_inferences(self, name: str, inferences: List[InferenceEntrySchema]):
        """Saves a list of inferences to a JSON file."""
        filepath = self._get_filepath(name)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                inference_file = InferenceFileSchema(inferences=inferences)
                json.dump(inference_file.dict(), f, indent=4)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving inferences for {name}: {e}")

    def get_inferences(self, name: str) -> List[InferenceEntrySchema]:
        """Retrieves all inferences for a given repository set name."""
        return self._load_inferences(name)

    def get_inference(self, name: str, inference_id: str) -> InferenceEntrySchema:
        """Retrieves a single inference by its ID."""
        inferences = self._load_inferences(name)
        for inference in inferences:
            if inference.id == inference_id:
                return inference
        raise HTTPException(status_code=404, detail=f"Inference with id {inference_id} not found in {name}")

    def add_inference(self, name: str, inference: InferenceEntrySchema) -> InferenceEntrySchema:
        """Adds a new inference."""
        inferences = self._load_inferences(name)
        inferences.append(inference)
        self._save_inferences(name, inferences)
        return inference

    def update_inference(self, name: str, inference_id: str, inference_update: InferenceEntrySchema) -> InferenceEntrySchema:
        """Updates an existing inference."""
        inferences = self._load_inferences(name)
        inference_found = False
        for i, inference in enumerate(inferences):
            if inference.id == inference_id:
                inferences[i] = inference_update
                inference_found = True
                break
        
        if not inference_found:
            raise HTTPException(status_code=404, detail=f"Inference with id {inference_id} not found.")
            
        self._save_inferences(name, inferences)
        return inference_update

    def delete_inference(self, name: str, inference_id: str):
        """Deletes an inference."""
        inferences = self._load_inferences(name)
        initial_len = len(inferences)
        inferences = [inf for inf in inferences if inf.id != inference_id]
        
        if len(inferences) == initial_len:
            raise HTTPException(status_code=404, detail=f"Inference with id {inference_id} not found.")
            
        self._save_inferences(name, inferences)
        return {"status": "success", "detail": f"Inference {inference_id} deleted."}

    def get_inferences_by_flow_index(self, name: str, flow_index: str) -> List[InferenceEntrySchema]:
        """Retrieves all inferences with a specific flow index."""
        inferences = self._load_inferences(name)
        return [
            inference for inference in inferences
            if inference.flow_info and inference.flow_info.get('flow_index') == flow_index
        ]

    def get_inferences_by_sequence(self, name: str, sequence: str) -> List[InferenceEntrySchema]:
        """Retrieves all inferences with a specific sequence type."""
        inferences = self._load_inferences(name)
        return [
            inference for inference in inferences
            if inference.inference_sequence == sequence
        ]

    def search_inferences(self, name: str, search_term: str) -> List[InferenceEntrySchema]:
        """Searches for inferences by concept names or flow info."""
        inferences = self._load_inferences(name)
        search_term_lower = search_term.lower()
        return [
            inference for inference in inferences
            if (search_term_lower in inference.concept_to_infer.lower() or
                search_term_lower in inference.function_concept.lower() or
                any(search_term_lower in vc.lower() for vc in inference.value_concepts) or
                (inference.context_concepts and any(search_term_lower in cc.lower() for cc in inference.context_concepts)))
        ]
