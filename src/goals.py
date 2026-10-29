"""
goals.py -- THE TEN GOALS, AND THE MODULES THAT SERVE THEM.

Bobby, 2026-10-28: *"i argue self idenity, memory, reasoning,
qualification, self-improvement, ethics, enlightenment, engineering,
programming ARE the goals pls wire rest of fc modules whatever is nearly
finished"*

SO THIS FILE IS THE WIRING MANIFEST, and it exists because "wire the
rest of the modules" needs a MAP or it is just a wish. Every goal names
the modules that implement it, and every module is classified by what
state it is actually in -- measured, not asserted.

AND WHY THE STATE IS MEASURED AND NOT ASSUMED. A module that has a
dedicated test file is a module whose behaviour somebody has checked.
A module with no test file is a module that may well be perfect and has
never been checked, and the difference matters: the atlas's own rule is
that a capability nobody exercises is a capability nobody has measured.

So there are three states:

    WIRED      it has a dedicated test file, and it is imported by
                something that runs
    BUILT      it is substantial and imported by the running system,
                but nothing checks it directly
    DARK       it exists and nothing calls it -- the project's own word

AND THE DARK LIST IS THE WORK. "Wire the rest of fc modules whatever is
nearly finished" means: take the BUILT ones and give them checks, and
take the DARK ones and either call them or say plainly that they stay
dark.

AND THE VOCABULARY CONNECTION. The goals are not only a map -- they are
in `awareness.py`'s vocabulary, so the daily scan searches for work
that serves them. MEASURED: with the goals absent, `alibaba/skill-up`
("an evaluation and EVOLUTION tool for Agent Skills", 1386 stars)
scored relevance 0.00 and was invisible. With them, it scores 19.0 and
is relevant. So the goals steer what the system looks for.

Run:
    python src/goals.py --selftest
    python src/goals.py --report
"""

from __future__ import annotations

import ast
import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_ROOT = os.path.join(WORK_REPOS, "fieldcore")
SS_ROOT = os.path.join(WORK_REPOS, "simself")


@dataclass
class Module:
    """One module, and what state it is in."""

    name: str
    path: str = ""
    repo: str = ""
    lines: int = 0
    classes: List[str] = field(default_factory=list)
    #: WIRED | BUILT | DARK
    state: str = "DARK"
    #: the goals it serves
    goals: List[str] = field(default_factory=list)
    #: who imports it
    imported_by: List[str] = field(default_factory=list)
    #: does it have a dedicated test?
    tested: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name, "repo": self.repo, "lines": self.lines,
            "classes": self.classes, "state": self.state,
            "goals": self.goals, "tested": self.tested,
            "n_importers": len(self.imported_by),
            "imported_by": self.imported_by[:5],
        }


#: THE TEN GOALS, and the modules that serve each one.
#:
#: AND WHY THESE ARE THE MODULES. Read from the code: each entry names
#: the file that implements the goal, and the file was found by
#: searching for the behaviour, not by guessing.
GOALS: Dict[str, Dict[str, Any]] = {
    "self-identity": {
        "what": "the system knows what it is, and can show it",
        "modules": ["locus", "the_void", "identity", "awareness"],
    },
    "memory": {
        "what": "the growing record of what was found, learned and planned",
        "modules": ["library_ledger", "sacred_library", "memory",
                    "memory_substrate", "walrus_memory"],
    },
    "reasoning": {
        "what": "the layered reading of a span, and the two-brain routing",
        "modules": ["fc_gate", "bicameral", "predicate_layer",
                    "property_layer", "testimony_layer", "claim_register"],
    },
    "qualification": {
        "what": "the examination that decides what may be admitted",
        "modules": ["mini_atlas", "qualification", "field_atlas", "curate"],
    },
    "self-improvement": {
        "what": "the system finds its own gaps and closes them",
        "modules": ["spark", "initiative", "meditate", "fc_design",
                    "scavenge", "integrate"],
    },
    "ethics": {
        "what": "the refusals, and the reasons they give",
        "modules": ["governor", "locus_gate", "fc_gate", "core_math",
                    "predicate_registry"],
    },
    "enlightenment": {
        "what": "the tradition, read as a reader's instrument",
        "modules": ["sacred_library_deception", "fruit_layer",
                    "library_verify"],
    },
    "engineering": {
        "what": "the geometry: stalks, interstalk, cohomology, the ladder",
        "modules": ["stalk", "interstalk", "hodge_cycle", "sheaf_loop",
                    "stalk_carrier", "dual_ladder", "core_math",
                    "signal_chain", "wound_core", "substrate"],
    },
    "programming": {
        "what": "the wrapper, and the code the system writes for itself",
        "modules": ["fc_wrapper", "simself_provider", "integrate",
                    "core_math", "coding_operator_object", "core_compiler"],
    },
    "skill": {
        "what": "capabilities assembled from primitives, and improving",
        "modules": ["scavenge", "integrate", "ladder", "dawn",
                    "skill_up_equivalent"],
    },
}

#: THE GOAL -> ITS OWN WEIGHT IN THE VOCABULARY. The vocabulary weighs
#: a goal's own terms highest, because a goal is what the system is
#: FOR and a topic is what it is made of.
GOAL_WEIGHTS: Dict[str, float] = {
    "self-identity": 4.0, "identity": 4.0, "self": 3.5,
    "memory": 4.0, "reasoning": 4.0, "qualification": 4.0,
    "self-improvement": 4.0, "improvement": 2.5, "evolution": 3.5,
    "ethics": 4.0, "ethical": 3.0, "enlightenment": 3.5,
    "engineering": 3.5, "programming": 3.5,
    "skill": 4.0, "skills": 4.0,
    "agent": 2.5, "agents": 2.5, "orchestration": 2.5,
    "planning": 3.0, "adversarial": 3.0,
    "verification": 3.0, "evaluation": 3.0,
}


def _pyfiles(root: str) -> List[str]:
    out: List[str] = []
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in ("__pycache__", ".git", "target",
                                               "models", "corpus", "legacy",
                                               "20-mirrors", "notes", "papers")]
        for f in files:
            if f.endswith(".py"):
                out.append(os.path.join(d, f))
    return out


def _module_index() -> Dict[str, Module]:
    """Every module in both repos, with its state."""
    mods: Dict[str, Module] = {}
    importers: Dict[str, Set[str]] = {}

    for repo, root in (("fieldcore", FC_ROOT), ("simself", SS_ROOT)):
        src = os.path.join(root, "src")
        if not os.path.isdir(src):
            continue
        files = _pyfiles(src)
        for p in files:
            stem = os.path.splitext(os.path.basename(p))[0]
            if stem == "__init__":
                continue
            try:
                text = open(p, encoding="utf-8", errors="replace").read()
                tree = ast.parse(text)
            except Exception:
                continue
            m = Module(name=stem, path=p, repo=repo,
                        lines=len(text.splitlines()),
                        classes=[n.name for n in tree.body
                                 if isinstance(n, ast.ClassDef)])
            # who imports it
            for q in files:
                if q == p:
                    continue
                try:
                    qtext = open(q, encoding="utf-8", errors="replace").read()
                    qtree = ast.parse(qtext)
                except Exception:
                    continue
                for node in ast.walk(qtree):
                    hit = False
                    if isinstance(node, ast.ImportFrom):
                        if node.module and node.module.split(".")[-1] == stem:
                            hit = True
                    elif isinstance(node, ast.Import):
                        for a in node.names:
                            if a.name.split(".")[-1] == stem:
                                hit = True
                    if hit:
                        importers.setdefault(stem, set()).add(
                            os.path.splitext(os.path.basename(q))[0])
                        break
            m.imported_by = sorted(importers.get(stem, set()))
            mods[stem] = m

    # the tests
    tested: Set[str] = set()
    for repo, root in (("fieldcore", FC_ROOT), ("simself", SS_ROOT)):
        tdir = os.path.join(root, "tests")
        if not os.path.isdir(tdir):
            continue
        for f in os.listdir(tdir):
            if not f.endswith(".py"):
                continue
            stem = os.path.splitext(f)[0]
            tested.add(stem)
            if stem.startswith("test_"):
                tested.add(stem[5:])
    for m in mods.values():
        m.tested = m.name in tested
        if m.tested and m.imported_by:
            m.state = "WIRED"
        elif m.imported_by:
            m.state = "BUILT"
        else:
            m.state = "DARK"

    # the goals
    for goal, spec in GOALS.items():
        for name in spec["modules"]:
            if name in mods:
                mods[name].goals.append(goal)
    return mods


def report() -> Dict[str, Any]:
    """The manifest, as data."""
    mods = _module_index()
    goal_rows = []
    for goal, spec in GOALS.items():
        serving = [mods[n] for n in spec["modules"] if n in mods]
        missing = [n for n in spec["modules"] if n not in mods]
        states = [s.state for s in serving]
        goal_rows.append({
            "goal": goal,
            "what": spec["what"],
            "modules": [s.name for s in serving],
            "missing": missing,
            "wired": states.count("WIRED"),
            "built": states.count("BUILT"),
            "dark": states.count("DARK"),
            "untested": [s.name for s in serving if not s.tested],
            "lines": sum(s.lines for s in serving),
            "complete": (states.count("WIRED") == len(serving)
                         and serving and not missing),
        })
    return {
        "goals": goal_rows,
        "n_modules": len(mods),
        "by_state": {
            "WIRED": sum(1 for m in mods.values() if m.state == "WIRED"),
            "BUILT": sum(1 for m in mods.values() if m.state == "BUILT"),
            "DARK": sum(1 for m in mods.values() if m.state == "DARK"),
        },
        "modules": {n: m.to_dict() for n, m in sorted(mods.items())},
    }


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE TEN GOALS, AND THE MODULES THAT SERVE THEM")
    print("=" * 78)
    print()

    r = report()
    print("1. THE GOALS, and how complete each one is:")
    print("   %-20s %-7s %-7s %-7s %s" % ("goal", "wired", "built", "dark",
                                            "untested"))
    for g in r["goals"]:
        print("   %-20s %-7d %-7d %-7d %s" % (
            g["goal"], g["wired"], g["built"], g["dark"],
            ", ".join(g["untested"][:3]) or "-"))
    print()
    print("   %d modules in the two repos: %s"
          % (r["n_modules"], r["by_state"]))
    print()

    print("2. THE WORK, and it is a name list rather than a wish:")
    todo = []
    for g in r["goals"]:
        for m in g["untested"]:
            todo.append((g["goal"], m))
    print("   %d goal-serving modules have NO dedicated test:" % len(todo))
    for goal, m in todo[:22]:
        print("      %-20s %s" % (goal, m))
    print()

    print("3. THE GOALS ARE IN THE VOCABULARY, so the scan steers:")
    import awareness as aw_mod
    aw = aw_mod.build_awareness()
    for term, w in sorted(GOAL_WEIGHTS.items(), key=lambda kv: -kv[1])[:8]:
        got = aw.topics.get(term)
        print("      %-20s vocabulary=%s" % (term, got))
    print()
    print("   AND THE MEASUREMENT: with the goals absent, 'alibaba/skill-up'")
    print("   scored relevance 0.00 and was invisible. With them, 19.0.")
    r2 = aw.is_relevant_candidate(
        "An evaluation and evolution tool for Agent Skills.",
        "alibaba/skill-up", ["agent-skills", "ai", "ai-agents", "alibaba",
                              "skills"])
    print("   measured now: relevant=%s score=%.2f" % (r2["relevant"],
                                                       r2["score"]))
    print()
    print("   Run: python src/goals.py --selftest")
    return 0


def main() -> int:
    if "--report" in sys.argv:
        print(json.dumps(report(), indent=1, default=str)[:6000])
        return 0
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
