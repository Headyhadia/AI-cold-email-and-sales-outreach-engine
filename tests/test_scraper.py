import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scraper import scrape_company

test_urls = [
    "https://stripe.com",
    "https://notion.so",
    "https://linear.app",
    "https://vercel.com",
    "https://basecamp.com",
    "https://cal.com",
    "https://posthog.com",
    "https://retool.com",
    "https://clerk.com",
    "https://resend.com",
]

for url in test_urls:
    print(f"\n{'=' * 60}")
    print(f"URL: {url}")
    result = scrape_company(url)
    print(f"Homepage : {len(result['homepage'])} chars")
    print(f"About    : {len(result['about'])} chars")
    print(f"Blog     : {len(result['blog'])} chars")
    print(f"Combined : {len(result['combined'])} chars")
    print(f"\n--- Combined preview (first 400 chars) ---")
    print(result["combined"][:400])
    print()