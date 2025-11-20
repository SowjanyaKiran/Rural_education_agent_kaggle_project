"""
Streamlit front-end for the REAL multi-agent demo.

This adapts your run_real_agents.py to an interactive Streamlit app:
- Load manifest (CSV) or use built-in sample resources
- Run run_ingest and run_summarize from demo_combined
- Build corpus and create OrchestratorReal from multi_agent_real
- Ask single or batch questions and display teaching output
- Evaluate a student's answer (assess_student_answer)

Notes:
- The app will attempt to import your project modules from src/.
- If imports fail, it falls back to safe MOCK implementations so the UI can be tested.
- A sample resource is included whose url points to the local file path shown in your traceback:
  /mount/src/rural_education_agent_kaggle_project/app.py
"""

import os
import sys
import json
import logging
from typing import List

import pandas as pd
import streamlit as st

# ------------------------------------------------------------------
# Ensure src/ is importable (same logic as your original script)
# ------------------------------------------------------------------
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streamlit_real_agents")

# ------------------------------------------------------------------
# Try to import real modules, else use mock fallbacks
# ------------------------------------------------------------------
USE_MOCK = False
try:
    from multi_agent_real import OrchestratorReal
    from demo_combined import run_ingest, run_summarize
except Exception as e:
    logger.exception("Failed to import project modules: %s", e)
    USE_MOCK = True

    # default sample resource uses the uploaded file path you provided earlier.
    # Per developer instruction, include that local path as a resource url.
    UPLOADED_APP_PATH = "/mount/src/rural_education_agent_kaggle_project/app.py"

    class OrchestratorReal:
        def __init__(self, corpus):
            self.corpus = corpus

        def handle_user_question(self, session_id, user_question, student_profile=None):
            # Very simple mock answer and teaching content
            return {
                "answer": f"(MOCK) Short answer to: {user_question}",
                "teaching": {
                    "explanation": f"(MOCK) Explanation for: {user_question}",
                    "examples": [f"(MOCK) Example 1 for {user_question}", f"(MOCK) Example 2 for {user_question}"],
                    "practice": [{"q": f"(MOCK) Practice: What is {user_question}?", "a": "(MOCK) expected"}],
                },
            }

        def assess_student_answer(self, session_id, student_answer, expected_answer):
            correct = student_answer.strip().lower() == expected_answer.strip().lower()
            return {
                "score": 1.0 if correct else 0.0,
                "correct": correct,
                "feedback": "Good! Your answer matches the expected solution closely." if correct else "Try to include the main idea; compare with expected answer.",
            }

    def run_ingest(manifest_path: str) -> List[dict]:
        # If CSV exists at path, load it. Else return fallback sample resources.
        if manifest_path and os.path.exists(manifest_path) and manifest_path.lower().endswith(".csv"):
            df = pd.read_csv(manifest_path)
            return df.fillna("").to_dict(orient="records")

        # fallback resources (id/title/tags/url/size_kb) - url uses the uploaded app path
        return [
            {"id": "r1", "title": "Run Real Agents script (app.py)", "tags": "code,script", "url": UPLOADED_APP_PATH, "size_kb": 10},
            {"id": "r2", "title": "Fractions Intro (sample)", "tags": "math", "url": "", "size_kb": 5},
        ]

    def run_summarize(resources, provider="mock", mode="short"):
        return {r.get("id"): f"(MOCK) Summary for {r.get('title', r.get('id'))}" for r in resources}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def build_corpus_from_resources(resources, summaries):
    corpus = {}
    for r in resources:
        rid = r.get("id") or r.get("title") or str(hash(json.dumps(r)))
        corpus[rid] = {
            "title": r.get("title", ""),
            "tags": r.get("tags", ""),
            "summary": summaries.get(rid, ""),
            "meta": {
                "url": r.get("url"),
                "size_kb": r.get("size_kb", 0),
            }
        }
    return corpus


def ensure_state_key(key, default=None):
    if key not in st.session_state:
        st.session_state[key] = default


# ------------------------------------------------------------------
# Streamlit UI layout (two columns)
# ------------------------------------------------------------------
st.set_page_config(page_title="REAL Multi-Agent Demo", layout="wide")
st.title("REAL multi-agent reasoning — Streamlit demo")

left_col, right_col = st.columns([0.4, 0.6])

with left_col:
    st.header("Controls")

    uploaded_manifest = st.file_uploader("Upload manifest CSV (optional)", type=["csv"])
    use_data_manifest = st.button("Use default: data/sample_resources.csv")
    manifest_path_input = st.text_input("Or enter manifest path on server", value=os.path.join("data", "sample_resources.csv"))

    if uploaded_manifest is not None:
        saved = os.path.join(".", "uploaded_manifest.csv")
        with open(saved, "wb") as fh:
            fh.write(uploaded_manifest.getbuffer())
        st.success(f"Uploaded → {saved}")
        st.session_state["manifest_path"] = saved

    if use_data_manifest:
        st.session_state["manifest_path"] = manifest_path_input
        st.success(f"Using manifest: {manifest_path_input}")

    st.markdown("---")
    run_ingest_btn = st.button("Run ingest + summarize")

    st.markdown("### Orchestrator settings")
    session_id = st.text_input("Session ID", value="student_demo_session")
    grade = st.number_input("Student grade", min_value=1, max_value=12, value=6)
    init_orch_btn = st.button("Initialize Orchestrator")

    st.markdown("---")
    st.markdown("### Ask questions")
    single_question = st.text_input("Ask a single question")
    ask_single_btn = st.button("Ask question")

    multiple_questions = st.text_area("Ask multiple questions (one per line)", value="what are fractions?\nwhat is addition?")
    ask_batch_btn = st.button("Ask questions (batch)")

    st.markdown("---")
    st.markdown("### Student answer evaluation")
    expected_answer = st.text_input("Expected answer", value="Fractions represent parts of a whole number.")
    student_answer = st.text_input("Student answer to evaluate", value="Fractions are parts of a whole.")
    eval_btn = st.button("Evaluate student answer")

with right_col:
    st.header("Output")

    ensure_state_key("resources", [])
    ensure_state_key("summaries", {})
    ensure_state_key("corpus", {})
    ensure_state_key("orch", None)

    # Run ingest + summarize
    if run_ingest_btn:
        manifest_to_use = st.session_state.get("manifest_path") or manifest_path_input
        st.info(f"Ingesting from: {manifest_to_use}")

        try:
            with st.spinner("Running ingest..."):
                resources = run_ingest(manifest_to_use)
                st.session_state["resources"] = resources

            with st.spinner("Generating summaries..."):
                summaries = run_summarize(st.session_state["resources"], provider="mock", mode="short")
                st.session_state["summaries"] = summaries

            st.success("Ingest and summarization completed.")
        except Exception as e:
            st.exception(e)
            st.error("Ingest or summarization failed. Check CSV path, columns, and that src/ is importable.")

    # Initialize Orchestrator
    if init_orch_btn:
        resources = st.session_state.get("resources") or run_ingest(manifest_path_input)
        summaries = st.session_state.get("summaries") or run_summarize(resources, provider="mock", mode="short")
        corpus = build_corpus_from_resources(resources, summaries)
        st.session_state["corpus"] = corpus

        try:
            with st.spinner("Initializing OrchestratorReal..."):
                orch = OrchestratorReal(corpus)
                st.session_state["orch"] = orch
            st.success("Orchestrator initialized.")
        except Exception as e:
            st.exception(e)
            st.error("Failed to initialize OrchestratorReal. Check its constructor signature and required args.")
            # fallback to mock orch if our mock class exists
            try:
                st.session_state["orch"] = OrchestratorReal(corpus)
            except Exception:
                st.session_state["orch"] = None

    # Show corpus preview
    if st.session_state.get("corpus"):
        st.subheader("Corpus preview")
        rows = []
        for rid, it in st.session_state["corpus"].items():
            rows.append({
                "id": rid,
                "title": it.get("title"),
                "tags": it.get("tags"),
                "summary": it.get("summary"),
                "size_kb": it.get("meta", {}).get("size_kb")
            })
        df = pd.DataFrame(rows)
        st.dataframe(df)

        st.subheader("Resource thumbnails / URLs")
        cols = st.columns(3)
        idx = 0
        for rid, it in st.session_state["corpus"].items():
            url = it.get("meta", {}).get("url")
            with cols[idx % 3]:
                st.markdown(f"**{it.get('title')}**")
                if url:
                    # show file if it exists locally, else show URL as text
                    if os.path.exists(url):
                        try:
                            st.image(url, caption=os.path.basename(url), use_column_width=True)
                        except Exception:
                            st.write(f"File exists but could not render image: {url}")
                    else:
                        st.write(f"URL: {url}")
                else:
                    st.write("(no url)")
            idx += 1

    # Handle single question
    if ask_single_btn and single_question.strip():
        orch = st.session_state.get("orch")
        if orch is None:
            st.error("Orchestrator not initialized. Initialize it first.")
        else:
            with st.spinner("Getting answer from multi-agent system..."):
                try:
                    resp = orch.handle_user_question(session_id=session_id, user_question=single_question, student_profile={"grade": int(grade)})
                    st.subheader("Answer")
                    st.write(resp.get("answer"))
                    st.subheader("Explanation")
                    st.write(resp.get("teaching", {}).get("explanation"))
                    st.subheader("Examples")
                    for ex in resp.get("teaching", {}).get("examples", []):
                        st.write("- ", ex)
                    st.subheader("Practice")
                    for p in resp.get("teaching", {}).get("practice", []):
                        st.write("Q:", p.get("q"), " — Expected:", p.get("a"))
                except Exception as e:
                    st.exception(e)
                    st.error("Error calling orchestrator.handle_user_question")

    # Handle batch questions
    if ask_batch_btn:
        orch = st.session_state.get("orch")
        if orch is None:
            st.error("Orchestrator not initialized. Initialize it first.")
        else:
            qs = [q.strip() for q in multiple_questions.splitlines() if q.strip()]
            for q in qs:
                with st.expander(f"Question: {q}"):
                    try:
                        resp = orch.handle_user_question(session_id=session_id, user_question=q, student_profile={"grade": int(grade)})
                        st.write("**Answer:**", resp.get("answer"))
                        st.write("**Explanation:**", resp.get("teaching", {}).get("explanation"))
                    except Exception as e:
                        st.exception(e)
                        st.write("Error answering this question.")

    # Evaluate student answer
    if eval_btn:
        orch = st.session_state.get("orch")
        if orch is None:
            st.error("Orchestrator not initialized. Initialize it first.")
        else:
            try:
                fb = orch.assess_student_answer(session_id=session_id, student_answer=student_answer, expected_answer=expected_answer)
                st.subheader("Evaluation Result")
                st.write("Score:", fb.get("score"))
                st.write("Correct:", fb.get("correct"))
                st.write("Feedback:", fb.get("feedback"))
            except Exception as e:
                st.exception(e)
                st.error("Error calling orchestrator.assess_student_answer")

    st.markdown("---")
    if st.button("Download corpus JSON"):
        corpus = st.session_state.get("corpus", {})
        st.download_button("Download", data=json.dumps(corpus, indent=2), file_name="corpus.json")

# Footer note
if USE_MOCK:
    st.warning("Running in MOCK mode because your project modules could not be imported. Check src/ exists and PYTHONPATH.")
else:
    st.info("Using your real project modules from src/ (multi_agent_real & demo_combined).")
