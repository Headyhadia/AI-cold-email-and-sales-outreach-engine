# Tavily search + context builder

import os
import re
from datetime import datetime
from tavily import TavilyClient
from core.scraper import scrape_company


client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def search_company_news(company_name: str) -> str:
    current_year = datetime.now().year

    try:
        query = f"{company_name} news updates {current_year}"
        results = client.search(query, max_results=3, search_depth="basic")

        snippets = [
            r.get("content", "")
            for r in results.get("results", [])
            if r.get("content", "").strip()
        ]

        if not snippets:
            return ""

        combined = "\n\n".join(snippets)
        combined = re.sub(r"\s+", " ", combined).strip()

        return combined[:1500]

    except Exception:
        return ""


def build_prospect_context(url: str, company_name: str, role: str) -> str:
    scraped = scrape_company(url)
    scraped_combined = scraped.get("combined", "")

    news = search_company_news(company_name)

    if not scraped_combined and not news:
        raise ValueError(
            f"No data found for '{company_name}'. "
            "Check the URL is correct and publicly accessible."
        )

    parts = []

    if scraped_combined:
        parts.append(f"COMPANY WEBSITE INFO:\n{scraped_combined}")

    if news:
        parts.append(f"RECENT NEWS:\n{news}")

    parts.append(f"PROSPECT ROLE: {role}")

    context = "\n\n".join(parts)

    return context[:4000]