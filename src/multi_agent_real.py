# src/multi_agent_real.py
"""
Real multi-agent reasoning module.

Agents:
 - RetrieverAgent: retrieves candidate resources (title/tags/summary search).
 - QAAgent: produces concise answers given question + contexts (mock LLM by default).
 - TutorAgent: expands answers into step-by-step explanations and creates practice items.
 - FeedbackAgent: evaluates a student's short answer and suggests remediation.
 - Orchestrator: routes a user's question through agents, maintains short-term memory,
                 and produces a combined response object.

Design goals:
 - Clear agent interfaces so you can plug a real LLM or embedding retriever later.
 - Runs offline with deterministic mock behavior for demos.
"""

from typing import List, Dict, Optional, Any
from difflib import SequenceMatcher
import logging
import math

logger = logging.getLogger("multi_agent_real")
logger.setLevel(logging.INFO)


# -------------------------
# UTILITIES
# -------------------------
def simple_text_score(a: str, b: str) -> float:
    """Return a 0..1 similarity score between two strings using SequenceMatcher."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


# -------------------------
# Base Agent (Interface)
# -------------------------
class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def handle(self, *args, **kwargs):
        raise NotImplementedError


# -------------------------
# RetrieverAgent
# -------------------------
class RetrieverAgent(BaseAgent):
    """
    Lightweight retriever that searches title, tags, and summaries for substring or
    fuzzy matches. Returns a ranked list of candidate docs.
    corpus: dict resource_id -> {"title":..., "tags":..., "summary":..., "meta": {...}}
    """

    def __init__(self, corpus: Dict[str, Dict[str, Any]]):
        super().__init__("RetrieverAgent")
        self.corpus = corpus

    def rank(self, query: str, top_k: int = 5) -> List[Dict]:
        q = query.lower().strip()
        results = []
        for rid, doc in self.corpus.items():
            title = (doc.get("title") or "").lower()
            tags = (doc.get("tags") or "").lower()
            summary = (doc.get("summary") or "").lower()

            # exact substring score
            subscore = 0
            if q in title:
                subscore += 1.2
            if q in tags:
                subscore += 1.0
            if q in summary:
                subscore += 0.8

            # fuzzy similarity on title and summary
            fuzz_title = simple_text_score(q, title)
            fuzz_summary = simple_text_score(q, summary)

            score = subscore + 0.6 * fuzz_title + 0.4 * fuzz_summary

            # penalize very short docs slightly
            length = len(summary)
            length_penalty = 0.0 if length > 50 else -0.2

            final_score = max(0.0, score + length_penalty)
            if final_score > 0:
                results.append({"id": rid, "score": final_score, "doc": doc})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


# -------------------------
# QAAgent
# -------------------------
class QAAgent(BaseAgent):
    """
    QAAgent returns a short answer based on contexts. This is a mock 'LLM' — it
    concatenates context and returns a short synthesized answer. Replace .answer()
    with a real LLM call (Gemini/OpenAI/HF) easily.
    """

    def __init__(self, provider: str = "mock", api_key: Optional[str] = None):
        super().__init__("QAAgent")
        self.provider = provider
        self.api_key = api_key

    def answer(self, question: str, contexts: List[Dict], max_chars: int = 800) -> str:
        """
        contexts: list of dicts {id, doc}
        """
        if not contexts:
            return "I couldn't find relevant material. Can you rephrase or add detail?"

        # Mock behavior: include top context title and a one-line synthesized answer
        top = contexts[0]["doc"]
        title = top.get("title") or ""
        # Build a short answer string
        ans = f"Short answer (based on {title}): This covers the concept related to '{question}'. " \
              f"See top resource '{title}' for details."
        # Truncate
        return ans[:max_chars]


# -------------------------
# TutorAgent
# -------------------------
class TutorAgent(BaseAgent):
    """
    TutorAgent expands an answer into step-by-step explanation, and generates
    2 practice questions (with answers) targeted to the student's level.
    """

    def __init__(self, provider: str = "mock", api_key: Optional[str] = None):
        super().__init__("TutorAgent")
        self.provider = provider
        self.api_key = api_key

    def teach(self, question: str, answer: str, contexts: List[Dict], student_level: Optional[int] = None) -> Dict:
        """
        Returns:
          {
            'explanation': "...",
            'examples': ["..."],
            'practice': [{'q': '...', 'a': '...'}, ...]
          }
        """
        # Mock deterministic teaching:
        explanation = f"Step-by-step: To approach '{question}', first recall the basics from the resource. {answer}"
        examples = [
            f"Example 1: A simple variant of {question}. Solution outline: ...",
            f"Example 2: Another practice on {question}. Solution outline: ..."
        ]

        # Craft two practice Q&A using slight variations
        practice = []
        practice.append({"q": f"Solve a basic problem related to {question} (easy).", "a": "Answer: use basic rules."})
        practice.append({"q": f"Solve a slightly harder {question} (medium).", "a": "Answer: combine steps."})

        return {
            "explanation": explanation,
            "examples": examples,
            "practice": practice
        }


# -------------------------
# FeedbackAgent
# -------------------------
class FeedbackAgent(BaseAgent):
    """
    Simple feedback/evaluation: given a student's short free-text answer,
    estimate correctness by string-similarity against expected answer text.
    """

    def __init__(self, threshold: float = 0.6):
        super().__init__("FeedbackAgent")
        self.threshold = threshold

    def assess(self, student_answer: str, expected_answer: str) -> Dict:
        """
        Returns: dict {'score': float(0..1), 'correct': bool, 'feedback': str}
        """
        score = simple_text_score(student_answer, expected_answer)
        correct = score >= self.threshold

        if correct:
            feedback = "Good! Your answer matches the expected solution closely."
        else:
            feedback = "Not quite — review the explanation and try the easier practice example."

        # Normalize to 0..1
        score = max(0.0, min(1.0, float(score)))

        return {"score": score, "correct": bool(correct), "feedback": feedback}


# -------------------------
# Orchestrator
# -------------------------
class OrchestratorReal:
    """
    Coordinates the full multi-agent pipeline.
    Maintains a per-session short-term memory (a simple list of recent Q&A pairs).
    """

    def __init__(self, corpus: Dict[str, Dict[str, Any]], memory_size: int = 10):
        self.retriever = RetrieverAgent(corpus)
        self.qa_agent = QAAgent()
        self.tutor_agent = TutorAgent()
        self.feedback_agent = FeedbackAgent()
        self.memory_size = memory_size
        self.sessions: Dict[str, List[Dict]] = {}  # session_id -> list of interactions

    def _add_memory(self, session_id: str, record: Dict):
        mem = self.sessions.setdefault(session_id, [])
        mem.append(record)
        if len(mem) > self.memory_size:
            mem.pop(0)

    def handle_user_question(self, session_id: str, user_question: str, student_profile: Optional[Dict] = None) -> Dict:
        # 1) Retrieve candidate docs
        ranked = self.retriever.rank(user_question, top_k=5)
        logger.info("Retriever returned %d docs", len(ranked))

        # 2) QA agent forms concise answer using top contexts
        answer = self.qa_agent.answer(user_question, ranked[:3])

        # 3) Tutor agent expands and creates practice
        student_level = None
        if student_profile:
            student_level = student_profile.get("grade")
        teaching = self.tutor_agent.teach(user_question, answer, ranked[:3], student_level=student_level)

        # 4) Save to memory
        record = {
            "question": user_question,
            "answer": answer,
            "teaching": teaching,
            "retrieved": [{"id": r["id"], "score": r["score"]} for r in ranked[:3]]
        }
        self._add_memory(session_id, record)

        # 5) Construct orchestrated response
        response = {
            "question": user_question,
            "answer": answer,
            "teaching": teaching,
            "retrieved": ranked[:3],
            "session_memory": self.sessions.get(session_id, [])
        }
        return response

    def assess_student_answer(self, session_id: str, student_answer: str, expected_answer: str) -> Dict:
        # Ask feedback agent to assess and record
        result = self.feedback_agent.assess(student_answer, expected_answer)
        rec = {"assessment": result, "student_answer": student_answer, "expected": expected_answer}
        self._add_memory(session_id, rec)
        return result
