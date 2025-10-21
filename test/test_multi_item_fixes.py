#!/usr/bin/env python3
"""
Test script to validate the multi-item entry splitting and URL title generation fixes
"""

import sys
sys.path.append('src')

from link_analysis_utils import split_multi_item_entries, generate_title_from_url_and_summary

def test_multi_item_splitting():
    """Test the multi-item entry splitting function"""
    print("=" * 60)
    print("TESTING MULTI-ITEM ENTRY SPLITTING")
    print("=" * 60)
    
    test_cases = [
        # Case 1: Multiple URLs separated by newlines (from actual data)
        """https://youtu.be/7xTGNNLPyMI?si=dm2ZuxnBymlg99kn

https://www.deeplearning.ai/short-courses/claude-code-a-highly-agentic-coding-assistant/""",
        
        # Case 2: Multiple text references separated by newlines
        """Andrej Karpathy's Zero to Hero series
3Blue1Brown Series on Neural Networks""",
        
        # Case 3: Comma-separated URLs
        "https://coursera.org/course1, https://udemy.com/course2",
        
        # Case 4: Single item (should not be split)
        "https://www.deeplearning.ai/courses/generative-ai-for-software-development/",
        
        # Case 5: Regular text with comma (should not be split)
        "This is a course about AI, machine learning, and data science",
        
        # Case 6: Mixed URL and text on separate lines
        """Course on Deep Learning
https://deeplearning.ai/course"""
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Input: {repr(test_case)}")
        
        result = split_multi_item_entries(test_case)
        print(f"Output: {len(result)} items")
        
        for j, item in enumerate(result):
            print(f"  {j+1}. {repr(item)}")
        
        print("-" * 40)

def test_url_title_generation():
    """Test the enhanced URL title generation"""
    print("\n" + "=" * 60)
    print("TESTING URL TITLE GENERATION")
    print("=" * 60)
    
    test_cases = [
        # Case 1: URL as title with good summary
        {
            'title': 'https://www.deeplearning.ai/courses/generative-ai-for-software-development/',
            'summary': 'Learn practical prompt engineering and pair programming techniques with LLMs to write, test, and improve your code.',
            'url': 'https://www.deeplearning.ai/courses/generative-ai-for-software-development/'
        },
        
        # Case 2: URL as title with poor summary
        {
            'title': 'https://agenticai-learning.org/f25',
            'summary': 'Resource: https://agenticai-learning.org/f25',
            'url': 'https://agenticai-learning.org/f25'
        },
        
        # Case 3: URL with whitespace
        {
            'title': '  https://anthropic.skilljar.com/claude-with-the-anthropic-api  ',
            'summary': 'This comprehensive course covers the full spectrum of working with Anthropic models using the Claude API',
            'url': 'https://anthropic.skilljar.com/claude-with-the-anthropic-api'
        },
        
        # Case 4: Normal title (should not change)
        {
            'title': 'Deep Learning Specialization',
            'summary': 'Complete course on deep learning',
            'url': 'https://coursera.org/specializations/deep-learning'
        },
        
        # Case 5: Domain without protocol
        {
            'title': 'www.youtube.com/watch?v=abc123',
            'summary': 'Video tutorial on neural networks',
            'url': 'https://www.youtube.com/watch?v=abc123'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Original title: {repr(test_case['title'])}")
        print(f"Summary: {test_case['summary'][:50]}...")
        print(f"URL: {test_case['url']}")
        
        result = generate_title_from_url_and_summary(
            test_case['title'], 
            test_case['summary'], 
            test_case['url']
        )
        
        print(f"Generated title: {repr(result)}")
        
        if result != test_case['title']:
            print("✅ Title was improved!")
        else:
            print("ℹ️  Title unchanged (expected for non-URL titles)")
        
        print("-" * 40)

if __name__ == "__main__":
    test_multi_item_splitting()
    test_url_title_generation()
    print("\n✅ All tests completed!")