import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

class OrchestratorDB:
    """
    Shared database for Orchestration persistence.
    Handles storage of execution history, logs, and checkpoints.
    Supports multiple orchestrator runs via run_id isolation.
    """
    def __init__(self, db_path: str, run_id: Optional[str] = None):
        self.db_path = Path(db_path)
        self.run_id = run_id  # If None, will be set when first used
        self._init_db()

    def _init_db(self):
        """Initialize database tables with run_id support."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table for execution records (with run_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                cycle INTEGER,
                flow_index TEXT,
                inference_type TEXT,
                status TEXT,
                concept_inferred TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table for detailed logs (with run_id via execution_id relationship)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id INTEGER,
                log_content TEXT,
                FOREIGN KEY(execution_id) REFERENCES executions(id)
            )
        ''')

        # Table for checkpoints (with run_id, cycle, and inference_count as composite primary key)
        # This allows multiple checkpoints per cycle (intra-cycle checkpointing)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkpoints (
                run_id TEXT,
                cycle INTEGER,
                inference_count INTEGER DEFAULT 0,
                state_json TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (run_id, cycle, inference_count)
            )
        ''')

        # Table for run metadata (environment, configuration, etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS run_metadata (
                run_id TEXT PRIMARY KEY,
                metadata_json TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_executions_run_id ON executions(run_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_checkpoints_run_id ON checkpoints(run_id)')

        # Migration: Add run_id column to existing tables if they don't have it
        try:
            cursor.execute('PRAGMA table_info(executions)')
            columns = [row[1] for row in cursor.fetchall()]
            if 'run_id' not in columns:
                cursor.execute('ALTER TABLE executions ADD COLUMN run_id TEXT')
                logging.info("Migrated executions table to include run_id column")
        except Exception as e:
            logging.warning(f"Could not check/migrate executions table: {e}")

        # Migration: Handle existing checkpoints table
        try:
            cursor.execute('PRAGMA table_info(checkpoints)')
            columns = [row[1] for row in cursor.fetchall()]
            
            needs_migration = False
            migration_steps = []
            
            # Check if run_id column exists
            if 'run_id' not in columns:
                needs_migration = True
                migration_steps.append('run_id')
            
            # Check if inference_count column exists
            if 'inference_count' not in columns:
                needs_migration = True
                migration_steps.append('inference_count')
            
            if needs_migration:
                # SQLite doesn't support adding columns to PRIMARY KEY, so we need to recreate
                # Step 1: Add run_id if missing (with default value)
                if 'run_id' not in columns:
                    cursor.execute('ALTER TABLE checkpoints ADD COLUMN run_id TEXT DEFAULT "default"')
                    cursor.execute('UPDATE checkpoints SET run_id = "default" WHERE run_id IS NULL')
                
                # Step 2: Add inference_count if missing (with default value 0 for old checkpoints)
                if 'inference_count' not in columns:
                    cursor.execute('ALTER TABLE checkpoints ADD COLUMN inference_count INTEGER DEFAULT 0')
                    cursor.execute('UPDATE checkpoints SET inference_count = 0 WHERE inference_count IS NULL')
                
                # Step 3: Recreate table with proper composite primary key
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS checkpoints_new (
                        run_id TEXT,
                        cycle INTEGER,
                        inference_count INTEGER DEFAULT 0,
                        state_json TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (run_id, cycle, inference_count)
                    )
                ''')
                cursor.execute('''
                    INSERT INTO checkpoints_new (run_id, cycle, inference_count, state_json, timestamp)
                    SELECT run_id, cycle, inference_count, state_json, timestamp FROM checkpoints
                ''')
                cursor.execute('DROP TABLE checkpoints')
                cursor.execute('ALTER TABLE checkpoints_new RENAME TO checkpoints')
                logging.info(f"Migrated checkpoints table to include {', '.join(migration_steps)} column(s)")
        except Exception as e:
            logging.warning(f"Could not check/migrate checkpoints table: {e}")

        conn.commit()
        conn.close()
        logging.info(f"OrchestratorDB initialized at {self.db_path} with run_id support")

    def get_connection(self):
        """Get a database connection."""
        return sqlite3.connect(self.db_path)

    def save_run_metadata(self, run_id: str, metadata: Dict[str, Any]):
        """Save metadata for a specific run (environment, configuration, etc.)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            metadata_json = json.dumps(metadata)
            cursor.execute('''
                INSERT OR REPLACE INTO run_metadata (run_id, metadata_json)
                VALUES (?, ?)
            ''', (run_id, metadata_json))
            conn.commit()
            logging.info(f"Saved run metadata for run_id: {run_id}")
        except Exception as e:
            logging.error(f"Failed to save run metadata for run_id {run_id}: {e}")
        finally:
            conn.close()

    def get_run_metadata(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve metadata for a specific run."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT metadata_json FROM run_metadata WHERE run_id = ?', (run_id,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to decode metadata JSON for run_id {run_id}: {e}")
                    return None
            return None
        except Exception as e:
            logging.error(f"Failed to retrieve run metadata for run_id {run_id}: {e}")
            return None
        finally:
            conn.close()

    def insert_execution(self, cycle: int, flow_index: str, inference_type: str, status: str, concept_inferred: str) -> int:
        """Insert execution record and return its ID."""
        if not self.run_id:
            raise ValueError("run_id must be set before inserting executions. Set it via set_run_id() or pass it to __init__.")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO executions (run_id, cycle, flow_index, inference_type, status, concept_inferred)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.run_id, cycle, flow_index, inference_type, status, concept_inferred))
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

    def save_checkpoint(self, cycle: int, state: Dict[str, Any], inference_count: int = 0):
        """Save checkpoint state. inference_count allows multiple checkpoints per cycle."""
        if not self.run_id:
            raise ValueError("run_id must be set before saving checkpoints. Set it via set_run_id() or pass it to __init__.")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            state_json = json.dumps(state)
        except TypeError as e:
            conn.close()
            raise TypeError(f"JSON serialization failed for cycle {cycle}, inference {inference_count}: {e}. State may contain non-serializable objects.")
        
        cursor.execute('''
            INSERT OR REPLACE INTO checkpoints (run_id, cycle, inference_count, state_json)
            VALUES (?, ?, ?, ?)
        ''', (self.run_id, cycle, inference_count, state_json))
        conn.commit()
        conn.close()

    def load_latest_checkpoint(self, run_id: Optional[str] = None) -> Optional[Tuple[int, int, Dict[str, Any]]]:
        """Load the latest checkpoint for the specified run_id. Returns (cycle, inference_count, state_dict)."""
        target_run_id = run_id or self.run_id
        if not target_run_id:
            raise ValueError("run_id must be provided either as parameter or set via set_run_id()")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cycle, inference_count, state_json FROM checkpoints 
            WHERE run_id = ? 
            ORDER BY cycle DESC, inference_count DESC LIMIT 1
        ''', (target_run_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0], row[1], json.loads(row[2])
        return None
    
    def load_checkpoint_by_cycle(self, cycle: int, run_id: Optional[str] = None, inference_count: Optional[int] = None) -> Optional[Tuple[int, int, Dict[str, Any]]]:
        """
        Load a specific checkpoint by cycle number (and optionally inference_count) for the specified run_id.
        If inference_count is None, loads the latest checkpoint for that cycle.
        Returns (cycle, inference_count, state_dict).
        """
        target_run_id = run_id or self.run_id
        if not target_run_id:
            raise ValueError("run_id must be provided either as parameter or set via set_run_id()")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if inference_count is not None:
            # Load specific checkpoint at cycle and inference_count
            cursor.execute('''
                SELECT cycle, inference_count, state_json FROM checkpoints 
                WHERE run_id = ? AND cycle = ? AND inference_count = ?
            ''', (target_run_id, cycle, inference_count))
        else:
            # Load latest checkpoint for that cycle (highest inference_count)
            cursor.execute('''
                SELECT cycle, inference_count, state_json FROM checkpoints 
                WHERE run_id = ? AND cycle = ?
                ORDER BY inference_count DESC LIMIT 1
            ''', (target_run_id, cycle))
        
        row = cursor.fetchone()
        conn.close()
        if row:
            return row[0], row[1], json.loads(row[2])
        return None
    
    def list_checkpoints(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available checkpoints for the specified run_id with their cycle numbers, inference counts, and timestamps."""
        target_run_id = run_id or self.run_id
        if not target_run_id:
            raise ValueError("run_id must be provided either as parameter or set via set_run_id()")
        
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cycle, inference_count, timestamp FROM checkpoints 
            WHERE run_id = ? 
            ORDER BY cycle ASC, inference_count ASC
        ''', (target_run_id,))
        rows = cursor.fetchall()
        checkpoints = [{'cycle': row['cycle'], 'inference_count': row['inference_count'], 'timestamp': row['timestamp']} for row in rows]
        conn.close()
        return checkpoints
    
    def get_all_checkpoints(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all checkpoints for the specified run_id (or self.run_id if not provided), ordered by cycle and inference_count."""
        target_run_id = run_id or self.run_id
        if not target_run_id:
            raise ValueError("run_id must be provided either as parameter or set via set_run_id()")
        
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cycle, inference_count, state_json, timestamp FROM checkpoints 
            WHERE run_id = ? 
            ORDER BY cycle ASC, inference_count ASC
        ''', (target_run_id,))
        rows = cursor.fetchall()
        checkpoints = []
        for row in rows:
            checkpoints.append({
                'cycle': row['cycle'],
                'inference_count': row['inference_count'],
                'timestamp': row['timestamp'],
                'state': json.loads(row['state_json'])
            })
        conn.close()
        return checkpoints

    def get_execution_history(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve full execution history for the specified run_id (or self.run_id if not provided)."""
        target_run_id = run_id or self.run_id
        if not target_run_id:
            raise ValueError("run_id must be provided either as parameter or set via set_run_id()")
        
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM executions WHERE run_id = ? ORDER BY id ASC', (target_run_id,))
        rows = cursor.fetchall()
        history = [dict(row) for row in rows]
        conn.close()
        return history

    def get_execution_counts(self, run_id: Optional[str] = None) -> Dict[str, int]:
        """Get counts of executions by status for the specified run_id (or self.run_id if not provided)."""
        target_run_id = run_id or self.run_id
        if not target_run_id:
            raise ValueError("run_id must be provided either as parameter or set via set_run_id()")
        
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT status, COUNT(*) FROM executions 
            WHERE run_id = ? 
            GROUP BY status
        ''', (target_run_id,))
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

    def get_all_logs(self, run_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve all logs with execution metadata for the specified run_id (or self.run_id if not provided)."""
        target_run_id = run_id or self.run_id
        if not target_run_id:
            raise ValueError("run_id must be provided either as parameter or set via set_run_id()")
        
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT l.id, l.execution_id, l.log_content, e.cycle, e.flow_index, e.status 
            FROM logs l
            JOIN executions e ON l.execution_id = e.id
            WHERE e.run_id = ?
            ORDER BY l.id ASC
        ''', (target_run_id,))
        rows = cursor.fetchall()
        logs = [dict(row) for row in rows]
        conn.close()
        return logs

    def get_full_state(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve the full execution history combined with logs for the specified run_id.
        Useful for comprehensive export.
        """
        target_run_id = run_id or self.run_id
        history = self.get_execution_history(target_run_id)
        
        # Fetch all logs and map them by execution_id
        logs = self.get_all_logs(target_run_id)
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
    
    def set_run_id(self, run_id: str):
        """Set the run_id for this database instance."""
        self.run_id = run_id
        logging.info(f"Set run_id to {run_id}")
    
    def list_runs(self, include_metadata: bool = False) -> List[Dict[str, Any]]:
        """
        List all unique run_ids in the database with metadata.
        
        Args:
            include_metadata: If True, includes run configuration metadata (agent_frame_model, base_dir, etc.)
        
        Returns:
            List of dictionaries with run information
        """
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get run metadata from executions table
        cursor.execute('''
            SELECT run_id, 
                   MIN(timestamp) as first_execution,
                   MAX(timestamp) as last_execution,
                   COUNT(*) as execution_count,
                   MAX(cycle) as max_cycle
            FROM executions
            GROUP BY run_id
            ORDER BY first_execution DESC
        ''')
        rows = cursor.fetchall()
        runs = [dict(row) for row in rows]
        
        # Optionally include configuration metadata
        if include_metadata:
            for run in runs:
                run_id = run['run_id']
                metadata = self.get_run_metadata(run_id)
                if metadata:
                    run['config'] = metadata
        
        conn.close()
        return runs

