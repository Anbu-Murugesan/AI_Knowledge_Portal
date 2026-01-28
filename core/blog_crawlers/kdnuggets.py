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
BLOG_START_URL = "https://www.kdnuggets.com/tag/artificial-intelligence"
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
    soup = BeautifulSoup(html, "html.parser")
    for text in ["Next", "Older", "Older Posts", "Next »", "->", "older posts"]:
        el = soup.find("a", string=lambda s: s and text.lower() in s.lower())
        if el and el.get("href"):
            return urljoin(base_url, el["href"])
    el = soup.find("link", rel="next")
    if el and el.get("href"):
        return urljoin(base_url, el["href"])
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

        urls = crawl_tag(
            start_url=BLOG_START_URL,
            max_pages=BLOG_MAX_PAGES
        )

        if not urls:
            raise RuntimeError("No KDnuggets blog URLs found")

        docs, failed = load_articles_to_docs(
            urls,
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
