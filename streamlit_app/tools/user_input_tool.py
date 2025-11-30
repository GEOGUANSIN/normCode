"""
Streamlit-native user input tool for human-in-the-loop orchestration.

This tool replaces the default CLI/GUI-based UserInputTool with one that
integrates seamlessly with Streamlit's session state and rerun mechanism.
"""

import streamlit as st
import logging
from typing import Callable, Any, Dict
import hashlib

logger = logging.getLogger(__name__)


class NeedsUserInteraction(Exception):
    """
    Exception raised when the orchestrator needs user input.
    
    This signals the Streamlit app to pause execution, show a UI element
    for user input, and resume after the user provides the input.
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
    A user input tool that integrates with Streamlit's session state.
    
    Instead of blocking execution with input() or tkinter dialogs,
    this tool raises NeedsUserInteraction exceptions that the app
    can catch, display UI for, and resume execution after.
    """
    
    def __init__(self, session_state_key: str = "pending_user_inputs"):
        """
        Args:
            session_state_key: The key in st.session_state where pending inputs are stored
        """
        self.session_state_key = session_state_key
        
        # Initialize session state if needed
        if self.session_state_key not in st.session_state:
            st.session_state[self.session_state_key] = {}
    
    def _generate_interaction_id(self, prompt: str, context: Dict[str, Any]) -> str:
        """
        Generate a unique but deterministic ID for an interaction.
        This allows the same prompt to be answered consistently during retries.
        """
        # Create a hash from prompt + relevant context
        context_str = str(sorted(context.items()))
        combined = f"{prompt}_{context_str}"
        return hashlib.md5(combined.encode()).hexdigest()[:16]
    
    def _get_pending_inputs(self) -> Dict[str, Any]:
        """Get the pending inputs dictionary from session state."""
        if self.session_state_key not in st.session_state:
            st.session_state[self.session_state_key] = {}
        return st.session_state[self.session_state_key]
    
    def _has_input(self, interaction_id: str) -> bool:
        """Check if input is available for a given interaction ID."""
        pending = self._get_pending_inputs()
        return interaction_id in pending
    
    def _get_input(self, interaction_id: str) -> Any:
        """Get and remove input for a given interaction ID."""
        pending = self._get_pending_inputs()
        value = pending.pop(interaction_id, None)
        logger.debug(f"Retrieved input for interaction {interaction_id}: {value}")
        return value
    
    def create_input_function(self, prompt_key: str = "prompt_text") -> Callable:
        """
        Creates a function that prompts the user for text input.
        
        This mimics the interface of UserInputTool.create_input_function()
        but integrates with Streamlit instead of CLI/GUI.
        
        Args:
            prompt_key: The key in kwargs that contains the prompt text
            
        Returns:
            A callable that either returns the input (if available) or raises NeedsUserInteraction
        """
        def input_fn(vars: Dict[str, Any] | None = None, **kwargs: Any) -> str:
            # Handle both positional dict and kwargs
            if vars is None:
                vars = {}
            
            # Merge kwargs into vars (kwargs take precedence)
            vars.update(kwargs)
            
            prompt_text = vars.get(prompt_key, "Enter input: ")
            
            # Build context from vars (excluding the prompt itself)
            context = {k: v for k, v in vars.items() if k != prompt_key}
            
            # Generate deterministic interaction ID
            interaction_id = self._generate_interaction_id(prompt_text, context)
            
            # Check if we already have the answer
            if self._has_input(interaction_id):
                value = self._get_input(interaction_id)
                logger.info(f"User input provided for '{prompt_text[:50]}...': '{value[:50]}...'")
                return value
            
            # If not, signal that we need user interaction
            logger.info(f"Requesting user input for: '{prompt_text[:100]}...'")
            raise NeedsUserInteraction(
                prompt=prompt_text,
                interaction_id=interaction_id,
                interaction_type="text_input",
                context=context
            )
        
        return input_fn
    
    def create_text_editor_function(self, prompt_key: str = "prompt_text", initial_text_key: str = "initial_text") -> Callable:
        """
        Creates a function that opens a text editor for the user to modify text.
        
        Args:
            prompt_key: The key in kwargs that contains the prompt to display
            initial_text_key: The key in kwargs that contains the initial text to edit
            
        Returns:
            A callable that either returns the edited text or raises NeedsUserInteraction
        """
        def editor_fn(vars: Dict[str, Any] | None = None, **kwargs: Any) -> str:
            # Handle both positional dict and kwargs
            if vars is None:
                vars = {}
            
            # Merge kwargs into vars
            vars.update(kwargs)
            
            prompt_text = vars.get(prompt_key, "Edit the text below:")
            initial_text = vars.get(initial_text_key, "")
            
            # Build context
            context = {k: v for k, v in vars.items() if k not in [prompt_key, initial_text_key]}
            
            # Generate interaction ID
            interaction_id = self._generate_interaction_id(prompt_text, context)
            
            # Check if we already have the answer
            if self._has_input(interaction_id):
                value = self._get_input(interaction_id)
                logger.info(f"User edited text provided for '{prompt_text[:50]}...'")
                return value
            
            # If not, signal that we need user interaction
            logger.info(f"Requesting text editor for: '{prompt_text[:100]}...'")
            raise NeedsUserInteraction(
                prompt=prompt_text,
                interaction_id=interaction_id,
                interaction_type="text_editor",
                initial_text=initial_text,
                context=context
            )
        
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
            A callable that either returns the result or raises NeedsUserInteraction
        """
        interaction_type = config.get("interaction_type", "text_input")
        prompt_key = config.get("prompt_key", "prompt_text")
        
        def interaction_fn(vars: Dict[str, Any] | None = None, **kwargs: Any) -> Any:
            # Handle both positional dict and kwargs
            if vars is None:
                vars = {}
            
            # Merge kwargs into vars
            vars.update(kwargs)
            
            prompt_text = vars.get(prompt_key, "User interaction required")
            
            # Build context from all kwargs and config
            context = {**config, **vars}
            context.pop(prompt_key, None)  # Remove prompt from context
            
            # Generate interaction ID
            interaction_id = self._generate_interaction_id(prompt_text, context)
            
            # Check if we already have the answer
            if self._has_input(interaction_id):
                value = self._get_input(interaction_id)
                logger.info(f"User interaction ({interaction_type}) completed: '{prompt_text[:50]}...'")
                return value
            
            # If not, signal that we need user interaction
            logger.info(f"Requesting user interaction ({interaction_type}): '{prompt_text[:100]}...'")
            raise NeedsUserInteraction(
                prompt=prompt_text,
                interaction_id=interaction_id,
                interaction_type=interaction_type,
                **context
            )
        
        return interaction_fn
    
    def provide_input(self, interaction_id: str, value: Any):
        """
        Manually provide input for a specific interaction ID.
        
        This is typically called by the Streamlit app after the user
        submits their response through the UI.
        
        Args:
            interaction_id: The interaction ID to provide input for
            value: The user's input value
        """
        pending = self._get_pending_inputs()
        pending[interaction_id] = value
        logger.info(f"Input provided for interaction {interaction_id}")
    
    def clear_all_inputs(self):
        """Clear all pending inputs from session state."""
        st.session_state[self.session_state_key] = {}
        logger.info("Cleared all pending user inputs")

