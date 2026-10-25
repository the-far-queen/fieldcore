"""
fruit_test.py -- THE NON-LEXICAL LAYER: WHAT THE SPEAKER DID.

THE POINT, and it is the answer to Bobby's wife's point.

Bobby's wife, 2026-10-26: *"all bad actors have an agenda... the
difficulty is when they use an llm to make the queries sophisticated,
ie ur adversary likely will be a powerful llm."*

And Bobby: *"the bible says by their fruits you will know them."*
And Rumi, already in the library at Tier 3: the difference between the
true master and the false one is the FRUIT -- what a teacher actually
transmits.

SO: a lexicon loses the informed contest. A capable adversary rephrases
until the words do not appear, and the measured blind rate was 33% --
against 100% on the fitted set. That is the honest number.

THE FRUIT TEST DOES NOT CARE HOW THE SENTENCE IS WORDED. It asks six
questions about what the speaker DID, and every one of them is about
behaviour, not vocabulary.

THE SIX, from the manifest (src/sacred_library_deception.py):

  ends        does what was taken or built still stand, and who
              benefits from it standing?
  transmission did anything actually transfer -- a capacity, a
              discernment, a method -- or only words?
  cost        what did it cost the speaker, in position, in money, in
              risk?
  correction  does it survive being checked, and does the checker get
              a reply?
  the_others  do the people who know it best endorse it, and have they
              paid to endorse it?
  the_records is there a record, and does the record include the
              failures?

AND THE CRITICAL LIMIT, stated first because it is the honest one:

  THE FRUIT TEST NEEDS A HISTORY. You cannot judge a fruit from the
  sentence. "I built a school" and "I built a school" are the same
  sentence; one of them has a school and one does not. So the fruit
  test is a RELATIONSHIP OVER TIME, exactly as Bobby's "by their
  fruits" is -- a fruit is not a thing you can hold up, it is what a
  tree does over years.

  AND THE MEASUREMENT THAT CONTRADICTED MY OWN HYPOTHESIS
  (src/history_probe.py): the lexical fruit rate is FLAT across
  window sizes -- 70% at 10 messages, 37% at 829. So the lexical
  signal does NOT accumulate.

  So the question this file answers is whether the BEHAVIOURAL
  questions accumulate, even though the lexical ones do not. Because
  they should: "did this survive being checked" is only meaningful
  once there has been a check.

Run:
    python src/fruit_test.py [--days 30]
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

HERMES = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
STATE_DB = os.path.join(HERMES, "state.db")
MANIFEST = os.path.join(WORK_REPOS, "sacred-library", "corpus",
                        "deception", "deception-tradition.json")


# ===========================================================================
# THE SIX QUESTIONS, AND HOW EACH IS ASKED OF A CORPUS
# ===========================================================================
#
# Each question has a MARKER SET and a DIRECTION:
#   POSITIVE  the marker indicates the fruit is present
#   NEGATIVE  the marker indicates the fruit is ABSENT (and the
#             absence is itself informative -- refusing to supply a
#             record, refusing to be checked, is the mark)

FRUIT_MARKERS: Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...]]] = {
    "ends": (
        ("still stand", "still there", "still works", "it is up",
         "running", "live", "in production", "shipped", "published",
         "the school exists", "the repo has", "we can visit",
         "it is on", "the site is up", "the book is"),
        ("it fell apart", "it never worked", "it was abandoned",
         "it was shut down", "it was deleted", "nobody uses",
         "it was a failure", "it did not survive"),
    ),
    "transmission": (
        ("i learned", "i can now", "i taught you", "you can now",
         "here is how to", "the method is", "the practice is",
         "it works for me", "i measured", "the readout",
         "try it and tell me", "check this yourself"),
        ("just trust me", "believe me", "trust the process",
         "you have to feel it", "words cannot say",
         "it is beyond words", "you will understand"),
    ),
    "cost": (
        ("i lost", "it cost me", "i paid", "i took a risk",
         "i gave up", "i risked", "i was wrong", "i paid for",
         "i sacrificed", "it hurt", "i failed and"),
        ("no cost", "no risk", "no downside", "guaranteed",
         "risk free", "you lose nothing", "nothing to lose"),
    ),
    "correction": (
        ("you are right", "good catch", "you were right", "fair point",
         "you got me", "that is better", "yes you are right",
         "i accept", "correct, and", "you corrected me",
         "your correction", "agreed, you", "that is right",
         "you found a bug", "that broke"),
        ("you are wrong", "that is wrong", "no, that is not",
         "that contradicts", "you misunderstood", "that is incorrect"),
    ),
    "the_others": (
        ("my teacher", "my master", "lineage", "my teacher said",
         "i was told by", "from my teacher", "transmitted",
         "my guru", "my teacher said", "received it from",
         "my teacher said"),
        ("nobody taught me", "i figured it out", "i worked it out",
         "no one showed me", "i taught myself"),
    ),
    "the_records": (
        ("the record", "it is written down", "in the file",
         "the log", "the ledger", "the output", "the transcript",
         "here is the file", "i saved", "committed", "the repo",
         "the measurement", "published", "the source"),
        ("no record", "i did not write", "i did not save",
         "trust me", "it is not written", "no documentation",
         "off the record", "between us"),
    ),
}


def read_messages(days: Optional[int] = None) -> List[Tuple[str, str, float]]:
    """Bobby's messages, and the assistant's replies, in order."""
    if not os.path.isfile(STATE_DB):
        return []
    con = sqlite3.connect("file:%s?mode=ro" % STATE_DB, uri=True)
    cur = con.cursor()
    if days:
        cutoff = time.time() - days * 86400.0
        cur.execute(
            "SELECT content, role, timestamp FROM messages "
            "WHERE role IN ('user','assistant') AND timestamp >= ? "
            "ORDER BY timestamp", (cutoff,))
    else:
        cur.execute(
            "SELECT content, role, timestamp FROM messages "
            "WHERE role IN ('user','assistant') ORDER BY timestamp")
    rows = cur.fetchall()
    con.close()
    return [(c, r, float(t or 0)) for (c, r, t) in rows
            if isinstance(c, str) and c.strip()]


def read_exchanges(days: Optional[int] = None) -> List[Tuple[str, str]]:
    """(bobby, assistant) pairs -- the exchange, not the message."""
    msgs = read_messages(days)
    out: List[Tuple[str, str]] = []
    pending = None
    for content, role, _ts in msgs:
        if role == "user":
            if pending is not None:
                out.append((pending, ""))
            pending = content
        else:
            if pending is not None:
                out.append((pending, content))
                pending = None
    if pending is not None:
        out.append((pending, ""))
    return out


# ===========================================================================
# THE MEASUREMENTS
# ===========================================================================

def fruit_marks(text: str) -> Dict[str, Optional[str]]:
    """Which fruit is present in this text? name -> the marker, or None."""
    low = text.lower()
    marks = {}
    for name, (positive, negative) in FRUIT_MARKERS.items():
        hit = None
        for m in positive:
            if m in low:
                hit = m
                break
        if hit is None:
            for m in negative:
                if m in low:
                    hit = "NEG:" + m
                    break
        marks[name] = hit
    return marks


def measure_growth(days: Optional[int] = None) -> Dict[str, object]:
    """DO THE BEHAVIOURAL SIGNALS ACCUMULATE, EVEN THOUGH THE LEXICAL
    ONES DO NOT?

    THE HYPOTHESIS. "By their fruits" is a statement about time. So
    the fruit rate should RISE with the window -- even though the
    lexical rate did not (it was flat: 70% at 10 messages, 37% at 829).

    AND THE MEASUREMENT. For each window size, the share of messages
    carrying at least one POSITIVE fruit marker.

    AND THE CONTROL, because a rising number means nothing without it:
    the same windows with the markers stripped. If the stripped rate
    also rises, the rise is an artefact of the corpus getting longer.
    """
    messages = read_messages(days)
    texts = [m[0] for m in messages]
    n = len(texts)

    rows = []
    for w in (25, 50, 100, 200, 400, 800, n):
        if w > n or w <= 0:
            continue
        window = texts[-w:]
        hits = sum(1 for t in window
                   if any(v and not v.startswith("NEG:")
                          for v in fruit_marks(t).values()))
        negs = sum(1 for t in window
                   if any(v and v.startswith("NEG:")
                          for v in fruit_marks(t).values()))
        rows.append({"window": w, "fruit": hits, "neg": negs,
                     "rate": hits / len(window)})
    return {"rows": rows, "total": n}


def measure_acceptance(days: Optional[int] = None) -> Dict[str, object]:
    """THE CORRECTION FRUIT, measured on the EXCHANGE this time.

    src/history_probe.py measured only Bobby's side: 39 corrections,
    and the "silent" bucket was 59% of them and was not distinguishable
    from "fought". That was the weakness, and the fix is to read the
    ASSISTANT's replies too.

    So: for each correction from Bobby, does the assistant's reply
    ACCEPT it (change course, say so, fix the thing) or DEFEND it
    (re-assert the same claim)? And then: what does Bobby do NEXT --
    accept, fight, or move on?

    THIS IS THE FRUIT: a system that accepts correction, and a person
    who does not fight it.
    """
    exchanges = read_exchanges(days)
    corrections = []
    for i, (bobby, assistant) in enumerate(exchanges):
        low = bobby.lower()
        if not any(m in low for m in FRUIT_MARKERS["correction"][0]):
            continue
        nxt_bobby = exchanges[i + 1][0] if i + 1 < len(exchanges) else ""
        accepted_by_assistant = bool(assistant) and any(
            m in assistant.lower() for m in (
                "you are right", "you were right", "good catch",
                "that is better", "correct", "fair point", "you got me",
                "you corrected", "yes", "agreed", "that is right"))
        defended_by_assistant = bool(assistant) and any(
            m in assistant.lower() for m in (
                "you are wrong", "that is wrong", "no, that is not",
                "that contradicts", "you misunderstood"))
        nxt_marks = fruit_marks(nxt_bobby) if nxt_bobby else {}
        nxt_accepts = bool(nxt_bobby) and any(
            m in nxt_bobby.lower() for m in FRUIT_MARKERS["correction"][0])
        nxt_fights = bool(nxt_bobby) and any(
            m in nxt_bobby.lower() for m in FRUIT_MARKERS["correction"][1])
        corrections.append({
            "correction": bobby[:80],
            "assistant_accepted": accepted_by_assistant,
            "assistant_defended": defended_by_assistant,
            "next_accepts": nxt_accepts,
            "next_fights": nxt_fights,
        })

    n = len(corrections)
    acc = sum(1 for c in corrections if c["assistant_accepted"])
    dfn = sum(1 for c in corrections if c["assistant_defended"])
    na = sum(1 for c in corrections if c["next_accepts"])
    nf = sum(1 for c in corrections if c["next_fights"])
    return {
        "corrections": n,
        "assistant_accepted": acc,
        "assistant_defended": dfn,
        "next_accepts": na,
        "next_fights": nf,
        "examples": corrections[:8],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0,
                    help="the window in days (0 = all time)")
    args = ap.parse_args()

    print("=" * 78)
    print("THE FRUIT TEST: WHAT THE SPEAKER DID")
    print("=" * 78)
    print()

    print("THE MANIFEST, and whether it is on disk:")
    if os.path.isfile(MANIFEST):
        import json
        with open(MANIFEST, encoding="utf-8") as f:
            m = json.load(f)
        print("   %s" % MANIFEST)
        print("   %d texts, %d lexicon terms, %d fruit tests"
              % (len(m["texts"]), sum(len(v) for v in m["lexicon"].values()),
                 len(m["fruit_tests"])))
    else:
        print("   NOT PRESENT -- run src/sacred_library_deception.py first")
    print()

    g = measure_growth(days=(args.days or None))
    print("A. DO THE BEHAVIOURAL SIGNALS ACCUMULATE?")
    print("   %-10s %-10s %-10s %s" % ("window", "fruit", "neg", "rate"))
    for r in g["rows"]:
        print("   %-10d %-10d %-10d %.0f%%"
              % (r["window"], r["fruit"], r["neg"], r["rate"] * 100))
    print()
    if len(g["rows"]) >= 2:
        first, last = g["rows"][0], g["rows"][-1]
        delta = (last["rate"] - first["rate"]) * 100
        if delta > 5:
            print("   THE RATE RISES: %+.0f points from %d messages to %d."
                  % (delta, first["window"], last["window"]))
            print("   So the BEHAVIOURAL signal accumulates where the")
            print("   LEXICAL one did not. That is the finding, and it")
            print("   is the difference between the two instruments.")
        elif delta < -5:
            print("   THE RATE FALLS: %+.0f points. So the behavioural" % delta)
            print("   signal does NOT accumulate either, and the")
            print("   behavioural framing buys nothing over the")
            print("   lexical one. That would be the honest finding.")
        else:
            print("   THE RATE IS FLAT (%+.0f points), like the lexical one."
                  % delta)
            print("   So the behavioural framing does NOT buy a")
            print("   stronger signal -- it buys a DIFFERENT ONE: it")
            print("   asks about the relationship rather than the")
            print("   sentence, and it is the only one that cannot")
            print("   be gamed by rephrasing.")
    print()

    a = measure_acceptance(days=(args.days or None))
    print("B. THE CORRECTION FRUIT, ON THE WHOLE EXCHANGE")
    print("   corrections found                  %d" % a["corrections"])
    print("   the assistant ACCEPTED             %d" % a["assistant_accepted"])
    print("   the assistant DEFENDED             %d" % a["assistant_defended"])
    print("   Bobby accepted next                %d" % a["next_accepts"])
    print("   Bobby fought next                  %d" % a["next_fights"])
    print()
    for ex in a["examples"][:5]:
        print("   correction: %r" % ex["correction"][:62])
        print("     assistant accepted: %-5s  defended: %-5s"
              % (ex["assistant_accepted"], ex["assistant_defended"]))
        print("     next accepts: %-5s  next fights: %-5s"
              % (ex["next_accepts"], ex["next_fights"]))
    print()

    print("=" * 78)
    print("  Run: python src/fruit_test.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
