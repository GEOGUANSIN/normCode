"""
Iteration History Service - Stores historical data from loop iterations.

This service handles:
- Saving concept reference snapshots before loop reset
- Retrieving historical values for a concept across iterations
- Providing iteration timeline data for the DetailPanel UI
"""

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IterationHistoryService:
    """
    Service for storing and retrieving historical iteration data.
    
    During quantifying/looping sequences, concept references are cleared
    between iterations. This service captures snapshots before the reset,
    allowing the UI to display historical values from past iterations.
    """
    
    def __init__(self):
        self._db_path: Optional[str] = None
        self._initialized = False
    
    def initialize(self, db_path: str):
        """
        Initialize the service with a database path.
        Creates the iteration_history table if it doesn't exist.
        
        Args:
            db_path: Path to the orchestration.db file
        """
        self._db_path = db_path
        self._init_tables()
        self._initialized = True
        logger.info(f"IterationHistoryService initialized with db: {db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        if not self._db_path:
            raise RuntimeError("IterationHistoryService not initialized. Call initialize() first.")
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self._db_path)
    
    def _init_tables(self):
        """Create iteration_history table if it doesn't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS iteration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                flow_index TEXT NOT NULL,
                concept_name TEXT NOT NULL,
                iteration_index INTEGER NOT NULL,
                cycle_number INTEGER NOT NULL,
                reference_data TEXT,
                axes TEXT,
                shape TEXT,
                timestamp REAL NOT NULL
            )
        """)
        
        # Create indexes for efficient querying
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_iteration_history_run_concept 
            ON iteration_history(run_id, concept_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_iteration_history_run_flow 
            ON iteration_history(run_id, flow_index)
        """)
        
        conn.commit()
        conn.close()
        logger.debug("iteration_history table initialized")
    
    def save_iteration_snapshot(
        self,
        run_id: str,
        flow_index: str,
        concept_name: str,
        iteration_index: int,
        cycle_number: int,
        reference: Any,
    ) -> bool:
        """
        Save a snapshot of concept reference data for a specific iteration.
        
        Args:
            run_id: The current run ID
            flow_index: The flow_index of the inference being reset
            concept_name: The name of the concept
            iteration_index: The iteration number within the loop
            cycle_number: The orchestrator cycle number
            reference: The Reference object to snapshot
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self._initialized:
            logger.warning("IterationHistoryService not initialized, skipping snapshot")
            return False
        
        try:
            # Extract data from reference
            ref_data = None
            axes = []
            shape = []
            
            if reference is not None:
                # Get tensor data
                if hasattr(reference, 'tensor'):
                    ref_data = reference.tensor
                elif hasattr(reference, 'data'):
                    ref_data = reference.data
                
                # Get axes
                if hasattr(reference, 'axes') and reference.axes:
                    axes = [
                        axis.name if hasattr(axis, 'name') else str(axis) 
                        for axis in reference.axes
                    ]
                
                # Get shape
                if hasattr(reference, 'shape'):
                    shape = list(reference.shape) if reference.shape else []
            
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO iteration_history 
                (run_id, flow_index, concept_name, iteration_index, cycle_number, 
                 reference_data, axes, shape, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                flow_index,
                concept_name,
                iteration_index,
                cycle_number,
                json.dumps(ref_data) if ref_data is not None else None,
                json.dumps(axes),
                json.dumps(shape),
                time.time()
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(
                f"Saved iteration snapshot: {concept_name} "
                f"(iter={iteration_index}, cycle={cycle_number})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to save iteration snapshot for {concept_name}: {e}")
            return False
    
    def get_iteration_history(
        self,
        run_id: str,
        concept_name: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get historical values for a concept across iterations.
        
        Args:
            run_id: The run ID to query
            concept_name: The concept name to get history for
            limit: Maximum number of entries to return
            
        Returns:
            List of historical entries, ordered by iteration (newest first)
        """
        if not self._initialized:
            return []
        
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT iteration_index, cycle_number, flow_index, 
                       reference_data, axes, shape, timestamp
                FROM iteration_history
                WHERE run_id = ? AND concept_name = ?
                ORDER BY iteration_index DESC
                LIMIT ?
            """, (run_id, concept_name, limit))
            
            results = []
            for row in cursor.fetchall():
                entry = {
                    "iteration_index": row[0],
                    "cycle_number": row[1],
                    "flow_index": row[2],
                    "data": json.loads(row[3]) if row[3] else None,
                    "axes": json.loads(row[4]) if row[4] else [],
                    "shape": json.loads(row[5]) if row[5] else [],
                    "timestamp": row[6],
                    "has_data": row[3] is not None,
                }
                results.append(entry)
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Failed to get iteration history for {concept_name}: {e}")
            return []
    
    def get_flow_iteration_history(
        self,
        run_id: str,
        flow_index: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get historical values for all concepts at a specific flow_index.
        
        Args:
            run_id: The run ID to query
            flow_index: The flow_index to get history for
            limit: Maximum number of entries to return
            
        Returns:
            List of historical entries for this flow_index
        """
        if not self._initialized:
            return []
        
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT concept_name, iteration_index, cycle_number, 
                       reference_data, axes, shape, timestamp
                FROM iteration_history
                WHERE run_id = ? AND flow_index = ?
                ORDER BY iteration_index DESC
                LIMIT ?
            """, (run_id, flow_index, limit))
            
            results = []
            for row in cursor.fetchall():
                entry = {
                    "concept_name": row[0],
                    "iteration_index": row[1],
                    "cycle_number": row[2],
                    "data": json.loads(row[3]) if row[3] else None,
                    "axes": json.loads(row[4]) if row[4] else [],
                    "shape": json.loads(row[5]) if row[5] else [],
                    "timestamp": row[6],
                    "has_data": row[3] is not None,
                }
                results.append(entry)
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Failed to get flow iteration history for {flow_index}: {e}")
            return []
    
    def get_iteration_count(self, run_id: str, concept_name: str) -> int:
        """
        Get the current iteration count for a concept.
        
        Args:
            run_id: The run ID
            concept_name: The concept name
            
        Returns:
            The highest iteration index + 1, or 0 if no history
        """
        if not self._initialized:
            return 0
        
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT MAX(iteration_index)
                FROM iteration_history
                WHERE run_id = ? AND concept_name = ?
            """, (run_id, concept_name))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0] is not None:
                return result[0] + 1
            return 0
            
        except Exception as e:
            logger.error(f"Failed to get iteration count for {concept_name}: {e}")
            return 0
    
    def clear_run_history(self, run_id: str) -> bool:
        """
        Clear all iteration history for a run.
        
        Args:
            run_id: The run ID to clear history for
            
        Returns:
            True if cleared successfully
        """
        if not self._initialized:
            return False
        
        try:
            conn = self._get_connection()
            conn.execute(
                "DELETE FROM iteration_history WHERE run_id = ?",
                (run_id,)
            )
            conn.commit()
            conn.close()
            
            logger.info(f"Cleared iteration history for run {run_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear iteration history for {run_id}: {e}")
            return False


# Global singleton instance
iteration_history_service = IterationHistoryService()

