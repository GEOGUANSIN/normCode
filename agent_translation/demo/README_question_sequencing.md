# Question Sequencing Agent Demo

This script demonstrates the QuestionSequencingAgent (Phase 1) functionality for deconstructing natural language instructions into structured question sequences using NormCode terminology.

## Features

- **Natural Language Processing**: Convert natural language instructions into structured question sequences
- **NormCode Integration**: Uses NormCode terminology for precise question generation
- **Multiple LLM Support**: Works with cloud APIs (DeepSeek, OpenAI) or local LLMs (Ollama)
- **Interactive Mode**: Command-line interface for easy testing
- **Context-Aware**: Loads NormCode terminology for improved accuracy

## Quick Start

### 1. Basic Usage

```bash
# Process a single instruction
python question_sequencing_demo.py "Create a user account with email and password"

# Run in interactive mode
python question_sequencing_demo.py
```

### 2. Configuration

Copy the `settings.yaml` file to your project root and add your API keys:

```yaml
deepseek-v3:
  DASHSCOPE_API_KEY: "your_actual_api_key_here"
```

### 3. Command Line Options

```bash
# Use local LLM (Ollama)
python question_sequencing_demo.py "Create a user account" --local

# Disable NormCode context
python question_sequencing_demo.py "Create a user account" --no-context

# Combine options
python question_sequencing_demo.py "Create a user account" --local --no-context
```

## Example Output

```
Processing instruction: Create a user account with email and password

============================================================
MAIN QUESTION
============================================================
Type: how
Target: {main_process}
Condition: @by
Question: $how?({main_process}, @by)

============================================================
ENSuing QUESTIONS
============================================================
Chunk 1 (Index 0):
  Question: $what?({chunk_0}, $=)
  Answer: Create a user account with email and password

============================================================
METADATA
============================================================
original_text: Create a user account with email and password
text_length: 47
chunk_count: 1
main_question_type: how
processing_timestamp: 2024-01-01T00:00:00Z
decomposition_version: 1.0
llm_used: True
prompt_database_used: True
prompt_context_provided: True
```

## Architecture

The script integrates several components:

```
LLMFactory (LLM Client)
    ↓
PromptDatabase (Prompt Management)
    ↓
QuestionSequencingAgent (Phase 1 Processing)
    ↓
NormCode Terminology Context (Domain Knowledge)
```

### Components

1. **LLMFactory**: Manages LLM client connections (cloud or local)
2. **PromptManager**: Handles prompt templates and database
3. **QuestionSequencingAgent**: Core processing agent
4. **NormCode Context**: Terminology and syntax reference

## Setup Options

### Cloud LLM Setup

1. Get API key from your preferred provider (DeepSeek, OpenAI, etc.)
2. Update `settings.yaml` with your API key
3. Run the script normally

### Local LLM Setup (Ollama)

1. Install Ollama: https://ollama.ai/
2. Pull a model: `ollama pull llama3.1:8b`
3. Run with `--local` flag

### Mock Mode

If no LLM is configured, the script runs in mock mode using fallback logic.

## Test Cases

The script can handle various types of instructions:

### Process Instructions
```bash
python question_sequencing_demo.py "Create a user account with email and password"
# Expected: how-type question with @by condition
```

### Definition Instructions
```bash
python question_sequencing_demo.py "What is a user account?"
# Expected: what-type question with $= condition
```

### Conditional Instructions
```bash
python question_sequencing_demo.py "When should the account be activated?"
# Expected: when-type question with @if condition
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running from the `agent_translation` directory
2. **API Key Errors**: Check your `settings.yaml` configuration
3. **Local LLM Connection**: Ensure Ollama is running on `localhost:11434`

### Debug Mode

Enable debug logging by modifying the script:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Integration with Other Agents

This script demonstrates Phase 1 of the NormCode generation process. The output can be used as input for:

- **Phase 2**: In-Question Analysis Agent
- **Phase 3**: NormCode Integration Agent

## File Structure

```
agent_translation/
├── question_sequencing_demo.py    # This script
├── settings.yaml                  # Configuration file
├── LLMFactory.py                  # LLM client factory
├── prompt_database.py             # Prompt management
├── phase_agent/
│   └── question_sequencing_agent.py  # Core agent
└── NormCode_terms/                # Terminology files
```

## Contributing

To extend the functionality:

1. Add new prompt templates to the prompt database
2. Enhance the NormCode terminology context
3. Implement additional question types in the agent
4. Add support for more LLM providers

## License

This script is part of the NormCode project and follows the same licensing terms. 