#!/usr/bin/env python3
"""
Simple test script for BaseAgent
Tests the basic functionality with a minimal example
"""

import os
import sys

# Add the sequence directory to the path so we can import from it
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from base_agent import BaseAgent, LLMRequest, LLMResponse


class TestAgent(BaseAgent):
    """Simple test agent to verify BaseAgent functionality"""
    
    def _get_agent_type(self) -> str:
        return "question_sequencing"
    
    def test_prompt_retrieval(self):
        """Test if we can retrieve prompts"""
        print("Testing prompt retrieval...")
        
        # Test getting a prompt
        prompt = self.prompt_manager.get_prompt("question_sequencing", "question_type_analysis")
        if prompt:
            print(f"✓ Prompt retrieved successfully")
            print(f"  Preview: {prompt[:100]}...")
            return True
        else:
            print("✗ Failed to retrieve prompt")
            return False
    
    def test_llm_request(self):
        """Test LLM request creation and execution"""
        print("\nTesting LLM request...")
        
        # Get normcode context
        normcode_context = self.prompt_manager.get_prompt("general", "context")
        if not normcode_context:
            print("✗ Failed to retrieve normcode context")
            return None
        
        # Create a simple request with context
        request = self.create_llm_request(
            prompt_type="question_type_analysis",
            prompt_params={
                "norm_text": "Create a password for a new user",
                "prompt_context": normcode_context
            }
        )
        
        print(f"✓ LLM request created")
        print(f"  Agent type: {request.agent_type}")
        print(f"  Prompt type: {request.prompt_type}")
        print(f"  Parameters: {list(request.prompt_params.keys())}")
        print(f"  Context preview: {normcode_context[:50]}...")
        
        return request
    
    def test_llm_call(self, request: LLMRequest):
        """Test actual LLM call (if API key is available)"""
        print("\nTesting LLM call...")
        
        try:
            response = self.call_llm(request)
            
            if response.success:
                print(f"✓ LLM call successful")
                print(f"  Response preview: {response.raw_response[:100]}...")
                return True
            else:
                print(f"✗ LLM call failed: {response.error_message}")
                return False
                
        except Exception as e:
            print(f"✗ LLM call error: {e}")
            return False


def main():
    """Main test function"""
    print("=== BaseAgent Test ===\n")
    
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
    
    # Create test agent
    print("Creating TestAgent...")
    agent = TestAgent()
    print(f"✓ Agent created with type: {agent.agent_type}")
    print(f"✓ Prompt manager mode: {agent.prompt_manager.mode}")
    
    # Test prompt retrieval
    prompt_ok = agent.test_prompt_retrieval()
    
    # Test LLM request creation
    request = agent.test_llm_request()
    if request is None:
        print("\n✗ Failed to create LLM request")
        sys.exit(1)
    
    # Test LLM call (if API key available)
    if api_key:
        llm_ok = agent.test_llm_call(request)
    else:
        print("\nSkipping LLM call test (no API key)")
        llm_ok = True  # Don't fail the test
    
    # Summary
    print(f"\n=== Test Summary ===")
    print(f"Prompt retrieval: {'✓ PASS' if prompt_ok else '✗ FAIL'}")
    print(f"LLM request: ✓ PASS")
    print(f"LLM call: {'✓ PASS' if llm_ok else '✗ FAIL'}")
    
    if prompt_ok:
        print(f"\n✓ BaseAgent is working correctly!")
        print(f"  - Prompt manager: {agent.prompt_manager.mode} mode")
        print(f"  - LLM client: {type(agent.llm_client).__name__}")
    else:
        print(f"\n✗ BaseAgent has issues with prompt retrieval")
        sys.exit(1)


if __name__ == "__main__":
    main() 