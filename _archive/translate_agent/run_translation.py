#!/usr/bin/env python3
"""
Simple Translation Agent Runner
The simplest way to run the NormCode translation agent
"""

import sys
import os

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline_agent import PipelineAgent

def main():
    """Run the translation agent with user input"""
    
    print("=" * 60)
    print("NORMCODE TRANSLATION AGENT")
    print("=" * 60)
    print("This agent translates natural language instructions into NormCode format.")
    print()
    
    # Get input text from user
    print("Enter your instructive text (or press Enter to use sample text):")
    user_input = input().strip()
    
    if not user_input:
        # Use sample text if no input provided
        user_input = """
        To create a user account, you must provide a valid email address and choose a strong password. 
        The password must be at least 8 characters long and contain at least one uppercase letter, 
        one lowercase letter, and one number. After submitting the form, you will receive a 
        confirmation email. Click the link in the email to verify your account.
        """
        print("\nUsing sample text...")
    
    print(f"\nProcessing text ({len(user_input)} characters)...")
    print("-" * 60)
    
    try:
        # Initialize the pipeline agent
        pipeline = PipelineAgent(
            llm_model="deepseek-v3",  # You can change this to your preferred model
            verbose=True
        )
        
        # Process the text
        result = pipeline.process(
            norm_text=user_input,
            save_result=True
        )
        
        # Display results
        print("\n" + "=" * 60)
        print("TRANSLATION RESULTS")
        print("=" * 60)
        
        # Show main question
        print(f"Main Question: {result.main_question['question']}")
        print(f"Type: {result.main_question['type']}")
        print()
        
        # Show question-answer pairs
        print(f"Question-Answer Pairs ({len(result.ensuing_questions)}):")
        for i, qa in enumerate(result.ensuing_questions):
            print(f"  {i+1}. Q: {qa['question']}")
            print(f"     A: {qa['answer'][:100]}{'...' if len(qa['answer']) > 100 else ''}")
        print()
        
        # Show final NormCode translations
        print("NormCode Translations:")
        for i, analysis in enumerate(result.question_analyses):
            print(f"  {i+1}. {analysis['analysis_id']}:")
            print(f"     {analysis['phase3_draft']['content']}")
            print()
        
        # Show summary
        summary = pipeline.get_pipeline_summary(result)
        print(f"Summary: {summary['question_pairs_processed']} pairs processed, "
              f"{summary['analyses_completed']} analyses completed, "
              f"{summary['total_template_mappings']} template mappings created")
        
        # Export results
        export_path = pipeline.export_to_json(result)
        print(f"\nResults saved to: {export_path}")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure you have the required dependencies installed and API access configured.")
        return 1
    
    print("\nTranslation completed successfully!")
    return 0

if __name__ == "__main__":
    exit(main()) 