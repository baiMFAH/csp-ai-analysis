"""
Test script for URL extraction and cleaning
"""

import sys
sys.path.append('/Users/bai_xiao/Documents/Code/claude-playground/csp-ai-analysis/src')

from link_analysis_utils import extract_links_from_text, clean_url


def test_extract_links():
    """Test URL extraction with various formats"""
    print("=" * 60)
    print("TEST: URL Extraction from Text")
    print("=" * 60)

    test_cases = [
        # (input_text, expected_urls)
        ("Check out https://example.com", ["https://example.com"]),
        ("Visit (https://example.com)", ["https://example.com"]),
        ("Link: [https://example.com]", ["https://example.com"]),
        ("URL: https://example.com)", ["https://example.com"]),
        ("See https://example.com.", ["https://example.com"]),
        ("Go to https://example.com, it's great", ["https://example.com"]),
        ("Multiple: https://site1.com and https://site2.com", ["https://site1.com", "https://site2.com"]),
        ("Markdown [text](https://example.com)", ["https://example.com"]),
        ("Wrapped (https://example.com]", ["https://example.com"]),
        ("With port https://example.com:8080/path", ["https://example.com:8080/path"]),
    ]

    passed = 0
    failed = 0

    for i, (text, expected) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {text[:50]}...")
        extracted = extract_links_from_text(text)

        # Sort for comparison
        extracted_sorted = sorted(extracted)
        expected_sorted = sorted(expected)

        if extracted_sorted == expected_sorted:
            print(f"  ✅ PASS - Extracted: {extracted}")
            passed += 1
        else:
            print(f"  ❌ FAIL")
            print(f"     Expected: {expected_sorted}")
            print(f"     Got:      {extracted_sorted}")
            failed += 1

    print(f"\n{'-' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_clean_url():
    """Test URL cleaning function"""
    print("\n" + "=" * 60)
    print("TEST: URL Cleaning")
    print("=" * 60)

    test_cases = [
        # (input_url, expected_url)
        ("https://example.com", "https://example.com"),
        ("https://example.com/", "https://example.com"),
        ("(https://example.com)", "https://example.com"),
        ("[https://example.com]", "https://example.com"),
        ("https://example.com)", "https://example.com"),
        ("(https://example.com]", "https://example.com"),
        ("https://example.com.", "https://example.com"),
        ("https://example.com,", "https://example.com"),
        ("https://example.com;", "https://example.com"),
        ("(https://example.com/path)", "https://example.com/path"),
        ("[https://example.com/path]", "https://example.com/path"),
        ("example.com", "https://example.com"),
        ("www.example.com", "https://www.example.com"),
    ]

    passed = 0
    failed = 0

    for i, (input_url, expected) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {input_url}")
        cleaned = clean_url(input_url)

        if cleaned == expected:
            print(f"  ✅ PASS - {cleaned}")
            passed += 1
        else:
            print(f"  ❌ FAIL")
            print(f"     Expected: {expected}")
            print(f"     Got:      {cleaned}")
            failed += 1

    print(f"\n{'-' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_real_world_examples():
    """Test with real-world examples from survey data"""
    print("\n" + "=" * 60)
    print("TEST: Real-World Examples")
    print("=" * 60)

    examples = [
        "https://youtu.be/7xTGNNLPyMI?si=dm2ZuxnBymlg99kn",
        "(https://www.deeplearning.ai/short-courses/)",
        "[https://www.coursera.org/specializations/deep-learning]",
        "Check out https://www.udemy.com/course/python-bootcamp/.",
        "Link: https://www.fast.ai), great course",
    ]

    for i, text in enumerate(examples, 1):
        print(f"\n{i}. Input: {text}")
        urls = extract_links_from_text(text)
        print(f"   Extracted URLs: {urls}")
        if urls:
            for url in urls:
                cleaned = clean_url(url)
                print(f"   Cleaned: {cleaned}")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("URL EXTRACTION AND CLEANING TESTS")
    print("=" * 60)

    results = []

    results.append(("Extract Links", test_extract_links()))
    results.append(("Clean URL", test_clean_url()))

    test_real_world_examples()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")


if __name__ == "__main__":
    main()
