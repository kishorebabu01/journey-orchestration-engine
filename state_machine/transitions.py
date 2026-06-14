# ============================================================
# FILE: state_machine/transitions.py
# PURPOSE: Manages journey state transitions and persists
#          state changes to Supabase.
# ============================================================

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import create_client

from state_machine.states import (
    JourneyState,
    is_valid_transition,
)

load_dotenv(override=True)

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


def transition_user_state(
    user_id: str,
    new_state: JourneyState,
    previous_state: JourneyState,
    trigger_event: str,
    dry_run: bool = False
) -> dict:
    """
    Transition a user from one journey state to another.

    Args:
        user_id: Unique user identifier.
        new_state: Target journey state.
        previous_state: Current journey state.
        trigger_event: Event responsible for the transition.
        dry_run: If True, validates the transition without
            writing to the database.

    Returns:
        Dictionary containing transition results.
    """

    # Validate transition rules
    if not is_valid_transition(previous_state, new_state):
        error_msg = (
            f"ILLEGAL TRANSITION: "
            f"{previous_state.value} → "
            f"{new_state.value} "
            f"for user {user_id}"
        )

        print(f"  ❌ {error_msg}")

        return {
            "success": False,
            "user_id": user_id,
            "from": previous_state.value,
            "to": new_state.value,
            "error": error_msg
        }

    # Validation-only mode
    if dry_run:
        print(
            f"  🔍 [DRY RUN] Would transition "
            f"{user_id[:8]}... "
            f"{previous_state.value} → "
            f"{new_state.value}"
        )

        return {
            "success": True,
            "user_id": user_id,
            "from": previous_state.value,
            "to": new_state.value,
            "dry_run": True
        }

    now = datetime.now(timezone.utc).isoformat()

    try:
        # Update current user state
        supabase.table("users").update({
            "current_state": new_state.value,
            "state_updated_at": now,
        }).eq(
            "id",
            user_id
        ).execute()

        # Store transition history
        supabase.table("journey_states").insert({
            "user_id": user_id,
            "state": new_state.value,
            "previous_state": previous_state.value,
            "trigger_event": trigger_event,
            "transitioned_at": now,
        }).execute()

        print(
            f"  ✅ Transitioned "
            f"{user_id[:8]}... "
            f"{previous_state.value} → "
            f"{new_state.value} "
            f"(trigger: {trigger_event})"
        )

        return {
            "success": True,
            "user_id": user_id,
            "from": previous_state.value,
            "to": new_state.value,
            "transitioned_at": now
        }

    except Exception as e:
        print(
            f"  ❌ Transition failed "
            f"for {user_id}: {e}"
        )

        return {
            "success": False,
            "user_id": user_id,
            "from": previous_state.value,
            "to": new_state.value,
            "error": str(e)
        }