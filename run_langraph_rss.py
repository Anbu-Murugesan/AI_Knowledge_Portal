#!/usr/bin/env python3
"""
Run LangGraph workflow for RSS Vector Database operations
"""

from core.workflows import run_full_workflow_example

def main():
    """Run RSS VDB workflow example"""

    # Example 1: Run RSS search with automatic index building
    print("=== Running RSS LangGraph Workflow ===")

    try:
        result = run_full_workflow_example(
            query="AI news",
            selected_tool="rss",
            build_if_missing=True  # This will build RSS FAISS index if missing
        )

        print("✅ Workflow completed successfully!")
        print(f"Status: {result.status}")

        if result.error:
            print(f"❌ Error: {result.error}")
        else:
            print(f"📄 Retrieved {len(result.retrieved_docs)} documents")
            if result.generated_post:
                print("🤖 Generated response available")
            else:
                print("📋 Raw documents retrieved (no LLM generation)")

    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

