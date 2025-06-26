#!/usr/bin/env python3
"""
Test script for LLMFactory functionality
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_llm_factory_import():
    """Test if LLMFactory can be imported"""
    print("1. Testing LLMFactory import...")
    try:
        from LLMFactory import LLMFactory
        print("   ✓ LLMFactory imported successfully")
        return LLMFactory
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return None

def test_constantpath():
    """Test constantpath module"""
    print("2. Testing constantpath...")
    try:
        from constantpath import CURRENT_DIR, PROJECT_ROOT
        print(f"   ✓ CURRENT_DIR: {CURRENT_DIR}")
        print(f"   ✓ PROJECT_ROOT: {PROJECT_ROOT}")
        return True
    except Exception as e:
        print(f"   ✗ constantpath failed: {e}")
        return False

def test_settings_file():
    """Test if settings.yaml exists"""
    print("3. Testing settings.yaml...")
    settings_path = Path(__file__).parent.parent / "settings.yaml"
    if settings_path.exists():
        print(f"   ✓ settings.yaml found at: {settings_path}")
        return str(settings_path)
    else:
        print(f"   ✗ settings.yaml not found at: {settings_path}")
        return None

def test_llm_factory_creation(LLMFactory_class):
    """Test LLMFactory creation methods"""
    print("4. Testing LLMFactory creation methods...")
    
    # Test 1: Basic creation (will fail without settings)
    print("   Testing basic creation...")
    try:
        factory = LLMFactory_class()
        print("   ✓ Basic creation successful")
        return factory
    except Exception as e:
        print(f"   ✗ Basic creation failed: {e}")
    
    # Test 2: Local endpoint creation
    print("   Testing local endpoint creation...")
    try:
        factory = LLMFactory_class.create_for_local_endpoint(
            model_name="llama3.1:8b",
            base_url="http://localhost:11434/v1",
            api_key="dummy-key"
        )
        print("   ✓ Local endpoint creation successful")
        return factory
    except Exception as e:
        print(f"   ✗ Local endpoint creation failed: {e}")
    
    # Test 3: Custom settings creation
    print("   Testing custom settings creation...")
    try:
        factory = LLMFactory_class.create_with_custom_settings(
            model_name="test-model",
            base_url="http://test.com/v1",
            api_key="test-key"
        )
        print("   ✓ Custom settings creation successful")
        return factory
    except Exception as e:
        print(f"   ✗ Custom settings creation failed: {e}")
    
    return None

def test_llm_factory_attributes(factory):
    """Test LLMFactory attributes"""
    if factory is None:
        print("   ✗ No factory to test")
        return False
    
    print("5. Testing LLMFactory attributes...")
    try:
        print(f"   ✓ model_name: {factory.model_name}")
        print(f"   ✓ base_url: {factory.base_url}")
        print(f"   ✓ api_key: {factory.api_key[:10]}..." if factory.api_key else "   ✓ api_key: None")
        print(f"   ✓ client: {type(factory.client).__name__}")
        return True
    except Exception as e:
        print(f"   ✗ Attribute test failed: {e}")
        return False

def test_simple_prompt(factory):
    """Test simple prompt execution"""
    if factory is None:
        print("   ✗ No factory to test")
        return False
    
    print("6. Testing simple prompt...")
    try:
        # Test with a simple prompt (without template)
        response = factory.client.chat.completions.create(
            model=factory.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, World!'"}
            ],
            max_tokens=50,
            temperature=0
        )
        result = response.choices[0].message.content
        print(f"   ✓ Simple prompt successful: {result}")
        return True
    except Exception as e:
        print(f"   ✗ Simple prompt failed: {e}")
        return False

def main():
    """Main test function"""
    print("LLMFactory Test Suite")
    print("=" * 50)
    
    # Test 1: Import
    LLMFactory_class = test_llm_factory_import()
    if not LLMFactory_class:
        return
    
    # Test 2: Constantpath
    if not test_constantpath():
        return
    
    # Test 3: Settings file
    settings_path = test_settings_file()
    
    # Test 4: Factory creation
    factory = test_llm_factory_creation(LLMFactory_class)
    
    # Test 5: Attributes
    if factory:
        test_llm_factory_attributes(factory)
        
        # Test 6: Simple prompt (only if we have a working factory)
        test_simple_prompt(factory)
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    main() 