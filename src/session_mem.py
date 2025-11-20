# src/session_mem.py

import os
import json
from typing import Dict, Any

# folder to store session files
BASE = "data/sessions"


def ensure_dir():
    """Create session directory if it doesn't exist."""
    os.makedirs(BASE, exist_ok=True)


def save_session(student_id: str, session: Dict[str, Any]):
    """Save a session to JSON file."""
    ensure_dir()
    path = os.path.join(BASE, f"{student_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)


def load_session(student_id: str) -> Dict[str, Any]:
    """Load a session JSON if exists, else return empty dict."""
    path = os.path.join(BASE, f"{student_id}.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
