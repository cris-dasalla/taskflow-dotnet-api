"""Entry point: orchestrate a full QA run against the live TaskFlow API.

    python -m taskflow_qa --seed            # create demo data, then audit
    python -m taskflow_qa                    # audit whatever is there
    python -m taskflow_qa --output report.json

Exit code is non-zero when issues at/above ``--fail-on`` are found, so this
drops straight into CI or a scheduled job and gates a release.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone

from .client import TaskFlowClient, TaskFlowError
from .models import SEVERITY_ORDER, QAReport
from .qa import evaluate_task
from .seed import seed_demo_tasks

DEFAULT_BASE_URL = "http://localhost:5020"


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="taskflow_qa", description=__doc__)
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--email", default="demo@taskflow.dev")
    p.add_argument("--password", default="Demo123!")
    p.add_argument("--seed", action="store_true", help="create demo tasks before auditing")
    p.add_argument("--no-verify-links", action="store_true", help="skip live link checks")
    p.add_argument("--output", help="write the JSON report to this path")
    p.add_argument(
        "--fail-on",
        choices=list(SEVERITY_ORDER),
        default="high",
        help="exit non-zero if any issue reaches this severity (default: high)",
    )
    return p.parse_args(argv)


def _print_summary(report: QAReport) -> None:
    d = report.to_dict()
    s = d["summary"]
    print("\n" + "=" * 64)
    print(f"  TaskFlow QA report  |  {d['baseUrl']}")
    print("=" * 64)
    print(f"  Tasks audited      : {s['totalTasks']}")
    print(f"  Tasks with issues  : {s['tasksWithIssues']}")
    print(f"  Total issues       : {s['totalIssues']}")
    print(f"  Broken links       : {s['brokenLinks']}")
    print(f"  High severity      : {s['highSeverity']}")
    print("-" * 64)
    for r in report.results:
        if r.passed:
            print(f"  [ OK ] #{r.task_id} {r.title}")
        else:
            flag = "[FAIL]" if r.max_severity == "high" else "[WARN]"
            print(f"  {flag} #{r.task_id} {r.title}  ({r.max_severity})")
            for issue in r.issues:
                print(f"           - {issue.severity:<6} {issue.code}: {issue.message}")
    print("=" * 64)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    # Be robust to legacy Windows console encodings (cp1252) so output never crashes.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except Exception:
            pass
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s  %(levelname)-7s %(name)s  %(message)s"
    )
    log = logging.getLogger("taskflow_qa")

    client = TaskFlowClient(args.base_url)
    try:
        client.login(args.email, args.password)
        if args.seed:
            created = seed_demo_tasks(client)
            log.info("Seeded %d demo tasks", created)

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        report = QAReport(generated_at=now.isoformat(timespec="seconds") + "Z", base_url=args.base_url)
        for task in client.iter_all_tasks():
            report.results.append(
                evaluate_task(task, now=now, verify_links=not args.no_verify_links)
            )
    except TaskFlowError as exc:
        log.error("Automation aborted: %s", exc)
        return 2

    _print_summary(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(report.to_dict(), fh, indent=2)
        log.info("Structured report written to %s", args.output)

    # Gate: fail the run if anything reached the configured severity threshold.
    threshold = SEVERITY_ORDER[args.fail_on]
    worst = max(
        (SEVERITY_ORDER[r.max_severity] for r in report.results if not r.passed),
        default=0,
    )
    if worst >= threshold:
        log.warning("QA gate failed: found issues at/above '%s'", args.fail_on)
        return 1
    log.info("QA gate passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
