import httpx
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def get_page_text(url: str) -> str:
    try:
        response = httpx.get(
            url,
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )

        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.text, "lxml")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()

        text_lower = text.lower()
        if any(phrase in text_lower for phrase in ["enable javascript", "cloudflare", "just a moment", "ddos protection"]):
            return ""

        return text[:3000]

    except Exception:
        return ""


def get_about_page_url(base_url: str) -> str:
    try:
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        candidates = [
            "/about",
            "/about-us",
            "/company",
            "/who-we-are",
            "/our-story",
            "/team",
        ]

        for path in candidates:
            url = urljoin(base, path)
            try:
                response = httpx.head(url, timeout=5, follow_redirects=True)
                if response.status_code < 400:
                    return url
            except Exception:
                continue

        return base_url

    except Exception:
        return base_url


def scrape_company(url: str) -> dict:
    homepage_text = get_page_text(url)

    about_url = get_about_page_url(url)
    about_text = get_page_text(about_url) if about_url != url else ""

    blog_text = ""
    try:
        response = httpx.get(
            url,
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            blog_keywords = ["blog", "news", "insights", "articles", "resources", "updates"]
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].lower()
                if any(kw in href for kw in blog_keywords):
                    blog_url = urljoin(url, a_tag["href"])
                    candidate_text = get_page_text(blog_url)
                    if candidate_text:
                        blog_text = candidate_text
                        break
    except Exception:
        pass

    parts = []
    if homepage_text:
        parts.append(f"HOMEPAGE:\n{homepage_text[:600]}")
    if about_text:
        parts.append(f"ABOUT:\n{about_text[:600]}")
    if blog_text:
        parts.append(f"BLOG/NEWS:\n{blog_text[:600]}")

    combined = "\n\n".join(parts)

    return {
        "homepage": homepage_text,
        "about": about_text,
        "blog": blog_text,
        "combined": combined[:2500],
    }