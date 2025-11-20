# tests/test_planner.py
from planner import StudentProfile, plan_weekly_lessons

def test_planner_small_budget():
    student = StudentProfile(
        id='s',
        name='A',
        grade=5,
        preferred_language='en',
        weekly_bandwidth_kb=100,
        available_hours_per_day=1
    )
    resources = [
        {'id': 'r1', 'title': 'A', 'language': 'en', 'size_kb': 60},
        {'id': 'r2', 'title': 'B', 'language': 'hi', 'size_kb': 60},
    ]
    summaries = {'r1': 's1', 'r2': 's2'}
    plan = plan_weekly_lessons(student, resources, summaries)
    assert len(plan) >= 1
    # ensure selected resource fits budget
    total_kb = sum(l.estimated_kb for l in plan)
    assert total_kb <= student.weekly_bandwidth_kb
