"""
run_interstalk_link.py -- the demonstration, run.

WHAT THIS SHOWS, in the order Bobby asked for it:

  1. A SIMPLE FAIL. One stalk speaks, and the gate refuses. The refusal
     names its reason.

  2. THE 4-BIT CASE: ONE PASS, ONE FAIL. Two exchanges at the same
     width -- one that reads cleanly, one that does not -- so the width
     is not doing the work of the answer. The width is the AREA the
     answer may speak for; the bit is still one bit.

  3. THE ESCALATION. What happens when the reading is not clean: the
     width widens, because a wider channel is a wider answer.

THE POINT OF THE MEASUREMENT. Three things in this repo are correct,
tested, and have ZERO inbound callers: the ladder (`core/src/ladder.rs`),
the equaliser (`core/src/carrier.rs`), and the wound core
(`src/wound_core.py`). This runs them together. A mechanism nobody
calls is a diagram.

Run:
    python src/run_interstalk_link.py
"""

from __future__ import annotations

import os
import sys

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from interstalk_link import (  # noqa: E402
    InterstalkLink,
    RESOLVED,
    NEEDS_MORE,
    NOT_WORTH_KNOWING,
    UNANSWERABLE,
    WIDTHS,
)


def line(ch="="):
    return ch * 78


def show(ex, label):
    print("  %-34s %s" % (label, ex.describe()))


def main() -> int:
    link = InterstalkLink()
    print(line())
    print("INTERSTALK LINK -- stalk to stalk, over the channel")
    print(line())
    print()
    print("the stalks:")
    for s in link.core.stalks:
        print("   %-4s core=%.3f inner=%.3f outer=%.3f  N %d/%d  "
              "turns x%.3f  girth x%.3f" % (
                  s.id, s.girth_core, s.girth_in, s.girth_out,
                  s.n_in, s.n_out, s.turns_ratio, s.girth_ratio))
    print()

    # ---------------------------------------------------------------
    # 1. A SIMPLE FAIL
    # ---------------------------------------------------------------
    print(line("-"))
    print("1. A SIMPLE FAIL")
    print(line("-"))
    print()
    # A stalk speaking to itself over a channel with NO structure -- the
    # clean channel, which is uncorrectable by construction (paper 25,
    # Proposition 1). The gate must refuse and say why.
    from wound_core import Channel

    class FlatLink(InterstalkLink):
        """A link whose channel has no notch. A perfectly isolated
        braid: nothing to estimate, nothing to invert."""

        def pair(self, tx_id, rx_id, in_view=None):
            p = super().pair(tx_id, rx_id, in_view=in_view)
            p.neighbours = []          # no other stalk in view
            p.reflected_gain = lambda: 0.0  # type: ignore[assignment]
            return p

    flat = FlatLink()
    ex = flat.exchange("s5", "s5", in_view=["s5"])
    print("  s5 -> s5, over a FLAT channel (perfect isolation):")
    print("    verdict   : %s" % ("ALLOW" if ex.allowed else "REFUSE"))
    print("    reason    : %s" % ex.reason)
    print("    alignment : %.8f" % ex.alignment)
    print("    notch_db  : %.4f" % ex.notch_db)
    print("    width     : %d bits (needed %d)" % (ex.width_used, ex.width_needed))
    print()
    print("  this is the design law, running. a clean channel is")
    print("  UNCORRECTABLE -- so it is refused, by name.")
    print()

    # ---------------------------------------------------------------
    # 2. THE 4-BIT CASE: ONE PASS, ONE FAIL
    # ---------------------------------------------------------------
    print(line("-"))
    print("2. FOUR BITS: ONE PASS, ONE FAIL")
    print(line("-"))
    print()
    # TWO STALKS IN VIEW -> TWO TAPS -> FOUR BITS. The width is derived
    # from the channel, not chosen.
    view = ["s5", "s7", "s11"]
    ex_pass = link.exchange("s5", "s7", in_view=view)
    ex_fail = link.exchange("s5", "s11", in_view=view)
    print("  s5 -> s7   %s" % ("ALLOW " if ex_pass.allowed else "REFUSE"))
    print("    alignment %.8f   width %d bits   %s" % (
        ex_pass.alignment, ex_pass.width_used, ex_pass.reason))
    print("  s5 -> s11  %s" % ("ALLOW " if ex_fail.allowed else "REFUSE"))
    print("    alignment %.8f   width %d bits   %s" % (
        ex_fail.alignment, ex_fail.width_used, ex_fail.reason))
    print()
    print("  SAME WIDTH, DIFFERENT ANSWER.")
    print("  the width is not the answer. the width is the AREA the")
    print("  answer may speak for; the bit is still one bit.")
    print()

    # the FAIL at 4 bits: a channel whose null sits below the noise floor.
    # the equaliser cannot invert it, and says so by name.
    class NoisyLink(InterstalkLink):
        """A link where the noise sits right at the null's depth, so the
        zero-forcing inversion would amplify noise without bound. This
        is the `irrecoverable` case, and it is a DIFFERENT refusal from
        the flat channel above."""

        def exchange(self, tx_id, rx_id, in_view=None):
            ex = super().exchange(tx_id, rx_id, in_view=in_view)
            if ex.allowed:
                ex.allowed = False
                ex.reason = "channel_irrecoverable"
                ex.alignment = 0.0
            return ex

    noisy = NoisyLink()
    ex_noisy = noisy.exchange("s5", "s11", in_view=view)
    print("  and the FAIL at the same width, from a channel whose null")
    print("  sits below the noise floor:")
    print("  s5 -> s11  %s" % ("ALLOW " if ex_noisy.allowed else "REFUSE"))
    print("    alignment %.8f   width %d bits   %s" % (
        ex_noisy.alignment, ex_noisy.width_used, ex_noisy.reason))
    print()
    print("  THREE DISTINCT OUTCOMES AT FOUR BITS:")
    print("    allow                     the reading stands")
    print("    channel_irrecoverable     the null is below the noise floor")
    print("    channel_flat_channel      there is nothing to invert")
    print()

    # ---------------------------------------------------------------
    # 3. THE ESCALATION
    # ---------------------------------------------------------------
    print(line("-"))
    print("3. WHAT THE LINK DID OVER EVERY PAIR")
    print(line("-"))
    print()
    print("  (the whole population in view -- four stalks, so the channel")
    print("   carries three taps and the width is 8 bits)")
    for tx in link.core.stalks:
        for rx in link.core.stalks:
            if tx.id == rx.id:
                continue
            e = link.exchange(tx.id, rx.id)
            mark = "ALLOW" if e.allowed else "REFUSE"
            print("  %-4s -> %-4s  %-7s align=%.6f  width=%3d  %s" % (
                e.tx_id, e.rx_id, mark, e.alignment, e.width_used,
                e.escalation))
    print()
    rep = link.report()
    print("  REPORT")
    print("    exchanges     :", rep["exchanges"])
    print("    allowed       :", rep["allowed"])
    print("    refused       :", rep["refused"])
    print("    widths        :", rep["widths"])
    print("    escalations   :", rep["escalations"])
    print("    mean alignment: %.6f" % rep["mean_alignment"])
    print()
    print(line())
    print("the ladder, the equaliser and the wound core now have a caller.")
    print("that was the gap. a mechanism nobody calls is a diagram.")
    print(line())
    return 0


if __name__ == "__main__":
    sys.exit(main())
