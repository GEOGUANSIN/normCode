"""
NormCode Orchestrator - Streamlit App

A minimal web interface for running the NormCode orchestration engine.
Upload repository JSON files, configure execution parameters, and view results.
"""

import streamlit as st
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path (app is in streamlit_app/, need to go up one level)
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Create directory for storing uploaded repository files
REPO_FILES_DIR = script_dir / "saved_repositories"
REPO_FILES_DIR.mkdir(exist_ok=True)

from infra import ConceptRepo, InferenceRepo, Orchestrator
from infra._orchest._db import OrchestratorDB
from infra._agent._body import Body
from typing import List, Tuple, Dict, Any

# Import custom Streamlit tools
from tools import StreamlitInputTool, NeedsUserInteraction

# Configure page
st.set_page_config(
    page_title="NormCode Orchestrator",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Functions ---

def save_uploaded_file(uploaded_file, run_id: str, file_type: str) -> str:
    """
    Save an uploaded file to disk for future reloading.
    
    Args:
        uploaded_file: Streamlit UploadedFile object
        run_id: Current run ID
        file_type: 'concepts', 'inferences', or 'inputs'
    
    Returns:
        Path to saved file
    """
    if uploaded_file is None:
        return None
    
    # Create directory for this run
    run_dir = REPO_FILES_DIR / run_id
    run_dir.mkdir(exist_ok=True)
    
    # Save file with standard name
    file_path = run_dir / f"{file_type}.json"
    
    # Write file contents
    uploaded_file.seek(0)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.read())
    
    uploaded_file.seek(0)  # Reset for later use
    
    return str(file_path)

def load_file_from_path(file_path: str):
    """
    Load a JSON file from disk and return its contents.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        File contents as string or None if file doesn't exist
    """
    if not file_path or not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logging.error(f"Failed to load file from {file_path}: {e}")
        return None

def verify_repository_files(concept_repo: ConceptRepo, inference_repo: InferenceRepo, base_dir: str) -> Tuple[bool, List[str], List[str]]:
    """
    Verify that all script and prompt files referenced in the repository exist in base_dir.
    
    Returns:
        Tuple of (all_valid, warnings, errors)
        - all_valid: True if all files exist or no files are referenced
        - warnings: List of warning messages
        - errors: List of error messages (missing files)
    """
    warnings = []
    errors = []
    base_path = Path(base_dir)
    
    # Check for prompt files
    # Prompts are typically named in inference sequences (e.g., "imperative_python" might use prompts)
    # We'll look for common prompt patterns
    potential_prompt_dirs = [
        base_path / "prompts",
        base_path / "_models" / "prompts",
        base_path / "generated_prompts"
    ]
    
    prompt_dir_exists = any(d.exists() and d.is_dir() for d in potential_prompt_dirs)
    
    # Check inference sequences for custom file references
    sequences_requiring_files = []
    for inference in inference_repo.get_all_inferences():
        seq = inference.inference_sequence
        
        # Check for sequences that typically generate or read files
        if "python" in seq.lower() or "script" in seq.lower():
            # Check for generated_scripts directory
            script_dirs = [
                base_path / "generated_scripts",
                base_path / "scripts"
            ]
            
            script_dir_exists = any(d.exists() and d.is_dir() for d in script_dirs)
            
            if not script_dir_exists:
                # This is just a warning - directories are created on demand
                warnings.append(
                    f"Inference '{inference.concept_to_infer.concept_name}' uses sequence '{seq}' "
                    f"which may generate scripts. Consider creating 'generated_scripts/' in base_dir."
                )
    
    # Check concepts for explicit file references in context or reference_data
    for concept in concept_repo.get_all_concepts():
        # Check if reference_data contains file paths
        if concept.reference_data:
            ref_data_str = str(concept.reference_data)
            
            # Look for NormCode file wrappers: %{type}(path/to/file.ext)
            # Examples: %{script_location}(generated_scripts/op_sum.py)
            #           %{prompt_location}(generated_prompts/op_sum_prompt.txt)
            import re
            
            # Pattern to match NormCode file references
            normcode_file_pattern = r'%\{[\w_]+\}\(([\w/\\.-]+)\)'
            normcode_matches = re.findall(normcode_file_pattern, ref_data_str)
            
            for file_path_str in normcode_matches:
                # This is a file reference wrapped in NormCode syntax
                file_path = base_path / file_path_str
                if not file_path.exists():
                    errors.append(
                        f"Concept '{concept.concept_name}' references file '{file_path_str}' "
                        f"which was not found in base_dir: {base_dir}"
                    )
            
            # Also check for plain file paths (less common, but possible)
            # Only match if it looks like a proper file path (has directory separator)
            # Use non-capturing group for extension to get full path
            plain_file_pattern = r'(?:[\w/\\]+/)[\w/\\.-]+\.(?:txt|py|json|prompt)'
            plain_matches = re.findall(plain_file_pattern, ref_data_str)
            
            for file_path_str in plain_matches:
                # Skip if already found in NormCode pattern
                if file_path_str not in normcode_matches:
                    file_path = base_path / file_path_str
                    if not file_path.exists():
                        errors.append(
                            f"Concept '{concept.concept_name}' references file '{file_path_str}' "
                            f"which was not found in base_dir: {base_dir}"
                        )
    
    # Check for ground concepts that need data (only semantical concepts, not syntactical operators)
    missing_ground_concepts = []
    for concept in concept_repo.get_all_concepts():
        # Only check ground concepts that are:
        # 1. Not invariant (invariants have embedded logic)
        # 2. Semantical (not syntactical operators like $., @if, etc.)
        if concept.is_ground_concept and not concept.is_invariant:
            # Skip syntactical concepts (they're operators, not data containers)
            if concept.concept and concept.concept.is_syntactical():
                continue
            
            # Check if this semantical ground concept has data
            has_data = False
            if concept.reference_data is not None:
                has_data = True
            elif concept.concept and concept.concept.reference:
                has_data = True
            
            if not has_data:
                missing_ground_concepts.append(concept.concept_name)
    
    if missing_ground_concepts:
        errors.append(
            f"Missing required input data for ground concepts: {', '.join(missing_ground_concepts)}. "
            f"Please provide an inputs.json file with these concepts."
        )
    
    # Summary
    all_valid = len(errors) == 0
    
    if all_valid and len(warnings) == 0:
        warnings.append(f"✓ Base directory structure looks good: {base_dir}")
        warnings.append(f"✓ All required ground concepts have data")
    
    return all_valid, warnings, errors

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box { background-color: #d4edda; border: 1px solid #c3e6cb; }
    .error-box { background-color: #f8d7da; border: 1px solid #f5c6cb; }
    .info-box { background-color: #d1ecf1; border: 1px solid #bee5eb; }
    
    /* Compact log display */
    .stCodeBlock {
        font-size: 0.7rem !important;
        line-height: 1.25 !important;
    }
    .stCodeBlock code {
        font-size: 0.7rem !important;
        line-height: 1.25 !important;
        padding: 0.5rem !important;
    }
    .stCodeBlock pre {
        font-size: 0.7rem !important;
        line-height: 1.25 !important;
        margin: 0.25rem 0 !important;
        padding: 0.5rem !important;
    }
    /* Make log content more compact */
    div[data-testid="stVerticalBlock"] > div:has(code) {
        margin-bottom: 0.2rem !important;
    }
    /* Compact markdown in logs */
    .element-container:has(small) {
        margin-bottom: 0.25rem !important;
    }
    /* Reduce spacing around code blocks */
    .element-container:has(pre) {
        margin-top: 0 !important;
        margin-bottom: 0.25rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'execution_log' not in st.session_state:
    st.session_state.execution_log = []
if 'last_run' not in st.session_state:
    st.session_state.last_run = None
if 'loaded_config' not in st.session_state:
    st.session_state.loaded_config = None
if 'config_loaded_from_run' not in st.session_state:
    st.session_state.config_loaded_from_run = None
if 'loaded_repo_files' not in st.session_state:
    st.session_state.loaded_repo_files = {
        'concepts': None,
        'inferences': None,
        'inputs': None
    }
# Session state for human-in-the-loop user interactions
if 'pending_user_inputs' not in st.session_state:
    st.session_state.pending_user_inputs = {}
if 'orchestrator_state' not in st.session_state:
    st.session_state.orchestrator_state = None
if 'waiting_for_input' not in st.session_state:
    st.session_state.waiting_for_input = False
if 'current_interaction' not in st.session_state:
    st.session_state.current_interaction = None

# --- SIDEBAR: Configuration ---
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # Load Configuration from Previous Runs
    st.subheader("📋 Load Previous Config")
    
    # Default database path - check common locations
    # User can override this later in Checkpoint Settings
    default_db_path = "orchestration.db"
    
    # Check if default exists (absolute or relative paths both work)
    db_path_for_config = default_db_path if os.path.exists(default_db_path) else None
    
    # Also check absolute path in app directory
    if not db_path_for_config:
        abs_path = str(script_dir / default_db_path)
        if os.path.exists(abs_path):
            db_path_for_config = abs_path
    
    if db_path_for_config:
        try:
            db_for_config = OrchestratorDB(db_path_for_config)
            runs_with_config = db_for_config.list_runs(include_metadata=True)
            
            if runs_with_config:
                # Create options for selectbox: run_id with timestamp
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
                
                if selected_config_idx > 0:  # Not the placeholder option
                    selected_run = runs_with_config[selected_config_idx - 1]
                    
                    # Check if repository files exist for this run
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
                        if run_config.get('concepts_file_path'):
                            available_files.append("concepts.json")
                        if run_config.get('inferences_file_path'):
                            available_files.append("inferences.json")
                        if run_config.get('inputs_file_path'):
                            available_files.append("inputs.json")
                        
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
                
                # Show loaded config indicator
                if st.session_state.config_loaded_from_run:
                    # Check if files were also loaded
                    loaded_files = [k for k, v in st.session_state.loaded_repo_files.items() if v is not None]
                    
                    if loaded_files:
                        st.success(f"📌 Config + Files loaded from: `{st.session_state.config_loaded_from_run[:12]}...`")
                        st.caption(f"Loaded files: {', '.join(loaded_files)}")
                    else:
                        st.success(f"📌 Config loaded from: `{st.session_state.config_loaded_from_run[:12]}...`")
                    
                    if st.button("🗑️ Clear Loaded Config", use_container_width=True):
                        st.session_state.loaded_config = None
                        st.session_state.config_loaded_from_run = None
                        st.session_state.loaded_repo_files = {
                            'concepts': None,
                            'inferences': None,
                            'inputs': None
                        }
                        st.rerun()
            else:
                st.info("No previous runs with configurations found")
        except Exception as e:
            st.warning(f"Could not load run configurations: {e}")
    else:
        st.info(f"Database not found. Run an orchestration to create it.")
    
    st.divider()
    
    st.subheader("📁 Repository Files")
    
    # Check if files were loaded from config
    loaded_concepts = st.session_state.loaded_repo_files.get('concepts')
    loaded_inferences = st.session_state.loaded_repo_files.get('inferences')
    loaded_inputs = st.session_state.loaded_repo_files.get('inputs')
    
    # Concepts file
    if loaded_concepts:
        st.info(f"📄 Using loaded: `{loaded_concepts['name']}`")
        if st.button("🔄 Upload Different Concepts File", key='change_concepts'):
            st.session_state.loaded_repo_files['concepts'] = None
            st.rerun()
        concepts_file = None  # Will use loaded file
    else:
        concepts_file = st.file_uploader("Concepts JSON", type=['json'], key='concepts')
    
    # Inferences file
    if loaded_inferences:
        st.info(f"📄 Using loaded: `{loaded_inferences['name']}`")
        if st.button("🔄 Upload Different Inferences File", key='change_inferences'):
            st.session_state.loaded_repo_files['inferences'] = None
            st.rerun()
        inferences_file = None  # Will use loaded file
    else:
        inferences_file = st.file_uploader("Inferences JSON", type=['json'], key='inferences')
    
    # Inputs file
    if loaded_inputs:
        st.info(f"📄 Using loaded: `{loaded_inputs['name']}`")
        if st.button("🔄 Upload Different Inputs File", key='change_inputs'):
            st.session_state.loaded_repo_files['inputs'] = None
            st.rerun()
        inputs_file = None  # Will use loaded file
    else:
        inputs_file = st.file_uploader(
            "Inputs JSON",
            type=['json'],
            key='inputs',
            help="Provides data for ground concepts (e.g., {number pair} for addition). See sample_inputs.json for format."
        )
    
    # Show tip only if no files are loaded or uploaded
    if not inputs_file and not loaded_inputs:
        st.info("💡 **Tip**: Most repositories need an inputs.json file to provide ground concept data. Check `sample_inputs.json` for an example.")
    
    st.divider()
    
    st.subheader("🔧 Runtime Settings")
    
    # Get defaults from loaded config if available
    loaded_config = st.session_state.loaded_config or {}
    
    # LLM Model selection
    llm_models = ["qwen-plus", "gpt-4o", "claude-3-sonnet", "qwen-turbo-latest"]
    default_llm = loaded_config.get("llm_model", "qwen-plus")
    try:
        default_llm_idx = llm_models.index(default_llm) if default_llm in llm_models else 0
    except ValueError:
        default_llm_idx = 0
    
    llm_model = st.selectbox(
        "LLM Model",
        llm_models,
        index=default_llm_idx,
        help="Loaded from previous run" if loaded_config.get("llm_model") else None
    )
    
    # Max Cycles
    default_max_cycles = loaded_config.get("max_cycles", 50)
    max_cycles = st.number_input(
        "Max Cycles", 
        min_value=1, 
        max_value=1000, 
        value=int(default_max_cycles), 
        step=10,
        help="Loaded from previous run" if loaded_config.get("max_cycles") else None
    )
    
    # Base directory for LLM file operations
    loaded_base_dir = loaded_config.get("base_dir")
    
    # Determine default base_dir_option from loaded config
    if loaded_base_dir:
        if loaded_base_dir == str(script_dir):
            default_base_dir_idx = 0  # App Directory
        elif loaded_base_dir == str(project_root):
            default_base_dir_idx = 1  # Project Root
        else:
            default_base_dir_idx = 2  # Custom Path
    else:
        default_base_dir_idx = 0
    
    base_dir_option = st.radio(
        "Base Directory",
        ["App Directory (default)", "Project Root", "Custom Path"],
        index=default_base_dir_idx,
        help="Where generated scripts and prompts will be stored. Loaded from previous run" if loaded_base_dir else "Where generated scripts and prompts will be stored"
    )
    
    if base_dir_option == "Custom Path":
        custom_base_dir = st.text_input(
            "Custom Base Directory",
            value=loaded_base_dir if loaded_base_dir and loaded_base_dir not in [str(script_dir), str(project_root)] else str(script_dir),
            help="Absolute or relative path for LLM file operations"
        )
    else:
        custom_base_dir = None
    
    st.divider()
    
    st.subheader("💾 Checkpoint Settings")
    
    # Get database path from loaded config if available
    default_db_path = loaded_config.get("db_path", "orchestration.db")
    
    if loaded_config.get("db_path"):
        db_path_help = "Loaded from previous run. Supports both absolute and relative paths."
    else:
        db_path_help = "Path to SQLite database file. Can be absolute (e.g., /path/to/db.sqlite) or relative (e.g., orchestration.db)"
    
    db_path = st.text_input(
        "Database Path", 
        value=default_db_path,
        help=db_path_help
    )
    
    resume_option = st.radio(
        "Execution Mode",
        ["Fresh Run", "Resume from Checkpoint", "Fork from Checkpoint"],
        help="Fresh Run: Start new execution\nResume: Continue existing run (configure reconciliation in Advanced Options)\nFork: Load state from one run, execute different repository with fresh history"
    )
    
    if resume_option == "Fresh Run":
        # Allow custom run name/ID for fresh runs
        # Load from previous config if available
        default_custom_run_id = loaded_config.get("custom_run_id", "")
        custom_run_id = st.text_input(
            "Run Name/ID (optional)",
            value=default_custom_run_id,
            placeholder="Leave empty to auto-generate",
            help="Specify a custom name/ID for this run. Leave empty to auto-generate a UUID. This helps identify and organize your runs." + (" (Loaded from previous run)" if default_custom_run_id else "")
        )
        run_id_to_resume = None
        new_run_id = None
    elif resume_option != "Fresh Run":
        # Load from previous config if available
        # For Fork mode, load forked_from_run_id; for Resume mode, load resumed_from_run_id
        default_run_id_to_resume = ""
        if resume_option == "Fork from Checkpoint":
            default_run_id_to_resume = loaded_config.get("forked_from_run_id", "")
        else:  # Resume from Checkpoint
            default_run_id_to_resume = loaded_config.get("resumed_from_run_id", "")
        
        run_id_to_resume = st.text_input(
            "Run ID to Resume", 
            value=default_run_id_to_resume,
            placeholder="Leave empty for latest",
            help="The run ID to load state from" + (" (Loaded from previous run)" if default_run_id_to_resume else "")
        )
        custom_run_id = None  # Not used for Resume/Fork modes
        
        # Forking option: specify a new run ID
        if resume_option == "Fork from Checkpoint":
            st.info("💡 **Forking**: Load state from one run, start a new run with different repository")
            # Load from previous config if available
            default_new_run_id = loaded_config.get("new_run_id", "")
            new_run_id = st.text_input(
                "New Run ID (optional)",
                value=default_new_run_id,
                placeholder="Leave empty to auto-generate",
                help="Specify a new run ID for the forked run. Leave empty to auto-generate." + (" (Loaded from previous run)" if default_new_run_id else "")
            )
        else:
            new_run_id = None
    
    # Advanced options (must come after resume_option is defined)
    with st.expander("🔧 Advanced Options"):
        verify_files = st.checkbox(
            "Verify repository file references",
            value=True,
            help="Check that all files referenced in concepts/inferences exist in base_dir before execution"
        )
        
        # Reconciliation mode (only shown for Resume/Fork modes)
        if resume_option != "Fresh Run":
            st.write("**Checkpoint Reconciliation Mode:**")
            
            # Set smart default based on execution mode
            if resume_option == "Fork from Checkpoint":
                default_reconciliation = "OVERWRITE"
                help_text = "OVERWRITE (default for forking): Trusts checkpoint data completely, keeps all values even if logic changed. PATCH: Discards values with changed logic. FILL_GAPS: Only fills empty concepts."
            else:
                default_reconciliation = "PATCH"
                help_text = "PATCH (default for resuming): Smart merge - discards stale state, keeps valid data. OVERWRITE: Trusts checkpoint completely. FILL_GAPS: Only fills empty concepts."
            
            # Map to radio button index
            mode_options = ["PATCH", "OVERWRITE", "FILL_GAPS"]
            default_index = mode_options.index(default_reconciliation)
            
            reconciliation_mode = st.radio(
                "How to apply checkpoint state:",
                mode_options,
                index=default_index,
                help=help_text,
                key="reconciliation_mode"
            )
        else:
            reconciliation_mode = None

# --- MAIN AREA ---
st.markdown('<h1 class="main-header">🧠 NormCode Orchestrator</h1>', unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Execute", "📊 Results", "📜 History", "📖 Help"])

# --- TAB 1: Execute ---
with tab1:
    st.header("Execute Orchestration")
    
    # Show success message from previous resumption if flag is set
    if st.session_state.get('show_success_message', False):
        st.success("✅ Execution completed successfully!")
        st.balloons()
        # Clear the flag
        st.session_state.show_success_message = False
        
        # Optionally show summary here too, or rely on Last Run
        if st.session_state.last_run:
            run_data = st.session_state.last_run
            st.subheader("📊 Execution Summary")
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            with summary_col1:
                st.metric("Run ID", run_data['run_id'][:8] + "...")
            with summary_col2:
                st.metric("Duration", f"{run_data['duration']:.2f}s")
            with summary_col3:
                completed_concepts = sum(1 for fc in run_data['final_concepts'] if fc and fc.concept and fc.concept.reference)
                st.metric("Completed Concepts", f"{completed_concepts}/{len(run_data['final_concepts'])}")
    
    # Handle user interaction if orchestrator is waiting for input
    if st.session_state.waiting_for_input and st.session_state.current_interaction:
        interaction = st.session_state.current_interaction
        
        st.warning("⏸️ **Execution Paused - Awaiting User Input**")
        
        # Display the prompt/context
        st.markdown(f"**Prompt:** {interaction['prompt']}")
        
        # Show interaction type-specific UI
        with st.form(key="user_interaction_form"):
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
                # Provide the input to the tool
                st.session_state.pending_user_inputs[interaction['id']] = user_input
                
                # Resume execution
                orchestrator_data = st.session_state.orchestrator_state
                if orchestrator_data:
                    try:
                        with st.spinner("▶️ Resuming execution..."):
                            # Re-initialize dependencies
                            # Note: concept_repo and inference_repo must be available from session state or closure
                            if not 'loaded_repo_files' in st.session_state:
                                st.error("Cannot resume: Repository files not found in session.")
                                st.stop()
                                
                            # Re-load repos if variables are not in scope (likely not in scope)
                            # We use the loaded_repo_files from session state
                            concepts_content = st.session_state.loaded_repo_files['concepts']['content']
                            inferences_content = st.session_state.loaded_repo_files['inferences']['content']
                            
                            # Parse JSON
                            concepts_json = json.loads(concepts_content)
                            inferences_json = json.loads(inferences_content)
                            
                            # Re-create repos
                            resume_concept_repo = ConceptRepo.from_json_list(concepts_json)
                            resume_inference_repo = InferenceRepo.from_json_list(inferences_json, resume_concept_repo)
                            
                            # Inject inputs again?
                            # If inputs were injected into the repo initially, they are needed here too 
                            # unless we trust the checkpoint fully.
                            # Since we use OVERWRITE mode, checkpoint data takes precedence.
                            
                            # Re-init Body & Tools
                            resume_body = Body(
                                llm_name=orchestrator_data['llm_model'], 
                                base_dir=orchestrator_data['base_dir']
                            )
                            resume_body.user_input = StreamlitInputTool() # Inject tool
                            
                            # Load Checkpoint
                            # We use load_checkpoint to get the exact state where we left off
                            orchestrator = Orchestrator.load_checkpoint(
                                concept_repo=resume_concept_repo,
                                inference_repo=resume_inference_repo,
                                db_path=orchestrator_data['db_path'],
                                run_id=orchestrator_data['run_id'],
                                body=resume_body,
                                mode="OVERWRITE" # Trust the checkpoint implicitly
                            )
                            
                            start_time = orchestrator_data['start_time']
                            
                            # Continue execution - the tool will now find the input and return it
                            final_concepts = orchestrator.run()
                            end_time = datetime.now()
                            duration = (end_time - start_time).total_seconds()
                            
                            # Success!
                            st.success(f"✅ Execution completed in {duration:.2f}s!")
                            
                            # Display results summary
                            st.subheader("📊 Execution Summary")
                            
                            summary_col1, summary_col2, summary_col3 = st.columns(3)
                            with summary_col1:
                                st.metric("Run ID", orchestrator.run_id[:8] + "...")
                            with summary_col2:
                                st.metric("Duration", f"{duration:.2f}s")
                            with summary_col3:
                                completed_concepts = sum(1 for fc in final_concepts if fc and fc.concept and fc.concept.reference)
                                st.metric("Completed Concepts", f"{completed_concepts}/{len(final_concepts)}")
                            
                            # Store results in session
                            st.session_state.last_run = {
                                'run_id': orchestrator.run_id,
                                'timestamp': datetime.now().isoformat(),
                                'duration': duration,
                                'final_concepts': final_concepts,
                                'llm_model': llm_model,
                                'max_cycles': max_cycles,
                                'base_dir': orchestrator.body.base_dir
                            }
                            
                            # Add to execution log
                            st.session_state.execution_log.insert(0, {
                                'run_id': orchestrator.run_id,
                                'timestamp': datetime.now().isoformat(),
                                'status': 'success',
                                'duration': duration,
                                'completed': completed_concepts
                            })
                            
                            # Clear waiting state
                            st.session_state.waiting_for_input = False
                            st.session_state.current_interaction = None
                            st.session_state.orchestrator_state = None
                            
                            # Set flag to show success message on next run
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
                        
                        # Clear waiting state
                        st.session_state.waiting_for_input = False
                        st.session_state.current_interaction = None
                        st.session_state.orchestrator_state = None
            
            elif cancel_btn:
                # Cancel execution
                st.warning("Execution cancelled by user")
                st.session_state.waiting_for_input = False
                st.session_state.current_interaction = None
                st.session_state.orchestrator_state = None
                st.rerun()
        
        st.divider()
        st.info("💡 **Tip:** The orchestrator will resume from where it paused once you submit your response.")
        
        # Don't show the normal execution UI when waiting for input
        st.stop()
    
    # Check if we have files (either uploaded or loaded)
    has_concepts = concepts_file is not None or loaded_concepts is not None
    has_inferences = inferences_file is not None or loaded_inferences is not None
    
    if has_concepts and has_inferences:
        # Preview section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📦 Concepts Preview")
            try:
                # Get concepts data from uploaded or loaded file
                if concepts_file:
                    concepts_file.seek(0)
                    concepts_data = json.load(concepts_file)
                else:
                    concepts_data = json.loads(loaded_concepts['content'])
                
                st.metric("Total Concepts", len(concepts_data))
                
                if concepts_data:
                    with st.expander("View Sample Concept"):
                        st.json(concepts_data[0], expanded=False)
            except Exception as e:
                st.error(f"Error loading concepts: {e}")
        
        with col2:
            st.subheader("🔗 Inferences Preview")
            try:
                # Get inferences data from uploaded or loaded file
                if inferences_file:
                    inferences_file.seek(0)
                    inferences_data = json.load(inferences_file)
                else:
                    inferences_data = json.loads(loaded_inferences['content'])
                
                st.metric("Total Inferences", len(inferences_data))
                
                if inferences_data:
                    with st.expander("View Sample Inference"):
                        st.json(inferences_data[0], expanded=False)
            except Exception as e:
                st.error(f"Error loading inferences: {e}")
        
        # Inputs preview
        has_inputs = inputs_file is not None or loaded_inputs is not None
        if has_inputs:
            st.subheader("📥 Inputs Preview")
            try:
                # Get inputs data from uploaded or loaded file
                if inputs_file:
                    inputs_file.seek(0)
                    inputs_data = json.load(inputs_file)
                else:
                    inputs_data = json.loads(loaded_inputs['content'])
                
                st.write(f"**{len(inputs_data)} input concept(s) will be injected:**")
                for concept_name in inputs_data.keys():
                    st.write(f"- `{concept_name}`")
            except Exception as e:
                st.error(f"Error loading inputs: {e}")
        
        st.divider()
        
        # Execution controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            execute_btn = st.button("▶️ **Start Execution**", type="primary", use_container_width=True)
        
        with col2:
            if st.button("🗑️ Clear Results", use_container_width=True):
                st.session_state.last_run = None
                st.session_state.execution_log = []
                st.success("Results cleared!")
                st.rerun()
        
        # Execute orchestration
        if execute_btn:
            with st.spinner("🔄 Executing orchestration..."):
                try:
                    # Get concepts data from uploaded or loaded file
                    if concepts_file:
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
                    
                    # Get inferences data from uploaded or loaded file
                    if inferences_file:
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
                    if inputs_file:
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
                    
                    # Load repositories
                    concept_repo = ConceptRepo.from_json_list(concepts_json_data)
                    
                    # Load and inject inputs
                    if inputs_json_data:
                        for concept_name, details in inputs_json_data.items():
                            if isinstance(details, dict) and 'data' in details:
                                data = details['data']
                                axes = details.get('axes')
                            else:
                                data = details
                                axes = None
                            concept_repo.add_reference(concept_name, data, axis_names=axes)
                        st.info(f"✓ Injected {len(inputs_json_data)} input concept(s)")
                    
                    # Load inferences
                    inference_repo = InferenceRepo.from_json_list(inferences_json_data, concept_repo)
                    
                    # Determine base directory for Body
                    st.info("Determining base directory...")
                    if base_dir_option == "Project Root":
                        body_base_dir = str(project_root)
                    elif base_dir_option == "Custom Path" and custom_base_dir:
                        body_base_dir = custom_base_dir
                    else:  # "App Directory (default)"
                        body_base_dir = str(script_dir)
                    
                    # Verify repository files against base directory (if enabled)
                    if verify_files:
                        st.info("Verifying repository files...")
                        valid, warnings_list, errors_list = verify_repository_files(
                            concept_repo, inference_repo, body_base_dir
                        )
                        
                        # Display verification results
                        if warnings_list:
                            for warning in warnings_list:
                                if warning.startswith("✓"):
                                    st.success(warning)
                                else:
                                    st.warning(f"⚠️ {warning}")
                        
                        if errors_list:
                            for error in errors_list:
                                st.error(f"❌ {error}")
                            st.error("**Cannot proceed**: Repository references files that don't exist in base_dir. Please fix the issues above.")
                            st.info("💡 **Tip**: You can disable verification in Advanced Options if these are false positives.")
                            raise ValueError("Repository file verification failed")
                    
                    # Initialize Body
                    body = Body(llm_name=llm_model, base_dir=body_base_dir)
                    
                    # Inject Streamlit-native user input tool for human-in-the-loop
                    body.user_input = StreamlitInputTool()
                    st.info(f"📂 Base directory: `{body_base_dir}`")
                    st.info(f"🤝 Human-in-the-loop mode enabled")
                    
                    # Create or load orchestrator
                    if resume_option == "Fresh Run":
                        # Use custom run_id if provided, otherwise auto-generate
                        run_id_for_fresh_run = custom_run_id.strip() if custom_run_id and custom_run_id.strip() else None
                        
                        orchestrator = Orchestrator(
                            concept_repo=concept_repo,
                            inference_repo=inference_repo,
                            body=body,
                            max_cycles=max_cycles,
                            db_path=db_path,
                            run_id=run_id_for_fresh_run  # Pass custom run_id if provided
                        )
                        
                        if run_id_for_fresh_run:
                            st.info(f"🆕 Started fresh run with custom ID: `{orchestrator.run_id}`")
                        else:
                            st.info(f"🆕 Started fresh run: `{orchestrator.run_id}`")
                        
                        # Save repository files to disk and get their paths
                        saved_file_paths = {}
                        try:
                            if concepts_file:
                                saved_file_paths['concepts'] = save_uploaded_file(concepts_file, orchestrator.run_id, 'concepts')
                            elif loaded_concepts:
                                saved_file_paths['concepts'] = loaded_concepts['path']
                            
                            if inferences_file:
                                saved_file_paths['inferences'] = save_uploaded_file(inferences_file, orchestrator.run_id, 'inferences')
                            elif loaded_inferences:
                                saved_file_paths['inferences'] = loaded_inferences['path']
                            
                            if inputs_file:
                                saved_file_paths['inputs'] = save_uploaded_file(inputs_file, orchestrator.run_id, 'inputs')
                            elif loaded_inputs:
                                saved_file_paths['inputs'] = loaded_inputs['path']
                            
                            st.info(f"✓ Saved repository files for run: {orchestrator.run_id[:8]}...")
                        except Exception as e:
                            st.warning(f"Could not save repository files: {e}")
                            logging.warning(f"Failed to save repository files: {e}")
                        
                        # Save app-specific configuration to database
                        try:
                            db_for_config = OrchestratorDB(db_path, run_id=orchestrator.run_id)
                            app_config = {
                                "llm_model": llm_model,
                                "max_cycles": max_cycles,
                                "base_dir": body_base_dir,
                                "base_dir_option": base_dir_option,
                                "db_path": db_path,
                                "agent_frame_model": orchestrator.agent_frame_model,
                                "resume_mode": "Fresh Run",
                                "verify_files": verify_files,
                                "app_version": "1.3.1",
                                # Add file paths
                                "concepts_file_path": saved_file_paths.get('concepts'),
                                "inferences_file_path": saved_file_paths.get('inferences'),
                                "inputs_file_path": saved_file_paths.get('inputs'),
                                # Save custom run name if provided
                                "custom_run_id": run_id_for_fresh_run if run_id_for_fresh_run else None
                            }
                            db_for_config.save_run_metadata(orchestrator.run_id, app_config)
                            logging.info(f"Saved app configuration for run_id: {orchestrator.run_id}")
                        except Exception as e:
                            logging.warning(f"Could not save app configuration: {e}")
                    elif resume_option == "Fork from Checkpoint":
                        # Forking: Load state from one run, start new history
                        import uuid
                        fork_new_run_id = new_run_id if new_run_id else f"fork-{uuid.uuid4().hex[:8]}"
                        
                        orchestrator = Orchestrator.load_checkpoint(
                            concept_repo=concept_repo,
                            inference_repo=inference_repo,
                            db_path=db_path,
                            body=body,
                            max_cycles=max_cycles,
                            run_id=run_id_to_resume if run_id_to_resume else None,
                            new_run_id=fork_new_run_id,
                            mode=reconciliation_mode,  # Use user-selected mode
                            validate_compatibility=True
                        )
                        st.success(f"🔱 Forked from `{run_id_to_resume or 'latest'}` → New run: `{orchestrator.run_id}`")
                        st.info(f"✓ State loaded from source run using {reconciliation_mode} mode, starting fresh execution history")
                        
                        # Save repository files to disk and get their paths
                        saved_file_paths = {}
                        try:
                            if concepts_file:
                                saved_file_paths['concepts'] = save_uploaded_file(concepts_file, orchestrator.run_id, 'concepts')
                            elif loaded_concepts:
                                saved_file_paths['concepts'] = loaded_concepts['path']
                            
                            if inferences_file:
                                saved_file_paths['inferences'] = save_uploaded_file(inferences_file, orchestrator.run_id, 'inferences')
                            elif loaded_inferences:
                                saved_file_paths['inferences'] = loaded_inferences['path']
                            
                            if inputs_file:
                                saved_file_paths['inputs'] = save_uploaded_file(inputs_file, orchestrator.run_id, 'inputs')
                            elif loaded_inputs:
                                saved_file_paths['inputs'] = loaded_inputs['path']
                        except Exception as e:
                            logging.warning(f"Failed to save repository files: {e}")
                        
                        # Save app-specific configuration to database
                        try:
                            db_for_config = OrchestratorDB(db_path, run_id=orchestrator.run_id)
                            app_config = {
                                "llm_model": llm_model,
                                "max_cycles": max_cycles,
                                "base_dir": body_base_dir,
                                "base_dir_option": base_dir_option,
                                "db_path": db_path,
                                "agent_frame_model": orchestrator.agent_frame_model,
                                "resume_mode": "Fork from Checkpoint",
                                "forked_from_run_id": run_id_to_resume or "latest",
                                "reconciliation_mode": reconciliation_mode,
                                "verify_files": verify_files,
                                "app_version": "1.3.1",
                                # Add file paths
                                "concepts_file_path": saved_file_paths.get('concepts'),
                                "inferences_file_path": saved_file_paths.get('inferences'),
                                "inputs_file_path": saved_file_paths.get('inputs'),
                                # Save custom run name if provided
                                "new_run_id": new_run_id if new_run_id and new_run_id.strip() else None
                            }
                            db_for_config.save_run_metadata(orchestrator.run_id, app_config)
                            logging.info(f"Saved app configuration for forked run_id: {orchestrator.run_id}")
                        except Exception as e:
                            logging.warning(f"Could not save app configuration: {e}")
                    else:
                        # Resume mode - use reconciliation_mode from Advanced Options
                        orchestrator = Orchestrator.load_checkpoint(
                            concept_repo=concept_repo,
                            inference_repo=inference_repo,
                            db_path=db_path,
                            body=body,
                            max_cycles=max_cycles,
                            run_id=run_id_to_resume if run_id_to_resume else None,
                            mode=reconciliation_mode  # Use user-selected mode
                        )
                        st.info(f"♻️ Resumed run: `{orchestrator.run_id}` (reconciliation: {reconciliation_mode})")
                        
                        # Save repository files to disk and get their paths
                        saved_file_paths = {}
                        try:
                            if concepts_file:
                                saved_file_paths['concepts'] = save_uploaded_file(concepts_file, orchestrator.run_id, 'concepts')
                            elif loaded_concepts:
                                saved_file_paths['concepts'] = loaded_concepts['path']
                            
                            if inferences_file:
                                saved_file_paths['inferences'] = save_uploaded_file(inferences_file, orchestrator.run_id, 'inferences')
                            elif loaded_inferences:
                                saved_file_paths['inferences'] = loaded_inferences['path']
                            
                            if inputs_file:
                                saved_file_paths['inputs'] = save_uploaded_file(inputs_file, orchestrator.run_id, 'inputs')
                            elif loaded_inputs:
                                saved_file_paths['inputs'] = loaded_inputs['path']
                        except Exception as e:
                            logging.warning(f"Failed to save repository files: {e}")
                        
                        # Update app-specific configuration in database (for resumed runs)
                        try:
                            db_for_config = OrchestratorDB(db_path, run_id=orchestrator.run_id)
                            # Get existing metadata and update it
                            existing_metadata = db_for_config.get_run_metadata(orchestrator.run_id) or {}
                            app_config = {
                                **existing_metadata,  # Keep existing metadata
                                "llm_model": llm_model,
                                "max_cycles": max_cycles,
                                "base_dir": body_base_dir,
                                "base_dir_option": base_dir_option,
                                "db_path": db_path,
                                "agent_frame_model": orchestrator.agent_frame_model,
                                "resume_mode": "Resume from Checkpoint",
                                "reconciliation_mode": reconciliation_mode,
                                "verify_files": verify_files,
                                "app_version": "1.3.1",
                                "last_resumed": datetime.now().isoformat(),
                                # Update file paths
                                "concepts_file_path": saved_file_paths.get('concepts') or existing_metadata.get('concepts_file_path'),
                                "inferences_file_path": saved_file_paths.get('inferences') or existing_metadata.get('inferences_file_path'),
                                "inputs_file_path": saved_file_paths.get('inputs') or existing_metadata.get('inputs_file_path'),
                                # Save resumed_from_run_id if it was a fresh resume (not continuing same run)
                                "resumed_from_run_id": run_id_to_resume if run_id_to_resume and run_id_to_resume.strip() else existing_metadata.get('resumed_from_run_id')
                            }
                            db_for_config.save_run_metadata(orchestrator.run_id, app_config)
                            logging.info(f"Updated app configuration for resumed run_id: {orchestrator.run_id}")
                        except Exception as e:
                            logging.warning(f"Could not update app configuration: {e}")
                    
                    # Progress tracking
                    progress_placeholder = st.empty()
                    progress_placeholder.text(f"⏳ Running orchestrator (Run ID: {orchestrator.run_id})...")
                    
                    # Execute with human-in-the-loop support
                    start_time = datetime.now()
                    
                    try:
                        final_concepts = orchestrator.run()
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        
                        progress_placeholder.empty()
                        
                        # Success message
                        st.success(f"✅ Execution completed in {duration:.2f}s!")
                        
                        # Clear any waiting state
                        st.session_state.waiting_for_input = False
                        st.session_state.current_interaction = None
                        
                    except NeedsUserInteraction as interaction:
                        # User interaction required - pause execution
                        progress_placeholder.empty()
                        
                        # Save orchestrator state for resumption
                        # We can't pickle the orchestrator object directly due to SQLite connection and Locks
                        # So we save the parameters needed to re-load it
                        st.session_state.orchestrator_state = {
                            'run_id': orchestrator.run_id,
                            'db_path': db_path,
                            'llm_model': llm_model,
                            'max_cycles': max_cycles,
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
                        
                        # Save a checkpoint so we can resume from this point
                        if orchestrator.checkpoint_manager:
                            orchestrator.checkpoint_manager.save_state(
                                orchestrator.tracker.cycle_count,
                                orchestrator,
                                inference_count=orchestrator.tracker.total_executions
                            )
                            logging.info(f"Checkpoint saved at user interaction point")
                        
                        st.info("🛑 **Execution paused - User input required**")
                        st.warning("⚠️ Please provide the requested information below and click Submit to continue execution.")
                        
                        # Don't proceed to success metrics - will be shown after resumption
                        raise  # Re-raise to skip the rest of the execution flow
                    
                    # Display results summary
                    st.subheader("📊 Execution Summary")
                    
                    summary_col1, summary_col2, summary_col3 = st.columns(3)
                    with summary_col1:
                        st.metric("Run ID", orchestrator.run_id[:8] + "...")
                    with summary_col2:
                        st.metric("Duration", f"{duration:.2f}s")
                    with summary_col3:
                        completed_concepts = sum(1 for fc in final_concepts if fc and fc.concept and fc.concept.reference)
                        st.metric("Completed Concepts", f"{completed_concepts}/{len(final_concepts)}")
                    
                    # Store results in session
                    st.session_state.last_run = {
                        'run_id': orchestrator.run_id,
                        'timestamp': datetime.now().isoformat(),
                        'duration': duration,
                        'final_concepts': final_concepts,
                        'llm_model': llm_model,
                        'max_cycles': max_cycles,
                        'base_dir': body_base_dir
                    }
                    
                    # Add to execution log
                    st.session_state.execution_log.insert(0, {
                        'run_id': orchestrator.run_id,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'success',
                        'duration': duration,
                        'completed': completed_concepts
                    })
                    
                    st.balloons()
                    
                except NeedsUserInteraction:
                    # User interaction required - UI is already shown above
                    # Just rerun to display the interaction form
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Execution failed: {str(e)}")
                    st.exception(e)
                    
                    # Clear any waiting state on error
                    st.session_state.waiting_for_input = False
                    st.session_state.current_interaction = None
                    st.session_state.orchestrator_state = None
                    
                    # Log failure
                    st.session_state.execution_log.insert(0, {
                        'run_id': 'unknown',
                        'timestamp': datetime.now().isoformat(),
                        'status': 'failed',
                        'error': str(e)
                    })
    else:
        st.info("👈 **Please upload repository files in the sidebar to begin**")
        
        st.markdown("""
        ### Required Files:
        1. **concepts.json** - Defines the concepts (variables/data structures)
        2. **inferences.json** - Defines the inference steps (logic/operations)
        3. **inputs.json** (optional) - Provides initial data for ground concepts
        
        You can find example files in `infra/examples/add_examples/repo/`
        """)

# --- TAB 2: Results ---
with tab2:
    st.header("Results Viewer")
    
    if st.session_state.last_run:
        run_data = st.session_state.last_run
        
        # Run info header
        st.subheader(f"🔖 Run: {run_data['run_id']}")
        
        info_col1, info_col2, info_col3, info_col4 = st.columns(4)
        with info_col1:
            st.caption("⏰ Completed")
            st.write(datetime.fromisoformat(run_data['timestamp']).strftime("%Y-%m-%d %H:%M:%S"))
        with info_col2:
            st.caption("⏱️ Duration")
            st.write(f"{run_data['duration']:.2f}s")
        with info_col3:
            st.caption("🤖 LLM Model")
            st.write(run_data['llm_model'])
        with info_col4:
            st.caption("🔄 Max Cycles")
            st.write(run_data['max_cycles'])
        
        # Show base directory if available
        if 'base_dir' in run_data:
            st.caption(f"📂 Base Directory: `{run_data['base_dir']}`")
        
        st.divider()
        
        # Quick access to logs for this run
        st.subheader("📋 Execution Logs")
        if os.path.exists(db_path):
            try:
                db_for_logs = OrchestratorDB(db_path)
                logs = db_for_logs.get_all_logs(run_data['run_id'])
                
                if logs:
                    st.caption(f"📊 {len(logs)} log entries available")
                    
                    # Quick view of recent logs
                    with st.expander("View Recent Logs (Last 10)", expanded=False):
                        recent_logs = logs[-10:] if len(logs) > 10 else logs
                        for i, log in enumerate(reversed(recent_logs)):
                            # Compact log header
                            st.markdown(
                                f"<small><b>Cycle {log['cycle']} | Flow {log['flow_index']} | Status: {log['status']}</b></small>",
                                unsafe_allow_html=True
                            )
                            st.code(log['log_content'], language="text")
                            if i < len(recent_logs) - 1:
                                st.markdown("<hr style='margin: 0.5rem 0; border: 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
                    
                    # Full logs view
                    if len(logs) > 10:
                        with st.expander("View All Logs", expanded=False):
                            for i, log in enumerate(logs):
                                # Compact log header
                                st.markdown(
                                    f"<small><b>Cycle {log['cycle']} | Flow {log['flow_index']} | Status: {log['status']}</b></small>",
                                    unsafe_allow_html=True
                                )
                                st.code(log['log_content'], language="text")
                                if i < len(logs) - 1:
                                    st.markdown("<hr style='margin: 0.5rem 0; border: 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
                    
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
                else:
                    st.info("ℹ️ No logs recorded for this run. This may be normal for older runs.")
            except Exception as e:
                st.warning(f"Could not load logs: {e}")
        else:
            st.info("ℹ️ Database not found. Logs are only available when using database checkpoints.")
        
        st.divider()
        
        # Export button
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
        
        # Display concepts
        st.subheader("📦 Final Concepts")
        
        # Filter options
        filter_option = st.radio(
            "Show:",
            ["All Concepts", "Only Completed", "Only Empty"],
            horizontal=True
        )
        
        for fc in run_data['final_concepts']:
            if not fc:
                continue
                
            has_reference = fc.concept and fc.concept.reference
            
            # Apply filter
            if filter_option == "Only Completed" and not has_reference:
                continue
            elif filter_option == "Only Empty" and has_reference:
                continue
            
            # Display concept
            if has_reference:
                with st.expander(f"✅ {fc.concept_name}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Type:** `{fc.type}`")
                        st.write(f"**Axes:** `{fc.concept.reference.axes}`")
                        st.write(f"**Shape:** `{fc.concept.reference.shape}`")
                    
                    with col2:
                        st.write("**Tensor:**")
                        st.code(str(fc.concept.reference.tensor), language="python")
            else:
                with st.expander(f"⚠️ {fc.concept_name} (no reference)", expanded=False):
                    st.warning(f"This concept has type `{fc.type}` but no reference data.")
    else:
        st.info("ℹ️ No results yet. Execute an orchestration in the **Execute** tab.")

# --- TAB 3: History ---
with tab3:
    st.header("Execution History")
    
    # Database runs
    st.subheader("💾 Database Runs")
    
    if os.path.exists(db_path):
        try:
            db = OrchestratorDB(db_path)
            runs = db.list_runs()
            
            if runs:
                for run in runs:
                    with st.expander(f"🔖 {run['run_id']}", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**First Execution:** {run['first_execution']}")
                            st.write(f"**Last Execution:** {run['last_execution']}")
                        
                        with col2:
                            st.write(f"**Execution Count:** {run['execution_count']}")
                            st.write(f"**Max Cycle:** {run['max_cycle']}")
                        
                        st.divider()
                        
                        # Show run configuration
                        st.write("**Run Configuration:**")
                        run_metadata = db.get_run_metadata(run['run_id'])
                        if run_metadata:
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
                            
                            # Show full config with checkbox toggle (can't use nested expander)
                            show_full_config = st.checkbox(
                                "View Full Configuration",
                                key=f"show_config_{run['run_id']}"
                            )
                            if show_full_config:
                                st.json(run_metadata)
                        else:
                            st.caption("ℹ️ No configuration metadata available")
                        
                        st.divider()
                        
                        # Show checkpoints
                        checkpoints = db.list_checkpoints(run['run_id'])
                        if checkpoints:
                            st.write(f"**Checkpoints:** {len(checkpoints)}")
                            
                            # Show last 3 checkpoints
                            if len(checkpoints) <= 3:
                                for cp in checkpoints:
                                    st.caption(f"Cycle {cp['cycle']}, Inference {cp.get('inference_count', 0)}: {cp['timestamp']}")
                            else:
                                st.caption(f"Latest: Cycle {checkpoints[-1]['cycle']}, Inference {checkpoints[-1].get('inference_count', 0)}")
                                st.caption(f"... and {len(checkpoints) - 1} more")
                        
                        st.divider()
                        
                        # Show execution history
                        st.write("**Execution History:**")
                        execution_history = db.get_execution_history(run['run_id'])
                        if execution_history:
                            st.caption(f"Total executions: {len(execution_history)}")
                            
                            # Show summary with checkbox toggle
                            show_exec_history = st.checkbox(
                                "View Execution Summary", 
                                key=f"show_exec_{run['run_id']}"
                            )
                            if show_exec_history:
                                for exec_record in execution_history:
                                    status_icon = "✅" if exec_record['status'] == 'success' else "❌" if exec_record['status'] == 'failed' else "⏳"
                                    st.text(
                                        f"{status_icon} Cycle {exec_record['cycle']}, "
                                        f"Flow {exec_record['flow_index']}: "
                                        f"{exec_record['concept_inferred']} "
                                        f"[{exec_record['status']}]"
                                    )
                        
                        st.divider()
                        
                        # Show logs
                        st.write("**Detailed Logs:**")
                        logs = db.get_all_logs(run['run_id'])
                        if logs:
                            st.caption(f"Total log entries: {len(logs)}")
                            
                            # Filter options for logs
                            log_filter = st.selectbox(
                                "Filter logs by:",
                                ["All Logs", "By Cycle", "By Status"],
                                key=f"log_filter_{run['run_id']}"
                            )
                            
                            filtered_logs = logs
                            
                            if log_filter == "By Cycle":
                                cycles = sorted(set(log['cycle'] for log in logs))
                                selected_cycle = st.selectbox(
                                    "Select Cycle:",
                                    cycles,
                                    key=f"cycle_select_{run['run_id']}"
                                )
                                filtered_logs = [log for log in logs if log['cycle'] == selected_cycle]
                            
                            elif log_filter == "By Status":
                                statuses = sorted(set(log['status'] for log in logs))
                                selected_status = st.selectbox(
                                    "Select Status:",
                                    statuses,
                                    key=f"status_select_{run['run_id']}"
                                )
                                filtered_logs = [log for log in logs if log['status'] == selected_status]
                            
                            # Display logs with checkbox toggle
                            show_logs = st.checkbox(
                                f"View Logs ({len(filtered_logs)} entries)",
                                key=f"show_logs_{run['run_id']}"
                            )
                            if show_logs:
                                for i, log in enumerate(filtered_logs):
                                    # Compact log header
                                    st.markdown(
                                        f"<small><b>Cycle {log['cycle']} | Flow {log['flow_index']} | Status: {log['status']}</b></small>",
                                        unsafe_allow_html=True
                                    )
                                    st.code(log['log_content'], language="text")
                                    if i < len(filtered_logs) - 1:  # Don't add divider after last entry
                                        st.markdown("<hr style='margin: 0.5rem 0; border: 0; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
                            
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
                        else:
                            st.info("No logs available for this run.")
            else:
                st.info("No runs found in database.")
        except Exception as e:
            st.error(f"Error loading database: {e}")
            st.exception(e)
    else:
        st.warning(f"Database not found: `{db_path}`")
    
    st.divider()
    
    # Session execution log
    st.subheader("📋 Session Log")
    
    if st.session_state.execution_log:
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
    else:
        st.info("No executions in this session yet.")

# --- TAB 4: Help ---
with tab4:
    st.header("📖 Quick Start Guide")
    
    st.markdown("""
    ## How to Use This App
    
    ### 🆕 Load Configuration from Previous Runs
    
    **NEW in v1.3!** You can now load configurations from previous runs to quickly replicate settings:
    
    1. In the sidebar, look for "📋 Load Previous Config"
    2. Select a previous run from the dropdown
    3. Click "🔄 Load Config" to automatically populate settings
    4. Settings loaded include: LLM model, max cycles, base directory, and more
    5. Click "👁️ Preview" to see full configuration details
    
    This feature is perfect for:
    - Re-running experiments with the same settings
    - Comparing results with different repositories but same configuration
    - Quickly setting up similar runs without manual configuration
    
    ---
    
    ### 1️⃣ Prepare Your Repository Files
    
    You need two JSON files to run an orchestration:
    
    - **`concepts.json`** - Defines all concepts (data structures, variables)
    - **`inferences.json`** - Defines inference steps (operations, logic)
    - **`inputs.json`** (optional) - Provides initial values for ground concepts
    
    ### 2️⃣ Upload Files
    
    Use the sidebar to upload your repository files. You can find example files in:
    ```
    infra/examples/add_examples/repo/
    ```
    
    ### 3️⃣ Configure Settings
    
    - **LLM Model**: Choose the language model for inference execution
    - **Max Cycles**: Set the maximum number of execution cycles
    - **Base Directory**: Where generated scripts/prompts are stored
      - **App Directory**: `streamlit_app/` (default, keeps files isolated)
      - **Project Root**: `normCode/` (useful for accessing generated files)
      - **Custom Path**: Specify any directory
    - **Database Path**: Path to store checkpoints (default: `orchestration.db`)
    
    #### Advanced Options
    
    - **Verify repository file references**: Check that scripts/prompts exist before execution (recommended)
    
    ### 4️⃣ Choose Execution Mode
    
    - **Fresh Run**: Start a new execution from scratch
    - **Resume from Checkpoint**: Continue an existing run from its last checkpoint
    - **Fork from Checkpoint**: Load state from one run, start new execution with different repository
    
    #### Reconciliation Mode (Advanced Options)
    
    When resuming or forking, you can choose how checkpoint state is applied:
    
    - **PATCH** (default for Resume): Smart merge - discards values with changed logic, keeps valid data
    - **OVERWRITE** (default for Fork): Trusts checkpoint completely - keeps all values even if logic changed
    - **FILL_GAPS**: Only fills empty concepts - prefers new repo defaults
    
    ### 5️⃣ Execute & View Results
    
    Click "Start Execution" and monitor progress. Results will appear in the Results tab.
    
    ---
    
    ## Input File Format
    
    ### inputs.json
    ```json
    {
      "{concept name}": {
        "data": [1, 2, 3],
        "axes": ["axis_name"]
      }
    }
    ```
    
    Or simply:
    ```json
    {
      "{concept name}": [1, 2, 3]
    }
    ```
    
    ---
    
    ## Checkpoint & Resume
    
    The orchestrator automatically saves checkpoints to a SQLite database. You can:
    
    - Resume interrupted executions
    - Fork runs to test changes
    - View execution history
    
    See the **History** tab for available runs and checkpoints.
    
    ### Forking Runs (Repository Chaining)
    
    **Forking** allows you to chain repositories together by loading completed concepts from one run and using them in a different repository:
    
    **Example: Addition → Combination**
    
    1. **Run the Addition Repository:**
       - Upload `addition_concepts.json`, `addition_inferences.json`, `addition_inputs.json`
       - Execute (produces `{new number pair}` with digit-by-digit results)
       - Note the run ID
    
    2. **Fork to Combination Repository:**
       - Upload `combination_concepts.json`, `combination_inferences.json`
       - NO inputs.json needed (will load from checkpoint)
       - Choose "Fork from Checkpoint" mode
       - Enter the addition run ID
       - Execute!
    
    **What Happens:**
    - State from addition run is loaded (including `{new number pair}`)
    - **OVERWRITE mode** keeps all checkpoint data (even if logic differs between repos)
    - New repository's inferences execute using the loaded data
    - Fresh execution history starts for the new run
    - Cycle count resets to 1
    
    **Why OVERWRITE for Forking?**
    - Different repos may have different signatures for same concept
    - PATCH would discard data due to signature mismatch
    - OVERWRITE trusts the checkpoint and keeps all data
    - You can change to PATCH in Advanced Options if needed
    
    **Use Cases:**
    - Multi-stage pipelines (addition → combination → analysis)
    - Testing different post-processing on same input
    - Reusing expensive computation results
    
    ---
    
    ## Execution Logs & History
    
    ### Viewing Logs
    
    The app provides comprehensive logging access in multiple locations:
    
    **Results Tab:**
    - View logs for the current run immediately after execution
    - Quick access to recent logs (last 10 entries)
    - Export logs to JSON for offline analysis
    
    **History Tab:**
    - Browse all runs in the database
    - View execution history with status, cycle, and concept information
    - Access detailed logs with filtering options:
      - Filter by cycle to see logs for specific execution phases
      - Filter by status to focus on success/failed executions
    - Export logs for any previous run
    
    ### Log Content
    
    Each log entry includes:
    - Cycle number
    - Flow index (inference identifier)
    - Execution status (success, failed, etc.)
    - Detailed execution information and debug output
    
    ### Session Log
    
    The Session Log shows high-level execution summaries for runs in the current browser session:
    - Quick overview of successful/failed runs
    - Duration and completion metrics
    - Useful for tracking multiple test runs
    
    ---
    
    ## Documentation
    
    - **Orchestration Guide**: `infra/_orchest/README.md`
    - **Repository Compatibility**: `infra/_orchest/REPO_COMPATIBILITY.md`
    - **Examples**: `infra/examples/add_examples/`
    """)

# Footer
st.divider()
st.caption("NormCode Orchestrator v1.3.1 | Powered by Streamlit | 📋 Load complete setups (config + files + database)!")

