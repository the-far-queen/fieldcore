#!/usr/bin/env python3
"""
sync_derived_terms.py -- WRITE THE DERIVED TERMS INTO THE REGISTER.

Bobby, 2026-11-07.

**AND THE REGISTER'S OWN RULE IS "THE DERIVATION IS A COMMAND".** MEASURED
2026-11-07: `tools/derive_mltr_terms.py --check` reported

    derived terms: 106   in the register: 106   missing: 1   extra: 1
       MISSING cover
       EXTRA   compatible

and the two were the SAME WORD COUNT -- so the register held 106 derived
terms and the derivation produced 106, and they were not the same 106.

**AND THE CAUSE WAS MEASURED, AND IT WAS NOT A DEFECT IN THE REGISTER.**
`compatible` was derived, and then it stopped being derived, because the
derivation refuses a word whose ENRICHMENT is below 2.000 -- how much
of the word's usage sits inside its own domain family. MEASURED:
`compatible` had an enrichment of 1.652, and the reason was that the
new `sheaf_bridge` uses the word and is not in the control family.

**AND THE HONEST FIX WAS TO PUT THE BRIDGE IN THE FAMILY**, because the
family is a list of what the module IS, and the bridge reads two sheafs
and refuses when they disagree -- it is a control instrument.

**AND THEN FOUR NEW TERMS APPEARED**, all of them real and all of them
from the new sheaf code: `coherent`, `cover`, `identity`, `overlap`.

**AND THIS TOOL WRITES THE BLOCK, so the register is a FUNCTION OF THE
SUBSTRATE and not a hand-kept list.** The register's own rule says the
derivation is a command; this makes the register's derived block the
output of that command.

Run:
    python tools/sync_derived_terms.py --check
    python tools/sync_derived_terms.py --write
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
REGISTER = os.path.join(REPO, "src", "mltr_register.py")
DERIVE = os.path.join(HERE, "derive_mltr_terms.py")

#: THE LINE THAT BEGINS A DERIVED TERM, and the one that begins a
#: curated term. The distinction is the `derived:` in the source field.
TERM_RE = re.compile(r'^\s*Term\("(\w+)",')

#: THE FINGERPRINT LINE, and it is matched as a WHOLE LINE so the
#: prose above it cannot be mistaken for the value.
FINGERPRINT_RE = re.compile(r'^DERIVED_AT_FINGERPRINT = "([0-9a-f]*)"$',
                            re.M)


def emitted_terms() -> Tuple[List[Tuple[str, str, str, float, float, str]], str]:
    """The derived terms, as the derivation produces them.

    **AND THE GLOSS AND THE TWO AXES COME FROM THE TOOL AND NOT FROM
    HERE.** A derived term cannot carry a hand-assigned number and call
    it measured -- that is the register's own rule.

    **AND IT RETURNS THE FINGERPRINT TOO**, because the register names
    the input it was derived from and only the derivation can compute
    it.
    """
    rows, fingerprint = emitted_rows()
    out = []
    for row in rows:
        out.append((row["word"], row["gloss"], row["domain"],
                    float(row["mmm"]), float(row["snr"]),
                    "derived:canon_vocab.json:%s+canon_corpus:%s"
                    % (row["canon"], row["domain"])))
    return out, fingerprint


def emitted_rows() -> Tuple[List[Dict], str]:
    """the derivation's rows, and the fingerprint of the input it read."""
    proc = subprocess.run([sys.executable, "-B", DERIVE, "--json"],
                          capture_output=True, text=True, cwd=REPO)
    if proc.returncode != 0:
        raise SystemExit("the derivation failed:\n%s" % proc.stderr[-1500:])
    data = json.loads(proc.stdout[proc.stdout.find("{"):])
    return data["rows"], str(data.get("source_fingerprint", ""))


def _escape(text: str) -> str:
    """The gloss, escaped for a python string literal."""
    return text.replace("\\", "\\\\").replace('"', '\\"')


def render(terms: Sequence[Tuple[str, str, str, float, float, str]]) -> List[str]:
    """The block, as the lines that go into the register."""
    lines = []
    for word, gloss, domain, mmm, snr, source in terms:
        lines.append(
            '        Term("%s", "%s", "%s", %.2f, %.2f, "%s"),'
            % (word, _escape(gloss), domain, mmm, snr, source))
    return lines


def current_block(text: str) -> Tuple[int, int]:
    """The derived block's line range, as (first, last) 0-based."""
    lines = text.splitlines()
    idxs = [i for i, l in enumerate(lines)
            if l.strip().startswith('Term("') and "derived:" in l]
    if not idxs:
        raise SystemExit("the register holds no derived terms")
    return idxs[0], idxs[-1]


def fingerprint_line(text: str) -> str:
    """the fingerprint the register names, or "" if it names none."""
    m = FINGERPRINT_RE.search(text)
    return m.group(1) if m else ""


def write_fingerprint(text: str, fingerprint: str) -> str:
    """the register, with the fingerprint naming the input it came from.

    AND WHY THE CONSTANT IS REPLACED RATHER THAN APPENDED. The
    register is a FIXED SET IN CODE and the constant is a line in it,
    so the sync tool rewrites the line in place. Appending a second
    one would leave two answers to "which input is this a snapshot
    of", and the second would win at import -- which is the register's
    own defect (a word in it twice is a word with two types) applied
    to its own provenance.
    """
    line = 'DERIVED_AT_FINGERPRINT = "%s"' % fingerprint
    if FINGERPRINT_RE.search(text):
        return FINGERPRINT_RE.sub(lambda _m: line, text, count=1)
    anchor = "REGISTER: Tuple[Term, ...] = ("
    if anchor not in text:
        raise SystemExit("the register has no REGISTER tuple to anchor on")
    return text.replace(anchor, line + "\n\n" + anchor, 1)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args(argv)

    terms, fingerprint = emitted_terms()
    text = open(REGISTER, encoding="utf-8").read()
    first, last = current_block(text)
    lines = text.splitlines()
    have = [re.match(TERM_RE, lines[i]).group(1) for i in
            range(first, last + 1)
            if re.match(TERM_RE, lines[i])]

    want = [t[0] for t in terms]
    missing = [w for w in want if w not in have]
    extra = [w for w in have if w not in want]
    reordered = (not missing and not extra
                 and have != want)
    #: THE FINGERPRINT IN THE REGISTER, and whether it still names the
    #: input the derivation just read. AND WHY IT IS CHECKED HERE AND
    #: NOT ONLY IN THE BLOCK: the block can be identical while the
    #: input moved -- the derivation is not sensitive to every change
    #: -- and then the register is a snapshot of an input nobody can
    #: name. So the fingerprint is compared too.
    stamp = fingerprint_line(text)
    stamp_ok = (stamp == fingerprint)

    print("the derived terms the derivation produces: %d" % len(want))
    print("the derived terms the register holds:       %d" % len(have))
    print("the fingerprint the register names:         %s"
          % (stamp or "(none)"))
    print("the fingerprint the derivation read:        %s" % fingerprint)
    print()
    if missing:
        print("   MISSING %s" % ", ".join(missing))
    if extra:
        print("   EXTRA   %s" % ", ".join(extra))
    if reordered:
        print("   THE ORDER DIFFERS")
    if not stamp_ok:
        print("   THE FINGERPRINT DIFFERS -- the register names a "
              "different input")
    if not (missing or extra or reordered) and stamp_ok:
        print("   the register's derived block IS the derivation's output")
        print("   and it names the input it was derived from")
        print()
        return 0

    if not args.write:
        print()
        print("   run with --write to make the register the derivation's output")
        return 1

    new_lines = lines[:first] + render(terms) + lines[last + 1:]
    out = "\n".join(new_lines) + "\n"
    out = write_fingerprint(out, fingerprint)
    with open(REGISTER, "w", encoding="utf-8") as fh:
        fh.write(out)
    print()
    print("   the register's derived block is now the derivation's output")
    print("   %d terms" % len(terms))
    print("   the register now names the input it was derived from")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
