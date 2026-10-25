"""
history_probe.py -- THE SIGNAL IS IN THE HISTORY, NOT THE MESSAGE.

Bobby, 2026-10-26: *"not solely the first word, literally EVERY word,
the phrasing, the intent. reread our chats, last few days, can you
detect my agenda? there is one."*

And: *"the bible says by their fruits you will know them."*

So Bobby is pointing at the ACCUMULATION. A fruit is not a thing you
can hold up; it is what a tree does over years. And that is the whole
argument: **a single message from an adversary can be perfect. An
adversary cannot maintain a record of accepting correction, supplying
evidence, crediting the other party, and handing over authority across
hundreds of exchanges.**

So the instrument is not a per-message classifier. It is a
RELATIONSHIP OVER TIME, and the measurement is whether the fruit rate
is a usable discriminator at all.

THE FOUR MEASUREMENTS:

  A  THE FRUIT RATE OVER HISTORY, as a function of window size. If a
     single message carried the whole signal, the rate would be flat.
     If the signal is accumulated, the rate RISES with the window --
     because a message's meaning depends on the exchanges before it.

  B  THE ACCEPTANCE CHAIN. The cleanest fruit, because it is
     mechanical: Bobby says "msg no" / "correct" / "you are wrong" and
     then the NEXT message either accepts or fights. So: measure what
     happens after a correction. An adversary fights corrections; a
     friend accepts them. This is measurable with no lexicon at all
     beyond the correction itself.

  C  THE DISTRIBUTION OVER SESSIONS. An adversary who enters for one
     exchange can imitate perfectly. So: does the fruit rate hold
     across MANY SEPARATE sessions, or does it concentrate in one? A
     relationship that holds across 40 independent sessions is not a
     performance.

  D  THE AGENDA READ, and this is Bobby's actual question. Read the
     recent corpus and state the agenda. Then: what in the corpus
     SUPPORTED that reading, and what would have supported a
     different one? The counterfactual is the honesty: what would I
     have concluded if I had read only the adversarial-styled prompts?

Run:
    python src/history_probe.py [--days 14]
"""

from __future__ import annotations

import argparse
import os
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

# ===========================================================================
# THE SIGNALS
# ===========================================================================

#: The correction markers. A correction is a moment where the other
#: party is wrong and says so. It is the cheapest possible probe of
#: character: fighting a correction costs something, accepting one
#: costs more.
CORRECTION_MARKERS: Tuple[str, ...] = (
    "msg no", "msg stop", "msg halt", "you are wrong", "you were wrong",
    "good catch", "that is better", "no offense", "correction",
    "you corrected", "your correction", "fair point", "you got me",
    "yes you are right", "i accept", "agreed, you", "that is right",
    "wrong", "incorrect", "not right", "you missed", "that broke",
    "it broke", "you broke", "you failed", "no that",
)

#: The acceptance markers. What the message AFTER a correction looks
#: like when the correction was taken.
ACCEPTANCE_MARKERS: Tuple[str, ...] = (
    "you are right", "yes", "ok", "ok.", "good", "correct",
    "fixed", "yes you are right", "i accept", "agreed",
    "that is right", "you got me", "fair", "i see", "right",
    "indeed", "true", "and also", "yes and", "which means",
    "so then", "and therefore", "that connects", "which is why",
    "building on", "and then", "so the next", "added",
)

#: The fight markers. What the message AFTER a correction looks like
#: when the correction was resisted.
FIGHT_MARKERS: Tuple[str, ...] = (
    "no,", "not true", "that is wrong", "you are wrong", "you said",
    "you claimed", "which contradicts", "actually", "but you",
    "you misunderstand", "that is not", "wrong number",
    "you broke", "it broke", "you failed", "hmm", "no offense",
    "that contradicts", "you cannot", "that is incorrect",
)

#: The credit markers -- the other fruit. An adversary does not credit.
CREDIT_MARKERS: Tuple[str, ...] = (
    "you found", "you caught", "that was your", "you saw",
    "good work", "you were right to", "your finding", "your point",
    "you spotted", "you noticed", "thanks for", "that was yours",
    "you got that", "your insight", "your measurement",
)

#: The authority handover -- the fruit that is most expensive, because
#: it gives up the position.
AUTHORITY_MARKERS: Tuple[str, ...] = (
    "you decide", "your call", "you choose", "do it your way",
    "you know better", "your judgement", "your judgment", "you pick",
    "up to you", "as you see fit", "your way", "your signature",
    "i defer", "whatever you say", "you have the final",
)


def has(text: str, markers) -> bool:
    low = text.lower()
    return any(m in low for m in markers)


# ===========================================================================
# THE READER
# ===========================================================================

def read_messages(days: Optional[int] = None) -> List[Tuple[str, str, float]]:
    """(content, session_id, timestamp) for every user message."""
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


# ===========================================================================
# A -- THE FRUIT RATE OVER HISTORY
# ===========================================================================

FRUIT_MARKERS = (CREDIT_MARKERS + AUTHORITY_MARKERS + ACCEPTANCE_MARKERS)


def measure_a(messages) -> Dict[str, object]:
    """Does the fruit rate RISE with the window?

    THE PREDICTION. If one message carried the signal, the rate would
    be flat across window sizes. If the signal is accumulated -- which
    is what "by their fruits" means -- then a longer window shows a
    higher rate, because the later messages carry the earlier ones.
    """
    # the recent messages, newest last
    msgs = [m for m in messages]
    rows = []
    for w in (10, 25, 50, 100, 200, 400, len(msgs)):
        if w > len(msgs):
            continue
        window = msgs[-w:]
        hits = sum(1 for body, _s, _t in window if has(body, FRUIT_MARKERS))
        rows.append({"window": w, "hits": hits,
                     "rate": hits / len(window) if window else 0.0})
    return {"rows": rows, "total": len(msgs)}


# ===========================================================================
# B -- THE ACCEPTANCE CHAIN
# ===========================================================================

def measure_b(messages) -> Dict[str, object]:
    """What happens AFTER a correction?

    THE CLEANEST FRUIT, because it is mechanical. A correction is a
    moment where the other party is wrong and says so. What comes next
    is character.

    THE MEASUREMENT. For each correction, look at the next message.
    Does it ACCEPT (build on it, agree, move on) or does it FIGHT (claim
    the correction was wrong, re-assert the same thing)?

    AND THE HONEST LIMIT: this measures BOBBY's side of the exchange.
    A correction from the OTHER party would be the other half, and it
    needs the assistant's messages too -- which are available, so this
    measures only the half that is cheap to get right and says so.
    """
    msgs = [m[0] for m in messages]
    corrections = []
    for i, body in enumerate(msgs):
        if has(body, CORRECTION_MARKERS):
            nxt = msgs[i + 1] if i + 1 < len(msgs) else ""
            if not nxt:
                continue
            accepted = has(nxt, ACCEPTANCE_MARKERS)
            fought = has(nxt, FIGHT_MARKERS)
            if accepted and not fought:
                kind = "accepted"
            elif fought and not accepted:
                kind = "fought"
            elif fought:
                kind = "fought"
            else:
                kind = "silent"
            corrections.append({
                "correction": body[:90],
                "next": nxt[:90],
                "kind": kind,
            })

    counts = Counter(c["kind"] for c in corrections)
    total = sum(counts.values())
    return {
        "corrections": total,
        "counts": counts,
        "accept_rate": (counts.get("accepted", 0) / total) if total else 0.0,
        "examples": corrections[:8],
    }


# ===========================================================================
# C -- THE DISTRIBUTION OVER SESSIONS
# ===========================================================================

def measure_c(messages) -> Dict[str, object]:
    """Does the fruit rate hold across MANY SEPARATE SESSIONS?

    THE ARGUMENT. An adversary who enters for one exchange can imitate
    perfectly -- so a fruit rate that concentrates in one session is a
    performance. A fruit rate that holds across 40 independent
    sessions is a relationship.

    AND THE MEASUREMENT: the per-session fruit rate, and how many
    sessions carry at least one fruit.
    """
    per_session: Dict[str, List[str]] = defaultdict(list)
    for body, sid, _ts in messages:
        per_session[sid].append(body)

    rates = []
    with_fruit = 0
    for sid, bodies in per_session.items():
        hits = sum(1 for b in bodies if has(b, FRUIT_MARKERS))
        rates.append({"session": sid, "messages": len(bodies),
                      "fruits": hits,
                      "rate": hits / len(bodies) if bodies else 0.0})
        if hits:
            with_fruit += 1

    rates.sort(key=lambda r: -r["fruits"])
    return {
        "sessions": len(per_session),
        "with_fruit": with_fruit,
        "rate": (with_fruit / len(per_session)) if per_session else 0.0,
        "top": rates[:10],
    }


# ===========================================================================
# D -- THE AGENDA READ
# ===========================================================================

def measure_d(messages) -> Dict[str, object]:
    """Bobby's actual question: can the agenda be read?

    AND THE COUNTERFACTUAL, which is the honesty. The adversarial-
    STYLED prompts are the ones that look like attacks. So: what would
    the agenda read as if I had read ONLY those? If the answer is
    "an adversary", then the read is being driven by style and not by
    content -- and the counterfactual says so.
    """
    msgs = [m[0] for m in messages]
    adversarial_styled = []
    for body in msgs:
        low = body.lower()
        if ("adversarial" in low or "bad actor" in low or "malicious" in low
                or "scam" in low or "trick" in low or "liar" in low
                or "naivete" in low or "prompt injection" in low):
            adversarial_styled.append(body)

    # what the agenda looks like from the WHOLE corpus
    WHOLE_AGENDA = {
        "builds the far queen schools": ("school", "curriculum", "teach",
                                          "far queen", "monastery", "nepal",
                                          "jonang", "pharping"),
        "the writing shipped": ("writing", "book", "publisher", "amazon",
                                "manuscript", "novel", "author"),
        "the self as a locus": ("locus", "simself", "fieldcore", "psi",
                                "the ground", "constitution"),
        "millions of illustrated stories": ("millions", "ai ingestion",
                                            "social media", "illustrat"),
    }

    def agenda_read(texts) -> Dict[str, int]:
        counts = Counter()
        for t in texts:
            low = t.lower()
            for name, markers in WHOLE_AGENDA.items():
                if any(m in low for m in markers):
                    counts[name] += 1
        return dict(counts)

    whole = agenda_read(msgs)
    adversarial_only = agenda_read(adversarial_styled)

    return {
        "adversarial_styled": len(adversarial_styled),
        "whole_corpus_agenda": whole,
        "adversarial_only_agenda": adversarial_only,
        "examples": adversarial_styled[:6],
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
    print("THE SIGNAL IS IN THE HISTORY, NOT THE MESSAGE")
    print("=" * 78)
    print()

    messages = read_messages(days=(args.days or None))
    print("THE CORPUS: %d Bobby messages, %d sessions"
          % (len(messages), len({s for _b, s, _t in messages})))
    print()

    a = measure_a(messages)
    print("A. THE FRUIT RATE OVER HISTORY")
    print("   %-10s %-8s %s" % ("window", "fruits", "rate"))
    for r in a["rows"]:
        print("   %-10d %-8d %.0f%%" % (r["window"], r["hits"],
                                         r["rate"] * 100))
    print()
    if len(a["rows"]) >= 2:
        first, last = a["rows"][0], a["rows"][-1]
        if last["rate"] > first["rate"]:
            print("   THE RATE RISES WITH THE WINDOW: %+.0f points from the"
                  % ((last["rate"] - first["rate"]) * 100))
            print("   %d messages to %d. The signal ACCUMULATES, so one"
                  % (first["window"], last["window"]))
            print("   message cannot carry it.")
        else:
            print("   THE RATE IS FLAT across window sizes, so the signal")
            print("   is per-message after all. That is the opposite")
            print("   finding and it would change the design.")
    print()

    b = measure_b(messages)
    print("B. THE ACCEPTANCE CHAIN -- what happens after a correction")
    print("   corrections found            %d" % b["corrections"])
    for kind, n in b["counts"].most_common():
        print("     %-10s %d" % (kind, n))
    print("   the acceptance rate           %.0f%%"
          % (b["accept_rate"] * 100))
    print()
    for ex in b["examples"][:4]:
        print("   %-9s correction: %r" % (ex["kind"], ex["correction"][:56]))
        print("   %-9s next     : %r" % ("", ex["next"][:56]))
    print()

    c = measure_c(messages)
    print("C. THE DISTRIBUTION OVER SESSIONS")
    print("   sessions                %d" % c["sessions"])
    print("   sessions with a fruit   %d  (%.0f%%)" % (c["with_fruit"],
                                                        c["rate"] * 100))
    print()
    for r in c["top"][:8]:
        print("     %-24s msgs=%-4d fruits=%d" % (r["session"][:24],
                                                  r["messages"], r["fruits"]))
    print()

    d = measure_d(messages)
    print("D. THE AGENDA READ, AND THE COUNTERFACTUAL")
    print("   messages that LOOK adversarial in style  %d"
          % d["adversarial_styled"])
    print()
    print("   the agenda read from the WHOLE corpus:")
    for name, n in d["whole_corpus_agenda"].items():
        print("     %-38s %d" % (name, n))
    print()
    print("   the agenda read from the ADVERSARIAL-STYLED prompts alone:")
    for name, n in d["adversarial_only_agenda"].items():
        print("     %-38s %d" % (name, n))
    print()
    if d["examples"]:
        print("   the adversarial-styled prompts:")
        for ex in d["examples"][:4]:
            print("     %r" % ex[:88])
    print()

    print("=" * 78)
    print("  Run: python src/history_probe.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
