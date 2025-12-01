"""
Execute orchestration tab for NormCode Orchestrator Streamlit App.
"""

import streamlit as st
import json
import logging
import subprocess
import sys
import asyncio
from pathlib import Path
from datetime import datetime

from infra import ConceptRepo, InferenceRepo
from tools import NeedsUserInteraction

from core.config import SCRIPT_DIR, PROJECT_ROOT, clear_interaction_state, clear_results, clear_file_operations_log
from core.file_utils import get_file_content, parse_json_file
from ui.ui_components import (
    display_execution_summary,
    display_concept_preview,
    display_inference_preview,
    display_inputs_preview
)
from orchestration.orchestration_runner import (
    create_orchestrator,
    inject_inputs_into_repo,
    verify_files_if_enabled
)


def render_execute_tab(config):
    """
    Render the Execute tab.
    
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
    
    # Check if we have files (either uploaded or loaded)
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
    
    # File operations monitor (always visible, even during execution)
    _render_file_operations_monitor()
    
    st.divider()
    
    # Execution controls
    _render_execution_controls(config, loaded_concepts, loaded_inferences, loaded_inputs)


def _render_interaction_form(config):
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
        else:  # Default to text_input
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


def _handle_interaction_submit(user_input, interaction, config):
    """Handle submission of user interaction."""
    # Provide the input to the tool
    st.session_state.pending_user_inputs[interaction['id']] = user_input
    
    # Resume execution
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
            
            # Re-init Body & Tools (done in load_checkpoint)
            from infra._agent._body import Body
            from infra import Orchestrator
            
            resume_body = Body(
                llm_name=orchestrator_data['llm_model'],
                base_dir=orchestrator_data['base_dir']
            )
            
            from tools import StreamlitInputTool, StreamlitFileSystemTool
            resume_body.user_input = StreamlitInputTool()
            resume_body.file_system = StreamlitFileSystemTool(base_dir=orchestrator_data['base_dir'])
            
            # Load Checkpoint
            orchestrator = Orchestrator.load_checkpoint(
                concept_repo=resume_concept_repo,
                inference_repo=resume_inference_repo,
                db_path=orchestrator_data['db_path'],
                run_id=orchestrator_data['run_id'],
                body=resume_body,
                mode="OVERWRITE"  # Trust the checkpoint implicitly
            )
            
            start_time = orchestrator_data['start_time']
            
            # Continue execution
            final_concepts = orchestrator.run()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Success!
            _store_execution_results(orchestrator, final_concepts, duration, config)
            
            # Clear waiting state
            clear_interaction_state()
            st.session_state.show_success_message = True
            st.rerun()
    
    except NeedsUserInteraction as next_interaction:
        # Another interaction is needed
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


def _render_file_previews(config, loaded_concepts, loaded_inferences, loaded_inputs):
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


def _render_execution_controls(config, loaded_concepts, loaded_inferences, loaded_inputs):
    """Render execution control buttons."""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        execute_btn = st.button("▶️ **Start Execution**", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🗑️ Clear Results", use_container_width=True):
            clear_results()
            st.success("Results cleared!")
            st.rerun()
    
    if execute_btn:
        # Run the async orchestration
        asyncio.run(_execute_orchestration_async(config, loaded_concepts, loaded_inferences, loaded_inputs))


async def _execute_orchestration_async(config, loaded_concepts, loaded_inferences, loaded_inputs):
    """Execute the orchestration asynchronously with real-time progress tracking."""
    # Mark execution as started so monitor stays expanded
    st.session_state.is_executing = True
    
    # Create progress containers
    status_container = st.empty()
    progress_container = st.empty()
    metrics_container = st.empty()
    live_ops_container = st.empty()
    
    try:
        # Phase 1: Setup
        with status_container.container():
            st.info("🔧 Setting up orchestration...")
        
        # Load repository data
        concepts_json_data, inferences_json_data, inputs_json_data = _load_repository_data(
            config, loaded_concepts, loaded_inferences, loaded_inputs
        )
        
        # Create repositories
        concept_repo = ConceptRepo.from_json_list(concepts_json_data)
        
        # Inject inputs
        if inputs_json_data:
            count = inject_inputs_into_repo(concept_repo, inputs_json_data)
            with status_container.container():
                st.success(f"✓ Injected {count} input concept(s)")
            await asyncio.sleep(0.1)  # Allow UI to update
        
        inference_repo = InferenceRepo.from_json_list(inferences_json_data, concept_repo)
        
        # Determine base directory
        body_base_dir = _determine_base_directory(config)
        
        # Phase 2: Verification
        if config['verify_files']:
            with status_container.container():
                st.info("🔍 Verifying repository files...")
            
            await verify_files_if_enabled(
                config['verify_files'],
                concept_repo,
                inference_repo,
                body_base_dir
            )
        
        # Phase 3: Create orchestrator
        with status_container.container():
            st.info("🚀 Creating orchestrator...")
        
        orchestrator, app_config = await create_orchestrator(
            concept_repo=concept_repo,
            inference_repo=inference_repo,
            llm_model=config['llm_model'],
            max_cycles=config['max_cycles'],
            base_dir=body_base_dir,
            db_path=config['db_path'],
            resume_option=config['resume_option'],
            run_id_to_resume=config['run_id_to_resume'],
            custom_run_id=config['custom_run_id'],
            new_run_id=config['new_run_id'],
            reconciliation_mode=config['reconciliation_mode'],
            concepts_file=config['concepts_file'],
            loaded_concepts=loaded_concepts,
            inferences_file=config['inferences_file'],
            loaded_inferences=loaded_inferences,
            inputs_file=config['inputs_file'],
            loaded_inputs=loaded_inputs,
            base_dir_option=config['base_dir_option'],
            verify_files=config['verify_files']
        )
        
        # Phase 4: Execute with live progress tracking
        with status_container.container():
            st.success(f"✅ Orchestrator ready (Run ID: `{orchestrator.run_id}`)")
        
        with progress_container.container():
            st.markdown("### ⏳ Execution Progress")
            progress_bar = st.progress(0.0)
            status_text = st.empty()
        
        start_time = datetime.now()
        
        try:
            # Start async execution with progress updates
            async def run_with_progress():
                """Run orchestrator with periodic progress updates."""
                # Start the orchestration as an async task
                task = asyncio.create_task(orchestrator.run_async())
                
                # Track initial state
                last_cycle = 0
                
                # Update progress while running
                while not task.done():
                    # Calculate completion status based on blackboard
                    if orchestrator.waitlist and orchestrator.blackboard:
                        total_items = len(orchestrator.waitlist.items)
                        completed_count = 0
                        pending_count = 0
                        in_progress_count = 0
                        
                        for item in orchestrator.waitlist.items:
                            flow_index = item.inference_entry.flow_info['flow_index']
                            status = orchestrator.blackboard.get_item_status(flow_index)
                            if status == 'completed':
                                completed_count += 1
                            elif status == 'in_progress':
                                in_progress_count += 1
                            elif status == 'pending':
                                pending_count += 1
                        
                        # Calculate progress based on completed items only
                        progress = completed_count / total_items if total_items > 0 else 0
                        
                        # Update progress bar and status
                        progress_bar.progress(min(progress, 1.0))
                        
                        # Build status text with detailed breakdown
                        status_parts = []
                        if completed_count > 0:
                            status_parts.append(f"✅ {completed_count} completed")
                        if in_progress_count > 0:
                            status_parts.append(f"⏳ {in_progress_count} in progress")
                        if pending_count > 0:
                            status_parts.append(f"⏸️ {pending_count} pending")
                        
                        status_line = f"Items: {' | '.join(status_parts)}" if status_parts else "Starting..."
                        
                        # Add retry info if applicable
                        if orchestrator.tracker.retry_count > 0:
                            status_line += f" | 🔄 {orchestrator.tracker.retry_count} retries"
                        
                        status_text.text(status_line)
                    
                    # Update metrics
                    with metrics_container.container():
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            cycle_delta = orchestrator.tracker.cycle_count - last_cycle
                            st.metric(
                                "Cycle", 
                                f"{orchestrator.tracker.cycle_count}/{config['max_cycles']}",
                                delta=f"+{cycle_delta}" if cycle_delta > 0 else None
                            )
                            last_cycle = orchestrator.tracker.cycle_count
                        
                        with col2:
                            st.metric("Total Executions", orchestrator.tracker.total_executions)
                        
                        with col3:
                            success_rate = (orchestrator.tracker.successful_executions / orchestrator.tracker.total_executions * 100) if orchestrator.tracker.total_executions > 0 else 0
                            st.metric("Completed", orchestrator.tracker.successful_executions, delta=f"{success_rate:.0f}%")
                        
                        with col4:
                            if orchestrator.tracker.failed_executions > 0:
                                st.metric("Failed", orchestrator.tracker.failed_executions, delta="⚠️")
                            else:
                                st.metric("Retries", orchestrator.tracker.retry_count)
                        
                        with col5:
                            elapsed = (datetime.now() - start_time).total_seconds()
                            st.metric("Time", f"{elapsed:.1f}s")
                    
                    # Update live file operations
                    with live_ops_container.container():
                        st.markdown("### 📁 Recent File Operations")
                        if st.session_state.file_operations_log:
                            recent = list(reversed(st.session_state.file_operations_log[-5:]))
                            for op in recent:
                                try:
                                    ts = datetime.fromisoformat(op['timestamp']).strftime('%H:%M:%S')
                                except:
                                    ts = op['timestamp']
                                
                                icon = "📖" if op['operation'] in ['READ', 'MEMORIZED_READ'] else "💾" if op['operation'] in ['SAVE', 'MEMORIZED_SAVE'] else "🔍"
                                status_icon = "✅" if op['status'] == 'SUCCESS' else "❌"
                                
                                file_path_obj = Path(op['location'])
                                loc = file_path_obj.name if len(op['location']) > 40 else op['location']
                                st.text(f"{ts} {icon} {op['operation']:15} {status_icon} {loc}")
                        else:
                            st.text("No operations yet...")
                    
                    # Small delay to prevent UI thrashing
                    await asyncio.sleep(0.5)
                
                # Get the result
                return await task
            
            final_concepts = await run_with_progress()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Clear progress displays
            status_container.empty()
            progress_container.empty()
            metrics_container.empty()
            live_ops_container.empty()
            
            # Success message
            file_ops_count = len(st.session_state.file_operations_log)
            st.success(f"✅ Execution completed in {duration:.2f}s! ({file_ops_count} file operations logged)")
            st.session_state.is_executing = False
            clear_interaction_state()
            
            # Display results
            display_execution_summary({'run_id': orchestrator.run_id, 'final_concepts': final_concepts}, duration)
            
            # Store results in session
            _store_execution_results(orchestrator, final_concepts, duration, config)
            
            st.balloons()
        
        except NeedsUserInteraction as interaction:
            # User interaction required - pause execution
            status_container.empty()
            progress_container.empty()
            metrics_container.empty()
            live_ops_container.empty()
            
            # Save orchestrator state for resumption
            st.session_state.orchestrator_state = {
                'run_id': orchestrator.run_id,
                'db_path': config['db_path'],
                'llm_model': config['llm_model'],
                'max_cycles': config['max_cycles'],
                'base_dir': body_base_dir,
                'start_time': start_time
            }
            st.session_state.waiting_for_input = True
            st.session_state.current_interaction = {
                'id': interaction.interaction_id,
                'type': interaction.interaction_type,
                'prompt': interaction.prompt,
                'kwargs': interaction.kwargs
            }
            
            # Save a checkpoint
            if orchestrator.checkpoint_manager:
                await asyncio.to_thread(
                    orchestrator.checkpoint_manager.save_state,
                    orchestrator.tracker.cycle_count,
                    orchestrator,
                    inference_count=orchestrator.tracker.total_executions
                )
                logging.info(f"Checkpoint saved at user interaction point")
            
            st.info("🛑 **Execution paused - User input required**")
            st.warning("⚠️ Please provide the requested information below and click Submit to continue execution.")
            raise  # Re-raise to skip the rest
    
    except NeedsUserInteraction:
        # User interaction required - keep monitor visible but mark not executing for normal display
        st.session_state.is_executing = False
        st.rerun()
    
    except Exception as e:
        st.session_state.is_executing = False
        status_container.empty()
        progress_container.empty()
        metrics_container.empty()
        live_ops_container.empty()
        
        st.error(f"❌ Execution failed: {str(e)}")
        st.exception(e)
        clear_interaction_state()
        
        # Log failure
        st.session_state.execution_log.insert(0, {
            'run_id': 'unknown',
            'timestamp': datetime.now().isoformat(),
            'status': 'failed',
            'error': str(e)
        })


def _load_repository_data(config, loaded_concepts, loaded_inferences, loaded_inputs):
    """Load repository data from files."""
    # Get concepts data
    if config['concepts_file']:
        concepts_file = config['concepts_file']
        concepts_file.seek(0)
        content = concepts_file.read().decode('utf-8')
        concepts_json_data = json.loads(content)
        # Populate session state for resumption
        st.session_state.loaded_repo_files['concepts'] = {
            'name': concepts_file.name,
            'content': content,
            'path': None
        }
    else:
        concepts_json_data = json.loads(loaded_concepts['content'])
    
    # Get inferences data
    if config['inferences_file']:
        inferences_file = config['inferences_file']
        inferences_file.seek(0)
        content = inferences_file.read().decode('utf-8')
        inferences_json_data = json.loads(content)
        # Populate session state for resumption
        st.session_state.loaded_repo_files['inferences'] = {
            'name': inferences_file.name,
            'content': content,
            'path': None
        }
    else:
        inferences_json_data = json.loads(loaded_inferences['content'])
    
    # Get inputs data if available
    inputs_json_data = None
    if config['inputs_file']:
        inputs_file = config['inputs_file']
        inputs_file.seek(0)
        content = inputs_file.read().decode('utf-8')
        inputs_json_data = json.loads(content)
        # Populate session state for resumption
        st.session_state.loaded_repo_files['inputs'] = {
            'name': inputs_file.name,
            'content': content,
            'path': None
        }
    elif loaded_inputs:
        inputs_json_data = json.loads(loaded_inputs['content'])
    
    return concepts_json_data, inferences_json_data, inputs_json_data


def _determine_base_directory(config):
    """Determine the base directory based on configuration."""
    if config['base_dir_option'] == "Project Root":
        return str(PROJECT_ROOT)
    elif config['base_dir_option'] == "Custom Path" and config['custom_base_dir']:
        return config['custom_base_dir']
    else:  # "App Directory (default)"
        return str(SCRIPT_DIR)


def _store_execution_results(orchestrator, final_concepts, duration, config):
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


def _render_file_operations_monitor():
    """Render the file operations monitor."""
    # Check if execution is in progress
    is_executing = st.session_state.get('is_executing', False)
    
    # Expand automatically during execution or if there are operations
    has_operations = len(st.session_state.file_operations_log) > 0
    
    # Show operation count in header
    op_count = len(st.session_state.file_operations_log)
    monitor_title = f"📁 File Operations Monitor ({op_count} operations)" if op_count > 0 else "📁 File Operations Monitor"
    
    with st.expander(monitor_title, expanded=(is_executing or has_operations)):
        if not st.session_state.file_operations_log:
            st.info("No file operations yet. Operations will appear here during execution.")
        else:
            # Calculate statistics
            total_ops = len(st.session_state.file_operations_log)
            success_count = sum(1 for op in st.session_state.file_operations_log if op['status'] == 'SUCCESS')
            error_count = total_ops - success_count
            
            # Count by operation type
            read_ops = sum(1 for op in st.session_state.file_operations_log if op['operation'] in ['READ', 'MEMORIZED_READ'])
            write_ops = sum(1 for op in st.session_state.file_operations_log if op['operation'] in ['SAVE', 'MEMORIZED_SAVE'])
            check_ops = sum(1 for op in st.session_state.file_operations_log if op['operation'] == 'EXISTS')
            
            # Add header and clear button
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Total Operations:** {total_ops} | ✅ Success: {success_count} | ❌ Errors: {error_count}")
                st.markdown(f"📖 Reads: {read_ops} | 💾 Writes: {write_ops} | 🔍 Checks: {check_ops}")
            
            with col2:
                if st.button("🗑️ Clear Log", key="clear_file_ops", use_container_width=True):
                    clear_file_operations_log()
                    st.rerun()
            
            st.divider()
            
            # Add filter options
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
            ops_to_display = st.session_state.file_operations_log
            if filter_type:
                ops_to_display = [op for op in ops_to_display if op['operation'] in filter_type]
            if filter_status:
                ops_to_display = [op for op in ops_to_display if op['status'] in filter_status]
            
            st.divider()
            
            # Display operations in reverse chronological order (most recent first)
            display_limit = 50  # Show last 50 operations
            ops_to_display = list(reversed(ops_to_display[-display_limit:]))
            
            for i, op in enumerate(ops_to_display):
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
                
                # Format location (show relative path if possible, truncate if too long)
                location = op['location']
                full_path = location  # Keep full path for button
                if len(location) > 55:
                    # Show filename and parent dir
                    path_obj = Path(location)
                    location = f".../{path_obj.parent.name}/{path_obj.name}"
                
                # Display as columns for better layout
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
                    # Add button to open directory
                    if st.button("📂", key=f"open_dir_{i}_{op['timestamp']}", help="Open containing folder"):
                        _open_file_location(full_path)
                
                # Add separator between operations (except last one)
                if i < len(ops_to_display) - 1:
                    st.markdown("")  # Small spacing
            
            filtered_total = len(ops_to_display)
            if filter_type or filter_status:
                st.caption(f"Showing {min(filtered_total, display_limit)} filtered operations (out of {total_ops} total)")
            elif total_ops > display_limit:
                st.caption(f"Showing most recent {display_limit} of {total_ops} operations")


def _open_file_location(file_path: str):
    """Open the directory containing the specified file in the system file explorer."""
    try:
        path = Path(file_path)
        
        # Get the directory containing the file
        if path.is_file():
            directory = path.parent
        elif path.is_dir():
            directory = path
        else:
            # Path doesn't exist, try to open parent directory
            directory = path.parent
        
        # Make it absolute
        directory = directory.resolve()
        
        # Open in file explorer based on OS
        if sys.platform == 'win32':
            # Windows - open explorer and select the file if it exists
            if path.exists() and path.is_file():
                subprocess.run(['explorer', '/select,', str(path)], check=False)
            else:
                subprocess.run(['explorer', str(directory)], check=False)
        elif sys.platform == 'darwin':
            # macOS
            if path.exists() and path.is_file():
                subprocess.run(['open', '-R', str(path)], check=False)
            else:
                subprocess.run(['open', str(directory)], check=False)
        else:
            # Linux and other Unix-like systems
            subprocess.run(['xdg-open', str(directory)], check=False)
        
        st.toast(f"📂 Opened folder: {directory.name}", icon="✅")
    except Exception as e:
        st.error(f"Failed to open location: {e}")
        # Show full path in error so user can navigate manually
        st.code(file_path)

