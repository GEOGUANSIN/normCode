import os
import json
import logging
import subprocess
import threading
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from fastapi import HTTPException

# Import normcode components
from infra._orchest._repo import ConceptEntry, ConceptRepo, InferenceEntry, InferenceRepo
from infra._orchest._orchestrator import Orchestrator
from schemas.repository_schemas import RepositorySetData


class NormcodeExecutionService:
    """Service class for executing normcode programs from RepositorySetData."""

    def __init__(self, project_root: str, logs_dir: str):
        self.project_root = project_root
        self.logs_dir = logs_dir
        os.makedirs(self.logs_dir, exist_ok=True)

    def _create_normcode_repos_from_schema(self, repo_set: RepositorySetData) -> tuple[ConceptRepo, InferenceRepo]:
        """Converts a RepositorySetData into ConceptRepo and InferenceRepo objects."""
        concept_entries_map: Dict[str, ConceptEntry] = {}
        for c_schema in repo_set.concepts:
            entry = ConceptEntry(
                id=c_schema.id,
                concept_name=c_schema.concept_name,
                type=c_schema.type,
                context=c_schema.context,
                axis_name=c_schema.axis_name,
                natural_name=c_schema.natural_name,
                description=c_schema.description,
                reference_data=c_schema.reference_data,
                reference_axis_names=c_schema.reference_axis_names,
                is_final_concept=c_schema.is_final_concept,
                is_ground_concept=c_schema.is_ground_concept,
                is_invariant=c_schema.is_invariant
            )
            concept_entries_map[entry.concept_name] = entry
        
        concept_entries = list(concept_entries_map.values())
        concept_repo = ConceptRepo(concept_entries)

        inference_entries = []
        for i_schema in repo_set.inferences:
            concept_to_infer = concept_entries_map.get(i_schema.concept_to_infer)
            if not concept_to_infer:
                raise ValueError(f"Concept '{i_schema.concept_to_infer}' not found for inference.")

            function_concept = concept_entries_map.get(i_schema.function_concept)
            if not function_concept:
                raise ValueError(f"Function concept '{i_schema.function_concept}' not found for inference.")
            
            value_concepts = [concept_entries_map.get(vc) for vc in i_schema.value_concepts]
            if not all(value_concepts):
                raise ValueError(f"One or more value concepts not found for inference.")

            context_concepts = []
            if i_schema.context_concepts:
                context_concepts = [concept_entries_map.get(cc) for cc in i_schema.context_concepts]
                if not all(context_concepts):
                    raise ValueError(f"One or more context concepts not found for inference.")
            
            inference_entries.append(InferenceEntry(
                id=i_schema.id,
                inference_sequence=i_schema.inference_sequence,
                concept_to_infer=concept_to_infer,
                function_concept=function_concept,
                value_concepts=value_concepts,
                context_concepts=context_concepts,
                flow_info=i_schema.flow_info,
                working_interpretation=i_schema.working_interpretation,
                start_without_value=i_schema.start_without_value,
                start_without_value_only_once=i_schema.start_without_value_only_once,
                start_without_function=i_schema.start_without_function,
                start_without_function_only_once=i_schema.start_without_function_only_once,
                start_with_support_reference_only=i_schema.start_with_support_reference_only,
                # 'condition' and 'inference_type' from schema are not directly in InferenceEntry,
                # might be part of working_interpretation or handled differently.
            ))
        inference_repo = InferenceRepo(inference_entries)
        return concept_repo, inference_repo

    def _execute_normcode_in_background(self, repo_set: RepositorySetData, log_filepath: str, repo_set_name: str):
        """Internal method to execute normcode and write logs in a separate thread."""
        root_logger = logging.getLogger()
        log_formatter = logging.Formatter('[%(levelname)s] %(message)s - %(asctime)s - root')
        file_handler = logging.FileHandler(log_filepath, mode='w', encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)

        try:
            concept_repo, inference_repo = self._create_normcode_repos_from_schema(repo_set)
            orchestrator = Orchestrator(concept_repo, inference_repo, max_cycles=1000)
            orchestrator.run()

            with open(log_filepath, 'a', encoding='utf-8') as f:
                f.write("\n--- Normcode Execution Completed ---\n")

        except Exception as e:
            root_logger.error(f"Error during background normcode execution: {e}", exc_info=True)
            with open(log_filepath, 'a', encoding='utf-8') as f:
                f.write(f"\n--- Normcode Execution Failed: {e} ---\n")

        finally:
            root_logger.removeHandler(file_handler)

    def run_repository_set(self, repo_set: RepositorySetData) -> str:
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
