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
    try:
        supabase.auth.set_session(access_token, refresh_token)
    except Exception as e:
        logger.warning(f"restore_session failed: {e}")


def get_user_from_token(access_token: str):
    """
    Validates the stored access token and returns the user object.
    Returns None if the token is expired or invalid.
    Used during cookie-based session restoration on page refresh.
    """
    try:
        return supabase.auth.get_user(access_token)
    except Exception:
        return None


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
        # Guard result itself before accessing .data
        if result is None or result.data is None:
            return {}
        return result.data
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
        if result is None or result.data is None:
            return []
        return result.data
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
        # result itself can be None on first-ever call; result.data is None when no row exists
        if result is None or result.data is None:
            return 0
        return result.data.get("emails_generated", 0)
    except Exception as e:
        logger.warning(f"get_today_count failed: {e}")
        return 0


def increment_usage(user_id: str, current_count: int) -> None:
    """
    Takes the already-known current_count to avoid a second DB read.
    Caller is responsible for passing the cached value.
    """
    try:
        supabase.table("usage_log").upsert(
            {
                "user_id":          user_id,
                "log_date":         date.today().isoformat(),
                "emails_generated": current_count + 1,
            },
            on_conflict="user_id,log_date",
        ).execute()
    except Exception as e:
        logger.warning(f"increment_usage failed: {e}")