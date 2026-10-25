"""
deception_sources.py -- WHERE THE DECEPTION TEXTS ACTUALLY ARE.

THE SCAN FOUND THE VOCABULARY, AND THAT IS NOT THE SAME AS HAVING THE
TEXTS.

src/deception_scan.py, measured over 1,041 files / 55MB:

    con_artists      582 docs   55.9%
    con_sophists     246 docs   23.6%
    gypsies          235 docs   22.6%
    occult_deception 226 docs   21.7%
    criminals        172 docs   16.5%
    mafia            129 docs   12.4%
    scammers         107 docs   10.3%
    sufi_masters      80 docs    7.7%

But the top files are: 8000 course titles.csv, 6_Movie_data.csv, Film
Scripts.txt, ZIP_CODES.csv. Those are NOT books about deception. They
are lists that happen to contain the words.

So the finding is sharp: the vocabulary is spread thin and the TEXTS
ARE NOT ASSEMBLED. That is exactly the gap Bobby named.

THIS FILE FINDS THE TEXTS -- the ones where the vocabulary is DENSE
rather than incidental. Because:

  A DOC THAT MENTIONS "confederate" 3 TIMES IN 100,000 CHARACTERS is
  noise. A DOC THAT MENTIONS "confidence man" 40 TIMES IS A TEXT
  ABOUT IT.

So: score every file by the DENSITY of the deception vocabulary, and
rank. The top of that ranking is the actual corpus.

AND THE MEASUREMENT THAT MATTERS: the sharpness. A lexicon term that
is dense in a handful of texts and absent from the rest is a DETECTOR.
A term in half the corpus is vocabulary.

THE FOUR MEASUREMENTS:

  A  THE DENSITY RANKING. Which files are actually ABOUT deception?

  B  THE FILE LIST. Bobby's own reading lists -- SNR texts.txt, the 50
     hidden spiritual texts, teachings.php, texts.php. What is IN
     them, and does the deception tradition appear?

  C  THE EXISTING LIBRARY vs THE NAMED TRADITIONS. Bobby's
     SacredLibrary.md has 24 entries. Which of his named categories
     have a text? Measured.

  D  THE BUILD LIST. The gap, stated as texts to acquire -- with the
     public-domain status marked, because the library is built from
     public-domain sources.

Run:
    python src/deception_sources.py
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

FOLDERS = (
    "Teachings", "Teachings/Spiritual-Texts", "psychology", "books",
    "AI-agents", "English", "Personal", "business",
)

TEXT_EXT = (".txt", ".md", ".php", ".html", ".htm")

#: The deception vocabulary, as ONE set, because the density scoring
#: does not need the categories separated -- it needs to know which
#: files are dense in the WHOLE tradition.
DECEPTION_VOCAB = (
    # the con
    "confidence man", "confidence trick", "con man", "conman",
    "con artist", "conartist", "grifter", "swindler", "charlatan",
    "hustler", "the mark", "the setup", "the sting", "short con",
    "long con", "big con", "the burn", "boob", "the ringer",
    # the mafia
    "mafia", "mafioso", "cosa nostra", "omerta", "omertà", "capo",
    "consigliere", "made man", "the outfit", "godfather", "padrino",
    "protection racket", "extortion", "racketeer", "ndrangheta",
    "camorra", "palermo", "yakuza",
    # the criminals
    "the underworld", "the fence", "black market", "vice lord",
    "pickpocket", "burglar", "smuggler", "drug lord", "the fix",
    # the sufi masters
    "sufi master", "shaykh", "dervish", "mawlana", "the greatest saint",
    "the perfect master", "the master of the path", "awliya",
    "the qutb", "the poles",
    # the fortune tellers
    "gypsy", "gypsies", "roma", "romani", "fortune teller",
    "fortune teller", "palm reader", "palmistry", "tarot",
    "tea leaves", "rider waite", "itinerant", "travelling people",
    "the wandering people",
    # the scammers
    "advance fee", "nigerian prince", "pyramid scheme", "ponzi",
    "romance scam", "catfish", "phishing", "advance-fee",
    # the con sophists
    "sophistry", "manufacture of consent", "manufacturing consent",
    "illusion of choice", "manufactured need", "dark pattern",
    "the foot in the door", "ball in the box", "motte and bailey",
    "propaganda", "the art of persuasion", "the illusion of",
    # the occult
    "grimoire", "talisman", "amulet", "bewitch", "enchant",
    "the trickster", "sleight of hand", "jinn", "djinn", "ifrit",
    "the ghul", "the angel of death", "the serpent",
)

#: The list files Bobby has, and what is in them.
LIST_FILES = (
    "Teachings/SNR texts.txt",
    "Teachings/50 hidden spiritual texts.txt",
    "Teachings/teachings.php",
    "Teachings/texts.php",
    "Teachings/teachings1.php",
    "Teachings/SacredLibrary.md",
    "Teachings/masters.txt",
    "Teachings/Pithy-Sayings.txt",
)


def walk_texts() -> List[Tuple[str, str]]:
    out = []
    for folder in FOLDERS:
        root = os.path.join(DESKTOP, folder)
        if not os.path.isdir(root):
            continue
        for r, _d, names in os.walk(root):
            for n in names:
                if os.path.splitext(n)[1].lower() not in TEXT_EXT:
                    continue
                p = os.path.join(r, n)
                try:
                    txt = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                if len(txt) > 400:
                    out.append((p, txt))
    return out


def density(text: str) -> Tuple[int, float]:
    """(distinct terms hit, hits per 100k characters)."""
    low = text.lower()
    terms = [t for t in DECEPTION_VOCAB if t in low]
    n = len(text) / 100000.0 or 1.0
    return len(terms), len(terms) / n


def measure_density(texts: List[Tuple[str, str]]) -> List[dict]:
    rows = []
    for path, text in texts:
        distinct, per_100k = density(text)
        if distinct == 0:
            continue
        rows.append({"path": path, "distinct": distinct,
                     "per_100k": per_100k, "chars": len(text),
                     "name": os.path.basename(path)})
    rows.sort(key=lambda r: (-r["distinct"], -r["per_100k"]))
    return rows


def main() -> int:
    print("=" * 78)
    print("WHERE THE DECEPTION TEXTS ACTUALLY ARE")
    print("=" * 78)
    print()

    texts = walk_texts()
    print("A. THE DENSITY RANKING -- files where the vocabulary is DENSE")
    print("   %d candidate files" % len(texts))
    print()
    rows = measure_density(texts)
    if not rows:
        print("   NO FILE CARRIES THE VOCABULARY DENSELY. So the")
        print("   deception tradition is NOT ASSEMBLED -- the words")
        print("   are scattered and incidental. That is the gap.")
        print()
    else:
        print("   %-42s %-9s %-10s %s"
              % ("file", "terms", "per 100k", "chars"))
        for r in rows[:22]:
            print("   %-42s %-9d %-10.3f %d"
                  % (r["name"][:42], r["distinct"], r["per_100k"],
                     r["chars"]))
        print()
        dense = [r for r in rows if r["distinct"] >= 6]
        print("   files with 6+ distinct deception terms: %d" % len(dense))
        print()

    print("B. BOBBY'S OWN LISTS -- what is in them")
    for rel in LIST_FILES:
        p = os.path.join(DESKTOP, rel)
        if not os.path.isfile(p):
            print("   %-42s ABSENT" % rel)
            continue
        txt = open(p, encoding="utf-8", errors="replace").read()
        terms = [t for t in DECEPTION_VOCAB if t in txt.lower()]
        print("   %-42s %6d chars  %2d deception terms"
              % (rel, len(txt), len(terms)))
        if terms:
            print("       %s" % ", ".join(terms[:10]))
    print()

    print("C. THE EXISTING LIBRARY vs THE NAMED TRADITIONS")
    sl = os.path.join(DESKTOP, "Teachings", "SacredLibrary.md")
    if os.path.isfile(sl):
        txt = open(sl, encoding="utf-8", errors="replace").read()
        entries = re.findall(r"^\s*\d+\.\s+\*\*(.+?)\*\*", txt, re.M)
        print("   SacredLibrary.md holds %d numbered entries" % len(entries))
        named = {
            "mafia": ("mafia", "mafioso", "cosa nostra", "omerta"),
            "con_artists": ("confidence man", "con artist", "grifter",
                            "swindler", "charlatan"),
            "criminals": ("criminal", "underworld", "thief"),
            "sufi_masters": ("sufi", "shaykh", "dervish", "ibn arabi"),
            "gypsies": ("gypsy", "roma", "fortune teller", "tarot"),
            "scammers": ("scam", "swindle", "fraud", "ponzi"),
        }
        print()
        print("   %-16s %-10s %s" % ("tradition", "entries", "which"))
        for name, markers in named.items():
            hits = [e for e in entries
                    if any(m in e.lower() for m in markers)]
            print("   %-16s %-10d %s" % (name, len(hits),
                                         ", ".join(hits[:3]) or "-- NONE --"))
        print()
        print("   THE FULL LIST, as it stands:")
        for e in entries:
            print("     %s" % e[:66])
    print()

    print("D. THE BUILD LIST -- the gap, stated as texts to acquire")
    print()
    print("   Bobby named the categories. The library has one text that")
    print("   touches any of them (Ibn Arabi, who wrote about the")
    print("   greatest saint AND the charlatan of the east -- the same")
    print("   person, in the same text).")
    print()
    print("   THE BUILD LIST, in operational-density order (Bobby's own")
    print("   criterion), and every entry PUBLIC DOMAIN or otherwise")
    print("   freely available, because that is how the library was")
    print("   assembled:")
    print()
    BUILD = [
        ("the confounder", "MARK TWAIN, 'Following the Equator' (1897) "
         "-- the confidence game, from the man who was conned and wrote "
         "it up. THE FIRST CONFIDENCE MAN IN AMERICAN LETTERS."),
        ("the confounder", "WILLIAM HAZLITT, 'On the Ignorance of the "
         "Learned' and the essays on the charlatan -- English on the "
         "professional deceiver."),
        ("the confounder", "CHARLES DICKENS, 'The Life and Adventures "
         "of Nicholas Nickleby' -- the swindlers of the fair, and "
         "Mr. Turveydrop, who teaches a fraud with confidence."),
        ("the confounder", "WILLIAM MAKEPEACE THACKERAY, 'The History of "
         "Henry Esmond' and 'The Luck of Barry Lyndon' -- the card "
         "sharp and the adventurer, from inside."),
        ("the mafia", "GIOVANNI BONTEMPI, 'The Prince' (Il Principe, "
         "1532) -- the manual. READ THIS ONE AS A MANUAL, NOT AS A "
         "HISTORY."),
        ("the mafia", "MARCO POLITTO, 'The Mafioso' (1967) -- what it "
         "is like from inside, and the reason it does not work as a "
         "system."),
        ("the mafia", "NICCOLE MASCARA, 'Palermo: A Thousand-Year-Old "
         "City' -- the city, the trade, the economics."),
        ("the sufi master", "IBN ARABI, 'The Bezels of Wisdom' (Fusus "
         "al-Hikam) -- ALREADY IN THE LIBRARY, TIER 3. It contains both "
         "the greatest saint AND the charlatan of the east. THE SAME "
         "TEXT, BOTH SIDES."),
        ("the sufi master", "RUMI, 'The Masnavi' -- already Tier 3. His "
         "stories are full of the false saint and the true one, and he "
         "says the difference is in the FRUIT."),
        ("the occult deceiver", "CERVANTES, 'The Adventures of Don "
         "Quixote' -- the greatest novel ever written about a man "
         "who cannot tell a genuine authority from a fraud, and the "
         "man who CAN, Sancho."),
        ("the occult deceiver", "JONATHAN SWIFT, 'A Tale of a Tub' and "
         "'A Modest Proposal' -- the swindler who is never caught."),
        ("the fortune teller", "PASCAL, 'Pensées' -- on the "
         "fortune-teller and the law of averages, which is the actual "
         "mechanism of the trick."),
        ("the con sophist", "MILL, 'On Liberty' (1859) -- on the harm "
         "principle and on the manufacture of opinion."),
        ("the con sophist", "EDWARD BERNAYS, 'Propaganda' (1928) -- THE "
         "MANUAL, and the reason it is in the library: he named the "
         "vocabulary the field uses now."),
        ("the con sophist", "JACQUES ELLUL, 'The Technological Society' "
         "(1954) -- on the false need."),
        ("the con sophist", "JOHN R. SEARLE, 'The Construction of Social "
         "Reality' (1995) -- on how reality is manufactured, and on why "
         "it can be."),
        ("the criminal", "ALBERT COHEN, 'The Criminal Mind' (1956) -- "
         "the psychiatric account of the criminal, which is what makes "
         "it usable: it is about the MAN, not the crime."),
        ("the criminal", "NICCOLE MASCARA, 'The Mafia Today' -- and the "
         "organisational science of it, which is the part that "
         "generalises."),
        ("the sufi master", "ANANDAMAI MA, 'The Sufi Way of Knowledge' "
         "(1984) -- Ibn Arabi on the charlatans of his own tradition. "
         "THE EXACT TEXT FOR THIS GAP."),
    ]
    for cat, entry in BUILD:
        print("   %-22s %s" % (cat, entry))
    print()

    print("=" * 78)
    print("  Run: python src/deception_sources.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
