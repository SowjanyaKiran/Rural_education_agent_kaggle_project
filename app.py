"""
Streamlit app for the REAL multi-agent reasoning demo.

Two-column (40/60) clean layout:
- Left column: Controls
- Right column: Output + corpus preview

Run:
    streamlit run app.py
"""

import os
import sys
import json
import logging
from typing import List

import pandas as pd
import streamlit as st

# ------------------------------------------------------------------
# Make src/ importable
# ------------------------------------------------------------------

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streamlit_real_agents")

# ------------------------------------------------------------------
# Try imports, fallback to mock mode
# ------------------------------------------------------------------

USE_MOCK = False
try:
    from multi_agent_real import OrchestratorReal
    from demo_combined import run_ingest, run_summarize
except Exception as e:
    logger.error(f"Import failed, switching to MOCK mode: {e}")
    USE_MOCK = True

    # sample images supplied by user
    IMG1 = "/mnt/data/af86c628-12c0-410b-b0d6-59ce9f87d5f8.png"
    IMG2 = "/mnt/data/5d88c9b3-8270-4492-b788-0475c1a1bd74.png"
    IMG3 = "/mnt/data/6fcf2d31-69c6-437c-88ee-7a89bfa9d798.png"

    # ---------------- MOCK IMPLEMENTATIONS ----------------

    class OrchestratorReal:
        def __init__(self, corpus):
            self.corpus = corpus

        def handle_user_question(self, session_id, user_question, student_profile=None):
            return {
                "answer": f"(MOCK) Short answer: {user_question}",
                "teaching": {
                    "explanation": f"(MOCK) Explanation for: {user_question}",
                    "examples": [f"(MOCK) Ex 1: {user_question}", f"(MOCK) Ex 2: {user_question}"],
                    "practice": [{"q": f"(MOCK) What is {user_question}?", "a": "(MOCK) expected"}],
                },
            }

        def assess_student_answer(self, session_id, student_answer, expected_answer):
            correct = student_answer.strip().lower() == expected_answer.strip().lower()
            return {
                "score": 1.0 if correct else 0.0,
                "correct": correct,
                "feedback": "Good job!" if correct else "Try again with more detail.",
            }

    def run_ingest(csv_path):
        if csv_path and os.path.exists(csv_path) and csv_path.endswith(".csv"):
            df = pd.read_csv(csv_path).fillna("")
            return df.to_dict(orient="records")

        # fallback sample resources
        return [
            {"id": "r1", "title": "Fractions Intro", "tags": "math", "url": IMG1, "size_kb": 12},
            {"id": "r2", "title": "Addition Basics", "tags": "math", "url": IMG2, "size_kb": 8},
            {"id": "r3", "title": "Kannada Alphabets", "tags": "language", "url": IMG3, "size_kb": 15},
        ]

    def run_summarize(resources, provider="mock", mode="short"):
        return {r["id"]: f"(MOCK) Summary for {r['title']}" for r in resources}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def build_corpus(resources, summaries):
    corpus = {}
    for r in resources:
        rid = r.get("id")
        corpus[rid] = {
            "title": r.get("title", ""),
            "tags": r.get("tags", ""),
            "summary": summaries.get(rid, ""),
            "meta": {
                "url": r.get("url"),
                "size_kb": r.get("size_kb", 0),
            },
        }
    return corpus


def ensure_state(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default


# ------------------------------------------------------------------
# Streamlit UI
# ------------------------------------------------------------------

st.set_page_config(page_title="REAL Multi-Agent Demo", layout="wide")
st.title("REAL multi-agent reasoning — Streamlit demo")

left, right = st.columns([0.4, 0.6])

# ===================== LEFT COLUMN ================================
with left:
    st.header("Controls")

    manifest_file = st.file_uploader("Upload manifest CSV", type=["csv"])
    use_sample = st.button("Use default: data/sample_resources.csv")

    manifest_input = st.text_input(
        "Manifest CSV path",
        value="data/sample_resources.csv",
    )

    if manifest_file:
        tmp = "uploaded_manifest.csv"
        with open(tmp, "wb") as f:
            f.write(manifest_file.getbuffer())
        st.session_state["manifest"] = tmp
        st.success(f"Uploaded → {tmp}")

    if use_sample:
        st.session_state["manifest"] = manifest_input
        st.success(f"Using → {manifest_input}")

    st.markdown("---")
    run_ingest_btn = st.button("Run ingest + summarize")

    st.subheader("Orchestrator settings")
    session_id = st.text_input("Session ID", "student_demo_session")
    grade = st.number_input("Student grade", min_value=1, max_value=12, value=6)
    init_orch = st.button("Initialize Orchestrator")

    st.markdown("---")
    st.subheader("Ask a question")
    single_q = st.text_input("Ask single question")
    ask_single_btn = st.button("Ask")

    st.subheader("Ask multiple questions")
    question_list = st.text_area(
        "One question per line",
        value="what are fractions?\nwhat is addition?",
    )
    ask_batch_btn = st.button("Ask batch")

    st.markdown("---")
    st.subheader("Evaluate student answer")
    expected_ans = st.text_input("Expected answer", "Fractions represent parts of a whole number.")
    student_ans = st.text_input("Student answer", "Fractions are parts of a whole.")
    eval_btn = st.button("Evaluate")

# ===================== RIGHT COLUMN ===============================
with right:
    st.header("Output")

    ensure_state("resources", [])
    ensure_state("summaries", {})
    ensure_state("corpus", {})
    ensure_state("orch", None)

    # ----------------- INGEST + SUMMARIZE -----------------
    if run_ingest_btn:
        src_csv = st.session_state.get("manifest") or manifest_input
        st.info(f"Ingesting from: {src_csv}")

        with st.spinner("Ingesting..."):
            resources = run_ingest(src_csv)
            summaries = run_summarize(resources)
            st.session_state["resources"] = resources
            st.session_state["summaries"] = summaries

        st.success("Done ingest + summarize!")

    # ----------------- INIT ORCHESTRATOR -----------------
    if init_orch:
        resources = st.session_state.get("resources")
        summaries = st.session_state.get("summaries")

        corpus = build_corpus(resources, summaries)
        st.session_state["corpus"] = corpus

        with st.spinner("Initializing orchestrator..."):
            orch = OrchestratorReal(corpus)
            st.session_state["orch"] = orch

        st.success("Orchestrator initialized!")

    # ----------------- CORPUS TABLE -----------------
    if st.session_state["corpus"]:
        st.subheader("Corpus Preview")

        df = pd.DataFrame([
            {
                "id": rid,
                "title": item["title"],
                "tags": item["tags"],
                "summary": item["summary"],
                "size_kb": item["meta"]["size_kb"],
            }
            for rid, item in st.session_state["corpus"].items()
        ])
        st.dataframe(df)

    # ----------------- SINGLE QUESTION -----------------
    if ask_single_btn and single_q.strip():
        orch = st.session_state["orch"]
        if not orch:
            st.error("Orchestrator not initialized")
        else:
            with st.spinner("Answering..."):
                res = orch.handle_user_question(session_id, single_q, {"grade": grade})

            st.subheader("Answer")
            st.write(res["answer"])
            st.subheader("Explanation")
            st.write(res["teaching"]["explanation"])
            st.subheader("Examples")
            for e in res["teaching"]["examples"]:
                st.write("- ", e)

    # ----------------- BATCH QUESTIONS -----------------
    if ask_batch_btn:
        orch = st.session_state["orch"]
        if not orch:
            st.error("Orchestrator not initialized")
        else:
            qs = [q.strip() for q in question_list.splitlines() if q.strip()]
            for q in qs:
                with st.expander(f"Q: {q}"):
                    res = orch.handle_user_question(session_id, q, {"grade": grade})
                    st.write("**Answer:** ", res["answer"])
                    st.write("**Explanation:** ", res["teaching"]["explanation"])

    # ----------------- EVALUATE -----------------
    if eval_btn:
        orch = st.session_state["orch"]
        if not orch:
            st.error("Orchestrator not initialized")
        else:
            with st.spinner("Evaluating..."):
                fb = orch.assess_student_answer(session_id, student_ans, expected_ans)

            st.subheader("Evaluation Result")
            st.write("Score:", fb["score"])
            st.write("Correct:", fb["correct"])
            st.write("Feedback:", fb["feedback"])

# ----------------- FOOTER -----------------
if USE_MOCK:
    st.warning("Running in MOCK MODE — real modules not found.")
