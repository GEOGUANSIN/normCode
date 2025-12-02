"""
Execute orchestration tab for NormCode Orchestrator Streamlit App.
REFACTORED for better debugging and maintainability.
"""

import streamlit as st
import json
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional

from infra import ConceptRepo, InferenceRepo
from tools import NeedsUserInteraction

from core.config import (
    SCRIPT_DIR, PROJECT_ROOT, clear_interaction_state, 
    clear_results, clear_file_operations_log
)
from core.file_utils import get_file_content
from ui.ui_components import (
    display_execution_summary,
    display_concept_preview,
    display_inference_preview,
    display_inputs_preview
)

# Import new refactored modules
from .state import ExecutionState, ExecutionStatus
from .engine import OrchestrationExecutionEngine
from .ui_components import (
    render_execution_metrics,
    render_progress_status,
    render_file_operations_live,
    render_file_operations_monitor,
    render_debug_panel
)
from .constants import ExecutionPhase

logger = logging.getLogger(__name__)


def render_execute_tab(config: Dict[str, Any]):
    """
    Render the Execute tab with improved structure.
    
    Args:
        config: Configuration dictionary from sidebar
    """
    st.header("Execute Orchestration")
    
    # Check for pending user input requests FIRST (before anything else)
    if st.session_state.get("user_input_request") is not None:
        request = st.session_state.user_input_request
        response = st.session_state.get("user_input_response")
        
        # Only show form if no response yet
        if response is None:
            logger.info(f"[UI] Showing user input form for request ID={request['id']}")
            st.info("⏸️ **Orchestration is waiting for your input...**")
            _render_user_input_form_inline(request)
            # Don't use st.stop() - let the rest of the page render so auto-polling continues
    
    # Show success message from previous resumption if flag is set
    if st.session_state.get('show_success_message', False):
        st.success("✅ Execution completed successfully!")
        st.balloons()
        st.session_state.show_success_message = False
        
        if st.session_state.last_run:
            display_execution_summary(st.session_state.last_run)
    
    # Check if we have files
    loaded_concepts = st.session_state.loaded_repo_files.get('concepts')
    loaded_inferences = st.session_state.loaded_repo_files.get('inferences')
    loaded_inputs = st.session_state.loaded_repo_files.get('inputs')
    
    has_concepts = config['concepts_file'] is not None or loaded_concepts is not None
    has_inferences = config['inferences_file'] is not None or loaded_inferences is not None
    
    if not (has_concepts and has_inferences):
        _render_instructions()
        return
    
    # Preview section
    _render_file_previews(config, loaded_concepts, loaded_inferences, loaded_inputs)
    
    st.divider()
    
    # File operations monitor (always visible) - placeholder for dynamic updates
    file_ops_placeholder = st.empty()
    
    st.divider()
    
    # Execution controls
    _render_execution_controls(config, loaded_concepts, loaded_inferences, loaded_inputs, file_ops_placeholder)


def _render_interaction_form(config: Dict[str, Any]):
    """Render the human-in-the-loop interaction form."""
    interaction = st.session_state.current_interaction
    
    st.warning("⏸️ **Execution Paused - Awaiting User Input**")
    st.markdown(f"**Prompt:** {interaction['prompt']}")
    
    with st.form(key="user_interaction_form"):
        # Show interaction type-specific UI
        if interaction['type'] == 'text_editor':
            initial_text = interaction['kwargs'].get('initial_text', '')
            st.caption(f"Initial text ({len(initial_text)} characters):")
            st.code(initial_text, language="text")
            user_input = st.text_area(
                "Edit the text below:",
                value=initial_text,
                height=300,
                key="interaction_text_editor"
            )
        elif interaction['type'] == 'confirm':
            user_input = st.radio(
                "Please confirm:",
                options=[True, False],
                format_func=lambda x: "Yes" if x else "No",
                key="interaction_confirm"
            )
        else:
            user_input = st.text_input(
                "Your response:",
                key="interaction_text_input"
            )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submit_btn = st.form_submit_button("✅ Submit & Resume", type="primary", use_container_width=True)
        with col2:
            cancel_btn = st.form_submit_button("❌ Cancel Execution", use_container_width=True)
        
        if submit_btn:
            _handle_interaction_submit(user_input, interaction, config)
        elif cancel_btn:
            _handle_interaction_cancel()
    
    st.divider()
    st.info("💡 **Tip:** The orchestrator will resume from where it paused once you submit your response.")


def _handle_interaction_submit(user_input: Any, interaction: Dict[str, Any], config: Dict[str, Any]):
    """Handle submission of user interaction."""
    st.session_state.pending_user_inputs[interaction['id']] = user_input
    
    orchestrator_data = st.session_state.orchestrator_state
    if not orchestrator_data:
        st.error("Cannot resume: Orchestrator state not found.")
        return
    
    try:
        with st.spinner("▶️ Resuming execution..."):
            # Re-load repos from session state
            concepts_content = st.session_state.loaded_repo_files['concepts']['content']
            inferences_content = st.session_state.loaded_repo_files['inferences']['content']
            
            concepts_json = json.loads(concepts_content)
            inferences_json = json.loads(inferences_content)
            
            resume_concept_repo = ConceptRepo.from_json_list(concepts_json)
            resume_inference_repo = InferenceRepo.from_json_list(inferences_json, resume_concept_repo)
            
            # Re-init Body & Tools
            from infra._agent._body import Body
            from infra import Orchestrator
            from tools import StreamlitInputTool, StreamlitFileSystemTool
            
            resume_body = Body(
                llm_name=orchestrator_data['llm_model'],
                base_dir=orchestrator_data['base_dir']
            )
            
            resume_body.user_input = StreamlitInputTool()
            
            # Pass the log manager reference
            log_manager = None
            if hasattr(st, 'session_state') and 'file_operations_log_manager' in st.session_state:
                log_manager = st.session_state.file_operations_log_manager
                logger.info(f"ExecuteTab (Resume): Found file_operations_log_manager (id={id(log_manager)})")
            else:
                logger.warning("ExecuteTab (Resume): st.session_state.file_operations_log_manager not found!")
                
            resume_body.file_system = StreamlitFileSystemTool(
                base_dir=orchestrator_data['base_dir'],
                log_manager=log_manager
            )
            
            # Load Checkpoint
            orchestrator = Orchestrator.load_checkpoint(
                concept_repo=resume_concept_repo,
                inference_repo=resume_inference_repo,
                db_path=orchestrator_data['db_path'],
                run_id=orchestrator_data['run_id'],
                body=resume_body,
                mode="OVERWRITE"
            )
            
            start_time = orchestrator_data['start_time']
            
            # Continue execution
            final_concepts = orchestrator.run()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Success!
            _store_execution_results(orchestrator, final_concepts, duration, config)
            
            clear_interaction_state()
            st.session_state.show_success_message = True
            st.rerun()
    
    except NeedsUserInteraction as next_interaction:
        st.session_state.current_interaction = {
            'id': next_interaction.interaction_id,
            'type': next_interaction.interaction_type,
            'prompt': next_interaction.prompt,
            'kwargs': next_interaction.kwargs
        }
        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Execution failed: {str(e)}")
        st.exception(e)
        clear_interaction_state()


def _handle_interaction_cancel():
    """Handle cancellation of user interaction."""
    st.warning("Execution cancelled by user")
    clear_interaction_state()
    st.rerun()


def _render_user_input_form_inline(request: Dict[str, Any]):
    """
    Render user input form inline during execution (threading-based approach).
    
    Args:
        request: The user input request dict from session state
    """
    st.warning("⏸️ **Orchestrator Needs Your Input**")
    st.markdown(f"**Prompt:** {request['prompt']}")
    
    with st.form(key=f"user_input_form_{request['id']}"):
        # Show interaction type-specific UI
        if request['type'] == 'text_editor':
            initial_text = request.get('vars', {}).get('initial_text', '')
            st.caption(f"Initial text ({len(initial_text)} characters):")
            if initial_text:
                st.code(initial_text, language="text")
            user_input = st.text_area(
                "Edit the text below:",
                value=initial_text,
                height=300,
                key=f"input_editor_{request['id']}"
            )
        elif request['type'] == 'confirm':
            user_input = st.radio(
                "Please confirm:",
                options=[True, False],
                format_func=lambda x: "Yes" if x else "No",
                key=f"input_confirm_{request['id']}"
            )
        else:  # text_input
            user_input = st.text_input(
                "Your response:",
                key=f"input_text_{request['id']}"
            )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submit_btn = st.form_submit_button("✅ Submit & Continue", type="primary", use_container_width=True)
        with col2:
            cancel_btn = st.form_submit_button("❌ Cancel Execution", use_container_width=True)
        
        if submit_btn:
            # Write response to session state
            st.session_state.user_input_response = {
                "id": request["id"],
                "answer": user_input
            }
            # Signal the worker thread to continue
            st.session_state.user_input_event.set()
            logger.info(f"[UI] User submitted answer for request ID={request['id']}, event set")
            
            # Clear the request so form doesn't show again
            st.session_state.user_input_request = None
            
            st.success("✅ Answer submitted! Worker thread will continue...")
            time.sleep(0.3)  # Brief pause to show success message
            
            # CRITICAL: Rerun to resume the polling loop
            st.rerun()
        
        elif cancel_btn:
            st.warning("Execution cancelled by user")
            st.session_state.user_input_request = None
            st.session_state.is_executing = False
            # For cancel, we DO need to rerun to stop showing the form
            st.rerun()
    
    st.divider()
    st.info("💡 **Tip:** The orchestrator is waiting for your response. Submit your answer to continue execution.")


def _render_instructions():
    """Render instructions when no files are uploaded."""
    st.info("👈 **Please upload repository files in the sidebar to begin**")
    
    st.markdown("""
    ### Required Files:
    1. **concepts.json** - Defines the concepts (variables/data structures)
    2. **inferences.json** - Defines the inference steps (logic/operations)
    3. **inputs.json** (optional) - Provides initial data for ground concepts
    
    You can find example files in `infra/examples/add_examples/repo/`
    """)


def _render_file_previews(
    config: Dict[str, Any],
    loaded_concepts: Optional[Dict],
    loaded_inferences: Optional[Dict],
    loaded_inputs: Optional[Dict]
):
    """Render file preview sections."""
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            concepts_content = get_file_content(config['concepts_file'], loaded_concepts)
            concepts_data = json.loads(concepts_content)
            display_concept_preview(concepts_data)
        except Exception as e:
            st.error(f"Error loading concepts: {e}")
    
    with col2:
        try:
            inferences_content = get_file_content(config['inferences_file'], loaded_inferences)
            inferences_data = json.loads(inferences_content)
            display_inference_preview(inferences_data)
        except Exception as e:
            st.error(f"Error loading inferences: {e}")
    
    # Inputs preview
    has_inputs = config['inputs_file'] is not None or loaded_inputs is not None
    if has_inputs:
        try:
            inputs_content = get_file_content(config['inputs_file'], loaded_inputs)
            inputs_data = json.loads(inputs_content)
            display_inputs_preview(inputs_data)
        except Exception as e:
            st.error(f"Error loading inputs: {e}")


def _render_execution_controls(
    config: Dict[str, Any],
    loaded_concepts: Optional[Dict],
    loaded_inferences: Optional[Dict],
    loaded_inputs: Optional[Dict],
    file_ops_placeholder=None
):
    """Render execution control buttons."""
    # Always render the file operations monitor (before execution or when not executing)
    if not st.session_state.get('is_executing', False) and file_ops_placeholder is not None:
        with file_ops_placeholder.container():
            render_file_operations_monitor(allow_interactions=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    # Disable execute button if already executing
    is_currently_executing = st.session_state.get('is_executing', False)
    
    with col1:
        execute_btn = st.button(
            "▶️ **Start Execution**" if not is_currently_executing else "⏳ **Executing...**",
            type="primary",
            use_container_width=True,
            disabled=is_currently_executing
        )
    
    with col2:
        if st.button("🗑️ Clear Results", use_container_width=True):
            clear_results()
            st.success("Results cleared!")
            st.rerun()
    
    if execute_btn and not is_currently_executing:
        # Import threading early since we need it for checks
        import threading
        from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
        
        # Double-check: if there's already a running thread, don't start another
        existing_thread = st.session_state.get('execution_thread')
        if existing_thread and existing_thread.is_alive():
            logger.warning("[MAIN] Execution thread already running! Ignoring button click.")
            st.warning("⚠️ An execution is already in progress!")
            return
        
        # CRITICAL: Set the flag IMMEDIATELY before starting thread
        st.session_state.is_executing = True
        logger.info("[MAIN] Execute button clicked, setting is_executing=True")
        
        # Reset any stale session state from previous runs
        st.session_state.user_input_request = None
        st.session_state.user_input_response = None
        if 'user_input_event' in st.session_state:
            st.session_state.user_input_event.clear()  # Reset the event
        else:
            st.session_state.user_input_event = threading.Event()
        st.session_state.user_input_next_id = 1  # Reset ID counter for new execution
        
        # Clear any previous execution state
        if 'execution_completed' in st.session_state:
            del st.session_state.execution_completed
        if 'execution_result' in st.session_state:
            del st.session_state.execution_result
        if 'execution_error' in st.session_state:
            del st.session_state.execution_error
        
        # Get current script run context
        ctx = get_script_run_ctx()
        
        def run_in_thread():
            """Run sync execution in a thread with Streamlit context."""
            try:
                logger.info("[THREAD] Starting sync execution...")
                _execute_orchestration_sync(
                    config, loaded_concepts, loaded_inferences, loaded_inputs
                )
                logger.info("[THREAD] Sync execution completed")
            except Exception as e:
                logger.error(f"[THREAD] Execution error: {e}", exc_info=True)
                st.session_state.is_executing = False
                st.session_state.execution_error = str(e)
        
        thread = threading.Thread(target=run_in_thread, daemon=True, name="OrchestratorThread")
        
        # Add script run context to thread before starting
        if ctx:
            add_script_run_ctx(thread, ctx)
            logger.info(f"[MAIN] Added script run context to execution thread")
        
        thread.start()
        
        # Store thread in session state
        st.session_state.execution_thread = thread
        logger.info(f"[MAIN] Started execution thread: {thread.name}")
        
        # Trigger immediate rerun to start showing progress
        time.sleep(0.1)
        st.rerun()
    
    # Check if execution completed successfully (MUST be checked BEFORE is_currently_executing)
    if st.session_state.get('execution_completed', False):
        result = st.session_state.execution_result
        
        # Clear flags
        st.session_state.execution_completed = False
        if 'execution_result' in st.session_state:
            del st.session_state.execution_result
        
        # Drain file operations log
        manager = st.session_state.file_operations_log_manager
        if hasattr(manager, 'drain_queue'):
            manager.drain_queue()
        file_ops_count = len(manager)
        
        # Store results
        _store_execution_results_from_result(result, config)
        
        # Show success
        st.success(f"✅ Execution completed in {result['duration']:.2f}s! ({file_ops_count} file operations)")
        display_execution_summary(
            {'run_id': result['run_id'], 'final_concepts': result['final_concepts']},
            result['duration']
        )
        st.balloons()
        return
    
    # Check if there's an execution error (MUST be checked BEFORE is_currently_executing)
    if 'execution_error' in st.session_state:
        error = st.session_state.execution_error
        exception = st.session_state.get('execution_exception')
        
        st.error(f"❌ Execution error: {error}")
        if exception:
            st.exception(exception)
        
        # Clean up
        del st.session_state.execution_error
        if 'execution_exception' in st.session_state:
            del st.session_state.execution_exception
        st.session_state.is_executing = False
        return
    
    # If execution is running, show live status using fragment for smoother updates
    if is_currently_executing:
        _render_live_execution_status(config)


@st.fragment(run_every=1.0)  # Auto-refresh this fragment every 1 second
def _render_live_execution_status(config: Dict[str, Any]):
    """
    Render live execution status using st.fragment for smoother updates.
    This fragment auto-refreshes every 1 second WITHOUT rerunning the entire page.
    """
    # CRITICAL: Check for pending user input - need full rerun to show form
    if st.session_state.get("user_input_request") is not None:
        response = st.session_state.get("user_input_response")
        if response is None:
            logger.info("[FRAGMENT] Detected user input request - triggering full rerun")
            st.warning("⏸️ **User input required - refreshing page...**")
            time.sleep(0.2)
            st.rerun()  # Full rerun to show user input form at top of page
            return
    
    # Check if execution is still running
    if not st.session_state.get('is_executing', False):
        st.success("✅ Execution completed! Refreshing page...")
        time.sleep(0.5)
        st.rerun()  # Full rerun only when execution completes
        return
    
    # Check for completion
    if st.session_state.get('execution_completed', False):
        st.success("✅ Execution completed!")
        time.sleep(0.3)
        st.rerun()  # Full rerun to show results
        return
    
    # Check for errors
    if 'execution_error' in st.session_state:
        st.error(f"❌ Error: {st.session_state.execution_error}")
        time.sleep(0.3)
        st.rerun()  # Full rerun to show error
        return
    
    # Show current status header
    st.info("⏳ **Execution in progress...** (Auto-updates every second)")
    
    # Show execution state if available
    if 'execution_state' in st.session_state:
        exec_state = st.session_state.execution_state
        
        # Phase and Run ID
        col1, col2 = st.columns([1, 2])
        with col1:
            phase_str = str(exec_state.current_phase) if exec_state.current_phase else 'Starting...'
            st.write(f"**Phase:** {phase_str}")
        with col2:
            if exec_state.run_id:
                st.write(f"**Run ID:** `{exec_state.run_id}`")
        
        # Progress bar
        if exec_state.metrics:
            metrics = exec_state.metrics
            progress = metrics.progress_percentage / 100.0
            st.progress(min(progress, 1.0))
            
            # Status text
            status_text = render_progress_status(metrics)
            st.caption(status_text)
    
    # Execution metrics
    st.markdown("### 📊 Execution Metrics")
    if 'execution_engine' in st.session_state:
        engine = st.session_state.execution_engine
        metrics = engine.get_current_metrics()
        render_execution_metrics(metrics, config.get('max_cycles', 10))
    else:
        st.caption("Waiting for metrics...")
    
    # File operations monitor
    st.markdown("### 📁 File Operations")
    render_file_operations_monitor(allow_interactions=False)
    
    # Live file operations (recent)
    render_file_operations_live(int(time.time()))
    
    # Debug panel (collapsed)
    if 'execution_state' in st.session_state:
        render_debug_panel(st.session_state.execution_state)


def _execute_orchestration_sync(
    config: Dict[str, Any],
    loaded_concepts: Optional[Dict],
    loaded_inferences: Optional[Dict],
    loaded_inputs: Optional[Dict]
):
    """
    Execute the orchestration synchronously in a background thread.
    Updates session state variables that the main UI thread can poll.
    """
    logger.info("[SYNC_EXEC] _execute_orchestration_sync() called")
    
    # Create execution state for tracking - store in session state
    execution_state = ExecutionState()
    st.session_state.execution_state = execution_state
    
    try:
        # Create execution engine
        engine = OrchestrationExecutionEngine(execution_state)
        st.session_state.execution_engine = engine
        
        logger.info("[SYNC_EXEC] Starting orchestration execution...")
        
        # Run the orchestration synchronously (this will block the thread)
        import asyncio
        result = asyncio.run(engine.execute_full_orchestration(
            config, loaded_concepts, loaded_inferences, loaded_inputs
        ))
        
        logger.info("[SYNC_EXEC] Orchestration execution completed!")
        
        # Store result and status in session state (no UI updates from thread!)
        st.session_state.execution_result = result
        st.session_state.execution_completed = True
        st.session_state.is_executing = False
        
        logger.info("[SYNC_EXEC] Result stored in session state")
    
    except Exception as e:
        logger.error(f"[SYNC_EXEC] Execution failed: {e}", exc_info=True)
        st.session_state.is_executing = False
        st.session_state.execution_error = str(e)
        st.session_state.execution_exception = e


def _store_execution_results(
    orchestrator,
    final_concepts,
    duration: float,
    config: Dict[str, Any]
):
    """Store execution results in session state."""
    st.session_state.last_run = {
        'run_id': orchestrator.run_id,
        'timestamp': datetime.now().isoformat(),
        'duration': duration,
        'final_concepts': final_concepts,
        'llm_model': config['llm_model'],
        'max_cycles': config['max_cycles'],
        'base_dir': orchestrator.body.base_dir
    }
    
    # Add to execution log
    completed_concepts = sum(
        1 for fc in final_concepts
        if fc and fc.concept and fc.concept.reference
    )
    st.session_state.execution_log.insert(0, {
        'run_id': orchestrator.run_id,
        'timestamp': datetime.now().isoformat(),
        'status': 'success',
        'duration': duration,
        'completed': completed_concepts
    })


def _store_execution_results_from_result(
    result: Dict[str, Any],
    config: Dict[str, Any]
):
    """Store execution results from engine result dict."""
    st.session_state.last_run = {
        'run_id': result['run_id'],
        'timestamp': datetime.now().isoformat(),
        'duration': result['duration'],
        'final_concepts': result['final_concepts'],
        'llm_model': config['llm_model'],
        'max_cycles': config['max_cycles'],
        'base_dir': result['app_config'].get('base_dir', 'unknown')
    }
    
    # Add to execution log
    completed_concepts = sum(
        1 for fc in result['final_concepts']
        if fc and fc.concept and fc.concept.reference
    )
    st.session_state.execution_log.insert(0, {
        'run_id': result['run_id'],
        'timestamp': datetime.now().isoformat(),
        'status': 'success',
        'duration': result['duration'],
        'completed': completed_concepts
    })

