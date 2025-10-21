"""
Enhanced Link Analysis Utility Functions

This module contains all utility functions for processing and analyzing links
from survey data, including web search functionality and resource categorization.
"""

import pandas as pd
import numpy as np
import re
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse, urljoin
import urllib.parse


def extract_links_from_text(text):
    """Extract URLs from text using regex patterns and clean them"""
    if pd.isna(text) or text == '':
        return []

    # Convert to string if not already
    text = str(text)

    # Regex pattern to find URLs
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)

    # Also look for www. patterns without http
    www_pattern = r'www\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    www_urls = re.findall(www_pattern, text)

    # Add http:// to www URLs
    www_urls = ['http://' + url for url in www_urls]

    # Combine all URLs
    all_urls = urls + www_urls

    # Clean each URL to remove trailing punctuation and brackets
    cleaned_urls = []
    for url in all_urls:
        # Remove trailing brackets, parentheses, and common punctuation
        while url and url[-1] in ')].,;:!?\'"':
            url = url[:-1]

        # Remove leading brackets and parentheses
        while url and url[0] in '([':
            url = url[1:]

        if url:  # Only add non-empty URLs
            cleaned_urls.append(url)

    return list(set(cleaned_urls))  # Remove duplicates


def identify_resource_references(text):
    """Identify potential resource references in text that don't contain URLs"""
    if pd.isna(text) or text == '' or len(str(text).strip()) < 3:
        return []
    
    text = str(text).strip()
    text_lower = text.lower()
    
    # Skip if already contains URLs
    if extract_links_from_text(text):
        return []
    
    # Check for Slack channels (starts with #)
    if text.startswith('#'):
        return [text]
    
    # Check for O'Reilly book pattern
    oreilly_pattern = r"o'reilly\s+([^,\n]+)"
    oreilly_match = re.search(oreilly_pattern, text_lower)
    if oreilly_match:
        return [text]
    
    # Return early for very short text to avoid false positives
    if len(text.strip()) < 10:
        return []
    
    # Patterns that suggest this is a resource reference
    resource_indicators = [
        r"course", r"series", r"tutorial", r"book", r"guide", r"training",
        r"lecture", r"workshop", r"certification", r"learning", r"education",
        r"class", r"lesson", r"program", r"specialization", r"nanodegree"
    ]
    
    # Creator/platform indicators
    creator_patterns = [
        r"[A-Z][a-z]+ [A-Z][a-z]+(?:'s|s'?)?",  # Names like "Andrej Karpathy's"
        r"(?:by|from|created by|taught by|with) [A-Z][a-z]+ [A-Z][a-z]+",
        r"coursera", r"udemy", r"edx", r"youtube", r"deeplearning\.ai",
        r"mit", r"stanford", r"harvard", r"berkeley"
    ]
    
    # Check if text contains resource indicators
    has_resource_indicator = any(re.search(pattern, text_lower) for pattern in resource_indicators)
    has_creator_pattern = any(re.search(pattern, text_lower) for pattern in creator_patterns)
    
    # If it looks like a resource reference, return it
    if has_resource_indicator or has_creator_pattern:
        return [text]
    
    # Additional check for specific known patterns
    known_references = [
        r"zero to hero",
        r"machine learning.*course",
        r"deep learning.*specialization",
        r"python.*tutorial",
        r"data science.*course",
        r"ai.*course",
        r"neural network.*course"
    ]
    
    if any(re.search(pattern, text_lower) for pattern in known_references):
        return [text]
    
    return []


def construct_search_query(text_reference):
    """Construct effective search queries for resource references"""
    text = str(text_reference).strip()
    text_lower = text.lower()
    
    # Handle Slack channels - don't search for these
    if text.startswith('#'):
        return []
    
    # Handle O'Reilly books
    oreilly_pattern = r"o'reilly\s+([^,\n]+)"
    oreilly_match = re.search(oreilly_pattern, text_lower)
    if oreilly_match:
        book_title = oreilly_match.group(1).strip()
        return [
            f'"{book_title}" O\'Reilly book site:oreilly.com',
            f'"{book_title}" book O\'Reilly amazon',
            f'O\'Reilly "{book_title}" learning'
        ]
    
    # Base query is the original text
    base_query = text
    
    # Enhanced queries based on patterns
    queries = []
    
    # For video series (especially YouTube)
    if any(term in text_lower for term in ['series', 'video', 'tutorial', 'lecture']):
        queries.append(f'"{text}" site:youtube.com')
        queries.append(f'{text} youtube playlist')
    
    # For courses
    if any(term in text_lower for term in ['course', 'training', 'specialization']):
        queries.append(f'"{text}" course')
        queries.append(f'{text} site:coursera.org OR site:udemy.com OR site:edx.org')
    
    # For books
    if 'book' in text_lower:
        queries.append(f'"{text}" book amazon')
        queries.append(f'{text} site:goodreads.com OR site:amazon.com')
    
    # Specific patterns
    if 'zero to hero' in text_lower:
        if 'karpathy' in text_lower:
            queries.append('Andrej Karpathy Zero to Hero neural networks site:youtube.com')
            queries.append('Andrej Karpathy makemore micrograd course')
    
    if 'deep learning' in text_lower and any(name in text_lower for name in ['andrew ng', 'coursera']):
        queries.append('Andrew Ng Deep Learning Specialization site:coursera.org')
    
    # Generic fallback
    queries.append(f'{text} course tutorial')
    queries.append(base_query)
    
    return queries[:3]  # Return top 3 queries


def parse_search_results(links, max_results):
    """Parse search result links from BeautifulSoup elements"""
    results = []
    
    for link in links:
        if len(results) >= max_results:
            break
            
        href = link.get('href')
        title = link.get_text().strip()
        
        if href and title:
            # Clean up the URL
            if href.startswith('/l/?uddg='):
                # DuckDuckGo redirect URL
                try:
                    actual_url = urllib.parse.parse_qs(urllib.parse.urlparse(href).query)['uddg'][0]
                    actual_url = urllib.parse.unquote(actual_url)
                except:
                    actual_url = href
            elif href.startswith('/'):
                # Relative URL, skip it
                continue
            else:
                actual_url = href
            
            # Validate URL
            if actual_url.startswith('http'):
                results.append({
                    'url': actual_url,
                    'title': title,
                    'snippet': ''
                })
    
    return results


def attempt_direct_url_construction(query):
    """Attempt to construct direct URLs for known platforms and resources"""
    query_lower = query.lower()
    results = []

    # YouTube searches
    if any(term in query_lower for term in ['youtube', 'video', 'karpathy', 'zero to hero']):
        if 'karpathy' in query_lower and 'zero to hero' in query_lower:
            results.append({
                'url': 'https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ',
                'title': 'Neural Networks: Zero to Hero by Andrej Karpathy',
                'snippet': 'Complete neural networks course'
            })

    # Coursera courses
    if 'deep learning' in query_lower and any(name in query_lower for name in ['andrew ng', 'ng']):
        results.append({
            'url': 'https://www.coursera.org/specializations/deep-learning',
            'title': 'Deep Learning Specialization by Andrew Ng',
            'snippet': 'Complete deep learning specialization'
        })

    if 'machine learning' in query_lower and any(name in query_lower for name in ['andrew ng', 'ng', 'coursera']):
        results.append({
            'url': 'https://www.coursera.org/learn/machine-learning',
            'title': 'Machine Learning by Andrew Ng - Coursera',
            'snippet': 'Complete machine learning course'
        })

    # DeepLearning.AI
    if 'deeplearning.ai' in query_lower or 'deep learning ai' in query_lower:
        results.append({
            'url': 'https://www.deeplearning.ai/courses/',
            'title': 'DeepLearning.AI Courses',
            'snippet': 'AI courses and specializations'
        })

    # Fast.ai
    if 'fast.ai' in query_lower or 'fastai' in query_lower:
        results.append({
            'url': 'https://www.fast.ai/',
            'title': 'fast.ai - Practical Deep Learning',
            'snippet': 'Practical deep learning for coders'
        })

    # Udemy generic
    if 'udemy' in query_lower and 'python' in query_lower:
        results.append({
            'url': 'https://www.udemy.com/courses/search/?q=python',
            'title': 'Python Courses on Udemy',
            'snippet': 'Python courses and tutorials'
        })

    # edX courses
    if 'edx' in query_lower and any(term in query_lower for term in ['mit', 'harvard', 'cs50']):
        if 'cs50' in query_lower:
            results.append({
                'url': 'https://www.edx.org/course/cs50s-introduction-to-computer-science',
                'title': "CS50's Introduction to Computer Science - Harvard",
                'snippet': 'Harvard CS50 computer science course'
            })

    # Stanford courses
    if 'stanford' in query_lower:
        if 'cs229' in query_lower or ('machine learning' in query_lower and 'ng' in query_lower):
            results.append({
                'url': 'http://cs229.stanford.edu/',
                'title': 'CS229: Machine Learning - Stanford',
                'snippet': 'Stanford machine learning course'
            })
        if 'cs231n' in query_lower or 'computer vision' in query_lower:
            results.append({
                'url': 'http://cs231n.stanford.edu/',
                'title': 'CS231n: Convolutional Neural Networks - Stanford',
                'snippet': 'Stanford computer vision course'
            })

    # Books - O'Reilly
    if "o'reilly" in query_lower or 'oreilly' in query_lower:
        results.append({
            'url': 'https://www.oreilly.com/',
            'title': "O'Reilly Media",
            'snippet': 'Technical books and learning platform'
        })

    return results


def search_duckduckgo(query, max_results=5):
    """Improved DuckDuckGo search with better error handling and parsing"""
    try:
        # Try multiple search approaches
        search_approaches = [
            f"https://duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}",
            f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        for search_url in search_approaches:
            try:
                response = requests.get(search_url, headers=headers, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple CSS selectors for result parsing
                    selectors = [
                        'a.result__a',           # Original selector
                        '.result__title a',      # Alternative 1
                        '.results_links_deep a', # Alternative 2
                        '.web-result a',         # Alternative 3
                        'h3 a',                  # Generic heading links
                        '.result a'              # Generic result links
                    ]
                    
                    for selector in selectors:
                        links = soup.select(selector)
                        if links:
                            results = parse_search_results(links, max_results)
                            if results:
                                return results
            except Exception as e:
                print(f"  ⚠️ Search attempt failed: {e}")
                continue
        
        return []
    
    except Exception as e:
        print(f"  ⚠️ DuckDuckGo search failed: {e}")
        return []


def search_with_fallback_methods(query, max_results=5):
    """Fallback search methods when DuckDuckGo fails"""
    try:
        # Try direct URL construction first
        direct_results = attempt_direct_url_construction(query)
        if direct_results:
            print(f"  ✅ Found direct URL match")
            return direct_results[:max_results]
        
        # Enhanced search logic based on content type
        query_lower = query.lower()
        
        # Platform-specific search URLs (these might work better)
        platform_searches = []
        
        if any(term in query_lower for term in ['course', 'training', 'specialization']):
            # Try constructing course platform URLs
            if 'coursera' in query_lower or 'andrew ng' in query_lower:
                platform_searches.append('https://www.coursera.org')
            elif 'udemy' in query_lower:
                platform_searches.append('https://www.udemy.com')
        
        # For now, return empty as we don't want to scrape other sites directly
        return []
        
    except Exception as e:
        print(f"  ⚠️ Fallback search failed: {e}")
        return []


def score_search_result(result, original_text):
    """Score search result relevance to original text"""
    if not result or not result.get('url') or not result.get('title'):
        return 0.0
    
    url = result['url'].lower()
    title = result['title'].lower()
    original = original_text.lower()
    
    score = 0.0
    
    # Domain authority scoring
    high_authority_domains = ['youtube.com', 'coursera.org', 'udemy.com', 'edx.org', 
                             'deeplearning.ai', 'github.com', 'arxiv.org', 'oreilly.com']
    medium_authority_domains = ['medium.com', 'towardsdatascience.com', 'kaggle.com']
    
    domain = urlparse(result['url']).netloc.replace('www.', '')
    
    if any(auth_domain in domain for auth_domain in high_authority_domains):
        score += 0.3
    elif any(auth_domain in domain for auth_domain in medium_authority_domains):
        score += 0.2
    
    # Title relevance
    original_words = set(re.findall(r'\b\w+\b', original))
    title_words = set(re.findall(r'\b\w+\b', title))
    
    if original_words and title_words:
        overlap = len(original_words.intersection(title_words))
        score += (overlap / len(original_words)) * 0.4
    
    # Specific pattern matching
    if 'karpathy' in original and 'karpathy' in title:
        score += 0.2
    
    if 'zero to hero' in original and 'zero to hero' in title:
        score += 0.2
    
    if 'course' in original and any(term in title for term in ['course', 'tutorial', 'lecture']):
        score += 0.1
    
    # O'Reilly specific scoring
    if "o'reilly" in original and 'oreilly' in domain:
        score += 0.3
    
    return min(score, 1.0)


def search_for_resource(text_reference):
    """Improved search for the best URL match with multiple strategies and lower threshold"""
    # Don't search for Slack channels
    if text_reference.strip().startswith('#'):
        return None

    queries = construct_search_query(text_reference)

    if not queries:  # No search queries generated (e.g., for Slack channels)
        return None

    all_results = []

    # Try direct URL construction first
    direct_results = attempt_direct_url_construction(text_reference)
    for result in direct_results:
        result['query'] = f"direct:{text_reference}"
        result['score'] = 0.9  # High confidence for direct matches
        all_results.append(result)

    # DISABLED: DuckDuckGo search is timing out/blocked
    # Skip web search and only use direct URL construction
    print(f"  ⚠️  Web search disabled (DuckDuckGo not accessible)")
    print(f"  ℹ️  Only using direct URL pattern matching")

    # # Try DuckDuckGo search for each query
    # for query in queries:
    #     print(f"  🔍 Searching: {query}")
    #     search_results = search_duckduckgo(query, max_results=3)
    #
    #     # If DuckDuckGo fails, try fallback methods
    #     if not search_results:
    #         print(f"  🔄 Trying fallback methods...")
    #         search_results = search_with_fallback_methods(query, max_results=3)
    #
    #     for result in search_results:
    #         result['query'] = query
    #         result['score'] = score_search_result(result, text_reference)
    #         all_results.append(result)
    #
    #     time.sleep(1)  # Be respectful to search engine

    # Sort by score and return best result with lower threshold
    if all_results:
        best_result = max(all_results, key=lambda x: x['score'])
        # Lowered threshold from 0.3 to 0.15 for better coverage
        if best_result['score'] > 0.15:
            print(f"  ✅ Best result score: {best_result['score']:.2f}")
            return best_result
        else:
            print(f"  ❌ Best result score too low: {best_result['score']:.2f}")

    return None


def clean_url(url):
    """Clean and normalize URL, removing markdown/text artifacts"""
    if not url:
        return url

    url = str(url).strip()

    # Remove leading/trailing brackets and parentheses that might wrap URLs
    # Handle cases like: (http://example.com) or [http://example.com] or (http://example.com]
    while url and url[0] in '([':
        url = url[1:].strip()

    while url and url[-1] in ')]':
        url = url[:-1].strip()

    # Remove any remaining trailing punctuation that's not part of URL
    # But preserve trailing slashes for now (will handle later)
    while url and url[-1] in '.,;:!?\'"':
        url = url[:-1].strip()

    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    # Remove trailing slash
    if url.endswith('/'):
        url = url[:-1]

    return url


def fetch_page_metadata(url):
    """Fetch page title and description"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title
        title = None
        if soup.title:
            title = soup.title.string.strip() if soup.title.string else None
        
        # Get description
        description = None
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content')
        
        if not description:
            # Try og:description
            og_desc = soup.find('meta', attrs={'property': 'og:description'})
            if og_desc:
                description = og_desc.get('content')
        
        return {
            'title': title,
            'description': description[:200] + '...' if description and len(description) > 200 else description,
            'status': 'working'
        }
        
    except Exception as e:
        return {
            'title': None,
            'description': None,
            'status': 'error'
        }


def categorize_url(url, title=None):
    """
    Categorize URL based on domain and content.

    Categories:
    - Book: Books and textbooks (Amazon, O'Reilly, etc.)
    - Course: General online courses (Coursera, Udemy, edX, Maven)
    - AI_Learning_Platform: Specialized AI/ML learning platforms (DeepLearning.AI, Fast.ai, Anthropic)
    - Video: Video content (YouTube, Vimeo)
    - Article: Blog posts and articles (Medium, etc.)
    - Code_Repository: Code repositories (GitHub, GitLab)
    - Documentation: Technical documentation
    - Research_Paper: Academic papers (arXiv, IEEE)
    - Other: Miscellaneous educational resources that don't fit above categories
    """
    if not url:
        return 'Unknown'

    url_lower = url.lower()
    title_lower = (title or '').lower()

    # Books/Reading materials - most specific first
    if any(domain in url_lower for domain in ['amazon.com', 'goodreads.com', 'springer.com', 'manning.com']):
        return 'Book'

    # O'Reilly can be books OR courses/videos
    if 'oreilly.com' in url_lower:
        if '/library/view/' in url_lower or '/book/' in url_lower:
            return 'Book'
        elif '/videos/' in url_lower:
            return 'Video'
        else:
            return 'Book'  # Default to Book for O'Reilly

    # Specialized AI/ML learning platforms (most specific)
    if any(domain in url_lower for domain in ['deeplearning.ai', 'fast.ai', 'anthropic.com/learn',
                                                'anthropic.skilljar.com', 'karpathy.ai']):
        return 'AI_Learning_Platform'

    # General course platforms
    if any(domain in url_lower for domain in ['coursera.org', 'udemy.com', 'edx.org', 'udacity.com',
                                                'pluralsight.com', 'maven.com', 'agenticai-learning.org']):
        return 'Course'

    # Video platforms
    if any(domain in url_lower for domain in ['youtube.com', 'youtu.be', 'vimeo.com']):
        return 'Video'

    # Code repositories
    if any(domain in url_lower for domain in ['github.com', 'gitlab.com', 'bitbucket.org']):
        return 'Code_Repository'

    # Academic/Research papers
    if any(domain in url_lower for domain in ['arxiv.org', 'papers.nips.cc', 'openreview.net', 'ieee.org']):
        return 'Research_Paper'

    # Blogs/Articles
    if any(domain in url_lower for domain in ['medium.com', 'towardsdatascience.com', 'dev.to',
                                                'hackernoon.com', 'journalclub.io']):
        return 'Article'

    # Documentation sites
    if any(keyword in url_lower for keyword in ['docs.', 'documentation', '/docs/', 'api-doc',
                                                  'developers.google.com']):
        return 'Documentation'

    # Use title for additional context when domain is ambiguous
    if title_lower:
        if any(keyword in title_lower for keyword in ['course', 'specialization', 'tutorial', 'lesson']):
            # Only override if category is currently "Other"
            if 'Other' in [categorize_url(url, None)]:
                return 'Course'
        elif any(keyword in title_lower for keyword in ['book', 'guide', 'textbook']):
            return 'Book'
        elif any(keyword in title_lower for keyword in ['video', 'watch', 'lecture series']):
            return 'Video'
        elif any(keyword in title_lower for keyword in ['paper', 'research', 'study']):
            return 'Research_Paper'

    # Default for unrecognized but valid resources
    return 'Other'


def should_filter_out_url(url, title):
    """
    Determine if a URL should be filtered out (generic homepage, not a specific resource)
    Returns True if URL should be excluded, False if it should be kept
    """
    if not url:
        return False

    url_lower = url.lower()
    title_lower = (title or '').lower()

    # Filter out O'Reilly homepage (unless it's a specific book or course)
    if 'oreilly.com' in url_lower:
        # Keep if URL contains book/course path or specific ISBN/ID
        if any(path in url_lower for path in ['/library/view/', '/videos/', '/book/', '/isbn/']):
            return False  # Keep - it's a specific resource
        # Filter out homepage
        if url_lower.rstrip('/') in ['https://oreilly.com', 'http://oreilly.com',
                                       'https://www.oreilly.com', 'http://www.oreilly.com']:
            return True
        # Filter out if title is generic
        if title_lower and any(generic in title_lower for generic in
                              ['technology and business training', 'online learning platform', 'homepage']):
            return True

    # Filter out generic Amazon homepage (keep specific product pages)
    if 'amazon.com' in url_lower:
        # Keep if it has a product ID (ASIN)
        if '/dp/' in url_lower or '/product/' in url_lower or '/gp/product/' in url_lower:
            return False  # Keep - it's a specific product
        # Filter out generic Amazon pages
        if url_lower.rstrip('/') in ['https://amazon.com', 'http://amazon.com',
                                       'https://www.amazon.com', 'http://www.amazon.com']:
            return True

    # Filter out generic platform homepages
    generic_homepages = [
        'coursera.org/', 'udemy.com/', 'edx.org/', 'youtube.com/',
        'deeplearning.ai/', 'fast.ai/', 'kaggle.com/'
    ]

    for homepage in generic_homepages:
        # Check if URL is exactly the homepage (with or without www)
        url_normalized = url_lower.replace('www.', '').rstrip('/')
        if url_normalized.endswith(homepage.rstrip('/')):
            # It's just the homepage with no specific path
            path_part = url_lower.split(homepage)[-1] if homepage in url_lower else ''
            if not path_part or path_part == '/':
                return True

    return False


def categorize_text_reference(text):
    """Categorize text references that don't have URLs"""
    if not text:
        return 'Unknown'

    text_lower = text.lower()

    # Slack channels
    if text.strip().startswith('#'):
        return 'Slack_Channel'

    # O'Reilly books
    if "o'reilly" in text_lower:
        return 'Book'

    # Other patterns
    if any(keyword in text_lower for keyword in ['course', 'specialization', 'training']):
        return 'Course'
    elif any(keyword in text_lower for keyword in ['book', 'guide']):
        return 'Book'
    elif any(keyword in text_lower for keyword in ['video', 'series', 'tutorial']):
        return 'Video'
    elif any(keyword in text_lower for keyword in ['paper', 'research']):
        return 'Research_Paper'

    return 'Text_Reference'


def generate_summary(title, description):
    """Generate a brief summary from title and description"""
    if not title and not description:
        return None
    
    summary_parts = []
    
    if title:
        # Clean up title
        clean_title = title.replace('\n', ' ').replace('\r', ' ').strip()
        summary_parts.append(clean_title)
    
    if description and description != title:
        # Clean up description and limit length
        clean_desc = description.replace('\n', ' ').replace('\r', ' ').strip()
        if len(clean_desc) > 100:
            clean_desc = clean_desc[:100] + '...'
        summary_parts.append(clean_desc)
    
    return ' - '.join(summary_parts) if summary_parts else None


def generate_text_summary(text):
    """Generate summary for text-only references"""
    if not text:
        return None
    
    text = str(text).strip()
    
    # For Slack channels
    if text.startswith('#'):
        return f"Slack channel: {text}"
    
    # For O'Reilly books, extract book title
    oreilly_pattern = r"o'reilly\s+([^,\n]+)"
    oreilly_match = re.search(oreilly_pattern, text.lower())
    if oreilly_match:
        book_title = oreilly_match.group(1).strip()
        return f"O'Reilly book: {book_title.title()}"
    
    # For other text references, return first 100 characters
    if len(text) > 100:
        return text[:100] + '...'
    
    return text


def split_multi_item_entries(text):
    """Split entries that contain multiple URLs or resources separated by newlines or commas"""
    if pd.isna(text) or text == '':
        return [text]
    
    text = str(text).strip()
    
    # First, split by newlines to handle multi-line entries
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) <= 1:
        # Single line - check for comma-separated URLs
        if ',' in text:
            # Look for pattern of multiple URLs separated by commas
            potential_items = [item.strip() for item in text.split(',')]
            
            # Check if we have multiple URLs
            url_count = 0
            for item in potential_items:
                if extract_links_from_text(item):
                    url_count += 1
            
            # If we have multiple URLs, split them
            if url_count >= 2:
                return potential_items
        
        return [text]
    
    # Multiple lines - each line is potentially a separate item
    separate_items = []
    
    for line in lines:
        # Skip empty lines
        if not line:
            continue
            
        # Check if this line contains URLs or looks like a resource reference
        urls = extract_links_from_text(line)
        resource_refs = identify_resource_references(line)
        
        if urls or resource_refs:
            separate_items.append(line)
        else:
            # If it doesn't look like a resource, it might be part of previous item
            # For now, treat each line as separate
            separate_items.append(line)
    
    # Return the split items or original if no clear separation
    return separate_items if len(separate_items) > 1 else [text]


def generate_title_from_url_and_summary(title, summary, url):
    """Generate readable title when title is just a URL"""
    from urllib.parse import urlparse
    
    # Check if title is essentially just a URL - enhanced pattern detection
    # Match various URL patterns that might appear as titles
    url_patterns = [
        r'^https?://[^\s]+$',                    # Standard URL
        r'^www\.[^\s]+\.[a-z]{2,}[^\s]*$',      # www.domain.com pattern
        r'^[a-z0-9.-]+\.[a-z]{2,}[^\s]*$',      # domain.com pattern
        r'^\s*https?://[^\s]+\s*$'              # URL with whitespace
    ]
    
    title_stripped = title.strip()
    is_url_title = any(re.match(pattern, title_stripped, re.IGNORECASE) for pattern in url_patterns)
    
    if is_url_title:
        print(f"  📝 Title is pure URL, generating from summary...")
        
        # Strategy 1: Extract meaningful title from summary
        if summary and summary != 'No summary available':
            # Remove "Resource: " prefix if present
            clean_summary = re.sub(r'^Resource:\s*', '', summary)
            
            # Take first sentence or first 60 characters
            sentences = clean_summary.split('.')
            if sentences and len(sentences[0].strip()) > 10:
                generated_title = sentences[0].strip()
            else:
                generated_title = clean_summary[:60].strip()
                if len(clean_summary) > 60:
                    generated_title += '...'
            
            # Ensure it's not empty and meaningful
            if len(generated_title) > 5 and not any(re.match(pattern, generated_title, re.IGNORECASE) for pattern in url_patterns):
                return generated_title
        
        # Strategy 2: Extract from URL path
        if url and url != 'N/A':
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
                path = parsed.path.strip('/')
                
                # Try to extract meaningful name from path
                if path:
                    # Remove file extensions and common path patterns
                    path_clean = re.sub(r'\.(html|php|aspx|jsp)$', '', path)
                    path_parts = path_clean.split('/')
                    
                    # Look for meaningful path components
                    for part in reversed(path_parts):
                        if len(part) > 3 and not part.isdigit():
                            # Convert kebab-case and snake_case to title case
                            readable = re.sub(r'[-_]', ' ', part).title()
                            if len(readable) > 5:
                                return f"{readable} - {domain.split('.')[0].title()}"
                
                # Fallback: Use domain name
                domain_name = domain.split('.')[0].title()
                return f"{domain_name} Resource"
            except:
                pass
        
        # Final fallback
        return "Online Resource"
    
    return title


def improve_summary_quality(summary, title, url):
    """Improve summary quality and avoid circular references"""
    if not summary or summary in ['No summary available', 'No description available']:
        # Try to generate from title if title is good
        if title and len(title) > 10 and not re.match(r'^https?://', title):
            return f"Educational resource: {title}"
        
        # Try to generate from URL domain
        if url and url != 'N/A':
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
                domain_name = domain.split('.')[0].title()
                return f"Learning resource from {domain_name}"
            except:
                pass
        
        return "Educational AI/ML resource"
    
    # Avoid circular summaries (when summary is just the title)
    if summary.strip().lower() == title.strip().lower():
        return f"Educational resource: {title}"
    
    # Check if summary starts with "Resource: " and is just repeating the title
    if summary.startswith("Resource: "):
        summary_content = summary[10:].strip()
        if summary_content.lower() == title.strip().lower():
            return f"Educational resource about {title}"
    
    return summary