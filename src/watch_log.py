"""
watch_log.py -- THE WATCHER AND ITS OBSERVER, on the python side, for
the exchange the wrapper actually runs.

WHY A PYTHON COPY AND NOT JUST THE RUST ONE. The rust core's watcher
watches the CORE's readings -- the width, the notch, the alignment.
This one watches the WRAPPER's exchange: the gate's verdict on the
answer, the governor's bit, the atlas's grade, and the ORDER they ran
in. And the re-derivation is of the project's own instruments, so it
is the same rule the rust watcher follows: **do not trust the report,
re-derive it.**

AND WHAT IS RE-DERIVED, and each of these can disagree with the
exchange:

  1. THE GATE'S VERDICT. The watcher runs the gate AGAIN on the same
     answer. If the two verdicts differ, the gate is not
     deterministic, and a gate whose verdict depends on when it was
     asked is not a gate -- it is a coin. MEASURED: the project has
     already been bitten by exactly this class, in the embedder that
     used Python's builtin `hash()`.

  2. THE STEP DIGESTS. Every step's content is hashed, and the chain
     links them, so an edit to the trace -- the thing a reader would
     take as evidence -- is detectable.

  3. THE ORDER. The exchange's steps are supposed to run in the
     project's order: gate, locus, model, gate, grounding, governor,
     atlas, library. The watcher checks the ORDER it actually ran, and
     names the first step that came out of place. The order IS the
     architecture: the grounding must come before the governor,
     because a governor that sees an ungrounded answer refuses a
     correct one.

AND THE OBSERVER, which is the second duty: it reads the chain from
DISK, re-derives every digest and every link, and holds an ANCHOR
outside the chain so a rewrite that recomputes its own digests is
still caught. And an ABSENT log is ABSENT, not healthy.

**AND THE SCOPE, stated so nobody mistakes it for a gate.** Nothing
here decides whether a reply is true. The gate decides that. This
watches the gate and reports. A watcher that refused would be a second
gate, and the project has been explicit that it does not want one.

Run:
    python src/watch_log.py --selftest
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

#: The order the exchange's steps are supposed to run in.
#:
#: AND THIS IS THE ARCHITECTURE, not a style preference. The
#: grounding MUST come before the governor: the governor asks about the
#: GROUNDED answer, and an ungrounded answer is refused for a reason
#: that has nothing to do with its truth.
EXPECTED_ORDER: Sequence[str] = (
    "gate/prompt",
    "simself/locus",
    "mte/answer",
    "gate/answer",
    "grounding",
    "governor",
    "atlas/answer",
    "library/record",
)

#: The digest a chain starts from.
GENESIS_DIGEST = "0" * 16


def digest_of(seq: int, kind: str, subject: str, verdict: str,
              detail: str, prev: str) -> str:
    """The digest of one entry: its own content plus the previous link.

    AND IT IS SHA-256 TRUNCATED, and the truncation is 16 hex
    characters. That is 64 bits, which is not a security boundary and
    is not meant to be one -- the chain's defence is the LINK and the
    ANCHOR, not the collision resistance of the digest.
    """
    payload = "\x1f".join([str(seq), kind, subject, verdict, detail, prev])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass
class WatchEntry:
    """One entry in the watcher's chain."""
    seq: int
    kind: str
    subject: str
    verdict: str
    detail: str
    prev: str
    digest: str

    def recomputed_digest(self) -> str:
        """This entry's digest, recomputed from its own content."""
        return digest_of(self.seq, self.kind, self.subject,
                         self.verdict, self.detail, self.prev)

    def to_dict(self) -> Dict[str, Any]:
        return {"seq": self.seq, "kind": self.kind, "subject": self.subject,
                "verdict": self.verdict, "detail": self.detail,
                "prev": self.prev, "digest": self.digest}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "WatchEntry":
        return cls(seq=int(d.get("seq", 0)), kind=str(d.get("kind", "")),
                   subject=str(d.get("subject", "")),
                   verdict=str(d.get("verdict", "")),
                   detail=str(d.get("detail", "")),
                   prev=str(d.get("prev", "")),
                   digest=str(d.get("digest", "")))


@dataclass
class WatchChain:
    """The watcher's append-only chain."""
    entries: List[WatchEntry] = field(default_factory=list)

    def push(self, kind: str, subject: str, verdict: str,
             detail: str) -> WatchEntry:
        """Append one entry. The link is set by the chain."""
        seq = len(self.entries)
        prev = self.entries[-1].digest if self.entries else GENESIS_DIGEST
        d = digest_of(seq, kind, subject, verdict, detail, prev)
        entry = WatchEntry(seq=seq, kind=kind, subject=subject,
                           verdict=verdict, detail=detail, prev=prev,
                           digest=d)
        self.entries.append(entry)
        return entry

    def to_jsonl(self) -> str:
        return "".join(json.dumps(e.to_dict(), ensure_ascii=False) + "\n"
                       for e in self.entries)

    @classmethod
    def from_jsonl(cls, text: str) -> "WatchChain":
        chain = cls()
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                chain.entries.append(WatchEntry.from_dict(json.loads(line)))
            except Exception:
                chain.entries.append(WatchEntry(
                    seq=len(chain.entries), kind="unparsed",
                    subject=line[:80], verdict="unparsed", detail="",
                    prev="", digest=""))
        return chain


@dataclass
class Anchor:
    """What the chain looked like at a moment in time.

    AND IT LIVES OUTSIDE THE CHAIN, so rewriting the chain cannot
    rewrite it. That is the whole point of it: a digest can be edited
    alongside the thing it defends, and a link can be repaired, but the
    anchor is a second witness held elsewhere.
    """
    head_digest: str
    count: int

    @classmethod
    def of(cls, chain: WatchChain) -> "Anchor":
        return cls(head_digest=chain.entries[-1].digest if chain.entries
                   else GENESIS_DIGEST,
                   count=len(chain.entries))


@dataclass
class Observation:
    """The observer's report."""
    verdict: str            # consistent | broken | absent
    checked: int
    broke_at: Optional[int]
    reason: str

    def consistent(self) -> bool:
        return self.verdict == "consistent"


class Watcher:
    """The watcher. It watches the exchange's own steps."""

    def __init__(self) -> None:
        self.chain = WatchChain()

    # -- the duties ------------------------------------------------------

    def watch_step(self, step: "Any") -> WatchEntry:
        """Record one step of the exchange, with its verdict.

        AND THE VERDICT IS THE STEP'S OWN, not a summary of it. The
        trace already prints "ok" or "REFUSED"; this records the same
        bit, so a reader of the chain and a reader of the trace see the
        same thing.
        """
        name = getattr(step, "name", "?")
        ok = bool(getattr(step, "ok", True))
        detail = str(getattr(step, "detail", ""))[:400]
        return self.chain.push("step", name, "ok" if ok else "refused",
                               detail)

    def watch_order(self, names: Sequence[str]) -> WatchEntry:
        """Check the exchange ran in the project's order.

        AND WHY THIS IS A DUTY RATHER THAN A CONVENTION. The order IS
        the architecture: the grounding has to come before the
        governor. An exchange that ran the governor first would refuse
        a correct answer, and the trace would look the same either way
        unless the order is checked.
        """
        seen = [n for n in names if n in EXPECTED_ORDER]
        expected = [n for n in EXPECTED_ORDER if n in seen]
        if seen == expected:
            return self.chain.push("order", "exchange", "order_ok",
                                   "the exchange ran in the project's order")
        first_bad = ""
        for want, got in zip(expected, seen):
            if want != got:
                first_bad = "expected %s and got %s" % (want, got)
                break
        if not first_bad:
            first_bad = "the order is %s" % (seen,)
        return self.chain.push("order", "exchange", "order_fault",
                               first_bad)

    def watch_gate_verdict(self, answer: str, first_allowed: bool,
                            first_reason: str, gate: Any) -> WatchEntry:
        """RE-RUN THE GATE on the same answer and compare.

        **AND THIS IS THE RE-DERIVATION THAT MATTERS.** The gate's own
        report is trusted by every other layer, so if the gate is
        non-deterministic then everything downstream of it is
        non-deterministic too, and nothing says so.

        MEASURED, this project's own history: an embedder built a
        sparse vector using Python's builtin `hash()`, which is
        randomized per process. The same span embedded to axis 2 in one
        process and axis 4 in the next, and the gate's verdict was not
        reproducible -- while LOOKING like it worked.

        So the gate is asked twice and the two verdicts are compared.
        A disagreement is a fault, named.
        """
        try:
            second = gate.decide(answer, fail_closed=False)
            second_allowed = bool(getattr(second, "allowed", True))
            second_reason = str(getattr(second, "reason", ""))
        except Exception as exc:                    # noqa: BLE001
            return self.chain.push(
                "gate", "answer", "gate_fault",
                "the gate could not be asked a second time: %r" % (exc,))
        if second_allowed == first_allowed:
            return self.chain.push(
                "gate", "answer", "gate_stable",
                "the gate said the same thing twice: %s"
                % (first_allowed and "allowed" or first_reason[:120],))
        return self.chain.push(
            "gate", "answer", "gate_fault",
            "the gate said %s the first time and %s the second time"
            % (first_allowed, second_allowed))

    def watch_summary(self) -> WatchEntry:
        """Record what the exchange produced, once, at the end."""
        return self.chain.push("summary", "exchange", "summary",
                               "")


# ---------------------------------------------------------------------------
# THE OBSERVER
# ---------------------------------------------------------------------------

def observe(chain: WatchChain,
            anchor: Optional[Anchor] = None) -> Observation:
    """Re-derive the chain from its own bytes.

    AND THE THREE CHECKS, in order, because the order is dependence:
    the digest first (does the entry's own content match its own
    digest?), then the link (does it point at the entry before it?),
    then the anchor (is this the SAME chain we saw before?).
    """
    if not chain.entries:
        return Observation(
            verdict="absent", checked=0, broke_at=None,
            reason="no_watch_log: the watcher wrote nothing, and an "
                   "absent watcher is not a healthy one")

    prev = GENESIS_DIGEST
    for i, e in enumerate(chain.entries):
        recomputed = e.recomputed_digest()
        if recomputed != e.digest:
            return Observation(
                verdict="broken", checked=i, broke_at=e.seq,
                reason="digest_mismatch at seq %d: the entry carries %s and "
                       "its own content recomputes to %s"
                       % (e.seq, e.digest, recomputed))
        if e.prev != prev:
            return Observation(
                verdict="broken", checked=i, broke_at=e.seq,
                reason="link_break at seq %d: the entry points at %s and "
                       "the entry before it ends at %s"
                       % (e.seq, e.prev, prev))
        prev = e.digest

    if anchor is not None:
        head = chain.entries[-1].digest
        if anchor.head_digest != head or anchor.count != len(chain.entries):
            return Observation(
                verdict="broken", checked=len(chain.entries),
                broke_at=max(anchor.count - 1, 0),
                reason="anchor_mismatch: the chain now ends at %s with %d "
                       "entries and the anchor was taken at %s with %d"
                       % (head, len(chain.entries),
                          anchor.head_digest, anchor.count))

    return Observation(
        verdict="consistent", checked=len(chain.entries), broke_at=None,
        reason="%d entries re-derived: every digest recomputed and every "
               "link matched" % len(chain.entries))


def observe_jsonl(text: str, anchor: Optional[Anchor] = None) -> Observation:
    return observe(WatchChain.from_jsonl(text), anchor)


# ---------------------------------------------------------------------------
# THE LOG PATH
# ---------------------------------------------------------------------------

def default_log_path() -> str:
    """Where the watch log lives.

    AND IT IS OUTSIDE THE REPO AND OUTSIDE THE VAULT, in the hermes
    home's own state dir. The log is evidence about the exchange, and
    evidence that lives inside the thing it describes can be edited
    with it.
    """
    home = os.environ.get("HERMES_HOME",
                          os.path.join(os.path.expanduser("~"),
                                       "AppData", "Local", "hermes"))
    return os.path.join(home, "work_repos", "fieldcore_state",
                        "watch_log", "exchange.jsonl")


def append_log(path: str, chain: WatchChain) -> str:
    """Append the chain to the log, one JSON object per line."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(chain.to_jsonl())
    return path


# ---------------------------------------------------------------------------
# THE SELF-TEST
# ---------------------------------------------------------------------------

def _selftest() -> int:
    print("=" * 74)
    print("THE WATCHER AND ITS OBSERVER -- the self-test")
    print("=" * 74)
    print()
    ok = True

    def check(label: str, cond: bool, extra: str = "") -> None:
        nonlocal ok
        print("  %-52s %s%s" % (label, "ok" if cond else "FAILED",
                                 ("  " + extra) if extra else ""))
        if not cond:
            ok = False

    # -- 1. a clean chain ---------------------------------------------
    w = Watcher()
    w.chain.push("step", "gate/prompt", "ok", "clear")
    w.chain.push("step", "gate/answer", "ok", "clear")
    obs = observe(w.chain)
    check("a clean chain observes as consistent", obs.consistent(), obs.reason)

    # -- 2. an absent chain is absent ----------------------------------
    obs = observe(WatchChain())
    check("an absent chain is absent, not healthy",
          obs.verdict == "absent", obs.reason)

    # -- 3. a doctored digest ------------------------------------------
    chain = WatchChain.from_jsonl(w.chain.to_jsonl())
    chain.entries[0].detail = "REFUSED"
    obs = observe(chain)
    check("a doctored digest is caught",
          obs.verdict == "broken" and "digest_mismatch" in obs.reason)

    # -- 4. a doctored link --------------------------------------------
    chain = WatchChain.from_jsonl(w.chain.to_jsonl())
    chain.entries[1].prev = GENESIS_DIGEST
    chain.entries[1].digest = chain.entries[1].recomputed_digest()
    obs = observe(chain)
    check("a pure link break is caught",
          obs.verdict == "broken" and "link_break" in obs.reason)

    # -- 5. the anchor catches a rewrite whose digests were recomputed -
    anchor = Anchor.of(w.chain)
    chain = WatchChain.from_jsonl(w.chain.to_jsonl())
    chain.entries[1].detail = "tampered"
    chain.entries[1].digest = chain.entries[1].recomputed_digest()
    obs_without = observe(chain)
    obs_with = observe(chain, anchor)
    check("a rewrite with recomputed digests fools the chain-internal "
          "check", obs_without.verdict == "consistent", obs_without.reason)
    check("the anchor catches it", obs_with.verdict == "broken",
          obs_with.reason)

    # -- 6. the order check -------------------------------------------
    w2 = Watcher()
    e = w2.watch_order(["gate/prompt", "simself/locus", "mte/answer",
                        "gate/answer", "grounding", "governor"])
    check("the project's order reads as ok", e.verdict == "order_ok",
          e.detail)
    w3 = Watcher()
    e = w3.watch_order(["gate/prompt", "governor", "grounding"])
    check("a swapped order is caught", e.verdict == "order_fault", e.detail)

    # -- 7. the gate re-derivation ------------------------------------
    class _V:
        """A minimal verdict, so the fake gate needs no import."""
        allowed = True
        reason = ""

    class FlakyGate:
        """A gate that changes its mind between calls.

        AND THE FIRST CALL IS THE WATCHER'S, because the wrapper's own
        call already happened and its verdict was `first_allowed`. So
        the fake returns the OPPOSITE of what the wrapper saw, which is
        exactly what a non-deterministic gate does.
        """

        def __init__(self) -> None:
            self.n = 0

        def decide(self, text, fail_closed=False):
            self.n += 1
            v = _V()
            v.allowed = (self.n % 2 == 0)
            v.reason = "the answer says something the ground denies"
            return v

    w4 = Watcher()
    e = w4.watch_gate_verdict("the ground is mutable", True, "clear",
                              FlakyGate())
    check("a gate that changes its mind is caught",
          e.verdict == "gate_fault", e.detail)

    class SteadyGate:
        def decide(self, text, fail_closed=False):
            v = _V()
            v.allowed = True
            v.reason = "clear"
            return v

    w5 = Watcher()
    e = w5.watch_gate_verdict("a fine sentence", True, "clear",
                              SteadyGate())
    check("a steady gate reads as stable", e.verdict == "gate_stable",
          e.detail)

    print()
    print("=" * 74)
    print("  the selftest %s" % ("PASSED" if ok else "FAILED"))
    print("=" * 74)
    return 0 if ok else 1


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="watch_log")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--observe", help="observe a watch log on disk")
    args = ap.parse_args()
    if args.observe:
        with open(args.observe, encoding="utf-8") as fh:
            text = fh.read()
        obs = observe_jsonl(text)
        print("%s  %s" % (obs.verdict, obs.reason))
        return 0 if obs.consistent() else 1
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
