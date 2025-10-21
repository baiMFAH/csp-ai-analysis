"""
URL Summarizer Module

Fetches content from a URL and generates a human-readable title and short summary.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from urllib.parse import urlparse
import re


def fetch_url_summary(url: str) -> Dict[str, str]:
    """
    Fetches a URL and extracts a title and short summary.

    Args:
        url: The URL to fetch and summarize

    Returns:
        Dictionary with 'title' and 'summary' keys

    Raises:
        requests.RequestException: If the URL cannot be fetched
        ValueError: If the content cannot be parsed
    """
    try:
        # Fetch the URL content with realistic browser headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

        response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        response.raise_for_status()

    except requests.HTTPError as e:
        # Handle 403 Forbidden errors - try to extract info from URL
        if e.response.status_code == 403:
            # Special handling for Udemy
            if 'udemy.com' in url.lower():
                # Try to extract from /course/ pattern
                match = re.search(r'/course/([^/?]+)', url)
                if match:
                    course_slug = match.group(1)
                    title = course_slug.replace('-', ' ').title()
                    return {
                        'title': f"{title} (Udemy Course)",
                        'summary': f"Udemy course: {title}. Access blocked - please visit URL to see full details."
                    }
                # Handle /share/ URLs (no course name available)
                elif '/share/' in url.lower():
                    return {
                        'title': "Udemy Course (Shared Link)",
                        'summary': "Udemy course shared link. Access blocked - please visit URL to see course details."
                    }
            # For other sites with 403
            raise requests.RequestException(f"Access denied (403): {url}")
        else:
            raise

    try:

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract title - try multiple sources (pass URL for special handling)
        title = _extract_title(soup, url)

        # Extract summary - try multiple sources
        summary = _extract_summary(soup)

        # Special case: If Amazon was blocked but we got a good summary with book title
        if 'amazon' in url.lower() and 'ASIN:' in title and summary and summary != 'No summary found':
            # Try to extract book title from summary (usually starts with title)
            extracted_title = _extract_title_from_summary(summary)
            if extracted_title:
                title = extracted_title

        return {
            'title': title,
            'summary': summary
        }

    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to fetch URL: {e}")
    except Exception as e:
        raise ValueError(f"Failed to parse content: {e}")


def _extract_title(soup: BeautifulSoup, url: str = None) -> str:
    """Extract title from various HTML sources, with special handling for book retailers."""

    # Special handling for Amazon product pages
    if url and 'amazon.com' in url.lower():
        return _extract_amazon_title(soup, url)

    # Special handling for Udemy courses
    if url and 'udemy.com' in url.lower():
        return _extract_udemy_title(soup, url)

    # Special handling for other book retailers
    if url and any(retailer in url.lower() for retailer in ['barnesandnoble.com', 'bn.com', 'bookshop.org', 'indiebound.org']):
        return _extract_book_retailer_title(soup)

    # Try Open Graph title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        title = og_title['content'].strip()
        # Clean up common title suffixes
        title = _clean_title(title)
        return title

    # Try Twitter title
    twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
    if twitter_title and twitter_title.get('content'):
        title = twitter_title['content'].strip()
        title = _clean_title(title)
        return title

    # Try standard title tag
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        title = title_tag.string.strip()
        title = _clean_title(title)
        return title

    # Try h1 tag
    h1_tag = soup.find('h1')
    if h1_tag:
        title = h1_tag.get_text().strip()
        title = _clean_title(title)
        return title

    return "No title found"


def _extract_amazon_title(soup: BeautifulSoup, url: str = None) -> str:
    """Extract book title from Amazon product pages."""
    # Check if we got a CAPTCHA/bot detection page
    page_text = soup.get_text()
    if 'robot' in page_text.lower() or 'captcha' in page_text.lower() or 'automated access' in page_text.lower():
        # Amazon blocked us - return a helpful message with ASIN
        if url:
            asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
            if asin_match:
                return f"Amazon Book (ASIN: {asin_match.group(1)})"
        return "Amazon Book (Access Blocked - Please verify manually)"

    # Try product title span (most reliable for books)
    product_title = soup.find('span', {'id': 'productTitle'})
    if product_title:
        title = product_title.get_text().strip()
        # Clean up extra whitespace
        title = re.sub(r'\s+', ' ', title)
        return title

    # Try book title span
    book_title = soup.find('span', {'id': 'ebooksProductTitle'})
    if book_title:
        title = book_title.get_text().strip()
        title = re.sub(r'\s+', ' ', title)
        return title

    # Try h1 with product title class
    h1_product = soup.find('h1', class_=lambda x: x and 'product' in x.lower())
    if h1_product:
        title = h1_product.get_text().strip()
        title = re.sub(r'\s+', ' ', title)
        return title

    # Fallback to Open Graph or title tag
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        title = og_title['content'].strip()
        # Remove "Amazon.com: " prefix if present
        title = re.sub(r'^Amazon\.com:\s*', '', title)
        # Remove " : Books" or similar suffixes
        title = re.sub(r'\s*:\s*(Books|Kindle Store|Everything Else).*$', '', title)
        return title

    # Last resort: Extract ASIN from URL and provide that
    if url:
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if asin_match:
            return f"Amazon Book (ASIN: {asin_match.group(1)})"

    return "Amazon product (title not found)"


def _extract_udemy_title(soup: BeautifulSoup, url: str = None) -> str:
    """Extract course title from Udemy pages."""
    # Check if we got blocked (403 error or access denied page)
    page_text = soup.get_text()
    if 'access denied' in page_text.lower() or '403 forbidden' in page_text.lower() or len(page_text) < 500:
        # Udemy blocked us - try to extract course name from URL
        if url:
            # Extract course slug from URL pattern: /course/course-name/
            match = re.search(r'/course/([^/?]+)', url)
            if match:
                course_slug = match.group(1)
                # Convert slug to title (replace hyphens with spaces, title case)
                title = course_slug.replace('-', ' ').title()
                return f"{title} (Udemy Course)"
        return "Udemy Course (Access Blocked - Please verify manually)"

    # Try course title from various selectors
    # Udemy uses different structures, try multiple approaches

    # Try data-purpose="course-header-title"
    course_header = soup.find(attrs={'data-purpose': 'course-header-title'})
    if course_header:
        title = course_header.get_text().strip()
        title = re.sub(r'\s+', ' ', title)
        return title

    # Try h1 with course title class
    h1_course = soup.find('h1', class_=lambda x: x and 'course' in str(x).lower())
    if h1_course:
        title = h1_course.get_text().strip()
        title = re.sub(r'\s+', ' ', title)
        return title

    # Try Open Graph title
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        title = og_title['content'].strip()
        # Remove "| Udemy" suffix if present
        title = re.sub(r'\s*[\|\-]\s*Udemy.*$', '', title, flags=re.IGNORECASE)
        return title

    # Try Twitter title
    twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
    if twitter_title and twitter_title.get('content'):
        title = twitter_title['content'].strip()
        title = re.sub(r'\s*[\|\-]\s*Udemy.*$', '', title, flags=re.IGNORECASE)
        return title

    # Try standard title tag
    title_tag = soup.find('title')
    if title_tag and title_tag.string:
        title = title_tag.string.strip()
        # Remove "| Udemy" suffix
        title = re.sub(r'\s*[\|\-]\s*Udemy.*$', '', title, flags=re.IGNORECASE)
        if title and title.lower() != 'udemy':
            return title

    # Last resort: Extract from URL
    if url:
        match = re.search(r'/course/([^/?]+)', url)
        if match:
            course_slug = match.group(1)
            title = course_slug.replace('-', ' ').title()
            return f"{title} (Udemy Course)"

    return "Udemy Course (title not found)"


def _extract_book_retailer_title(soup: BeautifulSoup) -> str:
    """Extract book title from other book retailer pages."""
    # Try common book title selectors
    book_title_selectors = [
        ('h1', {'class': lambda x: x and 'product' in str(x).lower()}),
        ('h1', {'class': lambda x: x and 'title' in str(x).lower()}),
        ('div', {'class': lambda x: x and 'product-title' in str(x).lower()}),
        ('span', {'class': lambda x: x and 'product-title' in str(x).lower()}),
    ]

    for tag, attrs in book_title_selectors:
        element = soup.find(tag, attrs)
        if element:
            title = element.get_text().strip()
            title = re.sub(r'\s+', ' ', title)
            return title

    # Fallback to standard extraction
    og_title = soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content'].strip()

    return "Book (title not found)"


def _clean_title(title: str) -> str:
    """Clean up common title suffixes and prefixes."""
    if not title:
        return title

    # Remove common site name suffixes (case-insensitive)
    patterns_to_remove = [
        r'\s*[\|\-]\s*Amazon\.com.*$',
        r'\s*[\|\-]\s*Barnes & Noble.*$',
        r'\s*[\|\-]\s*Goodreads.*$',
        r'\s*[\|\-]\s*YouTube.*$',
        r'\s*[\|\-]\s*Udemy.*$',
        r'\s*[\|\-]\s*Coursera.*$',
        r'\s*[\|\-]\s*DeepLearning\.AI.*$',
        r'\s*\|\s*.*?\s*$',  # Remove generic "| Site Name" suffixes
    ]

    for pattern in patterns_to_remove:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)

    # Clean up whitespace
    title = re.sub(r'\s+', ' ', title).strip()

    return title


def _extract_title_from_summary(summary: str) -> Optional[str]:
    """Extract book title from Amazon summary text."""
    if not summary:
        return None

    # Pattern: "Title [Author] on Amazon.com"
    match = re.match(r'^(.+?)\s+\[.+?\]\s+on\s+Amazon\.com', summary)
    if match:
        return match.group(1).strip()

    # Pattern: "Title by Author on Amazon"
    match = re.match(r'^(.+?)\s+by\s+.+?\s+on\s+Amazon', summary, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern: Just get the first sentence if it looks like a title
    first_sentence = summary.split('.')[0].strip()
    # If first sentence is reasonable length and doesn't contain "FREE shipping"
    if 20 < len(first_sentence) < 150 and 'free shipping' not in first_sentence.lower():
        return first_sentence

    return None


def _extract_summary(soup: BeautifulSoup) -> str:
    """Extract summary/description from various HTML sources."""
    # Try Open Graph description
    og_desc = soup.find('meta', property='og:description')
    if og_desc and og_desc.get('content'):
        return og_desc['content'].strip()

    # Try meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        return meta_desc['content'].strip()

    # Try Twitter description
    twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
    if twitter_desc and twitter_desc.get('content'):
        return twitter_desc['content'].strip()

    # Try to find first paragraph
    paragraphs = soup.find_all('p')
    for p in paragraphs:
        text = p.get_text().strip()
        if len(text) > 50:  # Only consider substantial paragraphs
            return text[:500]  # Limit to 500 characters

    return "No summary found"


def test_url_summarizer():
    """Test function for the URL summarizer."""
    # Test URLs
    test_urls = [
        "http://www.amazon.com/dp/1098166302",  # Amazon book
        "http://www.udemy.com/course/the-complete-agentic-ai-engineering-course",  # Udemy course
        "https://www.deeplearning.ai/short-courses/claude-code-a-highly-agentic-coding-assistant/",  # DeepLearning.AI
    ]

    for test_url in test_urls:
        print(f"Testing URL: {test_url}")
        print("=" * 80)

        try:
            result = fetch_url_summary(test_url)
            print(f"✅ Title: {result['title']}")
            print(f"📄 Summary: {result['summary'][:200]}...")

        except Exception as e:
            print(f"❌ Error: {e}")

        print("\n")


if __name__ == "__main__":
    test_url_summarizer()
