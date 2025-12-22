"""
Constants and configuration for the Results tab.
"""

from typing import Final

# Display configuration
MAX_RECENT_LOGS: Final[int] = 10
MAX_CONCEPT_NAME_LENGTH: Final[int] = 50

# Filter options
FILTER_ALL: Final[str] = "All Concepts"
FILTER_COMPLETED: Final[str] = "Only Completed"
FILTER_EMPTY: Final[str] = "Only Empty"

# Log display icons
LOG_ICONS: Final[dict[str, str]] = {
    'success': '✅',
    'error': '❌',
    'warning': '⚠️',
    'info': 'ℹ️'
}

# Export file prefixes
EXPORT_PREFIX_RESULTS: Final[str] = "results"
EXPORT_PREFIX_LOGS: Final[str] = "logs"

