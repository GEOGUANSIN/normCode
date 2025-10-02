import os
import json
from typing import List, Optional
from fastapi import HTTPException

from schemas.repository_schemas import ConceptEntrySchema, ConceptFileSchema


class ConceptService:
    """Service class for managing concepts."""

    def __init__(self, storage_dir: str):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_filepath(self, name: str) -> str:
        """Helper to get the full path for a concept file."""
        if ".." in name or name.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid name.")
        return os.path.join(self.storage_dir, f"{name}.json")

    def _load_concepts(self, name: str) -> List[ConceptEntrySchema]:
        """Loads a list of concepts from a JSON file."""
        filepath = self._get_filepath(name)
        if not os.path.isfile(filepath):
            # If the file doesn't exist, this repository has no concepts yet.
            return []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return ConceptFileSchema(**data).concepts
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading concepts for {name}: {e}")

    def _save_concepts(self, name: str, concepts: List[ConceptEntrySchema]):
        """Saves a list of concepts to a JSON file."""
        filepath = self._get_filepath(name)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                concept_file = ConceptFileSchema(concepts=concepts)
                json.dump(concept_file.dict(), f, indent=4)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error saving concepts for {name}: {e}")

    def get_concepts(self, name: str) -> List[ConceptEntrySchema]:
        """Retrieves all concepts for a given repository set name."""
        return self._load_concepts(name)

    def get_concept(self, name: str, concept_id: str) -> ConceptEntrySchema:
        """Retrieves a single concept by its ID."""
        concepts = self._load_concepts(name)
        for concept in concepts:
            if concept.id == concept_id:
                return concept
        raise HTTPException(status_code=404, detail=f"Concept with id {concept_id} not found in {name}")

    def add_concept(self, name: str, concept: ConceptEntrySchema) -> ConceptEntrySchema:
        """Adds a new concept."""
        concepts = self._load_concepts(name)
        if any(c.concept_name == concept.concept_name for c in concepts):
            raise HTTPException(status_code=409, detail=f"Concept with name '{concept.concept_name}' already exists.")
        concepts.append(concept)
        self._save_concepts(name, concepts)
        return concept

    def update_concept(self, name: str, concept_id: str, concept_update: ConceptEntrySchema) -> ConceptEntrySchema:
        """Updates an existing concept."""
        concepts = self._load_concepts(name)
        concept_found = False
        for i, concept in enumerate(concepts):
            if concept.id == concept_id:
                concepts[i] = concept_update
                concept_found = True
                break
        
        if not concept_found:
            raise HTTPException(status_code=404, detail=f"Concept with id {concept_id} not found.")
            
        self._save_concepts(name, concepts)
        return concept_update

    def delete_concept(self, name: str, concept_id: str):
        """Deletes a concept."""
        concepts = self._load_concepts(name)
        initial_len = len(concepts)
        concepts = [c for c in concepts if c.id != concept_id]
        
        if len(concepts) == initial_len:
            raise HTTPException(status_code=404, detail=f"Concept with id {concept_id} not found.")
            
        self._save_concepts(name, concepts)
        return {"status": "success", "detail": f"Concept {concept_id} deleted."}

    def get_concept_by_name(self, name: str, concept_name: str) -> ConceptEntrySchema:
        """Retrieves a concept by its name."""
        concepts = self._load_concepts(name)
        for concept in concepts:
            if concept.concept_name == concept_name:
                return concept
        raise HTTPException(status_code=404, detail=f"Concept with name '{concept_name}' not found in {name}")

    def search_concepts(self, name: str, search_term: str) -> List[ConceptEntrySchema]:
        """Searches for concepts by name or description."""
        concepts = self._load_concepts(name)
        search_term_lower = search_term.lower()
        return [
            concept for concept in concepts
            if (search_term_lower in concept.concept_name.lower() or
                (concept.description and search_term_lower in concept.description.lower()))
        ]
