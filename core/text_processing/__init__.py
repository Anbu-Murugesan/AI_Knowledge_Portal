import re
import os
import time
from html import unescape
from datetime import datetime
from typing import List, Dict, Any, Tuple

from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from tqdm import tqdm

# Global metadata map for CSV data
CSV_META_MAP: Dict[str, Dict[str, str]] = {}


def remove_diagram_lines(text: str, min_words_keep: int = 4, punct_ratio_thresh: float = 0.4) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    cleaned_lines = []
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        low = s.lower()
        if re.search(r'\bfig(?:ure)?\.?\s*\d+\b', low):
            continue
        if any(kw in low for kw in [
            "figure", "fig.", "diagram", "flowchart", "flow chart", "chart:", "table:", "image:",
            "illustration", "infographic", "caption:", "click to view", "download pdf", "view image",
            "see figure", "see diagram", "open image", "related image", "share this article",
            "embed", "powered by", "svg", "png", "jpg", "gif"
        ]):
            if len(s.split()) < 20:
                continue
        if re.fullmatch(r'[\W_]{3,}', s):
            continue
        words = s.split()
        if len(words) <= min_words_keep:
            non_alnum = re.sub(r'\w', '', s)
            punct_ratio = len(non_alnum) / max(1, len(s))
            if punct_ratio > punct_ratio_thresh:
                continue
            if re.search(r'^[\w\-\s\|,]{0,60}$', s) and ('|' in s or ',' in s or s.isupper()):
                continue
            cap_frac = sum(1 for w in words if w and w[0].isupper()) / max(1, len(words))
            if cap_frac > 0.6 and len(words) <= 6:
                continue
        if re.search(r'\b(share|twitter|facebook,linkedin,email,subscribe,subscribe to)\b', low) and len(words) <= 8:
            continue
        cleaned_lines.append(s)
    return "\n".join(cleaned_lines)


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    noisy_block_patterns = [
        r'(?is)table of contents.*',
        r'(?is)you might also like[:]?.*',
        r'(?is)related posts[:]?.*',
        r'(?is)more from.*',
    ]
    for pat in noisy_block_patterns:
        text = re.sub(pat, '', text)
    text = remove_diagram_lines(text)
    s = re.sub(r'\s+', ' ', text).strip()
    s = re.sub(r'^[^\w]+', '', s)
    s = re.sub(r'[^\w]+$', '', s)
    return s


def load_and_clean_pages(links: List[str], meta_map: Dict[str, Dict]) -> Tuple[List[Document], List[Tuple[str,str]]]:
    docs = []
    failed = []
    for url in links:
        try:
            loader = WebBaseLoader(url)
            loaded = loader.load()
            if not loaded:
                failed.append((url, "empty"))
                continue
            doc = loaded[0]
            clean_content = clean_text(doc.page_content) if hasattr(doc, "page_content") else clean_text(str(doc))
            doc.page_content = clean_content
            csv_meta = meta_map.get(url, {})
            title = csv_meta.get("title") or doc.metadata.get("title") or ""
            rss_summary = csv_meta.get("rss_summary") or ""
            if getattr(doc.metadata, "source", "") == "Towards Data Science":
                final_summary = clean_text(clean_content[:600])
            else:
                if rss_summary and len(rss_summary.strip()) > 20:
                    final_summary = clean_text(rss_summary)
                else:
                    final_summary = clean_content[:600].strip()

            doc.metadata["title"] = title.strip()
            doc.metadata["link"] = url
            doc.metadata["summary"] = final_summary.strip()
            docs.append(doc)
        except Exception as e:
            failed.append((url, str(e)))
    return docs, failed


def extract_title_from_doc(doc) -> str:
    # 1️⃣ Metadata title
    meta_title = (doc.metadata or {}).get("title")
    if meta_title and len(meta_title.strip()) > 5:
        return meta_title.strip()

    text = (doc.page_content or "").strip()
    if not text:
        return "Untitled Article"

    # 2️⃣ First line heuristic (often h1)
    first_line = text.split("\n")[0].strip()
    if 5 < len(first_line) < 120:
        return first_line

    # 3️⃣ First sentence fallback
    sentence = text.split(".")[0].strip()
    if 5 < len(sentence) < 120:
        return sentence

    return "Untitled Article"


def clean_blog_title(title: str) -> str:
    if not title:
        return ""

    t = title.strip()

    # Remove newlines
    t = t.replace("\n", " ")

    # Remove numbering like "1.", "2)", "1. 8"
    t = re.sub(r"^\s*\d+[\.\)\-]?\s*", "", t)

    # Cut off after separators
    for sep in [" – ", " - ", "|", " — "]:
        if sep in t:
            t = t.split(sep)[0]

    # Limit length (blog titles get noisy)
    t = t[:120]

    return " ".join(t.split())


def load_articles_to_docs(urls, use_unstructured=True):
    docs = []
    failed = []
    # if use_unstructured:
    #     try:
    #         loader = UnstructuredURLLoader(urls=urls)
    #         docs = loader.load()
    #         return docs, failed
    #     except Exception as e:
    #         print(f"[info] Unstructured loader failed, falling back to WebBaseLoader: {e}")
    for url in tqdm(urls, desc="Loading URLs"):
        try:
            loader = WebBaseLoader(url)
            d = loader.load()
            docs.extend(d)
        except Exception as e:
            failed.append((url, str(e)))
        time.sleep(1.0)  # REQUEST_DELAY
    return docs, failed