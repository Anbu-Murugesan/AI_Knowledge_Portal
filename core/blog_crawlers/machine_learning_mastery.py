"""
Machine Learning Mastery blog crawler
"""
import time
import re
import os
from typing import List
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ..models import WorkflowState
from ..text_processing import load_articles_to_docs
from ..vector_store import build_faiss_vectorstore_for_blog

# Configuration
MLM_START_URLS = [
    "https://machinelearningmastery.com/start-here/"
]

MLM_FAISS_DIR = "./faiss_blogs/ml_mastery"
MLM_MAX_PAGES = 150


def fetch_html(url):
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


def extract_mlm_article_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()

        if href.startswith("/"):
            href = urljoin(base_url, href)

        if "machinelearningmastery.com" not in href:
            continue

        # Filter category pages
        if any(x in href for x in [
            "/category/", "/tag/", "/author/", "/about", "/contact"
        ]):
            continue

        # Keep real articles (long slugs)
        if href.count("/") >= 4:
            links.add(href.split("?")[0].rstrip("/"))

    return sorted(links)


def crawl_machine_learning_mastery(start_urls, max_pages=300):
    visited = set()
    collected_urls = []

    for start_url in start_urls:
        print(f"[MLM] Crawling hub: {start_url}")

        resp = requests.get(start_url, timeout=20)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # ✅ Extract only MachineLearningMastery article links
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(start_url, href)

            parsed = urlparse(full_url)

            if (
                "machinelearningmastery.com" in parsed.netloc
                and full_url.startswith("https://machinelearningmastery.com/")
                and full_url not in visited
                and not any(x in full_url for x in [
                    "/category/",
                    "/tag/",
                    "/author/",
                    "/page/",
                    "#",
                ])
            ):
                links.append(full_url)

        print(f"[MLM] Found {len(links)} candidate article links")

        for url in links:
            if len(collected_urls) >= max_pages:
                break
            if url not in visited:
                visited.add(url)
                collected_urls.append(url)

    print(f"[MLM] Total articles selected: {len(collected_urls)}")
    return collected_urls


def build_machine_learning_mastery_index(state: WorkflowState) -> WorkflowState:
    state.status = "indexing_blog"
    try:
        print("🚀 Building Machine Learning Mastery index")

        urls = crawl_machine_learning_mastery(
            start_urls=MLM_START_URLS,
            max_pages=MLM_MAX_PAGES
        )

        if not urls:
            raise RuntimeError("No Machine Learning Mastery URLs found")

        docs, failed = load_articles_to_docs(urls)

        if not docs:
            raise RuntimeError("No Machine Learning Mastery docs loaded")

        # ✅ IMPORTANT: use blog_name instead of chunk params
        build_faiss_vectorstore_for_blog(
            docs=docs,
            persist_directory=MLM_FAISS_DIR,

        )

        # ✅ HARD VERIFICATION (this fixes your issue)
        index_path = os.path.join(MLM_FAISS_DIR, "index.faiss")
        if not os.path.exists(index_path):
            raise RuntimeError("FAISS index.faiss not created")

        state.status = "indexed_blog"
        print("✅ Machine Learning Mastery FAISS built successfully")
        return state

    except Exception as e:
        state.status = "error"
        state.error = str(e)
        print("❌ MLM indexing failed:", e)
        return state
