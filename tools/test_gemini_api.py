#!/usr/bin/env python3
"""
Test Gemini API key and connection.
Checks if the API key is valid and working.
"""

import os
import sys
from pathlib import Path

# Change to project root directory
project_root = Path(__file__).parent.parent
os.chdir(project_root)

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_api():
    """Test Gemini API key."""
    print("="*70)
    print("Gemini API Key Test")
    print("="*70)
    
    # Check if API key is set
    api_key = os.getenv("GEMINI_API_KEY")
    
    print("\n1. Checking API Key Configuration:")
    print("-" * 70)
    
    if not api_key:
        print("  ❌ GEMINI_API_KEY not found in environment")
        print("  Please set GEMINI_API_KEY in .env file")
        return False
    
    # Mask API key for display
    if len(api_key) > 20:
        masked_key = api_key[:10] + "..." + api_key[-10:]
    else:
        masked_key = "***"
    
    print(f"  ✅ API Key found: {masked_key}")
    print(f"  ✅ Key length: {len(api_key)} characters")
    
    # Try to import google.generativeai
    print("\n2. Checking Dependencies:")
    print("-" * 70)
    try:
        import google.generativeai as genai
        print("  ✅ google.generativeai imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import google.generativeai: {e}")
        print("  Please install: pip install google-generativeai")
        return False
    
    # Configure API
    print("\n3. Configuring API:")
    print("-" * 70)
    try:
        genai.configure(api_key=api_key)
        print("  ✅ API configured successfully")
    except Exception as e:
        print(f"  ❌ Failed to configure API: {e}")
        return False
    
    # Test model availability
    print("\n4. Testing Model Availability:")
    print("-" * 70)
    
    # Try different models (including the one from config)
    models_to_test = [
        "gemini-2.5-flash-preview-09-2025",  # From config
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro",
    ]
    
    available_models = []
    for model_name in models_to_test:
        try:
            model = genai.GenerativeModel(model_name)
            available_models.append(model_name)
            print(f"  ✅ {model_name} - available")
        except Exception as e:
            print(f"  ⚠️  {model_name} - not available: {str(e)[:50]}")
    
    if not available_models:
        print("  ❌ No models available")
        return False
    
    # Test simple generation
    print("\n5. Testing API Call:")
    print("-" * 70)
    
    test_model = available_models[0]
    print(f"  Using model: {test_model}")
    
    try:
        model = genai.GenerativeModel(test_model)
        
        test_prompt = "Say 'Hello, Gemini API is working!' in one sentence."
        print(f"  Test prompt: {test_prompt}")
        print("  Sending request...")
        
        response = model.generate_content(
            test_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=50,
            )
        )
        
        result_text = response.text if hasattr(response, 'text') else str(response)
        
        if result_text:
            print(f"  ✅ Response received: {result_text[:100]}")
            
            # Check usage metadata if available
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                print(f"\n  Usage info:")
                print(f"    Prompt tokens: {getattr(usage, 'prompt_token_count', 'N/A')}")
                print(f"    Candidates tokens: {getattr(usage, 'candidates_token_count', 'N/A')}")
                print(f"    Total tokens: {getattr(usage, 'total_token_count', 'N/A')}")
            
            print("\n" + "="*70)
            print("✅ SUCCESS: Gemini API is working correctly!")
            print("="*70)
            return True
        else:
            print("  ⚠️  Response received but empty")
            print(f"  Response object: {response}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        print(f"  ❌ API call failed: {error_msg}")
        
        # Provide helpful error messages
        if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            print("\n  💡 This usually means:")
            print("     - API key is incorrect")
            print("     - API key has been revoked")
            print("     - API key doesn't have proper permissions")
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            print("\n  💡 This usually means:")
            print("     - API quota exceeded")
            print("     - Rate limit reached")
        elif "permission" in error_msg.lower():
            print("\n  💡 This usually means:")
            print("     - API key doesn't have access to Gemini API")
            print("     - Need to enable Gemini API in Google Cloud Console")
        
        print("\n" + "="*70)
        print("❌ FAILED: Gemini API test failed")
        print("="*70)
        return False

def main():
    """Main function."""
    success = test_gemini_api()
    
    if success:
        print("\n✅ All tests passed! Gemini API is ready to use.")
        return 0
    else:
        print("\n❌ Tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())


