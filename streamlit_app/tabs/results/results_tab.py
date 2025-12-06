"""
Results viewer tab for NormCode Orchestrator Streamlit App.
REFACTORED for better debugging and maintainability.
"""

import streamlit as st
import os

from infra._orchest._db import OrchestratorDB
from ui.ui_components import display_run_info_header

from .ui_components import (
    render_execution_logs,
    render_export_button,
    render_final_concepts,
    render_no_results_message,
    render_database_warning
)


def render_results_tab(db_path: str):
    """
    Render the Results tab.
    
    Args:
        db_path: Path to the orchestrator database
    """
    st.header("Results Viewer")
    
    # Check if we have results
    if not st.session_state.last_run:
        render_no_results_message()
        return
    
    run_data = st.session_state.last_run
    
    # Run info header
    display_run_info_header(run_data)
    
    st.divider()
    
    # Quick access to logs for this run
    _display_execution_logs_section(run_data, db_path)
    
    st.divider()
    
    # Export button and final concepts
    render_export_button(run_data)
    render_final_concepts(run_data)


def _display_execution_logs_section(run_data, db_path: str):
    """
    Display execution logs section with error handling.
    
    Args:
        run_data: Run data dictionary
        db_path: Path to the orchestrator database
    """
    if not os.path.exists(db_path):
        render_database_warning(db_path)
        return
    
    try:
        db = OrchestratorDB(db_path)
        render_execution_logs(run_data, db)
    except Exception as e:
        st.warning(f"Could not load logs: {e}")

