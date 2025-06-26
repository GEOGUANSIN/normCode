"""
LlamaIndex Base Agent Framework
LlamaIndex-based implementation of the BaseAgent with RAG capabilities
"""

import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, TypeVar, Generic, Callable
from dataclasses import dataclass

# LlamaIndex imports
from llama_index.core import VectorStoreIndex, Document, Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import QueryBundle
from llama_index.llms.openai import OpenAI
from llama_index.core.prompts import PromptTemplate
from llama_index.core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Generic type for agent-specific result types


@dataclass
class LlamaIndexRequest:
    """Structure for LlamaIndex request configuration"""
    query: str
    prompt_template: str
    output_parser: Optional[Callable] = None
    response_mode: str = "compact"
    similarity_top_k: int = 2
    documents: Optional[List[Document]] = None


@dataclass
class LlamaIndexResponse:
    """Structure for LlamaIndex response handling"""
    raw_response: str
    parsed_result: Any
    success: bool
    error_message: Optional[str] = None
    source_nodes: List[Any] = None


class LlamaIndexBaseAgent(ABC, Generic[T]):
    """
    LlamaIndex-based abstract base class for all NormCode agents
    
    Provides common functionality for:
    - Document indexing and retrieval
    - Query engine setup with RAG capabilities
    - Response synthesis and parsing
    - Fallback mechanisms
    - Mock responses for testing
    """
    
    def __init__(self, 
                 llm_model: str = "gpt-3.5-turbo", 
                 documents: List[Document] = None,
                 llm_instance = None):
        """
        Initialize the base agent with LLM configuration
        
        Args:
            llm_model: Model name (default: "gpt-3.5-turbo")
            documents: Initial documents for indexing
            llm_instance: Pre-configured LLM instance (overrides llm_model)
        """
        # Initialize LLM - either use provided instance or create new one
        if llm_instance is not None:
            self.llm = llm_instance
            logger.info(f"Using provided LLM instance: {type(llm_instance).__name__}")
        else:
            # Use default OpenAI LLM
            self.llm = OpenAI(model=llm_model)
            logger.info(f"Using default OpenAI LLM: {llm_model}")
        
        Settings.llm = self.llm
        
        # Initialize documents and index
        self.documents = documents or []
        self.index = None
        self.query_engine = None
        self.agent_type = self._get_agent_type()
        
        if self.documents:
            self._build_index()
    
    @abstractmethod
    def _get_agent_type(self) -> str:
        """Return the agent type identifier"""
        pass
    
    @abstractmethod
    def _create_fallback_handler(self, request: LlamaIndexRequest) -> Callable[[], Any]:
        """Create a fallback handler for the specific request"""
        pass
    
    @abstractmethod
    def _create_mock_response_generator(self, request: LlamaIndexRequest) -> Callable[[str], str]:
        """Create a mock response generator for testing"""
        pass
    
    def _build_index(self):
        """Build vector index from documents"""
        if not self.documents:
            logger.warning("No documents provided, creating empty index")
            self.index = VectorStoreIndex([])
        else:
            self.index = VectorStoreIndex.from_documents(self.documents)
        self._setup_query_engine()
    
    def _setup_query_engine(self):
        """Setup query engine with retriever and response synthesizer"""
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=2
        )
        
        response_synthesizer = get_response_synthesizer(
            response_mode="compact",
            llm=self.llm
        )
        
        self.query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer
        )
    
    def add_documents(self, documents: List[Document]):
        """Add documents to the index"""
        self.documents.extend(documents)
        if self.index:
            # Rebuild index with new documents
            self._build_index()
    
    def call_llm(self, request: LlamaIndexRequest) -> LlamaIndexResponse:
        """
        Generic LlamaIndex query method
        
        Args:
            request: LlamaIndexRequest configuration
            
        Returns:
            LlamaIndexResponse: Structured response with parsed result
        """
        logger.info(f"Making LlamaIndex request: {request.prompt_template[:50]}...")
        
        try:
            # Add any additional documents for this specific request
            if request.documents:
                temp_index = VectorStoreIndex.from_documents(request.documents)
                temp_retriever = VectorIndexRetriever(
                    index=temp_index,
                    similarity_top_k=request.similarity_top_k
                )
                temp_synthesizer = get_response_synthesizer(
                    response_mode=request.response_mode,
                    llm=self.llm
                )
                temp_query_engine = RetrieverQueryEngine(
                    retriever=temp_retriever,
                    response_synthesizer=temp_synthesizer
                )
            else:
                temp_query_engine = self.query_engine
            
            if not temp_query_engine:
                logger.error("No query engine available")
                return self._handle_query_failure(request, "No query engine available")
            
            # Create query bundle
            query_bundle = QueryBundle(query_str=request.query)
            
            # Execute query
            response = temp_query_engine.query(query_bundle)
            
            # Parse response if parser provided
            parsed_result = None
            if request.output_parser:
                try:
                    parsed_result = request.output_parser(response.response)
                except Exception as e:
                    logger.error(f"Output parsing failed: {e}")
                    return self._handle_parsing_failure(response.response, request, str(e))
            else:
                parsed_result = response.response
            
            return LlamaIndexResponse(
                raw_response=response.response,
                parsed_result=parsed_result,
                success=True,
                source_nodes=response.source_nodes
            )
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return self._handle_query_failure(request, str(e))
    
    def _handle_query_failure(self, request: LlamaIndexRequest, error: str) -> LlamaIndexResponse:
        """Handle query execution failure"""
        if request.fallback_handler:
            try:
                fallback_result = request.fallback_handler()
                return LlamaIndexResponse(
                    raw_response="",
                    parsed_result=fallback_result,
                    success=True,
                    error_message=f"Used fallback handler due to query failure: {error}"
                )
            except Exception as e:
                logger.error(f"Fallback handler failed: {e}")
        
        return LlamaIndexResponse(
            raw_response="",
            parsed_result=None,
            success=False,
            error_message=f"Query execution failed: {error}"
        )
    
    def _handle_parsing_failure(self, raw_response: str, request: LlamaIndexRequest, error: str) -> LlamaIndexResponse:
        """Handle response parsing failure"""
        if request.fallback_handler:
            try:
                fallback_result = request.fallback_handler()
                return LlamaIndexResponse(
                    raw_response=raw_response,
                    parsed_result=fallback_result,
                    success=True,
                    error_message=f"Used fallback handler due to parsing failure: {error}"
                )
            except Exception as e:
                logger.error(f"Fallback handler failed: {e}")
        
        return LlamaIndexResponse(
            raw_response=raw_response,
            parsed_result=None,
            success=False,
            error_message=f"Response parsing failed: {error}"
        )
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Generate mock response for testing"""
        # This can be overridden by subclasses for agent-specific mock responses
        return json.dumps({"error": "Mock response not implemented"})
    
    def create_llm_request(
        self, 
        query: str,
        prompt_template: str,
        output_parser: Optional[Callable] = None,
        response_mode: str = "compact",
        similarity_top_k: int = 2,
        documents: Optional[List[Document]] = None,
        fallback_handler: Optional[Callable[[], Any]] = None,
        mock_response_generator: Optional[Callable[[str], str]] = None
    ) -> LlamaIndexRequest:
        """
        Create a LlamaIndexRequest configuration
        
        Args:
            query: The query string
            prompt_template: Prompt template string
            output_parser: Output parser function
            response_mode: Response synthesis mode
            similarity_top_k: Number of similar documents to retrieve
            documents: Additional documents for this specific request
            fallback_handler: Fallback handler function
            mock_response_generator: Mock response generator function
            
        Returns:
            LlamaIndexRequest: Configured request
        """
        return LlamaIndexRequest(
            query=query,
            prompt_template=prompt_template,
            output_parser=output_parser,
            response_mode=response_mode,
            similarity_top_k=similarity_top_k,
            documents=documents,
            fallback_handler=fallback_handler or self._create_fallback_handler,
            mock_response_generator=mock_response_generator or self._create_mock_response_generator
        )
    
    def create_prompt_template(self, template_str: str) -> PromptTemplate:
        """Create a prompt template"""
        return PromptTemplate(template_str)
    
    def create_pydantic_parser(self, model_class) -> PydanticOutputParser:
        """Create a Pydantic output parser"""
        return PydanticOutputParser(pydantic_object=model_class)
    
    def batch_llm_calls(self, requests: List[LlamaIndexRequest]) -> List[LlamaIndexResponse]:
        """
        Make multiple LlamaIndex calls in batch
        
        Args:
            requests: List of LlamaIndexRequest configurations
            
        Returns:
            List[LlamaIndexResponse]: List of responses
        """
        responses = []
        for request in requests:
            response = self.call_llm(request)
            responses.append(response)
        return responses
    
    def query_with_context(self, query: str, context_documents: List[Document]) -> LlamaIndexResponse:
        """
        Query with specific context documents
        
        Args:
            query: The query string
            context_documents: Documents to use as context
            
        Returns:
            LlamaIndexResponse: Response with context
        """
        request = self.create_llm_request(
            query=query,
            prompt_template=query,  # Simple template for context queries
            documents=context_documents
        )
        
        return self.call_llm(request)
    
    def get_relevant_documents(self, query: str, top_k: int = 5) -> List[Any]:
        """
        Get relevant documents for a query
        
        Args:
            query: The query string
            top_k: Number of documents to retrieve
            
        Returns:
            List[Any]: Relevant documents
        """
        if not self.index:
            return []
        
        retriever = VectorIndexRetriever(
            index=self.index,
            similarity_top_k=top_k
        )
        
        query_bundle = QueryBundle(query_str=query)
        nodes = retriever.retrieve(query_bundle)
        
        return nodes 