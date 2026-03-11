import os
from typing import List, Dict, Any, Callable, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from ..models import WorkflowState
from ..logging_config import get_vector_store_logger

logger = get_vector_store_logger()

# Configuration
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
RSS_FAISS_DIR = "faiss_index_local"
BLOG_FAISS_DIR = "./kdnuggets_faiss"

# Global stores
rss_faiss_store: Optional[FAISS] = None
blog_faiss_store: Optional[FAISS] = None

# Text splitter for chunking
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)


def build_faiss_from_docs_and_save(documents: List[Document], index_dir: str, model_name: str) -> FAISS:
    logger.info(f"Building FAISS index from {len(documents)} documents, saving to {index_dir}")
    split_docs = text_splitter.split_documents(documents)
    if not split_docs:
        logger.error("No split documents to index")
        raise RuntimeError("No split documents to index.")
    logger.debug(f"Split documents into {len(split_docs)} chunks")
    for d in split_docs:
        d.metadata["title"] = (d.metadata.get("title") or "").strip()
        d.metadata["link"] = (d.metadata.get("link") or "").strip()
        if not d.metadata.get("summary"):
            d.metadata["summary"] = (clean_text(d.page_content)[:300]).strip()
    logger.debug(f"Loading embeddings model: {model_name}")
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    store = FAISS.from_documents(split_docs, embeddings)
    os.makedirs(index_dir, exist_ok=True)
    store.save_local(index_dir)
    logger.info(f"FAISS index saved successfully to {index_dir}")
    return store


def build_faiss_vectorstore_for_blog(
    docs,
    persist_directory: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
):
    """
    Build FAISS index for blogs using UNIFORM chunking.
    Matches old (stable) blog logic exactly.
    """

    os.makedirs(persist_directory, exist_ok=True)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

    split_docs = []
    for d in docs:
        text = getattr(d, "page_content", None) or getattr(d, "content", "")
        metadata = getattr(d, "metadata", {}) or {}
        chunks = splitter.create_documents([text], metadatas=[metadata])
        split_docs.extend(chunks)

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME
    )

    vectordb = FAISS.from_documents(
        documents=split_docs,
        embedding=embeddings
    )

    vectordb.save_local(persist_directory)
    return vectordb


def load_faiss_local(persist_dir: str, model_name: str = EMBEDDING_MODEL_NAME) -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    if not os.path.isdir(persist_dir):
        raise FileNotFoundError(f"FAISS persist dir not found: {persist_dir}")
    # allow dangerous deserialization to support some older stores
    vectordb = FAISS.load_local(persist_dir, embeddings, allow_dangerous_deserialization=True)
    return vectordb


def load_blog_faiss() -> FAISS:
    return load_faiss_local(
        BLOG_FAISS_DIR,
        EMBEDDING_MODEL_NAME
    )


def make_faiss_retriever_tool_from_store(
    faiss_store_local: FAISS,
    k: int = 10,
    max_unique: int = 10,
    fetch_k: int = 50,
    use_mmr: bool = True,
) -> Callable[[str, WorkflowState], WorkflowState]:
    """
    Build a retriever_node(query, state) that:
      - calls the FAISS retriever (robust to method signatures)
      - deduplicates results by link/title keeping the best chunk per source
      - populates state.retrieved_docs (title, link, optional summary) up to max_unique
      - deliberately DOES NOT populate state.retrieved_text
    """

    # ------------------ Create retriever ------------------
    try:
        if use_mmr:
            retriever = faiss_store_local.as_retriever(
                search_type="mmr",
                search_kwargs={"k": k, "fetch_k": fetch_k, "lambda_mult": 0.7},
            )
        else:
            retriever = faiss_store_local.as_retriever(search_kwargs={"k": k})
    except Exception:
        retriever = faiss_store_local.as_retriever(search_kwargs={"k": k})

    # ------------------ Robust caller ------------------
    def call_get_relevant_documents(q: str):
    # ✅ Most reliable for current LangChain
        try:
            return retriever.invoke(q)
        except Exception:
            pass

    # ✅ Older versions
        try:
            return retriever.get_relevant_documents(q)
        except Exception:
            pass

    # ❌ If both fail, surface error
        raise RuntimeError("FAISS retriever returned no documents")


    # ------------------ Retriever node ------------------

    def retriever_node(query: str, state: WorkflowState) -> WorkflowState:
        try:
            docs = call_get_relevant_documents(query)

            logger.debug(f"Retrieved {len(docs)} documents from vector store for query: '{query[:50]}...'")

            state.retrieved_docs = []

            for d in docs[:max_unique]:
                meta = getattr(d, "metadata", {}) or {}

                title = extract_title_from_doc(d)

                link = (
            meta.get("link")
            or meta.get("source")
            or meta.get("url")
            or meta.get("source_url")
            or ""
        ).strip()

                summary = (meta.get("summary") or d.page_content or "")[:300]

                state.retrieved_docs.append({
            "title": title,
            "link": link,
            "summary": summary,
        })

            state.retrieved_text = ""
            state.status = "retrieved"

        except Exception as e:
            state.status = "error"
            state.error = str(e)

        return state

    return retriever_node


def blog_retriever_kdnuggets(query: str, state: WorkflowState) -> WorkflowState:
    try:
        blog_store = load_faiss_local(BLOG_FAISS_DIR, EMBEDDING_MODEL_NAME)
        retriever = make_faiss_retriever_tool_from_store(blog_store, k=6)
        return retriever(query, state)
    except Exception as e:
        state.status = "error"
        state.error = f"KDnuggets retriever error: {e}"
        return state


# Import here to avoid circular imports
def clean_text(text: str) -> str:
    from ..text_processing import clean_text as _clean_text
    return _clean_text(text)


def extract_title_from_doc(doc) -> str:
    from ..text_processing import extract_title_from_doc as _extract_title
    return _extract_title(doc)
