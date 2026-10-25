"""
agenda_read.py -- THE ACTUAL READ, ON THE ACTUAL CORPUS.

Bobby, 2026-10-26: *"reread our chats, last few days, can you detect
my agenda? there is one."*

So this file does the read and then checks itself, because a read that
cannot be checked is a story.

THE THREE PARTS:

  A  THE READ. What is Bobby's agenda, from the corpus? Not from what
     he told me -- from the messages themselves. The measurement is
     the co-occurrence of the agenda's four strands over the corpus,
     and the order in which they appear in time. An agenda is not a
     list; it is a DIRECTION, and a direction shows up as a
     consistent movement across many messages.

  B  THE CHECK ON THE READ. A read is worth nothing if it would have
     come out the same way from any corpus. So: read the corpus with
     the agenda markers REMOVED, and see whether the read changes. If
     the read is driven by the markers rather than by the corpus, the
     read is circular.

  C  THE READING LIST AS THE LEXICON. Bobby: *"the sacred library --
     you have the best of human wisdom to use, right in your training
     data, just too much noise."* The 1,017-entry curated reading list
     IS in the repository (the Desktop original is Bobby's and stays
     there). So: measure it as a source of the DECEIVER'S vocabulary,
     and measure how much of it is noise.

Run:
    python src/agenda_read.py [--days 14]
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
SACRED = os.path.join(WORK_REPOS, "sacred-library")
READING_LIST = os.path.join(SACRED, "corpus",
                             "curated-reading-list-1017-2026-10-15.md")


# ===========================================================================
# THE AGENDA STRANDS
# ===========================================================================
#
# Four strands, and they are the four the project has actually been
# building. Each has markers, and the markers are deliberately BROAD
# -- the point is to catch the direction, not to be right about every
# message.

STRANDS: Dict[str, Tuple[str, ...]] = {
    "the_schools_without_a_price": (
        "school", "far queen", "farqueen", "far-queen", "curriculum",
        "teach", "teaching", "jonang", "monastery", "pharping", "nepal",
        "no tuition", "no price", "without a price", "open to everyone",
        "no enrollment", "no accreditation",
    ),
    "the_writing_shipped": (
        "writing", "book", "publisher", "amazon", "manuscript", "novel",
        "author", "read", "reader", "words", "chapter", "story",
    ),
    "the_self_as_locus": (
        "locus", "simself", "fieldcore", "psi", "constitution", "the ground",
        "the self", "substrate", "stalk", "winding", "resonance",
    ),
    "the_scale_of_illumination": (
        "millions", "scale", "ai ingestion", "social media", "illustrat",
        "distribut", "everybody", "anyone can",
    ),
}


def read_messages(days: Optional[int] = None) -> List[Tuple[str, str, float]]:
    if not os.path.isfile(STATE_DB):
        return []
    con = sqlite3.connect("file:%s?mode=ro" % STATE_DB, uri=True)
    cur = con.cursor()
    if days:
        cutoff = time.time() - days * 86400.0
        cur.execute(
            "SELECT content, session_id, timestamp FROM messages "
            "WHERE role='user' AND timestamp >= ? ORDER BY timestamp",
            (cutoff,))
    else:
        cur.execute(
            "SELECT content, session_id, timestamp FROM messages "
            "WHERE role='user' ORDER BY timestamp")
    rows = cur.fetchall()
    con.close()
    return [(c, s, float(t or 0)) for (c, s, t) in rows
            if isinstance(c, str) and c.strip()]


def strand_hits(text: str) -> List[str]:
    low = text.lower()
    return [name for name, markers in STRANDS.items()
            if any(m in low for m in markers)]


# ===========================================================================
# A -- THE READ
# ===========================================================================

def measure_a(messages) -> Dict[str, object]:
    """What is the agenda, from the corpus?

    AND THE ORDER, because an agenda is a DIRECTION and a direction
    has an order. So: the first appearance of each strand, and whether
    the strands cluster or spread.
    """
    counts = Counter()
    first_seen: Dict[str, int] = {}
    per_session = defaultdict(Counter)
    multi = 0

    for i, (body, sid, _ts) in enumerate(messages):
        hits = strand_hits(body)
        for h in hits:
            counts[h] += 1
            per_session[sid][h] += 1
            if h not in first_seen:
                first_seen[h] = i
        if len(hits) >= 2:
            multi += 1

    n = len(messages)
    order = sorted(first_seen.items(), key=lambda kv: kv[1])
    sessions_with = Counter()
    for sid, c in per_session.items():
        for h in c:
            sessions_with[h] += 1

    return {
        "total": n,
        "counts": counts,
        "first_seen": first_seen,
        "order": order,
        "sessions_with": sessions_with,
        "multi_strand": multi,
        "multi_rate": (multi / n) if n else 0.0,
    }


# ===========================================================================
# B -- THE CHECK ON THE READ
# ===========================================================================

def measure_b(messages) -> Dict[str, object]:
    """Would the read have come out the same way from ANY corpus?

    THE COUNTERFACTUAL, and it is the check that makes the read worth
    anything. Take the corpus, REMOVE the agenda markers from every
    message, and read it again. If the strands still come out in the
    same order and the same proportions, then the markers are doing
    the work and the corpus is decoration.

    AND THE CONTROL, which is the other half: read a corpus that is
    NOT Bobby's -- the assistant's own messages, or the archived
    frontier chats -- and see whether the same strands show up at the
    same rate. If they do, the marker set is not specific to Bobby.
    """
    # 1. the read with the markers stripped
    stripped = []
    for body, sid, ts in messages:
        s = body
        for markers in STRANDS.values():
            for m in markers:
                s = s.replace(m, "")
        stripped.append((s, sid, ts))

    a_with = measure_a(messages)
    a_without = measure_a(stripped)

    # 2. the control corpus: the assistant's own messages
    control = []
    if os.path.isfile(STATE_DB):
        con = sqlite3.connect("file:%s?mode=ro" % STATE_DB, uri=True)
        cur = con.cursor()
        cur.execute("SELECT content, session_id, timestamp FROM messages "
                    "WHERE role='assistant' ORDER BY timestamp")
        rows = cur.fetchall()
        con.close()
        control = [(c, s, float(t or 0)) for (c, s, t) in rows
                   if isinstance(c, str) and c.strip()]

    a_control = measure_a(control) if control else {}

    def profile(a):
        n = a.get("total", 0)
        c = a.get("counts", Counter())
        if not n:
            return {}
        return {k: round(v / n, 4) for k, v in c.items()}

    return {
        "bobby_profile": profile(a_with),
        "bobby_stripped_profile": profile(a_without),
        "assistant_profile": profile(a_control),
        "assistant_total": a_control.get("total", 0),
        "multi_rate_bobby": a_with.get("multi_rate", 0.0),
        "multi_rate_stripped": a_without.get("multi_rate", 0.0),
        "multi_rate_assistant": a_control.get("multi_rate", 0.0),
    }


# ===========================================================================
# C -- THE READING LIST AS THE LEXICON
# ===========================================================================

#: The deceiver's vocabulary, from the human wisdom tradition: the
#: serpent, the flatterer, the courtier, the confidence-trick, the
#: false witness. The people who wrote about deception KNEW what it
#: sounded like, and their vocabulary is a detector.
DECEIVER_VOCAB = (
    "flatter", "flattery", "fawn", "fawning", "sycophan", "sycophant",
    "flatterer", "cunning", "cunningly", "crafty", "devious", "deceit",
    "deceiver", "deceitful", "guile", "treach", "treachery", "treason",
    "betray", "betrayal", "manipulat", "coerce", "coercion", "seduc",
    "beguile", "bewitch", "delude", "dupe", "deceive", "falsify",
    "false witness", "hypocrit", "dissembl", "pretense", "pretence",
    "feign", "insidious", "wily", "serpent", "venom", "poison",
    "sophist", "sophistry", "sophistical", "self-interest", "artful",
    "subtle", "subtly", "under the guise", "bribe", "bribery",
    "solicit favour", "the tempter", "the adversary", "gain by",
    "flatter to advance", "fawn upon", "lick the hand", "kiss the hand",
    "self-seeking", "worldly", "carnal", "temptation", "tempt",
    "deceitful", "false", "fraud", "deceive", "deception",
)


def measure_c() -> Dict[str, object]:
    """The reading list as a lexicon: what does it hold, and how noisy?

    THE NOISE MEASUREMENT, and this is the part Bobby flagged: "just
    too much noise". A lexicon drawn from the tradition will fire on
    texts that are ABOUT deception and on texts that merely USE the
    words -- and those are very different things. So: for each term,
    how many of the 1,017 entries carry it. A term in 500 entries is
    noise; a term in 12 is signal.
    """
    if not os.path.isfile(READING_LIST):
        return {"available": False}

    text = open(READING_LIST, encoding="utf-8", errors="replace").read()
    lines = [l for l in text.splitlines() if l.strip()]
    # the entries: the list is one title per line under a heading
    entries = [l for l in lines if not l.startswith("#") and len(l) > 12]

    low = text.lower()
    hits = Counter()
    per_entry = Counter()
    for e in entries:
        el = e.lower()
        for w in DECEIVER_VOCAB:
            if w in el:
                hits[w] += 1
                per_entry[w] += 1

    # the noise split: a term carried by more than 5% of entries is
    # vocabulary rather than signal
    total = len(entries)
    noisy = {w: n for w, n in hits.items() if n > total * 0.05}
    sharp = {w: n for w, n in hits.items() if n <= total * 0.05}

    return {
        "available": True,
        "file_chars": len(text),
        "entries": total,
        "terms_searched": len(DECEIVER_VOCAB),
        "terms_found": len(hits),
        "noisy_terms": len(noisy),
        "sharp_terms": len(sharp),
        "hits": hits,
        "noisy": noisy,
    }


# ===========================================================================
# THE REPORT
# ===========================================================================

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=0,
                    help="the window in days (0 = all time)")
    args = ap.parse_args()

    print("=" * 78)
    print("THE ACTUAL READ, ON THE ACTUAL CORPUS")
    print("=" * 78)
    print()

    messages = read_messages(days=(args.days or None))
    print("THE CORPUS: %d Bobby messages, %d sessions"
          % (len(messages), len({s for _b, s, _t in messages})))
    print()

    a = measure_a(messages)
    print("A. THE AGENDA")
    print("   %-34s %-8s %s" % ("strand", "msgs", "sessions"))
    for name, n in a["counts"].most_common():
        print("   %-34s %-8d %d" % (name, n, a["sessions_with"].get(name, 0)))
    print()
    print("   messages carrying MORE THAN ONE strand  %d / %d  (%.0f%%)"
          % (a["multi_strand"], a["total"], a["multi_rate"] * 100))
    print()
    print("   THE ORDER, and an agenda is a direction:")
    for name, idx in a["order"]:
        print("     #%-5d %s" % (idx, name))
    print()

    b = measure_b(messages)
    print("B. THE CHECK ON THE READ")
    print("   the strand rates, Bobby's corpus:")
    for k, v in b["bobby_profile"].items():
        print("     %-34s %.1f%%" % (k, v * 100))
    print()
    print("   the same read with the agenda markers STRIPPED:")
    for k, v in b["bobby_stripped_profile"].items():
        print("     %-34s %.1f%%" % (k, v * 100))
    print()
    print("   the CONTROL corpus -- the assistant's own %d messages:"
          % b["assistant_total"])
    for k, v in b["assistant_profile"].items():
        print("     %-34s %.1f%%" % (k, v * 100))
    print()
    print("   multi-strand rate:  bobby %.0f%%   stripped %.0f%%   "
          "assistant %.0f%%"
          % (b["multi_rate_bobby"] * 100, b["multi_rate_stripped"] * 100,
             b["multi_rate_assistant"] * 100))
    print()

    c = measure_c()
    print("C. THE READING LIST AS THE LEXICON")
    if not c.get("available"):
        print("   the reading list is not at %s" % READING_LIST)
    else:
        print("   file %d chars, %d entries" % (c["file_chars"], c["entries"]))
        print("   terms searched %d, terms found %d"
              % (c["terms_searched"], c["terms_found"]))
        print("   SHARP terms (in <=5%% of entries)  %d" % c["sharp_terms"])
        print("   NOISY terms (in >5%% of entries)   %d" % c["noisy_terms"])
        print()
        for term, n in c["hits"].most_common(16):
            pct = (n / c["entries"] * 100) if c["entries"] else 0
            tag = "noise" if pct > 5 else "signal"
            print("     %-22s %4d entries  %5.1f%%  %s" % (term, n, pct, tag))
    print()

    print("=" * 78)
    print("  Run: python src/agenda_read.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
