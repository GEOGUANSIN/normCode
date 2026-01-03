"""
Placeholder Service - Provides demo/fallback responses when no controller is connected.

This service provides graceful degradation for demos and when no real
chat controller is available. It generates helpful responses about
NormCode concepts and Canvas usage.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class PlaceholderService:
    """
    Service for generating placeholder/demo responses.
    
    Used when:
    - No controller is connected
    - Controller fails to start
    - Demo mode is explicitly enabled
    
    Provides helpful guidance about NormCode while the real
    controller is not available.
    """
    
    def __init__(self):
        """Initialize the placeholder service."""
        self._response_handlers: List[Tuple[List[str], str]] = [
            (
                ["compile", "create", "parse"],
                "I can help you compile a NormCode plan!\n\n"
                "Share your plan in .ncds format, or describe what you'd like to build "
                "and I'll help you structure it."
            ),
            (
                ["help", "how", "what", "explain"],
                "NormCode is a language for structured AI plans.\n\n"
                "• **Concepts** — typed data containers\n"
                "• **Inferences** — operations that transform data\n"
                "• **Isolation** — each step sees only its explicit inputs\n\n"
                "What would you like to learn more about?"
            ),
            (
                ["debug", "error", "fix", "wrong"],
                "I can help debug your plan.\n\n"
                "Share the error message or describe what's happening, "
                "and I'll help you find the issue."
            ),
            (
                ["run", "execute", "start"],
                "To run a plan:\n\n"
                "1. Load a project (File → Open Project)\n"
                "2. Click the **Run** button in the control bar\n"
                "3. Use **Step** to execute one inference at a time\n\n"
                "You can also set breakpoints by clicking on nodes."
            ),
        ]
        
        self._default_response = (
            "I'm the demo assistant for NormCode Canvas.\n\n"
            "Try asking me to:\n"
            "• \"Help with NormCode\"\n"
            "• \"Explain concepts\"\n"
            "• \"Debug an error\"\n"
            "• \"Run my plan\""
        )
        
        self._welcome_message = (
            "Ready to help with your NormCode plans.\n\n"
            "• Compile — parse and validate plans\n"
            "• Explain — learn NormCode concepts\n"
            "• Debug — find and fix issues"
        )
    
    # =========================================================================
    # Response Generation
    # =========================================================================
    
    def get_welcome_message(self) -> str:
        """
        Get the welcome message for when the placeholder is activated.
        
        Returns:
            Welcome message content
        """
        return self._welcome_message
    
    def generate_response(self, user_content: str) -> str:
        """
        Generate a placeholder response based on user input.
        
        Analyzes the user's message for keywords and returns
        an appropriate helpful response.
        
        Args:
            user_content: The user's message content
            
        Returns:
            Generated response content
        """
        content_lower = user_content.lower()
        
        # Check each handler for matching keywords
        for keywords, response in self._response_handlers:
            if any(kw in content_lower for kw in keywords):
                return response
        
        # Return default if no keywords matched
        return self._default_response
    
    def is_placeholder_mode(self) -> bool:
        """
        Check if we're in placeholder mode.
        
        Always returns True for this service - it exists
        specifically to handle placeholder scenarios.
        """
        return True
    
    # =========================================================================
    # Customization
    # =========================================================================
    
    def add_response_handler(self, keywords: List[str], response: str):
        """
        Add a custom response handler.
        
        Args:
            keywords: List of keywords to match (case-insensitive)
            response: Response content to return when matched
        """
        self._response_handlers.insert(0, (keywords, response))
    
    def set_default_response(self, response: str):
        """
        Set the default response when no keywords match.
        
        Args:
            response: The default response content
        """
        self._default_response = response
    
    def set_welcome_message(self, message: str):
        """
        Set the welcome message.
        
        Args:
            message: The welcome message content
        """
        self._welcome_message = message


# =============================================================================
# Singleton Instance
# =============================================================================

_placeholder_service: Optional[PlaceholderService] = None


def get_placeholder_service() -> PlaceholderService:
    """Get the global placeholder service instance."""
    global _placeholder_service
    if _placeholder_service is None:
        _placeholder_service = PlaceholderService()
    return _placeholder_service

