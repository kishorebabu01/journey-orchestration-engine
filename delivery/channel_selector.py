"""
Channel selection logic — applies config/channel_rules.yml preferences
as a fallback when the LLM does not return a channel recommendation.
"""

import yaml
import os

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "channel_rules.yml"
)


def get_preferred_channel(journey_state: str) -> str:
    """Return the primary preferred channel for a given journey state."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    state_rules = rules.get("channel_preferences", {}).get(journey_state, {})
    return state_rules.get("primary", "email")