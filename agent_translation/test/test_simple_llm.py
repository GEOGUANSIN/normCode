#!/usr/bin/env python3
"""
Simple test for LLMFactory setup logic
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_llm_factory_direct():
    """Test LLMFactory directly"""
    print("Testing LLMFactory directly...")
    
    try:
        from LLMFactory import LLMFactory
        
        # Test the exact same logic as the demo script
        print("1. Testing cloud LLM setup (demo script logic)...")
        
        try:
            # This is the same as the demo script's first attempt
            llm_client = LLMFactory(model_name="deepseek-v3")
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
                        {"role": "user", "content": "Say 'LLMFactory works!'"}
                    ],
                    max_tokens=20,
                    temperature=0
                )
                result = response.choices[0].message.content
                print(f"   ✓ Test prompt successful: {result}")
                return True
            except Exception as e:
                print(f"   ✗ Test prompt failed: {e}")
                return False
                
        except Exception as e:
            print(f"   ✗ Cloud LLM client creation failed: {e}")
            return False
            
    except Exception as e:
        print(f"   ✗ LLMFactory import failed: {e}")
        return False

def test_local_llm_setup():
    """Test local LLM setup"""
    print("\n2. Testing local LLM setup...")
    
    try:
        from LLMFactory import LLMFactory
        
        # Test local endpoint creation (same as demo script)
        local_llm_client = LLMFactory.create_for_local_endpoint(
            model_name="llama3.1:8b",
            base_url="http://localhost:11434/v1",
            api_key="dummy-key"
        )
        
        print(f"   ✓ Local LLM client created successfully")
        print(f"   ✓ Model: {local_llm_client.model_name}")
        print(f"   ✓ Base URL: {local_llm_client.base_url}")
        print(f"   ✓ API Key: {local_llm_client.api_key}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Local LLM client creation failed: {e}")
        return False

def test_settings_path_logic():
    """Test the settings path logic from demo script"""
    print("\n3. Testing settings path logic...")
    
    # Test the exact path logic from the demo script
    settings_path = Path(__file__).parent.parent / "settings.yaml"
    print(f"   Demo script would look for settings at: {settings_path}")
    print(f"   Settings file exists: {settings_path.exists()}")
    
    if settings_path.exists():
        print(f"   ✓ Settings file found")
        return True
    else:
        print(f"   ✗ Settings file not found")
        return False

def main():
    """Main test function"""
    print("Simple LLMFactory Test Suite")
    print("=" * 50)
    
    # Test 1: Direct LLMFactory
    if not test_llm_factory_direct():
        print("Direct LLMFactory test failed")
        return
    
    # Test 2: Local LLM setup
    test_local_llm_setup()
    
    # Test 3: Settings path
    test_settings_path_logic()
    
    print("\n" + "=" * 50)
    print("Simple LLMFactory tests completed!")

if __name__ == "__main__":
    main() 