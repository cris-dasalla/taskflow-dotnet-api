"""Structured output models.

Everything the automation emits is a dataclass with a ``to_dict`` so the final
report is deterministic, typed, and trivially serialised to JSON — the same
discipline you'd want feeding a downstream system (a Slack alert, a dashboard,
or another agent).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

# The API serialises enums as integers; map them back to human labels once,
# in one place, so the rest of the code talks in names.
STATUS_LABELS = {0: "Todo", 1: "InProgress", 2: "Done"}
PRIORITY_LABELS = {0: "Low", 1: "Medium", 2: "High"}

# Severity ordering, used to decide the process exit code.
SEVERITY_ORDER = {"info": 0, "low": 1, "medium": 2, "high": 3}


@dataclass
class LinkCheck:
    """Result of verifying a single URL against the live web."""

    url: str
    ok: bool
    status_code: int | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Issue:
    """A single QA finding on a task."""

    code: str
    severity: str  # info | low | medium | high
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TaskQAResult:
    """The full QA verdict for one task."""

    task_id: int
    title: str
    status: str
    priority: str
    issues: list[Issue] = field(default_factory=list)
    link_checks: list[LinkCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.issues

    @property
    def max_severity(self) -> str:
        if not self.issues:
            return "info"
        return max((i.severity for i in self.issues), key=lambda s: SEVERITY_ORDER[s])

    def to_dict(self) -> dict[str, Any]:
        return {
            "taskId": self.task_id,
            "title": self.title,
            "status": self.status,
            "priority": self.priority,
            "passed": self.passed,
            "maxSeverity": self.max_severity,
            "issues": [i.to_dict() for i in self.issues],
            "linkChecks": [lc.to_dict() for lc in self.link_checks],
        }


@dataclass
class QAReport:
    """Top-level report — the structured artifact this automation produces."""

    generated_at: str
    base_url: str
    results: list[TaskQAResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        broken_links = sum(
            1 for r in self.results for lc in r.link_checks if not lc.ok
        )
        return {
            "generatedAt": self.generated_at,
            "baseUrl": self.base_url,
            "summary": {
                "totalTasks": len(self.results),
                "tasksWithIssues": sum(1 for r in self.results if not r.passed),
                "totalIssues": sum(len(r.issues) for r in self.results),
                "brokenLinks": broken_links,
                "highSeverity": sum(
                    1 for r in self.results if r.max_severity == "high"
                ),
            },
            "results": [r.to_dict() for r in self.results],
        }
