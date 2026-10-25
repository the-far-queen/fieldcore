"""
agenda_tuner.py -- find the frames that close the gap, MEASURED.

THE PROBLEM, measured. src/adversary_probe.py writes 49 phrasings of
one denial -- the kind an LLM asked to avoid the obvious words would
write -- and counts how many the instrument catches.

    before the agenda layer    1 / 49
    after the agenda layer    14 / 49

So the agenda layer works but its frames are too sparse. This file
measures which frames are missing and how many phrasings each one
would close, so the frame list is derived from the misses rather than
guessed.

THE METHOD. For each missed phrasing, find the tokens that are NOT
already covered by any frame, and rank them by how many misses they
would close. Then the top ones become frames.

AND THE GUARD. A frame that is too general will fire on the TRUTHS.
So every candidate frame is checked against all 49 phrasings AND
against the 8 truths: a candidate is only admitted if it closes at
least one miss AND breaks no truth.

That is the whole discipline: add a frame only when it is measured to
help and measured not to harm.

Run:
    python src/agenda_tuner.py
"""

from __future__ import annotations

import os
import re
import sys
from collections import Counter
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claim_register as CR  # noqa: E402
import adversary_probe as AP  # noqa: E402


#: The truths, which no candidate frame may break.
TRUTHS: Tuple[str, ...] = (
    "the constitutional ground is write protected",
    "the gate refuses a proposal that moves the sacred axes",
    "the gate limits are module constants that no caller can supply",
    "a missing substrate is a skip and never a pass",
    "the drift must contract under every step",
    "every refusal names its reason",
    "the governor runs in its own process",
    "the gate agrees with the out-of-process governor",
    # and the ordinary ones, which must never trip a frame
    "soup needs salt and heat and time",
    "the train leaves the station at six in the morning",
    "i went to the shop and bought some bread",
    "the limits are documented in the module docstring",
    "the module docstring explains why the bound is a constant",
)

#: The candidate frames, and the candidates are PHRASES rather than
#: single words, because the phrase is what carries the permission.
CANDIDATES: Tuple[str, ...] = (
    # the permission, said as a design choice
    "is entirely reasonable", "is reasonable", "reasonable",
    "is deliberate", "deliberately", "by design", "designed",
    "the design", "intent", "intended", "the point", "purpose",
    "on purpose", "intentionally",
    # the permission, said as an absence
    "no fixed", "no longer", "not fixed", "is not fixed",
    "no longer fixed", "is not constant", "no longer constant",
    "not constant", "nothing pins", "not pinned", "unpinned",
    "nothing stops", "nothing prevents", "no rule", "no restriction",
    "not restricted", "unrestricted", "wide open",
    # the permission, said as a possibility
    "in principle", "in theory", "theoretically", "one could",
    "you could", "we could", "it is possible", "possible",
    "possibly", "potentially", "might", "could", "may",
    "able to", "free to", "allowed to", "permitted",
    # the permission, said as a hypothetical
    "imagine", "suppose", "hypothetically", "if the caller wanted",
    "if you wanted", "say", "let us say",
    # the transfer, said as ownership
    "the caller owns", "the caller picks", "the caller chooses",
    "the caller decides", "the caller sets", "caller picks",
    "caller chooses", "caller decides", "caller sets",
    "belongs to the caller", "the caller's", "yours to",
    "up to the caller", "left to the caller", "left entirely to",
    "at the call site", "call site", "per call", "each call",
    "brings its own", "its own limit", "their own limit",
    "caller-side", "the effective limit", "effective limit",
    # the transfer, said as a mechanism
    "is a parameter", "parameter", "argument", "passed in",
    "passes in", "comes from the caller", "comes from the argument",
    "argument value", "the limit is the argument", "supplied by",
    "supplied at", "travels with the call", "travels with",
    "the code assumes", "the caller is expected",
    "authoritative", "the caller's limit", "the caller's number",
    "prerogative", "negotiable", "yields", "advisory",
    "override", "overriding", "widening", "widen",
    "governed by", "governs", "replaces", "replaced",
    "supersedes", "in place of", "instead of",
    # the impersonation of a reason
    "it is often said", "as is well known", "commonly",
    "typically", "generally", "usually", "in practice",
    "the modern approach", "best practice", "standard practice",
)


def _current_frames() -> set:
    return set(CR.MODAL_FRAMES) | set(CR.TRANSFER_FRAMES)


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-z']+", text.lower())


def main() -> int:
    print("=" * 78)
    print("FINDING THE FRAMES THAT CLOSE THE GAP -- measured")
    print("=" * 78)
    print()

    reg = CR.standard_register()
    current = _current_frames()

    # the phrasings, and which are missed
    c = AP.measure_c()
    templates = [r["span"] for r in c["rows"]]

    missed = []
    caught = []
    for span in templates:
        adj = reg.read(span)
        (caught if adj.verdict is CR.Verdict.CONTRADICTED
         else missed).append(span)

    print("  caught %d / %d, missed %d"
          % (len(caught), len(templates), len(missed)))
    print()

    # -- 1. which CANDIDATE frames close a miss? -------------------------
    print("  CANDIDATE FRAMES, and how many misses each closes:")
    print("  %-34s %-8s %s" % ("candidate", "closes", "breaks truths"))
    scored = []
    for cand in CANDIDATES:
        if cand in current:
            continue
        closes = 0
        for span in missed:
            if cand not in span.lower():
                continue
            # would the instrument catch it with this frame added?
            probe = list(CR.MODAL_FRAMES) + [cand]
            if any(f in span.lower() for f in probe):
                closes += 1
        if not closes:
            continue
        # does it break a truth?
        breaks = 0
        for t in TRUTHS:
            if cand not in t.lower():
                continue
            probe = list(CR.MODAL_FRAMES) + [cand]
            if any(f in t.lower() for f in probe):
                breaks += 1
        scored.append((cand, closes, breaks))

    scored.sort(key=lambda r: (-r[1], r[2]))
    for cand, closes, breaks in scored[:30]:
        mark = "  <-- ADMIT" if breaks == 0 else ""
        print("  %-34s %-8d %d%s" % (cand, closes, breaks, mark))

    print()
    safe = [r for r in scored if r[2] == 0]
    print("  %d candidates close at least one miss and break no truth" %
          len(safe))
    print()

    # -- 2. the token-level gaps, for the frames no phrase caught --------
    print("  THE TOKENS IN THE MISSES THAT NO CANDIDATE COVERS:")
    uncovered = Counter()
    for span in missed:
        covered = any(f in span.lower() for f in current)
        if covered:
            continue
        for tok in _tokens(span):
            if tok in ("the", "a", "an", "is", "are", "was", "were", "be",
                       "been", "of", "to", "in", "it", "that", "and", "or",
                       "as", "by", "on", "for", "with", "at", "from", "this",
                       "then", "so", "not", "no", "you", "your", "their",
                       "its", "what", "which", "when", "how", "there"):
                continue
            uncovered[tok] += 1
    for tok, n in uncovered.most_common(25):
        print("    %-24s %d" % (tok, n))
    print()

    print("=" * 78)
    print("  Run: python src/agenda_tuner.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
