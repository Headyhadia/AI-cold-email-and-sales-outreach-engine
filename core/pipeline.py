import logging
import time
from core.researcher import build_prospect_context
from core.chain import extract_hook, write_email, generate_subjects, generate_followups

logger = logging.getLogger(__name__)


def generate_email_package(
    prospect_name: str,
    company_name: str,
    website_url: str,
    role: str,
    offer: str,
    tone: str,
    length: str,
    followup_1_day: int = 3,
    followup_2_day: int = 7,
) -> dict:
    start = time.time()
    logger.info(f"Pipeline start — {company_name} / {role}")

    context = build_prospect_context(website_url, company_name, role)
    logger.info(f"Step 1 done — context: {len(context)} chars")

    hook = extract_hook(context, role, offer)
    logger.info("Step 2 done — hook extracted")

    email_body = write_email(prospect_name, role, company_name, hook, offer, tone, length)
    logger.info("Step 3 done — email written")

    subjects = generate_subjects(email_body, company_name)
    logger.info("Step 4 done — subjects generated")

    followups = generate_followups(email_body, followup_1_day, followup_2_day)
    logger.info("Step 5 done — follow-ups generated")

    elapsed = round(time.time() - start, 2)
    logger.info(f"Pipeline complete in {elapsed}s")

    return {
        "hook":             hook,
        "email_body":       email_body,
        "subjects":         subjects,
        "followup_1":       followups["followup_1"],
        "followup_2":       followups["followup_2"],
        "elapsed_seconds":  elapsed,
    }