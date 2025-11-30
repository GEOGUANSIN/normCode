# NormCode Orchestrator - Streamlit App

A minimal web interface for running NormCode orchestrations without writing code.

## 🚀 Quick Start

### 1. Install Streamlit

```bash
pip install streamlit
```

### 2. Launch the App

From the project root:
```bash
cd streamlit_app
streamlit run app.py
```

Or use the launcher:
```bash
cd streamlit_app
python run_app.py
```

The app will open at `http://localhost:8501` 🎉

## 📚 Documentation

- **[QUICK_START_APP.md](QUICK_START_APP.md)** - Get running in 60 seconds
- **[STREAMLIT_APP_GUIDE.md](STREAMLIT_APP_GUIDE.md)** - Complete user guide with examples
- **[APP_ARCHITECTURE.md](APP_ARCHITECTURE.md)** - Technical architecture
- **[APP_SUMMARY.md](APP_SUMMARY.md)** - Implementation overview
- **[LOGGING_FEATURES_UPDATE.md](LOGGING_FEATURES_UPDATE.md)** - v1.1 logging features *(NEW)*

## ✨ Features

- 📁 **Upload Repository Files** - Load concepts, inferences, and inputs from JSON
- 🚀 **Execute Orchestrations** - Run with configurable LLM models and parameters
- 💾 **Checkpoint & Resume** - Save and restore execution state (PATCH/OVERWRITE/FILL_GAPS modes)
- 📊 **View Results** - Explore final concepts and their values
- 📜 **Browse History** - See all past runs and checkpoints
- 📋 **Access Logs** - View detailed execution logs with filtering and export *(NEW in v1.1)*
- 💾 **Export Results** - Download outputs and logs as JSON

## 📋 What You Need

Three JSON files (examples in `../infra/examples/add_examples/repo/`):

1. **concepts.json** - Concept definitions
2. **inferences.json** - Inference steps
3. **inputs.json** - Initial values (optional)

See `sample_inputs.json` for the input file format.

## 🎯 Example Workflow

### Running the Addition Example

1. Launch the app: `streamlit run app.py`

2. Upload files from `../infra/examples/add_examples/repo/`:
   - `addition_concepts.json`
   - `addition_inferences.json`
   - Create an `inputs.json` (or use `sample_inputs.json` as template)

3. Configure:
   - LLM Model: `qwen-plus`
   - Max Cycles: `50`
   - Base Directory: `App Directory (default)` or choose where to store generated files
   - Mode: `Fresh Run`

4. Click **▶️ Start Execution**

5. View results in the **Results** tab

### Combining from Checkpoint

After the addition example completes:

1. Upload:
   - `combination_concepts.json`
   - `combination_inferences.json`

2. Configure:
   - Mode: `Resume (PATCH)`

3. Execute - the app will load `{new number pair}` from the previous checkpoint!

## 🛠️ Files in This Directory

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application (v1.1 with logging) |
| `run_app.py` | Python launcher (checks dependencies) |
| `run_app.bat` | Windows batch launcher |
| `run_app.ps1` | PowerShell launcher |
| `sample_inputs.json` | Example input file format |
| `README.md` | This file |
| `QUICK_START_APP.md` | 60-second quick start guide |
| `STREAMLIT_APP_GUIDE.md` | Comprehensive user guide |
| `APP_ARCHITECTURE.md` | Technical architecture docs |
| `APP_SUMMARY.md` | Implementation summary |
| `LOGGING_FEATURES_UPDATE.md` | v1.1 logging features documentation |

## 💡 Tips

- **Use PATCH mode** - Safest for resuming with changed repositories
- **Check the Help tab** - Built-in documentation in the app
- **View execution logs** - Debug issues by viewing detailed logs in Results or History tabs
- **Filter logs** - Use cycle or status filters to find specific execution details
- **Export results & logs** - Download JSON backups of executions and logs
- **Browse history** - See all runs, checkpoints, and logs in the History tab

## 🆘 Troubleshooting

### "streamlit: command not found"
```bash
pip install streamlit
```

### "No module named 'infra'"
Make sure you're running from the `streamlit_app` directory (this directory).

### "Database not found"
Normal on first run - the database is created automatically.

## 🔗 Related Documentation

- **Orchestration Engine**: `../infra/_orchest/README.md`
- **Repository Compatibility**: `../infra/_orchest/REPO_COMPATIBILITY.md`
- **Example Scripts**: `../infra/examples/add_examples/`

---

**Ready to orchestrate!** 🎉

