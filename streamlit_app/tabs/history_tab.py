"""
Execution history tab for NormCode Orchestrator Streamlit App.
"""

import streamlit as st
import json
import os
from datetime import datetime

from infra._orchest._db import OrchestratorDB
from ui.ui_components import display_log_entry


def render_history_tab(db_path: str):
    """
    Render the History tab.
    
    Args:
        db_path: Path to the orchestrator database
    """
    st.header("Execution History")
    
    # Database runs
    st.subheader("💾 Database Runs")
    
    if not os.path.exists(db_path):
        st.warning(f"Database not found: `{db_path}`")
    else:
        _display_database_runs(db_path)
    
    st.divider()
    
    # Session execution log
    _display_session_log()


def _display_database_runs(db_path):
    """Display all runs from the database."""
    try:
        db = OrchestratorDB(db_path)
        runs = db.list_runs()
        
        if not runs:
            st.info("No runs found in database.")
            return
        
        for run in runs:
            _display_run_details(run, db)
    
    except Exception as e:
        st.error(f"Error loading database: {e}")
        st.exception(e)


def _display_run_details(run, db):
    """Display details for a single run."""
    with st.expander(f"🔖 {run['run_id']}", expanded=False):
        # Basic run info
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**First Execution:** {run['first_execution']}")
            st.write(f"**Last Execution:** {run['last_execution']}")
        
        with col2:
            st.write(f"**Execution Count:** {run['execution_count']}")
            st.write(f"**Max Cycle:** {run['max_cycle']}")
        
        st.divider()
        
        # Show run configuration
        _display_run_configuration(run, db)
        
        st.divider()
        
        # Show checkpoints
        _display_checkpoints(run, db)
        
        st.divider()
        
        # Show execution history
        _display_execution_history(run, db)
        
        st.divider()
        
        # Show logs
        _display_run_logs(run, db)


def _display_run_configuration(run, db):
    """Display run configuration metadata."""
    st.write("**Run Configuration:**")
    run_metadata = db.get_run_metadata(run['run_id'])
    
    if not run_metadata:
        st.caption("ℹ️ No configuration metadata available")
        return
    
    config_col1, config_col2 = st.columns(2)
    
    with config_col1:
        if 'llm_model' in run_metadata:
            st.caption(f"🤖 LLM Model: `{run_metadata['llm_model']}`")
        if 'max_cycles' in run_metadata:
            st.caption(f"🔄 Max Cycles: `{run_metadata['max_cycles']}`")
        if 'resume_mode' in run_metadata:
            st.caption(f"▶️ Mode: `{run_metadata['resume_mode']}`")
    
    with config_col2:
        if 'base_dir' in run_metadata:
            st.caption(f"📂 Base Dir: `{run_metadata['base_dir'][-30:]}`")
        if 'reconciliation_mode' in run_metadata:
            st.caption(f"🔧 Reconciliation: `{run_metadata['reconciliation_mode']}`")
        if 'forked_from_run_id' in run_metadata:
            st.caption(f"🔱 Forked from: `{run_metadata['forked_from_run_id'][:12]}...`")
    
    # Show full config with checkbox toggle
    show_full_config = st.checkbox(
        "View Full Configuration",
        key=f"show_config_{run['run_id']}"
    )
    if show_full_config:
        st.json(run_metadata)


def _display_checkpoints(run, db):
    """Display checkpoints for a run."""
    checkpoints = db.list_checkpoints(run['run_id'])
    
    if not checkpoints:
        return
    
    st.write(f"**Checkpoints:** {len(checkpoints)}")
    
    # Show last 3 checkpoints
    if len(checkpoints) <= 3:
        for cp in checkpoints:
            st.caption(
                f"Cycle {cp['cycle']}, Inference {cp.get('inference_count', 0)}: "
                f"{cp['timestamp']}"
            )
    else:
        st.caption(
            f"Latest: Cycle {checkpoints[-1]['cycle']}, "
            f"Inference {checkpoints[-1].get('inference_count', 0)}"
        )
        st.caption(f"... and {len(checkpoints) - 1} more")


def _display_execution_history(run, db):
    """Display execution history for a run."""
    st.write("**Execution History:**")
    execution_history = db.get_execution_history(run['run_id'])
    
    if not execution_history:
        return
    
    st.caption(f"Total executions: {len(execution_history)}")
    
    # Show summary with checkbox toggle
    show_exec_history = st.checkbox(
        "View Execution Summary", 
        key=f"show_exec_{run['run_id']}"
    )
    
    if show_exec_history:
        for exec_record in execution_history:
            status_icon = (
                "✅" if exec_record['status'] == 'success'
                else "❌" if exec_record['status'] == 'failed'
                else "⏳"
            )
            st.text(
                f"{status_icon} Cycle {exec_record['cycle']}, "
                f"Flow {exec_record['flow_index']}: "
                f"{exec_record['concept_inferred']} "
                f"[{exec_record['status']}]"
            )


def _display_run_logs(run, db):
    """Display logs for a run with filtering options."""
    st.write("**Detailed Logs:**")
    logs = db.get_all_logs(run['run_id'])
    
    if not logs:
        st.info("No logs available for this run.")
        return
    
    st.caption(f"Total log entries: {len(logs)}")
    
    # Filter options for logs
    log_filter = st.selectbox(
        "Filter logs by:",
        ["All Logs", "By Cycle", "By Status"],
        key=f"log_filter_{run['run_id']}"
    )
    
    filtered_logs = _filter_logs(logs, log_filter, run['run_id'])
    
    # Display logs with checkbox toggle
    show_logs = st.checkbox(
        f"View Logs ({len(filtered_logs)} entries)",
        key=f"show_logs_{run['run_id']}"
    )
    
    if show_logs:
        for i, log in enumerate(filtered_logs):
            display_log_entry(log, show_divider=(i < len(filtered_logs) - 1))
    
    # Export logs button
    col1, col2 = st.columns([3, 1])
    with col2:
        log_export_data = {
            "run_id": run['run_id'],
            "logs": filtered_logs
        }
        st.download_button(
            label="💾 Export Logs",
            data=json.dumps(log_export_data, indent=2),
            file_name=f"logs_{run['run_id'][:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            key=f"export_logs_{run['run_id']}",
            use_container_width=True
        )


def _filter_logs(logs, log_filter, run_id):
    """Filter logs based on selected filter option."""
    if log_filter == "All Logs":
        return logs
    
    elif log_filter == "By Cycle":
        cycles = sorted(set(log['cycle'] for log in logs))
        selected_cycle = st.selectbox(
            "Select Cycle:",
            cycles,
            key=f"cycle_select_{run_id}"
        )
        return [log for log in logs if log['cycle'] == selected_cycle]
    
    elif log_filter == "By Status":
        statuses = sorted(set(log['status'] for log in logs))
        selected_status = st.selectbox(
            "Select Status:",
            statuses,
            key=f"status_select_{run_id}"
        )
        return [log for log in logs if log['status'] == selected_status]
    
    return logs


def _display_session_log():
    """Display session execution log."""
    st.subheader("📋 Session Log")
    
    if not st.session_state.execution_log:
        st.info("No executions in this session yet.")
        return
    
    for log_entry in st.session_state.execution_log:
        if log_entry['status'] == 'success':
            st.success(
                f"✅ {log_entry['run_id'][:12]}... | "
                f"{datetime.fromisoformat(log_entry['timestamp']).strftime('%H:%M:%S')} | "
                f"{log_entry['duration']:.2f}s | "
                f"{log_entry['completed']} concepts"
            )
        else:
            st.error(
                f"❌ Failed | "
                f"{datetime.fromisoformat(log_entry['timestamp']).strftime('%H:%M:%S')} | "
                f"{log_entry.get('error', 'Unknown error')}"
            )

