"""
LangChain tool definitions for the journey orchestration agent.
Wraps RAG retrieval and message generation as callable agent tools.
"""

from langchain.tools import tool
from rag.retriever import retrieve, build_query_from_trigger, format_context


@tool
def query_rag_tool(trigger_type: str, journey_state: str) -> str:
    """Retrieve relevant marketing knowledge for a given trigger and journey state."""
    query = build_query_from_trigger(trigger_type, journey_state, {})
    chunks = retrieve(query, top_k=5)
    return format_context(chunks)