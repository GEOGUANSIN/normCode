# NormCode Orchestrator - Streamlit App

A minimal web interface for running NormCode orchestrations without writing code.

## 🚀 Quick Start

### Run the App

```bash
# From project root
python launch_streamlit_app.py

# Or directly
cd streamlit_app
streamlit run app.py
```

### Basic Usage

1. Upload your repository files:
   - `*_concepts.json` - Concept definitions
   - `*_inferences.json` - Inference definitions
   - `*_inputs.json` (optional) - Initial concept data

2. Configure execution settings (LLM model, max cycles, etc.)
   - **NEW in v1.3.1**: Load complete setups (config + files + database)!

3. Choose execution mode:
   - **Fresh Run**: Start a new execution
   - **Resume**: Continue from a checkpoint
   - **Fork from Checkpoint**: Load data from one run, execute with a different repository

4. Click "▶️ Start Execution"

## 📚 Documentation

All detailed documentation is available in the [`docs/`](./docs/) directory:

- **[Quick Start Guide](./docs/QUICK_START_APP.md)** - Get started quickly
- **[Streamlit App Guide](./docs/STREAMLIT_APP_GUIDE.md)** - Complete user guide
- **[Forking Guide](./docs/FORKING_GUIDE.md)** - How to fork between repositories
- **[Complete Setup Loading](./COMPLETE_SETUP_LOADING.md)** - Load config + files + database (NEW in v1.3.1)
- **[Configuration Loading](./docs/CONFIG_LOADING_FEATURE.md)** - Load settings from previous runs (v1.3)
- **[App Architecture](./docs/APP_ARCHITECTURE.md)** - Technical architecture
- **[Changelog](./docs/CHANGELOG.md)** - Version history

### Key Features

- ✅ Upload and execute repositories via web UI
- ✅ **Load complete setups: config + files + database** (NEW in v1.3.1)
  - One-click reload of entire previous runs
  - Automatic file saving and retrieval
  - No need to re-upload repository files
- ✅ Resume from checkpoints
- ✅ Fork between different repositories
- ✅ View execution history and results with detailed configuration
- ✅ Export checkpoints and logs

## Requirements

- Python 3.8+
- Streamlit: `pip install streamlit`
- All dependencies from project root

## Support

For issues or questions, see the documentation in [`docs/`](./docs/) or check the project's main README.

