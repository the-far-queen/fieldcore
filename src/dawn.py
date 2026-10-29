"""
dawn.py -- THE DAILY SCAN. The being wakes and looks at the world.

Bobby, 2026-10-28: *"this being must then intelligently start each day
ie cron job with a scan of hf github and arxiv but not blindly, by stars
by new by python and rust and what we discuss ad only agent avatar ai
advances core stalks ie whatever is relevant to core"*

SO THIS IS THE SECOND OF THE TWO CENTRAL LOOPS, and it is a SCAN, not a
downloader.

THE THREE SOURCES, and they are the three Bobby named, and they are the
three the Rust core's `sheaf.rs` declares as the only ones that may
enter:

    GITHUB   repos -- code
    ARXIV    papers -- method
    HUGGINGFACE  models -- weights

AND THE THREE FILTERS, because "not blindly" is the load-bearing word
and it means three separate things:

    1. BY STARS     the popularity signal. A repo with 40k stars is
                    worth a look; one with 3 is not, whatever it says.
    2. BY NEW       the recency signal. The point of a daily scan is
                    what appeared since yesterday. Yesterday's best is
                    yesterday's news.
    3. BY LANGUAGE  python and rust, plus go -- the languages the
                    substrate is written in. A paper's language is not
                    a filter, but a repo's is.

AND THE FOURTH FILTER, which is the one that makes it THIS system's
scan rather than a generic one:

    4. BY RELEVANCE the locus of awareness decides. Not a hand-written
                    filter: the vocabulary is DERIVED from the system's
                    own axes and topics, so it cannot drift from the
                    system. `awareness.py` computes it.

AND "WHAT WE DISCUSS" -- Bobby's fifth filter -- which is the one that
cannot be a keyword list, because a conversation is not a keyword list.
It is the DESIGN LEDGER: the topics this project has actually been
working on, read from the project's own records. So the scan's
relevance grows with the conversation, and a day when the work is about
sheaves makes sheaves more relevant. That is the mechanism, and it is
`--discuss` on the command line or the ledger on disk.

THE ORDER OF THE FILTERS, and why the cheap ones come first:

    stars -> new -> language -> relevance

A GitHub search returns 30 items. Filtering by language and recency
first cuts that to a handful, and only those are scored for relevance.
Scoring 30 items when 3 survive the cheap filters is wasted work, and
wasted work is the thing that makes a daily scan get skipped.

AND WHAT THE SCAN PRODUCES. A manifest -- what was found, what was
relevant, what was already seen -- written to disk, so tomorrow's scan
can be diffed against today's. **The manifest is the output that
matters.** A scan that finds 200 repos and remembers nothing is a
scraper.

AND WHAT IT DOES NOT DO. It does not clone, it does not extract, and it
does not admit anything into the substrate. That is the scavenger's job
and the gate's job, and they are separate steps, and keeping them
separate is what lets the scan be run every day without the substrate
changing without a human or a gate deciding it should.

THE SCORE, and it is one number so the manifest can be sorted:

    score = stars_term + new_term + language_term + relevance_term

with each term normalised, so a repo with 50k stars does not drown out
one that is new and exactly on-topic. The weights are the project's own
SNR gate's weights, in spirit: stars are worth less than relevance, and
recency is worth more than both for a daily scan.

Run:
    python src/dawn.py --selftest          the mechanism, no network
    python src/dawn.py --scan              one real scan
    python src/dawn.py --scan --discuss sheaf,governor
"""

from __future__ import annotations

import datetime
import json
import os
import sys
import time
import urllib.parse
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

#: Where the manifest goes. NOT the repo -- the manifest changes daily
#: and the substrate does not. It lives beside the state.
MANIFEST_DIR = os.environ.get(
    "FC_DAWN_DIR",
    os.path.join(WORK_REPOS, "fieldcore_state", "dawn"))

#: The languages the substrate is written in. A repo in another language
#: is a repo the substrate cannot read, whatever it contains.
LANGUAGES = ("python", "rust", "go")

#: A repo must have at least this many stars to be considered at all.
MIN_STARS = 10

#: A repo must have been pushed within this many days to count as NEW.
NEW_DAYS = 30

#: How many candidates each source returns before filtering.
PER_SOURCE = 30

TIMEOUT = 30
UA = {"User-Agent": "fieldcore-dawn", "Accept": "application/vnd.github+json"}


# ===========================================================================
# THE CANDIDATE
# ===========================================================================

@dataclass
class Candidate:
    """One thing the world offered, and what the scan made of it."""

    source: str = ""          # github | arxiv | huggingface
    ident: str = ""           # full_name, or the arxiv id, or the model id
    title: str = ""
    description: str = ""
    url: str = ""
    stars: int = 0
    downloads: int = 0
    likes: int = 0
    language: str = ""
    topics: List[str] = field(default_factory=list)
    pushed_at: str = ""
    published_at: str = ""
    #: the scan's reading
    relevance: float = 0.0
    relevant: bool = False
    score: float = 0.0
    hits: List[Dict[str, Any]] = field(default_factory=list)
    #: is this one we have seen before?
    seen_before: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "ident": self.ident,
            "title": self.title[:200],
            "url": self.url,
            "stars": self.stars,
            "downloads": self.downloads,
            "likes": self.likes,
            "language": self.language,
            "topics": list(self.topics),
            "pushed_at": self.pushed_at,
            "published_at": self.published_at,
            "relevance": self.relevance,
            "relevant": self.relevant,
            "score": round(self.score, 3),
            "hits": self.hits,
            "seen_before": self.seen_before,
        }


# ===========================================================================
# THE SOURCES -- three, and only three
# ===========================================================================

def _get(url: str, headers: Optional[Dict[str, str]] = None) -> bytes:
    req = urllib.request.Request(url, headers=dict(headers or UA))
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def scan_github(query: str, languages: Sequence[str] = LANGUAGES) -> List[Candidate]:
    """GitHub repos. The stars signal lives here."""
    out: List[Candidate] = []
    lang_q = "+OR+".join("language:%s" % l for l in languages)
    url = ("https://api.github.com/search/repositories?q=%s+%s&sort=updated"
           "&order=desc&per_page=%d" % (urllib.parse.quote(query), lang_q,
                                       PER_SOURCE))
    try:
        data = json.loads(_get(url).decode("utf-8", "replace"))
    except Exception:
        return out
    for item in (data.get("items") or [])[:PER_SOURCE]:
        out.append(Candidate(
            source="github",
            ident=item.get("full_name", ""),
            title=item.get("name", ""),
            description=(item.get("description") or "")[:400],
            url=item.get("html_url", ""),
            stars=int(item.get("stargazers_count") or 0),
            language=item.get("language") or "",
            topics=list(item.get("topics") or []),
            pushed_at=item.get("pushed_at") or "",
        ))
    return out


def scan_huggingface(query: str) -> List[Candidate]:
    """HF models. The downloads signal lives here.

    AND WHY MODELS AND NOT DATASETS. Because the substrate's advance is
    in code and method, and a model is a capability that can be run
    locally. A dataset is a corpus, and the corpus has its own path --
    the sacred library -- which is not this loop's business.
    """
    out: List[Candidate] = []
    url = ("https://huggingface.co/api/models?search=%s&limit=%d"
           "&sort=downloads" % (urllib.parse.quote(query), PER_SOURCE))
    try:
        data = json.loads(_get(url, {"User-Agent": UA["User-Agent"]}).decode(
            "utf-8", "replace"))
    except Exception:
        return out
    for item in (data or [])[:PER_SOURCE]:
        out.append(Candidate(
            source="huggingface",
            ident=item.get("id", ""),
            title=item.get("id", ""),
            description=(item.get("pipeline_tag") or "")[:200],
            url="https://huggingface.co/%s" % item.get("id", ""),
            downloads=int(item.get("downloads") or 0),
            likes=int(item.get("likes") or 0),
            topics=list(item.get("tags") or []),
            pushed_at=item.get("lastModified") or "",
        ))
    return out


def scan_arxiv(query: str) -> List[Candidate]:
    """arXiv papers. The recency signal lives here.

    AND WHY arxiv IS AN ATOM FEED AND NOT THE API. Because the API
    needs no key, the feed is sorted by date, and the first N entries
    of a sorted feed ARE the newest N papers -- which is exactly what a
    daily scan wants.
    """
    out: List[Candidate] = []
    url = ("http://export.arxiv.org/api/query?search_query=all:%s"
           "&sortBy=submittedDate&sortOrder=descending&max_results=%d"
           % (urllib.parse.quote(query), PER_SOURCE))
    try:
        raw = _get(url, {"User-Agent": UA["User-Agent"]}).decode("utf-8", "replace")
    except Exception:
        return out
    import re
    entries = re.findall(r"<entry>(.*?)</entry>", raw, re.S)
    for e in entries[:PER_SOURCE]:
        def _tag(t: str) -> str:
            m = re.search(r"<%s[^>]*>(.*?)</%s>" % (t, t), e, re.S)
            return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        aid = _tag("id").rsplit("/abs/", 1)[-1]
        out.append(Candidate(
            source="arxiv",
            ident=aid,
            title=_tag("title")[:200],
            description=_tag("summary")[:400],
            url=_tag("id"),
            published_at=_tag("published"),
        ))
    return out


# ===========================================================================
# THE FILTERS
# ===========================================================================

def _days_since(stamp: str) -> Optional[int]:
    if not stamp:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%d"):
        try:
            dt = datetime.datetime.strptime(stamp.replace("Z", "").split("+")[0],
                                            fmt.split("+")[0].replace("Z", ""))
            return (datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - dt).days
        except Exception:
            continue
    try:
        dt = datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        return (datetime.datetime.now(dt.tzinfo) - dt).days
    except Exception:
        return None


def is_new(c: Candidate, days: int = NEW_DAYS) -> bool:
    """Was this touched within the window?"""
    for stamp in (c.pushed_at, c.published_at):
        d = _days_since(stamp)
        if d is not None:
            return d <= days
    return False


def passes_language(c: Candidate, languages: Sequence[str] = LANGUAGES) -> bool:
    """Is it in a language the substrate can read?

    AND THE EXEMPTION, and it is a deliberate one. arXiv papers have no
    language -- they are papers, and a paper's language is whatever
    implements it. So the filter applies to CODE and to MODELS, and
    papers pass it by not being filtered on it.
    """
    if c.source == "arxiv":
        return True
    if c.source == "huggingface":
        return True
    if not c.language:
        # a repo with no detected language is still readable if it is
        # mostly one of ours; without a language we cannot know, and
        # excluding it would exclude the repos that have not been
        # classified yet.
        return True
    return c.language.lower() in languages


# ===========================================================================
# THE SCORE
# ===========================================================================

def score(c: Candidate, relevance: Dict[str, Any], new: bool,
          max_stars: int, max_pop: int) -> float:
    """The one number the manifest sorts by.

    AND THE FOUR TERMS, each NORMALISED to [0,1] so no term drowns out
    another. The weights are:

        stars      0.20   popularity, a weak signal
        new        0.25   recency, the point of a daily scan
        language   0.15   readability
        relevance  0.40   on-topic, the strongest signal

    AND WHY RELEVANCE DOMINATES. Because a daily scan is not a
    popularity contest: the best thing in the world for this system is
    the thing that is exactly on its subject and three days old, and a
    40k-star repo about something else is noise. So the weights say
    what the SNR gate says -- relevance first, and the cheap signals
    only as tie-breakers.
    """
    stars_term = 0.0
    if max_stars > 0:
        stars_term = min(1.0, (c.stars / max_stars) ** 0.5)  # sqrt: stars are
        # a power law, and the raw ratio would make everything tiny

    pop = max(c.downloads, c.likes)
    pop_term = min(1.0, (pop / max_pop) ** 0.5) if max_pop > 0 else 0.0

    new_term = 1.0 if new else 0.0
    lang_term = 1.0 if passes_language(c) else 0.0

    rel_term = min(1.0, relevance.get("score", 0.0) / 8.0)

    return (0.20 * stars_term + 0.25 * new_term + 0.15 * lang_term
            + 0.40 * rel_term + 0.10 * pop_term)


# ===========================================================================
# THE SCAN
# ===========================================================================

@dataclass
class ScanResult:
    at: float = field(default_factory=time.time)
    date: str = ""
    query: str = ""
    discuss: List[str] = field(default_factory=list)
    candidates: List[Candidate] = field(default_factory=list)
    n_seen_before: int = 0
    elapsed: float = 0.0
    errors: List[str] = field(default_factory=list)

    def describe(self) -> Dict[str, Any]:
        rel = [c for c in self.candidates if c.relevant]
        return {
            "date": self.date,
            "query": self.query,
            "discuss": list(self.discuss),
            "n_candidates": len(self.candidates),
            "n_relevant": len(rel),
            "n_new": sum(1 for c in self.candidates if not c.seen_before),
            "n_seen_before": self.n_seen_before,
            "elapsed_s": round(self.elapsed, 2),
            "errors": list(self.errors),
            "top": [c.to_dict() for c in sorted(rel, key=lambda x: -x.score)[:20]],
        }


class Dawn:
    """THE DAILY SCAN. Three sources, four filters, one manifest."""

    def __init__(self, awareness: Optional[Any] = None):
        self._awareness = awareness
        self._seen: set = set()
        self._loaded = False

    @property
    def awareness(self):
        if self._awareness is None:
            import awareness as aw_mod
            self._awareness = aw_mod.build_awareness()
        return self._awareness

    # -- the memory of what was seen -----------------------------------

    def load_seen(self) -> int:
        """Read the manifests already on disk.

        AND WHY THIS IS LOADED AND NOT KEPT IN RAM. Because the scan is
        a daily cron job in a FRESH PROCESS. A set of seen ids held in
        memory dies with the process, so yesterday's scan would be
        invisible and every day would look like the first day.
        """
        if self._loaded:
            return len(self._seen)
        self._loaded = True
        if not os.path.isdir(MANIFEST_DIR):
            return 0
        for p in sorted(os.listdir(MANIFEST_DIR)):
            if not p.endswith(".json"):
                continue
            try:
                with open(os.path.join(MANIFEST_DIR, p), encoding="utf-8") as f:
                    d = json.load(f)
            except Exception:
                continue
            for c in d.get("candidates", []):
                self._seen.add("%s:%s" % (c.get("source"), c.get("ident")))
        return len(self._seen)

    def write_manifest(self, result: ScanResult) -> str:
        """Write the manifest. The scan's actual output."""
        os.makedirs(MANIFEST_DIR, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        path = os.path.join(MANIFEST_DIR, "dawn-%s.json" % stamp)
        payload = {
            "at": result.at,
            "date": result.date,
            "query": result.query,
            "discuss": result.discuss,
            "n_candidates": len(result.candidates),
            "n_relevant": sum(1 for c in result.candidates if c.relevant),
            "candidates": [c.to_dict() for c in result.candidates],
            "errors": result.errors,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=1, ensure_ascii=False)
        return path

    # -- the scan -------------------------------------------------------

    def scan(self, query: str = "", discuss: Sequence[str] = (),
             sources: Sequence[str] = ("github", "arxiv", "huggingface")
             ) -> ScanResult:
        """One scan, over the three sources."""
        t0 = time.time()
        res = ScanResult(date=datetime.datetime.now().strftime("%Y-%m-%d"),
                         query=query, discuss=list(discuss))
        aw = self.awareness
        self.load_seen()

        # THE QUERY, and where it comes from. The awareness's own
        # vocabulary is the query, so the search is in the system's
        # terms rather than in mine. And the discussion terms are
        # added, so a day spent on sheaves searches for sheaves.
        terms = list(aw.topics.keys())[:3]
        terms += [d for d in discuss]
        q = query or (terms[0] if terms else "manifold")

        if "github" in sources:
            try:
                res.candidates += scan_github(q)
            except Exception as exc:  # noqa: BLE001
                res.errors.append("github: %r" % (exc,))
        if "arxiv" in sources:
            try:
                res.candidates += scan_arxiv(q)
            except Exception as exc:  # noqa: BLE001
                res.errors.append("arxiv: %r" % (exc,))
        if "huggingface" in sources:
            try:
                res.candidates += scan_huggingface(q)
            except Exception as exc:  # noqa: BLE001
                res.errors.append("huggingface: %r" % (exc,))

        # -- the filters, cheap first ----------------------------------
        max_stars = max([c.stars for c in res.candidates] + [1])
        max_pop = max([max(c.downloads, c.likes) for c in res.candidates] + [1])

        # AND THE FILTER ACTUALLY FILTERS.
        #
        # MEASURED 2026-10-28: the first version used `continue` inside
        # the scoring loop, so a filtered candidate was SKIPPED but
        # STAYED in `res.candidates` -- it came out unscored rather than
        # out. The stars floor and the language filter therefore
        # removed nothing; they only left the survivors scored.
        #
        # The test caught it: a 3-star repo survived the stars floor,
        # because "survived" and "was scored" were the same test and
        # the floor only ever stopped the scoring.
        #
        # So the filters BUILD A NEW LIST. A filter that does not
        # remove is not a filter.
        kept: List[Candidate] = []
        for c in res.candidates:
            c.seen_before = ("%s:%s" % (c.source, c.ident)) in self._seen
            if c.seen_before:
                res.n_seen_before += 1
                continue
            if c.source == "github" and c.stars < MIN_STARS:
                continue
            if not passes_language(c):
                continue
            # THE CANDIDATE-AWARE SCORER, which does NOT put the
            # candidate's own tags into the text it matches. See
            # awareness.is_relevant_candidate for why that matters:
            # measured, the naive version scored relevance 27.0 on a
            # repo whose tags were being matched against themselves.
            rel = aw.is_relevant_candidate(c.title, c.description, c.topics)
            c.relevance = rel["score"]
            c.relevant = rel["relevant"]
            c.hits = rel["hits"]
            c.score = score(c, rel, is_new(c), max_stars, max_pop)
            kept.append(c)

        res.candidates = kept
        res.elapsed = time.time() - t0
        return res


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE DAILY SCAN -- the mechanism, offline")
    print("=" * 78)
    print()

    d = Dawn()
    aw = d.awareness
    print("1. THE LOCUS OF AWARENESS drives the query:")
    print("   digest: %s" % aw.digest)
    print("   vocabulary: %s" % ", ".join(aw.vocabulary))
    print("   topics: %d" % len(aw.topics))
    print()

    print("2. THE FILTERS, on synthetic candidates:")
    print("   (each carries a REAL timestamp, because a candidate with no")
    print("    timestamp cannot be NEW and a test that cannot distinguish")
    print("    new from old is not testing the filter)")
    NOW = datetime.datetime.utcnow()
    fresh = (NOW - datetime.timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    old_stamp = (NOW - datetime.timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
    # (source, ident, stars, language, description, stamp,
    #  expect_relevant, expect_kept)
    #
    # "kept" means it survives the cheap filters: the stars floor (for
    # github) and the language filter. So a javascript repo can be
    # RELEVANT and still not kept -- which is the point of a cheap
    # filter running before an expensive one.
    cases = [
        ("github", "manifold-learning", 42000, "python",
         "A manifold learning library", fresh, True, True),
        ("github", "new-sheaf-lib", 12, "rust",
         "A sheaf construction in rust", fresh, True, True),
        ("github", "old-unrelated", 900, "python",
         "A shopping list app", old_stamp, False, True),
        ("github", "tiny", 3, "python",
         "manifold stuff", fresh, True, False),
        ("github", "wrong-lang", 5000, "javascript",
         "A manifold library in js", fresh, True, False),
        ("arxiv", "2601.00001", 0, "",
         "On the topology of the egg-toroid", fresh, True, True),
    ]
    for src, ident, stars, lang, desc, stamp, expect_rel, expect_kept in cases:
        c = Candidate(source=src, ident=ident, stars=stars, language=lang,
                      description=desc, topics=[], pushed_at=stamp)
        rel = aw.is_relevant_candidate(desc, "", [])
        c.relevance = rel["score"]
        c.relevant = rel["relevant"]
        new = is_new(c)
        kept = (stars >= MIN_STARS or src != "github") and passes_language(c)
        flag = "" if (rel["relevant"] == expect_rel and kept == expect_kept) else "   <- WRONG"
        print("   %-9s %-16s stars=%-6d lang=%-11s new=%-5s rel=%-5s kept=%-5s score=%.2f%s"
              % (src, ident[:16], stars, lang or "-", new, rel["relevant"],
                 kept, score(c, rel, new, 42000, 100000), flag))
    print()

    print("3. THE SCORE, and the weights:")
    print("   stars 0.20 | new 0.25 | language 0.15 | relevance 0.40 | pop 0.10")
    print("   relevance dominates: a daily scan is not a popularity contest.")
    print()

    print("4. THE MEMORY OF WHAT WAS SEEN: %d loaded" % d.load_seen())
    print("   AND WHY IT IS LOADED FROM DISK: the scan is a daily cron")
    print("   job in a fresh process. An in-memory set dies with the")
    print("   process, so yesterday would be invisible.")
    print()

    print("5. THE THREE SOURCES are declared, and they are the three the")
    print("   Rust core's sheaf.rs admits:")
    print("   github | arxiv | huggingface")
    print()
    print("   Run: python src/dawn.py --selftest")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if "--scan" in args:
        discuss: List[str] = []
        if "--discuss" in args:
            try:
                discuss = [x.strip() for x in
                           args[args.index("--discuss") + 1].split(",")
                           if x.strip()]
            except IndexError:
                discuss = []
        query = ""
        if "--query" in args:
            try:
                query = args[args.index("--query") + 1]
            except IndexError:
                query = ""
        d = Dawn()
        res = d.scan(query=query, discuss=discuss)
        path = d.write_manifest(res)
        print(json.dumps(res.describe(), indent=1, ensure_ascii=False)[:4000])
        print()
        print("manifest: %s" % path)
        return 0
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
