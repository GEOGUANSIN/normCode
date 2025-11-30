# NormCode Orchestrator - Streamlit App

A minimal web interface for running the NormCode orchestration engine.

## Quick Start

### 1. Install Dependencies

```bash
pip install streamlit
```

### 2. Launch the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Features

- 📁 **Upload Repository Files** - Load concepts, inferences, and input data from JSON files
- 🚀 **Execute Orchestration** - Run the orchestrator with configurable settings
- 💾 **Checkpoint & Resume** - Save and restore execution state with multiple modes
- 📊 **View Results** - Explore final concepts and their values
- 📜 **History** - Browse past runs and checkpoints
- 💾 **Export Results** - Download results as JSON

## Usage

### Preparing Repository Files

You need at least two JSON files:

1. **concepts.json** - Concept definitions
2. **inferences.json** - Inference step definitions
3. **inputs.json** (optional) - Initial ground concept values

Example files can be found in:
```
infra/examples/add_examples/repo/
```

### Execution Modes

- **Fresh Run** - Start new execution
- **Resume (PATCH)** - Smart merge (recommended) - discards stale state
- **Resume (OVERWRITE)** - Trust checkpoint completely
- **Resume (FILL_GAPS)** - Only fill empty concepts

### Input File Format

```json
{
  "{concept name}": {
    "data": [[1, 2], [3, 4]],
    "axes": ["row", "col"]
  }
}
```

Or simplified:
```json
{
  "{concept name}": [1, 2, 3]
}
```

## Example Workflow

### Running the Addition Example

1. Upload files from `infra/examples/add_examples/repo/`:
   - `addition_concepts.json`
   - `addition_inferences.json`

2. Create an `inputs.json`:
   ```json
   {
     "{number pair}": {
       "data": [["%(123)", "%(98)"]],
       "axes": ["number pair", "number"]
     }
   }
   ```

3. Click "Start Execution"

4. View results in the Results tab

### Running the Combination Example

1. First run the addition example to create a checkpoint

2. Upload files from `infra/examples/add_examples/repo/`:
   - `combination_concepts.json`
   - `combination_inferences.json`

3. Select "Resume (PATCH)" mode

4. The `{new number pair}` will be loaded from the addition checkpoint

5. Click "Start Execution"

## Configuration

### LLM Models

Supported models:
- `qwen-plus` (default)
- `gpt-4o`
- `claude-3-sonnet`
- `qwen-turbo-latest`

### Database Path

Default: `orchestration.db` in the project root

Change this to use different databases for different projects.

## Troubleshooting

### "Database not found"
- The database is created automatically on first run
- Make sure the path is writable

### "Execution failed"
- Check that all required concepts are defined
- Verify input data format
- Review error message in the app

### "Checkpoint incompatible"
- Use PATCH mode to handle logic changes
- Or start a Fresh Run

## Documentation

- **Orchestration Guide**: `infra/_orchest/README.md`
- **Repository Compatibility**: `infra/_orchest/REPO_COMPATIBILITY.md`
- **Implementation Details**: `infra/_orchest/REPOSITORY_COMPATIBILITY_IMPLEMENTATION.md`

## Development

To modify the app:

1. Edit `app.py`
2. Save the file
3. Streamlit will auto-reload

For debugging, run with verbose logging:
```bash
streamlit run app.py --logger.level=debug
```

## License

Part of the NormCode project.

