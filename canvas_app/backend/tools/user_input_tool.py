"""
Canvas-native user input tool for human-in-the-loop orchestration.

This tool uses WebSocket events to communicate with the frontend,
allowing the orchestrator to pause and wait for user input through the UI.

Unlike the Streamlit version which uses threading.Event, this version
uses asyncio.Event for async compatibility with FastAPI.
"""

import asyncio
import logging
import threading
import time
import uuid
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class UserInputRequest:
    """A pending user input request."""
    id: str
    prompt: str
    interaction_type: str  # text_input, text_editor, confirm, select
    options: Optional[Dict[str, Any]] = None
    response: Optional[Any] = None
    completed: bool = False
    created_at: float = field(default_factory=time.time)


class CanvasUserInputTool:
    """
    A user input tool that integrates with the Canvas app via WebSocket.
    
    When user input is needed:
    1. Tool creates a request and emits a WebSocket event
    2. Worker thread blocks on a threading.Event
    3. Frontend shows a UI form for user input
    4. User submits via REST API which sets the response
    5. Worker thread unblocks and returns the answer
    
    This design allows the synchronous orchestrator code to wait for
    async user input from the WebSocket-based frontend.
    """
    
    def __init__(self, emit_callback: Optional[Callable[[str, Dict], None]] = None):
        """
        Initialize the Canvas user input tool.
        
        Args:
            emit_callback: Callback to emit WebSocket events.
                          Signature: (event_type: str, data: dict) -> None
        """
        self._emit_callback = emit_callback
        self._pending_requests: Dict[str, UserInputRequest] = {}
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
    
    def create_input_function(
        self, 
        prompt_key: str = "prompt_text", 
        interaction_type: str = "text_input"
    ) -> Callable:
        """
        Creates a function that prompts the user for text input.
        
        This mimics the interface of UserInputTool.create_input_function()
        but blocks the worker thread until the UI provides an answer.
        
        Args:
            prompt_key: The key in kwargs that contains the prompt text
            interaction_type: Type of interaction (text_input, text_editor, etc.)
            
        Returns:
            A callable that takes **kwargs and returns user input string
        """
        def request_input(**kwargs) -> str:
            prompt = kwargs.get(prompt_key, "Please provide input:")
            return self._wait_for_input(prompt, interaction_type, kwargs)
        
        return request_input
    
    def create_text_editor_function(
        self,
        prompt_key: str = "prompt_text",
        initial_content_key: str = "initial_content"
    ) -> Callable:
        """
        Creates a function that opens a text editor for the user.
        
        Args:
            prompt_key: Key for the prompt/instructions
            initial_content_key: Key for initial content to edit
            
        Returns:
            A callable that returns the edited text
        """
        def request_editor(**kwargs) -> str:
            prompt = kwargs.get(prompt_key, "Edit the content:")
            initial_content = kwargs.get(initial_content_key, "")
            return self._wait_for_input(
                prompt, 
                "text_editor", 
                {"initial_content": initial_content, **kwargs}
            )
        
        return request_editor
    
    def create_confirm_function(self, prompt_key: str = "prompt_text") -> Callable:
        """
        Creates a function that asks for yes/no confirmation.
        
        Returns:
            A callable that returns True for yes, False for no
        """
        def request_confirm(**kwargs) -> bool:
            prompt = kwargs.get(prompt_key, "Confirm?")
            response = self._wait_for_input(prompt, "confirm", kwargs)
            return response.lower() in ("yes", "y", "true", "1", "confirm")
        
        return request_confirm
    
    def _wait_for_input(
        self, 
        prompt: str, 
        interaction_type: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Block and wait for user input from the frontend.
        
        Args:
            prompt: The prompt to show the user
            interaction_type: Type of input (text_input, text_editor, confirm)
            options: Additional options for the interaction
            
        Returns:
            The user's response as a string
        """
        request_id = str(uuid.uuid4())[:8]
        event = threading.Event()
        
        request = UserInputRequest(
            id=request_id,
            prompt=prompt,
            interaction_type=interaction_type,
            options=options or {},
        )
        
        with self._lock:
            self._pending_requests[request_id] = request
            self._events[request_id] = event
        
        # Emit WebSocket event to notify frontend
        self._emit("user_input:request", {
            "request_id": request_id,
            "prompt": prompt,
            "interaction_type": interaction_type,
            "options": options or {},
        })
        
        logger.info(f"Waiting for user input: {request_id} ({interaction_type})")
        
        # Block until response is received
        event.wait()
        
        # Get response and clean up
        with self._lock:
            response = self._pending_requests[request_id].response
            del self._pending_requests[request_id]
            del self._events[request_id]
        
        logger.info(f"Received user input for {request_id}")
        
        # Emit completion event
        self._emit("user_input:completed", {
            "request_id": request_id,
        })
        
        return str(response) if response is not None else ""
    
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
            if request_id not in self._pending_requests:
                logger.warning(f"No pending request found: {request_id}")
                return False
            
            self._pending_requests[request_id].response = response
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
        
        self._emit("user_input:cancelled", {
            "request_id": request_id,
        })
        
        return True
    
    def get_pending_requests(self) -> list:
        """Get all pending input requests."""
        with self._lock:
            return [
                {
                    "request_id": req.id,
                    "prompt": req.prompt,
                    "interaction_type": req.interaction_type,
                    "options": req.options,
                    "created_at": req.created_at,
                }
                for req in self._pending_requests.values()
                if not req.completed
            ]
    
    def has_pending_requests(self) -> bool:
        """Check if there are any pending requests."""
        with self._lock:
            return any(not req.completed for req in self._pending_requests.values())
