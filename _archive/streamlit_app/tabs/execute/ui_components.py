"""
UI components for the Execute tab.
Separated for better maintainability and testing.
"""

import streamlit as st
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from .constants import (
    MAX_OPERATIONS_DISPLAY, RECENT_OPERATIONS_COUNT, MAX_LOCATION_LENGTH,
    MAX_DETAIL_LENGTH, OPERATION_ICONS, OPERATION_COLORS, STATUS_ICONS, STATUS_COLORS
)
from .state import ExecutionState, ExecutionMetrics

logger = logging.getLogger(__name__)


def render_execution_metrics(metrics: ExecutionMetrics, max_cycles: int):
    """
    Render execution metrics in a clean column layout.
    
    Args:
        metrics: ExecutionMetrics instance
        max_cycles: Maximum number of cycles allowed
    """
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Cycle",
            f"{metrics.cycle_count}/{max_cycles}",
            delta=None
        )
    
    with col2:
        st.metric("Total Executions", metrics.total_executions)
    
    with col3:
        st.metric(
            "Completed",
            metrics.successful_executions,
            delta=f"{metrics.success_rate:.0f}%"
        )
    
    with col4:
        if metrics.failed_items > 0:
            st.metric("Failed", metrics.failed_items, delta="⚠️")
        else:
            st.metric("Retries", metrics.retry_count)
    
    with col5:
        st.metric("Time", f"{metrics.elapsed_time:.1f}s")


def render_progress_status(metrics: ExecutionMetrics) -> str:
    """
    Build a status message from metrics.
    
    Args:
        metrics: ExecutionMetrics instance
    
    Returns:
        Status message string
    """
    status_parts = []
    
    if metrics.completed_items > 0:
        status_parts.append(f"✅ {metrics.completed_items} completed")
    if metrics.in_progress_items > 0:
        status_parts.append(f"⏳ {metrics.in_progress_items} in progress")
    if metrics.pending_items > 0:
        status_parts.append(f"⏸️ {metrics.pending_items} pending")
    
    status_line = f"Items: {' | '.join(status_parts)}" if status_parts else "Starting..."
    
    if metrics.retry_count > 0:
        status_line += f" | 🔄 {metrics.retry_count} retries"
    
    return status_line


def render_file_operations_live(update_counter: int) -> None:
    """
    Render live file operations during execution.
    
    This drains the event queue and displays the most recent operations.
    
    Args:
        update_counter: Counter for tracking UI updates
    """
    st.markdown(f"### 📁 Recent File Operations (Update #{update_counter})")
    
    # Drain queue and retrieve logs
    if hasattr(st.session_state, 'file_operations_log_manager'):
        # Drain the queue to get latest events (if method exists)
        manager = st.session_state.file_operations_log_manager
        if hasattr(manager, 'drain_queue'):
            drained_count = manager.drain_queue()
            # Show drain info for debugging
            if drained_count > 0:
                logger.debug(f"Drained {drained_count} new file operation events from queue")
        
        current_logs = manager.get_logs()
    elif hasattr(st.session_state, 'file_operations_log'):
        current_logs = st.session_state.file_operations_log
    else:
        current_logs = []
    
    if current_logs:
        ops_count = len(current_logs)
        
        # Get queue size if available
        queue_size = 0
        if hasattr(st.session_state, 'file_operations_log_manager'):
            manager = st.session_state.file_operations_log_manager
            if hasattr(manager, 'queue_size'):
                queue_size = manager.queue_size()
        
        st.caption(f"Total operations: {ops_count} | Queue: {queue_size} pending")
        
        recent = list(reversed(current_logs[-RECENT_OPERATIONS_COUNT:]))
        
        for idx, op in enumerate(recent):
            _render_single_operation(op, idx)
    else:
        st.text("⏳ Waiting for file operations...")
        st.caption(f"Log manager initialized: {hasattr(st.session_state, 'file_operations_log_manager')}")


def _render_single_operation(op: Dict[str, Any], idx: int):
    """Render a single file operation entry."""
    try:
        ts = datetime.fromisoformat(op['timestamp']).strftime('%H:%M:%S')
    except:
        ts = str(op.get('timestamp', ''))[:8]
    
    # Determine operation icon
    op_type = op.get('operation', 'UNKNOWN')
    icon = OPERATION_ICONS.get(op_type, OPERATION_ICONS['UNKNOWN'])
    
    status_icon = STATUS_ICONS.get(op.get('status', 'WARNING'), STATUS_ICONS['WARNING'])
    
    # Format location
    location = op.get('location', 'unknown')
    try:
        file_path_obj = Path(location)
        loc = file_path_obj.name if len(location) > MAX_LOCATION_LENGTH else location
    except:
        loc = location[:MAX_LOCATION_LENGTH] if len(location) > MAX_LOCATION_LENGTH else location
    
    # Show details if available
    details = op.get('details', '')
    detail_text = f" - {details}" if details and len(details) < MAX_DETAIL_LENGTH else ""
    
    st.text(f"{ts} {icon} {op_type:15} {status_icon} {loc}{detail_text}")


def render_file_operations_monitor(allow_interactions: bool = True) -> None:
    """
    Render the file operations monitor section.
    Shows all file operations with filtering and statistics.
    
    This drains the event queue before displaying to ensure all events are shown.
    
    Args:
        allow_interactions: If False, disables interactive elements (buttons, filters)
                           to avoid key conflicts during live updates
    """
    is_executing = st.session_state.get('is_executing', False)
    
    # Drain queue and retrieve logs
    if hasattr(st.session_state, 'file_operations_log_manager'):
        manager = st.session_state.file_operations_log_manager
        
        # Always drain queue first to get latest events (if method exists)
        if hasattr(manager, 'drain_queue'):
            drained_count = manager.drain_queue()
            if drained_count > 0:
                logger.debug(f"Monitor: Drained {drained_count} new events from queue")
        
        current_logs = manager.get_logs()
    elif hasattr(st.session_state, 'file_operations_log'):
        current_logs = st.session_state.file_operations_log
    else:
        current_logs = []
    
    # Show operation count in header
    op_count = len(current_logs)
    
    # Get queue size if available
    queue_size = 0
    if hasattr(st.session_state, 'file_operations_log_manager'):
        manager = st.session_state.file_operations_log_manager
        if hasattr(manager, 'queue_size'):
            queue_size = manager.queue_size()
    
    if queue_size > 0:
        monitor_title = f"📁 File Operations Monitor ({op_count} operations, {queue_size} queued)"
    else:
        monitor_title = f"📁 File Operations Monitor ({op_count} operations)" if op_count > 0 else "📁 File Operations Monitor"
    
    with st.expander(monitor_title, expanded=(is_executing or op_count > 0)):
        if not current_logs:
            st.info("No file operations yet. Operations will appear here during execution.")
        else:
            _render_operations_list(current_logs, allow_interactions=allow_interactions)


def _render_operations_list(current_logs: List[Dict[str, Any]], allow_interactions: bool = True):
    """
    Render the complete operations list with statistics and filters.
    
    Args:
        current_logs: List of log entries to display
        allow_interactions: If False, disables interactive elements (buttons, filters)
    """
    # Calculate statistics
    total_ops = len(current_logs)
    success_count = sum(1 for op in current_logs if op['status'] == 'SUCCESS')
    error_count = total_ops - success_count
    
    # Count by operation type
    read_ops = sum(1 for op in current_logs if op['operation'] in ['READ', 'MEMORIZED_READ'])
    write_ops = sum(1 for op in current_logs if op['operation'] in ['SAVE', 'MEMORIZED_SAVE'])
    check_ops = sum(1 for op in current_logs if op['operation'] == 'EXISTS')
    
    # Header with statistics and clear button
    if allow_interactions:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**Total Operations:** {total_ops} | ✅ Success: {success_count} | ❌ Errors: {error_count}")
            st.markdown(f"📖 Reads: {read_ops} | 💾 Writes: {write_ops} | 🔍 Checks: {check_ops}")
        
        with col2:
            from core.config import clear_file_operations_log
            if st.button("🗑️ Clear Log", key="clear_file_ops", use_container_width=True):
                clear_file_operations_log()
                st.rerun()
    else:
        # Non-interactive version (for live updates)
        st.markdown(f"**Total Operations:** {total_ops} | ✅ Success: {success_count} | ❌ Errors: {error_count}")
        st.markdown(f"📖 Reads: {read_ops} | 💾 Writes: {write_ops} | 🔍 Checks: {check_ops}")
    
    st.divider()
    
    # Filter options (only if interactions allowed)
    if allow_interactions:
        col1, col2 = st.columns(2)
        with col1:
            filter_type = st.multiselect(
                "Filter by Operation Type",
                options=['READ', 'SAVE', 'EXISTS', 'MEMORIZED_READ', 'MEMORIZED_SAVE'],
                default=[],
                key="file_ops_filter_type"
            )
        with col2:
            filter_status = st.multiselect(
                "Filter by Status",
                options=['SUCCESS', 'ERROR'],
                default=[],
                key="file_ops_filter_status"
            )
        
        # Apply filters
        ops_to_display = current_logs
        if filter_type:
            ops_to_display = [op for op in ops_to_display if op['operation'] in filter_type]
        if filter_status:
            ops_to_display = [op for op in ops_to_display if op['status'] in filter_status]
    else:
        # No filtering during live updates - show all
        ops_to_display = current_logs
    
    st.divider()
    
    # Display operations
    ops_to_display = list(reversed(ops_to_display[-MAX_OPERATIONS_DISPLAY:]))
    
    for i, op in enumerate(ops_to_display):
        _render_detailed_operation(op, i, allow_interactions=allow_interactions)
    
    # Show filtering info
    filtered_total = len(ops_to_display)
    if allow_interactions and (filter_type or filter_status):
        st.caption(f"Showing {min(filtered_total, MAX_OPERATIONS_DISPLAY)} filtered operations (out of {total_ops} total)")
    elif total_ops > MAX_OPERATIONS_DISPLAY:
        st.caption(f"Showing most recent {MAX_OPERATIONS_DISPLAY} of {total_ops} operations")


def _render_detailed_operation(op: Dict[str, Any], index: int, allow_interactions: bool = True):
    """
    Render a detailed operation entry with all information.
    
    Args:
        op: Operation log entry
        index: Index in the display list
        allow_interactions: If False, disables the "Open folder" button
    """
    import subprocess
    import sys
    
    try:
        timestamp = datetime.fromisoformat(op['timestamp']).strftime('%H:%M:%S')
    except:
        timestamp = op['timestamp']
    
    # Get operation type icon and category
    operation_type = op['operation']
    if operation_type in ['READ', 'MEMORIZED_READ']:
        op_icon = "📖"
        op_category = "READ"
        op_color = "blue"
    elif operation_type in ['SAVE', 'MEMORIZED_SAVE']:
        op_icon = "💾"
        op_category = "WRITE"
        op_color = "violet"
    elif operation_type == 'EXISTS':
        op_icon = "🔍"
        op_category = "CHECK"
        op_color = "gray"
    else:
        op_icon = "📄"
        op_category = operation_type
        op_color = "gray"
    
    # Color code by status
    if op['status'] == 'SUCCESS':
        status_icon = "✅"
        status_color = "green"
    elif op['status'] == 'ERROR':
        status_icon = "❌"
        status_color = "red"
    else:
        status_icon = "⚠️"
        status_color = "orange"
    
    # Format location
    location = op['location']
    full_path = location
    if len(location) > MAX_LOCATION_LENGTH:
        path_obj = Path(location)
        location = f".../{path_obj.parent.name}/{path_obj.name}"
    
    # Display as columns
    if allow_interactions:
        col1, col2, col3, col4, col5 = st.columns([1, 2, 4, 3, 1])
        
        with col1:
            st.markdown(f"`{timestamp}`")
        with col2:
            st.markdown(f":{op_color}[{op_icon} **{op_category}**]")
        with col3:
            st.markdown(f"`{location}`")
        with col4:
            st.markdown(f":{status_color}[{status_icon} {op['details']}]")
        with col5:
            if st.button("📂", key=f"open_dir_{index}_{op['timestamp']}", help="Open containing folder"):
                _open_file_location(full_path)
    else:
        # Non-interactive version (no button)
        col1, col2, col3, col4 = st.columns([1, 2, 4, 4])
        
        with col1:
            st.markdown(f"`{timestamp}`")
        with col2:
            st.markdown(f":{op_color}[{op_icon} **{op_category}**]")
        with col3:
            st.markdown(f"`{location}`")
        with col4:
            st.markdown(f":{status_color}[{status_icon} {op['details']}]")
    
    if index < len(st.session_state.get('ops_to_display', [])) - 1:
        st.markdown("")


def _open_file_location(file_path: str):
    """Open the directory containing the specified file."""
    import subprocess
    import sys
    
    try:
        path = Path(file_path)
        
        if path.is_file():
            directory = path.parent
        elif path.is_dir():
            directory = path
        else:
            directory = path.parent
        
        directory = directory.resolve()
        
        if sys.platform == 'win32':
            if path.exists() and path.is_file():
                subprocess.run(['explorer', '/select,', str(path)], check=False)
            else:
                subprocess.run(['explorer', str(directory)], check=False)
        elif sys.platform == 'darwin':
            if path.exists() and path.is_file():
                subprocess.run(['open', '-R', str(path)], check=False)
            else:
                subprocess.run(['open', str(directory)], check=False)
        else:
            subprocess.run(['xdg-open', str(directory)], check=False)
        
        st.toast(f"📂 Opened folder: {directory.name}", icon="✅")
    except Exception as e:
        st.error(f"Failed to open location: {e}")
        st.code(file_path)


def render_debug_panel(state: ExecutionState):
    """
    Render a debug panel showing execution state details.
    
    Args:
        state: ExecutionState instance
    """
    with st.expander("🐛 Debug Information", expanded=False):
        st.json(state.get_status_summary())
        
        if state.debug_info:
            st.subheader("Debug Details")
            st.json(state.debug_info)
        
        if state.warnings:
            st.subheader("Warnings")
            for warning in state.warnings:
                st.warning(warning)

