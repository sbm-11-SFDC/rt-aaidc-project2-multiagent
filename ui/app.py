# ui/app.py

import os
import sys

# Make project root importable as a package
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from pathlib import Path  # (currently not used, but harmless if you want to log paths)

import streamlit as st
from dotenv import load_dotenv

from src.app import run_review_workflow
from src.tools import validate_repo_url, sanitize_text
from src.logging_utils import get_logger

logger = get_logger("ui")

# Load environment variables (e.g., GOOGLE_API_KEY)
load_dotenv()

st.set_page_config(
    page_title="Multi-Agent Publication Reviewer",
    layout="wide",
)

st.title("🧠 Multi-Agent Publication Reviewer & Recommendation System")
st.write(
    "Analyze a GitHub repository's README and receive AI-generated, "
    "multi-agent review suggestions with human-in-the-loop refinement."
)

# Sidebar configuration
st.sidebar.header("Configuration")
default_repo = "https://github.com/sbm-11-SFDC/rt-aaidc-project1-template"
repo_url = st.sidebar.text_input("GitHub Repo URL", value=default_repo)

model_name = st.sidebar.text_input("LLM Model", value="gemini-2.5-flash")
hitl_notes = st.sidebar.text_area(
    "Optional Human Reviewer Notes (HITL)",
    help="You can add your own comments or constraints that will be appended to the AI recommendations.",
)

st.sidebar.info(
    "Make sure your GOOGLE_API_KEY is set in a local .env file before running the app."
)

if st.button("🔍 Analyze Repository"):
    if not validate_repo_url(repo_url):
        st.error("Please enter a valid GitHub repo URL (https://github.com/owner/repo).")
    else:
        with st.spinner("Running multi-agent analysis..."):
            try:
                result = run_review_workflow(
                    repo_url=repo_url,
                    human_feedback=hitl_notes,
                    model_name=model_name,
                )
                final_text = result.get("final_recommendations", "")
                keywords = result.get("keywords", [])

                # Main layout
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader("📋 Final Recommendations")
                    st.write(sanitize_text(final_text, max_len=4500))

                with col2:
                    st.subheader("🔑 Extracted Keywords")
                    if keywords:
                        for k in keywords:
                            st.markdown(f"- {k}")
                    else:
                        st.write("No keywords extracted.")

                st.success("Analysis complete. Scroll to review the suggestions.")

            except Exception as e:
                logger.exception(f"UI error: {e}")
                st.error(
                    "An error occurred while analyzing the repository. "
                    "Please check your configuration and try again."
                )

# Footer
st.markdown("---")
st.caption(
    "Built as part of the Agentic AI Developer Certification (AAIDC) – Module 3. "
    "This is a productionized version of the Module 2 multi-agent system."
)