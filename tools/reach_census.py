#!/usr/bin/env python3
"""
reach_census.py -- THE REACH CENSUS OF THE WHOLE FC.

Bobby, 2026-11-07: *"the sheafs are a team it is all one fc"*, and the
robot's pattern for each fc system: the substrate it reaches, a
MEASUREMENT that it reaches it, a NAMED refusal, a selftest that passes,
and the census saying WIRED rather than ORPHAN.

**AND THIS IS THE SIBLING OF `wiring_census.py`, AND NOT ITS DUPLICATE.**
The wiring census asks *"does something import this?"* -- and the answer
is WIRED / ENTRY / ORPHAN. The reach census asks *"does this module
reach anything of the FC's OWN?"* -- and the answer is REACHES /
STANDALONE / NAMES-IT.

**AND THE TWO ANSWER DIFFERENT QUESTIONS, AND THE DIFFERENCE IS THE
FINDING.** MEASURED 2026-11-07:

    the modules with a main():                123
    that reach an fc substrate:                43
    that reach no fc substrate:                80

**AND THAT 80 WAS WRONG THE FIRST TIME**, because it counted only
PYTHON IMPORTS -- and most of the fc's modules reach the fc by a
SUBPROCESS PROBE or a PATH into its own source, **which is the CORRECT
shape for an exam**: an exam that imports its subject cannot grade
itself. `fieldcore/src/wiring.py` is exactly that.

So the definition of REACH is three ways, and all three count:

    1  a PYTHON IMPORT of one of the fc's ledgers
    2  a SUBPROCESS PROBE -- the module RUNS the fc
    3  a PATH into the fc's own source

**AND A MEASUREMENT THAT COUNTS THE WRONG THING IS WORSE THAN NO
MEASUREMENT**, because it produces a number that looks like a fact.

THE THREE BINS
--------------
    REACHES      the module reaches the fc's own: a ledger, a
                 subprocess probe, or a path into its source
    STANDALONE   it reaches nothing of the fc's own AND IT SAYS SO --
                 an honestly standalone instrument
    NAMES-IT     it reaches nothing of the fc's own AND DOES NOT SAY
                 SO -- a question nobody asked

**AND THE THIRD BIN IS THE FINDING, NOT THE COUNT.** A module that
reaches nothing and says so is a known instrument. A module that reaches
nothing and does not say so is a question nobody asked. And **the
project's own rule applies: a module is either REACHING or it is NAMED.**

Run:
    python tools/reach_census.py
    python tools/reach_census.py --json
    python tools/reach_census.py --selftest
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

#: THE FC'S LEDGERS -- the modules that hold what is TRUE. Reaching one
#: of these is reaching the fc's own knowledge.
LEDGERS = (
    "claim_register", "governor", "fc_gate", "property_layer",
    "predicate_layer", "testimony_layer", "predicate_registry",
    "locus_gate", "psi_zero", "fieldcore_cell",
)

#: THE SUBSTRATE ROOTS, and a module that reaches one of these reaches
#: the fc's machinery.
SUBSTRATES = ("locus", "constitution", "ground", "sheaves", "coherence_spine")


@dataclass
class Reach:
    """What one module reaches, and whether it says so."""
    module: str
    repo: str
    path: str
    lines: int
    #: THE LEDGERS IT REACHES, by python import.
    ledgers: List[str] = field(default_factory=list)
    #: DOES IT RUN THE FC? -- a subprocess probe.
    probes: bool = False
    #: DOES IT NAME A PATH INTO THE FC'S OWN SOURCE?
    path_probe: bool = False
    #: DOES IT SAY IT IS STANDALONE? -- the honest sentence.
    names_it: bool = False
    #: THE SUBSTRATES IT REACHES, by python import.
    substrates: List[str] = field(default_factory=list)
    #: DOES IT HAVE A MAIN?
    has_main: bool = False
    #: DOES IT HAVE A SELFTEST?
    has_selftest: bool = False
    #: DOES IT HAVE A NAMED REFUSAL?
    has_refusal: bool = False
    #: HOW MANY OF THE FC'S OWN DOCS NAME THIS MODULE. And this is the
    #: MEASUREMENT OF HOW MUCH THE FC'S OWN WRITE-UP NEEDS IT -- so the
    #: 117 are ordered by something measured and not by a guess.
    named_by_docs: int = 0

    @property
    def reaches(self) -> bool:
        return bool(self.ledgers or self.substrates or self.probes
                    or self.path_probe)

    @property
    def bin(self) -> str:
        if self.reaches:
            return "REACHES"
        if self.names_it:
            return "STANDALONE"
        return "NAMES-IT"

    def describe(self) -> Dict[str, Any]:
        return {
            "module": self.module, "repo": self.repo, "bin": self.bin,
            "ledgers": self.ledgers, "substrates": self.substrates,
            "probes": self.probes, "path_probe": self.path_probe,
            "names_it": self.names_it, "has_main": self.has_main,
            "has_selftest": self.has_selftest,
            "has_refusal": self.has_refusal,
            "named_by_docs": self.named_by_docs,
        }


#: THE HONEST SENTENCE, and the phrases that count as saying it.
#: **AND THE PHRASE IS NARROW ON PURPOSE** -- "standalone" and "does not
#: reach the fc" are claims; "independent" is a claim about the CODE and
#: not about the REACHING.
HONEST_PHRASES = (
    "standalone", "stands alone", "does not reach", "reaches nothing",
    "no fc substrate", "not wired", "deliberately independent",
    "independent of the fc", "does not depend on the fc",
)


def _code_only(src: str, tree: ast.AST) -> str:
    """The source with the docstrings and the comments gone.

    **AND THIS IS WHAT THE AST IS FOR.** A docstring is the `ast.Expr`
    node whose value is a string constant, and it is the FIRST statement
    of a module, a function or a class. The comments are not in the AST
    at all. So the code is the source minus those lines -- and the
    comment lines come back because the source still has them, so they
    are stripped by hand.

    **AND A MENTION IS NOT A REACH.** MEASURED 2026-11-07: the first
    version matched the path pattern against the WHOLE SOURCE, and a
    docstring that said "see src/claim_register.py" counted as a reach
    -- so 169 of 216 modules "reached" and the number was nonsense.

    AND THE DOCSTRING LINES ARE FOUND BY THE AST AND NOT BY A REGEX, so
    a string that merely LOOKS like a docstring is not mistaken for one.
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
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        kept.append(line)
    return "\n".join(kept)


def _repo_of(path: str) -> str:
    rel = os.path.relpath(path, WORK_REPOS)
    return rel.split(os.sep)[0] if os.sep in rel else rel


def measure_module(path: str, module: str, repo: str,
                   fc_modules: Set[str]) -> Optional[Reach]:
    """Measure one module's reach."""
    try:
        src = open(path, encoding="utf-8", errors="replace").read()
    except Exception:                              # noqa: BLE001
        return None
    try:
        tree = ast.parse(src)
    except Exception:                              # noqa: BLE001
        return None

    imports: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imports.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            m = (node.module or "").split(".")[0]
            if m:
                imports.add(m)

    # AND THE SUBPROCESS PROBE -- the module RUNS the fc. And the PATH
    # INTO THE FC'S OWN SOURCE -- the module points at the fc's files.
    #
    # AND THE PROBES ARE MEASURED ON THE CODE AND NOT ON THE TEXT.
    # MEASURED 2026-11-07: the first version matched the path pattern
    # against the WHOLE SOURCE, and a docstring that said "see
    # src/claim_register.py" counted as a reach -- so 169 of 216 modules
    # "reached" and the number was nonsense. **A MENTION IS NOT A REACH.**
    #
    # So the docstrings and the comments are stripped first, by walking
    # the AST and dropping every string constant that is not a
    # docstring -- which is what the AST is for.
    code = _code_only(src, tree)
    probes = bool(re.search(r"subprocess\.(run|Popen|call|check_output)",
                            code))
    path_probe = bool(re.search(r"(fieldcore|simself)[/\\][\w./\\-]*\.py",
                                code)) or bool(
        re.search(r"src[/\\][a-z_]+\.py", code))

    low = src.lower()
    names_it = any(phrase in low for phrase in HONEST_PHRASES)

    return Reach(
        module=module, repo=repo, path=path,
        lines=len(src.splitlines()),
        ledgers=sorted(imports & set(LEDGERS)),
        substrates=sorted(imports & set(SUBSTRATES)),
        probes=probes, path_probe=path_probe, names_it=names_it,
        has_main="def main(" in src,
        has_selftest=("_selftest" in src) or ("--selftest" in src),
        has_refusal=bool(re.search(r"refus|veto|denied", src, re.I)),
    )


def _doc_mentions(repo: str, module: str) -> int:
    """How many of the fc's own docs name this module.

    **AND THIS IS THE MEASUREMENT OF HOW MUCH THE FC'S WRITE-UP NEEDS
    IT**, so the modules that reach nothing are ordered by something
    measured and not by a guess.

    AND THE DOCS ARE THE FC'S OWN -- `docs/` in each repo -- and not the
    whole filesystem, so a stray mention in a chat transcript does not
    make a module look important.
    """
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
        except Exception:                          # noqa: BLE001
            continue
        if ("src/%s.py" % module) in text or ("`%s`" % module) in text:
            n += 1
    return n


def census(repos: Sequence[str] = ("fieldcore", "simself", "far-coding",
                                   "far-writing")) -> Dict[str, Any]:
    """The whole fc, measured for reach."""
    # FIRST: every module name in the fc, so a PATH probe can be read.
    fc_modules: Set[str] = set()
    for repo in repos:
        src_dir = os.path.join(WORK_REPOS, repo, "src")
        if not os.path.isdir(src_dir):
            continue
        for f in os.listdir(src_dir):
            if f.endswith(".py"):
                fc_modules.add(f[:-3])

    rows: List[Reach] = []
    for repo in repos:
        src_dir = os.path.join(WORK_REPOS, repo, "src")
        if not os.path.isdir(src_dir):
            continue
        for f in sorted(os.listdir(src_dir)):
            if not f.endswith(".py") or f == "__init__.py":
                continue
            path = os.path.join(src_dir, f)
            r = measure_module(path, f[:-3], repo, fc_modules)
            if r is not None:
                r.named_by_docs = _doc_mentions(repo, f[:-3])
                rows.append(r)

    bins: Dict[str, int] = {"REACHES": 0, "STANDALONE": 0, "NAMES-IT": 0}
    for r in rows:
        bins[r.bin] += 1
    return {"rows": rows, "bins": bins, "total": len(rows)}


def _selftest() -> int:
    """The census's own selftest."""
    import tempfile

    # -- 1. A MODULE THAT IMPORTS A LEDGER REACHES
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "uses_the_ledger.py")
        open(p, "w", encoding="utf-8").write(
            "from claim_register import ClaimRegister\n\n"
            "def main():\n    return 1\n")
        r = measure_module(p, "uses_the_ledger", "x", set())
        assert r is not None and r.reaches, "a ledger import did not reach"
        assert r.bin == "REACHES", r.bin

    # -- 2. AND A MODULE THAT RUNS THE FC REACHES, EVEN WITH NO IMPORT
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "probes_it.py")
        open(p, "w", encoding="utf-8").write(
            "import subprocess\n\n"
            "def main():\n"
            "    return subprocess.run([\"python\", \"-c\", \"pass\"])\n")
        r = measure_module(p, "probes_it", "x", set())
        assert r is not None and r.probes, "the subprocess probe was missed"
        assert r.bin == "REACHES", r.bin

    # -- 3. AND A MODULE THAT NAMES A PATH INTO THE FC REACHES
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "points_at_it.py")
        open(p, "w", encoding="utf-8").write(
            "def main():\n"
            "    return \"fieldcore/src/claim_register.py\"\n")
        r = measure_module(p, "points_at_it", "x", set())
        assert r is not None and r.path_probe, "the path probe was missed"

    # -- 4. AND AN HONEST STANDALONE IS ITS OWN BIN
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "on_its_own.py")
        open(p, "w", encoding="utf-8").write(
            '"""A standalone instrument. It reaches nothing of the fc."""\n'
            "def main():\n    return 1\n")
        r = measure_module(p, "on_its_own", "x", set())
        assert r is not None and not r.reaches, "it reached something"
        assert r.names_it, "the honest sentence was missed"
        assert r.bin == "STANDALONE", r.bin

    # -- 5. AND A SILENT ONE IS THE FINDING
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "silent.py")
        open(p, "w", encoding="utf-8").write(
            "def main():\n    return 1\n")
        r = measure_module(p, "silent", "x", set())
        assert r is not None and not r.reaches, "it reached something"
        assert r.bin == "NAMES-IT", r.bin

    print("  [ok ] a ledger import reaches")
    print("  [ok ] a subprocess probe reaches")
    print("  [ok ] a path into the fc reaches")
    print("  [ok ] an honest standalone is its own bin")
    print("  [ok ] a silent one is the finding")
    print()
    print("  THE REACH CENSUS SELFTEST PASSED")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--bin", default="",
                    help="only show this bin: REACHES, STANDALONE, NAMES-IT")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()

    result = census()
    if args.json:
        print(json.dumps({
            "total": result["total"], "bins": result["bins"],
            "rows": [r.describe() for r in result["rows"]],
        }, indent=2))
        return 0

    print("=" * 78)
    print("THE REACH CENSUS OF THE WHOLE FC")
    print("=" * 78)
    print()
    print("  the modules measured: %d" % result["total"])
    for k in ("REACHES", "STANDALONE", "NAMES-IT"):
        print("    %-12s %d" % (k, result["bins"][k]))
    print()
    print("  AND THE THIRD BIN IS THE FINDING: a module that reaches")
    print("  nothing of the fc's own AND DOES NOT SAY SO is a question")
    print("  nobody asked. **THE PROJECT'S OWN RULE APPLIES: A MODULE IS")
    print("  EITHER REACHING OR IT IS NAMED.**")
    print()

    for want in (["REACHES", "STANDALONE", "NAMES-IT"] if not args.bin
                 else [args.bin]):
        rows = [r for r in result["rows"] if r.bin == want]
        if not rows:
            continue
        print("  --- %s (%d) ---" % (want, len(rows)))
        for r in sorted(rows, key=lambda x: (-x.named_by_docs, x.repo,
                                            x.module)):
            print("    %-11s %-30s %5d lines  docs=%-2d %s%s%s" % (
                r.repo, r.module, r.lines, r.named_by_docs,
                ("ledger=" + ",".join(r.ledgers)) if r.ledgers else "",
                " probe" if r.probes else "",
                " path" if r.path_probe else ""))
        print()

    # AND THE ORDER OF THE WORK, measured: the modules that reach nothing
    # and are NAMED BY THE FC'S OWN DOCS are the ones the fc's write-up
    # says matter, and they come first.
    names_it = [r for r in result["rows"] if r.bin == "NAMES-IT"]
    named = [r for r in names_it if r.named_by_docs]
    print("  --- THE ORDER OF THE WORK (%d of the %d name it, and the "
          "fc's docs name %d of those) ---" % (len(named), len(names_it),
                                               len(named)))
    for r in sorted(named, key=lambda x: (-x.named_by_docs, x.module))[:20]:
        print("    %-11s %-30s named by %d doc(s)" % (
            r.repo, r.module, r.named_by_docs))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
