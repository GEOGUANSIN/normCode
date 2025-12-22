# NormCode Orchestrator - CLI Guide

A command-line interface for running NormCode orchestrations. Equivalent to the Streamlit app but designed for terminal users, scripting, and automation.

## Installation

No additional installation needed - uses the same dependencies as the main project.

```bash
# Make executable (Unix/Mac)
chmod +x cli_orchestrator.py

# Or run with python
python cli_orchestrator.py --help
```

## Quick Start

### 1. Fresh Run

Execute a new orchestration with your repository:

```bash
python cli_orchestrator.py run \
  --concepts path/to/concepts.json \
  --inferences path/to/inferences.json \
  --inputs path/to/inputs.json
```

### 2. Resume from Checkpoint

Continue an interrupted or previous run:

```bash
python cli_orchestrator.py resume \
  --concepts path/to/concepts.json \
  --inferences path/to/inferences.json \
  --run-id <run-id>
```

### 3. Fork Between Repositories

Load data from one run, execute with a different repository:

```bash
python cli_orchestrator.py fork \
  --concepts path/to/NEW_concepts.json \
  --inferences path/to/NEW_inferences.json \
  --from-run <source-run-id>
```

## Commands

### `run` - Fresh Execution

Start a new orchestration run from scratch.

**Required:**
- `--concepts FILE` - Path to concepts JSON file
- `--inferences FILE` - Path to inferences JSON file

**Optional:**
- `--inputs FILE` - Path to inputs JSON file
- `--llm MODEL` - LLM model name (default: demo)
- `--base-dir PATH` - Base directory for Body (default: current directory)
- `--max-cycles N` - Maximum cycles to run (default: 30)
- `--db-path FILE` - Database path (default: orchestration.db)

**Example:**
```bash
python cli_orchestrator.py run \
  --concepts infra/examples/add_examples/repo/addition_concepts.json \
  --inferences infra/examples/add_examples/repo/addition_inferences.json \
  --inputs infra/examples/add_examples/repo/addition_inputs.json \
  --llm qwen-plus \
  --max-cycles 50
```

### `resume` - Continue from Checkpoint

Resume execution from a saved checkpoint.

**Required:**
- `--concepts FILE` - Path to concepts JSON file
- `--inferences FILE` - Path to inferences JSON file

**Optional:**
- `--run-id ID` - Run ID to resume (default: latest)
- `--mode MODE` - Reconciliation mode: PATCH, OVERWRITE, FILL_GAPS (default: PATCH)
- `--inputs FILE` - Path to inputs JSON file
- `--llm MODEL` - LLM model name (default: demo)
- `--base-dir PATH` - Base directory for Body
- `--max-cycles N` - Maximum cycles to run (default: 30)

**Example:**
```bash
python cli_orchestrator.py resume \
  --concepts my_concepts.json \
  --inferences my_inferences.json \
  --run-id abc123-def456 \
  --mode PATCH
```

**Reconciliation Modes:**
- **PATCH** (default): Smart merge - discard stale state, keep valid state
- **OVERWRITE**: Trust checkpoint 100%, ignore repo changes
- **FILL_GAPS**: Only fill missing values, prefer new repo defaults

### `fork` - Fork to Different Repository

Load state from one run, execute with a completely different repository. Useful for multi-stage pipelines.

**Required:**
- `--concepts FILE` - Path to NEW concepts JSON file
- `--inferences FILE` - Path to NEW inferences JSON file

**Optional:**
- `--from-run ID` - Source run ID to fork from (default: latest)
- `--new-run-id ID` - New run ID (default: auto-generate as fork-XXXXXXXX)
- `--mode MODE` - Reconciliation mode (default: OVERWRITE recommended for forking)
- `--inputs FILE` - Path to NEW inputs JSON file
- `--llm MODEL` - LLM model name (default: demo)
- `--base-dir PATH` - Base directory for Body
- `--max-cycles N` - Maximum cycles to run (default: 30)

**Example:**
```bash
# Stage 1: Run addition
python cli_orchestrator.py run \
  --concepts addition_concepts.json \
  --inferences addition_inferences.json \
  --inputs addition_inputs.json

# Note the run ID from output, e.g., "abc123-def456"

# Stage 2: Fork to combination (uses {new number pair} from addition)
python cli_orchestrator.py fork \
  --concepts combination_concepts.json \
  --inferences combination_inferences.json \
  --from-run abc123-def456 \
  --new-run-id my-combination-run
```

### `list-runs` - List All Runs

Display all available runs in the database.

**Example:**
```bash
python cli_orchestrator.py list-runs --db-path orchestration.db
```

**Output:**
```
1. Run ID: abc123-def456
   First Execution: 2025-11-30 10:00:00
   Last Execution: 2025-11-30 10:05:00
   Execution Count: 1
   Max Cycle: 50
```

### `list-checkpoints` - List Checkpoints

Display all checkpoints for a specific run or all runs.

**Optional:**
- `--run-id ID` - Filter by specific run ID

**Example:**
```bash
# All checkpoints
python cli_orchestrator.py list-checkpoints

# Specific run
python cli_orchestrator.py list-checkpoints --run-id abc123-def456
```

### `export` - Export Checkpoint

Export a checkpoint to a JSON file for backup or inspection.

**Optional:**
- `--run-id ID` - Run ID to export (default: latest)
- `--cycle N` - Specific cycle number (default: latest)
- `--inference-count N` - Specific inference count within cycle
- `--output FILE` - Output file path (default: auto-generate)

**Example:**
```bash
# Export latest checkpoint
python cli_orchestrator.py export --run-id abc123-def456

# Export specific checkpoint
python cli_orchestrator.py export \
  --run-id abc123-def456 \
  --cycle 25 \
  --inference-count 5 \
  --output my_checkpoint.json
```

## Global Options

Available for all commands:

- `--db-path FILE` - Path to checkpoint database (default: orchestration.db)
- `--verbose` or `-v` - Enable verbose logging (DEBUG level)

## Examples

### Example 1: Complete Addition Workflow

```bash
# Run the addition example
python cli_orchestrator.py run \
  --concepts infra/examples/add_examples/repo/addition_concepts.json \
  --inferences infra/examples/add_examples/repo/addition_inferences.json \
  --inputs infra/examples/add_examples/repo/addition_inputs.json \
  --llm qwen-plus \
  --max-cycles 50 \
  --db-path my_runs.db

# Output will show: Run ID: <some-uuid>
```

### Example 2: Multi-Stage Pipeline (Addition → Combination)

```bash
# Stage 1: Addition
python cli_orchestrator.py run \
  --concepts addition_concepts.json \
  --inferences addition_inferences.json \
  --inputs addition_inputs.json \
  --db-path pipeline.db

# Note the run ID: addition-run-001

# Stage 2: Combination (fork from addition)
python cli_orchestrator.py fork \
  --concepts combination_concepts.json \
  --inferences combination_inferences.json \
  --from-run addition-run-001 \
  --new-run-id combination-run-001 \
  --db-path pipeline.db
```

### Example 3: Resume Interrupted Run

```bash
# Original run was interrupted
python cli_orchestrator.py run \
  --concepts my_concepts.json \
  --inferences my_inferences.json \
  --run-id interrupted-run

# Resume from where it left off
python cli_orchestrator.py resume \
  --concepts my_concepts.json \
  --inferences my_inferences.json \
  --run-id interrupted-run \
  --mode PATCH
```

### Example 4: Debugging with Verbose Output

```bash
python cli_orchestrator.py run \
  --concepts my_concepts.json \
  --inferences my_inferences.json \
  --verbose
```

### Example 5: Export and Backup

```bash
# Export latest checkpoint for backup
python cli_orchestrator.py export \
  --run-id production-run-001 \
  --output backups/checkpoint_$(date +%Y%m%d).json

# List all checkpoints first
python cli_orchestrator.py list-checkpoints --run-id production-run-001

# Export specific checkpoint
python cli_orchestrator.py export \
  --run-id production-run-001 \
  --cycle 42 \
  --output backups/checkpoint_c42.json
```

## Scripting and Automation

### Bash Script Example

```bash
#!/bin/bash
# multi_stage_pipeline.sh

DB="pipeline_$(date +%Y%m%d).db"

# Stage 1: Data loading
echo "Stage 1: Loading data..."
RUN1=$(python cli_orchestrator.py run \
  --concepts load_concepts.json \
  --inferences load_inferences.json \
  --inputs data.json \
  --db-path "$DB" | grep "Run ID:" | cut -d: -f2 | tr -d ' ')

if [ -z "$RUN1" ]; then
  echo "Stage 1 failed"
  exit 1
fi

echo "Stage 1 complete: $RUN1"

# Stage 2: Processing (fork from stage 1)
echo "Stage 2: Processing..."
RUN2=$(python cli_orchestrator.py fork \
  --concepts process_concepts.json \
  --inferences process_inferences.json \
  --from-run "$RUN1" \
  --db-path "$DB" | grep "Run ID:" | cut -d: -f2 | tr -d ' ')

if [ -z "$RUN2" ]; then
  echo "Stage 2 failed"
  exit 1
fi

echo "Stage 2 complete: $RUN2"

# Export final checkpoint
python cli_orchestrator.py export \
  --run-id "$RUN2" \
  --output "results/final_$(date +%Y%m%d_%H%M%S).json" \
  --db-path "$DB"

echo "Pipeline complete!"
```

### PowerShell Script Example

```powershell
# multi_stage_pipeline.ps1

$DB = "pipeline_$(Get-Date -Format 'yyyyMMdd').db"

# Stage 1
Write-Host "Stage 1: Loading data..."
$output = python cli_orchestrator.py run `
  --concepts load_concepts.json `
  --inferences load_inferences.json `
  --inputs data.json `
  --db-path $DB

$RUN1 = ($output | Select-String "Run ID:" | ForEach-Object { $_.ToString().Split(':')[1].Trim() })

if (-not $RUN1) {
    Write-Error "Stage 1 failed"
    exit 1
}

Write-Host "Stage 1 complete: $RUN1"

# Stage 2
Write-Host "Stage 2: Processing..."
$output = python cli_orchestrator.py fork `
  --concepts process_concepts.json `
  --inferences process_inferences.json `
  --from-run $RUN1 `
  --db-path $DB

$RUN2 = ($output | Select-String "Run ID:" | ForEach-Object { $_.ToString().Split(':')[1].Trim() })

if (-not $RUN2) {
    Write-Error "Stage 2 failed"
    exit 1
}

Write-Host "Stage 2 complete: $RUN2"

# Export
python cli_orchestrator.py export `
  --run-id $RUN2 `
  --output "results/final_$(Get-Date -Format 'yyyyMMdd_HHmmss').json" `
  --db-path $DB

Write-Host "Pipeline complete!"
```

## Comparison: CLI vs Streamlit App

| Feature | CLI | Streamlit App |
|---------|-----|---------------|
| **Fresh Run** | ✅ `run` command | ✅ Fresh Run option |
| **Resume** | ✅ `resume` command | ✅ Resume option |
| **Fork** | ✅ `fork` command | ✅ Fork from Checkpoint |
| **List Runs** | ✅ `list-runs` | ✅ History tab |
| **List Checkpoints** | ✅ `list-checkpoints` | ✅ In UI when resuming |
| **Export** | ✅ `export` command | ✅ Download buttons |
| **Scripting** | ✅ Perfect for automation | ❌ Not designed for automation |
| **Visual Interface** | ❌ Terminal only | ✅ Beautiful web UI |
| **Real-time Progress** | ✅ Logs to console | ✅ Progress bar |
| **Results Visualization** | ⚠️ Text output | ✅ Tables and metrics |

**Use CLI when:**
- Automating workflows
- Running in CI/CD pipelines
- SSH/remote server environments
- Scripting multi-stage pipelines
- You prefer terminal interfaces

**Use Streamlit App when:**
- Interactive exploration
- Visualizing results
- Demonstrating to others
- Prefer graphical interfaces
- Need real-time progress visualization

## Troubleshooting

### "No module named 'infra'"

Ensure you're running from the project root or that the project root is in your PYTHON_PATH:

```bash
cd /path/to/normCode
python cli_orchestrator.py run ...
```

### "FileNotFoundError: concepts.json"

Use absolute paths or ensure files are in current directory:

```bash
python cli_orchestrator.py run \
  --concepts $(pwd)/path/to/concepts.json \
  --inferences $(pwd)/path/to/inferences.json
```

### "No checkpoint found"

List available runs and checkpoints:

```bash
python cli_orchestrator.py list-runs
python cli_orchestrator.py list-checkpoints
```

### Verbose Debugging

Add `--verbose` to see detailed logs:

```bash
python cli_orchestrator.py run --verbose --concepts ...
```

## Best Practices

1. **Use meaningful database names** for different projects:
   ```bash
   --db-path projects/my_project.db
   ```

2. **Specify custom run IDs** for easier tracking:
   ```bash
   --new-run-id my-project-v2-$(date +%Y%m%d)
   ```

3. **Export important checkpoints** for backup:
   ```bash
   python cli_orchestrator.py export --run-id important-run --output backups/
   ```

4. **Use consistent reconciliation modes**:
   - PATCH for same repo, bug fixes
   - OVERWRITE for forking between different repos
   - FILL_GAPS for partial imports

5. **Script multi-stage pipelines** for repeatability

6. **Monitor with verbose mode** during development:
   ```bash
   python cli_orchestrator.py run --verbose ... 2>&1 | tee execution.log
   ```

---

**Version**: 1.0  
**Date**: November 30, 2025  
**Related**: `launch_streamlit_app.py`, `streamlit_app/app.py`

