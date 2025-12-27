"""
Canvas Chat Tool for compiler-driven chat interface.

This tool allows NormCode plans (specifically the compiler meta-project)
to interact with the chat panel in the Canvas app.

The tool supports:
- Writing messages to chat (write, write_code, write_artifact)
- Reading user input from chat (read_input, read_code, ask, confirm)
- Status updates and progress display

This is the backend counterpart to the ChatPanel frontend component.
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ChatInputRequest:
    """A pending chat input request."""
    id: str
    prompt: str
    input_type: str  # text, code, confirm, select
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None
    initial_value: Optional[str] = None
    response: Optional[str] = None
    completed: bool = False
    created_at: float = field(default_factory=time.time)


class CanvasChatTool:
    """
    A tool for NormCode plans to interact with the Canvas chat interface.
    
    This tool is designed to be used by the compiler meta-project to:
    1. Display messages, code blocks, and artifacts in the chat
    2. Request input from the user through the chat
    3. Show compilation progress and status updates
    
    The tool uses WebSocket events to communicate with the frontend.
    Similar to CanvasUserInputTool, it uses threading.Event for blocking
    input operations to be compatible with synchronous orchestrator code.
    """
    
    def __init__(
        self, 
        emit_callback: Optional[Callable[[str, Dict], None]] = None,
        source: str = "compiler"
    ):
        """
        Initialize the Canvas chat tool.
        
        Args:
            emit_callback: Callback to emit WebSocket events.
                          Signature: (event_type: str, data: dict) -> None
            source: Identifier for which service owns this tool.
                   "compiler" = CompilerService (/api/chat/input/)
                   "execution" = ExecutionController (/api/execution/chat-input/)
        """
        self._emit_callback = emit_callback
        self._source = source
        self._pending_requests: Dict[str, ChatInputRequest] = {}
        self._events: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()
        # Single message buffer for message received before a blocking read
        # Only ONE message can be buffered at a time - cleaner UX
        self._buffered_message: Optional[str] = None
        self._buffer_lock = threading.Lock()
        # Flag to indicate execution is active (messages should be buffered)
        self._execution_active = False
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """Set the callback for emitting WebSocket events."""
        self._emit_callback = callback
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event if callback is set."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit chat event {event_type}: {e}")
    
    def _generate_id(self) -> str:
        """Generate a unique ID for messages/requests."""
        return str(uuid.uuid4())[:8]
    
    # =========================================================================
    # Execution State and Message Queue
    # =========================================================================
    
    def set_execution_active(self, active: bool):
        """
        Set whether execution is active.
        
        When active, messages sent to the chat are buffered for the plan to consume.
        When inactive, messages go to the normal chat flow.
        
        Args:
            active: True when execution starts, False when it stops
        """
        with self._buffer_lock:
            self._execution_active = active
            if not active:
                # Clear buffer when execution stops
                self._buffered_message = None
            logger.debug(f"Execution active: {active}")
    
    def is_execution_active(self) -> bool:
        """Check if execution is currently active."""
        with self._buffer_lock:
            return self._execution_active
    
    def buffer_message(self, message: str) -> Dict[str, Any]:
        """
        Buffer a message for the running plan to consume.
        
        Only ONE message can be buffered at a time. If a message is already
        buffered, this will fail and return buffer_full=True.
        
        Called by the API when a user sends a message while execution is active.
        The message will be delivered when the plan next calls read_message().
        
        Args:
            message: The user's message content
            
        Returns:
            Dict with:
                success: True if message was buffered
                buffer_full: True if buffer already has a message
                delivered: True if message was delivered to waiting request
                buffered_message: The currently buffered message (if any)
        """
        with self._buffer_lock:
            if not self._execution_active:
                return {"success": False, "reason": "execution_not_active"}
            
            # Check if buffer already has a message
            if self._buffered_message is not None:
                return {
                    "success": False, 
                    "buffer_full": True,
                    "buffered_message": self._buffered_message,
                }
            
            # Buffer the message
            self._buffered_message = message
            logger.debug(f"Buffered message: {message[:50]}...")
        
        # If there's a pending input request waiting, deliver immediately
        with self._lock:
            for req_id, request in self._pending_requests.items():
                if not request.completed:
                    # Fulfill this request with the buffered message
                    request.response = message
                    request.completed = True
                    self._events[req_id].set()
                    # Clear the buffer since we delivered it
                    with self._buffer_lock:
                        self._buffered_message = None
                    logger.debug(f"Delivered buffered message to pending request {req_id}")
                    return {"success": True, "delivered": True}
        
        return {"success": True, "delivered": False, "buffered_message": message}
    
    def consume_buffered_message(self) -> Optional[str]:
        """
        Get and clear the buffered message.
        
        Called when the plan's read operation consumes the message.
        
        Returns:
            The message content, or None if buffer is empty
        """
        with self._buffer_lock:
            message = self._buffered_message
            self._buffered_message = None
            if message:
                logger.debug(f"Consumed buffered message: {message[:50]}...")
            return message
    
    def get_buffered_message(self) -> Optional[str]:
        """
        Peek at the buffered message without consuming it.
        
        Used by API to show buffer status to frontend.
        
        Returns:
            The message content, or None if buffer is empty
        """
        with self._buffer_lock:
            return self._buffered_message
    
    def has_buffered_message(self) -> bool:
        """Check if there is a buffered message waiting."""
        with self._buffer_lock:
            return self._buffered_message is not None
    
    # =========================================================================
    # Writing to Chat
    # =========================================================================
    
    def write(self, message: str, role: str = "compiler", metadata: Optional[Dict] = None):
        """
        Write a message to the chat.
        
        Args:
            message: The message content
            role: Message role ('compiler', 'system', 'assistant')
            metadata: Optional metadata (flowIndex, nodeLink, etc.)
        """
        msg_id = self._generate_id()
        self._emit("chat:message", {
            "id": msg_id,
            "role": role,
            "content": message,
            "metadata": metadata or {},
        })
        logger.debug(f"Chat message [{role}]: {message[:100]}...")
    
    def write_code(
        self, 
        code: str, 
        language: str = "ncd", 
        title: Optional[str] = None,
        collapsible: bool = True
    ):
        """
        Write a code block to the chat.
        
        Args:
            code: The code content
            language: Programming language for syntax highlighting
            title: Optional title for the code block
            collapsible: Whether the code block can be collapsed
        """
        block_id = self._generate_id()
        self._emit("chat:code_block", {
            "id": block_id,
            "code": code,
            "language": language,
            "title": title,
            "collapsible": collapsible,
        })
        logger.debug(f"Chat code block [{language}]: {len(code)} chars")
    
    def write_artifact(
        self, 
        data: Any, 
        artifact_type: str = "json",
        title: Optional[str] = None
    ):
        """
        Write a structured artifact to the chat.
        
        Args:
            data: The artifact data (will be serialized to JSON)
            artifact_type: Type of artifact ('json', 'table', 'tree', 'graph-preview')
            title: Optional title for the artifact
        """
        artifact_id = self._generate_id()
        self._emit("chat:artifact", {
            "id": artifact_id,
            "type": artifact_type,
            "data": data,
            "title": title,
        })
        logger.debug(f"Chat artifact [{artifact_type}]: {title or 'untitled'}")
    
    def update_status(self, status: str, step: Optional[str] = None):
        """
        Update the compiler status displayed in the chat header.
        
        Args:
            status: Status string ('connecting', 'connected', 'running', 'error')
            step: Optional current step description
        """
        self._emit("chat:compiler_status", {
            "status": status,
            "step": step,
        })
    
    # =========================================================================
    # Reading from Chat (User Input)
    # =========================================================================
    
    def read_input(self, prompt: Optional[str] = None) -> str:
        """
        Wait for and return user's next text message.
        
        Args:
            prompt: Optional prompt to show the user
            
        Returns:
            The user's text input
        """
        return self._wait_for_input(
            prompt=prompt or "Enter your response:",
            input_type="text",
        )
    
    def read_code(
        self, 
        prompt: Optional[str] = None,
        language: str = "ncd",
        initial_value: Optional[str] = None
    ) -> str:
        """
        Request code input from user (opens code editor in chat).
        
        Args:
            prompt: Optional prompt to show the user
            language: Expected language for syntax hints
            initial_value: Initial code to show in editor
            
        Returns:
            The user's code input
        """
        return self._wait_for_input(
            prompt=prompt or "Enter your code:",
            input_type="code",
            initial_value=initial_value,
            options={"language": language},
        )
    
    def ask(self, question: str, options: Optional[List[str]] = None) -> str:
        """
        Ask user a question and wait for response.
        
        Args:
            question: The question to ask
            options: Optional list of options for selection
            
        Returns:
            The user's response (selected option or free text)
        """
        input_type = "select" if options else "text"
        return self._wait_for_input(
            prompt=question,
            input_type=input_type,
            options=options,
        )
    
    def confirm(self, message: str) -> bool:
        """
        Ask for yes/no confirmation.
        
        Args:
            message: The confirmation message
            
        Returns:
            True if user confirmed, False otherwise
        """
        response = self._wait_for_input(
            prompt=message,
            input_type="confirm",
            options=["Yes", "No"],
        )
        return response.lower() in ("yes", "y", "true", "1", "confirm")
    
    def _wait_for_input(
        self,
        prompt: str,
        input_type: str,
        options: Optional[Any] = None,
        placeholder: Optional[str] = None,
        initial_value: Optional[str] = None,
    ) -> str:
        """
        Block and wait for user input from the chat.
        
        This method:
        1. First checks if there's a queued message (user typed before we blocked)
        2. If not, creates a pending request and emits a WebSocket event
        3. Blocks on a threading.Event until response is received
        4. Returns the user's response
        
        Args:
            prompt: The prompt to show the user
            input_type: Type of input (text, code, confirm, select)
            options: Options for select type, or additional config for code
            placeholder: Placeholder text for input
            initial_value: Initial value for code editor
            
        Returns:
            The user's response as a string
        """
        # Check if there's already a buffered message we can consume
        buffered = self.consume_buffered_message()
        if buffered is not None:
            logger.info(f"Consumed buffered message: {buffered[:50]}...")
            return buffered
        
        request_id = self._generate_id()
        event = threading.Event()
        
        # Handle options - could be list for select or dict for code config
        option_list = None
        if isinstance(options, list):
            option_list = options
        
        request = ChatInputRequest(
            id=request_id,
            prompt=prompt,
            input_type=input_type,
            options=option_list,
            placeholder=placeholder,
            initial_value=initial_value,
        )
        
        with self._lock:
            self._pending_requests[request_id] = request
            self._events[request_id] = event
        
        # Emit WebSocket event to notify frontend
        # Include source so frontend knows which endpoint to use for response
        self._emit("chat:input_request", {
            "id": request_id,
            "prompt": prompt,
            "input_type": input_type,
            "options": option_list,
            "placeholder": placeholder,
            "initial_value": initial_value,
            "source": self._source,  # "compiler" or "execution"
        })
        
        logger.info(f"Waiting for chat input: {request_id} ({input_type})")
        
        # Block until response is received
        event.wait()
        
        # Get response and clean up
        with self._lock:
            response = self._pending_requests[request_id].response
            del self._pending_requests[request_id]
            del self._events[request_id]
        
        logger.info(f"Received chat input for {request_id}")
        
        return response or ""
    
    # =========================================================================
    # Response Handling (called by REST API)
    # =========================================================================
    
    def submit_response(self, request_id: str, value: str) -> bool:
        """
        Submit a response for a pending input request.
        
        Called by the REST API when user submits input.
        
        Args:
            request_id: The request ID
            value: The user's response
            
        Returns:
            True if request was found and completed, False otherwise
        """
        with self._lock:
            if request_id not in self._pending_requests:
                logger.warning(f"No pending chat request found: {request_id}")
                return False
            
            self._pending_requests[request_id].response = value
            self._pending_requests[request_id].completed = True
            self._events[request_id].set()
        
        return True
    
    def cancel_request(self, request_id: str) -> bool:
        """
        Cancel a pending input request.
        
        Args:
            request_id: The request ID to cancel
            
        Returns:
            True if request was found and cancelled
        """
        with self._lock:
            if request_id not in self._pending_requests:
                return False
            
            self._pending_requests[request_id].response = None
            self._pending_requests[request_id].completed = True
            self._events[request_id].set()
        
        self._emit("chat:input_cancelled", {
            "request_id": request_id,
        })
        
        return True
    
    def get_pending_request(self) -> Optional[Dict[str, Any]]:
        """Get the current pending input request, if any."""
        with self._lock:
            for req in self._pending_requests.values():
                if not req.completed:
                    return {
                        "id": req.id,
                        "prompt": req.prompt,
                        "input_type": req.input_type,
                        "options": req.options,
                        "placeholder": req.placeholder,
                        "initial_value": req.initial_value,
                    }
        return None
    
    def has_pending_request(self) -> bool:
        """Check if there is a pending request."""
        with self._lock:
            return any(not req.completed for req in self._pending_requests.values())
    
    # =========================================================================
    # Factory Methods for NormCode Integration
    # =========================================================================
    
    def create_write_function(self, role: str = "compiler") -> Callable:
        """
        Create a function for writing messages to chat.
        
        Returns:
            A callable that takes (message: str, **kwargs) and writes to chat
        """
        def write_fn(message: str = "", **kwargs) -> None:
            # Support both positional and keyword arguments
            content = message or kwargs.get("content", "")
            metadata = kwargs.get("metadata", {})
            self.write(content, role=role, metadata=metadata)
        
        return write_fn
    
    def create_read_function(self) -> Callable:
        """
        Create a function for reading user input from chat.
        
        Returns:
            A callable that takes (**kwargs) and returns user input
        """
        def read_fn(**kwargs) -> str:
            prompt = kwargs.get("prompt_text", kwargs.get("prompt", "Enter input:"))
            return self.read_input(prompt)
        
        return read_fn
    
    def create_ask_function(self) -> Callable:
        """
        Create a function for asking questions in chat.
        
        Returns:
            A callable that takes (question: str, options: list) and returns response
        """
        def ask_fn(**kwargs) -> str:
            question = kwargs.get("question", kwargs.get("prompt", ""))
            options = kwargs.get("options", None)
            return self.ask(question, options)
        
        return ask_fn
    
    # =========================================================================
    # Paradigm Affordances - Functions for composition (MFP → TVA pattern)
    # These return callables that the paradigm's composition_tool uses
    # =========================================================================
    
    def read_message(self) -> Callable:
        """
        Affordance: Return a function that blocks and reads user message.
        
        Used by paradigm: c_ChatRead-o_Literal
        
        The returned function:
        - Blocks until user sends a message
        - Returns dict with {role: str, content: str}
        """
        def _read_message_fn(**kwargs) -> Dict[str, Any]:
            # Block and wait for user message
            content = self.read_input(kwargs.get("prompt", ""))
            return {
                "role": "user",
                "content": content,
            }
        
        return _read_message_fn
    
    @property
    def write_message(self) -> Callable:
        """
        Affordance: Return a function that sends a message to the user.
        
        Used by paradigm: h_Response-c_ChatWrite-o_Status
        
        The returned function:
        - Takes message text
        - Sends to chat
        - Returns status dict
        """
        def _write_message_fn(message: str = "", **kwargs) -> Dict[str, Any]:
            import time
            content = message or kwargs.get("message", kwargs.get("content", ""))
            self.write(content, role="compiler")
            return {
                "sent": True,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        
        return _write_message_fn
    
    def close_session(self) -> Callable:
        """
        Affordance: Return a function that closes the chat session.
        
        Used by paradigm: c_ChatSessionClose-o_Status
        
        The returned function:
        - Closes the session gracefully
        - Returns status dict
        """
        def _close_session_fn(**kwargs) -> Dict[str, Any]:
            # Emit session close event
            self._emit("chat:session_closed", {})
            self.write("Session ended. Goodbye!", role="system")
            return {
                "status": "closed",
            }
        
        return _close_session_fn