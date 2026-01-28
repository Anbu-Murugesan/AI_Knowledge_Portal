"""
Research paper processing and LLM summarization
"""
import os
import traceback
from typing import Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from langchain_groq import ChatGroq

from research.config import DEFAULT_LLM_MODEL, DEFAULT_TEMPERATURE


def generate_llm_summary_for_paper(title: str, abstract: str) -> Dict[str, Any]:
    """
    Generate LLM-powered summary and key points for a research paper.

    Args:
        title: Paper title
        abstract: Paper abstract
        llm_model: LLM model to use (optional)

    Returns:
        Dictionary with llm_overview and llm_key_points
    """
    try:
        # Initialize LLM
        llm = ChatGroq(
            api_key=os.environ.get("GROQ_API_KEY"),
            model=DEFAULT_LLM_MODEL,
            temperature=DEFAULT_TEMPERATURE
        )

        # Prepare the prompt
        prompt = f"""
You are an expert AI researcher. Analyze this research paper and provide:

1. A 2-line overview of what this paper does
2. 3-5 bullet points of the key contributions/methods

Paper Title: {title}
Abstract: {abstract}

Format your response as JSON:
{{
    "overview": "2-line overview here",
    "key_points": ["point 1", "point 2", "point 3", "point 4", "point 5"]
}}
"""

        response = llm.invoke(prompt)

        # Extract and parse the response
        raw_text = response.content if hasattr(response, "content") else str(response)

        # Try to extract JSON from the response
        import json
        import re

        # Look for JSON pattern in the response
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                data = json.loads(json_str)
                return {
                    "llm_overview": data.get("overview", ""),
                    "llm_key_points": data.get("key_points", [])
                }
            except json.JSONDecodeError:
                pass

        # Fallback: return empty results
        return {
            "llm_overview": "",
            "llm_key_points": []
        }

    except Exception as e:
        print(f"LLM summarization failed for '{title}': {e}")
        return {
            "llm_overview": "",
            "llm_key_points": []
        }


def make_paper_record_from_doc(doc) -> Dict[str, Any]:
    """
    Convert arXiv document to standardized paper record.

    Args:
        doc: ArXiv document object

    Returns:
        Standardized paper dictionary
    """
    from research.utils import parse_date, prepare_abstract_for_llm
    # from research.processors import generate_llm_summary_for_paper

    try:
        # Extract metadata
        meta = getattr(doc, 'metadata', {}) or {}
        page_content = getattr(doc, 'page_content', '')

        # Parse title
        title = meta.get('title', '').strip()
        if not title and page_content:
            # Fallback: try to extract title from content
            lines = page_content.split('\n', 3)
            title = lines[0].strip() if lines else ''

        # Parse authors
        authors = meta.get('authors', [])
        if isinstance(authors, str):
            authors = [authors]
        elif not authors:
            authors = []

        # Parse publication date
        published_date = parse_date(meta)

        # Extract URLs
        pdf_url = meta.get('pdf_url') or meta.get('entry_id', '')
        if pdf_url and 'arxiv.org' in pdf_url and not pdf_url.endswith('.pdf'):
            pdf_url = pdf_url.replace('abs', 'pdf') + '.pdf'

        entry_id = meta.get('entry_id', '')
        abs_url = entry_id if entry_id else ''

        # Prepare abstract for LLM
        raw_abstract = meta.get('summary', '') or page_content
        prepared_abstract = prepare_abstract_for_llm(raw_abstract)

        # Generate LLM summary (optional - can be expensive)
        llm_summary = {}
        if prepared_abstract and len(prepared_abstract) > 50:
            llm_summary = generate_llm_summary_for_paper(title, prepared_abstract)

        # Create the paper record
        paper_record = {
            "title": title,
            "authors": authors,
            "date": published_date,
            "url": abs_url,
            "pdf": pdf_url,
            "raw_summary": raw_abstract,
            "snippet": prepared_abstract,
            "llm_overview": llm_summary.get("llm_overview", ""),
            "llm_key_points": llm_summary.get("llm_key_points", []),
            "source": "arxiv",
            "metadata": meta
        }

        return paper_record

    except Exception as e:
        print(f"Failed to process document: {e}")
        # Return minimal record on failure
        return {
            "title": getattr(doc, 'metadata', {}).get('title', 'Unknown Title'),
            "authors": [],
            "date": None,
            "url": "",
            "pdf": "",
            "raw_summary": getattr(doc, 'page_content', ''),
            "snippet": "",
            "llm_overview": "",
            "llm_key_points": [],
            "source": "arxiv",
            "metadata": getattr(doc, 'metadata', {})
        }
