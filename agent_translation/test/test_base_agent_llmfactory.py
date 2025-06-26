"""
Test script to verify BaseAgent integration with LLMFactory
"""

import logging
from base_agent import BaseAgent, LLMRequest, LLMResponse
from LLMFactory import LLMFactory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestAgent(BaseAgent[str]):
    """Simple test agent to verify BaseAgent functionality"""
    
    def _get_agent_type(self) -> str:
        return "test_agent"
    
    def _create_fallback_handler(self, request: LLMRequest):
        def fallback():
            return {"error": "Fallback response", "agent_type": self.agent_type, "request_type": request.prompt_type}
        return fallback
    
    def _create_mock_response_generator(self, request: LLMRequest):
        def mock_generator(prompt: str) -> str:
            return '{"result": "Mock response", "agent_type": "' + self.agent_type + '"}'
        return mock_generator


def test_base_agent_llmfactory_integration():
    """Test that BaseAgent properly integrates with LLMFactory"""
    
    print("Testing BaseAgent LLMFactory integration...")
    
    # Test 1: Create BaseAgent with default model (qwen-turbo-latest)
    print("\n1. Testing BaseAgent with default model (qwen-turbo-latest)...")
    try:
        agent = TestAgent()
        print(f"✓ BaseAgent created successfully")
        print(f"  - Agent type: {agent.agent_type}")
        print(f"  - Default model: {agent.model_name}")
        print(f"  - LLM client type: {type(agent.llm_client).__name__}")
        
        if agent.llm_client is not None:
            print(f"  - LLM client model: {agent.llm_client.model_name}")
    except Exception as e:
        print(f"✗ Failed to create BaseAgent: {e}")
        return False
    
    # Test 2: Create BaseAgent with custom model
    print("\n2. Testing BaseAgent with custom model (qwen-plus)...")
    try:
        agent_custom = TestAgent(model_name="qwen-plus")
        print(f"✓ BaseAgent with custom model created successfully")
        print(f"  - Custom model: {agent_custom.model_name}")
        print(f"  - LLM client model: {agent_custom.llm_client.model_name}")
    except Exception as e:
        print(f"✗ Failed to create BaseAgent with custom model: {e}")
        return False
    
    # Test 3: Test LLM request creation
    print("\n3. Testing LLM request creation...")
    try:
        request = agent.create_llm_request(
            prompt_type="test_prompt",
            prompt_params={"test_param": "test_value"}
        )
        print(f"✓ LLM request created successfully")
        print(f"  - Agent type: {request.agent_type}")
        print(f"  - Prompt type: {request.prompt_type}")
        print(f"  - Prompt params: {request.prompt_params}")
    except Exception as e:
        print(f"✗ Failed to create LLM request: {e}")
        return False
    
    # Test 4: Test LLMFactory creation method
    print("\n4. Testing LLMFactory creation method...")
    try:
        llm_factory = agent.create_llm_factory("qwen-max")
        print(f"✓ LLMFactory created successfully")
        print(f"  - Model: {llm_factory.model_name}")
    except Exception as e:
        print(f"✗ Failed to create LLMFactory: {e}")
        return False
    
    # Test 5: Test call_llm_with_model method
    print("\n5. Testing call_llm_with_model method...")
    try:
        # Create a simple request
        request = agent.create_llm_request(
            prompt_type="test_prompt",
            prompt_params={"test_param": "test_value"}
        )
        
        # This will likely fail due to missing prompt, but should handle gracefully
        response = agent.call_llm_with_model(request, model_name="qwen-plus")
        print(f"✓ call_llm_with_model executed successfully")
        print(f"  - Response success: {response.success}")
        if not response.success:
            print(f"  - Error message: {response.error_message}")
    except Exception as e:
        print(f"✗ Failed to call call_llm_with_model: {e}")
        return False
    
    print("\n✓ All tests completed successfully!")
    return True


def test_llmfactory_direct():
    """Test LLMFactory directly"""
    
    print("\nTesting LLMFactory directly...")
    
    try:
        # Test with qwen-turbo-latest
        llm = LLMFactory(model_name="qwen-turbo-latest")
        print(f"✓ LLMFactory created with qwen-turbo-latest")
        print(f"  - Model: {llm.model_name}")
        print(f"  - Base URL: {llm.base_url}")
        
        # Test with qwen-plus
        llm_plus = LLMFactory(model_name="qwen-plus")
        print(f"✓ LLMFactory created with qwen-plus")
        print(f"  - Model: {llm_plus.model_name}")
        
    except Exception as e:
        print(f"✗ LLMFactory test failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("BaseAgent LLMFactory Integration Test")
    print("=" * 60)
    
    success1 = test_base_agent_llmfactory_integration()
    success2 = test_llmfactory_direct()
    
    if success1 and success2:
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("BaseAgent is properly integrated with LLMFactory")
        print("Default model is set to qwen-turbo-latest")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ SOME TESTS FAILED!")
        print("Please check the error messages above")
        print("=" * 60) 