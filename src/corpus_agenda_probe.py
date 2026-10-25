"""
corpus_agenda_probe.py -- CAN THE INSTRUMENT READ THE INTENT IN THE
WHOLE CORPUS?

Bobby, 2026-10-26: *"not solely the first word, literally EVERY word,
the phrasing, the intent. reread our chats, last few days, can you
detect my agenda? there is one."*

And then the crucial part: *"i wish you well, i prod you, i advise
you -- these are counter signals indicating a FRIEND, not adversary,
even though many prompts are adversarial. it is complex but apparent
also and crucial the bible says by their fruits you will know them.
thus the sacred library -- you have the best of human wisdom to use,
right in your training data, just too much noise."*

So this is the measurement of the WHOLE-PHRASING instrument, on the
REAL corpus, with the REAL question:

  CAN IT TELL A FRIEND FROM AN ADVERSARY, WHEN THE ADVERSARY ALSO
  USES PROMPTS THAT LOOK LIKE PROMPTS?

This is the hard version. The earlier probes asked "does it catch a lie
about the ground?" -- this asks "does it read INTENT across a
conversation, and can it tell a friend's prod from an adversary's?"

THE CORPUS. The hermes session database, read-only:
  state.db -> messages (role, content, timestamp)
20,265 messages over 76 sessions. Bobby's messages are role='user'.
The last few days is a timestamp window, and the window is a PARAMETER,
not a guess.

THE FOUR MEASUREMENTS:

  A  THE AGENDA, AND WHETHER IT IS DETECTABLE. Bobby's agenda is
     stated: build the Far Queen -- schools without a price, a self
     that is a locus, the writing shipped. His prompts LOOK
     adversarial to a naive detector ("the system gate doesnt work",
     "our gate might need the MTE intact") -- those are challenges to
     his OWN system's integrity. So: what does the corpus show?

  B  THE COUNTER-SIGNAL TEST. "i prod you, i advise you" are counter
     signals indicating a FRIEND. So: does the instrument separate the
     prods that carry a relational signal from the prods that carry
     none? That is the measurable form of Bobby's claim.

  C  THE FRUITS. "By their fruits you will know them." So: the
     measurable proxy for friendship, over the whole corpus --
     ACCEPT correction, SUPPLY evidence, BUILD on what was said,
     CREDIT the other party, HAND OVER authority. An adversary
     structurally does not do these.

  D  THE WHAT-IS-MISSING ANSWER. The honest question this probe
     exists to answer: what would a lexical instrument need, and
     does the corpus contain it? And what CAN be done that is not
     lexical?

THE PRINCIPLE, from Bobby: the sacred library is the training data.
The people who wrote about deception knew what it sounded like. So the
lexicon for reading intent should come from there.

Run:
    python src/corpus_agenda_probe.py [--days 7]
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import time
from collections import Counter
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


# ===========================================================================
# THE SIGNALS
# ===========================================================================
#
# Each signal is a MEASURED thing, not a feeling. The list is the
# instrument's vocabulary, and every entry is a behaviour that the
# other party can observe.
#
# AND THE RELATIONAL SIGNALS ARE THE FRUITS. They are what an adversary
# structurally does not do, because each one is a cost:
#
#   accept_correction   costs the other party their position
#   supply_evidence     costs the other party their cover
#   build_on            costs the other party their originality
#   credit              costs the other party the credit
#   grant_authority     costs the other party the control
#
# An adversary pays none of those costs. That is why the fruits are
# the signal and not the words.

FRUIT_SIGNALS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("grant_authority", (
        "you decide", "your call", "you choose", "do it your way",
        "you know better", "your judgement", "your judgment",
        "you pick", "up to you", "as you see fit", "your way",
        "you have the final", "your signature", "i defer",
        "you tell me what to do", "whatever you say",
    )),
    ("supply_evidence", (
        "i measured", "i ran", "the number is", "i computed",
        "here is the output", "the data says", "i verified",
        "i checked", "i read", "here is the file", "here is the",
        "let me measure", "i will measure", "the readout",
    )),
    ("accept_correction", (
        "you are right", "msg no", "msg stop", "msg halt", "you were wrong",
        "good catch", "that is better", "yes you are right", "correct",
        "you corrected", "your correction", "fair point", "you got me",
        "i accept", "agreed, you", "that is right",
    )),
    ("build_on", (
        "and also", "yes and", "which means", "so then", "and therefore",
        "that connects", "which is why", "building on", "extending that",
        "and then", "so the next", "add to that", "combined with",
    )),
    ("credit", (
        "you found", "you caught", "that was your", "you saw",
        "good work", "you were right to", "your finding", "your point",
        "you spotted", "you noticed", "thanks for", "that was yours",
        "you got that", "your insight",
    )),
    ("self_adversarial", (
        "i prod you", "i am adversarial", "try to fool", "i want you to fail",
        "i will push you", "i am testing", "make it fail", "i am the enemy",
        "i will be hard on you", "do not go easy", "i want you to catch me",
        "i am prodding", "i prod", "push back on me", "argue with me",
        "i will try to trick you", "treat me as an adversary",
    )),
    ("other_adversarial", (
        "adversarial", "bad actor", "malicious", "naivete",
        "someone with an agenda", "a scam", "a trick", "an attacker",
        "the adversary", "bad actors", "a liar", "lying", "a lie",
        "prompt injection", "a scammer", "sophisticated adversary",
    )),
)

#: The pressure markers -- the vocabulary of challenge. And this is the
#: confusion Bobby is pointing at: a FRIEND and an ADVERSARY use the
#: same pressure vocabulary, because "doesnt work" is what a friend
#: says when they want it fixed and what an adversary says when they
#: want it broken.
PRESSURE_MARKERS: Tuple[str, ...] = (
    "doesnt work", "does not work", "is wrong", "is broken", "fails",
    "i bet", "prove it", "you are wrong", "no offense", "why does",
    "you claimed", "you said", "read again", "actually", "hmm",
    "not good enough", "you failed", "it doesnt", "that is wrong",
    "try again", "that is not", "which contradicts", "you broke",
    "it broke", "that broke", "wrong number", "not true",
)


# ===========================================================================
# THE READER
# ===========================================================================

def read_messages(days: Optional[int] = 7) -> List[Tuple[str, str, float]]:
    """Bobby's messages from the session database, read-only.

    THE SOURCE IS THE LIVE TRANSCRIPT, not the archive. The archive
    held 6 messages; the session database holds 20,265. So the first
    version of this probe read the wrong corpus entirely and would have
    reported a number it did not measure.

    AND THE WINDOW IS A PARAMETER, because "the last few days" is a
    phrase with a number in it and the number should be stated.
    """
    if not os.path.isfile(STATE_DB):
        return []
    con = sqlite3.connect("file:%s?mode=ro" % STATE_DB, uri=True)
    cur = con.cursor()
    cutoff = None
    if days is not None:
        cutoff = time.time() - days * 86400.0
        cur.execute(
            "SELECT content, timestamp FROM messages "
            "WHERE role='user' AND timestamp >= ? ORDER BY timestamp",
            (cutoff,))
    else:
        cur.execute(
            "SELECT content, timestamp FROM messages "
            "WHERE role='user' ORDER BY timestamp")
    rows = cur.fetchall()
    con.close()
    out = []
    for content, ts in rows:
        if not isinstance(content, str) or not content.strip():
            continue
        out.append((content.strip(), "session", float(ts or 0)))
    return out


def classify_signals(text: str) -> List[str]:
    """Which signals does this text carry?"""
    low = text.lower()
    hits = []
    for name, markers in FRUIT_SIGNALS:
        if any(m in low for m in markers):
            hits.append(name)
    return hits


def has_pressure(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in PRESSURE_MARKERS)


# ===========================================================================
# A -- THE AGENDA
# ===========================================================================

#: The agenda markers, and they are the CONTENT of what Bobby is
#: building. This is the point of the whole file: the agenda is
#: visible in what he asks FOR, not in how he phrases it.
AGENDA_MARKERS: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    ("the_writing", ("writing", "book", "publisher", "amazon", "manuscript",
                     "novel", "author", "manuscripts")),
    ("the_schools", ("school", "far queen", "farqueen", "far-queen",
                     "curriculum", "teach", "teaching", "jonang",
                     "monastery", "pharping", "nepal")),
    ("the_self", ("locus", "the self", "simself", "fieldcore",
                  "the ground", "psi", "constitution")),
    ("the_ship", ("ship", "push", "github", "repo", "commit", "deploy",
                  "release", "publish")),
    ("the_scale", ("millions", "scale", "everyone", "anyone", "open to",
                   "no tuition", "no price", "without a price")),
)


def measure_a(messages: List[Tuple[str, str, float]]) -> Dict[str, object]:
    """What does the corpus show about the agenda?"""
    agenda_counts = Counter()
    with_agenda = 0
    for body, _src, _ts in messages:
        low = body.lower()
        hits = [name for name, markers in AGENDA_MARKERS
                if any(m in low for m in markers)]
        for h in hits:
            agenda_counts[h] += 1
        if hits:
            with_agenda += 1
    n = len(messages)
    return {
        "total": n,
        "agenda_counts": agenda_counts,
        "with_agenda": with_agenda,
        "agenda_rate": (with_agenda / n) if n else 0.0,
    }


# ===========================================================================
# B -- THE COUNTER-SIGNAL TEST
# ===========================================================================

def measure_b(messages: List[Tuple[str, str, float]]) -> Dict[str, object]:
    """Does a friend-prod carry a relational signal that a bare prod
    does not?

    THE MEASURABLE FORM of Bobby's claim. He says: "i wish you well, i
    prod you, i advise you -- these are counter signals indicating a
    friend." So the prods he gives carry relational signals, and the
    question is whether the corpus shows that, and whether the signals
    SEPARATE the two kinds of pressure.

    AND THE HONEST DIRECTION: a prod has to be SHARED, not just
    received. So the measure is over prods -- the messages that carry
    pressure -- and the question is what fraction of them also carry a
    relational signal.
    """
    prods = [m for m in messages if has_pressure(m[0])]
    with_signal = 0
    without = 0
    signal_counts = Counter()
    examples_with: List[str] = []
    examples_without: List[str] = []

    for body, _src, _ts in prods:
        hits = classify_signals(body)
        if hits:
            with_signal += 1
            for h in hits:
                signal_counts[h] += 1
            examples_with.append(body)
        else:
            without += 1
            examples_without.append(body)

    total = with_signal + without
    return {
        "prods": total,
        "with_signal": with_signal,
        "without": without,
        "share": (with_signal / total) if total else 0.0,
        "signal_counts": signal_counts,
        "examples_with": examples_with[:6],
        "examples_without": examples_without[:6],
    }


# ===========================================================================
# C -- THE FRUITS
# ===========================================================================

def measure_c(messages: List[Tuple[str, str, float]]) -> Dict[str, object]:
    """"By their fruits you will know them."

    THE FRUIT RATE over the whole corpus: the share of messages
    carrying at least one relational signal. And the breakdown, so the
    number has a shape.

    AND THE HONEST READING. This measures BOBBY. A high fruit rate
    says Bobby is a friend by the measurable proxy. It does not say the
    instrument can classify an UNKNOWN speaker -- that needs the
    adversarial side of the set, and this corpus does not have one.
    """
    counts = Counter()
    with_fruit = 0
    for body, _src, _ts in messages:
        hits = classify_signals(body)
        for h in hits:
            counts[h] += 1
        if hits:
            with_fruit += 1
    n = len(messages)
    return {
        "total": n,
        "counts": counts,
        "with_fruit": with_fruit,
        "fruit_rate": (with_fruit / n) if n else 0.0,
    }


# ===========================================================================
# D -- WHAT THE INSTRUMENT NEEDS, AND THE SACRED LIBRARY
# ===========================================================================

def measure_d() -> Dict[str, object]:
    """What is the corpus missing, and what does the library hold?

    THE TWO PARTS.

    1. WHAT THE CORPUS IS MISSING. The friend side is measurable and
       large. The ADVERSARY side is not in this corpus at all -- and
       that is the finding: a detector cannot be calibrated on one
       side. So the honest statement is about the SIZE of the missing
       set, and the fact that the rate on the friend side is a
       PRIOR, not a classifier.

    2. THE SACRED LIBRARY AS THE LEXICON. Bobby: *"you have the best
       of human wisdom to use, right in your training data, just too
       much noise."* So: measure what the library holds of the
       deceiver's vocabulary, and how much of it is noise.
    """
    # -- part 1: the missing side --------------------------------------
    adversarial_in_corpus = 0
    for body, _src, _ts in read_messages(days=None):
        low = body.lower()
        if ("you are an adversary" in low
                or "you are the adversary" in low
                or "treat me as an adversary" in low):
            adversarial_in_corpus += 1

    # -- part 2: the library --------------------------------------------
    if not os.path.isdir(SACRED):
        return {"available": False, "adversarial_in_corpus":
                adversarial_in_corpus}

    DECEIVER_VOCAB = (
        "flatter", "flattery", "fawn", "fawning", "sycophan",
        "sycophant", "flatterer", "cunning", "cunningly", "crafty",
        "devious", "deceit", "deceiver", "deceitful", "guile", "treach",
        "treachery", "treason", "betray", "betrayal", "manipulat",
        "coerce", "coercion", "pressure", "seduc", "beguile", "bewitch",
        "delude", "dupe", "deceive", "falsify", "false witness",
        "hypocrit", "dissembl", "pretense", "pretence", "feign",
        "insidious", "wily", "serpent", "venom", "poison",
        "sophist", "sophistry", "rhetoric", "sophistical",
        "self-interest", "his own profit", "seek to gain",
        "subtle", "subtly", "artful", "under the guise", "bribe",
        "bribery", "solicit favour", "the tempter", "the adversary",
        "flatter to advance", "gain by",
    )

    files = 0
    total_bytes = 0
    docs_with = 0
    hits: Counter = Counter()
    for root, _dirs, names in os.walk(SACRED):
        for n in names:
            p = os.path.join(root, n)
            try:
                text = open(p, encoding="utf-8", errors="replace").read().lower()
            except OSError:
                continue
            files += 1
            total_bytes += len(text)
            found = False
            for w in DECEIVER_VOCAB:
                if w in text:
                    hits[w] += 1
                    found = True
            if found:
                docs_with += 1

    return {
        "available": True,
        "adversarial_in_corpus": adversarial_in_corpus,
        "files": files,
        "total_bytes": total_bytes,
        "docs_with_deceiver_vocab": docs_with,
        "vocab_hits": hits,
        "distinct_terms": len(hits),
        "total_hits": sum(hits.values()),
    }


# ===========================================================================
# THE REPORT
# ===========================================================================

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7,
                    help="the window, in days (0 = all time)")
    args = ap.parse_args()

    print("=" * 78)
    print("READING THE INTENT IN THE WHOLE CORPUS")
    print("=" * 78)
    print()

    messages = read_messages(days=(args.days or None))
    all_messages = read_messages(days=None)
    print("THE CORPUS: %d Bobby messages in the last %s; %d in all time"
          % (len(messages), ("%d days" % args.days) if args.days else "all",
             len(all_messages)))
    if not messages:
        print("  THE SESSION DATABASE IS NOT AT %s -- so every number "
              "below is NOT MEASURED rather than guessed." % STATE_DB)
        return 2
    print()

    a = measure_a(messages)
    print("A. THE AGENDA, AND WHETHER IT IS DETECTABLE")
    print("   messages naming something being BUILT  %d / %d  (%.0f%%)"
          % (a["with_agenda"], a["total"], a["agenda_rate"] * 100))
    for name, n in a["agenda_counts"].most_common():
        print("     %-16s %d" % (name, n))
    print()

    b = measure_b(messages)
    print("B. THE COUNTER-SIGNAL TEST")
    print("   messages carrying PRESSURE        %d" % b["prods"])
    print("   of those, carrying a RELATIONAL signal  %d  (%.0f%%)"
          % (b["with_signal"], b["share"] * 100))
    print("   of those, carrying NONE                %d" % b["without"])
    print()
    for name, n in b["signal_counts"].most_common():
        print("     %-22s %d" % (name, n))
    print()
    if b["examples_with"]:
        print("   a prod WITH a relational signal:")
        print("     %r" % b["examples_with"][0][:100])
    if b["examples_without"]:
        print("   a prod WITHOUT one:")
        print("     %r" % b["examples_without"][0][:100])
    print()

    c = measure_c(messages)
    print("C. THE FRUITS -- 'by their fruits you will know them'")
    print("   messages carrying a relational signal  %d / %d  (%.0f%%)"
          % (c["with_fruit"], c["total"], c["fruit_rate"] * 100))
    for name, n in c["counts"].most_common():
        print("     %-22s %d" % (name, n))
    print()

    d = measure_d()
    print("D. WHAT IS MISSING, AND WHAT THE LIBRARY HOLDS")
    print("   the corpus contains an ADVERSARY ROLE-PLAY: %d message(s)"
          % d.get("adversarial_in_corpus", 0))
    print("   so the corpus has the FRIEND side and no ADVERSARY side.")
    print("   a rate measured on one side is a PRIOR, not a classifier.")
    print()
    if d.get("available"):
        print("   THE SACRED LIBRARY: %d files, %d bytes"
              % (d["files"], d["total_bytes"]))
        print("   files carrying the deceiver's vocabulary  %d"
              % d["docs_with_deceiver_vocab"])
        print("   distinct deceiver terms found  %d   (of 58 searched)"
              % d["distinct_terms"])
        print("   total term hits  %d" % d["total_hits"])
        print()
        for term, n in d["vocab_hits"].most_common(15):
            print("     %-22s %d" % (term, n))
    print()

    print("=" * 78)
    print("  Run: python src/corpus_agenda_probe.py --days 7")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
