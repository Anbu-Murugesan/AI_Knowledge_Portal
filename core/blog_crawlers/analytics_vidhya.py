"""
Analytics Vidhya blog crawler
"""
import time
import re
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from ..models import WorkflowState
from ..text_processing import load_articles_to_docs
from ..vector_store import build_faiss_vectorstore_for_blog

# Configuration
AV_START_URL = "https://www.analyticsvidhya.com/blog/category/artificial-intelligence/"
AV_FAISS_DIR = "./faiss_blogs/analyticsvidhya"
AV_MAX_PAGES = 25
AV_REQUEST_DELAY = 1.0


def fetch_html(url):
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


def extract_av_article_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()

        if href.startswith("/"):
            href = urljoin(base_url, href)

        if "analyticsvidhya.com/blog/" not in href:
            continue

        # Filter out category, tag, author pages
        if "/category/" in href or "/tag/" in href or "/author/" in href:
            continue

        # Keep only real articles
        if re.search(r"/\d{4}/", href):
            links.add(href.split("?")[0].rstrip("/"))

    return sorted(links)


def crawl_analytics_vidhya(start_url, max_pages=AV_MAX_PAGES):
    to_visit = [start_url]
    visited = set()
    article_urls = set()

    print(f"[AV crawl] START -> {start_url}")

    for page_no in range(max_pages):
        if not to_visit:
            break

        url = to_visit.pop(0)
        if url in visited:
            continue

        print(f"[AV crawl] ({page_no+1}/{max_pages}) Fetching: {url}")

        try:
            html = fetch_html(url)
        except Exception as e:
            print(f"[AV crawl][WARN] failed: {e}")
            visited.add(url)
            continue

        visited.add(url)

        found = extract_av_article_links(html, url)
        article_urls.update(found)

        print(f"[AV crawl] Found {len(found)} articles (total={len(article_urls)})")

        # Pagination: older posts
        soup = BeautifulSoup(html, "html.parser")
        next_link = soup.find("a", class_="next")
        if next_link and next_link.get("href"):
            next_url = urljoin(url, next_link["href"])
            if next_url not in visited:
                to_visit.append(next_url)

        time.sleep(AV_REQUEST_DELAY)

    print(f"[AV crawl] DONE. Total articles: {len(article_urls)}")
    return sorted(article_urls)


def build_analytics_vidhya_index(state: WorkflowState) -> WorkflowState:
    state.status = "indexing_blog"
    try:
        print("🚀 Building Analytics Vidhya blog index")

        urls = crawl_analytics_vidhya(
            start_url=AV_START_URL,
            max_pages=AV_MAX_PAGES
        )

        if not urls:
            raise RuntimeError("No Analytics Vidhya URLs found")

        docs, failed = load_articles_to_docs(urls)

        if not docs:
            raise RuntimeError("No Analytics Vidhya documents loaded")

        build_faiss_vectorstore_for_blog(
            docs,
            persist_directory=AV_FAISS_DIR
        )

        state.status = "indexed_blog"
        print("✅ Analytics Vidhya FAISS built successfully")
        return state

    except Exception as e:
        state.status = "error"
        state.error = str(e)
        return state
