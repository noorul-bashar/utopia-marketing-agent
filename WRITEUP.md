# Utopia Marketing Agent — Writeup
**Marketing & Events · M7 Go-to-Market**

---

## Operator & problem

The operator is the Marketing Lead at Utopia Studio — in the transcript, that is Noor Malik. After every studio meeting recorded in Granola, Noor reads the full transcript manually, decides what is safe to share publicly, and writes a LinkedIn post, a follow-up email, and a press angle from scratch. In the Week 3 Founder Check-In, Noor said out loud: "I have everything I need for the content" — then had to go write it herself. That is 2–3 hours of skilled work per meeting, done inconsistently depending on who has bandwidth. The agent gives Noor three publish-ready pieces in under 90 seconds, without her reading a single line of transcript.

---

## The agent

The agent takes a raw Granola transcript (exported as .txt) as input and runs it through three sequential agents: a Parser that extracts structured insights and seals internal pain points behind a privacy firewall, a Generator that writes three M7 outputs mapped to LAUNCH stages in the studio voice (declarative, specific, no hedging), and a Quality Checker that scores each piece 1–10 and auto-rewrites anything below 7. It calls the Gemini API for all three agents, posts live stage-by-stage updates to Slack, and saves five files to disk — including a structured JSON that a downstream agent (Linear issue creator, Google Sheets logger) can read without a human in the middle.

---

## Sample input

```
Zoom Transcript
Meeting: Utopia Studio — Founder Check-In Week 3
Date: May 14, 2025  10:00 AM (GMT+3 Doha)
Host: Sara Al-Farsi

00:00:51 Rami Hassan: The most valuable call was with Sarah Al-Mansouri.
She's VP of Logistics at Agility Qatar. She shared that they lose
approximately 15 percent of their pharmaceutical shipments annually to
temperature breaks during delivery. The cost in spoilage alone is
QAR 4.2 million per year. That's one company.

00:01:31 Rami Hassan: Yes. She said if we can get alert latency under
two minutes she'd commit 40 vehicles to a 90-day pilot on the Doha to
Al Khor corridor. She also offered us warm introductions to Milaha and
Qatar Cool. Both have the same problem. That offer was completely unprompted.

00:01:49 Noor Malik: Getting referrals on a discovery call before you
have a product is a sign that the market really wants this solved.
That's the story we should be telling publicly this week.

00:03:13 Rami Hassan: Yes I'm taking it [the top-up funding]. After the
calibration setback and the developer gap it's clear I need the runway.
Missing the Agility pilot window would be far more expensive than the dilution.
```

*(Full transcript: `samples/transcript_zoom.txt`)*

---

## Sample output

**LinkedIn Post** *(LAUNCH stage: Amplify — score: 10/10)*
```
Agility Qatar loses QAR 4.2 million annually in pharma shipments
to temperature breaks.

This is a problem Utopia Studio founders target. Rami Hassan's
real-time cargo visibility solution directly addresses this QAR 4.2
million annual loss. His technology tracks temperature, ensuring
critical goods remain viable.

Sarah Al-Mansouri, VP of Logistics at Agility Qatar, confirmed strong
interest in a 90-day pilot for 40 vehicles. This validates the urgent
market need and the effectiveness of Rami's approach. A successful pilot
leads to a commercial contract and introductions to Milaha and Qatar Cool.

Our model supports founders building solutions for specific, high-value
industry problems. Rami's progress exemplifies this: securing a major
pilot, validating market demand, and accelerating product development
with top-up funding. Utopia Studio backs founders who build companies
that matter.

Founders: Build a company addressing real market pain. Connect with
Utopia Studio.

#VentureStudio #FounderSuccess #DohaTech #LogisticsTech
#RealTimeTracking #QatarInnovation #StartupFunding #SupplyChain
```

**Follow-up Email** *(LAUNCH stage: Nurture — score: 10/10)*
```
Subject: Top-up funding & Agility pilot next steps
Preview: Finalizing top-up funding and Agility pilot details. Next steps for G1.
──────────────────────────────────────────────────
Hi [First Name],

Great work securing strong interest from Sarah Al-Mansouri at Agility
Qatar. Your decision to accept the top-up funding accelerates our
ability to capitalize on this pilot opportunity.

This funding ensures you finalize the automated rerouting logic and
secure the embedded systems expertise needed. Delivering zero undetected
temperature exceedances during the pilot leads directly to a commercial
contract.

Ahmed will send the top-up paperwork. Let's ensure the Agility pilot
structure is ready for the G1 review on May 28th.

Best,
[Your Name]
Utopia Studio
```

**Press Angle** *(LAUNCH stage: Lead — score: 10/10)*
```
Utopia Studio founder Rami Hassan secured a 90-day pilot with Agility
Qatar, targeting QAR 4.2 million in annual losses from temperature breaks.
```

**Quality:** Overall 10/10 — ready_to_send: true

**Slack messages received live during the run:**
```
🟡 Starting — Run ID: 848b37d0 | Transcript: transcript_zoom.txt
🔍 Parsed — Utopia Studio — Founder Check-In Week 3 · 5 highlights found
✍️  Generated — hook: "Agility Qatar loses QAR 4.2 million..."
✅ Complete — 10.0/10 · READY TO SEND
```

**Machine-readable JSON (pipeline_result_848b37d0.json — next agent reads this):**
```json
{
  "run_id": "848b37d0",
  "insights": {
    "meeting_title": "Utopia Studio — Founder Check-In Week 3",
    "key_decisions": [
      "Rami Hassan will take the top-up funding.",
      "Ahmed Khalil will prepare top-up paperwork by Wednesday.",
      "G1 review provisionally set for May 28th."
    ],
    "highlights": [
      "Sarah Al-Mansouri confirmed 90-day pilot for 40 vehicles.",
      "Agility Qatar loses QAR 4.2M annually to temperature breaks.",
      "Unprompted referrals to Milaha and Qatar Cool on discovery call."
    ]
  },
  "content": {
    "linkedin_post": {
      "launch_stage": "Amplify",
      "hook": "Agility Qatar loses QAR 4.2 million annually in pharma shipments to temperature breaks."
    },
    "press_angle": "Utopia Studio founder Rami Hassan secured a 90-day pilot with Agility Qatar, targeting QAR 4.2 million in annual losses from temperature breaks.",
    "follow_up_email": {
      "launch_stage": "Nurture",
      "subject": "Top-up funding & Agility pilot next steps"
    }
  },
  "quality": {
    "overall_score": 10.0,
    "ready_to_send": true
  }
}
```

---

## What you cut

- **LinkedIn API auto-posting.** The agent stages the post and notifies Slack. A studio brand publishing without human sign-off is a reputational risk — the right boundary is produce, not publish autonomously. One line of code adds it when trust is established.
- **Granola API integration.** Granola does not expose a public API. The agent accepts the exported `.txt` file directly, which is Granola's actual workflow. A file-watcher that auto-triggers on new exports in a watched folder is the obvious next step and takes one afternoon.
- **Cold outreach email.** M7 specifies exactly three outputs. A fourth output adds noise and dilutes the signal. Cut to stay precise and match the brief.

---

## What broke or surprised you

- **HTTP 503 crashed the pipeline with no retry.** During live testing, Gemini returned 503 (Service Overloaded) mid-pipeline at the content generation step. The original code crashed immediately. Fixed with exponential backoff: 5s → 10s → 20s → 40s → 80s. The agent recovered on attempt 2 with zero data loss. This is the failure mode that kills demos — handling it made the agent production-grade and is visible in the live terminal logs.
- **JSON truncation is silent without checking finishReason.** First run returned broken JSON because `max_tokens` was 2000. Gemini stopped mid-string with no error message — just a truncated response. Fixed by reading the `finishReason` field (must be `STOP`, not `MAX_TOKENS`) and raising immediately. Raised `max_tokens` to 8192. Added a `_repair_truncated_json()` fallback that walks open braces and closes them correctly.
- **Pain points leak into public content without a firewall.** First draft passed all meeting insights to the generator. Internal problems — "four-day calibration delay", "developer gap" — appeared in draft LinkedIn posts. Fixed: `pain_points` are extracted by the parser and never passed downstream to the generator.

---

## If you had two more days

- **Granola file-watcher.** Watch a local folder for new `.md` exports, trigger the pipeline automatically, push three outputs to Slack within 5 minutes of a meeting ending. This makes it zero-touch — the agent runs before Noor closes her laptop.
- **Linear issue creation.** Action items extracted by the parser (Ahmed: developer shortlist by Friday, Rami: rerouting logic, Noor: LinkedIn post today) auto-create Linear issues with owner and due date. The JSON is already structured for this — it needs one API call to close the loop with Utopia OS.
- **Post memory.** The agent has no memory of what has been published. The same highlight could appear in three consecutive posts. A lightweight log (one JSON file or one Notion row per run) prevents repetition across the week.
