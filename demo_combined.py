#!/usr/bin/env python3
"""
demo_combined.py

Single-file demo that:
- Loads CSV resources
- Generates better summaries (with title + tags)
- Creates a weekly plan
- Runs QA retrieval + answer
- Saves session to data/sessions/

Run with:
    python demo_combined.py
    python demo_combined.py --quiet
"""

import sys
import os
import argparse
import logging
from typing import Dict, List
from pprint import pprint
import pandas as pd

# Ensure src is importable when running from project root
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# Import project modules from src/
from summarizer import LLMSummarizer
from planner import StudentProfile, plan_weekly_lessons
from multi_agent import RetrieverAgent, QAAgent, Orchestrator
from session_mem import save_session, load_session

# ---------------------------------------------------------------------
# INGEST UTILITIES (BUILT-IN HERE)
# ---------------------------------------------------------------------

def read_resource_manifest(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    expected = ["id", "url", "title", "language", "size_kb", "tags"]
    for c in expected:
        if c not in df.columns:
            df[c] = None
    return df[expected]


def filter_by_bandwidth(df: pd.DataFrame, max_size_kb: int) -> pd.DataFrame:
    return df[df["size_kb"].fillna(0) <= max_size_kb].copy()


def sample_resources_for_demo(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return df.sample(min(n, len(df))).reset_index(drop=True)


# ---------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------

logger = logging.getLogger("demo_combined")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------
# UPDATED run_summarize()  (YOU REQUESTED THIS FIX)
# ---------------------------------------------------------------------

def run_summarize(resources: List[Dict], provider: str = "mock", mode: str = "short"):
    """
    Create summaries for each resource.

    IMPROVED VERSION:
    - Prepends title + tags to pseudo_text
    - Ensures retriever finds keywords
    """
    logger.info("Summarizing %d resources (provider=%s, mode=%s)", len(resources), provider, mode)
    summarizer = LLMSummarizer(provider=provider)
    summaries = {}

    for r in resources:
        title = r.get('title', '')
        tags = r.get('tags', '')

        pseudo_text = (
            f"{title}. {tags}. "
            f"Example content for resource {r.get('id')}. "
            f"Contains explanation, examples, and practice tasks."
        )

        summary = summarizer.summarize(pseudo_text, mode=mode)
        summaries[r["id"]] = summary

    logger.info("Summaries created for %d resources", len(summaries))
    return summaries


# ---------------------------------------------------------------------
# WEEKLY PLANNER
# ---------------------------------------------------------------------

def run_planner(student: StudentProfile, resources: List[Dict], summaries: Dict[str, str]):
    logger.info("Generating weekly plan for student %s (bandwidth %s KB)",
                student.name, student.weekly_bandwidth_kb)

    lessons = plan_weekly_lessons(student, resources, summaries)

    logger.info("Planned %d lessons", len(lessons))
    for l in lessons:
        print(f"Day {l.day}: {l.title} ({l.estimated_kb} KB) — {l.summary}")

    return lessons


# ---------------------------------------------------------------------
# Q&A MULTI-AGENT DEMO
# ---------------------------------------------------------------------

def run_qa_demo(summaries: Dict[str, str], queries: List[str]):
    logger.info("Initializing retriever and QA agent")
    retriever = RetrieverAgent(summaries)
    qa_agent = QAAgent()
    orch = Orchestrator(retriever, qa_agent)

    results = []

    for q in queries:
        logger.info("Querying: %s", q)
        resp = orch.handle_query(q)

        print("\n" + "-" * 60)
        print("Query:", q)
        print("Answer:\n", resp["answer"])
        print("Contexts returned:", [c["id"] for c in resp["contexts"]])

        results.append(resp)

    return results


# ---------------------------------------------------------------------
# MAIN FULL PIPELINE
# ---------------------------------------------------------------------

def demo_flow(manifest_path: str, quiet: bool = False):

    # 1. INGEST
    resources = run_ingest(manifest_path=manifest_path)

    # 2. SUMMARIZE (Title + Tags included)
    summaries = run_summarize(resources, provider="mock", mode="short")

    if not quiet:
        print("\nSummaries (id -> snippet):")
        for rid, s in summaries.items():
            print(f"{rid}: {s[:120]}")

    # 3. PLANNER
    student = StudentProfile(
        id="demo_student_1",
        name="Raju",
        grade=6,
        preferred_language="kn",
        weekly_bandwidth_kb=500,
        available_hours_per_day=1.0,
    )

    lessons = run_planner(student, resources, summaries)

    # 4. SAVE SESSION
    session = {
        "student": student.__dict__,
        "summaries": summaries,
        "lessons": [l.__dict__ for l in lessons]
    }

    save_session(student.id, session)
    logger.info("Saved session file to data/sessions/%s.json", student.id)

    # 5. QA RETRIEVAL TEST
    queries = ["addition", "fractions", "kannada", "plants"]
    qa_results = run_qa_demo(summaries, queries)

    return {
        "resources": resources,
        "summaries": summaries,
        "lessons": lessons,
        "qa_results": qa_results,
    }


# ---------------------------------------------------------------------
# INGEST WRAPPER (USED BY demo_flow)
# ---------------------------------------------------------------------

def run_ingest(manifest_path: str, sample_n: int = 8):
    logger.info("Reading manifest: %s", manifest_path)
    df = read_resource_manifest(manifest_path)
    logger.info("Total resources: %d", len(df))

    sample = sample_resources_for_demo(df, n=sample_n)
    resources = sample.to_dict(orient="records")

    logger.info("Sampled %d resources for demo", len(resources))
    return resources


# ---------------------------------------------------------------------
# CLI ARGUMENTS
# ---------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Run the rural-ed-agent demo.")
    p.add_argument("--manifest", type=str, default=os.path.join("data", "sample_resources.csv"))
    p.add_argument("--quiet", action="store_true")
    return p.parse_args()


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_args()

    if args.quiet:
        logger.setLevel(logging.WARNING)

    try:
        demo_flow(args.manifest, quiet=args.quiet)
        print("\nDemo finished. Session saved in data/sessions/")
    except Exception as e:
        logger.exception("Demo failed: %s", e)
        sys.exit(1)
