"""
Weekly RAG re-indexing entry point.
Triggered by GitHub Actions every Sunday to refresh the knowledge base
with the latest campaign and performance data.
"""

from rag.indexer import run_full_index

if __name__ == "__main__":
    run_full_index()