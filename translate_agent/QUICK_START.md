# Quick Start: Running the NormCode Translation Agent

## Prerequisites

1. **Python 3.7+** installed
2. **API Access** configured for your preferred LLM model
3. **Dependencies** installed (see requirements below)

## Installation

1. Navigate to the `translate_agent` directory:
   ```bash
   cd translate_agent
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Translation Agent

### Option 1: Interactive Script (Recommended for beginners)

```bash
python run_translation.py
```

This will:
- Prompt you to enter text (or use sample text if you press Enter)
- Show detailed processing steps
- Display comprehensive results
- Save results to JSON files

### Option 2: Command Line Script (Quick translations)

```bash
python simple_translate.py "Your instructive text here"
```

Example:
```bash
python simple_translate.py "To create an account, provide email and password"
```

This will:
- Process the text immediately
- Show only the final NormCode translations
- Save results automatically

### Option 3: Test Script (See full pipeline in action)

```bash
python test_pipeline.py
```

This runs a predefined example with detailed output.

## Example Usage

### Input Text:
```
To create a user account, you must provide a valid email address and choose a strong password. 
The password must be at least 8 characters long and contain at least one uppercase letter, 
one lowercase letter, and one number.
```

### Output (NormCode):
```
$how(create user account, @by(provide email address, $=valid) @by(choose password, $=strong))
$what(password, $=at least 8 characters @onlyIf(contain, $=uppercase letter) @onlyIf(contain, $=lowercase letter) @onlyIf(contain, $=number))
```

## Configuration

### Changing the LLM Model

Edit the model name in the script:
```python
pipeline = PipelineAgent(
    llm_model="your-model-name",  # Change this
    verbose=True
)
```

Common models:
- `qwen-turbo-latest` (default)
- `deepseek-r1`
- `gpt-4`
- `claude-3`

### API Configuration

Make sure your API credentials are configured in your environment or configuration files.

## Output Files

Results are automatically saved to:
- `results/pipeline_complete_analysis_[hash]_[timestamp].json`
- `results/pipeline_export_[hash]_[timestamp].json`

## Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure you're running from the `translate_agent` directory
2. **API Errors**: Check your API credentials and model access
3. **Missing Dependencies**: Run `pip install -r requirements.txt`

### Getting Help:

- Check the detailed documentation in `README_Pipeline.md`
- Look at example outputs in the `results/` directory
- Review the test script for usage patterns

## What the Agent Does

The translation agent performs a two-phase process:

1. **Phase 1**: Breaks down instructive text into question-answer pairs
2. **Phase 2**: Converts each pair into formal NormCode syntax

The result is a structured representation that can be used for:
- Formal reasoning
- Code generation
- Process automation
- Knowledge representation 