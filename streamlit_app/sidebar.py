"""
Sidebar configuration UI for NormCode Orchestrator Streamlit App.
"""

import streamlit as st
import os
from pathlib import Path

from infra._orchest._db import OrchestratorDB
from config import (
    SCRIPT_DIR, PROJECT_ROOT, DEFAULT_DB_PATH, LLM_MODELS,
    EXECUTION_MODES, RECONCILIATION_MODES, DEFAULT_MAX_CYCLES,
    clear_loaded_config
)
from file_utils import load_file_from_path


def render_sidebar():
    """
    Render the sidebar with configuration options.
    
    Returns:
        Dictionary with all configuration values
    """
    with st.sidebar:
        st.title("⚙️ Configuration")
        
        # Load Configuration from Previous Runs
        _render_config_loader()
        
        st.divider()
        
        # Repository Files
        st.subheader("📁 Repository Files")
        concepts_file, inferences_file, inputs_file = _render_file_uploaders()
        
        st.divider()
        
        # Runtime Settings
        st.subheader("🔧 Runtime Settings")
        llm_model, max_cycles, base_dir_option, custom_base_dir = _render_runtime_settings()
        
        st.divider()
        
        # Checkpoint Settings
        st.subheader("💾 Checkpoint Settings")
        (db_path, resume_option, run_id_to_resume, custom_run_id, 
         new_run_id, reconciliation_mode, verify_files) = _render_checkpoint_settings()
    
    return {
        'concepts_file': concepts_file,
        'inferences_file': inferences_file,
        'inputs_file': inputs_file,
        'llm_model': llm_model,
        'max_cycles': max_cycles,
        'base_dir_option': base_dir_option,
        'custom_base_dir': custom_base_dir,
        'db_path': db_path,
        'resume_option': resume_option,
        'run_id_to_resume': run_id_to_resume,
        'custom_run_id': custom_run_id,
        'new_run_id': new_run_id,
        'reconciliation_mode': reconciliation_mode,
        'verify_files': verify_files
    }


def _render_config_loader():
    """Render the configuration loader section."""
    st.subheader("📋 Load Previous Config")
    
    # Find database for config loading
    db_path_for_config = DEFAULT_DB_PATH if os.path.exists(DEFAULT_DB_PATH) else None
    
    if not db_path_for_config:
        abs_path = str(SCRIPT_DIR / DEFAULT_DB_PATH)
        if os.path.exists(abs_path):
            db_path_for_config = abs_path
    
    if not db_path_for_config:
        st.info(f"Database not found. Run an orchestration to create it.")
        return
    
    try:
        db_for_config = OrchestratorDB(db_path_for_config)
        runs_with_config = db_for_config.list_runs(include_metadata=True)
        
        if not runs_with_config:
            st.info("No previous runs with configurations found")
            return
        
        # Create options for selectbox
        config_options = ["-- Select a previous run --"] + [
            f"{run['run_id'][:12]}... ({run['first_execution'][:16]})"
            for run in runs_with_config
        ]
        
        selected_config_idx = st.selectbox(
            "Load settings from:",
            range(len(config_options)),
            format_func=lambda i: config_options[i],
            key="config_selector",
            help="Load configuration from a previous run to quickly replicate settings"
        )
        
        if selected_config_idx > 0:
            _handle_config_selection(runs_with_config[selected_config_idx - 1])
        
        # Show loaded config indicator
        if st.session_state.config_loaded_from_run:
            _show_loaded_config_indicator()
    
    except Exception as e:
        st.warning(f"Could not load run configurations: {e}")


def _handle_config_selection(selected_run):
    """Handle selection of a previous run configuration."""
    run_config = selected_run.get('config', {})
    has_repo_files = any([
        run_config.get('concepts_file_path'),
        run_config.get('inferences_file_path'),
        run_config.get('inputs_file_path')
    ])
    
    # Option to load repository files too
    load_repo_files = False
    if has_repo_files:
        load_repo_files = st.checkbox(
            "📁 Also load repository files",
            value=True,
            help="Load the exact repository files used in this run",
            key=f"load_files_{selected_run['run_id']}"
        )
        
        # Show which files are available
        available_files = []
        for file_type in ['concepts', 'inferences', 'inputs']:
            if run_config.get(f'{file_type}_file_path'):
                available_files.append(f"{file_type}.json")
        
        if available_files:
            st.caption(f"Available: {', '.join(available_files)}")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔄 Load Config", use_container_width=True):
            st.session_state.loaded_config = run_config
            st.session_state.config_loaded_from_run = selected_run['run_id']
            
            # Load repository files if requested
            if load_repo_files:
                for file_type in ['concepts', 'inferences', 'inputs']:
                    file_path = run_config.get(f'{file_type}_file_path')
                    if file_path:
                        file_contents = load_file_from_path(file_path)
                        if file_contents:
                            st.session_state.loaded_repo_files[file_type] = {
                                'name': os.path.basename(file_path),
                                'content': file_contents,
                                'path': file_path
                            }
            
            success_msg = f"✓ Loaded config from {selected_run['run_id'][:8]}..."
            if load_repo_files and has_repo_files:
                success_msg += " (with repository files)"
            st.success(success_msg)
            st.rerun()
    
    with col2:
        if st.button("👁️ Preview", use_container_width=True):
            if run_config:
                with st.expander("Configuration Details", expanded=True):
                    st.json(run_config)
            else:
                st.info("No configuration metadata saved for this run")


def _show_loaded_config_indicator():
    """Show indicator for loaded configuration."""
    loaded_files = [
        k for k, v in st.session_state.loaded_repo_files.items() 
        if v is not None
    ]
    
    if loaded_files:
        st.success(
            f"📌 Config + Files loaded from: "
            f"`{st.session_state.config_loaded_from_run[:12]}...`"
        )
        st.caption(f"Loaded files: {', '.join(loaded_files)}")
    else:
        st.success(
            f"📌 Config loaded from: "
            f"`{st.session_state.config_loaded_from_run[:12]}...`"
        )
    
    if st.button("🗑️ Clear Loaded Config", use_container_width=True):
        clear_loaded_config()
        st.rerun()


def _render_file_uploaders():
    """Render file uploader widgets."""
    loaded_concepts = st.session_state.loaded_repo_files.get('concepts')
    loaded_inferences = st.session_state.loaded_repo_files.get('inferences')
    loaded_inputs = st.session_state.loaded_repo_files.get('inputs')
    
    # Concepts file
    if loaded_concepts:
        st.info(f"📄 Using loaded: `{loaded_concepts['name']}`")
        if st.button("🔄 Upload Different Concepts File", key='change_concepts'):
            st.session_state.loaded_repo_files['concepts'] = None
            st.rerun()
        concepts_file = None
    else:
        concepts_file = st.file_uploader("Concepts JSON", type=['json'], key='concepts')
    
    # Inferences file
    if loaded_inferences:
        st.info(f"📄 Using loaded: `{loaded_inferences['name']}`")
        if st.button("🔄 Upload Different Inferences File", key='change_inferences'):
            st.session_state.loaded_repo_files['inferences'] = None
            st.rerun()
        inferences_file = None
    else:
        inferences_file = st.file_uploader("Inferences JSON", type=['json'], key='inferences')
    
    # Inputs file
    if loaded_inputs:
        st.info(f"📄 Using loaded: `{loaded_inputs['name']}`")
        if st.button("🔄 Upload Different Inputs File", key='change_inputs'):
            st.session_state.loaded_repo_files['inputs'] = None
            st.rerun()
        inputs_file = None
    else:
        inputs_file = st.file_uploader(
            "Inputs JSON",
            type=['json'],
            key='inputs',
            help="Provides data for ground concepts (e.g., {number pair} for addition). See sample_inputs.json for format."
        )
    
    # Show tip if no inputs
    if not inputs_file and not loaded_inputs:
        st.info(
            "💡 **Tip**: Most repositories need an inputs.json file to provide "
            "ground concept data. Check `sample_inputs.json` for an example."
        )
    
    return concepts_file, inferences_file, inputs_file


def _render_runtime_settings():
    """Render runtime settings widgets."""
    loaded_config = st.session_state.loaded_config or {}
    
    # LLM Model selection
    default_llm = loaded_config.get("llm_model", LLM_MODELS[0])
    try:
        default_llm_idx = LLM_MODELS.index(default_llm) if default_llm in LLM_MODELS else 0
    except ValueError:
        default_llm_idx = 0
    
    llm_model = st.selectbox(
        "LLM Model",
        LLM_MODELS,
        index=default_llm_idx,
        help="Loaded from previous run" if loaded_config.get("llm_model") else None
    )
    
    # Max Cycles
    default_max_cycles = loaded_config.get("max_cycles", DEFAULT_MAX_CYCLES)
    max_cycles = st.number_input(
        "Max Cycles",
        min_value=1,
        max_value=1000,
        value=int(default_max_cycles),
        step=10,
        help="Loaded from previous run" if loaded_config.get("max_cycles") else None
    )
    
    # Base directory
    loaded_base_dir = loaded_config.get("base_dir")
    
    # Determine default base_dir_option from loaded config
    if loaded_base_dir:
        if loaded_base_dir == str(SCRIPT_DIR):
            default_base_dir_idx = 0
        elif loaded_base_dir == str(PROJECT_ROOT):
            default_base_dir_idx = 1
        else:
            default_base_dir_idx = 2
    else:
        default_base_dir_idx = 0
    
    base_dir_option = st.radio(
        "Base Directory",
        ["App Directory (default)", "Project Root", "Custom Path"],
        index=default_base_dir_idx,
        help=(
            "Where generated scripts and prompts will be stored. "
            + ("Loaded from previous run" if loaded_base_dir else "")
        )
    )
    
    if base_dir_option == "Custom Path":
        default_custom = (
            loaded_base_dir if loaded_base_dir and 
            loaded_base_dir not in [str(SCRIPT_DIR), str(PROJECT_ROOT)]
            else str(SCRIPT_DIR)
        )
        custom_base_dir = st.text_input(
            "Custom Base Directory",
            value=default_custom,
            help="Absolute or relative path for LLM file operations"
        )
    else:
        custom_base_dir = None
    
    return llm_model, max_cycles, base_dir_option, custom_base_dir


def _render_checkpoint_settings():
    """Render checkpoint settings widgets."""
    loaded_config = st.session_state.loaded_config or {}
    
    # Database path
    default_db_path = loaded_config.get("db_path", DEFAULT_DB_PATH)
    
    db_path_help = (
        "Loaded from previous run. Supports both absolute and relative paths."
        if loaded_config.get("db_path")
        else "Path to SQLite database file. Can be absolute or relative."
    )
    
    db_path = st.text_input(
        "Database Path",
        value=default_db_path,
        help=db_path_help
    )
    
    # Execution mode
    resume_option = st.radio(
        "Execution Mode",
        EXECUTION_MODES,
        help=(
            "Fresh Run: Start new execution\n"
            "Resume: Continue existing run (configure reconciliation in Advanced Options)\n"
            "Fork: Load state from one run, execute different repository with fresh history"
        )
    )
    
    # Mode-specific options
    if resume_option == "Fresh Run":
        default_custom_run_id = loaded_config.get("custom_run_id", "")
        custom_run_id = st.text_input(
            "Run Name/ID (optional)",
            value=default_custom_run_id,
            placeholder="Leave empty to auto-generate",
            help=(
                "Specify a custom name/ID for this run. Leave empty to auto-generate a UUID. "
                "This helps identify and organize your runs."
                + (" (Loaded from previous run)" if default_custom_run_id else "")
            )
        )
        run_id_to_resume = None
        new_run_id = None
        reconciliation_mode = None
    
    else:
        # Load from previous config
        if resume_option == "Fork from Checkpoint":
            default_run_id = loaded_config.get("forked_from_run_id", "")
        else:
            default_run_id = loaded_config.get("resumed_from_run_id", "")
        
        run_id_to_resume = st.text_input(
            "Run ID to Resume",
            value=default_run_id,
            placeholder="Leave empty for latest",
            help="The run ID to load state from" + (" (Loaded from previous run)" if default_run_id else "")
        )
        custom_run_id = None
        
        # Forking specific
        if resume_option == "Fork from Checkpoint":
            st.info("💡 **Forking**: Load state from one run, start a new run with different repository")
            default_new_run_id = loaded_config.get("new_run_id", "")
            new_run_id = st.text_input(
                "New Run ID (optional)",
                value=default_new_run_id,
                placeholder="Leave empty to auto-generate",
                help=(
                    "Specify a new run ID for the forked run. Leave empty to auto-generate."
                    + (" (Loaded from previous run)" if default_new_run_id else "")
                )
            )
        else:
            new_run_id = None
        
        # Reconciliation mode
        reconciliation_mode = _render_reconciliation_mode(resume_option)
    
    # Advanced options (includes reconciliation mode if applicable)
    if resume_option != "Fresh Run":
        with st.expander("🔧 Advanced Options"):
            verify_files = st.checkbox(
                "Verify repository file references",
                value=True,
                help="Check that all files referenced in concepts/inferences exist in base_dir before execution"
            )
            
            st.write("**Checkpoint Reconciliation Mode:**")
            
            # Set smart default based on execution mode
            if resume_option == "Fork from Checkpoint":
                default_reconciliation = "OVERWRITE"
                help_text = (
                    "OVERWRITE (default for forking): Trusts checkpoint data completely, "
                    "keeps all values even if logic changed. PATCH: Discards values with changed logic. "
                    "FILL_GAPS: Only fills empty concepts."
                )
            else:
                default_reconciliation = "PATCH"
                help_text = (
                    "PATCH (default for resuming): Smart merge - discards stale state, keeps valid data. "
                    "OVERWRITE: Trusts checkpoint completely. FILL_GAPS: Only fills empty concepts."
                )
            
            default_index = RECONCILIATION_MODES.index(default_reconciliation)
            
            reconciliation_mode = st.radio(
                "How to apply checkpoint state:",
                RECONCILIATION_MODES,
                index=default_index,
                help=help_text,
                key="reconciliation_mode"
            )
    else:
        with st.expander("🔧 Advanced Options"):
            verify_files = st.checkbox(
                "Verify repository file references",
                value=True,
                help="Check that all files referenced in concepts/inferences exist in base_dir before execution"
            )
    
    return (db_path, resume_option, run_id_to_resume, custom_run_id,
            new_run_id, reconciliation_mode, verify_files)

