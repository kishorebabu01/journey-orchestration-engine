# ============================================================
# FILE: rag/retriever.py
# PURPOSE: Retrieves relevant knowledge base content using
#          vector similarity search for RAG workflows.
# ============================================================

import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client

load_dotenv(override=True)

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# Load embedding model
# The same model must be used for both indexing and retrieval.
print("Loading embedding model for retrieval...")
model = SentenceTransformer("all-MiniLM-L6-v2")


# ============================================================
# Retrieval
# ============================================================

def retrieve(
    query: str,
    top_k: int = 5,
    doc_type: str = None
) -> list:
    """
    Retrieve the most relevant document chunks.

    Args:
        query: Search query.
        top_k: Number of results to return.
        doc_type: Optional document type filter.

    Returns:
        List of matching document chunks.
    """

    query_embedding = model.encode(
        query
    ).tolist()

    try:
        result = supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_count": top_k
            }
        ).execute()

        return result.data if result.data else []

    except Exception as e:
        print(f"  ❌ Retrieval error: {e}")
        return []


# ============================================================
# Query Builder
# ============================================================

def build_query_from_trigger(
    trigger_type: str,
    journey_state: str,
    trigger_data: dict
) -> str:
    """
    Generate a semantic retrieval query from
    trigger metadata.

    Args:
        trigger_type: Trigger identifier.
        journey_state: Current user lifecycle state.
        trigger_data: Additional trigger attributes.

    Returns:
        Search query optimized for retrieval.
    """

    query = (
        f"{trigger_type} "
        f"{journey_state} "
        f"message campaign"
    )

    days_inactive = trigger_data.get(
        "days_inactive",
        0
    )

    engagement_score = trigger_data.get(
        "engagement_score",
        0
    )

    hours_since_signup = trigger_data.get(
        "hours_since_signup",
        0
    )

    if days_inactive > 0:
        query += (
            f" inactive {days_inactive} days "
            f"reengagement winback"
        )

    if engagement_score > 80:
        query += (
            " high engagement "
            "power user "
            "upgrade referral"
        )

    if 0 < engagement_score <= 80:
        query += (
            f" engagement score "
            f"{engagement_score} retention"
        )

    if hours_since_signup > 0:
        query += (
            " new user "
            "activation onboarding "
            "first session"
        )

    return query


# ============================================================
# Context Formatting
# ============================================================

def format_context(chunks: list) -> str:
    """
    Format retrieved document chunks for prompt injection.

    Args:
        chunks: Retrieved document chunks.

    Returns:
        Formatted context string.
    """

    if not chunks:
        return (
            "No relevant context found "
            "in knowledge base."
        )

    formatted = []

    for i, chunk in enumerate(chunks, 1):
        formatted.append(
            f"[Context {i}]\n"
            f"{chunk.get('content', '')}\n"
        )

    return "\n".join(formatted)


# ============================================================
# Local Testing
# ============================================================

if __name__ == "__main__":
    print("\n🔍 Testing RAG Retrieval...")
    print("=" * 60)

    print(
        "\nTest 1: "
        "Searching for CHURN_RISK winback content"
    )

    query1 = build_query_from_trigger(
        trigger_type="winback_day7",
        journey_state="CHURN_RISK",
        trigger_data={
            "days_inactive": 8
        }
    )

    print(f"Query: '{query1}'")

    results1 = retrieve(
        query1,
        top_k=3
    )

    print(
        f"Found {len(results1)} chunks:"
    )

    for r in results1:
        print(
            f"  → "
            f"[{r.get('doc_type')}] "
            f"{r.get('content', '')[:80]}..."
        )

    print(
        "\nTest 2: "
        "Searching for NEW_SIGNUP activation content"
    )

    query2 = build_query_from_trigger(
        trigger_type="activation_nudge_24h",
        journey_state="NEW_SIGNUP",
        trigger_data={
            "hours_since_signup": 26
        }
    )

    print(f"Query: '{query2}'")

    results2 = retrieve(
        query2,
        top_k=3
    )

    print(
        f"Found {len(results2)} chunks:"
    )

    for r in results2:
        print(
            f"  → "
            f"[{r.get('doc_type')}] "
            f"{r.get('content', '')[:80]}..."
        )

    print("\n✅ Retrieval test complete")