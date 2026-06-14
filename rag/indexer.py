# ============================================================
# FILE: rag/indexer.py
# PURPOSE: Read all knowledge documents, convert to embeddings,
#          store in Supabase pgvector (rag_documents table)
# ============================================================

import os
import sys
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from supabase import create_client

load_dotenv(override=True)

# ── Connect to Supabase ──────────────────────────────────────
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# ── Load the embedding model ─────────────────────────────────
# Converts any text into 384 numbers representing its meaning
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ Model loaded")


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_DIR = os.path.join(BASE_DIR, "config")


# ============================================================
# HELPER: Convert text into embedding (384 numbers)
# ============================================================

def embed(text: str) -> list:
    """
    Convert a string of text into a list of 384 numbers.
    These numbers represent the MEANING of the text.

    Example:
        embed("winback campaign") → [0.2, 0.8, 0.1, ...]
        embed("reengagement email") → [0.2, 0.7, 0.1, ...]
        (similar meaning = similar numbers)
    """
    vector = model.encode(text)
   
    return vector.tolist()


# ============================================================
# HELPER: Store one chunk in Supabase
# ============================================================

def store_chunk(doc_type: str, content: str, metadata: dict):
    """
    Store one document chunk in the rag_documents table.

    Parameters:
        doc_type : what kind of document is this?
                   e.g. 'past_campaign', 'brand_voice'
        content  : the actual text of this chunk
        metadata : extra info like source file, campaign name
    """
    # Step 1: Convert the content text into 384 numbers
    embedding = embed(content)

    # Step 2: Insert into Supabase rag_documents table
    supabase.table("rag_documents").insert({
        "doc_type":   doc_type,
        "content":    content,
        "metadata":   metadata,
        "embedding":  embedding,
        "indexed_at": datetime.now(timezone.utc).isoformat()
    }).execute()


# ============================================================
# INDEXER 1: past_campaigns.csv
# ============================================================

def index_past_campaigns():
    """
    Read past_campaigns.csv and store each campaign as one chunk.

    Each row = one campaign = one chunk in the knowledge base.
    The AI will find relevant campaigns when generating messages.
    """
    print("\n📄 Indexing past_campaigns.csv...")

    filepath = os.path.join(DATA_DIR, "past_campaigns.csv")

    
    df = pd.read_csv(filepath)

    count = 0
    for _, row in df.iterrows():
        
        content = (
            f"Campaign: {row['campaign_name']}. "
            f"Trigger: {row['trigger_type']}. "
            f"Journey state: {row['journey_state']}. "
            f"Channel: {row['channel']}. "
            f"Message style: {row['message_style']}. "
            f"Subject/headline: {row['subject_line']}. "
            f"Open rate: {row['open_rate']}. "
            f"CTR: {row['ctr']}. "
            f"Conversion rate: {row['conversion_rate']}. "
            f"Notes: {row['notes']}."
        )

        
        metadata = {
            "source_file":       "past_campaigns.csv",
            "campaign_id":       row['campaign_id'],
            "campaign_name":     row['campaign_name'],
            "trigger_type":      row['trigger_type'],
            "journey_state":     row['journey_state'],
            "channel":           row['channel'],
            "message_style":     row['message_style'],
            "open_rate":         float(row['open_rate']),
            "ctr":               float(row['ctr']),
            "conversion_rate":   float(row['conversion_rate']),
        }

        store_chunk("past_campaign", content, metadata)
        count += 1

    print(f"  ✅ Indexed {count} campaigns")


# ============================================================
# INDEXER 2: message_performance_history.csv
#                   - detailed message performance by segment
# ============================================================

def index_message_performance():
    """
    Read message_performance_history.csv and store each row.
    This gives the AI granular data about what works for
    which user segment and engagement score.
    """
    print("\n📄 Indexing message_performance_history.csv...")

    filepath = os.path.join(DATA_DIR, "message_performance_history.csv")
    df = pd.read_csv(filepath)

    count = 0
    for _, row in df.iterrows():
        content = (
            f"Message performance record. "
            f"Trigger: {row['trigger_type']}. "
            f"Journey state: {row['journey_state']}. "
            f"Channel: {row['channel']}. "
            f"Message style: {row['message_style']}. "
            f"User segment: {row['user_segment']}. "
            f"Engagement score at send: {row['engagement_score_at_send']}. "
            f"Open rate: {row['open_rate']}. "
            f"CTR: {row['ctr']}. "
            f"Conversion rate: {row['conversion_rate']}."
        )

        metadata = {
            "source_file":              "message_performance_history.csv",
            "message_id":               row['message_id'],
            "trigger_type":             row['trigger_type'],
            "journey_state":            row['journey_state'],
            "channel":                  row['channel'],
            "message_style":            row['message_style'],
            "user_segment":             row['user_segment'],
            "engagement_score_at_send": int(row['engagement_score_at_send']),
            "ctr":                      float(row['ctr']),
            "conversion_rate":          float(row['conversion_rate']),
        }

        store_chunk("message_performance", content, metadata)
        count += 1

    print(f"  ✅ Indexed {count} performance records")


# ============================================================
# INDEXER 3: brand_voice.md
# ============================================================

def index_brand_voice():
    """
    Read brand_voice.md and split into sections.
    Each section = one chunk.

    We split by '##' headings because each section
    covers a different aspect of brand voice.
    """
    print("\n📄 Indexing brand_voice.md...")

    filepath = os.path.join(CONFIG_DIR, "brand_voice.md")

    with open(filepath, "r", encoding="utf-8") as f:
        
        full_text = f.read()

    
    sections = full_text.split("## ")

    count = 0
    for section in sections:
        
        if len(section.strip()) < 20:
            continue

        content = f"Brand voice guideline: {section.strip()}"

        metadata = {
            "source_file": "brand_voice.md",
            "doc_type":    "brand_voice",
            "section":     section[:50]  # first 50 chars as label
        }

        store_chunk("brand_voice", content, metadata)
        count += 1

    print(f"  ✅ Indexed {count} brand voice sections")


# ============================================================
# INDEXER 4: product_features.md
# ============================================================

def index_product_features():
    """
    Read product_features.md and split into sections.
    AI uses this to mention specific features in messages.
    """
    print("\n📄 Indexing product_features.md...")

    filepath = os.path.join(DATA_DIR, "product_features.md")

    with open(filepath, "r", encoding="utf-8") as f:
        full_text = f.read()

    
    sections = full_text.split("## ")

    count = 0
    for section in sections:
        if len(section.strip()) < 20:
            continue

        content = f"Focusly product feature: {section.strip()}"

        metadata = {
            "source_file": "product_features.md",
            "doc_type":    "product_feature",
            "section":     section[:50]
        }

        store_chunk("product_feature", content, metadata)
        count += 1

    print(f"  ✅ Indexed {count} feature sections")


# ============================================================
# INDEXER 5: user_segments.md
# ============================================================

def index_user_segments():
    """
    Read user_segments.md and split into sections.
    Each segment = one chunk.
    AI uses this to tailor messages per segment type.
    """
    print("\n📄 Indexing user_segments.md...")

    filepath = os.path.join(DATA_DIR, "user_segments.md")

    with open(filepath, "r", encoding="utf-8") as f:
        full_text = f.read()

    sections = full_text.split("## ")

    count = 0
    for section in sections:
        if len(section.strip()) < 20:
            continue

        content = f"User segment insight: {section.strip()}"

        metadata = {
            "source_file": "user_segments.md",
            "doc_type":    "user_segment",
            "section":     section[:50]
        }

        store_chunk("user_segment", content, metadata)
        count += 1

    print(f"  ✅ Indexed {count} user segment sections")


# ============================================================
# MAIN: Run all indexers
# ============================================================

def run_full_index():
    """
    Clear existing rag_documents and rebuild from scratch.
    Called once at setup and weekly by GitHub Actions.
    """
    print("=" * 60)
    print("🗂️  RAG INDEXER — FOCUSLY KNOWLEDGE BASE")
    print("=" * 60)

    
    print("\n🗑️  Clearing existing rag_documents...")
    supabase.table("rag_documents").delete().neq(
        "id", "00000000-0000-0000-0000-000000000000"
    ).execute()
    
    print("  ✅ Cleared")

   
    index_past_campaigns()
    index_message_performance()
    index_brand_voice()
    index_product_features()
    index_user_segments()

    
    result = supabase.table("rag_documents").select(
        "id", count="exact"
    ).execute()
    total = result.count

    print(f"\n{'=' * 60}")
    print(f"✅ INDEXING COMPLETE")
    print(f"   Total chunks stored: {total}")
    print(f"   Table: rag_documents")
    print(f"   Ready for retrieval")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    run_full_index()