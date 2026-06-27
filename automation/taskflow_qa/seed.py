"""Demo data so a live run has something interesting to find.

Creates a handful of tasks that each trip a different QA rule — including one
with a deliberately broken link — so the audit visibly catches real problems.
Kept separate from the audit logic: the automation never mutates data unless
``--seed`` is passed.
"""
from __future__ import annotations

from .client import TaskFlowClient

# Each task is designed to exercise one rule. The broken `.invalid` host will
# fail DNS resolution, demonstrating live link verification + error handling.
_DEMO_TASKS = [
    {
        "title": "Summer Sale email — final QA",
        "description": (
            "Ship the summer sale campaign. Hero CTA -> "
            "https://github.com/cris-dasalla/taskflow-dotnet-api ; "
            "product link -> https://shop.example.invalid/products/sunhat-42"
        ),
        "priority": 2,  # High, intentionally left UNASSIGNED
        "dueDate": "2026-06-10T17:00:00Z",  # in the past -> OVERDUE
    },
    {
        "title": "Welcome flow — copy review",
        "description": "Docs: https://github.com/cris-dasalla/taskflow-dotnet-api",
        "priority": 1,
        "assignedToId": 1,
        "dueDate": "2030-01-01T00:00:00Z",
    },
    {
        "title": "Abandoned cart reminder",
        "description": "",  # NO_DESCRIPTION
        "priority": 2,  # UNASSIGNED_HIGH
    },
]


def seed_demo_tasks(client: TaskFlowClient) -> int:
    created = 0
    for task in _DEMO_TASKS:
        client.create_task(task)
        created += 1
    return created
