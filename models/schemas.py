"""
models/schemas.py — Typed data contracts between agents.
Fixed: added press_angle (required M7 output) + launch_stage fields.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ── 1. Parser Agent output ────────────────────────────────────────────────────

class MeetingInsights(BaseModel):
    meeting_title: str
    date: Optional[str] = None
    attendees: List[str] = Field(default_factory=list)
    key_decisions: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    pain_points: List[str] = Field(default_factory=list)
    topics_discussed: List[str] = Field(default_factory=list)
    one_line_summary: str


# ── 2. Content Generator output ──────────────────────────────────────────────

class LinkedInPost(BaseModel):
    launch_stage: str = Field(default="Amplify")
    hook: str
    body: str
    cta: str
    hashtags: List[str] = Field(default_factory=list)

    @property
    def full_text(self) -> str:
        tags = " ".join(f"#{h}" for h in self.hashtags)
        return f"{self.hook}\n\n{self.body}\n\n{self.cta}\n\n{tags}"


class Email(BaseModel):
    launch_stage: str = Field(default="Nurture")
    recipient_type: str
    subject: str
    preview_text: str = ""
    greeting: str
    body: str
    signature: str

    @property
    def full_email(self) -> str:
        return (
            f"Subject: {self.subject}\n"
            f"Preview: {self.preview_text}\n"
            f"{'─'*50}\n"
            f"{self.greeting}\n\n"
            f"{self.body}\n\n"
            f"{self.signature}"
        )


class GeneratedContent(BaseModel):
    linkedin_post: LinkedInPost
    follow_up_email: Email
    press_angle: str = Field(default="")
    launch_stage_press: str = Field(default="Lead")
    internal_summary: str = ""

    @field_validator("internal_summary", mode="before")
    @classmethod
    def coerce_summary_to_string(cls, v):
        """Model sometimes returns a list of bullet strings — join them."""
        if isinstance(v, list):
            return "\n".join(str(item) for item in v)
        return v or ""

# ── 3. Quality Checker output ─────────────────────────────────────────────────

class ContentScore(BaseModel):
    item: str
    score: int = Field(ge=1, le=10)
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    revised_version: Optional[str] = None


class QualityReport(BaseModel):
    scores: List[ContentScore]
    overall_score: float
    ready_to_send: bool
    executive_note: str


# ── 4. Final Pipeline output ──────────────────────────────────────────────────

class PipelineResult(BaseModel):
    run_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    transcript_file: str
    insights: MeetingInsights
    content: GeneratedContent
    quality: QualityReport
    output_files: List[str] = Field(default_factory=list)
