"""
Deployment LLM Tool - Language Model for server-side NormCode execution.

A standalone LLM tool for deployment that:
- Works without WebSocket/Canvas dependencies
- Supports multiple providers (OpenAI-compatible, Dashscope, etc.)
- Configurable via direct parameters or settings file
- Provides the same interface as infra LanguageModel
"""

import os
import json
import yaml
import logging
import time
from pathlib import Path
from string import Template
from typing import Optional, Any, Callable, Dict, List

logger = logging.getLogger(__name__)


def get_available_providers(settings_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get list of available LLM providers from settings.
    
    Returns:
        List of provider configs with id, name, model, base_url
    """
    providers = []
    
    # Always include demo mode
    providers.append({
        "id": "demo",
        "name": "Demo (Mock)",
        "model": "demo",
        "base_url": None,
        "is_mock": True,
    })
    
    # Try to load from settings file
    if settings_path is None:
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "settings.yaml"),
            os.path.join(os.path.dirname(__file__), "..", "settings.yaml"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                settings_path = p
                break
    
    if settings_path and os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = yaml.safe_load(f) or {}
            
            base_url = settings.pop("BASE_URL", None)
            
            for model_name, config in settings.items():
                if isinstance(config, dict):
                    providers.append({
                        "id": model_name,
                        "name": model_name,
                        "model": model_name,
                        "base_url": base_url,
                        "api_key_env": list(config.keys())[0] if config else None,
                        "is_mock": False,
                    })
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")
    
    return providers


class DeploymentLLMTool:
    """
    A Language Model tool for deployment/server execution.
    
    This tool provides LLM functionality without Canvas/WebSocket dependencies.
    Supports:
    - Direct configuration (api_key, base_url, model)
    - Settings file configuration
    - Mock mode for testing
    """
    
    def __init__(
        self,
        model_name: str = "demo",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        settings_path: Optional[str] = None,
        mock_mode: bool = False,
        log_callback: Optional[Callable[[str, Dict], None]] = None,
    ):
        """
        Initialize the deployment LLM tool.
        
        Args:
            model_name: Name of the model to use
            api_key: API key (overrides settings)
            base_url: Base URL for API (overrides settings)
            temperature: Generation temperature
            max_tokens: Max tokens for generation
            settings_path: Path to settings.yaml
            mock_mode: Force mock mode
            log_callback: Optional callback for logging events
        """
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._mock_mode = mock_mode
        self._log_callback = log_callback
        self._call_count = 0
        self.client = None
        
        if model_name == "demo" or mock_mode:
            self._mock_mode = True
            logger.info("LLM initialized in demo/mock mode")
            return
        
        # If API key not provided, try to load from settings
        if not api_key:
            self._load_from_settings(settings_path)
        
        # Initialize OpenAI client
        self._init_client()
    
    def _load_from_settings(self, settings_path: Optional[str]):
        """Load configuration from settings file."""
        if settings_path is None:
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "settings.yaml"),
                os.path.join(os.path.dirname(__file__), "..", "settings.yaml"),
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    settings_path = p
                    break
        
        if not settings_path or not os.path.exists(settings_path):
            logger.warning("No settings file found, using mock mode")
            self._mock_mode = True
            return
        
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = yaml.safe_load(f) or {}
            
            self.base_url = self.base_url or settings.get("BASE_URL")
            
            model_config = settings.get(self.model_name, {})
            if isinstance(model_config, dict):
                # Get API key from environment using the key name in config
                for env_key, env_value in model_config.items():
                    if env_key.endswith("_API_KEY"):
                        self.api_key = env_value or os.environ.get(env_key)
                        break
            
            if not self.api_key:
                logger.warning(f"No API key found for model {self.model_name}")
                self._mock_mode = True
                
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            self._mock_mode = True
    
    def _init_client(self):
        """Initialize the OpenAI client."""
        if self._mock_mode:
            return
        
        if not self.api_key:
            logger.warning("No API key provided, using mock mode")
            self._mock_mode = True
            return
        
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
            logger.info(f"LLM client initialized: {self.model_name} @ {self.base_url}")
        except ImportError:
            logger.error("OpenAI package not installed")
            self._mock_mode = True
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self._mock_mode = True
    
    def _log(self, event: str, data: Dict[str, Any]):
        """Log an event via callback if set."""
        if self._log_callback:
            try:
                self._log_callback(event, data)
            except Exception as e:
                logger.error(f"Log callback failed: {e}")
    
    def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Generate text from a prompt.
        
        Args:
            prompt: The prompt text
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stop: Stop sequences
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        self._call_count += 1
        start_time = time.time()
        
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        self._log("llm:call_started", {
            "call_id": self._call_count,
            "model": self.model_name,
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
        })
        
        if self._mock_mode:
            # Mock response
            response = f"[MOCK RESPONSE for: {prompt[:100]}...]"
            duration = time.time() - start_time
            
            self._log("llm:call_completed", {
                "call_id": self._call_count,
                "response_length": len(response),
                "duration_ms": int(duration * 1000),
                "is_mock": True,
            })
            
            return response
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            completion_kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temp,
            }
            
            if tokens:
                completion_kwargs["max_tokens"] = tokens
            if stop:
                completion_kwargs["stop"] = stop
            
            completion = self.client.chat.completions.create(**completion_kwargs)
            response = completion.choices[0].message.content or ""
            
            duration = time.time() - start_time
            
            self._log("llm:call_completed", {
                "call_id": self._call_count,
                "response_length": len(response),
                "duration_ms": int(duration * 1000),
                "usage": {
                    "prompt_tokens": getattr(completion.usage, "prompt_tokens", None),
                    "completion_tokens": getattr(completion.usage, "completion_tokens", None),
                } if completion.usage else None,
            })
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            self._log("llm:call_failed", {
                "call_id": self._call_count,
                "error": str(e),
                "duration_ms": int(duration * 1000),
            })
            
            logger.error(f"LLM call failed: {e}")
            raise
    
    def create_generation_function(
        self,
        template: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Callable[[Dict[str, Any]], str]:
        """
        Create a function that fills a template and generates text.
        
        Args:
            template: Template string with $variable placeholders
            temperature: Override temperature
            max_tokens: Override max tokens
            
        Returns:
            A callable that takes a variables dict and returns generated text
        """
        def generation_fn(variables: Dict[str, Any]) -> str:
            # Handle positional argument
            if "__positional__" in variables:
                prompt = str(variables["__positional__"])
            else:
                prompt = Template(template).safe_substitute(variables)
            
            return self.generate(prompt, temperature=temperature, max_tokens=max_tokens)
        
        return generation_fn
    
    @property
    def is_mock_mode(self) -> bool:
        """Check if tool is in mock mode."""
        return self._mock_mode
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "model": self.model_name,
            "call_count": self._call_count,
            "is_mock": self._mock_mode,
            "has_client": self.client is not None,
        }

