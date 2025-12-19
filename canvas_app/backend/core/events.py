"""Event system for WebSocket broadcasting."""
from typing import Dict, Any, Callable, Set
import asyncio
import logging

logger = logging.getLogger(__name__)


class EventEmitter:
    """Simple event emitter for broadcasting events to WebSocket clients."""
    
    def __init__(self):
        self._listeners: Set[Callable] = set()
        self._queue: asyncio.Queue = asyncio.Queue()
    
    def add_listener(self, callback: Callable):
        """Add a listener callback."""
        self._listeners.add(callback)
    
    def remove_listener(self, callback: Callable):
        """Remove a listener callback."""
        self._listeners.discard(callback)
    
    async def emit(self, event_type: str, data: Dict[str, Any]):
        """Emit an event to all listeners."""
        event = {"type": event_type, "data": data}
        for listener in self._listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")


# Global event emitter instance
event_emitter = EventEmitter()
