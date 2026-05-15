# Utopia Marketing Agent
**Marketing & Events · M7 Go-to-Market · Utopia Studio Fellowship Submission**

Takes a raw Granola meeting transcript and produces — in one run, in under 90 seconds — a LinkedIn post, a personalised follow-up email, and a press-angle sentence, all quality-checked and mapped to the LAUNCH framework.

---

## How to run it

```bash
# 1. Install
pip install -r requirements.txt

# 2. Set API keys
# Windows PowerShell:
$env:GEMINI_API_KEY = "AIza..."
$env:SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."  # optional

# Mac / Linux:
export GEMINI_API_KEY=AIza...
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...

# 3. Run on the sample Granola transcript
python main.py samples/transcript_zoom.txt

# 4. Run on any Granola export
python main.py path/to/your/granola_export.txt
```

---

## Pipeline

```
Granola transcript (.txt)
        │
        ▼
┌───────────────────────┐
│  Agent 1 · Parser     │  Extracts highlights, decisions, action items
│  temp = 0.3           │  pain_points sealed — never reach the generator
└──────────┬────────────┘
           │ MeetingInsights (Pydantic)
           ▼
┌───────────────────────┐
│  Agent 2 · Generator  │  Writes 3 M7 outputs, each mapped to a LAUNCH stage
│  temp = 0.75          │  Voice enforced: declarative, specific, no hedging
└──────────┬────────────┘
           │ GeneratedContent (Pydantic)
           ▼
┌───────────────────────┐
│  Agent 3 · Checker    │  Scores 1–10 per piece, auto-revises below 7
│  temp = 0.2           │  ready_to_send: true only if all scores ≥ 7
└──────────┬────────────┘
           ▼
  linkedin_post_*.txt        ← copy → paste → post
  email_followup_*.txt       ← personalise → send
  press_angle_*.txt          ← send to journalist
  marketing_bundle_*.md      ← full report with scores
  pipeline_result_*.json     ← structured output, next Utopia OS agent reads this
```

---

## Prompts used

**Agent 1 — Parser** (`prompts/parser_prompt.py`)

Extracts JSON: meeting title, attendees, key decisions, action items, public highlights, private pain_points. System prompt instructs strict extraction — no invention. `pain_points` are extracted but never passed to Agent 2. `temperature=0.3` for deterministic output.

**Agent 2 — Generator** (`prompts/content_prompt.py`)

System prompt embeds the full LAUNCH framework (Lead, Amplify, Unify, Nurture, Convert, Harvest) and the studio voice rules verbatim: *declarative, specific, no hedging, opinions not summaries*. Banned words listed explicitly. Each output asset must declare its LAUNCH stage. `temperature=0.75` for creative copy.

**Agent 3 — Checker** (`prompts/quality_prompt.py`)

Scores LinkedIn post: hook strength (30%), declarative voice (30%), specific claims (20%), CTA (20%). Scores press angle: newsworthiness (40%), real number or name present (40%), under 30 words (20%). Any score below 7 requires a `revised_version`. `temperature=0.2` for consistent scoring.

---

## Tools and APIs called

| Tool | Purpose |
|------|---------|
| Gemini API (`gemini-2.5-flash`) | All three agents — parse, generate, quality-check |
| Slack Incoming Webhook | 4 live stage notifications per run (started, parsed, generated, complete) |
| Local filesystem | 5 output files per run saved to `output/` |

---

## Output files

| File | Who uses it | Format |
|------|------------|--------|
| `linkedin_post_*.txt` | Marketing Lead — paste to LinkedIn | Plain text |
| `email_followup_*.txt` | Marketing Lead — personalise and send | Plain text |
| `press_angle_*.txt` | Marketing Lead — send to journalist | Plain text |
| `marketing_bundle_*.md` | Full report with LAUNCH stages and quality scores | Markdown |
| `pipeline_result_*.json` | Next agent in Utopia OS | JSON |

---

## Project structure

```
├── main.py                      # CLI entrypoint
├── config.py                    # All env vars in one place
├── requirements.txt
│
├── agents/
│   ├── transcript_parser.py     # Agent 1 — Parser
│   ├── content_generator.py     # Agent 2 — Generator
│   └── quality_checker.py       # Agent 3 — Quality Checker
│
├── models/
│   └── schemas.py               # Pydantic contracts between agents
│
├── prompts/
│   ├── parser_prompt.py         # Extraction prompt
│   ├── content_prompt.py        # LAUNCH framework + voice rules
│   └── quality_prompt.py        # M7 scoring criteria
│
├── tools/
│   ├── claude_client.py         # Gemini wrapper — retry, finishReason check, JSON repair
│   ├── file_handler.py          # All disk I/O
│   └── slack_notifier.py        # 4 stage notifications per run
│
└── samples/
    ├── transcript_zoom.txt      # Utopia Studio Founder Check-In Week 3 (best run: 10/10)
    ├── transcript_googlemeet.txt
    └── transcript_teams.txt
```

---

## Environment variables

| Variable | Required | Notes |
|----------|----------|-------|
| `GEMINI_API_KEY` | Yes | Free at aistudio.google.com/app/apikey |
| `SLACK_WEBHOOK_URL` | No | api.slack.com/apps → Incoming Webhooks |
