"""
Chat controller services module.

This package provides modular chat controller functionality:
- registry_service: Controller discovery and registration
- message_service: Chat message history management
- placeholder_service: Demo/fallback responses when no controller connected

For backwards compatibility, the main ChatControllerService facade is available
from services.chat_controller_service.
"""

from .registry_service import (
    ControllerRegistryService,
    BUILT_IN_PROJECTS_DIR,
)

from .message_service import (
    ChatMessageService,
)

from .placeholder_service import (
    PlaceholderService,
    get_placeholder_service,
)

__all__ = [
    # Registry
    'ControllerRegistryService',
    'BUILT_IN_PROJECTS_DIR',
    # Messages
    'ChatMessageService',
    # Placeholder
    'PlaceholderService',
    'get_placeholder_service',
]

