"""
tools/file_handler.py — All disk I/O in one place.

Why centralise this?
  • Easy to swap to S3/GCS later with zero agent changes
  • Consistent UTF-8 handling
  • Auto-creates output directories
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FileHandler:

    def __init__(self, output_dir: str = "output") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ── Reading ───────────────────────────────────────────────────────────────

    def read_transcript(self, path: str) -> str:
        """Read a plain-text or markdown transcript file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Transcript not found: {path}")
        text = p.read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"Transcript file is empty: {path}")
        logger.info("Loaded transcript: %s (%d chars)", path, len(text))
        return text

    # ── Writing ───────────────────────────────────────────────────────────────

    def save_json(self, data: Dict[str, Any], filename: str) -> str:
        """Save a dict as pretty-printed JSON. Returns the full path."""
        path = self.output_dir / filename
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("Saved JSON → %s", path)
        return str(path)

    def save_text(self, content: str, filename: str) -> str:
        """Save plain text. Returns the full path."""
        path = self.output_dir / filename
        path.write_text(content, encoding="utf-8")
        logger.info("Saved text → %s", path)
        return str(path)

    def save_markdown(self, content: str, filename: str) -> str:
        """Save markdown content. Returns the full path."""
        return self.save_text(content, filename)

    # ── Bundle ────────────────────────────────────────────────────────────────

    def build_markdown_bundle(
        self,
        run_id: str,
        insights,          # MeetingInsights
        content,           # GeneratedContent
        quality,           # QualityReport
    ) -> str:
        """
        Build a single human-readable .md file that a marketing lead can
        open Monday morning and immediately start working from.
        """
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            f"# 📣 Marketing Output — {insights.meeting_title}",
            f"*Generated {now} | Run ID: {run_id}*",
            "",
            "---",
            "",
            "## 📋 Meeting Summary",
            f"> {insights.one_line_summary}",
            "",
            "**Key Decisions:**",
        ]
        for d in insights.key_decisions:
            lines.append(f"- {d}")

        lines += [
            "",
            "**Action Items:**",
        ]
        for a in insights.action_items:
            lines.append(f"- {a}")

        lines += [
            "",
            "---",
            "",
            "## 🔵 LinkedIn Post",
            f"*Quality Score: {next((s.score for s in quality.scores if s.item == 'linkedin_post'), '?')}/10*",
            "",
            "```",
            content.linkedin_post.full_text,
            "```",
            "",
            "---",
            "",
            "## 📧 Follow-up Email (Warm Leads)",
            f"*Quality Score: {next((s.score for s in quality.scores if s.item == 'follow_up_email'), '?')}/10*",
            "",
            "```",
            content.follow_up_email.full_email,
            "```",
            "",
            "---",
            "",
            "## 📬 Cold Outreach Email",
            f"*Quality Score: {next((s.score for s in quality.scores if s.item == 'press_angle'), '?')}/10*",
            "",
            "```",
            content.press_angle,
            "```",
            "",
            "---",
            "",
            "## ✅ Quality Report",
            f"**Overall Score:** {quality.overall_score:.1f}/10  ",
            f"**Ready to Send:** {'✅ Yes' if quality.ready_to_send else '⚠️ Needs Review'}  ",
            f"**Note:** {quality.executive_note}",
            "",
        ]

        for score in quality.scores:
            lines += [
                f"### {score.item.replace('_', ' ').title()} ({score.score}/10)",
                f"**Strengths:** {', '.join(score.strengths)}",
                f"**Improve:** {', '.join(score.improvements)}",
            ]
            if score.revised_version:
                lines += ["**Revised version:**", "```", score.revised_version, "```"]
            lines.append("")

        lines += [
            "---",
            "",
            "## 📢 Internal Summary (Slack / Notion)",
            "",
            content.internal_summary,
        ]

        return "\n".join(lines)


# Module-level singleton
file_handler = FileHandler()
