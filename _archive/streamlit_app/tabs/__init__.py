"""
Tab modules for NormCode Orchestrator Streamlit App.
"""

# Use the refactored execute tab (now organized in execute/ package)
from .execute import render_execute_tab

# Use the refactored results tab (now organized in results/ package)
from .results import render_results_tab

from .history_tab import render_history_tab
from .help_tab import render_help_tab
from .sandbox_tab import render_sandbox_tab
from .paradigms import render_paradigms_tab
from .normcode_editor_tab import render_normcode_editor_tab

__all__ = [
    'render_execute_tab',
    'render_results_tab',
    'render_history_tab',
    'render_help_tab',
    'render_sandbox_tab',
    'render_paradigms_tab',
    'render_normcode_editor_tab'
]

