

"""
config.py — Central configuration for Utopia Marketing Agent
Uses Google Gemini API (FREE) instead of Anthropic.
 
Get your free Gemini API key at:
  https://aistudio.google.com/app/apikey
  Sign in with Google → Create API Key → Copy
 
Set it:
  Mac/Linux : export GEMINI_API_KEY=AIza...
  Windows   : $env:GEMINI_API_KEY = "AIza..."
"""
 
import os
from dataclasses import dataclass, field
 
 
@dataclass
class AgentConfig:
    # ── Google Gemini (FREE) ───────────────────────────────────
    gemini_api_key: str = field(
        default_factory=lambda: os.environ.get("GEMINI_API_KEY", "")
    )
    model: str = field(
        default_factory=lambda: os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    )
    max_tokens: int = 8192          # was 2000 — parser JSON alone can exceed 2k tokens
    temperature: float = 0.7
 
    # ── Pipeline behaviour ─────────────────────────────────────
    max_retries: int = 5               # was 3 — 503s need more attempts
    retry_delay_seconds: float = 5.0   # was 2.0 — gives Gemini time to recover
 
    # ── Slack (optional) ───────────────────────────────────────
    slack_webhook_url: str = field(
        default_factory=lambda: os.environ.get("SLACK_WEBHOOK_URL", "")
    )
    slack_channel: str = "#marketing-outputs"
 
    # ── I/O paths ──────────────────────────────────────────────
    output_dir: str = "output"
    samples_dir: str = "samples"
 
    def validate(self) -> None:
        """Fail fast with a clear message if API key is missing."""
        if not self.gemini_api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set.\n"
                "1. Get free key: https://aistudio.google.com/app/apikey\n"
                "2. Run: export GEMINI_API_KEY=AIza..."
            )
 
 
# Singleton — import this everywhere
config = AgentConfig()
 