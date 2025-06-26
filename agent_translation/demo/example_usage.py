"""
Example usage of BaseAgent with LLMFactory integration
"""

import logging
from base_agent import BaseAgent, LLMRequest, LLMResponse
from LLMFactory import LLMFactory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExampleAgent(BaseAgent[dict]):
    """Example agent that demonstrates BaseAgent functionality"""
    
    def _get_agent_type(self) -> str:
        return "example_agent"
    
    def _create_fallback_handler(self, request: LLMRequest):
        def fallback():
            return {
                "status": "fallback",
                "agent_type": self.agent_type,
                "request_type": request.prompt_type,
                "message": "Using fallback response"
            }
        return fallback
    
    def _create_mock_response_generator(self, request: LLMRequest):
        def mock_generator(prompt: str) -> str:
            return json.dumps({
                "status": "mock",
                "agent_type": self.agent_type,
                "request_type": request.prompt_type,
                "response": "This is a mock response"
            })
        return mock_generator
    
    def analyze_text(self, text: str, model_name: str = None) -> LLMResponse:
        """
        Example method that analyzes text using LLM
        
        Args:
            text: Text to analyze
            model_name: Optional model override
            
        Returns:
            LLMResponse: Analysis result
        """
        # Create request
        request = self.create_llm_request(
            prompt_type="text_analysis",
            prompt_params={"text": text},
            response_parser=self._parse_analysis_response
        )
        
        # Call LLM with optional model override
        if model_name:
            return self.call_llm_with_model(request, model_name=model_name)
        else:
            return self.call_llm(request)
    
    def _parse_analysis_response(self, response: str) -> dict:
        """Parse analysis response"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"raw_response": response, "parsed": False}


def main():
    """Main example function"""
    
    print("=" * 60)
    print("BaseAgent LLMFactory Integration Example")
    print("=" * 60)
    
    # Create agent with default model (qwen-turbo-latest)
    print("\n1. Creating ExampleAgent with default model...")
    agent = ExampleAgent()
    print(f"✓ Agent created with model: {agent.model_name}")
    
    # Create agent with custom model
    print("\n2. Creating ExampleAgent with custom model...")
    agent_custom = ExampleAgent(model_name="qwen-plus")
    print(f"✓ Agent created with model: {agent_custom.model_name}")
    
    # Example of using different models for different requests
    print("\n3. Example: Using different models for different requests...")
    
    # This would normally work with proper prompts in the database
    # For demonstration, we'll show the structure
    sample_text = "This is a sample text for analysis."
    
    print(f"Sample text: {sample_text}")
    print("Note: This example assumes you have 'text_analysis' prompt in your database")
    print("The agent will use fallback responses if prompts are not found")
    
    # Try analysis with default model
    print("\n4. Analyzing with default model (qwen-turbo-latest)...")
    try:
        response1 = agent.analyze_text(sample_text)
        print(f"Response success: {response1.success}")
        if response1.success:
            print(f"Result: {response1.parsed_result}")
        else:
            print(f"Error: {response1.error_message}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Try analysis with custom model
    print("\n5. Analyzing with custom model (qwen-plus)...")
    try:
        response2 = agent.analyze_text(sample_text, model_name="qwen-plus")
        print(f"Response success: {response2.success}")
        if response2.success:
            print(f"Result: {response2.parsed_result}")
        else:
            print(f"Error: {response2.error_message}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Show available models
    print("\n6. Available models in settings.yaml:")
    available_models = [
        "qwen-turbo-latest",  # Default
        "qwen-plus",
        "qwen-max", 
        "deepseek-v3",
        "deepseek-r1-distill-qwen-7b",
        "deepseek-r1-distill-qwen-1.5b"
    ]
    
    for i, model in enumerate(available_models, 1):
        default_marker = " (default)" if model == "qwen-turbo-latest" else ""
        print(f"  {i}. {model}{default_marker}")
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("Key features demonstrated:")
    print("- Default model: qwen-turbo-latest")
    print("- Custom model selection")
    print("- Model override per request")
    print("- Fallback handling")
    print("- Error handling")
    print("=" * 60)


if __name__ == "__main__":
    main() 