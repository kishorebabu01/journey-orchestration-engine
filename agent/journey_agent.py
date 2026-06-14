# ============================================================
# FILE: agent/journey_agent.py
# PURPOSE: Processes user journey triggers, retrieves
#          contextual knowledge, generates personalized
#          messages, and stores agent decisions.
# ============================================================

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

# Project modules
from agent.groq_client import call_llama
from agent.prompts import SYSTEM_PROMPT, build_message_prompt
from rag.retriever import retrieve, build_query_from_trigger, format_context

load_dotenv(override=True)

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


# ============================================================
# Trigger Management
# ============================================================

def get_unprocessed_triggers() -> list:
    """
    Retrieve all unprocessed journey triggers.

    Returns:
        List of trigger records awaiting processing.
    """
    result = supabase.table("journey_triggers").select(
        "*"
    ).eq(
        "processed", False
    ).execute()

    return result.data


# ============================================================
# User Retrieval
# ============================================================

def get_user(user_id: str) -> dict:
    """
    Retrieve a user's profile from Supabase.

    Args:
        user_id: Unique user identifier.

    Returns:
        User profile dictionary or None.
    """
    result = supabase.table("users").select(
        "*"
    ).eq(
        "id", user_id
    ).execute()

    return result.data[0] if result.data else None


# ============================================================
# Trigger Processing
# ============================================================

def process_trigger(trigger: dict) -> dict:
    """
    Process a single journey trigger.

    Workflow:
        1. Retrieve user profile
        2. Retrieve relevant knowledge using RAG
        3. Generate personalized content using LLM
        4. Persist agent decision and message records
        5. Mark trigger as processed

    Args:
        trigger: Trigger record from the database.

    Returns:
        Dictionary containing processing results.
    """

    trigger_id = trigger["id"]
    user_id = trigger["user_id"]
    trigger_type = trigger["trigger_type"]
    trigger_data = trigger["trigger_data"] or {}

    print(f"\n🤖 Processing trigger: {trigger_type}")
    print(f"   User: {user_id[:8]}...")

    # Retrieve user profile
    user = get_user(user_id)
    if not user:
        print(f"  ❌ User not found: {user_id}")
        return {"success": False, "error": "user_not_found"}

    user_name = user.get("name", "Student")
    journey_state = user.get("current_state", "NEW_SIGNUP")
    engagement_score = user.get("engagement_score", 0)
    acquisition_source = user.get("acquisition_source", "unknown")

    print(
        f"   Name: {user_name} | State: {journey_state} | "
        f"Score: {engagement_score}"
    )

    # Retrieve contextual knowledge using RAG
    print("  🔍 Searching knowledge base...")

    # Generate retrieval query
    query = build_query_from_trigger(
        trigger_type=trigger_type,
        journey_state=journey_state,
        trigger_data=trigger_data
    )

    # Retrieve relevant context
    chunks = retrieve(query, top_k=5)
    rag_context = format_context(chunks)

    print(f"  📚 Found {len(chunks)} relevant knowledge chunks")

    # Generate personalized content
    print("  🧠 Calling LLaMA 3.3 70B...")

    user_prompt = build_message_prompt(
        user_name=user_name,
        journey_state=journey_state,
        trigger_type=trigger_type,
        trigger_data=trigger_data,
        rag_context=rag_context,
        engagement_score=engagement_score,
        acquisition_source=acquisition_source
    )

    # Generate response using the configured LLM
    llm_response = call_llama(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt
    )

    if "error" in llm_response:
        print(f"  ❌ LLM error: {llm_response['error']}")
        return {"success": False, "error": llm_response["error"]}

    print("  ✅ Message generated!")
    print(
        f"  📱 Push: "
        f"{llm_response.get('push_notification', '')[:60]}..."
    )
    print(
        f"  📧 Subject: "
        f"{llm_response.get('email_subject', '')}"
    )
    print(
        f"  📺 Channel: "
        f"{llm_response.get('channel_recommendation', '')}"
    )
    print(
        f"  💭 Reasoning: "
        f"{llm_response.get('reasoning', '')[:80]}..."
    )

    # Persist agent decision
    print("  💾 Saving decision to Supabase...")

    # Store decision metadata for auditing and analysis
    decision_result = supabase.table("agent_decisions").insert({
        "trigger_id": trigger_id,
        "user_id": user_id,
        "rag_context": {
            "chunks": chunks,
            "query": query
        },
        "llm_prompt": user_prompt,
        "llm_response": llm_response,
        "channel_selected": llm_response.get(
            "channel_recommendation"
        ),
        "reasoning": llm_response.get("reasoning"),
        "created_at": datetime.now(
            timezone.utc
        ).isoformat()
    }).execute()

    decision_id = (
        decision_result.data[0]["id"]
        if decision_result.data
        else None
    )

    # Store generated message
    supabase.table("messages_sent").insert({
        "user_id": user_id,
        "agent_decision_id": decision_id,
        "channel": llm_response.get(
            "channel_recommendation",
            "email"
        ),
        "message_content": {
            "push_notification": llm_response.get(
                "push_notification"
            ),
            "email_subject": llm_response.get(
                "email_subject"
            ),
            "email_body": llm_response.get(
                "email_body"
            ),
            "in_app_tooltip": llm_response.get(
                "in_app_tooltip"
            ),
        },
        "sent_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "delivery_status": "pending"
    }).execute()

    # Mark trigger as processed
    supabase.table("journey_triggers").update({
        "processed": True,
        "agent_decision_id": decision_id
    }).eq(
        "id",
        trigger_id
    ).execute()

    print("  ✅ Trigger marked as processed")

    return {
        "success": True,
        "trigger_id": trigger_id,
        "user_name": user_name,
        "trigger_type": trigger_type,
        "channel": llm_response.get(
            "channel_recommendation"
        ),
        "decision_id": decision_id
    }


# ============================================================
# Agent Execution
# ============================================================

def run_agent():
    """
    Main execution entry point.

    Processes all pending journey triggers and records
    results in Supabase.

    Returns:
        List of processing results.
    """
    print("=" * 60)
    print(
        f"🤖 JOURNEY AI AGENT — "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    print("=" * 60)

    # Retrieve pending triggers
    triggers = get_unprocessed_triggers()

    print(
        f"📋 Found {len(triggers)} "
        f"unprocessed triggers"
    )

    if not triggers:
        print("✅ No triggers to process. All caught up!")
        return []

    results = []
    successful = 0

    for trigger in triggers:
        result = process_trigger(trigger)
        results.append(result)

        if result.get("success"):
            successful += 1

    print(f"\n{'=' * 60}")
    print("✅ AGENT RUN COMPLETE")
    print(
        f"   Processed: "
        f"{successful}/{len(triggers)} triggers"
    )
    print("   Review results in Supabase")
    print(f"{'=' * 60}")

    return results


if __name__ == "__main__":
    run_agent()