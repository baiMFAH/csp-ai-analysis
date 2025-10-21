#!/usr/bin/env python3
"""
Test function for URL processing: fetch basic info and generate human-readable title and summary
"""

import sys
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import time

def fetch_url_info(url, timeout=15):
    """
    Fetch basic information from a URL and generate human-readable title and summary
    
    Args:
        url (str): The URL to process
        timeout (int): Request timeout in seconds
        
    Returns:
        dict: Contains 'original_url', 'title', 'summary', 'status', 'raw_title', 'raw_description'
    """
    try:
        # Clean up URL
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print(f"🔍 Fetching: {url}")
        
        # Set up headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Fetch the page
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract raw title
        raw_title = None
        if soup.title and soup.title.string:
            raw_title = soup.title.string.strip()
        
        # Extract raw description
        raw_description = None
        
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            raw_description = meta_desc.get('content').strip()
        
        # Try og:description if no meta description
        if not raw_description:
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc and og_desc.get('content'):
                raw_description = og_desc.get('content').strip()
        
        # Try Twitter description
        if not raw_description:
            twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
            if twitter_desc and twitter_desc.get('content'):
                raw_description = twitter_desc.get('content').strip()
        
        # Generate human-readable title
        title = generate_readable_title(raw_title, url)
        
        # Generate short summary
        summary = generate_short_summary(raw_description, raw_title, url)
        
        return {
            'original_url': url,
            'title': title,
            'summary': summary,
            'status': 'success',
            'raw_title': raw_title,
            'raw_description': raw_description
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'original_url': url,
            'title': f"Error accessing URL",
            'summary': f"Failed to fetch content: {str(e)}",
            'status': 'error',
            'raw_title': None,
            'raw_description': None
        }
    except Exception as e:
        return {
            'original_url': url,
            'title': f"Processing error",
            'summary': f"Error processing URL: {str(e)}",
            'status': 'error',
            'raw_title': None,
            'raw_description': None
        }

def generate_readable_title(raw_title, url):
    """
    Generate a human-readable title from raw title and URL
    
    Args:
        raw_title (str): Raw title from the webpage
        url (str): The URL being processed
        
    Returns:
        str: Human-readable title
    """
    if not raw_title:
        # Extract from URL path as fallback
        return extract_title_from_url(url)
    
    # Clean up the raw title
    title = raw_title.strip()
    
    # Remove common suffixes like site names
    common_separators = [' | ', ' - ', ' :: ', ' — ', ' – ']
    for sep in common_separators:
        if sep in title:
            parts = title.split(sep)
            # Take the first part if it's substantial, otherwise keep original
            if len(parts[0].strip()) > 10:
                title = parts[0].strip()
                break
    
    # Clean up common patterns
    # Remove parenthetical content at the end that looks like site names
    title = re.sub(r'\s*\([^)]*\)\s*$', '', title)
    
    # Handle DeepLearning.AI specific patterns
    if 'deeplearning.ai' in url.lower():
        # Convert "Claude Code: A Highly Agentic Coding Assistant | DeepLearning.AI" 
        # to "Claude Code: A Highly Agentic Coding Assistant"
        title = re.sub(r'\s*\|\s*DeepLearning\.AI\s*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*-\s*DeepLearning\.AI\s*$', '', title, flags=re.IGNORECASE)
    
    # Handle Coursera patterns
    if 'coursera.org' in url.lower():
        title = re.sub(r'\s*\|\s*Coursera\s*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*-\s*Coursera\s*$', '', title, flags=re.IGNORECASE)
    
    # Handle YouTube patterns
    if 'youtube.com' in url.lower() or 'youtu.be' in url.lower():
        title = re.sub(r'\s*-\s*YouTube\s*$', '', title, flags=re.IGNORECASE)
    
    # Capitalize properly
    title = title.strip()
    
    # If title is still too generic or empty, extract from URL
    if not title or len(title) < 5 or title.lower() in ['untitled', 'no title', 'home', 'index']:
        title = extract_title_from_url(url)
    
    return title

def extract_title_from_url(url):
    """
    Extract a readable title from URL path
    
    Args:
        url (str): The URL to extract title from
        
    Returns:
        str: Extracted title
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        path = parsed.path.strip('/')
        
        if path:
            # Remove file extensions
            path = re.sub(r'\.(html|php|aspx|jsp)$', '', path)
            
            # Split path and take the last meaningful part
            path_parts = path.split('/')
            
            # Look for meaningful path components (not just numbers or short codes)
            for part in reversed(path_parts):
                if len(part) > 3 and not part.isdigit():
                    # Convert kebab-case and snake_case to title case
                    readable = re.sub(r'[-_]', ' ', part)
                    readable = readable.title()
                    
                    # Add domain context
                    domain_name = domain.split('.')[0].title()
                    return f"{readable} - {domain_name}"
        
        # Fallback: use domain name
        domain_name = domain.split('.')[0].title()
        return f"{domain_name} Resource"
        
    except Exception:
        return "Online Resource"

def generate_short_summary(raw_description, raw_title, url):
    """
    Generate a concise summary from description and context
    
    Args:
        raw_description (str): Raw description from webpage
        raw_title (str): Raw title from webpage  
        url (str): The URL being processed
        
    Returns:
        str: Short summary
    """
    if raw_description and len(raw_description.strip()) > 20:
        summary = raw_description.strip()
        
        # Limit length
        if len(summary) > 200:
            # Try to cut at sentence boundary
            sentences = summary.split('.')
            if sentences and len(sentences[0]) > 50 and len(sentences[0]) < 180:
                summary = sentences[0] + '.'
            else:
                summary = summary[:197] + '...'
        
        return summary
    
    # Fallback: use title or generate generic summary
    if raw_title and len(raw_title.strip()) > 10:
        return f"Educational resource: {raw_title.strip()}"
    
    # Final fallback based on domain
    try:
        domain = urlparse(url).netloc.replace('www.', '')
        domain_name = domain.split('.')[0].title()
        
        if 'deeplearning' in domain.lower():
            return "AI and machine learning course from DeepLearning.AI"
        elif 'coursera' in domain.lower():
            return "Online course from Coursera"
        elif 'youtube' in domain.lower():
            return "Educational video content"
        elif 'github' in domain.lower():
            return "Code repository and learning resource"
        else:
            return f"Learning resource from {domain_name}"
            
    except Exception:
        return "Educational AI/ML resource"

def test_url_processing():
    """Test the URL processing function with various examples"""
    
    test_urls = [
        # DeepLearning.AI example from user
        "https://www.deeplearning.ai/short-courses/claude-code-a-highly-agentic-coding-assistant/",
        
        # Other test cases
        "https://www.coursera.org/specializations/deep-learning",
        "https://www.youtube.com/watch?v=aircAruvnKk",
        "https://github.com/anthropics/courses",
        "https://agenticai-learning.org/f25",
        "https://anthropic.skilljar.com/claude-with-the-anthropic-api",
    ]
    
    print("=" * 80)
    print("URL PROCESSING TEST")
    print("=" * 80)
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🔍 Test {i}: {url}")
        print("-" * 60)
        
        result = fetch_url_info(url)
        
        print(f"✅ Status: {result['status']}")
        print(f"📝 Generated Title: {result['title']}")
        print(f"📄 Generated Summary: {result['summary']}")
        
        if result['status'] == 'success':
            print(f"🔍 Raw Title: {result['raw_title']}")
            print(f"🔍 Raw Description: {result['raw_description'][:100]}..." if result['raw_description'] and len(result['raw_description']) > 100 else f"🔍 Raw Description: {result['raw_description']}")
        
        print("-" * 60)
        
        # Small delay to be respectful
        time.sleep(1)
    
    print("\n✅ URL processing test completed!")

if __name__ == "__main__":
    test_url_processing()