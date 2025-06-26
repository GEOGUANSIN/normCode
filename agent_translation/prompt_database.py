"""
NormCode Prompt Database
SQLite database for storing and managing all agent prompts
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Prompt:
    """Prompt data structure"""
    id: int
    name: str
    agent_type: str
    prompt_type: str
    content: str
    version: str
    is_active: bool
    created_at: str
    updated_at: str
    metadata: Dict[str, Any]


class PromptDatabase:
    """SQLite database for managing NormCode agent prompts"""
    
    def __init__(self, db_path: str = "normcode_prompts.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create prompts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    prompt_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    version TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT,
                    UNIQUE(name, agent_type, prompt_type, version)
                )
            """)
            
            # Create prompt_versions table for version history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompt_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_id INTEGER,
                    version TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (prompt_id) REFERENCES prompts (id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_type ON prompts(agent_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_prompt_type ON prompts(prompt_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON prompts(is_active)")
            
            conn.commit()
    
    def insert_prompt(self, name: str, agent_type: str, prompt_type: str, content: str, 
                     version: str = "1.0", metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Insert a new prompt into the database
        
        Args:
            name: Prompt name/identifier
            agent_type: Type of agent (question_sequencing, in_question_analysis, integration)
            prompt_type: Type of prompt (question_type_analysis, sentence_chunking, etc.)
            content: The prompt content
            version: Prompt version
            metadata: Additional metadata
            
        Returns:
            int: Prompt ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT OR REPLACE INTO prompts 
                (name, agent_type, prompt_type, content, version, is_active, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?)
            """, (name, agent_type, prompt_type, content, version, now, now, metadata_json))
            
            prompt_id = cursor.lastrowid
            
            # Store version history
            cursor.execute("""
                INSERT INTO prompt_versions (prompt_id, version, content, created_at)
                VALUES (?, ?, ?, ?)
            """, (prompt_id, version, content, now))
            
            conn.commit()
            return prompt_id
    
    def get_prompt(self, agent_type: str, prompt_type: str, version: Optional[str] = None) -> Optional[Prompt]:
        """
        Get a prompt by agent type and prompt type
        
        Args:
            agent_type: Type of agent
            prompt_type: Type of prompt
            version: Specific version (if None, gets latest active version)
            
        Returns:
            Optional[Prompt]: The prompt if found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if version:
                cursor.execute("""
                    SELECT id, name, agent_type, prompt_type, content, version, is_active, 
                           created_at, updated_at, metadata
                    FROM prompts 
                    WHERE agent_type = ? AND prompt_type = ? AND version = ? AND is_active = 1
                """, (agent_type, prompt_type, version))
            else:
                cursor.execute("""
                    SELECT id, name, agent_type, prompt_type, content, version, is_active, 
                           created_at, updated_at, metadata
                    FROM prompts 
                    WHERE agent_type = ? AND prompt_type = ? AND is_active = 1
                    ORDER BY version DESC
                    LIMIT 1
                """, (agent_type, prompt_type))
            
            row = cursor.fetchone()
            
            if row:
                metadata = json.loads(row[9]) if row[9] else {}
                return Prompt(
                    id=row[0],
                    name=row[1],
                    agent_type=row[2],
                    prompt_type=row[3],
                    content=row[4],
                    version=row[5],
                    is_active=bool(row[6]),
                    created_at=row[7],
                    updated_at=row[8],
                    metadata=metadata
                )
            
            return None
    
    def get_prompts_by_agent(self, agent_type: str) -> List[Prompt]:
        """
        Get all prompts for a specific agent type
        
        Args:
            agent_type: Type of agent
            
        Returns:
            List[Prompt]: List of prompts for the agent
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, agent_type, prompt_type, content, version, is_active, 
                       created_at, updated_at, metadata
                FROM prompts 
                WHERE agent_type = ? AND is_active = 1
                ORDER BY prompt_type, version DESC
            """, (agent_type,))
            
            prompts = []
            for row in cursor.fetchall():
                metadata = json.loads(row[9]) if row[9] else {}
                prompts.append(Prompt(
                    id=row[0],
                    name=row[1],
                    agent_type=row[2],
                    prompt_type=row[3],
                    content=row[4],
                    version=row[5],
                    is_active=bool(row[6]),
                    created_at=row[7],
                    updated_at=row[8],
                    metadata=metadata
                ))
            
            return prompts
    
    def update_prompt(self, prompt_id: int, content: str, version: str = None, 
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update an existing prompt
        
        Args:
            prompt_id: ID of the prompt to update
            content: New prompt content
            version: New version (if None, increments current version)
            metadata: Updated metadata
            
        Returns:
            bool: True if update successful
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get current prompt
            cursor.execute("SELECT version FROM prompts WHERE id = ?", (prompt_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
            
            current_version = row[0]
            
            # Determine new version
            if version is None:
                # Auto-increment version
                try:
                    major, minor = current_version.split('.')
                    new_version = f"{major}.{int(minor) + 1}"
                except:
                    new_version = f"{current_version}.1"
            else:
                new_version = version
            
            now = datetime.now().isoformat()
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Update prompt
            cursor.execute("""
                UPDATE prompts 
                SET content = ?, version = ?, updated_at = ?, metadata = ?
                WHERE id = ?
            """, (content, new_version, now, metadata_json, prompt_id))
            
            # Store version history
            cursor.execute("""
                INSERT INTO prompt_versions (prompt_id, version, content, created_at)
                VALUES (?, ?, ?, ?)
            """, (prompt_id, new_version, content, now))
            
            conn.commit()
            return True
    
    def deactivate_prompt(self, prompt_id: int) -> bool:
        """
        Deactivate a prompt (soft delete)
        
        Args:
            prompt_id: ID of the prompt to deactivate
            
        Returns:
            bool: True if deactivation successful
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE prompts SET is_active = 0, updated_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), prompt_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def get_prompt_versions(self, prompt_id: int) -> List[Dict[str, Any]]:
        """
        Get version history for a prompt
        
        Args:
            prompt_id: ID of the prompt
            
        Returns:
            List[Dict[str, Any]]: Version history
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT version, content, created_at
                FROM prompt_versions
                WHERE prompt_id = ?
                ORDER BY created_at DESC
            """, (prompt_id,))
            
            versions = []
            for row in cursor.fetchall():
                versions.append({
                    "version": row[0],
                    "content": row[1],
                    "created_at": row[2]
                })
            
            return versions
    
    def search_prompts(self, search_term: str) -> List[Prompt]:
        """
        Search prompts by content or name
        
        Args:
            search_term: Search term
            
        Returns:
            List[Prompt]: Matching prompts
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, agent_type, prompt_type, content, version, is_active, 
                       created_at, updated_at, metadata
                FROM prompts 
                WHERE (content LIKE ? OR name LIKE ?) AND is_active = 1
                ORDER BY agent_type, prompt_type
            """, (f"%{search_term}%", f"%{search_term}%"))
            
            prompts = []
            for row in cursor.fetchall():
                metadata = json.loads(row[9]) if row[9] else {}
                prompts.append(Prompt(
                    id=row[0],
                    name=row[1],
                    agent_type=row[2],
                    prompt_type=row[3],
                    content=row[4],
                    version=row[5],
                    is_active=bool(row[6]),
                    created_at=row[7],
                    updated_at=row[8],
                    metadata=metadata
                ))
            
            return prompts


class PromptManager:
    """High-level prompt management interface"""
    
    def __init__(self, db_path: str = "normcode_prompts.db"):
        self.db = PromptDatabase(db_path)
        self.load_default_prompts()
    
    def load_default_prompts(self):
        """Load default prompts into the database"""
        default_prompts = self._get_default_prompts()
        
        for prompt in default_prompts:
            # Check if prompt already exists
            existing = self.db.get_prompt(prompt["agent_type"], prompt["prompt_type"])
            if not existing:
                self.db.insert_prompt(
                    name=prompt["name"],
                    agent_type=prompt["agent_type"],
                    prompt_type=prompt["prompt_type"],
                    content=prompt["content"],
                    version=prompt.get("version", "1.0"),
                    metadata=prompt.get("metadata", {})
                )
    
    def get_prompt(self, agent_type: str, prompt_type: str, version: Optional[str] = None) -> Optional[Prompt]:
        """Get a prompt by agent type and prompt type"""
        return self.db.get_prompt(agent_type, prompt_type, version)
    
    def format_prompt(self, agent_type: str, prompt_type: str, **kwargs) -> Optional[str]:
        """
        Get and format a prompt with the given parameters
        
        Args:
            agent_type: Type of agent
            prompt_type: Type of prompt
            **kwargs: Parameters to format into the prompt
            
        Returns:
            Optional[str]: Formatted prompt content
        """
        prompt = self.get_prompt(agent_type, prompt_type)
        if prompt:
            return prompt.content.format(**kwargs)
        return None
    
    def update_prompt_content(self, agent_type: str, prompt_type: str, new_content: str, 
                            version: str = None) -> bool:
        """Update prompt content"""
        prompt = self.get_prompt(agent_type, prompt_type)
        if prompt:
            return self.db.update_prompt(prompt.id, new_content, version)
        return False 