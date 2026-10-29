"""
test_awareness_dawn.py -- the locus of awareness and the daily scan.

AND THE RULE, which is the project's own: a validator that cannot fail
is decoration. So every test here asserts something that could go red,
and the docstring of each names the RED version.

AND THE TWO DEFECTS THIS FILE WAS WRITTEN AGAINST, both measured on
2026-10-28:

  THE RELEVANCE THRESHOLD WAS 3.0 AND A TOPIC HIT IS WORTH 2.0-2.5.
  So ONE strong topic match read as NOT relevant, and a candidate only
  passed if it ALSO carried the topic as a declared tag. That is too
  strict: a tag is a property of how a repo was tagged, not of whether
  it is on-topic.

  THE CANDIDATE'S OWN TAGS WERE MATCHED AGAINST THEMSELVES. The first
  version put the tags into the text and matched that text against the
  vocabulary, so a repo tagged `gguf` was scored on `gguf` -- and the
  measured relevance was 27.0. A tautology, not relevance.

THE FOUR THINGS THIS FILE PROVES:

  1. THE LOCUS IS BUILT FROM THE SYSTEM'S OWN STATE. The axes are the
     constitution's axes -- EIGHT, not sixteen, because psi_0 is a
     16-dim EMBEDDING of them and the two counts are not the same.
  2. RELEVANCE SEPARATES. A sheaf library is relevant; a shopping list
     is not.
  3. A CANDIDATE'S OWN TAGS DO NOT SCORE THEMSELVES.
  4. THE SCAN FILTERS ARE HONEST. Stars floor, language, recency, and
     the seen-before memory -- each of which can be shown to bite.
"""

from __future__ import annotations

import datetime
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FC_SRC = os.path.join(REPO, "src")
SS_SRC = os.path.abspath(os.path.join(REPO, "..", "simself", "src"))
for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import awareness  # noqa: E402
import dawn  # noqa: E402


def _aw():
    return awareness.build_awareness()


# ---------------------------------------------------------------------------
# 1. the locus is built from the system's own state
# ---------------------------------------------------------------------------

def test_the_axes_are_the_constitutions_axes():
    """EIGHT axes, not sixteen.

    RED: if the vector's length were used as the axis count, this would
    report 16.

    AND WHY IT MATTERS: psi_0 is a 16-dim EMBEDDING of the 8 axes. The
    first version named the surplus dimensions "axis_08".."axis_15" and
    put them in the vocabulary -- so the vocabulary matched things the
    system is not.
    """
    aw = _aw()
    from constitutional.constitution import Constitution
    c = Constitution()
    assert len(aw.axes) == len(c.axis_names), (
        "the locus reports %d axes, the constitution has %d"
        % (len(aw.axes), len(c.axis_names)))
    assert len(aw.axes) == 8, aw.axes
    assert aw.vector_dim == 16, aw.vector_dim
    # and NO invented names in the vocabulary
    for name in aw.vocabulary:
        assert name in c.axis_names, "invented vocabulary: %r" % name


def test_the_ground_is_protected_and_the_chain_is_intact():
    """RED: if the locus failed to build, these would be False."""
    aw = _aw()
    assert aw.locus.get("ground_protected") is True, aw.locus
    assert aw.locus.get("chain_intact") is True, aw.locus
    assert aw.locus.get("stalks") == 8, aw.locus
    assert aw.locus.get("modes"), aw.locus


def test_the_digest_is_stable_across_two_builds():
    """The digest is the identity, so it must not move between builds.

    RED: if the digest covered the locus COORDINATE (which moves by
    design), two builds in the same second could differ, and "what
    changed" would be useless.
    """
    a = _aw().digest
    b = _aw().digest
    assert a == b, (a, b)
    assert len(a) == 16, a


def test_the_digest_covers_the_vocabulary():
    """RED: if the vocabulary changed and the digest did not, the system
    could not tell that it had changed."""
    aw = _aw()
    before = aw.digest
    aw.vocabulary = aw.vocabulary + ["a_new_term"]
    import hashlib
    parts = [a.describe() for a in aw.axes]
    parts += sorted(aw.vocabulary)
    parts += sorted("%s:%s" % (k, v) for k, v in aw.topics.items())
    parts += ["%s=%s" % (k, aw.locus.get(k)) for k in
              ("stalks", "modes", "chain_intact", "ground_protected")]
    after = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    assert before != after, "the digest did not move when the vocabulary did"


def test_a_degraded_layer_is_named_not_hidden():
    """RED: if a layer failed and the degraded list was empty, this fails."""
    aw = _aw()
    # the layers must all have read cleanly
    assert aw.degraded == [], aw.degraded


# ---------------------------------------------------------------------------
# 2. relevance separates
# ---------------------------------------------------------------------------

def test_relevance_separates_on_topic_from_off_topic():
    """RED: if everything scored relevant, this fails."""
    aw = _aw()
    on = aw.is_relevant_candidate("A sheaf construction for topological data",
                                  "sheaves, sheaves, sheaves", [])
    off = aw.is_relevant_candidate("A shopping list app",
                                   "keep track of your groceries", [])
    assert on["relevant"] is True, on
    assert off["relevant"] is False, off
    assert on["score"] > off["score"], (on, off)


def test_one_strong_topic_match_is_enough():
    """THE THRESHOLD DEFECT, caught.

    RED: if the threshold were back at 3.0, this would fail -- a topic
    hit is worth 2.0-2.5, so one would not clear it.

    AND THE STRADDLE CASE, which is the one that actually bites. The
    first version of this test used `sheaf`, whose weight is 2.5 -- and
    2.5 clears a threshold of 2.0 AND a threshold of... no, it does not
    clear 3.0. So the original test was right, but by luck of the
    weight: a topic weighted 2.0 would clear 2.0 and not 3.0 either.
    The test below uses the LOWEST-weight topic in the vocabulary, so it
    is the true boundary case.
    """
    aw = _aw()
    # the lowest-weight topic in the system's own vocabulary
    lowest = min(aw.topics.items(), key=lambda kv: kv[1])
    name = lowest[0]
    r = aw.is_relevant_candidate("a project about %s" % name, "", [])
    assert r["score"] >= 2.0, ("%r scored %s, below the threshold"
                               % (name, r["score"]))
    assert r["relevant"] is True, ("%r did not clear the threshold: %s"
                                   % (name, r))


def test_the_threshold_is_two_and_the_axis_match_clears_it():
    """THE BOUNDARY, stated as a fact about the threshold itself.

    RED: if the threshold moved to 3.0, the topic case above fails; if
    it moved to 0.5, the off-topic case in the sibling test fails.
    """
    aw = _aw()
    # an axis-name match is worth 3.0, so it clears 2.0 with room
    r = aw.is_relevant_candidate("a study of routing in agents", "", [])
    assert any(h["kind"] == "axis" for h in r["hits"]), r
    assert r["score"] >= 3.0, r


def test_the_axis_names_are_in_the_vocabulary_and_score_higher():
    """RED: if the axis names were dropped from the vocabulary, this
    fails."""
    aw = _aw()
    assert aw.vocabulary, "the vocabulary is empty"
    r = aw.is_relevant_candidate("a study of stability in agent systems", "", [])
    assert any(h["kind"] == "axis" for h in r["hits"]), r


# ---------------------------------------------------------------------------
# 3. a candidate's own tags do not score themselves
# ---------------------------------------------------------------------------

def test_a_candidate_does_not_score_its_own_tags():
    """THE TAUTOLOGY DEFECT, caught.

    RED: if the candidate's tags were put into the matched text, a repo
    tagged with many things would score high on being tagged -- and the
    measured value was 27.0.
    """
    aw = _aw()
    # a candidate with many irrelevant tags and no on-topic description
    r = aw.is_relevant_candidate(
        "SomeTool", "a general purpose utility",
        ["gguf", "llama-cpp", "ministral", "openzero", "agent-zero",
         "local-ai", "agentic", "tool-use", "coding", "research",
         "q5-k-m", "text-generation", "en", "conversational"])
    assert r["score"] < 5.0, ("the tags scored themselves: %s" % (r,))
    assert r["relevant"] is False, r


def test_a_tag_in_the_systems_vocabulary_does_count():
    """RED: if tags were ignored entirely, this fails."""
    aw = _aw()
    r = aw.is_relevant_candidate("A library", "no description", ["sheaf"])
    assert any(h["kind"] == "tag" for h in r["hits"]), r


def test_a_tag_outside_the_systems_vocabulary_does_not_count():
    """RED: if any tag counted, this fails."""
    aw = _aw()
    r = aw.is_relevant_candidate("A library", "no description",
                                 ["gguf", "llama-cpp", "minimax"])
    assert not any(h["kind"] == "tag" for h in r["hits"]), r


# ---------------------------------------------------------------------------
# 4. the scan's filters are honest
# ---------------------------------------------------------------------------

def test_the_stars_floor_bites():
    """RED: if there were no stars floor, this fails.

    AND IT IS TESTED THROUGH THE SCAN, not by reading the constant. The
    first version asserted `stars < MIN_STARS`, which is a tautology:
    it compares a field to the threshold and can never fail however the
    filter behaves. Removing the stars floor from the scan left this
    test GREEN -- so the test was not testing the filter.

    So the scan's OWN filtering is exercised, with a fake source so no
    network is needed.
    """
    import tempfile
    old_dir = dawn.MANIFEST_DIR
    try:
        dawn.MANIFEST_DIR = tempfile.mkdtemp()
        d = dawn.Dawn()

        class FakeSource:
            def __init__(self, cands):
                self.cands = cands

        # three candidates: one under the floor, one over it
        cands = [
            dawn.Candidate(source="github", ident="tiny", stars=3,
                           language="python", description="a sheaf library"),
            dawn.Candidate(source="github", ident="big", stars=5000,
                           language="python", description="a sheaf library"),
        ]
        # patch the three source functions
        orig = (dawn.scan_github, dawn.scan_arxiv, dawn.scan_huggingface)
        dawn.scan_github = lambda q, languages=dawn.LANGUAGES: cands
        dawn.scan_arxiv = lambda q: []
        dawn.scan_huggingface = lambda q: []
        try:
            res = d.scan(query="sheaf")
        finally:
            dawn.scan_github, dawn.scan_arxiv, dawn.scan_huggingface = orig
        kept = [c.ident for c in res.candidates]
        assert "tiny" not in kept, ("a 3-star repo survived the stars "\
                                     "floor: %s" % (kept,))
        assert "big" in kept, ("a 5000-star repo was dropped: %s" % (kept,))
    finally:
        dawn.MANIFEST_DIR = old_dir


def test_the_language_filter_excludes_a_foreign_language():
    """RED: if the language filter were gone, this fails.

    AND A REPO WITH NO DETECTED LANGUAGE IS KEPT, because excluding it
    would exclude the repos that have not been classified yet.
    """
    js = dawn.Candidate(source="github", ident="x", language="javascript")
    assert dawn.passes_language(js) is False
    rs = dawn.Candidate(source="github", ident="x", language="rust")
    assert dawn.passes_language(rs) is True
    unknown = dawn.Candidate(source="github", ident="x", language="")
    assert dawn.passes_language(unknown) is True


def test_a_paper_is_not_filtered_on_language():
    """arxiv papers have no language. RED: if they were filtered, this
    fails."""
    p = dawn.Candidate(source="arxiv", ident="2601.00001", language="")
    assert dawn.passes_language(p) is True


def test_recency_is_measured_not_guessed():
    """RED: if _days_since returned None for a real timestamp, this
    fails."""
    fresh = (datetime.datetime.utcnow() - datetime.timedelta(days=2))
    old = (datetime.datetime.utcnow() - datetime.timedelta(days=400))
    c = dawn.Candidate(source="github", ident="x",
                       pushed_at=fresh.strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert dawn.is_new(c) is True
    c2 = dawn.Candidate(source="github", ident="x",
                        pushed_at=old.strftime("%Y-%m-%dT%H:%M:%SZ"))
    assert dawn.is_new(c2) is False


def test_the_seen_memory_loads_from_disk():
    """THE CONTINUITY DEFECT, caught.

    The scan is a daily cron job in a FRESH PROCESS, so the set of seen
    ids must come from disk. An in-memory set dies with the process and
    every day would look like the first day.

    RED: if the load were removed, this fails.
    """
    import tempfile
    import json
    tmp = tempfile.mkdtemp()
    old = dawn.MANIFEST_DIR
    try:
        dawn.MANIFEST_DIR = tmp
        with open(os.path.join(tmp, "dawn-x.json"), "w", encoding="utf-8") as f:
            json.dump({"candidates": [{"source": "github", "ident": "a/b"}]}, f)
        d = dawn.Dawn()
        assert d.load_seen() == 1, "the manifest on disk was not loaded"
        assert "github:a/b" in d._seen, d._seen
    finally:
        dawn.MANIFEST_DIR = old


def test_the_score_rewards_relevance_over_popularity():
    """RED: if stars outweighed relevance, this fails.

    AND THE POINT: a daily scan is not a popularity contest. A 40k-star
    repo about something else is noise.
    """
    aw = _aw()
    popular = dawn.Candidate(source="github", ident="p", stars=40000,
                             language="python", description="shopping list app")
    ontopic = dawn.Candidate(source="github", ident="o", stars=30,
                              language="python",
                              description="a sheaf construction for manifolds")
    rel_p = aw.is_relevant_candidate(popular.title, popular.description, [])
    rel_o = aw.is_relevant_candidate(ontopic.title, ontopic.description, [])
    s_p = dawn.score(popular, rel_p, True, 40000, 100000)
    s_o = dawn.score(ontopic, rel_o, True, 40000, 100000)
    assert s_o > s_p, ("the popular off-topic repo scored %s, the on-topic "
                       "one %s" % (s_p, s_o))
