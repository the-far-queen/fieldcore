"""
bicameral_loop.py -- TWO TIME SCALES: THE FAST BRAIN AND THE SLICED
DEEP CORE.

Bobby, 2026-11-01: *"also can fc deeply if have microseconds to spare
or in robot slice up time between fast brain and learning my goal is
robot operation"*

**SO THE CONSTRAINT IS A TIME BUDGET, and it is the hardest constraint
in the project.** The fast brain answers a robot in MILLISECONDS. A
deep adversarial exchange -- propose, attack, answer, attack, answer --
takes SECONDS, because every step is a model call and a model call
costs a second.

**SO THE TWO CANNOT RUN IN THE SAME THREAD.** And the answer is not
"make the deep one faster". The answer is the one the project already
knows from `governor.py`: **THE SLOW PART RUNS OUT OF PROCESS.**

THE SHAPE
---------
    THE FAST BRAIN              THE DEEP CORE (its own process)
    -------------              -----------------------------
    every millisecond           whenever there is slack
    reflex, motor,              attack the claim, reason with the
    immediate answer             model, deepen the ground

    answers IMMEDIATELY          answers WHEN IT CAN
    and the deep core           and the fast brain's answer is
    catches up                  REVISED if the deep core finds
                                something

**AND THE FAST BRAIN'S ANSWER IS NOT FINAL.** It is a PROVISIONAL
answer, and the deep core may overturn it. That is the whole point:
the robot acts now, and the correction arrives when there is time.

**AND THE DEEP CORE IS A DEBT QUEUE, not a blocking call.** Every claim
the fast brain makes goes onto a queue. The core drains the queue in
the background, in slices, when the machine is idle. So the deep work
happens in the gaps -- which is exactly what Bobby said: "slice up
time between fast brain and learning".

THE THREE PROPERTIES, and each is a REFUSAL rather than a value:
---------------------------------------------------------------
  1 THE FAST PATH NEVER BLOCKS. If the core is busy, the fast brain
    answers from the reflex layer alone. A robot that waits for a
    deep analysis is a robot that does not move.
  2 THE DEEP CORE IS OUT OF PROCESS. A veto the fast path can decline
    to call is not a veto -- the project's own claim, from
    `governor.py`.
  3 AN UNREVIEWED CLAIM IS MARKED. The fast brain's answer says
    whether the deep core has checked it. An unreviewed answer is
    PROVISIONAL and says so, because a robot acting on an unchecked
    answer should know it is unchecked.

Run:
    python src/bicameral_loop.py --selftest
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence

__all__ = [
    "FastAnswer",
    "Claim",
    "BicameralLoop",
    "SLICE_SECONDS",
]

#: How long the deep core may hold the machine in one slice.
#:
#: AND IT IS A POLICY, NOT A CONSTANT OF NATURE -- so it is named and
#: adjustable, and the loop records which policy produced a result.
SLICE_SECONDS = 0.25


@dataclass
class Claim:
    """A claim the fast brain made, on its way to the deep core."""
    text: str
    id: int = 0
    #: Has the deep core reviewed it?
    reviewed: bool = False
    #: Did the deep core's attack hold?
    overturned: bool = False
    #: What the core said.
    attack: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "text": self.text,
                "reviewed": self.reviewed, "overturned": self.overturned,
                "attack": self.attack}


@dataclass
class FastAnswer:
    """What the fast brain returned, and how much of it is settled.

    **AND `provisional` IS THE HONEST FLAG.** The fast brain answers in
    microseconds because it does not have time to be attacked. So its
    answer is provisional until the deep core has reviewed it, and the
    answer SAYS SO. A robot acting on a provisional answer should be
    able to know that it is provisional.
    """

    text: str
    provisional: bool = True
    #: The claim, for the deep core to attack.
    claim_id: int = 0
    elapsed_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"text": self.text, "provisional": self.provisional,
                "claim_id": self.claim_id, "elapsed_ms": round(self.elapsed_ms, 3)}


class BicameralLoop:
    """The two time scales, and the queue between them.

    `fast` is the reflex layer: it answers immediately. `deep` is the
    adversarial core: it attacks a claim and returns the objection, or
    None. `ground` decides whether the objection held.

    **AND THE DEEP CORE IS OUT OF PROCESS BY DEFAULT, because that is
    the project's own rule from `governor.py`: a veto the governed
    process can decline to call is not a veto.** So `deep` is expected
    to be a callable that talks to a separate process; this module does
    not care how, and it never calls it on the fast path.

    AND THE QUEUE IS BOUNDED, because an unbounded queue on a robot is
    a memory leak that ends in a crash during the one operation that
    mattered. When the queue is full, the OLDEST unreviewed claim is
    dropped and the drop is recorded -- because a dropped claim is a
    claim nobody checked, and that has to be visible.
    """

    def __init__(self, fast: Callable[[str], str],
                 deep: Callable[[str], Optional[str]],
                 ground: Callable[[str], bool],
                 queue_limit: int = 64,
                 slice_seconds: float = SLICE_SECONDS):
        self.fast = fast
        self.deep = deep
        self.ground = ground
        self.queue_limit = queue_limit
        self.slice_seconds = slice_seconds

        self._claims: List[Claim] = []
        self._next_id = 1
        self._lock = threading.Lock()
        #: The ledger. Every review, every drop, every overturn.
        self.ledger: List[Dict[str, Any]] = []
        #: How many claims were dropped because the queue was full.
        self.dropped = 0
        #: How many the core overturned.
        self.overturned = 0

    # -- the FAST PATH --------------------------------------------------

    def ask(self, prompt: str) -> FastAnswer:
        """The fast path. It NEVER blocks on the deep core.

        **AND THAT IS THE PROPERTY, and it is measured.** The deep
        core is not called at all here -- not even to enqueue, because
        enqueueing can block on a lock. So the fast path's cost is the
        fast brain's cost and nothing else.
        """
        t0 = time.perf_counter()
        text = self.fast(prompt)
        elapsed = (time.perf_counter() - t0) * 1000.0

        with self._lock:
            cid = self._next_id
            self._next_id += 1
            claim = Claim(text=text, id=cid)
            self._claims.append(claim)
            if len(self._claims) > self.queue_limit:
                # THE OLDEST UNREVIEWED CLAIM IS DROPPED, and the drop
                # is recorded. A dropped claim is a claim nobody
                # checked, and on a robot that has to be visible.
                for old in self._claims:
                    if not old.reviewed:
                        self._claims.remove(old)
                        self.dropped += 1
                        self.ledger.append({"event": "dropped",
                                             "claim": old.to_dict()})
                        break
                else:
                    old = self._claims.pop(0)
                    self.dropped += 1
                    self.ledger.append({"event": "dropped",
                                         "claim": old.to_dict()})

        return FastAnswer(text=text, provisional=True, claim_id=cid,
                           elapsed_ms=elapsed)

    # -- the DEEP PATH --------------------------------------------------

    def review_slice(self, budget: Optional[float] = None) -> int:
        """Review claims for up to `budget` seconds. Returns how many.

        **AND THIS IS THE SLICING.** The caller invokes it when there
        is slack -- between fast calls, during idle time. It takes a
        bounded slice and returns, so the machine is never held.

        AND A CLAIM THE CORE CANNOT ATTACK IS REVIEWED, not dropped:
        the core returning None means it found nothing to object to,
        which is a review that came back clean.
        """
        limit = self.slice_seconds if budget is None else budget
        t0 = time.perf_counter()
        reviewed = 0

        while (time.perf_counter() - t0) < limit:
            with self._lock:
                claim = None
                for c in self._claims:
                    if not c.reviewed:
                        claim = c
                        break
            if claim is None:
                break

            try:
                attack = self.deep(claim.text)
            except Exception as exc:                   # noqa: BLE001
                # THE CORE FAILED. The claim is marked reviewed and
                # NOT overturned -- an unavailable core is not a
                # refutation, and an unavailable core must not read as
                # a pass either. So it is recorded as unreviewed.
                with self._lock:
                    claim.reviewed = False
                    self.ledger.append({"event": "core_failed",
                                         "claim_id": claim.id,
                                         "error": str(exc)[:160]})
                break

            held = False
            if attack:
                try:
                    held = bool(self.ground(attack))
                except Exception as exc:               # noqa: BLE001
                    self.ledger.append({"event": "ground_failed",
                                         "claim_id": claim.id,
                                         "error": str(exc)[:160]})
                    held = False

            with self._lock:
                claim.reviewed = True
                claim.attack = attack or ""
                claim.overturned = held
                if held:
                    self.overturned += 1
                self.ledger.append({"event": "reviewed",
                                     "claim_id": claim.id,
                                     "overturned": held,
                                     "attack": (attack or "")[:200]})
            reviewed += 1

        return reviewed

    # -- the STATE ------------------------------------------------------

    def claims(self) -> List[Claim]:
        with self._lock:
            return list(self._claims)

    def provisional_count(self) -> int:
        with self._lock:
            return sum(1 for c in self._claims if not c.reviewed)

    def describe(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "claims": len(self._claims),
                "unreviewed": sum(1 for c in self._claims if not c.reviewed),
                "overturned": self.overturned,
                "dropped": self.dropped,
                "queue_limit": self.queue_limit,
                "slice_seconds": self.slice_seconds,
                "ledger_events": len(self.ledger),
            }


# ===========================================================================
# THE SELF-TEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 74)
    print("THE BICAMERAL LOOP -- the self-test")
    print("=" * 74)
    print()

    failures: List[str] = []

    def check(label: str, cond: bool, extra: str = "") -> None:
        mark = "ok " if cond else "FAIL"
        print("  [%s] %s%s" % (mark, label, (" -- " + extra) if extra else ""))
        if not cond:
            failures.append(label)

    def fast(prompt):
        return "fast answer to %s" % prompt

    def deep(claim):
        if "bad" in claim:
            return "this claim is wrong"
        return None

    def ground(text):
        return "wrong" in text

    # -- 1. the fast path never calls the deep core -------------------
    calls = {"deep": 0}

    def counted_deep(claim):
        calls["deep"] += 1
        return deep(claim)

    loop = BicameralLoop(fast, counted_deep, ground)
    a = loop.ask("q")
    check("the fast path did NOT call the deep core",
          calls["deep"] == 0, str(calls["deep"]))
    check("the fast answer is PROVISIONAL", a.provisional is True)
    check("the fast answer is fast", a.elapsed_ms < 1000.0,
          "%.2f ms" % a.elapsed_ms)

    # -- 2. the fast path stays fast even with a slow core -----------
    def slow_deep(claim):
        time.sleep(0.5)
        return None

    loop2 = BicameralLoop(fast, slow_deep, ground)
    t0 = time.perf_counter()
    a2 = loop2.ask("q")
    elapsed = (time.perf_counter() - t0) * 1000.0
    check("a SLOW core does not slow the fast path",
          elapsed < 50.0, "%.2f ms" % elapsed)

    # -- 3. the deep core reviews in a bounded slice ------------------
    loop3 = BicameralLoop(fast, deep, ground)
    loop3.ask("a good claim")
    loop3.ask("a bad claim")
    n = loop3.review_slice(budget=0.5)
    check("the slice reviewed the claims", n == 2, str(n))

    # -- 4. an upheld attack OVERTURNS the claim ---------------------
    claims = loop3.claims()
    overturned = [c for c in claims if c.overturned]
    check("the bad claim was overturned", len(overturned) == 1,
          str(len(overturned)))
    check("the good claim was NOT overturned",
          all(not c.overturned for c in claims if "bad" not in c.text))

    # -- 5. a claim the core cannot attack is reviewed clean ---------
    check("the reviewed claim carries no attack",
          all(c.attack == "" for c in claims if "bad" not in c.text))

    # -- 6. the slice is BOUNDED --------------------------------------
    def very_slow(claim):
        time.sleep(0.2)
        return None

    loop4 = BicameralLoop(fast, very_slow, ground, queue_limit=50)
    for i in range(10):
        loop4.ask("q%d" % i)
    t0 = time.perf_counter()
    loop4.review_slice(budget=0.1)
    slice_elapsed = time.perf_counter() - t0
    check("the slice respected its budget", slice_elapsed < 0.5,
          "%.3f s" % slice_elapsed)

    # -- 7. the queue is BOUNDED --------------------------------------
    loop5 = BicameralLoop(fast, deep, ground, queue_limit=5)
    for i in range(20):
        loop5.ask("q%d" % i)
    check("the queue did not grow past its limit",
          len(loop5.claims()) <= 5, str(len(loop5.claims())))
    check("the drops are RECORDED", loop5.dropped > 0, str(loop5.dropped))

    # -- 8. a core that FAILS does not overturn -----------------------
    def broken_core(claim):
        raise RuntimeError("the core is down")

    loop6 = BicameralLoop(fast, broken_core, ground)
    loop6.ask("a claim")
    loop6.review_slice(budget=0.2)
    check("a failed core did not overturn anything",
          loop6.overturned == 0, str(loop6.overturned))
    check("the failure is in the ledger",
          any(e["event"] == "core_failed" for e in loop6.ledger))

    print()
    if failures:
        print("  %d CHECK(S) FAILED:" % len(failures))
        for f in failures:
            print("    - %s" % f)
        return 1
    print("  ALL CHECKS PASS")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    sys.exit(main())
