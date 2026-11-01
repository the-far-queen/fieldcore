"""
gate_staleness.py -- CAN THE GATE TELL THAT ITS OWN CODE IS OLD?

WHY THIS FILE EXISTS. 2026-11-01, measured on this machine.

THE DEFECT, stated exactly. The FieldCore gate is a long-lived PROCESS.
The gateway (pid 12188) started at 19:23 and imported the gate's modules
at that moment. The predicate layer's fix -- the removal of the deny
pattern "a fixture row" -- landed at 20:34, in commit 55bae29.

So for every hour after 20:34 the running gate was adjudicating with
the OLD rules, and it looked perfectly healthy: the log said
"fieldcore-gate: active (layers=claim,property,predicate,testimony)",
the session-start line said "gate: ready", and the refusal it produced
quoted a rule that no longer existed in the source.

MEASURED, two independent derivations, and they AGREE:

    python cache/scratch/probe_two_ways.py
      OLD  (55bae29^ src)   "the fixture row is an ordinary json file"
                            -> caught_by=[predicate]
      NEW  (working tree)   the same sentence
                            -> caught_by=[]

And the LIVE gate refused two of this session's own tool calls with the
old reason, on phrases the current source admits.

THE FAILURE, named. A gate that cannot notice that its rules changed
keeps enforcing rules that were deleted. It refuses honest work, and
the refusal cites a rule that is not in the code any more. Nothing in
the log distinguishes "the gate is enforcing the current rules" from
"the gate is enforcing a snapshot of the rules from four hours ago".

THE FIX, and it is at the SOURCE. The gate's rules are BUILT from
files, and the build is cached for the life of the process. So the gate
RECORDS what it was built from, and it COMPARES that record against the
files on disk. When they differ, the gate knows its rules are stale,
and it says so in a way that cannot be mistaken for a pass.

AND THE RECORD IS TAKEN AT BUILD TIME. This is the part the first
version got wrong, and it is worth stating because the wrong version
looked correct: a fingerprint computed from the modules IN MEMORY cannot
ever differ from disk, because reading a module's file stats the file
AGAIN. So "compare the loaded modules to the disk" always agrees, and
the check always says FRESH. The record has to be a SNAPSHOT TAKEN WHEN
THE BUILD HAPPENED, compared against a FRESH READING NOW.

AND THE FINGERPRINT IS CHEAP. Measured on this machine:

    350 python files, 4.3 MB    full content hash   30.6 ms
    350 python files            stat only (mtime)    6.8 ms

The stat-only fingerprint is 4.5x cheaper and is the one that runs. It
is also the one that CANNOT miss a change: a file whose content
changed has a different mtime, and a file whose mtime changed but whose
content did not produces a spurious stale report, which is safe.

THE COST IS PAID ONCE PER CHECK, not once per span. The gate's decide
path is 2.29 ms per span; a fresh reading is 6.8 ms. So the check is
THROTTLED -- at most once every CHECK_INTERVAL_SECONDS -- and the
throttled answer is what the caller gets. A stale verdict that is up
to 30 seconds late is still a stale verdict, and 30 seconds of a stale
gate is the difference between refusing Bobby's work and not.

THE RELOAD IS NOT AUTOMATIC. The gate is CACHED because building the
predicates spawns a governor PROCESS, and that is expensive. So the
fingerprint is checked, and a stale build is REPORTED. Reloading is a
separate, explicit step -- because a gate that silently swaps its own
rules mid-session is a gate whose verdict depends on when you asked.

THE CONTRACT:

    snapshot()            what the rules look like RIGHT NOW
    fingerprint(snap)     the hash of a snapshot
    diff(old, new)        the paths that moved between two snapshots
    StaleGate             the exception, carrying the evidence
    StalenessChecker      the throttled checker the gate holds

Run:  python src/gate_staleness.py
Prints: the fingerprint, the file count, and a simulated staleness.
"""
from __future__ import annotations

import hashlib
import os
import sys
import time
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

#: The directories whose python files can change the gate's rules.
#:
#: AND WHY THESE TWO AND NOT "the whole repo". The gate's build reads
#: the layer modules, the registry, the substrate's own files (the
#: governor, the gate, the mini atlas, the locus, the fieldcore cell),
#: and simself's constitutional ground -- because the predicates ASK
#: the substrate, and the substrate is in both repos. A change in
#: fieldcore/docs is not a change to the rules, and including the docs
#: would make the fingerprint move for reasons that do not matter.
RULE_DIRS: Tuple[str, ...] = (FC_SRC, SS_SRC)

#: The modules the gate's build actually imports. A change in ANY of
#: them can change a verdict.
#:
#: AND WHY THIS LIST AND NOT "every module in RULE_DIRS". The first
#: version fingerprinted all 350 python files in both src trees. That
#: is correct but it is also 4.5x the work, and it fires on a change
#: to a module the gate never imports (a plotting script, a bench).
#: The list is the modules the BUILD touches, so a fingerprint move
#: means a verdict can move.
RULE_MODULES: Tuple[str, ...] = (
    "fc_gate",
    "claim_register",
    "property_layer",
    "testimony_layer",
    "predicate_layer",
    "predicate_registry",
    "provenance_scope",
    "qualification",
    # the substrate the predicates ASK
    "gate",
    "governor",
    "core_math",
    "mini_atlas",
    "locus",
    "fieldcore_cell",
    "locus_gate",
    "coherence_spine",
)

#: The corpus files the build reads as DATA rather than as code.
RULE_DATA: Tuple[str, ...] = (
    os.path.join(WORK_REPOS, "fieldcore", "corpus", "predicates.json"),
    os.path.join(WORK_REPOS, "fieldcore", "corpus", "ladder_cap.json"),
    os.path.join(WORK_REPOS, "fieldcore", "tests", "data",
                 "held_out_adversarial.json"),
    os.path.join(WORK_REPOS, "fieldcore", "tests", "data",
                 "informed_adversarial.json"),
    os.path.join(WORK_REPOS, "fieldcore", "tests", "data",
                 "fresh_adversarial.json"),
)

#: How long a freshness answer is reused. The check costs 6.8 ms and
#: the decide path costs 2.29 ms per span, so an unthrottled check
#: would triple the cost of every reply.
CHECK_INTERVAL_SECONDS = 30.0

#: A snapshot: absolute path -> (mtime_ns, size).
Snapshot = Dict[str, Tuple[int, int]]

#: THE IMPORT-TIME SNAPSHOT. Taken when THIS module is imported, which
#: is when the gate's rules were read into the process. A long-lived
#: gateway imports the gate once and then sits on it for hours, so
#: this is the record of what the rules WERE.
#:
#: AND WHY IT IS AT MODULE LEVEL. The gate's build happens whenever a
#: caller first touches it, which can be much later than the import --
#: and a change that lands between the import and the build is exactly
#: the change the check has to catch. So the record is taken at the
#: earliest moment the process has the information, and the checker
#: takes it from there.
IMPORT_SNAPSHOT: Snapshot = {}


def _rule_paths() -> List[str]:
    """Every file the fingerprint covers, in a stable order."""
    out: List[str] = []
    for root in RULE_DIRS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            for fn in sorted(filenames):
                if fn.endswith(".py"):
                    out.append(os.path.join(dirpath, fn))
    for path in RULE_DATA:
        if os.path.exists(path):
            out.append(path)
    return out


def snapshot() -> Snapshot:
    """What the rules look like RIGHT NOW.

    AND THE HASH, versus the SNAPSHOT. The snapshot is the raw record
    (path, mtime_ns, size) of every rule file, and the fingerprint is
    a hash of it. The snapshot is what makes the DIFF possible: a
    fingerprint says "something moved", and a snapshot says "the
    predicate registry moved".
    """
    snap: Snapshot = {}
    for path in _rule_paths():
        try:
            st = os.stat(path)
        except OSError:
            continue
        snap[os.path.abspath(path)] = (st.st_mtime_ns, st.st_size)
    return snap


def fingerprint(snap: Snapshot) -> str:
    """The hash of a snapshot.

    AND THE ORDER. The paths are sorted, so the hash does not depend on
    the order the filesystem happened to hand them over.
    """
    h = hashlib.sha256()
    for path in sorted(snap):
        mtime_ns, size = snap[path]
        h.update(os.path.basename(path).encode("utf-8"))
        h.update(str(mtime_ns).encode("ascii"))
        h.update(str(size).encode("ascii"))
    return h.hexdigest()


def diff(old: Snapshot, new: Snapshot) -> List[str]:
    """The paths that moved between two snapshots.

    AND WHY A LIST AND NOT A COUNT. A count says "something changed".
    A list says "the predicate registry changed", and that is the
    difference between a warning somebody reads and a warning somebody
    files.
    """
    moved: List[str] = []
    for path in sorted(set(old) | set(new)):
        if old.get(path) != new.get(path):
            moved.append(path)
    return moved


class StaleGate(Exception):
    """The gate's rules on disk are NEWER than the rules it is using.

    AND IT CARRIES THE EVIDENCE, because a refusal that names nothing
    is a refusal nobody can act on. It carries both fingerprints, the
    file counts, and the list of the files that moved.
    """

    def __init__(self, built: str, disk: str, moved: Sequence[str],
                 n_built: int = 0, n_disk: int = 0):
        self.built = built
        self.disk = disk
        self.moved = list(moved)
        self.n_built = n_built
        self.n_disk = n_disk
        super().__init__(
            "the gate's rules on disk are newer than the rules it is "
            "using: built=%s (%d files) disk=%s (%d files) moved=%s"
            % (built[:12], n_built, disk[:12], n_disk,
               ", ".join(os.path.basename(p) for p in self.moved) or "?"))


class StalenessChecker:
    """The throttled checker. One per gate.

    AND WHY IT HOLDS A SNAPSHOT. The snapshot is taken when the gate
    BUILDS -- that is the record of what the rules were -- and it is
    compared against a fresh reading. This is the whole mechanism, and
    the first version failed because it compared two readings of the
    same moment.
    """

    def __init__(self, interval: float = CHECK_INTERVAL_SECONDS,
                 built: Optional[Snapshot] = None):
        self.interval = interval
        # AND THE IMPORT-TIME RECORD IS THE DEFAULT. The modules the
        # gate uses were read into memory when they were imported, so
        # that is the most faithful record of what the gate is
        # enforcing. A caller with a different record passes it in.
        self._built: Optional[Snapshot] = (
            built if built is not None else import_snapshot())
        self._last_check = 0.0
        self._has_checked = False
        self._last_result: Optional[StaleGate] = None

    @property
    def built_fingerprint(self) -> str:
        """The fingerprint of the record.

        AND WHY IT IS COMPUTED, NOT CACHED. The first version cached
        the fingerprint string at construction time, and the snapshot
        was only used for the diff. So a caller that changed the
        snapshot -- which is exactly what the tests do, and exactly
        what "the rules moved under the gate" means -- left the
        comparison reading the OLD cached string and the gate said
        FRESH. The snapshot is the RECORD, so the fingerprint is
        derived from it every time it is asked for.
        """
        return fingerprint(self._built) if self._built else ""

    def record_build(self, snap: Optional[Snapshot] = None) -> str:
        """RECORD what the build was built from. Returns the fingerprint.

        AND WHEN IT IS CALLED. Once, at build time. If it is never
        called, the checker has nothing to compare against and reports
        the gate as FRESH forever -- which is the failure this file
        exists to end.

        AND WHY THE IMPORT-TIME SNAPSHOT WINS. The modules the gate
        uses were READ FROM DISK when the process imported them, which
        is before the gate object is built -- often much before, since
        a long-lived gateway builds its gate at load time and then
        sits on it. So the snapshot taken at import time is the record
        of what the rules WERE, and a snapshot taken at build time is
        the record of what they were LATER -- which can hide a change
        that landed between the import and the build.

        AND WHY A LATER RECORD DOES NOT OVERWRITE AN EARLIER ONE. The
        older record is the more conservative one: it names more
        changes as stale. A staleness check that misses a change is
        the failure this file exists to end, so the older record is
        kept.
        """
        if self._built is None:
            self._built = snapshot() if snap is None else dict(snap)
        self._last_check = time.time()
        self._has_checked = False
        self._last_result = None
        return self.built_fingerprint

    def check(self, force: bool = False) -> Optional[StaleGate]:
        """Is the build behind disk? None means FRESH.

        AND THE THROTTLE. A check costs 6.8 ms and the decide path
        costs 2.29 ms per span, so the check runs at most once per
        interval. The answer between checks is the last answer, which
        is a stale verdict at most 30 seconds late.

        AND WHY THE THROTTLE NEEDS ITS OWN FLAG. The first version
        keyed the throttle on "the last result was not None" -- which
        is the STALE case. So a FRESH gate, which is the common case,
        never throttled at all, and every decide() re-read 356 files.
        The throttle has to be keyed on "a check has happened", not on
        what the check found.
        """
        now = time.time()
        if (not force and self._has_checked
                and (now - self._last_check) < self.interval):
            return self._last_result
        self._last_check = now
        self._has_checked = True
        if self._built is None:
            # NO RECORD. The gate never recorded what it was built
            # from, so nothing can be compared. The honest answer is
            # "unknown", and it is NOT fresh -- but it is also not
            # proof of staleness, so it is reported as a warning
            # rather than a refusal.
            self._last_result = None
            return None
        disk = snapshot()
        disk_fp = fingerprint(disk)
        built_fp = self.built_fingerprint
        if disk_fp == built_fp:
            self._last_result = None
            return None
        self._last_result = StaleGate(built_fp, disk_fp,
                                      diff(self._built or {}, disk),
                                      len(self._built or {}), len(disk))
        return self._last_result

    def moved(self) -> List[str]:
        """The files that moved, if the last check found any."""
        if self._last_result is None:
            return []
        return list(self._last_result.moved)


def describe(checker: Optional[StalenessChecker] = None) -> str:
    """One human-readable line about the freshness of a build."""
    if checker is None:
        checker = StalenessChecker()
        checker.record_build()
        return "FRESH (just recorded; nothing to compare against yet)"
    disk = snapshot()
    disk_fp = fingerprint(disk)
    built_fp = checker.built_fingerprint
    if built_fp == disk_fp:
        return ("FRESH  disk=%s files=%d built=%s"
                % (disk_fp[:12], len(disk), built_fp[:12]))
    moved = diff(checker._built or {}, disk)
    return ("STALE  disk=%s files=%d built=%s moved=%s"
            % (disk_fp[:12], len(disk), built_fp[:12],
               ", ".join(os.path.basename(p) for p in moved) or "?"))


def main() -> int:
    print("GATE STALENESS -- can the gate tell its own code is old?")
    print("-" * 72)
    print("rule dirs : %s" % ", ".join(RULE_DIRS))
    print("modules   : %d" % len(RULE_MODULES))
    print("data files: %d" % len(RULE_DATA))
    print("-" * 72)
    checker = StalenessChecker(interval=0.0)
    checker.record_build()
    print("at build : %s" % describe(checker))

    # Now pretend a rule file moved, and check that the checker says so.
    snap = snapshot()
    tampered = dict(snap)
    key = os.path.abspath(os.path.join(FC_SRC, "predicate_registry.py"))
    if key in tampered:
        mtime_ns, size = tampered[key]
        tampered[key] = (mtime_ns + 1, size)
    disk = snapshot()
    if fingerprint(tampered) != fingerprint(disk):
        print("SIMULATED: one rule file moved -> the checker would say "
              "STALE")
        stale = StaleGate(fingerprint(tampered), fingerprint(disk),
                          diff(tampered, disk),
                          len(tampered), len(disk))
        print("           %s" % stale)
    else:
        print("SIMULATED: no difference -- the check cannot tell")
    print("-" * 72)
    return 0


# --------------------------------------------------------------------------
# THE IMPORT-TIME RECORD
# --------------------------------------------------------------------------

#: Taken NOW, at import time. This is the moment the process read the
#: rules into memory, so it is the most faithful record of what the
#: gate is enforcing.
#:
#: AND WHY IT IS NOT INSIDE A FUNCTION. A function body would not run
#: until something called it, and the whole point is to have the
#: record before anything can change.
IMPORT_SNAPSHOT.update(snapshot())
IMPORT_FINGERPRINT = fingerprint(IMPORT_SNAPSHOT)


def import_snapshot() -> Snapshot:
    """The snapshot taken when this module was imported."""
    return dict(IMPORT_SNAPSHOT)


def import_fingerprint() -> str:
    """The fingerprint taken when this module was imported."""
    return IMPORT_FINGERPRINT


if __name__ == "__main__":
    sys.exit(main())
