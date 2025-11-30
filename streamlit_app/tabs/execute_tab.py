"""
Execute orchestration tab for NormCode Orchestrator Streamlit App.
"""

import streamlit as st
import json
import logging
from datetime import datetime

from infra import ConceptRepo, InferenceRepo
from tools import NeedsUserInteraction

from config import SCRIPT_DIR, PROJECT_ROOT, clear_interaction_state, clear_results
from file_utils import get_file_content, parse_json_file
from ui_components import (
    display_execution_summary,
    display_concept_preview,
    display_inference_preview,
    display_inputs_preview
)
from orchestration_runner import (
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
            
            from tools import StreamlitInputTool
            resume_body.user_input = StreamlitInputTool()
            
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
        _execute_orchestration(config, loaded_concepts, loaded_inferences, loaded_inputs)


def _execute_orchestration(config, loaded_concepts, loaded_inferences, loaded_inputs):
    """Execute the orchestration."""
    with st.spinner("🔄 Executing orchestration..."):
        try:
            # Load repository data
            concepts_json_data, inferences_json_data, inputs_json_data = _load_repository_data(
                config, loaded_concepts, loaded_inferences, loaded_inputs
            )
            
            # Create repositories
            concept_repo = ConceptRepo.from_json_list(concepts_json_data)
            
            # Inject inputs
            if inputs_json_data:
                count = inject_inputs_into_repo(concept_repo, inputs_json_data)
                st.info(f"✓ Injected {count} input concept(s)")
            
            inference_repo = InferenceRepo.from_json_list(inferences_json_data, concept_repo)
            
            # Determine base directory
            body_base_dir = _determine_base_directory(config)
            
            # Verify files if enabled
            verify_files_if_enabled(
                config['verify_files'],
                concept_repo,
                inference_repo,
                body_base_dir
            )
            
            # Create orchestrator
            st.info("Determining base directory...")
            orchestrator, app_config = create_orchestrator(
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
            
            # Progress tracking
            progress_placeholder = st.empty()
            progress_placeholder.text(f"⏳ Running orchestrator (Run ID: {orchestrator.run_id})...")
            
            # Execute
            start_time = datetime.now()
            
            try:
                final_concepts = orchestrator.run()
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                progress_placeholder.empty()
                
                # Success message
                st.success(f"✅ Execution completed in {duration:.2f}s!")
                clear_interaction_state()
            
            except NeedsUserInteraction as interaction:
                # User interaction required - pause execution
                progress_placeholder.empty()
                
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
                    orchestrator.checkpoint_manager.save_state(
                        orchestrator.tracker.cycle_count,
                        orchestrator,
                        inference_count=orchestrator.tracker.total_executions
                    )
                    logging.info(f"Checkpoint saved at user interaction point")
                
                st.info("🛑 **Execution paused - User input required**")
                st.warning("⚠️ Please provide the requested information below and click Submit to continue execution.")
                raise  # Re-raise to skip the rest
            
            # Display results
            display_execution_summary({'run_id': orchestrator.run_id, 'final_concepts': final_concepts}, duration)
            
            # Store results in session
            _store_execution_results(orchestrator, final_concepts, duration, config)
            
            st.balloons()
        
        except NeedsUserInteraction:
            # User interaction required - UI is already shown
            st.rerun()
        
        except Exception as e:
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

