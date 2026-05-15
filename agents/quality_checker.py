"""
agents/quality_checker.py — Agent 3: Content → Quality Report

Acts as a tough editor:
  • Scores each content piece 1-10
  • Lists strengths and specific improvements
  • Auto-generates revised version if score < 7
  • Returns an overall readiness verdict

This is the gate before content reaches a human's inbox or LinkedIn feed.
"""

from __future__ import annotations

import json
import logging

from models.schemas import GeneratedContent, MeetingInsights, QualityReport
from prompts.quality_prompt import QUALITY_SYSTEM, build_quality_prompt
from tools.claude_client import claude

logger = logging.getLogger(__name__)

# Threshold below which content needs a revision
REVISION_THRESHOLD = 7


class QualityCheckerAgent:
    """
    Stateless agent. Call check() with GeneratedContent + MeetingInsights.
    Returns QualityReport.
    """

    def check(
        self,
        content: GeneratedContent,
        insights: MeetingInsights,
    ) -> QualityReport:
        logger.info("QualityCheckerAgent starting")

        content_json = json.dumps(
            {
                "linkedin_post": {
                    "full_text": content.linkedin_post.full_text,
                },
                "follow_up_email": content.follow_up_email.model_dump(),
                "press_angle": content.press_angle,
                "internal_summary": content.internal_summary,
            },
            indent=2,
        )

        insights_json = json.dumps(
            {
                "highlights": insights.highlights,
                "key_decisions": insights.key_decisions,
                "one_line_summary": insights.one_line_summary,
            },
            indent=2,
        )

        report = claude.complete_json(
            system=QUALITY_SYSTEM,
            user=build_quality_prompt(content_json, insights_json),
            schema=QualityReport,
            temperature=0.2,   # low temp = consistent, rigorous scoring
        )

        # Log summary
        for score in report.scores:
            level = "✅" if score.score >= 7 else "⚠️"
            logger.info(
                "%s %s: %d/10 | strengths=%d improvements=%d has_revision=%s",
                level,
                score.item,
                score.score,
                len(score.strengths),
                len(score.improvements),
                score.revised_version is not None,
            )

        logger.info(
            "Quality check complete | overall=%.1f/10 ready_to_send=%s",
            report.overall_score,
            report.ready_to_send,
        )
        return report
