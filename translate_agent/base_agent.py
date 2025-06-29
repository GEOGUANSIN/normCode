"""
Base Agent Framework
Abstract base class for all NormCode agents with common LLM interaction patterns
"""

import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypeVar, Generic, Callable
from dataclasses import dataclass
from prompt_manager import PromptManager
import os
from openai import OpenAI

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Generic type for agent-specific result types

# Try to load .env file from project root if python-dotenv is available
try:
    from dotenv import load_dotenv
    # Look for .env in the project root (2 levels up from this file)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, '.env')
    load_dotenv(env_path)
except ImportError:
    pass  # Continue without .env support


class LLMFactory:
    """
    Ultra-simple LLM client factory
    """

    def __init__(self, 
                 model_name="qwen-turbo-latest", 
                 base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                 api_key=None):
        """
        Initialize LLM client

        Args:
            model_name (str): Name of the model to use
            base_url (str): Base URL for the endpoint
            api_key (str): API key (will use environment variable if not provided)
        """
        self.model_name = model_name
        
        # Get API key from parameter or environment
        if api_key is None:
            api_key = os.getenv('DASHSCOPE_API_KEY')
            if not api_key:
                raise ValueError("API key not provided and DASHSCOPE_API_KEY environment variable not set")
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def ask(self, prompt: str, system_message: str = "You are a helpful assistant.", temperature: float = 0, max_tokens: int = 2048) -> str:
        """
        Ask a question to the LLM
        
        Args:
            prompt (str): The prompt/question to send to the LLM
            system_message (str): Optional system message
            temperature (float): Controls randomness (0 = deterministic)
            max_tokens (int): Maximum number of tokens in response
            
        Returns:
            str: The LLM response
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content


@dataclass
class LLMRequest:
    """Structure for LLM request configuration"""
    agent_type: str
    prompt_type: str
    prompt_params: Dict[str, Any]
    response_parser: Optional[Callable[[dict], Any]] = None


@dataclass
class LLMResponse:
    """Structure for LLM response handling"""
    raw_response: str
    parsed_result: Any
    success: bool
    error_message: Optional[str] = None


class BaseAgent(ABC, Generic[T]):
    """
    Abstract base class for all NormCode agents
    
    Provides common functionality for:
    - LLM interaction with prompt database
    - Response parsing and error handling
    """
    
    def __init__(self, llm_client=None, prompt_manager=None, model_name="qwen-turbo-latest"):
        """
        Initialize BaseAgent with LLMFactory integration
        
        Args:
            llm_client: Optional custom LLM client (if None, creates LLMFactory instance)
            prompt_manager: Optional custom prompt manager
            model_name: Model name for LLMFactory (default: qwen-turbo-latest)
        """
        # Initialize LLM client
        if llm_client is None:
            self.llm_client = LLMFactory(model_name=model_name)
        else:
            self.llm_client = llm_client
            
        # Initialize prompt manager with file mode as default
        self.prompt_manager = prompt_manager or PromptManager(mode="file")
        self.agent_type = self._get_agent_type()
    
    @abstractmethod
    def _get_agent_type(self) -> str:
        """Return the agent type identifier"""
        pass
    
    def call_llm(self, request: LLMRequest) -> LLMResponse:
        """
        Generic LLM interaction method
        
        Args:
            request: LLMRequest configuration
            
        Returns:
            LLMResponse: Structured response with parsed result
        """
        # Get prompt from manager
        prompt = self.prompt_manager.get_prompt(request.agent_type, request.prompt_type)
        
        if not prompt:
            return LLMResponse(
                raw_response="",
                parsed_result=None,
                success=False,
                error_message="Prompt retrieval failed"
            )
        
        # Format prompt with parameters
        try:
            formatted_prompt = prompt.format(**request.prompt_params)
        except KeyError as e:
            return LLMResponse(
                raw_response="",
                parsed_result=None,
                success=False,
                error_message=f"Missing prompt parameter: {e}"
            )
        
        # Call LLM
        try:
            raw_response = self.llm_client.ask(formatted_prompt)
            return self._parse_response(raw_response, request)
        except Exception as e:
            return LLMResponse(
                raw_response="",
                parsed_result=None,
                success=False,
                error_message=str(e)
            )
    
    def _parse_response(self, raw_response: str, request: LLMRequest) -> LLMResponse:
        """Parse LLM response using the provided parser"""
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith('```json'):
                # Remove ```json and ``` markers
                cleaned_response = cleaned_response.split('```json')[1].split('```')[0].strip()
            elif cleaned_response.startswith('```'):
                # Remove generic ``` markers
                cleaned_response = cleaned_response.split('```')[1].split('```')[0].strip()
            # Always parse JSON first since LLM is configured to return JSON format
            parsed_json = json.loads(cleaned_response)
            
            # If a custom parser is provided, apply it to the parsed JSON
            if request.response_parser:
                parsed_result = request.response_parser(parsed_json)
            else:
                parsed_result = parsed_json
            
            return LLMResponse(
                raw_response=raw_response,
                parsed_result=parsed_result,
                success=True
            )
        except json.JSONDecodeError as e:
            return LLMResponse(
                raw_response=raw_response,
                parsed_result=None,
                success=False,
                error_message=f"JSON parsing failed: {e}. Cleaned response: {cleaned_response if 'cleaned_response' in locals() else 'N/A'}"
            )
        except Exception as e:
            return LLMResponse(
                raw_response=raw_response,
                parsed_result=None,
                success=False,
                error_message=f"Response parsing failed: {e}"
            )
    
    def create_llm_request(
        self, 
        prompt_type: str, 
        prompt_params: Dict[str, Any],
        response_parser: Optional[Callable[[dict], Any]] = None
    ) -> LLMRequest:
        """
        Create an LLMRequest configuration
        
        Args:
            prompt_type: Type of prompt to use
            prompt_params: Parameters for prompt formatting
            response_parser: Custom response parser function
            
        Returns:
            LLMRequest: Configured request
        """
        return LLMRequest(
            agent_type=self.agent_type,
            prompt_type=prompt_type,
            prompt_params=prompt_params,
            response_parser=response_parser
        ) 