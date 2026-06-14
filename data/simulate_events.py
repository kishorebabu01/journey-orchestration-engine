# ============================================================
# FILE: data/simulate_events.py
# PURPOSE: Generate realistic simulated user events in PostHog
#          and create matching user records in Supabase
# PHASE 1, STEP 3 — UPDATED with correct PostHog client syntax
# ============================================================

import os
import sys
import random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(override=True)


from posthog import Posthog

ph = Posthog(
    project_api_key=os.getenv("POSTHOG_API_KEY").strip(),
    host=os.getenv("POSTHOG_HOST", "https://us.posthog.com").strip()
)


from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

print("✅ Connected to PostHog and Supabase")



def days_ago(days, hours=0, minutes=0):
    """Returns a UTC datetime N days/hours/minutes ago."""
    return datetime.now(timezone.utc) - timedelta(
        days=days, hours=hours, minutes=minutes
    )


def send_event(distinct_id, event_name, properties, timestamp=None):
    """Send a single event to PostHog with an optional backdated timestamp."""
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    ph.capture(
        distinct_id=distinct_id,
        event=event_name,
        properties=properties,
        timestamp=timestamp
    )
    print(f"  📡 {event_name} → {distinct_id[:8]}...")


def create_user_in_supabase(user_data):
    """Upsert a user record into Supabase (insert or skip if exists)."""
    try:
        result = supabase.table("users").upsert(
            user_data, on_conflict="email"
        ).execute()
        print(f"  💾 Supabase upsert: {user_data['email']}")
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"  ❌ Supabase error for {user_data['email']}: {e}")
        return None

# ============================================================
# 10 SIMULATED USERS — one per journey scenario
# ============================================================

SIMULATED_USERS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "email": "alice@focusly-demo.com",
        "name": "Alice Chen",
        "acquisition_source": "google_ads",
        "scenario": "new_signup_no_action",
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "email": "ben@focusly-demo.com",
        "name": "Ben Okafor",
        "acquisition_source": "referral",
        "scenario": "activating_in_progress",
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "email": "chloe@focusly-demo.com",
        "name": "Chloe Martinez",
        "acquisition_source": "organic_search",
        "scenario": "just_activated",
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "email": "david@focusly-demo.com",
        "name": "David Kim",
        "acquisition_source": "google_ads",
        "scenario": "retained_power_user",
    },
    {
        "id": "55555555-5555-5555-5555-555555555555",
        "email": "emma@focusly-demo.com",
        "name": "Emma Williams",
        "acquisition_source": "paid_social",
        "scenario": "churn_risk_day7",
    },
    {
        "id": "66666666-6666-6666-6666-666666666666",
        "email": "felix@focusly-demo.com",
        "name": "Felix Dubois",
        "acquisition_source": "organic_search",
        "scenario": "churned_user",
    },
    {
        "id": "77777777-7777-7777-7777-777777777777",
        "email": "grace@focusly-demo.com",
        "name": "Grace Patel",
        "acquisition_source": "referral",
        "scenario": "retained_steady",
    },
    {
        "id": "88888888-8888-8888-8888-888888888888",
        "email": "hassan@focusly-demo.com",
        "name": "Hassan Ali",
        "acquisition_source": "google_ads",
        "scenario": "activating_almost_there",
    },
    {
        "id": "99999999-9999-9999-9999-999999999999",
        "email": "isabella@focusly-demo.com",
        "name": "Isabella Rossi",
        "acquisition_source": "paid_social",
        "scenario": "new_signup_72h_no_action",
    },
    {
        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "email": "james@focusly-demo.com",
        "name": "James O'Brien",
        "acquisition_source": "organic_search",
        "scenario": "churn_risk_day14",
    },
]

# ============================================================
# SCENARIO FUNCTIONS
# Each returns a dict with current_state + engagement_score
# ============================================================

def simulate_new_signup_no_action(user):
    print(f"\n🎬 {user['name']} — NEW_SIGNUP (no action 24h)")
    send_event(user["id"], "signup_completed", {
        "user_id": user["id"], "email": user["email"],
        "name": user["name"],
        "acquisition_source": user["acquisition_source"],
        "plan": "free"
    }, days_ago(1, hours=2))
    return {"current_state": "NEW_SIGNUP", "engagement_score": 0,
            "signup_date": days_ago(1, hours=2).isoformat()}


def simulate_activating_in_progress(user):
    print(f"\n🎬 {user['name']} — ACTIVATING (1/3 steps)")
    send_event(user["id"], "signup_completed", {
        "user_id": user["id"], "email": user["email"],
        "name": user["name"],
        "acquisition_source": user["acquisition_source"],
        "plan": "free"
    }, days_ago(3))
    send_event(user["id"], "first_core_feature_used", {
        "user_id": user["id"], "feature_name": "focus_timer",
        "session_duration_minutes": 25,
        "activation_steps_completed": 1, "activation_steps_total": 3
    }, days_ago(2, hours=5))
    send_event(user["id"], "focus_timer_completed", {
        "user_id": user["id"], "duration_minutes": 25,
        "task_name": "Maths revision"
    }, days_ago(2, hours=4, minutes=35))
    return {"current_state": "ACTIVATING", "engagement_score": 15,
            "signup_date": days_ago(3).isoformat()}


def simulate_just_activated(user):
    print(f"\n🎬 {user['name']} — ACTIVATED (just hit milestone)")
    send_event(user["id"], "signup_completed", {
        "user_id": user["id"], "email": user["email"],
        "name": user["name"],
        "acquisition_source": user["acquisition_source"],
        "plan": "free"
    }, days_ago(5))
    send_event(user["id"], "first_core_feature_used", {
        "user_id": user["id"], "feature_name": "focus_timer",
        "activation_steps_completed": 1, "activation_steps_total": 3
    }, days_ago(4))
    send_event(user["id"], "task_added", {
        "user_id": user["id"], "task_count": 3,
        "activation_steps_completed": 2
    }, days_ago(2))
    send_event(user["id"], "activation_milestone", {
        "user_id": user["id"],
        "milestone_name": "full_activation",
        "activation_steps_completed": 3,
        "activation_steps_total": 3,
        "days_to_activate": 5
    }, days_ago(0, hours=3))
    return {"current_state": "ACTIVATED", "engagement_score": 35,
            "signup_date": days_ago(5).isoformat()}


def simulate_retained_power_user(user):
    print(f"\n🎬 {user['name']} — EXPANDING (power user, score 87)")
    send_event(user["id"], "signup_completed", {
        "user_id": user["id"], "email": user["email"],
        "name": user["name"],
        "acquisition_source": user["acquisition_source"],
        "plan": "free"
    }, days_ago(30))
    for day in range(20, 0, -1):
        send_event(user["id"], "app_session_started", {
            "user_id": user["id"],
            "session_number": 21 - day,
            "day_streak": 21 - day
        }, days_ago(day, hours=random.randint(8, 20)))
        send_event(user["id"], "focus_timer_completed", {
            "user_id": user["id"],
            "duration_minutes": random.choice([25, 50, 90])
        }, days_ago(day, hours=random.randint(9, 21)))
    send_event(user["id"], "high_engagement_score", {
        "user_id": user["id"], "engagement_score": 87,
        "streak_days": 20, "total_focus_minutes": 2400
    }, days_ago(1))
    return {"current_state": "EXPANDING", "engagement_score": 87,
            "signup_date": days_ago(30).isoformat()}


def simulate_churn_risk_day7(user):
    print(f"\n🎬 {user['name']} — CHURN_RISK (day 7)")
    send_event(user["id"], "signup_completed", {
        "user_id": user["id"], "email": user["email"],
        "name": user["name"],
        "acquisition_source": user["acquisition_source"],
        "plan": "free"
    }, days_ago(25))
    for day in range(17, 8, -1):
        send_event(user["id"], "app_session_started",
                   {"user_id": user["id"]}, days_ago(day))
    send_event(user["id"], "app_session_started", {
        "user_id": user["id"], "note": "last_session_before_churn"
    }, days_ago(8))
    return {"current_state": "CHURN_RISK", "engagement_score": 22,
            "signup_date": days_ago(25).isoformat()}


def simulate_churned_user(user):
    print(f"\n🎬 {user['name']} — CHURNED (35 days inactive)")
    send_event(user["id"], "signup_completed", {
        "user_id": user["id"], "email": user["email"],
        "name": user["name"],
        "acquisition_source": user["acquisition_source"],
        "plan": "free"
    }, days_ago(60))
    for day in range(55, 35, -5):
        send_event(user["id"], "app_session_started",
                   {"user_id": user["id"]}, days_ago(day))
    send_event(user["id"], "app_session_started", {
        "user_id": user["id"], "note": "final_session"
    }, days_ago(35))
    return {"current_state": "CHURNED", "engagement_score": 0,
            "signup_date": days_ago(60).isoformat()}


def simulate_retained_steady(user):
    print(f"\n🎬 {user['name']} — RETAINED (steady, score 72)")
    send_event(user["id"], "signup_completed", {
        "user_id": user["id"], "email": user["email"],
        "name": user["name"],
        "acquisition_source": user["acquisition_source"],
        "plan": "free"
    }, days_ago(21))
    for day in [20, 18, 16, 14, 12, 10, 8, 6, 4, 3, 1]:
        send_event(user["id"], "app_session_started",
                   {"user_id": user["id"]}, days_ago(day))
        send_event(user["id"], "focus_timer_completed", {
            "user_id": user["id"], "duration_minutes": 25
        }, days_ago(day, hours=1))
    return {"current_state": "RETAINED", "engagement_score": 72,
            "signup_date": days_ago(21).isoformat()}


def simulate_activating_almost_there(user):
    print(f"\n🎬 {user['name']} — ACTIVATING (2/3 steps)")
    send_event(user["id"], "signup_completed", {
        "user_id": user["id"], "email": user["email"],
        "name": user["name"],
        "acquisition_source": user["acquisition_source"],
        "plan": "free"
    }, days_ago(4))
    send_event(user["id"], "first_core_feature_used", {
        "user_id": user["id"], "feature_name": "focus_timer",
        "activation_steps_completed": 1
    }, days_ago(3))
    send_event(user["id"], "task_added", {
        "user_id": user["id"],
        "activation_steps_completed": 2, "activation_steps_total": 3
    }, days_ago(2))
    return {"current_state": "ACTIVATING", "engagement_score": 20,
            "signup_date": days_ago(4).isoformat()}


def simulate_new_signup_72h(user):
    print(f"\n🎬 {user['name']} — NEW_SIGNUP (72h no action)")
    send_event(user["id"], "signup_completed", {
        "user_id": user["id"], "email": user["email"],
        "name": user["name"],
        "acquisition_source": user["acquisition_source"],
        "plan": "free"
    }, days_ago(4))
    return {"current_state": "NEW_SIGNUP", "engagement_score": 0,
            "signup_date": days_ago(4).isoformat()}


def simulate_churn_risk_day14(user):
    print(f"\n🎬 {user['name']} — CHURN_RISK (day 14)")
    send_event(user["id"], "signup_completed", {
        "user_id": user["id"], "email": user["email"],
        "name": user["name"],
        "acquisition_source": user["acquisition_source"],
        "plan": "free"
    }, days_ago(45))
    for day in range(40, 15, -3):
        send_event(user["id"], "app_session_started",
                   {"user_id": user["id"]}, days_ago(day))
    send_event(user["id"], "app_session_started", {
        "user_id": user["id"], "note": "last_session"
    }, days_ago(15))
    return {"current_state": "CHURN_RISK", "engagement_score": 14,
            "signup_date": days_ago(45).isoformat()}


# ============================================================
# SCENARIO ROUTER
# ============================================================

SCENARIO_MAP = {
    "new_signup_no_action":       simulate_new_signup_no_action,
    "activating_in_progress":     simulate_activating_in_progress,
    "just_activated":             simulate_just_activated,
    "retained_power_user":        simulate_retained_power_user,
    "churn_risk_day7":            simulate_churn_risk_day7,
    "churned_user":               simulate_churned_user,
    "retained_steady":            simulate_retained_steady,
    "activating_almost_there":    simulate_activating_almost_there,
    "new_signup_72h_no_action":   simulate_new_signup_72h,
    "churn_risk_day14":           simulate_churn_risk_day14,
}

# ============================================================
# MAIN
# ============================================================

def run_all_simulations():
    print("=" * 60)
    print("🚀 FOCUSLY USER SIMULATION — PROJECT 5")
    print("=" * 60)

    results = []

    for user in SIMULATED_USERS:
        fn = SCENARIO_MAP[user["scenario"]]
        state_data = fn(user)

        create_user_in_supabase({
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "acquisition_source": user["acquisition_source"],
            "signup_date": state_data["signup_date"],
            "current_state": state_data["current_state"],
            "engagement_score": state_data["engagement_score"],
            "state_updated_at": datetime.now(timezone.utc).isoformat(),
        })

        results.append({
            "name": user["name"],
            "state": state_data["current_state"],
            "score": state_data["engagement_score"],
        })

    
    ph.shutdown()

    print("\n" + "=" * 60)
    print("✅ SIMULATION COMPLETE")
    print("=" * 60)
    print(f"{'Name':<20} {'State':<15} {'Score':>5}")
    print("-" * 42)
    for r in results:
        print(f"{r['name']:<20} {r['state']:<15} {r['score']:>5}")

    print("\n📡 All events sent to PostHog")
    print("💾 All users upserted in Supabase")
    print("🎯 Next: Run the state machine (Step 4)")


if __name__ == "__main__":
    run_all_simulations()