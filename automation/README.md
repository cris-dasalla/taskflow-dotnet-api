# TaskFlow QA — an API automation (Python)

A small, dependency-free Python automation that audits the [TaskFlow API](../) end to end:
it **authenticates**, **pages through every task**, **verifies external links against the live web**,
applies a set of **QA rules**, and emits a **structured JSON report** — exiting non-zero when it
finds high-severity problems so it can gate a release in CI.

It mirrors a real agency workflow — *"verify every product link against the live store before
sending"* — applied to tasks instead of emails.

---

## Run it

The only prerequisite is **Python 3.10+** and the TaskFlow API running locally (`dotnet run` in
[`src/TaskFlow.Api`](../src/TaskFlow.Api)). No `pip install` — it uses the standard library only.

```bash
cd automation

# Seed demo data (incl. a deliberately broken link), then audit:
python -m taskflow_qa --seed

# Audit existing data and write the structured report:
python -m taskflow_qa --output report.json

# Treat any medium+ issue as a failure (default gate is "high"):
python -m taskflow_qa --fail-on medium
```

### Example run

```
================================================================
  TaskFlow QA report  |  http://localhost:5020
================================================================
  Tasks audited      : 8
  Tasks with issues  : 5
  Total issues       : 8
  Broken links       : 1
  High severity      : 3
----------------------------------------------------------------
  [FAIL] #7 Summer Sale email — final QA  (high)
           - high   OVERDUE: Due 2026-06-10 but status is Todo
           - medium UNASSIGNED_HIGH: High-priority task has no assignee
           - high   BROKEN_LINK: Unreachable link: https://shop.example.invalid/... ([Errno 11001] getaddrinfo failed)
  [ OK ] #6 Implement JWT authentication
  ...
```

The same data is written as JSON (`--output`), keyed for easy downstream consumption:

```json
{
  "summary": { "totalTasks": 8, "tasksWithIssues": 5, "brokenLinks": 1, "highSeverity": 3 },
  "results": [
    {
      "taskId": 7, "title": "Summer Sale email — final QA", "priority": "High", "passed": false,
      "issues": [ { "code": "BROKEN_LINK", "severity": "high", "message": "Unreachable link: ..." } ],
      "linkChecks": [ { "url": "https://github.com/...", "ok": true, "status_code": 200 } ]
    }
  ]
}
```

---

## How it's wired (architecture)

Separation of concerns, so each piece is small and testable:

| Module | Responsibility |
|---|---|
| [`client.py`](taskflow_qa/client.py) | **Integration layer** — JWT login, bearer auth, pagination, retry with exponential backoff, and automatic re-auth on a `401`. |
| [`qa.py`](taskflow_qa/qa.py) | **Rules + live link verification** — extract URLs, check each against the web (HEAD→GET fallback), and apply QA rules that each return a typed `Issue`. |
| [`models.py`](taskflow_qa/models.py) | **Structured output** — dataclasses (`Issue`, `LinkCheck`, `TaskQAResult`, `QAReport`) with deterministic `to_dict()` serialisation. |
| [`__main__.py`](taskflow_qa/__main__.py) | **Orchestration** — CLI, run the pipeline, print a summary, write JSON, and set the exit code from a severity gate. |
| [`seed.py`](taskflow_qa/seed.py) | Demo data (only runs with `--seed`; the audit never mutates data otherwise). |

### How auth, errors, and edge cases are handled
- **Auth:** log in once for a JWT; attach it as a bearer token; if a request returns `401`
  mid-run, the client re-authenticates and retries exactly once.
- **Transient failures** (timeouts, `5xx`, connection refused) are retried with exponential
  backoff; **client errors** (`4xx`) fail fast with the API's RFC 7807 `detail` message surfaced.
- **Link checks never crash the run** — DNS failures, timeouts, and HTTP errors are each captured
  as a structured `LinkCheck` and turned into a finding.
- **Pagination** is followed via the API's `hasNext` metadata — it never assumes a single page.

---

## As a Claude Code skill

This automation is written to be run and extended by an AI coding agent. The structured
instructions an agent follows live in [`SKILL.md`](SKILL.md) — the same "skill" pattern used to
maintain it: clear inputs, explicit steps, validation, and a definition of done.
