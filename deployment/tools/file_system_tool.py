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
    
    def _log(self, event: str, data: Dict[str, Any]):
        """Log an event via callback if set."""
        if self._log_callback:
            try:
                self._log_callback(event, data)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to base_dir if not absolute."""
        p = Path(path)
        if not p.is_absolute():
            p = Path(self.base_dir) / path
        return p.resolve()
    
    def read(self, path: str) -> str:
        """
        Read content from a file.
        
        Args:
            path: Path to file (relative to base_dir or absolute)
            
        Returns:
            File content as string
        """
        self._operation_count += 1
        resolved = self._resolve_path(path)
        
        self._log("file:read", {
            "path": str(resolved),
            "status": "started",
        })
        
        try:
            with open(resolved, "r", encoding="utf-8") as f:
                content = f.read()
            
            self._log("file:read", {
                "path": str(resolved),
                "status": "completed",
                "size": len(content),
            })
            
            return content
            
        except Exception as e:
            self._log("file:read", {
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            raise
    
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

