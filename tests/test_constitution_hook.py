"""
Unit tests for the Intent Governance Layer.
Run with:  python -m pytest tests/ -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

# Ensure project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def constitution_path(tmp_path):
    """Write a test constitution and return its path."""
    rules = {
        "stripe_refund": [
            {
                "condition": "high_value",
                "threshold": 100,
                "action": "reject",
                "reason": "Only enterprise accounts can auto-refund >= $100.",
            },
            {
                "condition": "any",
                "action": "approve",
                "reason": "Standard refund approved.",
            },
        ],
        "send_email": [
            {
                "condition": "any",
                "action": "approve",
                "reason": "Email is low-risk.",
            },
        ],
    }
    path = tmp_path / "test_constitution.yaml"
    path.write_text(yaml.dump(rules), encoding="utf-8")
    return path


@pytest.fixture
def mock_run_context_standard():
    """RunContext stub with customer_tier=standard."""
    ctx = MagicMock()
    ctx.session_state = {"customer_tier": "standard"}
    return ctx


@pytest.fixture
def mock_run_context_enterprise():
    """RunContext stub with customer_tier=enterprise."""
    ctx = MagicMock()
    ctx.session_state = {"customer_tier": "enterprise"}
    return ctx


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 1 — Constitution Hook
# ═══════════════════════════════════════════════════════════════════════════════

class TestConstitutionHook:
    """Test the constitution hook factory."""

    def test_reject_high_value_standard_user(
        self, constitution_path, mock_run_context_standard
    ):
        from hooks.constitution_hook import create_constitution_hook

        hook = create_constitution_hook(constitution_path)
        mock_fn = MagicMock(return_value="ok")

        with pytest.raises(ValueError, match="Intent Block"):
            hook(
                run_context=mock_run_context_standard,
                function_name="stripe_refund",
                function_call=mock_fn,
                arguments={"customer_id": "C-1", "amount": 500},
            )
        mock_fn.assert_not_called()

    def test_approve_high_value_enterprise_user(
        self, constitution_path, mock_run_context_enterprise
    ):
        from hooks.constitution_hook import create_constitution_hook

        hook = create_constitution_hook(constitution_path)
        mock_fn = MagicMock(return_value="refund_ok")

        result = hook(
            run_context=mock_run_context_enterprise,
            function_name="stripe_refund",
            function_call=mock_fn,
            arguments={"customer_id": "C-1", "amount": 500},
        )
        assert result == "refund_ok"
        mock_fn.assert_called_once()

    def test_approve_low_value_standard_user(
        self, constitution_path, mock_run_context_standard
    ):
        from hooks.constitution_hook import create_constitution_hook

        hook = create_constitution_hook(constitution_path)
        mock_fn = MagicMock(return_value="small_refund_ok")

        result = hook(
            run_context=mock_run_context_standard,
            function_name="stripe_refund",
            function_call=mock_fn,
            arguments={"customer_id": "C-1", "amount": 50},
        )
        assert result == "small_refund_ok"
        mock_fn.assert_called_once()

    def test_approve_unknown_tool(
        self, constitution_path, mock_run_context_standard
    ):
        from hooks.constitution_hook import create_constitution_hook

        hook = create_constitution_hook(constitution_path)
        mock_fn = MagicMock(return_value="unknown_ok")

        result = hook(
            run_context=mock_run_context_standard,
            function_name="unknown_tool",
            function_call=mock_fn,
            arguments={},
        )
        assert result == "unknown_ok"
        mock_fn.assert_called_once()

    def test_approve_email(
        self, constitution_path, mock_run_context_standard
    ):
        from hooks.constitution_hook import create_constitution_hook

        hook = create_constitution_hook(constitution_path)
        mock_fn = MagicMock(return_value="email_sent")

        result = hook(
            run_context=mock_run_context_standard,
            function_name="send_email",
            function_call=mock_fn,
            arguments={"to": "a@b.com", "subject": "Hi", "body": "Hello"},
        )
        assert result == "email_sent"
        mock_fn.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# Layer 3 — Intent Retriever
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntentRetriever:
    """Test dynamic instruction generation."""

    def test_retention_strategy(self):
        from intent.retriever import create_intent_retriever

        retriever = create_intent_retriever(base_intent="Base.")
        result = retriever({"org_goal": "retention", "customer_tier": "standard"})

        assert "Base." in result
        assert "retention" in result.lower()
        assert "standard" in result

    def test_cost_reduction_strategy(self):
        from intent.retriever import create_intent_retriever

        retriever = create_intent_retriever(base_intent="Base.")
        result = retriever({"org_goal": "cost_reduction", "customer_tier": "enterprise"})

        assert "store credit" in result.lower()
        assert "enterprise" in result

    def test_no_strategy(self):
        from intent.retriever import create_intent_retriever

        retriever = create_intent_retriever(base_intent="Base.")
        result = retriever({"customer_tier": "standard"})

        assert result.startswith("Base.")
        assert "PRIORITY" not in result

    def test_custom_strategy_override(self):
        from intent.retriever import create_intent_retriever

        retriever = create_intent_retriever(
            base_intent="Base.",
            strategy_overrides={"custom_mode": "\nCUSTOM INSTRUCTIONS HERE."},
        )
        result = retriever({"org_goal": "custom_mode", "customer_tier": "standard"})

        assert "CUSTOM INSTRUCTIONS HERE" in result
