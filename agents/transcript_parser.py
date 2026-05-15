"""
agents/transcript_parser.py — Agent 1: Transcript → Structured Insights

This agent has ONE job: read a meeting transcript and return a MeetingInsights
object. It knows nothing about LinkedIn or emails — single responsibility.

If the transcript is very long (>8000 chars), we chunk and merge.
"""

from __future__ import annotations

import json
import logging

from models.schemas import MeetingInsights
from prompts.parser_prompt import PARSER_SYSTEM, build_parser_prompt
from tools.claude_client import claude

logger = logging.getLogger(__name__)

# Chunking threshold — transcripts longer than this get chunked
CHUNK_THRESHOLD = 8_000
CHUNK_SIZE = 6_000


class TranscriptParserAgent:
    """
    Stateless agent. Call parse() with raw transcript text.
    Returns MeetingInsights.
    """

    def parse(self, transcript: str) -> MeetingInsights:
        logger.info(
            "TranscriptParserAgent starting | transcript_length=%d", len(transcript)
        )

        if len(transcript) <= CHUNK_THRESHOLD:
            return self._parse_single(transcript)
        else:
            logger.info("Long transcript detected — using chunked parsing")
            return self._parse_chunked(transcript)

    # ── Single-pass parsing ────────────────────────────────────────────────────

    def _parse_single(self, transcript: str) -> MeetingInsights:
        insights = claude.complete_json(
            system=PARSER_SYSTEM,
            user=build_parser_prompt(transcript),
            schema=MeetingInsights,
        )
        logger.info(
            "Parsed insights: decisions=%d actions=%d highlights=%d",
            len(insights.key_decisions),
            len(insights.action_items),
            len(insights.highlights),
        )
        return insights

    # ── Chunked parsing for long transcripts ──────────────────────────────────

    def _parse_chunked(self, transcript: str) -> MeetingInsights:
        """
        Split transcript into overlapping chunks, parse each, then merge.
        Overlap prevents losing context at chunk boundaries.
        """
        chunks = self._split_with_overlap(transcript, CHUNK_SIZE, overlap=500)
        logger.info("Split transcript into %d chunks", len(chunks))

        partial_insights = []
        for i, chunk in enumerate(chunks):
            logger.info("Parsing chunk %d/%d", i + 1, len(chunks))
            try:
                partial = self._parse_single(chunk)
                partial_insights.append(partial)
            except Exception as e:
                logger.warning("Chunk %d failed: %s — skipping", i + 1, e)

        if not partial_insights:
            raise RuntimeError("All transcript chunks failed to parse")

        return self._merge_insights(partial_insights)

    @staticmethod
    def _split_with_overlap(text: str, chunk_size: int, overlap: int) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks

    @staticmethod
    def _merge_insights(partials: list[MeetingInsights]) -> MeetingInsights:
        """Deduplicate and merge partial results from chunked parsing."""
        first = partials[0]

        def dedup(lists: list[list[str]]) -> list[str]:
            seen = set()
            result = []
            for lst in lists:
                for item in lst:
                    key = item.strip().lower()
                    if key not in seen:
                        seen.add(key)
                        result.append(item)
            return result

        return MeetingInsights(
            meeting_title=first.meeting_title,
            date=first.date,
            attendees=dedup([p.attendees for p in partials]),
            key_decisions=dedup([p.key_decisions for p in partials]),
            action_items=dedup([p.action_items for p in partials]),
            highlights=dedup([p.highlights for p in partials]),
            pain_points=dedup([p.pain_points for p in partials]),
            topics_discussed=dedup([p.topics_discussed for p in partials]),
            one_line_summary=first.one_line_summary,
        )
