"""
Workflow orchestration
"""
import traceback
from typing import List, Dict, Any, Optional

from ..models import WorkflowState, NodeSpec, StateGraph
from ..rss import rebuild_rss_faiss_always
from ..blog_crawlers.kdnuggets import build_blog_index_node as build_kdnuggets_index
from ..blog_crawlers.analytics_vidhya import build_analytics_vidhya_index
from ..blog_crawlers.machine_learning_mastery import build_machine_learning_mastery_index
from ..vector_store import make_faiss_retriever_tool_from_store, rss_faiss_store, blog_faiss_store, load_faiss_local
from ..llm import make_react_agent_node_with_tool

# Blog sources mapping
BLOG_SOURCES = {
    "KDnuggets": {
        "faiss_dir": "./kdnuggets_faiss",
        "build_fn": build_kdnuggets_index,
    },
    "Analytics Vidhya": {
        "faiss_dir": "./faiss_blogs/analyticsvidhya",
        "build_fn": build_analytics_vidhya_index,
    },
    "Machine Learning Mastery": {
        "faiss_dir": "./faiss_blogs/ml_mastery",
        "build_fn": build_machine_learning_mastery_index,
    },

}


def run_full_workflow_example(
    query: str,
    selected_tool: str = "rss",
    selected_blog: Optional[str] = None,
    build_if_missing: bool = False,
):
    """
    FINAL CLEAN WORKFLOW

    - RSS -> searches ONLY rss FAISS
    - BLOG -> searches ONLY blog FAISS (KDnuggets HTML crawl)
    - Builds index ONLY if missing + explicitly requested
    """

    global rss_faiss_store, blog_faiss_store

    # ---------------------------------------------------
    # STEP 1: RSS MODE
    # ---------------------------------------------------
    if selected_tool == "rss":
        print("[main] RSS mode -> LOAD existing FAISS or build if missing")

        if rss_faiss_store is None:
            try:
                from ..vector_store import RSS_FAISS_DIR, EMBEDDING_MODEL_NAME
                rss_faiss_store = load_faiss_local(
                    RSS_FAISS_DIR,
                    EMBEDDING_MODEL_NAME
                )
                print("[main] RSS FAISS loaded successfully")

            except Exception as e:
                print(f"[main] RSS FAISS not found: {e}")

                if not build_if_missing:
                    raise RuntimeError(
                        "RSS FAISS index missing. Run once with build_if_missing=True."
                    )

                print("[main] Building RSS FAISS index (this may take time)...")
                rebuild_state = WorkflowState(
                    request_id="build-rss-main",
                    query="",
                    selected_tool="rss"
                )

                rebuild_rss_faiss_always(rebuild_state)

                if rebuild_state.status == "error":
                    raise RuntimeError(f"RSS rebuild failed: {rebuild_state.error}")

                rss_faiss_store = load_faiss_local(
                    RSS_FAISS_DIR,
                    EMBEDDING_MODEL_NAME
                )
                print("[main] RSS FAISS loaded after build")

        retriever_node = make_faiss_retriever_tool_from_store(
            rss_faiss_store,
            k=10
        )

    # ---------------------------------------------------
    # STEP 2: BLOG MODE (KDnuggets)
    # ---------------------------------------------------
    elif selected_tool == "blog":
        if not selected_blog or selected_blog not in BLOG_SOURCES:
            raise ValueError("Invalid or missing blog selection")

        blog_cfg = BLOG_SOURCES[selected_blog]
        blog_dir = blog_cfg["faiss_dir"]
        build_fn = blog_cfg["build_fn"]

        print(f"[main] BLOG mode -> {selected_blog}")

        try:
            from ..vector_store import EMBEDDING_MODEL_NAME
            blog_faiss_store = load_faiss_local(blog_dir, EMBEDDING_MODEL_NAME)
            print(f"[main] Loaded {selected_blog} FAISS")

        except Exception as e:
            if not build_if_missing:
                raise RuntimeError(
                    f"{selected_blog} FAISS missing. Run with build_if_missing=True"
                )

            print(f"[main] Building {selected_blog} FAISS")
            build_state = WorkflowState(
                request_id=f"build-{selected_blog}",
                query="",
                selected_tool="blog",
                selected_blog=selected_blog,
            )

            build_fn(build_state)

            if build_state.status == "error":
                raise RuntimeError(build_state.error)

            blog_faiss_store = load_faiss_local(blog_dir, EMBEDDING_MODEL_NAME)

        retriever_node = make_faiss_retriever_tool_from_store(
        blog_faiss_store,
        k=6
    )


    else:
        raise ValueError(f"Unknown selected_tool: {selected_tool}")

    # ---------------------------------------------------
    # STEP 3: Agent
    # ---------------------------------------------------
    agent_node = make_react_agent_node_with_tool(
        retriever_call_fn=retriever_node,
        llm_model="openai/gpt-oss-120b",
    )

    # ---------------------------------------------------
    # STEP 4: Graph (FAST PATH)
    # ---------------------------------------------------
    nodes = [
        NodeSpec(id="start", func=lambda s: s),
        NodeSpec(id="retriever", func=retriever_node, run_with_query=True),
        NodeSpec(id="agent", func=agent_node),
        NodeSpec(id="end", func=lambda s: s),
    ]

    edges = [
        ("start", "retriever"),
        ("retriever", "agent"),
        ("agent", "end"),
    ]

    graph = StateGraph(nodes=nodes, edges=edges, start_node="start")

    init_state = WorkflowState(
        request_id="req-001",
        query=query,
        selected_tool=selected_tool,
        selected_blog=selected_blog,
    )

    return graph.run(init_state)
