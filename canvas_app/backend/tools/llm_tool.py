"""
Canvas-native LLM tool for NormCode orchestration.

This tool wraps the standard LanguageModel but adds WebSocket event
emission for LLM operations, allowing the UI to show real-time
LLM call progress, prompts, and responses.

The tool is self-contained and can work with or without the infra
LanguageModel, falling back to mock mode if the infra is unavailable.

Supports loading configuration from:
1. Canvas LLM settings service (preferred)
2. settings.yaml file (legacy)
3. Direct parameters
"""

import os
import json
import yaml
import logging
import time
from pathlib import Path
from string import Template
from typing import Optional, Any, Callable, Dict, List, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.llm_schemas import LLMProviderConfig

logger = logging.getLogger(__name__)


class CanvasLLMTool:
    """
    A Language Model tool that emits WebSocket events for LLM operations.
    
    This tool proxies the standard LanguageModel functionality while
    adding event emission for UI monitoring. It tracks:
    - Prompt content and length
    - Response content and tokens
    - Duration of LLM calls
    - Model used
    
    Can work in mock mode for testing without API credentials.
    
    Supports multiple configuration sources:
    1. Canvas LLM settings service (use from_provider_id or from_settings_service)
    2. Direct configuration (api_key, base_url, model_name)
    3. settings.yaml file (legacy)
    """
    
    def __init__(
        self,
        model_name: str = "demo",
        settings_path: Optional[str] = None,
        emit_callback: Optional[Callable[[str, Dict], None]] = None,
        mock_mode: bool = False,
        # New: direct configuration options
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        # New: provider config
        provider_config: Optional["LLMProviderConfig"] = None,
    ):
        """
        Initialize the Canvas LLM tool.
        
        Args:
            model_name: Name of the LLM model to use (e.g., "qwen-plus", "gpt-4o")
            settings_path: Path to settings.yaml file with API keys (legacy)
            emit_callback: Callback to emit WebSocket events
            mock_mode: Force mock mode (no actual API calls)
            api_key: Direct API key (overrides settings)
            base_url: Direct base URL (overrides settings)
            temperature: Default temperature for generation
            max_tokens: Default max tokens for generation
            provider_config: LLMProviderConfig object from settings service
        """
        self.model_name = model_name
        self._emit_callback = emit_callback
        self._mock_mode = mock_mode
        self._call_count = 0
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # If provider config is passed, use it directly
        if provider_config:
            self._init_from_provider_config(provider_config)
            return
        
        # If direct API key is provided, use it
        if api_key:
            self.api_key = api_key
            self.base_url = base_url
            self.settings_path = None
            self.settings = {}
            self._infra_llm = None
            self._init_direct_client()
            return
        
        # Try to use the LLM settings service first
        if self._try_init_from_settings_service(model_name):
            return
        
        # Fall back to settings.yaml
        if settings_path is None:
            # Try common locations - prefer same directory as this tool
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "settings.yaml"),  # Same dir as llm_tool.py
            ]
            
            try:
                from infra._constants import PROJECT_ROOT
                possible_paths.append(os.path.join(PROJECT_ROOT, "settings.yaml"))
            except ImportError:
                pass
            
            possible_paths.extend([
                os.path.join(os.getcwd(), "settings.yaml"),
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "settings.yaml"),
            ])
            
            for p in possible_paths:
                if os.path.exists(p):
                    settings_path = p
                    break
        
        self.settings_path = settings_path
        self.settings = {}
        self.api_key = None
        self.base_url = None
        self.client = None
        
        # Try to import and initialize the underlying LanguageModel
        self._infra_llm = None
        if not mock_mode:
            self._initialize_llm()
    
    def _try_init_from_settings_service(self, model_name: str) -> bool:
        """Try to initialize from the LLM settings service."""
        try:
            from services.llm_settings_service import llm_settings_service
            
            # Try to find provider by name or model
            provider = llm_settings_service.get_provider_by_name(model_name)
            
            # If not found by name, try the default provider
            if not provider and model_name == "demo":
                provider = llm_settings_service.get_default_provider()
            
            if provider and provider.is_enabled:
                self._init_from_provider_config(provider)
                logger.info(f"Initialized LLM from settings service: {provider.name}")
                return True
        except ImportError:
            logger.debug("LLM settings service not available")
        except Exception as e:
            logger.warning(f"Failed to init from settings service: {e}")
        
        return False
    
    def _init_from_provider_config(self, config: "LLMProviderConfig"):
        """Initialize from a provider config object."""
        self.model_name = config.model
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.settings_path = None
        self.settings = {}
        self._infra_llm = None
        
        # Check for demo mode
        if config.model == "demo" or config.id == "demo":
            self._mock_mode = True
            self.client = None
            logger.info("LLM initialized in demo/mock mode")
            return
        
        self._init_direct_client()
    
    def _init_direct_client(self):
        """Initialize OpenAI client directly with provided credentials."""
        if not self.api_key and self.base_url and "localhost" not in (self.base_url or ""):
            self._mock_mode = True
            logger.warning("No API key provided, using mock mode")
            return
        
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key or "not-needed",
                base_url=self.base_url,
            )
            self._mock_mode = False
            logger.info(f"Initialized LLM with direct client: {self.model_name} @ {self.base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self._mock_mode = True
            self.client = None
    
    @classmethod
    def from_provider_id(
        cls,
        provider_id: str,
        emit_callback: Optional[Callable[[str, Dict], None]] = None,
    ) -> "CanvasLLMTool":
        """
        Create an LLM tool from a configured provider ID.
        
        Args:
            provider_id: The provider ID from the LLM settings service
            emit_callback: Callback to emit WebSocket events
            
        Returns:
            Configured CanvasLLMTool instance
        """
        from services.llm_settings_service import llm_settings_service
        
        provider = llm_settings_service.get_provider(provider_id)
        if not provider:
            raise ValueError(f"Provider not found: {provider_id}")
        
        return cls(
            model_name=provider.model,
            emit_callback=emit_callback,
            provider_config=provider,
        )
    
    @classmethod
    def from_default_provider(
        cls,
        emit_callback: Optional[Callable[[str, Dict], None]] = None,
    ) -> "CanvasLLMTool":
        """
        Create an LLM tool using the default configured provider.
        
        Args:
            emit_callback: Callback to emit WebSocket events
            
        Returns:
            Configured CanvasLLMTool instance
        """
        from services.llm_settings_service import llm_settings_service
        
        provider = llm_settings_service.get_default_provider()
        if not provider:
            # Fall back to demo mode
            return cls(model_name="demo", emit_callback=emit_callback, mock_mode=True)
        
        return cls(
            model_name=provider.model,
            emit_callback=emit_callback,
            provider_config=provider,
        )
    
    def _initialize_llm(self):
        """Initialize the LLM client, either via infra or directly."""
        # Try infra LanguageModel first
        try:
            from infra._agent._models._language_models import LanguageModel
            self._infra_llm = LanguageModel(self.model_name, self.settings_path)
            self._mock_mode = self._infra_llm.mock_mode
            logger.info(f"Initialized LLM via infra LanguageModel: {self.model_name} (mock={self._mock_mode})")
            return
        except ImportError:
            logger.info("Could not import infra LanguageModel, using direct initialization")
        except Exception as e:
            logger.warning(f"Failed to initialize infra LanguageModel: {e}")
        
        # Direct initialization fallback
        try:
            if self.settings_path and os.path.exists(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    self.settings = yaml.safe_load(f) or {}
            
            if self.model_name in self.settings:
                self.api_key = self.settings[self.model_name].get('DASHSCOPE_API_KEY')
                self.base_url = self.settings.get(
                    'BASE_URL', 
                    "https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                
                if self.api_key:
                    from openai import OpenAI
                    self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
                    logger.info(f"Initialized LLM directly with OpenAI client: {self.model_name}")
                    return
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Fall back to mock mode
        self._mock_mode = True
        logger.info(f"LLM initialized in mock mode: {self.model_name}")
    
    def set_emit_callback(self, callback: Callable[[str, Dict], None]):
        """Set the callback for emitting WebSocket events."""
        self._emit_callback = callback
    
    def _emit(self, event_type: str, data: Dict[str, Any]):
        """Emit a WebSocket event if callback is set."""
        if self._emit_callback:
            try:
                self._emit_callback(event_type, data)
            except Exception as e:
                logger.error(f"Failed to emit event {event_type}: {e}")
    
    @property
    def mock_mode(self) -> bool:
        """Whether the LLM is in mock mode (no actual API calls)."""
        if self._infra_llm:
            return self._infra_llm.mock_mode
        return self._mock_mode
    
    def generate(
        self,
        prompt: str,
        system_message: str = "You are a helpful assistant.",
        response_format: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt to send to the LLM
            system_message: Optional system message to set context
            response_format: Optional response format specification (e.g., {"type": "json_object"})
            
        Returns:
            The LLM response as a string
        """
        self._call_count += 1
        call_id = f"llm_{self._call_count}_{int(time.time())}"
        start_time = time.time()
        
        # Emit start event
        self._emit("llm:call_started", {
            "call_id": call_id,
            "model": self.model_name,
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:500] + "..." if len(prompt) > 500 else prompt,
            "system_message": system_message[:200] if system_message else None,
            "response_format": response_format,
            "mock_mode": self.mock_mode,
            "timestamp": time.time(),
        })
        
        try:
            # Use infra LLM if available
            if self._infra_llm:
                response = self._infra_llm.generate(prompt, system_message, response_format)
            elif self.mock_mode:
                # Mock response
                response = f"MOCK_RESPONSE[{prompt[:100]}...]"
            else:
                # Direct OpenAI call
                response = self._generate_direct(prompt, system_message, response_format)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Emit completion event
            self._emit("llm:call_completed", {
                "call_id": call_id,
                "model": self.model_name,
                "response_length": len(response) if response else 0,
                "response_preview": (response[:500] + "...") if response and len(response) > 500 else response,
                "duration_ms": duration_ms,
                "mock_mode": self.mock_mode,
                "timestamp": time.time(),
            })
            
            return response
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Emit error event
            self._emit("llm:call_failed", {
                "call_id": call_id,
                "model": self.model_name,
                "error": str(e),
                "duration_ms": duration_ms,
                "timestamp": time.time(),
            })
            raise
    
    def _generate_direct(
        self,
        prompt: str,
        system_message: str,
        response_format: Optional[Dict[str, Any]]
    ) -> str:
        """Generate response using direct OpenAI client."""
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        request_params = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,  # Use configured temperature
        }
        
        # Add max_tokens if configured
        if self.max_tokens:
            request_params["max_tokens"] = self.max_tokens
        
        if response_format:
            request_params["response_format"] = response_format
            # Add JSON instruction if needed
            if response_format.get("type") == "json_object" and "json" not in prompt.lower():
                messages[-1]["content"] += "\n\nYour response must be in JSON format."
        
        response = self.client.chat.completions.create(**request_params)
        return response.choices[0].message.content
    
    def run_prompt(self, prompt_template_name: str, **kwargs) -> str:
        """
        Run a prompt through the LLM using a template file.
        
        Args:
            prompt_template_name: Name of the prompt template file (without .txt)
            **kwargs: Variables to substitute in the template
            
        Returns:
            The LLM response
        """
        if self._infra_llm:
            return self._infra_llm.run_prompt(prompt_template_name, **kwargs)
        
        # Fallback - load template and generate
        template = self.load_prompt_template(prompt_template_name)
        prompt = template.safe_substitute(kwargs)
        return self.generate(prompt)
    
    def load_prompt_template(self, template_name: str) -> Template:
        """
        Load a prompt template from file.
        
        Args:
            template_name: Name of the template file (without .txt)
            
        Returns:
            A string.Template object
        """
        if self._infra_llm:
            return self._infra_llm.load_prompt_template(template_name)
        
        # Try to find the template
        try:
            from infra._constants import CURRENT_DIR
            prompt_path = os.path.join(CURRENT_DIR, "prompts", f"{template_name}.txt")
        except ImportError:
            prompt_path = os.path.join(os.path.dirname(__file__), "prompts", f"{template_name}.txt")
        
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Template file '{template_name}.txt' not found")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return Template(f.read())
    
    # =========================================================================
    # Factory methods for creating specialized generation functions
    # These proxy to the infra LanguageModel when available
    # =========================================================================
    
    def create_generation_function(self, prompt_template: str) -> Callable:
        """
        Create a generation function with a fixed prompt template.
        
        Args:
            prompt_template: The template string with $variable placeholders
            
        Returns:
            A callable that takes a vars dict and returns the LLM response
        """
        if self._infra_llm:
            return self._infra_llm.create_generation_function(prompt_template)
        
        def _generate_with(vars: Optional[Dict] = None) -> str:
            vars = vars or {}
            formatted_prompt = Template(prompt_template).safe_substitute(vars)
            return self.generate(formatted_prompt)
        
        return _generate_with
    
    def create_generation_function_with_template_in_vars(
        self,
        template_key: str = "prompt_template"
    ) -> Callable:
        """
        Create a generation function that gets the template from vars.
        
        Args:
            template_key: Key in vars dict containing the prompt template
            
        Returns:
            A callable that takes a vars dict and returns the LLM response
        """
        if self._infra_llm:
            return self._infra_llm.create_generation_function_with_template_in_vars(template_key)
        
        def _generate_with_template_in_vars(vars: Optional[Dict] = None) -> str:
            vars = vars or {}
            if template_key not in vars:
                return f"ERROR: Template key '{template_key}' not found in variables."
            
            prompt_template = vars[template_key]
            substitution_vars = {k: v for k, v in vars.items() if k != template_key}
            formatted_prompt = Template(str(prompt_template)).safe_substitute(substitution_vars)
            return self.generate(formatted_prompt)
        
        return _generate_with_template_in_vars
    
    def create_generation_function_with_template_in_vars_with_thinking(
        self,
        template_key: str = "prompt_template"
    ) -> Callable:
        """
        Create a generation function with JSON thinking output.
        
        Args:
            template_key: Key in vars dict containing the prompt template
            
        Returns:
            A callable that takes a vars dict and returns parsed JSON
        """
        if self._infra_llm:
            return self._infra_llm.create_generation_function_with_template_in_vars_with_thinking(template_key)
        
        def _generate_with_thinking(vars: Optional[Dict] = None) -> Any:
            vars = vars or {}
            if template_key not in vars:
                return {"error": f"Template key '{template_key}' not found"}
            
            prompt_template = vars[template_key]
            substitution_vars = {k: v for k, v in vars.items() if k != template_key}
            formatted_prompt = Template(str(prompt_template)).safe_substitute(substitution_vars)
            
            raw_response = self.generate(
                prompt=formatted_prompt,
                response_format={"type": "json_object"}
            )
            
            try:
                parsed = json.loads(raw_response)
                if isinstance(parsed, dict) and 'answer' in parsed:
                    return parsed['answer']
                return parsed
            except json.JSONDecodeError:
                return {"raw_response": raw_response, "error": "Failed to parse JSON"}
        
        return _generate_with_thinking
    
    def create_generation_function_thinking_json(self, prompt_template: str) -> Callable:
        """
        Create a generation function that expects JSON with thinking/output.
        
        Args:
            prompt_template: The template string
            
        Returns:
            A callable that returns parsed JSON response
        """
        if self._infra_llm:
            return self._infra_llm.create_generation_function_thinking_json(prompt_template)
        
        def _generate_with_thinking(vars: Optional[Dict] = None) -> Any:
            vars = vars or {}
            formatted_prompt = Template(prompt_template).safe_substitute(vars)
            
            raw_response = self.generate(
                prompt=formatted_prompt,
                response_format={"type": "json_object"}
            )
            
            try:
                parsed = json.loads(raw_response)
                return parsed.get("answer", parsed)
            except json.JSONDecodeError:
                return {"raw_response": raw_response, "error": "Failed to parse JSON"}
        
        return _generate_with_thinking
    
    def create_python_generate_and_run_function(
        self,
        prompt_key: str = "prompt_location",
        script_key: str = "script_location",
        with_thinking: bool = False,
        file_tool: Any = None,
        python_interpreter: Any = None
    ) -> Callable:
        """
        Create a function that generates and executes Python scripts.
        
        Proxies to infra LanguageModel when available.
        """
        if self._infra_llm:
            return self._infra_llm.create_python_generate_and_run_function(
                prompt_key=prompt_key,
                script_key=script_key,
                with_thinking=with_thinking,
                file_tool=file_tool,
                python_interpreter=python_interpreter
            )
        
        raise NotImplementedError(
            "create_python_generate_and_run_function requires infra LanguageModel"
        )
    
    def create_python_generate_and_run_function_from_prompt(
        self,
        prompt_template: str,
        script_key: str = "script_location",
        prompt_key: str = "prompt_location",
        with_thinking: bool = False,
        file_tool: Any = None,
        python_interpreter: Any = None
    ) -> Callable:
        """
        Create a function that uses a provided prompt to generate and run scripts.
        
        Proxies to infra LanguageModel when available.
        """
        if self._infra_llm:
            return self._infra_llm.create_python_generate_and_run_function_from_prompt(
                prompt_template=prompt_template,
                script_key=script_key,
                prompt_key=prompt_key,
                with_thinking=with_thinking,
                file_tool=file_tool,
                python_interpreter=python_interpreter
            )
        
        raise NotImplementedError(
            "create_python_generate_and_run_function_from_prompt requires infra LanguageModel"
        )
    
    def create_generation_function_with_composition(
        self,
        plan: List[Dict[str, Any]],
        return_key: Optional[str] = None
    ) -> Callable:
        """
        Create a composed generation function from an execution plan.
        
        Proxies to infra LanguageModel when available.
        """
        if self._infra_llm:
            return self._infra_llm.create_generation_function_with_composition(
                plan=plan,
                return_key=return_key
            )
        
        raise NotImplementedError(
            "create_generation_function_with_composition requires infra LanguageModel"
        )
    
    def expand_generation_function(
        self,
        base_generation_function: Callable,
        expansion_function: Callable,
        expansion_params: Optional[Dict] = None
    ) -> Callable:
        """
        Expand a generation function with an additional step.
        
        Proxies to infra LanguageModel when available.
        """
        if self._infra_llm:
            return self._infra_llm.expand_generation_function(
                base_generation_function,
                expansion_function,
                expansion_params
            )
        
        # Simple implementation
        expansion_params = dict(expansion_params or {})
        
        def _expanded(vars: Optional[Dict] = None):
            base_out = base_generation_function(vars or {})
            params = {**expansion_params, "new_record": base_out}
            return expansion_function(params)
        
        return _expanded
    
    # =========================================================================
    # Utility methods
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics for this LLM instance."""
        return {
            "model_name": self.model_name,
            "mock_mode": self.mock_mode,
            "call_count": self._call_count,
            "has_infra_llm": self._infra_llm is not None,
        }


def get_available_llm_models(settings_path: Optional[str] = None) -> List[str]:
    """
    Get list of available LLM models from settings.yaml.
    
    Args:
        settings_path: Path to settings.yaml file
        
    Returns:
        List of model names
    """
    if settings_path is None:
        # Try common locations - prefer same directory as this tool
        possible_paths = [
            os.path.join(os.path.dirname(__file__), "settings.yaml"),  # Same dir as llm_tool.py
        ]
        
        try:
            from infra._constants import PROJECT_ROOT
            possible_paths.append(os.path.join(PROJECT_ROOT, "settings.yaml"))
        except ImportError:
            pass
        
        possible_paths.append(os.path.join(os.getcwd(), "settings.yaml"))
        
        # Find first existing file
        for p in possible_paths:
            if os.path.exists(p):
                settings_path = p
                break
    
    models = ["demo"]  # Always include demo mode
    
    try:
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                settings = yaml.safe_load(f) or {}
            
            # Add models that have API keys configured
            for key, value in settings.items():
                if isinstance(value, dict) and 'DASHSCOPE_API_KEY' in value:
                    models.append(key)
    except Exception as e:
        logger.warning(f"Failed to load LLM models from settings: {e}")
    
    return models
