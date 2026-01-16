"""
Deployment File System Tool - File operations for NormCode deployment.

A standalone file system tool that provides:
- Read/write/delete file operations
- Directory listing
- Path resolution relative to base directory
- Same interface as infra FileSystemTool
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class DeploymentFileSystemTool:
    """
    A file system tool for deployment/server execution.
    
    Provides file operations within a sandboxed base directory.
    Supports registered paths for provisions (data, scripts, etc.).
    """
    
    def __init__(
        self,
        base_dir: Optional[str] = None,
        log_callback: Optional[callable] = None,
    ):
        """
        Initialize the file system tool.
        
        Args:
            base_dir: Base directory for file operations (defaults to cwd)
            log_callback: Optional callback for logging events
        """
        self.base_dir = base_dir or os.getcwd()
        self._log_callback = log_callback
        self._operation_count = 0
        
        # Registered paths for provisions (data, scripts, prompts, etc.)
        self._registered_paths: Dict[str, str] = {}
    
    def register_path(self, name: str, path: str):
        """
        Register a named path for provision resolution.
        
        This allows provisions like data files to be resolved using
        a prefix like 'data:investor_profile.json' or by path lookup.
        
        Args:
            name: Name of the path (e.g., 'data', 'scripts', 'prompts')
            path: Absolute path to the directory
        """
        self._registered_paths[name] = path
        logger.info(f"Registered path '{name}': {path}")
    
    def get_registered_path(self, name: str) -> Optional[str]:
        """Get a registered path by name."""
        return self._registered_paths.get(name)
    
    def set_provisions_base(self, path: str):
        """
        Set the base directory for provisions.
        
        This is the directory containing subdirs like 'data', 'scripts', 'prompts'.
        Used to resolve paths like 'provision/scripts/file.py'.
        
        Args:
            path: Absolute path to the provisions base directory
        """
        self._provisions_base = path
        logger.info(f"Set provisions base: {path}")
    
    def get_provisions_base(self) -> Optional[str]:
        """Get the provisions base directory (parent of data, scripts, etc.)."""
        # Check for explicitly set provisions base
        if hasattr(self, '_provisions_base') and self._provisions_base:
            return self._provisions_base
        
        # Fallback: return the first registered path's parent
        for path in self._registered_paths.values():
            return str(Path(path).parent)
        return None
    
    def _log(self, event: str, data: Dict[str, Any]):
        """Log an event via callback if set."""
        if self._log_callback:
            try:
                self._log_callback(event, data)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")
    
    def _resolve_path(self, path: str) -> Path:
        """
        Resolve a path relative to base_dir if not absolute.
        
        Supports:
        - Registered path prefixes like 'data:filename.json'
        - Provision paths like 'provision/scripts/file.py' or 'provisions/scripts/file.py'
        """
        logger.debug(f"[FileSystemTool] _resolve_path called with: '{path}'")
        logger.debug(f"[FileSystemTool]   base_dir: {self.base_dir}")
        logger.debug(f"[FileSystemTool]   registered_paths: {self._registered_paths}")
        
        # Check for registered path prefix (e.g., 'data:filename.json')
        if ':' in path and not Path(path).is_absolute():
            prefix, rest = path.split(':', 1)
            if prefix in self._registered_paths:
                resolved = Path(self._registered_paths[prefix]) / rest
                logger.debug(f"[FileSystemTool]   -> Resolved via prefix '{prefix}': {resolved}")
                return resolved
        
        p = Path(path)
        if not p.is_absolute():
            # Handle provision paths like 'provision/scripts/file.py' or 'provisions/scripts/file.py'
            # These need to be mapped to registered paths
            path_parts = p.parts
            logger.debug(f"[FileSystemTool]   path_parts: {path_parts}")
            
            if len(path_parts) >= 2 and path_parts[0] in ('provision', 'provisions'):
                # Extract provision type (data, scripts, prompts, etc.) and remaining path
                provision_type = path_parts[1]  # e.g., 'scripts', 'data', 'prompts'
                remaining = '/'.join(path_parts[2:]) if len(path_parts) > 2 else ''
                logger.debug(f"[FileSystemTool]   Detected provision path: type='{provision_type}', remaining='{remaining}'")
                
                # Check if we have a registered path for this provision type
                if provision_type in self._registered_paths:
                    resolved = Path(self._registered_paths[provision_type])
                    if remaining:
                        resolved = resolved / remaining
                    logger.debug(f"[FileSystemTool]   Checking registered path: {resolved}, exists={resolved.exists()}")
                    if resolved.exists():
                        logger.debug(f"[FileSystemTool]   -> Resolved provision path '{path}' -> '{resolved}'")
                        return resolved.resolve()
                else:
                    logger.debug(f"[FileSystemTool]   provision_type '{provision_type}' NOT in registered_paths")
                
                # Try with variants (e.g., scripts_chinese for scripts)
                for name, reg_path in self._registered_paths.items():
                    if name.startswith(provision_type + '_') or name == provision_type:
                        possible = Path(reg_path)
                        if remaining:
                            possible = possible / remaining
                        if possible.exists():
                            logger.debug(f"Resolved provision path '{path}' -> '{possible}' via {name}")
                            return possible.resolve()
                
                # Also check provisions base if we have one
                provisions_base = self.get_provisions_base()
                logger.debug(f"[FileSystemTool]   provisions_base: {provisions_base}")
                if provisions_base:
                    # The provisions_base is the directory containing 'data', 'scripts', etc.
                    # So we just need to append the provision_type and remaining path
                    possible = Path(provisions_base) / provision_type
                    if remaining:
                        possible = possible / remaining
                    logger.debug(f"[FileSystemTool]   Checking provisions_base path: {possible}, exists={possible.exists()}")
                    if possible.exists():
                        logger.debug(f"[FileSystemTool]   -> Resolved provision path '{path}' -> '{possible}' via provisions_base")
                        return possible.resolve()
                
                # Try resolving directly relative to base_dir since path starts with provision/
                # This handles cases where base_dir is the project root and provision/ exists there
                direct_path = Path(self.base_dir) / path
                logger.debug(f"[FileSystemTool]   Checking direct path: {direct_path}, exists={direct_path.exists()}")
                if direct_path.exists():
                    logger.debug(f"[FileSystemTool]   -> Resolved provision path '{path}' -> '{direct_path}' via base_dir")
                    return direct_path.resolve()
                
                # Try the alternative plural/singular form (provision vs provisions)
                alt_prefix = 'provisions' if path_parts[0] == 'provision' else 'provision'
                alt_path = Path(self.base_dir) / alt_prefix / '/'.join(path_parts[1:])
                logger.debug(f"[FileSystemTool]   Checking alt path: {alt_path}, exists={alt_path.exists()}")
                if alt_path.exists():
                    logger.debug(f"[FileSystemTool]   -> Resolved provision path '{path}' -> '{alt_path}' via alt prefix")
                    return alt_path.resolve()
            
            # Try to resolve against registered paths
            for name, registered_path in self._registered_paths.items():
                possible = Path(registered_path) / path
                if possible.exists():
                    return possible.resolve()
            
            # Fall back to base_dir
            p = Path(self.base_dir) / path
            logger.debug(f"[FileSystemTool]   Fallback to base_dir path: {p}, exists={p.exists()}")
            
            # If base_dir path doesn't exist, try looking for provisions directory variations
            if not p.exists() and len(path_parts) >= 2:
                # Check if this might be a provision path without the prefix
                possible_type = path_parts[0]
                if possible_type in self._registered_paths:
                    alt = Path(self._registered_paths[possible_type]) / '/'.join(path_parts[1:])
                    logger.debug(f"[FileSystemTool]   Checking alt type path: {alt}, exists={alt.exists()}")
                    if alt.exists():
                        logger.debug(f"[FileSystemTool]   -> Resolved via type '{possible_type}': {alt}")
                        return alt.resolve()
        
        logger.debug(f"[FileSystemTool]   -> Final resolved path: {p.resolve()}")
        return p.resolve()
    
    def read(self, path: str = None, location: str = None) -> Dict[str, Any]:
        """
        Read content from a file.
        
        Args:
            path: Path to file (relative to base_dir or absolute)
            location: Alias for path (for compatibility with infra tool)
            
        Returns:
            Dict with status and content (matches infra FileSystemTool interface)
        """
        # Support both 'path' and 'location' parameter names
        filepath = path or location
        logger.info(f"[FileSystemTool] read() called with path='{path}', location='{location}'")
        
        if not filepath:
            logger.error("[FileSystemTool] read() called without path or location!")
            return {"status": "error", "message": "Either 'path' or 'location' must be provided"}
        
        self._operation_count += 1
        resolved = self._resolve_path(filepath)
        logger.info(f"[FileSystemTool] Resolved path: {resolved}")
        
        self._log("file:read", {
            "path": str(resolved),
            "status": "started",
        })
        
        try:
            if not resolved.exists():
                logger.warning(f"File not found at {resolved}")
                return {"status": "error", "message": f"File not found at {resolved}"}
            
            with open(resolved, "r", encoding="utf-8") as f:
                content = f.read()
            
            self._log("file:read", {
                "path": str(resolved),
                "status": "completed",
                "size": len(content),
            })
            
            return {"status": "success", "content": content}
            
        except Exception as e:
            self._log("file:read", {
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            return {"status": "error", "message": str(e)}
    
    def write(self, path: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file.
        
        Args:
            path: Path to file
            content: Content to write
            
        Returns:
            Result dict with status and location
        """
        self._operation_count += 1
        resolved = self._resolve_path(path)
        
        self._log("file:write", {
            "path": str(resolved),
            "status": "started",
            "size": len(content),
        })
        
        try:
            # Create parent directories if needed
            resolved.parent.mkdir(parents=True, exist_ok=True)
            
            with open(resolved, "w", encoding="utf-8") as f:
                f.write(content)
            
            self._log("file:write", {
                "path": str(resolved),
                "status": "completed",
            })
            
            return {
                "status": "success",
                "location": str(resolved),
                "message": f"Successfully wrote to {path}",
            }
            
        except Exception as e:
            self._log("file:write", {
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            return {
                "status": "error",
                "message": str(e),
            }
    
    def save(self, content: str, path: str) -> Dict[str, Any]:
        """
        Save content to a file (alias for write with swapped args).
        
        Args:
            content: Content to save
            path: Path to file
            
        Returns:
            Result dict
        """
        return self.write(path, content)
    
    def delete(self, path: str) -> Dict[str, Any]:
        """
        Delete a file.
        
        Args:
            path: Path to file
            
        Returns:
            Result dict
        """
        self._operation_count += 1
        resolved = self._resolve_path(path)
        
        try:
            if resolved.exists():
                resolved.unlink()
                self._log("file:delete", {
                    "path": str(resolved),
                    "status": "completed",
                })
                return {"status": "success", "message": f"Deleted {path}"}
            else:
                return {"status": "error", "message": f"File not found: {path}"}
                
        except Exception as e:
            self._log("file:delete", {
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            return {"status": "error", "message": str(e)}
    
    def exists(self, path: str) -> bool:
        """Check if a file exists."""
        resolved = self._resolve_path(path)
        return resolved.exists()
    
    def list_dir(self, path: str = ".") -> List[Dict[str, Any]]:
        """
        List contents of a directory.
        
        Args:
            path: Path to directory
            
        Returns:
            List of file/directory info dicts
        """
        self._operation_count += 1
        resolved = self._resolve_path(path)
        
        if not resolved.is_dir():
            return []
        
        items = []
        try:
            for entry in resolved.iterdir():
                stat = entry.stat()
                items.append({
                    "name": entry.name,
                    "path": str(entry),
                    "is_dir": entry.is_dir(),
                    "size": stat.st_size if entry.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        except Exception as e:
            logger.error(f"Failed to list directory {path}: {e}")
        
        return sorted(items, key=lambda x: (not x["is_dir"], x["name"].lower()))
    
    def mkdir(self, path: str) -> Dict[str, Any]:
        """
        Create a directory.
        
        Args:
            path: Path to directory
            
        Returns:
            Result dict
        """
        resolved = self._resolve_path(path)
        
        try:
            resolved.mkdir(parents=True, exist_ok=True)
            return {"status": "success", "message": f"Created directory {path}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "base_dir": self.base_dir,
            "operation_count": self._operation_count,
        }

