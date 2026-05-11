import os
import logging
from datetime import date
from supabase import create_client, Client

logger = logging.getLogger(__name__)

FREE_TIER_LIMIT = 5

supabase: Client = create_client(
    os.getenv("SUPABASE_URL", ""),
    os.getenv("SUPABASE_ANON_KEY", ""),
)


# ── Auth ──────────────────────────────────────────────────────────────────────

def sign_up(email: str, password: str):
    return supabase.auth.sign_up({"email": email, "password": password})


def sign_in(email: str, password: str):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})


def sign_out() -> None:
    try:
        supabase.auth.sign_out()
    except Exception:
        pass


def restore_session(access_token: str, refresh_token: str) -> None:
    """
    Re-attach a user session to the Supabase client on every Streamlit rerun.
    Without this, the client is anonymous and RLS blocks every DB call.
    """
    try:
        supabase.auth.set_session(access_token, refresh_token)
    except Exception as e:
        logger.warning(f"Could not restore session: {e}")


# ── Preferences ───────────────────────────────────────────────────────────────

def load_preferences(user_id: str) -> dict:
    try:
        result = (
            supabase.table("user_preferences")
            .select("*")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        return result.data or {}
    except Exception as e:
        logger.warning(f"load_preferences failed: {e}")
        return {}


def save_preferences(user_id: str, offer: str, tone: str, length: str) -> None:
    try:
        supabase.table("user_preferences").upsert(
            {
                "user_id":        user_id,
                "offer_text":     offer,
                "default_tone":   tone,
                "default_length": length,
            },
            on_conflict="user_id",
        ).execute()
    except Exception as e:
        logger.warning(f"save_preferences failed: {e}")


# ── Templates ─────────────────────────────────────────────────────────────────

def save_template(
    user_id: str,
    name: str,
    result: dict,
    prospect_name: str,
    company_name: str,
    role: str,
) -> None:
    supabase.table("saved_templates").insert(
        {
            "user_id":       user_id,
            "name":          name,
            "prospect_name": prospect_name,
            "company_name":  company_name,
            "role":          role,
            "hook":          result.get("hook", ""),
            "email_body":    result.get("email_body", ""),
            "followup_1":    result.get("followup_1", ""),
            "followup_2":    result.get("followup_2", ""),
            "subjects":      result.get("subjects", {}),
        }
    ).execute()


def load_templates(user_id: str) -> list:
    try:
        result = (
            supabase.table("saved_templates")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.warning(f"load_templates failed: {e}")
        return []


def delete_template(template_id: str) -> None:
    try:
        supabase.table("saved_templates").delete().eq("id", template_id).execute()
    except Exception as e:
        logger.warning(f"delete_template failed: {e}")


# ── Usage tracking ────────────────────────────────────────────────────────────

def get_today_count(user_id: str) -> int:
    try:
        result = (
            supabase.table("usage_log")
            .select("emails_generated")
            .eq("user_id", user_id)
            .eq("log_date", date.today().isoformat())
            .maybe_single()
            .execute()
        )
        return result.data.get("emails_generated", 0) if result.data else 0
    except Exception as e:
        logger.warning(f"get_today_count failed: {e}")
        return 0


def increment_usage(user_id: str) -> None:
    try:
        current = get_today_count(user_id)
        supabase.table("usage_log").upsert(
            {
                "user_id":          user_id,
                "log_date":         date.today().isoformat(),
                "emails_generated": current + 1,
            },
            on_conflict="user_id,log_date",
        ).execute()
    except Exception as e:
        logger.warning(f"increment_usage failed: {e}")


def is_at_limit(user_id: str, is_paid: bool) -> tuple[bool, int]:
    """Returns (at_limit, today_count). Paid users are never at limit."""
    if is_paid:
        return False, 0
    count = get_today_count(user_id)
    return count >= FREE_TIER_LIMIT, count