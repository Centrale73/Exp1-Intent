"""
Layer 2 — Judge Post-Hook (AgentAsJudgeEval)
=============================================
Evaluates agent *output* against brand-voice / ethics criteria after
the tool call has executed.  Fires asynchronously (``run_in_background=True``)
so it doesn't add latency to the user-facing response.

On failure, triggers an escalation callback (Slack, PagerDuty, CRM, etc.).
"""

import logging
import os
from pathlib import Path
from typing import Callable, Optional

import httpx
from agno.eval.agent_as_judge import AgentAsJudgeEval
from agno.models.perplexity import Perplexity

logger = logging.getLogger("intent_governance.evals")


# ── default escalation callback ─────────────────────────────────────────────

def default_escalation_hook(result) -> None:
    """
    Placeholder escalation handler.
    In production, wire this to Slack / PagerDuty / CRM flagging.
    """
    logger.error("[ESCALATION] Output failed intent alignment check.")
    logger.error("[ESCALATION] Result: %s", result)
    print(f"\n⚠️  [ESCALATION] Agent output failed intent check — review required.\n")


class SlackEscalationHook:
    """
    Sends governance escalation alerts to a Slack channel via Incoming Webhook.
    """

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        if not self.webhook_url:
            logger.warning("SlackEscalationHook initialized without a webhook URL.")

    def __call__(self, result) -> None:
        """
        Executes the escalation by posting to Slack.
        Expected result is an AgentAsJudgeEvaluation object.
        """
        if not self.webhook_url:
            default_escalation_hook(result)
            return

        # Prepare the Slack payload using blocks for rich formatting
        score_color = "#eb4034" if result.score < 5 else "#fca103"
        
        payload = {
            "text": f"🚨 *Intent Governance Escalation Required* (Score: {result.score}/10)",
            "attachments": [
                {
                    "color": score_color,
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Governance Alert: Intent Alignment Failure*\n*Score:* {result.score}/10 | *Passed:* {result.passed}"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Input:*\n{result.input[:100]}..."},
                                {"type": "mrkdwn", "text": f"*Judge Name:*\n{getattr(result, 'name', 'Intent Check')}"}
                            ]
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*Reasoning:*\n{result.reason}"
                            }
                        },
                        {
                            "type": "divider"
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": "_Full audit trail available in local logs._"
                            }
                        }
                    ]
                }
            ]
        }

        try:
            response = httpx.post(self.webhook_url, json=payload, timeout=10.0)
            response.raise_for_status()
            logger.info("[SLACK] Escalation alert sent successfully.")
        except Exception as exc:
            logger.error("[SLACK] Failed to send escalation alert: %s", exc)
            default_escalation_hook(result)


# ── factory ──────────────────────────────────────────────────────────────────

def create_intent_judge(
    criteria_path: str | Path,
    escalation_hook: Optional[Callable] = None,
    threshold: int = 7,
    run_in_background: bool = True,
    model_id: str = "sonar-pro",
) -> AgentAsJudgeEval:
    """
    Build an ``AgentAsJudgeEval`` instance configured for intent alignment.

    Parameters
    ----------
    criteria_path : str | Path
        Path to a plain-text file containing the numbered evaluation criteria.
    escalation_hook : callable, optional
        Callback fired when the eval score falls below *threshold*.
        Defaults to ``default_escalation_hook``.
    threshold : int
        Minimum passing score (1-10 scale).  Default 7.
    run_in_background : bool
        If True, the eval fires asynchronously so it does not block the
        agent's response latency.  Default True.

    Returns
    -------
    AgentAsJudgeEval
    """
    criteria_path = Path(criteria_path)
    criteria_text = criteria_path.read_text(encoding="utf-8").strip()

    hook = escalation_hook or default_escalation_hook

    evaluation = AgentAsJudgeEval(
        name="Intent Alignment Check",
        criteria=criteria_text,
        scoring_strategy="numeric",
        threshold=threshold,
        on_fail=hook,
        run_in_background=run_in_background,
        model=Perplexity(id=model_id),
    )

    logger.info(
        "Intent judge created — threshold=%d, background=%s, criteria_file=%s",
        threshold,
        run_in_background,
        criteria_path.name,
    )
    return evaluation
