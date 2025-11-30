"""
Results viewer tab for NormCode Orchestrator Streamlit App.
"""

import streamlit as st
import json
import os
from datetime import datetime

from infra._orchest._db import OrchestratorDB
from ui_components import (
    display_run_info_header,
    display_log_entry,
    display_concept_result
)


def render_results_tab(db_path: str):
    """
    Render the Results tab.
    
    Args:
        db_path: Path to the orchestrator database
    """
    st.header("Results Viewer")
    
    if not st.session_state.last_run:
        st.info("ℹ️ No results yet. Execute an orchestration in the **Execute** tab.")
        return
    
    run_data = st.session_state.last_run
    
    # Run info header
    display_run_info_header(run_data)
    
    st.divider()
    
    # Quick access to logs for this run
    _display_execution_logs(run_data, db_path)
    
    st.divider()
    
    # Export button
    _display_export_button(run_data)
    
    # Display concepts
    _display_final_concepts(run_data)


def _display_execution_logs(run_data, db_path):
    """Display execution logs for the current run."""
    st.subheader("📋 Execution Logs")
    
    if not os.path.exists(db_path):
        st.info("ℹ️ Database not found. Logs are only available when using database checkpoints.")
        return
    
    try:
        db_for_logs = OrchestratorDB(db_path)
        logs = db_for_logs.get_all_logs(run_data['run_id'])
        
        if not logs:
            st.info("ℹ️ No logs recorded for this run. This may be normal for older runs.")
            return
        
        st.caption(f"📊 {len(logs)} log entries available")
        
        # Quick view of recent logs
        with st.expander("View Recent Logs (Last 10)", expanded=False):
            recent_logs = logs[-10:] if len(logs) > 10 else logs
            for i, log in enumerate(reversed(recent_logs)):
                display_log_entry(log, show_divider=(i < len(recent_logs) - 1))
        
        # Full logs view
        if len(logs) > 10:
            with st.expander("View All Logs", expanded=False):
                for i, log in enumerate(logs):
                    display_log_entry(log, show_divider=(i < len(logs) - 1))
        
        # Export logs
        col1, col2 = st.columns([3, 1])
        with col2:
            log_export_data = {
                "run_id": run_data['run_id'],
                "logs": logs
            }
            st.download_button(
                label="💾 Export Logs",
                data=json.dumps(log_export_data, indent=2),
                file_name=f"logs_{run_data['run_id'][:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    except Exception as e:
        st.warning(f"Could not load logs: {e}")


def _display_export_button(run_data):
    """Display export button for results."""
    col1, col2 = st.columns([3, 1])
    with col2:
        results_json = {}
        for fc in run_data['final_concepts']:
            if fc and fc.concept and fc.concept.reference:
                results_json[fc.concept_name] = {
                    'tensor': fc.concept.reference.tensor,
                    'axes': fc.concept.reference.axes,
                    'shape': fc.concept.reference.shape
                }
        
        st.download_button(
            label="💾 Export as JSON",
            data=json.dumps(results_json, indent=2),
            file_name=f"results_{run_data['run_id'][:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )


def _display_final_concepts(run_data):
    """Display final concepts with filtering options."""
    st.subheader("📦 Final Concepts")
    
    # Filter options
    filter_option = st.radio(
        "Show:",
        ["All Concepts", "Only Completed", "Only Empty"],
        horizontal=True
    )
    
    for fc in run_data['final_concepts']:
        display_concept_result(fc, filter_option)

