"""
Aggregates message outcome data into performance summaries
used to refresh the RAG knowledge base during weekly re-indexing.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


def log_performance_summary():
    """Generate and print a performance summary across all channels."""
    outcomes = supabase.table("message_outcomes").select("*").execute()

    total = len(outcomes.data)
    opened = sum(1 for o in outcomes.data if o.get("opened"))
    clicked = sum(1 for o in outcomes.data if o.get("clicked"))

    print(f"Total messages tracked: {total}")
    print(f"Open rate: {opened / total * 100:.1f}%" if total else "No data")
    print(f"Click rate: {clicked / total * 100:.1f}%" if total else "No data")


if __name__ == "__main__":
    log_performance_summary()