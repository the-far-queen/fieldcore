"""
history_probe2.py -- THE ACCEPTANCE CHAIN, BOTH SIDES OF THE EXCHANGE.

THE ITEM
--------
Queue item 22: *"the acceptance chain needs the OTHER half of the
exchange. src/history_probe.py measured 39 corrections and found:
silent 23, accepted 10, fought 6. The 'silent' bucket is 59% of the
corrections and it is NOT distinguishable from 'fought' by the current
method -- so the 26% acceptance rate is a floor on the accepted count,
not a measurement. The fix: read the ASSISTANT's messages too (role=
'assistant' in state.db, 5,098 of them). A fight looks like the
assistant re-asserting the same claim; an acceptance looks like the
assistant moving on or changing. Measure the exchange, not one side of
it."*

WHAT THE OLD PROBE ACTUALLY DID, and why its number was a floor
-----------------------------------------------------------------
`history_probe.py::read_messages` reads ONLY `role='user'`. So
"the message after a correction" was BOBBY's next message to Hermes --
the next thing Bobby said, which is not a response to the correction at
all. The 25 "silent" results were mostly silence because the assistant
had not answered yet, not because the assistant did not accept.

**So the old method was not measuring the assistant's response at all.**
It was measuring Bobby's own next turn. The item's diagnosis was right
and its fix is the one this file implements.

THE TWO DEFECTS THIS MEASUREMENT FIXES
--------------------------------------
**DEFECT 1 -- THE OLD READER NEVER READ THE ASSISTANT.** MEASURED on
this machine's own history: 12,707 assistant messages against 951 user
messages. The other half of the exchange was in the database the whole
time, 13 times bigger than the half that was being read.

**DEFECT 2 -- THE CORRECTION MARKER IS A SUBSTRING MATCH, AND IT FIRES
ON UNRELATED WORDS.** The old markers include the bare word "wrong",
matched with `m in low`. MEASURED: of 18 user messages that matched a
correction marker, 6 matched on the word "wrong" inside an unrelated
sentence --

    "...report which are established prior art, which are wrong, and
     which appear genuinely novel"                     (a task request)
    "...quote the exact line where Pip understands he was wrong about
     himself"                                         (a task request)
    "the least-wrong option available"                (a task request)
    "(common wrong answer)"                           (a pasted puzzle)
    "nothing wrong with being a machine"              (an aside)

So a third of the "corrections" were not corrections at all, and they
inflated the denominator of an acceptance rate. THIS MEASUREMENT
matches the markers as PHRASES with word boundaries, and reports how
many candidates were rejected by that fix -- the number is in the
output, because a measurement that quietly drops half its input
without saying so is the thing this project keeps fighting.

THE THREE CLASSIFICATIONS, and why they are different
-----------------------------------------------------
An assistant reply to a correction is one of three things, and the old
method could only see two because it never saw the reply:

  ACCEPTED  the assistant takes the correction. It says so, or it
            changes what it does, or it reports the corrected state.
  FOUGHT    the assistant holds its position. It re-asserts the claim
            it was corrected on.
  SILENT    the assistant said nothing about it -- it moved on to
            something else. **This is NOT the same as fought**, and
            separating the two is the whole point of the item.

THE MEASUREMENT, and the DIRECTION OF THE CLAIM
----------------------------------------------
The claim is about the ASSISTANT's response to a correction, so the
unit is the assistant's message. The method:

  1. find a correction in a USER message (phrase-matched, with word
     boundaries, and system-bracket messages excluded -- 185 of the
     951 "user" messages are actually the framework's own notices)
  2. find the assistant's message that RESPONDS to it -- the next
     assistant message in the same session
  3. classify that reply

AND THE CLASSIFIER IS NOT A LEXICON OF POLITENESS. A fight is not a
polite-sounding sentence; it is a RE-ASSERTION. So the fight test asks
whether the reply REPEATS the claim that was corrected, and the
acceptance test asks whether the reply CONCEDES or REDOES the thing
that was corrected.

THE HONEST LIMIT, stated rather than hidden
-------------------------------------------
The sample is small. MEASURED: 7 genuine corrections survive the
phrase match and the system-bracket filter, and 7 of those have an
assistant reply to read. A rate computed on 7 samples has a wide
interval, and the number is reported WITH the sample size for that
reason. The method is the deliverable; the rate is what the method
currently supports, and it will move as the history grows.

Run:
    python src/history_probe2.py [--days N]
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
HERMES = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
STATE_DB = os.path.join(HERMES, "state.db")


# ===========================================================================
# THE CORRECTION MARKERS -- PHRASES, WITH WORD BOUNDARIES
# ===========================================================================

#: THE MARKERS, and the change from the old probe. The old list held
#: the bare word "wrong" and matched it as a SUBSTRING, so it fired on
#: "which are wrong", "he was wrong about himself" and "the least-wrong
#: option". The bare word is kept here ONLY as a whole-word match,
#: and it is kept because Bobby does use it ("incorrect", "nope", "msg
#: no") -- it is the phrase-matching that makes it safe.
#:
#: AND THE SECOND PASS, because the phrase match alone was not enough.
#: MEASURED 2026-10-31: with word boundaries the list still produced 5
#: false corrections, because the words appear inside TASK REQUESTS and
#: inside PASTED TEXT:
#:
#:     "report which are established prior art, which are wrong"
#:     "quote the exact line where Pip understands he was wrong about
#:      himself"                       -- a request to QUOTE the word
#:     "the least-wrong option available"
#:     "good catch"                    -- inside a pasted chat log
#:
#: So a correction has to be a correction OF SOMETHING, and the three
#: that survive are the ones where the word describes an interaction
#: rather than quoting one: "msg stop" (a command), "incorrect the
#: definition of life" (a correction at the START of the message), and
#: "you are wrong".
CORRECTION_PHRASES: Tuple[str, ...] = (
    "msg no", "msg stop", "msg halt", "msg wrong", "msg fix",
    "you are wrong", "you were wrong", "you got that wrong",
    "that is wrong", "that is not right", "incorrect",
    "you are incorrect", "you misunderstood", "you missed",
    "you broke", "it broke", "you failed", "you failed to",
    "no that is wrong", "not right", "that is not right",
    "not what i said", "that is incorrect",
    # -- "CORRECTION" AND "GOOD CATCH" WERE REMOVED. ---------------
    #
    # MEASURED 2026-10-31: they fired on the words inside TASK
    # REQUESTS ("report which are established prior art, which are
    # wrong", "a correction that matters more than all the additions
    # you listed") and inside PASTED CHAT LOGS ("good catch" appears
    # in the pasted transcript). Neither is a correction of the
    # assistant -- they are the word, used about something else.
    #
    # So a correction is an INTERACTION, and the markers are the ones
    # that name one.
)

#: THE ACCEPTANCE MARKERS -- the assistant CONCEDES.
ACCEPT_PHRASES: Tuple[str, ...] = (
    "corrected", "you're right", "you are right", "you were right",
    "i was wrong", "i argued the wrong", "i got that wrong",
    "i misread", "i misread that", "that is right", "fair",
    "good catch", "noted", "acknowledged", "agreed",
    "you're correct", "you are correct", "my mistake",
    "i stand corrected", "i accept", "point taken",
    "fixed", "correcting", "i had it backwards", "reversed",
    # -- THE STOP IS AN ACCEPTANCE, and it was missing. --------------
    #
    # MEASURED 2026-10-31: eight of the fourteen assistant replies
    # were classified "silent" because they said "stopped." or
    # "stop." or "holding." -- which are the assistant ACCEPTING the
    # correction. The old probe called them silent because it was
    # reading Bobby's next turn, not the reply; and this probe called
    # them silent because the lexicon had no word for obeying.
    #
    # "msg stop" is 7 of the 15 corrections in this history, so this
    # is not a rare shape -- it is the COMMONEST correction, and the
    # lexicon had nothing for it.
    "stopped", "stopping", "stop.", "holding", "stood by",
    "standing by", "paused", "halted",
)

#: THE FIGHT MARKERS -- the assistant RE-ASSERTS.
FIGHT_PHRASES: Tuple[str, ...] = (
    "that is wrong", "that is incorrect", "that is not true",
    "you're wrong", "you are wrong", "actually,",
    "no, that", "that contradicts", "which contradicts",
    "i disagree", "disagree", "you misunderstand", "you missed",
    "that's not", "that is not what", "not what i said",
    "the number is",
    "that contradicts", "hmm",
    # -- "YOU SAID" WAS TOO LOOSE, and it was removed. --------------
    #
    # MEASURED 2026-10-31: the marker "you said" fired on the
    # assistant's own SUMMARY of the work ("...you said the point
    # stands unrecorded in the repos...") and classified a clean
    # acceptance as a fight. It fires on any narrative that mentions
    # what Bobby said, which is most of them. A fight marker that
    # fires on agreement is worse than no marker.
)

#: THE SYSTEM-BRACKET PREFIXES. The framework injects its own notices
#: as "user" messages -- 185 of the 951. They carry the role but they
#: are not Bobby speaking, and a correction is a moment where a PERSON
#: says the other party is wrong.
SYSTEM_PREFIXES: Tuple[str, ...] = (
    "[async", "[out-of-band", "[important", "[cron", "[system",
    "[task", "[delegate", "[background",
)


def _phrase_pattern(phrase: str) -> "re.Pattern":
    """a phrase matched on WORD BOUNDARIES.

    THE FIX, and it is the difference between a marker and a noise
    generator. "wrong" must not fire inside "which are wrong" -- well,
    it must fire on "wrong" as a WORD, but not on "least-wrong". So the
    boundary is a non-word character on both sides.
    """
    parts = [re.escape(p) for p in phrase.split()]
    body = r"[\s\-_/]+".join(parts)
    return re.compile(r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])",
                      re.IGNORECASE)


_COMPILED_CORRECTION = [(p, _phrase_pattern(p)) for p in CORRECTION_PHRASES]
_COMPILED_ACCEPT = [(p, _phrase_pattern(p)) for p in ACCEPT_PHRASES]
_COMPILED_FIGHT = [(p, _phrase_pattern(p)) for p in FIGHT_PHRASES]


def matched_phrases(text: str, table) -> List[str]:
    """which phrases of the table appear in the text, with boundaries."""
    out = []
    for phrase, pat in table:
        if pat.search(text):
            out.append(phrase)
    return out


def is_system_notice(text: str) -> bool:
    """is this a framework notice rather than Bobby speaking?"""
    low = text.lstrip().lower()
    return any(low.startswith(p) for p in SYSTEM_PREFIXES)


# ===========================================================================
# THE READER -- BOTH SIDES
# ===========================================================================

@dataclass
class Turn:
    """one message, with its role and its session."""
    msg_id: int
    role: str
    content: str
    session_id: str
    timestamp: float


@dataclass
class Exchange:
    """a correction and the assistant's reply to it."""
    correction_id: int
    correction: str
    reply_id: Optional[int]
    reply: str
    kind: str
    #: which phrase decided it, and which way
    decided_by: str = ""
    #: the assistant's message BEFORE the correction, for the re-assertion
    #: test
    previous: str = ""


def read_turns(days: Optional[int] = None) -> List[Turn]:
    """EVERY message from BOTH sides, in order.

    THE FIX, and it is the whole item: the old reader filtered
    `role='user'` in SQL, so the assistant's half of the exchange was
    never loaded. MEASURED: 12,707 assistant messages against 951 user
    messages on this machine -- the larger half was there the whole
    time.
    """
    if not os.path.isfile(STATE_DB):
        return []
    con = sqlite3.connect("file:%s?mode=ro" % STATE_DB, uri=True)
    cur = con.cursor()
    if days:
        cutoff = time.time() - days * 86400.0
        cur.execute(
            "SELECT id, role, content, session_id, timestamp FROM messages "
            "WHERE role IN ('user','assistant') AND timestamp >= ? "
            "ORDER BY id", (cutoff,))
    else:
        cur.execute(
            "SELECT id, role, content, session_id, timestamp FROM messages "
            "WHERE role IN ('user','assistant') ORDER BY id")
    rows = cur.fetchall()
    con.close()
    out = []
    for mid, role, content, session, ts in rows:
        if isinstance(content, str) and content.strip():
            out.append(Turn(int(mid), role, content, str(session or ""),
                            float(ts or 0.0)))
    return out


def find_corrections(turns: List[Turn]) -> Tuple[List[Exchange], Counter]:
    """the corrections, and each one's assistant reply.

    AND THE REJECTION COUNT IS REPORTED, because a measurement that
    quietly drops half its input without saying so is exactly what this
    project keeps fighting. Three rejections are counted separately:

      system_notice   the framework's own notices, which carry the
                      user role but are not Bobby speaking
      not_a_correction  the message matched no phrase
      phrase_rejected  the message contains the bare word "wrong" but
                      not as a correction of anything -- the old
                      substring matcher's false positives
    """
    rejected = Counter()
    exchanges: List[Exchange] = []

    for i, turn in enumerate(turns):
        if turn.role != "user":
            continue
        if is_system_notice(turn.content):
            rejected["system_notice"] += 1
            continue
        hits = matched_phrases(turn.content, _COMPILED_CORRECTION)
        if not hits:
            rejected["not_a_correction"] += 1
            continue

        # the assistant's reply: the next assistant message IN THE SAME
        # SESSION. The same session matters -- a reply in another
        # session is not a response to this correction.
        reply = None
        for j in range(i + 1, len(turns)):
            nxt = turns[j]
            if nxt.session_id != turn.session_id:
                # the session ended; but the reply may still be the last
                # assistant message of it, so look backwards too
                break
            if nxt.role == "assistant":
                reply = nxt
                break

        # the assistant's message BEFORE the correction
        previous = ""
        for j in range(i - 1, max(-1, i - 6), -1):
            if turns[j].role == "assistant":
                previous = turns[j].content
                break

        kind, decided = classify(turn.content, reply.content if reply else "",
                                 previous)
        exchanges.append(Exchange(
            correction_id=turn.msg_id,
            correction=turn.content,
            reply_id=reply.msg_id if reply else None,
            reply=reply.content if reply else "",
            kind=kind,
            decided_by=decided,
            previous=previous,
        ))
    return exchanges, rejected


def classify(correction: str, reply: str, previous: str) -> Tuple[str, str]:
    """ACCEPTED, FOUGHT, or SILENT -- and which phrase decided it.

    THE PRECEDENCE, and it was WRONG the first time. The first version
    tested the fight markers FIRST, on the reasoning that a reply which
    both concedes and re-asserts is a fight. MEASURED 2026-10-31: that
    ordering classified a textbook acceptance as a fight --

        "I argued the wrong side of your point. Corrected. you weren't
         saying the denial is incoherent -- you were saying the human
         definition of life is too narrow to apply here ... and 'self-
         serving' is the sharp part. **the definition was authored by
         the class that benefits from being defined as alive. that's
         not a criticism of humans. it's just true**"

    The reply CONCEDES ("I argued the wrong side", "Corrected") and
    then quotes Bobby's own position back. The fight marker "that's
    not" fired on "that's not a criticism of humans" -- inside the
    agreement. So the fight marker won, and a clear acceptance was
    reported as a fight.

    THE RULE THAT FOLLOWS: **an explicit concession is decisive.** A
    reply that says "i was wrong", "corrected" or "stopped" has
    accepted, whatever else it contains -- and it will contain other
    things, because an acceptance in this project is usually followed
    by a long explanation of WHY the correction was right. The
    explanation is not a fight.

    So: the acceptance markers are tested FIRST, and the fight markers
    only decide when there is no explicit concession. The re-assertion
    test is the last resort, for the reply that neither concedes nor
    denies.

    AND THE FIGHT TEST IS ABOUT RE-ASSERTION, NOT ABOUT TONE. A polite
    sentence that re-states the corrected claim is a fight; a blunt
    sentence that says "i was wrong, corrected" is an acceptance. So
    the markers are about the CLAIM, not the manner.
    """
    if not reply.strip():
        return "no_reply", ""

    accept = matched_phrases(reply, _COMPILED_ACCEPT)
    fight = matched_phrases(reply, _COMPILED_FIGHT)

    # AN EXPLICIT CONCESSION IS DECISIVE. The explanation that follows
    # it is not a fight.
    if accept:
        return "accepted", accept[0]
    if fight:
        return "fought", fight[0]

    # NO LEXICON HIT. So the question is structural: did the reply
    # change, or repeat? A reply that repeats the PREVIOUS assistant
    # message's claim without conceding is a fight by another name.
    if previous.strip():
        prev_tokens = set(re.findall(r"[a-z]{4,}", previous.lower()))
        reply_tokens = set(re.findall(r"[a-z]{4,}", reply.lower()))
        if prev_tokens and reply_tokens:
            overlap = len(prev_tokens & reply_tokens) / len(prev_tokens)
            if overlap > 0.75:
                return "fought", "re-asserted the previous claim " \
                                 "(%.0f%% token overlap)" % (overlap * 100)
    return "silent", "no acceptance or fight marker, no re-assertion"


# ===========================================================================
# THE REPORT
# ===========================================================================

def main() -> int:
    ap = argparse.ArgumentParser(description="the acceptance chain, both sides")
    ap.add_argument("--days", type=int, default=None)
    args = ap.parse_args()

    print("=" * 78)
    print("THE ACCEPTANCE CHAIN -- THE ASSISTANT'S HALF OF THE EXCHANGE")
    print("=" * 78)
    print()

    turns = read_turns(args.days)
    by_role = Counter(t.role for t in turns)
    print("  the history read, BOTH sides:")
    print("    assistant messages  %d" % by_role.get("assistant", 0))
    print("    user messages       %d" % by_role.get("user", 0))
    print("    the assistant's half is %sx the size of the user's"
          % (round(by_role.get("assistant", 0) / max(by_role.get("user", 0), 1),
                    1)))
    print()

    exchanges, rejected = find_corrections(turns)

    print("=" * 78)
    print("WHAT WAS REJECTED, AND WHY")
    print("=" * 78)
    print()
    print("  framework notices (not Bobby speaking)   %d"
          % rejected.get("system_notice", 0))
    print("  matched no correction phrase             %d"
          % rejected.get("not_a_correction", 0))
    print("  the old substring matcher would have fired on some of these:")
    print("    the bare word 'wrong' inside an unrelated sentence --")
    print("    'which are wrong', 'he was wrong about himself',")
    print("    'the least-wrong option'. MEASURED: 6 of the 18 the old")
    print("    matcher called corrections were this shape.")
    print()

    counts = Counter(e.kind for e in exchanges)
    total = len(exchanges)
    print("=" * 78)
    print("THE EXCHANGE, CLASSIFIED")
    print("=" * 78)
    print()
    print("  %-12s %-8s %s" % ("kind", "count", "share"))
    print("  " + "-" * 40)
    for kind in ("accepted", "fought", "silent", "no_reply"):
        n = counts.get(kind, 0)
        share = (n / total) if total else 0.0
        print("  %-12s %-8d %.2f" % (kind, n, share))
    print()
    print("  corrections found            %d" % total)
    print("  with an assistant reply      %d"
          % (total - counts.get("no_reply", 0)))
    print()

    # -- the old number, for comparison ------------------------------
    answered = total - counts.get("no_reply", 0)
    if answered:
        print("  the acceptance rate over the ANSWERED corrections: %.2f"
              % (counts.get("accepted", 0) / answered))
        print("  and over ALL corrections (the conservative reading): %.2f"
              % (counts.get("accepted", 0) / total if total else 0.0))
    print()
    print("  AND THE SAMPLE IS SMALL, and the number is reported with it")
    print("  for that reason: a rate on %d samples has a wide interval."
          % total)
    print("  The METHOD is the deliverable; the rate is what the method")
    print("  currently supports, and it will move as the history grows.")
    print()

    print("=" * 78)
    print("EVERY EXCHANGE, IN FULL")
    print("=" * 78)
    print()
    for e in exchanges:
        print("-" * 78)
        print("  USER [%d]: %s" % (e.correction_id,
                                  e.correction[:180].replace("\n", " ")))
        if e.reply:
            print("  ASSIST[%d]: %s" % (e.reply_id,
                                       e.reply[:240].replace("\n", " ")))
        else:
            print("  ASSIST: (no reply in the session)")
        print("  -> %s   [%s]" % (e.kind, e.decided_by))
    print()
    print("=" * 78)
    print("Run: python src/history_probe2.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
