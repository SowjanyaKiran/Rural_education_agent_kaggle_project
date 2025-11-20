# app.py
"""
Streamlit UI for the run_real_agents multi-agent demo.

Run with:
    streamlit run app.py
or:
    python -m streamlit run app.py
"""

import streamlit as st
import sys
import os
import logging
from typing import Dict, Any

st.set_page_config(page_title="Rural Education Agent — Multi-Agent Demo", layout="wide")

# ensure src/ is importable
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Debug info
st.sidebar.markdown("**Project Root:** `%s`" % ROOT)
st.sidebar.markdown("**src path:** `%s`" % SRC)

# Logger
logger = logging.getLogger("streamlit_app")
logger.setLevel(logging.INFO)

# Importing main modules
try:
    from multi_agent_real import OrchestratorReal
except Exception as e:
    st.error("Missing file: src/multi_agent_real.py (required for OrchestratorReal)")
    st.exception(e)
    st.stop()

try:
    from demo_combined import run_ingest, run_summarize
except Exception as e:
    st.error("Missing file: demo_combined.py (must contain run_ingest & run_summarize)")
    st.exception(e)
    st.stop()


# ==================  SIDEBAR  ==================
st.sidebar.header("Options & Settings")

manifest_path = st.sidebar.text_input("Resource CSV path:", "data/sample_resources.csv")
generate_on_start = st.sidebar.checkbox("Auto-generate summaries on load", True)
top_k = st.sidebar.number_input("Retriever top_k", 1, 10, 5)

st.sidebar.markdown("---")
session_id = st.sidebar.text_input("Session ID", "student_demo_session")
grade = st.sidebar.number_input("Student grade", 1, 12, 6)

st.sidebar.markdown("---")
show_corpus = st.sidebar.checkbox("Show Corpus")
show_summaries = st.sidebar.checkbox("Show Summaries")


# ================== LOAD RESOURCES ==================
st.title("🌾 Rural Education Agent — Multi-Agent Reasoning (Streamlit)")
st.subheader("1
