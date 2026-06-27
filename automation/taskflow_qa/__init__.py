"""TaskFlow QA — an API automation that audits tasks against the live TaskFlow API.

Mirrors a real agency workflow: authenticate, page through every record,
verify external links against the live source, apply QA rules, and emit a
structured, machine-readable report. Standard library only — no dependencies.
"""

__version__ = "1.0.0"
