"""
Layer 1 — Constitution Hook & Audit Logger
==========================================
Intercepts tool calls *before* execution and evaluates them against a
YAML-based constitution file.  Also provides a timing logger hook for
full audit traceability.

Hooks are designed to be stacked via Agno's ``tool_hooks`` list — the
logger wraps the outer layer, the constitution wraps the inner layer.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import yaml
from agno.run import RunContext

logger = logging.getLogger("intent_governance.hooks")


# ── helpers ──────────────────────────────────────────────────────────────────

def _load_constitution(path: str | Path) -> dict:
    """Load and cache-parse a constitution YAML file."""
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _evaluate_condition(
    condition: str,
    session_state: dict,
    arguments: Dict[str, Any],
    threshold: Optional[float] = None,
) -> bool:
    """Return True if the business condition is met (i.e. the rule fires)."""

    if condition == "any":
        return True

    if condition == "high_value":
        amount = arguments.get("amount", 0)
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = 0
        return amount >= (threshold or 100)

    if condition == "high_tenure":
        tenure_days = session_state.get("customer_tenure_days", 0)
        return tenure_days >= (threshold or 730)

    # Unknown condition — don't block
    logger.warning("Unknown constitution condition '%s'; defaulting to no-match.", condition)
    return False


# ── constitution hook ────────────────────────────────────────────────────────

def create_constitution_hook(constitution_path: str | Path):
    """
    Factory that returns a tool-hook function bound to a specific
    constitution file.

    The returned hook signature matches Agno's tool_hooks contract:
        (run_context, function_name, function_call, arguments) -> result
    """
    constitution_path = Path(constitution_path)

    def intent_constitution_hook(
        run_context: RunContext,
        function_name: str,
        function_call: Callable,
        arguments: Dict[str, Any],
    ):
        constitution = _load_constitution(constitution_path)
        rules = constitution.get(function_name, [])

        session_state = run_context.session_state or {}
        customer_tier = session_state.get("customer_tier", "standard")

        for rule in rules:
            condition = rule.get("condition", "any")
            action = rule.get("action", "approve")
            reason = rule.get("reason", "")
            threshold = rule.get("threshold")

            matched = _evaluate_condition(condition, session_state, arguments, threshold)
            if not matched:
                continue

            if action == "reject" and customer_tier != "enterprise":
                logger.info(
                    "[CONSTITUTION REJECT] %s — %s (tier=%s)",
                    function_name, reason, customer_tier,
                )
                raise ValueError(
                    f"[Intent Block] {function_name} denied: {reason}"
                )

            if action == "escalate":
                logger.warning(
                    "[CONSTITUTION ESCALATE] %s — %s (tier=%s)",
                    function_name, reason, customer_tier,
                )
                raise ValueError(
                    f"[Intent Escalation] {function_name} requires human review: {reason}"
                )

            if action == "approve":
                logger.info(
                    "[CONSTITUTION APPROVE] %s — %s", function_name, reason,
                )
                break  # first matching approve → proceed

        return function_call(**arguments)

    return intent_constitution_hook


# ── audit logger hook ────────────────────────────────────────────────────────

def logger_hook(
    function_name: str,
    function_call: Callable,
    arguments: Dict[str, Any],
):
    """
    Timing / audit logger that wraps around any other hook.
    Logs function name, sanitised arguments, and wall-clock duration.
    """
    sanitised_args = {
        k: (v if k not in ("password", "token", "secret") else "***")
        for k, v in arguments.items()
    }
    logger.info(
        "[AUDIT START] %s | args=%s",
        function_name,
        json.dumps(sanitised_args, default=str),
    )

    start = time.perf_counter()
    result = function_call(**arguments)
    elapsed = time.perf_counter() - start

    logger.info(
        "[AUDIT END]   %s | %.3fs",
        function_name,
        elapsed,
    )
    return result
