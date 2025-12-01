"""
Orchestration execution logic for NormCode Orchestrator Streamlit App.
"""

import streamlit as st
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import uuid

from infra import ConceptRepo, InferenceRepo, Orchestrator
from infra._orchest._db import OrchestratorDB
from infra._agent._body import Body
from tools import StreamlitInputTool, StreamlitFileSystemTool

from core.config import APP_VERSION
from core.file_utils import save_file_paths_for_run
from core.verification import verify_repository_files


async def create_orchestrator(
    concept_repo: ConceptRepo,
    inference_repo: InferenceRepo,
    llm_model: str,
    max_cycles: int,
    base_dir: str,
    db_path: str,
    resume_option: str,
    run_id_to_resume: Optional[str],
    custom_run_id: Optional[str],
    new_run_id: Optional[str],
    reconciliation_mode: Optional[str],
    concepts_file,
    loaded_concepts,
    inferences_file,
    loaded_inferences,
    inputs_file,
    loaded_inputs,
    base_dir_option: str,
    verify_files: bool
) -> Tuple[Orchestrator, Dict[str, Any]]:
    """
    Create or load an orchestrator based on execution mode.
    
    Returns:
        Tuple of (orchestrator, config_dict)
    """
    # Initialize Body
    body = Body(llm_name=llm_model, base_dir=base_dir)
    
    # Inject Streamlit-native user input tool for human-in-the-loop
    body.user_input = StreamlitInputTool()
    
    # Inject Streamlit-native file system tool
    body.file_system = StreamlitFileSystemTool(base_dir=base_dir)
    
    st.info(f"📂 Base directory: `{base_dir}`")
    st.info(f"🤝 Human-in-the-loop mode enabled")
    
    if resume_option == "Fresh Run":
        return await _create_fresh_run(
            concept_repo, inference_repo, body, max_cycles, db_path,
            custom_run_id, concepts_file, loaded_concepts, inferences_file,
            loaded_inferences, inputs_file, loaded_inputs, llm_model,
            base_dir, base_dir_option, verify_files
        )
    
    elif resume_option == "Fork from Checkpoint":
        return await _create_fork_run(
            concept_repo, inference_repo, body, max_cycles, db_path,
            run_id_to_resume, new_run_id, reconciliation_mode,
            concepts_file, loaded_concepts, inferences_file,
            loaded_inferences, inputs_file, loaded_inputs, llm_model,
            base_dir, base_dir_option, verify_files
        )
    
    else:  # Resume from Checkpoint
        return await _create_resume_run(
            concept_repo, inference_repo, body, max_cycles, db_path,
            run_id_to_resume, reconciliation_mode, concepts_file,
            loaded_concepts, inferences_file, loaded_inferences,
            inputs_file, loaded_inputs, llm_model, base_dir,
            base_dir_option, verify_files
        )


async def _create_fresh_run(
    concept_repo, inference_repo, body, max_cycles, db_path,
    custom_run_id, concepts_file, loaded_concepts, inferences_file,
    loaded_inferences, inputs_file, loaded_inputs, llm_model,
    base_dir, base_dir_option, verify_files
):
    """Create a fresh orchestration run."""
    # Use custom run_id if provided, otherwise auto-generate
    run_id_for_fresh_run = custom_run_id.strip() if custom_run_id and custom_run_id.strip() else None
    
    # Offload Orchestrator initialization (DB connection) to thread
    orchestrator = await asyncio.to_thread(
        Orchestrator,
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        body=body,
        max_cycles=max_cycles,
        db_path=db_path,
        run_id=run_id_for_fresh_run
    )
    
    if run_id_for_fresh_run:
        st.info(f"🆕 Started fresh run with custom ID: `{orchestrator.run_id}`")
    else:
        st.info(f"🆕 Started fresh run: `{orchestrator.run_id}`")
    
    # Save repository files to disk and get their paths
    saved_file_paths = await asyncio.to_thread(
        save_file_paths_for_run,
        orchestrator, concepts_file, loaded_concepts, inferences_file,
        loaded_inferences, inputs_file, loaded_inputs
    )
    
    if saved_file_paths:
        st.info(f"✓ Saved repository files for run: {orchestrator.run_id[:8]}...")
    
    # Save app-specific configuration to database
    app_config = {
        "llm_model": llm_model,
        "max_cycles": max_cycles,
        "base_dir": base_dir,
        "base_dir_option": base_dir_option,
        "db_path": db_path,
        "agent_frame_model": orchestrator.agent_frame_model,
        "resume_mode": "Fresh Run",
        "verify_files": verify_files,
        "app_version": APP_VERSION,
        "concepts_file_path": saved_file_paths.get('concepts'),
        "inferences_file_path": saved_file_paths.get('inferences'),
        "inputs_file_path": saved_file_paths.get('inputs'),
        "custom_run_id": run_id_for_fresh_run if run_id_for_fresh_run else None
    }
    
    try:
        def save_config():
            db_for_config = OrchestratorDB(db_path, run_id=orchestrator.run_id)
            db_for_config.save_run_metadata(orchestrator.run_id, app_config)
        
        await asyncio.to_thread(save_config)
        logging.info(f"Saved app configuration for run_id: {orchestrator.run_id}")
    except Exception as e:
        logging.warning(f"Could not save app configuration: {e}")
    
    return orchestrator, app_config


async def _create_fork_run(
    concept_repo, inference_repo, body, max_cycles, db_path,
    run_id_to_resume, new_run_id, reconciliation_mode, concepts_file,
    loaded_concepts, inferences_file, loaded_inferences, inputs_file,
    loaded_inputs, llm_model, base_dir, base_dir_option, verify_files
):
    """Create a forked orchestration run."""
    fork_new_run_id = new_run_id if new_run_id else f"fork-{uuid.uuid4().hex[:8]}"
    
    # Offload heavy checkpoint loading and reconciliation
    orchestrator = await asyncio.to_thread(
        Orchestrator.load_checkpoint,
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        db_path=db_path,
        body=body,
        max_cycles=max_cycles,
        run_id=run_id_to_resume if run_id_to_resume else None,
        new_run_id=fork_new_run_id,
        mode=reconciliation_mode,
        validate_compatibility=True
    )
    
    st.success(f"🔱 Forked from `{run_id_to_resume or 'latest'}` → New run: `{orchestrator.run_id}`")
    st.info(f"✓ State loaded from source run using {reconciliation_mode} mode, starting fresh execution history")
    
    # Save repository files
    saved_file_paths = await asyncio.to_thread(
        save_file_paths_for_run,
        orchestrator, concepts_file, loaded_concepts, inferences_file,
        loaded_inferences, inputs_file, loaded_inputs
    )
    
    # Save app-specific configuration
    app_config = {
        "llm_model": llm_model,
        "max_cycles": max_cycles,
        "base_dir": base_dir,
        "base_dir_option": base_dir_option,
        "db_path": db_path,
        "agent_frame_model": orchestrator.agent_frame_model,
        "resume_mode": "Fork from Checkpoint",
        "forked_from_run_id": run_id_to_resume or "latest",
        "reconciliation_mode": reconciliation_mode,
        "verify_files": verify_files,
        "app_version": APP_VERSION,
        "concepts_file_path": saved_file_paths.get('concepts'),
        "inferences_file_path": saved_file_paths.get('inferences'),
        "inputs_file_path": saved_file_paths.get('inputs'),
        "new_run_id": new_run_id if new_run_id and new_run_id.strip() else None
    }
    
    try:
        def save_config():
            db_for_config = OrchestratorDB(db_path, run_id=orchestrator.run_id)
            db_for_config.save_run_metadata(orchestrator.run_id, app_config)
        
        await asyncio.to_thread(save_config)
        logging.info(f"Saved app configuration for forked run_id: {orchestrator.run_id}")
    except Exception as e:
        logging.warning(f"Could not save app configuration: {e}")
    
    return orchestrator, app_config


async def _create_resume_run(
    concept_repo, inference_repo, body, max_cycles, db_path,
    run_id_to_resume, reconciliation_mode, concepts_file, loaded_concepts,
    inferences_file, loaded_inferences, inputs_file, loaded_inputs,
    llm_model, base_dir, base_dir_option, verify_files
):
    """Create a resumed orchestration run."""
    # Offload checkpoint loading
    orchestrator = await asyncio.to_thread(
        Orchestrator.load_checkpoint,
        concept_repo=concept_repo,
        inference_repo=inference_repo,
        db_path=db_path,
        body=body,
        max_cycles=max_cycles,
        run_id=run_id_to_resume if run_id_to_resume else None,
        mode=reconciliation_mode
    )
    
    st.info(f"♻️ Resumed run: `{orchestrator.run_id}` (reconciliation: {reconciliation_mode})")
    
    # Save repository files
    saved_file_paths = await asyncio.to_thread(
        save_file_paths_for_run,
        orchestrator, concepts_file, loaded_concepts, inferences_file,
        loaded_inferences, inputs_file, loaded_inputs
    )
    
    # Update app-specific configuration
    try:
        def update_config():
            db_for_config = OrchestratorDB(db_path, run_id=orchestrator.run_id)
            existing_metadata = db_for_config.get_run_metadata(orchestrator.run_id) or {}
            
            app_config = {
                **existing_metadata,
                "llm_model": llm_model,
                "max_cycles": max_cycles,
                "base_dir": base_dir,
                "base_dir_option": base_dir_option,
                "db_path": db_path,
                "agent_frame_model": orchestrator.agent_frame_model,
                "resume_mode": "Resume from Checkpoint",
                "reconciliation_mode": reconciliation_mode,
                "verify_files": verify_files,
                "app_version": APP_VERSION,
                "last_resumed": datetime.now().isoformat(),
                "concepts_file_path": saved_file_paths.get('concepts') or existing_metadata.get('concepts_file_path'),
                "inferences_file_path": saved_file_paths.get('inferences') or existing_metadata.get('inferences_file_path'),
                "inputs_file_path": saved_file_paths.get('inputs') or existing_metadata.get('inputs_file_path'),
                "resumed_from_run_id": run_id_to_resume if run_id_to_resume and run_id_to_resume.strip() else existing_metadata.get('resumed_from_run_id')
            }
            
            db_for_config.save_run_metadata(orchestrator.run_id, app_config)
            return app_config
        
        app_config = await asyncio.to_thread(update_config)
        logging.info(f"Updated app configuration for resumed run_id: {orchestrator.run_id}")
    except Exception as e:
        logging.warning(f"Could not update app configuration: {e}")
        app_config = {}  # Fallback
    
    return orchestrator, app_config


def inject_inputs_into_repo(concept_repo: ConceptRepo, inputs_json_data: Dict) -> int:
    """
    Inject input data into concept repository.
    
    Args:
        concept_repo: Concept repository
        inputs_json_data: Dictionary of input concepts
    
    Returns:
        Number of concepts injected
    """
    count = 0
    for concept_name, details in inputs_json_data.items():
        if isinstance(details, dict) and 'data' in details:
            data = details['data']
            axes = details.get('axes')
        else:
            data = details
            axes = None
        concept_repo.add_reference(concept_name, data, axis_names=axes)
        count += 1
    return count


async def verify_files_if_enabled(
    verify_files: bool,
    concept_repo: ConceptRepo,
    inference_repo: InferenceRepo,
    base_dir: str
):
    """
    Verify repository files if verification is enabled.
    
    Args:
        verify_files: Whether to verify files
        concept_repo: Concept repository
        inference_repo: Inference repository
        base_dir: Base directory for verification
    
    Raises:
        ValueError: If verification fails
    """
    if not verify_files:
        return
    
    st.info("Verifying repository files...")
    
    # Offload verification (CPU/IO bound) to thread
    valid, warnings_list, errors_list = await asyncio.to_thread(
        verify_repository_files,
        concept_repo, inference_repo, base_dir
    )
    
    # Display verification results
    if warnings_list:
        for warning in warnings_list:
            if warning.startswith("✓"):
                st.success(warning)
            else:
                st.warning(f"⚠️ {warning}")
    
    if errors_list:
        for error in errors_list:
            st.error(f"❌ {error}")
        st.error("**Cannot proceed**: Repository references files that don't exist in base_dir. Please fix the issues above.")
        st.info("💡 **Tip**: You can disable verification in Advanced Options if these are false positives.")
        raise ValueError("Repository file verification failed")

