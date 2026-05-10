import os
import logging
from langchain_groq import ChatGroq
from prompts.hook import HOOK_PROMPT
from prompts.email import EMAIL_PROMPT
from prompts.subjects import SUBJECTS_PROMPT
from prompts.followups import FOLLOWUPS_PROMPT
from utils.parsers import parse_hook, parse_subjects, parse_followups

logger = logging.getLogger(__name__)

_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.4,
    api_key=os.getenv("GROQ_API_KEY"),
)

_llm_creative = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key=os.getenv("GROQ_API_KEY"),
)

LENGTH_MAP = {
    "ultra-short (3 lines)": "ultra-short — 3 sentences maximum, no fluff",
    "short (5-6 lines)":     "short — 5 to 6 sentences",
    "full (8-10 lines)":     "full — 8 to 10 sentences",
}


def extract_hook(context: str, role: str, offer: str) -> str:
    logger.info("Stage 1: Extracting personalization hook...")
    chain = HOOK_PROMPT | _llm
    result = chain.invoke({
        "company_research": context,
        "prospect_role": role,
        "our_offer": offer,
    })
    hook = parse_hook(result.content)
    logger.info(f"Hook extracted: {hook}")
    return hook


def write_email(
    name: str,
    role: str,
    company: str,
    hook: str,
    offer: str,
    tone: str,
    length: str,
) -> str:
    logger.info("Stage 2: Writing email body...")
    length_instruction = LENGTH_MAP.get(length, length)
    chain = EMAIL_PROMPT | _llm
    result = chain.invoke({
        "prospect_name": name,
        "prospect_role": role,
        "company_name": company,
        "hook": hook,
        "our_offer": offer,
        "tone": tone,
        "length": length_instruction,
    })
    return result.content.strip()


def generate_subjects(email_body: str, company_name: str) -> dict:
    logger.info("Stage 3: Generating subject lines...")
    chain = SUBJECTS_PROMPT | _llm_creative
    result = chain.invoke({
        "email_body": email_body,
        "company_name": company_name,
    })
    subjects = parse_subjects(result.content)
    logger.info(f"Subjects: {subjects}")
    return subjects


def generate_followups(
    original_email: str,
    followup_1_day: int = 3,
    followup_2_day: int = 7,
) -> dict:
    logger.info(f"Stage 4: Generating follow-ups (day {followup_1_day} + day {followup_2_day})...")
    chain = FOLLOWUPS_PROMPT | _llm
    result = chain.invoke({
        "original_email": original_email,
        "followup_1_day": followup_1_day,
        "followup_2_day": followup_2_day,
    })
    return parse_followups(result.content)