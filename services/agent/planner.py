"""Conversation Planner for AURA Stylist.

Evaluates the current state, transcript, and intent to define the strategic goal
for the current conversation turn before retrieving knowledge or reasoning.
"""

from typing import Any
from services.agent.master import classify_intent

class PlanGoal:
    GATHER_REQUIREMENTS = "GATHER_REQUIREMENTS"
    RESOLVE_MEASUREMENTS = "RESOLVE_MEASUREMENTS"
    PROPOSE_OUTFIT = "PROPOSE_OUTFIT"
    REFINE_OUTFIT = "REFINE_OUTFIT"
    FINALIZE = "FINALIZE"
    GENERAL_CHAT = "GENERAL_CHAT"


def plan_next_step(transcript: str, session_stage: str, spec_is_complete: bool, has_validation_errors: bool) -> dict[str, Any]:
    """Determine the next step in the conversation flow."""
    intent = classify_intent(transcript)
    
    # 1. If there are bad measurements, top priority is resolving them
    if has_validation_errors:
        goal = PlanGoal.RESOLVE_MEASUREMENTS
    # 2. Check explicit finalize intent
    elif intent in ("product_search", "tailoring") or session_stage == "finalized":
        goal = PlanGoal.FINALIZE
    # 3. If they are talking fashion but spec is incomplete
    elif intent == "design_request":
        if not spec_is_complete:
            goal = PlanGoal.GATHER_REQUIREMENTS
        else:
            goal = PlanGoal.PROPOSE_OUTFIT
    # 4. Refinement during active proposing
    elif session_stage == "refining":
        if not spec_is_complete:
            goal = PlanGoal.GATHER_REQUIREMENTS
        else:
            goal = PlanGoal.REFINE_OUTFIT
    # 5. Fallback
    else:
        goal = PlanGoal.GENERAL_CHAT
        
    return {
        "intent": intent,
        "goal": goal,
        "action_required": goal in (PlanGoal.GATHER_REQUIREMENTS, PlanGoal.RESOLVE_MEASUREMENTS)
    }
