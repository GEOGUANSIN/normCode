"""
LLM Provider Settings Service - Manages LLM provider configurations.

Stores configurations in:
- Primary: canvas_app/backend/tools/llm-settings.json (same dir as llm_tool.py)
- Also exports to settings.yaml for compatibility with legacy code

This module provides CRUD operations for LLM provider configurations,
including import/export and connection testing.
"""

import os
import json
import logging
import time
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

from schemas.llm_schemas import (
    LLMProviderConfig,
    LLMSettingsConfig,
    LLMProvider,
    PROVIDER_PRESETS,
    CreateProviderRequest,
    UpdateProviderRequest,
)

logger = logging.getLogger(__name__)

# Settings location - same directory as the tools
TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
LLM_SETTINGS_FILE = TOOLS_DIR / "llm-settings.json"

# Legacy settings.yaml location (for backward-compatible imports only, NOT for export)
# This allows importing from existing settings.yaml files if llm-settings.json doesn't exist
SETTINGS_YAML_FILE = TOOLS_DIR / "settings.yaml"

# Fallback to user config dir
USER_CONFIG_DIR = Path.home() / ".normcode-canvas"
FALLBACK_SETTINGS_FILE = USER_CONFIG_DIR / "llm-settings.json"


class LLMSettingsService:
    """Service for managing LLM provider configurations.
    
    Provides:
    - CRUD operations for providers
    - Default provider management
    - Import/export with settings.yaml
    - Connection testing
    """
    
    def __init__(self):
        """Initialize the LLM settings service."""
        self._settings: Optional[LLMSettingsConfig] = None
        self._settings_file = self._determine_settings_file()
    
    def _determine_settings_file(self) -> Path:
        """Determine which settings file to use."""
        # Prefer the tools directory
        if TOOLS_DIR.exists():
            return LLM_SETTINGS_FILE
        # Fall back to user config dir
        USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return FALLBACK_SETTINGS_FILE
    
    def _load_settings(self) -> LLMSettingsConfig:
        """Load settings from file."""
        if self._settings is not None:
            return self._settings
        
        # Try loading from primary location
        if self._settings_file.exists():
            try:
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._settings = LLMSettingsConfig(**data)
                logger.info(f"Loaded LLM settings from {self._settings_file} with {len(self._settings.providers)} providers")
                return self._settings
            except Exception as e:
                logger.error(f"Failed to load LLM settings: {e}")
        
        # Try importing from settings.yaml if it exists
        if SETTINGS_YAML_FILE.exists():
            self._settings = self._create_default_settings()
            self._import_from_yaml(SETTINGS_YAML_FILE)
            self._save_settings()
            return self._settings
        
        # Create default settings
        self._settings = self._create_default_settings()
        self._save_settings()
        
        return self._settings
    
    def _create_default_settings(self) -> LLMSettingsConfig:
        """Create default settings with demo provider."""
        return LLMSettingsConfig(
            providers=[
                LLMProviderConfig(
                    id="demo",
                    name="Demo (No LLM)",
                    provider=LLMProvider.CUSTOM,
                    model="demo",
                    is_default=True,
                    is_enabled=True,
                    description="Demo mode - returns mock responses"
                )
            ],
            default_provider_id="demo"
        )
    
    def _import_from_yaml(self, yaml_path: Path) -> int:
        """Import providers from a settings.yaml file."""
        try:
            with open(yaml_path, 'r') as f:
                yaml_settings = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load settings.yaml: {e}")
            return 0
        
        # Default base URL for DashScope
        base_url = yaml_settings.get('BASE_URL', "https://dashscope.aliyuncs.com/compatible-mode/v1")
        imported = 0
        
        for key, value in yaml_settings.items():
            if key == 'BASE_URL':
                continue
            if isinstance(value, dict) and 'DASHSCOPE_API_KEY' in value:
                # Check if already exists
                existing = self.get_provider_by_name(key)
                if existing:
                    continue
                
                provider = LLMProviderConfig(
                    name=key,
                    provider=LLMProvider.DASHSCOPE,
                    api_key=value['DASHSCOPE_API_KEY'],
                    base_url=base_url,
                    model=key,
                    description=f"Imported from settings.yaml",
                )
                
                if self._settings:
                    self._settings.providers.append(provider)
                imported += 1
        
        logger.info(f"Imported {imported} providers from settings.yaml")
        return imported
    
    def _save_settings(self):
        """Save settings to llm-settings.json file."""
        if self._settings is None:
            return
        
        self._settings.updated_at = datetime.now()
        
        try:
            # Ensure directory exists
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to JSON-serializable dict
            data = json.loads(self._settings.model_dump_json())
            
            # Save JSON settings
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Saved LLM settings to {self._settings_file}")
            
        except Exception as e:
            logger.error(f"Failed to save LLM settings: {e}")
            raise
    
    def get_settings(self) -> LLMSettingsConfig:
        """Get the current LLM settings."""
        return self._load_settings()
    
    def get_providers(self) -> List[LLMProviderConfig]:
        """Get all configured providers."""
        settings = self._load_settings()
        return settings.providers
    
    def get_provider(self, provider_id: str) -> Optional[LLMProviderConfig]:
        """Get a specific provider by ID."""
        settings = self._load_settings()
        for provider in settings.providers:
            if provider.id == provider_id:
                return provider
        return None
    
    def get_default_provider(self) -> Optional[LLMProviderConfig]:
        """Get the default provider."""
        settings = self._load_settings()
        
        # Try to find by default_provider_id
        if settings.default_provider_id:
            provider = self.get_provider(settings.default_provider_id)
            if provider and provider.is_enabled:
                return provider
        
        # Fall back to first enabled provider marked as default
        for provider in settings.providers:
            if provider.is_default and provider.is_enabled:
                return provider
        
        # Fall back to first enabled provider
        for provider in settings.providers:
            if provider.is_enabled:
                return provider
        
        return None
    
    def get_provider_by_name(self, name: str) -> Optional[LLMProviderConfig]:
        """Get a provider by name (case-insensitive)."""
        settings = self._load_settings()
        name_lower = name.lower()
        for provider in settings.providers:
            if provider.name.lower() == name_lower or provider.model.lower() == name_lower:
                return provider
        return None
    
    def create_provider(self, request: CreateProviderRequest) -> LLMProviderConfig:
        """Create a new provider configuration."""
        settings = self._load_settings()
        
        # Create the provider config
        provider = LLMProviderConfig(
            name=request.name,
            provider=request.provider,
            api_key=request.api_key,
            base_url=request.base_url,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            is_default=request.is_default,
            description=request.description,
        )
        
        # If this is the default, unset other defaults
        if provider.is_default:
            for p in settings.providers:
                p.is_default = False
            settings.default_provider_id = provider.id
        
        settings.providers.append(provider)
        self._save_settings()
        
        logger.info(f"Created LLM provider: {provider.name} ({provider.id})")
        return provider
    
    def update_provider(self, provider_id: str, request: UpdateProviderRequest) -> Optional[LLMProviderConfig]:
        """Update an existing provider configuration."""
        settings = self._load_settings()
        
        provider = None
        for i, p in enumerate(settings.providers):
            if p.id == provider_id:
                provider = p
                break
        
        if provider is None:
            return None
        
        # Update fields if provided
        if request.name is not None:
            provider.name = request.name
        if request.provider is not None:
            provider.provider = request.provider
        if request.api_key is not None:
            provider.api_key = request.api_key
        if request.base_url is not None:
            provider.base_url = request.base_url
        if request.model is not None:
            provider.model = request.model
        if request.temperature is not None:
            provider.temperature = request.temperature
        if request.max_tokens is not None:
            provider.max_tokens = request.max_tokens
        if request.is_enabled is not None:
            provider.is_enabled = request.is_enabled
        if request.description is not None:
            provider.description = request.description
        
        # Handle default flag
        if request.is_default is not None:
            if request.is_default:
                # Unset other defaults
                for p in settings.providers:
                    p.is_default = False
                settings.default_provider_id = provider.id
            provider.is_default = request.is_default
        
        provider.updated_at = datetime.now()
        self._save_settings()
        
        logger.info(f"Updated LLM provider: {provider.name} ({provider.id})")
        return provider
    
    def delete_provider(self, provider_id: str) -> bool:
        """Delete a provider configuration."""
        settings = self._load_settings()
        
        # Don't allow deleting the demo provider
        if provider_id == "demo":
            logger.warning("Cannot delete the demo provider")
            return False
        
        original_count = len(settings.providers)
        settings.providers = [p for p in settings.providers if p.id != provider_id]
        
        if len(settings.providers) < original_count:
            # If we deleted the default, reset default
            if settings.default_provider_id == provider_id:
                settings.default_provider_id = None
                # Set first available as default
                for p in settings.providers:
                    if p.is_enabled:
                        p.is_default = True
                        settings.default_provider_id = p.id
                        break
            
            self._save_settings()
            logger.info(f"Deleted LLM provider: {provider_id}")
            return True
        
        return False
    
    def set_default_provider(self, provider_id: str) -> bool:
        """Set a provider as the default."""
        settings = self._load_settings()
        
        found = False
        for p in settings.providers:
            if p.id == provider_id:
                p.is_default = True
                settings.default_provider_id = provider_id
                found = True
            else:
                p.is_default = False
        
        if found:
            self._save_settings()
            logger.info(f"Set default LLM provider: {provider_id}")
        
        return found
    
    def create_provider_from_preset(
        self,
        preset_key: str,
        api_key: Optional[str] = None,
        custom_name: Optional[str] = None
    ) -> Optional[LLMProviderConfig]:
        """Create a provider from a preset configuration."""
        if preset_key not in PROVIDER_PRESETS:
            logger.warning(f"Unknown preset: {preset_key}")
            return None
        
        preset = PROVIDER_PRESETS[preset_key]
        
        request = CreateProviderRequest(
            name=custom_name or f"{preset.name} - {preset.default_model}",
            provider=preset.provider,
            api_key=api_key,
            base_url=preset.base_url,
            model=preset.default_model,
            description=preset.description,
        )
        
        return self.create_provider(request)
    
    def get_available_models(self) -> List[str]:
        """Get list of all available model names from enabled providers."""
        settings = self._load_settings()
        models = []
        
        for provider in settings.providers:
            if provider.is_enabled:
                # Add the provider name as the model identifier
                models.append(provider.name)
        
        return models
    
    def test_provider(
        self,
        provider_id: Optional[str] = None,
        provider_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test a provider connection with a simple prompt."""
        config = None
        
        if provider_id:
            config = self.get_provider(provider_id)
            if not config:
                return {
                    "success": False,
                    "message": f"Provider not found: {provider_id}",
                }
        elif provider_config:
            # Create temporary config from dict
            try:
                config = LLMProviderConfig(**provider_config)
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Invalid provider config: {e}",
                }
        else:
            return {
                "success": False,
                "message": "No provider specified",
            }
        
        # Check for demo mode
        if config.model == "demo" or config.id == "demo":
            return {
                "success": True,
                "message": "Demo mode - no API call made",
                "response_preview": "MOCK_RESPONSE[Test prompt]",
                "latency_ms": 0,
            }
        
        # Check for required API key
        if not config.api_key and config.provider != LLMProvider.OLLAMA:
            return {
                "success": False,
                "message": "API key is required for this provider",
            }
        
        # Try to make a test call
        try:
            from openai import OpenAI, APIConnectionError, APITimeoutError, AuthenticationError
            
            start_time = time.time()
            
            # Use shorter timeout for test
            client = OpenAI(
                api_key=config.api_key or "not-needed",
                base_url=config.base_url,
                timeout=30.0,  # 30 second timeout for test
                max_retries=1,  # Only 1 retry for test
            )
            
            response = client.chat.completions.create(
                model=config.model,
                messages=[{"role": "user", "content": "Say 'Hello' and nothing else."}],
                max_tokens=10,
                temperature=0,
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            content = response.choices[0].message.content
            
            return {
                "success": True,
                "message": "Connection successful",
                "response_preview": content,
                "latency_ms": latency_ms,
            }
        
        except AuthenticationError as e:
            return {
                "success": False,
                "message": f"Authentication failed: Invalid API key. Please check your API key.",
                "error_type": "auth",
            }
        except APIConnectionError as e:
            # More detailed connection error info
            error_detail = str(e)
            if "getaddrinfo" in error_detail or "DNS" in error_detail.upper():
                hint = "DNS resolution failed. Check your network connection."
            elif "timeout" in error_detail.lower():
                hint = "Connection timed out. The API server may be unreachable."
            elif "proxy" in error_detail.lower():
                hint = "Proxy error. Check your network proxy settings."
            elif "ssl" in error_detail.lower() or "certificate" in error_detail.lower():
                hint = "SSL/TLS error. There may be a certificate issue."
            else:
                hint = f"Network error: {error_detail}"
            
            return {
                "success": False,
                "message": f"Connection failed: {hint}",
                "error_type": "connection",
                "base_url": config.base_url,
            }
        except APITimeoutError as e:
            return {
                "success": False,
                "message": "Request timed out. The API server is not responding in time.",
                "error_type": "timeout",
            }
        except Exception as e:
            error_type = type(e).__name__
            return {
                "success": False,
                "message": f"Connection failed ({error_type}): {str(e)}",
                "error_type": "unknown",
            }
    
    def import_from_settings_yaml(self, settings_path: Optional[str] = None) -> int:
        """Import providers from a settings.yaml file (for migration)."""
        if settings_path is None:
            # Try multiple locations in order of preference
            possible_paths = [
                str(SETTINGS_YAML_FILE),  # tools directory
            ]
            
            # Also try project root
            try:
                from infra._constants import PROJECT_ROOT
                possible_paths.append(os.path.join(PROJECT_ROOT, "settings.yaml"))
            except ImportError:
                possible_paths.append(os.path.join(os.getcwd(), "settings.yaml"))
            
            # Find first existing file
            settings_path = None
            for p in possible_paths:
                if os.path.exists(p):
                    settings_path = p
                    break
            
            if not settings_path:
                logger.warning("No settings.yaml found in any location")
                return 0
        
        if not os.path.exists(settings_path):
            logger.warning(f"Settings file not found: {settings_path}")
            return 0
        
        try:
            with open(settings_path, 'r') as f:
                yaml_settings = yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Failed to load settings.yaml: {e}")
            return 0
        
        base_url = yaml_settings.get('BASE_URL', "https://dashscope.aliyuncs.com/compatible-mode/v1")
        imported = 0
        
        for key, value in yaml_settings.items():
            if isinstance(value, dict) and 'DASHSCOPE_API_KEY' in value:
                # Check if already exists
                existing = self.get_provider_by_name(key)
                if existing:
                    continue
                
                request = CreateProviderRequest(
                    name=key,
                    provider=LLMProvider.DASHSCOPE,
                    api_key=value['DASHSCOPE_API_KEY'],
                    base_url=base_url,
                    model=key,
                    description=f"Imported from settings.yaml",
                )
                
                self.create_provider(request)
                imported += 1
        
        logger.info(f"Imported {imported} providers from settings.yaml")
        return imported


# Global service instance
llm_settings_service = LLMSettingsService()

