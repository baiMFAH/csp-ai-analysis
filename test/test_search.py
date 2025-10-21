"""
Test script for DuckDuckGo search functionality
"""

import sys
import time
import requests
from bs4 import BeautifulSoup
import urllib.parse

def test_basic_request():
    """Test if we can make a basic request to DuckDuckGo"""
    print("=" * 60)
    print("TEST 1: Basic Request to DuckDuckGo")
    print("=" * 60)

    test_query = "python tutorial"
    url = f"https://duckduckgo.com/html/?q={urllib.parse.quote_plus(test_query)}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    try:
        print(f"🔍 Sending request to: {url}")
        print(f"⏱️  Timeout: 15 seconds")

        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=15)
        elapsed = time.time() - start_time

        print(f"✅ Response received in {elapsed:.2f} seconds")
        print(f"📊 Status code: {response.status_code}")
        print(f"📊 Content length: {len(response.content)} bytes")

        if response.status_code == 200:
            # Try to parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            print(f"✅ HTML parsed successfully")

            # Check for different selectors
            selectors = [
                'a.result__a',
                '.result__title a',
                '.results_links_deep a',
                '.web-result a',
                'h3 a',
                '.result a'
            ]

            print("\n🔍 Checking CSS selectors:")
            for selector in selectors:
                links = soup.select(selector)
                print(f"   {selector}: {len(links)} elements found")
                if links:
                    print(f"      First link: {links[0].get('href', 'no href')[:60]}...")

            # Save HTML to file for inspection
            with open('/tmp/duckduckgo_response.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("\n💾 Full HTML saved to: /tmp/duckduckgo_response.html")

            return True
        else:
            print(f"❌ Non-200 status code: {response.status_code}")
            return False

    except requests.Timeout:
        print(f"❌ Request timed out after 15 seconds")
        return False
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_alternative_search_urls():
    """Test alternative DuckDuckGo URLs"""
    print("\n" + "=" * 60)
    print("TEST 2: Alternative DuckDuckGo URLs")
    print("=" * 60)

    test_query = "python tutorial"
    urls = [
        f"https://duckduckgo.com/html/?q={urllib.parse.quote_plus(test_query)}",
        f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(test_query)}",
        f"https://duckduckgo.com/?q={urllib.parse.quote_plus(test_query)}",
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for i, url in enumerate(urls, 1):
        print(f"\n🔍 Test {i}: {url[:70]}...")
        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            elapsed = time.time() - start_time

            print(f"   ✅ Status: {response.status_code}, Time: {elapsed:.2f}s, Size: {len(response.content)} bytes")

        except requests.Timeout:
            print(f"   ❌ Timeout")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")


def test_with_different_headers():
    """Test with different User-Agent headers"""
    print("\n" + "=" * 60)
    print("TEST 3: Different User-Agent Headers")
    print("=" * 60)

    test_query = "python tutorial"
    url = f"https://duckduckgo.com/html/?q={urllib.parse.quote_plus(test_query)}"

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'curl/7.64.1',
        'Python-requests/2.28.0'
    ]

    for i, ua in enumerate(user_agents, 1):
        print(f"\n🔍 Test {i}: {ua[:50]}...")
        headers = {'User-Agent': ua}

        try:
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            elapsed = time.time() - start_time

            print(f"   ✅ Status: {response.status_code}, Time: {elapsed:.2f}s")

        except requests.Timeout:
            print(f"   ❌ Timeout")
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")


def test_connection_diagnostics():
    """Test basic internet connectivity"""
    print("\n" + "=" * 60)
    print("TEST 4: Connection Diagnostics")
    print("=" * 60)

    test_urls = [
        ("Google", "https://www.google.com"),
        ("Python.org", "https://www.python.org"),
        ("DuckDuckGo main", "https://duckduckgo.com"),
    ]

    for name, url in test_urls:
        print(f"\n🔍 Testing {name}: {url}")
        try:
            start_time = time.time()
            response = requests.get(url, timeout=5)
            elapsed = time.time() - start_time

            print(f"   ✅ Status: {response.status_code}, Time: {elapsed:.2f}s")

        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")


def test_search_from_link_analysis_utils():
    """Test the actual search_duckduckgo function from link_analysis_utils"""
    print("\n" + "=" * 60)
    print("TEST 5: Using search_duckduckgo() from link_analysis_utils")
    print("=" * 60)

    try:
        # Import the function
        sys.path.append('/Users/bai_xiao/Documents/Code/claude-playground/csp-ai-analysis/src')
        from link_analysis_utils import search_duckduckgo

        test_query = "python tutorial"
        print(f"🔍 Searching for: {test_query}")

        start_time = time.time()
        results = search_duckduckgo(test_query, max_results=3)
        elapsed = time.time() - start_time

        print(f"⏱️  Search completed in {elapsed:.2f} seconds")
        print(f"📊 Results found: {len(results)}")

        if results:
            print("\n📋 Search results:")
            for i, result in enumerate(results, 1):
                print(f"\n   {i}. {result.get('title', 'No title')[:60]}...")
                print(f"      URL: {result.get('url', 'No URL')[:60]}...")
                print(f"      Snippet: {result.get('snippet', 'No snippet')[:60]}...")
        else:
            print("❌ No results returned")

        return len(results) > 0

    except Exception as e:
        print(f"❌ Error importing or running search_duckduckgo: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("DUCKDUCKGO SEARCH DIAGNOSTICS")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Basic Request", test_basic_request()))
    time.sleep(1)  # Respect rate limits

    test_alternative_search_urls()
    time.sleep(1)

    test_with_different_headers()
    time.sleep(1)

    test_connection_diagnostics()
    time.sleep(1)

    results.append(("link_analysis_utils function", test_search_from_link_analysis_utils()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    print("\n💡 If all tests fail with timeouts:")
    print("   - Check your internet connection")
    print("   - Check if you're behind a proxy/firewall")
    print("   - DuckDuckGo might be rate-limiting or blocking automated requests")
    print("   - Consider using alternative search methods")


if __name__ == "__main__":
    main()
