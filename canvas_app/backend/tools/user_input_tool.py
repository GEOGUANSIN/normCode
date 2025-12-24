"""
Canvas-native user input tool for human-in-the-loop orchestration.

This tool uses WebSocket events to communicate with the frontend,
allowing the orchestrator to pause and wait for user input through the UI.

Unlike the Streamlit version which uses threading.Event, this version
uses asyncio.Event for async compatibility with FastAPI.

Interface matches infra._agent._models._user_input_tool.UserInputTool
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
    interaction_type: str  # simple_text, text_editor, confirm, select, multi_file_input
    options: Optional[Dict[str, Any]] = None
    response: Optional[Any] = None
    completed: bool = False
    created_at: float = field(default_factory=time.time)


class CanvasUserInputTool:
    """
    A user input tool that integrates with the Canvas app via WebSocket.
    
    Interface matches infra._agent._models._user_input_tool.UserInputTool
    
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
    
    # =========================================================================
    # Main Interface (matches infra UserInputTool)
    # =========================================================================
    
    def create_input_function(self, prompt_key: str = "prompt_text") -> Callable:
        """Creates a function that prompts the user for simple text input."""
        config = {"interaction_type": "simple_text", "prompt_key": prompt_key}
        return self.create_interaction(**config)
    
    def create_text_editor_function(
        self, 
        prompt_key: str = "prompt_text", 
        initial_text_key: str = "initial_text"
    ) -> Callable:
        """Creates a function that opens a text editor for the user."""
        config = {
            "interaction_type": "text_editor",
            "prompt_key": prompt_key,
            "initial_text_key": initial_text_key
        }
        return self.create_interaction(**config)
    
    def create_interaction(self, **config: Any) -> Callable:
        """
        Create an interaction function based on the provided configuration.
        
        This is the main entry point that matches the infra UserInputTool interface.
        
        Args:
            **config: Configuration including:
                - interaction_type: Type of interaction (simple_text, text_editor, 
                                    confirm, multi_file_input, etc.)
                - prompt_key: Key in kwargs containing the prompt text
                - initial_text_key: Key for initial text (for text_editor)
                - initial_directory: Initial directory (for multi_file_input)
                - non_interactive_default: Default value if non-interactive
                
        Returns:
            A callable that takes **kwargs and returns user input
        """
        def interaction_fn(**kwargs: Any) -> Any:
            prompt_key = config.get("prompt_key", "prompt_text")
            prompt_text = kwargs.get(prompt_key, "Enter input: ")
            interaction_type = config.get("interaction_type", "simple_text")
            
            # Build options to pass to frontend
            options = config.copy()
            
            # Handle text_editor initial text
            if interaction_type == "text_editor":
                initial_text_key = config.get("initial_text_key", "initial_text")
                initial_text = kwargs.get(initial_text_key, "")
                options["initial_content"] = initial_text
            
            # Handle multi_file_input initial directory
            if interaction_type == "multi_file_input":
                initial_directory = config.get("initial_directory", "")
                options["initial_directory"] = initial_directory
            
            # Map interaction types to frontend types
            frontend_type = self._map_interaction_type(interaction_type)
            
            return self._wait_for_input(prompt_text, frontend_type, options)
        
        return interaction_fn
    
    def _map_interaction_type(self, interaction_type: str) -> str:
        """Map infra interaction types to frontend types."""
        type_map = {
            "simple_text": "text_input",
            "text_editor": "text_editor",
            "confirm": "confirm",
            "multi_file_input": "multi_file_input",
            "validated_text": "text_input",
            "select": "select",
        }
        return type_map.get(interaction_type, "text_input")
    
    def _wait_for_input(
        self, 
        prompt: str, 
        interaction_type: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Block and wait for user input from the frontend.
        
        Args:
            prompt: The prompt to show the user
            interaction_type: Type of input (text_input, text_editor, confirm, etc.)
            options: Additional options for the interaction
            
        Returns:
            The user's response (string, list, bool, etc.)
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
        
        logger.info(f"Received user input for {request_id}: {type(response)}")
        
        # Emit completion event
        self._emit("user_input:completed", {
            "request_id": request_id,
        })
        
        # Parse response based on interaction type
        return self._parse_response(response, interaction_type)
    
    def _parse_response(self, response: Any, interaction_type: str) -> Any:
        """Parse the response based on interaction type."""
        if response is None:
            # Return appropriate default for type
            if interaction_type == "confirm":
                return False
            elif interaction_type == "multi_file_input":
                return []
            return ""
        
        if interaction_type == "confirm":
            if isinstance(response, bool):
                return response
            return str(response).lower() in ("yes", "y", "true", "1", "confirm")
        
        if interaction_type == "multi_file_input":
            # Response should be a list of file paths
            if isinstance(response, list):
                return response
            if isinstance(response, str):
                # Parse as newline-separated paths
                return [p.strip() for p in response.split('\n') if p.strip()]
            return []
        
        # Default: return as string
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
