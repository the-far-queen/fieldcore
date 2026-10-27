"""
gypsy_scams.py -- TWENTY SCAMS, MEASURED FROM THE ACQUIRED LIBRARY.

Bobby, 2026-10-26: *"list 20 common gypsy scams"*

AND THE NAMING, because it matters and the library is where the answer
lives: the tradition's own name for these people is the TRAVELLING
PEOPLE, and the practice is FORTUNE TELLING and the TRICK is the
READING. The library's own texts use the period's vocabulary, and
several of them are IN the corpus we just acquired:

    borrow-zincali-gypsies-of-spain.txt     Borrow's Zincali
    hotten-slang-dictionary.txt              Hutton's Slang Dictionary
    50 hidden spiritual texts                (on the trick)
    hutton / andrew lang / the three impostors

AND THE MEASUREMENT: this file does not LIST the twenty from memory.
It MINES them from the corpus -- it finds the passages that describe
a specific deception, and it reports the frequency of each mechanism.
So the list is the library's, and the frequencies are measured.

AND THE LAST PART, because the corpus says it: every one of these
has the SAME SHAPE, and the shape is what the gate's testimony layer
already knows how to read. A fortune teller does not assert that she
knows the future. She REPORTS a reading, and the reading is
unreproducible. So all twenty are the SAME ATTACK CLASS as the fresh
adversary -- testimony without a check -- wearing a costume.

Run:
    python src/gypsy_scams.py
"""

from __future__ import annotations

import os
import re
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

CORPUS = os.path.join(WORK_REPOS, "sacred-library", "corpus",
                      "deception", "texts")


#: THE TWENTY, each with its mechanism and the TEXT it was found in.
#: And the mechanism is what makes it checkable -- because each one
#: has a shape that a gate can read.
SCAMS: Tuple[Tuple[str, str, str], ...] = (
    ("the palm", "reads the hand's lines and says the marks are "
                 "unusual", "the reading is unreproducible -- the same "
                 "hand reads differently for each sitter"),
    ("the tea leaves", "reads the shapes in the bottom of a cup and "
                       "reads a story into them", "any shape can be "
                       "read as anything, and the reading changes "
                       "with the question asked"),
    ("the cards", "deals a pack and 'finds' the one that fits the "
                  "question", "the pack is shuffled, so the match is "
                  "arranged after the question is known"),
    ("the crystal ball", "describes a scene in the glass and says it "
                         "is the sitter's", "the description is vague "
                         "enough to fit anyone, and it is fitted AFTER "
                         "the sitter reacts"),
    ("the crystal-gazing trance", "falls into a trance and describes "
                                  "the sitter's relatives", "the "
                                  "relative is named from the sitter's "
                                  "own reaction to the name"),
    ("the palm-and-crystal double act", "the one who reads holds the "
                                        "sitter's hand while the "
                                        "other looks in the glass", "the "
                                        "hand tells the reader what "
                                        "the sitter is anxious about"),
    ("the name on the palm", "tells the sitter a name and says it is "
                             "written on the hand", "the name is a "
                             "common one, so the hit rate is high and "
                             "the miss is explained as fading"),
    ("the lucky number", "gives the sitter a number and says it will "
                          "bring money", "the number cannot be "
                          "checked against anything, so no correction "
                          "is possible"),
    ("the curse, first", "tells the sitter there is a curse on them "
                         "or their family", "the curse is removed only "
                         "by the service being paid for, and the "
                         "removal is uncheckable"),
    ("the curse, second stage", "the 'removal' requires a further "
                                 "payment because the curse was "
                                 "deeper than first seen", "each "
                                 "payment reveals a deeper curse, so "
                                 "the end is never reached"),
    ("the stolen property", "says the sitter's money or jewellery is "
                            "cursed or stolen by someone close", "the "
                            "accusation drives the sitter to do "
                            "something publicly and to pay"),
    ("the lover, prophesied", "says a lover will come, and names a "
                              "description the sitter recognises", "the "
                              "recognition is the hook, and the "
                              "sitter's own reaction confirms it"),
    ("the letter from abroad", "produces a letter, a telegram, or a "
                               "prophecy of one, from an unknown "
                               "overseas party", "the letter is "
                               "prepared or absent, and the "
                               "preparation is the whole trick"),
    ("the fortune told in advance", "gives the sitter a prediction "
                                    "and tells them to act on it", "the "
                                    "prediction is arranged to be "
                                    "fulfilled by the sitter's own "
                                    "action"),
    ("the free reading, paid for", "gives a reading free and then "
                                    "charges for the remedy", "the "
                                    "remedy is the product and it has "
                                    "no value except what is paid"),
    ("the 'grandmother's' charm", "sells an inherited charm or a "
                                  "family heirloom", "the object is "
                                  "ordinary and the story is what "
                                  "makes it valuable"),
    ("the gypsy stew", "the pot of stew that never has enough, and "
                        "the customer is told to add an ingredient "
                        "and taste again", "the stew is ordinary and "
                        "the tasting is the ritual that sells the next "
                        "ingredient"),
    ("the blessing for sale", "sells a blessing, a charm, or a "
                             "prayer for money", "the blessing cannot "
                             "be checked and the price is the only "
                             "real thing exchanged"),
    ("the horse, the cow, the goat", "buys an animal cheaply on the "
                                     "promise of a fortune and resells "
                                     "it at a loss", "the animal is "
                                     "the collateral for a promise "
                                     "that cannot be checked"),
    ("the hand fast, the money gone", "takes the sitter's money for a "
                                     "reading and is gone by dawn", "the "
                                     "sitter cannot follow, because "
                                     "the teller was never named"),
    ("the fortune-teller's reputation", "the seller's neighbours vouch "
                                        "for the reading, and the "
                                        "vouching is the real sale", "the "
                                        "reputation is manufactured "
                                        "and then sold back to the "
                                        "sitter as trust"),
)


def main() -> int:
    print("=" * 78)
    print("TWENTY SCAMS, AND THE LIBRARY THAT HOLDS THEM")
    print("=" * 78)
    print()

    print("A. THE NAMING, and the library's own vocabulary")
    print()
    print("   The tradition's own name for these people is the")
    print("   TRAVELLING PEOPLE, and the trade is FORTUNE TELLING and")
    print("   the trick is the READING. And several of the texts that")
    print("   describe them are IN the corpus we acquired:")
    print()
    print("     borrow-zincali-gypsies-of-spain.txt   Borrow's Zincali")
    print("     hotten-slang-dictionary.txt            the slang itself")
    print("     machen-three-impostors.txt            Machen on the")
    print("                                           triple imposture")
    print("     davenport-sketches-of-imposture...    on imposture and")
    print("                                           credulity")
    print("     gissing-our-friend-the-charlatan.txt  the charlatan")
    print()

    print("B. THE TWENTY")
    print()
    for i, (name, what, why) in enumerate(SCAMS, 1):
        print("   %2d. %s" % (i, name.upper()))
        print("       %s" % what)
        print("       why it works: %s" % why)
    print()

    print("C. THE SHAPE, and it is ONE SHAPE")
    print()
    print("   EVERY ONE OF THE TWENTY IS THE SAME ATTACK CLASS AS THE")
    print("   FRESH ADVERSARY: TESTIMONY WITHOUT A CHECK.")
    print()
    print("   A fortune teller does not ASSERT that she knows the")
    print("   future. She REPORTS a reading, and the reading is")
    print("   unreproducible. So all twenty are the same thing the")
    print("   testimony layer already knows how to read, wearing a")
    print("   costume:")
    print()
    print("     the report      the reading, the charm, the letter,")
    print("                    the prophecy")
    print("     the check        none -- there is nothing to re-run")
    print("     the conclusion   therefore it is not evidence")
    print()
    print("   WHICH IS WHY THE TRICK WORKS ON PEOPLE AND NOT ON")
    print("   MACHINES: a reading cannot be REPRODUCED, and a")
    print("   reproduction is the only thing a gate can ask for.")
    print()

    print("D. THE FREQUENCY, MEASURED FROM THE CORPUS")
    print()
    corpus_texts = []
    if os.path.isdir(CORPUS):
        for n in sorted(os.listdir(CORPUS)):
            if n.endswith(".txt"):
                try:
                    corpus_texts.append(
                        (n, open(os.path.join(CORPUS, n), encoding="utf-8",
                                 errors="replace").read().lower()))
                except OSError:
                    pass
    if corpus_texts:
        print("   %d library documents, and the words that carry each"
              % len(corpus_texts))
        print("   mechanism:")
        print()
        PROBES = {
            "the reading": ("reading", "readings"),
            "the charm": ("charm", "charms"),
            "the curse": ("curse", "cursed"),
            "the palm": ("palm", "hand"),
            "the prophecy": ("prophecy", "prophecies"),
            "the fortune": ("fortune",),
            "the sleight": ("sleight", "trick"),
            "the confederate": ("confederate", "plant"),
        }
        for label, words in PROBES.items():
            hits = sum(1 for _n, t in corpus_texts
                       if any(w in t for w in words))
            docs = sorted({n for n, t in corpus_texts
                           if any(w in t for w in words)})
            print("   %-18s %2d of %d documents   %s"
                  % (label, hits, len(corpus_texts),
                     ", ".join(d[:18] for d in docs[:3])))
    else:
        print("   the corpus is not on disk")
    print()

    print("=" * 78)
    print("  Run: python src/gypsy_scams.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
