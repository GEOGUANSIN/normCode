"""
Pipeline Agent
Combines Question Sequencing Agent (Phase 1) and In-Question Analysis Agent (Phase 2)
Processes instructive text through complete deconstruction and analysis pipeline
"""

import logging
import json
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import base_agent
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from base_agent import BaseAgent, LLMRequest, LLMResponse
from result_manager import ResultManager
from phase_agent.question_sequencing_agent import QuestionSequencingAgent, QuestionDecomposition
from phase_agent.in_question_analysis_agent import InQuestionAnalysisAgent, InQuestionAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete pipeline result containing all phases"""
    # Phase 1: Question Decomposition
    main_question: Dict[str, Any]
    ensuing_questions: List[Dict[str, Any]]
    decomposition_metadata: Dict[str, Any]
    
    # Phase 2: Question Analysis Results
    question_analyses: List[Dict[str, Any]]
    
    # Pipeline Metadata
    pipeline_metadata: Dict[str, Any]
    processing_timestamp: str
    input_text_hash: str


class PipelineAgent(BaseAgent[PipelineResult]):
    """
    Pipeline Agent: Combines Phase 1 (Question Sequencing) and Phase 2 (In-Question Analysis)
    
    Workflow:
    1. Phase 1: Deconstruct instructive text into question sequences
    2. Phase 2: Analyze each question-answer pair into NormCode structures
    3. Combine all results into single comprehensive JSON output
    
    Args:
        llm_client: Optional custom LLM client
        prompt_manager: Optional custom prompt manager
        result_manager: Optional custom result manager
        llm_model: LLM model name (default: "qwen-turbo-latest")
        verbose: Enable verbose logging (default: False)
    """
    
    def __init__(self, llm_client=None, prompt_manager=None, result_manager=None, llm_model="qwen-turbo-latest", verbose=False):
        super().__init__(llm_client, prompt_manager, model_name=llm_model)
        self.verbose = verbose
        
        # Initialize result manager (file-based by default)
        if result_manager is None:
            results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
            self.result_manager = ResultManager(mode="file", results_dir=results_dir)
        else:
            self.result_manager = result_manager
        
        # Initialize phase agents
        self.question_sequencing_agent = QuestionSequencingAgent(
            llm_client=llm_client,
            prompt_manager=prompt_manager,
            result_manager=None,  # We'll handle result management at pipeline level
            llm_model=llm_model,
            verbose=verbose
        )
        
        self.in_question_analysis_agent = InQuestionAnalysisAgent(
            llm_client=llm_client,
            prompt_manager=prompt_manager,
            result_manager=None,  # We'll handle result management at pipeline level
            llm_model=llm_model,
            verbose=verbose
        )
    
    def _get_agent_type(self) -> str:
        return "pipeline"
    
    def process(self, norm_text: str, prompt_context: Optional[str] = None, save_result: bool = True) -> PipelineResult:
        """
        Core method: Process instructive text through complete pipeline
        
        Args:
            norm_text: Natural language instructions to process
            prompt_context: Optional context containing NormCode terminology (if None, will retrieve from prompt manager)
            save_result: Whether to save the result to file (default: True)
            
        Returns:
            PipelineResult: Complete pipeline result with all phases
        """
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"PIPELINE AGENT - COMPLETE PROCESSING")
            print(f"{'='*80}")
            print(f"Input text: {norm_text[:100]}{'...' if len(norm_text) > 100 else ''}")
            print(f"Text length: {len(norm_text)} characters")
            print(f"Prompt context: {'Provided' if prompt_context else 'Will retrieve from prompt manager'}")
            print(f"Save result: {save_result}")
            print(f"{'='*80}\n")
        
        # Retrieve NormCode context if not provided
        if prompt_context is None:
            if self.verbose:
                print("Retrieving NormCode context from prompt manager...")
            prompt_context = self.prompt_manager.get_prompt("general", "context")
            if prompt_context:
                if self.verbose:
                    print(f"✓ NormCode context retrieved ({len(prompt_context)} characters)")
            else:
                if self.verbose:
                    print("⚠ No NormCode context found in prompt manager")
                prompt_context = ""  # Use empty string as fallback
        
        # Generate input hash for tracking
        input_hash = hashlib.md5(norm_text.encode()).hexdigest()
        
        # Phase 1: Question Decomposition
        if self.verbose:
            print("PHASE 1: Question Decomposition (Question Sequencing Agent)")
            print("-" * 60)
        
        decomposition = self.question_sequencing_agent.deconstruct(
            norm_text=norm_text,
            prompt_context=prompt_context,
            save_result=False  # We'll save everything at pipeline level
        )
        
        if self.verbose:
            print(f"✓ Phase 1 completed:")
            print(f"  Main question: {decomposition.main_question.question}")
            print(f"  Question-answer pairs: {len(decomposition.ensuing_questions)}")
            print()
        
        # Phase 2: Question Analysis for each pair
        if self.verbose:
            print("PHASE 2: Question Analysis (In-Question Analysis Agent)")
            print("-" * 60)
        
        question_analyses = []
        
        # Analyze main question if it has an answer (use first chunk as answer)
        if decomposition.ensuing_questions:
            main_answer = decomposition.ensuing_questions[0].answer
            if self.verbose:
                print(f"Analyzing main question: {decomposition.main_question.question}")
            
            main_analysis = self.in_question_analysis_agent.analyze(
                question=decomposition.main_question.question,
                answer=main_answer,
                prompt_context=prompt_context,
                save_result=False
            )
            
            # Convert to serializable format
            main_analysis_data = self._serialize_analysis_result(main_analysis, "main_question")
            question_analyses.append(main_analysis_data)
            
            if self.verbose:
                print(f"✓ Main question analysis completed")
        
        # Analyze each ensuing question-answer pair
        for i, qa_pair in enumerate(decomposition.ensuing_questions):
            if self.verbose:
                print(f"Analyzing question-answer pair {i+1}/{len(decomposition.ensuing_questions)}")
                print(f"  Question: {qa_pair.question}")
                print(f"  Answer: {qa_pair.answer[:60]}{'...' if len(qa_pair.answer) > 60 else ''}")
            
            analysis = self.in_question_analysis_agent.analyze(
                question=qa_pair.question,
                answer=qa_pair.answer,
                prompt_context=prompt_context,
                save_result=False
            )
            
            # Convert to serializable format
            analysis_data = self._serialize_analysis_result(analysis, f"ensuing_question_{i}")
            question_analyses.append(analysis_data)
            
            if self.verbose:
                print(f"✓ Question-answer pair {i+1} analysis completed")
        
        if self.verbose:
            print(f"✓ Phase 2 completed: {len(question_analyses)} analyses")
            print()
        
        # Create pipeline metadata
        if self.verbose:
            print("Creating pipeline metadata...")
        
        pipeline_metadata = self._create_pipeline_metadata(
            norm_text=norm_text,
            decomposition=decomposition,
            question_analyses=question_analyses
        )
        
        if self.verbose:
            print(f"✓ Pipeline metadata created:")
            for key, value in pipeline_metadata.items():
                print(f"  {key}: {value}")
            print()
        
        # Create final result
        result = PipelineResult(
            main_question=asdict(decomposition.main_question),
            ensuing_questions=[asdict(qa) for qa in decomposition.ensuing_questions],
            decomposition_metadata=decomposition.decomposition_metadata,
            question_analyses=question_analyses,
            pipeline_metadata=pipeline_metadata,
            processing_timestamp=datetime.now().isoformat(),
            input_text_hash=input_hash
        )
        
        # Save result if requested
        if save_result:
            if self.verbose:
                print("Saving complete pipeline result...")
            
            try:
                # Convert result to serializable format
                result_data = asdict(result)
                
                # Generate session ID from input text hash
                session_id = input_hash[:8]
                
                saved_path = self.result_manager.save_result(
                    agent_type="pipeline",
                    result_type="complete_analysis",
                    result_data=result_data,
                    session_id=session_id,
                    input_hash=input_hash,
                    metadata={
                        "text_length": len(norm_text),
                        "question_pairs_count": len(decomposition.ensuing_questions),
                        "analysis_count": len(question_analyses)
                    }
                )
                
                if self.verbose:
                    print(f"✓ Complete pipeline result saved to: {saved_path}")
                    print()
            except Exception as e:
                if self.verbose:
                    print(f"⚠ Warning: Failed to save pipeline result: {e}")
                    print()
        
        if self.verbose:
            print(f"{'='*80}")
            print(f"PIPELINE COMPLETED SUCCESSFULLY")
            print(f"{'='*80}")
            print(f"Total question-answer pairs processed: {len(decomposition.ensuing_questions)}")
            print(f"Total analyses completed: {len(question_analyses)}")
            print(f"Result saved: {save_result}")
            print(f"{'='*80}\n")
        
        return result
    
    def _serialize_analysis_result(self, analysis: InQuestionAnalysisResult, analysis_id: str) -> Dict[str, Any]:
        """
        Convert InQuestionAnalysisResult to serializable dictionary format
        
        Args:
            analysis: InQuestionAnalysisResult object
            analysis_id: Identifier for this analysis
            
        Returns:
            Dict containing serialized analysis data
        """
        return {
            "analysis_id": analysis_id,
            "question_structure": {
                "marker": analysis.question_structure.marker,
                "target": analysis.question_structure.target,
                "condition": analysis.question_structure.condition,
                "question": analysis.question_structure.question
            },
            "clause_analysis": {
                "structure_type": analysis.clause_analysis.structure_type,
                "clause_count": analysis.clause_analysis.clause_count,
                "clause_types": analysis.clause_analysis.clause_types,
                "clauses": analysis.clause_analysis.clauses
            },
            "phase1_draft": {
                "target": analysis.phase1_draft.target,
                "condition": analysis.phase1_draft.condition,
                "content": analysis.phase1_draft.content,
                "horizontal_layout": analysis.phase1_draft.horizontal_layout
            },
            "phase2_draft": {
                "target": analysis.phase2_draft.target,
                "condition": analysis.phase2_draft.condition,
                "content": analysis.phase2_draft.content,
                "horizontal_layout": analysis.phase2_draft.horizontal_layout
            },
            "phase3_draft": {
                "target": analysis.phase3_draft.target,
                "condition": analysis.phase3_draft.condition,
                "content": analysis.phase3_draft.content,
                "horizontal_layout": analysis.phase3_draft.horizontal_layout
            },
            "template_mappings": [
                {
                    "concrete_term": mapping.concrete_term,
                    "abstract_placeholder": mapping.abstract_placeholder,
                    "placeholder_type": mapping.placeholder_type
                }
                for mapping in analysis.template_mappings
            ],
            "analysis_metadata": analysis.analysis_metadata
        }
    
    def _create_pipeline_metadata(self, norm_text: str, decomposition: QuestionDecomposition, question_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create comprehensive metadata for the pipeline result
        
        Args:
            norm_text: Original input text
            decomposition: Question decomposition result
            question_analyses: List of question analysis results
            
        Returns:
            Dict containing pipeline metadata
        """
        return {
            "pipeline_version": "1.0",
            "input_text_length": len(norm_text),
            "main_question_type": decomposition.main_question.type,
            "question_pairs_count": len(decomposition.ensuing_questions),
            "total_analyses_count": len(question_analyses),
            "decomposition_metadata": decomposition.decomposition_metadata,
            "analysis_summary": {
                "total_template_mappings": sum(
                    len(analysis.get("template_mappings", [])) 
                    for analysis in question_analyses
                ),
                "average_clause_count": sum(
                    analysis.get("clause_analysis", {}).get("clause_count", 0)
                    for analysis in question_analyses
                ) / len(question_analyses) if question_analyses else 0,
                "structure_types": list(set(
                    analysis.get("clause_analysis", {}).get("structure_type", "")
                    for analysis in question_analyses
                ))
            }
        }
    
    def get_pipeline_summary(self, result: PipelineResult) -> Dict[str, Any]:
        """
        Generate a summary of the pipeline result
        
        Args:
            result: PipelineResult object
            
        Returns:
            Dict containing summary information
        """
        return {
            "pipeline_status": "completed",
            "processing_timestamp": result.processing_timestamp,
            "input_text_hash": result.input_text_hash,
            "main_question": result.main_question["question"],
            "question_pairs_processed": len(result.ensuing_questions),
            "analyses_completed": len(result.question_analyses),
            "total_template_mappings": sum(
                len(analysis.get("template_mappings", [])) 
                for analysis in result.question_analyses
            ),
            "pipeline_metadata": result.pipeline_metadata
        }
    
    def export_to_json(self, result: PipelineResult, filepath: Optional[str] = None) -> str:
        """
        Export pipeline result to JSON file
        
        Args:
            result: PipelineResult object
            filepath: Optional custom filepath (if None, uses default naming)
            
        Returns:
            Path to the exported JSON file
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(
                self.result_manager.results_dir,
                f"pipeline_export_{result.input_text_hash[:8]}_{timestamp}.json"
            )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Convert to serializable format and save
        result_data = asdict(result)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        if self.verbose:
            print(f"✓ Pipeline result exported to: {filepath}")
        
        return filepath