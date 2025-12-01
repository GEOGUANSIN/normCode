"""
File handling utilities for NormCode Orchestrator Streamlit App.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from .config import REPO_FILES_DIR


def save_uploaded_file(uploaded_file, run_id: str, file_type: str) -> Optional[str]:
    """
    Save an uploaded file to disk for future reloading.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        run_id: Current run ID
        file_type: 'concepts', 'inferences', or 'inputs'
    
    Returns:
        Path to saved file or None if uploaded_file is None
    """
    if uploaded_file is None:
        return None
    
    # Create directory for this run
    run_dir = REPO_FILES_DIR / run_id
    run_dir.mkdir(exist_ok=True)
    
    # Save file with standard name
    file_path = run_dir / f"{file_type}.json"
    
    # Write file contents
    uploaded_file.seek(0)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.read())
    
    uploaded_file.seek(0)  # Reset for later use
    
    return str(file_path)


def load_file_from_path(file_path: str) -> Optional[str]:
    """
    Load a JSON file from disk and return its contents.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        File contents as string or None if file doesn't exist
    """
    if not file_path or not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Failed to load file from {file_path}: {e}")
        return None


def parse_json_file(file_obj=None, file_content: str = None) -> Dict[str, Any]:
    """
    Parse JSON from either an uploaded file object or file content string.
    
    Args:
        file_obj: Streamlit UploadedFile object (optional)
        file_content: JSON string content (optional)
    
    Returns:
        Parsed JSON data as dictionary
    """
    if file_obj is not None:
        file_obj.seek(0)
        content = file_obj.read().decode('utf-8')
        return json.loads(content)
    elif file_content is not None:
        return json.loads(file_content)
    else:
        raise ValueError("Either file_obj or file_content must be provided")


def get_file_content(uploaded_file, loaded_file_info: Optional[Dict]) -> Optional[str]:
    """
    Get file content from either an uploaded file or loaded file info.
    
    Args:
        uploaded_file: Streamlit UploadedFile object or None
        loaded_file_info: Dictionary with 'content' key or None
    
    Returns:
        File content as string or None
    """
    if uploaded_file is not None:
        uploaded_file.seek(0)
        return uploaded_file.read().decode('utf-8')
    elif loaded_file_info is not None:
        return loaded_file_info['content']
    else:
        return None


def save_file_paths_for_run(
    orchestrator,
    concepts_file,
    loaded_concepts,
    inferences_file,
    loaded_inferences,
    inputs_file,
    loaded_inputs
) -> Dict[str, Optional[str]]:
    """
    Save repository files to disk and return their paths.
    
    Args:
        orchestrator: Orchestrator instance with run_id
        concepts_file: Uploaded concepts file or None
        loaded_concepts: Loaded concepts file info or None
        inferences_file: Uploaded inferences file or None
        loaded_inferences: Loaded inferences file info or None
        inputs_file: Uploaded inputs file or None
        loaded_inputs: Loaded inputs file info or None
    
    Returns:
        Dictionary mapping file types to their saved paths
    """
    saved_file_paths = {}
    
    try:
        if concepts_file:
            saved_file_paths['concepts'] = save_uploaded_file(
                concepts_file, orchestrator.run_id, 'concepts'
            )
        elif loaded_concepts:
            saved_file_paths['concepts'] = loaded_concepts['path']
        
        if inferences_file:
            saved_file_paths['inferences'] = save_uploaded_file(
                inferences_file, orchestrator.run_id, 'inferences'
            )
        elif loaded_inferences:
            saved_file_paths['inferences'] = loaded_inferences['path']
        
        if inputs_file:
            saved_file_paths['inputs'] = save_uploaded_file(
                inputs_file, orchestrator.run_id, 'inputs'
            )
        elif loaded_inputs:
            saved_file_paths['inputs'] = loaded_inputs['path']
    
    except Exception as e:
        logging.warning(f"Failed to save repository files: {e}")
    
    return saved_file_paths

