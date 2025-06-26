#!/usr/bin/env python3
"""
Manual Phase 1 Test Script

Simple integration test for QuestionSequencingAgent with:
- LLMFactory (LLM Client)
- PromptDatabase (Prompt Management)
- NormCode Terminology Context
- Account Creation Example

This is a manual, step-by-step test that's easy to understand and debug.
"""

import sys
import os
import json
from typing import Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_normcode_context() -> Optional[str]:
    """Load NormCode terminology context from files"""
    print("📚 Loading NormCode terminology context...")
    
    context_parts = []
    
    # Load NormCode Syntax Reference
    try:
        syntax_ref_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "NormCode_terms", "NormCode_Syntax_Reference.md"
        )
        with open(syntax_ref_path, 'r', encoding='utf-8') as f:
            syntax_content = f.read()
            # Take first 1000 characters for testing
            context_parts.append(f"=== NormCode Syntax Reference ===\n{syntax_content[:1000]}...")
            print(f"✅ Loaded NormCode Syntax Reference ({len(syntax_content)} chars)")
    except Exception as e:
        print(f"❌ Failed to load NormCode Syntax Reference: {e}")
    
    # Load NormCode Terminology Clarification
    try:
        terminology_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "NormCode_terms", "normcode_terminology_clarification.md"
        )
        with open(terminology_path, 'r', encoding='utf-8') as f:
            terminology_content = f.read()
            # Take first 1000 characters for testing
            context_parts.append(f"=== NormCode Terminology Clarification ===\n{terminology_content[:1000]}...")
            print(f"✅ Loaded NormCode Terminology Clarification ({len(terminology_content)} chars)")
    except Exception as e:
        print(f"❌ Failed to load NormCode Terminology Clarification: {e}")
    
    # Combine context
    if context_parts:
        context = "\n\n".join(context_parts)
        print(f"📖 Total context loaded: {len(context)} characters")
        return context
    else:
        print("⚠️  No NormCode context loaded")
        return None

def setup_llm_factory(use_llm: bool = False) -> Optional[object]:
    """Setup LLMFactory (optional)"""
    if not use_llm:
        print("🤖 Using mock responses (no LLM)")
        return None
    
    try:
        from agent_translation.LLMFactory import LLMFactory
        llm_factory = LLMFactory(model_name="deepseek-v3")
        print("✅ LLMFactory initialized successfully")
        return llm_factory
    except Exception as e:
        print(f"❌ Failed to initialize LLMFactory: {e}")
        print("🤖 Falling back to mock responses")
        return None

def setup_prompt_manager():
    """Setup PromptManager"""
    try:
        from agent_translation.prompt_database import PromptManager
        prompt_manager = PromptManager()
        print("✅ PromptManager initialized successfully")
        return prompt_manager
    except Exception as e:
        print(f"❌ Failed to initialize PromptManager: {e}")
        raise

def setup_question_sequencing_agent(llm_client, prompt_manager):
    """Setup QuestionSequencingAgent"""
    try:
        from agent_translation.phase_agent.question_sequencing_agent import QuestionSequencingAgent
        agent = QuestionSequencingAgent(
            llm_client=llm_client,
            prompt_manager=prompt_manager
        )
        print("✅ QuestionSequencingAgent initialized successfully")
        return agent
    except Exception as e:
        print(f"❌ Failed to initialize QuestionSequencingAgent: {e}")
        raise

def test_basic_functionality(agent, context: Optional[str]):
    """Test basic functionality without context"""
    print("\n🧪 Test 1: Basic functionality (no context)")
    print("=" * 50)
    
    input_text = "Create a user account with email and password"
    print(f"Input: {input_text}")
    
    try:
        result = agent.deconstruct(
            norm_text=input_text,
            prompt_context=None  # No context
        )
        
        print(f"✅ Success!")
        print(f"Main Question Type: {result.main_question.type}")
        print(f"Main Question: {result.main_question.question}")
        print(f"Target: {result.main_question.target}")
        print(f"Condition: {result.main_question.condition}")
        print(f"Number of chunks: {len(result.ensuing_questions)}")
        print(f"Context provided: {result.decomposition_metadata.get('prompt_context_provided', False)}")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_with_context(agent, context: Optional[str]):
    """Test with NormCode context"""
    print("\n🧪 Test 2: With NormCode context")
    print("=" * 50)
    
    input_text = "Create a user account with email and password"
    print(f"Input: {input_text}")
    print(f"Context length: {len(context) if context else 0} characters")
    
    try:
        result = agent.deconstruct(
            norm_text=input_text,
            prompt_context=context
        )
        
        print(f"✅ Success!")
        print(f"Main Question Type: {result.main_question.type}")
        print(f"Main Question: {result.main_question.question}")
        print(f"Target: {result.main_question.target}")
        print(f"Condition: {result.main_question.condition}")
        print(f"Number of chunks: {len(result.ensuing_questions)}")
        print(f"Context provided: {result.decomposition_metadata.get('prompt_context_provided', False)}")
        print(f"Context length: {result.decomposition_metadata.get('prompt_context_length', 0)}")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_account_creation_example(agent, context: Optional[str]):
    """Test the complete account creation example"""
    print("\n🧪 Test 3: Account creation example")
    print("=" * 50)
    
    input_text = "Create a user account with email and password. The account has admin privileges and is active by default."
    print(f"Input: {input_text}")
    
    try:
        result = agent.deconstruct(
            norm_text=input_text,
            prompt_context=context
        )
        
        print(f"✅ Success!")
        print(f"Main Question Type: {result.main_question.type}")
        print(f"Main Question: {result.main_question.question}")
        print(f"Number of chunks: {len(result.ensuing_questions)}")
        
        # Show ensuing questions
        print("\nEnsuing Questions:")
        for i, qa in enumerate(result.ensuing_questions):
            print(f"  {i+1}. Question: {qa.question}")
            print(f"     Answer: {qa.answer[:50]}...")
            print(f"     Chunk Index: {qa.chunk_index}")
        
        # Show metadata
        print(f"\nMetadata:")
        for key, value in result.decomposition_metadata.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:100]}...")
            else:
                print(f"  {key}: {value}")
        
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

def test_different_question_types(agent, context: Optional[str]):
    """Test different question types"""
    print("\n🧪 Test 4: Different question types")
    print("=" * 50)
    
    test_cases = [
        ("What is a user account?", "what"),
        ("How to create an account?", "how"),
        ("When should verification be sent?", "when")
    ]
    
    results = []
    for input_text, expected_type in test_cases:
        print(f"\nTesting: {input_text}")
        print(f"Expected type: {expected_type}")
        
        try:
            result = agent.deconstruct(
                norm_text=input_text,
                prompt_context=context
            )
            
            actual_type = result.main_question.type
            success = actual_type == expected_type
            
            print(f"  Actual type: {actual_type}")
            print(f"  Question: {result.main_question.question}")
            print(f"  {'✅ PASS' if success else '❌ FAIL'}")
            
            results.append(success)
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\nQuestion type accuracy: {passed}/{total} ({passed/total*100:.1f}%)")
    
    return passed == total

def main():
    """Main test execution"""
    print("🚀 Starting Manual Phase 1 Test")
    print("=" * 60)
    
    # Step 1: Load NormCode context
    context = load_normcode_context()
    
    # Step 2: Setup components
    print("\n🔧 Setting up components...")
    llm_client = setup_llm_factory(use_llm=False)  # Use mock responses for now
    prompt_manager = setup_prompt_manager()
    agent = setup_question_sequencing_agent(llm_client, prompt_manager)
    
    # Step 3: Run tests
    print("\n🧪 Running tests...")
    test_results = []
    
    # Test 1: Basic functionality
    test_results.append(test_basic_functionality(agent, context))
    
    # Test 2: With context
    test_results.append(test_with_context(agent, context))
    
    # Test 3: Account creation example
    test_results.append(test_account_creation_example(agent, context))
    
    # Test 4: Different question types
    test_results.append(test_different_question_types(agent, context))
    
    # Step 4: Summary
    print("\n📊 Test Summary")
    print("=" * 60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        sys.exit(1) 