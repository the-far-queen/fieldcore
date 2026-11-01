"""
population_escalation.py -- THE ESCALATION POLICY, POPULATION FIRST.

Bobby, 2026-11-01, twice:
  *"nope we got as far as increasng number of stalks ie population was
  cheaper at 1 bit and only the 4 and 8 bit then increase pop again not
  16 32 64 etc"*
  *"no grow pop at 1 bit first"*

**SO THE POLICY IS NOT A LADDER UP TO 256. IT IS THIS:**

        1 bit     ONE stalk in view. The population as it is.
                  AND THE FIRST MOVE IS TO GROW THE POPULATION -- bring
                  MORE STALKS into view -- WHILE STAYING AT 1 BIT.
        4 bits    only if the population cannot read it at 1 bit.
        8 bits    only if 4 bits cannot either.
        and past 8 bits: POPULATION AGAIN, never a wider word.

**AND THE REASON IS THE COST.** A wider answer costs more compute per
exchange. More stalks in view cost the CHANNEL, not the answer. So the
cheap move is always more population, and the width is the LAST resort.
That is the 747 lesson applied to the channel: the overwhelming majority
of exchanges must not leave the cheap layer.

**AND THE COST PROPERTY IS WHAT THE INSTRUMENT MUST REPORT.** For every
escalation:

        the width that was NEEDED   -- derived from the channel
        the width that was USED    -- the policy's answer
        the POPULATION that was USED -- and how many stalks were added
        the escalation reason       -- why it went up, or why it stopped

A system that escalates the WIDTH on every exchange is not saving
compute. A system that never escalates is not reading anything hard.
**The measurement is the distribution, not the mean.**

**AND THE POLICY IS A SEPARATE MODULE, not an edit to the link.** The
link's `exchange()` decides one exchange. The policy decides what to
TRY NEXT, and it is the thing that must be measured -- so it is
measured on its own, and the link keeps its own behaviour.

Run:
    python src/population_escalation.py --selftest
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "Escalation",
    "PopulationPolicy",
    "POPULATION_FIRST_WIDTHS",
]

#: The widths the policy is allowed to use, IN ORDER.
#:
#: AND IT STOPS AT 8, and that is the correction. MEASURED against the
#: width ladder in `interstalk_link.py`, which runs 1, 4, 8, 16, 32, 64,
#: 128, 256. **The policy does not use the upper rungs**, because past 8
#: bits the answer changes KIND -- and the project's own rule is that
#: the answer's width is the AREA OF AUTHORITY, so a wider word past the
#: point where the population can carry it is authority nobody can
#: check.
POPULATION_FIRST_WIDTHS: Tuple[int, ...] = (1, 4, 8)

#: The escalation reasons. And THEY ARE THE POINT, because the reason
#: is what a reader of the ledger sees.
GROW_POPULATION = "grow_population"
WIDEN = "widen"
RESOLVED = "resolved"
STOPPED = "stopped"


@dataclass
class Escalation:
    """What the policy decided, and what it cost.

    **AND THE POPULATION IS RECORDED, not just the width.** Because the
    whole point of this policy is that the population is the thing that
    moves first -- so a ledger that only recorded the width would
    report "nothing escalated" for a system that was quietly growing
    its population on every exchange.
    """

    #: The width the channel needed.
    width_needed: int
    #: The width the policy used.
    width_used: int
    #: How many stalks were in view.
    population_before: int
    #: How many stalks the policy brought in.
    population_after: int
    #: Why.
    reason: str
    #: Did the reading succeed at this setting?
    resolved: bool = False

    @property
    def grew_population(self) -> bool:
        return self.population_after > self.population_before

    @property
    def widened(self) -> bool:
        return self.width_used > self.width_needed

    def describe(self) -> Dict[str, Any]:
        return {
            "width_needed": self.width_needed,
            "width_used": self.width_used,
            "population_before": self.population_before,
            "population_after": self.population_after,
            "reason": self.reason,
            "resolved": self.resolved,
            "grew_population": self.grew_population,
            "widened": self.widened,
        }


@dataclass
class PopulationPolicy:
    """The population-first escalation policy.

    `width_for_taps` is the link's own function, injected so the policy
    derives the width the same way the link does -- and so the policy
    cannot drift from it.

    **AND THE ORDER OF THE TWO MOVES IS THE WHOLE POLICY:**

        1. if the reading succeeded, STOP. Nothing is escalated.
        2. otherwise, GROW THE POPULATION first -- while staying at the
           same width.
        3. only if the population cannot grow further, WIDEN -- to the
           next width, and only up to 8.
        4. if neither is possible, STOP with a reason. And a stop is a
           DECISION, not a limitation.
    """

    #: The link's width derivation. Injected.
    width_for_taps: Any = None
    #: How many stalks to add per population step.
    population_step: int = 1
    #: The maximum population the caller will bring into view.
    max_population: int = 16

    def decide(self, channel_taps: int, population: int,
               readable: bool, max_population: Optional[int] = None) -> Escalation:
        """Decide what to do about one unreadable exchange.

        `readable` is whether the reading succeeded at the current
        setting -- and THAT is the input the policy acts on, not the
        width.
        """
        cap = self.max_population if max_population is None else max_population
        needed = self._width(channel_taps)

        if readable:
            return Escalation(width_needed=needed, width_used=needed,
                              population_before=population,
                              population_after=population,
                              reason=RESOLVED, resolved=True)

        # 1. GROW THE POPULATION FIRST.
        if population + self.population_step <= cap:
            return Escalation(
                width_needed=needed, width_used=needed,
                population_before=population,
                population_after=population + self.population_step,
                reason=GROW_POPULATION)

        # 2. ONLY THEN WIDEN -- and only to 8.
        idx = POPULATION_FIRST_WIDTHS.index(needed) \
            if needed in POPULATION_FIRST_WIDTHS else None
        if idx is not None and idx + 1 < len(POPULATION_FIRST_WIDTHS):
            nxt = POPULATION_FIRST_WIDTHS[idx + 1]
            return Escalation(
                width_needed=needed, width_used=nxt,
                population_before=population, population_after=population,
                reason=WIDEN)

        # 3. STOPPED. And a stop is a DECISION.
        return Escalation(width_needed=needed, width_used=needed,
                          population_before=population,
                          population_after=population,
                          reason=STOPPED)

    def _width(self, channel_taps: int) -> int:
        if self.width_for_taps is None:
            return 1 if channel_taps <= 1 else (4 if channel_taps <= 2 else 8)
        return int(self.width_for_taps(channel_taps))

    # -- the ledger -----------------------------------------------------

    def plan(self, channel_taps: int, population: int,
             readable: bool, max_population: Optional[int] = None
             ) -> List[Escalation]:
        """The whole escalation SEQUENCE for one exchange: what to try,
        in order, until it resolves or stops.

        **AND THIS IS THE PART THE LINK LACKS.** The link's `exchange()`
        computes ONE escalation and returns it. A caller wanting to know
        what the system would do next has to run the exchange again
        with the new setting. So the sequence is made explicit here, and
        it is the sequence the policy means.
        """
        out: List[Escalation] = []
        taps = channel_taps
        pop = population
        for _ in range(16):          # a bound, so it terminates
            esc = self.decide(taps, pop, readable,
                              max_population=max_population)
            out.append(esc)
            if esc.resolved or esc.reason == STOPPED:
                break
            if esc.grew_population:
                pop = esc.population_after
                # MORE STALKS IN VIEW MEANS MORE TAPS, so the width the
                # channel NEEDS grows with the population -- and that is
                # the whole point: the population carries the width.
                taps = taps + self.population_step
            else:
                taps = taps + 1
                readable = False
        return out


# ===========================================================================
# THE SELF-TEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 74)
    print("THE POPULATION-FIRST ESCALATION -- the self-test")
    print("=" * 74)
    print()

    failures: List[str] = []

    def check(label, cond, extra=""):
        mark = "ok " if cond else "FAIL"
        print("  [%s] %s%s" % (mark, label, (" -- " + extra) if extra else ""))
        if not cond:
            failures.append(label)

    def link_width(taps):
        return 1 if taps <= 1 else (4 if taps <= 2 else 8)

    pol = PopulationPolicy(width_for_taps=link_width,
                           population_step=1, max_population=4)

    # -- 1. a readable exchange ESCALATES NOTHING -----------------------
    e = pol.decide(1, 1, readable=True)
    check("a readable exchange stops at 1 bit",
          e.width_used == 1 and e.population_after == 1, e.describe().__str__())
    check("a readable exchange is RESOLVED", e.resolved is True)

    # -- 2. an unreadable exchange GROWS THE POPULATION FIRST -----------
    e2 = pol.decide(1, 1, readable=False)
    check("an unreadable exchange grows the POPULATION first",
          e2.grew_population and not e2.widened, e2.describe().__str__())
    check("and it stays at 1 BIT", e2.width_used == 1, str(e2.width_used))
    check("the reason says so", e2.reason == GROW_POPULATION, e2.reason)

    # -- 3. it does NOT widen while the population can still grow -------
    e3 = pol.decide(1, 3, readable=False)
    check("it still grows the population at 3 of 4",
          e3.grew_population and e3.width_used == 1, e3.describe().__str__())

    # -- 4. only when the population is spent does it widen -----------
    e4 = pol.decide(1, 4, readable=False)
    check("at the population cap it WIDENS", e4.widened, e4.describe().__str__())
    check("and it widens to 4 bits", e4.width_used == 4, str(e4.width_used))
    check("and the reason says so", e4.reason == WIDEN, e4.reason)

    # -- 5. and it NEVER goes past 8 bits ------------------------------
    e5 = pol.decide(3, 4, readable=False)
    check("it never widens past 8 bits",
          e5.width_used in (1, 4, 8) and e5.width_used <= 8,
          str(e5.width_used))
    check("the policy's widths stop at 8",
          POPULATION_FIRST_WIDTHS[-1] == 8, str(POPULATION_FIRST_WIDTHS))

    # -- 6. when nothing is left it STOPS, with a reason --------------
    e6 = pol.decide(5, 4, readable=False)
    check("it stops when nothing is left", e6.reason == STOPPED,
          e6.reason)
    check("and a stop is not a widening",
          e6.width_used == e6.width_needed, e6.describe().__str__())

    # -- 7. the SEQUENCE, which is the part the link lacks -------------
    seq = pol.plan(1, 1, readable=False)
    print("     the sequence from 1 stalk at 1 bit:")
    for x in seq:
        print("       %-16s pop %d->%d  width %d->%d  %s"
              % (x.reason, x.population_before, x.population_after,
                 x.width_needed, x.width_used,
                 "RESOLVED" if x.resolved else ""))
    check("the sequence grows the population BEFORE widening",
          [x.reason for x in seq][:3] == [GROW_POPULATION] * 3,
          str([x.reason for x in seq]))
    check("the sequence terminates", len(seq) < 16, str(len(seq)))

    # -- 8. a readable exchange produces a ONE-STEP sequence -----------
    seq2 = pol.plan(1, 1, readable=True)
    check("a readable exchange is a one-step sequence",
          len(seq2) == 1 and seq2[0].resolved, str(len(seq2)))

    # -- 9. the ledger shape -------------------------------------------
    check("the escalation describes itself",
          set(e.describe()) >= {"width_needed", "width_used",
                                "population_before", "population_after",
                                "reason", "resolved"})
    check("and it is JSON-serialisable",
          json.dumps(e.describe()) is not None)

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
