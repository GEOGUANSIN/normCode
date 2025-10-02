import os
import json
import subprocess
import threading
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from fastapi import HTTPException

# Import normcode components
# TODO: Uncomment these when normcode is properly installed and accessible
# from infra._core.concept import ConceptEntry, ConceptRepository
# from infra._core.inference import InferenceEntry, InferenceRepository  
# from infra._orchest.orchestrator import Orchestrator

# Mock classes for MVP testing
class MockConceptEntry:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockConceptRepository:
    def __init__(self, entries):
        self.entries = entries
    def get_concept(self, name):
        return MockConceptEntry(concept_name=name)

class MockInferenceEntry:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockInferenceRepository:
    def __init__(self, entries):
        self.entries = entries

class MockOrchestrator:
    def __init__(self, concept_repo, inference_repo):
        self.concept_repo = concept_repo
        self.inference_repo = inference_repo
    def run(self):
        print("Mock orchestrator running...")
        print("Processing concepts and inferences...")
        print("Simulating normcode execution...")
        print("Execution completed successfully!")

from schemas.repository_schemas import RepositorySetSchema


class NormcodeExecutionService:
    """Service class for executing normcode programs from RepositorySetSchema."""

    def __init__(self, project_root: str, logs_dir: str):
        self.project_root = project_root
        self.logs_dir = logs_dir
        os.makedirs(self.logs_dir, exist_ok=True)

    def _create_normcode_repos_from_schema(self, repo_set: RepositorySetSchema) -> tuple[MockConceptRepository, MockInferenceRepository]:
        """Converts a RepositorySetSchema into MockConceptRepository and MockInferenceRepository objects."""
        concept_entries = []
        for c_schema in repo_set.concepts:
            # Using mock classes for MVP
            concept_entries.append(MockConceptEntry(
                concept_name=c_schema.concept_name,
                concept_type=c_schema.concept_type,
                description=c_schema.description,
                reference_data=c_schema.reference_data,
                reference_axis_names=c_schema.reference_axis_names,
                is_final_concept=c_schema.is_final_concept
            ))
        concept_repo = MockConceptRepository(concept_entries)

        inference_entries = []
        for i_schema in repo_set.inferences:
            # Using mock classes for MVP
            inference_entries.append(MockInferenceEntry(
                concept_to_infer=concept_repo.get_concept(i_schema.concept_to_infer),
                function_concept=concept_repo.get_concept(i_schema.function_concept),
                value_concepts=[concept_repo.get_concept(vc) for vc in i_schema.value_concepts],
                context_concepts=[concept_repo.get_concept(cc) for cc in i_schema.context_concepts] if i_schema.context_concepts else [],
                flow_info=i_schema.flow_info,
                working_interpretation=i_schema.working_interpretation,
                inference_type=i_schema.inference_type,
                condition=i_schema.condition
            ))
        inference_repo = MockInferenceRepository(inference_entries)
        return concept_repo, inference_repo

    def _execute_normcode_in_background(self, repo_set: RepositorySetSchema, log_filepath: str, repo_set_name: str):
        """Internal method to execute normcode and write logs in a separate thread."""
        try:
            concept_repo, inference_repo = self._create_normcode_repos_from_schema(repo_set)
            orchestrator = MockOrchestrator(concept_repo, inference_repo)

            with open(log_filepath, 'w', encoding='utf-8') as log_file:
                # Redirect stdout and stderr to the log file for the orchestrator run
                # This requires temporarily redirecting sys.stdout and sys.stderr
                import sys
                original_stdout = sys.stdout
                original_stderr = sys.stderr
                sys.stdout = log_file
                sys.stderr = log_file
                try:
                    orchestrator.run()
                    with open(log_filepath, 'a', encoding='utf-8') as f:
                        f.write("\n--- Normcode Execution Completed ---\n")
                except Exception as e:
                    with open(log_filepath, 'a', encoding='utf-8') as f:
                        f.write(f"\n--- Normcode Execution Failed: {e} ---\n")
                finally:
                    sys.stdout = original_stdout
                    sys.stderr = original_stderr

        except Exception as e:
            with open(log_filepath, 'a', encoding='utf-8') as log_file:
                log_file.write(f"\nError during background normcode execution setup: {e}\n")
            print(f"Error executing normcode {repo_set_name} in background: {e}")

    def run_repository_set(self, repo_set: RepositorySetSchema) -> str:
        """Starts execution of a RepositorySet in a background thread and returns log file name."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"{repo_set.name}_log_{timestamp}.txt"
        log_filepath = os.path.join(self.logs_dir, log_filename)

        thread = threading.Thread(
            target=self._execute_normcode_in_background,
            args=(repo_set, log_filepath, repo_set.name)
        )
        thread.daemon = True
        thread.start()

        return log_filename

    def get_log_content(self, log_filename: str) -> str:
        """Reads and returns the content of a specified log file."""
        if ".." in log_filename or log_filename.startswith("/"):
            raise HTTPException(status_code=400, detail="Invalid log filename.")

        log_filepath = os.path.join(self.logs_dir, log_filename)

        if not os.path.isfile(log_filepath):
            return "Log file not found or run has not produced output yet."

        try:
            with open(log_filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading log file {log_filename}: {e}")
