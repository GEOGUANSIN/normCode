# Phase Agent Architecture - Simple Explanation

## Overview

The Phase Agent system is a modular framework for processing natural language instructions into structured question sequences. It uses Large Language Models (LLMs) to break down complex instructions into manageable, answerable questions.

## 🏗️ Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase Agent System                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Base Agent  │    │ Prompt      │    │ Result      │     │
│  │ Framework   │    │ Manager     │    │ Manager     │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
├─────────────────────────────────────────────────────────────┤
│              Question Sequencing Agent                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Step 1:     │    │ Step 2:     │    │ Step 3:     │     │
│  │ Main        │    │ Sentence    │    │ Generate    │     │
│  │ Question    │    │ Chunking    │    │ Questions   │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Key Components

### 1. Base Agent Framework (`base_agent.py`)

**Purpose**: Provides the foundation for all agents with common LLM interaction patterns.

**Key Features**:
- **LLMFactory**: Creates and manages LLM client connections
- **Generic Response Handling**: Structured request/response system
- **Error Management**: Consistent error handling across all agents
- **Prompt Integration**: Seamless integration with prompt management

**Core Classes**:
```python
class BaseAgent(ABC, Generic[T]):
    # Abstract base class for all agents
    # Handles LLM interactions, prompt management, response parsing

class LLMFactory:
    # Simple LLM client factory
    # Supports OpenAI-compatible APIs (like DashScope)

@dataclass
class LLMRequest:
    # Structured request configuration
    # agent_type, prompt_type, prompt_params, response_parser

@dataclass
class LLMResponse:
    # Structured response handling
    # raw_response, parsed_result, success, error_message
```

### 2. Prompt Manager (`prompt_manager.py`)

**Purpose**: Manages prompts for different agents and operations.

**Two Modes**:
- **File Mode**: Reads prompts from text files
- **Database Mode**: Stores prompts in SQLite database

**File Structure**:
```
prompts/
├── ntd_1_establishing_main_question.txt
├── ntd_2_sentence_chunking.txt
├── ntd_3_chunk_question_generation.txt
├── normcode_context.txt
└── direct_prompt.txt
```

**Key Features**:
- Automatic file-to-database synchronization
- Flexible prompt retrieval system
- Support for different agent types

### 3. Result Manager (`result_manager.py`)

**Purpose**: Handles saving and managing agent results.

**Two Storage Modes**:
- **File Mode**: Saves results as JSON files
- **Database Mode**: Stores results in SQLite database

**Features**:
- Automatic session ID generation
- Input hash tracking for deduplication
- Metadata storage
- Timestamp tracking

### 4. Question Sequencing Agent (`question_sequencing_agent.py`)

**Purpose**: Phase 1 agent that deconstructs instructive text into question sequences.

## 🔄 How It Works - Step by Step

### Step 1: Initialization
```python
agent = QuestionSequencingAgent(
    verbose=True,                    # Enable detailed logging
    llm_model="qwen-turbo-latest"    # Specify LLM model
)
```

### Step 2: Main Question Analysis
**Input**: Natural language instructions
**Process**: 
1. Agent retrieves appropriate prompt from PromptManager
2. Sends formatted prompt to LLM
3. LLM analyzes text and identifies main question type
4. Response is parsed into structured format

**Output**: `MainQuestion` object with:
- `type`: Question type (what, how, when)
- `target`: What the question targets
- `condition`: Conditions or constraints
- `question`: Formatted NormCode question

### Step 3: Sentence Chunking
**Input**: Original text
**Process**:
1. Agent sends text to LLM for chunking
2. LLM breaks text into logical sentence chunks
3. Each chunk represents a discrete piece of information

**Output**: List of sentence chunks

### Step 4: Question Generation
**Input**: Sentence chunks + main question
**Process**:
1. For each chunk, generate a specific question
2. Question relates to the main question
3. Chunk becomes the answer to its generated question

**Output**: List of `QuestionAnswerPair` objects

### Step 5: Result Assembly
**Input**: All processed components
**Process**:
1. Combine main question, question-answer pairs, and metadata
2. Create `QuestionDecomposition` object
3. Save result if requested

**Output**: Complete question decomposition

## 📊 Data Flow

```
Input Text
    ↓
[Prompt Manager] → Get appropriate prompts
    ↓
[Base Agent] → Format prompts with parameters
    ↓
[LLM Factory] → Send to LLM API
    ↓
[Response Parser] → Parse JSON responses
    ↓
[Result Manager] → Save structured results
    ↓
Final Question Decomposition
```

## 🎯 Example Workflow

**Input**: "Create a password for a new user account. The password should be at least 8 characters long and include a mix of uppercase and lowercase letters, numbers, and special characters."

**Step 1 - Main Question**:
```json
{
  "type": "what",
  "target": "{password_creation}",
  "condition": "$=",
  "question": "$what?({password_creation}, $=)"
}
```

**Step 2 - Chunking**:
```
Chunk 1: "Create a password for a new user account."
Chunk 2: "The password should be at least 8 characters long"
Chunk 3: "and include a mix of uppercase and lowercase letters, numbers, and special characters."
```

**Step 3 - Question Generation**:
```
Q1: "What is the purpose of the password?"
A1: "Create a password for a new user account."

Q2: "What is the minimum length requirement?"
A2: "The password should be at least 8 characters long"

Q3: "What character types are required?"
A3: "and include a mix of uppercase and lowercase letters, numbers, and special characters."
```

## 🔧 Configuration Options

### LLM Configuration
```python
# Use different models
agent = QuestionSequencingAgent(llm_model="gpt-4")

# Custom LLM client
custom_client = MyLLMClient()
agent = QuestionSequencingAgent(llm_client=custom_client)
```

### Prompt Management
```python
# File-based prompts
prompt_manager = PromptManager(mode="file")

# Database-based prompts
prompt_manager = PromptManager(mode="database")
```

### Result Storage
```python
# File-based results
result_manager = ResultManager(mode="file", results_dir="./results")

# Database-based results
result_manager = ResultManager(mode="database", db_path="./results.db")
```

## 🚀 Key Benefits

1. **Modularity**: Each component can be replaced or extended independently
2. **Flexibility**: Supports different LLM providers and storage backends
3. **Structured Output**: Consistent, parseable results
4. **Error Handling**: Robust error management throughout the pipeline
5. **Extensibility**: Easy to add new agent types and capabilities
6. **Debugging**: Verbose mode for detailed process tracking

## 🔮 Future Extensions

The architecture supports easy extension for:
- Additional phase agents (translation, compilation, etc.)
- Different LLM providers
- Custom prompt templates
- Advanced result analysis
- Real-time processing pipelines

This modular design makes the system both powerful and maintainable, allowing for easy customization and extension as requirements evolve. 