"""
Compiler Service - Manages the meta compiler project.

The meta compiler is a NormCode plan that drives the chat interface.
It is loaded as a read-only "background" project that orchestrates
the conversation and compilation process.

Key features:
- Loads the compiler NormCode plan from a fixed location
- Runs in parallel with user projects (independent execution)
- Provides chat and canvas tools to the compiler plan
- Manages compiler state and status updates
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from tools.chat_tool import CanvasChatTool

logger = logging.getLogger(__name__)


# Location of the compiler meta project
# This is in the canvas_app/compiler directory
COMPILER_PROJECT_DIR = Path(__file__).parent.parent.parent / "compiler"
COMPILER_CONFIG_FILE = COMPILER_PROJECT_DIR / "compiler.normcode-canvas.json"


class CompilerService:
    """
    Service for managing the meta compiler project.
    
    The compiler project is a special NormCode plan that:
    1. Drives the chat conversation
    2. Can read user input from chat
    3. Can write messages, code, and artifacts to chat
    4. Can interact with the canvas to display compilation results
    
    The compiler runs independently of user projects and is always
    read-only to prevent accidental modification.
    """
    
    def __init__(self):
        """Initialize the compiler service."""
        self._project_id: Optional[str] = "compiler-meta"
        self._status: str = "disconnected"
        self._is_loaded: bool = False
        self._current_step: Optional[str] = None
        self._error_message: Optional[str] = None
        
        # Tools for the compiler to use
        self._chat_tool: Optional[CanvasChatTool] = None
        self._emit_callback: Optional[Callable] = None
        
        # Execution state
        self._execution_task: Optional[asyncio.Task] = None
        self._is_running: bool = False
        
        # Message history (stored here for persistence)
        self._messages: List[Dict[str, Any]] = []
        
        # Pending input request
        self._pending_input: Optional[Dict[str, Any]] = None
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """Set the WebSocket emit callback."""
        self._emit_callback = callback
        
        # Create chat tool with the callback
        self._chat_tool = CanvasChatTool(emit_callback=callback)
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    # =========================================================================
    # Compiler State
    # =========================================================================
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current compiler state."""
        return {
            "project_id": self._project_id,
            "status": self._status,
            "is_loaded": self._is_loaded,
            "is_read_only": True,
            "current_step": self._current_step,
            "error_message": self._error_message,
            "pending_input": self._chat_tool.get_pending_request() if self._chat_tool else None,
            "project_path": str(COMPILER_PROJECT_DIR) if COMPILER_PROJECT_DIR.exists() else None,
            "project_config_file": COMPILER_CONFIG_FILE.name if COMPILER_CONFIG_FILE.exists() else None,
        }
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all chat messages."""
        return self._messages
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the history."""
        import uuid
        from datetime import datetime
        
        message = {
            "id": str(uuid.uuid4())[:8],
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self._messages.append(message)
        
        # Emit to frontend
        self._emit("chat:message", message)
        
        return message
    
    def clear_messages(self):
        """Clear all chat messages."""
        self._messages = []
    
    # =========================================================================
    # Compiler Lifecycle
    # =========================================================================
    
    async def start(self) -> Dict[str, Any]:
        """
        Start/connect the compiler meta project.
        
        This initializes the compiler and makes it ready to receive
        user input through the chat.
        
        Returns:
            State information about the compiler
        """
        try:
            self._status = "connecting"
            self._emit("chat:compiler_status", {"status": "connecting"})
            
            # For now, we'll simulate the compiler being ready
            # In the full implementation, this would load the actual
            # compiler NormCode plan from COMPILER_PROJECT_DIR
            
            await asyncio.sleep(0.1)  # Simulate initialization
            
            self._status = "connected"
            self._is_loaded = True
            self._emit("chat:compiler_status", {"status": "connected"})
            
            # Add welcome message
            self.add_message(
                role="compiler",
                content="Ready to help with your NormCode plans.\n\n"
                       "• Compile — parse and validate plans\n"
                       "• Explain — learn NormCode concepts\n"
                       "• Debug — find and fix issues"
            )
            
            logger.info("Compiler service started")
            
            return self.get_state()
            
        except Exception as e:
            self._status = "error"
            self._error_message = str(e)
            self._emit("chat:compiler_status", {"status": "error", "error": str(e)})
            logger.error(f"Failed to start compiler: {e}")
            raise
    
    async def stop(self):
        """Stop the compiler execution."""
        if self._execution_task and not self._execution_task.done():
            self._execution_task.cancel()
            try:
                await self._execution_task
            except asyncio.CancelledError:
                pass
        
        self._is_running = False
        self._status = "connected"  # Still connected, just not running
        self._emit("chat:compiler_status", {"status": "connected"})
    
    async def disconnect(self):
        """Disconnect the compiler completely."""
        await self.stop()
        self._status = "disconnected"
        self._is_loaded = False
        self._emit("chat:compiler_status", {"status": "disconnected"})
    
    # =========================================================================
    # Chat Input Handling
    # =========================================================================
    
    async def send_message(self, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Handle a message from the user.
        
        This is the main entry point for user messages. The message is:
        1. Added to history
        2. If there's a pending input request, it's fulfilled
        3. Otherwise, processed by the compiler (triggers new execution)
        
        Args:
            content: The message content
            metadata: Optional metadata
            
        Returns:
            The created message
        """
        # Add user message to history
        message = self.add_message("user", content, metadata)
        
        # Check if there's a pending input request
        if self._chat_tool and self._chat_tool.has_pending_request():
            pending = self._chat_tool.get_pending_request()
            if pending:
                self._chat_tool.submit_response(pending["id"], content)
                return message
        
        # Otherwise, this is a new request - process it
        # For now, we'll use a simple echo/response pattern
        # In full implementation, this would trigger the compiler plan
        await self._process_user_message(content)
        
        return message
    
    async def _process_user_message(self, content: str):
        """
        Process a user message that isn't a response to an input request.
        
        This method will eventually trigger the compiler NormCode plan.
        For now, it provides helpful responses.
        """
        self._status = "running"
        self._emit("chat:compiler_status", {"status": "running"})
        
        try:
            # Simple pattern matching for demo purposes
            content_lower = content.lower()
            
            if "compile" in content_lower or "create" in content_lower:
                self.add_message(
                    role="compiler",
                    content="I can help you compile a NormCode plan!\n\n"
                           "Share your plan in .ncds format, or describe what you'd like to build "
                           "and I'll help you structure it."
                )
            elif "help" in content_lower or "how" in content_lower:
                self.add_message(
                    role="compiler",
                    content="NormCode is a language for structured AI plans.\n\n"
                           "• Concepts — typed data containers\n"
                           "• Inferences — operations that transform data\n"
                           "• Isolation — each step sees only its explicit inputs\n\n"
                           "What would you like to learn more about?"
                )
            elif "debug" in content_lower or "error" in content_lower:
                self.add_message(
                    role="compiler",
                    content="I can help debug your plan.\n\n"
                           "Share the error message or describe what's happening, "
                           "and I'll help you find the issue."
                )
            else:
                self.add_message(
                    role="compiler",
                    content="The compiler is in preview mode.\n\n"
                           "Try asking me to:\n"
                           "• \"Compile my plan\"\n"
                           "• \"Help with NormCode\"\n"
                           "• \"Debug an error\""
                )
            
        finally:
            self._status = "connected"
            self._emit("chat:compiler_status", {"status": "connected"})
    
    def submit_input_response(self, request_id: str, value: str) -> bool:
        """
        Submit a response to a pending input request.
        
        Args:
            request_id: The request ID
            value: The user's response
            
        Returns:
            True if successful
        """
        if not self._chat_tool:
            return False
        
        return self._chat_tool.submit_response(request_id, value)
    
    def cancel_input_request(self, request_id: str) -> bool:
        """
        Cancel a pending input request.
        
        Args:
            request_id: The request ID
            
        Returns:
            True if successful
        """
        if not self._chat_tool:
            return False
        
        return self._chat_tool.cancel_request(request_id)
    
    # =========================================================================
    # Chat Tool Access (for compiler NormCode plan)
    # =========================================================================
    
    @property
    def chat(self) -> Optional[CanvasChatTool]:
        """Get the chat tool for the compiler to use."""
        return self._chat_tool


# Global singleton instance
_compiler_service: Optional[CompilerService] = None


def get_compiler_service() -> CompilerService:
    """Get the global compiler service instance."""
    global _compiler_service
    if _compiler_service is None:
        _compiler_service = CompilerService()
    return _compiler_service

