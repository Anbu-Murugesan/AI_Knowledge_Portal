"""
KDnuggets blog crawler
"""
import time
import re
from typing import List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..models import WorkflowState
from ..text_processing import load_articles_to_docs
from ..vector_store import build_faiss_vectorstore_for_blog, load_faiss_local, BLOG_FAISS_DIR, EMBEDDING_MODEL_NAME

# Local constants
BLOG_REQUEST_DELAY = 1.0
MAX_PAGES = 25

# Configuration
BLOG_START_URLS = [
    "https://www.kdnuggets.com/tag/artificial-intelligence",
    "https://www.kdnuggets.com/tag/language-models"
]
BLOG_FAISS_DIR = "./kdnuggets_faiss"
BLOG_REQUEST_DELAY = 1.0
BLOG_MAX_PAGES = 25


def fetch_html(url):
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


def extract_article_links_from_tag_page(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a", href=True)
    links = set()
    for a in anchors:
        href = a["href"].strip()
        href = urljoin(base_url, href)
        parsed = urlparse(href)
        if "kdnuggets.com" not in parsed.netloc:
            continue
        if re.search(r"/\d{4}/\d{2}/|/20\d{2}/|-[a-z0-9\-]+$", href):
            links.add(href.split("?")[0].rstrip("/"))
        else:
            if "/blog" in href or (len(parsed.path.split("/")) > 2 and "-" in parsed.path):
                links.add(href.split("?")[0].rstrip("/"))
    return sorted(links)


def find_pagination_next(html, base_url):
    """
    Find the next pagination page URL.
    Uses multiple strategies to ensure we get the correct pagination link.
    """
    from urllib.parse import urlparse
    import re
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Strategy 1: Extract page number from current URL and increment
    match = re.search(r'/page/(\d+)', base_url)
    if match:
        current_page = int(match.group(1))
        next_page = current_page + 1
        # Construct next page URL by replacing page number
        next_url = re.sub(r'/page/\d+', f'/page/{next_page}', base_url)
        # Verify it's still a kdnuggets.com URL
        parsed = urlparse(next_url)
        if "kdnuggets.com" in parsed.netloc:
            return next_url
    else:
        # First page, construct page 2 URL
        if '/tag/' in base_url:
            next_url = base_url.rstrip('/') + '/page/2'
            parsed = urlparse(next_url)
            if "kdnuggets.com" in parsed.netloc:
                return next_url
    
    # Strategy 2: Look for pagination section and find "Next" link
    pagination = soup.find("nav", class_=lambda x: x and "pagination" in str(x).lower())
    if not pagination:
        pagination = soup.find("div", class_=lambda x: x and "pagination" in str(x).lower())
    
    search_area = pagination if pagination else soup
    
    for text in ["Next", "Older", "Older Posts", "Next »", "->", "older posts"]:
        el = search_area.find("a", string=lambda s: s and text.lower() in s.lower())
        if el and el.get("href"):
            next_url = urljoin(base_url, el["href"])
            parsed = urlparse(next_url)
            
            # Verify it's a valid pagination link
            if "kdnuggets.com" in parsed.netloc:
                # Must be a pagination URL (contains /page/ or /tag/ with page)
                if "/page/" in parsed.path or ("/tag/" in parsed.path and "/page/" in parsed.path):
                    return next_url
    
    # Strategy 3: Look for <link rel="next">
    el = soup.find("link", rel="next")
    if el and el.get("href"):
        next_url = urljoin(base_url, el["href"])
        parsed = urlparse(next_url)
        if "kdnuggets.com" in parsed.netloc and "/page/" in parsed.path:
            return next_url
    
    return None


def crawl_tag(start_url, max_pages=MAX_PAGES):
    to_visit = [start_url]
    visited = set()
    article_urls = set()

    print(f"[crawl] START url={start_url}, max_pages={max_pages}")

    for page_no in range(max_pages):
        if not to_visit:
            break

        url = to_visit.pop(0)
        if url in visited:
            continue

        print(f"[crawl] ({page_no+1}/{max_pages}) Fetching: {url}")

        try:
            html = fetch_html(url)
        except Exception as e:
            print(f"[crawl][WARN] failed to fetch {url}: {e}")
            visited.add(url)
            continue

        visited.add(url)

        found = extract_article_links_from_tag_page(html, url)
        article_urls.update(found)

        print(f"[crawl] Found {len(found)} links (total={len(article_urls)})")

        next_page = find_pagination_next(html, url)
        if next_page and next_page not in visited:
            to_visit.append(next_page)

        time.sleep(BLOG_REQUEST_DELAY)

    print(f"[crawl] DONE. Total article URLs: {len(article_urls)}")
    return sorted(article_urls)


def build_blog_index_node(state: WorkflowState) -> WorkflowState:
    state.status = "indexing_blog"
    try:
        print("🚀 Building KDnuggets blog index using HTML crawl")
        
        all_urls = set()  # Use set to avoid duplicates across tags
        
        # Crawl each tag URL
        for start_url in BLOG_START_URLS:
            print(f"\n📌 Crawling tag: {start_url}")
            urls = crawl_tag(
                start_url=start_url,
                max_pages=BLOG_MAX_PAGES
            )
            all_urls.update(urls)
            print(f"✅ Found {len(urls)} articles from {start_url}")
        
        if not all_urls:
            raise RuntimeError("No KDnuggets blog URLs found")
        
        print(f"\n📊 Total unique articles collected: {len(all_urls)}")
        
        docs, failed = load_articles_to_docs(
            list(all_urls),  # Convert set back to list
            use_unstructured=True
        )
        
        if not docs:
            raise RuntimeError("No blog documents loaded")
        
        build_faiss_vectorstore_for_blog(
            docs,
            persist_directory=BLOG_FAISS_DIR
        )
        
        state.status = "indexed_blog"
        print("✅ KDnuggets blog FAISS built successfully")
        return state
        
    except Exception as e:
        state.status = "error"
        state.error = str(e)
        return state
