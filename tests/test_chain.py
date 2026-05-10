import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")

from core.chain import extract_hook, write_email, generate_subjects, generate_followups
from core.pipeline import generate_email_package

FAKE_CONTEXT = """COMPANY WEBSITE INFO:
PostHog is an open-source product analytics platform. They help \
engineering teams understand user behavior without sending data to \
third parties. Recently launched session replay and feature flags \
as part of their all-in-one suite. Self-hosted or cloud options.

RECENT NEWS:
PostHog raised a $25M Series B and announced a new data warehouse \
integration allowing teams to sync product data directly to BigQuery \
and Snowflake without a separate ETL tool.

PROSPECT ROLE: VP of Engineering"""

OFFER = "We build async onboarding flows that reduce time-to-value for \
B2B SaaS products by 40% — without adding engineering overhead."


# --- Test each stage individually ---

print("\n" + "=" * 60)
print("TEST 1 — extract_hook()")
print("=" * 60)
hook = extract_hook(FAKE_CONTEXT, "VP of Engineering", OFFER)
print(f"Hook: {hook}\n")


print("=" * 60)
print("TEST 2 — write_email()")
print("=" * 60)
email = write_email(
    name="James",
    role="VP of Engineering",
    company="PostHog",
    hook=hook,
    offer=OFFER,
    tone="direct",
    length="short (5-6 lines)",
)
print(f"Email:\n{email}\n")


print("=" * 60)
print("TEST 3 — generate_subjects()")
print("=" * 60)
subjects = generate_subjects(email, "PostHog")
print(f"CURIOSITY : {subjects['curiosity']}")
print(f"DIRECT    : {subjects['direct']}")
print(f"QUESTION  : {subjects['question']}\n")


print("=" * 60)
print("TEST 4 — generate_followups() — custom days")
print("=" * 60)
followups = generate_followups(email, followup_1_day=4, followup_2_day=10)
print(f"Follow-up 1 (day 4):\n{followups['followup_1']}\n")
print(f"Follow-up 2 (day 10):\n{followups['followup_2']}\n")


# --- Test full pipeline ---

print("=" * 60)
print("TEST 5 — generate_email_package() full pipeline")
print("=" * 60)
result = generate_email_package(
    prospect_name="James",
    company_name="PostHog",
    website_url="https://posthog.com",
    role="VP of Engineering",
    offer=OFFER,
    tone="direct",
    length="short (5-6 lines)",
    followup_1_day=3,
    followup_2_day=7,
)

print(f"Hook        : {result['hook']}")
print(f"Subjects    : {result['subjects']}")
print(f"Email body  :\n{result['email_body']}")
print(f"Follow-up 1 :\n{result['followup_1']}")
print(f"Follow-up 2 :\n{result['followup_2']}")
print(f"Time        : {result['elapsed_seconds']}s")