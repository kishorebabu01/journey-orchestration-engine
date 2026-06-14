# ============================================================
# FILE: delivery/n8n_webhook.py
# PURPOSE: Sends AI-generated messages to n8n workflows
#          for channel-specific delivery.
# ============================================================

import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

# n8n webhook endpoint
N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/journey-delivery"
)


def deliver_message(agent_decision: dict, user: dict) -> dict:
    """
    Send a generated message to n8n for delivery.

    Args:
        agent_decision: Stored agent decision record.
        user: User profile information.

    Returns:
        Dictionary containing delivery status.
    """

    llm_response = agent_decision.get("llm_response", {})
    channel = agent_decision.get("channel_selected", "email")

    message_content = {
        "push_notification": llm_response.get(
            "push_notification", ""
        ),
        "email_subject": llm_response.get(
            "email_subject", ""
        ),
        "email_body": llm_response.get(
            "email_body", ""
        ),
        "in_app_tooltip": llm_response.get(
            "in_app_tooltip", ""
        ),
    }

    payload = {
        "user_id": user["id"],
        "user_email": user["email"],
        "user_name": user.get("name", "Student"),
        "channel": channel,
        "message_content": message_content,
        "trigger_type": agent_decision.get(
            "trigger_type", ""
        ),
        "journey_state": user.get(
            "current_state", ""
        ),
        "sent_at": datetime.now(
            timezone.utc
        ).isoformat()
    }

    print(
        f"  📤 Sending to n8n: "
        f"{channel} for {user.get('name')}"
    )

    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            print("  ✅ n8n accepted delivery")

            supabase.table("messages_sent").update({
                "delivery_status": "delivered"
            }).eq(
                "agent_decision_id",
                agent_decision["id"]
            ).execute()

            return {
                "success": True,
                "channel": channel
            }

        print(
            f"  ❌ n8n rejected: "
            f"{response.status_code}"
        )

        return {
            "success": False,
            "error": response.text
        }

    except Exception as e:
        print(f"  ❌ Delivery error: {e}")

        return {
            "success": False,
            "error": str(e)
        }


def deliver_all_pending() -> list:
    """
    Deliver all pending messages queued for dispatch.

    Returns:
        List containing delivery results.
    """

    print("=" * 60)
    print(
        f"📤 DELIVERY LAYER — "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    print("=" * 60)

    # Retrieve pending messages
    messages = supabase.table(
        "messages_sent"
    ).select(
        "*, agent_decisions(*)"
    ).eq(
        "delivery_status",
        "pending"
    ).execute()

    print(
        f"📋 Found "
        f"{len(messages.data)} pending messages"
    )

    results = []

    for msg in messages.data:
        decision = msg.get(
            "agent_decisions"
        ) or {}

        user_id = msg.get("user_id")

        user_result = supabase.table(
            "users"
        ).select(
            "*"
        ).eq(
            "id",
            user_id
        ).execute()

        if not user_result.data:
            continue

        user = user_result.data[0]

        # Attach decision identifier for status updates
        decision["id"] = msg.get(
            "agent_decision_id"
        )

        result = deliver_message(
            decision,
            user
        )

        results.append(result)

    successful = sum(
        1 for r in results
        if r.get("success")
    )

    print(
        f"\n✅ Delivered: "
        f"{successful}/{len(results)} messages"
    )

    return results


if __name__ == "__main__":
    deliver_all_pending()