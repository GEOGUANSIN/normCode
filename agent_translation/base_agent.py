"""
Base Agent Framework
Abstract base class for all NormCode agents with common LLM interaction patterns
"""

import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypeVar, Generic, Callable
from dataclasses import dataclass
from prompt_database import PromptManager
from LLMFactory import LLMFactory

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Generic type for agent-specific result types


@dataclass
class LLMRequest:
    """Structure for LLM request configuration"""
    agent_type: str
    prompt_type: str
    prompt_params: Dict[str, Any]
    response_parser: Optional[Callable[[str], Any]] = None
    fallback_handler: Optional[Callable[[], Any]] = None
    mock_response_generator: Optional[Callable[[str], str]] = None


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
    - Fallback mechanisms
    - Mock responses for testing
    """
    
    def __init__(self, llm_client=None, prompt_manager=None, model_name="qwen-turbo-latest"):
        """
        Initialize BaseAgent with LLMFactory integration
        
        Args:
            llm_client: Optional custom LLM client (if None, creates LLMFactory instance)
            prompt_manager: Optional custom prompt manager
            model_name: Model name for LLMFactory (default: qwen-turbo-latest)
        """
        # Initialize LLM client - use provided client or create LLMFactory instance
        if llm_client is None:
            try:
                self.llm_client = LLMFactory(model_name=model_name)
                logger.info(f"Created LLMFactory instance with model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to create LLMFactory instance: {e}. Using mock responses.")
                self.llm_client = None
        else:
            self.llm_client = llm_client
            
        self.prompt_manager = prompt_manager or PromptManager()
        self.agent_type = self._get_agent_type()
        self.model_name = model_name
    
    @abstractmethod
    def _get_agent_type(self) -> str:
        """Return the agent type identifier"""
        pass
    
    @abstractmethod
    def _create_fallback_handler(self, request: LLMRequest) -> Callable[[], Any]:
        """Create a fallback handler for the specific request"""
        pass
    
    @abstractmethod
    def _create_mock_response_generator(self, request: LLMRequest) -> Callable[[str], str]:
        """Create a mock response generator for testing"""
        pass
    
    def call_llm(self, request: LLMRequest, llm_client=None) -> LLMResponse:
        """
        Generic LLM interaction method
        
        Args:
            request: LLMRequest configuration
            llm_client: Optional LLM client override for this request
            
        Returns:
            LLMResponse: Structured response with parsed result
        """
        logger.info(f"Making LLM request: {request.agent_type}.{request.prompt_type}")
        
        # Get prompt from database
        prompt = self.prompt_manager.format_prompt(
            request.agent_type, 
            request.prompt_type, 
            **request.prompt_params
        )
        
        if not prompt:
            logger.error(f"Failed to get prompt: {request.agent_type}.{request.prompt_type}")
            return self._handle_prompt_failure(request)
        
        # Use provided llm_client or fall back to instance llm_client
        client_to_use = llm_client or self.llm_client
        
        # Call LLM
        raw_response = self._call_llm_raw_with_client(prompt, client_to_use)
        
        # Parse response
        return self._parse_llm_response(raw_response, request)
    
    def _call_llm_raw(self, prompt: str) -> str:
        """
        Make raw LLM call using the instance's LLM client (backward compatibility)
        
        Args:
            prompt: Formatted prompt string
            
        Returns:
            str: Raw LLM response
        """
        return self._call_llm_raw_with_client(prompt, self.llm_client)
    
    def _call_llm_raw_with_client(self, prompt: str, llm_client) -> str:
        """
        Make raw LLM call using specified client
        
        Args:
            prompt: Formatted prompt string
            llm_client: LLM client to use
            
        Returns:
            str: Raw LLM response
        """
        if llm_client is None:
            logger.warning("No LLM client available, using mock response")
            return self._generate_mock_response(prompt)
        
        try:
            # Check if it's an LLMFactory instance
            if isinstance(llm_client, LLMFactory):
                response = llm_client.ask(prompt)
                logger.debug(f"LLMFactory response received for model: {llm_client.model_name}")
                return response
            # Fallback for other LLM client types that have ask method
            elif hasattr(llm_client, 'ask'):
                response = llm_client.ask(prompt)
                return response
            else:
                logger.warning("LLM client doesn't have ask method, using mock response")
                return self._generate_mock_response(prompt)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return self._generate_mock_response(prompt)
    
    def _parse_llm_response(self, raw_response: str, request: LLMRequest) -> LLMResponse:
        """
        Parse LLM response using the provided parser
        
        Args:
            raw_response: Raw LLM response string
            request: Original request configuration
            
        Returns:
            LLMResponse: Parsed response structure
        """
        try:
            if request.response_parser:
                parsed_result = request.response_parser(raw_response)
            else:
                # Default JSON parsing
                parsed_result = json.loads(raw_response)
            
            return LLMResponse(
                raw_response=raw_response,
                parsed_result=parsed_result,
                success=True
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {raw_response}")
            return self._handle_parsing_failure(raw_response, request, str(e))
        except Exception as e:
            logger.error(f"Response parsing failed: {e}")
            return self._handle_parsing_failure(raw_response, request, str(e))
    
    def _handle_prompt_failure(self, request: LLMRequest) -> LLMResponse:
        """Handle prompt retrieval failure"""
        if request.fallback_handler:
            try:
                fallback_result = request.fallback_handler()
                return LLMResponse(
                    raw_response="",
                    parsed_result=fallback_result,
                    success=True,
                    error_message="Used fallback handler due to prompt failure"
                )
            except Exception as e:
                logger.error(f"Fallback handler failed: {e}")
        
        return LLMResponse(
            raw_response="",
            parsed_result=None,
            success=False,
            error_message="Prompt retrieval failed and no fallback available"
        )
    
    def _handle_parsing_failure(self, raw_response: str, request: LLMRequest, error: str) -> LLMResponse:
        """Handle response parsing failure"""
        if request.fallback_handler:
            try:
                fallback_result = request.fallback_handler()
                return LLMResponse(
                    raw_response=raw_response,
                    parsed_result=fallback_result,
                    success=True,
                    error_message=f"Used fallback handler due to parsing failure: {error}"
                )
            except Exception as e:
                logger.error(f"Fallback handler failed: {e}")
        
        return LLMResponse(
            raw_response=raw_response,
            parsed_result=None,
            success=False,
            error_message=f"Response parsing failed: {error}"
        )
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate mock response for testing"""
        # This can be overridden by subclasses for agent-specific mock responses
        return json.dumps({"error": "Mock response not implemented"})
    
    def create_llm_factory(self, model_name: str = None) -> LLMFactory:
        """
        Create a new LLMFactory instance with specified model
        
        Args:
            model_name: Model name (defaults to instance model_name)
            
        Returns:
            LLMFactory: New LLMFactory instance
        """
        model = model_name or self.model_name
        try:
            return LLMFactory(model_name=model)
        except Exception as e:
            logger.error(f"Failed to create LLMFactory with model {model}: {e}")
            raise
    
    def create_llm_request(
        self, 
        prompt_type: str, 
        prompt_params: Dict[str, Any],
        response_parser: Optional[Callable[[str], Any]] = None,
        fallback_handler: Optional[Callable[[], Any]] = None,
        mock_response_generator: Optional[Callable[[str], str]] = None,
        model_name: str = None
    ) -> LLMRequest:
        """
        Create an LLMRequest configuration
        
        Args:
            prompt_type: Type of prompt to use
            prompt_params: Parameters for prompt formatting
            response_parser: Custom response parser function
            fallback_handler: Fallback handler function
            mock_response_generator: Mock response generator function
            model_name: Optional model name override for this request
            
        Returns:
            LLMRequest: Configured request
        """
        return LLMRequest(
            agent_type=self.agent_type,
            prompt_type=prompt_type,
            prompt_params=prompt_params,
            response_parser=response_parser,
            fallback_handler=fallback_handler or self._create_fallback_handler,
            mock_response_generator=mock_response_generator or self._create_mock_response_generator
        )
    
    def call_llm_with_model(self, request: LLMRequest, model_name: str = None) -> LLMResponse:
        """
        Call LLM with optional model override
        
        Args:
            request: LLMRequest configuration
            model_name: Optional model name override
            
        Returns:
            LLMResponse: Structured response with parsed result
        """
        # If model_name is specified and different from current, create temporary client
        if model_name and model_name != self.model_name:
            try:
                temp_llm_client = self.create_llm_factory(model_name)
                logger.info(f"Using temporary LLMFactory for request with model: {model_name}")
                return self.call_llm(request, llm_client=temp_llm_client)
            except Exception as e:
                logger.warning(f"Failed to create temporary LLMFactory, using default: {e}")
        
        # Use default client
        return self.call_llm(request)
    
    def batch_llm_calls(self, requests: List[LLMRequest]) -> List[LLMResponse]:
        """
        Make multiple LLM calls in batch
        
        Args:
            requests: List of LLMRequest configurations
            
        Returns:
            List[LLMResponse]: List of responses
        """
        responses = []
        for request in requests:
            response = self.call_llm(request)
            responses.append(response)
        return responses 