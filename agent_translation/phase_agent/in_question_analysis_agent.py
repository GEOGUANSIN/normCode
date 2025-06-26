"""
In-Question Analysis Agent
Phase 2: Transforms questions and answers into formal NormCode structures
"""

import logging
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from base_agent import BaseAgent, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)


@dataclass
class NormCodeStructure:
    """NormCode structure result"""
    content: str
    validation_status: str
    errors: List[str]


@dataclass
class IndividualAnalysisResult:
    """Individual analysis result for a question-answer pair"""
    question: str
    answer: str
    normcode_structure: NormCodeStructure
    validation_status: str
    processing_time: float
    analysis_metadata: Dict[str, Any]


class InQuestionAnalysisAgent(BaseAgent[IndividualAnalysisResult]):
    """
    Phase 2 Agent: Transforms questions and answers into formal NormCode structures
    
    Purpose: Transforms questions and answers into formal NormCode structures
    Input: Question-answer pairs from Phase 1
    Output: Complete NormCode structures with templates and references
    """
    
    def __init__(self, llm_client=None, prompt_manager=None, model_name="qwen-turbo-latest"):
        super().__init__(llm_client, prompt_manager, model_name)
        self.clause_operators = {
            "coordinate": "across",
            "conditional": "@if",
            "sequential": "&in",
            "single": "direct"
        }
    
    def _get_agent_type(self) -> str:
        """Return the agent type identifier"""
        return "in_question_analysis"
    
    def _create_fallback_handler(self, request: LLMRequest) -> Callable[[], Any]:
        """Create a fallback handler for the specific request"""
        def fallback():
            return {
                "error": "Fallback response",
                "agent_type": self.agent_type,
                "request_type": request.prompt_type,
                "content": "Default NormCode structure"
            }
        return fallback
    
    def _create_mock_response_generator(self, request: LLMRequest) -> Callable[[str], str]:
        """Create a mock response generator for testing"""
        def mock_generator(prompt: str) -> str:
            return json.dumps({
                "result": "Mock response",
                "agent_type": self.agent_type,
                "content": "Mock NormCode structure",
                "validation_status": "mock"
            })
        return mock_generator
    
    def analyze(self, qa_pair: Dict[str, str]) -> IndividualAnalysisResult:
        """
        Analyze a single question-answer pair
        
        Args:
            qa_pair: Dictionary with 'question' and 'answer' keys
            
        Returns:
            IndividualAnalysisResult: Complete analysis result
        """
        import time
        start_time = time.time()
        
        question = qa_pair["question"]
        answer = qa_pair["answer"]
        
        logger.info(f"Starting in-question analysis for: {question}")
        
        # Phase 1: Question Analysis
        normcode_draft = self._phase1_question_analysis(question)
        
        # Phase 2: Clause Analysis
        normcode_draft = self._phase2_clause_analysis(normcode_draft, answer)
        
        # Phase 3: Template Creation
        final_structure = self._phase3_template_creation(normcode_draft)
        
        # Create analysis result
        processing_time = time.time() - start_time
        
        return IndividualAnalysisResult(
            question=question,
            answer=answer,
            normcode_structure=final_structure,
            validation_status=final_structure.validation_status,
            processing_time=processing_time,
            analysis_metadata=self._create_analysis_metadata(qa_pair, final_structure, processing_time)
        )
    
    def _phase1_question_analysis(self, question: str) -> str:
        """
        Phase 1: Parse and validate question structure
        
        Args:
            question: Formal question string
            
        Returns:
            str: Basic NormCode inference ground
        """
        # TODO: Implement question analysis
        # - Parse question marker, target, and condition
        # - Validate question structure
        # - Create basic NormCode inference ground
        
        # Simple parsing for now
        if "$what?" in question:
            # Extract target from question
            target_start = question.find("(") + 1
            target_end = question.find(",")
            target = question[target_start:target_end].strip()
            
            condition_start = question.find(",") + 1
            condition_end = question.find(")")
            condition = question[condition_start:condition_end].strip()
            
            normcode_draft = f"""{target}
    <= {condition}"""
        else:
            # Default structure
            normcode_draft = """{target}
    <= $="""
        
        return normcode_draft
    
    def _phase2_clause_analysis(self, normcode_draft: str, answer: str) -> str:
        """
        Phase 2: Analyze clauses and translate to NormCode syntax
        
        Args:
            normcode_draft: Current NormCode draft
            answer: Natural language answer
            
        Returns:
            str: Updated NormCode draft with clause analysis
        """
        # TODO: Implement clause analysis
        # - Identify sentence structure type (imperative/declarative)
        # - Classify clause types (single, coordinate, conditional, sequential)
        # - Translate clauses to appropriate NormCode syntax
        # - Apply appropriate operators
        
        # Analyze sentence structure
        structure_type = self._identify_sentence_structure(answer)
        clause_type = self._classify_clause_type(answer)
        
        # Translate to NormCode syntax
        normcode_clause = self._translate_clause_to_normcode(answer, structure_type, clause_type)
        
        # Add to draft
        updated_draft = normcode_draft + f"\n    <- {normcode_clause}"
        
        return updated_draft
    
    def _identify_sentence_structure(self, sentence: str) -> str:
        """
        Identify if sentence is imperative or declarative
        
        Args:
            sentence: The sentence to analyze
            
        Returns:
            str: Structure type (imperative/declarative)
        """
        # TODO: Implement sentence structure identification
        # - Use NLP techniques to identify sentence type
        # - Look for imperative keywords
        # - Analyze sentence patterns
        
        sentence_lower = sentence.lower()
        
        imperative_keywords = ["mix", "add", "bake", "stir", "combine", "pour", "heat", "cook", "prepare", "create"]
        
        if any(keyword in sentence_lower for keyword in imperative_keywords):
            return "imperative"
        else:
            return "declarative"
    
    def _classify_clause_type(self, sentence: str) -> str:
        """
        Classify clause type
        
        Args:
            sentence: The sentence to classify
            
        Returns:
            str: Clause type (single/coordinate/conditional/sequential)
        """
        # TODO: Implement clause classification
        # - Identify coordinate conjunctions (and, or, but)
        # - Identify conditional conjunctions (if, when, while, until)
        # - Identify sequential markers (first, then, next, finally)
        
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in [" and ", " or ", " but ", " nor "]):
            return "coordinate"
        elif any(word in sentence_lower for word in ["if", "when", "while", "until", "unless"]):
            return "conditional"
        elif any(word in sentence_lower for word in ["first", "then", "next", "finally", "after"]):
            return "sequential"
        else:
            return "single"
    
    def _translate_clause_to_normcode(self, sentence: str, structure_type: str, clause_type: str) -> str:
        """
        Translate clause to NormCode syntax
        
        Args:
            sentence: The sentence to translate
            structure_type: Structure type (imperative/declarative)
            clause_type: Clause type (single/coordinate/conditional/sequential)
            
        Returns:
            str: NormCode syntax representation
        """
        # TODO: Implement clause translation
        # - Handle different clause types with appropriate operators
        # - Apply coordinate logic with 'across' operator
        # - Apply conditional logic with '@if' operator
        # - Apply sequential logic with '&in' operator
        
        if clause_type == "coordinate":
            return self._translate_coordinate_clause(sentence)
        elif clause_type == "conditional":
            return self._translate_conditional_clause(sentence)
        elif clause_type == "sequential":
            return self._translate_sequential_clause(sentence)
        else:
            return self._translate_single_clause(sentence, structure_type)
    
    def _translate_coordinate_clause(self, sentence: str) -> str:
        """
        Translate coordinate clause with 'and'/'or' logic
        
        Args:
            sentence: The coordinate sentence
            
        Returns:
            str: NormCode syntax for coordinate clause
        """
        # TODO: Implement coordinate clause translation
        # - Split by coordinate conjunctions
        # - Create 'across' operator structure
        # - Handle multiple sub-clauses
        
        return f"<{sentence}>"
    
    def _translate_conditional_clause(self, sentence: str) -> str:
        """
        Translate conditional clause
        
        Args:
            sentence: The conditional sentence
            
        Returns:
            str: NormCode syntax for conditional clause
        """
        # TODO: Implement conditional clause translation
        # - Parse condition and action
        # - Create '@if' operator structure
        # - Handle complex conditional logic
        
        return f"::({sentence})"
    
    def _translate_sequential_clause(self, sentence: str) -> str:
        """
        Translate sequential clause
        
        Args:
            sentence: The sequential sentence
            
        Returns:
            str: NormCode syntax for sequential clause
        """
        # TODO: Implement sequential clause translation
        # - Handle ordering of actions
        # - Create '&in' operator structure
        # - Maintain sequence relationships
        
        return f"::({sentence})"
    
    def _translate_single_clause(self, sentence: str, structure_type: str) -> str:
        """
        Translate single clause
        
        Args:
            sentence: The single clause sentence
            structure_type: Structure type (imperative/declarative)
            
        Returns:
            str: NormCode syntax for single clause
        """
        if structure_type == "imperative":
            return f"::({sentence})"
        else:
            return f"<{sentence}>"
    
    def _phase3_template_creation(self, normcode_draft: str) -> NormCodeStructure:
        """
        Phase 3: Create templates and reference mappings
        
        Args:
            normcode_draft: Current NormCode draft
            
        Returns:
            NormCodeStructure: Complete structure with templates
        """
        # TODO: Implement template creation
        # - Add template abstractions with typed placeholders
        # - Create reference mappings between concrete and abstract levels
        # - Preserve logical structure
        # - Validate template integrity
        
        # For now, return the draft as-is
        return NormCodeStructure(
            content=normcode_draft,
            validation_status="pending",
            errors=[]
        )
    
    def _create_analysis_metadata(self, qa_pair: Dict[str, str], structure: NormCodeStructure, processing_time: float) -> Dict[str, Any]:
        """
        Create metadata for the analysis process
        
        Args:
            qa_pair: Original question-answer pair
            structure: Generated NormCode structure
            processing_time: Time taken for analysis
            
        Returns:
            Dict[str, Any]: Analysis metadata
        """
        return {
            "question": qa_pair["question"],
            "answer_length": len(qa_pair["answer"]),
            "structure_length": len(structure.content),
            "processing_time": processing_time,
            "validation_status": structure.validation_status,
            "error_count": len(structure.errors),
            "analysis_version": "1.0"
        } 