# LLMFactory + LlamaIndex Integration Guide

## Quick Start

### Basic Usage (One Line!)
```python
from LLMFactory import LLMFactory
from llamaindex_base_agent import LlamaIndexBaseAgent

# Create agent with LLMFactory in one line
agent = LlamaIndexBaseAgent(
    llm_instance=LLMFactory("deepseek-v3").create_llamaindex_wrapper()
)
```

### Step-by-Step Usage
```python
# 1. Create LLMFactory
llm_factory = LLMFactory("deepseek-v3")

# 2. Get LlamaIndex wrapper
llm_wrapper = llm_factory.create_llamaindex_wrapper()

# 3. Create agent
agent = LlamaIndexBaseAgent(llm_instance=llm_wrapper)
```

## Local LLM Endpoints

### Ollama
```python
# For Ollama local models
llm_factory = LLMFactory.create_for_local_endpoint(
    model_name="llama2:7b",
    base_url="http://localhost:11434/v1"
)
agent = LlamaIndexBaseAgent(
    llm_instance=llm_factory.create_llamaindex_wrapper()
)
```

### LocalAI
```python
# For LocalAI
llm_factory = LLMFactory.create_for_local_endpoint(
    model_name="gpt-3.5-turbo",
    base_url="http://localhost:8080/v1"
)
agent = LlamaIndexBaseAgent(
    llm_instance=llm_factory.create_llamaindex_wrapper()
)
```

### Custom OpenAI-Compatible Endpoint
```python
# For any OpenAI-compatible endpoint
llm_factory = LLMFactory.create_with_custom_settings(
    model_name="mistral-7b-instruct",
    base_url="http://localhost:8000/v1",
    api_key="your-api-key"
)
agent = LlamaIndexBaseAgent(
    llm_instance=llm_factory.create_llamaindex_wrapper()
)
```

## Advanced Usage

### With Documents
```python
from llama_index.core import Document

documents = [
    Document(text="Your document content here"),
    Document(text="More document content")
]

agent = LlamaIndexBaseAgent(
    llm_instance=LLMFactory("deepseek-v3").create_llamaindex_wrapper(),
    documents=documents
)
```

### Custom Agent Implementation
```python
class MyAgent(LlamaIndexBaseAgent):
    def _get_agent_type(self) -> str:
        return "my_agent"
    
    def _create_fallback_handler(self, request):
        return lambda: {"error": "Fallback response"}
    
    def _create_mock_response_generator(self, request):
        return lambda prompt: '{"result": "mock response"}'

# Use with LLMFactory
agent = MyAgent(
    llm_instance=LLMFactory("deepseek-v3").create_llamaindex_wrapper()
)
```

## Available Methods

### LLMFactory Constructor Options
```python
# Standard usage (from settings.yaml)
LLMFactory(model_name="deepseek-v3")

# With custom base URL and API key
LLMFactory(
    model_name="llama2:7b",
    base_url="http://localhost:11434/v1",
    api_key="your-key"
)

# With custom settings file
LLMFactory(
    model_name="deepseek-v3",
    settings_path="/path/to/custom/settings.yaml"
)
```

### Class Methods for Easy Setup
```python
# For local endpoints
LLMFactory.create_for_local_endpoint(
    model_name="llama2:7b",
    base_url="http://localhost:11434/v1"
)

# With custom settings
LLMFactory.create_with_custom_settings(
    model_name="mistral-7b-instruct",
    base_url="http://localhost:8000/v1",
    api_key="your-api-key"
)
```

### Wrapper Creation
```python
# Create wrapper for LlamaIndex
llm_factory = LLMFactory("deepseek-v3")
llm_wrapper = llm_factory.create_llamaindex_wrapper()
```

## Benefits

1. **Simple Integration**: One method call to get LlamaIndex compatibility
2. **Local LLM Support**: Easy setup for local endpoints
3. **Flexible Configuration**: Support for custom base URLs and API keys
4. **Backward Compatibility**: Existing LLMFactory code continues to work
5. **Full RAG Capabilities**: All LlamaIndex features available

## Error Handling

The integration includes proper error handling:
- Import errors if wrapper is not available
- Validation of model names and API keys
- Fallback mechanisms in the base agent
- Graceful degradation for local endpoints

## Migration from Previous Versions

If you were using the separate wrapper approach:
```python
# Old way
from llm_wrapper import LLMFactoryAdapter
llm_wrapper = LLMFactoryAdapter.create_llm_factory_wrapper("deepseek-v3")

# New way
llm_wrapper = LLMFactory("deepseek-v3").create_llamaindex_wrapper()
```

The new approach is simpler and more direct! 