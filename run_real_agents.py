"""
run_real_agents.py
Real multi-agent reasoning demo.

This script:
1. Loads resources from sample_resources.csv
2. Generates summaries using your existing summarizer
3. Builds a corpus for retrieval
4. Runs the REAL multi-agent system (Retriever + QA + Tutor + Feedback)
"""

import os
import sys
import logging

# ------------------------------------------------------------------
# 1) Ensure src/ is importable
# ------------------------------------------------------------------

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

# ------------------------------------------------------------------
# 2) Imports from src/
# ------------------------------------------------------------------

from multi_agent_real import OrchestratorReal
from demo_combined import run_ingest, run_summarize   # reuse existing functions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("run_real_agents")


# ------------------------------------------------------------------
# 3) Load resources & summaries
# ------------------------------------------------------------------

manifest_path = os.path.join("data", "sample_resources.csv")

logger.info("Loading resources...")
resources = run_ingest(manifest_path)

logger.info("Generating summaries...")
summaries = run_summarize(resources, provider="mock", mode="short")


# ------------------------------------------------------------------
# 4) Build corpus for multi-agent system
# ------------------------------------------------------------------

logger.info("Building corpus for multi-agent agents...")

corpus = {}
for r in resources:
    rid = r["id"]
    corpus[rid] = {
        "title": r.get("title", ""),
        "tags": r.get("tags", ""),
        "summary": summaries.get(rid, ""),
        "meta": {
            "url": r.get("url"),
            "size_kb": r.get("size_kb", 0)
        }
    }


# ------------------------------------------------------------------
# 5) Initialize OrchestratorReal
# ------------------------------------------------------------------

orch = OrchestratorReal(corpus)
session_id = "student_demo_session"

logger.info("Orchestrator initialized. Starting Q&A...")

# ------------------------------------------------------------------
# 6) Ask questions to the multi-agent system
# ------------------------------------------------------------------

questions = [
    "what are fractions?",
    "what is addition?",
    "explain kannada alphabets",
    "what are plants?"
]

for q in questions:
    print("\n" + "=" * 70)
    print("USER QUESTION:", q)

    response = orch.handle_user_question(
        session_id=session_id,
        user_question=q,
        student_profile={"grade": 6}
    )

    print("\nAnswer:")
    print(response["answer"])

    print("\nExplanation:")
    print(response["teaching"]["explanation"])

    print("\nExamples:")
    for ex in response["teaching"]["examples"]:
        print(" -", ex)

    print("\nPractice Questions:")
    for p in response["teaching"]["practice"]:
        print(" -", p["q"], "| Expected:", p["a"])


# ------------------------------------------------------------------
# 7) Feedback Evaluation Example
# ------------------------------------------------------------------

print("\n" + "=" * 70)
print("NOW TESTING STUDENT ANSWER EVALUATION")

student_ans = "Fractions are parts of a whole."
expected_ans = "Fractions represent parts of a whole number."

feedback = orch.assess_student_answer(
    session_id=session_id,
    student_answer=student_ans,
    expected_answer=expected_ans
)

print("\nStudent Answer:", student_ans)
print("Expected:", expected_ans)
print("Score:", feedback["score"])
print("Correct:", feedback["correct"])
print("Feedback:", feedback["feedback"])

print("\nDONE! Multi-agent reasoning demo finished successfully.")
