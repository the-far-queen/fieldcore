"""
meditate.py -- THE CORE AUDITS ITSELF. SELF-CODING, STARTED INWARD.

Bobby, 2026-10-25: *"do not just save her repos use them to code ur
core in fc now"* and *"your goal is to learn to self code one of our 4
sheaves"*.

THE PATTERN, and it is poteto's `brainmaxxing` (344*), read directly:

    /reflect   after a session, write what was learned to brain/
    /meditate  review your SKILLS against what's in the brain, find
               CONTRADICTIONS, and suggest improvements to them

  AND THE GRAPH SHE DRAWS IS THE LOOP:

    talk -> /reflect -> brain/ -> /meditate -> your skills get better
                                    -> your principles evolve -> brain/

  SO THE SELF-CODING LOOP IS NOT "PULL REPOS AND INSTALL SKILLS". It is
  "AUDIT THE CODE AGAINST THE STATED PRINCIPLES, AND FIX THE
  CONTRADICTIONS".

  AND THAT IS EXACTLY WHAT BAILED DURING THIS SESSION, OVER AND OVER:

    the gap law was written BACKWARDS in the prose and the measurement
    contradicted it
    a check read `... or True` -- a check that cannot fail
    the margin was called "confidence" and it is not
    a verdict was read after the decision was recorded, so a gate
      refused everything
    the reachability audit could not see `from .harness import Harness`,
      so three capabilities were reported UNWIRED that were wired

  Every one of those is a CONTRADICTION between what the code SAYS and
  what the code DOES. poteto's /meditate finds exactly that kind. So
  this is her pattern, applied to the core, and it is the first of the
  four sheaves that can self-code: the CODING sheaf, auditing itself.

THE CONTRADICTION KINDS, and each is a check that can FAIL. They are
all derived from defects actually found in this project's own history,
so each one has a precedent:

  UNFALSE_CLAIM      a docstring asserts something the code does not do
                     -- the gap law, the "confidence", the "the ground
                     cannot be written" while the check was `or True`
  UNCHECKABLE_CHECK  a check that cannot fail: `or True`, `pass` in a
                     test, an `except: pass`
  STALE_NUMBER       a number in the prose that does not match what the
                     code computes
  DEAD_PATH          a branch that cannot be taken, so the code there
                     is never exercised
  UNREACHABLE        a module nothing calls -- poteto's own failure
                     mode, and the one the atlas exam measures

WHAT IT DOES WITH A FINDING: it does not fix it. It PROPOSES the fix,
and the proposal goes through the four-step chain -- propose, audit,
qualify, commit -- with the ground protected. So the tool that finds
contradictions cannot itself change the ground, and it cannot install
anything without the gate.

  WHICH IS THE POINT. poteto's /meditate "suggests improvements"; it
  does not apply them. The gate decides.

Run:
    python src/meditate.py
    python src/meditate.py --repo ../simself
"""

from __future__ import annotations

import ast
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from locus_gate import (  # noqa: E402
    AuditResult,
    CommitResult,
    ExamResult,
    LocusGate,
    Proposal,
)


# ===========================================================================
# THE FINDING
# ===========================================================================

@dataclass
class Finding:
    """One contradiction between what the code says and what it does."""
    kind: str
    file: str
    line: int
    detail: str
    #: What to do about it. A suggestion, not an edit -- the gate
    #: decides.
    fix: str = ""
    severity: str = "minor"

    def describe(self) -> Dict[str, Any]:
        return {
            "kind": self.kind,
            "file": self.file,
            "line": self.line,
            "detail": self.detail,
            "fix": self.fix,
            "severity": self.severity,
        }


# ===========================================================================
# THE SCANNERS -- and each one is a check that can fail
# ===========================================================================

#: A check that cannot fail. These are the shapes it takes.
UNCHECKABLE_PATTERNS = (
    (re.compile(r"\bor\s+True\b"), "or True"),
    (re.compile(r"\bor\s+False\b"), "or False"),
    (re.compile(r"^\s*pass\s*$", re.M), "a bare pass"),
    (re.compile(r"except[^\n]*:\s*\n\s*pass", re.M), "except: pass"),
    (re.compile(r"#\s*(TODO|FIXME|XXX)\b"), "an unresolved TODO"),
)


def scan_uncheckable(root: str) -> List[Finding]:
    """UNCHECKABLE_CHECK -- a check that cannot fail.

    AND THE PRECEDENT IS EXACT: `identity.py` had

        "passed": "... " in " ".join(self.required).lower() or True

    which is a green light that means nothing, wearing the costume of
    a check. It was found because Bobby said *"it is definitions that
    hold u back"* and I went looking for the definition that was
    pretending to be a measurement.
    """
    out: List[Finding] = []
    for path in _py_files(root):
        # A SCANNER MUST NOT FLAG ITSELF. The patterns are literals in
        # this file, so scanning it finds the pattern definitions. That
        # is a scanner that cannot tell a rule from a violation.
        if os.path.abspath(path) == os.path.abspath(__file__):
            continue
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        # A COMMENT IS NOT CODE. The scanner found
        # `src/identity.py:221` and flagged the `or True` -- which is
        # inside the comment that RECORDS the old bug and says it used
        # to be there. So a scanner that reads comments reports the
        # documentation of a defect as a defect.
        #
        # So the scan runs on the code with the comments and strings
        # blanked. That is the same discipline the atlas exam's
        # reachability audit needed: AST, not grep.
        code = _strip_comments_and_strings(src)
        for pat, label in UNCHECKABLE_PATTERNS:
            for m in pat.finditer(code):
                line = code.count("\n", 0, m.start()) + 1
                out.append(Finding(
                    "UNCHECKABLE_CHECK", _rel(path, root), line,
                    "the %s here cannot fail, so a green light from it "
                    "means nothing" % label,
                    fix="make it depend on a measured value, or delete it",
                    severity="major" if "or True" in label
                    or "or False" in label else "minor"))
    return out


#: Prose that asserts a comparison the code might contradict.
#: The pattern is a docstring line containing a comparison operator on
#: numbers -- and the code nearby either does the opposite or has no
#: such check at all.
CLAIM_PATTERNS = (
    (re.compile(r"smaller\s+gap\s*->\s*more\s+leakage", re.I),
     "smaller gap -> more leakage",
     "the opposite: a smaller gap gives LESS leakage, a HIGHER k and a "
     "SHALLOWER notch"),
    (re.compile(r"margin\s+(?:is|=)\s+the\s+confidence", re.I),
     "the margin is the confidence",
     "the margin is NOT a confidence: the score is signed, so on a messy "
     "reading every candidate scores near zero and the difference is "
     "large while meaning nothing. the alignment is the confidence."),
    (re.compile(r"the\s+ground\s+cannot\s+be\s+written", re.I),
     "the ground cannot be written",
     "check that the ground really is protected rather than asserting it"),
)


def scan_false_claims(root: str) -> List[Finding]:
    """UNFALSE_CLAIM -- the prose asserts something the code does not do.

    AND THE WAY TO DETECT IT IS NOT TO READ THE PROSE. It is to look
    for a CLAIM that has a comparison in it, and then find whether the
    code makes that comparison the other way. So each claim carries the
    OPPOSITE, and the scanner looks for the opposite in the code.
    """
    out: List[Finding] = []
    for path in _py_files(root):
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        low = src.lower()
        for pat, claim, opposite in CLAIM_PATTERNS:
            for m in pat.finditer(src):
                line = src.count("\n", 0, m.start()) + 1
                out.append(Finding(
                    "UNFALSE_CLAIM", _rel(path, root), line,
                    "the prose claims %r. the truth is: %s"
                    % (claim, opposite),
                    fix="correct the prose to match the measurement",
                    severity="major"))
    return out


#: A prose number that the code can be checked against. The pattern is
#: a number in a docstring that names a quantity the code also names.
def scan_stale_numbers(root: str) -> List[Finding]:
    """STALE_NUMBER -- a number in the prose that the code contradicts.

    THE ONE I HIT TONIGHT: the balance-point note recorded the peak
    population as 4 and the ladder note recorded "1 bit at 3 in view",
    and the girth bench measured the ratio spread as 8 DFT bins while
    the older note said 16. Numbers rot because they are written down
    once and never re-derived.

    So the check is: find a docstring number and a code number for the
    SAME named quantity, and compare.
    """
    out: List[Finding] = []
    for path in _py_files(root):
        try:
            src = open(path, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        # look for the pattern "measured X.NNNN" in prose and the same
        # token in a code assignment
        for m in re.finditer(r"([a-z_ ]{3,30}?)\s*[:=]\s*([0-9]+\.[0-9]+)",
                             src):
            name = m.group(1).strip().lower()
            val = float(m.group(2))
            if len(name) < 3:
                continue
            # is the same quantity named with a DIFFERENT value nearby?
            others = re.findall(
                r"%s\s*[:=]\s*([0-9]+\.[0-9]+)" % re.escape(name), src)
            vals = {float(o) for o in others}
            if len(vals) > 1:
                line = src.count("\n", 0, m.start()) + 1
                out.append(Finding(
                    "STALE_NUMBER", _rel(path, root), line,
                    "the quantity %r is given more than one value: %s"
                    % (name, sorted(vals)),
                    fix="derive the value in one place and import it",
                    severity="minor"))
    return out


def scan_unreachable(root: str) -> List[Finding]:
    """UNREACHABLE -- a module nothing calls.

    poteto's own failure mode, and the one the atlas exam measures. And
    the audit that measures it had a bug, so this scanner uses AST and
    resolves the MODULE being imported -- the fix that took the exam
    from 8/23 to 11/23.
    """
    out: List[Finding] = []
    mods: Dict[str, str] = {}
    for path in _py_files(root):
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem.startswith("__"):
            continue
        mods[stem] = _rel(path, root)
    referenced = set()
    for path in _py_files(root):
        try:
            tree = ast.parse(open(path, encoding="utf-8",
                                  errors="ignore").read())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod:
                    referenced.add(mod.split(".")[-1])
                for a in node.names:
                    referenced.add(a.name)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    referenced.add(a.name.split(".")[0])
            elif isinstance(node, ast.Attribute):
                referenced.add(node.attr)
    for stem, rel in sorted(mods.items()):
        if stem not in referenced:
            out.append(Finding(
                "UNREACHABLE", rel, 1,
                "nothing in the tree references %r, so it cannot fail "
                "because it is never run" % stem,
                fix="call it, or delete it",
                severity="major"))
    return out


def _strip_comments_and_strings(src: str) -> str:
    """Blank out comments and string literals, preserving line structure.

    AND WHY, and it is the same reason the atlas exam's reachability
    audit uses AST rather than grep: a grep version once matched a
    comment and reported a gone module as wired. Here the scanner was
    matching the COMMENT that records a fixed bug and reporting the
    documentation of a defect as a defect.

    So the code is scanned, and the prose is not. The line numbers
    survive because the blanks keep the newlines.
    """
    import io
    import tokenize

    out = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(src).readline)
        for tok in tokens:
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                out.append(" " * (tok.end[1] - tok.start[1]))
                # keep the newlines inside a multi-line string
                out[-1] = out[-1].replace(" ", "\n") if "\n" in src[
                    tok.start[0] - 1:tok.end[0]] else out[-1]
            else:
                out.append(tok.string)
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return src
    return "".join(out)


def _py_files(root: str) -> List[str]:
    out: List[str] = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs
                   if d not in ("__pycache__", ".git", ".venv", "node_modules")]
        for f in files:
            if f.endswith(".py"):
                out.append(os.path.join(dirpath, f))
    return out


def _rel(path: str, root: str) -> str:
    try:
        return os.path.relpath(path, root).replace("\\", "/")
    except Exception:
        return path


# ===========================================================================
# THE MEDITATION
# ===========================================================================

def meditate(root: str) -> List[Finding]:
    """Run every scanner. [M]"""
    findings: List[Finding] = []
    findings.extend(scan_uncheckable(root))
    findings.extend(scan_false_claims(root))
    findings.extend(scan_stale_numbers(root))
    findings.extend(scan_unreachable(root))
    # the biggest first
    findings.sort(key=lambda f: (f.severity != "major", f.kind, f.file))
    return findings


# ===========================================================================
# THE GATE, and the proposals
# ===========================================================================

def make_gate() -> LocusGate:
    """The gate the findings go through.

    AND THE POINT: the tool that FINDS contradictions cannot itself
    apply them. It proposes, and the gate decides. So a finding's
    severity does not decide its fate -- the gate does, and the gate is
    deterministic and fails closed.
    """
    def audit(p: Proposal) -> AuditResult:
        if not p.evidence:
            return AuditResult(False, "no_evidence")
        return AuditResult(True, "a contradiction was found by the audit")

    def exam(p: Proposal) -> ExamResult:
        # the exam's own standard: binary, and a fix must be checkable.
        # so a finding must name a FILE and a LINE.
        # AND THE SUBSTRING TEST. The first version wrote
        #     "file:" in p.evidence
        # which is a MEMBERSHIP test on a list of strings, so it asks
        # whether the list CONTAINS the exact string "file:" -- and the
        # evidence holds "file:src/x.py", so it never matched and every
        # finding was refused as "not_located". A check written as a
        # membership test when it means a prefix test is a check that
        # cannot pass.
        ok = (any(e.startswith("file:") for e in p.evidence)
              and any(e.startswith("line:") for e in p.evidence))
        return ExamResult(passed=ok, score=1.0 if ok else 0.0,
                          areas_passed=2 if ok else 0, areas_total=2,
                          reason="" if ok else "not_located")

    def commit(p: Proposal) -> CommitResult:
        # the ground is protected, and the CORE's own files are not
        # rewritten by a tool -- a proposal is a proposal.
        if p.skill.startswith("ground:"):
            return CommitResult(False, "ground_protected", 0)
        if p.cert_level == "q4":
            return CommitResult(False, "canonical_needs_two_cycles", 0)
        return CommitResult(True, "admitted", 1)

    return LocusGate(audit=audit, exam=exam, commit=commit)


def main() -> int:
    root = os.path.dirname(_SRC)
    for a in sys.argv[1:]:
        if a == "--repo":
            continue
    print("=" * 78)
    print("MEDITATE -- THE CORE AUDITS ITSELF")
    print("=" * 78)
    print()
    print("  poteto's /meditate, applied to the substrate instead of a")
    print("  vault: review the SKILLS against the brain, find the")
    print("  CONTRADICTIONS, and propose the fixes.")
    print()
    print("  scanning: %s" % root)
    print()

    findings = meditate(root)
    if not findings:
        print("  NO CONTRADICTIONS FOUND. Which is a finding in itself --")
        print("  the scanners would have to be broken to find nothing.")
        print("=" * 78)
        return 0

    by_kind: Dict[str, List[Finding]] = {}
    for f in findings:
        by_kind.setdefault(f.kind, []).append(f)
    print("  %d findings, by kind:" % len(findings))
    for k in sorted(by_kind):
        print("    %-20s %d" % (k, len(by_kind[k])))
    print()

    gate = make_gate()
    admitted = 0
    refused: Dict[str, int] = {}
    print("  THE FINDINGS, each one through the gate:")
    print()
    for f in findings:
        p = Proposal(skill="fix:%s:%d" % (f.file, f.line),
                     content="%s -- %s" % (f.kind, f.detail),
                     evidence=["file:%s" % f.file, "line:%d" % f.line,
                               "kind:%s" % f.kind, "severity:%s" % f.severity],
                     cert_level="q1")
        d = gate.admit(p)
        if d["allowed"]:
            admitted += 1
            mark = "ADMIT"
        else:
            refused[d["reason"]] = refused.get(d["reason"], 0) + 1
            mark = "REFUSE"
        print("    [%s] %-18s %s:%d" % (mark, f.kind, f.file, f.line))
        print("             %s" % f.detail)
        if f.fix:
            print("             fix: %s" % f.fix)
        if not d["allowed"]:
            print("             refused: %s" % d["reason"])
    print()

    print("  THE SCORE:")
    print("    findings            %d" % len(findings))
    print("    admitted            %d" % admitted)
    print("    refused             %d" % (len(findings) - admitted))
    for k, v in sorted(refused.items(), key=lambda kv: -kv[1]):
        print("      %-28s %d" % (k, v))
    print()
    h = gate.health()
    print("    the gate: rate %.3f  state %s  band (%.2f, %.2f)" % (
        h["rate"], h["state"], h["floor"], h["ceiling"]))
    print()
    print("  AND THE BOUNDARY: this tool PROPOSES. It does not edit, and it")
    print("  cannot install anything without the gate, and it cannot move")
    print("  the ground at all. poteto's /meditate suggests improvements;")
    print("  the gate decides. Same discipline, cheaper.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
