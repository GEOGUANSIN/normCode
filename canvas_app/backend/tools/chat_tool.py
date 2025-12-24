"""
Canvas-native chat tool for compiler-user interaction.

This tool allows NormCode plans to interact with users through a chat interface.
The chat is both an output (display messages) and an input (receive user responses).

The compiler NormCode plan runs "under" the chat, driving the conversation:
- Plan writes messages → appear in chat UI
- Plan reads input → waits for user to respond in chat UI

Interface similar to CanvasUserInputTool but specialized for conversational flow.
"""

import logging
import threading
import time
import uuid
from typing import Callable, Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MessageRole(str, Enum):
    """Role of a chat message."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"
    SUCCESS = "success"


class InputType(str, Enum):
    """Type of input request."""
    TEXT = "text"
    CODE = "code"
    QUESTION = "question"
    CONFIRM = "confirm"
    SELECT = "select"


@dataclass
class ChatMessage:
    """A message in the chat history."""
    id: str
    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    # For code blocks
    code: Optional[str] = None
    language: Optional[str] = None
    # For artifacts
    artifact: Optional[Any] = None
    artifact_type: Optional[str] = None
    title: Optional[str] = None


@dataclass
class PendingInput:
    """A pending input request from the chat."""
    id: str
    input_type: InputType
    prompt: str
    options: Optional[List[str]] = None
    language: Optional[str] = None
    response: Optional[Any] = None
    completed: bool = False
    created_at: float = field(default_factory=time.time)


class CanvasChatTool:
    """
    Tool for NormCode plans to interact with the chat interface.
    
    The chat is both an output (display messages) and input (receive user responses).
    
    Usage in NormCode plan:
        # Write to chat
        Body.chat.write("Analyzing your input...")
        
        # Read from chat
        code = Body.chat.read_code("Paste your NormCode draft:")
        
        # Ask a question
        answer = Body.chat.ask("Is this correct?", ["Yes", "No"])
        
        # Confirm
        if Body.chat.confirm("Proceed with compilation?"):
            ...
    """
    
    def __init__(self, emit_callback: Optional[Callable[[str, Dict], None]] = None):
        """
        Initialize the Canvas chat tool.
        
        Args:
            emit_callback: Callback to emit WebSocket events.
                          Signature: (event_type: str, data: dict) -> None
        """
        self._emit_callback = emit_callback
        self._messages: List[ChatMessage] = []
        self._pending_inputs: Dict[str, PendingInput] = {}
        self._events: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """Set the callback for emitting WebSocket events."""
        self._emit_callback = callback
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event if callback is set."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    def _generate_id(self) -> str:
        """Generate a unique ID."""
        return str(uuid.uuid4())[:8]
    
    # =========================================================================
    # Output Methods (write to chat)
    # =========================================================================
    
    def write(self, message: str, role: str = "assistant") -> None:
        """
        Write a plain text message to the chat.
        
        Args:
            message: The message content
            role: Message role (assistant, system, error, success)
        """
        msg = ChatMessage(
            id=self._generate_id(),
            role=MessageRole(role) if role in MessageRole.__members__.values() else MessageRole.ASSISTANT,
            content=message,
        )
        
        with self._lock:
            self._messages.append(msg)
        
        self._emit("chat:message", {
            "id": msg.id,
            "role": msg.role.value,
            "content": msg.content,
            "timestamp": msg.timestamp,
        })
        
        logger.debug(f"Chat message [{msg.role.value}]: {message[:50]}...")
    
    def write_code(self, code: str, language: str = "ncd", title: str = None) -> None:
        """
        Write a code block to the chat.
        
        Args:
            code: The code content
            language: Programming language for syntax highlighting
            title: Optional title for the code block
        """
        msg = ChatMessage(
            id=self._generate_id(),
            role=MessageRole.ASSISTANT,
            content=f"```{language}\n{code}\n```",
            code=code,
            language=language,
            title=title,
        )
        
        with self._lock:
            self._messages.append(msg)
        
        self._emit("chat:code_block", {
            "id": msg.id,
            "code": code,
            "language": language,
            "title": title,
            "timestamp": msg.timestamp,
        })
        
        logger.debug(f"Chat code block [{language}]: {len(code)} chars")
    
    def write_artifact(self, data: Any, artifact_type: str = "json", title: str = None) -> None:
        """
        Write a structured artifact (collapsible JSON, table, tree, etc.).
        
        Args:
            data: The artifact data (will be JSON serialized)
            artifact_type: Type of artifact (json, tree, table, diff)
            title: Optional title for the artifact
        """
        msg = ChatMessage(
            id=self._generate_id(),
            role=MessageRole.ASSISTANT,
            content=f"[Artifact: {title or artifact_type}]",
            artifact=data,
            artifact_type=artifact_type,
            title=title,
        )
        
        with self._lock:
            self._messages.append(msg)
        
        self._emit("chat:artifact", {
            "id": msg.id,
            "data": data,
            "type": artifact_type,
            "title": title,
            "timestamp": msg.timestamp,
        })
        
        logger.debug(f"Chat artifact [{artifact_type}]: {title or 'untitled'}")
    
    def write_error(self, message: str) -> None:
        """Write an error message to the chat."""
        self.write(message, role="error")
    
    def write_success(self, message: str) -> None:
        """Write a success message to the chat."""
        self.write(message, role="success")
    
    # =========================================================================
    # Input Methods (read from chat)
    # =========================================================================
    
    def read(self, prompt: str = None) -> str:
        """
        Wait for user's next text message.
        
        Args:
            prompt: Optional prompt to display before waiting
            
        Returns:
            The user's text response
        """
        if prompt:
            self.write(prompt)
        
        return self._wait_for_input(InputType.TEXT, prompt or "Enter text:")
    
    def read_code(self, prompt: str = None, language: str = "ncd") -> str:
        """
        Request code input from user (opens code editor in chat).
        
        Args:
            prompt: Optional prompt to display
            language: Expected code language for syntax highlighting
            
        Returns:
            The user's code input
        """
        if prompt:
            self.write(prompt)
        
        return self._wait_for_input(
            InputType.CODE, 
            prompt or "Enter code:",
            language=language
        )
    
    def ask(self, question: str, options: List[str] = None) -> str:
        """
        Ask a question and wait for response.
        
        Args:
            question: The question to ask
            options: Optional list of options to display as buttons
            
        Returns:
            The user's response (selected option or free text)
        """
        self.write(question)
        
        return self._wait_for_input(
            InputType.QUESTION,
            question,
            options=options
        )
    
    def confirm(self, message: str) -> bool:
        """
        Ask for yes/no confirmation.
        
        Args:
            message: The confirmation message
            
        Returns:
            True if user confirmed, False otherwise
        """
        self.write(message)
        
        response = self._wait_for_input(
            InputType.CONFIRM,
            message,
            options=["Yes", "No"]
        )
        
        return response.lower() in ("yes", "y", "true", "1", "confirm")
    
    def select(self, prompt: str, choices: List[str]) -> str:
        """
        Show a selection dropdown/list.
        
        Args:
            prompt: The prompt message
            choices: List of choices to select from
            
        Returns:
            The selected choice
        """
        self.write(prompt)
        
        return self._wait_for_input(
            InputType.SELECT,
            prompt,
            options=choices
        )
    
    def _wait_for_input(
        self,
        input_type: InputType,
        prompt: str,
        options: List[str] = None,
        language: str = None
    ) -> str:
        """
        Block and wait for user input from the frontend.
        
        Args:
            input_type: Type of input expected
            prompt: The prompt shown to user
            options: Optional list of options
            language: Optional language for code input
            
        Returns:
            The user's response as a string
        """
        request_id = self._generate_id()
        event = threading.Event()
        
        pending = PendingInput(
            id=request_id,
            input_type=input_type,
            prompt=prompt,
            options=options,
            language=language,
        )
        
        with self._lock:
            self._pending_inputs[request_id] = pending
            self._events[request_id] = event
        
        # Emit WebSocket event to notify frontend
        self._emit("chat:input_request", {
            "request_id": request_id,
            "type": input_type.value,
            "prompt": prompt,
            "options": options,
            "language": language,
        })
        
        logger.info(f"Waiting for chat input: {request_id} ({input_type.value})")
        
        # Block until response is received
        event.wait()
        
        # Get response and clean up
        with self._lock:
            response = self._pending_inputs[request_id].response
            del self._pending_inputs[request_id]
            del self._events[request_id]
        
        logger.info(f"Received chat input for {request_id}")
        
        # Store user's response as a message
        user_msg = ChatMessage(
            id=self._generate_id(),
            role=MessageRole.USER,
            content=str(response) if response else "",
            code=response if input_type == InputType.CODE else None,
            language=language if input_type == InputType.CODE else None,
        )
        
        with self._lock:
            self._messages.append(user_msg)
        
        return str(response) if response is not None else ""
    
    # =========================================================================
    # Response Handling (called by REST API)
    # =========================================================================
    
    def submit_response(self, request_id: str, response: Any) -> bool:
        """
        Submit a response for a pending input request.
        
        Called by the REST API when user submits input.
        
        Args:
            request_id: The request ID
            response: The user's response
            
        Returns:
            True if request was found and completed, False otherwise
        """
        with self._lock:
            if request_id not in self._pending_inputs:
                logger.warning(f"No pending chat input found: {request_id}")
                return False
            
            self._pending_inputs[request_id].response = response
            self._pending_inputs[request_id].completed = True
            self._events[request_id].set()
        
        self._emit("chat:input_response", {
            "request_id": request_id,
            "response": response,
        })
        
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
            if request_id not in self._pending_inputs:
                return False
            
            self._pending_inputs[request_id].response = None
            self._pending_inputs[request_id].completed = True
            self._events[request_id].set()
        
        self._emit("chat:input_cancelled", {
            "request_id": request_id,
        })
        
        return True
    
    def get_pending_requests(self) -> List[Dict]:
        """Get all pending input requests."""
        with self._lock:
            return [
                {
                    "request_id": req.id,
                    "type": req.input_type.value,
                    "prompt": req.prompt,
                    "options": req.options,
                    "language": req.language,
                    "created_at": req.created_at,
                }
                for req in self._pending_inputs.values()
                if not req.completed
            ]
    
    def has_pending_requests(self) -> bool:
        """Check if there are any pending input requests."""
        with self._lock:
            return any(not req.completed for req in self._pending_inputs.values())
    
    # =========================================================================
    # History Management
    # =========================================================================
    
    def get_messages(self, limit: int = None) -> List[Dict]:
        """
        Get chat message history.
        
        Args:
            limit: Optional limit on number of messages (most recent)
            
        Returns:
            List of message dictionaries
        """
        with self._lock:
            messages = self._messages[-limit:] if limit else self._messages
            return [
                {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "code": msg.code,
                    "language": msg.language,
                    "artifact": msg.artifact,
                    "artifact_type": msg.artifact_type,
                    "title": msg.title,
                }
                for msg in messages
            ]
    
    def clear_messages(self) -> None:
        """Clear all chat messages."""
        with self._lock:
            self._messages.clear()
        
        self._emit("chat:cleared", {})
        logger.info("Chat history cleared")
    
    def add_user_message(self, content: str) -> None:
        """
        Add a user message to history (for messages sent directly, not via read()).
        
        Args:
            content: The message content
        """
        msg = ChatMessage(
            id=self._generate_id(),
            role=MessageRole.USER,
            content=content,
        )
        
        with self._lock:
            self._messages.append(msg)
        
        self._emit("chat:message", {
            "id": msg.id,
            "role": msg.role.value,
            "content": msg.content,
            "timestamp": msg.timestamp,
        })

