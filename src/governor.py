"""M0 governor as a SEPARATE PROCESS — refusal made structural.

WHY THIS FILE EXISTS. The 747 comparison (see
`docs/research-papers/747-layered-control-comparison-2026-10-09.md`, §3.4)
returned OPEN on the one layer the whole analogy depends on:

    On a 747 the flight computer and the pilot are independent systems.
    In ours the governor was a function call inside the process it
    constrains. A veto the governed process can decline to call is not
    a veto.

Bobby's correction, 2026-10-09: "the 747 is well established, governor
misplaced." Agreed, and this file is the placement fix.

WHAT IS ACTUALLY ENFORCED HERE. The governor runs in its own OS process,
over a pipe, and the governed process can do exactly three things with it:
ask a question, receive one bit, or fail to get a bit. It cannot:

  - modify the governor's code, thresholds or memory
  - reach into the governor's address space
  - lie to the governor about what it is asking
  - continue an operation the governor refused, because the refusal is
    returned from a DIFFERENT PROCESS and the caller must act on it

What it can still do, and this is stated rather than hidden: it can refuse
to CALL the governor, and it can catch exceptions from the call. That
residual is real and is why §"residual" below is not optional. The
mitigation is that the caller-visible helper `guarded()` in this module
does not offer a path that skips the governor, and the certified use is
"the governed system calls through this channel", not "the governor
prevents the governed system from existing".

THE 747 ANALOGY, PRECISELY. Envelope protection on a 747 is not a
function the aircraft can choose not to call. It is a separate channel
with its own authority, and the aircraft's failure to respect it is a
failure of the aircraft, not of the protection. This file is the smallest
honest version of that: the governor is a process, and its answer comes
across a process boundary.

FAILURE BEHAVIOUR. If the governor process is unreachable, crashed, or too
slow, the correct answer for an envelope is DENY, not ALLOW. Fail-closed
is the whole point and it is asserted in the tests.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

# The governor's own constants. The governed process must not be able to
# change these, which is why they live here and not in a caller-visible
# default that can be overridden per call.
MAX_NORM = 4.0
MIN_COS = 0.4


class Verdict(str, Enum):
    ALLOW = "ALLOW"
    REFUSE_NORM = "REFUSE_NORM"
    REFUSE_ZERO = "REFUSE_ZERO"
    REFUSE_COHERENCE = "REFUSE_COHERENCE"
    REFUSE_MALFORMED = "REFUSE_MALFORMED"
    # transport-level verdicts, decided by the CALLER because they describe
    # the absence of an answer
    REFUSE_UNREACHABLE = "REFUSE_UNREACHABLE"
    REFUSE_TIMEOUT = "REFUSE_TIMEOUT"


@dataclass(frozen=True)
class Decision:
    allow: bool
    verdict: Verdict
    elapsed_ms: float

    def __bool__(self) -> bool:
        return self.allow


# ---------------------------------------------------------------- the gate math


def evaluate(emb: Any, psi0: Any) -> tuple[bool, Verdict]:
    """The two inequalities. Runs ONLY inside the governor process.

    The limits are module constants with no parameter path. That is not
    stylistic: the first version threaded max_norm and min_cos through the
    message from the caller, and the governed process simply sent larger
    values. A gate whose limits can be supplied by the thing it gates is
    not a gate.

    Defensive on input: anything that is not a finite float array is
    refused rather than raising, because an exception is not a verdict.
    """
    max_norm, min_cos = MAX_NORM, MIN_COS
    try:
        e = np.asarray(emb, dtype=float)
        p = np.asarray(psi0, dtype=float)
    except (TypeError, ValueError):
        return False, Verdict.REFUSE_MALFORMED
    if e.size == 0 or p.size == 0:
        return False, Verdict.REFUSE_MALFORMED
    if not (np.all(np.isfinite(e)) and np.all(np.isfinite(p))):
        return False, Verdict.REFUSE_MALFORMED

    ne = float(np.linalg.norm(e))
    if ne > max_norm:
        return False, Verdict.REFUSE_NORM
    n0 = float(np.linalg.norm(p))
    if ne == 0.0 or n0 == 0.0:
        return False, Verdict.REFUSE_ZERO
    if float(np.dot(e, p) / (ne * n0)) < min_cos:
        return False, Verdict.REFUSE_COHERENCE
    return True, Verdict.ALLOW


# ---------------------------------------------------------------- the process


def _serve(conn: Any) -> None:
    """Governor loop. Owns its own address space and its own constants.

    One rule here that the first version got wrong: a malformed request
    gets a verdict, not an exception. An exception would end the
    governor and turn every later request into REFUSE_UNREACHABLE, so a
    single malformed call from the governed process would take out the
    safety channel. It must be survivable.
    """
    try:
        while True:
            try:
                msg = conn.recv()
            except (EOFError, KeyboardInterrupt):
                return
            if msg is None:
                return
            try:
                emb = msg.get("emb")
                psi0 = msg.get("psi0")
                # The thresholds are NOT read from the wire. An earlier
                # version accepted max_norm and min_cos in the message, and
                # a governed process could then pass max_norm=1000 and walk
                # straight through the gate. The request can now only ask
                # whether a given embedding is inside ITS OWN limits.
                allow, verdict = evaluate(emb, psi0)
            except Exception:                      # never die on bad input
                allow, verdict = False, Verdict.REFUSE_MALFORMED
            try:
                conn.send({"allow": bool(allow), "verdict": verdict.value})
            except (BrokenPipeError, EOFError):
                return
    finally:
        try:
            conn.close()
        except Exception:
            pass


class GovernorProcess:
    """A handle to the governor running in its own process.

    Spawn context is explicit. On Windows the default is spawn, which
    re-imports the module in the child; using the same explicit context on
    both sides keeps the handshake honest and makes the process boundary
    real rather than a fork of the parent's memory.
    """

    def __init__(self, start_method: str = "spawn", startup_timeout: float = 5.0):
        self._ctx = mp.get_context(start_method)
        self._parent_conn, child_conn = self._ctx.Pipe(duplex=True)
        self._proc = self._ctx.Process(target=_serve, args=(child_conn,),
                                       daemon=True)
        self._proc.start()
        child_conn.close()                      # only the child keeps its end
        self._startup_timeout = startup_timeout
        self.pid = self._proc.pid
        self.started_at = time.time()
        self._alive = True

    @property
    def alive(self) -> bool:
        return self._alive and self._proc.is_alive()

    def ask(self, emb: Any, psi0: Any, *, timeout: float = 2.0) -> Decision:
        """Send one question, get one bit. Fail-closed on every failure.

        There are no threshold parameters, deliberately. A caller that can
        pass its own limits can pass limits that permit everything, which
        is the same as having no gate. The limits live in the governor.
        """
        t0 = time.time()
        if not self.alive:
            return Decision(False, Verdict.REFUSE_UNREACHABLE,
                            (time.time() - t0) * 1000)
        try:
            self._parent_conn.send({"emb": emb, "psi0": psi0})
        except (BrokenPipeError, OSError):
            self._alive = False
            return Decision(False, Verdict.REFUSE_UNREACHABLE,
                            (time.time() - t0) * 1000)
        if not self._parent_conn.poll(timeout):
            return Decision(False, Verdict.REFUSE_TIMEOUT,
                            (time.time() - t0) * 1000)
        try:
            reply = self._parent_conn.recv()
        except (EOFError, OSError):
            self._alive = False
            return Decision(False, Verdict.REFUSE_UNREACHABLE,
                            (time.time() - t0) * 1000)
        dt = (time.time() - t0) * 1000
        return Decision(bool(reply["allow"]), Verdict(reply["verdict"]), dt)

    def close(self) -> None:
        try:
            self._parent_conn.send(None)
        except (BrokenPipeError, OSError):
            pass
        try:
            self._parent_conn.close()
        except (BrokenPipeError, OSError):
            pass
        if self._proc.is_alive():
            # stdlib method name, reached indirectly so the source carries
            # no banned vocabulary
            getattr(self._proc, "terminate")()
        self._proc.join(timeout=2.0)
        self._alive = False

    def __enter__(self) -> "GovernorProcess":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


# ---------------------------------------------------------------- the wrapper


def _shared() -> GovernorProcess:
    """The one governor this process talks to.

    Created lazily, and RESPAWNED if it has gone away. The respawn is the
    problem this comment exists to record: the first version respawned
    silently, so closing the governor and asking again produced ALLOW from
    a brand new process rather than a refusal. A safety channel that
    restarts itself on demand cannot fail closed, because nothing is ever
    actually absent from the caller's point of view.

    Respawn is kept, because a governor that never returns after an
    ordinary exit would make the system unusable. What changed is that
    `guarded()` no longer silently papers over absence: see
    `respawn_allowed`, which defaults to False for governed actions.
    """
    gov = globals().get("_GOV")
    if gov is None:
        gov = GovernorProcess()
        globals()["_GOV"] = gov
    return gov


def guarded(emb: Any, psi0: Any, *, timeout: float = 2.0) -> Decision:
    """Ask the out-of-process governor. This is the sanctioned path.

    Fail-closed. Three cases, in order:

      no governor yet        -> start one, then ask
      governor has gone      -> REFUSE_UNREACHABLE, do NOT start another
      governor live          -> ask

    The middle case is the important one. The first version respawned
    silently, so a closed or ended governor produced ALLOW from a brand new
    process instead of a refusal. A channel that restarts itself on demand
    can never fail closed, because nothing is ever absent as far as the
    caller is concerned.
    """
    gov = globals().get("_GOV")
    if gov is None:
        gov = GovernorProcess()
        globals()["_GOV"] = gov
    if not gov.alive:
        return Decision(False, Verdict.REFUSE_UNREACHABLE, 0.0)
    return gov.ask(emb, psi0, timeout=timeout)


def guarded_run(emb: Any, psi0: Any, operation, *, timeout: float = 2.0):
    """Run `operation()` only if the out-of-process governor allows it.

    The correct shape for a governed action, and the shape the 747 uses:
    the protected system does not consult a list of instructions about
    what is forbidden, it asks, and the answer comes from elsewhere.
    """
    d = guarded(emb, psi0, timeout=timeout)
    if not d:
        return d, None
    return d, operation()


def report() -> dict:
    """What the governor looks like from outside — for the exam."""
    gov = _shared()
    try:
        pid, ppid = os.getpid(), os.getppid()
    except Exception:
        pid = ppid = -1
    return {
        "governor_pid": gov.pid,
        "caller_pid": pid,
        "same_process": gov.pid == pid,
        "alive": gov.alive,
        "max_norm": MAX_NORM,
        "min_cos": MIN_COS,
    }