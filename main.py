"""
main.py — Utopia Marketing Agent Orchestrator

Pipeline:
  Transcript file
      → [Agent 1] TranscriptParserAgent    → MeetingInsights
      → [Agent 2] ContentGeneratorAgent    → GeneratedContent
      → [Agent 3] QualityCheckerAgent      → QualityReport
      → FileHandler                        → output/*.md + output/*.json
      → SlackNotifier                      → #marketing-outputs (optional)

Usage:
  python main.py samples/sample_transcript.txt
  python main.py my_transcript.txt --output-dir results/
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import uuid
from pathlib import Path

from agents.content_generator import ContentGeneratorAgent
from agents.quality_checker import QualityCheckerAgent
from agents.transcript_parser import TranscriptParserAgent
from config import config
from models.schemas import PipelineResult
from tools.file_handler import FileHandler
from tools.slack_notifier import SlackNotifier

# ── Logging setup ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


# ── Orchestrator ───────────────────────────────────────────────────────────────

def run_pipeline(transcript_path: str, output_dir: str = "output") -> PipelineResult:
    """
    Run the full marketing agent pipeline.
    Returns a PipelineResult with all outputs and file paths.
    """
    run_id = str(uuid.uuid4())[:8]
    logger.info("=" * 60)
    logger.info("🚀 Utopia Marketing Agent | Run ID: %s", run_id)
    logger.info("=" * 60)

    # ── Tools ──────────────────────────────────────────────────────────────────
    files = FileHandler(output_dir=output_dir)
    slack = SlackNotifier()
    slack.notify_started(run_id, transcript_path)

    # ── Step 1: Load transcript ────────────────────────────────────────────────
    logger.info("📄 Step 1/4 — Loading transcript: %s", transcript_path)
    transcript = files.read_transcript(transcript_path)

    # ── Step 2: Parse ──────────────────────────────────────────────────────────
    logger.info("🔍 Step 2/4 — Parsing transcript → insights")
    parser = TranscriptParserAgent()
    try:
        insights = parser.parse(transcript)
    except Exception as e:
        slack.notify_error(run_id, "Transcript Parser", str(e))
        raise
    logger.info("   Meeting: '%s'", insights.meeting_title)
    logger.info("   Summary: %s", insights.one_line_summary)
    slack.notify_parsed(insights.meeting_title, insights.one_line_summary, len(insights.highlights))

    # ── Step 3: Generate content ───────────────────────────────────────────────
    logger.info("✍️  Step 3/4 — Generating marketing content")
    generator = ContentGeneratorAgent()
    try:
        content = generator.generate(insights)
    except Exception as e:
        slack.notify_error(run_id, "Content Generator", str(e))
        raise
    slack.notify_generated(content.linkedin_post.hook, content.follow_up_email.subject)

    # ── Step 4: Quality check ──────────────────────────────────────────────────
    logger.info("🔎 Step 4/4 — Quality checking all content")
    checker = QualityCheckerAgent()
    try:
        quality = checker.check(content, insights)
    except Exception as e:
        slack.notify_error(run_id, "Quality Checker", str(e))
        raise

    # ── Save outputs ───────────────────────────────────────────────────────────
    slug = run_id
    output_files = []

    # Full pipeline result as JSON (machine-readable)
    result = PipelineResult(
        run_id=run_id,
        transcript_file=transcript_path,
        insights=insights,
        content=content,
        quality=quality,
    )
    json_path = files.save_json(
        result.model_dump(),
        f"pipeline_result_{slug}.json",
    )
    output_files.append(json_path)

    # Human-readable markdown bundle
    md_bundle = files.build_markdown_bundle(run_id, insights, content, quality)
    md_path = files.save_markdown(md_bundle, f"marketing_bundle_{slug}.md")
    output_files.append(md_path)

    # Individual files for easy copy-paste
    linkedin_path = files.save_text(
        content.linkedin_post.full_text,
        f"linkedin_post_{slug}.txt",
    )
    output_files.append(linkedin_path)

    followup_path = files.save_text(
        content.follow_up_email.full_email,
        f"email_followup_{slug}.txt",
    )
    output_files.append(followup_path)

    # ✅ M7 REQUIRED: save press-angle sentence
    divider = "─" * 50
    press_text = "PRESS ANGLE\n" + divider + "\n" + content.press_angle + "\n\nLAUNCH STAGE: " + content.launch_stage_press + "\n"
    press_path = files.save_text(
        press_text,
        f"press_angle_{slug}.txt",
    )
    output_files.append(press_path)

    result.output_files = output_files

    # ── Slack final notification ───────────────────────────────────────────────
    slack.notify_complete(
        run_id=run_id,
        overall_score=quality.overall_score,
        ready_to_send=quality.ready_to_send,
        executive_note=quality.executive_note,
        scores=[s.model_dump() for s in quality.scores],
        output_files=output_files,
    )

    # ── Summary ────────────────────────────────────────────────────────────────
    _print_summary(result)
    return result


def _print_summary(result: PipelineResult) -> None:
    q = result.quality
    ready_str = "✅ READY TO SEND" if q.ready_to_send else "⚠️  NEEDS REVIEW"

    print("\n" + "=" * 60)
    print(f"  UTOPIA MARKETING AGENT — COMPLETE")
    print("=" * 60)
    print(f"  Meeting : {result.insights.meeting_title}")
    print(f"  Run ID  : {result.run_id}")
    print(f"  Status  : {ready_str}")
    print(f"  Score   : {q.overall_score:.1f}/10")
    print(f"  Press   : {result.content.press_angle[:80]}...")
    print(f"  Note    : {q.executive_note}")
    print()
    print("  OUTPUT FILES:")
    for f in result.output_files:
        print(f"    → {f}")
    print("=" * 60 + "\n")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Utopia Marketing Agent — transcript to LinkedIn + email"
    )
    parser.add_argument(
        "transcript",
        help="Path to meeting transcript file (.txt or .md)",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory to save output files (default: output/)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable DEBUG logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not Path(args.transcript).exists():
        print(f"❌ Transcript file not found: {args.transcript}", file=sys.stderr)
        return 1

    try:
        run_pipeline(args.transcript, output_dir=args.output_dir)
        return 0
    except EnvironmentError as e:
        print(f"\n❌ Configuration error:\n{e}\n", file=sys.stderr)
        return 1
    except Exception as e:
        logger.exception("Pipeline failed: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())