"""
Help/Documentation tab for NormCode Orchestrator Streamlit App.
"""

import streamlit as st


def render_help_tab():
    """Render the Help tab with documentation and quick start guide."""
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

