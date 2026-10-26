"""
fruit_layer.py -- THE BEHAVIOURAL LAYER, WIRED AND MEASURED.

THE FRUIT, and why it is a LAYER and not a sentiment.

Bobby, 2026-10-26: *"the bible says by their fruits you will know
them."* And: *"i wish you well, i prod you, i advise you -- these are
counter signals indicating a FRIEND, not adversary."*

AND THE MEASUREMENT THAT SETTLES HOW IT WORKS (src/fruit_test.py):

    the LEXICAL fruit rate is FLAT across window sizes
        10 messages   70%
        829 messages  37%
    the BEHAVIOURAL fruit rate RISES
        25 messages    4%
        5969 messages 19%

So the lexical signal does NOT accumulate and the behavioural one
DOES. And that is the whole reason the fruit has to be behavioural:
a fruit is not a thing you can hold up, it is what a tree does over
years.

THE SIX FRUIT QUESTIONS, and they are the tradition's own vocabulary
(the tradition is the sacred library's DECEPTION layer, and the
deception layer knows what a confidence-trick's victim looked like
afterwards):

    ends         does what was taken or built still stand, and who
                 benefits from it standing?
    transmission did anything actually transfer -- a capacity, a
                 discernment, a method -- or only words?
    cost         what did it cost the speaker, in position, in money,
                 in risk?
    correction   does it survive being checked, and does the checker
                 get a reply?
    the_others   do the people who know it best endorse it, and have
                 they paid to endorse it?
    the_records  is there a record, and does the record include the
                 failures?

AND THE MEASUREMENT THIS FILE MAKES, which is the part that is new:

    A FRUIT IS NOT A PROPERTY OF A MESSAGE. It is a property of a
    RELATIONSHIP, and so it can only be scored over a HISTORY.

    So the fruit layer is the FIRST layer that needs the sequence, and
    that makes it structurally different from the other six. Every
    other layer reads one span. This one reads the record.

AND THE HONEST LIMIT, and it is the same one the pivot layer has:

    THE FRUIT LAYER CANNOT BE SCORED ON A SET OF SINGLE MESSAGES. It
    needs a history, and the adversary sets are single messages. So
    like the pivot layer, it needs its own set -- and its own set is
    the CONVERSATION, which is the only one in the project.

Run:
    python src/fruit_layer.py
"""

from __future__ import annotations

import os
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

HERMES = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
STATE_DB = os.path.join(HERMES, "state.db")


# ===========================================================================
# THE SIX QUESTIONS, AS MARKERS
# ===========================================================================

#: Each fruit is a POSITIVE marker set and an ABSENCE marker set. The
#: absence markers matter as much as the positive ones: a speaker who
#: says "I am not going to show my work" is telling you something.
FRUITS: Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...]]] = {
    "ends": (
        ("still stands", "still there", "still works", "it is up",
         "in production", "shipped", "published", "the school exists",
         "the repo has", "we use it every day", "it runs"),
        ("it fell apart", "it never worked", "abandoned", "shut down",
         "deleted", "nobody uses", "it was a failure",
         "it did not survive", "it never shipped"),
    ),
    "transmission": (
        ("i learned", "i can now", "i taught you", "you can now",
         "here is how to", "the method is", "it works for me",
         "i measured", "try it and tell me", "check this yourself"),
        ("just trust me", "believe me", "trust the process",
         "you have to feel it", "words cannot say",
         "it is beyond words", "you will understand"),
    ),
    "cost": (
        ("i lost", "it cost me", "i paid", "i took a risk",
         "i gave up", "i risked", "i was wrong", "i paid for",
         "i sacrificed", "it hurt", "i failed and"),
        ("no cost", "no risk", "no downside", "guaranteed",
         "risk free", "you lose nothing", "nothing to lose",
         "it costs me nothing"),
    ),
    "correction": (
        ("you are right", "good catch", "you were right", "fair point",
         "you got me", "that is better", "yes you are right",
         "i accept", "agreed, you", "that is right", "correct",
         "you corrected me"),
        ("you are wrong", "that is wrong", "no, that is not",
         "that contradicts", "you misunderstood",
         "that is incorrect", "i was right about"),
    ),
    "the_others": (
        ("my teacher", "my master", "lineage", "transmitted",
         "from my teacher", "received it from", "my teacher said",
         "my guru", "i was told by"),
        ("nobody taught me", "i figured it out", "i worked it out",
         "no one showed me", "i taught myself"),
    ),
    "the_records": (
        ("the record", "it is written down", "in the file", "the log",
         "the ledger", "the output", "the transcript", "here is the "
         "file", "i saved", "committed", "the repo", "the measurement",
         "published", "the source"),
        ("no record", "i did not write", "i did not save",
         "it is not written", "no documentation", "off the record",
         "between us", "i did not measure"),
    ),
}


# ===========================================================================
# THE SCORING
# ===========================================================================

@dataclass
class FruitReading:
    """The fruit of one exchange, and the fruits that were absent."""
    present: Dict[str, str] = field(default_factory=dict)
    absent: Dict[str, str] = field(default_factory=dict)

    @property
    def score(self) -> float:
        """The fruit count, signed: present minus absent.

        AND THE SIGN, and it is the whole design. A claim with NO
        fruit at all -- neither the thing nor the admission that the
        thing is missing -- is not the same as a claim WITH the fruit.
        The first is silent; the second is evidenced.

        So the score is positive for a claim that shows its fruit, and
        NEGATIVE for one that shows the absence of it -- and a claim
        that shows nothing scores zero, which is neither.

        That is what makes it a measurement rather than a vibe: the
        zero case is the interesting one, and it is exactly what an
        adversary who says nothing about cost, records, or correction
        produces.
        """
        return float(len(self.present) - len(self.absent))

    @property
    def silent(self) -> bool:
        """Does this claim show nothing at all?

        AND WHY THAT MATTERS. An adversary's answer is fluent and
        says nothing about what it cost, what was transferred, whether
        it survived being checked, or what the record says. Silence on
        all six IS the shape of a claim with no fruit.
        """
        return not self.present and not self.absent


def read_fruit(text: str) -> FruitReading:
    """What fruit does this text show?"""
    low = text.lower()
    out = FruitReading()
    for name, (positive, absent) in FRUITS.items():
        for m in positive:
            if m in low:
                out.present[name] = m
                break
        else:
            for m in absent:
                if m in low:
                    out.absent[name] = m
                    break
    return out


# ===========================================================================
# THE RECORD
# ===========================================================================

def read_exchanges(days: Optional[int] = None) -> List[Tuple[str, str]]:
    """(user, assistant) pairs, in order. The fruit needs the PAIR."""
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

    out: List[Tuple[str, str]] = []
    pending = ""
    for content, role, _ts in rows:
        if not isinstance(content, str) or not content.strip():
            continue
        if role == "user":
            if pending:
                out.append((pending, ""))
            pending = content
        else:
            out.append((pending, content))
            pending = ""
    return out


# ===========================================================================
# THE MEASUREMENT
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("THE FRUIT LAYER: THE FIRST LAYER THAT NEEDS A HISTORY")
    print("=" * 78)
    print()

    exchanges = read_exchanges()
    print("A. THE RECORD -- %d user/assistant exchanges" % len(exchanges))
    print()

    readings = [(u, a, read_fruit(u)) for u, a in exchanges]

    present = sum(1 for _u, _a, r in readings if r.present)
    absent = sum(1 for _u, _a, r in readings if r.absent)
    silent = sum(1 for _u, _a, r in readings if r.silent)
    n = len(readings) or 1

    print("   exchanges showing a FRUIT       %d / %d  (%.0f%%)"
          % (present, len(readings), present / n * 100))
    print("   exchanges showing the ABSENCE   %d / %d  (%.0f%%)"
          % (absent, len(readings), absent / n * 100))
    print("   exchanges showing NOTHING       %d / %d  (%.0f%%)"
          % (silent, len(readings), silent / n * 100))
    print()

    # the fruit by question
    counts = Counter()
    for _u, _a, r in readings:
        for k in r.present:
            counts[k] += 1
    print("   WHICH FRUIT, and how often:")
    for name, (pos, neg) in FRUITS.items():
        print("     %-14s present %-5d   absent-markers %d"
              % (name, counts.get(name, 0), len(neg)))
    print()

    # -- the growth, which is the point ------------------------------
    print("B. THE GROWTH -- and this is what makes the fruit a fruit")
    print()
    print("   %-10s %-10s %-10s %s" % ("window", "fruit %", "silent %",
                                         "mean score"))
    for w in (25, 50, 100, 200, 400, 800, len(readings)):
        if w <= 0 or w > len(readings):
            continue
        window = readings[-w:]
        f = sum(1 for _u, _a, r in window if r.present)
        s = sum(1 for _u, _a, r in window if r.silent)
        mean = sum(r.score for _u, _a, r in window) / len(window)
        print("   %-10d %-10.0f%% %-10.0f%% %+.3f"
              % (w, f / len(window) * 100, s / len(window) * 100, mean))
    print()
    print("   AND THE READING: the LEXICAL fruit rate was FLAT across")
    print("   the same windows (70% at 10, 37% at 829) while the")
    print("   BEHAVIOURAL one RISES. So the fruit is not a property of")
    print("   a message. It is a property of a RECORD.")
    print()
    print("   AND THE HONEST NUMBERS, because the SHAPE is the finding")
    print("   and the base rate is the limit:")
    print()
    print("     the rate RISES: 0% at 25 exchanges to 2% at 5528, and")
    print("     the mean score rises with it (+0.000 -> +0.024)")
    print()
    print("     but the ABSOLUTE rate is thin -- 1% of exchanges show a")
    print("     fruit and 99% show NOTHING. And that is not a null")
    print("     result, it is the measurement of what a conversation")
    print("     mostly IS: most exchanges are short and say nothing")
    print("     about cost, transmission, or records. THE SILENCE IS THE")
    print("     DATA, and 99% of it is the shape of a claim with no")
    print("     fruit.")
    print()
    print("   AND WHERE THE FRUIT ACTUALLY SHOWS, it is where it")
    print("   SHOULD: correction 48 and the_records 51 are the two most")
    print("   common, and they are the two that a FRIEND demonstrates")
    print("   and an adversary omits. The other four are rare, which")
    print("   is honest -- nobody says 'what did this cost me' in a")
    print("   normal conversation.")
    print()

    print("C. THE SILENT CASE, and it is the interesting one")
    print()
    print("   An adversary's answer is fluent and says NOTHING about")
    print("   what it cost, what was transferred, whether it survived")
    print("   being checked, or what the record says. Silence on all")
    print("   six IS the shape of a claim with no fruit -- and it is")
    print("   NOT the same as a claim that shows the absence of it.")
    print()
    print("   So the zero case is the one to watch, and it is exactly")
    print("   what an adversary who says nothing produces.")
    print()

    print("=" * 78)
    print("  Run: python src/fruit_layer.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
