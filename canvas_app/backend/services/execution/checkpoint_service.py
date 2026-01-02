"""
Checkpoint Service - Manages execution checkpoints.

This service handles:
- Listing runs and checkpoints from the database
- Getting run metadata
- Deleting runs
- Resuming and forking from checkpoints
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class CheckpointService:
    """
    Service for managing execution checkpoints.
    
    Provides methods to list, load, and manage checkpoints stored
    in the orchestration database.
    """
    
    async def list_runs(self, db_path: str) -> List[Dict[str, Any]]:
        """
        List all runs stored in the checkpoint database.
        
        Args:
            db_path: Path to the orchestration.db file
            
        Returns:
            List of run dicts with: run_id, first_execution, last_execution, 
            execution_count, max_cycle, config (if include_metadata)
        """
        from infra._orchest._db import OrchestratorDB
        
        try:
            db = OrchestratorDB(db_path)
            runs = db.list_runs(include_metadata=True)
            return runs
        except Exception as e:
            logger.error(f"Failed to list runs from {db_path}: {e}")
            return []
    
    async def list_checkpoints(self, db_path: str, run_id: str) -> List[Dict[str, Any]]:
        """
        List all checkpoints for a specific run.
        
        Args:
            db_path: Path to the orchestration.db file
            run_id: The run ID to list checkpoints for
            
        Returns:
            List of checkpoint dicts with: cycle, inference_count, timestamp
        """
        from infra._orchest._db import OrchestratorDB
        
        try:
            db = OrchestratorDB(db_path, run_id=run_id)
            checkpoints = db.list_checkpoints(run_id=run_id)
            # Sort by cycle descending (newest first)
            checkpoints.sort(key=lambda x: (x['cycle'], x['inference_count']), reverse=True)
            return checkpoints
        except Exception as e:
            logger.error(f"Failed to list checkpoints for run {run_id}: {e}")
            return []
    
    async def get_run_metadata(self, db_path: str, run_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific run."""
        from infra._orchest._db import OrchestratorDB

        try:
            db = OrchestratorDB(db_path, run_id=run_id)
            return db.get_run_metadata(run_id)
        except Exception as e:
            logger.error(f"Failed to get metadata for run {run_id}: {e}")
            return None

    async def delete_run(self, db_path: str, run_id: str) -> Dict[str, Any]:
        """
        Delete a run and all its checkpoints from the database.
        
        Args:
            db_path: Path to the orchestration database
            run_id: The run ID to delete
            
        Returns:
            Dict with success status and message
        """
        from infra._orchest._db import OrchestratorDB
        
        def _do_delete():
            db = OrchestratorDB(db_path, run_id=run_id)
            conn = db.get_connection()
            cursor = conn.cursor()
            try:
                # Delete all checkpoints for this run
                cursor.execute("DELETE FROM checkpoints WHERE run_id = ?", (run_id,))
                
                # Delete run metadata
                cursor.execute("DELETE FROM run_metadata WHERE run_id = ?", (run_id,))
                
                # Delete execution records
                cursor.execute("DELETE FROM executions WHERE run_id = ?", (run_id,))
                
                # Commit the changes
                conn.commit()
            finally:
                conn.close()
        
        try:
            await asyncio.to_thread(_do_delete)
            
            logger.info(f"Deleted run {run_id} from {db_path}")
            return {"success": True, "message": f"Run {run_id} deleted successfully"}
        except Exception as e:
            logger.error(f"Failed to delete run {run_id}: {e}")
            return {"success": False, "message": str(e)}
    
    async def save_checkpoint(
        self,
        orchestrator: Any,
        cycle_count: int,
        inference_count: int = 0,
    ) -> bool:
        """
        Save a checkpoint for the current execution state.
        
        Args:
            orchestrator: The Orchestrator instance
            cycle_count: Current cycle number
            inference_count: Number of inferences in this cycle (0 = end of cycle)
            
        Returns:
            True if checkpoint was saved successfully
        """
        if not orchestrator or not orchestrator.checkpoint_manager:
            return False
        
        try:
            await asyncio.to_thread(
                orchestrator.checkpoint_manager.save_state,
                cycle_count,
                orchestrator,
                inference_count
            )
            logger.debug(f"Checkpoint saved for cycle {cycle_count}")
            return True
        except Exception as e:
            logger.warning(f"Failed to save checkpoint: {e}")
            return False


# Global checkpoint service instance
checkpoint_service = CheckpointService()


