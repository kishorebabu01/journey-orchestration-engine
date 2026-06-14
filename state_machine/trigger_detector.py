# ============================================================
# FILE: state_machine/trigger_detector.py
# PURPOSE: Detects and creates journey triggers based on
#          current user state and behavioral signals.
# ============================================================

import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from supabase import create_client

from state_machine.states import (
    JourneyState,
    get_state_from_string,
)

load_dotenv(override=True)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


def has_trigger_been_fired(
    user_id: str,
    trigger_type: str
) -> bool:
    """
    Check whether a trigger has already been fired
    for a given user.

    Args:
        user_id: User identifier.
        trigger_type: Trigger name.

    Returns:
        True if the trigger already exists, otherwise False.
    """

    result = (
        supabase.table("journey_triggers")
        .select("id")
        .eq("user_id", user_id)
        .eq("trigger_type", trigger_type)
        .execute()
    )

    return len(result.data) > 0


def fire_trigger(
    user_id: str,
    trigger_type: str,
    trigger_data: dict
) -> dict:
    """
    Create a trigger record for downstream processing.

    Args:
        user_id: User identifier.
        trigger_type: Trigger name.
        trigger_data: Trigger metadata.

    Returns:
        Dictionary containing trigger creation results.
    """

    if has_trigger_been_fired(
        user_id,
        trigger_type
    ):
        print(
            f"  ⏭️ Trigger already fired: "
            f"{trigger_type} for {user_id[:8]}"
        )

        return {
            "fired": False,
            "reason": "already_fired"
        }

    try:
        result = (
            supabase.table("journey_triggers")
            .insert({
                "user_id": user_id,
                "trigger_type": trigger_type,
                "trigger_data": trigger_data,
                "fired_at": datetime.now(
                    timezone.utc
                ).isoformat(),
                "processed": False,
            })
            .execute()
        )

        print(
            f"  🎯 Trigger fired: "
            f"{trigger_type} for {user_id[:8]}..."
        )

        return {
            "fired": True,
            "trigger_id": (
                result.data[0]["id"]
                if result.data
                else None
            ),
            "trigger_type": trigger_type
        }

    except Exception as e:
        print(f"  ❌ Failed to fire trigger: {e}")

        return {
            "fired": False,
            "error": str(e)
        }


def detect_triggers_for_user(
    user: dict,
    facts: dict
) -> list:
    """
    Determine which triggers should be fired for a user.

    Args:
        user: User record.
        facts: Evaluated behavioral metrics.

    Returns:
        List of successfully fired triggers.
    """

    user_id = user["id"]

    current_state = get_state_from_string(
        user["current_state"]
    )

    days_inactive = facts.get(
        "days_since_last_session",
        0
    )

    steps = facts.get(
        "activation_steps_completed",
        0
    )

    score = facts.get(
        "engagement_score",
        0
    )

    hours_since_signup = facts.get(
        "hours_since_signup",
        0
    )

    fired_triggers = []

    # NEW_SIGNUP
    if current_state == JourneyState.NEW_SIGNUP:

        if hours_since_signup >= 168:
            t = fire_trigger(
                user_id,
                "activation_final_7d",
                {
                    "hours_since_signup":
                        hours_since_signup,
                    "days_inactive":
                        days_inactive
                }
            )
            fired_triggers.append(t)

        elif hours_since_signup >= 72:
            t = fire_trigger(
                user_id,
                "activation_nudge_72h",
                {
                    "hours_since_signup":
                        hours_since_signup
                }
            )
            fired_triggers.append(t)

        elif hours_since_signup >= 24:
            t = fire_trigger(
                user_id,
                "activation_nudge_24h",
                {
                    "hours_since_signup":
                        hours_since_signup
                }
            )
            fired_triggers.append(t)

    # ACTIVATING
    elif current_state == JourneyState.ACTIVATING:

        if steps == 2:
            t = fire_trigger(
                user_id,
                "almost_there_nudge",
                {
                    "steps_completed": steps,
                    "steps_total": 3
                }
            )
            fired_triggers.append(t)

        elif steps == 1:
            t = fire_trigger(
                user_id,
                "progress_encouragement",
                {
                    "steps_completed": steps,
                    "steps_total": 3
                }
            )
            fired_triggers.append(t)

    # ACTIVATED
    elif current_state == JourneyState.ACTIVATED:

        t = fire_trigger(
            user_id,
            "celebration_message",
            {
                "activation_completed": True,
                "engagement_score": score
            }
        )

        fired_triggers.append(t)

    # RETAINED
    elif current_state == JourneyState.RETAINED:

        if score >= 60:
            t = fire_trigger(
                user_id,
                "power_feature_unlock",
                {
                    "engagement_score": score
                }
            )

        else:
            t = fire_trigger(
                user_id,
                "weekly_progress_insight",
                {
                    "engagement_score": score,
                    "days_since_last_session":
                        days_inactive
                }
            )

        fired_triggers.append(t)

    # CHURN_RISK
    elif current_state == JourneyState.CHURN_RISK:

        if days_inactive >= 21:
            t = fire_trigger(
                user_id,
                "winback_final_day21",
                {
                    "days_inactive":
                        days_inactive
                }
            )

        elif days_inactive >= 14:
            t = fire_trigger(
                user_id,
                "winback_day14",
                {
                    "days_inactive":
                        days_inactive
                }
            )

        elif days_inactive >= 7:
            t = fire_trigger(
                user_id,
                "winback_day7",
                {
                    "days_inactive":
                        days_inactive
                }
            )

        else:
            t = None

        if t:
            fired_triggers.append(t)

    # CHURNED
    elif current_state == JourneyState.CHURNED:

        t = fire_trigger(
            user_id,
            "reactivation_monthly",
            {
                "days_inactive":
                    days_inactive
            }
        )

        fired_triggers.append(t)

    # EXPANDING
    elif current_state == JourneyState.EXPANDING:

        if score >= 85:
            t = fire_trigger(
                user_id,
                "referral_invitation",
                {
                    "engagement_score":
                        score
                }
            )

        else:
            t = fire_trigger(
                user_id,
                "upgrade_prompt",
                {
                    "engagement_score":
                        score
                }
            )

        fired_triggers.append(t)

    return [
        trigger
        for trigger in fired_triggers
        if trigger.get("fired")
    ]