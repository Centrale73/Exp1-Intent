"""
IntentGovernor — Assembly Layer
================================
Wires all four Agno governance primitives into a single ``wrap()`` call:

1. **tool_hooks**          → Constitution Hook + Audit Logger
2. **AgentAsJudgeEval**    → Post-run output scoring
3. **instructions**        → Dynamic Intent Retriever (callable)
4. **requires_confirmation** → Already on sensitive @tool decorators

Usage
-----
    from governor import IntentGovernor

    governor = IntentGovernor(
        constitution="constitutions/acme_corp.yaml",
        judge_criteria="criteria/brand_voice.txt",
        escalation_hook=my_slack_alert,
    )
    agent = governor.wrap(
        Agent(model=Perplexity(id="sonar-pro"), tools=[...])
    )
"""

import logging
from pathlib import Path
from typing import Callable, Dict, Optional

from agno.agent import Agent
from agno.models.base import Model

from hooks.constitution_hook import create_constitution_hook, logger_hook
from evals.judge_eval import create_intent_judge, default_escalation_hook
from intent.retriever import create_intent_retriever

logger = logging.getLogger("intent_governance.governor")


class IntentGovernor:
    """
    Central 73 Intent Governance Layer.

    Bundles Agno's four governance primitives into a single composable
    wrapper that can be applied to *any* Agno Agent.

    Parameters
    ----------
    constitution : str | Path
        Path to the constitution YAML file.
    judge_criteria : str | Path
        Path to the plain-text criteria file for the AgentAsJudgeEval.
    escalation_hook : callable, optional
        Callback fired on eval failure (default: console logger).
    base_intent : str
        Default system prompt injected on every turn.
    strategy_overrides : dict, optional
        Extra ``org_goal → instruction suffix`` mappings.
    judge_threshold : int
        Minimum passing score (1-10).  Default 7.
    judge_background : bool
        Run the judge asynchronously.  Default True.
    judge_model : Model, optional
        The Agno model instance to use for evaluation.
        If None, the judge will not be pre-built (must be provided or defaults).
    """

    def __init__(
        self,
        constitution: str | Path = "constitutions/acme_corp.yaml",
        judge_criteria: str | Path = "criteria/brand_voice.txt",
        judge_model: Optional[Model] = None,
        escalation_hook: Optional[Callable] = None,
        base_intent: str = "You are a support agent for Acme Corp.",
        strategy_overrides: Optional[Dict[str, str]] = None,
        judge_threshold: int = 7,
        judge_background: bool = True,
    ):
        self.constitution_path = Path(constitution)
        self.judge_criteria_path = Path(judge_criteria)
        self.escalation_hook = escalation_hook or default_escalation_hook
        self.base_intent = base_intent
        self.strategy_overrides = strategy_overrides
        self.judge_threshold = judge_threshold
        self.judge_background = judge_background

        # ── pre-build components ─────────────────────────────────────────
        self._constitution_hook = create_constitution_hook(self.constitution_path)
        self._intent_retriever = create_intent_retriever(
            base_intent=self.base_intent,
            strategy_overrides=self.strategy_overrides,
        )
        if judge_model:
            self._judge = create_intent_judge(
                criteria_path=self.judge_criteria_path,
                model=judge_model,
                escalation_hook=self.escalation_hook,
                threshold=self.judge_threshold,
                run_in_background=self.judge_background,
            )
        else:
            self._judge = None
            logger.warning("IntentGovernor initialised without a judge model.")

        logger.info(
            "IntentGovernor initialised — constitution=%s, criteria=%s",
            self.constitution_path,
            self.judge_criteria_path,
        )

    # ── wrap ─────────────────────────────────────────────────────────────

    def wrap(self, agent: Agent) -> Agent:
        """
        Apply all governance layers to an existing Agent **in-place** and
        return it for chaining convenience.

        Modifications:
            - ``agent.tool_hooks`` ← [logger_hook, constitution_hook]
            - ``agent.instructions`` ← callable intent retriever
        """
        # 1. Inject tool hooks (logger outermost, constitution innermost)
        existing_hooks = list(agent.tool_hooks or [])
        agent.tool_hooks = [logger_hook, self._constitution_hook] + existing_hooks

        # 2. Replace instructions with callable retriever
        agent.instructions = self._intent_retriever

        logger.info("Agent wrapped with IntentGovernor.")
        return agent

    # ── post-run evaluation ──────────────────────────────────────────────

    def evaluate_response(self, input_text: str, output_text: str):
        """
        Run the AgentAsJudgeEval against a completed agent turn.

        Call this after each ``agent.run()`` to score the response against
        brand-voice and ethics criteria.

        Returns the eval result (or None if running in background mode).
        """
        try:
            result = self._judge.run(
                input=input_text,
                output=output_text,
            )
            return result
        except Exception as exc:
            logger.error("Judge eval failed: %s", exc)
            return None

    # ── convenience properties ───────────────────────────────────────────

    @property
    def judge(self):
        """Access the underlying AgentAsJudgeEval instance."""
        return self._judge

    @property
    def constitution_hook(self):
        """Access the bound constitution hook function."""
        return self._constitution_hook

    @property
    def intent_retriever(self):
        """Access the bound intent retriever callable."""
        return self._intent_retriever
