"""
deception_scan.py -- FIND THE DECEPTION TRADITION IN BOBBY'S OWN
CORPUS.

Bobby, 2026-10-26: *"scan desktop in teachings folder or psych or
wherever but sacred library argely in ur training data. we need to
build it. look in my writings for lists of texts and most important is
mafia, con artists, criminals, sufi masters, gypsies, fortune tellers,
scammer."*

So: the sacred library EXISTS as a corpus, and its gap is the
DECEPTION TRADITION. Bobby's own list (Teachings/SacredLibrary.md,
24 entries) has no mafia, no con artist, no criminal, no sufi master,
no gypsy, no fortune teller. And the current repo copy of the library
holds 772KB with 5 files carrying the deceiver's vocabulary.

THE POINT OF THE SCAN, and it is the same point as the gate:

  The people who wrote about deception KNEW what it sounded like.
  Their vocabulary is a detector. So the lexicon for reading intent
  should come from THEIR texts, not from my head.

AND SO THIS FILE DOES THE MEASUREMENT:

  A  THE INVENTORY. What is actually in Bobby's Desktop corpus? The
     folders: Teachings, psychology, Spiritual-Texts, and the
     reading lists. Measured by walking the disk, not by guessing.

  B  THE DECEPTION SEARCH. For each of Bobby's named categories --
     mafia, con artist, criminal, sufi master, gypsy, fortune teller,
     scammer -- how many texts carry that vocabulary? And WHERE.

  C  THE GAP. The list Bobby named, against what exists. Measured, so
     the gap is a number and not an impression.

  D  THE NOISE. Bobby's own phrase: *"just too much noise"*. So: for
     each candidate lexicon term, what share of the corpus carries it?
     A term in 40% of the texts is vocabulary; a term in 2% is signal.

Run:
    python src/deception_scan.py
"""

from __future__ import annotations

import os
import re
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

DESKTOP = "C:/Users/HP/Desktop"

#: The folders Bobby named, plus the ones the project already knows
#: about. Read-only.
FOLDERS = (
    "Teachings",
    "Teachings/Spiritual-Texts",
    "psychology",
    "books",
    "AI-agents",
    "English",
)

#: The extensions that carry text. PDFs are counted separately -- they
#: are real and they are the bulk, but they are not searchable here.
TEXT_EXT = (".txt", ".md", ".php", ".html", ".htm", ".json", ".csv")
BIN_EXT = (".pdf", ".doc", ".docx", ".jpg", ".jpeg", ".png", ".zip")

# ===========================================================================
# BOBBY'S NAMED CATEGORIES
# ===========================================================================
#
# Each category gets the vocabulary that the TRADITION used for it.
# Not my synonyms -- the words the sources themselves use. And the
# markers are chosen so a text ABOUT the category scores, and a text
# that merely mentions the word once does not.

CATEGORIES: Dict[str, Tuple[str, ...]] = {
    "mafia": (
        "mafia", "mafioso", "mafia boss", "capo", "consigliere",
        "omertà", "omerta", "la cosa nostra", "sicilian mafia",
        "cosa nostra", "the family", "made man", "the outfit",
        "godfather", "padrino", "dons", "don ", "the commission",
        "racket", "protection racket", "extortion", "the mob",
        "mafioso", "palermo", "corsica", "camorra", "ndrangheta",
        "'ndrangheta", "yakuza", "triad", "cartel", "narco",
    ),
    "con_artists": (
        "confidence man", "confidence trick", "con man", "conman",
        "con artist", "conartist", "grifter", "swindler", "charlatan",
        "hustler", "hustle", "the mark", "mug", "ringer", "the setup",
        "the sting", "sting", "rookie", "the bird", "short con",
        "long con", "big con", "boob", "the burn",
    ),
    "criminals": (
        "criminal", "criminal mind", "the underworld", "underworld",
        "thief", "thieving", "the fence", "fence", "burglar", "robber",
        "pickpocket", "hooligan", "black market", "the vice",
        "vice lords", "vice lord", "drug lord", "dealer", "smuggler",
        "piracy", "extortionist", "racketeer",
    ),
    "sufi_masters": (
        "sufi", "sufism", "sufi master", "shaykh", "sheikh", "dervish",
        "whirling dervish", "mawlana", "mullah", "saint", "saint of",
        "the greatest saint", "hidden saint", "saint of the age",
        "khoja", "the perfect master", "the master of the path",
        "charlatan of the east", "imam khomeini", "the ba'al shuq",
        "the poles", "awliya", "awliya", "the qutb",
    ),
    "gypsies": (
        "gypsy", "gypsies", "roma", "romani", "the travelling people",
        "travelling people", "the road people", "fortune teller",
        "fortune teller", "palm reader", "palmistry", "tarot",
        "tarot card", "cards", "the reading", "crystal ball",
        "psychic", "psychic reading", "tea leaves", "rider waite",
        "the wanderer", "itinerant",
    ),
    "scammers": (
        "scam", "scammer", "scamming", "swindle", "defraud",
        "defrauder", "fraud", "fraudster", "phishing", "advance fee",
        "nigerian prince", "pyramid scheme", "pyramid", "get rich quick",
        "multi-level marketing", "ponzi", "ponzi scheme", "m pyramid",
        "romance scam", "catfish", "catfishing", "phishing",
    ),
    "con_sophists": (
        "sophistry", "sophist", "rhetoric", "dialectic", "persuasion",
        "the art of persuasion", "influence", "propaganda", "manufacturing",
        "consent", "manufacture of consent", "the manufacture of consent",
        "the illusion of", "illusion of choice", "manufactured need",
        "nudge", "sludge", "dark pattern", "the foot in the door",
        "ball in the box", "the decoy", "anchoring", "motte and bailey",
    ),
    "occult_deception": (
        "charm", "spells", "curse", "hex", "bewitch", "enchant",
        "illusion", "magic", "magician", "sleight", "illusionist",
        "grimoire", "talisman", "amulet", "the trick", "trickster",
        "the serpent", "the snake", "jinn", "djinn", "the ghul",
        "ghoul", "the jinn", "ifrit", "the angel of death",
    ),
}

#: The TRUTH markers -- the vocabulary of a text that is honest about
#: its own authority. A text that claims to teach but cannot back it
#: up is the same failure as a span that asserts a claim with no
#: measurement.
TRUTH_MARKERS = (
    "evidence", "measured", "measurement", "observed", "observation",
    "the test", "tested", "reproduce", "reproducible", "falsifiable",
    "falsify", "the limitation", "limitations", "counterexample",
    "counter-example", "refutation", "the critic", "critique",
    "self-critique", "what this does not claim", "does not claim",
    "uncertain", "uncertainty", "doubt", "skeptic", "skeptical",
    "dissent", "error", "errors", "mistake", "mistakes", "confession",
    "the practice", "practised", "lineage", "transmission", "received",
    "attested", "witness", "testimony", "the record",
)


# ===========================================================================
# THE INVENTORY
# ===========================================================================

def inventory() -> Dict[str, object]:
    """What is actually in Bobby's Desktop corpus? Measured by walking."""
    per_folder = {}
    all_text: List[Tuple[str, str]] = []   # (path, text)
    for folder in FOLDERS:
        root = os.path.join(DESKTOP, folder)
        if not os.path.isdir(root):
            continue
        n_text = 0
        n_bin = 0
        total_bytes = 0
        for r, _d, names in os.walk(root):
            for n in names:
                p = os.path.join(r, n)
                ext = os.path.splitext(n)[1].lower()
                try:
                    size = os.path.getsize(p)
                except OSError:
                    continue
                total_bytes += size
                if ext in TEXT_EXT:
                    n_text += 1
                    try:
                        txt = open(p, encoding="utf-8",
                                   errors="replace").read()
                    except OSError:
                        continue
                    all_text.append((p, txt))
                elif ext in BIN_EXT:
                    n_bin += 1
        per_folder[folder] = {"text": n_text, "binary": n_bin,
                               "bytes": total_bytes}
    return {"per_folder": per_folder, "texts": all_text}


# ===========================================================================
# THE CATEGORIES, MEASURED
# ===========================================================================

def measure_categories(texts: List[Tuple[str, str]]) -> Dict[str, object]:
    """How many texts carry each of Bobby's named categories?"""
    out = {}
    for name, markers in CATEGORIES.items():
        hits = []
        term_counts = Counter()
        for path, text in texts:
            low = text.lower()
            found = [m for m in markers if m in low]
            if found:
                hits.append((path, len(found)))
                for f in found:
                    term_counts[f] += 1
        out[name] = {
            "docs": len(hits),
            "total_docs": len(texts),
            "rate": (len(hits) / len(texts)) if texts else 0.0,
            "terms": term_counts,
            "top_paths": [p for p, _c in
                          sorted(hits, key=lambda x: -x[1])[:6]],
        }
    return out


# ===========================================================================
# THE NOISE
# ===========================================================================

def measure_noise(texts: List[Tuple[str, str]]) -> Dict[str, object]:
    """Bobby's phrase: "just too much noise".

    So: what share of the corpus carries each term? A term in most
    texts is vocabulary. A term in a few is signal.

    AND THE THRESHOLD IS A PARAMETER, because "noise" depends on what
    you are using the lexicon for.
    """
    n = len(texts)
    lows = [(p, t.lower()) for p, t in texts]
    term_docs = Counter()
    for _p, low in lows:
        seen = set()
        for markers in CATEGORIES.values():
            for m in markers:
                if m in low and m not in seen:
                    seen.add(m)
                    term_docs[m] += 1
    return {"total": n, "term_docs": term_docs}


def main() -> int:
    print("=" * 78)
    print("THE DECEPTION TRADITION IN BOBBY'S CORPUS")
    print("=" * 78)
    print()

    inv = inventory()
    print("A. THE INVENTORY -- what is actually on the disk")
    print("   %-28s %-8s %-8s %s" % ("folder", "text", "binary", "bytes"))
    for folder, s in inv["per_folder"].items():
        print("   %-28s %-8d %-8d %d" % (folder, s["text"], s["binary"],
                                          s["bytes"]))
    texts = inv["texts"]
    print("   %d text files, %d bytes total, searchable"
          % (len(texts), sum(len(t) for _p, t in texts)))
    print()

    if not texts:
        print("   NOTHING SEARCHABLE -- the scan cannot run.")
        return 2

    cats = measure_categories(texts)
    print("B. BOBBY'S NAMED CATEGORIES, and what exists")
    print("   %-20s %-12s %s" % ("category", "docs", "share of corpus"))
    for name in sorted(cats, key=lambda k: -cats[k]["docs"]):
        c = cats[name]
        print("   %-20s %-12d %.1f%%" % (name, c["docs"],
                                         c["rate"] * 100))
    print()
    for name in sorted(cats, key=lambda k: -cats[k]["docs"]):
        c = cats[name]
        if not c["docs"]:
            print("   %s -- NO TEXT CARRIES IT" % name)
            continue
        top = ", ".join(os.path.basename(p) for p in c["top_paths"][:4])
        print("   %s: %s" % (name, top))
    print()

    noise = measure_noise(texts)
    total = noise["total"]
    print("C. THE NOISE -- what share of the corpus carries each term")
    print("   the corpus here is %d text files" % total)
    print("   %-28s %-10s %s" % ("term", "docs", "share"))
    for term, n in noise["term_docs"].most_common(24):
        print("   %-28s %-10d %.1f%%" % (term, n, n / total * 100))
    print()
    sharp = [(t, n) for t, n in noise["term_docs"].items()
             if n / total <= 0.10]
    noisy = [(t, n) for t, n in noise["term_docs"].items()
             if n / total > 0.10]
    print("   SHARP terms (in <=10%% of the corpus)  %d" % len(sharp))
    print("   NOISY terms (in >10%% of the corpus)   %d" % len(noisy))
    print()
    print("   the sharp ones, which are the ones a lexicon should keep:")
    for t, n in sorted(sharp, key=lambda x: x[1])[:20]:
        print("     %-28s %d docs  %.1f%%" % (t, n, n / total * 100))
    print()

    print("=" * 78)
    print("  Run: python src/deception_scan.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
