# src/planner.py

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class StudentProfile:
    id: str
    name: str
    grade: int
    preferred_language: str
    weekly_bandwidth_kb: int
    available_hours_per_day: float


@dataclass
class Lesson:
    resource_id: str
    title: str
    lang: str
    estimated_kb: int
    summary: str
    day: int


def plan_weekly_lessons(student: StudentProfile,
                        resources: List[Dict],
                        summaries: Dict[str, str]) -> List[Lesson]:
    """
    Greedy weekly lesson planner.
    Prefers:
      1. resources in student's preferred_language
      2. smaller size_kb first
    Stops when bandwidth is exhausted.
    """

    pref = student.preferred_language

    # Sort resources: (not preferred lang), then by size_kb ascending
    res_sorted = sorted(
        resources,
        key=lambda r: (
            r.get("language") != pref,
            int(r.get("size_kb") or 0)
        )
    )

    budget = int(student.weekly_bandwidth_kb)
    lessons: List[Lesson] = []
    day = 1

    for r in res_sorted:
        try:
            size = int(r.get("size_kb") or 0)
        except Exception:
            size = 0

        if size == 0:
            continue

        if size <= budget:
            lessons.append(
                Lesson(
                    resource_id=r["id"],
                    title=r.get("title", "Untitled"),
                    lang=r.get("language", "en"),
                    estimated_kb=size,
                    summary=summaries.get(r["id"], ""),
                    day=day,
                )
            )
            budget -= size
            day = day + 1 if day < 7 else 1

        if budget <= 0:
            break

    return lessons
