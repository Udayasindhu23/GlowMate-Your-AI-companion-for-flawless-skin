#!/usr/bin/env python
"""
Test script for chatbot functionality
"""
from chatbot.bot_engine import get_chatbot_response

def test_chatbot():
    """Test various chatbot queries"""
    test_queries = [
        "What should I do for acne?",
        "How often should I exfoliate?",
        "Which sunscreen suits oily skin?",
        "Tell me about my skincare routine",
        "What's good for dark circles?",
        "Hello",
        "Help me with wrinkles",
        "My skin is sensitive, what should I use?",
    ]
    
    print("=" * 60)
    print("Testing Chatbot Responses")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. User: {query}")
        try:
            response = get_chatbot_response(query)
            print(f"   Bot: {response}")
        except Exception as e:
            print(f"   ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("Chatbot test completed!")
    print("=" * 60)

if __name__ == '__main__':
    test_chatbot()

