# AI Cold Email & Sales Outreach Engine

A personalized AI cold email & Sales Outreach generation tool powered by LLaMA 3.3 via Groq, Tavily search, and web scraping. Paste a prospect's company URL and receive a fully researched, personalized cold email with subject line variants and a follow-up sequence — in under 30 seconds.

Built with Streamlit. Deployed on Streamlit Cloud.

---

## Overview

Generic cold emails get ignored. This tool solves that by researching each prospect's company in real time — scraping their website, pulling recent news, and extracting a specific personalization hook — before writing a single word of the email.

The result is an email that references something real about the recipient's company, written in a tone and length you control, with three subject line variants and two follow-ups ready to go.

---

## Features

- **Real-time research** — scrapes the prospect's homepage, About page, and blog, then queries Tavily for recent news coverage
- **4-stage LangChain prompt chain** — hook extraction → email writing → subject line generation → follow-up sequence
- **Personalization hook identification** — isolates the single most compelling research detail before writing begins
- **Subject line A/B variants** — generates Curiosity, Direct, and Question variants with one-click regeneration
- **Follow-up sequence** — Day 3 and Day 7 follow-ups with configurable timing, each using a different angle
- **Tone and length control** — casual, direct, formal, or consultative; ultra-short through full-length
- **In-app editing** — edit the generated email before copying
- **Template library** — save and reload generated emails across sessions
- **User authentication** — Supabase Auth with persistent browser sessions
- **Usage tracking** — free tier gate of 5 emails per day with per-user daily counters
- **Offer persistence** — sidebar settings and offer text saved per user and pre-loaded on next login

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| LLM inference | Groq API — LLaMA 3.3 70B Versatile |
| Prompt orchestration | LangChain |
| Web research | Tavily Search API |
| Web scraping | httpx + BeautifulSoup4 |
| Database + Auth | Supabase (PostgreSQL + GoTrue) |
| Session persistence | streamlit-cookies-controller |
| Deployment | Streamlit Cloud |

---

## Project Structure

```
cold-email-engine/
├── app/
│   ├── main.py              # Streamlit entrypoint
│   └── components.py        # Reusable UI blocks
├── core/
│   ├── scraper.py           # Web scraper (httpx + BeautifulSoup)
│   ├── researcher.py        # Tavily search + context builder
│   ├── chain.py             # LangChain LLM calls (4 stages)
│   └── pipeline.py          # Master orchestrator function
├── prompts/
│   ├── hook.py              # Stage 1 — hook extractor prompt
│   ├── email.py             # Stage 2 — email writer prompt
│   ├── subjects.py          # Stage 3 — subject line generator prompt
│   └── followups.py         # Stage 4 — follow-up sequence prompt
├── utils/
│   ├── db.py                # Supabase client + all DB helpers
│   └── parsers.py           # LLM output parsers
├── supabase/
│   └── schema.sql           # Database schema (run once in Supabase SQL Editor)
├── tests/
│   ├── test_scraper.py
│   ├── test_researcher.py
│   └── test_chain.py
├── .env.example
├── requirements.txt
└── config.py
```

---

## Local Setup

### Prerequisites

- Python 3.10 or higher
- A [Groq](https://console.groq.com) account — free, instant API key
- A [Tavily](https://tavily.com) account — free tier, 1,000 searches/month
- A [Supabase](https://supabase.com) project — free tier

### 1. Clone and install

```bash
git clone https://github.com/Headyhadia/AI-cold-email-and-sales-outreach-engine
cd cold-email-engine
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in all four values:

```
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly-...
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=eyJ...
```

### 3. Set up the database

1. Open your Supabase project → **SQL Editor** → **New query**
2. Paste the contents of `supabase/schema.sql`
3. Click **Run**

This creates the `user_preferences`, `saved_templates`, and `usage_log` tables with Row Level Security policies applied.

### 4. Configure Supabase Auth

1. Supabase Dashboard → **Authentication** → **Settings**
2. Set **Site URL** to `http://localhost:8501`
3. For local development, disable **Email Confirmations** under **Email** provider settings so you can sign in immediately without confirming your inbox

### 5. Run

```bash
streamlit run app/main.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Environment Variables

| Variable | Description | Where to find it |
|---|---|---|
| `GROQ_API_KEY` | Groq API key for LLM inference | [console.groq.com](https://console.groq.com) → API Keys |
| `TAVILY_API_KEY` | Tavily API key for web search | [tavily.com](https://tavily.com) → Dashboard |
| `SUPABASE_URL` | Supabase project URL | Supabase → Settings → API → Project URL |
| `SUPABASE_ANON_KEY` | Supabase anonymous public key | Supabase → Settings → API → anon public |

---

## How It Works

### The 4-stage prompt chain

Each email generation runs four sequential LLM calls, each building on the previous output:

**Stage 1 — Hook Extractor**
Takes the scraped website content and recent news as input. Identifies the single most compelling personalization hook — a specific recent event, achievement, or detail that makes the email feel researched rather than templated.

**Stage 2 — Email Writer**
Takes the hook, offer description, prospect details, tone, and length target. Writes the email body with the hook woven into the opening line naturally. Banned phrases list enforced at the prompt level.

**Stage 3 — Subject Line Generator**
Takes the completed email body and generates three variants: a curiosity-driven line, a direct value-prop line under 7 words, and a question-based line specific to the prospect's situation.

**Stage 4 — Follow-up Generator**
Takes the original email and generates two follow-ups at configurable day intervals. Follow-up 1 references the original and adds a new angle. Follow-up 2 is a pattern interrupt — shorter, different approach entirely.

### Research pipeline

Before any LLM call, `build_prospect_context()` assembles a research brief:

1. Scrapes homepage, About page, and first blog post via httpx + BeautifulSoup
2. Strips navigation, footers, scripts, and bot-detection pages
3. Queries Tavily for the current year's news on the company
4. Combines both into a structured 4,000-character context string with labeled sections

---

## Usage Notes

- **Free tier limit** — 5 email generations per calendar day per user. Resets at midnight.
- **Pipeline time** — typically 20–30 seconds depending on Groq inference speed and Tavily response time
- **JS-rendered sites** — companies whose websites are fully client-side rendered (SPAs with no server-side HTML) will return limited scrape data. Tavily news coverage compensates for most cases.
- **Tavily quota** — the free tier provides 1,000 searches per month. Each email generation uses 1 search.

---

## Future Enhancements

### Planned — next phase

**Bulk mode** — upload a CSV of prospects (name, company, URL, role) and generate a full email sequence for each row in sequence, with a progress bar and downloadable output CSV.

**Gmail API integration** — connect your Gmail account via OAuth and send the generated email directly from the tool without copying to your email client.

### Under consideration

**Stripe payment integration** — self-serve upgrade flow that sets `is_paid = true` in the database after successful checkout, removing the daily generation limit automatically.

**A/B subject line tracking** — record which subject line variant was used per email and surface open rate data if the user connects their email provider.

**Sequence scheduler** — set send dates for the initial email and both follow-ups. Integrates with Gmail API to queue them automatically rather than requiring manual sends on day 3 and day 7.

**Team workspaces** — shared offer library and template library across multiple users on the same account. Relevant for sales teams where multiple reps use the same product positioning.

**Analytics dashboard** — per-user view of emails generated, templates saved, and (if Gmail connected) reply rates by hook type, tone, and length.

**Chrome extension** — trigger email generation directly from a LinkedIn profile page without opening the tool separately.
