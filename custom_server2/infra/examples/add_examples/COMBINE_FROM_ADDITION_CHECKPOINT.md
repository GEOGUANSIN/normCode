# Running Combination Repository from Addition Checkpoint

This demonstrates how to run the **combination repository** (`ex_combine_standalone.py`) using data from an **addition checkpoint** (`ex_add_complete_code_with_checkpoint_meta.py`).

## Overview

The addition repository produces `{new number pair}` as its final output. The combination repository takes `{new number pair}` as input (ground concept) and combines all digits to produce `{sum}`.

This demonstrates **cross-repository checkpoint resumption** - using state from one repository to initialize another.

## Workflow

1. **Run Addition Example** → Creates checkpoint with `{new number pair}` data
2. **Run Combination Example** → Loads `{new number pair}` from checkpoint → Produces `{sum}`

## Step-by-Step Usage

### Step 1: Run Addition Example

First, run the addition example to create a checkpoint:

```bash
cd infra/examples/add_examples
python ex_add_complete_code_with_checkpoint_meta.py --number1 "123" --number2 "98" --db-path orchestration_checkpoint.db
```

This will:
- Create a checkpoint database (`orchestration_checkpoint.db`)
- Produce `{new number pair}` as the final result
- Save the checkpoint with `{new number pair}` data

**Note the Run ID** from the output (or use `--run-id` to specify one).

### Step 2: List Available Checkpoints (Optional)

Check what checkpoints are available:

```bash
# List all runs
python ex_combine_standalone.py --list-runs --db-path orchestration_checkpoint.db

# List checkpoints for a specific run
python ex_combine_standalone.py --list-checkpoints --run-id <run-id> --db-path orchestration_checkpoint.db
```

### Step 3: Run Combination from Checkpoint

Run the combination example, loading `{new number pair}` from the addition checkpoint:

```bash
# Use latest checkpoint from latest run
python ex_combine_standalone.py --resume --db-path orchestration_checkpoint.db

# Use specific run ID
python ex_combine_standalone.py --resume --run-id <addition-run-id> --db-path orchestration_checkpoint.db

# Use specific checkpoint (by cycle)
python ex_combine_standalone.py --resume --run-id <addition-run-id> --cycle 5 --db-path orchestration_checkpoint.db
```

## Reconciliation Modes

The `--mode` parameter controls how checkpoint state is applied:

- **`FILL_GAPS`** (default): Only fills concepts that are empty in the combination repo. Perfect for this use case - only `{new number pair}` will be filled from checkpoint.
- **`PATCH`**: Smart merge - compares signatures, keeps valid state, discards stale state. Useful if concepts have changed.
- **`OVERWRITE`**: Trusts checkpoint completely. Use with caution.

Example with mode:

```bash
python ex_combine_standalone.py --resume --mode FILL_GAPS --db-path orchestration_checkpoint.db
```

## How It Works

### 1. Signature-Based Compatibility

When loading the checkpoint:
- The system compares concept signatures between the addition checkpoint and combination repository
- `{new number pair}` exists in both repos, so its data can be transferred
- Other concepts are ignored (they're specific to each repo)

### 2. Data Transfer

- The combination repo clears `{new number pair}` reference_data when `--resume` is used
- This makes it "empty" in the new repo
- `FILL_GAPS` mode fills it from the checkpoint
- The combination repo then uses this data as input

### 3. Execution Flow

```
Addition Repo:
  {number pair} → [addition logic] → {new number pair} ✓ (saved to checkpoint)

Combination Repo:
  {new number pair} (from checkpoint) → [grouping] → {number digits} → [combine] → {sum} ✓
```

## Example Output

When running with `--resume`, you should see:

```
=== Starting Standalone Combine Demo ===
Resuming from checkpoint: orchestration_checkpoint.db
  Run ID: latest
  Mode: FILL_GAPS
✓ Successfully loaded {new number pair} from checkpoint
  Data shape: (...)
  Data axes: ['number pair', 'remainder explanation', ...]
Starting execution...
...
SUCCESS: Final Sum Calculated: [result]
```

## Troubleshooting

### "Checkpoint database not found"
- Make sure you ran the addition example first
- Check the `--db-path` matches the path used in addition example

### "{new number pair} not found in checkpoint"
- The addition run may not have completed successfully
- Check the addition checkpoint has `{new number pair}` marked as complete
- Try using `--list-checkpoints` to verify checkpoint contents

### "Repository compatibility validation found errors"
- The `{new number pair}` concept definition may differ between repos
- Check that both repos define `{new number pair}` with compatible structure
- Try using `--mode OVERWRITE` (with caution) if definitions are intentionally different

## Key Concepts Demonstrated

1. **Cross-Repository Checkpoint Resumption**: Using state from one repo to initialize another
2. **Signature-Based Compatibility**: Automatic detection of compatible concepts
3. **Reconciliation Modes**: Flexible control over how checkpoint state is applied
4. **Data Sufficiency**: Ensuring ground concepts have data before execution

This demonstrates the power of the NormCode orchestration system's checkpoint compatibility features!

