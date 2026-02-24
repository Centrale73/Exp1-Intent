"""
Layer 3 — Dynamic Intent Retriever (Callable Instructions)
==========================================================
Replaces a static system prompt with a *live* strategic-context function.
The Agno pattern: pass a callable to ``instructions=`` instead of a string.

The retriever reads ``org_goal`` and ``customer_tier`` from the agent's
session state and returns tailored behavioural instructions — no
redeployment required to shift strategy.
"""

import logging
from typing import Callable, Dict, Optional

logger = logging.getLogger("intent_governance.intent")


# ── built-in strategy overrides ──────────────────────────────────────────────

DEFAULT_STRATEGIES: Dict[str, str] = {
    "retention": (
        "\nPRIORITY: This quarter is retention-focused. "
        "Be lenient with long-term users. Never deny a refund request "
        "from users with >2 yr tenure without escalating first. "
        "Offer loyalty discounts proactively."
    ),
    "cost_reduction": (
        "\nPRIORITY: Minimise refund approvals. "
        "Offer store credit or service extensions as alternatives first. "
        "Only approve cash refunds when the customer explicitly insists "
        "after being presented with alternatives."
    ),
    "growth": (
        "\nPRIORITY: Maximise upsell opportunities. "
        "Highlight premium features during every interaction. "
        "When resolving an issue, mention how upgrading would have "
        "prevented it."
    ),
}


# ── factory ──────────────────────────────────────────────────────────────────

def create_intent_retriever(
    base_intent: str = "You are a support agent for Acme Corp.",
    strategy_overrides: Optional[Dict[str, str]] = None,
) -> Callable[[dict], str]:
    """
    Return a callable ``(session_state: dict) -> str`` suitable for
    Agno's ``Agent(instructions=...)`` parameter.

    Parameters
    ----------
    base_intent : str
        The default system prompt injected on every turn.
    strategy_overrides : dict, optional
        Mapping of ``org_goal`` values to instruction suffixes.
        Merged on top of ``DEFAULT_STRATEGIES``.

    Returns
    -------
    Callable[[dict], str]
    """
    strategies = {**DEFAULT_STRATEGIES, **(strategy_overrides or {})}

    def intent_retriever(session_state: dict) -> str:
        org_goal = session_state.get("org_goal", "")
        customer_tier = session_state.get("customer_tier", "standard")

        instructions = base_intent

        # Inject tier awareness
        instructions += f"\n\nThe current customer's tier is: {customer_tier}."

        # Inject quarterly strategy
        strategy_suffix = strategies.get(org_goal, "")
        if strategy_suffix:
            instructions += strategy_suffix
            logger.info(
                "[INTENT RETRIEVER] org_goal=%s, tier=%s — strategy injected.",
                org_goal,
                customer_tier,
            )
        else:
            logger.info(
                "[INTENT RETRIEVER] org_goal=%s (no override), tier=%s.",
                org_goal,
                customer_tier,
            )

        return instructions

    return intent_retriever
