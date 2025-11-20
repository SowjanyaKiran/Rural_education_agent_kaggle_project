# src/summarizer.py
"""
Summarization utilities.
Includes a simple extractive fallback and a mock LLM summarizer.
"""

from typing import List, Optional
import heapq
import re


def simple_extractive_summary(text: str, max_sentences: int = 3) -> str:
    """
    Extractive summarizer: split by naive sentence boundary
    and pick longest sentences. This is a demo placeholder.
    """
    # split text into sentences (tiny naive rule)
    sentences = re.split(r'(?<=[.!?]) +', text.strip())
    if not sentences:
        return ""

    # score sentences by length (-len ensures longest first)
    scored = [(-len(s), i, s) for i, s in enumerate(sentences) if s.strip()]
    if not scored:
        return ""

    # pick top N by length
    top = heapq.nsmallest(min(max_sentences, len(scored)), scored)
    top_sorted = sorted(top, key=lambda t: t[1])  # keep original order

    return " ".join(t[2] for t in top_sorted)


class LLMSummarizer:
    """
    Mock summarizer that uses simple_extractive_summary for now.
    Replace with actual LLM API calls later.
    """

    def __init__(self, provider: str = "mock", api_key: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key

    def summarize(self, text: str, mode: str = "short") -> str:
        """
        mode = 'short' → 2 sentences
        mode = 'long' → 5 sentences
        """
        if not text:
            return ""

        if self.provider == "mock":
            sentences = 2 if mode == "short" else 5
            return simple_extractive_summary(text, max_sentences=sentences)

        # If user switches provider to actual API
        raise NotImplementedError("Implement real LLM call here.")
