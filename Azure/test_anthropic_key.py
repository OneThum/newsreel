#!/usr/bin/env python3
"""
Test script to verify Anthropic API key is working
"""

import os
import sys
import anthropic
from datetime import datetime

# Add functions to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'functions'))

def test_anthropic_key():
    """Test that the Anthropic API key works"""
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        return False

    if not api_key.startswith("sk-ant-api03-"):
        print("❌ ANTHROPIC_API_KEY doesn't look like a valid key")
        return False

    try:
        print("🔑 Testing Anthropic API key...")
        client = anthropic.Anthropic(api_key=api_key)

        # Simple test message
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'Hello, world!' and nothing else."}]
        )

        result = response.content[0].text.strip()
        print(f"✅ API key works! Response: '{result}'")

        if result.lower() == "hello, world!":
            print("🎉 Anthropic API key is fully functional!")
            return True
        else:
            print(f"⚠️ Unexpected response: {result}")
            return True  # Still works, just unexpected

    except Exception as e:
        print(f"❌ Anthropic API key test failed: {e}")
        return False

def test_summarization_function():
    """Test the summarization function directly"""
    try:
        from shared.utils import build_summarization_prompt

        # Test data
        articles = [{
            "title": "Test Article",
            "description": "This is a test article for summarization.",
            "content": "This is test content that should be summarized by Claude."
        }]

        prompt, system_msg = build_summarization_prompt(articles)
        print("✅ Summarization prompt building works")
        print(f"📝 Prompt length: {len(prompt)} characters")
        return True

    except Exception as e:
        print(f"❌ Summarization function test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTING ANTHROPIC API KEY SETUP")
    print("=" * 50)

    key_works = test_anthropic_key()
    print()

    func_works = test_summarization_function()
    print()

    if key_works and func_works:
        print("🎉 ALL TESTS PASSED - Summarization should work!")
        print()
        print("📋 Next steps:")
        print("   1. The function app has been restarted")
        print("   2. Summarization should work on new stories")
        print("   3. Run the iOS quality test again in a few minutes")
    else:
        print("❌ SOME TESTS FAILED - Check the errors above")




