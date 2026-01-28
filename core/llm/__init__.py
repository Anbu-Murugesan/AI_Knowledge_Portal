"""
LLM and agent logic
"""
import re
import traceback
from typing import List, Dict, Any, Callable

import os
from langchain_groq import ChatGroq

from ..models import WorkflowState
from ..text_processing import clean_blog_title


def normalize_summary(summary: str) -> str:
    """
    Clean summary text for LLM consumption.
    """
    if not summary:
        return ""
    summary = re.sub(r"\s+", " ", summary)
    return summary.strip()


def make_react_agent_node_with_tool(
    retriever_call_fn: Callable[[str, WorkflowState], WorkflowState],
    llm_model: str = "llama-3.1-70b-versatile"
):
    """
    FINAL AGENT
    Output per article:
    title
    link
    key_points
    """

    import json
    import re
    from langchain_groq import ChatGroq

    def node(state: WorkflowState) -> WorkflowState:
        state.status = "generating"

        try:
            sources = state.retrieved_docs or []

            if not sources:
                state.generated_post = []
                state.status = "done"
                return state
            source_payload = []

            for s in sources:
                clean_title = clean_blog_title(s.get("title", ""))

                clean_summary = normalize_summary(s.get("summary", ""))

                source_payload.append({
            "title": clean_title,
            "link": s.get("link", ""),
            "summary": clean_summary
        })


            prompt = f"""
You are an expert tech news and blog summarizer.
STRICT RULES (MANDATORY):
- Title must be clean, professional mainly for blogs
- Do NOT include conversational phrases like "Here's the response"
- Use ONLY the information explicitly present in SOURCES
- If information is missing, say so
- Do NOT infer, guess, or add future announcements
- Do NOT mention model versions unless present in SOURCES
- Do NOT summarize beyond retrieved content
- If sources are insufficient, return an empty list

TASK:
For EACH source below:
- Understand the topic
STRICT RULE:
- Use the title EXACTLY as provided for your undertsing
- rephrase, summarize, or rewrite titles just small title
- Do NOT prepend numbers or headings to titles

- Generate key bullet points covering the main aspects

STRICT RULES:
- Output must be a SINGLE valid JSON ARRAY
- ONE object per source
- Each object MUST contain:
  - title
  - link
  - key_points
- key_points must contain 3–5 concise bullets
- Do NOT merge sources
- Do NOT add extra text

JSON FORMAT:
[
  {{
    "title": "<title>",
    "link": "<url>",
    "key_points": ["point 1", "point 2", "point 3"]

  }}
]

SOURCES:
{json.dumps(source_payload, indent=2)}
"""

            llm = ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"),
                model=llm_model,
                temperature=0.2
            )

            response = llm.invoke(prompt)
            raw_text = response.content if hasattr(response, "content") else str(response)

            try:
                data = json.loads(raw_text)
            except Exception:
                match = re.search(r"\[.*\]", raw_text, re.DOTALL)
                if not match:
                    raise ValueError("Invalid JSON from LLM")
                data = json.loads(match.group(0))

            state.generated_post = [
                {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "key_points": [k for k in item.get("key_points", []) if k]
                }
                for item in data
            ]

            state.status = "done"
            return state

        except Exception as e:
            state.status = "error"
            state.error = f"agent error: {repr(e)}\n{traceback.format_exc()}"
            return state

    return node
