import os
import csv
import re
import feedparser
import calendar
from html import unescape
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Tuple

from ..models import WorkflowState

# RSS Configuration
CSV_PATH = "ai_rss_results.csv"
RSS_FAISS_DIR = "faiss_index_local"
DAYS_WINDOW = 7
MIN_PER_FEED = 5

AI_FEEDS = [
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://venturebeat.com/category/ai/feed/",
    "https://www.analyticsvidhya.com/blog/category/artificial-intelligence/feed/",
    "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-IN&gl=IN&ceid=IN:en",
    "https://techcrunch.com/feed/",
    "https://yourstory.com/feed",
    "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
    "https://blog.langchain.dev/rss/",
    "https://www.llamaindex.ai/blog/rss.xml",
    "https://openai.com/blog/rss/",
    "https://huggingface.co/blog/feed.xml",
    "https://mistral.ai/news/feed.xml",
    "https://www.anthropic.com/news/feed.xml",
    "https://vercel.com/changelog/rss",
    "https://weaviate.io/blog/rss.xml",
    "https://www.pinecone.io/rss.xml",
    "https://milvus.io/blog/index.xml",
    "https://news.ycombinator.com/rss",
]


def entry_published_dt(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    try:
        ts = int(calendar.timegm(parsed))
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except Exception:
        return None


def to_iso(dt: datetime):
    if not dt:
        return ""
    return dt.astimezone(timezone.utc).isoformat()


def clean_html_summary(raw_html: str) -> str:
    if not raw_html:
        return ""
    s = unescape(raw_html)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def collect_rss_and_write_csv(output_csv: str = CSV_PATH,
                              days_window: int = DAYS_WINDOW,
                              min_per_feed: int = MIN_PER_FEED) -> List[Dict[str, Any]]:
    feeds = list(AI_FEEDS)
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days_window)

    all_articles = []
    seen_links = set()

    for feed_url in feeds:
        parsed_feed = feedparser.parse(feed_url)
        feed_title = parsed_feed.feed.get("title", feed_url)

        items = []
        for idx, entry in enumerate(parsed_feed.entries):
            link = (entry.get("link") or entry.get("id") or "").strip()
            if not link:
                continue
            pub_dt = entry_published_dt(entry)
            pub_ts = int(pub_dt.timestamp()) if pub_dt else 0
            items.append({
                "entry": entry,
                "link": link,
                "published_dt": pub_dt,
                "published_ts": pub_ts,
                "index": idx
            })

        recent = [it for it in items if it["published_dt"] and it["published_dt"] >= cutoff]
        recent.sort(key=lambda x: x["published_ts"], reverse=True)

        if len(recent) < min_per_feed:
            recent_links = {it["link"] for it in recent}
            candidates = [it for it in items if it["link"] not in recent_links]
            candidates.sort(key=lambda x: (x["published_ts"], -x["index"]), reverse=True)
            needed = min_per_feed - len(recent)
            for c in candidates:
                if needed <= 0:
                    break
                recent.append(c)
                needed -= 1

        selected = recent[:max(min_per_feed, len(recent))]

        for sel in selected:
            link = sel["link"]
            if link in seen_links:
                continue
            entry = sel["entry"]
            pub_dt = sel["published_dt"]
            pub_ts = sel["published_ts"] if sel["published_dt"] else 0

            published_str = entry.get("published", "") or entry.get("updated", "") or ""

            raw_summary = entry.get("summary", "") or entry.get("description", "") or ""
            summary = clean_html_summary(raw_summary)

            title = (entry.get("title") or "No title").strip()

            all_articles.append({
                "feed": feed_title,
                "title": title,
                "link": link,
                "published_iso": to_iso(pub_dt),
                "published_ts": pub_ts,
                "published_raw": published_str,
                "summary": summary
            })
            seen_links.add(link)

    all_articles.sort(key=lambda x: x["published_ts"], reverse=True)

    fieldnames = ["feed", "title", "link", "published_iso", "published_ts", "published_raw", "summary"]
    with open(output_csv, "w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_articles:
            writer.writerow(row)

    return all_articles


def read_csv_metadata(csv_path: str) -> Tuple[List[str], Dict[str, Dict]]:
    links = []
    meta_map = {}
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{csv_path} not found.")
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            link = (row.get("link") or "").strip()
            title = (row.get("title") or "").strip()
            rss_summary = (row.get("summary") or "").strip()
            if not link:
                continue
            links.append(link)
            meta_map[link] = {"title": title, "rss_summary": rss_summary}
    return links, meta_map


# RSS Workflow functions - these depend on other modules, will be imported when needed
def rebuild_rss_faiss_always(state: WorkflowState) -> WorkflowState:
    """
    ALWAYS rebuild RSS FAISS from latest RSS feeds.
    This ensures no stale news.
    """
    # Import here to avoid circular imports
    from ..text_processing import load_and_clean_pages
    from ..vector_store import build_faiss_from_docs_and_save, rss_faiss_store, EMBEDDING_MODEL_NAME, RSS_FAISS_DIR

    state.status = "rebuilding_rss"

    try:
        print("[RSS] Collecting latest RSS feeds -> CSV")
        collect_rss_and_write_csv(
            output_csv=CSV_PATH,
            days_window=DAYS_WINDOW,
            min_per_feed=MIN_PER_FEED
        )

        print("[RSS] Loading pages + cleaning")
        links, meta_map = read_csv_metadata(CSV_PATH)

        docs, failed = load_and_clean_pages(links, meta_map)
        if not docs:
            raise RuntimeError("No RSS documents loaded")

        print("[RSS] Rebuilding FAISS index (overwrite)")
        global rss_faiss_store
        rss_faiss_store = build_faiss_from_docs_and_save(
            docs,
            RSS_FAISS_DIR,
            EMBEDDING_MODEL_NAME
        )

        state.status = "rss_rebuilt"
        return state

    except Exception as e:
        state.status = "error"
        state.error = f"RSS rebuild failed: {repr(e)}\n{traceback.format_exc()}"
        return state


def build_rss_index_node(state: WorkflowState) -> WorkflowState:
    # Import here to avoid circular imports
    from ..text_processing import load_and_clean_pages, CSV_META_MAP
    from ..vector_store import build_faiss_from_docs_and_save, rss_faiss_store, EMBEDDING_MODEL_NAME, RSS_FAISS_DIR

    state.status = "indexing_rss"
    try:
        links, meta_map = read_csv_metadata(CSV_PATH)
        global CSV_META_MAP
        CSV_META_MAP = {}
        CSV_META_MAP.update(meta_map)
        docs, failed = load_and_clean_pages(links, meta_map)
        if not docs:
            raise RuntimeError("No docs loaded for indexing.")
        global rss_faiss_store
        rss_faiss_store = build_faiss_from_docs_and_save(docs, RSS_FAISS_DIR, EMBEDDING_MODEL_NAME)
        state.status = "indexed_rss"
    except Exception as e:
        state.status = "error"
        state.error = f"build_rss_index_node failed: {repr(e)}\n{traceback.format_exc()}"
    return state
