"""
Streaming Routes

WebSocket and Server-Sent Events (SSE) endpoints for real-time run updates.
"""

import json
import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from service import active_runs, websocket_connections

router = APIRouter()


@router.websocket("/ws/runs/{run_id}")
async def websocket_run_events(websocket: WebSocket, run_id: str):
    """WebSocket for real-time run events."""
    await websocket.accept()
    
    # Register connection
    if run_id not in websocket_connections:
        websocket_connections[run_id] = []
    websocket_connections[run_id].append(websocket)
    
    try:
        # Send current status
        if run_id in active_runs:
            await websocket.send_json({
                "event": "connected",
                "run_id": run_id,
                "status": active_runs[run_id].status
            })
        
        # Keep connection alive
        while True:
            try:
                # Wait for messages (ping/pong or commands)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send ping to keep alive
                await websocket.send_text("ping")
    except WebSocketDisconnect:
        pass
    finally:
        # Unregister connection
        if run_id in websocket_connections:
            if websocket in websocket_connections[run_id]:
                websocket_connections[run_id].remove(websocket)


@router.get("/api/runs/{run_id}/stream")
async def stream_run_events(run_id: str):
    """
    SSE (Server-Sent Events) endpoint for streaming run execution events.
    
    This is an alternative to WebSocket that works better with HTTP proxies.
    Events are streamed in the SSE format: "data: {json}\n\n"
    
    Event types:
    - run:started - Run has started
    - node:statuses - Batch of node status changes {statuses: {flow_index: status}}
    - inference:started - An inference is about to execute
    - inference:completed - An inference finished successfully
    - inference:failed - An inference failed
    - inference:error - An inference threw an error
    - execution:progress - Progress update {completed_count, total_count, cycle_count}
    - cycle:started - A new cycle is starting
    - cycle:completed - A cycle finished
    - run:completed - Run finished successfully
    - run:failed - Run failed with error
    """
    if run_id not in active_runs:
        raise HTTPException(404, f"Run not found: {run_id}")
    
    run_state = active_runs[run_id]
    
    async def event_generator():
        """Generate SSE events."""
        queue = asyncio.Queue()
        run_state.add_event_subscriber(queue)
        
        try:
            # Send initial connection event with current state
            initial_event = {
                "event": "connected",
                "run_id": run_id,
                "status": run_state.status,
                "node_statuses": run_state._node_statuses,
            }
            yield f"data: {json.dumps(initial_event)}\n\n"
            
            # Stream events until run completes
            while run_state.status in ("pending", "running"):
                try:
                    # Wait for next event with timeout
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    
                    # Stop streaming after completion or failure
                    if event.get("event") in ("run:completed", "run:failed"):
                        break
                        
                except asyncio.TimeoutError:
                    # Send keepalive comment
                    yield ": keepalive\n\n"
            
            # Send final state if not already sent
            if run_state.status == "completed" and run_state.result:
                final_event = {
                    "event": "run:completed",
                    "run_id": run_id,
                    "result": run_state.result,
                }
                yield f"data: {json.dumps(final_event)}\n\n"
            elif run_state.status == "failed":
                final_event = {
                    "event": "run:failed",
                    "run_id": run_id,
                    "error": run_state.error,
                }
                yield f"data: {json.dumps(final_event)}\n\n"
                
        finally:
            run_state.remove_event_subscriber(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )

