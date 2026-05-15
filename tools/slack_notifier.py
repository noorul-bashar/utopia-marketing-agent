"""
tools/slack_notifier.py — Real-time Slack updates at every pipeline stage.

Sends 4 messages to Slack as the pipeline runs:
  1. 🟡 Pipeline started
  2. 🔍 Insights parsed (shows meeting title + summary)
  3. ✍️  Content generated (shows LinkedIn hook preview)
  4. ✅ / ⚠️  Complete with scores and file list

Set SLACK_WEBHOOK_URL in your environment or .env file to enable.
If not set, all calls are silent no-ops — pipeline always continues.
"""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Optional

from config import config

logger = logging.getLogger(__name__)


class SlackNotifier:

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        self.webhook_url = webhook_url or config.slack_webhook_url
        self.enabled = bool(self.webhook_url)

        if self.enabled:
            logger.info("Slack notifier enabled → %s", config.slack_channel)
        else:
            logger.info(
                "Slack notifier disabled — set SLACK_WEBHOOK_URL to enable live updates"
            )

    # ── Stage messages ────────────────────────────────────────────────────────

    def notify_started(self, run_id: str, transcript_file: str) -> None:
        """Send when the pipeline kicks off."""
        self._send(blocks=[
            self._header("🟡  Utopia Marketing Agent — Starting"),
            self._section(
                f"*Run ID:* `{run_id}`\n"
                f"*Transcript:* `{transcript_file}`\n\n"
                f"Processing transcript through 3 agents… this takes ~60s."
            ),
            self._divider(),
        ])

    def notify_parsed(self, meeting_title: str, summary: str, n_highlights: int) -> None:
        """Send after Agent 1 finishes parsing."""
        self._send(blocks=[
            self._header("🔍  Step 2/4 — Transcript Parsed"),
            self._section(
                f"*Meeting:* {meeting_title}\n"
                f"*Summary:* {summary}\n"
                f"*Public highlights found:* {n_highlights}"
            ),
        ])

    def notify_generated(self, hook: str, subject: str) -> None:
        """Send after Agent 2 finishes generating content."""
        self._send(blocks=[
            self._header("✍️  Step 3/4 — Content Generated"),
            self._section(
                f"*LinkedIn hook:*\n>{hook}\n\n"
                f"*Email subject:* {subject}"
            ),
        ])

    def notify_complete(
        self,
        run_id: str,
        overall_score: float,
        ready_to_send: bool,
        executive_note: str,
        scores: list,
        output_files: list,
    ) -> None:
        """Send the final summary with scores and file list."""
        status_emoji = "✅" if ready_to_send else "⚠️"
        status_text  = "READY TO SEND" if ready_to_send else "NEEDS REVIEW"

        score_lines = "\n".join(
            f"• *{s['item'].replace('_', ' ').title()}:* "
            f"{s['score']}/10 {'✅' if s['score'] >= 7 else '⚠️'}"
            for s in scores
        )

        file_lines = "\n".join(f"• `{f}`" for f in output_files)

        self._send(blocks=[
            self._header(f"{status_emoji}  Marketing Agent Complete — {status_text}"),
            self._section(
                f"*Overall Score:* {overall_score:.1f}/10\n"
                f"*Run ID:* `{run_id}`\n\n"
                f"{score_lines}"
            ),
            self._divider(),
            self._section(f"*Editor note:* {executive_note}"),
            self._divider(),
            self._section(f"*Output files:*\n{file_lines}"),
            self._context("Posted by *Utopia Marketing Agent* | Check your output/ folder"),
        ])

    def notify_error(self, run_id: str, stage: str, error: str) -> None:
        """Send if any stage fails."""
        self._send(blocks=[
            self._header("🔴  Pipeline Error"),
            self._section(
                f"*Run ID:* `{run_id}`\n"
                f"*Failed at:* {stage}\n"
                f"*Error:* ```{error[:300]}```"
            ),
        ])

    # ── Core send ─────────────────────────────────────────────────────────────

    def _send(self, blocks: list) -> bool:
        if not self.enabled:
            return False
        payload = {"blocks": blocks}
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                ok = resp.status == 200
                if ok:
                    logger.info("Slack message sent")
                else:
                    logger.warning("Slack returned status %d", resp.status)
                return ok
        except Exception as e:
            logger.warning("Slack send failed (non-critical): %s", e)
            return False

    # ── Block builders ────────────────────────────────────────────────────────

    @staticmethod
    def _header(text: str) -> dict:
        return {"type": "header", "text": {"type": "plain_text", "text": text}}

    @staticmethod
    def _section(text: str) -> dict:
        return {"type": "section", "text": {"type": "mrkdwn", "text": text}}

    @staticmethod
    def _divider() -> dict:
        return {"type": "divider"}

    @staticmethod
    def _context(text: str) -> dict:
        return {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": text}],
        }

    def context(self, text: str) -> dict:
        """Public alias for _context — required by test_slack.py."""
        return self._context(text)


# Module-level singleton
slack = SlackNotifier()
