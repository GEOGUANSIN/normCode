"""
Minimal ResultManager: Only supports saving results to a file or SQLite database.
"""

import os
import json
import sqlite3
from typing import Optional, Dict, Any
from datetime import datetime

class ResultManager:
    """
    Minimal result manager. Supports saving results to a file or SQLite database.
    Usage:
        manager = ResultManager(mode="file", results_dir="sequence/results")
        manager.save_result(...)
    or:
        manager = ResultManager(mode="database", db_path="sequence/normcode_results.db")
        manager.save_result(...)
    """
    def __init__(self, mode: str = "file", results_dir: str = "sequence/results", db_path: str = "sequence/normcode_results.db"):
        assert mode in ("file", "database"), "mode must be 'file' or 'database'"
        self.mode = mode
        self.results_dir = results_dir
        self.db_path = db_path
        if mode == "file":
            os.makedirs(results_dir, exist_ok=True)
        elif mode == "database":
            self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_type TEXT NOT NULL,
                    result_type TEXT NOT NULL,
                    session_id TEXT,
                    input_hash TEXT,
                    result_data TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def save_result(self, agent_type: str, result_type: str, result_data: Any,
                    session_id: Optional[str] = None, input_hash: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Save result to file or database. Returns file path or DB row id as string.
        """
        if self.mode == "file":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{agent_type}_{result_type}_{session_id or timestamp}.json"
            file_path = os.path.join(self.results_dir, filename)
            result_obj = {
                'agent_type': agent_type,
                'result_type': result_type,
                'session_id': session_id,
                'input_hash': input_hash,
                'result_data': result_data,
                'metadata': metadata,
                'created_at': datetime.now().isoformat(),
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result_obj, f, ensure_ascii=False, indent=2)
            return file_path
        else:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                serialized_data = json.dumps(result_data, ensure_ascii=False)
                serialized_metadata = json.dumps(metadata, ensure_ascii=False) if metadata else None
                cursor.execute(
                    """
                    INSERT INTO results (agent_type, result_type, session_id, input_hash, result_data, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (agent_type, result_type, session_id, input_hash, serialized_data, serialized_metadata)
                )
                conn.commit()
                return str(cursor.lastrowid) 