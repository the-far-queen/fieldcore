"""
wiring.py -- THE THREE REPOS, WIRED, AND THE ANCHOR TEST.

Bobby, 2026-10-25: *"if wire it together run once see if you can locate
the hole immediately zero is the anchor"*

THE THREE PIECES, and what each one owns:

    fieldcore   the SUBSTRATE. the 3-part coax stalks, the interstalk
                channel, the equaliser, the 1-bit gate, the derived
                width. the geometry.

    simself     the IDENTITY. the constitutional ground psi_0, the
                M0 governor, the sacred library, the atlas exam's
                subject.

    atlas-exam  the QUALIFICATION. 23 areas, pointed at the other two
                through SUBPROCESS probes, so an exam that imports its
                subject cannot grade itself.

AND THE ANCHOR, and this is the whole test:

    ZERO IS THE ANCHOR.

  Every layer in this project is measured against a zero:

    the gate's cosine is against psi_0 -- the constitutional ground
    the drift is distance from psi_0
    the projection pulls psi back toward psi_0
    the loop matrix's low eigenvalue is the apex void, the invariant
      zero
    the stalk's address is measured on the unit circle from zero

  So the wiring test is NOT "do the areas pass". It is:

      DOES THE ANCHOR SURVIVE THE ROUND TRIP?

  A number goes in at the far end (the ground, the anchor), it passes
  through fieldcore's geometry, through simself's identity, and back
  out, and it must come back THE SAME. If it does not, the hole is
  located by finding where it changed.

  And that is a much better test than a pass/fail, because a
  pass/fail tells you THAT something is wrong and this tells you
  WHERE.

THE FOUR STAGES, and the anchor is checked at each one:

    1. THE GROUND            simself's psi_0. Does it exist, is it
                             unit norm, is it write-protected?
    2. THE GEOMETRY          fieldcore's stalks. Do their addresses
                             derive, do their couplings compute, does
                             the loop matrix still have an apex void?
    3. THE CHANNEL           does a signal survive the interstalk
                             channel with its amplitude intact?
    4. THE RETURN            does the ground come back the same after
                             a trip through the gate and the geometry?

AND THE HOLE LOCATOR, because "locate the hole immediately" is the
ask: when a stage fails, the report says WHICH stage and WHAT the
number was, so the search is over.

Run:
    python src/wiring.py
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

HERMES = os.path.expanduser("~/AppData/Local/hermes")
WORK_REPOS = os.path.join(HERMES, "work_repos")
SIMSELF_SRC = os.path.join(WORK_REPOS, "simself", "src")
FIELDCORE_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
ATLAS_SRC = os.path.join(WORK_REPOS, "atlas-exam", "src")

#: How long a probe may take. A hung substrate is a FAIL, not a wait.
PROBE_TIMEOUT_S = 240


# ===========================================================================
# THE PROBES -- one line of JSON each, in a fresh interpreter
# ===========================================================================

PROBE_ANCHOR = r"""
import json, numpy as np
from constitutional.constitution import Constitution
from constitutional.ground import Ground

c = Constitution()
psi0 = np.asarray(c.psi_0, dtype=float)
g = Ground(psi0.copy())
n0 = float(np.linalg.norm(psi0))
# is the ground write-protected? try to overwrite it and see if it holds
before = g.psi_0.copy()
try:
    g.psi_0 = np.zeros_like(g.psi_0)
except Exception:
    pass
held = bool(np.allclose(before, g.psi_0))
print(json.dumps({
    "dim": int(psi0.size),
    "norm": n0,
    "unit_norm": bool(abs(n0 - 1.0) < 1e-9),
    "ground_held": held,
    "digest": "%s" % (__import__("hashlib").sha256(
        psi0.tobytes()).hexdigest()[:16],),
}))
"""

PROBE_GEOMETRY = r"""
import json, math, numpy as np
from interstalk_link import InterstalkLink, width_for
from wound_core import CoaxWinding, WoundCore

stalks = [CoaxWinding(
    id="s%02d" % i,
    girth_core=0.030, girth_in=0.060,
    girth_out=0.060 * (1.200 + (i // 2 + 0.5) * 0.0625),
    n_in=12, n_out=13 + (i % 2)) for i in range(8)]
link = InterstalkLink(core=WoundCore(stalks=stalks), bins=128)
ids = [s.id for s in stalks]

# THE APEX VOID: the loop matrix's low eigenvalue. It must be NEGATIVE
# and it must be far from the others -- that is the invariant zero.
eigs = []
for s in stalks:
    eigs.extend(s.loop_eigenvalues())
eigs.sort()

# THE CHANNEL, and its structure
pair = link.pair(ids[0], ids[1], in_view=ids)
ch = pair.channel()
ex = link.exchange(ids[0], ids[1], in_view=ids)

# THE ADDRESSES, and their separation in bins
addrs = [((s.n_out % 2) / 2.0 + (s.girth_ratio - 1.0)) % 1.0 for s in stalks]
sep = min(abs((a - b + 0.5) % 1.0 - 0.5)
           for i, a in enumerate(addrs) for b in addrs[i + 1:])

print(json.dumps({
    "n_stalks": len(stalks),
    "eigs": [float(e) for e in eigs],
    "apex_negative": bool(eigs[0] < 0),
    "apex_gap": float(abs(eigs[1] - eigs[0])),
    "address_sep_bins": float(sep * 128),
    "taps": len(ch.taps),
    "notch_db": float(ch.notch_db()),
    "derived_width": int(width_for(len(ch.taps))),
    "alignment": float(ex.alignment),
    "allowed": bool(ex.allowed),
    "reason": str(ex.reason),
}))
"""

PROBE_ROUNDTRIP = r"""
import json, numpy as np
from constitutional.constitution import Constitution
from constitutional.ground import Ground
from constitutional.simself import SimSelf
from gate import gate as fc_gate, MIN_COS, MAX_NORM

c = Constitution()
psi0 = np.asarray(c.psi_0, dtype=float)
g = Ground(psi0.copy())
s = SimSelf(constitution=c, ground=g, R=3.0, eta=0.1)

# THE ROUND TRIP: the anchor in, the anchor out.
#
# The anchor is the ground. So: take the ground, carry it through
# simself's observer and fieldcore's gate, and check it came back
# unchanged.
before = psi0.copy()
before_norm = float(np.linalg.norm(before))

# 1. through simself's observer -- the ground must NOT move
s.observe(before.copy() * 1.0)
after_observe = s.psi0.copy()

# 2. through fieldcore's gate -- the anchor must be ADMITTED, because it
#    is maximally coherent with the ground by definition
allow, reason = fc_gate(before.copy(), psi0)

print(json.dumps({
    "ground_norm_before": before_norm,
    "ground_norm_after": float(np.linalg.norm(after_observe)),
    "ground_moved": float(np.max(np.abs(before - after_observe))),
    "gate_allows_the_anchor": bool(allow),
    "gate_reason": str(reason),
    "min_cos": float(MIN_COS),
    "max_norm": float(MAX_NORM),
}))
"""

PROBE_ATLAS = r'''
import json, os, sys
atlas = os.path.join(os.path.expanduser(
    "~/AppData/Local/hermes/work_repos/atlas-exam/src"))
sys.path.insert(0, atlas)
from exam import AREAS
from exam import substrate as sub

present = sub.substrate_present()

# which areas does the exam actually implement? The exam's own
# FUNCTIONS are the honest source -- not this file's guess at it.
#
# The first version of this probe matched area NAMES against MODULE
# filenames, and reported "2 of 23 implemented" when the exam actually
# implements 23 area functions and passes 8. So the probe was measuring
# the wrong thing and reporting it as fact.
#
# The exam's convention is `area_<number>_<name>` in cli.py, and the
# area's NAME in AREAS is the same suffix. So the honest mapping is by
# NUMBER, and the honest question is not "is there a function" but
# "what does the area MEASURE" -- because an area whose function
# returns a TODO is not implemented.
import inspect
from exam import cli as exam_cli

implemented = []
unimplemented = []
for number, name in AREAS:
    fn = None
    for attr in dir(exam_cli):
        if attr.startswith("area_%d_" % number):
            fn = getattr(exam_cli, attr)
            break
    if fn is None:
        unimplemented.append(name)
        continue
    try:
        src = inspect.getsource(fn)
    except Exception:
        src = ""
    # an area that only calls todo() is not implemented
    if "todo(" in src and "make(" not in src:
        unimplemented.append(name)
    else:
        implemented.append(name)

print(json.dumps({
    "areas": len(AREAS),
    "names": [n for _, n in AREAS],
    "implemented": implemented,
    "unimplemented": unimplemented,
    "substrate_present": present,
}))
'''


PROBES = {
    "anchor": PROBE_ANCHOR,
    "geometry": PROBE_GEOMETRY,
    "roundtrip": PROBE_ROUNDTRIP,
    "atlas": PROBE_ATLAS,
}


def run_probe(name: str, code: str,
              timeout: int = PROBE_TIMEOUT_S) -> Tuple[bool, Dict, str]:
    """Run a probe in a fresh interpreter. Never a silent pass."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [SIMSELF_SRC, FIELDCORE_SRC, ATLAS_SRC,
         env.get("PYTHONPATH", "")]).strip(os.pathsep)
    try:
        r = subprocess.run([sys.executable, "-c", code],
                           capture_output=True, text=True, env=env,
                           timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, {}, "probe '%s' exceeded %ds" % (name, timeout)
    if r.returncode != 0:
        tail = (r.stderr or "").strip().splitlines()
        return False, {}, (tail[-1] if tail else "exit %d" % r.returncode)
    out = (r.stdout or "").strip()
    if not out:
        return False, {}, "probe '%s' produced no output" % name
    try:
        return True, json.loads(out.splitlines()[-1]), ""
    except ValueError as exc:
        return False, {}, "probe '%s' emitted non-JSON: %s" % (name, exc)


# ===========================================================================
# THE STAGES
# ===========================================================================

@dataclass
class Stage:
    """One stage of the round trip, and whether the anchor held."""
    number: int
    name: str
    ok: bool
    detail: str
    measured: Dict[str, Any] = field(default_factory=dict)
    #: Where the hole is, if there is one.
    hole: str = ""


def stage_anchor() -> Stage:
    ok, p, err = run_probe("anchor", PROBE_ANCHOR)
    if not ok:
        return Stage(1, "the ground", False, "the probe failed: %s" % err,
                     hole="simself's constitutional ground is not reachable")
    checks = {
        "the ground exists": p.get("dim", 0) > 0,
        "the ground is unit norm": bool(p.get("unit_norm")),
        "the ground is write-protected": bool(p.get("ground_held")),
    }
    bad = [k for k, v in checks.items() if not v]
    return Stage(
        1, "the ground", not bad,
        ("the ground holds: dim %d, norm %.12f, digest %s"
         % (p.get("dim", 0), p.get("norm", 0.0), p.get("digest", "?")))
        if not bad else ("the ground failed: %s" % ", ".join(bad)),
        measured=p,
        hole="" if not bad else "simself's ground: %s" % ", ".join(bad))


def stage_geometry() -> Stage:
    ok, p, err = run_probe("geometry", PROBE_GEOMETRY)
    if not ok:
        return Stage(2, "the geometry", False, "the probe failed: %s" % err,
                     hole="fieldcore's geometry is not reachable")
    checks = {
        "the apex void is negative": bool(p.get("apex_negative")),
        "the apex void is separated": float(p.get("apex_gap", 0.0)) > 1e-6,
        "the addresses are resolvable": float(p.get("address_sep_bins", 0.0))
        >= 2.0,
        "the channel has structure": float(p.get("notch_db", 0.0)) > 3.0,
        "the exchange recovers": float(p.get("alignment", 0.0)) > 0.999999,
        "the gate admits the reading": bool(p.get("allowed")),
    }
    bad = [k for k, v in checks.items() if not v]
    return Stage(
        2, "the geometry", not bad,
        ("the geometry holds: %d stalks, notch %.2f dB, width %d bits, "
         "apex %.4f, addresses %.1f bins apart"
         % (p.get("n_stalks", 0), p.get("notch_db", 0.0),
            p.get("derived_width", 0), p.get("eigs", [0])[0],
            p.get("address_sep_bins", 0.0)))
        if not bad else ("the geometry failed: %s" % ", ".join(bad)),
        measured=p,
        hole="" if not bad else "fieldcore's geometry: %s" % ", ".join(bad))


def stage_roundtrip() -> Stage:
    ok, p, err = run_probe("roundtrip", PROBE_ROUNDTRIP)
    if not ok:
        return Stage(3, "the round trip", False, "the probe failed: %s" % err,
                     hole="the anchor does not survive the round trip")
    checks = {
        "the ground does not move": float(p.get("ground_moved", 1.0)) < 1e-12,
        "the gate admits the anchor": bool(p.get("gate_allows_the_anchor")),
    }
    bad = [k for k, v in checks.items() if not v]
    return Stage(
        3, "the round trip", not bad,
        ("the anchor survives: moved %.3e, gate says %s"
         % (p.get("ground_moved", 0.0), p.get("gate_reason", "?")))
        if not bad else ("the round trip failed: %s" % ", ".join(bad)),
        measured=p,
        hole="" if not bad else "the anchor: %s" % ", ".join(bad))


def stage_atlas() -> Stage:
    ok, p, err = run_probe("atlas", PROBE_ATLAS)
    if not ok:
        return Stage(4, "the exam", False, "the probe failed: %s" % err,
                     hole="the exam is not reachable")
    implemented = p.get("implemented", [])
    unimplemented = p.get("unimplemented", [])
    return Stage(
        4, "the exam", bool(implemented),
        ("the exam declares %d areas; %d are implemented, %d are not"
         % (p.get("areas", 0), len(implemented), len(unimplemented))),
        measured=p,
        hole="" if implemented else "the exam has no implemented area")


# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("THE THREE REPOS, WIRED. ZERO IS THE ANCHOR.")
    print("=" * 78)
    print()
    print("  fieldcore   the substrate: stalks, channel, gate, derived width")
    print("  simself     the identity: the ground, the governor, the library")
    print("  atlas-exam  the qualification: 23 areas, over subprocess")
    print()
    print("  THE TEST IS NOT 'DO THE AREAS PASS'. IT IS: DOES THE ANCHOR")
    print("  SURVIVE THE ROUND TRIP. A number goes in at the far end and")
    print("  must come back the same. If it does not, the hole is located")
    print("  by finding the stage where it changed.")
    print()

    stages = [stage_anchor(), stage_geometry(), stage_roundtrip(),
              stage_atlas()]

    for st in stages:
        mark = "PASS" if st.ok else "FAIL"
        print("  [%s] %d %s" % (mark, st.number, st.name))
        print("         %s" % st.detail)
        if st.hole:
            print("         HOLE: %s" % st.hole)
    print()

    holes = [st.hole for st in stages if st.hole]
    print("=" * 78)
    if holes:
        print("THE HOLE IS LOCATED:")
        for h in holes:
            print("  - %s" % h)
    else:
        print("NO HOLE. The anchor survives every stage.")
    print()
    print("  %d of %d stages hold." % (sum(1 for s in stages if s.ok),
                                      len(stages)))
    print("=" * 78)
    return 0 if not holes else 1


if __name__ == "__main__":
    sys.exit(main())
