"""
Deployment User Input Tool - CLI/API-based user input for NormCode deployment.

A standalone user input tool that provides:
- CLI-based input for interactive mode
- API-based input for server mode (with pending request queue)
- Non-interactive defaults for headless mode
- Same interface as infra UserInputTool
"""

import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class UserInputRequest:
    """A pending user input request."""
    id: str
    prompt: str
    interaction_type: str  # simple_text, text_editor, confirm, select
    options: Optional[Dict[str, Any]] = None
    response: Optional[Any] = None
    completed: bool = False
    created_at: float = field(default_factory=time.time)


class DeploymentUserInputTool:
    """
    A user input tool for deployment/server execution.
    
    Supports three modes:
    1. CLI mode (interactive=True): Prompts user via command line
    2. API mode (interactive=False): Waits for API response submission
    3. Non-interactive mode: Uses default values
    
    Interface matches infra._agent._models._user_input_tool.UserInputTool
    """
    
    def __init__(
        self,
        interactive: bool = True,
        non_interactive_defaults: Optional[Dict[str, Any]] = None,
        log_callback: Optional[Callable[[str, Dict], None]] = None,
    ):
        """
        Initialize the user input tool.
        
        Args:
            interactive: If True, prompt via CLI. If False, use API mode.
            non_interactive_defaults: Default values for non-interactive mode
            log_callback: Optional callback for logging events
        """
        self.interactive = interactive
        self.non_interactive_defaults = non_interactive_defaults or {}
        self._log_callback = log_callback
        self._pending_requests: Dict[str, UserInputRequest] = {}
        self._events: Dict[str, threading.Event] = {}
        self._lock = threading.Lock()
    
    def _log(self, event: str, data: Dict[str, Any]):
        """Log an event via callback if set."""
        if self._log_callback:
            try:
                self._log_callback(event, data)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")
    
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
        
        Args:
            **config: Configuration including:
                - interaction_type: Type of interaction
                - prompt_key: Key in kwargs containing the prompt text
                - initial_text_key: Key for initial text (for text_editor)
                - non_interactive_default: Default value if non-interactive
                
        Returns:
            A callable that takes **kwargs and returns user input
        """
        def interaction_fn(**kwargs: Any) -> Any:
            prompt_key = config.get("prompt_key", "prompt_text")
            prompt_text = kwargs.get(prompt_key, "Enter input: ")
            interaction_type = config.get("interaction_type", "simple_text")
            
            # Build options
            options = config.copy()
            
            # Handle text_editor initial text
            if interaction_type == "text_editor":
                initial_text_key = config.get("initial_text_key", "initial_text")
                initial_text = kwargs.get(initial_text_key, "")
                options["initial_content"] = initial_text
            
            # Check for non-interactive default
            non_interactive_default = config.get("non_interactive_default")
            if non_interactive_default is None:
                non_interactive_default = self.non_interactive_defaults.get(interaction_type)
            
            return self._get_input(prompt_text, interaction_type, options, non_interactive_default)
        
        return interaction_fn
    
    def _get_input(
        self,
        prompt: str,
        interaction_type: str,
        options: Optional[Dict[str, Any]] = None,
        default: Any = None
    ) -> Any:
        """
        Get user input based on mode.
        
        Args:
            prompt: The prompt to show
            interaction_type: Type of input
            options: Additional options
            default: Default value for non-interactive mode
            
        Returns:
            User input or default
        """
        self._log("user_input:request", {
            "prompt": prompt,
            "interaction_type": interaction_type,
            "options": options,
        })
        
        if self.interactive:
            return self._cli_input(prompt, interaction_type, options)
        else:
            return self._api_input(prompt, interaction_type, options, default)
    
    def _cli_input(
        self,
        prompt: str,
        interaction_type: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Get input via command line."""
        try:
            if interaction_type == "confirm":
                response = input(f"{prompt} [y/n]: ").strip().lower()
                result = response in ("y", "yes", "true", "1")
            elif interaction_type == "select":
                choices = options.get("choices", []) if options else []
                print(f"{prompt}")
                for i, choice in enumerate(choices, 1):
                    print(f"  {i}. {choice}")
                response = input("Enter number: ").strip()
                try:
                    idx = int(response) - 1
                    result = choices[idx] if 0 <= idx < len(choices) else choices[0]
                except (ValueError, IndexError):
                    result = choices[0] if choices else ""
            elif interaction_type == "text_editor":
                initial = options.get("initial_content", "") if options else ""
                print(f"{prompt}")
                if initial:
                    print(f"[Initial: {initial[:100]}...]")
                print("Enter text (end with Ctrl+D or empty line):")
                lines = []
                try:
                    while True:
                        line = input()
                        if not line:
                            break
                        lines.append(line)
                except EOFError:
                    pass
                result = "\n".join(lines) if lines else initial
            else:
                # simple_text
                result = input(f"{prompt}: ").strip()
            
            self._log("user_input:completed", {
                "interaction_type": interaction_type,
                "response_type": type(result).__name__,
            })
            
            return result
            
        except Exception as e:
            logger.error(f"CLI input failed: {e}")
            return ""
    
    def _api_input(
        self,
        prompt: str,
        interaction_type: str,
        options: Optional[Dict[str, Any]] = None,
        default: Any = None
    ) -> Any:
        """Wait for input via API (submit_response)."""
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
        
        self._log("user_input:pending", {
            "request_id": request_id,
            "prompt": prompt,
            "interaction_type": interaction_type,
        })
        
        logger.info(f"Waiting for user input: {request_id} ({interaction_type})")
        logger.info(f"Prompt: {prompt}")
        
        # Wait with timeout
        timeout = 300  # 5 minutes
        received = event.wait(timeout=timeout)
        
        # Get response and clean up
        with self._lock:
            if request_id in self._pending_requests:
                response = self._pending_requests[request_id].response
                del self._pending_requests[request_id]
            else:
                response = default
            if request_id in self._events:
                del self._events[request_id]
        
        if not received:
            logger.warning(f"Timeout waiting for input {request_id}, using default")
            response = default
        
        self._log("user_input:completed", {
            "request_id": request_id,
            "timed_out": not received,
        })
        
        return self._parse_response(response, interaction_type)
    
    def _parse_response(self, response: Any, interaction_type: str) -> Any:
        """Parse the response based on interaction type."""
        if response is None:
            if interaction_type == "confirm":
                return False
            return ""
        
        if interaction_type == "confirm":
            if isinstance(response, bool):
                return response
            return str(response).lower() in ("yes", "y", "true", "1", "confirm")
        
        return str(response) if response is not None else ""
    
    def submit_response(self, request_id: str, response: Any) -> bool:
        """
        Submit a response for a pending input request.
        
        Called by API when user provides input.
        
        Args:
            request_id: The request ID
            response: The user's response
            
        Returns:
            True if request was found and completed
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
        """Cancel a pending input request."""
        with self._lock:
            if request_id not in self._pending_requests:
                return False
            
            self._pending_requests[request_id].response = None
            self._pending_requests[request_id].completed = True
            self._events[request_id].set()
        
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

