"""Unit tests for the QA rules engine.

These are deterministic and offline — the rules take an explicit ``now`` and
links are not verified — so they validate the logic without depending on the
network or the live API. Run with:  python -m unittest discover -s tests
"""
import unittest
from datetime import datetime

from taskflow_qa.qa import extract_urls, evaluate_task

NOW = datetime(2026, 6, 27)


def make_task(**overrides):
    """A clean, passing task; override fields to trip a specific rule."""
    task = {
        "id": 1,
        "title": "Clean task",
        "status": 0,            # Todo
        "priority": 1,          # Medium
        "description": "A description.",
        "dueDate": "2030-01-01T00:00:00",
        "assignedTo": {"id": 1, "displayName": "Demo", "email": "demo@x.dev"},
        "createdAt": "2026-06-26T00:00:00",
    }
    task.update(overrides)
    return task


def codes(result):
    return {i.code for i in result.issues}


class ExtractUrlsTests(unittest.TestCase):
    def test_finds_and_dedupes_preserving_order(self):
        text = "CTA https://a.com/x then https://a.com/x and http://b.io/y."
        self.assertEqual(extract_urls(text), ["https://a.com/x", "http://b.io/y"])

    def test_empty_and_none(self):
        self.assertEqual(extract_urls(None), [])
        self.assertEqual(extract_urls(""), [])


class EvaluateTaskTests(unittest.TestCase):
    def test_clean_task_passes(self):
        result = evaluate_task(make_task(), now=NOW, verify_links=False)
        self.assertTrue(result.passed)
        self.assertEqual(result.max_severity, "info")

    def test_overdue_when_past_due_and_not_done(self):
        task = make_task(dueDate="2026-06-01T00:00:00", status=0)
        self.assertIn("OVERDUE", codes(evaluate_task(task, now=NOW, verify_links=False)))

    def test_done_task_is_never_overdue(self):
        task = make_task(dueDate="2026-06-01T00:00:00", status=2)  # Done
        self.assertNotIn("OVERDUE", codes(evaluate_task(task, now=NOW, verify_links=False)))

    def test_high_priority_without_assignee_flagged(self):
        task = make_task(priority=2, assignedTo=None)
        self.assertIn("UNASSIGNED_HIGH", codes(evaluate_task(task, now=NOW, verify_links=False)))

    def test_missing_description_flagged(self):
        task = make_task(description="   ")
        self.assertIn("NO_DESCRIPTION", codes(evaluate_task(task, now=NOW, verify_links=False)))

    def test_severity_escalates_to_high(self):
        # Overdue (high) + unassigned-high (medium) -> overall high.
        task = make_task(dueDate="2026-06-01T00:00:00", priority=2, assignedTo=None)
        self.assertEqual(evaluate_task(task, now=NOW, verify_links=False).max_severity, "high")


if __name__ == "__main__":
    unittest.main()
