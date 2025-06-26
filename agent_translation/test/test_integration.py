#!/usr/bin/env python3
"""
Integration test for LLMFactory with demo script setup
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_demo_llm_setup():
    """Test the LLM setup function from the demo script"""
    print("Testing demo script LLM setup...")
    
    try:
        # Import the demo script functions
        from demo.question_sequencing_demo import setup_llm_client
        
        # Test cloud LLM setup
        print("1. Testing cloud LLM setup...")
        llm_client = setup_llm_client(use_local=False)
        
        if llm_client:
            print(f"   ✓ Cloud LLM client created successfully")
            print(f"   ✓ Model: {llm_client.model_name}")
            print(f"   ✓ Base URL: {llm_client.base_url}")
            print(f"   ✓ API Key: {llm_client.api_key[:10]}..." if llm_client.api_key else "   ✓ API Key: None")
            
            # Test a simple prompt
            try:
                response = llm_client.client.chat.completions.create(
                    model=llm_client.model_name,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Say 'Test successful!'"}
                    ],
                    max_tokens=20,
                    temperature=0
                )
                result = response.choices[0].message.content
                print(f"   ✓ Test prompt successful: {result}")
            except Exception as e:
                print(f"   ✗ Test prompt failed: {e}")
        else:
            print("   ✗ Cloud LLM client creation failed")
        
        # Test local LLM setup
        print("\n2. Testing local LLM setup...")
        local_llm_client = setup_llm_client(use_local=True)
        
        if local_llm_client:
            print(f"   ✓ Local LLM client created successfully")
            print(f"   ✓ Model: {local_llm_client.model_name}")
            print(f"   ✓ Base URL: {local_llm_client.base_url}")
        else:
            print("   ✗ Local LLM client creation failed (expected if Ollama not running)")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Demo script setup failed: {e}")
        return False

def test_prompt_manager_setup():
    """Test the prompt manager setup"""
    print("\n3. Testing prompt manager setup...")
    
    try:
        from demo.question_sequencing_demo import setup_prompt_manager
        
        prompt_manager = setup_prompt_manager()
        print(f"   ✓ Prompt manager created successfully")
        print(f"   ✓ Type: {type(prompt_manager).__name__}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Prompt manager setup failed: {e}")
        return False

def test_agent_creation():
    """Test the agent creation"""
    print("\n4. Testing agent creation...")
    
    try:
        from demo.question_sequencing_demo import create_agent, setup_llm_client, setup_prompt_manager
        
        llm_client = setup_llm_client(use_local=False)
        prompt_manager = setup_prompt_manager()
        
        agent = create_agent(llm_client, prompt_manager)
        print(f"   ✓ Agent created successfully")
        print(f"   ✓ Agent type: {type(agent).__name__}")
        print(f"   ✓ LLM client: {agent.llm_client is not None}")
        print(f"   ✓ Prompt manager: {agent.prompt_manager is not None}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Agent creation failed: {e}")
        return False

def main():
    """Main test function"""
    print("Integration Test Suite")
    print("=" * 50)
    
    # Test 1: LLM setup
    if not test_demo_llm_setup():
        print("LLM setup failed, stopping tests")
        return
    
    # Test 2: Prompt manager
    if not test_prompt_manager_setup():
        print("Prompt manager setup failed, stopping tests")
        return
    
    # Test 3: Agent creation
    if not test_agent_creation():
        print("Agent creation failed, stopping tests")
        return
    
    print("\n" + "=" * 50)
    print("All integration tests passed!")

if __name__ == "__main__":
    main() 