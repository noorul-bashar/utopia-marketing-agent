"""
test_slack.py — Verify your Slack webhook is working before running the full pipeline.

Usage:
  python test_slack.py

You should see a test message appear in your Slack channel within 2 seconds.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from tools.slack_notifier import SlackNotifier


def main():
    webhook = os.environ.get("SLACK_WEBHOOK_URL", "")

    if not webhook:
        print("❌  SLACK_WEBHOOK_URL is not set.")
        print()
        print("Set it first:")
        print("  Mac/Linux:  export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...")
        print("  Windows PS: $env:SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/...'")
        sys.exit(1)

    print(f"🔗  Testing webhook: {webhook[:50]}...")

    notifier = SlackNotifier(webhook_url=webhook)
    ok = notifier._send(blocks=[
        notifier._header("🧪  Slack Connection Test — Utopia Marketing Agent"),
        notifier._section(
            "If you see this, your webhook is working correctly.\n\n"
            "Run the agent now:\n"
            "```python main.py samples/sample_transcript.txt```"
        ),
        notifier.context("Sent from test_slack.py"),
    ])

    if ok:
        print("✅  Message sent! Check your Slack channel.")
    else:
        print("❌  Send failed — check the webhook URL and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
