import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class OrchestratorDB:
    """
    Shared database for Orchestration persistence.
    Handles storage of execution history, logs, and checkpoints.
    """
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table for execution records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle INTEGER,
                flow_index TEXT,
                inference_type TEXT,
                status TEXT,
                concept_inferred TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table for detailed logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id INTEGER,
                log_content TEXT,
                FOREIGN KEY(execution_id) REFERENCES executions(id)
            )
        ''')

        # Table for checkpoints
        # Storing state as JSON blob
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkpoints (
                cycle INTEGER PRIMARY KEY,
                state_json TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()
        logging.info(f"OrchestratorDB initialized at {self.db_path}")

    def get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def insert_execution(self, cycle: int, flow_index: str, inference_type: str, status: str, concept_inferred: str) -> int:
        """Insert execution record and return its ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO executions (cycle, flow_index, inference_type, status, concept_inferred)
            VALUES (?, ?, ?, ?, ?)
        ''', (cycle, flow_index, inference_type, status, concept_inferred))
        execution_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return execution_id

    def insert_log(self, execution_id: int, log_content: str):
        """Insert log for an execution."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (execution_id, log_content)
            VALUES (?, ?)
        ''', (execution_id, log_content))
        conn.commit()
        conn.close()
    
    def update_execution_status(self, execution_id: int, status: str):
        """Update the status of an existing execution record."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE executions
            SET status = ?
            WHERE id = ?
        ''', (status, execution_id))
        conn.commit()
        conn.close()

    def save_checkpoint(self, cycle: int, state: Dict[str, Any]):
        """Save checkpoint state."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            state_json = json.dumps(state)
        except TypeError as e:
            conn.close()
            raise TypeError(f"JSON serialization failed for cycle {cycle}: {e}. State may contain non-serializable objects.")
        
        cursor.execute('''
            INSERT OR REPLACE INTO checkpoints (cycle, state_json)
            VALUES (?, ?)
        ''', (cycle, state_json))
        conn.commit()
        conn.close()

    def load_latest_checkpoint(self) -> Optional[Tuple[int, Dict[str, Any]]]:
        """Load the latest checkpoint. Returns (cycle, state_dict)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT cycle, state_json FROM checkpoints ORDER BY cycle DESC LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0], json.loads(row[1])
        return None
    
    def get_all_checkpoints(self) -> List[Dict[str, Any]]:
        """Retrieve all checkpoints ordered by cycle."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT cycle, state_json, timestamp FROM checkpoints ORDER BY cycle ASC')
        rows = cursor.fetchall()
        checkpoints = []
        for row in rows:
            checkpoints.append({
                'cycle': row['cycle'],
                'timestamp': row['timestamp'],
                'state': json.loads(row['state_json'])
            })
        conn.close()
        return checkpoints

    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Retrieve full execution history."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM executions ORDER BY id ASC')
        rows = cursor.fetchall()
        history = [dict(row) for row in rows]
        conn.close()
        return history

    def get_execution_counts(self) -> Dict[str, int]:
        """Get counts of executions by status."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT status, COUNT(*) FROM executions GROUP BY status')
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def get_logs_for_execution(self, execution_id: int) -> str:
        """Retrieve logs for a specific execution."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT log_content FROM logs WHERE execution_id = ?', (execution_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ""

    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Retrieve all logs with execution metadata."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.id, l.execution_id, l.log_content, e.cycle, e.flow_index, e.status 
            FROM logs l
            JOIN executions e ON l.execution_id = e.id
            ORDER BY l.id ASC
        ''')
        rows = cursor.fetchall()
        logs = [dict(row) for row in rows]
        conn.close()
        return logs

    def get_full_state(self) -> Dict[str, Any]:
        """
        Retrieve the full execution history combined with logs.
        Useful for comprehensive export.
        """
        history = self.get_execution_history()
        
        # Fetch all logs and map them by execution_id
        logs = self.get_all_logs()
        logs_by_exec_id = {log['execution_id']: log['log_content'] for log in logs}
        
        full_history = []
        for record in history:
            # Create a copy to avoid modifying the original list item if it's reused
            record_copy = record.copy()
            record_copy['log_content'] = logs_by_exec_id.get(record['id'], "")
            full_history.append(record_copy)
            
        return {
            "executions": full_history
        }

