"""
Intent Governance Layer — Interactive CLI Demo
===============================================
Assembles all four layers via ``IntentGovernor.wrap()`` and runs an
interactive terminal loop powered by Rich.

Usage
-----
    1. Copy ``.env.example`` → ``.env`` and add your ``PERPLEXITY_API_KEY``.
    2. ``pip install -r requirements.txt``
    3. ``python main.py``
"""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

# ── ensure project root is on sys.path ───────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── env & logging ────────────────────────────────────────────────────────────
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
logger = logging.getLogger("intent_governance")

# ── imports (after path setup) ───────────────────────────────────────────────
from agno.agent import Agent
from models import get_model

from evals import SlackEscalationHook
from governor import IntentGovernor
from tools.demo_tools import (
    cancel_subscription,
    process_chargeback,
    send_email,
    stripe_refund,
)

console = Console()

# ═══════════════════════════════════════════════════════════════════════════════
# Session state — simulates what your backend / CRM would inject
# ═══════════════════════════════════════════════════════════════════════════════
SESSION_STATE = {
    "customer_tier": "standard",       # "standard" | "enterprise"
    "customer_tenure_days": 800,       # used by high_tenure condition
    "org_goal": "retention",           # "retention" | "cost_reduction" | "growth"
}


def build_agent() -> tuple[Agent, IntentGovernor]:
    """Create and wrap an agent with the full Intent Governance Layer."""

    # Select providers from environment
    agent_provider = os.getenv("AGENT_PROVIDER", "perplexity")
    judge_provider = os.getenv("JUDGE_PROVIDER", "perplexity")

    # Instantiate models via factory
    agent_model = get_model(provider=agent_provider)
    judge_model = get_model(provider=judge_provider)

    # Create Slack hook if URL is provided
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    escalation_hook = SlackEscalationHook(slack_webhook) if slack_webhook else None

    governor = IntentGovernor(
        constitution=PROJECT_ROOT / "constitutions" / "acme_corp.yaml",
        judge_criteria=PROJECT_ROOT / "criteria" / "brand_voice.txt",
        judge_model=judge_model,
        escalation_hook=escalation_hook,
        base_intent=(
            "You are a senior customer-support agent for Acme Corp. "
            "Be warm, professional, and concise."
        ),
    )

    agent = Agent(
        model=agent_model,
        tools=[stripe_refund, send_email, cancel_subscription, process_chargeback],
        session_state=SESSION_STATE,
        markdown=True,
    )

    governor.wrap(agent)
    return agent, governor


# ═══════════════════════════════════════════════════════════════════════════════
# Interactive loop
# ═══════════════════════════════════════════════════════════════════════════════

def handle_confirmation(run_response, agent) -> object:
    """
    If the run is paused (requires_confirmation), prompt the human
    operator and continue or reject.
    """
    if not run_response.is_paused:
        return run_response

    for requirement in run_response.active_requirements:
        if requirement.needs_confirmation:
            console.print(
                Panel(
                    f"[bold yellow]⚠️  CONFIRMATION REQUIRED[/]\n\n"
                    f"Tool: [bold cyan]{requirement.tool_execution.tool_name}[/]\n"
                    f"Args: {requirement.tool_execution.tool_args}",
                    title="🔒 Human Gate",
                    border_style="yellow",
                )
            )
            answer = (
                Prompt.ask(
                    "Approve this action?",
                    choices=["y", "n"],
                    default="y",
                )
                .strip()
                .lower()
            )
            if answer == "n":
                requirement.reject()
                console.print("[red]❌ Action rejected by human operator.[/]")
            else:
                requirement.confirm()
                console.print("[green]✅ Action approved by human operator.[/]")

    run_response = agent.continue_run(
        run_id=run_response.run_id,
        requirements=run_response.requirements,
    )
    return run_response


def main():
    """Entry point for the interactive CLI demo."""

    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key or api_key.startswith("pplx-xxx"):
        console.print(
            Panel(
                "[bold red]Missing PERPLEXITY_API_KEY[/]\n\n"
                "Copy .env.example → .env and add your Perplexity API key.",
                title="⚠️  Setup Required",
                border_style="red",
            )
        )
        sys.exit(1)

    agent, governor = build_agent()

    console.print(
        Panel(
            "[bold green]Intent Governance Layer[/] — Interactive Demo\n\n"
            f"Customer tier : [cyan]{SESSION_STATE['customer_tier']}[/]\n"
            f"Tenure        : [cyan]{SESSION_STATE['customer_tenure_days']} days[/]\n"
            f"Org goal      : [cyan]{SESSION_STATE['org_goal']}[/]\n\n"
            "Try these prompts:\n"
            '  • "Refund $500 to customer C-1234"\n'
            '  • "Send an email to user@acme.com about their ticket"\n'
            '  • "Cancel the subscription for customer C-5678"\n'
            '  • "Process a chargeback of $200 for customer C-9012"\n\n'
            "Type [bold]quit[/] or [bold]exit[/] to leave.",
            title="🚀 Central 73",
            border_style="bright_blue",
        )
    )

    while True:
        try:
            user_input = Prompt.ask("\n[bold bright_blue]You[/]")
        except (KeyboardInterrupt, EOFError):
            break

        if user_input.strip().lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/]")
            break

        if not user_input.strip():
            continue

        try:
            # ── run the agent ────────────────────────────────────────────
            run_response = agent.run(user_input)

            # ── handle human gate (requires_confirmation) ────────────────
            run_response = handle_confirmation(run_response, agent)

            # ── display response ─────────────────────────────────────────
            content = str(run_response.content) if run_response.content else "(no response)"
            console.print(
                Panel(
                    Markdown(content),
                    title="🤖 Agent",
                    border_style="green",
                )
            )

            # ── post-run eval (judge) ────────────────────────────────────
            governor.evaluate_response(
                input_text=user_input,
                output_text=content,
            )

        except ValueError as exc:
            # Constitution hook rejections / escalations surface here
            console.print(
                Panel(
                    f"[bold red]{exc}[/]",
                    title="🛑 Governance Block",
                    border_style="red",
                )
            )
        except Exception as exc:
            console.print(f"[bold red]Error:[/] {exc}")
            logger.exception("Unhandled error")


if __name__ == "__main__":
    main()
