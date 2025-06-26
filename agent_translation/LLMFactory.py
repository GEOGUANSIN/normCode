import yaml
import os
import json
from string import Template
from openai import OpenAI
from constantpath import CURRENT_DIR, PROJECT_ROOT


class LLMFactory:
    """
    Factory class to create LLM instances based on model name and configuration
    """

    def __init__(self, 
                 model_name = "deepseek-v3", 
                 settings_path=os.path.join(PROJECT_ROOT, "settings.yaml"),
                 base_url: str = None,
                 api_key: str = None):
        """
        Initialize LLM with specified model from settings

        Args:
            model_name (str): Name of the model to use
            settings_path (str): Path to the settings YAML file
            base_url (str): Optional custom base URL for local endpoints
            api_key (str): Optional custom API key
        """
        self.model_name = model_name
        self.settings_path = settings_path

        # Load settings
        with open(settings_path, 'r') as f:
            self.settings = yaml.safe_load(f)

        # Validate model exists in settings (only if not using custom base_url)
        if base_url is None and model_name not in self.settings:
            raise ValueError(f"Model '{model_name}' not found in settings")

        # Get API key - use custom if provided, otherwise from settings
        if api_key is not None:
            self.api_key = api_key
        elif base_url is None:
            self.api_key = self.settings[model_name].get('DASHSCOPE_API_KEY')
            if not self.api_key:
                raise ValueError(f"API key not found for model '{model_name}'")
        else:
            # For local endpoints, use a dummy key if none provided
            self.api_key = api_key or "dummy-key"

        # Get base URL - use custom if provided, otherwise from settings
        if base_url is not None:
            self.base_url = base_url
        else:
            self.base_url = self.settings.get('BASE_URL', "https://dashscope.aliyuncs.com/compatible-mode/v1")

        # Initialize OpenAI client
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def create_llamaindex_wrapper(self):
        """
        Create a LlamaIndex wrapper for this LLMFactory instance
        
        Returns:
            LLMFactoryWrapper: Wrapped instance compatible with LlamaIndex
        """
        try:
            from .llm_wrapper import LLMFactoryWrapper
            return LLMFactoryWrapper(self)
        except ImportError:
            raise ImportError("LLMFactoryWrapper not available. Make sure llm_wrapper.py is in the same directory.")

    def ask(self, prompt: str, system_message: str = "You are a helpful assistant.", temperature: float = 0, max_tokens: int = 2048) -> str:
        """
        Simple method to ask a question with a complete prompt string
        
        Args:
            prompt (str): The complete prompt/question to send to the LLM
            system_message (str): Optional system message to set context
            temperature (float): Controls randomness (0 = deterministic, 1 = very random)
            max_tokens (int): Maximum number of tokens in the response
            
        Returns:
            str: The LLM response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"Failed to get response from LLM: {e}")

    def run_prompt(self, prompt_template_name, **kwargs):
        """
        Run a prompt through the LLM using a template with safe variable substitution

        Args:
            prompt_template_name (str): name of the prompt template file
            **kwargs: Variables to substitute in the template using $variable_name format

        Returns:
            str: The LLM response, sanitized for CSV storage
        """
        # Load prompt template
        prompt_template_path = os.path.join(CURRENT_DIR, "prompts", f"{prompt_template_name}.txt")
        with open(prompt_template_path, 'r', encoding="utf-8") as f:
            template = Template(f.read())

        # Replace variables in template using safe substitution
        try:
            prompt = template.safe_substitute(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing required variable in prompt template: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid template variable: {e}")

        # Run the prompt through the LLM
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "system", "content": "You are a linguistic analysis system."},
                      {"role": "user", "content": prompt}],
            response_format={"type": "text"},
            temperature=0
        )

        # Get the raw response content and sanitize for CSV storage
        raw_response = response.choices[0].message.content
        # Replace newlines and carriage returns with spaces
        sanitized_response = raw_response.replace('\n', ' ').replace('\r', ' ')
        # Remove any double spaces created by the replacement
        sanitized_response = ' '.join(sanitized_response.split())
        # Handle quotes and commas to avoid CSV parsing issues
        sanitized_response = sanitized_response.replace('"', "'").replace('",', ',').replace(',"', ',')
        return sanitized_response

    @classmethod
    def create_for_local_endpoint(cls, 
                                 model_name: str, 
                                 base_url: str, 
                                 api_key: str = None):
        """
        Create LLMFactory instance for a local LLM endpoint
        
        Args:
            model_name (str): Name of the model
            base_url (str): Base URL for the local endpoint
            api_key (str): Optional API key for authentication
            
        Returns:
            LLMFactory: Configured instance for local endpoint
        """
        return cls(
            model_name=model_name,
            base_url=base_url,
            api_key=api_key
        )

    @classmethod
    def create_with_custom_settings(cls, 
                                   model_name: str, 
                                   base_url: str, 
                                   api_key: str,
                                   settings_path: str = None):
        """
        Create LLMFactory instance with custom settings
        
        Args:
            model_name (str): Name of the model
            base_url (str): Base URL for the endpoint
            api_key (str): API key for authentication
            settings_path (str): Optional path to settings file
            
        Returns:
            LLMFactory: Configured instance
        """
        return cls(
            model_name=model_name,
            settings_path=settings_path or os.path.join(PROJECT_ROOT, "settings.yaml"),
            base_url=base_url,
            api_key=api_key
        )