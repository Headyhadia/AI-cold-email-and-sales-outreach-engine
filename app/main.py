import sys
import os
import logging

# Must be first — before any project imports.
# Streamlit adds the /app directory to sys.path, not the project root.
# Without this, "from core.pipeline import ..." would fail with ModuleNotFoundError.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")

import streamlit as st
from core.pipeline import generate_email_package
from core.chain import generate_subjects
from app.components import copyable_block, subject_card


# ── PAGE CONFIG ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Cold Email Engine",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── CUSTOM CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Reduce top padding in sidebar */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1.5rem;
}
/* Give code blocks a subtle border so they read as "output" containers */
.stCode {
    border: 1px solid rgba(128, 128, 128, 0.18);
    border-radius: 6px;
}
/* Tighten space between caption and the element below it */
.stCaption {
    margin-bottom: 2px !important;
}
/* Widen the generate button padding */
.stButton > button[data-testid="baseButton-primary"] {
    padding-left: 2.5rem;
    padding-right: 2.5rem;
}
</style>
""", unsafe_allow_html=True)


# ── SESSION STATE INIT ───────────────────────────────────────────────────────
# Initialize keys once. After this, Streamlit manages them across reruns.
# Never assume a key exists without initializing it here first.

if "result" not in st.session_state:
    st.session_state["result"] = None

if "last_inputs" not in st.session_state:
    st.session_state["last_inputs"] = {}


# ── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    st.divider()

    offer = st.text_area(
        "Your offer / product",
        placeholder=(
            "e.g. We help B2B SaaS teams reduce churn by building "
            "async onboarding flows — without adding engineering overhead."
        ),
        height=140,
        key="offer",
    )

    tone = st.selectbox(
        "Tone",
        options=["casual", "direct", "formal", "consultative"],
        index=1,
        key="tone",
    )

    length = st.selectbox(
        "Email length",
        options=["ultra-short (3 lines)", "short (5-6 lines)", "full (8-10 lines)"],
        index=1,
        key="length",
    )

    st.divider()
    st.caption("FOLLOW-UP TIMING")

    followup_1_day = st.number_input(
        "Follow-up 1 (send on day)",
        min_value=1,
        max_value=30,
        value=3,
        step=1,
        key="followup_1_day",
    )

    followup_2_day = st.number_input(
        "Follow-up 2 (send on day)",
        min_value=2,
        max_value=60,
        value=7,
        step=1,
        key="followup_2_day",
    )

    follow_up_days_valid = int(followup_2_day) > int(followup_1_day)
    if not follow_up_days_valid:
        st.warning("Follow-up 2 must be after Follow-up 1.")

    st.divider()

    # Clear button — only shown when there's a result to clear
    if st.session_state["result"]:
        if st.button("Clear results", use_container_width=True):
            st.session_state["result"] = None
            st.session_state["last_inputs"] = {}
            st.rerun()


# ── MAIN AREA ────────────────────────────────────────────────────────────────

st.markdown("## Cold Email & Sales Outreach Engine")
st.caption("Paste a company URL — get a personalized cold email + follow-up sequence.")
st.divider()


# ── INPUT FORM ───────────────────────────────────────────────────────────────

col_left, col_right = st.columns(2)

with col_left:
    prospect_name = st.text_input(
        "Prospect name",
        placeholder="James",
        key="prospect_name",
    )
    company_name = st.text_input(
        "Company name",
        placeholder="PostHog",
        key="company_name",
    )

with col_right:
    role = st.text_input(
        "Prospect role / title",
        placeholder="VP of Engineering",
        key="role",
    )
    website_url = st.text_input(
        "Company website URL",
        placeholder="https://posthog.com",
        key="website_url",
    )


# ── VALIDATION ───────────────────────────────────────────────────────────────

all_fields_filled = all([
    prospect_name.strip(),
    company_name.strip(),
    role.strip(),
    website_url.strip(),
    offer.strip(),
])

can_generate = all_fields_filled and follow_up_days_valid

if not offer.strip():
    st.caption("⚠️ Add your offer in the sidebar before generating.")
elif not all_fields_filled:
    st.caption("Fill in all fields above to generate.")


# ── GENERATE BUTTON ──────────────────────────────────────────────────────────

generate_btn = st.button(
    "Generate Email →",
    type="primary",
    disabled=not can_generate,
)


# ── URL NORMALIZATION ────────────────────────────────────────────────────────

def normalize_url(url: str) -> str:
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


# ── PIPELINE CALL ────────────────────────────────────────────────────────────

if generate_btn:
    # Clear any previous result immediately so stale data never bleeds through
    st.session_state["result"] = None

    normalized_url = normalize_url(website_url)

    with st.spinner("Researching prospect and generating email sequence… (10–20 seconds)"):
        try:
            result = generate_email_package(
                prospect_name=prospect_name.strip(),
                company_name=company_name.strip(),
                website_url=normalized_url,
                role=role.strip(),
                offer=offer.strip(),
                tone=tone,
                length=length,
                followup_1_day=int(followup_1_day),
                followup_2_day=int(followup_2_day),
            )
            st.session_state["result"] = result
            st.session_state["last_inputs"] = {
                "company_name": company_name.strip(),
                "followup_1_day": int(followup_1_day),
                "followup_2_day": int(followup_2_day),
            }
        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Something went wrong: {e}")
            logging.exception("Pipeline error")


# ── OUTPUT SECTION ───────────────────────────────────────────────────────────

if st.session_state["result"]:
    result = st.session_state["result"]
    last = st.session_state.get("last_inputs", {})

    # Read saved values — these are what was used to generate the current result.
    # Don't use the live sidebar values here; the user may have changed them
    # after generating without regenerating.
    f1_day = last.get("followup_1_day", int(followup_1_day))
    f2_day = last.get("followup_2_day", int(followup_2_day))
    saved_company = last.get("company_name", company_name.strip())

    st.divider()

    # ── Hook + elapsed time ──
    hook_col, time_col = st.columns([5, 1])
    with hook_col:
        st.caption("PERSONALIZATION HOOK IDENTIFIED")
        st.info(f"💡 {result['hook']}")
    with time_col:
        elapsed = result.get("elapsed_seconds")
        if elapsed:
            st.metric(label="Generated in", value=f"{elapsed}s")

    st.divider()

    # ── Subject lines ────────────────────────────────────────────────────────
    st.subheader("Subject lines")

    sub_col1, sub_col2, sub_col3 = st.columns(3)
    subject_card(sub_col1, "CURIOSITY", result["subjects"]["curiosity"])
    subject_card(sub_col2, "DIRECT",    result["subjects"]["direct"])
    subject_card(sub_col3, "QUESTION",  result["subjects"]["question"])

    if st.button("↻ Regenerate subject lines"):
        with st.spinner("Generating new subject lines…"):
            try:
                new_subjects = generate_subjects(
                    email_body=result["email_body"],
                    company_name=saved_company,
                )
                st.session_state["result"]["subjects"] = new_subjects
                st.rerun()
            except Exception as e:
                st.error(f"Regeneration failed: {e}")

    st.divider()

    # ── Email tabs ───────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "Initial email",
        f"Follow-up · Day {f1_day}",
        f"Follow-up · Day {f2_day}",
    ])

    with tab1:
        copyable_block(
            "Click the copy icon in the top-right corner of the block below ↓",
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
            f"No reply after {f1_day} days? "
            "This references your original email and adds one new angle."
        )
        if result.get("followup_1"):
            copyable_block("", result["followup_1"])
        else:
            st.warning("Follow-up 1 was not generated. Regenerate the full email.")

    with tab3:
        st.caption(
            f"Still no reply by day {f2_day}? "
            "Pattern interrupt — completely different approach, shorter, more casual."
        )
        if result.get("followup_2"):
            copyable_block("", result["followup_2"])
        else:
            st.warning("Follow-up 2 was not generated. Regenerate the full email.")