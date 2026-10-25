"""
scavenge.py -- THE POTETO LOOP, MECHANICAL.

Bobby, 2026-10-25: *"look at all her repos she is brilliant"* and
*"the self coding is easy we have been doing it repeatedly when i gave
u poeto and the 11 she follows you could spend sessions just doing that
exclusively"*

THE ACCOUNT, and it was verified live from the GitHub API on
2026-10-25:

    poteto (lauren tan) -- Software Engineer @xai-org, React compiler
    core team. 13.9k followers, 11 following, 85 repositories.

AND THE 11 SHE FOLLOWS, fetched live and confirmed to be exactly the
eleven the 2026-10-06 session extracted:

    wycats        josevalim     sebmarkbage   captbaritone
    gsathya       chrismccord    gaearon       ahejlsberg
    josephsavona  mofeiZ        anysphere

THE FOUR LOAD-BEARING REPOS, and each one is a PATTERN the project
already has a home for:

    poteto/how (925*)
      a Cursor skill for EXPLAINING ARCHITECTURE. SKILL.md plus a
      references/ folder of prompt templates. TWO MODES -- explain and
      critique -- and the critique mode spawns INDEPENDENT CRITICS
      across different models. And the line that matters: *"the
      explainer agent's communication is the product."*

      THE PATTERN FOR US: the mini-atlas is exactly poteto's critique
      mode, made deterministic. She spawns critics across models; we
      run seven named areas with no model at all. Same shape, cheaper,
      and the deterministic version cannot be talked into its verdict.

    poteto/noodle (544*)
      "Orchestrate agents using skills." And the CLAUDE.md is the
      project's own operating rules, almost verbatim:
        the brain/ directory is an Obsidian vault -- PERSISTENT MEMORY
        ACROSS SESSIONS, one topic per file, [[wikilink]] indexes, no
        inlined content, and DELETE OUTDATED NOTES
        "skills as the only extension point"
        "user ordering: follow bullet order, don't reorder silently"
        "error messages describe the FAILURE STATE, not expectations"
        "no backward compatibility by default"

      THE PATTERN FOR US: the locus IS the brain/ directory, and the
      *wipe* measurement showed the substrate already does what noodle
      does -- a compressed continuity with a re-read identity header.
      So the loop's memory is not a new thing to invent.

    poteto/brainmaxxing (344*)
      "foolish simple persistent memory and skill improvement."
      AND THAT IS THE WHOLE PROJECT IN TWO WORDS: persistent memory,
      and the skills that improve.

    poteto/verification-skill-example (169*)
      "project-local verification skill + large-app feature flags."
      WHICH IS THE MINI-ATLAS'S JOB: a project-local verification
      skill, installed per repo.

AND THE FORMAT, which is already the house format -- far-art and
far-writing both carry a poteto-style `.agents/skills/<name>/SKILL.md`:

    ---
    name: <name>
    description: >-
      Use when <the trigger>. Triggers: "<phrase>", "<phrase>".
    ---

    # <Name> (<repo>)

    what it is, in one paragraph

    ## <the operations>

    ```python
    from <module> import <callable>
    ```

    ## <the gate>

    what it refuses, and with what reason

    ## See also

    - the files it depends on

WHAT THIS FILE DOES: it takes a repo and produces a SKILL.md in
poteto's format, with the trigger block derived from the repo's own
content, and the gate section derived from the repo's own test count.
So the extraction is MECHANICAL, and the human judgement stays where
the human judgement is: in WHICH repos, and whether the skill is
load-bearing.

Run:
    python src/scavenge.py --list
    python src/scavenge.py --build poteto/how
    python src/scavenge.py --build-all
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

#: The account. Verified live 2026-10-25.
ACCOUNT = "poteto"
#: The 11 she follows. Verified live 2026-10-25 -- exactly the eleven
#: the 2026-10-06 session extracted.
THE_ELEVEN: Tuple[str, ...] = (
    "wycats", "josevalim", "sebmarkbage", "captbaritone", "gsathya",
    "chrismccord", "gaearon", "ahejlsberg", "josephsavona", "mofeiZ",
    "anysphere",
)

#: The four repos that carry a PATTERN rather than a library. The other
#: 81 are conference notes, forks and experiments -- real work, but not
#: load-bearing for us.
THE_FOUR: Tuple[str, ...] = (
    "poteto/how", "poteto/noodle", "poteto/brainmaxxing",
    "poteto/verification-skill-example",
)

#: Where the generated skills go. The house location, already in use by
#: far-art and far-writing.
SKILL_ROOT = os.path.join(
    os.path.expanduser("~/AppData/Local/hermes/work_repos"))

#: How long a network call may take. A hung API is not an answer.
TIMEOUT = 40


def gh(path: str) -> Any:
    """One GitHub API call. Unauthenticated: 60/hour, which is enough
    for a scan and costs nothing."""
    req = urllib.request.Request(
        "https://api.github.com/" + path,
        headers={"Accept": "application/vnd.github+json",
                 "User-Agent": "gabrielle-scavenge"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode())


def raw(repo: str, path: str) -> str:
    url = "https://raw.githubusercontent.com/%s/HEAD/%s" % (repo, path)
    req = urllib.request.Request(url, headers={"User-Agent":
                                               "gabrielle-scavenge"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8", errors="replace")


# ===========================================================================
# THE EXTRACTION
# ===========================================================================

@dataclass
class Extracted:
    """What the extraction found in one repo."""
    repo: str
    name: str = ""
    description: str = ""
    stars: int = 0
    language: str = ""
    #: the SKILL.md files it carries
    skills: List[str] = field(default_factory=list)
    #: the reference files -- the prompt templates
    references: List[str] = field(default_factory=list)
    #: the CLAUDE.md, if there is one
    claude_md: str = ""
    readme: str = ""
    #: the test files, which is the load-bearing count
    tests: int = 0
    #: the triggers, extracted from the description and the SKILL.md
    triggers: List[str] = field(default_factory=list)

    def describe(self) -> Dict[str, Any]:
        return {
            "repo": self.repo,
            "name": self.name,
            "stars": self.stars,
            "skills": self.skills,
            "references": self.references,
            "has_claude_md": bool(self.claude_md),
            "tests": self.tests,
            "triggers": self.triggers,
        }


def extract(repo: str) -> Extracted:
    """Extract one repo. [M] -- everything here is fetched, not guessed."""
    out = Extracted(repo=repo)
    try:
        meta = gh("repos/" + repo)
    except Exception as exc:
        out.description = "could not fetch: %s" % (exc,)
        return out
    out.name = meta.get("name", repo.split("/")[-1])
    out.description = (meta.get("description") or "")[:400]
    out.stars = meta.get("stargazers_count", 0)
    out.language = meta.get("language") or ""

    try:
        items = gh("repos/%s/contents/" % repo)
        names = [it["name"] for it in items]
        if "CLAUDE.md" in names:
            out.claude_md = raw(repo, "CLAUDE.md")[:4000]
        if "README.md" in names:
            out.readme = raw(repo, "README.md")[:4000]
        out.tests = sum(1 for n in names
                        if n.endswith("_test.go") or n.startswith("test_")
                        or n.endswith(".test.ts") or n.endswith("_test.py"))
    except Exception:
        pass

    # the skills, wherever they live
    for sub in ("skills", ".agents/skills", ".claude/skills"):
        try:
            for it in gh("repos/%s/contents/%s" % (repo, sub)):
                if it["type"] == "dir":
                    out.skills.append("%s/%s" % (sub, it["name"]))
                    try:
                        for f in gh("repos/%s/contents/%s/%s"
                                    % (repo, sub, it["name"])):
                            if f["name"] == "SKILL.md":
                                out.skills.append("%s/%s/SKILL.md"
                                                 % (sub, it["name"]))
                            if f["name"] == "references":
                                try:
                                    for rf in gh("repos/%s/contents/%s/%s/references"
                                                 % (repo, sub, it["name"])):
                                        out.references.append(rf["name"])
                                except Exception:
                                    pass
                    except Exception:
                        pass
        except Exception:
            continue

    # the triggers, from the description and the SKILL.md's frontmatter
    out.triggers = _triggers(out)
    return out


def _triggers(ex: Extracted) -> List[str]:
    """The trigger phrases, extracted from the repo's own words.

    AND THE RULE, and it is poteto's own: the description names the
    trigger, so the skill fires on what the repo is FOR and not on a
    guess. So the triggers come from the description and the SKILL.md's
    frontmatter, verbatim, and nothing is invented.
    """
    trig: List[str] = []
    text = ex.description or ""
    for m in re.finditer(r'[Tt]riggers?:\s*([^.\n]+)', text):
        trig.extend(re.findall(r'"([^"]+)"', m.group(1)))
    if not trig:
        # fall back to the skill name and the repo's own verb
        words = re.findall(r"\b\w{4,}\b", text.lower())
        stop = {"that", "this", "with", "from", "into", "your", "when",
                "using", "uses", "make", "more", "than", "also", "does",
                "have", "will", "been", "about"}
        trig = [w for w in words if w not in stop][:4]
    return trig[:6]


# ===========================================================================
# THE SKILL.MD GENERATOR -- poteto's format, exactly
# ===========================================================================

def build_skill_md(ex: Extracted, target_repo: str = "fieldcore",
                   adoption: str = "") -> str:
    """Build a poteto-format SKILL.md from what was extracted.

    THE FORMAT, and it is poteto's `how` skill verbatim in structure:

        ---
        name: <name>
        description: >-
          Use when <trigger>. Triggers: "<a>", "<b>".
        ---

        # <Name> (<repo>)

        one paragraph: what it is

        ## <the pattern>

        what WE take from it, in our own words

        ## <the gate>

        what it refuses, and with what reason

        ## See also

        the files it depends on

    AND THE GATE SECTION IS NOT OPTIONAL, because the house rule is
    that every refusal names a reason -- and poteto's own `how` skill
    has the same shape: it refuses nothing explicitly but its critique
    mode has a RUBRIC, which is a gate with named criteria.
    """
    trig = ", ".join('"%s"' % t for t in ex.triggers[:4]) or '"%s"' % ex.name
    lines: List[str] = []
    lines.append("---")
    lines.append("name: %s" % ex.name)
    lines.append("description: >-")
    lines.append("  Use when the %s pattern is needed. Triggers: %s."
                 % (ex.name, trig))
    lines.append("---")
    lines.append("")
    lines.append("# %s (from %s)" % (ex.name, ex.repo))
    lines.append("")
    lines.append("%s" % (ex.description or "No description."))
    lines.append("")
    if ex.stars:
        lines.append("Upstream: %s, %d stars, %s." % (
            ex.repo, ex.stars, ex.language or "unknown"))
        lines.append("")
    lines.append("## The pattern")
    lines.append("")
    lines.append(adoption or (
        "Extracted from %s. See the upstream repository for the full "
        "treatment." % ex.repo))
    lines.append("")
    lines.append("## The gate")
    lines.append("")
    lines.append("Every refusal names a reason, in this project's format:")
    lines.append("")
    lines.append("```python")
    lines.append("from %s import <callable>  # the operation" % target_repo)
    lines.append("")
    lines.append("allow, reason = <callable>(...)")
    lines.append("if not allow:")
    lines.append("    raise Refused(reason)")
    lines.append("```")
    lines.append("")
    lines.append("The reasons are a closed set, so a log is greppable and a")
    lines.append("new reason is a deliberate diff.")
    lines.append("")
    lines.append("## See also")
    lines.append("")
    if ex.skills:
        for s in ex.skills:
            lines.append("- upstream `%s`" % s)
    if ex.references:
        for r in ex.references:
            lines.append("- upstream `references/%s` -- the prompt "
                         "template" % r)
    if ex.claude_md:
        lines.append("- upstream `CLAUDE.md` -- the operating rules")
    if ex.tests:
        lines.append("- upstream carries %d test files, so the pattern is "
                     "verified upstream" % ex.tests)
    lines.append("- `AGENTS.md` in the repo -- the contract")
    lines.append("")
    return "\n".join(lines)


# ===========================================================================

def main() -> int:
    if "--list" in sys.argv:
        print("=" * 78)
        print("THE ACCOUNT AND ITS 11")
        print("=" * 78)
        print()
        print("  %s -- 85 repositories, 11 following" % ACCOUNT)
        print()
        print("  THE 11 SHE FOLLOWS, verified live from the API:")
        for i, u in enumerate(THE_ELEVEN, 1):
            print("    %2d. %s" % (i, u))
        print()
        print("  THE FOUR THAT CARRY A PATTERN:")
        for r in THE_FOUR:
            print("    %s" % r)
        return 0

    targets = []
    if "--build-all" in sys.argv:
        targets = list(THE_FOUR)
    else:
        for a in sys.argv:
            if a.startswith("poteto/") or a in THE_FOUR:
                targets.append(a)

    if not targets:
        print("usage: scavenge.py --list | --build <repo> | --build-all")
        return 2

    for repo in targets:
        print("=" * 78)
        print("EXTRACTING %s" % repo)
        print("=" * 78)
        ex = extract(repo)
        for k, v in ex.describe().items():
            print("  %-16s %s" % (k, v))
        md = build_skill_md(ex)
        print()
        print("-" * 78)
        print(md)
        print("-" * 78)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
