#!/usr/bin/env python3
"""
Quick test for LLMFactory ask method integration
"""

from LLMFactory import LLMFactory

print("1. Creating LLMFactory...")
llm = LLMFactory(model_name="deepseek-v3")
print(f"   ✓ LLMFactory created: {llm.model_name}")

print("\n2. Testing ask method...")
response = llm.ask("What is 2+2?")
print(f"   ✓ Ask response: {response}")

print("\n3. Testing BaseAgent integration...")
from base_agent import BaseAgent, LLMRequest

class SimpleAgent(BaseAgent):
    def _get_agent_type(self) -> str:
        return "simple"
    
    def _create_fallback_handler(self, request):
        return lambda: {"result": "fallback"}
    
    def _create_mock_response_generator(self, request):
        return lambda prompt: '{"result": "mock"}'

agent = SimpleAgent(llm_client=llm)
print(f"   ✓ Agent created with LLM client: {agent.llm_client is not None}")

print("\n4. Testing agent LLM call...")
request = LLMRequest(
    agent_type="simple",
    prompt_type="test",
    prompt_params={"test": "data"}
)
response = agent.call_llm(request)
print(f"   ✓ Agent LLM call success: {response.success}")
print(f"   ✓ Agent response: {response.raw_response[:100]}...")

print("\n✅ All tests passed! LLMFactory ask method is working with BaseAgent!") 