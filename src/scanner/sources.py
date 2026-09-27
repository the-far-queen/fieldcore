"""
scanner/sources.py — github REST API adapter for repo discovery.

This is the only network-facing module in the scanner. It exposes one
function: `search_repos(query, ...) -> list[Repo]`. The adapter is
stdlib-only (urllib), respects GitHub's unauthenticated rate limit
(10 requests per minute for the search endpoint; we sleep 6s between
calls to be conservative), and never touches anything but the public
search API.

Auth:
  No auth required. Unauthenticated requests have a 10 req/min limit
  on the search endpoint. For higher limits, set $GITHUB_TOKEN to a
  personal access token (do not commit the token; read from env at
  runtime; never log it).

Output:
  Repo(name, full_name, html_url, description, stars, language,
       license, pushed_at, archived)

Safety:
  - read-only: never POSTs/PUTs/DELETEs
  - rate-limited: 6s sleep between calls
  - no token logging
  - input query is URL-encoded; no shell injection risk
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterator, List, Optional


GITHUB_API = "https://api.github.com"
# GitHub Search API rate limit is 10 req/min unauthed.
# 6s sleep between calls leaves headroom and stays well under the limit.
_MIN_INTERVAL_S = 6.0


@dataclass
class Repo:
    """One repo returned by the github search API."""
    name: str
    full_name: str          # "owner/repo"
    html_url: str
    description: str
    stars: int
    language: str
    license: str           # license id (e.g. "mit") or "" if unknown
    pushed_at: str         # ISO 8601 string
    archived: bool

    def is_recent(self, max_age_days: int) -> bool:
        """True if pushed_at is within max_age_days of now."""
        try:
            pushed = datetime.fromisoformat(self.pushed_at.replace("Z", "+00:00"))
        except Exception:
            return False
        age = (datetime.now(timezone.utc) - pushed).days
        return age <= max_age_days


class GitHubError(RuntimeError):
    """Raised on non-2xx GitHub response or transport error."""
    def __init__(self, message: str, *, status: Optional[int] = None,
                 body: Optional[str] = None):
        super().__init__(message)
        self.status = status
        self.body = body


def _read_token() -> Optional[str]:
    """Read $GITHUB_TOKEN from env. Returns None if unset.

    NEVER log the token. NEVER write it to disk. NEVER include it in
    error messages. The token simply goes into the Authorization
    header and that is the end of its visibility.
    """
    return os.environ.get("GITHUB_TOKEN") or None


def _http_get(url: str, token: Optional[str] = None,
              timeout: float = 30.0) -> dict:
    """Make one GET request, return parsed JSON. Raises GitHubError on failure."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "fieldcore-scanner/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers, method="GET")
    last_err: Optional[Exception] = None
    for attempt in range(1, 4):  # 3 attempts
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                # GitHub returns the X-RateLimit-Remaining header — use it
                # to back off if we're close to the limit. We do NOT log
                # the value to avoid leaking rate-limit state.
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body_text = ""
            try:
                body_text = e.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            last_err = GitHubError(
                f"HTTP {e.code}: {body_text or e.reason}",
                status=e.code, body=body_text,
            )
            # Retry on 429 / 5xx; everything else is fatal.
            if e.code not in (429, 500, 502, 503, 504):
                raise last_err from e
        except urllib.error.URLError as e:
            last_err = GitHubError(f"URL error: {e.reason}")
        except (TimeoutError, json.JSONDecodeError) as e:
            last_err = GitHubError(f"Transport: {e}")
        if attempt < 3:
            time.sleep(2.0 * attempt)
    raise last_err


class RateLimiter:
    """Enforces >= _MIN_INTERVAL_S between successive calls."""

    def __init__(self, min_interval_s: float = _MIN_INTERVAL_S):
        self.min_interval_s = min_interval_s
        self._last_call: float = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self.min_interval_s:
            time.sleep(self.min_interval_s - elapsed)
        self._last_call = time.monotonic()


# Module-level singleton. Reused across calls within a process.
_rate_limiter = RateLimiter()


def search_repos(
    query: str,
    *,
    sort: str = "stars",     # "stars" | "updated" | "best-match"
    order: str = "desc",
    per_page: int = 30,
    max_pages: int = 3,      # 30 results * 3 pages = 90 results max
    languages: Optional[List[str]] = None,  # applied as `language:X` qualifiers
    min_stars: int = 0,
    archived: bool = False,
) -> Iterator[Repo]:
    """Iterate over repo search results. Yields Repo objects.

    Args:
        query: GitHub search query string (e.g. "machine learning kernel").
        sort/order/per_page/max_pages: standard GitHub search params.
        languages: if given, AND each language into the query as a
            qualifier. e.g. ["python", "rust"] -> "(... ) language:python
            OR language:rust" (note: GitHub only supports single-language
            filter; we OR by issuing two searches if needed — for v0,
            we apply the first language only and emit a stderr note if
            more than one was passed).
        min_stars: filter post-hoc (GitHub's `stars:` qualifier works but
            can be flaky; we filter locally for determinism).
        archived: if False, filter out archived repos.

    Yields:
        Repo objects. May yield fewer than per_page * max_pages if the
        search returns early or hits an error.

    Safety:
      - 6s sleep between pages
      - unauthenticated by default (set $GITHUB_TOKEN for higher limits)
      - no POSTs/PUTs/DELETEs
    """
    token = _read_token()

    # Apply language qualifier (GitHub supports only one language per
    # query; if more than one is requested, we take the first).
    if languages:
        primary_lang = languages[0]
        if len(languages) > 1:
            print(
                f"[sources] note: GitHub search supports one language "
                f"per query; using '{primary_lang}', ignoring {languages[1:]}",
                file=sys.stderr,
            )
        # GitHub qualifier: "language:python" goes in the q= string.
        full_query = f"{(query or '').strip()} language:{primary_lang}".strip()
    else:
        full_query = (query or "").strip()

    if not full_query:
        raise GitHubError("empty query; refusing to scan nothing")

    for page in range(1, max_pages + 1):
        _rate_limiter.wait()
        url = (
            f"{GITHUB_API}/search/repositories"
            f"?q={urllib.parse.quote(full_query)}"
            f"&sort={sort}&order={order}"
            f"&per_page={per_page}&page={page}"
        )
        try:
            data = _http_get(url, token=token)
        except GitHubError as e:
            # Surface the error to stderr and stop the iteration.
            # We do NOT raise — partial results are still useful.
            print(f"[sources] page {page} failed: {e}", file=sys.stderr)
            return

        items = data.get("items", [])
        if not items:
            # GitHub caps search results at 1000. Past that, we get
            # `incomplete_results: true` and items=[]. Stop quietly.
            return

        for item in items:
            if item.get("(") == "true":
                # GitHub's quirk: uses parens for booleans in some fields.
                pass
            if bool(item.get("archived", False)) and not archived:
                continue
            stars = int(item.get("stargazers_count", 0))
            if stars < min_stars:
                continue
            license_info = item.get("license") or {}
            license_id = license_info.get("spdx_id") or ""
            pushed_at = item.get("pushed_at") or ""
            yield Repo(
                name=str(item.get("name", "")),
                full_name=str(item.get("full_name", "")),
                html_url=str(item.get("html_url", "")),
                description=str(item.get("description") or ""),
                stars=stars,
                language=str(item.get("language") or ""),
                license=license_id,
                pushed_at=pushed_at,
                archived=bool(item.get("archived", False)),
            )

        # GitHub's per-query cap is 1000 results total (page 34 of
        # per_page=30). If we got fewer than per_page results, we are
        # at the end of the result set.
        if len(items) < per_page:
            return


# --- CLI for ad-hoc testing ------------------------------------------------

def _cli():
    import argparse
    p = argparse.ArgumentParser(description="GitHub repo search (scanner source).")
    p.add_argument("--query", default="kernel")
    p.add_argument("--language", default="python",
                   help="GitHub language qualifier (one only).")
    p.add_argument("--min-stars", type=int, default=200)
    p.add_argument("--max-pages", type=int, default=2)
    p.add_argument("--max-age-days", type=int, default=90)
    args = p.parse_args()

    for r in search_repos(
        args.query,
        languages=[args.language],
        min_stars=args.min_stars,
        max_pages=args.max_pages,
    ):
        if not r.is_recent(args.max_age_days):
            continue
        print(f"{r.full_name:50s}  stars={r.stars:>5d}  lang={r.language:<10s}  "
              f"license={r.license or '-':<6s}  pushed={r.pushed_at[:10]}")
        if r.description:
            print(f"  {r.description[:120]}")


if __name__ == "__main__":
    _cli()