"""
NormCode Manifest Management

Manages manifest files that link related NormCode files (.ncd, .nc, .ncn).
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List


class ManifestManager:
    """Manages NormCode project manifests."""
    
    def __init__(self, manifests_dir: str = "data/manifests"):
        """
        Initialize the manifest manager.
        
        Args:
            manifests_dir: Directory to store manifest files
        """
        # Get the streamlit_app directory
        script_dir = Path(__file__).parent.parent
        self.manifests_dir = script_dir / manifests_dir
        self.manifests_dir.mkdir(parents=True, exist_ok=True)
    
    def create(
        self, 
        project_name: str,
        draft_path: Optional[str] = None,
        formal_path: Optional[str] = None,
        natural_path: Optional[str] = None,
        description: str = "",
        version: str = "1.0"
    ) -> Dict:
        """
        Create a new manifest.
        
        Args:
            project_name: Name of the project
            draft_path: Path to .ncd file
            formal_path: Path to .nc file
            natural_path: Path to .ncn file
            description: Project description
            version: Project version
            
        Returns:
            Created manifest dictionary
        """
        manifest = {
            "project_name": project_name,
            "created": datetime.now().isoformat(),
            "files": {
                "draft": draft_path,
                "formal": formal_path,
                "natural": natural_path
            },
            "metadata": {
                "description": description,
                "version": version
            }
        }
        
        # Validate the manifest
        self._validate(manifest)
        
        return manifest
    
    def save(self, manifest: Dict) -> str:
        """
        Save a manifest to disk.
        
        Args:
            manifest: Manifest dictionary to save
            
        Returns:
            Path to saved manifest file
        """
        self._validate(manifest)
        
        project_name = manifest["project_name"]
        manifest_path = self.manifests_dir / f"{project_name}.json"
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        return str(manifest_path)
    
    def load(self, project_name: str) -> Optional[Dict]:
        """
        Load a manifest from disk.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Manifest dictionary or None if not found
        """
        manifest_path = self.manifests_dir / f"{project_name}.json"
        
        if not manifest_path.exists():
            return None
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        self._validate(manifest)
        return manifest
    
    def list_manifests(self) -> List[str]:
        """
        List all available manifest files.
        
        Returns:
            List of project names
        """
        if not self.manifests_dir.exists():
            return []
        
        manifests = []
        for file_path in self.manifests_dir.glob("*.json"):
            project_name = file_path.stem
            manifests.append(project_name)
        
        return sorted(manifests)
    
    def update_file_path(
        self, 
        manifest: Dict, 
        file_type: str, 
        new_path: str
    ) -> Dict:
        """
        Update a file path in the manifest.
        
        Args:
            manifest: Manifest dictionary
            file_type: Type of file ('draft', 'formal', or 'natural')
            new_path: New file path
            
        Returns:
            Updated manifest
        """
        if file_type not in ['draft', 'formal', 'natural']:
            raise ValueError(f"Invalid file type: {file_type}")
        
        manifest["files"][file_type] = new_path
        self._validate(manifest)
        
        return manifest
    
    def delete(self, project_name: str) -> bool:
        """
        Delete a manifest file.
        
        Args:
            project_name: Name of the project
            
        Returns:
            True if deleted, False if not found
        """
        manifest_path = self.manifests_dir / f"{project_name}.json"
        
        if manifest_path.exists():
            manifest_path.unlink()
            return True
        
        return False
    
    def _validate(self, manifest: Dict) -> None:
        """
        Validate manifest structure.
        
        Args:
            manifest: Manifest to validate
            
        Raises:
            ValueError: If manifest is invalid
        """
        required_keys = ["project_name", "created", "files", "metadata"]
        for key in required_keys:
            if key not in manifest:
                raise ValueError(f"Missing required key: {key}")
        
        # Validate files section
        if not isinstance(manifest["files"], dict):
            raise ValueError("'files' must be a dictionary")
        
        file_types = ["draft", "formal", "natural"]
        for file_type in file_types:
            if file_type not in manifest["files"]:
                raise ValueError(f"Missing file type in 'files': {file_type}")
        
        # Validate metadata section
        if not isinstance(manifest["metadata"], dict):
            raise ValueError("'metadata' must be a dictionary")
        
        if "description" not in manifest["metadata"]:
            raise ValueError("Missing 'description' in metadata")
        
        if "version" not in manifest["metadata"]:
            raise ValueError("Missing 'version' in metadata")

