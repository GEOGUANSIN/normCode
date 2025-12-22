"""
Version Control System for NormCode Files

Provides version history, rollback, and diff capabilities for NormCode files.
"""

import sqlite3
import hashlib
import difflib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Version:
    """Represents a version snapshot."""
    id: str
    file_path: str
    content: str
    timestamp: str
    message: str
    hash: str


class VersionControl:
    """Version control system for NormCode files."""
    
    def __init__(self, db_path: str = "data/normcode_versions.db"):
        """
        Initialize version control system.
        
        Args:
            db_path: Path to SQLite database file
        """
        # Get the streamlit_app directory
        script_dir = Path(__file__).parent.parent
        self.db_path = script_dir / db_path
        
        # Ensure data directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                message TEXT NOT NULL,
                hash TEXT NOT NULL
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_path 
            ON versions(file_path, timestamp DESC)
        """)
        
        conn.commit()
        conn.close()
    
    def save_snapshot(
        self, 
        file_path: str, 
        content: str, 
        message: str = "Manual save"
    ) -> str:
        """
        Save a snapshot of file content.
        
        Args:
            file_path: Path to the file
            content: File content
            message: Commit message
            
        Returns:
            Version ID
        """
        # Generate version ID and hash
        timestamp = datetime.now().isoformat()
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        version_id = f"{content_hash[:8]}_{timestamp.replace(':', '-').replace('.', '-')}"
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO versions (id, file_path, content, timestamp, message, hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (version_id, file_path, content, timestamp, message, content_hash))
        
        conn.commit()
        conn.close()
        
        return version_id
    
    def get_history(self, file_path: str, limit: int = 50) -> List[Version]:
        """
        Get version history for a file.
        
        Args:
            file_path: Path to the file
            limit: Maximum number of versions to return
            
        Returns:
            List of Version objects, newest first
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, file_path, content, timestamp, message, hash
            FROM versions
            WHERE file_path = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (file_path, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        versions = [
            Version(
                id=row[0],
                file_path=row[1],
                content=row[2],
                timestamp=row[3],
                message=row[4],
                hash=row[5]
            )
            for row in rows
        ]
        
        return versions
    
    def get_version(self, version_id: str) -> Optional[Version]:
        """
        Get a specific version by ID.
        
        Args:
            version_id: Version ID
            
        Returns:
            Version object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, file_path, content, timestamp, message, hash
            FROM versions
            WHERE id = ?
        """, (version_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return Version(
            id=row[0],
            file_path=row[1],
            content=row[2],
            timestamp=row[3],
            message=row[4],
            hash=row[5]
        )
    
    def rollback(self, file_path: str, version_id: str) -> str:
        """
        Rollback to a specific version.
        
        This creates a new version with the old content.
        
        Args:
            file_path: Path to the file
            version_id: Version ID to rollback to
            
        Returns:
            New version ID
        """
        # Get the target version
        target_version = self.get_version(version_id)
        
        if not target_version:
            raise ValueError(f"Version not found: {version_id}")
        
        if target_version.file_path != file_path:
            raise ValueError("Version does not belong to this file")
        
        # Create a new snapshot with the old content
        message = f"Rollback to version {version_id[:8]}"
        new_version_id = self.save_snapshot(file_path, target_version.content, message)
        
        return new_version_id
    
    def diff(
        self, 
        file_path: str, 
        version1_id: Optional[str] = None, 
        version2_id: Optional[str] = None,
        content1: Optional[str] = None,
        content2: Optional[str] = None
    ) -> str:
        """
        Generate a unified diff between two versions or content.
        
        Args:
            file_path: Path to the file
            version1_id: First version ID (or None to use content1)
            version2_id: Second version ID (or None to use content2)
            content1: First content (if version1_id is None)
            content2: Second content (if version2_id is None)
            
        Returns:
            Unified diff string
        """
        # Get content for version 1
        if version1_id:
            v1 = self.get_version(version1_id)
            if not v1:
                raise ValueError(f"Version not found: {version1_id}")
            text1 = v1.content
            label1 = f"Version {version1_id[:8]}"
        elif content1 is not None:
            text1 = content1
            label1 = "Current"
        else:
            raise ValueError("Must provide either version1_id or content1")
        
        # Get content for version 2
        if version2_id:
            v2 = self.get_version(version2_id)
            if not v2:
                raise ValueError(f"Version not found: {version2_id}")
            text2 = v2.content
            label2 = f"Version {version2_id[:8]}"
        elif content2 is not None:
            text2 = content2
            label2 = "New"
        else:
            raise ValueError("Must provide either version2_id or content2")
        
        # Generate unified diff
        diff = difflib.unified_diff(
            text1.splitlines(keepends=True),
            text2.splitlines(keepends=True),
            fromfile=label1,
            tofile=label2,
            lineterm=''
        )
        
        return ''.join(diff)
    
    def get_file_versions_count(self, file_path: str) -> int:
        """
        Get the number of versions for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of versions
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM versions WHERE file_path = ?
        """, (file_path,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def delete_file_versions(self, file_path: str) -> int:
        """
        Delete all versions for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of versions deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM versions WHERE file_path = ?
        """, (file_path,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted

