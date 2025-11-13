#!/usr/bin/env python3
"""
Simple NormCode Translation Script
Usage: python simple_translate.py "your text here"
"""

import sys
import os

# Add the current directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline_agent import PipelineAgent

def translate_text(text):
    """Translate text to NormCode format"""
    
    # Initialize the pipeline agent
    pipeline = PipelineAgent(
        llm_model="qwen-turbo-latest",
        verbose=False  # Set to True for detailed output
    )
    
    # Process the text
    result = pipeline.process(
        norm_text=text,
        save_result=True
    )
    
    # Return the final NormCode translations
    translations = []
    for analysis in result.question_analyses:
        translations.append(analysis['phase3_draft']['content'])
    
    return translations

def main():
    if len(sys.argv) < 2:
        print("Usage: python simple_translate.py \"your text here\"")
        print("Example: python simple_translate.py \"To create an account, provide email and password\"")
        return 1
    
    text = sys.argv[1]
    print(f"Translating: {text}")
    
    try:
        translations = translate_text(text)
        
        print("\nNormCode Translations:")
        for i, translation in enumerate(translations, 1):
            print(f"{i}. {translation}")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 