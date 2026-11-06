#!/usr/bin/env python3
"""
wiring_census.py -- THE WIRING CENSUS OF THE WHOLE FC.

Bobby, 2026-11-06: *"main thing is to get the whole fc wires all
modules"*, *"the sheafs are a team its all one fc"*, and *"fc is just
multiple control loops"*.

WHY A CENSUS AND NOT ANOTHER LIST. The project already has three
inventories -- `fc_app.py`'s ten LETTERS, `src/control_loops.py`'s loop
REGISTRY, and the atlas exam's REACHABILITY area. Each one names a
hand-picked set, so each one can be complete while the SYSTEM is not.
The lettered modules are all reachable; nothing says the other 350
modules are.

So this is the census: EVERY module in the four repos, measured, and
sorted into three bins.

    WIRED     something imports it (or it imports something that does)
    ENTRY     nothing imports it and that is CORRECT -- it is a bench,
              a probe, a check, a script, a CLI. It is run from a
              shell, so an inbound import is not what makes it real.
    ORPHAN    nothing imports it AND it is not an entry point. A
              capability that cannot be reached, so it cannot fail.

**AND THE BIN IS THE FINDING, NOT THE COUNT.** A module that nobody
imports may be a bench (fine) or the answer to a question nobody asks
(fine) or a gate that guards nothing (not fine). The census does not
decide which -- it says WHICH, so a human or a session can. The
project's own rule applies: a module is either WIRED or it is NAMED.

AST, NOT GREP
-------------
The exam's `reachability.py` already learned this: a grep version
counted a name in a docstring and reported a gone module as wired. So
the census parses every file and resolves REAL imports --

    from x import NAME       counted (module x AND name NAME)
    import x                 counted
    import a.b               counted (a.b and a)
    x.NAME (attribute)       counted
    a NAME inside a docstring NOT counted

and it counts an inbound reference only when the importing file is
ITSELF reachable from an entry point, so a dead-end island does not
make a module look wired.

THE ENTRY-POINT RULE, and it is a LIST OF SHAPES, NOT A LIST OF FILES.
A filename cannot be trusted (a capability called `probe_x.py` is not
a probe). So an entry point is a file that

  1  has a `__main__` guard, OR
  2  is under a `tools/` directory, OR
  3  is named `bench_*`, `probe_*`, `measure_*`, `check_*`,
     `mutation_check_*`, `demo*`, `run_*`, `scan*`, `curate_*`

and the reason it is an entry point is reported, so the classification
can be argued with.

Run:
    python tools/wiring_census.py
    python tools/wiring_census.py --json
    python tools/wiring_census.py --orphans
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORK_REPOS = os.path.dirname(REPO)
HERMES = os.path.expanduser("~/AppData/Local/hermes")

#: WHERE THE REPOS ARE, and it can be overridden.
#:
#: AND WHY IT NEEDS AN OVERRIDE. The census reads the OTHER repos, so
#: it must find them even when the census file itself has been COPIED
#: somewhere else -- which is exactly what the mutation harness does.
#: The first version derived the repos from the script's own location,
#: so the copy in a temp directory looked at a directory with no repos
#: in it and reported ZERO modules. The harness then compared zero
#: against zero and declared every mutation caught, which is the
#: classic defect: a check that passes because both sides are empty.
#:
#: So the repos are found by an ENV VAR first, then by the documented
#: default, and the harness sets the var.
FC_WORK_REPOS = os.environ.get("FC_WORK_REPOS", "").strip()
if FC_WORK_REPOS:
    WORK_REPOS = FC_WORK_REPOS
else:
    _default = os.path.join(HERMES, "work_repos")
    if not os.path.isdir(os.path.join(WORK_REPOS, "fieldcore")) \
            and os.path.isdir(_default):
        WORK_REPOS = _default

#: The four repos of the fc, and the source roots inside each.
FC_REPOS: Tuple[str, ...] = ("fieldcore", "simself", "far-coding",
                             "atlas-exam")

#: The roots scanned in each repo. `src` is the substrate; `tools` is
#: the bench surface.
FC_ROOTS: Tuple[str, ...] = ("src", "tools")

#: A file whose name starts with one of these is an ENTRY POINT unless
#: something else says otherwise. The list is a list of SHAPES.
ENTRY_PREFIXES: Tuple[str, ...] = (
    "bench_", "probe_", "measure_", "check_", "mutation_check_",
    "demo", "run_", "scan", "curate_", "extract_", "shortlist",
    "apply_canonical",
)

#: A file whose name starts with one of these is a SCRIPT, not a
#: capability, and is not counted as an orphan even if nothing imports
#: it. `__init__.py` is the same.
SCRIPT_NAMES: Tuple[str, ...] = ("__init__.py", "setup.py", "conftest.py")


@dataclass
class Module:
    """One python file, and what the census found about it."""
    path: str                      # absolute
    rel: str                       # relative to the repo root
    repo: str
    stem: str                      # module name without .py
    dotted: str                    # repo-relative dotted name
    #: the PACKAGE this module lives in, as a list of parts. For a
    #: package's own `__init__.py` the package is ITSELF, which is
    #: the case a relative import depends on.
    pkg_parts: List[str] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)     # module names
    attr_refs: Set[str] = field(default_factory=set)    # x.NAME
    #: module names named in STRINGS -- a dynamic import, or a
    #: registry table's `module="..."` entry. Counted only when the
    #: name matches a module the census knows.
    dynamic: Set[str] = field(default_factory=set)
    has_main: bool = False
    is_tools: bool = False
    matched_entry_prefix: str = ""
    inbound: List[str] = field(default_factory=list)    # importing files
    reachable: bool = False
    #: TRUE when this module's bare stem names MORE THAN ONE module
    #: in the tree. A reference by that stem is ambiguous, so it is
    #: counted for neither -- and the census says so.
    stem_ambiguous: bool = False
    #: TRUE when this module is a PACKAGE's own `__init__.py`.
    is_package_init: bool = False
    #: the package this module lives in (its dotted prefix), or "".
    package: str = ""

    @property
    def entry_reason(self) -> str:
        if self.has_main:
            return "has a __main__ guard"
        if self.is_tools:
            return "lives under tools/"
        if self.matched_entry_prefix:
            return "named %s* (a bench or a probe)" % self.matched_entry_prefix
        return ""

    @property
    def is_entry(self) -> bool:
        return bool(self.entry_reason)

    @property
    def bin(self) -> str:
        """WIRED, ISLAND, ENTRY, or ORPHAN.

        **AND THE FOUR BINS, because three was not enough.** The third
        bin was "WIRED" for anything with an inbound reference, and
        that counted a DEAD-END ISLAND as wired: module A imports
        module B, and nothing imports A, so B has an inbound reference
        and is unreachable. A capability inside such a chain cannot
        fail either, and it must not be counted as wired.

            WIRED   something REACHABLE imports it
            ISLAND  something imports it, but nothing reachable does,
                    so the whole chain floats free of the system
            ENTRY   nothing imports it and that is correct -- it is a
                    bench, a probe, a check, a script
            ORPHAN  nothing imports it and it is not an entry point
        """
        if self.inbound:
            return "WIRED" if self.reachable else "ISLAND"
        if self.is_entry:
            return "ENTRY"
        return "ORPHAN"

    def to_dict(self) -> Dict:
        return {
            "repo": self.repo,
            "path": self.rel,
            "stem": self.stem,
            "bin": self.bin,
            "entry_reason": self.entry_reason,
            "inbound": len(self.inbound),
            "reachable": self.reachable,
            "stem_ambiguous": self.stem_ambiguous,
        }


# ===========================================================================
# THE PARSE
# ===========================================================================

def _module_name(rel: str) -> str:
    """`src/foo/bar.py` -> `foo.bar`; `src/foo/__init__.py` -> `foo`."""
    rel = rel.replace("\\", "/")
    if rel.endswith("/__init__.py"):
        rel = rel[: -len("/__init__.py")]
    elif rel.endswith(".py"):
        rel = rel[:-3]
    parts = [p for p in rel.split("/") if p]
    if parts and parts[0] in FC_ROOTS:
        parts = parts[1:]
    return ".".join(parts)


def _scan_file(path: str, rel: str, repo: str) -> Optional[Module]:
    try:
        src = open(path, encoding="utf-8", errors="ignore").read()
    except OSError:
        return None
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    m = Module(path=path, rel=rel, repo=repo,
               stem=os.path.splitext(os.path.basename(path))[0],
               dotted=_module_name(rel))
    m.is_tools = "/tools/" in rel.replace("\\", "/")
    if m.stem == "__init__":
        # a package's own init: the package IS its dotted name
        m.pkg_parts = [p for p in m.dotted.split(".") if p]
        m.is_package_init = True
        m.package = m.dotted
    else:
        m.pkg_parts = [p for p in m.dotted.split(".")[:-1] if p]
        m.package = ".".join(m.pkg_parts)
    for pref in ENTRY_PREFIXES:
        if m.stem.startswith(pref):
            m.matched_entry_prefix = pref
            break
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level:                       # relative import
                # `from .result import X` in `exam/adversarial.py`
                # means `exam.result`.
                #
                # AND THE LEVEL ARITHMETIC WAS WRONG AT FIRST: it
                # stripped `level - 1` components, so a single dot
                # (`level == 1`) kept the module's OWN name in the
                # prefix and produced `exam.adversarial.result`. No
                # such module exists, so every relative import in the
                # exam counted as a reference to nothing -- and the
                # census reported `exam/result.py` as an ORPHAN while
                # NINE files import it. A census that misses the most
                # common import form in python is not a census.
                #
                # The rule, and it is stated from the PACKAGE and not
                # from the module: level 1 is this module's own
                # package, level 2 is its parent's package, and so on.
                # So strip `level - 1` components from the PACKAGE.
                #
                # AND THE PACKAGE IS NOT ALWAYS THE MODULE'S PARENT.
                # For `pkg/__init__.py` the package IS `pkg`, so
                # `from . import x` there means `pkg.x` and NOT `x`.
                # Getting that wrong lost every `from . import x`
                # in the tree -- six of them, including the exam's own
                # `from . import substrate as sub`, which is the
                # substrate the exam grades. The fixture tree has one
                # of each shape so this cannot regress quietly.
                parts = m.pkg_parts
                up = node.level - 1
                prefix_parts = parts[:len(parts) - up] if len(parts) >= up else []
                prefix = ".".join(prefix_parts)
                if mod:
                    target = (prefix + "." + mod) if prefix else mod
                    m.imports.add(target)
                    # AND THE TOP-LEVEL NAME IS **NOT** ADDED HERE, and
                    # that is a fix, not an omission.
                    #
                    # MEASURED 2026-11-06: the relative branch used to
                    # add `target.split(".")[0]` as well, so
                    # `from .result import helper` in `pkg/mod_rel.py`
                    # also added the name `pkg`. And `pkg/__init__.py`
                    # then read as IMPORTED by `pkg/mod_rel.py`, so the
                    # package's own init came out WIRED when it is
                    # reached by nothing. The fixture tree has the
                    # decoy for exactly this: the census must not
                    # invent an edge to a package's init.
                    #
                    # The absolute branch still adds the top-level
                    # name, because `import constitutional.mte` DOES
                    # make `constitutional` a referenced module.
                else:
                    # `from . import x` -- x is a MODULE, and there is
                    # no module attribute to read it from
                    for a in node.names:
                        t = (prefix + "." + a.name) if prefix else a.name
                        m.imports.add(t)
            else:
                if mod:
                    m.imports.add(mod)
                    m.imports.add(mod.split(".")[0])
                for a in node.names:
                    m.imports.add(a.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                m.imports.add(a.name)
                m.imports.add(a.name.split(".")[0])
        elif isinstance(node, ast.Attribute):
            m.attr_refs.add(node.attr)
        elif isinstance(node, ast.Call):
            # A DYNAMIC IMPORT, and the census was WRONG without it.
            #
            # MEASURED 2026-11-06: the first version of this census
            # reported `fieldcore/src/adversarial_brain.py` as an
            # ORPHAN -- a capability nothing reaches -- while
            # `fieldcore/src/control_loops.py` loads it with
            # `importlib.import_module(entry.module)`. The registry
            # names the module in a STRING, so an AST walk over import
            # statements never sees it. A census that calls a
            # dynamically-imported module an orphan is a census that
            # reports the wrong thing confidently, which is worse than
            # saying nothing.
            #
            # So two dynamic shapes are counted:
            #
            #   importlib.import_module("name")   a literal argument
            #   LoopEntry(module="name")          a registry table
            #
            # and the name is only counted if it MATCHES a module the
            # census knows, so a stray string cannot invent an edge.
            fn = node.func
            fname = ""
            if isinstance(fn, ast.Attribute):
                fname = fn.attr
            elif isinstance(fn, ast.Name):
                fname = fn.id
            if fname == "import_module" and node.args:
                a0 = node.args[0]
                if isinstance(a0, ast.Constant) and isinstance(a0.value, str):
                    m.dynamic.add(a0.value)
            if fname == "import_module" and node.args:
                continue
        elif isinstance(node, ast.keyword):
            # a registry table's `module="name"` entry
            if node.arg == "module" and isinstance(node.value, ast.Constant) \
                    and isinstance(node.value.value, str):
                m.dynamic.add(node.value.value)
        elif isinstance(node, ast.If):
            # a `__main__` guard
            test = node.test
            if isinstance(test, ast.Compare):
                left = test.left
                if (isinstance(left, ast.Name) and left.id == "__name__"
                        and any(isinstance(c, ast.Constant) and c.value == "__main__"
                                for c in test.comparators)):
                    m.has_main = True
    return m


def census(repos: Sequence[str] = FC_REPOS,
           roots: Sequence[str] = FC_ROOTS,
           work_repos: Optional[str] = None) -> List[Module]:
    """Every module in the fc, measured.

    AND `work_repos` IS A PARAMETER, because the mutation harness
    needs to run the census over a FIXTURE tree with a known shape.
    MEASURED 2026-11-06: the first version of the harness ran the
    census over the REAL tree and asserted that the counts moved. Two
    of the five mutations then "failed" for the wrong reason -- they
    moved a DIFFERENT count, because the real tree is too big and too
    noisy to attribute a change to one rule. A fixture with one
    example of each shape gives every mutation exactly one thing it
    can break, and the assertion names WHICH module's bin must move.
    """
    # AND THE TWO ROOTS HAVE DIFFERENT NAMES, because one name was
    # used for both and the second assignment clobbered the first.
    #
    # MEASURED 2026-11-06: the census reported 212 modules in ONE
    # repo, and every run agreed, so it looked like a settled
    # measurement. The cause: the repos root was called `base`, and so
    # was the per-repo source root, and the inner assignment ran
    # BEFORE the outer one was read again on the next iteration -- so
    # repo 2 was looked for under `fieldcore/src`. A census that
    # silently surveys one repo and calls it the whole fc is worse
    # than no census, because the number looks measured.
    repo_root = work_repos or WORK_REPOS
    mods: List[Module] = []
    for repo in repos:
        rdir = os.path.join(repo_root, repo)
        if not os.path.isdir(rdir):
            continue
        for root in roots:
            src_root = os.path.join(rdir, root)
            if not os.path.isdir(src_root):
                continue
            for dirpath, dirnames, filenames in os.walk(src_root):
                # `__pycache__` is noise, and a DOTTED directory is
                # not part of the tree -- `fieldcore/src/.simself/`
                # is a scratch copy, and counting it makes the census
                # report a module that does not exist as far as anyone
                # importing the tree is concerned.
                dirnames[:] = [d for d in dirnames
                               if d != "__pycache__" and not d.startswith(".")]
                for f in filenames:
                    if not f.endswith(".py"):
                        continue
                    path = os.path.join(dirpath, f)
                    rel = os.path.relpath(path, rdir).replace("\\", "/")
                    m = _scan_file(path, rel, repo)
                    if m is None:
                        continue
                    mods.append(m)

    # -- the inbound edges -------------------------------------------------
    # A reference to `foo` counts if the importer mentions `foo` as an
    # import, or as an attribute of the module `foo`.
    # THE STEM INDEX, and it is what makes a bare name safe.
    #
    # fieldcore's modules import each other FLATLY (`import fc_gate`),
    # because the src directory is on sys.path. So a reference by bare
    # stem is the normal case and must count. But a bare stem that
    # names TWO modules is ambiguous, and counting it for both is how
    # a census invents edges.
    #
    # MEASURED 2026-11-06: the fixture tree has `pkg/result.py` and
    # `other/result.py` -- the same leaf name in two packages. A
    # relative import that resolves to the wrong place names the stem
    # "result", and with a naive stem match BOTH modules read as
    # referenced. So a bare stem counts only when it is UNIQUE, and an
    # ambiguous one counts for neither -- and the module is flagged so
    # the census can say why.
    stem_index: Dict[str, List[Module]] = {}
    for m in mods:
        stem_index.setdefault(m.stem, []).append(m)

    for m in mods:
        m.stem_ambiguous = len(stem_index.get(m.stem, [])) > 1
        for other in mods:
            if other is m:
                continue
            names = set(other.imports) | set(other.attr_refs) | set(other.dynamic)
            hit = None
            # (a) the DOTTED name matches exactly
            if m.dotted in names:
                hit = m.dotted
            # (b) the bare STEM matches, and it is UNIQUE in the tree
            if hit is None and m.stem in names and not m.stem_ambiguous:
                hit = m.stem
            if hit is None:
                continue
            m.inbound.append(other.rel)

    # -- the reachability closure -----------------------------------------
    # A module is REACHABLE if it is an entry point, or if something
    # reachable imports it. Entry points are the roots of the graph.
    #
    # AND THE CLOSURE HAS TO RUN TWICE, because of the PACKAGE RULE
    # below: importing `services.kokoro_tts` EXECUTES
    # `services/__init__.py` first, so a package's own init is reached
    # whenever any of its children is reached.
    changed = True
    while changed:
        changed = False
        for m in mods:
            if m.reachable:
                continue
            if m.is_entry:
                m.reachable = True
                changed = True
                continue
            for imp_rel in m.inbound:
                imp = next((x for x in mods if x.rel == imp_rel), None)
                if imp is not None and imp.reachable:
                    m.reachable = True
                    changed = True
                    break

    # -- the PACKAGE RULE -------------------------------------------------
    # MEASURED 2026-11-06: without it the census reported 12 package
    # `__init__.py` files as ORPHANS -- `simself/src/services/`,
    # `simself/src/demos/`, `atlas-exam`-adjacent packages and so on.
    # Every one of them IS reached: python executes a package's init
    # before any of its children, so `from services.kokoro_tts import
    # X` runs `services/__init__.py` on the way.
    #
    # And the rule is the OTHER WAY ROUND too: a package init that is
    # reached makes its children reachable IF it imports them, which
    # the ordinary edge already says.
    changed = True
    while changed:
        changed = False
        for m in mods:
            if not m.is_package_init or m.reachable:
                continue
            for child in mods:
                if child is m or not child.package:
                    continue
                if child.package != m.dotted:
                    continue
                if child.reachable:
                    m.reachable = True
                    m.inbound.append(child.rel + " (its package)")
                    changed = True
                    break
    return mods


# ===========================================================================
# THE REPORT
# ===========================================================================

def summarise(mods: Sequence[Module]) -> Dict:
    by_repo: Dict[str, Dict[str, int]] = {}
    for m in mods:
        r = by_repo.setdefault(m.repo, {"WIRED": 0, "ISLAND": 0,
                                        "ENTRY": 0, "ORPHAN": 0})
        r[m.bin] += 1
    orphans = [m for m in mods if m.bin == "ORPHAN"]
    islands = [m for m in mods if m.bin == "ISLAND"]
    return {
        "total": len(mods),
        "wired": sum(1 for m in mods if m.bin == "WIRED"),
        "island": len(islands),
        "entry": sum(1 for m in mods if m.bin == "ENTRY"),
        "orphan": len(orphans),
        "by_repo": by_repo,
        #: EVERY module and its bin. The mutation harness reads this,
        #: so a bin that moves is visible by name and not only in a
        #: count.
        "rows": [m.to_dict() for m in mods],
        "orphans": [m.to_dict() for m in orphans],
        "islands": [m.to_dict() for m in islands],
    }


def _print_report(s: Dict, mods: Sequence[Module]) -> None:
    print("=" * 78)
    print("THE WIRING CENSUS OF THE WHOLE FC")
    print("=" * 78)
    print()
    print("  %d modules across %d repos" % (s["total"], len(s["by_repo"])))
    print("    WIRED   %d   imported by something reachable" % s["wired"])
    print("    ISLAND  %d   imported only by unreachable code"
          % s["island"])
    print("    ENTRY   %d   run from a shell, so no import is expected"
          % s["entry"])
    print("    ORPHAN  %d   nothing imports them and they are not entries"
          % s["orphan"])
    print()
    for repo, counts in sorted(s["by_repo"].items()):
        print("  %-12s wired %3d  island %2d  entry %3d  orphan %3d  of %3d"
              % (repo, counts["WIRED"], counts["ISLAND"], counts["ENTRY"],
                 counts["ORPHAN"], sum(counts.values())))
    print()
    if s["orphan"] or s["island"]:
        print("-" * 78)
        print("THE UNREACHED -- a capability nobody reaches cannot fail")
        print("-" * 78)
        by_repo: Dict[str, List[Module]] = {}
        for m in mods:
            if m.bin in ("ORPHAN", "ISLAND"):
                by_repo.setdefault(m.repo, []).append(m)
        for repo in sorted(by_repo):
            print()
            print("  %s" % repo)
            for m in sorted(by_repo[repo], key=lambda x: x.rel):
                print("    %-9s %s" % (m.bin, m.rel))
        print()
        print("  EVERY UNREACHED MODULE IS EITHER WIRED OR NAMED. The census")
        print("  does not decide which -- that is a session's call, and the")
        print("  naming is what makes the gap visible.")
    print()
    print("=" * 78)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true",
                    help="print the census as JSON")
    ap.add_argument("--orphans", action="store_true",
                    help="print only the orphan paths, one per line")
    ap.add_argument("--repo", action="append",
                    help="limit to a repo (repeatable)")
    ap.add_argument("--work-repos", default=None,
                    help="the directory that holds the repos (for the "
                         "fixture tree)")
    args = ap.parse_args(argv)

    repos = tuple(args.repo) if args.repo else FC_REPOS
    mods = census(repos=repos, work_repos=args.work_repos)
    s = summarise(mods)

    if args.orphans:
        for m in mods:
            if m.bin in ("ORPHAN", "ISLAND"):
                print("%s/%s" % (m.repo, m.rel))
        return 0
    if args.json:
        print(json.dumps(s, indent=2))
        return 0
    _print_report(s, mods)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
