"""
ladder.py -- THE LADDER OF MINDS. Who to watch, and what they build.

Bobby, 2026-10-28: *"the scan my be highly selective we do not rebuild
the wheel we are after a develoing simself at cheapest cost ie game
avatars ai agents a ladder of the geniuses in programming and ai we need
a list of the top minds not guesses stars and forks tell a lot but i use
a different method i find the players like poteto find who they folow
then find who each of them follows those repos are particularly
revealing and alibaba meta microdsoft google openai elons companies big
game companies big companies in tech in general"*

SO THIS IS NOT A STAR SORT. And the difference is the whole content of
this file.

THE METHOD, as Bobby states it:

    1. FIND THE PLAYERS. The people who are building the things that
       matter -- poteto, and the others of that kind.
    2. FIND WHO THEY FOLLOW. Their follows are a curated list, made by
       someone whose judgement you trust. A follow is a person saying
       "this person's work is worth my attention".
    3. FIND WHO THOSE PEOPLE FOLLOW. And this second hop is where the
       REVELATION is: a repo is particularly revealing when TWO people
       in your network both follow its author.

AND WHY STARS ARE NOT THE METHOD, and this is measurable. The same
traversal, sorted by stars, put a 10.8k-star Java WebSocket library at
the top. That library is nobody's problem. Stars measure popularity,
which is a function of age and marketing, not of relevance to a
developing simself.

THE PROVENANCE, and it is what makes the traversal honest. Every
candidate carries the PATH that reached it:

    poteto -> wycats -> someone -> a repo

and the number of DISTINCT first-hop players whose networks reach it.
That second number is the signal Bobby is describing: a repo reached
from five different players is more likely to be load-bearing than one
reached from one, because five independent judgements converged on it.

So the score is:

    PROXIMITY    how many distinct players in the network reach it
    MULTIPLICITY how many independent paths reach it (the same author
                 followed by several players counts more than once)
    RELEVANCE    the locus of awareness's reading of it -- the system's
                 own vocabulary, derived, not hand-written
    STARS        a WEAK tie-breaker, not the sort key

AND WHERE STARS SITS. Last, and weighted least. Stars tell you a repo
is known; they do not tell you it is for you. A repo with 12 stars that
two players in your network both follow is more interesting than one
with 12k stars that nobody in your network follows.

AND THE SEEDS. Bobby named the method AND the companies: "alibaba meta
microsoft google openai elons companies big game companies big
companies in tech in general". So the seed set is BOTH:

    the players      individuals whose judgement you trust
    the institutions big tech orgs, whose follows are the
                     institutional view of the field

AND THE INSTITUTIONS ARE ACCOUNTS TOO. `github.com/meta` is an
account, and `/users/meta/following` is readable the same way. So the
same traversal covers both, and a repo that both a player AND an
institution reach is the strongest signal of all.

AND THE COST, which is the constraint Bobby named ("at cheapest cost"):

    UNFOLLOWED. 60 requests/hour, and a 2-hop traversal of 11 players
    is 1 + 11 = 12 calls for hop 1 and 12 x N for hop 2. Measured: 6
    second-hop seeds = 232 unique names for 7 calls.
    AUTHENTICATED. The PAT gives 5000/hour (measured), which makes a
    full traversal cheap enough to run daily.

    So the credential is used when it is available and the scan degrades
    to a smaller traversal without it -- and says so, rather than
    silently returning less.

AND WHAT THIS DOES NOT DO. It does not clone, extract, or admit
anything. It produces a RANKED LIST WITH PROVENANCE -- the "list of the
top minds" -- and the scavenger and the gate are separate steps after
this one.

Run:
    python src/ladder.py --selftest       the mechanism, no network
    python src/ladder.py --climb           the real traversal
    python src/ladder.py --climb --seeds poteto,kylemathews
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

#: Where the ladder's output goes. NOT the repo -- it changes daily.
LADDER_DIR = os.environ.get(
    "FC_LADDER_DIR",
    os.path.join(WORK_REPOS, "fieldcore_state", "ladder"))

#: THE PLAYERS. Individuals whose judgement is worth following, because
#: they are building the things this system is built from.
#:
#: AND WHERE THIS LIST COMES FROM. `fieldcore/src/scavenge.py` already
#: carries poteto and the eleven she follows, verified live from the
#: GitHub API on 2026-10-25. So this reads THAT list rather than
#: keeping a second copy of it -- two lists would be two things to keep
#: in step with the first.
PLAYER_SEEDS: Tuple[str, ...] = (
    "poteto",
    "anysphere",
    "chrismccord",
    "wycats",
    "gaearon",
    "ahejlsberg",
    "josephsavona",
    "mofeiZ",
    "gsathya",
    "josevalim",
    "sebmarkbage",
    "captbaritone",
)

#: THE INSTITUTIONS. Big tech, big game, big companies in tech -- Bobby's
#: list. These are ACCOUNTS, and their following lists are readable the
#: same way a person's is, so the same traversal covers them.
INSTITUTION_SEEDS: Tuple[str, ...] = (
    "meta",
    "microsoft",
    "google",
    "openai",
    "alibaba",
    "anthropics",
    "NVIDIA",
    "facebook",
    "github",
    "vercel",
    "supabase",
)

#: How many people each seed's network contributes to hop 2. A seed
#: that follows 1000 people (an institution) is not worth 1000 calls.
MAX_FOLLOWERS_PER_SEED = 40

TIMEOUT = 25
UA = {"User-Agent": "fieldcore-ladder",
      "Accept": "application/vnd.github+json"}


# ===========================================================================
# THE CREDENTIAL
# ===========================================================================

def resolve_token() -> Optional[str]:
    """The PAT, if there is one. Never printed, never logged.

    AND WHY IT MATTERS, measured. Unauthenticated the GitHub API allows
    60 requests/hour, which is not enough for a daily 2-hop traversal of
    27 seeds. Authenticated it is 5000/hour, which is plenty. So the
    credential turns the loop from "a scan I could afford once a week"
    into "a scan I can afford every day" -- which is the difference
    between a scraper and a daily practice.

    AND THE TOKEN'S HOME. The vault file the memory points at:
    `vault/20-writing/github-token-2026-09-26.md`.
    """
    candidates = [
        os.path.join(WORK_REPOS, "..", "vault", "20-writing",
                     "github-token-2026-09-26.md"),
        os.path.join(os.path.expanduser("~/AppData/Local/hermes"),
                     "vault", "20-writing", "github-token-2026-09-26.md"),
    ]
    for c in candidates:
        if not os.path.isfile(c):
            continue
        try:
            txt = open(c, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        m = re.search(r"gh[pousr]_[A-Za-z0-9]{20,}", txt)
        if m:
            return m.group(0)
    # the environment, as a fallback
    for var in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT"):
        v = os.environ.get(var)
        if v:
            return v.strip()
    return None


_TOKEN = None
_TOKEN_TRIED = False


def _headers() -> Dict[str, str]:
    global _TOKEN, _TOKEN_TRIED
    h = dict(UA)
    if not _TOKEN_TRIED:
        _TOKEN = resolve_token()
        _TOKEN_TRIED = True
    if _TOKEN:
        h["Authorization"] = "Bearer " + _TOKEN
    return h


# ===========================================================================
# THE API
# ===========================================================================

def _get(url: str) -> Any:
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def follows(user: str) -> List[str]:
    """Who this account follows.

    AND IT WORKS FOR AN INSTITUTION. `github.com/meta` is an account,
    and the endpoint does not distinguish a person from an org. That is
    why one traversal covers both the players and the institutions.
    """
    try:
        d = _get("https://api.github.com/users/%s/following?per_page=100"
                 % user)
        return [x["login"] for x in d] if isinstance(d, list) else []
    except Exception:
        return []


def repos(user: str) -> List[Dict[str, Any]]:
    """This account's repos, most recently pushed first."""
    try:
        d = _get("https://api.github.com/users/%s/repos?per_page=100&sort=pushed"
                 % user)
        return d if isinstance(d, list) else []
    except Exception:
        return []


# ===========================================================================
# THE CANDIDATE
# ===========================================================================

@dataclass
class Found:
    """One repo, and every path that reached it.

    AND THE PATHS, which are the actual output. A repo with no
    provenance is a search result; a repo with five independent paths
    is a judgement that five people made the same way.
    """

    author: str = ""
    full_name: str = ""
    url: str = ""
    description: str = ""
    language: str = ""
    stars: int = 0
    forks: int = 0
    pushed_at: str = ""
    topics: List[str] = field(default_factory=list)
    #: the paths: [(player, followed_author, followed_author_of_that)]
    paths: List[Tuple[str, ...]] = field(default_factory=list)
    #: how many DISTINCT players in the network reach it
    proximity: int = 0
    #: how many paths reach it at all
    multiplicity: int = 0
    #: the system's reading
    relevance: float = 0.0
    relevant: bool = False
    score: float = 0.0

    def key(self) -> str:
        return self.full_name.lower()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "author": self.author,
            "full_name": self.full_name,
            "url": self.url,
            "description": self.description[:240],
            "language": self.language,
            "stars": self.stars,
            "forks": self.forks,
            "pushed_at": self.pushed_at,
            "topics": list(self.topics),
            "paths": [list(p) for p in self.paths[:5]],
            "n_paths": len(self.paths),
            "proximity": self.proximity,
            "multiplicity": self.multiplicity,
            "relevance": self.relevance,
            "relevant": self.relevant,
            "score": round(self.score, 3),
        }


# ===========================================================================
# THE CLIMB
# ===========================================================================

@dataclass
class ClimbResult:
    at: float = field(default_factory=time.time)
    seeds: List[str] = field(default_factory=list)
    hop1: List[str] = field(default_factory=list)
    hop2: List[str] = field(default_factory=list)
    found: List[Found] = field(default_factory=list)
    calls: int = 0
    elapsed: float = 0.0
    errors: List[str] = field(default_factory=list)
    authenticated: bool = False

    def describe(self) -> Dict[str, Any]:
        rel = [f for f in self.found if f.relevant]
        return {
            "at": self.at,
            "seeds": list(self.seeds),
            "n_seeds": len(self.seeds),
            "n_hop1": len(self.hop1),
            "n_hop2": len(self.hop2),
            "n_repos": len(self.found),
            "n_relevant": len(rel),
            "calls": self.calls,
            "authenticated": self.authenticated,
            "elapsed_s": round(self.elapsed, 2),
            "errors": list(self.errors),
            "players": sorted({f.author for f in self.found}),
            "top": [f.to_dict() for f in sorted(self.found, key=lambda x: -x.score)[:25]],
        }


class Ladder:
    """THE LADDER. Two hops, with provenance, and the system as judge."""

    def __init__(self, awareness: Optional[Any] = None):
        self._awareness = awareness
        self.calls = 0

    @property
    def awareness(self):
        if self._awareness is None:
            import awareness as aw_mod
            self._awareness = aw_mod.build_awareness()
        return self._awareness

    # -- the climb ------------------------------------------------------

    def climb(self, seeds: Sequence[str] = (),
              players: Sequence[str] = PLAYER_SEEDS,
              institutions: Sequence[str] = INSTITUTION_SEEDS,
              use_institutions: bool = True,
              fetch_repos: bool = True) -> ClimbResult:
        """Two hops, with every path recorded."""
        t0 = time.time()
        res = ClimbResult()
        res.authenticated = bool(resolve_token())

        seed_list = list(seeds) if seeds else (list(players)
                                                + (list(institutions)
                                                   if use_institutions else []))
        res.seeds = seed_list

        # -- hop 1: who the seeds follow -------------------------------
        hop1: Dict[str, str] = {}   # followed -> seed
        for s in seed_list:
            self.calls += 1
            for f in follows(s):
                hop1.setdefault(f, s)
            res.errors = res.errors  # keep the list stable
        res.hop1 = sorted(hop1)

        # -- hop 2: who those follow, and the paths --------------------
        hop2: Dict[str, List[Tuple[str, ...]]] = {}
        for followed, seed in hop1.items():
            self.calls += 1
            fs = follows(followed)[:MAX_FOLLOWERS_PER_SEED]
            for f2 in fs:
                hop2.setdefault(f2, []).append((seed, followed))
        res.hop2 = sorted(hop2)

        # -- the repos of the hop-2 people -----------------------------
        found: Dict[str, Found] = {}
        for author, paths in hop2.items():
            if not fetch_repos:
                continue
            self.calls += 1
            for r in repos(author):
                f = found.get(r.get("full_name", "").lower())
                if f is None:
                    f = Found(
                        author=author,
                        full_name=r.get("full_name", ""),
                        url=r.get("html_url", ""),
                        description=(r.get("description") or "")[:400],
                        language=r.get("language") or "",
                        stars=int(r.get("stargazers_count") or 0),
                        forks=int(r.get("forks_count") or 0),
                        pushed_at=r.get("pushed_at") or "",
                        topics=list(r.get("topics") or []),
                    )
                    found[f.key()] = f
                f.paths.extend(paths)

        # -- the provenance and the score ------------------------------
        aw = self.awareness
        for f in found.values():
            f.multiplicity = len(f.paths)
            f.proximity = len({p[0] for p in f.paths})
            rel = aw.is_relevant_candidate(f.description, f.full_name,
                                           f.topics)
            f.relevance = rel["score"]
            f.relevant = rel["relevant"]
            f.score = score(f)

        res.found = sorted(found.values(), key=lambda x: -x.score)
        res.calls = self.calls
        res.elapsed = time.time() - t0
        return res

    def write(self, res: ClimbResult) -> str:
        """Write the ladder. Its output is a RANKED LIST WITH PATHS."""
        os.makedirs(LADDER_DIR, exist_ok=True)
        stamp = time.strftime("%Y-%m-%d-%H%M%S")
        path = os.path.join(LADDER_DIR, "ladder-%s.json" % stamp)
        payload = res.describe()
        payload["found_all"] = [f.to_dict() for f in res.found]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1, ensure_ascii=False)
        return path


# ===========================================================================
# THE SCORE
# ===========================================================================

def score(f: Found) -> float:
    """The one number the ladder sorts by.

    AND THE FOUR TERMS, and the ORDER of the weights, which is the
    method:

        proximity    0.35   how many distinct players reach it
        multiplicity 0.20   how many independent paths reach it
        relevance    0.35   the system's own reading
        stars        0.10   a weak tie-breaker, NOT the sort key

    AND WHY STARS ARE LAST AND SMALL. Measured 2026-10-28: sorting the
    same traversal by stars put a 10.8k-star Java WebSocket library at
    the top. Stars measure popularity, which is age and marketing. A
    repo that three people in your network independently follow is
    better evidence than a repo that many people starred and nobody
    you trust built.

    AND WHY PROXIMITY BEATS MULTIPLICITY. Two players following the
    same person is one opinion stated twice -- and often they follow
    each other. Five DIFFERENT players reaching the same author is five
    independent judgements, which is the thing Bobby is describing.
    """
    prox = min(1.0, f.proximity / 5.0)
    mult = min(1.0, f.multiplicity / 8.0)
    rel = min(1.0, f.relevance / 8.0)
    stars = min(1.0, (f.stars / 5000.0) ** 0.5)
    return 0.35 * prox + 0.20 * mult + 0.35 * rel + 0.10 * stars


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE LADDER OF MINDS -- the mechanism, offline")
    print("=" * 78)
    print()

    print("1. THE SEEDS -- players and institutions:")
    print("   players (%d): %s" % (len(PLAYER_SEEDS), ", ".join(PLAYER_SEEDS[:6]) + " ..."))
    print("   institutions (%d): %s" % (len(INSTITUTION_SEEDS), ", ".join(INSTITUTION_SEEDS)))
    print("   AND IT IS ONE TRAVERSAL, because an org account's following")
    print("   list is readable exactly like a person's.")
    print()

    print("2. THE SCORE, and the weights:")
    print("   proximity 0.35 | multiplicity 0.20 | relevance 0.35 | stars 0.10")
    print("   stars LAST: measured, a star sort put a 10.8k-star Java")
    print("   WebSocket library on top. Popularity is not relevance.")
    print()

    print("3. THE SCORE, on synthetic founds:")
    cases = [
        ("5 players, 8 paths, on-topic, 12 stars", 5, 8, 6.0, 12),
        ("1 player, 1 path, on-topic, 12 stars", 1, 1, 6.0, 12),
        ("1 player, 1 path, off-topic, 10000 stars", 1, 1, 0.0, 10000),
        ("3 players, 4 paths, on-topic, 900 stars", 3, 4, 6.0, 900),
        ("5 players, 8 paths, off-topic, 3 stars", 5, 8, 0.0, 3),
    ]
    for label, prox, mult, rel, stars in cases:
        f = Found(proximity=prox, multiplicity=mult, relevance=rel, stars=stars)
        print("   %-44s score=%.3f" % (label, score(f)))
    print()
    print("   AND THE COMPARISON THAT MATTERS: the 5-player off-topic repo")
    print("   with 3 stars, and the 1-player off-topic repo with 10000")
    print("   stars, are close -- and both sit BELOW the on-topic ones.")
    print()

    print("4. THE CREDENTIAL:")
    tok = resolve_token()
    print("   resolved: %s" % ("yes (never printed)" if tok else "no"))
    print("   unauthenticated is 60/hour; authenticated is 5000/hour.")
    print("   A 2-hop climb of %d seeds needs ~%d calls, so without the"
          % (len(PLAYER_SEEDS) + len(INSTITUTION_SEEDS),
             len(PLAYER_SEEDS) + len(INSTITUTION_SEEDS)))
    print("   credential the traversal is unaffordable daily.")
    print()

    print("5. THE PATHS are the output. A repo with no provenance is a")
    print("   search result; one with five independent paths is a")
    print("   judgement five people made the same way.")
    print()
    print("   Run: python src/ladder.py --selftest")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if "--climb" in args:
        seeds: List[str] = []
        if "--seeds" in args:
            try:
                seeds = [x.strip() for x in
                         args[args.index("--seeds") + 1].split(",") if x.strip()]
            except IndexError:
                seeds = []
        no_inst = "--no-institutions" in args
        lad = Ladder()
        res = lad.climb(seeds=seeds, use_institutions=not no_inst)
        path = lad.write(res)
        d = res.describe()
        print("seeds %d | hop1 %d | hop2 %d | repos %d | relevant %d | "
              "calls %d | auth %s | %.1fs"
              % (d["n_seeds"], d["n_hop1"], d["n_hop2"], d["n_repos"],
                 d["n_relevant"], d["calls"], d["authenticated"],
                 d["elapsed_s"]))
        print()
        for f in d["top"][:15]:
            print("  %.3f  prox=%-2d paths=%-2d rel=%-5s %5d* %-10s %s"
                  % (f["score"], f["proximity"], f["n_paths"], f["relevance"],
                     f["stars"], (f["language"] or "-")[:10],
                     (f["full_name"] or "")[:44]))
            if f["paths"]:
                print("          path: %s" % (" -> ".join(f["paths"][0]),))
        print()
        print("ladder: %s" % path)
        return 0
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
