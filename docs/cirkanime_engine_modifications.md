# Cirkanime Adaptation Plan for the Intent Governance Engine

This document maps the current **Acme-style support demo** to the operational reality of
[Cirkanime](https://cirkanime.com/fr/index.html): anime-themed at-home circus birthday events.

## Why adaptation is needed

The current project is oriented around generic customer-support actions (`refund`,
`chargeback`, `cancel_subscription`). Cirkanime's business model is different:

- Event booking and scheduling (not subscriptions)
- Capacity constraints (maximum children / costumes)
- Suitability checks (age range, required space)
- Channel coordination (email/phone/social)
- Follow-up and review collection

## Engine modifications recommended

### 1) Replace generic tools with event-business tools

Use tools centered on booking operations and CRM updates:

- `qualify_event_request(...)`
- `propose_package(...)`
- `create_booking(...)`
- `reschedule_booking(...)`
- `log_parent_call(...)`
- `send_quote_email(...)`
- `create_crm_contact(...)`
- `create_crm_deal(...)`
- `update_crm_stage(...)`

A starter set is provided in `tools/crm_tools.py`.

### 2) Business constitution for Cirkanime

Create a domain constitution with rules such as:

- Reject if `children_count > 11` (10 friends + birthday child)
- Escalate if age is under 7 without parent support confirmation
- Escalate if indoor space is below 10x8 ft and no outdoor backup
- Escalate if booking is requested with less than 14 days lead time
- Approve quote email and lead creation by default

A starter policy is provided in `constitutions/cirkanime.yaml`.

### 3) Dynamic instruction retriever for event strategy

Add strategy flags beyond retention/cost/growth:

- `weekend_fill`
- `premium_upsell`
- `school_outreach`
- `review_collection`

These can tune package recommendation behavior and script style for parents.

### 4) Judge criteria specialized to parent-facing communication

Judge should score:

- Clarity in French (and optional English adaptation)
- Safety wording for non-acrobatic playful activities
- Correct mention of constraints (capacity, age, space)
- Tone (reassuring, warm, concise)
- Clear CTA (book now / call / email)

Starter criteria are in `criteria/cirkanime_voice.txt`.

### 5) Human approval gates for high-risk actions

Require confirmation before:

- Final booking commitment with date lock
- Refund exceptions
- Last-minute schedule changes

## Suggested agent topology

Use a **3-agent setup** orchestrated by one coordinator:

1. **Frontdesk Conversation Agent**
   - Handles website/chat/DM questions
   - Qualifies parent intent and gathers missing fields

2. **Booking & Operations Agent**
   - Validates eligibility (age/space/date/capacity)
   - Recommends package and creates tentative booking

3. **CRM Copilot Agent**
   - Creates/updates contacts, deals, notes, and follow-up tasks
   - Sends reminders and review requests after event completion

### Why this works for a solo creator

For a creator-operator, the highest leverage is a **CRM Copilot Agent** because it:

- Preserves lead context across channels
- Avoids missed follow-ups
- Keeps pipeline visibility (new lead -> qualified -> quote -> booked -> completed)
- Automates repetitive communication while keeping the creator in control

## Minimal CRM schema (recommended)

Store these fields in CRM for each lead/opportunity:

- Parent name + contact channels (email, phone)
- Child age and birthday date
- Children count
- Preferred package (SUPRA/EXTRA/ULTIME)
- Event address area + indoor/outdoor feasibility
- Language preference (FR/EN)
- Stage + next action date
- Last interaction summary

## Rollout checklist

1. Add business tools and wire them in `Agent(tools=[...])`.
2. Switch constitution path to `constitutions/cirkanime.yaml`.
3. Switch judge criteria path to `criteria/cirkanime_voice.txt`.
4. Inject CRM adapter functions (HubSpot/Pipedrive/Notion/Airtable).
5. Keep `requires_confirmation=True` on commitment/refund tools.
6. Test 10 core parent scenarios before production.
