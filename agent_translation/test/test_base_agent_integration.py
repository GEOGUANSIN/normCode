#!/usr/bin/env python3
"""
Test BaseAgent integration with LLMFactory ask method
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_base_agent_with_llm():
    """Test BaseAgent with LLMFactory"""
    print("Testing BaseAgent integration with LLMFactory...")
    
    try:
        from LLMFactory import LLMFactory
        from base_agent import BaseAgent, LLMRequest, LLMResponse
        
        # Create LLM client
        llm = LLMFactory(model_name="deepseek-v3")
        print(f"✓ LLMFactory created with model: {llm.model_name}")
        
        # Test direct ask method
        print("\n1. Testing direct ask method...")
        direct_response = llm.ask("What is 2+2?")
        print(f"   Direct ask response: {direct_response}")
        
        # Create a simple test agent that inherits from BaseAgent
        class TestAgent(BaseAgent):
            def _get_agent_type(self) -> str:
                return "test_agent"
            
            def _create_fallback_handler(self, request):
                return lambda: {"result": "fallback"}
            
            def _create_mock_response_generator(self, request):
                return lambda prompt: '{"result": "mock"}'
            
            def test_llm_call(self, prompt: str):
                """Test LLM call through BaseAgent"""
                request = LLMRequest(
                    agent_type="test_agent",
                    prompt_type="test",
                    prompt_params={"prompt": prompt}
                )
                return self.call_llm(request)
        
        # Create test agent with LLM client
        agent = TestAgent(llm_client=llm)
        print(f"✓ TestAgent created with LLM client: {agent.llm_client is not None}")
        
        # Test LLM call through BaseAgent
        print("\n2. Testing LLM call through BaseAgent...")
        response = agent.test_llm_call("What is 3+3?")
        print(f"   BaseAgent response success: {response.success}")
        print(f"   BaseAgent raw response: {response.raw_response}")
        print(f"   BaseAgent parsed result: {response.parsed_result}")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_demo_integration():
    """Test the demo script integration"""
    print("\n3. Testing demo script integration...")
    
    try:
        from demo.question_sequencing_demo import setup_llm_client, create_agent
        
        # Setup LLM client using demo function
        llm_client = setup_llm_client(use_local=False)
        if llm_client:
            print(f"   ✓ Demo LLM client created: {llm_client.model_name}")
            
            # Create agent using demo function
            agent = create_agent(llm_client=llm_client)
            print(f"   ✓ Demo agent created: {type(agent).__name__}")
            print(f"   ✓ Agent has LLM client: {agent.llm_client is not None}")
            
            return True
        else:
            print("   ✗ Demo LLM client creation failed")
            return False
            
    except Exception as e:
        print(f"   ✗ Demo integration failed: {e}")
        return False

def main():
    """Main test function"""
    print("BaseAgent Integration Test")
    print("=" * 50)
    
    # Test 1: BaseAgent with LLMFactory
    if not test_base_agent_with_llm():
        print("BaseAgent test failed")
        return
    
    # Test 2: Demo integration
    if not test_demo_integration():
        print("Demo integration test failed")
        return
    
    print("\n" + "=" * 50)
    print("✓ All integration tests passed!")
    print("The LLMFactory ask method is now properly integrated with BaseAgent!")

if __name__ == "__main__":
    main() 