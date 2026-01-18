"""
Global State Management

Shared state for active runs and websocket connections.
"""

from typing import Dict, List, Any, TYPE_CHECKING
from fastapi import WebSocket

if TYPE_CHECKING:
    from .state import RunState

# Active runs keyed by run_id
active_runs: Dict[str, "RunState"] = {}

# WebSocket connections keyed by run_id
websocket_connections: Dict[str, List[WebSocket]] = {}


async def broadcast_event(run_id: str, event: Dict[str, Any]):
    """Broadcast event to all websocket subscribers for a run."""
    connections = websocket_connections.get(run_id, [])
    disconnected = []
    
    for ws in connections:
        try:
            await ws.send_json(event)
        except Exception:
            disconnected.append(ws)
    
    # Remove disconnected
    for ws in disconnected:
        connections.remove(ws)

