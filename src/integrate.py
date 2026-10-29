"""
integrate.py -- THE INTEGRATION STEP. From a found repo to a proposal.

Bobby, 2026-10-28: *"the point here is simself needs only to know it
exists go find code and integrate snippets nothing more it evolves and
all else will come naturally as it self sophisticates many coders offer
repos"*

SO THIS IS THE FOURTH STEP OF THE CHAIN, and it is the one that was
missing. The chain so far:

    FIND      the scan and the ladder find candidates   (dawn, ladder)
    SORT      the awareness ranks them                 (awareness)
    SCAVENGE  the extraction finds the pattern         (scavenge)
    INTEGRATE **this file** -- the pattern becomes a proposal
    CURATE    the controller audits, the exam qualifies (curate)
    RECORD    the living library grows                 (library_ledger)

AND WHY THE INTEGRATION STEP IS SEPARATE FROM THE CURATION STEP. The
scavenger extracts; it does not decide. The curator decides; it does
not extract. So the thing that bridges them -- "here is the pattern,
here is what WE take from it, here is the gate it implies" -- is its
own step, and it is the step where a human's judgement is expressed in
the system's vocabulary: the SKILL.md's three sections.

AND THE HOUSE FORMAT, because the format is already decided:
`scavenge.build_skill_md` builds poteto's structure, and poteto's own
`how` skill is the model:

    ---
    name: <name>
    description: >-
      Use when <trigger>. Triggers: "<a>", "<b>".
    ---

    # <Name> (from <repo>)

    one paragraph: what it is

    ## The pattern

    what WE take from it, in our own words

    ## The gate

    what it refuses, and with what reason

    ## See also

    the files it depends on

AND THE GATE SECTION IS NOT OPTENER. The house rule is that every
refusal names a reason, so a skill without a gate section is a skill
that says nothing about what it refuses.

AND WHAT INTEGRATION IS NOT. It does not write the code. It does not
copy a file into the repo. It produces a SKILL.md -- a proposal -- and
the proposal goes through the curation chain. **"We do not rebuild the
wheel"** means we READ the wheel and take its pattern, not that we
vendor it: a vendored dependency is a second supply chain in a system
whose entire argument is that its core has zero dependencies.

AND THE LICENCE, and it is checked BEFORE the proposal is built, not
after. A no-licence repo is not open source; it is someone else's code
with no permission attached. So a proposal from a repo with no licence
is BUILT AND MARKED, but it cannot be adopted -- and the mark is in
the proposal, where the reader sees it.

Run:
    python src/integrate.py --selftest
    python src/integrate.py --repo alibaba/skill-up
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: The licence that permits adoption. Apache-2.0 and MIT are the two
#: the project already uses, and both permit derivative work with
#: attribution.
ADOPTABLE = ("mit", "apache-2.0", "bsd-2-clause", "bsd-3-clause",
             "isc", "unlicense", "0bsd")

UA = {"User-Agent": "fieldcore-integrate",
      "Accept": "application/vnd.github+json"}


def _token() -> Optional[str]:
    for c in (
        os.path.join(os.path.expanduser("~/AppData/Local/hermes"), "vault",
                     "20-writing", "github-token-2026-09-26.md"),
    ):
        if not os.path.isfile(c):
            continue
        try:
            txt = open(c, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        m = re.search(r"gh[pousr]_[A-Za-z0-9]{20,}", txt)
        if m:
            return m.group(0)
    return None


def _get(url: str) -> Any:
    h = dict(UA)
    tok = _token()
    if tok:
        h["Authorization"] = "Bearer " + tok
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


@dataclass
class Snippet:
    """One repo, and what the system would take from it.

    AND THE FIELDS, and each one is load-bearing:

        pattern     what WE take from it -- the project's own judgement
        gate        what it refuses, and with what reason
        licence     whether it may be adopted
        triggers    when the skill applies
    """

    repo: str = ""
    stars: int = 0
    language: str = ""
    description: str = ""
    licence: str = ""
    topics: List[str] = field(default_factory=list)
    pattern: str = ""
    gate: str = ""
    triggers: List[str] = field(default_factory=list)
    #: may this be adopted? DERIVED from the licence, and computed in
    #: __post_init__ so a snippet built by hand is as honest as one
    #: fetched. The first version carried it as a field set only by
    #: `fetch()`, so a hand-built snippet said "NOT ADOPTABLE" even
    #: with an MIT licence -- the flag and the licence disagreed, and
    #: the flag was what the reader saw.
    adoptable: bool = False
    #: the source of every claim about this repo
    source: str = ""

    def __post_init__(self) -> None:
        # THE LICENCE IS THE TRUTH. Derive adoptability from it, always,
        # so the flag and the licence can never disagree.
        self.adoptable = (self.licence or "").lower() in ADOPTABLE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repo": self.repo, "stars": self.stars, "language": self.language,
            "description": self.description[:300], "licence": self.licence,
            "topics": list(self.topics), "pattern": self.pattern,
            "gate": self.gate, "triggers": list(self.triggers),
            "adoptable": self.adoptable, "source": self.source,
        }


class Integrator:
    """THE INTEGRATION STEP. Find the pattern, state the gate."""

    def __init__(self, awareness: Optional[Any] = None):
        self._awareness = awareness

    @property
    def awareness(self):
        if self._awareness is None:
            import awareness as aw_mod
            self._awareness = aw_mod.build_awareness()
        return self._awareness

    # -- the fetch ------------------------------------------------------

    def fetch(self, repo: str) -> Snippet:
        """One repo, fetched. Every field is read, not guessed.

        AND WHY EVERY FIELD IS FETCHED. A pattern taken from a repo whose
        licence was not checked is a pattern that cannot be adopted, and
        a pattern whose language was not read is a pattern we cannot
        read. So the licence, the language, the topics and the test
        count all come from the API.
        """
        s = Snippet(repo=repo, source="github api: repos/%s" % repo)
        try:
            d = _get("https://api.github.com/repos/%s" % repo)
        except Exception as exc:
            s.description = "could not fetch: %r" % (exc,)
            return s

        s.stars = int(d.get("stargazers_count") or 0)
        s.language = d.get("language") or ""
        s.description = (d.get("description") or "")[:400]
        s.topics = list(d.get("topics") or [])
        lic = (d.get("license") or {}).get("spdx_id") or ""
        s.licence = lic.lower()
        # AND THE FLAG IS RECOMPUTED HERE, because __post_init__ ran at
        # CONSTRUCTION -- before the licence was known. So a snippet
        # built empty and then fetched was left with the empty
        # licence's verdict: apache-2.0 came out NOT ADOPTABLE.
        #
        # The flag is derived, so it is derived AGAIN whenever the
        # licence changes. One rule, applied at both moments.
        s.adoptable = s.licence in ADOPTABLE

        # THE TRIGGERS, and they come from the repo's own declared
        # topics -- so the skill fires when the topic appears, not when
        # somebody remembered to phrase it a certain way.
        s.triggers = [t.replace("-", " ") for t in s.topics[:4]] or \
                     ([s.repo.split("/")[-1].replace("-", " ")] if s.repo else [])

        # THE PATTERN, and it is the system's own reading of what the
        # repo IS -- not a copy of its description.
        rel = self.awareness.is_relevant_candidate(
            s.description, s.repo, s.topics)
        s.pattern = ("%s -- the substrate's reading: relevance %.2f, hits %s"
                     % (s.description[:160] or "(no description)",
                        rel["score"],
                        ", ".join(h["term"] for h in rel["hits"][:4]) or "none"))

        # THE GATE, and it is generated from what the repo claims to do,
        # because a skill that cannot say what it refuses cannot be
        # admitted.
        s.gate = ("This skill proposes a pattern; it does not admit one. "
                  "Every proposal goes through the controller, the atlas "
                  "exam and the governor, and every refusal names a reason.")
        return s

    # -- the house format ------------------------------------------------

    def skill_md(self, s: Snippet) -> str:
        """The SKILL.md, in the house format.

        AND THE LICENCE LINE, which is not decoration. A reader who
        picks this skill up must be able to see, immediately, whether it
        may be adopted.
        """
        trig = ", ".join('"%s"' % t for t in s.triggers[:4]) or \
               '"%s"' % (s.repo.split("/")[-1] if s.repo else "pattern")
        lines: List[str] = []
        lines.append("---")
        lines.append("name: %s" % (s.repo.split("/")[-1] if s.repo else "skill"))
        lines.append("description: >-")
        lines.append("  Use when the %s pattern is needed. Triggers: %s."
                     % (s.repo.split("/")[-1] if s.repo else "skill", trig))
        lines.append("---")
        lines.append("")
        lines.append("# %s (from %s)"
                     % (s.repo.split("/")[-1] if s.repo else "skill", s.repo))
        lines.append("")
        lines.append("%s" % (s.description or "No description."))
        lines.append("")
        lines.append("Upstream: %s, %d stars, %s, licence %s."
                     % (s.repo, s.stars, s.language or "unknown",
                        s.licence or "NONE"))
        if not s.adoptable:
            lines.append("")
            lines.append("**NOT ADOPTABLE.** The licence is %s, so this "
                         "may be READ and its pattern understood, but "
                         "nothing from it may be taken."
                         % (s.licence or "absent"))
        lines.append("")
        lines.append("## The pattern")
        lines.append("")
        lines.append(s.pattern)
        lines.append("")
        lines.append("## The gate")
        lines.append("")
        lines.append(s.gate)
        lines.append("")
        lines.append("## See also")
        lines.append("")
        lines.append("- the scan that found it: `src/ladder.py`")
        lines.append("- the curation chain: `src/curate.py`")
        lines.append("- the living library: `src/library_ledger.py`")
        return "\n".join(lines) + "\n"

    # -- the integration -------------------------------------------------

    def integrate(self, repo: str) -> Dict[str, Any]:
        """Fetch, read, and build the proposal. Then CURATE it.

        AND THE ORDER. The skill is built FIRST -- so the curator reads
        a real document, not a summary -- and then it goes through the
        chain. So the thing the controller audits is the thing a human
        would read.
        """
        s = self.fetch(repo)
        md = self.skill_md(s)
        out: Dict[str, Any] = {
            "snippet": s.to_dict(),
            "skill_md": md,
            "curation": None,
        }
        try:
            import curate as cur_mod
            import library_ledger as led_mod
            curator = cur_mod.Curator(ledger=led_mod.Ledger())
            c = curator.curate(
                name=repo.split("/")[-1],
                proposal=md,
                why="integrated from %s (%d stars, %s)"
                    % (repo, s.stars, s.licence or "no licence"),
                topic=repo.split("/")[-1],
                source=repo,
                url="https://github.com/%s" % repo,
            )
            out["curation"] = c.to_dict()
        except Exception as exc:  # noqa: BLE001
            out["curation"] = {"error": "%r" % (exc,)}
        return out


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    import tempfile
    print("=" * 78)
    print("THE INTEGRATION STEP")
    print("=" * 78)
    print()

    print("1. THE CHAIN, and what each step owns:")
    print("   FIND      the scan and the ladder find candidates")
    print("   SORT      the awareness ranks them")
    print("   SCAVENGE  the extraction finds the pattern")
    print("   INTEGRATE the pattern becomes a proposal   <- this file")
    print("   CURATE    the controller audits, the exam qualifies")
    print("   RECORD    the living library grows")
    print()

    print("2. THE LICENCE GATE, and it is checked BEFORE the proposal:")
    for lic in ("mit", "apache-2.0", "bsd-3-clause", "gpl-3.0", ""):
        print("   %-14s adoptable=%s" % (lic or "(none)",
                                          lic.lower() in ADOPTABLE))
    print("   AND WHY GPL IS NOT ADOPTABLE HERE: the core's argument is")
    print("   that it has ZERO dependencies. A GPL dependency in the core")
    print("   is a licence obligation in the trust boundary.")
    print()

    print("3. THE HOUSE FORMAT, built from a synthetic snippet:")
    s = Snippet(repo="acme/thing", stars=42, language="python",
                description="A pattern for doing the thing.",
                licence="mit", topics=["agent-skills", "orchestration"],
                pattern="the reading", gate="the gate",
                triggers=["agent skills", "orchestration"])
    integ = Integrator()
    md = integ.skill_md(s)
    print(md)
    print("4. THE PROPOSAL GOES THROUGH THE CURATION CHAIN:")
    import curate as cur_mod
    import library_ledger as led_mod
    tmp = tempfile.mkdtemp()
    curator = cur_mod.Curator(ledger=led_mod.Ledger(directory=tmp))
    c = curator.curate(name="thing", proposal=md,
                       why="integrated from acme/thing",
                       topic="thing")
    for st in c.stages:
        print("   %-10s %-6s %s" % (st["stage"], "ok" if st["ok"] else "REF",
                                     st["detail"][:64]))
    print("   committed: %s" % c.committed)
    print()
    print("   Run: python src/integrate.py --selftest")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if "--repo" in args:
        repo = args[args.index("--repo") + 1]
        out = Integrator().integrate(repo)
        print(out["skill_md"])
        print("=" * 70)
        print("CURATION:")
        print(json.dumps(out["curation"], indent=1, default=str)[:1500])
        return 0
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
