import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from core.researcher import search_company_news, build_prospect_context

# --- Test 1: news search alone ---

print("=" * 60)
print("TEST 1 — search_company_news()")
print("=" * 60)

news_tests = ["Stripe", "Linear", "Posthog"]

for company in news_tests:
    print(f"\nCompany: {company}")
    result = search_company_news(company)
    print(f"Length : {len(result)} chars")
    print(f"Preview: {result[:300]}")
    print()

# --- Test 2: full context builder ---

print("=" * 60)
print("TEST 2 — build_prospect_context()")
print("=" * 60)

context_tests = [
    {
        "url": "https://cal.com",
        "company_name": "Cal.com",
        "role": "Head of Growth",
    },
    {
        "url": "https://resend.com",
        "company_name": "Resend",
        "role": "CTO",
    },
    {
        "url": "https://posthog.com",
        "company_name": "PostHog",
        "role": "VP of Engineering",
    },
]

for test in context_tests:
    print(f"\nCompany : {test['company_name']}")
    print(f"Role    : {test['role']}")
    try:
        context = build_prospect_context(
            url=test["url"],
            company_name=test["company_name"],
            role=test["role"],
        )
        print(f"Length  : {len(context)} chars")
        print(f"Preview :\n{context[:500]}")
    except ValueError as e:
        print(f"ERROR   : {e}")
    print()