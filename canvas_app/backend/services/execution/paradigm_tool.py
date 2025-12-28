"""
Custom Paradigm Tool - Loads paradigms from project-local directories.

This tool allows projects to define their own paradigms locally instead of
using the default infra/_agent/_models/_paradigms location.

Based on the pattern from direct_infra_experiment executors.
"""

import os
import json
import logging
import importlib.util
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CustomParadigmTool:
    """
    Custom paradigm tool that loads paradigms from a specified directory
    instead of the default infra/_agent/_models/_paradigms location.
    
    This allows projects to define their own paradigms locally.
    Based on the pattern from direct_infra_experiment executors.
    """
    
    def __init__(self, paradigm_dir: Path):
        self.paradigm_dir = Path(paradigm_dir)
        self._Paradigm = None
        
        # Try to load the Paradigm class from the local paradigm directory
        local_paradigm_py = self.paradigm_dir / "_paradigm.py"
        if local_paradigm_py.exists():
            self._init_from_local_paradigm_py(local_paradigm_py)
        else:
            self._init_from_infra_paradigm()
    
    def _init_from_local_paradigm_py(self, local_paradigm_py: Path):
        """Initialize using a local _paradigm.py file."""
        # Load from local _paradigm.py (allows full customization)
        spec = importlib.util.spec_from_file_location("_paradigm", local_paradigm_py)
        paradigm_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(paradigm_module)
        LocalParadigmClass = paradigm_module.Paradigm
        # Override PARADIGMS_DIR in the module to point to our custom dir
        paradigm_module.PARADIGMS_DIR = self.paradigm_dir
        logger.info(f"Loaded custom Paradigm class from {local_paradigm_py}")
        
        # Wrap with fallback to default paradigms
        try:
            from infra._agent._models._paradigms._paradigm import Paradigm as DefaultParadigm, PARADIGMS_DIR
            custom_dir = self.paradigm_dir
            
            class WrappedLocalParadigm:
                """Wrapper that tries local paradigm first, then falls back to default."""
                @classmethod
                def load(cls, paradigm_name: str):
                    # Try local paradigm directory first
                    paradigm_file = custom_dir / f"{paradigm_name}.json"
                    if paradigm_file.exists():
                        logger.debug(f"Loading paradigm '{paradigm_name}' from custom directory")
                        return LocalParadigmClass.load(paradigm_name)
                    
                    # Fall back to default paradigms
                    default_paradigm_file = PARADIGMS_DIR / f"{paradigm_name}.json"
                    if default_paradigm_file.exists():
                        logger.info(f"Paradigm '{paradigm_name}' not in custom dir, loading from default")
                        return DefaultParadigm.load(paradigm_name)
                    
                    # Not found in either location
                    raise FileNotFoundError(
                        f"Paradigm '{paradigm_name}' not found in custom ({custom_dir}) or default ({PARADIGMS_DIR})"
                    )
            
            self._Paradigm = WrappedLocalParadigm
            logger.info(f"Wrapped local Paradigm with fallback to default paradigms")
        except ImportError as e:
            # If infra not available, just use local paradigm without fallback
            logger.warning(f"Could not import default paradigms for fallback: {e}")
            self._Paradigm = LocalParadigmClass
    
    def _init_from_infra_paradigm(self):
        """Initialize using infra's Paradigm class with custom directory fallback."""
        paradigm_dir = self.paradigm_dir
        
        try:
            from infra._agent._models._paradigms._paradigm import (
                Paradigm, PARADIGMS_DIR, 
                _paradigm_object_hook, _build_env_spec, _build_sequence_spec
            )
            
            # Create a wrapper that loads from custom directory first, then falls back to default
            class LocalParadigm:
                """Wrapper to load paradigms from custom directory, falling back to default."""
                @classmethod
                def load(cls, paradigm_name: str):
                    # Try custom directory first
                    paradigm_file = paradigm_dir / f"{paradigm_name}.json"
                    if paradigm_file.exists():
                        with open(paradigm_file, 'r', encoding='utf-8') as f:
                            # Use the proper object hook to handle MetaValue etc
                            raw_spec = json.load(f, object_hook=_paradigm_object_hook)
                        
                        # Properly reconstruct spec objects (not raw dicts!)
                        env_spec_data = raw_spec.get('env_spec', {})
                        sequence_spec_data = raw_spec.get('sequence_spec', {})
                        metadata_data = raw_spec.get('metadata', {})
                        
                        env_spec = _build_env_spec(env_spec_data)
                        sequence_spec = _build_sequence_spec(sequence_spec_data, env_spec)
                        
                        # Create Paradigm instance properly
                        paradigm = Paradigm(env_spec, sequence_spec, metadata_data)
                        logger.debug(f"Loaded paradigm '{paradigm_name}' from custom directory")
                        return paradigm
                    
                    # Fall back to default paradigms directory
                    default_paradigm_file = PARADIGMS_DIR / f"{paradigm_name}.json"
                    if default_paradigm_file.exists():
                        logger.debug(f"Paradigm '{paradigm_name}' not in custom dir, loading from default")
                        return Paradigm.load(paradigm_name)
                    
                    # Not found in either location
                    raise FileNotFoundError(
                        f"Paradigm '{paradigm_name}' not found in custom ({paradigm_dir}) or default ({PARADIGMS_DIR})"
                    )
            
            self._Paradigm = LocalParadigm
            logger.info(f"Using infra Paradigm with custom directory fallback: {paradigm_dir}")
        except ImportError as e:
            logger.error(f"Failed to import Paradigm from infra: {e}")
            raise
    
    def load(self, paradigm_name: str) -> Any:
        """Load a paradigm by name."""
        return self._Paradigm.load(paradigm_name)
    
    def list_manifest(self) -> str:
        """List all available paradigms in the custom directory."""
        manifest = []
        for filename in os.listdir(self.paradigm_dir):
            if filename.endswith(".json"):
                name = filename[:-5]  # Remove .json extension
                try:
                    with open(self.paradigm_dir / filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata = data.get('metadata', {})
                        desc = metadata.get('description', 'No description provided.')
                        manifest.append(
                            f"<paradigm name=\"{name}\">\n"
                            f"    <description>{desc}</description>\n"
                            f"</paradigm>"
                        )
                except Exception as e:
                    manifest.append(f"<error paradigm=\"{name}\">{str(e)}</error>")
        return "\n\n".join(manifest)


def create_paradigm_tool(paradigm_dir: Optional[str], base_dir: str) -> Optional[CustomParadigmTool]:
    """
    Create a CustomParadigmTool if paradigm_dir is specified and exists.
    
    Args:
        paradigm_dir: Relative or absolute path to paradigm directory
        base_dir: Base directory for resolving relative paths
        
    Returns:
        CustomParadigmTool instance, or None if not applicable
    """
    if not paradigm_dir:
        return None
    
    paradigm_path = Path(paradigm_dir)
    # If relative path, resolve relative to base_dir
    if not paradigm_path.is_absolute():
        paradigm_path = Path(base_dir) / paradigm_dir
    
    if paradigm_path.exists() and paradigm_path.is_dir():
        logger.info(f"Using custom paradigm directory: {paradigm_path}")
        return CustomParadigmTool(paradigm_path)
    else:
        logger.warning(f"Paradigm directory not found: {paradigm_path}")
        return None

