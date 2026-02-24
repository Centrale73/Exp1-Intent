"""
Layer 4 — Demo Tools
====================
Example tools that exercise every governance layer:

- ``stripe_refund``          — governed by constitution (high_value condition)
- ``send_email``             — low-risk, auto-approved
- ``cancel_subscription``    — governed by constitution (high_tenure condition)
- ``process_chargeback``     — ``requires_confirmation=True`` → human gate
"""

import logging
from agno.tools import tool

logger = logging.getLogger("intent_governance.tools")


# ── standard tools (governed by constitution hook) ───────────────────────────

@tool
def stripe_refund(customer_id: str, amount: float) -> str:
    """
    Process a refund for a customer via Stripe.

    Args:
        customer_id: The unique customer identifier.
        amount: Dollar amount to refund.

    Returns:
        Confirmation message with the refund details.
    """
    logger.info("stripe_refund executed: customer=%s amount=%.2f", customer_id, amount)
    return (
        f"✅ Refund of ${amount:.2f} processed for customer {customer_id}. "
        f"Stripe transaction ID: txn_sim_{customer_id[-4:]}_{int(amount*100)}"
    )


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email to a customer.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body text.

    Returns:
        Confirmation that the email was sent.
    """
    logger.info("send_email executed: to=%s subject=%s", to, subject)
    return f"✅ Email sent to {to} — subject: '{subject}'"


@tool
def cancel_subscription(customer_id: str) -> str:
    """
    Cancel a customer's subscription.

    Args:
        customer_id: The unique customer identifier.

    Returns:
        Confirmation message.
    """
    logger.info("cancel_subscription executed: customer=%s", customer_id)
    return f"✅ Subscription cancelled for customer {customer_id}."


# ── human-gated tool (requires_confirmation) ─────────────────────────────────

@tool(requires_confirmation=True)
def process_chargeback(customer_id: str, amount: float) -> str:
    """
    Process a full chargeback. This action is irreversible and requires
    human approval before execution.

    Args:
        customer_id: The unique customer identifier.
        amount: Dollar amount of the chargeback.

    Returns:
        Confirmation message.
    """
    logger.info(
        "process_chargeback executed: customer=%s amount=%.2f",
        customer_id,
        amount,
    )
    return (
        f"⚠️  Chargeback of ${amount:.2f} processed for customer {customer_id}. "
        f"This action is irreversible."
    )
