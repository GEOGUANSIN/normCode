"""
Question Sequencing Agent
Phase 1: Deconstructs instructive text into question sequences using LLM
"""

import logging
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from base_agent import BaseAgent, LLMRequest, LLMResponse
from prompt_database import PromptManager

logger = logging.getLogger(__name__)


@dataclass
class MainQuestion:
    """Main question structure"""
    type: str  # "what", "how", "when"
    target: str
    condition: str
    question: str


@dataclass
class QuestionAnswerPair:
    """Question-answer pair structure"""
    question: str
    answer: str
    chunk_index: int


@dataclass
class QuestionDecomposition:
    """Complete question decomposition result"""
    main_question: MainQuestion
    ensuing_questions: List[QuestionAnswerPair]
    decomposition_metadata: Dict[str, Any]


class QuestionSequencingAgent(BaseAgent[QuestionDecomposition]):
    """
    Phase 1 Agent: Deconstructs instructive text into question sequences using LLM
    
    Purpose: Deconstructs instructive text into question sequences
    Input: Natural language instructions (norm-text)
    Output: Structured question hierarchy with main and ensuing questions
    
    Usage Example:
        # Create agent
        agent = QuestionSequencingAgent(llm_client=your_llm_client)
        
        # Prepare NormCode terminology documents
        normcode_terminology = '''
        NormCode Syntax Reference:
        - $what?(target, condition): Asks what something is
        - $how?(target, condition): Asks how to do something  
        - $when?(target, condition): Asks when something happens
        - Conditions: $= (equals), $. (contains), $:: (is-a), $% (percentage)
        - Process markers: @by, @after, @before, @with
        - Conditional markers: @if, @onlyIf, @while, @until
        '''
        
        # Deconstruct with context
        result = agent.deconstruct(
            norm_text="Create a user account with email verification",
            prompt_context=normcode_terminology
        )
    """
    
    def __init__(self, llm_client=None, prompt_manager=None):
        super().__init__(llm_client, prompt_manager)
        self.question_markers = ["what", "how", "when"]
        self.condition_mappings = {
            "what": ["$=", "$.", "$::", "$%"],
            "how": ["@by", "@after", "@before", "@with"],
            "when": ["@if", "@onlyIf", "@ifOnlyIf", "@while", "@until", "@afterstep"]
        }
    
    def _get_agent_type(self) -> str:
        return "question_sequencing"
    
    def deconstruct(self, norm_text: str, main_question_type: Optional[str] = None, prompt_context: Optional[str] = None) -> QuestionDecomposition:
        """
        Deconstruct instructive text into question sequences using LLM
        
        Args:
            norm_text: Natural language instructions to deconstruct
            main_question_type: Optional forced question type
            prompt_context: Optional context containing NormCode terminology documents
            
        Returns:
            QuestionDecomposition: Complete question hierarchy
        """
        logger.info(f"Starting question sequencing for: {norm_text[:50]}...")
        
        # Step 1: Establish main question using LLM
        main_question = self._establish_main_question_llm(norm_text, main_question_type, prompt_context)
        
        # Step 2: Find sentence chunks using LLM
        sentence_chunks = self._find_sentence_chunks_llm(norm_text, prompt_context)
        
        # Step 3: Generate ensuing questions using LLM
        ensuing_questions = self._generate_ensuing_questions_llm(sentence_chunks, main_question, prompt_context)
        
        # Step 4: Create decomposition metadata
        decomposition_metadata = self._create_decomposition_metadata(
            norm_text, main_question, ensuing_questions, prompt_context
        )
        
        return QuestionDecomposition(
            main_question=main_question,
            ensuing_questions=ensuing_questions,
            decomposition_metadata=decomposition_metadata
        )
    
    def _establish_main_question_llm(self, norm_text: str, question_type: Optional[str] = None, prompt_context: Optional[str] = None) -> MainQuestion:
        """Establish the main question using LLM analysis"""
        prompt_params = {"norm_text": norm_text}
        if prompt_context:
            prompt_params["prompt_context"] = prompt_context
            
        request = self.create_llm_request(
            prompt_type="question_type_analysis",
            prompt_params=prompt_params,
            response_parser=self._parse_main_question_response,
            fallback_handler=lambda: self._fallback_main_question(norm_text, question_type, prompt_context)
        )
        
        response = self.call_llm(request)
        
        if response.success:
            return response.parsed_result
        else:
            logger.error(f"Failed to establish main question: {response.error_message}")
            return self._fallback_main_question(norm_text, question_type, prompt_context)
    
    def _find_sentence_chunks_llm(self, norm_text: str, prompt_context: Optional[str] = None) -> List[str]:
        """Find sentence chunks using LLM analysis"""
        prompt_params = {"norm_text": norm_text}
        if prompt_context:
            prompt_params["prompt_context"] = prompt_context
            
        request = self.create_llm_request(
            prompt_type="sentence_chunking",
            prompt_params=prompt_params,
            response_parser=self._parse_sentence_chunks_response,
            fallback_handler=lambda: self._fallback_sentence_chunks(norm_text, prompt_context)
        )
        
        response = self.call_llm(request)
        
        if response.success:
            return response.parsed_result
        else:
            logger.error(f"Failed to find sentence chunks: {response.error_message}")
            return self._fallback_sentence_chunks(norm_text, prompt_context)
    
    def _generate_ensuing_questions_llm(self, sentence_chunks: List[str], main_question: MainQuestion, prompt_context: Optional[str] = None) -> List[QuestionAnswerPair]:
        """Generate ensuing questions using LLM analysis"""
        ensuing_questions = []
        
        for i, chunk in enumerate(sentence_chunks):
            question_pair = self._generate_single_question_llm(chunk, i, main_question, prompt_context)
            ensuing_questions.append(question_pair)
        
        return ensuing_questions
    
    def _generate_single_question_llm(self, chunk: str, index: int, main_question: MainQuestion, prompt_context: Optional[str] = None) -> QuestionAnswerPair:
        """Generate a single question-answer pair using LLM"""
        prompt_params = {
            "main_question": main_question.question,
            "chunk": chunk,
            "index": index
        }
        if prompt_context:
            prompt_params["prompt_context"] = prompt_context
            
        request = self.create_llm_request(
            prompt_type="question_generation",
            prompt_params=prompt_params,
            response_parser=self._parse_question_generation_response,
            fallback_handler=lambda: self._fallback_question_generation(chunk, index, prompt_context)
        )
        
        response = self.call_llm(request)
        
        if response.success:
            return response.parsed_result
        else:
            logger.error(f"Failed to generate question: {response.error_message}")
            return self._fallback_question_generation(chunk, index, prompt_context)
    
    # Response parsers
    def _parse_main_question_response(self, response: str) -> MainQuestion:
        """Parse main question response"""
        result = json.loads(response)
        return MainQuestion(
            type=result.get("question_type", "what"),
            target=result.get("target", "{main_process}"),
            condition=result.get("condition", "$="),
            question=result.get("question", "$what?({main_process}, $=)")
        )
    
    def _parse_sentence_chunks_response(self, response: str) -> List[str]:
        """Parse sentence chunks response"""
        result = json.loads(response)
        chunks = result.get("sentence_chunks", [])
        return chunks if chunks else []
    
    def _parse_question_generation_response(self, response: str) -> QuestionAnswerPair:
        """Parse question generation response"""
        result = json.loads(response)
        return QuestionAnswerPair(
            question=result.get("question", f"$what?({{chunk_0}}, $=)"),
            answer=result.get("chunk", ""),  # This should be passed from the original chunk
            chunk_index=result.get("index", 0)
        )
    
    # Fallback handlers
    def _create_fallback_handler(self, request: LLMRequest) -> Callable[[], Any]:
        """Create fallback handler based on request type"""
        if request.prompt_type == "question_type_analysis":
            norm_text = request.prompt_params.get("norm_text", "")
            prompt_context = request.prompt_params.get("prompt_context")
            return lambda: self._fallback_main_question(norm_text, prompt_context=prompt_context)
        elif request.prompt_type == "sentence_chunking":
            norm_text = request.prompt_params.get("norm_text", "")
            prompt_context = request.prompt_params.get("prompt_context")
            return lambda: self._fallback_sentence_chunks(norm_text, prompt_context)
        elif request.prompt_type == "question_generation":
            chunk = request.prompt_params.get("chunk", "")
            index = request.prompt_params.get("index", 0)
            prompt_context = request.prompt_params.get("prompt_context")
            return lambda: self._fallback_question_generation(chunk, index, prompt_context)
        else:
            return lambda: None
    
    def _create_mock_response_generator(self, request: LLMRequest) -> Callable[[str], str]:
        """Create mock response generator based on request type"""
        def generate_mock_response(prompt: str) -> str:
            if request.prompt_type == "question_type_analysis":
                # Analyze the input text to determine question type
                norm_text = request.prompt_params.get("norm_text", "")
                question_type = self._analyze_question_type_simple(norm_text)
                target = "{main_process}"
                condition = self._select_condition(question_type)
                question = f"${question_type}?({target}, {condition})"
                
                return json.dumps({
                    "question_type": question_type,
                    "target": target,
                    "condition": condition,
                    "question": question,
                    "reasoning": f"Mock response: analyzed text and determined {question_type} type"
                })
            elif request.prompt_type == "sentence_chunking":
                # Split text into sentences for chunking
                norm_text = request.prompt_params.get("norm_text", "")
                sentences = [s.strip() for s in norm_text.split('.') if s.strip()]
                if not sentences:
                    sentences = [norm_text]  # If no periods, treat as single chunk
                
                return json.dumps({
                    "sentence_chunks": sentences,
                    "reasoning": f"Mock chunking: split into {len(sentences)} chunks"
                })
            elif request.prompt_type == "question_generation":
                # Generate appropriate question for the chunk
                chunk = request.prompt_params.get("chunk", "")
                index = request.prompt_params.get("index", 0)
                main_question = request.prompt_params.get("main_question", "$what?({main_process}, $=)")
                
                # Analyze chunk to determine question type
                chunk_question_type = self._analyze_question_type_simple(chunk)
                chunk_condition = self._select_condition(chunk_question_type)
                chunk_question = f"${chunk_question_type}?({{chunk_{index}}}, {chunk_condition})"
                
                return json.dumps({
                    "question": chunk_question,
                    "chunk": chunk,
                    "index": index,
                    "reasoning": f"Mock generation: created {chunk_question_type} question for chunk {index}"
                })
            else:
                return json.dumps({"error": "Unknown prompt type"})
        
        return generate_mock_response
    
    def _fallback_main_question(self, norm_text: str, question_type: Optional[str] = None, prompt_context: Optional[str] = None) -> MainQuestion:
        """Fallback method for main question establishment"""
        if not question_type:
            question_type = self._analyze_question_type_simple(norm_text)
        
        target = "{main_process}"
        condition = self._select_condition(question_type)
        question = f"${question_type}?({target}, {condition})"
        
        return MainQuestion(
            type=question_type,
            target=target,
            condition=condition,
            question=question
        )
    
    def _analyze_question_type_simple(self, norm_text: str) -> str:
        """Simple question type analysis as fallback"""
        text_lower = norm_text.lower()
        
        if any(word in text_lower for word in ["how", "process", "method", "steps", "procedure"]):
            return "how"
        elif any(word in text_lower for word in ["when", "if", "while", "until", "condition"]):
            return "when"
        else:
            return "what"
    
    def _fallback_sentence_chunks(self, norm_text: str, prompt_context: Optional[str] = None) -> List[str]:
        """Fallback method for sentence chunking"""
        sentences = [s.strip() for s in norm_text.split('.') if s.strip()]
        return sentences
    
    def _fallback_question_generation(self, chunk: str, index: int, prompt_context: Optional[str] = None) -> QuestionAnswerPair:
        """Fallback method for question generation"""
        return QuestionAnswerPair(
            question=f"$what?({{chunk_{index}}}, $=)",
            answer=chunk,
            chunk_index=index
        )
    
    def _select_condition(self, question_type: str) -> str:
        """Select appropriate condition based on question type"""
        conditions = self.condition_mappings.get(question_type, [])
        return conditions[0] if conditions else "$="
    
    def _create_decomposition_metadata(self, norm_text: str, main_question: MainQuestion, ensuing_questions: List[QuestionAnswerPair], prompt_context: Optional[str] = None) -> Dict[str, Any]:
        """Create metadata for the decomposition process"""
        metadata = {
            "original_text": norm_text,
            "text_length": len(norm_text),
            "chunk_count": len(ensuing_questions),
            "main_question_type": main_question.type,
            "processing_timestamp": "2024-01-01T00:00:00Z",  # TODO: Use actual timestamp
            "decomposition_version": "1.0",
            "llm_used": self.llm_client is not None,
            "prompt_database_used": True,
            "prompt_context_provided": prompt_context is not None,
        }
        
        if prompt_context:
            metadata["prompt_context_length"] = len(prompt_context)
            metadata["prompt_context_preview"] = prompt_context[:100] + "..." if len(prompt_context) > 100 else prompt_context
        
        return metadata 