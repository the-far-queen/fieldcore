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
    #: DOES IT SAY THE FC'S OWN REACHES IT? -- the other honest
    #: sentence. MEASURED 2026-11-07: the census had ONE honest
    #: phrase list, for "I reach nothing" -- so a module that is a
    #: SUBSTRATE the fc is built on, and says so, was filed beside a
    #: module nothing touches. **AND THEY ARE NOT THE SAME MODULE.**
    names_the_reverse: bool = False
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
    #: WHO REACHES THIS MODULE -- the REVERSE direction. MEASURED
    #: 2026-11-07: the census measured reach in ONE direction only --
    #: "does this module reach the fc's own?" -- and so a module the
    #: fc's own DEPENDS ON and a module NOTHING touches landed in the
    #: same bin. **AND THEY ARE NOT THE SAME MODULE.** One is a
    #: substrate the fc is built on; the other is a question nobody
    #: asked. Measured: 48 of the 121 NAMES-IT modules are reached by
    #: the fc's own, and 73 by nothing at all.
    #:
    #: AND THE THREE WAYS COUNT, and all three count: a python import
    #: of the module, a PATH into its file, and a SUBPROCESS that runs
    #: it.
    reached_by: List[str] = field(default_factory=list)
    #: AND WHICH WAYS, so the reader can tell an import from a probe.
    reached_by_import: List[str] = field(default_factory=list)
    reached_by_path: List[str] = field(default_factory=list)
    reached_by_probe: List[str] = field(default_factory=list)

    @property
    def is_reached(self) -> bool:
        """DOES THE FC'S OWN DEPEND ON THIS?"""
        return bool(self.reached_by)

    @property
    def reaches(self) -> bool:
        return bool(self.ledgers or self.substrates or self.probes
                    or self.path_probe)

    @property
    def bin(self) -> str:
        """WHICH BIN, and the four bins are four DIFFERENT SITUATIONS.

        **AND THE FOURTH BIN EXISTS BECAUSE THE MEASUREMENT WAS IN
        ONE DIRECTION ONLY.** MEASURED 2026-11-07: the census asked
        "does this module reach the fc's own?" and never asked the
        other question. So a module the fc is BUILT ON -- a
        substrate -- and a module NOTHING TOUCHES landed in the same
        bin, and the third bin's own name ("a question nobody asked")
        was wrong for half of its members.

        REACHES     it reaches the fc's own
        STANDALONE  it reaches nothing, and says so -- and NOTHING
                    reaches it either
        SUBSTRATE   the fc's own REACHES IT, and it says so -- it is
                    what the fc is built on
        NAMES-IT    it reaches nothing, does not say so, and NOTHING
                    reaches it -- a question nobody asked
        """
        if self.reaches:
            return "REACHES"
        if self.names_the_reverse and self.is_reached:
            return "SUBSTRATE"
        if self.names_it and not self.is_reached:
            return "STANDALONE"
        return "NAMES-IT"

    def describe(self) -> Dict[str, Any]:
        return {
            "module": self.module, "repo": self.repo, "bin": self.bin,
            "ledgers": self.ledgers, "substrates": self.substrates,
            "probes": self.probes, "path_probe": self.path_probe,
            "names_it": self.names_it,
            "names_the_reverse": self.names_the_reverse, "has_main": self.has_main,
            "has_selftest": self.has_selftest,
            "has_refusal": self.has_refusal,
            "named_by_docs": self.named_by_docs,
            "reached_by": self.reached_by,
            "reached_by_import": self.reached_by_import,
            "reached_by_path": self.reached_by_path,
            "reached_by_probe": self.reached_by_probe,
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

#: AND THE OTHER HONEST SENTENCE -- the module says the fc's own
#: REACHES IT. MEASURED 2026-11-07: the census had one honest phrase
#: list, for "I reach nothing", and so a SUBSTRATE -- a module the fc
#: is built on -- had no way to say so and was filed beside a module
#: nothing touches. **A MODULE IS EITHER REACHING OR IT IS NAMED**, and
#: the naming has two directions: what it reaches, and what reaches it.
HONEST_REVERSE_PHRASES = (
    "the fc's own reaches it", "the fc reaches it", "reaches this module",
    "the fc's own reaches this", "imports this one", "the fc is built on",
    "reached by the fc", "the fc's ground asks it",
    # AND THE WORDING THE MODULES ACTUALLY USE. MEASURED 2026-11-07:
    # `sheaf_loop.py` says "this module REACHES THE FC THROUGH THE
    # BRIDGE" -- the same claim, in the other order -- and the first
    # version of this list did not have it, so the module that had
    # ALREADY DONE THE WORK was filed as one that had not. **A PHRASE
    # LIST THAT ONLY THE INSTRUMENT'S OWN WORDING MATCHES WILL MISS
    # EVERY MODULE THAT SAID IT DIFFERENTLY.**
    "reaches the fc through", "reaches the fc", "the fc's own reaches",
    "the fc reaches", "reached by the fc's own", "the fc's own imports",
)


def _docstrings(src: str, tree: ast.AST) -> str:
    """The module's own PROSE -- every docstring in the file.

    **AND THIS IS WHERE THE HONEST SENTENCE LIVES.** MEASURED
    2026-11-07: the phrase was searched over the whole source, so a
    module that merely SEARCHED FOR the words ("is not wired",
    "orphan") in a list of vocabulary counted as having said it. **A
    WORD THE MODULE SEARCHES FOR IS NOT A SENTENCE THE MODULE SAYS.**

    So the honest sentence is read from the docstrings -- the module's
    own prose about itself -- and not from the code.
    """
    out: List[str] = []
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
            out.append(first.value.value)
    return "\n".join(out)


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

    # AND THE HONEST SENTENCE IS A SENTENCE IN A DOCSTRING, and not a
    # word anywhere in the file. MEASURED 2026-11-07: the phrase was
    # searched over the WHOLE source, so three modules counted as
    # having said it -- `chain_audit`, `informed_miss_analysis` and
    # `self_review` -- and in each case the phrase was in the CODE, in
    # a list of vocabulary words the module searches for. **A WORD THE
    # MODULE SEARCHES FOR IS NOT A SENTENCE THE MODULE SAYS.**
    #
    # AND THE SENTENCE IS ALSO THE HONEST ONE IT SHOULD BE. The
    # census's job is to ask "does this module say what it reaches?",
    # and the answer has to come from the module's own prose.
    doc = _docstrings(src, tree)
    low = doc.lower()
    names_it = any(phrase in low for phrase in HONEST_PHRASES)
    names_the_reverse = any(phrase in low
                            for phrase in HONEST_REVERSE_PHRASES)

    # AND THE TWO PATTERN COLUMNS ARE MEASURED ON THE CODE, and not on
    # the prose. MEASURED 2026-11-07: `has_refusal` and
    # `has_selftest` were searched over the WHOLE source, docstrings
    # included -- so a module whose DOCSTRING said "refuse" counted as
    # having a refusal in its code, and a module whose docstring said
    # "Run: python src/x.py --selftest" counted as having a selftest.
    # **21 of 220 modules claimed a refusal they did not have, and 4
    # claimed a selftest they did not have.** And this is the SAME
    # mistake the census already fixed for the reach columns -- a
    # mention is not a reach -- so the fix belongs here too.
    #
    # AND THE REFUSAL MUST NAME SOMETHING. A bare `raise` names
    # nothing, and a caller cannot tell "never written" from
    # "written and then deleted". So the refusal is a raise or a
    # returned string that CARRIES A NAME -- the module's own subject
    # in the message.
    has_refusal = _has_named_refusal(code)
    has_selftest = _has_selftest(code)

    return Reach(
        module=module, repo=repo, path=path,
        lines=len(src.splitlines()),
        ledgers=sorted(imports & set(LEDGERS)),
        substrates=sorted(imports & set(SUBSTRATES)),
        probes=probes, path_probe=path_probe, names_it=names_it,
        names_the_reverse=names_the_reverse,
        has_main="def main(" in code,
        has_selftest=has_selftest,
        has_refusal=has_refusal,
    )


def _has_selftest(code: str) -> bool:
    """Does the CODE have a selftest?

    **AND IT IS MEASURED ON THE CODE, not on the prose.** MEASURED
    2026-11-07: the first version searched the whole source, so a
    docstring that said "Run: python src/x.py --selftest" counted as a
    selftest -- and 4 of 220 modules claimed one they did not have.

    So the selftest is a real one: a FUNCTION named selftest or
    _selftest, or an argparse flag --selftest that the code reads.
    """
    if re.search(r"def (_?selftest)\s*\(", code):
        return True
    return bool(re.search(r'add_argument\(\s*["\']--selftest', code))


def _has_named_refusal(code: str) -> bool:
    """Does the CODE refuse, AND DOES THE REFUSAL NAME SOMETHING?

    **AND THIS IS THE ROBOT'S PATTERN'S THIRD COLUMN, measured on the
    code.** The pattern is: a MEASUREMENT, a NAMED REFUSAL, and a
    selftest that can go RED. "Named" is the load-bearing word -- a
    bare `raise ValueError("bad")` names nothing, and a caller cannot
    tell "never written" from "written and then deleted" from "the
    store is on the wrong machine".

    MEASURED 2026-11-07: the first version was a regex over the whole
    source for "refus|veto|denied", and 21 of 220 modules claimed a
    refusal that existed only in their DOCSTRING. So the refusal is
    measured on the code, and the message must CARRY A NAME -- a
    string with a name in it, not a bare exception.
    """
    # 1. A REFUSAL VERB IN THE CODE: a raise, or a disposition.
    if not re.search(r"\braise\b|\bREFUSE\b|\bVETO\b|\bDENY\b|\bDENIED\b",
                     code):
        return False
    # 2. AND THE MESSAGE NAMES SOMETHING: a quoted string with a word
    #    in it. A bare `raise ValueError` with no message names
    #    nothing, and that is not a NAMED refusal.
    for m in re.finditer(r"""raise\s+\w+\(\s*(?:f?["'])([^"']{4,})""", code):
        if re.search(r"[A-Za-z_][A-Za-z_0-9]{2,}", m.group(1)):
            return True
    # 3. AND A DISPOSITION THAT CARRIES A REASON: a returned tuple or
    #    dict whose second field is a named string.
    if re.search(r"""(Disposition\.REFUSE|"refuse")""", code):
        for m in re.finditer(r"""f?["']([^"']{6,})["']""", code):
            if re.search(r"[A-Za-z_][A-Za-z_0-9]{2,}", m.group(1)):
                return True
    return False


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

    # AND THE REVERSE REACH, measured on the code. MEASURED
    # 2026-11-07: the census asked "does this module reach the fc's
    # own?" and never asked the other question -- "does the fc's own
    # reach THIS?" -- so a module the fc is BUILT ON and a module
    # NOTHING TOUCHES landed in the same bin. **AND THEY ARE NOT THE
    # SAME MODULE.** Measured over the fc: 109 of 220 modules are
    # reached by the fc's own, and of the 121 in the third bin, 48 are
    # reached by the fc's own and 73 by nothing at all.
    _apply_reverse_reach(rows, repos)

    bins: Dict[str, int] = {"REACHES": 0, "STANDALONE": 0, "SUBSTRATE": 0,
                            "NAMES-IT": 0}
    for r in rows:
        bins[r.bin] += 1
    return {"rows": rows, "bins": bins, "total": len(rows)}


def _apply_reverse_reach(rows: List[Reach],
                         repos: Sequence[str]) -> None:
    """Fill in each row's WHO REACHES IT -- the reverse direction.

    **AND THE THREE WAYS COUNT, and all three count**: a python import
    of the module, a PATH into its file, and a SUBPROCESS that runs it.

    **AND IT IS MEASURED ON THE CODE, not on the text** -- for the same
    reason the forward direction is: a docstring that says "see
    src/x.py" is not a reach. So the docstrings and the comments are
    stripped first, by walking the AST.

    **AND IT READS THE ROWS' OWN PATHS, and not a rebuilt directory.**
    MEASURED 2026-11-07: the first version rebuilt the source
    directory from the repo name, so the census could only ever be run
    over the real tree -- and the selftest could not point it at a
    fixture. **AN INSTRUMENT THAT CAN ONLY BE RUN OVER THE REAL TREE
    CANNOT BE TESTED ON A CASE YOU CONTROLLED.**
    """
    by_key = {(r.repo, r.module): r for r in rows}
    names = {r.module for r in rows}
    if not names:
        return

    for row in rows:
        try:
            src = open(row.path, encoding="utf-8", errors="replace").read()
            tree = ast.parse(src)
        except Exception:                              # noqa: BLE001
            continue
        code = _code_only(src, tree)
        me = "%s/%s" % (row.repo, row.module)

        # 1. A PYTHON IMPORT OF THE MODULE.
        for node in ast.walk(tree):
            target = None
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.split(".")[0] in names:
                        target = a.name.split(".")[0]
            elif isinstance(node, ast.ImportFrom):
                b = (node.module or "").split(".")[0]
                if b in names:
                    target = b
            if target is None or target == row.module:
                continue
            for (r2, m2), other in by_key.items():
                if m2 != target:
                    continue
                if me not in other.reached_by_import:
                    other.reached_by_import.append(me)

        # 2. A PATH INTO THE MODULE'S FILE.
        for (r2, m2), other in by_key.items():
            if m2 == row.module:
                continue
            if re.search(r"src[/\\]%s\.py" % re.escape(m2), code):
                if me not in other.reached_by_path:
                    other.reached_by_path.append(me)

        # 3. A SUBPROCESS THAT RUNS IT.
        if re.search(r"subprocess\.(run|Popen|call|check_output)", code):
            for (r2, m2), other in by_key.items():
                if m2 == row.module:
                    continue
                if re.search(r"\b%s\b" % re.escape(m2), code):
                    if me not in other.reached_by_probe:
                        other.reached_by_probe.append(me)

    for row in rows:
        seen: List[str] = []
        for lst in (row.reached_by_import, row.reached_by_path,
                    row.reached_by_probe):
            for who in lst:
                if who not in seen:
                    seen.append(who)
        row.reached_by = sorted(seen)


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

    # -- 6. AND A DOCSTRING IS NOT A REFUSAL. MEASURED 2026-11-07: the
    #       refusal column was searched over the whole source, so a
    #       module whose DOCSTRING said "refuse" counted as having a
    #       refusal in its code -- 21 of 220 modules claimed one they
    #       did not have. **A MENTION IS NOT A REACH, AND A MENTION IS
    #       NOT A REFUSAL EITHER.**
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "talks.py")
        open(p, "w", encoding="utf-8").write(
            '"""This module refuses to be confused with anything."""\n'
            "def main():\n    return 1\n")
        r = measure_module(p, "talks", "x", set())
        assert r is not None and not r.has_refusal, (
            "a docstring was counted as a refusal")

    # -- 7. AND A DOCSTRING IS NOT A SELFTEST
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "promises.py")
        open(p, "w", encoding="utf-8").write(
            '"""Run: python src/promises.py --selftest"""\n'
            "def main():\n    return 1\n")
        r = measure_module(p, "promises", "x", set())
        assert r is not None and not r.has_selftest, (
            "a docstring was counted as a selftest")

    # -- 8. AND A REFUSAL THAT NAMES SOMETHING IS COUNTED
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "names_it.py")
        open(p, "w", encoding="utf-8").write(
            "def load(self):\n"
            '    raise ValueError(f"{self.name}: no such store")\n')
        r = measure_module(p, "names_it", "x", set())
        assert r is not None and r.has_refusal, (
            "a named refusal was missed")

    # -- 9. AND THE REVERSE REACH IS MEASURED. MEASURED 2026-11-07: the
    #       census asked only "does this module reach the fc's own?" --
    #       so a module the fc is BUILT ON and a module NOTHING TOUCHES
    #       landed in the same bin. **AND THEY ARE NOT THE SAME
    #       MODULE.**
    with tempfile.TemporaryDirectory() as d:
        src_dir = os.path.join(d, "src")
        os.makedirs(src_dir)
        target = os.path.join(src_dir, "substrate.py")
        open(target, "w", encoding="utf-8").write(
            "def value():\n    return 1.0\n")
        user = os.path.join(src_dir, "user.py")
        open(user, "w", encoding="utf-8").write(
            "from substrate import value\n\n"
            "def go():\n    return value()\n")
        rows = []
        for f in ("substrate.py", "user.py"):
            r = measure_module(os.path.join(src_dir, f), f[:-3], "x", set())
            assert r is not None
            rows.append(r)
        _apply_reverse_reach(rows, ("x",))
        by_name = {r.module: r for r in rows}
        assert by_name["substrate"].is_reached, (
            "the reverse reach was missed: %r"
            % by_name["substrate"].reached_by)
        assert "x/user" in by_name["substrate"].reached_by, (
            by_name["substrate"].reached_by)
        assert not by_name["user"].is_reached, (
            "the reverse reach was measured backwards")

    # -- 10. AND A DOCSTRING IS NOT A REVERSE REACH EITHER
    with tempfile.TemporaryDirectory() as d:
        src_dir = os.path.join(d, "src")
        os.makedirs(src_dir)
        target = os.path.join(src_dir, "spoken.py")
        open(target, "w", encoding="utf-8").write("def value():\n    return 1.0\n")
        user = os.path.join(src_dir, "talker.py")
        open(user, "w", encoding="utf-8").write(
            '"""See src/spoken.py for the details."""\n'
            "def go():\n    return 1\n")
        rows = []
        for f in ("spoken.py", "talker.py"):
            r = measure_module(os.path.join(src_dir, f), f[:-3], "x", set())
            assert r is not None
            rows.append(r)
        _apply_reverse_reach(rows, ("x",))
        by_name = {r.module: r for r in rows}
        assert not by_name["spoken"].is_reached, (
            "a docstring was counted as a reverse reach: %r"
            % by_name["spoken"].reached_by)

    # -- 11. AND A WORD THE MODULE SEARCHES FOR IS NOT A SENTENCE THE
    #        MODULE SAYS. MEASURED 2026-11-07: the honest phrase was
    #        searched over the WHOLE source, so three modules counted
    #        as having said it when the phrase was in a list of
    #        vocabulary the module searches for.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "searches.py")
        open(p, "w", encoding="utf-8").write(
            "WORDS = (\"is not wired\", \"orphan\", \"standalone\")\n\n"
            "def go():\n    return 1\n")
        r = measure_module(p, "searches", "x", set())
        assert r is not None and not r.names_it, (
            "a word the module searches for was counted as the module "
            "saying it")

    # -- 12. AND THE HONEST SENTENCE, IN A DOCSTRING, COUNTS
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "says_it.py")
        open(p, "w", encoding="utf-8").write(
            '"""A standalone instrument. It reaches nothing of the fc."""\n'
            "def main():\n    return 1\n")
        r = measure_module(p, "says_it", "x", set())
        assert r is not None and r.names_it, "the honest sentence was missed"

    # -- 13. AND THE REVERSE HONEST SENTENCE, IN A DOCSTRING, COUNTS.
    #        MEASURED 2026-11-07: `sheaf_loop.py` says "this module
    #        REACHES THE FC THROUGH THE BRIDGE" -- the same claim in
    #        the other order -- and the first phrase list did not have
    #        it, so the module that had ALREADY DONE THE WORK was
    #        filed as one that had not.
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "substrate.py")
        open(p, "w", encoding="utf-8").write(
            '"""SO THIS MODULE REACHES THE FC THROUGH THE BRIDGE."""\n'
            "def main():\n    return 1\n")
        r = measure_module(p, "substrate", "x", set())
        assert r is not None and r.names_the_reverse, (
            "the reverse honest sentence was missed")

    print("  [ok ] a ledger import reaches")
    print("  [ok ] a subprocess probe reaches")
    print("  [ok ] a path into the fc reaches")
    print("  [ok ] an honest standalone is its own bin")
    print("  [ok ] a silent one is the finding")
    print("  [ok ] a docstring is not a refusal")
    print("  [ok ] a docstring is not a selftest")
    print("  [ok ] a refusal that names something is counted")
    print("  [ok ] the reverse reach is measured")
    print("  [ok ] a docstring is not a reverse reach")
    print("  [ok ] a word the module searches for is not a sentence")
    print("  [ok ] the honest sentence, in a docstring, counts")
    print("  [ok ] the reverse honest sentence counts too")
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
    for k in ("REACHES", "SUBSTRATE", "STANDALONE", "NAMES-IT"):
        print("    %-12s %d" % (k, result["bins"][k]))
    print()
    print("  AND THE FOUR BINS ARE FOUR DIFFERENT SITUATIONS:")
    print("    REACHES    it reaches the fc's own")
    print("    SUBSTRATE  the fc's own REACHES IT -- it is what the fc")
    print("               is built on, and it says so")
    print("    STANDALONE it reaches nothing and says so, and nothing")
    print("               reaches it either")
    print("    NAMES-IT   it reaches nothing, does not say so, and")
    print("               nothing reaches it -- a question nobody asked")
    print()
    print("  AND THE THIRD BIN'S OWN NAME WAS WRONG FOR HALF OF IT")
    print("  BEFORE THE REVERSE REACH WAS MEASURED. MEASURED")
    print("  2026-11-07: the census asked only 'does this module reach")
    print("  the fc's own?' -- so a module the fc is BUILT ON and a")
    print("  module NOTHING TOUCHES landed in the same bin. **AND THEY")
    print("  ARE NOT THE SAME MODULE.**")
    names_it = [r for r in result["rows"] if r.bin == "NAMES-IT"]
    by_fc = [r for r in names_it if r.is_reached]
    by_none = [r for r in names_it if not r.is_reached]
    print()
    print("    the fc's own DEPENDS ON it : %d" % len(by_fc))
    print("    NOTHING reaches it        : %d" % len(by_none))
    print()
    print("  AND THE FIRST POPULATION IS THE SUBSTRATE: the fc's own")
    print("  imports it, or names its path, or runs it -- and it does")
    print("  not say so. **THE FC DEPENDS ON IT AND THE MODULE IS SILENT.**")
    print()

    for want in (["REACHES", "SUBSTRATE", "STANDALONE", "NAMES-IT"]
                 if not args.bin else [args.bin]):
        rows = [r for r in result["rows"] if r.bin == want]
        if not rows:
            continue
        print("  --- %s (%d) ---" % (want, len(rows)))
        for r in sorted(rows, key=lambda x: (-x.named_by_docs, x.repo,
                                            x.module)):
            print("    %-11s %-30s %5d lines  docs=%-2d %s%s%s%s" % (
                r.repo, r.module, r.lines, r.named_by_docs,
                ("ledger=" + ",".join(r.ledgers)) if r.ledgers else "",
                " probe" if r.probes else "",
                " path" if r.path_probe else "",
                ("  <- reached by %d: %s" % (
                    len(r.reached_by), ", ".join(r.reached_by[:2])))
                if r.reached_by else ""))
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
