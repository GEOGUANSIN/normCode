"""
Question Sequencing Agent
Phase 1: Deconstructs instructive text into question sequences using LLM
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import sys
import os

# Add the parent directory to the path so we can import base_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agent import BaseAgent, LLMRequest, LLMResponse
from result_manager import ResultManager

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
    
    Core Functionalities:
    1. Establish main question from input text
    2. Split text into sentence chunks
    3. Generate ensuing questions for each chunk
    4. Return structured question decomposition
    5. Save results to files by default
    
    Args:
        llm_client: Optional custom LLM client (if None, creates LLMFactory instance)
        prompt_manager: Optional custom prompt manager
        result_manager: Optional custom result manager (if None, creates file-based ResultManager)
        llm_model: LLM model name (default: "qwen-turbo-latest")
        verbose: Enable verbose logging (default: False)
    """
    
    def __init__(self, llm_client=None, prompt_manager=None, result_manager=None, llm_model="qwen-turbo-latest", verbose=False):
        super().__init__(llm_client, prompt_manager, model_name=llm_model)
        self.verbose = verbose
        
        # Initialize result manager (file-based by default)
        if result_manager is None:
            results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
            self.result_manager = ResultManager(mode="file", results_dir=results_dir)
        else:
            self.result_manager = result_manager
    
    def _get_agent_type(self) -> str:
        return "question_sequencing"
    
    def deconstruct(self, norm_text: str, prompt_context: Optional[str] = None, save_result: bool = True) -> QuestionDecomposition:
        """
        Core method: Deconstruct instructive text into question sequences
        
        Args:
            norm_text: Natural language instructions to deconstruct
            prompt_context: Optional context containing NormCode terminology
            save_result: Whether to save the result to file (default: True)
            
        Returns:
            QuestionDecomposition: Complete question hierarchy
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"QUESTION SEQUENCING AGENT - VERBOSE MODE")
            print(f"{'='*60}")
            print(f"Input text: {norm_text[:100]}{'...' if len(norm_text) > 100 else ''}")
            print(f"Text length: {len(norm_text)} characters")
            print(f"Prompt context: {'Provided' if prompt_context else 'None'}")
            print(f"Save result: {save_result}")
            print(f"{'='*60}\n")
        
        # Step 1: Establish main question
        if self.verbose:
            print("STEP 1: Establishing main question...")
        main_question = self._establish_main_question(norm_text, prompt_context)
        if self.verbose:
            print(f"  ✓ Main question established:")
            print(f"    Type: {main_question.type}")
            print(f"    Target: {main_question.target}")
            print(f"    Condition: {main_question.condition}")
            print(f"    Question: {main_question.question}")
            print()
        
        # Step 2: Split into sentence chunks
        if self.verbose:
            print("STEP 2: Splitting text into sentence chunks...")
        sentence_chunks = self._split_into_chunks(norm_text, prompt_context)
        if self.verbose:
            print(f"  ✓ Text split into {len(sentence_chunks)} chunks:")
            for i, chunk in enumerate(sentence_chunks):
                print(f"    Chunk {i}: {chunk[:80]}{'...' if len(chunk) > 80 else ''}")
            print()
        
        # Step 3: Generate ensuing questions
        if self.verbose:
            print("STEP 3: Generating ensuing questions for each chunk...")
        ensuing_questions = self._generate_ensuing_questions(sentence_chunks, main_question, prompt_context, norm_text)
        if self.verbose:
            print(f"  ✓ Generated {len(ensuing_questions)} question-answer pairs:")
            for i, qa_pair in enumerate(ensuing_questions):
                print(f"    Pair {i}:")
                print(f"      Question: {qa_pair.question}")
                print(f"      Answer: {qa_pair.answer[:60]}{'...' if len(qa_pair.answer) > 60 else ''}")
                print(f"      Chunk index: {qa_pair.chunk_index}")
            print()
        
        # Step 4: Create metadata
        if self.verbose:
            print("STEP 4: Creating metadata...")
        metadata = self._create_metadata(norm_text, main_question, ensuing_questions)
        if self.verbose:
            print(f"  ✓ Metadata created:")
            for key, value in metadata.items():
                print(f"    {key}: {value}")
            print()
        
        result = QuestionDecomposition(
            main_question=main_question,
            ensuing_questions=ensuing_questions,
            decomposition_metadata=metadata
        )
        
        # Step 5: Save result if requested
        if save_result:
            if self.verbose:
                print("STEP 5: Saving result to file...")
            try:
                # Convert result to serializable format
                result_data = {
                    "main_question": {
                        "type": result.main_question.type,
                        "target": result.main_question.target,
                        "condition": result.main_question.condition,
                        "question": result.main_question.question
                    },
                    "ensuing_questions": [
                        {
                            "question": qa.question,
                            "answer": qa.answer,
                            "chunk_index": qa.chunk_index
                        }
                        for qa in result.ensuing_questions
                    ],
                    "decomposition_metadata": result.decomposition_metadata
                }
                
                # Generate session ID from input text hash
                import hashlib
                session_id = hashlib.md5(norm_text.encode()).hexdigest()[:8]
                
                saved_path = self.result_manager.save_result(
                    agent_type="question_sequencing",
                    result_type="decomposition",
                    result_data=result_data,
                    session_id=session_id,
                    input_hash=hashlib.md5(norm_text.encode()).hexdigest(),
                    metadata={
                        "text_length": len(norm_text),
                        "chunk_count": len(ensuing_questions),
                        "main_question_type": main_question.type
                    }
                )
                
                if self.verbose:
                    print(f"  ✓ Result saved to: {saved_path}")
                    print()
            except Exception as e:
                if self.verbose:
                    print(f"  ⚠ Warning: Failed to save result: {e}")
                    print()
        
        if self.verbose:
            print(f"{'='*60}")
            print(f"DECONSTRUCTION COMPLETE")
            print(f"{'='*60}")
            print(f"Total chunks processed: {len(ensuing_questions)}")
            print(f"Main question type: {main_question.type}")
            print(f"Processing timestamp: {metadata['processing_timestamp']}")
            print(f"{'='*60}\n")
        
        return result
    
    def _establish_main_question(self, norm_text: str, prompt_context: Optional[str] = None) -> MainQuestion:
        """Establish the main question using LLM"""
        if self.verbose:
            print(f"    Making LLM request for main question analysis...")
        
        prompt_params = {"norm_text": norm_text}
        if prompt_context:
            prompt_params["prompt_context"] = prompt_context
            
        request = self.create_llm_request(
            prompt_type="question_type_analysis",
            prompt_params=prompt_params,
            response_parser=self._parse_main_question_response
        )
        
        response = self.call_llm(request)
        if not response.success:
            if self.verbose:
                print(f"    ❌ LLM request failed: {response.error_message}")
                print(f"    Raw response: '{response.raw_response}'")
            raise Exception(f"Failed to establish main question: {response.error_message}")
        
        if self.verbose:
            print(f"    LLM response received successfully")
            print(f"    Raw response: '{response.raw_response[:200]}{'...' if len(response.raw_response) > 200 else ''}'")
        
        return response.parsed_result
    
    def _split_into_chunks(self, norm_text: str, prompt_context: Optional[str] = None) -> List[str]:
        """Split text into sentence chunks using LLM"""
        if self.verbose:
            print(f"    Making LLM request for sentence chunking...")
        
        prompt_params = {"norm_text": norm_text}
        if prompt_context:
            prompt_params["prompt_context"] = prompt_context
            
        request = self.create_llm_request(
            prompt_type="sentence_chunking",
            prompt_params=prompt_params,
            response_parser=self._parse_sentence_chunks_response
        )
        
        response = self.call_llm(request)
        if not response.success:
            if self.verbose:
                print(f"    ❌ LLM request failed: {response.error_message}")
                print(f"    Raw response: '{response.raw_response}'")
            raise Exception(f"Failed to split into chunks: {response.error_message}")
        
        if self.verbose:
            print(f"    LLM response received successfully")
            print(f"    Raw response: '{response.raw_response[:200]}{'...' if len(response.raw_response) > 200 else ''}'")
        
        return response.parsed_result
    
    def _generate_ensuing_questions(self, sentence_chunks: List[str], main_question: MainQuestion, prompt_context: Optional[str] = None, norm_text: str = "") -> List[QuestionAnswerPair]:
        """Generate ensuing questions for each chunk"""
        ensuing_questions = []
        
        for i, chunk in enumerate(sentence_chunks):
            if self.verbose:
                print(f"    Processing chunk {i+1}/{len(sentence_chunks)}...")
            
            prompt_params = {
                "main_question": main_question.question,
                "chunk": chunk,
                "index": i,
                "norm_text": norm_text
            }
            if prompt_context:
                prompt_params["prompt_context"] = prompt_context
                
            request = self.create_llm_request(
                prompt_type="chunk_question_generation",
                prompt_params=prompt_params,
                response_parser=self._parse_question_generation_response
            )
            
            response = self.call_llm(request)
            if not response.success:
                if self.verbose:
                    print(f"    ❌ LLM request failed for chunk {i+1}: {response.error_message}")
                    print(f"    Raw response: '{response.raw_response}'")
                raise Exception(f"Failed to generate question for chunk {i}: {response.error_message}")
            
            if self.verbose:
                print(f"    LLM response received for chunk {i+1}")
                print(f"    Raw response: '{response.raw_response[:150]}{'...' if len(response.raw_response) > 150 else ''}'")
            
            # Use the chunk as the answer
            ensuing_questions.append(
                QuestionAnswerPair(
                    question=response.parsed_result.question,
                    answer=chunk,
                    chunk_index=i
                )
            )
        
        return ensuing_questions
    
    # Response parsers
    def _parse_main_question_response(self, response: dict) -> MainQuestion:
        """Parse main question response"""
        return MainQuestion(
            type=response.get("question_type", "what"),
            target=response.get("target", "{main_process}"),
            condition=response.get("condition", "$="),
            question=response.get("question", "$what?({main_process}, $=)")
        )
    
    def _parse_sentence_chunks_response(self, response: dict) -> List[str]:
        """Parse sentence chunks response"""
        chunks = response.get("sentence_chunks", [])
        return chunks if chunks else []
    
    def _parse_question_generation_response(self, response: dict) -> QuestionAnswerPair:
        """Parse question generation response"""
        return QuestionAnswerPair(
            question=response.get("question", f"$what?({{chunk_0}}, $=)"),
            answer=response.get("chunk", ""),
            chunk_index=response.get("index", 0)
        )
    
    def _create_metadata(self, norm_text: str, main_question: MainQuestion, ensuing_questions: List[QuestionAnswerPair]) -> Dict[str, Any]:
        """Create simple metadata for the decomposition"""
        return {
            "original_text": norm_text,
            "text_length": len(norm_text),
            "chunk_count": len(ensuing_questions),
            "main_question_type": main_question.type,
            "processing_timestamp": "2024-01-01T00:00:00Z"
        }
    
if __name__ == "__main__":
    try:
        print("Initializing QuestionSequencingAgent...")
        
        # Create agent with verbose mode enabled
        agent = QuestionSequencingAgent(verbose=True, llm_model="qwen-turbo-latest")  # Use default model
        print("Agent created successfully")

        print("Retrieving NormCode context...")
        normcode_context = agent.prompt_manager.get_prompt("general", "context")
        if normcode_context:
            print(f"  ✓ general/context: Retrieved ({len(normcode_context)} characters)")
        else:
            print("  ⚠ No context found")

        norm_text = "Create a password for a new user account. The password should be at least 8 characters long and include a mix of uppercase and lowercase letters, numbers, and special characters."

        print("Starting deconstruction process...")
        result = agent.deconstruct(norm_text, normcode_context)
        
        # Print final result summary
        print("\nFINAL RESULT:")
        print(f"Main Question: {result.main_question.question}")
        print(f"Number of Q&A pairs: {len(result.ensuing_questions)}")
        print(f"Metadata: {result.decomposition_metadata}")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()