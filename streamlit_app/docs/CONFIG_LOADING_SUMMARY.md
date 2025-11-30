# Configuration Loading Feature - Quick Summary

## What It Does

**Load and reuse configurations from previous runs** - No more manually re-entering settings!

## How to Use

### In 3 Steps:

1. **Select** a previous run from dropdown in sidebar
2. **Click** "🔄 Load Config" button  
3. **Execute** with auto-populated settings

## What Gets Loaded

✅ LLM Model  
✅ Max Cycles  
✅ Base Directory  
✅ All execution settings

❌ Repository files (still need to upload manually)

## Where to Find It

**Sidebar → "📋 Load Previous Config"**

## Common Use Cases

| Use Case | How |
|----------|-----|
| **Re-run same experiment** | Load config → Upload same files → Execute |
| **Compare repositories** | Load config from Run A → Upload Repo B files → Execute |
| **Consistent testing** | Load "template" config → Upload modified repo → Execute |

## Key Benefits

- 🚀 **Faster setup** - No manual re-entry
- 🎯 **Consistency** - Same settings across runs
- 📊 **Easy comparison** - Same config, different repos
- 🔄 **Reproducibility** - Exact same settings as before

## Example Workflow

```
1. Previous successful run used:
   - LLM: gpt-4o
   - Max Cycles: 100
   - Base Dir: App Directory
   
2. Load that configuration
   
3. Upload new repository files
   
4. Execute → Same settings, new repository!
```

## Configuration Saved Automatically

Every run now saves:
- LLM model
- Max cycles  
- Base directory
- Execution mode
- Advanced options
- Timestamps

View in **History Tab** for each run!

## Need More Info?

📖 See full documentation: `CONFIG_LOADING_FEATURE.md`

---

**Version 1.3** | Feature: Configuration Loading

