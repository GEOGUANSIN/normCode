"""
Run Database Inspector API

Endpoints for inspecting run databases, checkpoints, and execution history.
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException

from service import get_config

router = APIRouter()


def _get_run_db_path(run_id: str) -> Path:
    """Get the database path for a run, checking both active and historical."""
    cfg = get_config()
    run_dir = cfg.runs_dir / run_id
    db_path = run_dir / "run.db"
    
    if not db_path.exists():
        raise HTTPException(404, f"Database not found for run: {run_id}")
    
    return db_path


@router.get("/api/runs/{run_id}/db/overview")
async def get_run_db_overview(run_id: str):
    """
    Get an overview of the run's database structure and contents.
    Shows tables, row counts, and general statistics.
    """
    db_path = _get_run_db_path(run_id)
    
    try:
        db_size = db_path.stat().st_size
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row[0] for row in cursor.fetchall()]
        
        tables = []
        for table_name in table_names:
            # Get column info
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [{"name": row[1], "type": row[2]} for row in cursor.fetchall()]
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            tables.append({
                "name": table_name,
                "columns": columns,
                "row_count": row_count,
            })
        
        # Get counts
        total_executions = 0
        total_checkpoints = 0
        
        if "executions" in table_names:
            cursor.execute("SELECT COUNT(*) FROM executions")
            total_executions = cursor.fetchone()[0] or 0
        
        if "checkpoints" in table_names:
            cursor.execute("SELECT COUNT(*) FROM checkpoints")
            total_checkpoints = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "run_id": run_id,
            "path": str(db_path),
            "size_bytes": db_size,
            "tables": tables,
            "total_executions": total_executions,
            "total_checkpoints": total_checkpoints,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to read database: {e}")


@router.get("/api/runs/{run_id}/db/executions")
async def get_run_executions(
    run_id: str,
    include_logs: bool = False,
    limit: int = 500,
    offset: int = 0,
):
    """
    Get execution history for a run.
    Optionally includes log content for each execution.
    """
    db_path = _get_run_db_path(run_id)
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if include_logs:
            # Join with logs table
            cursor.execute("""
                SELECT e.id, e.run_id, e.cycle, e.flow_index, e.inference_type,
                       e.status, e.concept_inferred, e.timestamp, l.log_content
                FROM executions e
                LEFT JOIN logs l ON e.id = l.execution_id
                WHERE e.run_id = ?
                ORDER BY e.id
                LIMIT ? OFFSET ?
            """, (run_id, limit, offset))
        else:
            cursor.execute("""
                SELECT id, run_id, cycle, flow_index, inference_type,
                       status, concept_inferred, timestamp
                FROM executions
                WHERE run_id = ?
                ORDER BY id
                LIMIT ? OFFSET ?
            """, (run_id, limit, offset))
        
        executions = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM executions WHERE run_id = ?", (run_id,))
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "run_id": run_id,
            "executions": executions,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to read executions: {e}")


@router.get("/api/runs/{run_id}/db/executions/{execution_id}/logs")
async def get_execution_logs(run_id: str, execution_id: int):
    """Get detailed logs for a specific execution."""
    db_path = _get_run_db_path(run_id)
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT log_content FROM logs WHERE execution_id = ?
        """, (execution_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        log_content = row['log_content'] if row else "(No logs recorded)"
        
        return {
            "run_id": run_id,
            "execution_id": execution_id,
            "log_content": log_content,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to read logs: {e}")


@router.get("/api/runs/{run_id}/db/statistics")
async def get_run_statistics(run_id: str):
    """Get statistics about a run."""
    db_path = _get_run_db_path(run_id)
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get status counts
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM executions 
            WHERE run_id = ? 
            GROUP BY status
        """, (run_id,))
        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
        
        # Get max cycle
        cursor.execute("""
            SELECT MAX(cycle) as max_cycle 
            FROM executions 
            WHERE run_id = ?
        """, (run_id,))
        max_cycle = cursor.fetchone()["max_cycle"] or 0
        
        # Get unique concepts
        cursor.execute("""
            SELECT COUNT(DISTINCT concept_inferred) as unique_concepts 
            FROM executions 
            WHERE run_id = ? AND concept_inferred IS NOT NULL
        """, (run_id,))
        unique_concepts = cursor.fetchone()["unique_concepts"] or 0
        
        # Get execution by type
        cursor.execute("""
            SELECT inference_type, COUNT(*) as count 
            FROM executions 
            WHERE run_id = ? 
            GROUP BY inference_type
        """, (run_id,))
        execution_by_type = {row["inference_type"] or "unknown": row["count"] for row in cursor.fetchall()}
        
        # Total executions
        cursor.execute("SELECT COUNT(*) FROM executions WHERE run_id = ?", (run_id,))
        total_executions = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "run_id": run_id,
            "total_executions": total_executions,
            "completed": status_counts.get("completed", 0),
            "failed": status_counts.get("failed", 0),
            "in_progress": status_counts.get("in_progress", 0),
            "cycles_completed": max_cycle,
            "unique_concepts_inferred": unique_concepts,
            "execution_by_type": execution_by_type,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get statistics: {e}")


@router.get("/api/runs/{run_id}/db/checkpoints")
async def list_run_checkpoints(run_id: str):
    """List all available checkpoints for a run."""
    db_path = _get_run_db_path(run_id)
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cycle, inference_count, timestamp,
                   LENGTH(state_json) as state_size
            FROM checkpoints
            WHERE run_id = ?
            ORDER BY cycle ASC, inference_count ASC
        """, (run_id,))
        
        checkpoints = []
        for row in cursor.fetchall():
            checkpoints.append({
                "cycle": row["cycle"],
                "inference_count": row["inference_count"],
                "timestamp": row["timestamp"],
                "state_size": row["state_size"],
            })
        
        conn.close()
        
        return {
            "run_id": run_id,
            "checkpoints": checkpoints,
            "total_count": len(checkpoints),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to list checkpoints: {e}")


@router.get("/api/runs/{run_id}/db/checkpoints/{cycle}")
async def get_checkpoint_state(
    run_id: str, 
    cycle: int,
    inference_count: Optional[int] = None,
):
    """
    Get the full state data stored in a checkpoint.
    This includes blackboard, workspace, tracker, and completed concepts.
    """
    db_path = _get_run_db_path(run_id)
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if inference_count is not None:
            cursor.execute("""
                SELECT cycle, inference_count, state_json, timestamp 
                FROM checkpoints 
                WHERE run_id = ? AND cycle = ? AND inference_count = ?
            """, (run_id, cycle, inference_count))
        else:
            cursor.execute("""
                SELECT cycle, inference_count, state_json, timestamp 
                FROM checkpoints 
                WHERE run_id = ? AND cycle = ?
                ORDER BY inference_count DESC
                LIMIT 1
            """, (run_id, cycle))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(404, f"Checkpoint not found for cycle {cycle}")
        
        state = json.loads(row["state_json"])
        
        return {
            "run_id": run_id,
            "cycle": row["cycle"],
            "inference_count": row["inference_count"],
            "timestamp": row["timestamp"],
            "blackboard": state.get("blackboard"),
            "workspace": state.get("workspace"),
            "tracker": state.get("tracker"),
            "completed_concepts": state.get("completed_concepts"),
            "signatures": state.get("signatures"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get checkpoint: {e}")


@router.get("/api/runs/{run_id}/db/blackboard")
async def get_blackboard_summary(run_id: str, cycle: Optional[int] = None):
    """
    Get a summary of the blackboard state from a checkpoint.
    This provides a quick overview of concept and item statuses.
    """
    db_path = _get_run_db_path(run_id)
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if cycle is not None:
            cursor.execute("""
                SELECT state_json FROM checkpoints 
                WHERE run_id = ? AND cycle = ?
                ORDER BY inference_count DESC
                LIMIT 1
            """, (run_id, cycle))
        else:
            cursor.execute("""
                SELECT state_json FROM checkpoints 
                WHERE run_id = ?
                ORDER BY cycle DESC, inference_count DESC
                LIMIT 1
            """, (run_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(404, "No checkpoint found for this run")
        
        state = json.loads(row["state_json"])
        blackboard = state.get("blackboard", {})
        
        concept_statuses = blackboard.get("concept_statuses", {})
        item_statuses = blackboard.get("item_statuses", {})
        item_results = blackboard.get("item_results", {})
        
        # Count completed
        completed_concepts = sum(1 for s in concept_statuses.values() if s == "complete")
        completed_items = sum(1 for s in item_statuses.values() if s == "completed")
        
        return {
            "run_id": run_id,
            "concept_statuses": concept_statuses,
            "item_statuses": item_statuses,
            "item_results": item_results,
            "concept_count": len(concept_statuses),
            "item_count": len(item_statuses),
            "completed_concepts": completed_concepts,
            "completed_items": completed_items,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get blackboard: {e}")


@router.get("/api/runs/{run_id}/db/concepts")
async def get_completed_concepts(run_id: str, cycle: Optional[int] = None):
    """
    Get the completed concepts with their reference data from a checkpoint.
    """
    db_path = _get_run_db_path(run_id)
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if cycle is not None:
            cursor.execute("""
                SELECT state_json FROM checkpoints 
                WHERE run_id = ? AND cycle = ?
                ORDER BY inference_count DESC
                LIMIT 1
            """, (run_id, cycle))
        else:
            cursor.execute("""
                SELECT state_json FROM checkpoints 
                WHERE run_id = ?
                ORDER BY cycle DESC, inference_count DESC
                LIMIT 1
            """, (run_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(404, "No checkpoint found for this run")
        
        state = json.loads(row["state_json"])
        completed_concepts = state.get("completed_concepts", {})
        
        # Process each concept to extract useful info
        result = {}
        for name, data in completed_concepts.items():
            if isinstance(data, dict):
                tensor_preview = None
                if "tensor" in data:
                    tensor = data["tensor"]
                    if isinstance(tensor, (list, dict)):
                        if isinstance(tensor, list) and len(tensor) > 5:
                            tensor_preview = f"[...{len(tensor)} items...]"
                        elif isinstance(tensor, dict) and len(tensor) > 5:
                            tensor_preview = f"{{...{len(tensor)} keys...}}"
                        else:
                            tensor_preview = str(tensor)[:200]
                    else:
                        tensor_preview = str(tensor)[:200]
                
                result[name] = {
                    "has_tensor": "tensor" in data,
                    "shape": data.get("shape"),
                    "axes": data.get("axes"),
                    "data_preview": tensor_preview,
                }
            else:
                result[name] = {"value": str(data)[:200]}
        
        return {
            "run_id": run_id,
            "concepts": result,
            "count": len(result),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to get concepts: {e}")

