# ============================================================
# FILE: state_machine/states.py
# PURPOSE: Defines journey states, metadata, and transition
#          rules used by the user lifecycle state machine.
# ============================================================

from enum import Enum


# ============================================================
# Journey States
# ============================================================

class JourneyState(Enum):
    """
    Supported user lifecycle states.
    """

    NEW_SIGNUP = "NEW_SIGNUP"
    ACTIVATING = "ACTIVATING"
    ACTIVATED = "ACTIVATED"
    RETAINED = "RETAINED"
    CHURN_RISK = "CHURN_RISK"
    CHURNED = "CHURNED"
    EXPANDING = "EXPANDING"


# ============================================================
# State Metadata
# ============================================================

STATE_METADATA = {
    JourneyState.NEW_SIGNUP: {
        "description": "Just signed up, hasn't used core feature",
        "priority": 2,
        "color": "#3B82F6",
        "intervention_urgency": "medium",
    },
    JourneyState.ACTIVATING: {
        "description": "Using features but not yet fully activated",
        "priority": 2,
        "color": "#F59E0B",
        "intervention_urgency": "medium",
    },
    JourneyState.ACTIVATED: {
        "description": "Completed all activation steps",
        "priority": 3,
        "color": "#10B981",
        "intervention_urgency": "low",
    },
    JourneyState.RETAINED: {
        "description": "Actively engaged with regular usage",
        "priority": 3,
        "color": "#6366F1",
        "intervention_urgency": "low",
    },
    JourneyState.CHURN_RISK: {
        "description": "Previously active user showing signs of disengagement",
        "priority": 1,
        "color": "#F97316",
        "intervention_urgency": "high",
    },
    JourneyState.CHURNED: {
        "description": "Inactive user requiring reactivation efforts",
        "priority": 1,
        "color": "#EF4444",
        "intervention_urgency": "high",
    },
    JourneyState.EXPANDING: {
        "description": "Highly engaged user with growth potential",
        "priority": 2,
        "color": "#8B5CF6",
        "intervention_urgency": "medium",
    },
}


# ============================================================
# Valid State Transitions
# ============================================================

VALID_TRANSITIONS = {
    JourneyState.NEW_SIGNUP: [
        JourneyState.ACTIVATING,
        JourneyState.CHURNED,
    ],
    JourneyState.ACTIVATING: [
        JourneyState.ACTIVATED,
        JourneyState.CHURN_RISK,
    ],
    JourneyState.ACTIVATED: [
        JourneyState.RETAINED,
        JourneyState.CHURN_RISK,
    ],
    JourneyState.RETAINED: [
        JourneyState.CHURN_RISK,
        JourneyState.EXPANDING,
    ],
    JourneyState.CHURN_RISK: [
        JourneyState.RETAINED,
        JourneyState.CHURNED,
    ],
    JourneyState.CHURNED: [
        JourneyState.RETAINED,
    ],
    JourneyState.EXPANDING: [
        JourneyState.RETAINED,
    ],
}


def is_valid_transition(
    from_state: JourneyState,
    to_state: JourneyState
) -> bool:
    """
    Validate whether a state transition is allowed.

    Args:
        from_state: Current journey state.
        to_state: Target journey state.

    Returns:
        True if the transition is allowed, otherwise False.
    """
    allowed = VALID_TRANSITIONS.get(
        from_state,
        []
    )

    return to_state in allowed


def get_state_from_string(
    state_str: str
) -> JourneyState:
    """
    Convert a string value to a JourneyState enum.

    Args:
        state_str: State name stored in persistence.

    Returns:
        Matching JourneyState enum value.

    Raises:
        ValueError: If the provided state is invalid.
    """
    try:
        return JourneyState(state_str)

    except ValueError:
        raise ValueError(
            f"'{state_str}' is not a valid journey state. "
            f"Valid states: "
            f"{[s.value for s in JourneyState]}"
        )