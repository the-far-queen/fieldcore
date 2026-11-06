#!/usr/bin/env python3
"""
check_population_recipe.py -- THE CHECK THAT THE RECIPE IS ONE RECIPE.

MEASURED 2026-11-05: seven files in fieldcore/src each carried their own
copy of `make_population`, and the copies had DIVERGED into two
behaviours.  Four of them put every stalk in its own address class and
three of them collapsed the population into a couple of classes -- and
the repo's own `bench_tradeoff.py` docstring already called the
collapsing one a CONFOUND, while the published "population code's real
ceiling" was measured on it.

A copy is a promise that somebody will remember to update it.  Seven
copies is seven promises, and one of them was already broken.

WHAT THIS CHECKS
----------------
  1. EVERY required bench's `make_population` produces the SAME
     population as the canonical one -- stalk for stalk, geometry for
     geometry -- and its `address_of` agrees with the canonical one.
  1b. THE CENSUS: every population builder in `src/`, DISCOVERED by
     AST.  A builder that is neither the canonical one nor a NAMED
     deliberate variant is an UNNAMED COPY and goes RED.  A named
     variant that no longer exists is a STALE NAME and goes RED too.

     MEASURED 2026-11-06: the first version of this check used a
     HARDCODED LIST of the seven benches.  A list cannot report a copy
     it does not know about, and TWO MORE COPIES were sitting in
     `src/` -- `bench_ladder.make_population` and
     `bench_population.make_stalk` -- both DIVERGED from the canonical
     recipe at every population, both invisible to the check that was
     supposed to catch divergence.
  2. The canonical population is ADDRESSABLE: every stalk is in its own
     address class, at every population the benches sweep.  A recipe
     that collapses the population cannot measure a CHANNEL limit, so
     this is the check that would have caught the confound.
  3. The canonical `address_of` agrees with the SUBSTRATE's own two
     derivations: `interstalk_link._address` and
     `wound_core.WoundCore.population()`.  Two derivations, one number
     -- and a third copy that has drifted goes RED.

WHY IT IS A SEPARATE TOOL AND NOT A TEST
-----------------------------------------
Because it must be RUN against the bench files as they are, from the
outside, and report per-file.  `tests/test_stalk_population.py` asserts
the same properties from inside the suite; this tool is what a reader
runs to see the divergence itself.

Run:
    python tools/check_population_recipe.py
    python tools/check_population_recipe.py --all-agree
"""

from __future__ import annotations

import argparse
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(_HERE), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import stalk_population as SP  # noqa: E402

#: The populations the benches sweep, and the bins each uses.
SWEEP = ((2, 32), (3, 32), (4, 32), (8, 64), (16, 64), (32, 128),
         (64, 256))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all-agree", action="store_true",
                    help="exit non-zero unless every check passes")
    args = ap.parse_args()

    ok = True
    print("=" * 78)
    print("1. THE CENSUS: EVERY POPULATION BUILDER IN src/, DISCOVERED")
    print("=" * 78)
    print()
    print("  MEASURED 2026-11-06: the first version of this check named")
    print("  the seven benches in a HARDCODED LIST.  A list cannot report")
    print("  a copy it does not know about, and TWO MORE COPIES were")
    print("  sitting in src/ that the list never mentioned -- both")
    print("  DIVERGED from the canonical recipe at every population.")
    print("  So the builders are now DISCOVERED by AST, and the list")
    print("  only says which benches must still CARRY the recipe.")
    print()
    agree = 0
    for name in SP.REQUIRED:
        try:
            mod = __import__(name)
        except Exception as exc:
            print("  %-24s IMPORT FAILED: %s" % (name, exc))
            ok = False
            continue
        if not hasattr(mod, "make_population"):
            print("  %-24s NO make_population -- the recipe was DROPPED"
                  % name)
            ok = False
            continue
        same = True
        for pop in SP.POPS:
            mine = mod.make_population(pop)
            theirs = SP.make_population(pop)
            if len(mine) != len(theirs):
                same = False
                break
            for a, b in zip(mine, theirs):
                if (a.id != b.id or a.n_in != b.n_in or a.n_out != b.n_out
                        or abs(a.girth_in - b.girth_in) > 1e-12
                        or abs(a.girth_out - b.girth_out) > 1e-12
                        or abs(a.girth_core - b.girth_core) > 1e-12):
                    same = False
                    break
            if not same:
                break
        # and the ADDRESS derivation
        addr_same = True
        if hasattr(mod, "address_of"):
            for s in SP.make_population(8):
                if abs(mod.address_of(s) - SP.address_of(s)) > 1e-15:
                    addr_same = False
                    break
        else:
            addr_same = None
        status = "AGREE" if same and addr_same is not False else "DIVERGED"
        print("  %-24s population %s   address_of %s"
              % (name, "AGREE" if same else "DIVERGED",
                 ("AGREE" if addr_same else "DIVERGED")
                 if addr_same is not None else "absent"))
        if same and addr_same is not False:
            agree += 1
        else:
            ok = False
    print()
    print("  %d of %d required benches agree with the canonical recipe"
          % (agree, len(SP.REQUIRED)))
    print()
    print("=" * 78)
    print("1b. EVERY OTHER BUILDER IN src/, DISCOVERED")
    print("=" * 78)
    print()
    print("  A builder that is NOT the canonical one and NOT named as a")
    print("  DELIBERATE VARIANT is a DIVERGED copy, and it goes RED.")
    census = SP.census()
    seen = set()
    for mod_name in sorted(census):
        for fn_name in census[mod_name]:
            key = "%s:%s" % (mod_name, fn_name)
            seen.add(key)
            verdict = SP.compare_builder(mod_name, fn_name)
            if verdict == "AGREE":
                continue
            if verdict in ("NOT-A-POPULATION", "UNCALLABLE") or \
                    verdict.startswith("UNCALLABLE"):
                # not a fixed recipe: it builds one stalk, or it needs
                # arguments a population call cannot supply
                continue
            note = SP.DELIBERATE_VARIANTS.get(key)
            if note:
                print("  %-46s %-12s DELIBERATE" % (key, verdict))
                print("      %s" % note)
                continue
            print("  %-46s %-12s UNNAMED COPY -- the census goes RED"
                  % (key, verdict))
            ok = False
    print()
    print("=" * 78)
    print("1c. THE LOCUS FAMILY: FOUR MODULES, ONE BUILDER")
    print("=" * 78)
    print()
    print("  MEASURED 2026-11-06: the census found a SECOND family -- four")
    print("  modules carried the same 8-bin-spread recipe, identical stalk")
    print("  for stalk.  They now share ONE builder in the substrate.")
    for mod_name in sorted(SP.LOCUS_BUILDERS):
        fn_name = SP.LOCUS_BUILDERS[mod_name]
        try:
            mod = __import__(mod_name)
        except Exception as exc:
            print("  %-24s IMPORT FAILED: %s" % (mod_name, exc))
            ok = False
            continue
        if not hasattr(mod, fn_name):
            print("  %-24s NO %s -- the locus recipe was DROPPED"
                  % (mod_name, fn_name))
            ok = False
            continue
        got = getattr(mod, fn_name)(8)
        want = SP.make_locus_population(8, id_fmt=SP.LOCUS_REQUIRED[mod_name])
        same = (len(got) == len(want) and all(
            a.id == b.id and a.n_in == b.n_in and a.n_out == b.n_out
            and abs(a.girth_in - b.girth_in) < 1e-12
            and abs(a.girth_out - b.girth_out) < 1e-12
            and abs(a.girth_core - b.girth_core) < 1e-12
            for a, b in zip(got, want)))
        print("  %-24s %-22s %s"
              % (mod_name, fn_name, "AGREE" if same else "DIVERGED"))
        if not same:
            ok = False
    print()
    print("  the locus recipe's own limit, MEASURED: the 8-bin spread")
    print("  caps the addressable population at 16 -- at 32 it gives 16")
    print("  classes with the largest holding 2, at 64 the largest 4.")
    print("  Every module that uses it uses it at 8 or fewer.")
    print()
    unknown = [k for k in SP.DELIBERATE_VARIANTS if k not in seen]
    if unknown:
        print("  DELIBERATE VARIANTS that no longer exist (stale names):")
        for k in sorted(unknown):
            print("      %s" % k)
        ok = False
    else:
        print("  every named DELIBERATE VARIANT still exists -- no stale "
              "names")
    print()

    print()
    print("=" * 78)
    print("2. THE CANONICAL POPULATION IS ADDRESSABLE")
    print("=" * 78)
    print("  (a recipe that collapses the population cannot measure a")
    print("   CHANNEL limit -- so this is the check that catches a")
    print("   confound before it is published as a ceiling)")
    for pop, bins in SWEEP:
        stalks = SP.make_population(pop)
        labels, sizes = SP.address_classes(stalks, bins)
        good = sizes[0] == 1
        print("  population %3d bins %3d : %3d classes, largest %d  %s"
              % (pop, bins, len(sizes), sizes[0],
                 "ADDRESSABLE" if good else "DEGENERATE -- CONFOUND"))
        if not good:
            ok = False

    print()
    print("=" * 78)
    print("3. THE ADDRESS DERIVATION: THREE COPIES, ONE NUMBER")
    print("=" * 78)
    try:
        from interstalk_link import InterstalkLink
        from wound_core import WoundCore
        stalks = SP.make_population(8)
        link = InterstalkLink(core=WoundCore(stalks=stalks), bins=64)
        worst_link = 0.0
        worst_pop = 0.0
        for s in stalks:
            canonical = SP.address_of(s)
            worst_link = max(worst_link,
                             abs(InterstalkLink._address(link.stalk(s.id))
                                 - canonical))
        phases = [st.phase for st in
                  WoundCore(stalks=stalks).population().strata]
        for canonical, phase in zip((SP.address_of(s) for s in stalks),
                                    phases):
            worst_pop = max(worst_pop, abs(phase - canonical))
        print("  canonical vs interstalk_link._address : max |diff| = %.3e"
              % worst_link)
        print("  canonical vs wound_core.population    : max |diff| = %.3e"
              % worst_pop)
        if worst_link > 1e-15 or worst_pop > 1e-15:
            ok = False
    except Exception as exc:
        print("  COULD NOT MEASURE: %s" % exc)
        ok = False

    print()
    print("=" * 78)
    print("VERDICT")
    print("=" * 78)
    print("  %s" % ("PASS" if ok else "FAIL"))
    if args.all_agree:
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
