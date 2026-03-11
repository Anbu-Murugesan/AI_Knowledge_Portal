"""
Background rebuild manager for vector stores and events cache.
Handles automatic rebuilding every 7 days.
"""
import os
import json
import threading
import traceback
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path

from core.models import WorkflowState
from core.rss import rebuild_rss_faiss_always
from core.workflows import BLOG_SOURCES
from events.event_collector import collect_all_events
from events.storage import save_cache
from core.logging_config import get_rebuild_logger

logger = get_rebuild_logger()

# Rebuild interval in days
REBUILD_INTERVAL_DAYS = 7

# Status file path
STATUS_FILE = "rebuild_status.json"

# Vector store directories
VECTOR_STORES = {
    "rss": "faiss_index_local",
    "kdnuggets": "kdnuggets_faiss",
    "analyticsvidhya": "faiss_blogs/analyticsvidhya",
    "ml_mastery": "faiss_blogs/ml_mastery",
}

# Events cache file
EVENTS_CACHE_FILE = "events_cache.json"

# Global lock to prevent concurrent rebuilds
_rebuild_lock = threading.Lock()
_rebuild_in_progress = False


def load_rebuild_status() -> Dict:
    """Load rebuild status from file."""
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r') as f:
                status = json.load(f)
                logger.debug(f"Loaded rebuild status from {STATUS_FILE}")
                return status
        except Exception as e:
            logger.error(f"Error loading rebuild status: {e}", exc_info=True)
    return {}


def save_rebuild_status(status: Dict):
    """Save rebuild status to file."""
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f, indent=2)
        logger.debug(f"Saved rebuild status to {STATUS_FILE}")
    except Exception as e:
        logger.error(f"Error saving rebuild status: {e}", exc_info=True)


def get_last_rebuild_time(store_name: str) -> Optional[datetime]:
    """Get last rebuild time for a store."""
    status = load_rebuild_status()
    store_status = status.get(store_name, {})
    last_rebuild_str = store_status.get("last_rebuild")
    
    if last_rebuild_str:
        try:
            return datetime.fromisoformat(last_rebuild_str)
        except Exception:
            return None
    return None


def needs_rebuild(store_name: str) -> bool:
    """Check if a store needs rebuilding (>7 days old)."""
    last_rebuild = get_last_rebuild_time(store_name)
    
    if last_rebuild is None:
        logger.info(f"Store '{store_name}' has never been rebuilt - rebuild needed")
        return True  # Never rebuilt
    
    days_since_rebuild = (datetime.now() - last_rebuild).days
    needs = days_since_rebuild >= REBUILD_INTERVAL_DAYS
    logger.debug(f"Store '{store_name}' - last rebuild: {last_rebuild}, days since: {days_since_rebuild}, needs rebuild: {needs}")
    return needs

def update_rebuild_status(store_name: str, status_str: str = "completed", error: Optional[str] = None):
    """Update rebuild status for a store."""
    status = load_rebuild_status()
    
    if store_name not in status:
        status[store_name] = {}
    
    status[store_name]["last_rebuild"] = datetime.now().isoformat()
    status[store_name]["status"] = status_str
    
    if error:
        status[store_name]["error"] = error
    elif "error" in status[store_name]:
        del status[store_name]["error"]
    
    save_rebuild_status(status)

def is_tavily_key_exhausted() -> bool:
    """Check if Tavily API key is exhausted based on rebuild status."""
    status = load_rebuild_status()
    events_status = status.get("events_cache", {})
    return events_status.get("status") == "tavily_key_exhausted"


def rebuild_rss_index():
    """Rebuild RSS FAISS index."""
    logger.info(f"Starting RSS index rebuild")
    try:
        state = WorkflowState(
            request_id=f"rebuild-rss-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            query="",
            selected_tool="rss"
        )
        logger.debug(f"Created WorkflowState with request_id: {state.request_id}")
        rebuild_rss_faiss_always(state)
        
        if state.status == "error":
            error_msg = state.error or "Unknown error"
            update_rebuild_status("rss", "failed", error_msg)
            logger.error(f"RSS rebuild failed: {error_msg}")
            return False
        else:
            update_rebuild_status("rss", "completed")
            logger.info(f"RSS index rebuilt successfully")
            return True
    except Exception as e:
        error_msg = str(e)
        update_rebuild_status("rss", "failed", error_msg)
        logger.error(f"RSS rebuild error: {e}", exc_info=True)
        return False


def rebuild_blog_index(blog_name: str):
    """Rebuild a specific blog FAISS index."""
    logger.info(f"Starting {blog_name} index rebuild")
    
    if blog_name not in BLOG_SOURCES:
        logger.error(f"Unknown blog: {blog_name}")
        return False
    
    blog_cfg = BLOG_SOURCES[blog_name]
    build_fn = blog_cfg["build_fn"]
    
    try:
        state = WorkflowState(
            request_id=f"rebuild-{blog_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            query="",
            selected_tool="blog",
            selected_blog=blog_name
        )
        logger.debug(f"Created WorkflowState for {blog_name} with request_id: {state.request_id}")
        build_fn(state)
        
        if state.status == "error":
            error_msg = state.error or "Unknown error"
            store_key = blog_name.lower().replace(" ", "_")
            update_rebuild_status(store_key, "failed", error_msg)
            logger.error(f"{blog_name} rebuild failed: {error_msg}")
            return False
        else:
            store_key = blog_name.lower().replace(" ", "_")
            update_rebuild_status(store_key, "completed")
            logger.info(f"{blog_name} index rebuilt successfully")
            return True
    except Exception as e:
        error_msg = str(e)
        store_key = blog_name.lower().replace(" ", "_")
        update_rebuild_status(store_key, "failed", error_msg)
        logger.error(f"{blog_name} rebuild error: {e}", exc_info=True)
        return False


def rebuild_events_cache():
    """Rebuild events cache by running event collector."""
    logger.info(f"Starting events cache rebuild")
    try:
        logger.debug("Calling collect_all_events()")
        events = collect_all_events()
        logger.debug(f"Collected {len(events)} events")
        save_cache(events)
        update_rebuild_status("events_cache", "completed")
        logger.info(f"Events cache rebuilt successfully - {len(events)} events cached")
        return True
    except Exception as e:
        error_msg = str(e)
        # Check if error is related to Tavily API key exhaustion
        tavily_key_exhausted = any(keyword in error_msg for keyword in [
            "quota", "rate limit", "api key", "exhausted", 
            "limit reached", "insufficient", "tavily"
        ])
        
        if tavily_key_exhausted:
            # Mark as Tavily key exhausted (special status)
            update_rebuild_status("events_cache", "tavily_key_exhausted", str(e))
            logger.warning(f"Events cache rebuild failed: Tavily API key exhausted")
        else:
            # Regular error
            update_rebuild_status("events_cache", "failed", str(e))
            logger.error(f"Events cache rebuild error: {e}", exc_info=True)
        
        return False


def rebuild_all_background():
    """Rebuild all stores that need rebuilding (runs in background thread)."""
    global _rebuild_in_progress
    
    with _rebuild_lock:
        if _rebuild_in_progress:
            logger.warning("Rebuild already in progress, skipping...")
            return
        _rebuild_in_progress = True
    
    try:
        logger.info(f"Background rebuild started at {datetime.now()}")
        
        results = {}
        
        # Check and rebuild RSS index
        if needs_rebuild("rss"):
            results["rss"] = rebuild_rss_index()
        else:
            logger.debug("RSS index is up to date")
        
        # Check and rebuild blog indices
        blog_mapping = {
            "KDnuggets": "kdnuggets",
            "Analytics Vidhya": "analyticsvidhya",
            "Machine Learning Mastery": "ml_mastery"
        }
        
        for blog_name, store_key in blog_mapping.items():
            if needs_rebuild(store_key):
                results[store_key] = rebuild_blog_index(blog_name)
            else:
                logger.debug(f"{blog_name} index is up to date")
        
        # Check and rebuild events cache
        if needs_rebuild("events_cache"):
            results["events_cache"] = rebuild_events_cache()
        else:
            logger.debug("Events cache is up to date")
        
        # Summary
        logger.info(f"Rebuild summary:")
        for store, success in results.items():
            status = "Success" if success else "Failed"
            logger.info(f"  {store}: {status}")
        
    finally:
        _rebuild_in_progress = False
        logger.info("Background rebuild completed")


def trigger_rebuild_if_needed():
    """Check if rebuild is needed and trigger in background if so."""
    logger.debug("Checking if rebuild is needed")
    # Check if any store needs rebuilding
    stores_to_rebuild = []
    
    if needs_rebuild("rss"):
        stores_to_rebuild.append("rss")
    
    blog_mapping = {
        "KDnuggets": "kdnuggets",
        "Analytics Vidhya": "analyticsvidhya",
        "Machine Learning Mastery": "ml_mastery"
    }
    
    for blog_name, store_key in blog_mapping.items():
        if needs_rebuild(store_key):
            stores_to_rebuild.append(store_key)
    
    if needs_rebuild("events_cache"):
        stores_to_rebuild.append("events_cache")
    
    if stores_to_rebuild:
        logger.info(f"Stores needing rebuild: {', '.join(stores_to_rebuild)}")
        logger.info("Starting background rebuild thread...")
        
        # Start rebuild in background thread
        rebuild_thread = threading.Thread(
            target=rebuild_all_background,
            daemon=True,
            name="RebuildThread"
        )
        rebuild_thread.start()
        logger.info("Background rebuild thread started")
    else:
        logger.debug("All stores are up to date")