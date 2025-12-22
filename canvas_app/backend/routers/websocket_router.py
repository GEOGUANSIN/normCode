"""WebSocket endpoints for real-time updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import json
import logging
import asyncio

from core.events import event_emitter

router = APIRouter()
logger = logging.getLogger(__name__)

# Active WebSocket connections
active_connections: Set[WebSocket] = set()


async def broadcast_event(event: dict):
    """Broadcast event to all connected WebSocket clients."""
    if not active_connections:
        return
    
    message = json.dumps(event)
    disconnected = set()
    
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.warning(f"Failed to send to WebSocket: {e}")
            disconnected.add(connection)
    
    active_connections.difference_update(disconnected)


# Register broadcast function with event emitter
event_emitter.add_listener(broadcast_event)


@router.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time execution events.
    
    Events sent from server:
    - execution:loaded
    - execution:started
    - execution:paused
    - execution:resumed
    - execution:completed
    - execution:error
    - execution:stopped
    - execution:stepping
    - inference:started
    - inference:completed
    - inference:failed
    - inference:updated
    - breakpoint:hit
    - breakpoint:set
    - breakpoint:cleared
    
    Commands accepted from client:
    - ping: Returns pong
    """
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket connected. Total connections: {len(active_connections)}")
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection:established",
            "data": {"message": "Connected to NormCode Canvas"}
        }))
        
        while True:
            try:
                # Receive messages from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                msg_type = message.get("type", "")
                payload = message.get("payload", {})
                
                # Handle client commands
                if msg_type == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "data": {}
                    }))
                    
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON from WebSocket")
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(active_connections)}")
