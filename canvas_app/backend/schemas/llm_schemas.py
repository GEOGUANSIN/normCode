"""LLM configuration schemas for customizable LLM settings."""
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
import uuid


def generate_provider_id() -> str:
    """Generate a unique provider ID."""
    return str(uuid.uuid4())[:8]


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    DASHSCOPE = "dashscope"  # Alibaba Cloud (qwen models)
    OLLAMA = "ollama"  # Local models
    CUSTOM = "custom"  # Custom OpenAI-compatible endpoint


class LLMProviderConfig(BaseModel):
    """Configuration for a single LLM provider/endpoint."""
    id: str = Field(default_factory=generate_provider_id)
    name: str  # Display name (e.g., "GPT-4o", "Qwen Plus", "Local Llama")
    provider: LLMProvider = LLMProvider.OPENAI
    
    # Connection settings
    api_key: Optional[str] = None  # API key (stored securely)
    base_url: Optional[str] = None  # Custom base URL for the API
    model: str  # Model name (e.g., "gpt-4o", "qwen-plus", "llama3")
    
    # Generation settings
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, ge=1)
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    
    # Metadata
    is_default: bool = False
    is_enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Notes/description
    description: Optional[str] = None


class LLMProviderPreset(BaseModel):
    """Preset configuration for common providers."""
    provider: LLMProvider
    name: str
    base_url: str
    default_model: str
    available_models: List[str]
    requires_api_key: bool = True
    description: str


# Default presets for common providers
PROVIDER_PRESETS: Dict[str, LLMProviderPreset] = {
    "openai": LLMProviderPreset(
        provider=LLMProvider.OPENAI,
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o",
        available_models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo", "o1-preview", "o1-mini"],
        description="OpenAI's GPT models"
    ),
    "anthropic": LLMProviderPreset(
        provider=LLMProvider.ANTHROPIC,
        name="Anthropic",
        base_url="https://api.anthropic.com/v1",
        default_model="claude-3-5-sonnet-20241022",
        available_models=["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        description="Anthropic's Claude models"
    ),
    "dashscope": LLMProviderPreset(
        provider=LLMProvider.DASHSCOPE,
        name="Alibaba Cloud (DashScope)",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        default_model="qwen-plus",
        available_models=["qwen-plus", "qwen-turbo", "qwen-turbo-latest", "qwen-max", "qwen-long"],
        description="Alibaba Cloud's Qwen models via DashScope"
    ),
    "azure": LLMProviderPreset(
        provider=LLMProvider.AZURE,
        name="Azure OpenAI",
        base_url="",  # User must provide their Azure endpoint
        default_model="gpt-4o",
        available_models=["gpt-4o", "gpt-4-turbo", "gpt-35-turbo"],
        requires_api_key=True,
        description="Microsoft Azure OpenAI Service"
    ),
    "ollama": LLMProviderPreset(
        provider=LLMProvider.OLLAMA,
        name="Ollama (Local)",
        base_url="http://localhost:11434/v1",
        default_model="llama3",
        available_models=["llama3", "llama3:70b", "mistral", "codellama", "qwen2"],
        requires_api_key=False,
        description="Local models via Ollama"
    ),
    "deepseek": LLMProviderPreset(
        provider=LLMProvider.CUSTOM,
        name="DeepSeek",
        base_url="https://api.deepseek.com/v1",
        default_model="deepseek-chat",
        available_models=["deepseek-chat", "deepseek-coder", "deepseek-reasoner"],
        description="DeepSeek AI models"
    ),
    "together": LLMProviderPreset(
        provider=LLMProvider.CUSTOM,
        name="Together AI",
        base_url="https://api.together.xyz/v1",
        default_model="meta-llama/Llama-3-70b-chat-hf",
        available_models=["meta-llama/Llama-3-70b-chat-hf", "mistralai/Mixtral-8x7B-Instruct-v0.1"],
        description="Together AI hosted models"
    ),
    "groq": LLMProviderPreset(
        provider=LLMProvider.CUSTOM,
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        default_model="llama-3.3-70b-versatile",
        available_models=["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"],
        description="Groq ultra-fast inference"
    ),
}


class LLMSettingsConfig(BaseModel):
    """Complete LLM settings configuration."""
    providers: List[LLMProviderConfig] = Field(default_factory=list)
    default_provider_id: Optional[str] = None
    # Global settings
    timeout_seconds: int = Field(default=120, ge=10, le=600)
    retry_count: int = Field(default=3, ge=0, le=10)
    # Metadata
    updated_at: datetime = Field(default_factory=datetime.now)


# API Request/Response models

class CreateProviderRequest(BaseModel):
    """Request to create a new LLM provider configuration."""
    name: str
    provider: LLMProvider = LLMProvider.OPENAI
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    is_default: bool = False
    description: Optional[str] = None


class UpdateProviderRequest(BaseModel):
    """Request to update an existing LLM provider configuration."""
    name: Optional[str] = None
    provider: Optional[LLMProvider] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_default: Optional[bool] = None
    is_enabled: Optional[bool] = None
    description: Optional[str] = None


class TestProviderRequest(BaseModel):
    """Request to test an LLM provider connection."""
    provider_id: Optional[str] = None  # Test existing provider
    # Or test with inline config
    provider: Optional[LLMProvider] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


class TestProviderResponse(BaseModel):
    """Response from testing an LLM provider."""
    success: bool
    message: str
    response_preview: Optional[str] = None
    latency_ms: Optional[int] = None


class ProviderListResponse(BaseModel):
    """Response containing list of configured providers."""
    providers: List[LLMProviderConfig]
    default_provider_id: Optional[str] = None


class ProviderPresetsResponse(BaseModel):
    """Response containing available provider presets."""
    presets: Dict[str, LLMProviderPreset]
