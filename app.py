"""
Streamlit app for the REAL multi-agent reasoning demo.

This app provides a friendly UI to:
- Upload or select the sample_resources.csv manifest
- Run ingest & summarization (uses demo_combined.run_ingest, run_summarize)
- Build corpus and initialize OrchestratorReal
- Ask questions to the multi-agent system and display teaching content
- Evaluate a student's answer against an expected answer

Usage: `streamlit run app.py`

If your environment doesn't expose the `src/` package layout, this app will try to add `src/` to sys.path.
If imports fail, the app shows helpful error messages and offers to run in "mock" mode so you can still try the UI.

"""

import os
import sys
import json
import logging
from typing import List

import pandas as pd
import streamlit as st

# ensure src/ is importable (same logic as original script)
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

logger = logging.getLogger("streamlit_real_agents")
logging.basicConfig(level=logging.INFO)

# Attempt imports from your package. If they fail, provide a clear message and mock fallbacks.
USE_MOCK = False
try:
    from multi_agent_real import OrchestratorReal
    from demo_combined import run_ingest, run_summarize
except Exception as e:
    # Import failed — switch to mock behavior so the UI remains usable for testing
    logger.exception("Failed to import project modules: %s", e)
    USE_MOCK = True

    # Mock implementations (minimal, safe to run) -------------------------------------------------
    class OrchestratorReal:
        def __init__(self, corpus):
            self.corpus = corpus

        def handle_user_question(self, session_id, user_question, student_profile=None):
            # very simple mock response for UI testing
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
        # If a CSV exists, try to load; else return a small sample list
        if os.path.exists(manifest_path):
            df = pd.read_csv(manifest_path)
            records = df.fillna("").to_dict(orient="records")
            # expected fields: id,title,tags,url,size_kb
            return records
        else:
            # sample resources
            return [
                {"id": "r1", "title": "Fractions Intro", "tags": "math", "url": "", "size_kb": 12},
                {"id": "r2", "title": "Addition Basics", "tags": "math", "url": "", "size_kb": 8},
            ]

    def run_summarize(resources, provider="mock", mode="short"):
        # return a mapping id->short summary
        return {r.get("id"): f"(MOCK) Summary for {r.get('title', r.get('id'))}" for r in resources}
    # ----------------------------------------------------------------------------------------------

# ---------------------- Streamlit UI helpers -----------------------------------------------------

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


# ---------------------- Streamlit layout ---------------------------------------------------------

st.set_page_config(page_title="REAL Multi-Agent Demo", layout="wide")
st.title("REAL multi-agent reasoning — Streamlit demo")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Controls")

    manifest_file = st.file_uploader("Upload manifest CSV (optional)", type=["csv"])
    use_sample_button = st.button("Load default sample_resources.csv from data/ (if present)")

    manifest_path_input = st.text_input("Or enter manifest path on server", value=os.path.join("data", "sample_resources.csv"))

    if 'last_manifest' not in st.session_state:
        st.session_state['last_manifest'] = None

    if manifest_file is not None:
        # save uploaded csv to a temporary file in the working directory so run_ingest can read it
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
            st.warning(f"{manifest_path_input} not found on server. The demo will use a mocked sample if imports fail.")

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

    question_list = st.text_area("Ask multiple questions (one per line)", value="what are fractions?\nwhat is addition?")
    ask_batch_btn = st.button("Ask questions (batch)")

    st.markdown("---")
    st.markdown("### Student answer evaluation")
    expected_ans = st.text_input("Expected answer", value="Fractions represent parts of a whole number.")
    student_ans = st.text_input("Student answer to evaluate", value="Fractions are parts of a whole.")
    eval_btn = st.button("Evaluate student answer")

with col2:
    st.header("Output")

    ensure_state_key("resources", [])
    ensure_state_key("summaries", {})
    ensure_state_key("corpus", {})
    ensure_state_key("orch", None)

    # Run ingest & summarize
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
            st.error("Ingest or summarization failed. If you're running this in a different working dir, make sure src/ is on PYTHONPATH and that data/sample_resources.csv exists.")

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
            st.error("Failed to initialize OrchestratorReal. Check imports and paths. Using mock orchestrator instead.")
            st.session_state['orch'] = OrchestratorReal(corpus)

    # Display corpus
    if st.session_state['corpus']:
        st.subheader("Corpus preview")
        # show as dataframe with id,title,tags,size
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

    # Handle single question
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

    # Handle batch questions
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
    st.markdown("### Misc")
    if st.button("Download current corpus as JSON"):
        corpus = st.session_state.get('corpus', {})
        st.download_button("Download corpus JSON", data=json.dumps(corpus, indent=2), file_name="corpus.json")

    if USE_MOCK:
        st.warning("The app is running in MOCK mode because imports from your project failed. This lets you test the UI even if your package isn't importable from this path.")
        st.info("To run with your real code, ensure `src/` contains modules `multi_agent_real.py` and `demo_combined.py` and that `data/sample_resources.csv` exists (or upload a manifest CSV).")

st.sidebar.markdown("---")
st.sidebar.write("Developed to run the REAL multi-agent demo inside Streamlit.\n\nRun: `streamlit run app.py`")

# Footer / quick tips
st.caption("If you get an ImportError for multi_agent_real or demo_combined, check that this script is placed at the project root and that `src/` contains your source modules.")
