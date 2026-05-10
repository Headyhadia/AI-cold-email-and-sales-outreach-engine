import streamlit as st


def copyable_block(label: str, text: str) -> None:
    """
    Renders a labeled copyable text block.
    st.code() with language=None gives plain text with a copy icon
    built into the top-right corner — no JavaScript or clipboard
    hacks needed.
    """
    if label:
        st.caption(label)
    st.code(text, language=None)


def subject_card(col, type_label: str, subject: str) -> None:
    """
    Renders one subject line card inside a given Streamlit column.
    The column object is passed in so the caller controls layout —
    this function just fills whatever column it's given.
    """
    with col:
        st.caption(type_label)
        st.code(subject, language=None)