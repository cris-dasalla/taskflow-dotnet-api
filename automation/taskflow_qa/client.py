"""TaskFlow API client — auth, pagination, and resilient HTTP.

This is the integration layer. It owns three things you have to get right when
wiring any real API automation:

  1. **Auth** — log in once for a JWT, attach it as a bearer token, and
     transparently re-authenticate if the token expires mid-run (401).
  2. **Resilience** — retry transient failures (timeouts, 5xx) with
     exponential backoff; fail loudly and clearly on everything else.
  3. **Pagination** — never assume one page; walk until the API says stop.

Standard library only (``urllib``) so it runs anywhere with zero install.
"""
from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any, Iterator

log = logging.getLogger("taskflow_qa.client")


class TaskFlowError(RuntimeError):
    """Raised when the API cannot satisfy a request after retries."""


class TaskFlowClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_base: float = 0.5,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._token: str | None = None
        self._credentials: tuple[str, str] | None = None

    # -- auth ---------------------------------------------------------------
    def login(self, email: str, password: str) -> None:
        """Authenticate and cache the JWT (and the credentials, for re-auth)."""
        self._credentials = (email, password)
        data = self._request(
            "POST",
            "/api/auth/login",
            body={"email": email, "password": password},
            authed=False,
        )
        self._token = data["token"]
        log.info("Authenticated as %s (token expires %s)", data["email"], data["expiresAt"])

    # -- task endpoints -----------------------------------------------------
    def iter_all_tasks(self, page_size: int = 50) -> Iterator[dict[str, Any]]:
        """Yield every task, transparently following pagination metadata."""
        page = 1
        while True:
            payload = self._request(
                "GET", f"/api/tasks?page={page}&pageSize={page_size}"
            )
            for item in payload.get("items", []):
                yield item
            if not payload.get("hasNext"):
                break
            page += 1

    def create_task(self, task: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/api/tasks", body=task)

    # -- core HTTP with retry + re-auth ------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        authed: bool = True,
        _reauthed: bool = False,
    ) -> Any:
        url = f"{self.base_url}{path}"
        payload = json.dumps(body).encode() if body is not None else None
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            req = urllib.request.Request(url, data=payload, method=method)
            req.add_header("Accept", "application/json")
            if payload is not None:
                req.add_header("Content-Type", "application/json")
            if authed and self._token:
                req.add_header("Authorization", f"Bearer {self._token}")

            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode()
                    return json.loads(raw) if raw else None

            except urllib.error.HTTPError as exc:
                # 401 with cached credentials -> token likely expired; re-auth once.
                if exc.code == 401 and authed and not _reauthed and self._credentials:
                    log.warning("401 received — re-authenticating and retrying")
                    self.login(*self._credentials)
                    return self._request(
                        method, path, body=body, authed=authed, _reauthed=True
                    )
                # 5xx is transient and worth retrying; 4xx is the caller's fault.
                if 500 <= exc.code < 600 and attempt < self.max_retries:
                    last_error = exc
                    self._sleep(attempt, exc)
                    continue
                detail = self._safe_problem_detail(exc)
                raise TaskFlowError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc

            except (urllib.error.URLError, TimeoutError) as exc:
                # Connection refused, DNS, timeout -> transient, back off and retry.
                last_error = exc
                if attempt < self.max_retries:
                    self._sleep(attempt, exc)
                    continue

        raise TaskFlowError(f"{method} {path} failed after {self.max_retries} attempts: {last_error}")

    def _sleep(self, attempt: int, exc: Exception) -> None:
        delay = self.backoff_base * (2 ** (attempt - 1))
        log.warning("Attempt %d failed (%s) — retrying in %.1fs", attempt, exc, delay)
        time.sleep(delay)

    @staticmethod
    def _safe_problem_detail(exc: urllib.error.HTTPError) -> str:
        """Pull the RFC 7807 ProblemDetails 'detail' if the API returned one."""
        try:
            body = json.loads(exc.read().decode())
            return body.get("detail") or body.get("title") or exc.reason
        except Exception:
            return str(exc.reason)
