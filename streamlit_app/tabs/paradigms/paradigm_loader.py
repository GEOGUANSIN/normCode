"""
Paradigm Loader Utility

Handles loading, listing, and managing paradigms from both built-in
and custom directories.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import shutil


@dataclass
class ParadigmInfo:
    """Metadata about a paradigm"""
    name: str
    file_path: Path
    is_builtin: bool
    inputs: str
    composition: str
    outputs: str
    
    @property
    def display_name(self) -> str:
        """Return formatted display name"""
        return self.name.replace('.json', '')
    
    @property
    def source_label(self) -> str:
        """Return source label for UI"""
        return "Built-in" if self.is_builtin else "Custom"


class ParadigmLoader:
    """Manages paradigm loading and CRUD operations"""
    
    def __init__(self):
        # Get paths relative to this file
        self.streamlit_dir = Path(__file__).parent.parent.parent
        self.project_root = self.streamlit_dir.parent
        
        # Built-in paradigms directory
        self.builtin_dir = self.project_root / "infra" / "_agent" / "_models" / "_paradigms"
        
        # Custom paradigms directory
        self.custom_dir = self.streamlit_dir / "custom_paradigms"
        
        # Ensure custom directory exists
        self.custom_dir.mkdir(exist_ok=True)
    
    def parse_paradigm_name(self, filename: str) -> Tuple[str, str, str]:
        """
        Parse paradigm filename to extract inputs, composition, and outputs.
        
        Format: [inputs]-[composition]-[outputs].json
        Examples:
        - h_PromptTemplate_SavePath-c_GenerateThinkJson-Extract-Save-o_FileLocation
        - v_PromptTemplate-h_ScriptLocation-c_Retrieve_or_GenerateThinkJson_ExtractPy_Execute-o_Normal
        
        Returns:
            Tuple of (inputs, composition, outputs)
        """
        name = filename.replace('.json', '')
        
        try:
            # Split by '-' to find major sections
            parts = name.split('-')
            
            # Find indices of composition (c_) and outputs (o_)
            comp_idx = None
            out_idx = None
            
            for i, part in enumerate(parts):
                if part.startswith('c_'):
                    comp_idx = i
                elif part.startswith('o_'):
                    out_idx = i
            
            if comp_idx is None or out_idx is None:
                # Fallback for non-standard names
                return ("Unknown", "Unknown", "Unknown")
            
            # Extract sections
            inputs = '-'.join(parts[:comp_idx])
            composition = '-'.join(parts[comp_idx:out_idx])
            outputs = '-'.join(parts[out_idx:])
            
            # Clean up prefixes for display
            inputs = inputs.replace('h_', '').replace('v_', '').replace('_', ' ')
            composition = composition.replace('c_', '').replace('_', ' ')
            outputs = outputs.replace('o_', '').replace('_', ' ')
            
            return (inputs, composition, outputs)
        except Exception:
            return ("Unknown", "Unknown", "Unknown")
    
    def list_paradigms(self, include_builtin: bool = True, include_custom: bool = True) -> List[ParadigmInfo]:
        """
        List all available paradigms.
        
        Args:
            include_builtin: Include built-in paradigms
            include_custom: Include custom paradigms
            
        Returns:
            List of ParadigmInfo objects
        """
        paradigms = []
        
        if include_builtin and self.builtin_dir.exists():
            for file_path in self.builtin_dir.glob("*.json"):
                # Skip README and other non-paradigm files
                if file_path.stem in ['README', '__pycache__']:
                    continue
                
                inputs, comp, outputs = self.parse_paradigm_name(file_path.name)
                paradigms.append(ParadigmInfo(
                    name=file_path.name,
                    file_path=file_path,
                    is_builtin=True,
                    inputs=inputs,
                    composition=comp,
                    outputs=outputs
                ))
        
        if include_custom and self.custom_dir.exists():
            for file_path in self.custom_dir.glob("*.json"):
                # Skip non-paradigm files
                if file_path.stem in ['__init__', '__pycache__']:
                    continue
                
                inputs, comp, outputs = self.parse_paradigm_name(file_path.name)
                paradigms.append(ParadigmInfo(
                    name=file_path.name,
                    file_path=file_path,
                    is_builtin=False,
                    inputs=inputs,
                    composition=comp,
                    outputs=outputs
                ))
        
        # Sort: custom first, then by name
        paradigms.sort(key=lambda p: (p.is_builtin, p.name))
        return paradigms
    
    def load_paradigm(self, paradigm_info: ParadigmInfo) -> Dict[str, Any]:
        """
        Load paradigm JSON content.
        
        Args:
            paradigm_info: ParadigmInfo object
            
        Returns:
            Dictionary with paradigm content
        """
        with open(paradigm_info.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_paradigm(self, name: str, content: Dict[str, Any], overwrite: bool = False) -> Tuple[bool, str]:
        """
        Save a paradigm to the custom directory.
        
        Args:
            name: Paradigm filename (should end with .json)
            content: Paradigm JSON content
            overwrite: Whether to overwrite if exists
            
        Returns:
            Tuple of (success, message)
        """
        if not name.endswith('.json'):
            name = f"{name}.json"
        
        target_path = self.custom_dir / name
        
        # Check if file exists
        if target_path.exists() and not overwrite:
            return (False, f"Paradigm '{name}' already exists in custom directory")
        
        try:
            # Validate JSON structure
            if 'env_spec' not in content or 'sequence_spec' not in content:
                return (False, "Invalid paradigm structure: missing 'env_spec' or 'sequence_spec'")
            
            # Save with pretty formatting
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False)
            
            return (True, f"Successfully saved paradigm '{name}'")
        except Exception as e:
            return (False, f"Error saving paradigm: {str(e)}")
    
    def delete_paradigm(self, paradigm_info: ParadigmInfo) -> Tuple[bool, str]:
        """
        Delete a custom paradigm.
        
        Args:
            paradigm_info: ParadigmInfo object
            
        Returns:
            Tuple of (success, message)
        """
        if paradigm_info.is_builtin:
            return (False, "Cannot delete built-in paradigms")
        
        try:
            paradigm_info.file_path.unlink()
            return (True, f"Successfully deleted paradigm '{paradigm_info.name}'")
        except Exception as e:
            return (False, f"Error deleting paradigm: {str(e)}")
    
    def clone_paradigm(self, paradigm_info: ParadigmInfo, new_name: str) -> Tuple[bool, str]:
        """
        Clone a paradigm to the custom directory.
        
        Args:
            paradigm_info: ParadigmInfo object to clone
            new_name: New name for the cloned paradigm
            
        Returns:
            Tuple of (success, message)
        """
        if not new_name.endswith('.json'):
            new_name = f"{new_name}.json"
        
        target_path = self.custom_dir / new_name
        
        if target_path.exists():
            return (False, f"Paradigm '{new_name}' already exists")
        
        try:
            # Load original content
            content = self.load_paradigm(paradigm_info)
            
            # Save to custom directory
            return self.save_paradigm(new_name, content, overwrite=False)
        except Exception as e:
            return (False, f"Error cloning paradigm: {str(e)}")
    
    def validate_paradigm(self, content: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate paradigm structure.
        
        Args:
            content: Paradigm JSON content
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check required top-level keys
        if 'env_spec' not in content:
            errors.append("Missing 'env_spec' key")
        if 'sequence_spec' not in content:
            errors.append("Missing 'sequence_spec' key")
        
        # Validate env_spec structure
        if 'env_spec' in content:
            env_spec = content['env_spec']
            if not isinstance(env_spec, dict):
                errors.append("'env_spec' must be a dictionary")
            elif 'tools' not in env_spec:
                errors.append("'env_spec' missing 'tools' key")
            elif not isinstance(env_spec['tools'], list):
                errors.append("'env_spec.tools' must be a list")
        
        # Validate sequence_spec structure
        if 'sequence_spec' in content:
            seq_spec = content['sequence_spec']
            if not isinstance(seq_spec, dict):
                errors.append("'sequence_spec' must be a dictionary")
            elif 'steps' not in seq_spec:
                errors.append("'sequence_spec' missing 'steps' key")
            elif not isinstance(seq_spec['steps'], list):
                errors.append("'sequence_spec.steps' must be a list")
        
        return (len(errors) == 0, errors)
    
    def create_blank_paradigm(self) -> Dict[str, Any]:
        """Create a blank paradigm template"""
        return {
            "env_spec": {
                "tools": []
            },
            "sequence_spec": {
                "steps": []
            }
        }

