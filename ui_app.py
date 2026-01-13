import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.resolve()))

import streamlit as st
from log_parser import parse_log_file
from rca import run_rca


st.set_page_config(
    page_title="LogTech Tool",
    page_icon="🔍",
    layout="centered"
)

st.title("LogTech Tool")
st.caption("AI-powered RCA with Jira correlation")

desc = st.text_area(
    "Issue Description",
)

uploaded_file = st.file_uploader("Upload SIP log", type=["txt"])

parsed_logs = None

if uploaded_file:
    with open("uploaded_log.txt", "wb") as f:
        f.write(uploaded_file.getbuffer())

    parsed_logs = parse_log_file(
        "uploaded_log.txt",
        return_json=True
    )

if st.button("🔍 Analyze"):
    if not desc and not parsed_logs:
        st.warning("Please provide a description or a log file.")
    else:
        with st.spinner("Analyzing logs and Jira issues..."):
            result = run_rca(
                description=desc,
                parsed_logs=parsed_logs
            )

        st.subheader("Result")
        st.markdown(result)


st.caption("© LogTech | Next-Gen RCA Assistant Tool")
