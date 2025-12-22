# Custom Run Name Feature - Complete Implementation

## Overview
This feature allows users to specify custom run names/IDs when creating runs, and automatically loads these values when loading configurations from previous runs.

## Changes Summary

### 1. Fresh Run Mode
**UI Changes:**
- Added "Run Name/ID (optional)" text input field
- Pre-populates from loaded config (`custom_run_id` field)
- Shows "(Loaded from previous run)" in help text when loaded

**Backend Changes:**
- Passes `custom_run_id` to Orchestrator constructor
- Saves `custom_run_id` in config metadata (line 854)
- Loads `custom_run_id` from config when loading previous runs (line 554)

### 2. Fork from Checkpoint Mode
**UI Changes:**
- "Run ID to Resume" field pre-populates from `forked_from_run_id` (line 568)
- "New Run ID (optional)" field pre-populates from `new_run_id` (line 584)
- Both show "(Loaded from previous run)" in help text when loaded

**Backend Changes:**
- Saves `forked_from_run_id` in config metadata (line 910)
- Saves `new_run_id` in config metadata (line 919)
- Loads both values when loading previous runs

### 3. Resume from Checkpoint Mode
**UI Changes:**
- "Run ID to Resume" field pre-populates from `resumed_from_run_id` (line 570)
- Shows "(Loaded from previous run)" in help text when loaded

**Backend Changes:**
- Saves `resumed_from_run_id` in config metadata (line 981)
- Loads value when loading previous runs

## Config Metadata Fields

### Fresh Run
```json
{
  "custom_run_id": "my-custom-name" or null
}
```

### Fork from Checkpoint
```json
{
  "forked_from_run_id": "source-run-id",
  "new_run_id": "my-fork-name" or null
}
```

### Resume from Checkpoint
```json
{
  "resumed_from_run_id": "run-to-resume" or null
}
```

## User Experience Flow

### Scenario 1: Fresh Run with Custom Name
1. User enters custom name "experiment-001"
2. Run executes → Config saved with `custom_run_id: "experiment-001"`
3. Later, user loads that config → Field pre-populated with "experiment-001"
4. User can use same name or modify it

### Scenario 2: Fork from Checkpoint
1. User selects Fork mode
2. Loads config from previous fork
3. "Run ID to Resume" → Pre-populated with "source-run-id"
4. "New Run ID" → Pre-populated with "my-fork-name"
5. User can modify either field or execute as-is

### Scenario 3: Resume from Checkpoint
1. User selects Resume mode
2. Loads config from previous resume
3. "Run ID to Resume" → Pre-populated with "run-to-resume"
4. User can change or execute as-is

## Benefits

1. **Complete Config Replication**: Loading a config now restores ALL settings including run IDs
2. **Faster Workflow**: No need to remember or look up run IDs
3. **Fewer Errors**: Pre-populated fields reduce typos
4. **Better Organization**: Custom names make it easier to identify and reload experiments

## Code Locations

- **UI Input Fields**: Lines 551-593
- **Fresh Run Config Save**: Lines 836-856
- **Fork Config Save**: Lines 900-922
- **Resume Config Save**: Lines 970-984

## Testing Checklist

- [x] Fresh Run with custom name saves correctly
- [x] Fresh Run config loading pre-populates custom name
- [x] Fork mode saves both forked_from and new_run_id
- [x] Fork mode config loading pre-populates both fields
- [x] Resume mode saves resumed_from_run_id
- [x] Resume mode config loading pre-populates field
- [x] Empty/null values handled gracefully
- [x] No linter errors

## Status
✅ **COMPLETE** - All functionality implemented and tested

