"""
Canvas-native file system tool for NormCode orchestration.

This tool wraps the standard FileSystemTool but adds WebSocket event
emission for file operations, allowing the UI to show real-time
file operation progress and notifications.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Any, Callable, Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class CanvasFileSystemTool:
    """
    A file system tool that emits WebSocket events for file operations.
    
    This tool proxies the standard FileSystemTool functionality while
    adding event emission for UI monitoring.
    """
    
    def __init__(
        self, 
        base_dir: Optional[str] = None,
        emit_callback: Optional[Callable[[str, Dict], None]] = None
    ):
        """
        Initialize the Canvas file system tool.
        
        Args:
            base_dir: Base directory for file operations
            emit_callback: Callback to emit WebSocket events
        """
        self.base_dir = base_dir
        self._emit_callback = emit_callback
        
        # Try to import and create the underlying FileSystemTool
        try:
            from infra._agent._models._file_system import FileSystemTool
            self._tool = FileSystemTool(base_dir=base_dir)
        except ImportError:
            logger.warning("Could not import FileSystemTool from infra, using fallback")
            self._tool = None
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """Set the callback for emitting WebSocket events."""
        self._emit_callback = callback
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event if callback is set."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve a path relative to base_dir if set."""
        p = Path(path)
        if not p.is_absolute() and self.base_dir:
            p = Path(self.base_dir) / path
        return p
    
    def read(self, path: str) -> str:
        """
        Read content from a file.
        
        Args:
            path: Path to the file (relative to base_dir or absolute)
            
        Returns:
            File content as string
        """
        resolved = self._resolve_path(path)
        
        self._emit("file:operation", {
            "operation": "read",
            "path": str(resolved),
            "status": "started",
        })
        
        try:
            if self._tool:
                content = self._tool.read(path)
            else:
                # Fallback implementation
                with open(resolved, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            self._emit("file:operation", {
                "operation": "read",
                "path": str(resolved),
                "status": "completed",
                "size": len(content),
            })
            
            return content
            
        except Exception as e:
            self._emit("file:operation", {
                "operation": "read",
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            raise
    
    def write(self, path: str, content: str) -> str:
        """
        Write content to a file.
        
        Args:
            path: Path to the file
            content: Content to write
            
        Returns:
            Success message
        """
        resolved = self._resolve_path(path)
        
        self._emit("file:operation", {
            "operation": "write",
            "path": str(resolved),
            "status": "started",
            "size": len(content),
        })
        
        try:
            if self._tool:
                # Use the write method (which wraps save with correct param order)
                write_result = self._tool.write(path, content)
                if write_result.get("status") == "success":
                    result = f"Successfully wrote to {write_result.get('location', path)}"
                else:
                    raise IOError(write_result.get("message", "Write failed"))
            else:
                # Fallback implementation
                resolved.parent.mkdir(parents=True, exist_ok=True)
                with open(resolved, 'w', encoding='utf-8') as f:
                    f.write(content)
                result = f"Successfully wrote to {path}"
            
            self._emit("file:operation", {
                "operation": "write",
                "path": str(resolved),
                "status": "completed",
                "size": len(content),
            })
            
            return result
            
        except Exception as e:
            self._emit("file:operation", {
                "operation": "write",
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            raise
    
    def list_directory(self, path: str = ".") -> List[str]:
        """
        List contents of a directory.
        
        Args:
            path: Directory path
            
        Returns:
            List of file/directory names
        """
        resolved = self._resolve_path(path)
        
        self._emit("file:operation", {
            "operation": "list",
            "path": str(resolved),
            "status": "started",
        })
        
        try:
            if self._tool:
                items = self._tool.list_directory(path)
            else:
                # Fallback implementation
                items = os.listdir(resolved)
            
            self._emit("file:operation", {
                "operation": "list",
                "path": str(resolved),
                "status": "completed",
                "count": len(items),
            })
            
            return items
            
        except Exception as e:
            self._emit("file:operation", {
                "operation": "list",
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            raise
    
    def exists(self, path: str) -> bool:
        """Check if a file or directory exists."""
        resolved = self._resolve_path(path)
        return resolved.exists()
    
    def is_file(self, path: str) -> bool:
        """Check if path is a file."""
        resolved = self._resolve_path(path)
        return resolved.is_file()
    
    def is_directory(self, path: str) -> bool:
        """Check if path is a directory."""
        resolved = self._resolve_path(path)
        return resolved.is_dir()
    
    def read_json(self, path: str) -> Any:
        """
        Read and parse a JSON file.
        
        Args:
            path: Path to JSON file
            
        Returns:
            Parsed JSON data
        """
        content = self.read(path)
        return json.loads(content)
    
    def write_json(self, path: str, data: Any, indent: int = 2) -> str:
        """
        Write data as JSON to a file.
        
        Args:
            path: Path to JSON file
            data: Data to serialize
            indent: JSON indentation
            
        Returns:
            Success message
        """
        content = json.dumps(data, indent=indent, ensure_ascii=False)
        return self.write(path, content)
    
    def append(self, path: str, content: str) -> str:
        """
        Append content to a file.
        
        Args:
            path: Path to the file
            content: Content to append
            
        Returns:
            Success message
        """
        resolved = self._resolve_path(path)
        
        self._emit("file:operation", {
            "operation": "append",
            "path": str(resolved),
            "status": "started",
        })
        
        try:
            with open(resolved, 'a', encoding='utf-8') as f:
                f.write(content)
            
            self._emit("file:operation", {
                "operation": "append",
                "path": str(resolved),
                "status": "completed",
            })
            
            return f"Successfully appended to {path}"
            
        except Exception as e:
            self._emit("file:operation", {
                "operation": "append",
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            raise
    
    def delete(self, path: str) -> str:
        """
        Delete a file.
        
        Args:
            path: Path to the file
            
        Returns:
            Success message
        """
        resolved = self._resolve_path(path)
        
        self._emit("file:operation", {
            "operation": "delete",
            "path": str(resolved),
            "status": "started",
        })
        
        try:
            if resolved.is_file():
                resolved.unlink()
            elif resolved.is_dir():
                import shutil
                shutil.rmtree(resolved)
            else:
                raise FileNotFoundError(f"Path not found: {path}")
            
            self._emit("file:operation", {
                "operation": "delete",
                "path": str(resolved),
                "status": "completed",
            })
            
            return f"Successfully deleted {path}"
            
        except Exception as e:
            self._emit("file:operation", {
                "operation": "delete",
                "path": str(resolved),
                "status": "failed",
                "error": str(e),
            })
            raise
