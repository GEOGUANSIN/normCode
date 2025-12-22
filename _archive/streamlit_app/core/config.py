"""
Configuration and session state management for NormCode Orchestrator Streamlit App.
"""

import streamlit as st
from pathlib import Path
from core.log_manager import LogManager

# Get directory paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
REPO_FILES_DIR = SCRIPT_DIR / "saved_repositories"

# Ensure directories exist
REPO_FILES_DIR.mkdir(exist_ok=True)

# Default configuration values
DEFAULT_DB_PATH = "orchestration.db"
DEFAULT_LLM_MODEL = "qwen-plus"
DEFAULT_MAX_CYCLES = 50
APP_VERSION = "1.3.1"

# Available LLM models
LLM_MODELS = ["qwen-plus", "gpt-4o", "claude-3-sonnet", "qwen-turbo-latest"]

# Execution modes
EXECUTION_MODES = ["Fresh Run", "Resume from Checkpoint", "Fork from Checkpoint"]

# Reconciliation modes
RECONCILIATION_MODES = ["PATCH", "OVERWRITE", "FILL_GAPS"]


def init_session_state():
    """Initialize all session state variables."""
    if 'execution_log' not in st.session_state:
        st.session_state.execution_log = []
    
    if 'last_run' not in st.session_state:
        st.session_state.last_run = None
    
    if 'loaded_config' not in st.session_state:
        st.session_state.loaded_config = None
    
    if 'config_loaded_from_run' not in st.session_state:
        st.session_state.config_loaded_from_run = None
    
    if 'loaded_repo_files' not in st.session_state:
        st.session_state.loaded_repo_files = {
            'concepts': None,
            'inferences': None,
            'inputs': None
        }
    
    # Session state for human-in-the-loop user interactions
    if 'pending_user_inputs' not in st.session_state:
        st.session_state.pending_user_inputs = {}
    
    if 'orchestrator_state' not in st.session_state:
        st.session_state.orchestrator_state = None
    
    if 'waiting_for_input' not in st.session_state:
        st.session_state.waiting_for_input = False
    
    if 'current_interaction' not in st.session_state:
        st.session_state.current_interaction = None
    
    if 'show_success_message' not in st.session_state:
        st.session_state.show_success_message = False
    
    # File operations monitoring
    if 'file_operations_log_manager' not in st.session_state:
        st.session_state.file_operations_log_manager = LogManager()
    elif not hasattr(st.session_state.file_operations_log_manager, 'drain_queue'):
        # Reinitialize if old version without queue support
        # This handles upgrading from the old lock-based to new queue-based implementation
        st.session_state.file_operations_log_manager = LogManager()
    
    # Backward compatibility for code accessing the list directly (though they should switch to manager)
    if 'file_operations_log' not in st.session_state:
        st.session_state.file_operations_log = [] # Deprecated
    
    if 'is_executing' not in st.session_state:
        st.session_state.is_executing = False


def clear_loaded_config():
    """Clear loaded configuration and repository files."""
    st.session_state.loaded_config = None
    st.session_state.config_loaded_from_run = None
    st.session_state.loaded_repo_files = {
        'concepts': None,
        'inferences': None,
        'inputs': None
    }


def clear_results():
    """Clear execution results and logs."""
    st.session_state.last_run = None
    st.session_state.execution_log = []


def clear_interaction_state():
    """Clear human-in-the-loop interaction state."""
    st.session_state.waiting_for_input = False
    st.session_state.current_interaction = None
    st.session_state.orchestrator_state = None


def clear_file_operations_log():
    """Clear file operations log."""
    if 'file_operations_log_manager' in st.session_state:
        st.session_state.file_operations_log_manager.clear()
    st.session_state.file_operations_log = []

