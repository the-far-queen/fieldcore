"""
scanner/ — the daily repo scan pipeline.

This is a read-only scanner. It does NOT call any LLM (curator is a
future PR). It does NOT generate patches (ingest is a future PR). It
does NOT post to GitHub. It pulls candidate repos from the public
GitHub Search API, filters by language / license / stars / recency,
and writes a summary to the vault.

Public API:
    from scanner import sources, filter, daily

    # low-level
    repos = list(sources.search_repos("kernel", languages=["python"],
                                       min_stars=200))
    kept, dropped = filter.apply_filter(repos, filter.Filter())

    # high-level (the daily scan)
    result = daily.run(min_stars=200, max_age_days=90)

    # CLI
    python -m src.scanner.daily --min-stars 500 --max-pages 3
    python -m src.scanner.sources --query "kernel" --language python

Safety:
  - GitHub API is hit with GET only. No POST/PUT/DELETE.
  - Rate-limited at 6s between calls (well under the 10 req/min
    unauthenticated search endpoint limit).
  - Output goes to $SCAN_DIR (default: vault/10-minimax/40-scratch/scans/<date>/).
    Nothing is written to GitHub. Nothing is written to fieldcore/simself.
  - $GITHUB_TOKEN, if set, is used only for the Authorization header
    and is never logged.
"""

__version__ = "0.1.0"
__all__ = ["sources", "filter", "daily"]