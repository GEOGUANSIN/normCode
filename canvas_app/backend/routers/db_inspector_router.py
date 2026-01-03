"""
Database Inspector Router - Endpoints for exploring orchestrator databases.

Provides read-only inspection of:
- Execution history with logs
- Checkpoint states (blackboard, workspace, concepts)
- Run statistics and metadata
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import logging
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Schemas
# ============================================================================

class ExecutionRecord(BaseModel):
    """Single execution record from the database."""
    id: int
    run_id: Optional[str] = None
    cycle: int
    flow_index: str
    inference_type: Optional[str] = None
    status: str
    concept_inferred: Optional[str] = None
    timestamp: Optional[str] = None
    log_content: Optional[str] = None


class ExecutionHistoryResponse(BaseModel):
    """Response containing execution history."""
    executions: List[ExecutionRecord]
    total_count: int
    run_id: str


class CheckpointStateResponse(BaseModel):
    """Response containing detailed checkpoint state."""
    cycle: int
    inference_count: int
    timestamp: Optional[str] = None
    blackboard: Optional[Dict[str, Any]] = None
    workspace: Optional[Dict[str, Any]] = None
    tracker: Optional[Dict[str, Any]] = None
    completed_concepts: Optional[Dict[str, Any]] = None
    signatures: Optional[Dict[str, Any]] = None


class ConceptStatusEntry(BaseModel):
    """Status of a single concept."""
    concept_name: str
    status: str
    has_reference: bool
    reference_shape: Optional[List[int]] = None
    axes: Optional[List[str]] = None


class BlackboardSummary(BaseModel):
    """Summary of blackboard state."""
    concept_statuses: Dict[str, str]
    item_statuses: Dict[str, str]
    item_results: Dict[str, str]
    item_completion_details: Dict[str, str]
    execution_counts: Dict[str, int]
    concept_count: int
    item_count: int
    completed_concepts: int
    completed_items: int


class RunStatistics(BaseModel):
    """Statistics about a run."""
    run_id: str
    total_executions: int
    completed: int
    failed: int
    in_progress: int
    cycles_completed: int
    unique_concepts_inferred: int
    execution_by_type: Dict[str, int]


class TableSchema(BaseModel):
    """Schema information for a database table."""
    name: str
    columns: List[Dict[str, str]]
    row_count: int


class DatabaseOverview(BaseModel):
    """Overview of database structure and contents."""
    path: str
    size_bytes: int
    tables: List[TableSchema]
    run_count: int
    total_executions: int
    total_checkpoints: int


# ============================================================================
# Helper Functions
# ============================================================================

def _get_db(db_path: str):
    """Get an OrchestratorDB instance."""
    from infra._orchest._db import OrchestratorDB
    return OrchestratorDB(db_path)


async def _run_in_thread(func, *args, **kwargs):
    """Run a blocking function in a thread pool."""
    return await asyncio.to_thread(func, *args, **kwargs)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/overview", response_model=DatabaseOverview)
async def get_database_overview(
    db_path: str = Query(..., description="Path to the orchestration.db file")
):
    """
    Get an overview of the database structure and contents.
    Shows tables, row counts, and general statistics.
    """
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail=f"Database not found: {db_path}")
    
    def _get_overview():
        import sqlite3
        
        db_size = os.path.getsize(db_path)
        conn = sqlite3.connect(db_path)
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
            
            tables.append(TableSchema(
                name=table_name,
                columns=columns,
                row_count=row_count
            ))
        
        # Get counts
        run_count = 0
        total_executions = 0
        total_checkpoints = 0
        
        if "executions" in table_names:
            cursor.execute("SELECT COUNT(DISTINCT run_id) FROM executions")
            run_count = cursor.fetchone()[0] or 0
            cursor.execute("SELECT COUNT(*) FROM executions")
            total_executions = cursor.fetchone()[0] or 0
        
        if "checkpoints" in table_names:
            cursor.execute("SELECT COUNT(*) FROM checkpoints")
            total_checkpoints = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return DatabaseOverview(
            path=db_path,
            size_bytes=db_size,
            tables=tables,
            run_count=run_count,
            total_executions=total_executions,
            total_checkpoints=total_checkpoints
        )
    
    try:
        return await _run_in_thread(_get_overview)
    except Exception as e:
        logger.exception(f"Failed to get database overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/executions", response_model=ExecutionHistoryResponse)
async def get_execution_history(
    run_id: str,
    db_path: str = Query(..., description="Path to orchestration.db"),
    include_logs: bool = Query(False, description="Include log content for each execution"),
    limit: int = Query(500, description="Maximum number of records to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Get execution history for a specific run.
    Optionally includes log content for each execution.
    """
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    def _get_history():
        db = _get_db(db_path)
        db.set_run_id(run_id)
        
        if include_logs:
            # Get full state with logs
            full_state = db.get_full_state(run_id)
            executions = full_state.get("executions", [])
        else:
            executions = db.get_execution_history(run_id)
        
        total_count = len(executions)
        
        # Apply pagination
        paginated = executions[offset:offset + limit]
        
        return {
            "executions": [ExecutionRecord(**e) for e in paginated],
            "total_count": total_count,
            "run_id": run_id
        }
    
    try:
        result = await _run_in_thread(_get_history)
        return ExecutionHistoryResponse(**result)
    except Exception as e:
        logger.exception(f"Failed to get execution history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/executions/{execution_id}/logs")
async def get_execution_logs(
    run_id: str,
    execution_id: int,
    db_path: str = Query(..., description="Path to orchestration.db")
):
    """Get detailed logs for a specific execution."""
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    def _get_logs():
        db = _get_db(db_path)
        log_content = db.get_logs_for_execution(execution_id)
        return {"execution_id": execution_id, "log_content": log_content}
    
    try:
        return await _run_in_thread(_get_logs)
    except Exception as e:
        logger.exception(f"Failed to get execution logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/statistics", response_model=RunStatistics)
async def get_run_statistics(
    run_id: str,
    db_path: str = Query(..., description="Path to orchestration.db")
):
    """Get statistics about a specific run."""
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    def _get_stats():
        import sqlite3
        
        conn = sqlite3.connect(db_path)
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
        
        return RunStatistics(
            run_id=run_id,
            total_executions=total_executions,
            completed=status_counts.get("completed", 0),
            failed=status_counts.get("failed", 0),
            in_progress=status_counts.get("in_progress", 0),
            cycles_completed=max_cycle,
            unique_concepts_inferred=unique_concepts,
            execution_by_type=execution_by_type
        )
    
    try:
        return await _run_in_thread(_get_stats)
    except Exception as e:
        logger.exception(f"Failed to get run statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/checkpoints/{cycle}", response_model=CheckpointStateResponse)
async def get_checkpoint_state(
    run_id: str,
    cycle: int,
    db_path: str = Query(..., description="Path to orchestration.db"),
    inference_count: Optional[int] = Query(None, description="Specific inference count within cycle")
):
    """
    Get the full state data stored in a checkpoint.
    This includes blackboard, workspace, tracker, and completed concepts.
    """
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    def _get_checkpoint():
        import sqlite3
        import json
        
        conn = sqlite3.connect(db_path)
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
            return None
        
        state = json.loads(row["state_json"])
        
        return CheckpointStateResponse(
            cycle=row["cycle"],
            inference_count=row["inference_count"],
            timestamp=row["timestamp"],
            blackboard=state.get("blackboard"),
            workspace=state.get("workspace"),
            tracker=state.get("tracker"),
            completed_concepts=state.get("completed_concepts"),
            signatures=state.get("signatures")
        )
    
    try:
        result = await _run_in_thread(_get_checkpoint)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Checkpoint not found for cycle {cycle}")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get checkpoint state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/blackboard", response_model=BlackboardSummary)
async def get_blackboard_summary(
    run_id: str,
    db_path: str = Query(..., description="Path to orchestration.db"),
    cycle: Optional[int] = Query(None, description="Specific cycle (latest if not provided)")
):
    """
    Get a summary of the blackboard state from a checkpoint.
    This provides a quick overview of concept and item statuses.
    """
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    def _get_blackboard():
        import sqlite3
        import json
        
        conn = sqlite3.connect(db_path)
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
            return None
        
        state = json.loads(row["state_json"])
        blackboard = state.get("blackboard", {})
        
        concept_statuses = blackboard.get("concept_statuses", {})
        item_statuses = blackboard.get("item_statuses", {})
        item_results = blackboard.get("item_results", {})
        item_completion_details = blackboard.get("item_completion_details", {})
        execution_counts = blackboard.get("execution_counts", {})
        
        # Count completed
        completed_concepts = sum(1 for s in concept_statuses.values() if s == "complete")
        completed_items = sum(1 for s in item_statuses.values() if s == "completed")
        
        return BlackboardSummary(
            concept_statuses=concept_statuses,
            item_statuses=item_statuses,
            item_results=item_results,
            item_completion_details=item_completion_details,
            execution_counts=execution_counts,
            concept_count=len(concept_statuses),
            item_count=len(item_statuses),
            completed_concepts=completed_concepts,
            completed_items=completed_items
        )
    
    try:
        result = await _run_in_thread(_get_blackboard)
        if result is None:
            raise HTTPException(status_code=404, detail="No checkpoint found for this run")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get blackboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/concepts")
async def get_completed_concepts(
    run_id: str,
    db_path: str = Query(..., description="Path to orchestration.db"),
    cycle: Optional[int] = Query(None, description="Specific cycle (latest if not provided)")
):
    """
    Get the completed concepts with their reference data from a checkpoint.
    """
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    def _get_concepts():
        import sqlite3
        import json
        
        conn = sqlite3.connect(db_path)
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
            return None
        
        state = json.loads(row["state_json"])
        completed_concepts = state.get("completed_concepts", {})
        
        # Process each concept to extract useful info
        result = {}
        for name, data in completed_concepts.items():
            if isinstance(data, dict):
                result[name] = {
                    "has_tensor": "tensor" in data,
                    "shape": data.get("shape"),
                    "axes": data.get("axes"),
                    "data_preview": _get_data_preview(data.get("tensor"))
                }
            else:
                result[name] = {"value": data}
        
        return {"concepts": result, "count": len(result)}
    
    def _get_data_preview(tensor):
        """Get a preview of tensor data."""
        if tensor is None:
            return None
        if isinstance(tensor, (list, dict)):
            # For large data, just show structure
            if isinstance(tensor, list):
                if len(tensor) > 5:
                    return f"[...{len(tensor)} items...]"
                return tensor[:5]
            return f"{{...{len(tensor)} keys...}}"
        return str(tensor)[:100]
    
    try:
        result = await _run_in_thread(_get_concepts)
        if result is None:
            raise HTTPException(status_code=404, detail="No checkpoint found for this run")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get completed concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query")
async def run_custom_query(
    db_path: str = Query(..., description="Path to orchestration.db"),
    table: str = Query(..., description="Table to query"),
    limit: int = Query(100, description="Maximum rows to return"),
    offset: int = Query(0, description="Offset for pagination"),
    where: Optional[str] = Query(None, description="WHERE clause (e.g., 'run_id = \"abc\"')")
):
    """
    Run a custom read-only query against a table.
    Only SELECT queries are allowed for safety.
    """
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    # Validate table name (basic SQL injection prevention)
    allowed_tables = ["executions", "logs", "checkpoints", "run_metadata"]
    if table not in allowed_tables:
        raise HTTPException(status_code=400, detail=f"Invalid table. Allowed: {allowed_tables}")
    
    def _run_query():
        import sqlite3
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = f"SELECT * FROM {table}"
        params = []
        
        if where:
            # Basic sanitization - only allow simple conditions
            if any(kw in where.lower() for kw in ["drop", "delete", "insert", "update", "alter", "create", ";"]):
                raise ValueError("Invalid WHERE clause")
            query += f" WHERE {where}"
        
        query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor.execute(query)
        rows = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM {table}"
        if where:
            count_query += f" WHERE {where}"
        cursor.execute(count_query)
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {"rows": rows, "total_count": total_count, "table": table}
    
    try:
        return await _run_in_thread(_run_query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to run query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

