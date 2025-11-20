# src/translation.py
"""
Provider-agnostic translation wrapper (mock fallback included).
Replace the mock internals with real API calls (Google/Microsoft/HuggingFace) when ready.
"""
from typing import Optional




class TranslationClient:
def __init__(self, provider: str = "mock", api_key: Optional[str] = None):
self.provider = provider
self.api_key = api_key


def detect_language(self, text: str) -> str:
"""Naive heuristic for demo: detect Kannada vs English vs Hindi by Unicode ranges."""
if any("\u0C80" <= ch <= "\u0CFF" for ch in text):
return "kn"
if any("\u0900" <= ch <= "\u097F" for ch in text):
return "hi"
return "en"


def translate_text(self, text: str, target_lang: str = "en") -> str:
"""Demo fallback: if source==target => original; else a mock prefix.
Replace with provider call.
"""
src = self.detect_language(text)
if src == target_lang:
return text
return f"[translated {src}->{target_lang}] {text}"