"""
Test script for Pipeline Agent
Demonstrates how to use the complete pipeline that combines both phase agents
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline_agent import PipelineAgent

def test_pipeline():
    """Test the complete pipeline with a sample instructive text"""
    
    # Sample instructive text
    sample_text = """
    To create a user account, you must provide a valid email address and choose a strong password. 
    The password must be at least 8 characters long and contain at least one uppercase letter, 
    one lowercase letter, and one number. After submitting the form, you will receive a 
    confirmation email. Click the link in the email to verify your account.
    """
    
    # Initialize the pipeline agent
    pipeline = PipelineAgent(llm_model="deepseek-r1", verbose=True)
    
    print("Starting Pipeline Test")
    print("=" * 50)
    
    # Process the text through the complete pipeline
    result = pipeline.process(
        norm_text=sample_text,
        save_result=True
    )
    
    print("\nPipeline Results Summary:")
    print("=" * 50)
    
    # Get a summary of the results
    summary = pipeline.get_pipeline_summary(result)
    
    print(f"Status: {summary['pipeline_status']}")
    print(f"Main Question: {summary['main_question']}")
    print(f"Question Pairs Processed: {summary['question_pairs_processed']}")
    print(f"Analyses Completed: {summary['analyses_completed']}")
    print(f"Total Template Mappings: {summary['total_template_mappings']}")
    
    print("\nDetailed Results:")
    print("=" * 50)
    
    # Show main question
    print(f"Main Question: {result.main_question['question']}")
    print(f"Type: {result.main_question['type']}")
    print(f"Target: {result.main_question['target']}")
    print(f"Condition: {result.main_question['condition']}")
    
    print(f"\nQuestion-Answer Pairs ({len(result.ensuing_questions)}):")
    for i, qa in enumerate(result.ensuing_questions):
        print(f"  {i+1}. Q: {qa['question']}")
        print(f"     A: {qa['answer'][:80]}{'...' if len(qa['answer']) > 80 else ''}")
    
    print(f"\nQuestion Analyses ({len(result.question_analyses)}):")
    for i, analysis in enumerate(result.question_analyses):
        print(f"  {i+1}. Analysis ID: {analysis['analysis_id']}")
        print(f"     Question: {analysis['question_structure']['question']}")
        print(f"     Structure Type: {analysis['clause_analysis']['structure_type']}")
        print(f"     Clause Count: {analysis['clause_analysis']['clause_count']}")
        print(f"     Template Mappings: {len(analysis['template_mappings'])}")
        
        # Show phase 3 draft (final result)
        print(f"     Final Draft: {analysis['phase3_draft']['content']}")
        print()
    
    # Export to JSON file
    export_path = pipeline.export_to_json(result)
    print(f"Results exported to: {export_path}")
    
    return result

if __name__ == "__main__":
    test_pipeline() 