"""
File and path discovery utilities for NormCode Canvas projects.

This module provides functions for auto-discovering repository files
and paradigm directories within project directories.
"""

import logging
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# Directories to skip during file discovery
SKIP_DIRS = {
    '.git', '.svn', '.hg', '__pycache__', 'node_modules', '.venv', 'venv',
    '.idea', '.vscode', '.cursor', 'dist', 'build', '.tox', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', 'egg-info', '.eggs', '.conda',
}

# Max depth for recursive file search
MAX_SEARCH_DEPTH = 5


def discover_files_recursive(
    root_dir: Path,
    patterns: List[str],
    max_depth: int = MAX_SEARCH_DEPTH,
    skip_dirs: set = SKIP_DIRS,
) -> List[Path]:
    """
    Recursively search for files matching patterns within a directory.
    
    Args:
        root_dir: Directory to start search from
        patterns: List of glob patterns to match (e.g., ['*.concept.json', 'concepts.json'])
        max_depth: Maximum directory depth to search
        skip_dirs: Set of directory names to skip
        
    Returns:
        List of matching file paths, sorted by depth (shallower first)
    """
    found = []
    
    def _search(current_dir: Path, depth: int):
        if depth > max_depth:
            return
        
        try:
            for item in current_dir.iterdir():
                if item.is_file():
                    for pattern in patterns:
                        if item.match(pattern):
                            found.append(item)
                            break
                elif item.is_dir() and item.name not in skip_dirs:
                    _search(item, depth + 1)
        except PermissionError:
            pass  # Skip directories we can't access
    
    _search(root_dir, 0)
    
    # Sort by path depth (shallower = better), then alphabetically
    found.sort(key=lambda p: (len(p.relative_to(root_dir).parts), str(p)))
    return found


def discover_paradigm_directories(
    root_dir: Path,
    max_depth: int = MAX_SEARCH_DEPTH,
    skip_dirs: set = SKIP_DIRS,
) -> List[Path]:
    """
    Search for directories containing paradigm JSON files.
    
    Paradigm directories typically:
    - Are named 'paradigm' or 'paradigms'
    - OR contain files matching paradigm naming patterns (e.g., 'h_*-c_*.json', 'v_*-h_*.json')
    
    Args:
        root_dir: Directory to start search from
        max_depth: Maximum directory depth to search
        skip_dirs: Set of directory names to skip
        
    Returns:
        List of directory paths that appear to contain paradigms
    """
    found = []
    
    def _is_paradigm_file(filename: str) -> bool:
        """Check if a filename looks like a paradigm file."""
        name = filename.lower()
        # Common paradigm file patterns
        if name.endswith('.json'):
            # Pattern: h_Something-c_Something.json or v_Something-h_Something.json
            if ('-c_' in name and 'h_' in name) or ('-h_' in name and 'v_' in name):
                return True
            # Pattern: c_Something-o_Something.json
            if '-c_' in name and '-o_' in name:
                return True
        return False
    
    def _search(current_dir: Path, depth: int):
        if depth > max_depth:
            return
        
        try:
            # Check if this directory is a paradigm directory
            is_paradigm_dir = False
            
            # Check by name
            if current_dir.name.lower() in ('paradigm', 'paradigms'):
                is_paradigm_dir = True
            else:
                # Check if contains paradigm-like files
                paradigm_file_count = 0
                for item in current_dir.iterdir():
                    if item.is_file() and _is_paradigm_file(item.name):
                        paradigm_file_count += 1
                        if paradigm_file_count >= 2:  # At least 2 paradigm files
                            is_paradigm_dir = True
                            break
            
            if is_paradigm_dir:
                found.append(current_dir)
            
            # Continue searching subdirectories
            for item in current_dir.iterdir():
                if item.is_dir() and item.name not in skip_dirs:
                    _search(item, depth + 1)
                    
        except PermissionError:
            pass
    
    _search(root_dir, 0)
    
    # Sort by path depth (shallower = better)
    found.sort(key=lambda p: (len(p.relative_to(root_dir).parts), str(p)))
    return found


class DiscoveredPaths:
    """Container for auto-discovered repository paths."""
    
    def __init__(
        self,
        concepts: Optional[str] = None,
        inferences: Optional[str] = None,
        inputs: Optional[str] = None,
        paradigm_dir: Optional[str] = None,
    ):
        self.concepts = concepts
        self.inferences = inferences
        self.inputs = inputs
        self.paradigm_dir = paradigm_dir
    
    def to_dict(self) -> Dict[str, Optional[str]]:
        return {
            'concepts': self.concepts,
            'inferences': self.inferences,
            'inputs': self.inputs,
            'paradigm_dir': self.paradigm_dir,
        }
    
    def __repr__(self):
        return f"DiscoveredPaths({self.to_dict()})"


def discover_project_paths(project_dir: Path) -> DiscoveredPaths:
    """
    Auto-discover repository files and paradigm directory within a project directory.
    
    Searches for:
    - Concept files: *.concept.json, concepts.json
    - Inference files: *.inference.json, inferences.json
    - Input files: *.inputs.json, inputs.json
    - Paradigm directories: directories named 'paradigm' or containing paradigm files
    
    Args:
        project_dir: The project directory to search
        
    Returns:
        DiscoveredPaths with relative paths to discovered files
    """
    discovered = DiscoveredPaths()
    
    # Search for concept files
    concept_patterns = ['*.concept.json', 'concepts.json', '*_concept.json', 'concept_*.json']
    concept_files = discover_files_recursive(project_dir, concept_patterns)
    if concept_files:
        # Prefer files in 'repos' or 'repository' subdirectories
        for f in concept_files:
            parent_name = f.parent.name.lower()
            if parent_name in ('repos', 'repo', 'repository', 'repositories'):
                discovered.concepts = str(f.relative_to(project_dir))
                break
        # If not found in preferred dirs, use first match
        if not discovered.concepts:
            discovered.concepts = str(concept_files[0].relative_to(project_dir))
    
    # Search for inference files
    inference_patterns = ['*.inference.json', 'inferences.json', '*_inference.json', 'inference_*.json']
    inference_files = discover_files_recursive(project_dir, inference_patterns)
    if inference_files:
        # Prefer files in same directory as concepts
        if discovered.concepts:
            concepts_dir = Path(discovered.concepts).parent
            for f in inference_files:
                if f.relative_to(project_dir).parent == concepts_dir:
                    discovered.inferences = str(f.relative_to(project_dir))
                    break
        # If not found, prefer 'repos' directories
        if not discovered.inferences:
            for f in inference_files:
                parent_name = f.parent.name.lower()
                if parent_name in ('repos', 'repo', 'repository', 'repositories'):
                    discovered.inferences = str(f.relative_to(project_dir))
                    break
        # Fallback to first match
        if not discovered.inferences:
            discovered.inferences = str(inference_files[0].relative_to(project_dir))
    
    # Search for input files (optional)
    input_patterns = ['*.inputs.json', 'inputs.json', '*_inputs.json', 'input_*.json']
    input_files = discover_files_recursive(project_dir, input_patterns)
    if input_files:
        # Prefer files in same directory as concepts
        if discovered.concepts:
            concepts_dir = Path(discovered.concepts).parent
            for f in input_files:
                if f.relative_to(project_dir).parent == concepts_dir:
                    discovered.inputs = str(f.relative_to(project_dir))
                    break
        if not discovered.inputs:
            discovered.inputs = str(input_files[0].relative_to(project_dir))
    
    # Search for paradigm directories
    paradigm_dirs = discover_paradigm_directories(project_dir)
    if paradigm_dirs:
        discovered.paradigm_dir = str(paradigm_dirs[0].relative_to(project_dir))
    
    logger.info(f"Discovered paths in {project_dir}: {discovered}")
    return discovered

