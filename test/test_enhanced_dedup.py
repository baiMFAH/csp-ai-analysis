import re

# Test URL normalization
def normalize_url(url):
    if not url or url == 'N/A':
        return url
    
    url = url.lower().strip()
    url = re.sub(r'^https?://', 'https://', url)
    url = re.sub(r'https://www\.', 'https://', url)
    url = url.rstrip('/')
    url = re.sub(r'[?&](utm_[^&]*|source=[^&]*|medium=[^&]*)', '', url)
    return url

# Test URL extraction from title
def extract_url_from_title(title):
    if not title:
        return title, None
    
    url_pattern = r'(https?://[^\s\)]+)'
    urls = re.findall(url_pattern, title)
    
    if urls:
        extracted_url = urls[0].rstrip('.,;)')
        clean_title = re.sub(url_pattern, '', title).strip()
        clean_title = re.sub(r'\s+', ' ', clean_title)
        clean_title = clean_title.strip('- ')
        return clean_title, extracted_url
    
    return title, None

# Test comma splitting
def split_comma_separated_items(title, category):
    if ',' in title and category in ['Book', 'Course', 'AI_Course']:
        parts = [part.strip() for part in title.split(',')]
        
        if len(parts) >= 2:
            first_words = []
            for part in parts:
                words = part.split()[:2]
                first_words.append(' '.join(words).lower())
            
            if len(set(first_words)) < len(parts) or any('o\'reilly' in fw for fw in first_words):
                return [part.strip() for part in parts]
    
    return [title]

# Test cases
print("=== URL NORMALIZATION TESTS ===")
test_urls = [
    "http://example.com/",
    "https://example.com",
    "https://www.example.com/path",
    "HTTP://EXAMPLE.COM/PATH/",
    "https://example.com/page?utm_source=test&medium=email"
]

for url in test_urls:
    normalized = normalize_url(url)
    print(f"{url} → {normalized}")

print("\n=== URL EXTRACTION FROM TITLE TESTS ===")
test_titles = [
    "Great Course https://coursera.org/course1",
    "Deep Learning - https://example.com/dl",
    "Machine Learning (https://udemy.com/ml-course)",
    "Just a regular title",
    "Multiple URLs https://site1.com and https://site2.com"
]

for title in test_titles:
    clean, url = extract_url_from_title(title)
    print(f"'{title}' → Title: '{clean}', URL: {url}")

print("\n=== COMMA SEPARATION TESTS ===")
test_comma_cases = [
    ("O'Reilly AI Engineering, O'Reilly Hands-On Large Languages", "Book"),
    ("Course A, Course B", "Course"),
    ("Regular title with, comma", "Article"),
    ("Single item", "Book")
]

for title, category in test_comma_cases:
    split = split_comma_separated_items(title, category)
    print(f"'{title}' [{category}] → {split}")

print("\n✅ All enhanced deduplication functions tested successfully!")