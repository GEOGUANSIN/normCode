import pytest
import tempfile
import os
import json
from fastapi import HTTPException

from ..schemas.repository_schemas import (
    ConceptEntrySchema,
    InferenceEntrySchema,
    RepositorySetSchema,
    RepositorySetData
)
from ..services.repository_service import RepositoryService
from ..services.concept_service import ConceptService
from ..services.inference_service import InferenceService


class TestRepositoryService:
    """Test cases for RepositoryService."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = os.path.join(self.temp_dir, "data", "repositories")
        self.concept_dir = os.path.join(self.temp_dir, "data", "concepts")
        self.inference_dir = os.path.join(self.temp_dir, "data", "inferences")
        
        os.makedirs(self.repo_dir)
        os.makedirs(self.concept_dir)
        os.makedirs(self.inference_dir)

        self.concept_service = ConceptService(self.concept_dir)
        self.inference_service = InferenceService(self.inference_dir)
        self.repo_service = RepositoryService(self.repo_dir, self.concept_service, self.inference_service)

    def teardown_method(self):
        """Clean up after each test."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_get_all_repository_sets_empty(self):
        """Test listing repository sets in an empty directory."""
        repo_sets = self.repo_service.get_all_repository_sets()
        assert repo_sets == []

    def test_create_and_get_repository_set(self):
        """Test creating and retrieving a repository set definition."""
        repo_set_def = RepositorySetSchema(name="my_test_repo", concepts=[], inferences=[])
        
        created_repo = self.repo_service.create_repository_set(repo_set_def)
        assert created_repo.name == "my_test_repo"
        assert os.path.exists(os.path.join(self.repo_dir, "my_test_repo.json"))
        assert os.path.exists(os.path.join(self.concept_dir, "my_test_repo.json"))
        assert os.path.exists(os.path.join(self.inference_dir, "my_test_repo.json"))

        retrieved_repo = self.repo_service.get_repository_set("my_test_repo")
        assert retrieved_repo.name == "my_test_repo"

    def test_get_repository_set_data(self):
        """Test retrieving the full data for a repository set."""
        concept1 = ConceptEntrySchema(concept_name="test_concept_1", concept_type="ground")
        concept2 = ConceptEntrySchema(concept_name="test_concept_2", concept_type="ground")
        inference1 = InferenceEntrySchema(
            concept_to_infer="test_concept_1",
            function_concept="func_concept",
            value_concepts=["val_concept"]
        )
        
        # Manually add concepts and inferences
        self.concept_service.add_concept("my_test_repo", concept1)
        self.concept_service.add_concept("my_test_repo", concept2)
        self.inference_service.add_inference("my_test_repo", inference1)

        # Create the repo set definition that links to them by ID
        repo_set_def = RepositorySetSchema(
            name="my_test_repo",
            concepts=[concept1.id, concept2.id],
            inferences=[inference1.id]
        )
        self.repo_service.create_repository_set(repo_set_def)

        # Get the full data
        repo_data = self.repo_service.get_repository_set_data("my_test_repo")
        assert repo_data.name == "my_test_repo"
        assert len(repo_data.concepts) == 2
        assert len(repo_data.inferences) == 1
        assert repo_data.concepts[0].id == concept1.id
        assert repo_data.inferences[0].id == inference1.id

    def test_get_nonexistent_repository_set(self):
        """Test loading a non-existent repository set."""
        with pytest.raises(HTTPException) as exc_info:
            self.repo_service.get_repository_set("nonexistent_repo")
        assert exc_info.value.status_code == 404

    def test_delete_repository_set(self):
        """Test deleting a repository set."""
        repo_set_def = RepositorySetSchema(name="to_delete", concepts=[], inferences=[])
        self.repo_service.create_repository_set(repo_set_def)
        
        assert os.path.exists(os.path.join(self.repo_dir, "to_delete.json"))
        assert os.path.exists(os.path.join(self.concept_dir, "to_delete.json"))
        assert os.path.exists(os.path.join(self.inference_dir, "to_delete.json"))

        self.repo_service.delete_repository_set("to_delete")

        assert not os.path.exists(os.path.join(self.repo_dir, "to_delete.json"))
        assert not os.path.exists(os.path.join(self.concept_dir, "to_delete.json"))
        assert not os.path.exists(os.path.join(self.inference_dir, "to_delete.json"))
        
        with pytest.raises(HTTPException):
            self.repo_service.get_repository_set("to_delete")

    def test_delete_nonexistent_repository_set(self):
        """Test deleting a non-existent repository set."""
        with pytest.raises(HTTPException) as exc_info:
            self.repo_service.delete_repository_set("nonexistent_delete")
        assert exc_info.value.status_code == 404

    def test_path_traversal_prevention(self):
        """Test that path traversal is prevented for filenames."""
        with pytest.raises(HTTPException) as exc_info:
            self.repo_service._get_filepath("../malicious")
        assert exc_info.value.status_code == 400
