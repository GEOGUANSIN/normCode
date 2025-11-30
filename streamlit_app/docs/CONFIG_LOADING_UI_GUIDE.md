# Configuration Loading - UI Guide

## Visual Walkthrough

### 1. Loading Configuration (Sidebar)

```
┌─────────────────────────────────────────────┐
│ ⚙️ Configuration                            │
├─────────────────────────────────────────────┤
│                                             │
│ 📋 Load Previous Config                     │
│                                             │
│ Load settings from:                         │
│ ┌─────────────────────────────────────────┐ │
│ │ abc12345678... (2025-11-30 10:30)     ▼ │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ ┌───────────────┐  ┌───────────────────┐   │
│ │ 🔄 Load Config│  │ 👁️ Preview      │   │
│ └───────────────┘  └───────────────────┘   │
│                                             │
│ ✅ Config loaded from: `abc12345...`        │
│ ┌───────────────────────────────────────┐   │
│ │   🗑️ Clear Loaded Config             │   │
│ └───────────────────────────────────────┘   │
│                                             │
├─────────────────────────────────────────────┤
│ 📁 Repository Files                         │
│ ...                                         │
└─────────────────────────────────────────────┘
```

### 2. Auto-populated Runtime Settings

```
┌─────────────────────────────────────────────┐
│ 🔧 Runtime Settings                         │
├─────────────────────────────────────────────┤
│                                             │
│ LLM Model                                   │
│ ┌─────────────────────────────────────────┐ │
│ │ gpt-4o                              ▼  │ │  ← Loaded!
│ └─────────────────────────────────────────┘ │
│ ℹ️ Loaded from previous run                 │
│                                             │
│ Max Cycles                                  │
│ ┌─────────────────────────────────────────┐ │
│ │ 100                                     │ │  ← Loaded!
│ └─────────────────────────────────────────┘ │
│ ℹ️ Loaded from previous run                 │
│                                             │
│ Base Directory                              │
│ ◉ App Directory (default)  ← Loaded!        │
│ ○ Project Root                              │
│ ○ Custom Path                               │
│                                             │
└─────────────────────────────────────────────┘
```

### 3. Configuration Preview Modal

```
When you click "👁️ Preview":

┌─────────────────────────────────────────────────┐
│ Configuration Details                         ▼ │
├─────────────────────────────────────────────────┤
│ {                                               │
│   "llm_model": "gpt-4o",                       │
│   "max_cycles": 100,                           │
│   "base_dir": "/path/to/streamlit_app",        │
│   "base_dir_option": "App Directory (default)",│
│   "agent_frame_model": "demo",                 │
│   "resume_mode": "Fresh Run",                  │
│   "verify_files": true,                        │
│   "app_version": "1.3"                         │
│ }                                               │
└─────────────────────────────────────────────────┘
```

### 4. History Tab - Configuration Display

```
┌─────────────────────────────────────────────────────┐
│ 🔖 abc123456789...                               ▼  │
├─────────────────────────────────────────────────────┤
│                                                     │
│ First Execution: 2025-11-30 10:30:15                │
│ Execution Count: 25                                 │
│ Last Execution: 2025-11-30 10:35:42                 │
│ Max Cycle: 3                                        │
│                                                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Run Configuration:                                  │
│                                                     │
│ 🤖 LLM Model: `gpt-4o`         📂 Base Dir: `...app`│
│ 🔄 Max Cycles: `100`           🔧 Reconciliation:   │
│ ▶️ Mode: `Fresh Run`                `PATCH`         │
│                                                     │
│ View Full Configuration                          ▼  │
│ ┌─────────────────────────────────────────────────┐ │
│ │ {                                               │ │
│ │   "llm_model": "gpt-4o",                       │ │
│ │   "max_cycles": 100,                           │ │
│ │   ...                                           │ │
│ │ }                                               │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
├─────────────────────────────────────────────────────┤
│ Checkpoints: 5                                      │
│ ...                                                 │
└─────────────────────────────────────────────────────┘
```

## User Interaction Flow

### Scenario 1: Quick Re-run

```
User Action                     App Response
───────────────────────────────────────────────────────
1. Select previous run         → Highlights selection
   from dropdown

2. Click "🔄 Load Config"      → ✅ Success message
                                → Settings populate below
                                → Shows loaded indicator

3. Upload repository files     → Files ready

4. Click "Start Execution"     → Executes with loaded config
```

### Scenario 2: Compare Repositories

```
User Action                     App Response
───────────────────────────────────────────────────────
1. Load config from Run A      → Settings from Run A populate

2. Upload Repository B files   → Different repo, same config

3. Execute                     → Fair comparison!
```

### Scenario 3: Configuration Templates

```
User Action                     App Response
───────────────────────────────────────────────────────
1. Create "fast_run" template  → Execute once, config saved
   - qwen-turbo, 30 cycles

2. Later: Load "fast_run"      → Fast settings populate
   config

3. Upload new repository       → Execute with fast settings

4. Create "deep_run" template  → Execute once, config saved
   - gpt-4o, 100 cycles

5. Later: Load "deep_run"      → Deep settings populate
   config

6. Upload same repository      → Execute with deep settings
```

## UI Elements

### Dropdown Options Format
```
-- Select a previous run --        ← Placeholder
abc12345678... (2025-11-30 10:30) ← Run ID + Timestamp
def98765432... (2025-11-29 15:20)
ghi55667788... (2025-11-28 09:10)
```

### Success Indicators
```
✓ Loaded config from abc12345...   ← After loading
📌 Config loaded from: `abc12345...` ← Active indicator
```

### Help Text
```
ℹ️ Loaded from previous run        ← On form fields
```

### Buttons
```
┌─────────────────┐
│ 🔄 Load Config  │  ← Primary action
└─────────────────┘

┌─────────────────┐
│ 👁️ Preview      │  ← Secondary action
└─────────────────┘

┌───────────────────────────────────┐
│   🗑️ Clear Loaded Config         │  ← Reset action
└───────────────────────────────────┘
```

## Color Coding (Streamlit Default)

- **Success**: Green background for loaded indicator
- **Info**: Blue background for help text
- **Warning**: Yellow background for missing metadata
- **Error**: Red background for errors

## Responsive Behavior

### Desktop (Wide Screen)
- Buttons side-by-side: [Load Config] [Preview]
- Config summary in two columns
- Full JSON visible in expanders

### Mobile (Narrow Screen)
- Buttons stack vertically
- Config summary stacks
- JSON scrollable in expanders

## Accessibility

- All buttons have clear labels
- Icons supplement text (not replace)
- Help text provides context
- Preview before action (non-destructive)
- Clear loaded status

## Error States

### No Previous Runs
```
┌─────────────────────────────────────────┐
│ ℹ️ No previous runs with                │
│    configurations found                 │
└─────────────────────────────────────────┘
```

### Database Not Found
```
┌─────────────────────────────────────────┐
│ ℹ️ Database not found. Run an           │
│    orchestration to create it.          │
└─────────────────────────────────────────┘
```

### No Metadata for Run
```
┌─────────────────────────────────────────┐
│ ℹ️ No configuration metadata            │
│    saved for this run                   │
└─────────────────────────────────────────┘
```

## Best Practices

### When to Use Load Config

✅ **DO**:
- Re-running same experiment
- Comparing different repositories
- Using proven configurations
- Quick setup for testing

❌ **DON'T**:
- When exploring new settings
- When requirements changed
- For completely different tasks

### Managing Configurations

1. **Create Templates**: Run once with optimal settings
2. **Name Meaningfully**: Use descriptive run_ids if possible
3. **Review Before Load**: Use Preview to verify
4. **Adjust as Needed**: Loaded config is editable
5. **Document Changes**: Note modifications in execution

## Tips & Tricks

### Quick Identification
- Use timestamps to find recent runs
- Most recent runs appear first
- Run_id prefix helps identify related runs

### Verification
- Always preview config before loading
- Check History tab for run details
- Verify settings after loading

### Workflow Integration
- Load → Verify → Adjust → Execute
- Keep "template" runs for reference
- Export important configurations

---

**UI Version**: v1.3  
**Platform**: Streamlit  
**Last Updated**: 2025-11-30

