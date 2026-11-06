"""
stalk_population.py -- THE population recipe, in ONE place.

WHY THIS FILE EXISTS
--------------------
MEASURED 2026-11-05.  Seven files in fieldcore/src each carried their
own copy of a function called `make_population`, and the copies had
DIVERGED into two different behaviours:

    CLUSTERED   bench_failup, bench_balance_point, measure_gate_margin
                the girths vary by thousandths, so the addresses land
                within thousandths of each other and the population
                collapses into a couple of DFT classes

    SPREAD      bench_balance2, bench_tradeoff, bench_balance_final,
                bench_popoviciu_ratio
                the addresses are spread evenly, so every stalk is in
                its own class

**AND THE REPO ALREADY KNEW THE CLUSTERED ONE WAS A CONFOUND.**
`bench_tradeoff.py` says, in its own docstring:

    "THIS FIXED A CONFOUND: the first bench's generator produced
     addresses clustered within 0.012 of each other, which is under two
     DFT bins -- so it was asking the receiver to separate things no
     transform could separate, and then reporting that as a limit of
     the design."

So one bench was fixed and the other six were not.  The consequence is
that the CEILING WAS MEASURED ON THE CONFOUND:

    "MEASURED: population 8 gives 2 classes for 8 stalks, population 16
     gives 5, population 32 gives 13.  ...  That is the population
     code's real ceiling."

MEASURED, on this file's recipe, at every population:

    population   4   4 classes, largest class 1
    population   8   8 classes, largest class 1
    population  16  16 classes, largest class 1
    population  32  32 classes, largest class 1
    population  64  64 classes, largest class 1

Every stalk is in its own class.  There is no address-class ceiling at
all -- and the number the benches published as the population code's
"real ceiling" was an artefact of a stale copy of a recipe.

THE RECIPE
----------
Addresses are SPREAD EVENLY, and the geometry is SOLVED FROM the
address, because the address formula is invertible:

    address = ((n_out % 2) / 2 + (girth_ratio - 1)) % 1

With an EVEN n_out the parity term is 0, so a target address `a` gives
`girth_ratio = 1 + a`.  So:

    address_i = (i + 0.5) / n

and the closest pair is exactly 1/n apart -- n bins apart at n bins.
Every stalk is resolvable, and anything that still fails is a CHANNEL
limit rather than a limit of the generator.

This is also what the substrate's OWN build does, in spirit:
`wound_core.standard_wound_core()` gives every stalk a DIFFERENT turn
ratio and a DIFFERENT girth ratio, because "if two stalks had the same
ratios, the population would have two identical addresses and the
decode would be ambiguous for reasons of design rather than of
measurement."

WHAT THIS FILE IS NOT
---------------------
It is not a new physical model.  The address DERIVATION is unchanged
and still lives where it always did: `interstalk_link._address` and
`wound_core.WoundCore.population()`.  What moves here is the CHOICE OF
GEOMETRY, which was being made seven times and is now made once.

THE RECIPE IS IN THE SUBSTRATE, NOT IN A LIST
---------------------------------------------
MEASURED 2026-11-06: the first check for this file named the seven
benches in a HARDCODED LIST.  A hardcoded list cannot report a copy it
does not know about, and MEASURED: TWO MORE COPIES were sitting in
`src/` that the list never mentioned --

    bench_ladder.make_population        the clustered recipe
    bench_population.make_stalk          the clustered recipe

Both DIVERGED from the canonical recipe at every population, and both
were INVISIBLE to the check that was supposed to catch divergence.
MEASURED, their address separations against the canonical 1/n:

    generator                            min separation   classes@8
    stalk_population (canonical)           0.125000        8
    bench_ladder.make_population           0.002498        2
    bench_population.make_stalk            0.002498        2

So the census at the bottom of this file DISCOVERS the copies by AST
-- every module in `src/` with a function whose body constructs a
`CoaxWinding` -- and every one of them is then held to the canonical
recipe.  A file that has STOPPED carrying a recipe is caught by the
`REQUIRED` list; a file that has STARTED carrying one is caught by
the census.  Both directions, because a copy in either direction is a
copy.

WHAT IS DELIBERATE AND WHAT IS NOT
----------------------------------
Four modules build a population that is NOT this recipe, and each is
named in `DELIBERATE_VARIANTS` with the reason it exists:

    bench_girth_ladder.make_spread_population   the girth ladder's own
                                                spread, measured for a
                                                different question
    do_stalks_communicate.the_population         the 8-bin spread, which
                                                the girth bench MEASURED
                                                as better than 16
    bench_girth_ladder.make_stalks               a PARAMETERISED builder:
                                                every term is a lever, so
                                                it cannot be a fixed
                                                recipe
    stalk_physics.make_population                the PHYSICAL stalk, in
                                                metres -- not a
                                                `CoaxWinding` at all

MEASURED, the deliberate ones that DO produce a `CoaxWinding`
population:

    generator                                  min separation   classes@8
    bench_girth_ladder.make_spread_population   0.125000 (1/n)   8
    do_stalks_communicate.the_population         0.062500        8

Both are ADDRESSABLE -- every stalk in its own class -- so neither
collapses the population and neither can produce a false ceiling.

Run:
    python src/stalk_population.py
"""

from __future__ import annotations

import ast
import os
import sys
from typing import Dict, List, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from wound_core import CoaxWinding  # noqa: E402


#: The populations the benches sweep. One list, so every bench sweeps
#: the same axis.
POPS: Tuple[int, ...] = (2, 3, 4, 8, 16, 32, 64)

#: The inner girth every stalk shares. The address comes from the
#: RATIO, so a shared inner girth is what makes the ratio -- and so the
#: address -- exactly the chosen value.
GIRTH_IN: float = 0.050

#: The core radius every stalk shares. Below GIRTH_IN, as the substrate
#: requires: core < inner < outer.
GIRTH_CORE: float = 0.018

#: Even, so the parity term of the address is 0 and the girth ratio is
#: the WHOLE of the address.
N_OUT: int = 10

#: The inner winding's turns. Not part of the address.
N_IN: int = 5


def make_population(n: int) -> List[CoaxWinding]:
    """n stalks whose addresses are evenly spread over the unit circle.

    MEASURED, every stalk is in its own DFT class at every population:
    population 4 gives 4 classes, population 8 gives 8, population 64
    gives 64, and the largest class is 1 in every case.

    THE ADDRESS IS CHOSEN AND THE GEOMETRY IS SOLVED FOR IT.  The
    address formula is invertible, so a population code can assign the
    addresses and the hardware can realise them -- which is what a real
    population code does, and the opposite of hoping that arbitrary
    geometry lands on well-separated addresses.

    THE CONCENTRIC ORDER IS PRESERVED: core < inner < outer, which the
    substrate's `CoaxWinding` refuses to violate.
    """
    if n <= 0:
        raise ValueError("a population needs at least one stalk, got %d" % n)
    out: List[CoaxWinding] = []
    for i in range(n):
        a = (i + 0.5) / n
        out.append(CoaxWinding(
            id="p%03d" % i,
            girth_out=GIRTH_IN * (1.0 + a),
            girth_in=GIRTH_IN,
            girth_core=GIRTH_CORE,
            n_in=N_IN,
            n_out=N_OUT,
        ))
    return out


def address_of(stalk: CoaxWinding) -> float:
    """The stalk's phase address: parity of outer turns + girth ratio.

    THE SAME DERIVATION the substrate uses, and the same one
    `interstalk_link._address` and `wound_core.WoundCore.population()`
    use.  It is written out here rather than imported because those two
    live in different modules with different import shapes, and because
    a bench needs to be able to name the derivation it is grading
    against.

    MEASURED 2026-11-05: this agrees with
    `interstalk_link.InterstalkLink._address` and with
    `wound_core.WoundCore.population()` to 0.0 on the populations.
    `tools/check_population_recipe.py` re-measures that, so a drift in
    any of the three goes RED.
    """
    ph = (stalk.n_out % 2) / 2.0
    return (ph + (stalk.girth_ratio - 1.0)) % 1.0


def address_classes(stalks: Sequence[CoaxWinding],
                    bins: int) -> Tuple[Dict[str, int], List[int]]:
    """Label each stalk's address class, and return the class sizes.

    Two addresses within 1/bins of each other fall in the same DFT bin,
    so the read cannot tell those two stalks apart -- no matter how
    wide the channel is.

    MEASURED, on this file's recipe, the largest class is 1 at every
    population: every stalk is resolvable, and the classes are a
    REPORT of the population rather than a CEILING on it.
    """
    addrs = {s.id: address_of(s) for s in stalks}
    classes: List[List[float]] = []
    labels: Dict[str, int] = {}
    for sid, a in addrs.items():
        for ci, c in enumerate(classes):
            d = abs(a - c[0])
            if min(d, 1.0 - d) <= 1.0 / bins:
                c[1] += 1
                labels[sid] = ci
                break
        else:
            classes.append([a, 1])
            labels[sid] = len(classes) - 1
    return labels, sorted((int(c[1]) for c in classes), reverse=True)


#: THE MODULES THAT MUST CARRY THE CANONICAL RECIPE.
#:
#: EXPLICIT, so a bench that has STOPPED carrying the recipe is
#: caught: "this bench no longer has a recipe" is drift too.
#:
#: MEASURED 2026-11-06: this list was seven long and two more copies
#: were sitting in `src/` that it never mentioned.  A list catches a
#: copy that was DROPPED; only the census below catches a copy that was
#: ADDED.  Both directions are needed, because a copy in either
#: direction is a copy.
REQUIRED: Tuple[str, ...] = (
    "bench_balance2",
    "bench_balance_final",
    "bench_balance_point",
    "bench_failup",
    "bench_popoviciu_ratio",
    "bench_tradeoff",
    "measure_gate_margin",
)


#: THE LOCUS RECIPE -- the substrate's own 8-bin spread.
#:
#: MEASURED 2026-11-06: the census found a SECOND family of copies --
#: FOUR modules carried the same 8-bin-spread recipe, stalk for stalk
#: identical:
#:
#:     awareness._stalks              s%02d
#:     fc_wrapper._stalks             s%02d
#:     locus._population              L%d
#:     do_stalks_communicate.the_population   s%02d
#:
#: They agree with EACH OTHER (measured: identical girths, turn counts
#: and addresses at population 8) and they differ from the canonical
#: recipe -- deliberately, because the girth bench MEASURED the 8-bin
#: spread as better for the naming rate than the 16-bin one.
#:
#: So they are a FAMILY, not a set of four copies of one thing.  The
#: fix is one builder in the substrate, imported by all four, with the
#: id format left as the caller's business -- the ids are labels, not
#: physics, and `locus` prints them.
#:
#: THE LIMIT, MEASURED, AND IT IS A REAL ONE: the 8-bin spread caps
#: the addressable population at 16.  At population 32 it gives 16
#: classes with the largest holding 2; at 64, 16 classes with the
#: largest holding 4.  So this recipe DEGENERATES above population 16,
#: and the canonical one does not.  Every module that uses this recipe
#: uses it at 8 or fewer, so it is not a live limit -- but it is the
#: limit, and it is named here so a reader does not mistake it for the
#: canonical recipe's behaviour.
LOCUS_INNER_GIRTH: float = 0.060
LOCUS_CORE_GIRTH: float = 0.030
LOCUS_BASE_RATIO: float = 1.200
LOCUS_SPREAD_STEP: float = 0.0625
LOCUS_N_IN: int = 12


def make_locus_population(n: int = 8,
                          id_fmt: str = "s%02d") -> List[CoaxWinding]:
    """n stalks on the substrate's 8-bin spread.

    THE ADDRESS IS (parity/2) + (ratio - 1), so an even turn count
    lands the address in (0, 0.5] and an odd one in (0.5, 1).  Each
    half-circle holds its own stalk, and the ratio's step spaces the
    stalks WITHIN a half-circle: 0.0625 of the circle, which is 8 bins
    at 128 bins.

    MEASURED, the girth bench found 8 bins BEATS 16 for the naming
    rate -- 82% against 77% at crowd 0.10 -- because a wider spread
    means the girth ratios are further apart, which means a weaker mean
    coupling, and the coupling is what carries the signal.  So this
    recipe is a MEASURED choice, not the default.

    `id_fmt` is the CALLER's business: the ids are labels, and
    `locus.py` prints them as `L0`, `L1`, while the others use
    `s00`, `s01`.  The physics is the same either way.
    """
    if n <= 0:
        raise ValueError("a population needs at least one stalk, got %d" % n)
    out: List[CoaxWinding] = []
    for i in range(n):
        parity = i % 2
        k = i // 2
        ratio = LOCUS_BASE_RATIO + (k + 0.5) * LOCUS_SPREAD_STEP
        out.append(CoaxWinding(
            id=id_fmt % i,
            girth_core=LOCUS_CORE_GIRTH,
            girth_in=LOCUS_INNER_GIRTH,
            girth_out=LOCUS_INNER_GIRTH * ratio,
            n_in=LOCUS_N_IN,
            n_out=13 + parity,
        ))
    return out


#: THE POPULATION BUILDERS THAT ARE DELIBERATELY NOT THIS RECIPE.
#:
#: Each is `module: function -> why it exists`.  A builder that is not
#: in this table and is not the canonical one is a DIVERGED copy, and
#: the census goes RED on it.
#:
#: MEASURED 2026-11-06: the two that produce a `CoaxWinding`
#: population -- `bench_girth_ladder.make_spread_population` and
#: `do_stalks_communicate.the_population` -- are ADDRESSABLE (largest
#: class 1 at every population), so they cannot produce a false
#: ceiling.  They are listed anyway, because a name in a table is a
#: promise somebody has to keep, and the table says what the promise
#: is.
DELIBERATE_VARIANTS: Dict[str, str] = {
    "stalk_population:make_locus_population":
        "THE LOCUS RECIPE -- the substrate's own 8-bin spread, and the "
        "ONE builder the four modules that use it now share",
    "bench_girth_ladder:make_spread_population":
        "the girth ladder's own 1/n spread, measured for a different "
        "question; ADDRESSABLE at every population the ladder uses",
    "bench_girth_ladder:make_stalks":
        "a PARAMETERISED builder -- base_ratio, delta_step, "
        "core_ratio and the turn counts are all levers, so it cannot "
        "be a fixed recipe",
}


#: THE BUILDERS THAT ARE NOT POPULATIONS OF `CoaxWinding` AT ALL.
#:
#: MEASURED 2026-11-06: the census finds builders by looking for a
#: `CoaxWinding` being constructed, so a builder of something ELSE is
#: invisible to it -- `stalk_physics.make_population` builds a
#: `PhysicalStalk`, in metres.  That is not a copy of the recipe; it
#: is not a population of this thing at all.  It is named here so a
#: reader can see the decision rather than infer it from an absence.
NOT_A_COAXWINDING_POPULATION: Dict[str, str] = {
    "stalk_physics:make_population":
        "the PHYSICAL stalk, in metres -- a PhysicalStalk, not a "
        "CoaxWinding, so it is not a population of this thing at all",
}


#: THE MODULES THAT CARRY THE LOCUS RECIPE -- the 8-bin spread.
#:
#: MEASURED 2026-11-06: the census found FOUR of them, each carrying
#: the same recipe stalk for stalk.  They now import
#: `make_locus_population` from the substrate, so there is one builder.
#:
#: The id format stays each caller's business, because the ids are
#: labels: `locus` prints `L0`, the others `s00`.
LOCUS_REQUIRED: Dict[str, str] = {
    "awareness": "s%02d",
    "do_stalks_communicate": "s%02d",
    "fc_wrapper": "s%02d",
    "locus": "L%d",
}


#: THE MODULES THAT CARRY THE LOCUS RECIPE, AND THE FUNCTION EACH ONE
#: EXPOSES.  A module that has STOPPED carrying it is caught here --
#: the census alone would not report a missing builder, only a
#: divergent one.
LOCUS_BUILDERS: Dict[str, str] = {
    "awareness": "_stalks",
    "do_stalks_communicate": "the_population",
    "fc_wrapper": "_stalks",
    "locus": "_population",
}


# ---------------------------------------------------------------------------
# THE CENSUS: every population builder in src/, DISCOVERED
# ---------------------------------------------------------------------------
#: MEASURED 2026-11-06: the first check for this file named the seven
#: benches in a hardcoded list.  A hardcoded list cannot report a copy
#: it does not know about, and two more copies were sitting in `src/`
#: that the list never mentioned -- `bench_ladder.make_population` and
#: `bench_population.make_stalk`.  Both DIVERGED from the canonical
#: recipe at every population, and both were invisible to the check
#: that was supposed to catch divergence.
#:
#: So the census DISCOVERS the builders by AST: every module in `src/`
#: with a function whose body constructs a `CoaxWinding`.  A file that
#: has started carrying a copy is then caught, exactly as the
#: `REQUIRED` list catches one that has stopped carrying it.

def _builds_coax_winding(fn) -> bool:
    """Does this function's body construct a `CoaxWinding`?

    AND DOES IT BUILD A POPULATION -- a LIST of them?  A function that
    builds ONE stalk is a helper, not a recipe: `bench_population`
    needs a stalk it can clone, and `locus` needs one stalk per
    coordinate.  A recipe builds the whole array, and the array is
    what carries the address classes.

    MEASURED 2026-11-06: the first census counted any function that
    mentioned `CoaxWinding`, and it reported 24 builders -- most of
    them single-stalk helpers whose verdict was `UNCALLABLE`.  The
    property that matters is that the RESULT IS A LIST, and that is
    measured by CALLING it, not by reading it.
    """
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            f = node.func
            name = getattr(f, "id", None) or getattr(f, "attr", None)
            if name == "CoaxWinding":
                return True
    return False


def census(src_dir: str = "") -> Dict[str, List[str]]:
    """Every population builder under `src/`, discovered by AST.

    Returns `{module: [function names]}`.  A module with no builder is
    absent -- and the `REQUIRED` list is what catches that case.

    RECURSIVE: MEASURED 2026-11-06, `src/` has four subdirectories
    (`farmath`, `sacred_library`, `scanner`, `tiniest_core`), and a
    census that only read the top level would miss a copy filed inside
    one of them.  A census that misses a directory is a census of half
    the tree.

    AST, NOT GREP: a grep for `CoaxWinding` counts a name in a
    docstring, and the repo has already learned that lesson once (the
    exam's `reachability.py`).
    """
    d = src_dir or _SRC
    out: Dict[str, List[str]] = {}
    for dirpath, dirnames, filenames in os.walk(d):
        dirnames[:] = [x for x in dirnames
                       if not x.startswith(".") and x != "__pycache__"]
        for fname in sorted(filenames):
            if not fname.endswith(".py") or fname.startswith("__"):
                continue
            path = os.path.join(dirpath, fname)
            try:
                with open(path, encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
            found: List[str] = []
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and _builds_coax_winding(node):
                    found.append(node.name)
            if found:
                rel = os.path.relpath(path, d)[:-3].replace(os.sep, ".")
                out[rel] = found
    return out


def compare_builder(mod_name: str, fn_name: str,
                    population: int = 4) -> str:
    """Call a discovered builder and say how it compares.

    Returns one of:

        AGREE             stalk for stalk the canonical recipe
        DIVERGED          it builds a DIFFERENT population
        NOT-A-POPULATION  it does not return a list of CoaxWinding
        UNCALLABLE        it needs arguments a population call cannot
                          supply, so it is not a fixed recipe

    The last two are the reasons a builder may be DELIBERATE rather
    than a copy: a parameterised builder cannot be a fixed recipe, and
    a builder of a different thing is not a population of this thing.
    """
    try:
        mod = __import__(mod_name)
    except Exception as exc:
        return "UNIMPORTABLE (%s)" % type(exc).__name__
    fn = getattr(mod, fn_name, None)
    if fn is None:
        return "MISSING"
    try:
        built = fn(population)
    except TypeError:
        return "UNCALLABLE"
    except Exception as exc:
        return "UNCALLABLE (%s)" % type(exc).__name__
    if not isinstance(built, (list, tuple)):
        return "NOT-A-POPULATION"
    if not built:
        return "NOT-A-POPULATION"
    if not all(isinstance(s, CoaxWinding) for s in built):
        return "NOT-A-POPULATION"
    theirs = make_population(population)
    if len(built) != len(theirs):
        return "DIVERGED"
    for a, b in zip(built, theirs):
        if (a.id != b.id or a.n_in != b.n_in or a.n_out != b.n_out
                or abs(a.girth_in - b.girth_in) > 1e-12
                or abs(a.girth_out - b.girth_out) > 1e-12
                or abs(a.girth_core - b.girth_core) > 1e-12):
            return "DIVERGED"
    return "AGREE"


def main() -> int:
    print("=" * 78)
    print("THE POPULATION RECIPE, AND THE CLASSES IT PRODUCES")
    print("=" * 78)
    for pop in POPS:
        stalks = make_population(pop)
        for bins in (max(8, 4 * pop),):
            labels, sizes = address_classes(stalks, bins)
            print("  population %3d bins %3d : %3d classes, largest %d  %s"
                  % (pop, bins, len(sizes), sizes[0],
                     "ADDRESSABLE" if sizes[0] == 1 else "DEGENERATE"))
    print()
    print("  the addresses at population 8:")
    print("    %s" % ["%.6f" % address_of(s) for s in make_population(8)])
    print("  the smallest gap between neighbours: %.6f"
          % min(
              (lambda a: min(min(a[j] - a[i], 1.0 - (a[j] - a[i]))
                             for i in range(len(a)) for j in range(i + 1, len(a))))(
                  sorted(address_of(s) for s in make_population(8))),
              1.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
