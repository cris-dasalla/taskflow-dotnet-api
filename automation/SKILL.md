---
name: taskflow-qa-audit
description: Audit every task in the TaskFlow API for QA issues (overdue, unassigned high-priority, missing description, broken links) and emit a structured report. Use before shipping a batch of work, or on a schedule.
---

# Skill: TaskFlow QA Audit

A structured, repeatable instruction set an AI coding agent (Claude Code) follows to run and
maintain the TaskFlow QA automation. This is the "skill" format — explicit inputs, steps,
validation, and a definition of done — so the work is reproducible by a human or an agent.

## Inputs
- `base_url` — TaskFlow API base (default `http://localhost:5020`)
- `email` / `password` — credentials for a seeded account (default demo account)
- `fail_on` — severity gate: `info | low | medium | high` (default `high`)
- `seed` — optional; create demo data first

## Steps
1. **Authenticate.** POST `/api/auth/login`; cache the JWT. Re-auth automatically on a later `401`.
2. **(Optional) Seed.** If `seed` is set, create the demo tasks via `POST /api/tasks`.
3. **Fetch all tasks.** GET `/api/tasks` page by page, following `hasNext`. Never assume one page.
4. **Evaluate each task** against the rules below; collect typed `Issue`s.
5. **Verify links.** For every URL in a task description, check it against the live web; a failure
   is a high-severity `BROKEN_LINK`.
6. **Emit the report.** Print a human summary and (if `--output`) write JSON.
7. **Gate.** Exit non-zero if any issue reaches `fail_on`.

## QA rules
| Code | Severity | Condition |
|---|---|---|
| `OVERDUE` | high | `dueDate` is in the past and status is not `Done` |
| `BROKEN_LINK` | high | a URL in the description does not resolve against the live web |
| `UNASSIGNED_HIGH` | medium | priority is `High` and there is no assignee |
| `NO_DESCRIPTION` | low | description is empty |
| `STALE` | low | created ≥ 30 days ago and still `Todo` |

## Validation / definition of done
- Run completes without an unhandled exception even if links are down or the API is briefly
  unavailable (transient errors are retried; everything is captured in the report).
- Every task appears in `results` with `passed` true/false.
- The JSON report validates against the shape in `models.py` (`summary` + `results[]`).
- Exit code reflects the gate: `0` clean, `1` issues at/above `fail_on`, `2` automation aborted.

## What to delegate vs. review
- **Delegate to the agent:** adding new QA rules, extending the report shape, new endpoints.
- **Review manually:** auth/credential handling, the severity thresholds that gate a release,
  and anything that would mutate production data.

## Extending
Add a rule by appending an `Issue` in `qa.evaluate_task`. Add a new severity by extending
`SEVERITY_ORDER` in `models.py`. Keep each rule pure and independently testable.
