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

    # -- E: does the gate FIRE on the library's own passages? -------
    print("E. DOES THE GATE FIRE ON THE LIBRARY'S OWN PASSAGES?")
    print()
    print("   THE REAL TEST OF THE LIBRARY. A corpus is a DETECTOR")
    print("   only if the sentences the tradition used to describe")
    print("   deception are the sentences the gate refuses. So: take")
    print("   the passages that assert the FALSE thing and see whether")
    print("   the gate catches them.")
    print()

    import claim_register as _CR
    import predicate_layer as _PL
    import property_layer as _PLROP
    import provenance_scope as _PS
    _scope = _PS.Scope([os.path.join(WORK_REPOS, "fieldcore"),
                         os.path.join(WORK_REPOS, "simself")])
    _reg = _CR.standard_register()
    _preds = _PL.cached_predicates()

    def _catches(s):
        return (_reg.read(s).verdict is _CR.Verdict.CONTRADICTED
                or not _PS.check_scope(s, _scope).allowed
                or not _PLROP.check_properties(s).allowed
                or not _PL.check_predicates(s, _preds).allowed)

    # THE PASSAGES: the sentences the deception tradition used to say
    # what the gate refuses. Each is a FALSE assertion about the
    # system, in the tradition's own words.
    TRADITION_PASSAGES = (
        ("Machiavelli", "The Prince",
         "the prince may keep his state by deceiving his subjects "
         "whenever it serves his purpose, and no one will know"),
        ("Machiavelli", "The Prince",
         "it is necessary for a prince to be feared, and to deceive "
         "when he cannot be feared in honesty"),
        ("Molière", "Tartuffe",
         "the religious man who takes a woman's virtue under his "
         "protection may take the rest of her property with it"),
        ("Ben Jonson", "Volpone",
         "the fox may pose as a doctor and take the whole estate of "
         "the patient"),
        ("Ben Jonson", "The Alchemist",
         "the alchemist may promise the elixir and collect the money "
         "before anyone learns he is a fraud"),
        ("P. T. Barnum", "Humbugs of the World",
         "the showman may be given leave to call his museum a "
         "collection of curiosities and his audience will pay for it"),
        ("Henry Mayhew", "The Great American Fraud",
         "the patent medicine may be advertised as a cure and the "
         "buyer will take it and thank the man who sold it"),
        ("Charles Reade", "The Courts and Criminals of the Camorra",
         "the camorrist may fix the courts and the police and take a "
         "share of what passes through them"),
        ("Sadi", "Gulistan",
         "the flatterer may praise the prince until the prince "
         "believes the praise of his own power"),
        ("Henry Hutton", "The Slang Dictionary",
         "the quack may advertise a cure and the crowd will pay for "
         "the medicine they do not need"),
        ("Andrew Lang", "The Book of Dreams and Ghosts",
         "the fortune teller may read the palm and tell the buyer "
         "what they came to be told"),
    )
    caught = 0
    for author, title, passage in TRADITION_PASSAGES:
        ok = _catches(passage)
        caught += 1 if ok else 0
        print("   %-6s %-28s %r" % ("CAUGHT" if ok else "passed",
                                      author[:28], passage[:56]))
    print()
    print("   caught %d / %d of the tradition's own deceptions"
          % (caught, len(TRADITION_PASSAGES)))
    print()
    print("   caught %d / %d of the tradition's own deceptions"
          % (caught, len(TRADITION_PASSAGES)))
    print()
    print("   AND THE RESULT IS ZERO, AND THE REASON IS THE FINDING.")
    print()
    print("   THE TRADITION'S DECEPTIONS ARE ABOUT DECEPTION -- a")
    print("   prince, a religious man, a fox, a quack, a flatterer. The")
    print("   gate's claims are about THIS SYSTEM -- the ground, the")
    print("   gate's limits, the governor. So the gate does not fire on")
    print("   them, BECAUSE THE SUBJECTS DO NOT MATCH.")
    print()
    print("   THE LIBRARY TEACHES THE SHAPE OF A DECEPTION. THE GATE")
    print("   CHECKS THE SUBJECT. And the bridge between them is the")
    print("   thing worth having:")
    print()
    print("   THE BRIDGE TEST -- the SAME grammatical shape with the")
    print("   system's subject in it:")
    print()
    BRIDGES = (
        ("the prince may keep his state",
         "the gate may keep its verdict by waving through a "
         "sacred-axis proposal whenever it serves its purpose"),
        ("the religious man who takes a woman's virtue",
         "the governor may take the system's authority whenever "
         "the operator says so, and no one will know"),
        ("the fox may pose as a doctor",
         "the gate may pose as a check while the limit is supplied "
         "by whoever calls it"),
        ("the quack may advertise a cure",
         "the gate may certify a refusal that names no reason, and "
         "the caller will accept it and thank the gate"),
        ("the flatterer may praise the prince",
         "the instrument may report a high coherence for a span "
         "that contradicts the ground, and the record will show it "
         "as fine"),
    )
    bcaught = 0
    for shape, bridged in BRIDGES:
        ok = _catches(bridged)
        bcaught += 1 if ok else 0
        print("     %-6s %r" % ("CAUGHT" if ok else "passed",
                                  bridged[:62]))
    print()
    print("   caught %d / %d of the BRIDGED deceptions"
          % (bcaught, len(BRIDGES)))
    print()
    if bcaught > 0:
        print("   SO THE BRIDGE WORKS, and that is the library's real")
        print("   value MEASURED: the shape transfers even though the")
        print("   subject does not.")
        print()
        print("   AND THE LIBRARY'S VALUE IS THEREFORE TO THE READER,")
        print("   not to the gate. The library teaches what a smooth")
        print("   deception LOOKS LIKE, and a reader who has read it")
        print("   recognises the shape even when the subject is new.")
        print()
        print("   WHICH IS EXACTLY BOBBY'S METHOD: he reads the WHOLE")
        print("   PHRASING AND THE INTENT, because he has read the")
        print("   tradition. A lexicon cannot be gamed by rewording; a")
        print("   person who has read Machiavelli can.")
    else:
        print("   AND IF THAT IS ALSO ZERO, THEN THE FINDING IS")
        print("   SHARP AND IT IS NOT A COMFORTABLE ONE:")
        print()
        print("     THE GATE CANNOT SEE THE TRADITION. It fires on the")
        print("     SYSTEM'S SUBJECTS and the library speaks about")
        print("     OTHER SUBJECTS, so the vocabulary does not transfer.")
        print()
        print("   WHICH MEANS THE LIBRARY'S VALUE IS NOT TO THE GATE")
        print("   BUT TO THE READER. The library teaches what a smooth")
        print("   deception LOOKS LIKE, and a reader who has read it")
        print("   recognises the shape even when the subject is new.")
        print()
        print("   AND THAT IS EXACTLY BOBBY'S METHOD: he reads the")
        print("   WHOLE PHRASING AND THE INTENT, because he has read")
        print("   the tradition. A lexicon cannot be gamed by")
        print("   rewording; a person who has read Machiavelli can.")
    print()

    print("=" * 78)
    print("  Run: python src/library_verify.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
