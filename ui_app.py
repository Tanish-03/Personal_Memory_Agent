import streamlit as st
import sys
import os

# --- Ensure local package path is included ---
sys.path.append(os.path.join(os.path.dirname(__file__)))

# --- Local imports from sibling modules ---
from main_email_agent import fetch_latest_emails, extract_memory, intent_model

# --- UI Setup ---
st.set_page_config(page_title="🧠 Email Memory Agent", layout="wide")
st.title("📬 Personal Email Memory & Intent Agent")

n = st.slider("How many recent emails to analyze?", 1, 10, 3)

if st.button("🔍 Fetch and Analyze Emails"):
    with st.spinner("Fetching and analyzing emails..."):
        emails = fetch_latest_emails(n=n)

        if not emails:
            st.warning("No emails found or failed to connect.")
        else:
            for i, email in enumerate(emails, 1):
                st.subheader(f"📧 Email {i}: {email['subject']}")
                st.markdown(f"**From:** {email['from']} | **Date:** {email['date']}")
                st.markdown("**Email Preview:**")
                st.info(email['body'][:500] + "..." if len(email['body']) > 500 else email['body'])

                summary = extract_memory(email)
                st.markdown("🧠 **Memory Summary:**")
                st.success(summary if summary else "Could not extract summary.")

                intent_class = intent_model.classify_intent(email['body'])
                st.markdown("🎯 **Predicted Intent Class:**")
                st.code(f"Intent Class: {intent_class}", language="yaml")
