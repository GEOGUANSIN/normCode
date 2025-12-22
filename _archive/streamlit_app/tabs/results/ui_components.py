"""
UI components for the Results tab.
Separated for better maintainability and testing.
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any, List

from ui.ui_components import display_log_entry
from .constants import (
    MAX_RECENT_LOGS, FILTER_ALL, FILTER_COMPLETED, FILTER_EMPTY,
    EXPORT_PREFIX_RESULTS, EXPORT_PREFIX_LOGS
)
from .concept_display import display_concept_result_enhanced


def render_execution_logs(run_data: Dict[str, Any], db):
    """
    Render execution logs for the current run.
    
    Args:
        run_data: Run data dictionary containing run_id
        db: OrchestratorDB instance
    """
    st.subheader("📋 Execution Logs")
    
    logs = db.get_all_logs(run_data['run_id'])
    
    if not logs:
        st.info("ℹ️ No logs recorded for this run. This may be normal for older runs.")
        return
    
    st.caption(f"📊 {len(logs)} log entries available")
    
    # Quick view of recent logs
    _render_recent_logs(logs)
    
    # Full logs view
    if len(logs) > MAX_RECENT_LOGS:
        _render_full_logs(logs)
    
    # Export logs button
    _render_log_export_button(run_data, logs)


def _render_recent_logs(logs: List[Dict[str, Any]]):
    """Render recent logs section."""
    with st.expander("View Recent Logs (Last 10)", expanded=False):
        recent_logs = logs[-MAX_RECENT_LOGS:] if len(logs) > MAX_RECENT_LOGS else logs
        for i, log in enumerate(reversed(recent_logs)):
            display_log_entry(log, show_divider=(i < len(recent_logs) - 1))


def _render_full_logs(logs: List[Dict[str, Any]]):
    """Render full logs section."""
    with st.expander("View All Logs", expanded=False):
        for i, log in enumerate(logs):
            display_log_entry(log, show_divider=(i < len(logs) - 1))


def _render_log_export_button(run_data: Dict[str, Any], logs: List[Dict[str, Any]]):
    """Render export logs button."""
    col1, col2 = st.columns([3, 1])
    with col2:
        log_export_data = {
            "run_id": run_data['run_id'],
            "logs": logs
        }
        st.download_button(
            label="💾 Export Logs",
            data=json.dumps(log_export_data, indent=2),
            file_name=f"{EXPORT_PREFIX_LOGS}_{run_data['run_id'][:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )


def render_export_button(run_data: Dict[str, Any]):
    """
    Render export button for results.
    
    Args:
        run_data: Run data dictionary containing final_concepts
    """
    col1, col2 = st.columns([3, 1])
    with col2:
        results_json = _prepare_results_export(run_data)
        
        st.download_button(
            label="💾 Export as JSON",
            data=json.dumps(results_json, indent=2),
            file_name=f"{EXPORT_PREFIX_RESULTS}_{run_data['run_id'][:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )


def _prepare_results_export(run_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare results data for export.
    
    Args:
        run_data: Run data dictionary
        
    Returns:
        Dictionary ready for JSON export
    """
    results_json = {}
    for fc in run_data['final_concepts']:
        if fc and fc.concept and fc.concept.reference:
            results_json[fc.concept_name] = {
                'tensor': fc.concept.reference.tensor,
                'axes': fc.concept.reference.axes,
                'shape': fc.concept.reference.shape
            }
    return results_json


def render_final_concepts(run_data: Dict[str, Any]):
    """
    Render final concepts with filtering options and enhanced tensor display.
    
    Args:
        run_data: Run data dictionary containing final_concepts
    """
    st.subheader("📦 Final Concepts")
    
    # Filter options
    filter_option = st.radio(
        "Show:",
        [FILTER_ALL, FILTER_COMPLETED, FILTER_EMPTY],
        horizontal=True
    )
    
    # Count concepts for display
    displayed_count = 0
    total_count = len(run_data['final_concepts'])
    
    # Display concepts based on filter using enhanced display
    for fc in run_data['final_concepts']:
        if display_concept_result_enhanced(fc, filter_option):
            displayed_count += 1
    
    # Show count
    if displayed_count < total_count:
        st.caption(f"Showing {displayed_count} of {total_count} concepts")


def render_no_results_message():
    """Render message when no results are available."""
    st.info("ℹ️ No results yet. Execute an orchestration in the **Execute** tab.")


def render_database_warning(db_path: str):
    """Render warning when database is not found."""
    st.info(f"ℹ️ Database not found: `{db_path}`. Logs are only available when using database checkpoints.")

