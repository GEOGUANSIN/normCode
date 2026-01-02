"""
Chat Message Service - Manages chat message history.

Handles:
- Storing and retrieving chat messages
- Message creation with timestamps and IDs
- WebSocket emission of new messages
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChatMessageService:
    """
    Service for managing chat message history.
    
    Responsibilities:
    - Store messages in memory
    - Generate message IDs and timestamps
    - Emit messages via WebSocket when callback is set
    - Provide message history access
    """
    
    def __init__(self, emit_callback: Optional[Callable[[str, Dict], None]] = None):
        """
        Initialize the message service.
        
        Args:
            emit_callback: Optional WebSocket emit callback
        """
        self._messages: List[Dict[str, Any]] = []
        self._emit_callback = emit_callback
    
    # =========================================================================
    # Configuration
    # =========================================================================
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """
        Set the WebSocket emit callback.
        
        Args:
            callback: Function that takes (event_type, data) and emits via WebSocket
        """
        self._emit_callback = callback
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event if callback is set."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    # =========================================================================
    # Message Operations
    # =========================================================================
    
    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
        flow_index: Optional[str] = None,
        emit: bool = True,
    ) -> Dict[str, Any]:
        """
        Add a message to history.
        
        Args:
            role: Message role ('user', 'controller', 'system')
            content: Message content
            metadata: Optional metadata dict
            flow_index: Optional flow index that generated this message
            emit: Whether to emit via WebSocket (default True)
            
        Returns:
            The created message dict
        """
        msg_metadata = metadata.copy() if metadata else {}
        if flow_index:
            msg_metadata["flowIndex"] = flow_index
        
        message = {
            "id": str(uuid.uuid4())[:8],
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": msg_metadata,
        }
        
        self._messages.append(message)
        
        if emit:
            self._emit("chat:message", message)
        
        return message
    
    def get_messages(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Get messages from history.
        
        Args:
            limit: Maximum number of messages to return (None for all)
            offset: Offset for pagination
            
        Returns:
            List of message dicts
        """
        messages = self._messages[offset:]
        if limit is not None:
            messages = messages[:limit]
        return messages
    
    def get_message_count(self) -> int:
        """Get total number of messages."""
        return len(self._messages)
    
    def get_message_by_id(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific message by ID.
        
        Args:
            message_id: The message ID
            
        Returns:
            The message dict if found, None otherwise
        """
        for msg in self._messages:
            if msg.get("id") == message_id:
                return msg
        return None
    
    def clear_messages(self):
        """Clear all chat messages."""
        self._messages = []
        logger.debug("Cleared all chat messages")
    
    def get_last_message(self, role: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get the last message, optionally filtered by role.
        
        Args:
            role: Optional role filter
            
        Returns:
            The last message matching criteria, or None
        """
        if role:
            for msg in reversed(self._messages):
                if msg.get("role") == role:
                    return msg
            return None
        
        return self._messages[-1] if self._messages else None
    
    def get_messages_by_role(self, role: str) -> List[Dict[str, Any]]:
        """
        Get all messages with a specific role.
        
        Args:
            role: The role to filter by
            
        Returns:
            List of messages with that role
        """
        return [msg for msg in self._messages if msg.get("role") == role]

