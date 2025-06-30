# Pipeline Agent Documentation

## Overview

The Pipeline Agent combines two phase agents to create a complete processing pipeline for instructive text:

1. **Phase 1: Question Sequencing Agent** - Deconstructs instructive text into question sequences
2. **Phase 2: In-Question Analysis Agent** - Analyzes each question-answer pair into formal NormCode structures

## Features

- **Complete Pipeline Processing**: Combines both phase agents in sequence
- **Unified Result Storage**: Stores all results in a single comprehensive JSON file
- **Comprehensive Metadata**: Tracks processing statistics and analysis summaries
- **Export Functionality**: Easy export to JSON files with custom naming
- **Verbose Logging**: Detailed progress reporting during processing

## Usage

### Basic Usage

```python
from pipeline_agent import PipelineAgent

# Initialize the pipeline agent
pipeline = PipelineAgent(verbose=True)

# Process instructive text
result = pipeline.process(
    norm_text="Your instructive text here...",
    save_result=True
)
```

### Advanced Usage

```python
from pipeline_agent import PipelineAgent

# Initialize with custom settings
pipeline = PipelineAgent(
    llm_model="qwen-turbo-latest",
    verbose=True
)

# Process with custom context
result = pipeline.process(
    norm_text="Your instructive text here...",
    prompt_context="Additional NormCode context...",
    save_result=True
)

# Get summary
summary = pipeline.get_pipeline_summary(result)
print(f"Processed {summary['question_pairs_processed']} question pairs")

# Export to custom location
export_path = pipeline.export_to_json(result, "custom_output.json")
```

## Pipeline Result Structure

The `PipelineResult` contains:

### Phase 1 Results (Question Decomposition)
- `main_question`: The primary question extracted from the text
- `ensuing_questions`: List of question-answer pairs from text chunks
- `decomposition_metadata`: Metadata about the decomposition process

### Phase 2 Results (Question Analysis)
- `question_analyses`: List of detailed analyses for each question-answer pair
  - Question structure analysis
  - Clause analysis
  - Three-phase NormCode drafts
  - Template mappings

### Pipeline Metadata
- `pipeline_metadata`: Comprehensive processing statistics
- `processing_timestamp`: When the pipeline was executed
- `input_text_hash`: Hash of the input text for tracking

## Example Output Structure

```json
{
  "main_question": {
    "type": "how",
    "target": "create user account",
    "condition": "must provide valid email and password",
    "question": "$how(create user account, $=must provide valid email and password)"
  },
  "ensuing_questions": [
    {
      "question": "$what(email address, $=valid)",
      "answer": "A valid email address must be provided...",
      "chunk_index": 0
    }
  ],
  "question_analyses": [
    {
      "analysis_id": "main_question",
      "question_structure": { ... },
      "clause_analysis": { ... },
      "phase1_draft": { ... },
      "phase2_draft": { ... },
      "phase3_draft": { ... },
      "template_mappings": [ ... ],
      "analysis_metadata": { ... }
    }
  ],
  "pipeline_metadata": {
    "pipeline_version": "1.0",
    "input_text_length": 245,
    "main_question_type": "how",
    "question_pairs_count": 4,
    "total_analyses_count": 5,
    "analysis_summary": { ... }
  },
  "processing_timestamp": "2024-01-15T10:30:45.123456",
  "input_text_hash": "a1b2c3d4e5f6..."
}
```

## File Storage

Results are automatically saved to:
- `translate_agent/results/pipeline_complete_analysis_[hash]_[timestamp].json`

Additional exports can be created using:
- `pipeline.export_to_json(result, "custom_filename.json")`

## Testing

Run the test script to see the pipeline in action:

```bash
python test_pipeline.py
```

This will process a sample instructive text and display detailed results.

## Dependencies

- `base_agent.py` - Base agent framework
- `result_manager.py` - Result storage management
- `phase_agent/question_sequencing_agent.py` - Phase 1 agent
- `phase_agent/in_question_analysis_agent.py` - Phase 2 agent
- `prompt_manager.py` - Prompt management system

## Configuration

The pipeline agent supports the same configuration options as individual phase agents:

- `llm_client`: Custom LLM client
- `prompt_manager`: Custom prompt manager
- `result_manager`: Custom result manager
- `llm_model`: LLM model name (default: "qwen-turbo-latest")
- `verbose`: Enable verbose logging (default: False) 