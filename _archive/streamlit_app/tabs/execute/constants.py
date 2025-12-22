"""
Constants and configuration for the Execute tab.
"""

from typing import Final

# Display configuration
MAX_OPERATIONS_DISPLAY: Final[int] = 50
RECENT_OPERATIONS_COUNT: Final[int] = 8
MAX_LOCATION_LENGTH: Final[int] = 55
MAX_DETAIL_LENGTH: Final[int] = 30

# Update intervals
PROGRESS_UPDATE_INTERVAL: Final[float] = 0.5  # seconds

# Operation type icons
OPERATION_ICONS: Final[dict[str, str]] = {
    'READ': '📖',
    'MEMORIZED_READ': '📖',
    'SAVE': '💾',
    'MEMORIZED_SAVE': '💾',
    'EXISTS': '🔍',
    'UNKNOWN': '📄'
}

# Operation type colors
OPERATION_COLORS: Final[dict[str, str]] = {
    'READ': 'blue',
    'WRITE': 'violet',
    'CHECK': 'gray',
    'UNKNOWN': 'gray'
}

# Status icons and colors
STATUS_ICONS: Final[dict[str, str]] = {
    'SUCCESS': '✅',
    'ERROR': '❌',
    'WARNING': '⚠️'
}

STATUS_COLORS: Final[dict[str, str]] = {
    'SUCCESS': 'green',
    'ERROR': 'red',
    'WARNING': 'orange'
}

# Execution phases
class ExecutionPhase:
    """Enum-like class for execution phases."""
    SETUP = "setup"
    INPUT_INJECTION = "input_injection"
    VERIFICATION = "verification"
    ORCHESTRATOR_CREATION = "orchestrator_creation"
    EXECUTION = "execution"
    COMPLETION = "completion"
    ERROR = "error"

