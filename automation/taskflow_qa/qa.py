"""QA rules engine + live link verification.

Two responsibilities:

  * **Link verification** — extract URLs from a task's text and check each one
    against the live web, exactly like verifying product links against a store
    before an email goes out. Network failures are caught and reported, never
    allowed to crash the run.
  * **Rules** — a small, explicit set of checks. Each returns an ``Issue`` with
    a severity so the report is actionable and the exit code is meaningful.
"""
from __future__ import annotations

import logging
import re
import urllib.error
import urllib.request
from datetime import datetime

from .models import (
    PRIORITY_LABELS,
    STATUS_LABELS,
    Issue,
    LinkCheck,
    TaskQAResult,
)

log = logging.getLogger("taskflow_qa.qa")

URL_RE = re.compile(r"https?://[^\s\)\]\}<>\"']+")


def extract_urls(text: str | None) -> list[str]:
    if not text:
        return []
    # De-dupe while preserving order.
    seen: dict[str, None] = {}
    for match in URL_RE.findall(text):
        seen.setdefault(match.rstrip(".,;"), None)
    return list(seen)


def verify_link(url: str, *, timeout: float = 6.0) -> LinkCheck:
    """Check one URL with a HEAD request, falling back to GET on 405.

    Every failure mode (DNS, timeout, connection refused, HTTP error) is
    captured as a structured result instead of an exception.
    """
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "TaskFlow-QA/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return LinkCheck(url=url, ok=True, status_code=resp.status)
    except urllib.error.HTTPError as exc:
        if exc.code == 405:  # HEAD not allowed — retry with GET
            return _verify_with_get(url, timeout=timeout)
        return LinkCheck(url=url, ok=False, status_code=exc.code, error=f"HTTP {exc.code}")
    except urllib.error.URLError as exc:
        return LinkCheck(url=url, ok=False, error=str(exc.reason))
    except (TimeoutError, ValueError) as exc:
        return LinkCheck(url=url, ok=False, error=str(exc))


def _verify_with_get(url: str, *, timeout: float) -> LinkCheck:
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "TaskFlow-QA/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return LinkCheck(url=url, ok=True, status_code=resp.status)
    except urllib.error.HTTPError as exc:
        return LinkCheck(url=url, ok=False, status_code=exc.code, error=f"HTTP {exc.code}")
    except Exception as exc:  # noqa: BLE001 - last-resort capture for the report
        return LinkCheck(url=url, ok=False, error=str(exc))


def _parse_due(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "").split("+")[0])
    except ValueError:
        return None


def evaluate_task(
    task: dict,
    *,
    now: datetime,
    verify_links: bool = True,
    stale_days: int = 30,
) -> TaskQAResult:
    """Apply every QA rule to one task and return a structured verdict."""
    status_code = task.get("status", 0)
    priority_code = task.get("priority", 0)
    result = TaskQAResult(
        task_id=task.get("id", -1),
        title=task.get("title", "(untitled)"),
        status=STATUS_LABELS.get(status_code, str(status_code)),
        priority=PRIORITY_LABELS.get(priority_code, str(priority_code)),
    )

    # Rule: overdue and not done.
    due = _parse_due(task.get("dueDate"))
    if due and due < now and status_code != 2:
        result.issues.append(
            Issue("OVERDUE", "high", f"Due {due.date()} but status is {result.status}")
        )

    # Rule: high-priority work with nobody assigned.
    if priority_code == 2 and not task.get("assignedTo"):
        result.issues.append(
            Issue("UNASSIGNED_HIGH", "medium", "High-priority task has no assignee")
        )

    # Rule: missing description (hard to QA an email/task with no body).
    if not (task.get("description") or "").strip():
        result.issues.append(Issue("NO_DESCRIPTION", "low", "Task has no description"))

    # Rule: stale — created long ago, still not started.
    created = _parse_due(task.get("createdAt"))
    if created and status_code == 0 and (now - created).days >= stale_days:
        result.issues.append(
            Issue("STALE", "low", f"Open for {(now - created).days} days, still Todo")
        )

    # Rule: every link in the description must resolve against the live web.
    if verify_links:
        for url in extract_urls(task.get("description")):
            check = verify_link(url)
            result.link_checks.append(check)
            if not check.ok:
                result.issues.append(
                    Issue("BROKEN_LINK", "high", f"Unreachable link: {url} ({check.error})")
                )

    return result
