"""
In-Question Analysis Agent
Phase 2: Transforms question-answer pairs into formal NormCode structures
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
class QuestionStructure:
    """Formal question structure"""
    marker: str  # $what?, $how?, $when?
    target: str  # The entity, imperative, or judgement being questioned
    condition: str  # $=, $::, @by, @onlyIf, @If, etc.
    question: str  # Full formatted question


@dataclass
class ClauseAnalysis:
    """Clause analysis result"""
    structure_type: str  # "imperative" or "declarative"
    clause_count: int
    clause_types: List[str]  # "single", "coordinate", "conditional", "sequential"
    clauses: List[str]  # Individual clause texts


@dataclass
class NormCodeDraft:
    """NormCode draft structure"""
    target: str
    condition: str
    content: str
    horizontal_layout: str


@dataclass
class TemplateMapping:
    """Template reference mapping"""
    concrete_term: str
    abstract_placeholder: str
    placeholder_type: str


@dataclass
class InQuestionAnalysisResult:
    """Complete in-question analysis result"""
    question_structure: QuestionStructure
    clause_analysis: ClauseAnalysis
    phase1_draft: NormCodeDraft
    phase2_draft: NormCodeDraft
    phase3_draft: NormCodeDraft
    template_mappings: List[TemplateMapping]
    analysis_metadata: Dict[str, Any]


class InQuestionAnalysisAgent(BaseAgent[InQuestionAnalysisResult]):
    """
    Phase 2 Agent: Transforms question-answer pairs into formal NormCode structures
    
    Three phases:
    1. Question Analysis - Parse formal question structure
    2. Clause Analysis - Analyze sentence structure and clauses
    3. Template Creation - Create abstract templates with references
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
        return "in_question_analysis"
    
    def analyze(self, question: str, answer: str, prompt_context: Optional[str] = None, save_result: bool = True) -> InQuestionAnalysisResult:
        """
        Core method: Analyze question-answer pair into NormCode structure
        
        Args:
            question: Formal question in format "question_marker(question_target, question_condition)"
            answer: Natural language answer to the question
            prompt_context: Optional context containing NormCode terminology
            save_result: Whether to save the result to file (default: True)
            
        Returns:
            InQuestionAnalysisResult: Complete three-phase analysis
        """
        if self.verbose:
            print(f"\n{'='*60}")
            print(f"IN-QUESTION ANALYSIS AGENT - VERBOSE MODE")
            print(f"{'='*60}")
            print(f"Question: {question}")
            print(f"Answer: {answer[:100]}{'...' if len(answer) > 100 else ''}")
            print(f"Answer length: {len(answer)} characters")
            print(f"Prompt context: {'Provided' if prompt_context else 'None'}")
            print(f"Save result: {save_result}")
            print(f"{'='*60}\n")
        
        # Phase 1: Question Analysis
        if self.verbose:
            print("PHASE 1: Question Analysis...")
        question_structure = self._analyze_question_structure(question, prompt_context)
        phase1_draft = self._create_phase1_draft(question_structure)
        if self.verbose:
            print(f"  ✓ Question structure analyzed:")
            print(f"    Marker: {question_structure.marker}")
            print(f"    Target: {question_structure.target}")
            print(f"    Condition: {question_structure.condition}")
            print(f"    Question: {question_structure.question}")
            print(f"  ✓ Phase 1 draft created:")
            print(f"    {phase1_draft.content}")
            print()
        
        # Phase 2: Clause Analysis
        if self.verbose:
            print("PHASE 2: Clause Analysis...")
        clause_analysis = self._analyze_clauses(answer, prompt_context)
        phase2_draft = self._create_phase2_draft(phase1_draft, clause_analysis, answer, prompt_context)
        if self.verbose:
            print(f"  ✓ Clause analysis completed:")
            print(f"    Structure type: {clause_analysis.structure_type}")
            print(f"    Clause count: {clause_analysis.clause_count}")
            print(f"    Clause types: {clause_analysis.clause_types}")
            print(f"  ✓ Phase 2 draft created:")
            print(f"    {phase2_draft.content}")
            print()
        
        # Phase 3: Template Creation
        if self.verbose:
            print("PHASE 3: Template Creation...")
        phase3_draft, template_mappings = self._create_templates(phase2_draft, prompt_context)
        if self.verbose:
            print(f"  ✓ Template creation completed:")
            print(f"    Template mappings: {len(template_mappings)}")
            for mapping in template_mappings:
                print(f"      {mapping.concrete_term} -> {mapping.abstract_placeholder} ({mapping.placeholder_type})")
            print(f"  ✓ Phase 3 draft created:")
            print(f"    {phase3_draft.content}")
            print()
        
        # Create metadata
        if self.verbose:
            print("Creating metadata...")
        metadata = self._create_metadata(question, answer, question_structure, clause_analysis)
        if self.verbose:
            print(f"  ✓ Metadata created:")
            for key, value in metadata.items():
                print(f"    {key}: {value}")
            print()
        
        result = InQuestionAnalysisResult(
            question_structure=question_structure,
            clause_analysis=clause_analysis,
            phase1_draft=phase1_draft,
            phase2_draft=phase2_draft,
            phase3_draft=phase3_draft,
            template_mappings=template_mappings,
            analysis_metadata=metadata
        )
        
        # Save result if requested
        if save_result:
            if self.verbose:
                print("Saving result to file...")
            try:
                # Convert result to serializable format
                result_data = {
                    "question_structure": {
                        "marker": result.question_structure.marker,
                        "target": result.question_structure.target,
                        "condition": result.question_structure.condition,
                        "question": result.question_structure.question
                    },
                    "clause_analysis": {
                        "structure_type": result.clause_analysis.structure_type,
                        "clause_count": result.clause_analysis.clause_count,
                        "clause_types": result.clause_analysis.clause_types,
                        "clauses": result.clause_analysis.clauses
                    },
                    "phase1_draft": {
                        "target": result.phase1_draft.target,
                        "condition": result.phase1_draft.condition,
                        "content": result.phase1_draft.content,
                        "horizontal_layout": result.phase1_draft.horizontal_layout
                    },
                    "phase2_draft": {
                        "target": result.phase2_draft.target,
                        "condition": result.phase2_draft.condition,
                        "content": result.phase2_draft.content,
                        "horizontal_layout": result.phase2_draft.horizontal_layout
                    },
                    "phase3_draft": {
                        "target": result.phase3_draft.target,
                        "condition": result.phase3_draft.condition,
                        "content": result.phase3_draft.content,
                        "horizontal_layout": result.phase3_draft.horizontal_layout
                    },
                    "template_mappings": [
                        {
                            "concrete_term": mapping.concrete_term,
                            "abstract_placeholder": mapping.abstract_placeholder,
                            "placeholder_type": mapping.placeholder_type
                        }
                        for mapping in result.template_mappings
                    ],
                    "analysis_metadata": result.analysis_metadata
                }
                
                # Generate session ID from input hash
                import hashlib
                input_text = f"{question}:{answer}"
                session_id = hashlib.md5(input_text.encode()).hexdigest()[:8]
                
                saved_path = self.result_manager.save_result(
                    agent_type="in_question_analysis",
                    result_type="analysis",
                    result_data=result_data,
                    session_id=session_id,
                    input_hash=hashlib.md5(input_text.encode()).hexdigest(),
                    metadata={
                        "question_length": len(question),
                        "answer_length": len(answer),
                        "clause_count": clause_analysis.clause_count,
                        "template_count": len(template_mappings)
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
            print(f"ANALYSIS COMPLETE")
            print(f"{'='*60}")
            print(f"Question: {question}")
            print(f"Answer length: {len(answer)} characters")
            print(f"Clause count: {clause_analysis.clause_count}")
            print(f"Template mappings: {len(template_mappings)}")
            print(f"Processing timestamp: {metadata['processing_timestamp']}")
            print(f"{'='*60}\n")
        
        return result
    
    def _analyze_question_structure(self, question: str, prompt_context: Optional[str] = None) -> QuestionStructure:
        """Phase 1: Analyze formal question structure"""
        if self.verbose:
            print(f"    Making LLM request for question structure analysis...")
        
        prompt_params = {"question": question}
        if prompt_context:
            prompt_params["prompt_context"] = prompt_context
            
        request = self.create_llm_request(
            prompt_type="question_structure_analysis",
            prompt_params=prompt_params,
            response_parser=self._parse_question_structure_response
        )
        
        response = self.call_llm(request)
        if not response.success:
            if self.verbose:
                print(f"    ❌ LLM request failed: {response.error_message}")
                print(f"    Raw response: '{response.raw_response}'")
            raise Exception(f"Failed to analyze question structure: {response.error_message}")
        
        if self.verbose:
            print(f"    LLM response received successfully")
            print(f"    Raw response: '{response.raw_response[:200]}{'...' if len(response.raw_response) > 200 else ''}'")
        
        return response.parsed_result
    
    def _create_phase1_draft(self, question_structure: QuestionStructure) -> NormCodeDraft:
        """Create Phase 1 NormCode draft"""
        # Create basic NormCode inference ground
        content = f"{question_structure.target}\n    <= {question_structure.condition}"
        horizontal_layout = f"|1|{question_structure.target} |1.1|<= {question_structure.condition} |/1.1||/1|"
        
        return NormCodeDraft(
            target=question_structure.target,
            condition=question_structure.condition,
            content=content,
            horizontal_layout=horizontal_layout
        )
    
    def _analyze_clauses(self, answer: str, prompt_context: Optional[str] = None) -> ClauseAnalysis:
        """Phase 2: Analyze sentence structure and clauses"""
        if self.verbose:
            print(f"    Making LLM request for clause analysis...")
        
        prompt_params = {"answer": answer}
        if prompt_context:
            prompt_params["prompt_context"] = prompt_context
            
        request = self.create_llm_request(
            prompt_type="clause_analysis",
            prompt_params=prompt_params,
            response_parser=self._parse_clause_analysis_response
        )
        
        response = self.call_llm(request)
        if not response.success:
            if self.verbose:
                print(f"    ❌ LLM request failed: {response.error_message}")
                print(f"    Raw response: '{response.raw_response}'")
            raise Exception(f"Failed to analyze clauses: {response.error_message}")
        
        if self.verbose:
            print(f"    LLM response received successfully")
            print(f"    Raw response: '{response.raw_response[:200]}{'...' if len(response.raw_response) > 200 else ''}'")
        
        return response.parsed_result
    
    def _create_phase2_draft(self, phase1_draft: NormCodeDraft, clause_analysis: ClauseAnalysis, answer: str, prompt_context: Optional[str] = None) -> NormCodeDraft:
        """Create Phase 2 NormCode draft with clause structure"""
        if self.verbose:
            print(f"    Making LLM request for Phase 2 draft creation...")
        
        prompt_params = {
            "phase1_draft": phase1_draft.content,
            "clause_analysis": {
                "structure_type": clause_analysis.structure_type,
                "clause_count": clause_analysis.clause_count,
                "clause_types": clause_analysis.clause_types,
                "clauses": clause_analysis.clauses
            },
            "answer": answer
        }
        if prompt_context:
            prompt_params["prompt_context"] = prompt_context
            
        request = self.create_llm_request(
            prompt_type="phase2_draft_creation",
            prompt_params=prompt_params,
            response_parser=self._parse_phase2_draft_response
        )
        
        response = self.call_llm(request)
        if not response.success:
            if self.verbose:
                print(f"    ❌ LLM request failed: {response.error_message}")
                print(f"    Raw response: '{response.raw_response}'")
            raise Exception(f"Failed to create Phase 2 draft: {response.error_message}")
        
        if self.verbose:
            print(f"    LLM response received successfully")
            print(f"    Raw response: '{response.raw_response[:200]}{'...' if len(response.raw_response) > 200 else ''}'")
        
        return response.parsed_result
    
    def _create_templates(self, phase2_draft: NormCodeDraft, prompt_context: Optional[str] = None) -> tuple[NormCodeDraft, List[TemplateMapping]]:
        """Phase 3: Create templates with abstract placeholders"""
        if self.verbose:
            print(f"    Making LLM request for template creation...")
        
        prompt_params = {"phase2_draft": phase2_draft.content}
        if prompt_context:
            prompt_params["prompt_context"] = prompt_context
            
        request = self.create_llm_request(
            prompt_type="template_creation",
            prompt_params=prompt_params,
            response_parser=self._parse_template_creation_response
        )
        
        response = self.call_llm(request)
        if not response.success:
            if self.verbose:
                print(f"    ❌ LLM request failed: {response.error_message}")
                print(f"    Raw response: '{response.raw_response}'")
            raise Exception(f"Failed to create templates: {response.error_message}")
        
        if self.verbose:
            print(f"    LLM response received successfully")
            print(f"    Raw response: '{response.raw_response[:200]}{'...' if len(response.raw_response) > 200 else ''}'")
        
        return response.parsed_result
    
    # Response parsers
    def _parse_question_structure_response(self, response: dict) -> QuestionStructure:
        """Parse question structure response"""
        return QuestionStructure(
            marker=response.get("marker", "$what?"),
            target=response.get("target", "{target}"),
            condition=response.get("condition", "$="),
            question=response.get("question", "$what?({target}, $=)")
        )
    
    def _parse_clause_analysis_response(self, response: dict) -> ClauseAnalysis:
        """Parse clause analysis response"""
        return ClauseAnalysis(
            structure_type=response.get("structure_type", "declarative"),
            clause_count=response.get("clause_count", 1),
            clause_types=response.get("clause_types", ["single"]),
            clauses=response.get("clauses", [])
        )
    
    def _parse_phase2_draft_response(self, response: dict) -> NormCodeDraft:
        """Parse Phase 2 draft response"""
        return NormCodeDraft(
            target=response.get("target", "{target}"),
            condition=response.get("condition", "$="),
            content=response.get("content", ""),
            horizontal_layout=response.get("horizontal_layout", "")
        )
    
    def _parse_template_creation_response(self, response: dict) -> tuple[NormCodeDraft, List[TemplateMapping]]:
        """Parse template creation response"""
        phase3_draft = NormCodeDraft(
            target=response.get("target", "{target}"),
            condition=response.get("condition", "$="),
            content=response.get("content", ""),
            horizontal_layout=response.get("horizontal_layout", "")
        )
        
        template_mappings = []
        mappings_data = response.get("template_mappings", [])
        for mapping_data in mappings_data:
            template_mappings.append(TemplateMapping(
                concrete_term=mapping_data.get("concrete_term", ""),
                abstract_placeholder=mapping_data.get("abstract_placeholder", ""),
                placeholder_type=mapping_data.get("placeholder_type", "")
            ))
        
        return phase3_draft, template_mappings
    
    def _create_metadata(self, question: str, answer: str, question_structure: QuestionStructure, clause_analysis: ClauseAnalysis) -> Dict[str, Any]:
        """Create metadata for the analysis"""
        return {
            "question": question,
            "answer": answer,
            "question_length": len(question),
            "answer_length": len(answer),
            "question_marker": question_structure.marker,
            "question_target": question_structure.target,
            "question_condition": question_structure.condition,
            "structure_type": clause_analysis.structure_type,
            "clause_count": clause_analysis.clause_count,
            "clause_types": clause_analysis.clause_types,
            "processing_timestamp": "2024-01-01T00:00:00Z"
        }
    
if __name__ == "__main__":
    try:
        print("Initializing InQuestionAnalysisAgent...")
        
        # Create agent with verbose mode enabled
        agent = InQuestionAnalysisAgent(verbose=True, llm_model="qwen-turbo-latest")
        print("Agent created successfully")

        print("Retrieving NormCode context...")
        normcode_context = agent.prompt_manager.get_prompt("general", "context")
        if normcode_context:
            print(f"  ✓ general/context: Retrieved ({len(normcode_context)} characters)")
        else:
            print("  ⚠ No context found")

        # Example question-answer pair
        question = "$what?({step_2}, $::)"
        answer = "Mix the ingredients together"

        print("Starting analysis process...")
        result = agent.analyze(question, answer, normcode_context)
        
        # Print final result summary
        print("\nFINAL RESULT:")
        print(f"Question Structure: {result.question_structure.question}")
        print(f"Clause Analysis: {result.clause_analysis.structure_type} with {result.clause_analysis.clause_count} clauses")
        print(f"Phase 1 Draft: {result.phase1_draft.content}")
        print(f"Phase 2 Draft: {result.phase2_draft.content}")
        print(f"Phase 3 Draft: {result.phase3_draft.content}")
        print(f"Template Mappings: {len(result.template_mappings)}")
        print(f"Metadata: {result.analysis_metadata}")
        
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback
        traceback.print_exc() 