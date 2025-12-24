"""WebSocket endpoints for real-time updates."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Set
import json
import logging
import asyncio

from core.events import event_emitter
from services.compiler_service import get_compiler_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Active WebSocket connections
active_connections: Set[WebSocket] = set()

# Flag to track if compiler service has been wired up
_compiler_wired = False


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


def _setup_compiler_service():
    """Set up the compiler service with the WebSocket emit callback."""
    global _compiler_wired
    if not _compiler_wired:
        def emit_sync(event_type: str, data: dict):
            """Synchronous emit wrapper that schedules the async broadcast."""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(broadcast_event({
                        "type": event_type,
                        "data": data
                    }))
                else:
                    loop.run_until_complete(broadcast_event({
                        "type": event_type,
                        "data": data
                    }))
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
        
        compiler_service = get_compiler_service()
        compiler_service.set_emit_callback(emit_sync)
        _compiler_wired = True
        logger.info("Compiler service wired to WebSocket")


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
    - chat:message
    - chat:code_block
    - chat:artifact
    - chat:input_request
    - chat:compiler_status
    
    Commands accepted from client:
    - ping: Returns pong
    """
    await websocket.accept()
    active_connections.add(websocket)
    logger.info(f"WebSocket connected. Total connections: {len(active_connections)}")
    
    # Set up compiler service with emit callback on first connection
    _setup_compiler_service()
    
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
