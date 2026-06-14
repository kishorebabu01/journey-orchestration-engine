# ============================================================
# FILE: state_machine/evaluator.py
# PURPOSE: The BRAIN of the state machine
# For every user, it:
# 1. Fetches their PostHog events (last 90 days)
# 2. Applies transition rules
# 3. Decides if they should move to a new state
# 4. Calls transitions.py to write the change
# ============================================================

import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from posthog import Posthog
from supabase import create_client

from state_machine.states import JourneyState, get_state_from_string
from state_machine.transitions import transition_user_state

load_dotenv(override=True)

# ── Clients ──────────────────────────────────────────────────
ph = Posthog(
    project_api_key=os.getenv("POSTHOG_PERSONAL_API_KEY").strip(),
    host=os.getenv("POSTHOG_HOST", "https://us.posthog.com").strip()
)

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


# ============================================================
# Fetch PostHog events for one user
# ============================================================

def get_user_events(user_id: str, days_back: int = 90) -> list:
    """
    Fetch all PostHog events for a user in the last N days.

    PostHog stores events with distinct_id = user_id (UUID).
    We query their API to get the event history.

    Returns a list of event dicts, sorted newest first.
    """
    import requests

    api_key  = os.getenv("POSTHOG_PERSONAL_API_KEY").strip()
    host     = os.getenv("POSTHOG_HOST", "https://us.posthog.com").strip()

    
    url = f"{host}/api/projects/@current/events/"

    params = {
        "distinct_id": user_id,
        "limit": 500,   
    }

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        events = data.get("results", [])
        return events
    except Exception as e:
        print(f"  ⚠️  Could not fetch PostHog events for {user_id[:8]}: {e}")
        return []


# ============================================================
# Analyse events to extract useful facts
# ============================================================

def analyse_events(events: list, user: dict) -> dict:
    """
    Turn a raw list of PostHog events into a structured
    summary of facts the evaluator can use to make decisions.

    Returns a dict like:
    {
        "has_used_core_feature": True,
        "has_activation_milestone": False,
        "days_since_last_session": 8,
        "sessions_last_7_days": 0,
        "activation_steps_completed": 1,
        ...
    }
    """
    now = datetime.now(timezone.utc)

    
    event_names = set()
    
    event_times = {}

    for event in events:
        name = event.get("event", "")
        event_names.add(name)

        
        ts_str = event.get("timestamp", "")
        if ts_str:
            try:
                ts = datetime.fromisoformat(
                    ts_str.replace("Z", "+00:00")
                )
                if name not in event_times:
                    event_times[name] = []
                event_times[name].append(ts)
            except Exception:
                pass

   
    last_session = None
    session_events = event_times.get("app_session_started", [])

    
    signup_events = event_times.get("signup_completed", [])
    all_activity = session_events + signup_events

    if all_activity:
        last_session = max(all_activity)
        days_since_last_session = (now - last_session).days
    else:
        days_since_last_session = 999  # never had a session

   
    sessions_last_7_days = sum(
        1 for ts in session_events
        if (now - ts).days <= 7
    )

    # ── Activation steps ──────────────────────────────────
    # infer steps from which events exist:
    # Step 1: first_core_feature_used
    # Step 2: task_added (with task_count >= 3)
    # Step 3: activation_milestone
    activation_steps = 0
    if "first_core_feature_used" in event_names:
        activation_steps = max(activation_steps, 1)
    if "task_added" in event_names:
        activation_steps = max(activation_steps, 2)
    if "activation_milestone" in event_names:
        activation_steps = 3

        signup_date_str = user.get("signup_date", "")
    hours_since_signup = 0
    days_since_signup = 0
    if signup_date_str:
        try:
            signup_dt = datetime.fromisoformat(
                signup_date_str.replace("Z", "+00:00")
            )
            delta = now - signup_dt
            hours_since_signup = delta.total_seconds() / 3600
            days_since_signup = delta.days
        except Exception:
            pass

        engagement_score = user.get("engagement_score", 0)

    return {
        "event_names": event_names,
        "has_used_core_feature": "first_core_feature_used" in event_names,
        "has_activation_milestone": "activation_milestone" in event_names,
        "days_since_last_session": days_since_last_session,
        "sessions_last_7_days": sessions_last_7_days,
        "activation_steps_completed": activation_steps,
        "hours_since_signup": hours_since_signup,
        "days_since_signup": days_since_signup,
        "engagement_score": engagement_score,
        "last_session": last_session,
    }


# ============================================================
# CORE: Evaluate one user's state
# ============================================================

def evaluate_user(user: dict, dry_run: bool = False) -> dict:
    """
    Given a user record from Supabase, determine if they
    should transition to a new state.

    Returns a dict describing what happened.
    """
    user_id       = user["id"]
    current_state = get_state_from_string(user["current_state"])
    user_name     = user.get("name", user_id[:8])

    print(f"\n👤 Evaluating: {user_name} [{current_state.value}]")

   
    events = get_user_events(user_id)
    print(f"  📊 Found {len(events)} events in PostHog")

    
    facts = analyse_events(events, user)

    print(f"  📋 Facts: last_session={facts['days_since_last_session']}d ago | "
          f"steps={facts['activation_steps_completed']}/3 | "
          f"score={facts['engagement_score']} | "
          f"sessions_7d={facts['sessions_last_7_days']}")

    # ── Apply transition rules ────────────────────────────
    

    new_state  = None
    trigger_ev = None

    if current_state == JourneyState.NEW_SIGNUP:
        if facts["has_used_core_feature"]:
            new_state  = JourneyState.ACTIVATING
            trigger_ev = "first_core_feature_used"
        elif facts["days_since_signup"] >= 30:
            new_state  = JourneyState.CHURNED
            trigger_ev = "inactivity_30d"

    elif current_state == JourneyState.ACTIVATING:
        if facts["has_activation_milestone"]:
            new_state  = JourneyState.ACTIVATED
            trigger_ev = "activation_milestone"
        elif facts["days_since_last_session"] >= 5:
            new_state  = JourneyState.CHURN_RISK
            trigger_ev = "inactivity_5d"

    elif current_state == JourneyState.ACTIVATED:
        if facts["sessions_last_7_days"] >= 3:
            new_state  = JourneyState.RETAINED
            trigger_ev = "consistent_sessions_7d"
        elif facts["days_since_last_session"] >= 7:
            new_state  = JourneyState.CHURN_RISK
            trigger_ev = "inactivity_7d"

    elif current_state == JourneyState.RETAINED:
        if facts["engagement_score"] > 80:
            new_state  = JourneyState.EXPANDING
            trigger_ev = "high_engagement_score"
        elif facts["days_since_last_session"] >= 7:
            new_state  = JourneyState.CHURN_RISK
            trigger_ev = "inactivity_7d"

    elif current_state == JourneyState.CHURN_RISK:
        if facts["days_since_last_session"] <= 1:
            new_state  = JourneyState.RETAINED
            trigger_ev = "session_after_absence"
        elif facts["days_since_last_session"] >= 30:
            new_state  = JourneyState.CHURNED
            trigger_ev = "inactivity_30d"

    elif current_state == JourneyState.CHURNED:
        if facts["days_since_last_session"] <= 1:
            new_state  = JourneyState.RETAINED
            trigger_ev = "reactivation"

    elif current_state == JourneyState.EXPANDING:
        if facts["engagement_score"] < 60:
            new_state  = JourneyState.RETAINED
            trigger_ev = "engagement_score_dropped"

   
    if new_state and new_state != current_state:
        result = transition_user_state(
            user_id=user_id,
            new_state=new_state,
            previous_state=current_state,
            trigger_event=trigger_ev,
            dry_run=dry_run
        )
        return {**result, "facts": facts}
    else:
        print(f"  ⏸️  No transition needed — stays in {current_state.value}")
        return {
            "success": True,
            "user_id": user_id,
            "from": current_state.value,
            "to": current_state.value,
            "changed": False,
            "facts": facts
        }


# ============================================================
# RUN: Evaluate all users
# ============================================================

def evaluate_all_users(dry_run: bool = False) -> list:
    """
    Fetch all users from Supabase and evaluate each one.
    This is called by GitHub Actions every hour.
    """
    print("=" * 60)
    print(f"🔄 STATE MACHINE EVALUATION — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    if dry_run:
        print("⚠️  DRY RUN MODE — no writes to database")
    print("=" * 60)

    
    result = supabase.table("users").select("*").execute()
    users = result.data

    print(f"📦 Found {len(users)} users to evaluate")

    results = []
    transitions_made = 0

    for user in users:
        result = evaluate_user(user, dry_run=dry_run)
        results.append(result)
        if result.get("from") != result.get("to"):
            transitions_made += 1

    print(f"\n{'=' * 60}")
    print(f"✅ Evaluation complete")
    print(f"   Total users:      {len(users)}")
    print(f"   Transitions made: {transitions_made}")
    print(f"   No change:        {len(users) - transitions_made}")
    print(f"{'=' * 60}")

    return results


if __name__ == "__main__":
    evaluate_all_users(dry_run=False)