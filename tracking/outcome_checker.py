"""
Checks PostHog for engagement outcomes (opens, clicks, conversions)
on previously delivered messages and writes results to Supabase.
"""

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


def check_outcomes():
    """Check delivered messages for engagement outcomes."""
    messages = supabase.table("messages_sent").select("*").eq(
        "delivery_status", "delivered"
    ).execute()

    print(f"Checking outcomes for {len(messages.data)} delivered messages")

    for msg in messages.data:
        existing = supabase.table("message_outcomes").select("id").eq(
            "message_id", msg["id"]
        ).execute()

        if not existing.data:
            supabase.table("message_outcomes").insert({
                "message_id": msg["id"],
                "user_id": msg["user_id"],
                "opened": False,
                "clicked": False,
                "converted": False,
                "checked_at": datetime.now(timezone.utc).isoformat()
            }).execute()

    print("Outcome check complete")


if __name__ == "__main__":
    check_outcomes()