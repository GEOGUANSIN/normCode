"""
Compiler Service - Manages the meta compiler project.

The meta compiler is a NormCode plan that drives the chat interface.
It is loaded as a read-only "background" project that orchestrates
the conversation and compilation process.

Architecture:
    CompilerService acts as a facade that will eventually execute the
    compiler NormCode plan via ExecutionController. The compiler plan
    uses ChatTool and CanvasTool to interact with the user.

    ┌─────────────────────────────────────────────────────────────┐
    │                    CompilerService                          │
    │  - Lifecycle: start/stop/disconnect                         │
    │  - Message routing: user → compiler plan                    │
    │  - WebSocket: emit events to frontend                       │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │              ExecutionController (planned)                  │
    │  - Runs compiler.normcode-canvas.json                       │
    │  - Has ChatTool injected for chat I/O                       │
    │  - Has CanvasTool injected for canvas operations            │
    └─────────────────────────────────────────────────────────────┘

Current Status:
    PLACEHOLDER IMPLEMENTATION - The _process_user_message() method
    currently provides demo responses. Real integration will execute
    the compiler NormCode plan from canvas_app/compiler/.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from tools.chat_tool import CanvasChatTool

logger = logging.getLogger(__name__)


# =============================================================================
# Compiler Project Location
# =============================================================================

# Location of the compiler meta project (a NormCode plan)
COMPILER_PROJECT_DIR = Path(__file__).parent.parent.parent / "compiler"
COMPILER_CONFIG_FILE = COMPILER_PROJECT_DIR / "compiler.normcode-canvas.json"


class CompilerStatus:
    """Valid status values for the compiler."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RUNNING = "running"
    ERROR = "error"


class CompilerService:
    """
    Service for managing the meta compiler project.
    
    The compiler project is a special NormCode plan that:
    1. Drives the chat conversation (reads user input, writes responses)
    2. Can execute canvas commands (create nodes, run execution, etc.)
    3. Uses LLM to understand user intent and generate responses
    
    The compiler runs independently of user projects and is always
    read-only to prevent accidental modification.
    
    Lifecycle:
        1. start() - Initialize and connect the compiler
        2. send_message() - Route user messages to the compiler
        3. stop() - Pause execution (stay connected)
        4. disconnect() - Fully disconnect
    """
    
    def __init__(self):
        """Initialize the compiler service."""
        self._project_id: str = "compiler-meta"
        self._status: str = CompilerStatus.DISCONNECTED
        self._current_step: Optional[str] = None
        self._error_message: Optional[str] = None
        
        # Tools for the compiler to use
        self._chat_tool: Optional[CanvasChatTool] = None
        self._emit_callback: Optional[Callable] = None
        
        # Execution state (for future ExecutionController integration)
        self._execution_task: Optional[asyncio.Task] = None
        
        # Message history (stored here for persistence across restarts)
        self._messages: List[Dict[str, Any]] = []
    
    # =========================================================================
    # Configuration
    # =========================================================================
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """
        Set the WebSocket emit callback.
        
        This is called by websocket_router when a connection is established.
        The callback is used by the chat_tool to send events to the frontend.
        """
        self._emit_callback = callback
        self._chat_tool = CanvasChatTool(emit_callback=callback, source="compiler")
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    # =========================================================================
    # State Accessors
    # =========================================================================
    
    @property
    def is_connected(self) -> bool:
        """Check if compiler is connected (ready to receive messages)."""
        return self._status in (CompilerStatus.CONNECTED, CompilerStatus.RUNNING)
    
    @property
    def is_running(self) -> bool:
        """Check if compiler is actively processing."""
        return self._status == CompilerStatus.RUNNING
    
    def get_state(self) -> Dict[str, Any]:
        """Get the current compiler state for API responses."""
        return {
            "project_id": self._project_id,
            "status": self._status,
            "is_loaded": self.is_connected,
            "is_read_only": True,
            "current_step": self._current_step,
            "error_message": self._error_message,
            "pending_input": self._chat_tool.get_pending_request() if self._chat_tool else None,
            "project_path": str(COMPILER_PROJECT_DIR) if COMPILER_PROJECT_DIR.exists() else None,
            "project_config_file": COMPILER_CONFIG_FILE.name if COMPILER_CONFIG_FILE.exists() else None,
        }
    
    # =========================================================================
    # Message History
    # =========================================================================
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get all chat messages."""
        return self._messages
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Add a message to the history and emit to frontend.
        
        Args:
            role: Message role ('user', 'compiler', 'system')
            content: Message content
            metadata: Optional metadata (e.g., flowIndex for linking to nodes)
            
        Returns:
            The created message dict
        """
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
        self._emit("chat:message", message)
        
        return message
    
    def clear_messages(self):
        """Clear all chat messages."""
        self._messages = []
    
    # =========================================================================
    # Lifecycle Management
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
            self._status = CompilerStatus.CONNECTING
            self._emit("chat:compiler_status", {"status": CompilerStatus.CONNECTING})
            
            # Validate compiler project exists
            if not COMPILER_PROJECT_DIR.exists():
                raise FileNotFoundError(f"Compiler project not found: {COMPILER_PROJECT_DIR}")
            
            # TODO: Load and initialize ExecutionController for compiler plan
            # This will be implemented when we integrate the real compiler plan
            await asyncio.sleep(0.1)  # Placeholder for initialization
            
            self._status = CompilerStatus.CONNECTED
            self._error_message = None
            self._emit("chat:compiler_status", {"status": CompilerStatus.CONNECTED})
            
            # Add welcome message
            self.add_message(
                role="compiler",
                content="Ready to help with your NormCode plans.\n\n"
                       "• Compile — parse and validate plans\n"
                       "• Explain — learn NormCode concepts\n"
                       "• Debug — find and fix issues"
            )
            
            logger.info("Compiler service started successfully")
            return self.get_state()
            
        except Exception as e:
            self._status = CompilerStatus.ERROR
            self._error_message = str(e)
            self._emit("chat:compiler_status", {"status": CompilerStatus.ERROR, "error": str(e)})
            logger.error(f"Failed to start compiler: {e}")
            raise
    
    async def stop(self):
        """
        Stop the compiler execution (but keep it connected).
        
        This cancels any running execution task but keeps the service
        in a connected state, ready to receive new messages.
        """
        if self._execution_task and not self._execution_task.done():
            self._execution_task.cancel()
            try:
                await self._execution_task
            except asyncio.CancelledError:
                pass
            self._execution_task = None
        
        if self._status == CompilerStatus.RUNNING:
            self._status = CompilerStatus.CONNECTED
            self._emit("chat:compiler_status", {"status": CompilerStatus.CONNECTED})
    
    async def disconnect(self):
        """
        Disconnect the compiler completely.
        
        This stops execution and marks the service as disconnected.
        """
        await self.stop()
        self._status = CompilerStatus.DISCONNECTED
        self._emit("chat:compiler_status", {"status": CompilerStatus.DISCONNECTED})
    
    # =========================================================================
    # Message Handling
    # =========================================================================
    
    async def send_message(self, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Handle a message from the user.
        
        This is the main entry point for user messages. The message is:
        1. Added to history
        2. If there's a pending input request, it's fulfilled
        3. Otherwise, processed by the compiler
        
        Args:
            content: The message content
            metadata: Optional metadata
            
        Returns:
            The created message
        """
        # Add user message to history
        message = self.add_message("user", content, metadata)
        
        # Check if there's a pending input request from the compiler
        if self._chat_tool and self._chat_tool.has_pending_request():
            pending = self._chat_tool.get_pending_request()
            if pending:
                self._chat_tool.submit_response(pending["id"], content)
                logger.info(f"Fulfilled pending input request: {pending['id']}")
                return message
        
        # Otherwise, process as a new command
        await self._process_user_message(content)
        
        return message
    
    async def _process_user_message(self, content: str):
        """
        Process a user message that isn't a response to an input request.
        
        PLACEHOLDER IMPLEMENTATION:
        This method currently provides demo responses. When the compiler
        NormCode plan is integrated, this will:
        1. Buffer the message for the running plan
        2. Or start a new execution cycle if no plan is running
        
        The real implementation will use ExecutionController to run
        the compiler plan from canvas_app/compiler/.
        """
        self._status = CompilerStatus.RUNNING
        self._emit("chat:compiler_status", {"status": CompilerStatus.RUNNING})
        
        try:
            # TODO: Replace with actual compiler plan execution
            # When integrated, this will:
            #   1. If compiler plan is running and waiting for input:
            #      self._chat_tool.buffer_message(content)
            #   2. If compiler plan is not running:
            #      Start new execution via ExecutionController
            
            await self._placeholder_response(content)
            
        finally:
            self._status = CompilerStatus.CONNECTED
            self._emit("chat:compiler_status", {"status": CompilerStatus.CONNECTED})
    
    async def _placeholder_response(self, content: str):
        """
        Generate placeholder responses for demo purposes.
        
        This will be removed when the compiler NormCode plan is integrated.
        """
        content_lower = content.lower()
        
        if any(kw in content_lower for kw in ["compile", "create", "parse"]):
            self.add_message(
                role="compiler",
                content="I can help you compile a NormCode plan!\n\n"
                       "Share your plan in .ncds format, or describe what you'd like to build "
                       "and I'll help you structure it."
            )
        elif any(kw in content_lower for kw in ["help", "how", "what", "explain"]):
            self.add_message(
                role="compiler",
                content="NormCode is a language for structured AI plans.\n\n"
                       "• **Concepts** — typed data containers\n"
                       "• **Inferences** — operations that transform data\n"
                       "• **Isolation** — each step sees only its explicit inputs\n\n"
                       "What would you like to learn more about?"
            )
        elif any(kw in content_lower for kw in ["debug", "error", "fix", "wrong"]):
            self.add_message(
                role="compiler",
                content="I can help debug your plan.\n\n"
                       "Share the error message or describe what's happening, "
                       "and I'll help you find the issue."
            )
        elif any(kw in content_lower for kw in ["run", "execute", "start"]):
            self.add_message(
                role="compiler",
                content="To run a plan:\n\n"
                       "1. Load a project (File → Open Project)\n"
                       "2. Click the **Run** button in the control bar\n"
                       "3. Use **Step** to execute one inference at a time\n\n"
                       "You can also set breakpoints by clicking on nodes."
            )
        else:
            self.add_message(
                role="compiler",
                content="The compiler is in preview mode.\n\n"
                       "Try asking me to:\n"
                       "• \"Compile my plan\"\n"
                       "• \"Help with NormCode\"\n"
                       "• \"Debug an error\"\n"
                       "• \"Run my plan\""
            )
    
    # =========================================================================
    # Input Request Handling
    # =========================================================================
    
    def submit_input_response(self, request_id: str, value: str) -> bool:
        """
        Submit a response to a pending input request.
        
        This is called by the chat_router when the user submits input
        via the POST /api/chat/input/{request_id} endpoint.
        
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
    # Tool Access (for future compiler NormCode plan integration)
    # =========================================================================
    
    @property
    def chat(self) -> Optional[CanvasChatTool]:
        """Get the chat tool for the compiler to use."""
        return self._chat_tool


# =============================================================================
# Singleton Instance
# =============================================================================

_compiler_service: Optional[CompilerService] = None


def get_compiler_service() -> CompilerService:
    """
    Get the global compiler service instance.
    
    The compiler service is a singleton because there's only one
    compiler meta-project that drives all chat interactions.
    """
    global _compiler_service
    if _compiler_service is None:
        _compiler_service = CompilerService()
    return _compiler_service
