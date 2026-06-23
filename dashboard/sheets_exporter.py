"""
Exports Supabase journey and performance data to Google Sheets
for Looker Studio dashboard consumption.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


def export_journey_distribution():
    """Export current user counts per journey state."""
    users = supabase.table("users").select("current_state").execute()

    distribution = {}
    for user in users.data:
        state = user["current_state"]
        distribution[state] = distribution.get(state, 0) + 1

    return distribution


if __name__ == "__main__":
    print(export_journey_distribution())