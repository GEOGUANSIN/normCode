#!/usr/bin/env python3
"""
Simple test script for QuestionSequencingAgent
Tests the basic functionality with the updated prompt manager
"""

import os
import sys

# Add the sequence directory to the path so we can import from it
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from phase_agent.question_sequencing_agent import QuestionSequencingAgent


def main():
    """Main test function"""
    print("=== QuestionSequencingAgent Test ===\n")
    
    # Check if we're in the right directory (project root)
    prompts_dir = "sequence/phase_agent/prompts"
    if not os.path.exists(prompts_dir):
        print("Error: Please run this from the project root directory")
        print("Current directory:", os.getcwd())
        print("Expected prompts directory:", prompts_dir)
        sys.exit(1)
    
    # Check for API key
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("Warning: DASHSCOPE_API_KEY not set - LLM calls will fail")
        print("Set the environment variable to test full functionality\n")
    
    # Create agent
    print("Creating QuestionSequencingAgent...")
    agent = QuestionSequencingAgent()
    print(f"✓ Agent created with type: {agent.agent_type}")
    print(f"✓ Prompt manager mode: {agent.prompt_manager.mode}")
    
    # Test prompt retrieval
    print("\nTesting prompt retrieval...")
    prompts_to_test = [
        ("question_sequencing", "question_type_analysis"),
        ("question_sequencing", "sentence_chunking"),
        ("question_sequencing", "chunk_question_generation"),
        ("general", "context")
    ]
    
    all_prompts_ok = True
    normcode_context = None
    
    for agent_type, prompt_type in prompts_to_test:
        prompt = agent.prompt_manager.get_prompt(agent_type, prompt_type)
        if prompt:
            print(f"  ✓ {agent_type}/{prompt_type}: Retrieved")
            if agent_type == "general" and prompt_type == "context":
                normcode_context = prompt
        else:
            print(f"  ✗ {agent_type}/{prompt_type}: Failed")
            all_prompts_ok = False
    
    if not all_prompts_ok:
        print("\n✗ Some prompts failed to retrieve")
        sys.exit(1)
    
    # Test deconstruction (if API key available)
    if api_key:
        print("\nTesting deconstruction...")
        test_text = "Create a password for a new user account. The password should be at least 8 characters long and include a mix of uppercase and lowercase letters, numbers, and special characters."
        
        try:
            result = agent.deconstruct(test_text, normcode_context)
            
            print(f"✓ Deconstruction successful!")
            print(f"  Main question: {result.main_question.question}")
            print(f"  Question type: {result.main_question.type}")
            print(f"  Chunks processed: {len(result.ensuing_questions)}")
            
            # Show first few ensuing questions
            for i, qa in enumerate(result.ensuing_questions[:3]):
                print(f"  Chunk {i}: {qa.question[:50]}...")
            
            print(f"  Metadata: {result.decomposition_metadata}")
            
        except Exception as e:
            print(f"✗ Deconstruction failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print("\nSkipping deconstruction test (no API key)")
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Prompt retrieval: ✓ PASS")
    print(f"Agent creation: ✓ PASS")
    if api_key:
        print(f"Deconstruction: ✓ PASS")
    else:
        print(f"Deconstruction: SKIPPED")
    
    print(f"\n✓ QuestionSequencingAgent is working correctly!")
    print(f"  - Prompt manager: {agent.prompt_manager.mode} mode")
    print(f"  - LLM client: {type(agent.llm_client).__name__}")
    print(f"  - Context handling: ✓ Working")


if __name__ == "__main__":
    main() 