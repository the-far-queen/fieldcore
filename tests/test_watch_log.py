"""
tests/test_watch_log.py -- the watcher and its observer, on the python
side, with checks that can FAIL.

THE CONTROLS, and each is green before any mutation:
  1. a clean exchange's chain observes as consistent
  2. an absent chain is ABSENT, not healthy
  3. a doctored digest is caught
  4. a pure link break is caught
  5. a rewrite whose digests were recomputed fools the chain-internal
     check, and the ANCHOR catches it
  6. a swapped step order is caught
  7. a gate that changes its mind is caught

AND THE MUTATION, in `tools/mutation_check_watch_log.py`: each of the
observer's three checks is removed in turn, and each must turn a check
RED. A check that cannot fail is not a check.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import watch_log  # noqa: E402


def _chain_with_two() -> watch_log.WatchChain:
    w = watch_log.Watcher()
    w.chain.push("step", "gate/prompt", "ok", "clear")
    w.chain.push("step", "gate/answer", "ok", "clear")
    return w.chain


# ---------------------------------------------------------------------------
# 1. the control
# ---------------------------------------------------------------------------

def test_a_clean_chain_observes_as_consistent():
    chain = _chain_with_two()
    obs = watch_log.observe(chain)
    assert obs.verdict == "consistent", obs.reason
    assert obs.checked == 2


# ---------------------------------------------------------------------------
# 2. absence is not health
# ---------------------------------------------------------------------------

def test_an_absent_chain_is_absent_and_not_healthy():
    obs = watch_log.observe(watch_log.WatchChain())
    assert obs.verdict == "absent", obs.reason
    assert not obs.consistent()


# ---------------------------------------------------------------------------
# 3. a doctored digest
# ---------------------------------------------------------------------------

def test_a_doctored_digest_is_caught():
    chain = watch_log.WatchChain.from_jsonl(_chain_with_two().to_jsonl())
    chain.entries[0].detail = "REFUSED"
    obs = watch_log.observe(chain)
    assert obs.verdict == "broken", obs.reason
    assert "digest_mismatch" in obs.reason


# ---------------------------------------------------------------------------
# 4. a pure link break
# ---------------------------------------------------------------------------

def test_a_pure_link_break_is_caught():
    chain = watch_log.WatchChain.from_jsonl(_chain_with_two().to_jsonl())
    chain.entries[1].prev = watch_log.GENESIS_DIGEST
    chain.entries[1].digest = chain.entries[1].recomputed_digest()
    obs = watch_log.observe(chain)
    assert obs.verdict == "broken", obs.reason
    assert "link_break" in obs.reason
    assert obs.broke_at == 1


# ---------------------------------------------------------------------------
# 5. the anchor
# ---------------------------------------------------------------------------

def test_a_rewrite_with_recomputed_digests_is_caught_by_the_anchor():
    original = _chain_with_two()
    anchor = watch_log.Anchor.of(original)

    chain = watch_log.WatchChain.from_jsonl(original.to_jsonl())
    chain.entries[1].detail = "tampered"
    chain.entries[1].digest = chain.entries[1].recomputed_digest()

    # WITHOUT the anchor, the chain-internal check is fooled. This is
    # the MEASURED behaviour, and it is why the anchor exists.
    without = watch_log.observe(chain)
    assert without.verdict == "consistent", without.reason

    # WITH the anchor, the rewrite is caught.
    with_anchor = watch_log.observe(chain, anchor)
    assert with_anchor.verdict == "broken", with_anchor.reason
    assert "anchor_mismatch" in with_anchor.reason


# ---------------------------------------------------------------------------
# 6. the order
# ---------------------------------------------------------------------------

def test_the_projects_order_reads_as_ok():
    w = watch_log.Watcher()
    e = w.watch_order(["gate/prompt", "simself/locus", "mte/answer",
                        "gate/answer", "grounding", "governor"])
    assert e.verdict == "order_ok", e.detail


def test_a_swapped_order_is_caught():
    w = watch_log.Watcher()
    e = w.watch_order(["gate/prompt", "governor", "grounding"])
    assert e.verdict == "order_fault", e.detail
    assert "grounding" in e.detail and "governor" in e.detail


# ---------------------------------------------------------------------------
# 7. the gate's determinism
# ---------------------------------------------------------------------------

class _V:
    allowed = True
    reason = ""


class _FlakyGate:
    def __init__(self):
        self.n = 0

    def decide(self, text, fail_closed=False):
        self.n += 1
        v = _V()
        v.allowed = (self.n % 2 == 0)
        v.reason = "the answer says something the ground denies"
        return v


class _SteadyGate:
    def decide(self, text, fail_closed=False):
        v = _V()
        v.allowed = True
        v.reason = "clear"
        return v


def test_a_gate_that_changes_its_mind_is_caught():
    w = watch_log.Watcher()
    e = w.watch_gate_verdict("the ground is mutable", True, "clear",
                             _FlakyGate())
    assert e.verdict == "gate_fault", e.detail


def test_a_steady_gate_reads_as_stable():
    w = watch_log.Watcher()
    e = w.watch_gate_verdict("a fine sentence", True, "clear",
                             _SteadyGate())
    assert e.verdict == "gate_stable", e.detail


# ---------------------------------------------------------------------------
# 8. the log round trip, and the observer reading it from disk
# ---------------------------------------------------------------------------

def test_the_log_round_trips_through_disk_and_observes_consistent():
    chain = _chain_with_two()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "exchange.jsonl")
        watch_log.append_log(path, chain)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        obs = watch_log.observe_jsonl(text)
        assert obs.verdict == "consistent", obs.reason
        assert obs.checked == 2


def test_a_doctored_log_line_on_disk_is_caught():
    chain = _chain_with_two()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "exchange.jsonl")
        watch_log.append_log(path, chain)
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        doctored = text.replace('"clear"', '"REFUSED"')
        assert text != doctored
        obs = watch_log.observe_jsonl(doctored)
        assert obs.verdict == "broken", obs.reason
        assert "digest_mismatch" in obs.reason


# ---------------------------------------------------------------------------
# 9. the wrapper wiring
# ---------------------------------------------------------------------------

def test_the_wrapper_watches_its_exchange_when_asked():
    """The watcher is a DUTY on the wrapper, and it is off by default."""
    from fc_wrapper import FieldCoreWrapper

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "watch.jsonl")
        w = FieldCoreWrapper(live=False, watch_log_path=path)
        ex = w.ask("what is the ground?")
        assert ex.steps, "the exchange produced no steps"
        names = [s.name for s in ex.steps]
        assert "watcher" in names, "the watcher did not report: %s" % (names,)
        watcher_step = next(s for s in ex.steps if s.name == "watcher")
        assert watcher_step.ok, watcher_step.detail
        assert os.path.isfile(path), "the chain was not written"
        obs = watch_log.observe_jsonl(open(path, encoding="utf-8").read())
        assert obs.verdict == "consistent", obs.reason


def test_the_wrapper_does_not_write_when_the_watcher_is_off():
    from fc_wrapper import FieldCoreWrapper

    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "watch.jsonl")
        w = FieldCoreWrapper(live=False)
        ex = w.ask("what is the ground?")
        names = [s.name for s in ex.steps]
        assert "watcher" not in names, "the watcher wrote without being asked"
        assert not os.path.exists(path), "a log was written nobody asked for"
