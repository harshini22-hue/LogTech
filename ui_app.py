import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

import streamlit as st
from rca import run_rca

st.set_page_config(
    page_title="LogTech Tool",
    page_icon="🔍",
    layout="centered"
)

st.title("🔍 LogTech Tool")
st.caption("AI-powered RCA with Jira correlation")

desc = st.text_area(
    "Issue Description",
    placeholder="Example: Unable to unlock phone when locked from user settings menu"
)

uploaded_files = st.file_uploader(
    "Upload log files (optional)",
    type=["log", "txt"],
    accept_multiple_files=True
)

if st.button("🔍 Analyze"):
    if not desc and not uploaded_files:
        st.warning("Please provide a description or a log file.")
    else:
        combined_log = []

        if uploaded_files:
            for f in uploaded_files:
                data = f.read()
                combined_log.append(data.decode("utf-8", errors="ignore"))

        log_text = "\n".join(combined_log)

        with st.spinner("Analyzing logs and Jira issues..."):
            result = run_rca(desc, log_text)

        st.subheader(" RCA Result")
        st.markdown(result)

st.caption("© LogTech| Next-Gen RCA Assistant Tool")
