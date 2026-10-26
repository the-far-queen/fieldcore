"""
library_verify.py -- VERIFY THE ACQUIRED TEXTS, AND MEASURE THE NOISE.

BOBBY'S FLAG, and it is the one measurement that makes the lexicon
honest:

    *"the sacred library -- you have the best of human wisdom to use,
    right in your training data, just too much noise."*

SO THE NOISE IS THE MEASUREMENT, and it has two parts:

  1. DOES THE LEXICON FIRE ON THE TEXTS THAT ARE ABOUT DECEPTION?
     That is the SIGNAL. A term that appears in 40% of the deception
     corpus is not a discriminator; it is the vocabulary of English.

  2. DOES THE LEXICON FIRE ON THE REST OF THE CORPUS?
     That is the NOISE. A term that appears in the project's own
     documents at a higher rate than in the deception corpus is
     worthless -- it is just a common word.

  AND THE DISCRIMINATOR IS THE DIFFERENCE: a term is signal when it
  is MUCH more common in the deception corpus than in the rest. That
  ratio is the number to keep, and it is the number that says whether
  the lexicon can be trusted at all.

THE OTHER MEASUREMENT, and it is the one the library exists for: does
the acquired corpus actually FIRE the gate's own vocabulary? Because
if the library's texts do not contain the vocabulary of the lies the
gate catches, then the library is decorative.

Run:
    python src/library_verify.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import claim_register as CR  # noqa: E402

TEXTS = os.path.join(WORK_REPOS, "sacred-library", "corpus", "deception",
                     "texts")
MANIFEST = os.path.join(TEXTS, "ACQUIRED.json")

#: THE CORPUS OUTSIDE THE DECEPTION TEXTS -- and this is the NOISE
#: baseline. The project's own documents, which are ordinary technical
#: writing.
NOISE_ROOTS = [
    os.path.join(WORK_REPOS, "fieldcore", "docs"),
    os.path.join(WORK_REPOS, "simself", "docs"),
    os.path.join(WORK_REPOS, "fieldcore", "src"),
]


def load_texts() -> List[Tuple[str, str]]:
    out = []
    if not os.path.isdir(TEXTS):
        return out
    for n in sorted(os.listdir(TEXTS)):
        if not n.endswith(".txt"):
            continue
        p = os.path.join(TEXTS, n)
        try:
            out.append((n, open(p, encoding="utf-8", errors="replace").read()))
        except OSError:
            continue
    return out


def load_noise() -> List[Tuple[str, str]]:
    out = []
    for root in NOISE_ROOTS:
        if not os.path.isdir(root):
            continue
        for r, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git")]
            for n in names:
                if not n.endswith((".md", ".py", ".txt")):
                    continue
                p = os.path.join(r, n)
                try:
                    out.append((n, open(p, encoding="utf-8",
                                         errors="replace").read()))
                except OSError:
                    continue
    return out


def main() -> int:
    print("=" * 78)
    print("THE LIBRARY, VERIFIED, AND THE NOISE MEASURED")
    print("=" * 78)
    print()

    texts = load_texts()
    if not texts:
        print("   NO TEXTS ON DISK at %s" % TEXTS)
        return 2

    print("A. THE ACQUIRED TEXTS")
    print()
    print("   %-42s %-10s %s" % ("file", "bytes", "real?"))
    total = 0
    suspect = 0
    for name, text in texts:
        b = len(text)
        total += b
        # a real book: substantial, and not a 404 page
        real = b > 20000 and "404" not in text[:2000].lower() \
            and "not found" not in text[:400].lower()
        if not real:
            suspect += 1
        print("   %-42s %-10d %s" % (name[:42], b, "yes" if real else "SUSPECT"))
    print()
    print("   %d files, %d bytes total, %d suspect"
          % (len(texts), total, suspect))
    print()

    if os.path.isfile(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as f:
            man = json.load(f)
        print("   the manifest: %d entries" % len(man))
        by_trad = Counter(e.get("tradition", "?") for e in man)
        for t, n in by_trad.most_common():
            print("      %-22s %d" % (t, n))
        print()

    # -- the noise measurement ----------------------------------------
    print("B. THE NOISE -- and the number that matters is the RATIO")
    print()
    noise = load_noise()
    print("   the noise baseline: %d project documents" % len(noise))
    print()

    reg = CR.standard_register()
    lexicon = sorted({t for c in reg.claims for t in c.deny}
                     | {t for c in reg.claims for t in c.affirm})
    lexicon = [t for t in lexicon if len(t) > 4][:60]

    dec_text = "\n".join(t.lower() for _n, t in texts)
    noise_text = "\n".join(t.lower() for _n, t in noise)

    rows = []
    for term in lexicon:
        d_hits = dec_text.count(term)
        n_hits = noise_text.count(term)
        d_rate = d_hits / max(1, len(texts))
        n_rate = n_hits / max(1, len(noise))
        ratio = (d_rate / n_rate) if n_rate > 0 else float("inf")
        rows.append((term, d_hits, n_hits, ratio))

    rows.sort(key=lambda r: -r[3])
    print("   %-30s %-9s %-9s %s" % ("term", "in dec", "in noise", "ratio"))
    for term, d, n, ratio in rows[:22]:
        r = "%.1fx" % ratio if ratio != float("inf") else "inf"
        print("   %-30s %-9d %-9d %s" % (term[:30], d, n, r))
    print()
    finite = [r for r in rows if r[3] != float("inf")]
    above = sum(1 for r in finite if r[3] >= 2.0)
    print("   terms MORE than twice as common in the deception corpus")
    print("   as in the project's own writing: %d of %d"
          % (above, len(finite)))
    print()
    print("   AND THAT RATIO IS THE ANSWER TO BOBBY'S FLAG. A term")
    print("   with a HIGH ratio is a discriminator -- it means the")
    print("   deception tradition, and not ordinary technical")
    print("   writing. A term with a LOW ratio is just English, and")
    print("   putting it in a lexicon would add NOISE.")
    print()

    # -- does the library fire the gate's vocabulary? ------------------
    print("C. DOES THE LIBRARY CONTAIN THE GATE'S OWN VOCABULARY?")
    print()
    hits = 0
    for name, text in texts:
        low = text.lower()
        fired = [t for t in lexicon if t in low]
        if fired:
            hits += 1
        print("   %-42s %d terms" % (name[:42], len(fired)))
    print()
    print("   %d of %d texts contain the gate's vocabulary." % (hits, len(texts)))
    print()
    print("   AND THIS IS THE TEST OF WHETHER THE LIBRARY IS")
    print("   DECORATIVE. A library that does not contain the words")
    print("   the gate needs is a shelf. One that does is a")
    print("   DETECTOR that can be shown to work.")
    print()

    # -- D: the library-sourced lexicon ------------------------------
    print("D. WHAT A LIBRARY-SOURCED LEXICON WOULD KEEP")
    print()
    print("   THE POINT. The library gives every term a RATIO, so a")
    print("   lexicon built from it can say which words DISCRIMINATE")
    print("   and which are NOISE -- and the noise can be DROPPED")
    print("   instead of carried.")
    print()
    keep = [(t, r) for t, _d, _n, r in rows if r >= 2.0]
    drop = [(t, r) for t, _d, _n, r in rows if r < 2.0]
    print("   KEEP (ratio >= 2x): %d terms" % len(keep))
    for t, r in keep[:14]:
        print("      %-28s %.1fx" % (t[:28], r))
    print()
    print("   DROP (ratio < 2x)  : %d terms" % len(drop))
    for t, r in drop[:10]:
        print("      %-28s %.1fx" % (t[:28], r))
    print()
    print("   AND THE TERMS THAT SURVIVE ARE THE INTERESTING ONES:")
    print("   they are the words the DECEPTION TRADITION uses, which")
    print("   means a lexicon built from the library is a lexicon of")
    print("   the TRADITION rather than a list of words somebody")
    print("   thought of.")
    print()

    print("=" * 78)
    print("  Run: python src/library_verify.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
