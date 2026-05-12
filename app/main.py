import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")

import streamlit as st
from core.pipeline import generate_email_package
from core.chain import generate_subjects
from app.components import copyable_block, subject_card
from utils.db import (
    sign_up, sign_in, sign_out, restore_session,
    load_preferences, save_preferences,
    save_template, load_templates, delete_template,
    is_at_limit, increment_usage,
    FREE_TIER_LIMIT,
)


# ── PAGE CONFIG ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Cold Email & Sales Outreach Engine",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── CSS ───────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
section[data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
.stCode pre {
    max-height: none !important;
    white-space: pre-wrap !important;
    word-break: break-word !important;
    overflow: visible !important;
}
.stCode { border: 1px solid rgba(128,128,128,0.18); border-radius: 6px; }
.stCaption { margin-bottom: 2px !important; }
.stButton > button[data-testid="baseButton-primary"] {
    padding-left: 2.5rem;
    padding-right: 2.5rem;
}
</style>
""", unsafe_allow_html=True)


# ── SESSION STATE INIT ────────────────────────────────────────────────────────
# All keys initialized once. Widgets with matching keys read these as defaults.

_defaults = {
    "user":          None,
    "access_token":  None,
    "refresh_token": None,
    "result":        None,
    "last_inputs":   {},
    "prefs_loaded":  False,
    "is_paid":       False,
    "templates":     [],
    "offer":         "",
    "tone":          "direct",
    "length":        "short (5-6 lines)",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── RESTORE SESSION ───────────────────────────────────────────────────────────
# On every rerun, re-attach the stored tokens to the Supabase client.
# If this is skipped, RLS treats every DB call as anonymous and blocks it.

if st.session_state["access_token"]:
    restore_session(
        st.session_state["access_token"],
        st.session_state["refresh_token"],
    )


# ══════════════════════════════════════════════════════════════════════════════
# AUTH SCREEN
# ══════════════════════════════════════════════════════════════════════════════

def render_auth_screen() -> None:
    _, col, _ = st.columns([1, 1.4, 1])

    with col:
        st.markdown("## ✉️ AI Cold Email & Sales Outreach Engine")
        st.caption("Sign in or create an account to get started.")
        st.divider()

        tab_in, tab_up = st.tabs(["Sign in", "Create account"])

        with tab_in:
            email_in = st.text_input(
                "Email", key="signin_email", placeholder="you@example.com"
            )
            pass_in = st.text_input(
                "Password", type="password", key="signin_password"
            )

            if st.button(
                "Sign in", type="primary", use_container_width=True, key="signin_btn"
            ):
                if not email_in.strip() or not pass_in:
                    st.warning("Enter your email and password.")
                else:
                    try:
                        response = sign_in(email_in.strip(), pass_in)
                        st.session_state["user"]          = response.user
                        st.session_state["access_token"]  = response.session.access_token
                        st.session_state["refresh_token"] = response.session.refresh_token
                        st.rerun()
                    except Exception as e:
                        st.error(f"Sign in failed — {e}")

        with tab_up:
            email_up = st.text_input(
                "Email", key="signup_email", placeholder="you@example.com"
            )
            pass_up = st.text_input(
                "Password", type="password", key="signup_password",
                help="Minimum 6 characters"
            )

            if st.button(
                "Create account", type="primary",
                use_container_width=True, key="signup_btn"
            ):
                if not email_up.strip() or not pass_up:
                    st.warning("Enter your email and password.")
                elif len(pass_up) < 6:
                    st.warning("Password must be at least 6 characters.")
                else:
                    try:
                        sign_up(email_up.strip(), pass_up)
                        st.success(
                            "Account created. Check your inbox to confirm your "
                            "email, then sign in."
                        )
                    except Exception as e:
                        st.error(f"Sign up failed — {e}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

def render_main_app() -> None:
    user    = st.session_state["user"]
    user_id = user.id

    # ── Load preferences once per login session ───────────────────────────────
    if not st.session_state["prefs_loaded"]:
        prefs = load_preferences(user_id)
        if prefs:
            st.session_state["offer"]   = prefs.get("offer_text", "") or ""
            st.session_state["tone"]    = prefs.get("default_tone", "direct")
            st.session_state["length"]  = prefs.get("default_length", "short (5-6 lines)")
            st.session_state["is_paid"] = prefs.get("is_paid", False)
        st.session_state["templates"]    = load_templates(user_id)
        st.session_state["prefs_loaded"] = True

    is_paid          = st.session_state["is_paid"]
    at_limit, today_count = is_at_limit(user_id, is_paid)

    # ── SIDEBAR ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.caption(f"Signed in as {user.email}")

        if st.button("Sign out", use_container_width=True):
            sign_out()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

        st.divider()

        # Widgets read their value from st.session_state[key],
        # which was pre-populated from the DB in load_preferences above.
        offer = st.text_area(
            "Your offer / product",
            placeholder=(
                "e.g. We help B2B SaaS teams reduce churn by building "
                "async onboarding flows — no engineering overhead."
            ),
            height=140,
            key="offer",
        )

        tone = st.selectbox(
            "Tone",
            options=["casual", "direct", "formal", "consultative"],
            key="tone",
        )

        length = st.selectbox(
            "Email length",
            options=["ultra-short (3 lines)", "short (5-6 lines)", "full (8-10 lines)"],
            key="length",
        )

        st.divider()
        st.caption("FOLLOW-UP TIMING")

        followup_1_day = st.number_input(
            "Follow-up 1 (send on day)",
            min_value=1, max_value=30, value=3, step=1, key="followup_1_day",
        )
        followup_2_day = st.number_input(
            "Follow-up 2 (send on day)",
            min_value=2, max_value=60, value=7, step=1, key="followup_2_day",
        )

        follow_up_days_valid = int(followup_2_day) > int(followup_1_day)
        if not follow_up_days_valid:
            st.warning("Follow-up 2 must be after Follow-up 1.")

        # ── Usage meter ───────────────────────────────────────────────────────
        st.divider()
        if is_paid:
            st.caption("✅ Paid plan — unlimited emails")
        else:
            remaining = max(0, FREE_TIER_LIMIT - today_count)
            st.caption(f"FREE TIER · {remaining} of {FREE_TIER_LIMIT} emails left today")
            if at_limit:
                st.warning(
                    f"Daily limit of {FREE_TIER_LIMIT} emails reached. "
                    "Contact us to upgrade."
                )

        # ── Template library ──────────────────────────────────────────────────
        templates = st.session_state.get("templates", [])
        if templates:
            st.divider()
            st.caption("SAVED TEMPLATES")

            for tmpl in templates:
                with st.expander(tmpl["name"]):
                    if tmpl.get("company_name"):
                        st.caption(
                            f"{tmpl.get('prospect_name', '')} · "
                            f"{tmpl['company_name']}"
                        )

                    if st.button("Load", key=f"load_{tmpl['id']}"):
                        st.session_state["result"] = {
                            "hook":             tmpl.get("hook", ""),
                            "email_body":       tmpl.get("email_body", ""),
                            "followup_1":       tmpl.get("followup_1", ""),
                            "followup_2":       tmpl.get("followup_2", ""),
                            "subjects":         tmpl.get("subjects") or {
                                                    "curiosity": "",
                                                    "direct":    "",
                                                    "question":  "",
                                                },
                            "elapsed_seconds":  None,
                        }
                        st.session_state["last_inputs"] = {
                            "company_name":   tmpl.get("company_name", ""),
                            "followup_1_day": 3,
                            "followup_2_day": 7,
                        }
                        st.rerun()

                    if st.button("Delete", key=f"del_{tmpl['id']}"):
                        delete_template(tmpl["id"])
                        st.session_state["templates"] = load_templates(user_id)
                        st.rerun()

        if st.session_state["result"]:
            st.divider()
            if st.button("Clear results", use_container_width=True):
                st.session_state["result"] = None
                st.session_state["last_inputs"] = {}
                st.rerun()

    # ── MAIN AREA ─────────────────────────────────────────────────────────────
    st.markdown("## AI Cold Email & Sales Outreach Engine")
    st.caption("Paste a company URL — get a personalized cold email + follow-up sequence.")
    st.divider()

    # ── INPUT FORM ────────────────────────────────────────────────────────────
    col_left, col_right = st.columns(2)

    with col_left:
        prospect_name = st.text_input(
            "Prospect name", placeholder="James", key="prospect_name"
        )
        company_name = st.text_input(
            "Company name", placeholder="PostHog", key="company_name"
        )

    with col_right:
        role = st.text_input(
            "Prospect role / title", placeholder="VP of Engineering", key="role"
        )
        website_url = st.text_input(
            "Company website URL", placeholder="https://posthog.com", key="website_url"
        )

    # ── VALIDATION ────────────────────────────────────────────────────────────
    all_fields_filled = all([
        prospect_name.strip(),
        company_name.strip(),
        role.strip(),
        website_url.strip(),
        offer.strip(),
    ])

    can_generate = all_fields_filled and follow_up_days_valid and not at_limit

    if not offer.strip():
        st.caption("⚠️ Add your offer in the sidebar first.")
    elif at_limit:
        st.caption(f"⚠️ Daily limit of {FREE_TIER_LIMIT} emails reached.")
    elif not all_fields_filled:
        st.caption("Fill in all fields to generate.")

    # ── GENERATE BUTTON ───────────────────────────────────────────────────────
    generate_btn = st.button(
        "Generate Email →", type="primary", disabled=not can_generate
    )

    def normalize_url(url: str) -> str:
        url = url.strip()
        if url and not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url

    # ── PIPELINE CALL ─────────────────────────────────────────────────────────
    if generate_btn:
        st.session_state["result"] = None

        with st.spinner("Researching prospect and generating email sequence… (20–30 seconds)"):
            try:
                result = generate_email_package(
                    prospect_name=prospect_name.strip(),
                    company_name=company_name.strip(),
                    website_url=normalize_url(website_url),
                    role=role.strip(),
                    offer=offer.strip(),
                    tone=tone,
                    length=length,
                    followup_1_day=int(followup_1_day),
                    followup_2_day=int(followup_2_day),
                )
                st.session_state["result"] = result
                st.session_state["last_inputs"] = {
                    "company_name":   company_name.strip(),
                    "followup_1_day": int(followup_1_day),
                    "followup_2_day": int(followup_2_day),
                }

                # Both fire silently — user never sees them
                save_preferences(user_id, offer.strip(), tone, length)
                increment_usage(user_id)

            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                logging.exception("Pipeline error")

    # ── OUTPUT ────────────────────────────────────────────────────────────────
    if st.session_state["result"]:
        result = st.session_state["result"]
        last   = st.session_state.get("last_inputs", {})

        f1_day        = last.get("followup_1_day", int(followup_1_day))
        f2_day        = last.get("followup_2_day", int(followup_2_day))
        saved_company = last.get("company_name", company_name.strip())

        st.divider()

        # Hook + elapsed time
        hook_col, time_col = st.columns([5, 1])
        with hook_col:
            st.caption("PERSONALIZATION HOOK IDENTIFIED")
            st.info(f"💡 {result['hook']}")
        with time_col:
            elapsed = result.get("elapsed_seconds")
            if elapsed:
                st.metric(label="Generated in", value=f"{elapsed}s")

        st.divider()

        # Subject lines
        st.subheader("Subject lines")
        sub_col1, sub_col2, sub_col3 = st.columns(3)
        subject_card(sub_col1, "CURIOSITY", result["subjects"]["curiosity"])
        subject_card(sub_col2, "DIRECT",    result["subjects"]["direct"])
        subject_card(sub_col3, "QUESTION",  result["subjects"]["question"])

        if st.button("↻ Regenerate subject lines"):
            with st.spinner("Generating new subject lines…"):
                try:
                    new_subjects = generate_subjects(
                        result["email_body"], saved_company
                    )
                    st.session_state["result"]["subjects"] = new_subjects
                    st.rerun()
                except Exception as e:
                    st.error(f"Regeneration failed: {e}")

        st.divider()

        # Email tabs
        tab1, tab2, tab3 = st.tabs([
            "Initial email",
            f"Follow-up · Day {f1_day}",
            f"Follow-up · Day {f2_day}",
        ])

        with tab1:
            copyable_block(
                "Click the copy icon in the top-right corner ↓",
                result["email_body"],
            )
            st.divider()
            st.caption("EDIT BEFORE SENDING")
            st.text_area(
                label="edit_email_label",
                value=result["email_body"],
                height=250,
                key="edited_email",
                label_visibility="collapsed",
            )

        with tab2:
            st.caption(
                f"No reply after {f1_day} days — references original, adds a new angle."
            )
            if result.get("followup_1"):
                copyable_block("", result["followup_1"])
            else:
                st.warning("Follow-up 1 not generated — regenerate the full email.")

        with tab3:
            st.caption(
                f"Still no reply at day {f2_day} — pattern interrupt, shorter, different approach."
            )
            if result.get("followup_2"):
                copyable_block("", result["followup_2"])
            else:
                st.warning("Follow-up 2 not generated — regenerate the full email.")

        # ── Template saving ───────────────────────────────────────────────────
        st.divider()
        with st.expander("💾 Save as template"):
            tmpl_name_input = st.text_input(
                "Template name",
                placeholder="e.g. SaaS VP Engineering — direct, short",
                key="tmpl_name_input",
            )
            if st.button("Save template", key="save_tmpl_btn"):
                if not tmpl_name_input.strip():
                    st.warning("Enter a name before saving.")
                else:
                    try:
                        save_template(
                            user_id=user_id,
                            name=tmpl_name_input.strip(),
                            result=result,
                            prospect_name=st.session_state.get("prospect_name", ""),
                            company_name=saved_company,
                            role=st.session_state.get("role", ""),
                        )
                        st.session_state["templates"] = load_templates(user_id)
                        st.success(f'✅ Saved as "{tmpl_name_input.strip()}"')
                    except Exception as e:
                        st.error(f"Could not save template: {e}")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if st.session_state["user"] is None:
    render_auth_screen()
else:
    render_main_app()