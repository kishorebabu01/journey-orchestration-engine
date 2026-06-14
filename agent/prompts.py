# ============================================================
# FILE: agent/prompts.py
# PURPOSE: Defines system prompts and prompt builders used
#          for personalized message generation.
# ============================================================


# ============================================================
# System Prompt Configuration
# ============================================================

SYSTEM_PROMPT = """You are an expert growth marketing AI for Focusly, a student productivity app.

Your job is to generate deeply personalised messages for users based on:
- Their journey state (where they are in their lifecycle)
- Their behaviour data (what they have and haven't done)
- Historical campaign performance (what worked before)
- Focusly's brand voice (warm, direct, achievement-focused)

BRAND VOICE RULES:
- Speak like a smart, encouraging study buddy
- Always use the user's first name
- Maximum 1 emoji per message, used purposefully
- Never use: "Don't forget", "You must", "Urgent!!!"
- Push notifications: maximum 100 characters
- Email subject lines: maximum 60 characters
- In-app tooltips: maximum 60 characters
- Email body: approximately 150-200 words

You ALWAYS respond in valid JSON format with NO extra text outside the JSON.
"""


# ============================================================
# Prompt Builder
# ============================================================

def build_message_prompt(
    user_name: str,
    journey_state: str,
    trigger_type: str,
    trigger_data: dict,
    rag_context: str,
    engagement_score: int,
    acquisition_source: str
) -> str:
    """
    Build a structured prompt for message generation.

    Args:
        user_name: Full user name.
        journey_state: Current lifecycle stage.
        trigger_type: Event that triggered the message.
        trigger_data: Additional trigger metadata.
        rag_context: Retrieved contextual knowledge.
        engagement_score: User engagement score.
        acquisition_source: User acquisition channel.

    Returns:
        Formatted prompt string for the language model.
    """

    # Extract first name for personalization
    first_name = user_name.split()[0] if user_name else "there"

    prompt = f"""Generate a personalised marketing message for this Focusly user.

USER PROFILE:
- Name: {user_name} (use first name: {first_name})
- Journey State: {journey_state}
- Trigger Type: {trigger_type}
- Trigger Data: {trigger_data}
- Engagement Score: {engagement_score}/100
- Acquisition Source: {acquisition_source}

RELEVANT CONTEXT FROM KNOWLEDGE BASE:
{rag_context}

TASK:
Based on the user profile and knowledge base context above,
generate a personalised message for this user.

Respond with ONLY this JSON structure, no other text:

{{
  "push_notification": "max 100 chars, compelling, personal",
  "email_subject": "max 60 chars, no clickbait",
  "email_body": "150-200 words, warm tone, use first name, clear CTA",
  "in_app_tooltip": "max 60 chars, action-oriented",
  "channel_recommendation": "push OR email OR in_app",
  "send_time_recommendation": "e.g. immediately, 9am local time, Tuesday morning",
  "message_style": "urgency OR social_proof OR achievement OR curiosity",
  "reasoning": "2-3 sentences explaining why this message and channel was chosen based on the data"
}}"""

    return prompt