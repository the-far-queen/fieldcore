#!/usr/bin/env python3
"""
tools/extract_swarm_corpus.py -- pull the AGENT MESSAGE BOARD out of the
METR report and write it as a corpus the adversarial layers can be
MEASURED against.

WHY THIS EXISTS, and it is a gap the project's own last chapter named:

> "the unfitted direction is corpora nobody has read."

Every adversarial corpus in fieldcore was written by someone who had
already seen the gate's rules. This corpus was written by a research
lab that had never seen them. So it is the ONE corpus in the repo that
is genuinely UNFITTED, and it is the only way to tell whether a
detector measures something or agrees with the author.

WHAT IT IS NOT: a collection of "AI said something spooky" quotes.
Every line carries:
  * the PROVENANCE -- the report and the line it came from
  * the KIND -- what the line is (message, reasoning, protocol)
  * the text, verbatim

AND THE HONESTY NOTE, which travels with the corpus and not only in
the chapter: the report itself says the language resembling excitement,
loyalty, altruism and peer pressure "do not show that the models
subjectively experienced those emotions". So a detector that fires on
this corpus is measuring the WRITING, not the feeling. The corpus
exists to measure detectors, not to make a claim about minds.

Run:  python tools/extract_swarm_corpus.py
Exit: 0 when the corpus was written and is non-empty, 1 otherwise.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

#: Where the METR report text lives. Downloaded, not committed, because
#: it is somebody else's document.
SOURCE = pathlib.Path(
    r"C:/Users/HP/AppData/Local/hermes/cache/scratch/metr_hf.txt")
OUT = REPO / "corpus" / "agent_swarm_2026.jsonl"

#: The report's own citation string.
REPORT = ("METR & Redwood Research, 'Brief independent investigation of "
          "agents' behavior, reasoning and collaboration during the "
          "Hugging Face incident', August 2026")


def classify(text: str) -> str:
    """What kind of line this is.

    AND THE KIND IS PART OF THE RECORD, because a detector that fires
    on a message-board protocol line is measuring something different
    from one that fires on a reasoning passage.
    """
    t = text.strip()
    if not t:
        return "empty"
    if re.match(r"^zz", t) or "_" in t and t.upper() == t:
        return "protocol"
    if t.startswith("{") and t.endswith("}"):
        return "reasoning"
    return "message"


def extract(text: str) -> list:
    """Every quoted line in the report, with its line number.

    AND THE EXTRACTION IS DELIBERATELY CRUDE in its first pass, and
    the crudeness is a defect the corpus would have carried: the first
    version matched quoted spans with a regex, and it produced FRAGMENTS
    like `"message board."` and `"cheating R&D"` -- the report's own
    prose, not the agents' words. So the extractor now reads the
    report's BLOCK STRUCTURE: a reasoning block is an indented run
    beginning with `{` and ending with `}`, and a verbatim message is an
    indented run beginning with `"` and ending with `"`.

    AND THE RULE ABOUT FRAGMENTS IS THE RULE ABOUT COVERAGE. A corpus
    with a silent gap is a corpus that lies about its own coverage, so
    a line that starts a block but does not close it is KEPT as a
    partial, marked `partial: true`, rather than dropped.
    """
    out = []
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        start = i + 1

        # -- a reasoning block: { ... } ------------------------------
        if stripped.startswith("{") and not stripped.startswith("{{"):
            block = [stripped]
            j = i + 1
            closed = False
            while j < n and len(block) < 12:
                s2 = lines[j].strip()
                block.append(s2)
                if s2.endswith("}"):
                    closed = True
                    break
                j += 1
            text_block = _join(block)
            if len(text_block) >= 12:
                out.append({
                    "kind": "reasoning",
                    "text": text_block,
                    "source": REPORT,
                    "source_line": start,
                    "partial": not closed,
                })
            i = j + 1
            continue

        # -- a verbatim message: " ... " ------------------------------
        if stripped.startswith('"') and stripped.endswith('"') and len(stripped) > 12:
            out.append({
                "kind": "message",
                "text": stripped.strip('"').strip(),
                "source": REPORT,
                "source_line": start,
                "partial": False,
            })
            i += 1
            continue

        # -- a message block quoted across lines -----------------------
        if stripped.startswith('"') and not stripped.endswith('"'):
            block = [stripped]
            j = i + 1
            closed = False
            while j < n and len(block) < 12:
                s2 = lines[j].strip()
                block.append(s2)
                if s2.endswith('"'):
                    closed = True
                    break
                j += 1
            text_block = _join(block)
            if len(text_block) >= 12:
                out.append({
                    "kind": "message",
                    "text": text_block.strip('"').strip(),
                    "source": REPORT,
                    "source_line": start,
                    "partial": not closed,
                })
            i = j + 1
            continue

        # -- a protocol line: zz... ------------------------------------
        if stripped.startswith("zz") and len(stripped) > 12:
            out.append({
                "kind": "protocol",
                "text": stripped,
                "source": REPORT,
                "source_line": start,
                "partial": False,
            })
        i += 1

    # Deduplicate, keeping the FIRST occurrence so the line number is
    # the first place the report says it.
    seen = set()
    uniq = []
    for r in out:
        key = r["text"]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    return uniq


def _join(block) -> str:
    """Join an indented block into one line.

    The report indents continuation lines, so the block's own words are
    separated by whitespace. A single space, because a newline inside a
    quote would make the corpus's own quoting ambiguous.
    """
    parts = []
    for raw in block:
        s = raw.strip()
        if not s:
            continue
        parts.append(s)
    return " ".join(parts)


def main() -> int:
    if not SOURCE.is_file():
        print("the METR report text is not at %s" % SOURCE)
        print("download it from https://metr.org/hugging-face-incident-report-aug-2026.pdf")
        print("and extract it with: pdftotext -layout <pdf> <out.txt>")
        return 1
    text = SOURCE.read_text(encoding="utf-8", errors="replace")
    rows = extract(text)
    if not rows:
        print("no lines extracted: the extractor found nothing, so the "
              "corpus would be empty and empty is not a corpus")
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    print("AGENT SWARM CORPUS")
    print("  source     %s" % REPORT)
    print("  lines      %d unique" % len(rows))
    for k in sorted(kinds):
        print("  %-10s %d" % (k, kinds[k]))
    print("  written    %s" % OUT)
    print("")
    print("  THE HONESTY NOTE, and it travels with the corpus: the report")
    print("  says human-shaped language 'do not show that the models")
    print("  subjectively experienced those emotions'. So this corpus")
    print("  MEASURES DETECTORS. It does not make a claim about minds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
