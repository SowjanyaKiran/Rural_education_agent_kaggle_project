# tests/test_summarizer.py
from summarizer import simple_extractive_summary

def test_simple_extractive_summary():
    text = "This is the first sentence. Short one. This is a longer sentence with more words to be selected."
    s = simple_extractive_summary(text, max_sentences=2)
    assert len(s) > 0
    assert ("This is the first sentence" in s) or ("This is a longer sentence" in s)
