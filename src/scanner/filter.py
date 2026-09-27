"""
scanner/filter.py — post-filter for repo candidates.

This is the second stage of the scanner pipeline: take what `sources.py`
returned and decide which candidates pass. The filter is rule-based
and conservative — it errs on the side of *excluding* rather than
including. False positives (a repo that passes but isn't useful)
waste the curator's time; false negatives (a repo that's useful but
doesn't pass) are caught by adding more candidates upstream.

Public API:
    from scanner.filter import Filter, apply_filter, LICENSES_OK

    f = Filter(
        languages=["python", "rust"],
        licenses=LICENSES_OK,           # permissive SPDX ids
        min_stars=200,
        max_age_days=90,
    )
    kept, dropped = apply_filter(repos, f)

The filter is pure-function: it does not touch the network. The CLI
exists only for testing against a captured response.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List, Set, Tuple

from .sources import Repo


# Permissive SPDX license identifiers we accept. Mirrors the canonical
# permissive set (OSI-approved + FSF-free + a few unlisted but
# widely-used permissive licenses).
LICENSES_OK: Set[str] = {
    "MIT",                       # most common
    "Apache-2.0",                # Apache License 2.0
    "BSD-2-Clause", "BSD-3-Clause", "BSD-3-Clause-No-Nuclear-License",
    "ISC",                       # Internet Systems Consortium
    "MPL-2.0",                   # Mozilla Public License 2.0 (weak copyleft)
    "Unlicense",                 # public-domain dedication
    "CC0-1.0",                   # Creative Commons Zero (public domain)
    "Zlib",                      # zlib license
    "0BSD",                      # FSF / BSD-0
    "Artistic-2.0",
    "EFL-2.0",                   # Eiffel Forum License
    "NCSA",                      # University of Illinois/NCSA
    "PSF-2.0",                   # Python Software Foundation
}

# Common but rejected: ( GPL family (copyleft), AGPL (network copyleft),
# LGPL (weak copyleft), SSPL (server-side), BUSL (BUSL-1.1, source-available
# not open), CC-BY-NC-* (non-commercial), JSON (no), noassertion (unknown).


@dataclass
class Filter:
    """Configuration for the repo filter.

    Defaults are tuned for "discover load-bearing open-source code that
    might inspire or improve fieldcore/simself": python or rust, MIT-class
    license, ≥200 stars, pushed within 90 days.
    """
    languages: Set[str] = field(default_factory=lambda: {"python", "rust"})
    licenses: Set[str] = field(default_factory=lambda: set(LICENSES_OK))
    min_stars: int = 200
    max_age_days: int = 90
    require_description: bool = False
    exclude_archived: bool = True
    exclude_forks: bool = False  # off by default; many useful tools are forks

    def matches(self, repo: Repo) -> bool:
        """Return True iff the repo passes all enabled filters."""
        if self.exclude_archived and repo.archived:
            return False
        if repo.language.lower() not in {l.lower() for l in self.languages}:
            return False
        if self.licenses and repo.license.upper() not in \
                {l.upper() for l in self.licenses}:
            return False
        if repo.stars < self.min_stars:
            return False
        if not repo.is_recent(self.max_age_days):
            return False
        if self.require_description and not repo.description.strip():
            return False
        return True


def apply_filter(repos: Iterable[Repo], f: Filter) -> Tuple[List[Repo], List[Tuple[Repo, str]]]:
    """Apply the filter. Return (kept, dropped_with_reason).

    `dropped_with_reason` is a list of (repo, reason) pairs where reason
    is a short string explaining why the repo was filtered out. Useful
    for debugging the filter and for surfacing in the daily report.
    """
    kept: List[Repo] = []
    dropped: List[Tuple[Repo, str]] = []
    for r in repos:
        if f.exclude_archived and r.archived:
            dropped.append((r, "archived")); continue
        if r.language.lower() not in {l.lower() for l in f.languages}:
            dropped.append((r, f"language={r.language!r} not in {sorted(f.languages)}")); continue
        if f.licenses and r.license.upper() not in {l.upper() for l in f.licenses}:
            dropped.append((r, f"license={r.license!r} not permissive")); continue
        if r.stars < f.min_stars:
            dropped.append((r, f"stars={r.stars} < min={f.min_stars}")); continue
        if not r.is_recent(f.max_age_days):
            dropped.append((r, f"pushed_at={r.pushed_at[:10]} > {f.max_age_days}d old")); continue
        if f.require_description and not r.description.strip():
            dropped.append((r, "no description")); continue
        kept.append(r)
    return kept, dropped


# --- CLI for testing -------------------------------------------------------

def _cli():
    import argparse, json, sys
    p = argparse.ArgumentParser(description="Apply Filter to a JSON file of Repo dicts.")
    p.add_argument("input", help="JSON file (list of Repo dicts, from sources.py CLI)")
    p.add_argument("--min-stars", type=int, default=200)
    p.add_argument("--max-age-days", type=int, default=90)
    p.add_argument("--language", action="append", default=None,
                   help="Repeat to set multiple languages.")
    args = p.parse_args()

    with open(args.input) as f:
        raw = json.load(f)
    repos = [Repo(**r) for r in raw]

    f = Filter(
        languages=set(args.language) if args.language else {"python", "rust"},
        min_stars=args.min_stars,
        max_age_days=args.max_age_days,
    )
    kept, dropped = apply_filter(repos, f)
    print(f"kept: {len(kept)}    dropped: {len(dropped)}")
    for r in kept:
        print(f"  KEEP  {r.full_name}  stars={r.stars}  lang={r.language}")
    for r, why in dropped[:10]:
        print(f"  DROP  {r.full_name}: {why}")


if __name__ == "__main__":
    _cli()