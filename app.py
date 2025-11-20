"""
Streamlit app for the REAL multi-agent reasoning demo.

This is a cleaned-up two-column (40/60) layout version optimized to avoid stretching and overflow.
- Left column: controls (narrow, scrollable)
- Right column: outputs, corpus preview and detailed teaching view

Features:
- Robust import fallback to MOCK mode
- Load manifest CSV or use embedded sample resources (with local image paths)
- Corpus preview with optional image thumbnails (uses local file paths when present)
- Proper session-state usage and balanced 40/60 layout

Run: streamlit run app.py
"""

import os
import sys
import json
import logging
from typing import List

import pandas as pd
import streamlit as st

# ensure src/ is importable
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

logger = logging.getLogger("streamlit_real_agents")
logging.basicConfig(level=logging.INFO)

USE_MOCK = False
try:
    from multi_agent_real import OrchestratorReal
    from demo_combined import run_ingest, run_summarize
except Exception as e:
    logger.exception("Failed to import project modules: %s", e)
    USE_MOCK = True

    # Local file URLs (images uploaded in the session) — developer provided paths
    SAMPLE_IMAGE_1 = "/mnt/data/af86c628-12c0-410b-b0d6-59ce9f87d5f8.png"
    SAMPLE_IMAGE_2 = "/mnt/data/5d88c9b3-8270-4492-b788-0475c1a1bd74.png"
    SAMPLE_IMAGE_3 = "/mnt/data/6fcf2d31-69c6-437c-88ee-7a89bfa9d798.png"

    class OrchestratorReal:
        def __init__(self, corpus):
            self.corpus = corpus

        def handle_user_question(self, session_id, user_question, student_profile=None):
            return {
                "answer": f"(MOCK) Short answer to: {user_question}",
                "teaching": {
                    "explanation": f"(MOCK) Explanation for: {user_question}",
                    "examples": [f"(MOCK) Example 1 for {user_question}", f"(MOCK) Example 2 for {user_question}"],
                    "practice": [{"q": f"(MOCK) Practice: What is {user_question}?", "a": "(MOCK) expected"}]
                }
            }

        def assess_student_answer(self, session_id, student_answer, expected_answer):
            correct = student_answer.strip().lower() == expected_answer.strip().lower()
            return {
                "score": 1.0 if correct else 0.0,
                "correct": correct,
                "feedback": "Good job!" if correct else "Try to mention the parts of the definition."
            }

    def run_ingest(manifest_path: str) -> List[dict]:
        # If CSV exists, load it. Otherwise return a small sample with local image URLs provided by developer.
        if manifest_path and os.path.exists(manifest_path) and manifest_path.lower().endswith('.csv'):
            df = pd.read_csv(manifest_path)
            return df.fillna("").to_dict(orient="records")
        # fallback sample resources — note the 'url' fields use local paths that your environment can transform.
        return [
            {"id": "r1", "title": "Fractions Intro", "tags": "math", "url": SAMPLE_IMAGE_1, "size_kb": 12},
            {"id": "r2", "title": "Addition Basics", "tags": "math", "url": SAMPLE_IMAGE_2, "size_kb": 8},
            {"id": "r3", "title": "Kannada Alphabets", "tags": "language", "url": SAMPLE_IMAGE_3, "size_kb": 15},
        ]

    def run_summarize(resources, provider="mock", mode="short"):
        return {r.get("id"): f"(MOCK) Summary for {r.get('title', r.get('id'))}" for r in resources}

# Helpers

def build_corpus_from_resources(resources, summaries):
    corpus = {}
    for r in resources:
        rid = r.get("id") or r.get("name") or str(hash(json.dumps(r)))
        corpus[rid] = {
            "title": r.get("title", ""),
            "tags": r.get("tags", ""),
            "summary": summaries.get(rid, ""),
            "meta": {
                "url": r.get("url"),
                "size_kb": r.get("size_kb", 0)
            }
        }
    return corpus


def ensure_state_key(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default


# App layout
st.set_page_config(page_title="REAL Multi-Agent Demo", layout="wide")
st.title("REAL multi-agent reasoning — Streamlit demo")

# Two-column balanced layout: controls (40%) | output (60%)
col_left, col_right = st.columns([0.4, 0.6])

with col_left:
    st.header("Controls")
    manifest_file = st.file_uploader("Upload manifest CSV (optional)", type=["csv"])
    use_sample_button = st.button("Load default sample_resources.csv from data/ (if present)")
    manifest_path_input = st.text_input("Or enter manifest path on server", value=os.path.join("data", "sample_resources.csv"))

    if manifest_file is not None:
        tmp_path = os.path.join(".", "uploaded_manifest.csv")
        with open(tmp_path, "wb") as f:
            f.write(manifest_file.getbuffer())
        st.session_state['last_manifest'] = tmp_path
        st.success(f"Uploaded manifest saved to {tmp_path}")

    if use_sample_button:
        if os.path.exists(manifest_path_input):
            st.session_state['last_manifest'] = manifest_path_input
            st.success(f"Using manifest: {manifest_path_input}")
        else:
            st.warning(f"{manifest_path_input} not found on server. Using embedded sample resources.")

    st.markdown("---")
    run_ingest_btn = st.button("Run ingest & summarize")

    st.markdown("### Orchestrator settings")
    session_id = st.text_input("Session ID", value="student_demo_session")
    grade = st.number_input("Student grade", min_value=1, max_value=12, value=6)
    init_orch_btn = st.button("Initialize Orchestrator")

    st.markdown("---")
    st.markdown("### Quick actions")
    ask_input = st.text_input("Ask a question (single)")
    ask_btn = st.button("Ask question")

    question_list = st.text_area("Ask multiple questions (one per line)", value="what are fractions?
what is addition?")
    ask_batch_btn = st.button("Ask questions (batch)")

    st.markdown("---")
    st.markdown("### Student answer evaluation")
    expected_ans = st.text_input("Expected answer", value="Fractions represent parts of a whole number.")
    student_ans = st.text_input("Student answer to evaluate", value="Fractions are parts of a whole.")
    eval_btn = st.button("Evaluate student answer")

with col_right:
    st.header("Output")

    ensure_state_key("resources", [])
    ensure_state_key("summaries", {})
    ensure_state_key("corpus", {})
    ensure_state_key("orch", None)

    # Ingest & summarize
    if run_ingest_btn:
        manifest_to_use = st.session_state.get('last_manifest') or manifest_path_input
        st.info(f"Ingesting from: {manifest_to_use}")
        try:
            with st.spinner("Running ingest..."):
                resources = run_ingest(manifest_to_use)
                st.session_state['resources'] = resources
            with st.spinner("Generating summaries..."):
                summaries = run_summarize(resources, provider="mock", mode="short")
                st.session_state['summaries'] = summaries
            st.success("Ingest and summarization completed.")
        except Exception as e:
            st.exception(e)
            st.error("Ingest or summarization failed. Ensure src/ is on PYTHONPATH and data/sample_resources.csv exists.")

    # Initialize orchestrator
    if init_orch_btn:
        resources = st.session_state.get('resources') or []
        summaries = st.session_state.get('summaries') or {}
        if not resources:
            st.warning("No resources found — running ingest automatically with defaults.")
            try:
                resources = run_ingest(manifest_path_input)
                st.session_state['resources'] = resources
                st.session_state['summaries'] = run_summarize(resources, provider="mock", mode="short")
                summaries = st.session_state['summaries']
            except Exception as e:
                st.exception(e)
                st.warning("Falling back to empty corpus.")
                resources = []
                summaries = {}

        corpus = build_corpus_from_resources(resources, summaries)
        st.session_state['corpus'] = corpus
        try:
            with st.spinner("Initializing OrchestratorReal..."):
                orch = OrchestratorReal(corpus)
                st.session_state['orch'] = orch
            st.success("Orchestrator initialized.")
        except Exception as e:
            st.exception(e)
            st.error("Failed to initialize OrchestratorReal. Using mock orchestrator instead.")
            st.session_state['orch'] = OrchestratorReal(corpus)

    # Corpus preview (table + thumbnails)
    if st.session_state['corpus']:
        st.subheader("Corpus preview")
        rows = []
        for rid, item in st.session_state['corpus'].items():
            rows.append({
                "id": rid,
                "title": item.get('title'),
                "tags": item.get('tags'),
                "summary": item.get('summary'),
                "size_kb": item.get('meta', {}).get('size_kb')
            })
        df = pd.DataFrame(rows)
        st.dataframe(df)

        # thumbnails
        st.subheader("Thumbnails (if available)")
        thumb_cols = st.columns(3)
        i = 0
        for rid, item in st.session_state['corpus'].items():
            url = item.get('meta', {}).get('url')
            with thumb_cols[i % 3]:
                st.markdown(f"**{item.get('title')}**")
                if url and os.path.exists(url):
                    st.image(url, use_column_width=True)
                elif url:
                    st.write(f"URL: {url}")
                else:
                    st.write("(no image)")
            i += 1

    # Single question handling
    if ask_btn and ask_input.strip():
        orch = st.session_state.get('orch')
        if orch is None:
            st.warning("Orchestrator not initialized. Initializing now...")
            corpus = st.session_state.get('corpus') or build_corpus_from_resources(st.session_state.get('resources', []), st.session_state.get('summaries', {}))
            st.session_state['orch'] = OrchestratorReal(corpus)
            orch = st.session_state['orch']
        with st.spinner("Getting answer from multi-agent system..."):
            response = orch.handle_user_question(session_id=session_id, user_question=ask_input, student_profile={"grade": int(grade)})
        st.subheader("Answer")
        st.write(response.get('answer'))
        st.subheader("Teaching: Explanation")
        st.write(response.get('teaching', {}).get('explanation'))
        st.subheader("Examples")
        for ex in response.get('teaching', {}).get('examples', []):
            st.write(f"- {ex}")
        st.subheader("Practice")
        for p in response.get('teaching', {}).get('practice', []):
            st.write(f"Q: {p.get('q')} — Expected: {p.get('a')}")

    # Batch questions
    if ask_batch_btn:
        qs = [q.strip() for q in question_list.splitlines() if q.strip()]
        orch = st.session_state.get('orch')
        if orch is None:
            st.warning("Orchestrator not initialized. Initializing now...")
            corpus = st.session_state.get('corpus') or build_corpus_from_resources(st.session_state.get('resources', []), st.session_state.get('summaries', {}))
            st.session_state['orch'] = OrchestratorReal(corpus)
            orch = st.session_state['orch']

        for q in qs:
            with st.expander(f"Question: {q}"):
                response = orch.handle_user_question(session_id=session_id, user_question=q, student_profile={"grade": int(grade)})
                st.write("**Answer**")
                st.write(response.get('answer'))
                st.write("**Explanation**")
                st.write(response.get('teaching', {}).get('explanation'))
                st.write("**Examples**")
                for ex in response.get('teaching', {}).get('examples', []):
                    st.write(f"- {ex}")

    # Evaluate student answer
    if eval_btn:
        orch = st.session_state.get('orch')
        if orch is None:
            st.warning("Orchestrator not initialized. Initializing now...")
            corpus = st.session_state.get('corpus') or build_corpus_from_resources(st.session_state.get('resources', []), st.session_state.get('summaries', {}))
            st.session_state['orch'] = OrchestratorReal(corpus)
            orch = st.session_state['orch']
        with st.spinner("Assessing student answer..."):
            feedback = orch.assess_student_answer(session_id=session_id, student_answer=student_ans, expected_answer=expected_ans)
        st.subheader("Evaluation result")
        st.write(f"Score: {feedback.get('score')}")
        st.write(f"Correct: {feedback.get('correct')}")
        st.write(f"Feedback: {feedback.get('feedback')}")

    st.markdown("---")
    if st.button("Download current corpus as JSON"):
        corpus = st.session_state.get('corpus', {})
        st.download_button("Download corpus JSON", data=json.dumps(corpus, indent=2), file_name="corpus.json")

    if USE_MOCK:
        st.warning("Running in MOCK mode because imports failed. To use your real modules, ensure src/multi_agent_real.py and src/demo_combined.py exist.")

# Sidebar help
st.sidebar.markdown("---")
st.sidebar.write("Developed to run the REAL multi-agent demo inside Streamlit.

Run: `streamlit run app.py`")
st.caption("This layout uses a fixed 40/60 columns ratio to avoid stretching and improve readability.")
