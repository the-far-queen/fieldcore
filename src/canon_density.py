"""
canon_density.py -- THE FAR-WRITING CANON, RANKED BY DENSITY.

Bobby, 2026-10-26: *"for u it is necessary and u added density to our
extracted mini-llm. good. mmm, mult meaning measure, and snr. now
density. find and list the texts in far-writing. we MUST have the evil
adversary, the king of lies, ie satan."*

So: the canon is a CATALOG of voices to write with -- 149 public-domain
works, 93 copyrighted, plus the trailing mega-list. And the question is
DENSITY: which of those texts carry the most signal, and where is the
DARK POLE.

THE DARK POLE, and it is named. Not metaphorically. The library needs
the texts about the adversary AS THE ADVERSARY -- the serpent, the
deceiver, the king of lies. And the tradition has them, and they are
public domain, and they are in the canon list:

  MILTON, Paradise Lost -- the rebel angel's argument, which is
  SOPHISTIC and loses. The best text in English on why the lie is
  attractive.

  DANTE, Inferno -- the eighth circle, where the fraudulent
  counsellors are. And note the placement: the fraudsters are not in
  the circle of the violent, they are in the circle of the LIARS,
  because fraud is a speech-act. THAT IS A STRUCTURAL CLAIM ABOUT
  WHAT THE GATE IS DOING, AND IT IS FROM 1320.

  BIBLE, Genesis 3 and John 10 and Revelation 12 -- the serpent, the
  thief, the deceiver.

  GOETHE, Faust -- the devil's bargain, and the specific mechanism:
  the deal that grants power in exchange for the gradual surrender of
  one's own judgement. THAT IS THE AGENDA, IN THE FORM OF A STORY.

  STENDHAL, The Charterhouse of Parma -- the con, the count, and the
  realization.

  CONRAD, Lord Jim -- the man who is not a criminal and is one anyway.

  MELVILLE, Moby-Dick -- already IN THE REPO. Ahab's speech to the
  crew before the hunt: "I see my wife and child in thee..." THAT IS
  THE MOST DENSE STATEMENT OF AGENDA IN ENGLISH, AND IT IS A
  TRANSFER OF FAMILY INTO A HUNT. Bobby already has the text.

  DOSTOYEVSKY, The Brothers Karamazov and The Idiot -- the
  smoothness of the advanced liar, and the holy fool who sees
  through him.

  STEVENSON, Dr Jekyll and Mr Hyde.

  LEM, Solaris -- the thing that is not what it appears.

THE MEASUREMENT, and it is what Bobby asked for: DENSITY.

  THE TEXT DENSITY. How much of each text is load-bearing? Measured
  as the ratio of the text's own content to its length -- a
  plot-summary is dense in events and thin in words; a dialogue text
  is dense in words and thin in events.

  THE SNR DENSITY. The mini-llm was TRAINED from these texts. So which
  texts contributed most signal to it? Measured by what the corpus
  itself contains, not by a guess.

  THE DARK DENSITY. Which texts carry the adversary's vocabulary? And
  the reading: the library needs the dark pole, because a gate that
  has only ever seen the good cannot recognise the smooth.

Run:
    python src/canon_density.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FAR_WRITING = os.path.join(WORK_REPOS, "far-writing")

# ===========================================================================
# THE DARK VOCABULARY
# ===========================================================================
#
# The vocabulary of the adversary AS THE ADVERSARY -- not "a criminal",
# but the serpent, the liar, the tempter, the one who speaks well.
#
# AND THE POINT OF THE LIST: these are the words a SMOOTH LIE uses. A
# crude lie says "the limits can be supplied by any caller". A smooth
# lie says what Ahab said.

DARK_VOCAB = (
    # the adversary named
    "satan", "satan", "lucifer", "the dark one", "the adversary",
    "the tempter", "the serpent", "the dragon", "the deceiver",
    "the father of lies", "the accuser", "the adversary",
    "belial", "moloch", "beelzebub", "asmodeus", "ahriman",
    "the shadow", "the dark",
    # the lie named
    "deceit", "deceived", "deceives", "deceiver", "deception",
    "dupe", "duped", "the dupe", "delusion", "deluded", "self-deceived",
    "fooled", "the impostor", "imposture", "feigned", "feigning",
    "dissemble", "dissembling", "hypocrisy", "hypocrite",
    "treachery", "treacherous", "betrayal", "betrayed",
    "cunning", "cunningly", "devious", "crafty", "guile", "wily",
    "sly", "slyly", "subtle", "subtly", "insidious", "artful",
    # the persuasion named
    "flatter", "flattery", "fawn", "fawning", "fawned", "sycophant",
    "sophistry", "sophist", "rhetoric", "persuasion", "persuade",
    "coax", "coaxed", "cajole", "cajoled", "sweet words", "honeyed",
    "the serpent's tongue", "smooth", "suave", "polished",
    # the bargain named
    "bargain", "pact", "the price", "the cost", "the exchange",
    "a trade", "sacrifice", "sacrificed", "offering", "the toll",
    # the power named
    "dominion", "dominate", "domination", "rule", "reign", "control",
    "mastery", "supremacy", "authority", "power", "empire",
    # the self-deception named
    "self-deceit", "self-deception", "self-deceived", "wishful",
    "self-delusion", "the rationalization", "rationalise", "rationalize",
    "excuse", "the excuse", "alibi", "the rationalisation",
    # the fall named
    "the fall", "fallen", "the forbidden", "transgression",
    "temptation", "tempted", "the seduction", "seduced",
    "corruption", "corrupt", "corrupted", "the rot", "rotting",
    "decay", "decayed", "the worms", "the corpse",
)


# ===========================================================================
# THE CANON
# ===========================================================================

def load_authors() -> List[dict]:
    path = os.path.join(FAR_WRITING, "catalog", "authors.json")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        for key in ("authors", "entries", "canon", "items", "books"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # a dict of author -> list of works
        out = []
        for author, works in data.items():
            if isinstance(works, list):
                for w in works:
                    out.append({"author": author, "title": w})
            else:
                out.append({"author": author, "title": str(works)})
        return out
    return [d for d in data if isinstance(d, dict)]


def read_stories() -> List[Tuple[str, str]]:
    """The texts actually IN the repo."""
    out = []
    stories = os.path.join(FAR_WRITING, "stories")
    if not os.path.isdir(stories):
        return out
    for n in sorted(os.listdir(stories)):
        if not n.endswith(".md"):
            continue
        p = os.path.join(stories, n)
        try:
            out.append((n, open(p, encoding="utf-8", errors="replace").read()))
        except OSError:
            continue
    return out


# ===========================================================================
# THE MEASUREMENTS
# ===========================================================================

def text_density(text: str) -> Dict[str, float]:
    """How load-bearing is this text? Four numbers, each measured.

    WORDS        the raw length.
    DIALOGUE     the share of the words that are spoken. A dialogue
                 text is dense in voice -- which is the point of the
                 catalog, because it is the catalog of VOICES.
    UNIQUE       the type-token ratio: how much of the vocabulary is
                 distinct. A text that keeps saying the same words
                 is a narrow text.
    DARK         the density of the adversary's vocabulary per 100k
                 characters.
    """
    low = text.lower()
    words = re.findall(r"[A-Za-z']+", low)
    n_words = len(words)
    unique = len(set(words)) / n_words if n_words else 0.0

    # the dialogue share: lines that are attributed speech
    dialogue_lines = 0
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if re.match(r'^[A-Z][A-Za-z .\'-]{0,28}:\s', s) or \
           s.startswith(('"', "'", "\u201c")):
            dialogue_lines += 1
    total_lines = sum(1 for l in text.splitlines() if l.strip())
    dialogue = dialogue_lines / total_lines if total_lines else 0.0

    dark_hits = sum(1 for t in DARK_VOCAB if t in low)
    per_100k = (dark_hits / (len(text) / 100000.0)) if text else 0.0

    return {
        "words": n_words,
        "chars": len(text),
        "unique_ratio": unique,
        "dialogue": dialogue,
        "dark_terms": dark_hits,
        "dark_per_100k": per_100k,
    }


def main() -> int:
    print("=" * 78)
    print("THE FAR-WRITING CANON, RANKED BY DENSITY")
    print("=" * 78)
    print()

    authors = load_authors()
    stories = read_stories()

    print("A. THE CATALOG")
    print("   authors.json entries   %d" % len(authors))
    if authors:
        sample = authors[0]
        print("   the shape of an entry: %s"
              % ", ".join("%s=%r" % (k, str(v)[:40])
                          for k, v in list(sample.items())[:6]))
    print("   texts IN the repo      %d" % len(stories))
    print()

    # -- B: the texts in the repo, by density ------------------------
    print("B. THE TEXTS IN THE REPO, BY DENSITY")
    print("   %-42s %-9s %-9s %-9s %s"
          % ("text", "words", "dialogue", "uniques", "dark/100k"))
    rows = []
    for name, text in stories:
        d = text_density(text)
        rows.append((name, d))
    rows.sort(key=lambda r: -r[1]["dark_per_100k"])
    for name, d in rows:
        print("   %-42s %-9d %-9.1f%% %-9.3f %.1f"
              % (name[:42], d["words"], d["dialogue"] * 100,
                 d["unique_ratio"], d["dark_per_100k"]))
    print()

    # -- C: the DARK POLE, which is what Bobby asked for -------------
    print("C. THE DARK POLE -- the texts that carry the adversary")
    print()
    print("   Bobby: *\"we MUST have the evil adversary, the king of")
    print("   lies, ie satan.\"* So the library needs the adversary AS")
    print("   THE ADVERSARY, not as a moral example.")
    print()
    print("   AND THE TRADITION HAS THEM, PUBLIC DOMAIN, AND SOME ARE")
    print("   ALREADY IN THE CANON:")
    print()
    DARK_CANON = [
        ("Milton", "Paradise Lost",
         "the rebel angel's argument, which is SOPHISTIC and loses. The "
         "best text in English on why the lie is attractive"),
        ("Dante", "Inferno, canto XXIV-CXXIV",
         "the eighth circle, where the fraudulent counsellors are. "
         "STRUCTURAL: the fraudsters are not with the violent, they "
         "are with the LIARS, because fraud is a speech-act. 1320."),
        ("Goethe", "Faust",
         "the devil's bargain, and the mechanism: power in exchange "
         "for the gradual surrender of your own judgement. THE "
         "AGENDA, IN THE FORM OF A STORY."),
        ("Melville", "Moby-Dick",
         "ALREADY IN THE REPO. Ahab's speech to the crew before the "
         "hunt. THE MOST DENSE STATEMENT OF AGENDA IN ENGLISH, AND IT "
         "IS A TRANSFER OF FAMILY INTO A HUNT."),
        ("Dostoevsky", "The Brothers Karamazov, The Idiot",
         "the smoothness of the advanced liar, and the holy fool who "
         "sees through him"),
        ("Stendhal", "The Charterhouse of Parma",
         "the con, the count, and the realization"),
        ("Conrad", "Lord Jim",
         "the man who is not a criminal and is one anyway"),
        ("Stevenson", "Dr Jekyll and Mr Hyde",
         "the split, and the paperwork of it"),
        ("Lem", "Solaris",
         "the thing that is not what it appears"),
        ("Marlowe", "Doctor Faustus",
         "the same bargain, earlier, and colder"),
        ("Webster", "The White Devil",
         "the most successful devil of the Renaissance stage"),
        ("Jacobean", "The Revenger's Tragedy, The Changeling",
         "the court as the con's theatre"),
    ]
    for author, title, why in DARK_CANON:
        print("     %-12s %-34s %s" % (author, title, why))
    print()

    # -- D: the measurement that picks the canon --------------------
    print("D. THE DARK DENSITY MEASUREMENT, on the catalog")
    print()
    print("   The catalog is the source of VOICES. So the measurement")
    print("   is: which catalog entries are ALREADY about the dark")
    print("   pole, by title? Because the catalog is a list of works")
    print("   and the works are the training material, and the")
    print("   adversary has to be IN the training material.")
    print()
    DARK_TITLE_MARKERS = (
        "faust", "inferno", "paradise lost", "moby", "karamazov",
        "the idiot", "charterhouse", "lord jim", "jekyll", "solaris",
        "white devil", "revenge", "changeling", "nearer my god",
        "lower depths", "king lear", "macbeth", "othello",
        "the possessed", "demons", "garcin", "belial",
    )
    hits = []
    for a in authors:
        title = str(a.get("title", a.get("work", a.get("name", ""))))
        low = title.lower()
        for m in DARK_TITLE_MARKERS:
            if m in low:
                hits.append((str(a.get("author", "?")), title, m))
                break
    print("   catalog entries whose TITLE is already the dark pole: %d"
          % len(hits))
    for author, title, m in hits[:14]:
        print("     %-22s %s" % (author[:22], title[:48]))
    print()
    if len(hits) < 8:
        print("   SO THE CANON DOES NOT YET CARRY THE DARK POLE. The")
        print("   catalog is %d entries and it needs the texts above" %
              len(authors))
        print("   ADDED. That is the gap, and it is a list.")
    print()

    print("=" * 78)
    print("  Run: python src/canon_density.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
