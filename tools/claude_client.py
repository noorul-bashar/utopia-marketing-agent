"""
tools/claude_client.py — AI client using Google Gemini (FREE).

Drop-in replacement for the original Anthropic client.
Same interface: complete() and complete_json() — nothing else changes.

Free tier limits (Gemini 1.5 Flash):
  • 15 requests/minute
  • 1,000,000 tokens/day
  • No credit card required

Get your key at: https://aistudio.google.com/app/apikey
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.request
import urllib.error
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel
from config import config

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)


class ClaudeClient:
    """
    Gemini-backed AI client with same interface as original Anthropic client.
    Name kept as ClaudeClient so zero other files need changing.
    """

    # ── Core call ──────────────────────────────────────────────────────────────

    def complete(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.7,
        max_tokens: int = 8192,
    ) -> str:
        """Call Gemini and return the raw text response."""
        config.validate()

        temperature = temperature if temperature is not None else config.temperature
        max_tokens  = max_tokens  if max_tokens  is not None else config.max_tokens

        url = GEMINI_URL.format(model=config.model, key=config.gemini_api_key)

        payload = {
            "system_instruction": {
                "parts": [{"text": system}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": user}]}
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        last_error: Optional[Exception] = None

        for attempt in range(1, config.max_retries + 1):
            try:
                t0 = time.perf_counter()
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read().decode("utf-8"))

                latency = time.perf_counter() - t0

                candidate = result["candidates"][0]

                # ── Critical: check why Gemini stopped generating ──────────────
                finish_reason = candidate.get("finishReason", "STOP")
                if finish_reason == "MAX_TOKENS":
                    # Response was cut off — increasing max_tokens in config.py fixes this
                    raise RuntimeError(
                        f"Gemini truncated the response (MAX_TOKENS hit).\n"
                        f"Fix: increase max_tokens in config.py (currently {config.max_tokens}).\n"
                        f"Gemini 2.5 Flash supports up to 65 536 output tokens."
                    )
                if finish_reason not in ("STOP", "END_OF_TURN", ""):
                    logger.warning("Unexpected finishReason: %s", finish_reason)

                text = candidate["content"]["parts"][0]["text"]
                logger.info(
                    "Gemini call OK | attempt=%d latency=%.2fs finishReason=%s",
                    attempt, latency, finish_reason,
                )
                return text

            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="ignore")

                # Retryable errors: 429 rate limit, 503 overloaded, 500 transient
                if e.code in (429, 500, 503):
                    wait = config.retry_delay_seconds * (2 ** (attempt - 1))
                    reason = {
                        429: "Rate limit",
                        500: "Server error",
                        503: "Service overloaded",
                    }[e.code]
                    logger.warning(
                        "%s (HTTP %d) — retrying in %.1fs (attempt %d/%d)",
                        reason, e.code, wait, attempt, config.max_retries,
                    )
                    time.sleep(wait)
                    last_error = e
                else:
                    logger.error("Gemini HTTP %d: %s", e.code, body[:200])
                    raise RuntimeError(
                        f"Gemini API error {e.code}: {body[:200]}"
                    ) from e

            except Exception as e:
                logger.error("Gemini call failed: %s", e)
                raise

        raise RuntimeError(
            f"Gemini call failed after {config.max_retries} retries"
        ) from last_error

    # ── Structured JSON extraction ─────────────────────────────────────────────

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        schema: Type[T],
        temperature: float = 0.3,
    ) -> T:
        """
        Call Gemini and parse the response into a Pydantic model.
        Uses max_tokens from config (must be high enough — 8192 recommended).
        """
        raw = self.complete(system=system, user=user, temperature=temperature,
                            max_tokens=config.max_tokens)
        data = self._extract_json(raw)
        return schema.model_validate(data)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_json(text: str) -> Dict[str, Any]:
        """
        Robustly extract JSON from model output.

        Handles:
          1. Markdown fences  (```json ... ```)
          2. Preamble text    ("Here is the JSON: {...}")
          3. Truncated JSON   (model cut off mid-string — attempts repair)
        """
        # Step 1: strip markdown code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`").strip()

        # Step 2: find the first { and the last } — greedy outer match
        start = cleaned.find("{")
        if start == -1:
            logger.error("No JSON object found in response:\n%s", text)
            raise ValueError("Model returned no JSON object. Full response logged above.")

        # Try from outermost braces first
        last_brace = cleaned.rfind("}")
        if last_brace != -1 and last_brace > start:
            candidate = cleaned[start:last_brace + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass  # fall through to repair

        # Step 3: Truncation repair — response was cut off before closing braces
        # Count unclosed braces and quotes, then close them
        candidate = cleaned[start:]
        logger.warning(
            "JSON appears truncated (no valid closing brace). "
            "Attempting repair. Check max_tokens in config.py."
        )

        repaired = _repair_truncated_json(candidate)
        try:
            result = json.loads(repaired)
            logger.info("JSON repaired successfully after truncation")
            return result
        except json.JSONDecodeError as e:
            logger.error(
                "JSON repair failed.\n"
                "Root cause: response was truncated (max_tokens too low).\n"
                "Fix: increase max_tokens in config.py to 8192 or higher.\n"
                "Raw text:\n%s",
                text,
            )
            raise ValueError(
                f"Model returned truncated JSON (max_tokens too low). "
                f"Increase max_tokens in config.py. Detail: {e}"
            ) from e


def _repair_truncated_json(text: str) -> str:
    """
    Best-effort repair of a JSON string truncated mid-stream.

    Strategy:
      - Track open braces { and [
      - If we're inside a string when truncated, escape bad chars and close it
      - Close all open arrays and objects in reverse order
      - Strip trailing commas before closing (invalid JSON)
    """
    in_string = False
    escape_next = False
    open_stack = []   # tracks '{' and '['

    for i, ch in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch in ("{", "["):
                open_stack.append(ch)
            elif ch in ("}", "]"):
                if open_stack:
                    open_stack.pop()

    # Strip trailing whitespace and newlines from the raw text
    text = text.rstrip()

    # If we ended mid-string, the last characters may include raw newlines
    # which are illegal inside JSON strings — replace with a space
    if in_string:
        # Replace any raw newline at the very tail of the open string
        text = text.replace("\n", " ").replace("\r", " ")

    # Remove trailing comma before closing (invalid JSON)
    if text.endswith(","):
        text = text[:-1]

    # Build the closing suffix
    suffix = ""
    if in_string:
        suffix += '"'   # close the open string
    for opener in reversed(open_stack):
        suffix += "}" if opener == "{" else "]"

    return text + suffix


# Module-level singleton
claude = ClaudeClient()