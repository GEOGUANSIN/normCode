import pytest
import tempfile
import os
import shutil
import time
import threading
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from ..main import app
from ..schemas.repository_schemas import RepositorySetSchema, RepositorySetData, ConceptEntrySchema, InferenceEntrySchema
from ..services.normcode_execution_service import NormcodeExecutionService
from ..services.repository_service import RepositoryService
from ..services.concept_service import ConceptService
from ..services.inference_service import InferenceService


class TestNormcodeExecutionService:
    """Test cases for NormcodeExecutionService."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.logs_dir = os.path.join(self.temp_dir, "logs")
        self.project_root = self.temp_dir # For simplicity in testing
        self.execution_service = NormcodeExecutionService(self.project_root, self.logs_dir)
        os.makedirs(self.logs_dir, exist_ok=True)

    def teardown_method(self):
        """Clean up after each test."""
        shutil.rmtree(self.temp_dir)

    @pytest.fixture
    def mock_normcode_repos(self):
        """Fixture to mock normcode repository creation and orchestrator run."""
        with (
            patch('app.services.normcode_execution_service.ConceptRepository') as MockConceptRepository,
            patch('app.services.normcode_execution_service.InferenceRepository') as MockInferenceRepository,
            patch('app.services.normcode_execution_service.Orchestrator') as MockOrchestrator
        ):
            mock_concept_repo_instance = MockConceptRepository.return_value
            mock_inference_repo_instance = MockInferenceRepository.return_value
            mock_orchestrator_instance = MockOrchestrator.return_value

            yield (
                MockConceptRepository,
                MockInferenceRepository,
                MockOrchestrator,
                mock_concept_repo_instance,
                mock_inference_repo_instance,
                mock_orchestrator_instance
            )

    def test_run_repository_set(self, mock_normcode_repos):
        """Test running a repository set and capturing logs."""
        (MockConceptRepository, MockInferenceRepository, MockOrchestrator, 
         mock_concept_repo_instance, mock_inference_repo_instance, mock_orchestrator_instance) = mock_normcode_repos

        # Mock the run() method to write some content to stdout
        def mock_orchestrator_run():
            print("Orchestrator output line 1")
            print("Orchestrator output line 2")
        mock_orchestrator_instance.run.side_effect = mock_orchestrator_run

        concept = ConceptEntrySchema(concept_name="test_concept", concept_type="ground")
        inference = InferenceEntrySchema(
            concept_to_infer="test_concept",
            function_concept="func_concept",
            value_concepts=["val_concept"]
        )
        repo_set = RepositorySetSchema(name="test_run_repo", concepts=[concept], inferences=[inference])

        log_filename = self.execution_service.run_repository_set(repo_set)
        assert log_filename.startswith("test_run_repo_log_")
        assert log_filename.endswith(".txt")

        # Wait a bit for the background thread to finish
        # In a real scenario, you'd have a more robust way to signal completion
        time.sleep(1)

        log_content = self.execution_service.get_log_content(log_filename)
        assert "Orchestrator output line 1" in log_content
        assert "Orchestrator output line 2" in log_content
        assert "--- Normcode Execution Completed ---" in log_content

    def test_get_log_content_not_found(self):
        """Test getting content for a non-existent log file."""
        content = self.execution_service.get_log_content("nonexistent_log.txt")
        assert "Log file not found or run has not produced output yet." in content

    def test_get_log_content_path_traversal(self):
        """Test that path traversal is prevented for log filenames."""
        with pytest.raises(HTTPException) as exc_info:
            self.execution_service.get_log_content("../malicious.txt")
        assert exc_info.value.status_code == 400


class TestRepositoryRouter:
    """Test cases for repository router endpoints."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_storage_dir = os.path.join(self.temp_dir, "data", "repositories")
        self.concept_storage_dir = os.path.join(self.temp_dir, "data", "concepts")
        self.inference_storage_dir = os.path.join(self.temp_dir, "data", "inferences")
        self.logs_dir = os.path.join(self.temp_dir, "data", "logs")
        os.makedirs(self.repo_storage_dir, exist_ok=True)
        os.makedirs(self.concept_storage_dir, exist_ok=True)
        os.makedirs(self.inference_storage_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        # Patch dependencies for testing
        self.patcher_repo_service = patch('app.routers.repository_router.get_repository_service')
        self.mock_get_repo_service = self.patcher_repo_service.start()
        
        self.patcher_concept_service = patch('app.routers.repository_router.get_concept_service')
        self.mock_get_concept_service = self.patcher_concept_service.start()

        self.patcher_inference_service = patch('app.routers.repository_router.get_inference_service')
        self.mock_get_inference_service = self.patcher_inference_service.start()

        self.concept_service_instance = ConceptService(self.concept_storage_dir)
        self.inference_service_instance = InferenceService(self.inference_storage_dir)
        self.repo_service_instance = RepositoryService(
            self.repo_storage_dir, self.concept_service_instance, self.inference_service_instance
        )

        self.mock_get_repo_service.return_value = self.repo_service_instance
        self.mock_get_concept_service.return_value = self.concept_service_instance
        self.mock_get_inference_service.return_value = self.inference_service_instance

        self.patcher_exec_service = patch('app.routers.repository_router.get_normcode_execution_service')
        self.mock_get_exec_service = self.patcher_exec_service.start()
        self.mock_get_exec_service.return_value = NormcodeExecutionService(self.temp_dir, self.logs_dir)

        self.client = TestClient(app)

    def teardown_method(self):
        """Clean up after each test."""
        self.patcher_repo_service.stop()
        self.patcher_concept_service.stop()
        self.patcher_inference_service.stop()
        self.patcher_exec_service.stop()
        shutil.rmtree(self.temp_dir)

    def test_list_repository_sets_endpoint(self):
        """Test the list repository sets endpoint."""
        repo_set_def = RepositorySetSchema(name="test_repo_list", concepts=[], inferences=[])
        self.repo_service_instance.create_repository_set(repo_set_def)

        response = self.client.get("/api/repositories/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['name'] == "test_repo_list"

    def test_create_repository_set_endpoint(self):
        """Test creating a repository set via the endpoint."""
        repo_set_def = RepositorySetSchema(name="test_create_repo", concepts=[], inferences=[])

        response = self.client.post("/api/repositories/", json=repo_set_def.dict())
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_create_repo"

        # Verify it was actually saved
        loaded_repo = self.repo_service_instance.get_repository_set("test_create_repo")
        assert loaded_repo.name == "test_create_repo"

    def test_get_repository_set_endpoint(self):
        """Test retrieving a repository set via the endpoint."""
        repo_set_def = RepositorySetSchema(name="test_get_repo", concepts=['c1'], inferences=['i1'])
        self.repo_service_instance.create_repository_set(repo_set_def)

        response = self.client.get("/api/repositories/test_get_repo")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_get_repo"
        assert data["concepts"] == ['c1']
    
    def test_get_repository_set_data_endpoint(self):
        """Test retrieving full repository set data via the endpoint."""
        concept = ConceptEntrySchema(concept_name="get_concept", concept_type="ground")
        self.concept_service_instance.add_concept("test_get_data_repo", concept)
        
        repo_set_def = RepositorySetSchema(name="test_get_data_repo", concepts=[concept.id], inferences=[])
        self.repo_service_instance.create_repository_set(repo_set_def)

        response = self.client.get("/api/repositories/test_get_data_repo/data")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test_get_data_repo"
        assert data["concepts"][0]["concept_name"] == "get_concept"

    def test_run_repository_set_endpoint(self, mock_normcode_repos):
        """Test running a repository set via the endpoint."""
        (MockConceptRepository, MockInferenceRepository, MockOrchestrator, 
         mock_concept_repo_instance, mock_inference_repo_instance, mock_orchestrator_instance) = mock_normcode_repos

        def mock_orchestrator_run():
            print("Endpoint orchestrator output")
        mock_orchestrator_instance.run.side_effect = mock_orchestrator_run

        repo_set_def = RepositorySetSchema(name="test_run_endpoint", concepts=[], inferences=[])
        self.repo_service_instance.create_repository_set(repo_set_def)

        response = self.client.post("/api/repositories/run", json={'repository_set_name': 'test_run_endpoint'})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
        assert data["log_file"].startswith("test_run_endpoint_log_")

        time.sleep(1) # Give background thread a moment
        log_content = self.mock_get_exec_service.return_value.get_log_content(data["log_file"])
        assert "Endpoint orchestrator output" in log_content

    def test_get_normcode_logs_endpoint(self):
        """Test retrieving normcode logs via the endpoint."""
        # Simulate a log file being created by the execution service
        log_filename = "test_log_file.txt"
        log_filepath = os.path.join(self.logs_dir, log_filename)
        with open(log_filepath, 'w') as f:
            f.write("Simulated log content.")

        response = self.client.get(f"/api/repositories/logs/{log_filename}")
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Simulated log content."
