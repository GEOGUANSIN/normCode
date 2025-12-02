"""
Streamlit-native user input tool for human-in-the-loop orchestration.

This tool uses a threading-based approach where the orchestrator worker thread
blocks on a threading.Event while waiting for user input through the Streamlit UI.
"""

import streamlit as st
import logging
import threading
import time
from typing import Callable, Any, Dict, Optional
import hashlib

logger = logging.getLogger(__name__)


class NeedsUserInteraction(Exception):
    """
    Exception raised when the orchestrator needs user input.
    
    NOTE: This is kept for backwards compatibility but is NOT used
    in the threading-based approach.
    """
    def __init__(self, prompt: str, interaction_id: str, interaction_type: str = "text_input", **kwargs):
        """
        Args:
            prompt: The prompt/question to show the user
            interaction_id: Unique identifier for this interaction
            interaction_type: Type of interaction needed (text_input, text_editor, confirm, etc.)
            **kwargs: Additional context or configuration for the interaction
        """
        self.prompt = prompt
        self.interaction_id = interaction_id
        self.interaction_type = interaction_type
        self.kwargs = kwargs
        super().__init__(f"User interaction required: {prompt}")


class StreamlitInputTool:
    """
    A user input tool that integrates with Streamlit using threading.
    
    When user input is needed:
    1. Worker thread posts a request to session state
    2. Worker thread blocks on a threading.Event
    3. UI detects the pending request and shows a form
    4. User submits answer through UI
    5. UI writes response and sets the event
    6. Worker thread unblocks and returns the answer
    """
    
    def __init__(self):
        """Initialize the threading-based user input tool."""
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state for user input handling."""
        if "user_input_request" not in st.session_state:
            st.session_state.user_input_request = None
        
        if "user_input_response" not in st.session_state:
            st.session_state.user_input_response = None
        
        if "user_input_event" not in st.session_state:
            st.session_state.user_input_event = threading.Event()
        
        if "user_input_next_id" not in st.session_state:
            st.session_state.user_input_next_id = 1
    
    def create_input_function(self, prompt_key: str = "prompt_text", interaction_type: str = "text_input") -> Callable:
        """
        Creates a function that prompts the user for text input.
        
        This mimics the interface of UserInputTool.create_input_function()
        but blocks the worker thread until the UI provides an answer.
        
        Args:
            prompt_key: The key in kwargs that contains the prompt text
            interaction_type: Type of interaction (text_input, text_editor, etc.)
            
        Returns:
            A callable that blocks until user provides input via UI
        """
        def input_fn(vars: Dict[str, Any] | None = None, **kwargs: Any) -> str:
            # DEBUG: Log entry and delay
            logger.info("=" * 80)
            logger.info(f"[USER_INPUT_TOOL] TEXT INPUT EXECUTION STARTED")
            logger.info(f"[USER_INPUT_TOOL] vars={vars}")
            logger.info(f"[USER_INPUT_TOOL] kwargs={kwargs}")
            logger.info("=" * 80)
            time.sleep(0.5)  # Debug delay
            
            # Handle both positional dict and kwargs
            if vars is None:
                vars = {}
            
            # Merge kwargs into vars (kwargs take precedence)
            vars.update(kwargs)
            
            prompt_text = vars.get(prompt_key, "Enter input: ")
            
            # Allocate a new request ID
            request_id = st.session_state.user_input_next_id
            st.session_state.user_input_next_id += 1
            
            logger.info(f"[Worker] Requesting user input (ID={request_id}): '{prompt_text[:100]}...'")
            
            # Create the request object
            st.session_state.user_input_request = {
                "id": request_id,
                "prompt": prompt_text,
                "type": interaction_type,
                "vars": vars,
                "kwargs": kwargs
            }
            
            # Clear any old response + reset event
            st.session_state.user_input_response = None
            st.session_state.user_input_event.clear()
            
            # Block this worker thread until UI provides an answer
            logger.info(f"[Worker] Blocking on event (ID={request_id})...")
            event = st.session_state.user_input_event
            event.wait()  # Worker blocks here until UI calls event.set()
            
            # When unblocked, read the response
            logger.info(f"[Worker] Unblocked! Reading response (ID={request_id})...")
            resp = st.session_state.user_input_response
            
            if not resp or resp.get("id") != request_id:
                # Defensive fallback
                logger.error(f"[Worker] Response mismatch! Expected ID={request_id}, got {resp}")
                raise RuntimeError(f"user_input response mismatch or missing (expected ID={request_id})")
            
            answer = resp["answer"]
            logger.info(f"[Worker] Received answer (ID={request_id}): '{str(answer)[:50]}...'")
            
            # Clear the request now that it's been handled
            st.session_state.user_input_request = None
            
            return answer
        
        return input_fn
    
    def create_text_editor_function(self, prompt_key: str = "prompt_text", initial_text_key: str = "initial_text") -> Callable:
        """
        Creates a function that opens a text editor for the user to modify text.
        
        Args:
            prompt_key: The key in kwargs that contains the prompt to display
            initial_text_key: The key in kwargs that contains the initial text to edit
            
        Returns:
            A callable that blocks until user provides edited text via UI
        """
        def editor_fn(vars: Dict[str, Any] | None = None, **kwargs: Any) -> str:
            # DEBUG: Log entry and delay
            logger.info("=" * 80)
            logger.info(f"[USER_INPUT_TOOL] TEXT EDITOR EXECUTION STARTED")
            logger.info(f"[USER_INPUT_TOOL] vars={vars}")
            logger.info(f"[USER_INPUT_TOOL] kwargs={kwargs}")
            logger.info("=" * 80)
            time.sleep(0.5)  # Debug delay
            
            # Handle both positional dict and kwargs
            if vars is None:
                vars = {}
            
            # Merge kwargs into vars
            vars.update(kwargs)
            
            prompt_text = vars.get(prompt_key, "Edit the text below:")
            initial_text = vars.get(initial_text_key, "")
            
            # Store initial_text in vars for UI to access
            vars["initial_text"] = initial_text
            
            # Allocate a new request ID
            request_id = st.session_state.user_input_next_id
            st.session_state.user_input_next_id += 1
            
            logger.info(f"[Worker] Requesting text editor (ID={request_id}): '{prompt_text[:100]}...'")
            
            # Create the request object
            st.session_state.user_input_request = {
                "id": request_id,
                "prompt": prompt_text,
                "type": "text_editor",
                "vars": vars,
                "kwargs": kwargs
            }
            
            # Clear any old response + reset event
            st.session_state.user_input_response = None
            st.session_state.user_input_event.clear()
            
            # Block this worker thread until UI provides an answer
            logger.info(f"[Worker] Blocking on event (ID={request_id})...")
            event = st.session_state.user_input_event
            event.wait()
            
            # When unblocked, read the response
            logger.info(f"[Worker] Unblocked! Reading response (ID={request_id})...")
            resp = st.session_state.user_input_response
            
            if not resp or resp.get("id") != request_id:
                logger.error(f"[Worker] Response mismatch! Expected ID={request_id}, got {resp}")
                raise RuntimeError(f"user_input response mismatch or missing (expected ID={request_id})")
            
            answer = resp["answer"]
            logger.info(f"[Worker] Received edited text (ID={request_id})")
            
            # Clear the request now that it's been handled
            st.session_state.user_input_request = None
            
            return answer
        
        return editor_fn
    
    def create_interaction(self, **config: Any) -> Callable:
        """
        Creates a generic interaction function.
        
        This is the most flexible method that supports various interaction types.
        
        Args:
            **config: Configuration for the interaction, including:
                - interaction_type: Type of interaction (text_input, text_editor, confirm, etc.)
                - prompt_key: Key for the prompt text in kwargs
                - Other type-specific config
                
        Returns:
            A callable that blocks until user provides response via UI
        """
        interaction_type = config.get("interaction_type", "text_input")
        prompt_key = config.get("prompt_key", "prompt_text")
        
        def interaction_fn(vars: Dict[str, Any] | None = None, **kwargs: Any) -> Any:
            # DEBUG: Log entry and delay
            logger.info("=" * 80)
            logger.info(f"[USER_INPUT_TOOL] GENERIC INTERACTION EXECUTION STARTED")
            logger.info(f"[USER_INPUT_TOOL] interaction_type={interaction_type}")
            logger.info(f"[USER_INPUT_TOOL] vars={vars}")
            logger.info(f"[USER_INPUT_TOOL] kwargs={kwargs}")
            logger.info("=" * 80)
            time.sleep(0.5)  # Debug delay
            
            # Handle both positional dict and kwargs
            if vars is None:
                vars = {}
            
            # Merge kwargs into vars
            vars.update(kwargs)
            
            prompt_text = vars.get(prompt_key, "User interaction required")
            
            # Allocate a new request ID
            request_id = st.session_state.user_input_next_id
            st.session_state.user_input_next_id += 1
            
            logger.info(f"[Worker] Requesting interaction (ID={request_id}, type={interaction_type}): '{prompt_text[:100]}...'")
            
            # Create the request object
            st.session_state.user_input_request = {
                "id": request_id,
                "prompt": prompt_text,
                "type": interaction_type,
                "vars": vars,
                "kwargs": kwargs,
                "config": config
            }
            
            # Clear any old response + reset event
            st.session_state.user_input_response = None
            st.session_state.user_input_event.clear()
            
            # Block this worker thread until UI provides an answer
            logger.info(f"[Worker] Blocking on event (ID={request_id})...")
            event = st.session_state.user_input_event
            event.wait()
            
            # When unblocked, read the response
            logger.info(f"[Worker] Unblocked! Reading response (ID={request_id})...")
            resp = st.session_state.user_input_response
            
            if not resp or resp.get("id") != request_id:
                logger.error(f"[Worker] Response mismatch! Expected ID={request_id}, got {resp}")
                raise RuntimeError(f"user_input response mismatch or missing (expected ID={request_id})")
            
            answer = resp["answer"]
            logger.info(f"[Worker] Received answer (ID={request_id}, type={interaction_type})")
            
            # Clear the request now that it's been handled
            st.session_state.user_input_request = None
            
            return answer
        
        return interaction_fn

