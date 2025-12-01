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
    
    # Show success message from previous resumption if flag is set
    if st.session_state.get('show_success_message', False):
        st.success("✅ Execution completed successfully!")
        st.balloons()
        st.session_state.show_success_message = False
        
        if st.session_state.last_run:
            display_execution_summary(st.session_state.last_run)
    
    # Handle user interaction if orchestrator is waiting for input
    if st.session_state.waiting_for_input and st.session_state.current_interaction:
        _render_interaction_form(config)
        st.stop()
    
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
    
    with col1:
        execute_btn = st.button("▶️ **Start Execution**", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🗑️ Clear Results", use_container_width=True):
            clear_results()
            st.success("Results cleared!")
            st.rerun()
    
    if execute_btn:
        asyncio.run(_execute_orchestration_async(
            config, loaded_concepts, loaded_inferences, loaded_inputs, file_ops_placeholder
        ))


async def _execute_orchestration_async(
    config: Dict[str, Any],
    loaded_concepts: Optional[Dict],
    loaded_inferences: Optional[Dict],
    loaded_inputs: Optional[Dict],
    file_ops_placeholder=None
):
    """
    Execute the orchestration asynchronously with real-time progress tracking.
    REFACTORED for better debugging and maintainability.
    """
    # Mark execution as started
    st.session_state.is_executing = True
    
    # Create execution state for tracking
    execution_state = ExecutionState()
    
    # Create progress containers
    status_container = st.empty()
    progress_container = st.empty()
    metrics_container = st.empty()
    live_ops_container = st.empty()
    debug_container = st.empty()
    
    try:
        # Create execution engine
        engine = OrchestrationExecutionEngine(execution_state)
        
        # Show initial status
        with status_container.container():
            st.info("🔧 Setting up orchestration...")
        
        # Start execution with live progress updates
        async def run_with_live_updates():
            """Run orchestration with periodic UI updates."""
            # Start the execution as a task
            task = asyncio.create_task(
                engine.execute_full_orchestration(
                    config, loaded_concepts, loaded_inferences, loaded_inputs
                )
            )
            
            update_counter = 0
            
            # Update UI while running
            while not task.done():
                update_counter += 1
                
                # Get current metrics
                metrics = engine.get_current_metrics()
                
                # Update status based on phase
                with status_container.container():
                    phase_messages = {
                        ExecutionPhase.SETUP: "🔧 Setting up orchestration...",
                        ExecutionPhase.INPUT_INJECTION: "📥 Injecting inputs...",
                        ExecutionPhase.VERIFICATION: "🔍 Verifying files...",
                        ExecutionPhase.ORCHESTRATOR_CREATION: "🚀 Creating orchestrator...",
                        ExecutionPhase.EXECUTION: f"⚙️ Running orchestration (Run ID: `{execution_state.run_id}`)",
                        ExecutionPhase.COMPLETION: "✅ Finalizing..."
                    }
                    message = phase_messages.get(execution_state.current_phase, "⏳ Processing...")
                    st.info(message)
                
                # Update progress bar
                if execution_state.current_phase == ExecutionPhase.EXECUTION:
                    with progress_container.container():
                        st.markdown("### ⏳ Execution Progress")
                        progress = metrics.progress_percentage / 100.0
                        st.progress(min(progress, 1.0))
                        status_text = render_progress_status(metrics)
                        st.text(status_text)
                
                # Update metrics
                if execution_state.current_phase == ExecutionPhase.EXECUTION:
                    with metrics_container.container():
                        render_execution_metrics(metrics, config['max_cycles'])
                
                # Update the file operations monitor at the top (if available)
                if file_ops_placeholder is not None:
                    file_ops_placeholder.empty()
                    with file_ops_placeholder.container():
                        render_file_operations_monitor(allow_interactions=False)
                
                # Update live file operations
                live_ops_container.empty()
                with live_ops_container.container():
                    render_file_operations_live(update_counter)
                
                # Update debug panel
                with debug_container:
                    render_debug_panel(execution_state)
                
                # Small delay to prevent UI thrashing
                await asyncio.sleep(0.5)
            
            # Get the result
            return await task
        
        # Execute with live updates
        result = await run_with_live_updates()
        
        # Clear progress displays
        status_container.empty()
        progress_container.empty()
        metrics_container.empty()
        live_ops_container.empty()
        debug_container.empty()
        
        # Don't restore monitor here - it will be rendered on next page rerun
        
        # Drain any remaining events from queue and get final count
        manager = st.session_state.file_operations_log_manager
        if hasattr(manager, 'drain_queue'):
            manager.drain_queue()
        file_ops_count = len(manager)
        
        # Mark execution as complete
        st.session_state.is_executing = False
        clear_interaction_state()
        
        # Success message
        st.success(
            f"✅ Execution completed in {result['duration']:.2f}s! "
            f"({file_ops_count} file operations logged)"
        )
        
        # Display results
        display_execution_summary(
            {'run_id': result['run_id'], 'final_concepts': result['final_concepts']},
            result['duration']
        )
        
        # Store results in session
        _store_execution_results_from_result(result, config)
        
        st.balloons()
        
        # Trigger rerun to restore interactive elements in file operations monitor
        time.sleep(0.5)  # Brief pause to let user see the success message
        st.rerun()
    
    except NeedsUserInteraction as interaction:
        # User interaction required - pause execution
        status_container.empty()
        progress_container.empty()
        metrics_container.empty()
        live_ops_container.empty()
        debug_container.empty()
        
        # Don't restore monitor here - it will be rendered on next page rerun
        
        # Save orchestrator state for resumption
        if engine.orchestrator:
            st.session_state.orchestrator_state = {
                'run_id': engine.orchestrator.run_id,
                'db_path': config['db_path'],
                'llm_model': config['llm_model'],
                'max_cycles': config['max_cycles'],
                'base_dir': engine.orchestrator.body.base_dir,
                'start_time': execution_state.metrics.start_time
            }
            
            # Save checkpoint
            if engine.orchestrator.checkpoint_manager:
                await asyncio.to_thread(
                    engine.orchestrator.checkpoint_manager.save_state,
                    engine.orchestrator.tracker.cycle_count,
                    engine.orchestrator,
                    inference_count=engine.orchestrator.tracker.total_executions
                )
                logger.info(f"Checkpoint saved at user interaction point")
        
        st.session_state.waiting_for_input = True
        st.session_state.current_interaction = {
            'id': interaction.interaction_id,
            'type': interaction.interaction_type,
            'prompt': interaction.prompt,
            'kwargs': interaction.kwargs
        }
        
        st.info("🛑 **Execution paused - User input required**")
        st.warning("⚠️ Please provide the requested information below and click Submit to continue execution.")
        st.session_state.is_executing = False
        st.rerun()
    
    except Exception as e:
        st.session_state.is_executing = False
        status_container.empty()
        progress_container.empty()
        metrics_container.empty()
        live_ops_container.empty()
        debug_container.empty()
        
        # Don't restore monitor here - it will be rendered on next page rerun
        
        st.error(f"❌ Execution failed: {str(e)}")
        st.exception(e)
        
        # Show execution state for debugging
        with st.expander("🐛 Debug Information", expanded=True):
            st.json(execution_state.get_status_summary())
        
        clear_interaction_state()
        
        # Log failure
        st.session_state.execution_log.insert(0, {
            'run_id': execution_state.run_id or 'unknown',
            'timestamp': datetime.now().isoformat(),
            'status': 'failed',
            'error': str(e)
        })


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

