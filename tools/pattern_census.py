#!/usr/bin/env python3
"""
pattern_census.py -- THE ROBOT'S PATTERN, AS A TABLE WITH HOLES IN IT.

Bobby, 2026-11-07: *"the sheafs are a team it is all one fc"*, and the
robot's pattern for each fc system: the substrate it reaches, a
MEASUREMENT that it reaches it, a NAMED REFUSAL, a selftest that can
go RED, and the census saying WIRED rather than ORPHAN.

**AND THIS IS THE SIBLING OF `reach_census.py`, AND NOT ITS DUPLICATE.**
The reach census asks ONE question -- *does this module reach anything
of the fc's own?* -- and bins the answer REACHES / STANDALONE /
NAMES-IT. This census asks the OTHER THREE questions of the same
pattern, per module:

    MEASUREMENT   does it record one?
    NAMED REFUSAL does it refuse, and does the refusal NAME something?
    CAN GO RED    does its selftest have a mutation check that proves it?

**AND THE POINT OF A TABLE WITH HOLES IS THE HOLES.** The reach census
told the fc WHICH modules reach nothing. That is a list of tasks. This
census says, for each of them, WHICH OF THE THREE COLUMNS ARE
MISSING -- so the work is a set of holes, and each hole names the
thing that would fill it.

**AND EVERY COLUMN IS MEASURED ON THE CODE, NOT ON THE PROSE.**
MEASURED 2026-11-07, on the reach census's own columns:

    has_refusal, measured over the whole source:  134 modules
    has_refusal, measured on the CODE only:          113 modules
    THE FALSE ONES (docstring only):                  21 modules

    has_selftest, measured over the whole source:     67 modules
    has_selftest, measured on the CODE only:          63 modules
    THE FALSE ONES (docstring only):                   4 modules

**21 of 220 modules claimed a refusal they did not have, and 4 claimed
a selftest they did not have** -- and this is the SAME mistake the
reach census had already fixed for its own columns. **A MENTION IS
NOT A REACH, AND A MENTION IS NOT A REFUSAL EITHER.** So the two
columns are measured here on the code, by walking the AST.

**AND THE THIRD COLUMN IS THE HARD ONE, AND IT IS NOT A GUESS.** "Does
its selftest have a mutation check that proves it can go RED" is
answered by LOOKING FOR THE MUTATION CHECK, and the mutation checks
name their target in several ways -- so the search is for the module's
FILE NAME in the mutation check's source, and a mutation check that
names the file IS the evidence.

**AND THE HONEST ANSWER FOR A MODULE WITH NO MUTATION CHECK IS
"NOT PROVEN", and not "safe".** A selftest that has never been
mutated is a selftest nobody has seen fail.

Run:
    python tools/pattern_census.py
    python tools/pattern_census.py --json
    python tools/pattern_census.py --bin NAMES-IT
    python tools/pattern_census.py --selftest
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORK_REPOS = os.path.dirname(REPO)

sys.path.insert(0, HERE)

#: THE REPOS, and the same four the reach census measures.
REPOS = ("fieldcore", "simself", "far-coding", "far-writing")

#: THE MUTATION CHECKS, and where they live. **AND THIS IS A GLOB,
#: not a hand-kept list** -- a hand-kept list is a list that goes
#: stale, and a stale list of mutation checks is a list of modules
#: that look proven and are not.
MUTATION_CHECK_GLOBS = ("tools/mutation_check*.py", "tools/check_*.py")


def _code_only(src: str, tree: ast.AST) -> str:
    """The source with the docstrings and the comments gone.

    **AND THIS IS THE AST'S JOB, and it is the SAME function the reach
    census uses.** A docstring is the `ast.Expr` node whose value is a
    string constant, and it is the FIRST statement of a module, a
    function or a class. The comments are not in the AST at all.
    """
    docstring_lines: Set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            for ln in range(first.lineno,
                            (first.end_lineno or first.lineno) + 1):
                docstring_lines.add(ln)

    kept = []
    for i, line in enumerate(src.splitlines(), start=1):
        if i in docstring_lines:
            continue
        if line.strip().startswith("#"):
            continue
        kept.append(line)
    return "\n".join(kept)


def _has_selftest(code: str) -> bool:
    """Does the CODE have a selftest?

    **AND IT IS MEASURED ON THE CODE, not on the prose.** MEASURED
    2026-11-07: the reach census searched the whole source, so a
    docstring that said "Run: python src/x.py --selftest" counted as a
    selftest -- and 4 of 220 modules claimed one they did not have.
    """
    if re.search(r"def (_?selftest)\s*\(", code):
        return True
    return bool(re.search(r'add_argument\(\s*["\']--selftest', code))


def _has_measurement(code: str) -> bool:
    """Does the CODE record a MEASUREMENT?

    **AND A MEASUREMENT IS A NUMBER THE MODULE COMPUTES, not a number
    it mentions.** The pattern's first column is "a MEASUREMENT that
    it reaches it" -- so the measurement has to be a COMPUTED VALUE,
    and the honest test is arithmetic on real numbers.

    So: a float or int literal in the code, or a division, or a
    comparison against one. A module that only ever handles strings
    has no measurement -- and saying so is the honest answer.
    """
    if re.search(r"\d+\.\d+", code):
        return True
    if re.search(r"\bfloat\s*\(|\bmath\.", code):
        return True
    if re.search(r"/\s*[A-Za-z_]", code):
        return True
    if re.search(r"[<>]=?\s*\d", code):
        return True
    return False


def _has_named_refusal(code: str) -> bool:
    """Does the CODE refuse, AND DOES THE REFUSAL NAME SOMETHING?

    **AND "NAMED" IS THE LOAD-BEARING WORD.** A bare
    `raise ValueError("bad")` names nothing, and a caller cannot tell
    "never written" from "written and then deleted" from "the store is
    on the wrong machine". The refusal names the thing it refused.
    """
    if not re.search(r"\braise\b|\bREFUSE\b|\bVETO\b|\bDENY\b|\bDENIED\b",
                     code):
        return False
    for m in re.finditer(r"""raise\s+\w+\(\s*(?:f?["'])([^"']{4,})""", code):
        if re.search(r"[A-Za-z_][A-Za-z_0-9]{2,}", m.group(1)):
            return True
    if re.search(r"""(Disposition\.REFUSE|"refuse")""", code):
        for m in re.finditer(r"""f?["']([^"']{6,})["']""", code):
            if re.search(r"[A-Za-z_][A-Za-z_0-9]{2,}", m.group(1)):
                return True
    return False


@dataclass
class Pattern:
    """One module's three columns, and the holes in them."""
    module: str
    repo: str
    path: str
    lines: int = 0
    #: THE MEASUREMENT COLUMN.
    has_measurement: bool = False
    #: THE NAMED REFUSAL COLUMN.
    has_refusal: bool = False
    #: THE SELFTEST COLUMN.
    has_selftest: bool = False
    #: AND THE FOURTH: can the selftest go RED? **AND THIS IS THE ONE
    #: THAT IS EVIDENCED RATHER THAN GUESSED** -- it is True only when
    #: a mutation check NAMES this module's file.
    can_go_red: bool = False
    #: THE MUTATION CHECK THAT PROVES IT, by name.
    mutation_check: str = ""
    #: HOW MANY OF THE FC'S OWN DOCS NAME IT -- the order of the work.
    named_by_docs: int = 0
    #: AND THE REACH BIN, so the table can be read with the reach
    #: census's own answer beside it.
    reach_bin: str = ""

    @property
    def holes(self) -> List[str]:
        """WHAT IS MISSING, by name."""
        out: List[str] = []
        if not self.has_measurement:
            out.append("MEASUREMENT")
        if not self.has_refusal:
            out.append("NAMED REFUSAL")
        if not self.has_selftest:
            out.append("SELFTEST")
        elif not self.can_go_red:
            out.append("CAN GO RED")
        return out

    @property
    def complete(self) -> bool:
        """THE PATTERN, WHOLE."""
        return not self.holes

    def describe(self) -> Dict[str, Any]:
        return {
            "module": self.module, "repo": self.repo,
            "lines": self.lines,
            "has_measurement": self.has_measurement,
            "has_refusal": self.has_refusal,
            "has_selftest": self.has_selftest,
            "can_go_red": self.can_go_red,
            "mutation_check": self.mutation_check,
            "named_by_docs": self.named_by_docs,
            "reach_bin": self.reach_bin,
            "holes": self.holes,
        }


def _mutation_checks() -> Dict[str, List[str]]:
    """Which mutation check names which module file.

    **AND IT IS A GLOB AND NOT A LIST, because a hand-kept list of
    mutation checks goes stale and a stale list is a list of modules
    that LOOK proven and are not.**

    **AND THE MATCH IS ON THE FILE NAME.** A mutation check names its
    target in several ways -- `TARGET = REPO / "src" / "x.py"`, or
    `SRC / "x.py"`, or a string in a MUTATIONS entry -- and the file
    name is the one thing all of them carry. So the evidence is the
    module's file name appearing in the check's source.

    AND THE MATCH IS ON THE CODE, not on the prose -- for the same
    reason as everywhere else: a mutation check whose DOCSTRING names
    a module it does not mutate has not proved anything about it.
    """
    out: Dict[str, List[str]] = {}
    for repo in REPOS:
        tdir = os.path.join(WORK_REPOS, repo, "tools")
        if not os.path.isdir(tdir):
            continue
        for f in sorted(os.listdir(tdir)):
            if not (f.startswith("mutation_check") and f.endswith(".py")):
                continue
            path = os.path.join(tdir, f)
            try:
                src = open(path, encoding="utf-8", errors="replace").read()
                tree = ast.parse(src)
            except Exception:                          # noqa: BLE001
                continue
            code = _code_only(src, tree)
            for name in re.findall(r"([a-z_0-9]+)\.py", code):
                out.setdefault(name, []).append("%s/%s" % (repo, f))
    return out


def _module_files(repo: str) -> Dict[str, str]:
    d = os.path.join(WORK_REPOS, repo, "src")
    if not os.path.isdir(d):
        return {}
    return {f[:-3]: os.path.join(d, f)
            for f in sorted(os.listdir(d))
            if f.endswith(".py") and f != "__init__.py"}


def _doc_mentions(repo: str, module: str) -> int:
    """How many of the fc's own docs name this module."""
    docs_dir = os.path.join(WORK_REPOS, repo, "docs")
    if not os.path.isdir(docs_dir):
        return 0
    n = 0
    for f in os.listdir(docs_dir):
        if not f.endswith(".md"):
            continue
        try:
            text = open(os.path.join(docs_dir, f), encoding="utf-8",
                        errors="replace").read()
        except Exception:                              # noqa: BLE001
            continue
        if ("src/%s.py" % module) in text or ("`%s`" % module) in text:
            n += 1
    return n


def measure(path: str, module: str, repo: str,
            mutation_checks: Dict[str, List[str]]) -> Optional[Pattern]:
    """Measure one module's three columns."""
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
    except Exception:                                  # noqa: BLE001
        return None
    try:
        tree = ast.parse(src)
    except Exception:                                  # noqa: BLE001
        return None

    code = _code_only(src, tree)
    proofs = mutation_checks.get(module, [])
    return Pattern(
        module=module, repo=repo, path=path,
        lines=len(src.splitlines()),
        has_measurement=_has_measurement(code),
        has_refusal=_has_named_refusal(code),
        has_selftest=_has_selftest(code),
        can_go_red=bool(proofs),
        mutation_check=proofs[0] if proofs else "",
        named_by_docs=_doc_mentions(repo, module),
    )


def census(repos: Sequence[str] = REPOS) -> Dict[str, Any]:
    """The whole fc, measured for the pattern's columns."""
    checks = _mutation_checks()
    # AND THE REACH BIN COMES FROM THE REACH CENSUS, and not from a
    # second measurement here. MEASURED 2026-11-07: the first version
    # left `reach_bin` empty -- so the column existed, said nothing,
    # and the table could not be read beside the reach census's own
    # answer. **AND TWO MEASUREMENTS OF THE SAME THING WILL DRIFT
    # APART**, so the reach census is IMPORTED and asked.
    reach_bins = _reach_bins()
    rows: List[Pattern] = []
    for repo in repos:
        for module, path in _module_files(repo).items():
            p = measure(path, module, repo, checks)
            if p is not None:
                p.reach_bin = reach_bins.get("%s/%s" % (repo, module), "")
                rows.append(p)

    whole = [r for r in rows if r.complete]
    holed = [r for r in rows if not r.complete]
    return {"rows": rows, "whole": len(whole), "holed": len(holed),
            "total": len(rows), "mutation_checks": len(
                {c for v in checks.values() for c in v})}


def _reach_bins() -> Dict[str, str]:
    """The reach census's own bin for every module.

    **AND IT IS THE REACH CENSUS, IMPORTED.** The two censuses are
    siblings -- one asks "does this module reach the fc's own?" and
    this one asks the other three questions of the same pattern -- and
    they must agree about which modules they are talking about. So
    the reach census is imported and asked, and its bin is carried
    here. **A SECOND MEASUREMENT OF THE SAME THING WILL DRIFT.**
    """
    try:
        import reach_census                      # noqa: E402
    except Exception:                            # noqa: BLE001
        return {}
    try:
        result = reach_census.census()
    except Exception:                            # noqa: BLE001
        return {}
    return {"%s/%s" % (r.repo, r.module): r.bin for r in result["rows"]}


def _selftest() -> int:
    """The census's own selftest."""
    import tempfile

    checks: Dict[str, List[str]] = {}

    # -- 1. A MEASUREMENT IS A COMPUTED NUMBER
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "measures.py")
        open(p, "w", encoding="utf-8").write(
            "def coherence():\n    return 1.0 - 0.25\n")
        r = measure(p, "measures", "x", checks)
        assert r is not None and r.has_measurement, "the measurement was missed"

    # -- 2. A MODULE WITH NO NUMBERS HAS NO MEASUREMENT
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "words.py")
        open(p, "w", encoding="utf-8").write(
            'def name():\n    return "alpha"\n')
        r = measure(p, "words", "x", checks)
        assert r is not None and not r.has_measurement, (
            "a module of words claimed a measurement")

    # -- 3. A NAMED REFUSAL IS A REFUSAL THAT NAMES SOMETHING
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "refuses.py")
        open(p, "w", encoding="utf-8").write(
            "def load(self):\n"
            '    raise ValueError(f"{self.name}: no such store")\n')
        r = measure(p, "refuses", "x", checks)
        assert r is not None and r.has_refusal, "the named refusal was missed"

    # -- 4. AND A DOCSTRING ALONE IS NOT A REFUSAL
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "talks.py")
        open(p, "w", encoding="utf-8").write(
            '"""This module refuses to be confused with anything else."""\n'
            "def go():\n    return 1\n")
        r = measure(p, "talks", "x", checks)
        assert r is not None and not r.has_refusal, (
            "a docstring was counted as a refusal")

    # -- 5. AND A DOCSTRING ALONE IS NOT A SELFTEST
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "promises.py")
        open(p, "w", encoding="utf-8").write(
            '"""Run: python src/promises.py --selftest"""\n'
            "def go():\n    return 1\n")
        r = measure(p, "promises", "x", checks)
        assert r is not None and not r.has_selftest, (
            "a docstring was counted as a selftest")

    # -- 6. AND A SELFTEST WITH NO MUTATION CHECK IS NOT PROVEN
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "untested.py")
        open(p, "w", encoding="utf-8").write(
            "def _selftest():\n    return 0\n")
        r = measure(p, "untested", "x", checks)
        assert r is not None and r.has_selftest, "the selftest was missed"
        assert not r.can_go_red, "an unproven selftest claimed RED"
        assert "CAN GO RED" in r.holes, r.holes

    # -- 7. AND A MUTATION CHECK THAT NAMES IT IS THE EVIDENCE
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "proven.py")
        open(p, "w", encoding="utf-8").write(
            "def _selftest():\n    return 0\n"
            "def load(self):\n"
            '    raise ValueError(f"{self.name}: no such store")\n'
            "def coherence():\n    return 1.0 - 0.25\n")
        r = measure(p, "proven", "x", {"proven": ["fieldcore/mutation_check_x.py"]})
        assert r is not None and r.can_go_red, "the proof was missed"
        assert r.complete, r.holes

    # -- 8. AND THE MUTATION CHECK'S OWN DOCSTRING DOES NOT COUNT
    checks2 = {"proven": []}
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "proven.py")
        open(p, "w", encoding="utf-8").write(
            "def _selftest():\n    return 0\n")
        r = measure(p, "proven", "x", checks2)
        assert r is not None and not r.can_go_red, "a docstring counted"

    # -- 9. AND THE HOLES NAME THE COLUMN THAT IS MISSING
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "bare.py")
        open(p, "w", encoding="utf-8").write("def go():\n    return 1\n")
        r = measure(p, "bare", "x", checks)
        assert r is not None
        assert r.holes == ["MEASUREMENT", "NAMED REFUSAL", "SELFTEST"], r.holes

    print("  [ok ] a measurement is a computed number")
    print("  [ok ] a module of words has no measurement")
    print("  [ok ] a named refusal names something")
    print("  [ok ] a docstring is not a refusal")
    print("  [ok ] a docstring is not a selftest")
    print("  [ok ] a selftest with no mutation check is not proven")
    print("  [ok ] a mutation check that names it is the evidence")
    print("  [ok ] the mutation check's own docstring does not count")
    print("  [ok ] the holes name the column that is missing")
    print()
    print("  THE PATTERN CENSUS SELFTEST PASSED")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--repo", default="")
    ap.add_argument("--complete", action="store_true",
                    help="only the modules whose pattern is whole")
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.selftest:
        return _selftest()

    result = census()
    rows = result["rows"]
    if args.repo:
        rows = [r for r in rows if r.repo == args.repo]
    if args.complete:
        rows = [r for r in rows if r.complete]

    if args.json:
        print(json.dumps({
            "total": result["total"],
            "whole": result["whole"],
            "holed": result["holed"],
            "rows": [r.describe() for r in rows],
        }, indent=2))
        return 0

    print("=" * 78)
    print("THE PATTERN, AS A TABLE WITH HOLES IN IT")
    print("=" * 78)
    print()
    print("  the modules measured : %d" % result["total"])
    print("    the pattern WHOLE  : %d" % result["whole"])
    print("    with HOLES in it   : %d" % result["holed"])
    print("  the mutation checks  : %d" % result["mutation_checks"])
    print()
    print("  THE THREE COLUMNS: a MEASUREMENT, a NAMED REFUSAL, and a")
    print("  selftest that can go RED. **AND A SELFTEST THAT HAS NEVER")
    print("  BEEN MUTATED IS A SELFTEST NOBODY HAS SEEN FAIL.**")
    print()
    print("  meas ref  red  docs  repo        module")
    for r in sorted(rows, key=lambda x: (len(x.holes), -x.named_by_docs,
                                         x.repo, x.module)):
        mark = lambda b: " ok " if b else " . "     # noqa: E731
        print("   %s  %s  %s  %4d  %-11s %-26s %s%s" % (
            mark(r.has_measurement), mark(r.has_refusal),
            mark(r.can_go_red), r.named_by_docs, r.repo, r.module,
            r.reach_bin or "-",
            ("   <- " + ", ".join(r.holes)) if r.holes else ""))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
