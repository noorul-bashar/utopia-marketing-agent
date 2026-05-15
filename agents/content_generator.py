"""
agents/content_generator.py — Agent 2: Insights → Marketing Content

Takes structured MeetingInsights and generates:
  • LinkedIn post (hook + body + CTA + hashtags)
  • Follow-up email (warm leads)
  • Cold outreach email (new prospects)
  • Internal summary (Slack/Notion-ready)
"""

from __future__ import annotations

import json
import logging

from models.schemas import GeneratedContent, MeetingInsights
from prompts.content_prompt import CONTENT_SYSTEM, build_content_prompt
from tools.claude_client import claude

logger = logging.getLogger(__name__)


class ContentGeneratorAgent:
    """
    Stateless agent. Call generate() with MeetingInsights.
    Returns GeneratedContent.
    """

    def generate(self, insights: MeetingInsights) -> GeneratedContent:
        logger.info(
            "ContentGeneratorAgent starting | meeting='%s'", insights.meeting_title
        )

        # Serialize insights to JSON string for the prompt
        # We only include publicly-shareable fields — pain_points stay private
        safe_insights = {
            "meeting_title": insights.meeting_title,
            "date": insights.date,
            "attendees": insights.attendees,
            "key_decisions": insights.key_decisions,
            "action_items": insights.action_items,
            "highlights": insights.highlights,   # ← safe for public
            "topics_discussed": insights.topics_discussed,
            "one_line_summary": insights.one_line_summary,
            # NOTE: pain_points deliberately excluded — internal only
        }
        insights_json = json.dumps(safe_insights, indent=2)

        content = claude.complete_json(
            system=CONTENT_SYSTEM,
            user=build_content_prompt(insights_json),
            schema=GeneratedContent,
            temperature=0.75,   # more creativity for marketing copy
        )

        logger.info(
            "Content generated | linkedin_hook='%s...'",
            content.linkedin_post.hook[:40],
        )
        return content
