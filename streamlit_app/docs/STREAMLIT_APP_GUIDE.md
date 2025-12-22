# NormCode Orchestrator - Streamlit App Guide

This guide provides complete information about the minimal Streamlit app for running NormCode orchestrations.

## 📋 Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Launching the App](#launching-the-app)
- [Features](#features)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The Streamlit Orchestrator App provides a **zero-configuration web interface** for running NormCode orchestrations. It eliminates the need to write Python scripts for each execution scenario.

### Key Benefits

✅ **No coding required** - Just upload JSON files  
✅ **Visual feedback** - See execution progress and results in real-time  
✅ **Checkpoint management** - Resume, fork, and explore run history  
✅ **Export results** - Download outputs as JSON  
✅ **Multi-mode support** - Fresh runs, smart resume (PATCH), and more  

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- The NormCode project (this repository)

### Install Streamlit

```bash
pip install streamlit
```

That's it! The app uses the existing `infra` module from the project.

## 🎬 Launching the App

### Method 1: Python Launcher (Recommended)

```bash
python run_app.py
```

This script will:
- Check if streamlit is installed
- Offer to install it if missing
- Launch the app automatically

### Method 2: Direct Streamlit Command

```bash
cd streamlit_app
streamlit run app.py
```

### Method 3: Platform-Specific Scripts

**Windows (PowerShell):**
```powershell
.\run_app.ps1
```

**Windows (Command Prompt):**
```cmd
run_app.bat
```

**Linux/Mac:**
```bash
python run_app.py
```

The app will open in your browser at `http://localhost:8501`

## ✨ Features

### 1. Repository Management

- **Upload Files**: Drag and drop or browse for JSON files
  - `concepts.json` - Concept definitions
  - `inferences.json` - Inference steps
  - `inputs.json` - Ground concept values (optional)
  
- **Preview**: See file contents before execution

### 2. Execution Configuration

- **LLM Model Selection**: Choose from multiple models
  - qwen-plus (default)
  - gpt-4o
  - claude-3-sonnet
  - qwen-turbo-latest

- **Max Cycles**: Set execution limits (1-1000)

- **Base Directory**: Where LLM-generated files are stored
  - **App Directory** (default): Stores in `streamlit_app/` - keeps files isolated
  - **Project Root**: Stores in project root - easier to find generated scripts
  - **Custom Path**: Specify any directory path
  
  *Why this matters*: When the LLM generates Python scripts or prompts during execution, they're saved to this directory. Choose based on where you want to access these files.

- **Database Path**: Specify checkpoint storage location

### Advanced Options

Expand the "Advanced Options" section for additional settings:

- **Verify repository file references**: 
  - **Enabled (default)**: Checks that all files referenced in concepts/inferences exist before execution
  - **Disabled**: Skip verification (useful if you know files will be generated during execution)
  
  The verifier looks for:
  - Script files (`.py`) referenced in concepts
  - Prompt files (`.txt`, `.prompt`) referenced in concepts
  - Missing `generated_scripts/` or `prompts/` directories
  
  **Benefits**:
  - Catch configuration errors early
  - Avoid runtime failures due to missing files
  - Get warnings about expected directory structure
  
  **When to disable**:
  - Files are generated dynamically during execution
  - You're using mock/test data that doesn't require real files
  - You know the warnings are false positives

### 3. Execution Modes

#### Fresh Run
Start a new execution from scratch with no checkpoint dependency.

**Use when:**
- Starting a new orchestration
- No existing checkpoint needed
- Testing new repositories

#### Resume (PATCH) - Recommended
Smart merge that discards stale state but keeps valid data.

**Use when:**
- You fixed a bug in one step
- Repository logic changed
- Want to skip already-completed valid steps

**Behavior:**
- Compares logic signatures
- Keeps data if logic unchanged
- Re-runs steps with changed logic

#### Resume (OVERWRITE)
Trust checkpoint completely, ignore logic changes.

**Use when:**
- Resuming identical repositories
- You're certain no logic changed
- Maximum performance (no signature checks)

#### Resume (FILL_GAPS)
Only fill empty concepts from checkpoint.

**Use when:**
- Importing partial results
- Prefer new repo defaults
- Conservative state application

### 4. Results Viewer

- **Concept Browser**: Explore all final concepts
- **Filters**: Show all, completed only, or empty only
- **Details**: View tensor, axes, shape for each concept
- **Export**: Download results as JSON

### 5. History & Checkpointing

- **Database Runs**: Browse all runs in the database
- **Checkpoints**: See available checkpoints per run
- **Session Log**: Track executions in current session

## 📚 Usage Examples

### Example 1: Running the Addition Example

This example demonstrates multi-digit addition with carry-over logic.

**Step 1: Prepare Input File**

Create `my_inputs.json`:
```json
{
  "{number pair}": {
    "data": [["%(123)", "%(456)"]],
    "axes": ["number pair", "number"]
  }
}
```

**Step 2: Launch App**
```bash
streamlit run app.py
```

**Step 3: Upload Files**
- Concepts: `infra/examples/add_examples/repo/addition_concepts.json`
- Inferences: `infra/examples/add_examples/repo/addition_inferences.json`
- Inputs: `my_inputs.json`

**Step 4: Configure**
- LLM Model: `qwen-plus`
- Max Cycles: `50`
- Mode: `Fresh Run`

**Step 5: Execute**
Click "▶️ Start Execution"

**Step 6: View Results**
Go to "Results" tab to see `{new number pair}` and other concepts.

### Example 2: Combination from Addition Checkpoint

This example demonstrates repository chaining - using output from one repo as input to another.

**Prerequisites:** Complete Example 1 first to create the checkpoint.

**Step 1: Upload Combination Repository**
- Concepts: `infra/examples/add_examples/repo/combination_concepts.json`
- Inferences: `infra/examples/add_examples/repo/combination_inferences.json`
- Inputs: None (will load from checkpoint)

**Step 2: Configure for Resume**
- Mode: `Resume (PATCH)`
- Database Path: `orchestration.db` (same as Example 1)
- Leave Run ID empty to use latest

**Step 3: Execute**
The app will:
1. Load `{new number pair}` from the addition checkpoint
2. Execute the combination logic
3. Produce `{sum}` as the final result

### Example 3: Fixing a Bug and Re-running

Scenario: You found a bug in one inference step and want to re-run just that step.

**Step 1: Fix the Repository**
Edit your `inferences.json` to fix the bug.

**Step 2: Upload Fixed Repository**
Upload the corrected files in the app.

**Step 3: Use PATCH Mode**
- Mode: `Resume (PATCH)`
- Run ID: (specify the run to fix)

**Step 4: Execute**
The app will:
- Detect the changed logic (signature mismatch)
- Discard the old result for that step
- Re-run only the changed step
- Keep all other completed steps

## 🔧 Troubleshooting

### App Won't Start

**Error: "streamlit: command not found"**

**Solution:**
```bash
pip install streamlit
```

**Error: "No module named 'infra'"**

**Solution:** Make sure you're running from the streamlit_app directory:
```bash
cd /path/to/normCode/streamlit_app
streamlit run app.py
```

### Execution Errors

**"Database not found"**

This is normal on first run. The database is created automatically.

**"Concept not found in repo"**

Check that all concepts referenced in `inferences.json` exist in `concepts.json`.

**"Checkpoint incompatible"**

- Try using `PATCH` mode instead of `OVERWRITE`
- Or start a `Fresh Run`

### File Upload Issues

**"Error loading concepts"**

Verify JSON syntax:
```bash
python -m json.tool concepts.json
```

**"File too large"**

Streamlit has upload limits. For very large repositories, consider running the command-line scripts instead.

### Performance Issues

**App is slow**

- Reduce `Max Cycles` for testing
- Use simpler LLM models (e.g., `qwen-turbo-latest`)
- Check if LLM API is responding

## 📖 Additional Resources

- **Orchestration Engine**: `infra/_orchest/README.md`
- **Repository Compatibility**: `infra/_orchest/REPO_COMPATIBILITY.md`
- **Implementation Guide**: `infra/_orchest/REPOSITORY_COMPATIBILITY_IMPLEMENTATION.md`
- **Example Scripts**: `infra/examples/add_examples/`

## 🆘 Getting Help

If you encounter issues:

1. Check the app's built-in **Help** tab
2. Review execution logs in the terminal
3. Examine the database with: `python -c "from infra._orchest._db import OrchestratorDB; db = OrchestratorDB('orchestration.db'); print(db.list_runs())"`
4. Run examples from command line first to verify setup

## 🎓 Learning Path

Recommended progression:

1. **Start Here**: Run Example 1 (Addition) to understand basics
2. **Next**: Try Example 2 (Combination) to learn checkpointing
3. **Advanced**: Experiment with Example 3 (Bug fixing) to master PATCH mode
4. **Create**: Build your own repositories and run them in the app

## 🚀 Tips & Best Practices

### Checkpoint Strategy

- Use unique database paths for different projects
- Keep `orchestration.db` in `.gitignore`
- Regularly export results for backup

### Repository Design

- Start simple, add complexity incrementally
- Test each inference step independently
- Use descriptive concept names

### Mode Selection

- **Default to PATCH**: Safest for most scenarios
- **Use OVERWRITE**: Only for truly identical repos
- **Use FILL_GAPS**: When testing repo changes with partial data

### Performance

- Set realistic `Max Cycles` limits
- Monitor checkpoint database size
- Clean up old runs periodically

## 📝 Version History

- **v1.0** (2025-11-30): Initial release
  - Basic orchestration execution
  - Checkpoint management
  - Results viewer
  - History browser

---

**Happy Orchestrating! 🎉**

