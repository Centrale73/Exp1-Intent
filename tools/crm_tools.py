"""
Cirkanime CRM & booking demo tools.

These are in-memory stubs showing the target shape of a CRM-connected
workflow. Replace internals with real adapters (HubSpot / Pipedrive / Airtable)
in production.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from agno.tools import tool


@tool
def create_crm_contact(parent_name: str, email: str, phone: str, language: str = "fr") -> str:
    """Create or update a parent contact in CRM."""
    contact_id = f"ct_{uuid.uuid4().hex[:8]}"
    return (
        f"✅ CRM contact saved: {contact_id} | name={parent_name} | email={email} "
        f"| phone={phone} | language={language}"
    )


@tool
def create_crm_deal(
    contact_id: str,
    package_name: str,
    requested_date: str,
    children_count: int,
    location_area: str,
) -> str:
    """Create a booking opportunity/deal in CRM."""
    deal_id = f"dl_{uuid.uuid4().hex[:8]}"
    return (
        f"✅ CRM deal created: {deal_id} | contact={contact_id} | package={package_name} "
        f"| date={requested_date} | children={children_count} | area={location_area}"
    )


@tool(requires_confirmation=True)
def create_booking(
    deal_id: str,
    event_date: str,
    children_count: int,
    indoor_space_sqft: int,
    deposit_received: bool,
) -> str:
    """Confirm a booking and lock event slot. Human confirmation required."""
    booking_id = f"bk_{uuid.uuid4().hex[:8]}"
    return (
        f"✅ Booking confirmed: {booking_id} | deal={deal_id} | date={event_date} "
        f"| children={children_count} | indoor_space_sqft={indoor_space_sqft} "
        f"| deposit_received={deposit_received}"
    )


@tool
def reschedule_booking(booking_id: str, new_date: str, reason: Optional[str] = None) -> str:
    """Reschedule an existing event booking."""
    return f"✅ Booking {booking_id} rescheduled to {new_date}. reason={reason or 'n/a'}"


@tool
def send_quote_email(to: str, package_name: str, quoted_price_cad: float, valid_until: str) -> str:
    """Send a quote email with package and validity date."""
    return (
        f"✅ Quote email sent to {to}: package={package_name}, "
        f"price={quoted_price_cad:.2f} CAD, valid_until={valid_until}"
    )


@tool(requires_confirmation=True)
def issue_refund(booking_id: str, amount_cad: float, reason: str) -> str:
    """Issue refund for a booking. Human confirmation required."""
    refund_id = f"rf_{uuid.uuid4().hex[:8]}"
    return (
        f"⚠️ Refund issued: {refund_id} | booking={booking_id} "
        f"| amount={amount_cad:.2f} CAD | reason={reason}"
    )


def days_until(target_date_iso: str) -> int:
    """Helper for policy engines that need lead-time checks."""
    target = date.fromisoformat(target_date_iso)
    return (target - date.today()).days
