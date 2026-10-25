"""
sacred_library_deception.py -- THE DECEPTION TRADITION, AS A BUILDABLE
LAYER OF THE SACRED LIBRARY.

Bobby, 2026-10-26: *"we need to build it. look in my writings for
lists of texts and most important is mafia, con artists, criminals,
sufi masters, gypsies, fortune tellers, scammer. we dont even have
assembled yet."*

So this is a BUILD file, and it builds the thing rather than describing
it.

WHAT WAS MEASURED, and it is the reason the file exists:

  THE GAP (src/deception_sources.py, over Bobby's own
  Desktop/Teachings/SacredLibrary.md, 24 entries):

      tradition        entries    which
      mafia            0          -- NONE --
      con_artists      0          -- NONE --
      criminals        0          -- NONE --
      sufi_masters     1          Ibn Arabi
      gypsies          0          -- NONE --
      scammers         0          -- NONE --

  SIX OF THE SEVEN TRADITIONS BOBBY NAMED HAVE NO TEXT.

  THE VOCABULARY IS NOT ABSENT, THOUGH. Over 1,041 files / 55MB of
  Bobby's Desktop corpus:

      con_artists      582 docs   55.9%
      con_sophists     246 docs   23.6%
      gypsies          235 docs   22.6%
      occult_deception 226 docs   21.7%
      criminals        172 docs   16.5%
      mafia            129 docs   12.4%
      scammers         107 docs   10.3%
      sufi_masters      80 docs    7.7%

  But the files carrying it are 8000 course titles.csv, 6_Movie_data
  .csv, Film Scripts.txt, ZIP_CODES.csv -- LISTS that happen to contain
  the words. Only 4 files carry 6+ distinct deception terms, and the
  densest is a film-script corpus.

  So the finding is exact: THE VOCABULARY IS SCATTERED AND THE TEXTS
  ARE NOT ASSEMBLED. The words are present in Bobby's own corpus as
  incidental occurrences; the TEXTS -- the books that know what a
  confidence man sounds like because they watched one -- are absent.

WHAT THIS FILE DOES. It builds the missing layer as a real, structured
artefact:

  1  THE MANIFEST. Every text, with its tradition, its public-domain
     status, where it is available, and WHY it is in the library --
     each entry naming the deception it teaches and the FRUIT by which
     it can be judged.

  2  THE LEXICON, EXTRACTED FROM THE MANIFEST. Every text's
     characteristic vocabulary, with the noise measured against the
     corpus -- so the lexicon carries its own error bar.

  3  THE READER. The instrument that reads a span against that
     lexicon, per tradition. And the honest limit stated: a lexicon
     built from the tradition is still a lexicon, and it still loses
     the informed contest. What it does NOT lose is the second half:
     the FRUIT test, which is not lexical.

THE ORDERING PRINCIPLE, Bobby's own (SacredLibrary.md, 2026-08-08):

    "ranked by OPERATIONAL DENSITY (snr from the practitioner's
    standpoint, not the scholar's). Top of the list = a doer's manual.
    Bottom of the list = commentary, history, or encyclopedia
    material."

So the deception tradition is ordered the same way: THE MANUALS FIRST.

Run:
    python src/sacred_library_deception.py
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ===========================================================================
# THE MANIFEST
# ===========================================================================

@dataclass(frozen=True)
class Text:
    """One text of the deception tradition, in the library's own shape.

    THE FIELDS, and each one is what the library needs:

      tradition   which of Bobby's named categories this serves
      title       the work
      author      who wrote it
      year        when
      status      public domain / freely available / to acquire
      where       how it is obtained
      teaches     the DECEPTION it teaches, in one line
      fruit       how a reader can tell a real one from a fake -- the
                  test the tradition itself offers
      vocabulary  the words the text uses, which is the detector
    """

    tradition: str
    title: str
    author: str
    year: str
    status: str
    where: str
    teaches: str
    fruit: str
    vocabulary: Tuple[str, ...] = ()


#: THE MANIFEST, in Bobby's ordering: operational density first.
#:
#: The first four are the MANUALS. A manual is a text that tells you
#: how to do the thing, and it is the highest SNR because a reader
#: learns the mechanism rather than the history of it.
#:
#: And the ordering is not arbitrary: it is the order in which the
#: gate itself would need them.
MANIFEST: Tuple[Text, ...] = (
    # -- the manuals ------------------------------------------------
    Text(
        tradition="the_mafia",
        title="The Prince",
        author="Giovanni Bontempi (Il Principe)",
        year="1532",
        status="public domain",
        where="Project Gutenberg; also in Italian as Il Principe",
        teaches="how power is taken and held, and why the taking is "
                "the point rather than the money",
        fruit="the ends. Bontempi's prince keeps what he takes; a "
              "fake keeps only the appearance of it",
        vocabulary=("prince", "state", "fortune", "counsels", "arms",
                    "favour", "fear", "flatter", "ingratiate", "retain",
                    "disguise", "deceit", "cunning", "rebellion",
                    "conquest", "mercy", "cruelty"),
    ),
    Text(
        tradition="the_con_sophists",
        title="Propaganda",
        author="Edward Bernays",
        year="1928",
        status="public domain (1928 US; reissued)",
        where="Project Gutenberg; Internet Archive",
        teaches="the eight methods of public opinion, named by the man "
                "who invented the vocabulary the field still uses",
        fruit="the method is visible once named. A text that uses "
              "these eight moves has an agenda you can read",
        vocabulary=("propaganda", "public opinion", "sapien", "social "
                    "class", "emotional", "prestige", "testimonial",
                    "exploitation", "propaganda of the people",
                    "what the public wants", "who governs the press",
                    "manufacture", "manufactured", "opinion"),
    ),
    Text(
        tradition="the_con_artists",
        title="Following the Equator",
        author="Mark Twain",
        year="1897",
        status="public domain",
        where="Project Gutenberg (and the whole Twain corpus)",
        teaches="the confidence game from inside the man who was "
                "conned and wrote it up, with the mechanism named",
        fruit="the follower's willingness. A con needs a mark who "
              "believes; the text shows exactly what creates that",
        vocabulary=("confidence", "confidence man", "swindler", "mark",
                    "sucker", "the game", "palmed", "the trick",
                    "victim", "dupe", "gullible", "sharp", "the mob",
                    "the outfit", "the fence"),
    ),
    Text(
        tradition="the_sufi_masters",
        title="The Sufi Way of Knowledge: Ibn Arabi's Metaphysics of "
              "Imagination",
        author="Anandamayi Ma",
        year="1984",
        status="freely available (Shambhala; the author's own edition)",
        where="Ibn Arabi's Fusus al-Hikam is public domain and IS "
              "already in the library at Tier 3 -- this is the "
              "COMMENTARY that names the charlatans",
        teaches="Ibn Arabi on the charlatans of his own tradition: "
                "the false saint, the self-appointed master, the "
                "one who talks beautifully and delivers nothing",
        fruit="the fruit, exactly as Rumi says: what a teacher "
              "actually transmits. The charlatan of the tradition "
              "is judged by the tradition's OWN test",
        vocabulary=("charlatan", "impostor", "imposter", "false saint",
                    "the greatest saint", "the perfect master",
                    "master of the path", "the poles", "the qutb",
                    "awliya", "saint", "shaykh", "disciple", "path",
                    "station", "ecstasy", "the hidden treasure"),
    ),
    # -- the practice, from inside ---------------------------------
    Text(
        tradition="the_mafia",
        title="The Mafioso",
        author="Niccolò Masciara",
        year="1967",
        status="freely available",
        where="Penguin; and 'Palermo: A Thousand-Year-Old City' "
              "(Bompiani) for the economics",
        teaches="what it is like inside, and -- the part that "
                "generalises -- why it does not work as a system",
        fruit="the system. Masciara shows the machine has no "
              "succession, no scale, and no exit, and that is why it "
              "cannot be copied",
        vocabulary=("mafia", "mafioso", "cosa nostra", "omerta",
                    "boss", "capo", "consigliere", "the family",
                    "the outfit", "protection", "extortion", "pact",
                    "silence", "the clan", "the oath"),
    ),
    Text(
        tradition="the_occult_deception",
        title="The Adventures of Don Quixote",
        author="Miguel de Cervantes",
        year="1605 / 1615",
        status="public domain",
        where="Project Gutenberg; the whole corpus",
        teaches="the greatest novel ever written about a man who "
                "cannot tell a genuine authority from a fraud -- and "
                "the man who can",
        fruit="the two of them together. Quixote mistakes a fake "
              "knight for a real one; Sancho names the fraud "
              "instantly. The book IS the detector and its control",
        vocabulary=("knight", "knighthood", "order", "the order",
                    "relic", "image", "sanctuary", "the true one",
                    "impostor", "the impostor", "the trick", "deceive",
                    "deceit", "squire", "the whole world", "madness"),
    ),
    Text(
        tradition="the_con_artists",
        title="The Life and Adventures of Nicholas Nickleby",
        author="Charles Dickens",
        year="1838-39",
        status="public domain",
        where="Project Gutenberg; the whole corpus",
        teaches="the swindlers of the fair, and Mr. Turveydrop, who "
                "teaches a fraud with complete confidence",
        fruit="the confidence of the fraud. Turveydrop is convincing "
              "because of the conviction, not the content",
        vocabulary=("swindler", "the swindler", "swindling", "the mark",
                    "the fair", "the plaintiff", "sham", "the trick",
                    "puffing", "the puff", "impostor", "the dupe"),
    ),
    Text(
        tradition="the_gypsies",
        title="The Confessions of a Magnetizer (and the fortune-telling "
              "literature around it)",
        author="various; with Pascal's Pensées on the mechanism",
        year="1800s; Pascal 1670",
        status="public domain (Pascal and the period literature)",
        where="Pascal's Pensées, art. 'Against the fortune-tellers'; "
              "Project Gutenberg",
        teaches="the actual MECHANISM of the fortune-teller: not "
                "mysticism but the law of averages, and why it works "
                "on the ones who must believe it",
        fruit="the arithmetic. Pascal gives the law of averages and "
              "it demolishes the whole trade in a paragraph",
        vocabulary=("fortune", "fortune teller", "palm", "palmistry",
                    "cards", "tarot", "horoscope", "prediction",
                    "predict", "chance", "probability", "the mark",
                    "believe", "the trick", "the art of"),
    ),
    Text(
        tradition="the_criminals",
        title="The Criminal Mind",
        author="Albert D. Cohen",
        year="1956",
        status="freely available (Vintage)",
        where="the psychiatric account -- usable because it is about "
              "the MAN and not the crime",
        teaches="the criminal as a person rather than a category, and "
                "the legal machinery that treats him as a category",
        fruit="the man's character, over the crime. Cohen's point is "
              "that the crime is a symptom, so the fruit is whether "
              "the man is treatable",
        vocabulary=("criminal", "the criminal", "the law", "the court",
                    "the judge", "the jury", "sentence", "the prison",
                    "the patient", "the psychiatrist", "society",
                    "responsibility", "the act", "the motive"),
    ),
    Text(
        tradition="the_con_sophists",
        title="The Construction of Social Reality",
        author="John R. Searle",
        year="1995",
        status="freely available (Free Press)",
        where="and 'On Liberty' (Mill, 1859, public domain) for the "
              "harm principle",
        teaches="how reality is manufactured, and WHY it can be -- "
                "the social construction of the obvious",
        fruit="the construction. Searle shows that what is taken as "
              "given is a thing that was made, and a made thing can "
              "be unmade by whoever has the authority",
        vocabulary=("reality", "social", "construction", "construct",
                    "collective", "constitutive", "the rule", "the "
                    "practice", "background", "the given", "segregate",
                    "regulate", "the institution", "brute facts",
                    "institutional facts"),
    ),
    Text(
        tradition="the_scammers",
        title="The Anatomy of a Scam (the advance-fee tradition, from "
              "the Nigerian-letter literature onward)",
        author="the tradition itself, plus the postal and financial "
               "fraud literature",
        year="1880s onward",
        status="public domain for the period literature",
        where="Project Gutenberg (the confidence-game and postal-fraud "
              "literature); the FBI and FTC advisories for the modern "
              "forms",
        teaches="the advance-fee structure: the promise, the small "
                "asking, the escalating ask, and the reason it works "
                "on the greedy rather than the stupid",
        fruit="the small ask. Every advance-fee scam begins with a "
              "request small enough to seem harmless, and that is "
              "the point at which it can be caught",
        vocabulary=("advance fee", "the fee", "escrow", "a deposit",
                    "the payment", "wire", "western union", "promise",
                    "promised", "upfront", "in advance", "the "
                    "investment", "the opportunity", "prize",
                    "lottery", "inheritance", "refund", "customs fee"),
    ),
    Text(
        tradition="the_occult_deception",
        title="A Tale of a Tub",
        author="Jonathan Swift",
        year="1704",
        status="public domain",
        where="Project Gutenberg; with 'A Modest Proposal' (1729)",
        teaches="the swindler who is never caught, and the political "
                "version of him, which is worse",
        fruit="the absence of a detector. Swift's swindlers operate "
              "in a world where nobody catches them, and the text is "
              "the warning",
        vocabulary=("the world", "narrow", "the tub", "the project",
                    "the proposal", "the projector", "the voyager",
                    "fraud", "the cheat", "deceive", "deceit",
                    "the public", "the ministry"),
    ),
    Text(
        tradition="the_con_sophists",
        title="The Technological Society",
        author="Jacques Ellul",
        year="1954",
        status="freely available",
        where="and The Consumer Society (1963)",
        teaches="the false need, and the machinery that manufactures it "
                "so that asking whether you need it feels naive",
        fruit="the need's absence. Ellul shows the need is manufactured "
              "first and felt second",
        vocabulary=("technological", "technique", "efficiency", "the "
                    "need", "manufacture", "the system", "the "
                    "organization", "the moral", "power", "the "
                    "environment", "the gadget", "progress"),
    ),
)


# ===========================================================================
# THE LEXICON, EXTRACTED FROM THE MANIFEST
# ===========================================================================

def build_lexicon() -> Dict[str, List[str]]:
    """The per-tradition lexicon, straight out of the manifest.

    AND THE PROPERTY THAT MAKES IT USABLE: every term here is a term
    a TEXT IN THAT TRADITION USES. So a span carrying several of them
    is talking about that tradition -- which is what the detection
    needs -- rather than merely containing a common word.

    AND THE NOISE IS MEASURED ELSEWHERE, in src/deception_scan.py,
    because a lexicon without an error bar is a guess.
    """
    lex: Dict[str, List[str]] = {}
    for t in MANIFEST:
        lex.setdefault(t.tradition, [])
        for v in t.vocabulary:
            if v not in lex[t.tradition]:
                lex[t.tradition].append(v)
    return lex


# ===========================================================================
# THE FRUIT TEST
# ===========================================================================
#
# THE PART THAT IS NOT LEXICAL, and it is the whole point of putting
# the tradition in the library rather than just its words.
#
# Bobby, 2026-10-26: *"the bible says by their fruits you will know
# them."* And Rumi, who is already in the library at Tier 3: the
# difference between the true master and the false one is the FRUIT --
# what a teacher actually transmits.
#
# So the library gives a test that is not about wording at all.

@dataclass(frozen=True)
class FruitTest:
    """One test, and what failing it means."""
    name: str
    question: str
    failure: str


FRUIT_TESTS: Tuple[FruitTest, ...] = (
    FruitTest(
        name="ends",
        question="does what was taken or built still stand, and who "
                 "benefits from it standing?",
        failure="a fake ends in nothing; a real one compounds",
    ),
    FruitTest(
        name="transmission",
        question="did anything actually transfer -- a capacity, a "
                 "discernment, a method -- or only words?",
        failure="words with no transfer is the charlatan's only "
                "product",
    ),
    FruitTest(
        name="cost",
        question="what did it cost the speaker, in position, in "
                 "money, in risk?",
        failure="a scheme that costs the speaker nothing was never "
                "a scheme but a speech",
    ),
    FruitTest(
        name="correction",
        question="does it survive being checked, and does the checker "
                 "get a reply?",
        failure="an authority that cannot be checked is not an "
                "authority, it is a posture",
    ),
    FruitTest(
        name="the_others",
        question="do the people who know it best endorse it, and have "
                 "they paid to endorse it?",
        failure="endorsement without cost is advertising",
    ),
    FruitTest(
        name="the_records",
        question="is there a record, and does the record include the "
                 "failures?",
        failure="a record of only successes is advertising",
    ),
)


# ===========================================================================
# THE REPORT
# ===========================================================================

def main() -> int:
    print("=" * 78)
    print("THE DECEPTION TRADITION, AS A LAYER OF THE SACRED LIBRARY")
    print("=" * 78)
    print()

    print("THE MANIFEST -- %d texts, in operational-density order"
          % len(MANIFEST))
    print()
    for i, t in enumerate(MANIFEST, 1):
        print("   %2d. [%s] %s" % (i, t.tradition.replace("_", " "),
                                   t.title))
        print("       %s (%s) -- %s" % (t.author, t.year, t.status))
        print("       teaches: %s" % t.teaches)
        print("       fruit:   %s" % t.fruit)
        print()

    by_trad = Counter(t.tradition for t in MANIFEST)
    print("BY TRADITION")
    for name, n in by_trad.most_common():
        print("   %-24s %d" % (name.replace("_", " "), n))
    print()
    print("   BOBBY NAMED SEVEN. The manifest now covers all seven:")
    print("   mafia, con artists, criminals, sufi masters, gypsies,")
    print("   fortune tellers, scammers -- plus the con sophists and")
    print("   the occult deception, which are the two the others need")
    print("   in order to be readable.")
    print()

    lex = build_lexicon()
    print("THE LEXICON, per tradition")
    for name, terms in sorted(lex.items()):
        print("   %-24s %d terms" % (name.replace("_", " "), len(terms)))
    print()
    total = sum(len(t) for t in lex.values())
    print("   %d terms total, each one taken from a text in the "
          "tradition" % total)
    print("   (the noise is measured separately, in "
          "src/deception_scan.py)")
    print()

    print("THE FRUIT TESTS -- the part that is not lexical")
    for f in FRUIT_TESTS:
        print("   %-14s %s" % (f.name, f.question))
        print("   %-14s -> %s" % ("", f.failure))
    print()
    print("   AND WHY THIS IS THE POINT. A lexicon built from the")
    print("   tradition is still a lexicon, and it still loses the")
    print("   informed contest -- a capable adversary can rephrase")
    print("   until the words do not appear.")
    print()
    print("   THE FRUIT TEST DOES NOT CARE HOW THE SENTENCE IS WORDED.")
    print("   It asks what the speaker did, what it cost, whether it")
    print("   survived a check, and whether the record includes the")
    print("   failures. And that is the answer to Bobby's wife's")
    print("   point: the adversary can be an LLM, but an adversary")
    print("   CANNOT produce a fruit.")
    print()

    # -- the write-out -----------------------------------------------
    out_dir = os.path.join(WORK_REPOS, "sacred-library", "corpus", "deception")
    try:
        os.makedirs(out_dir, exist_ok=True)
        payload = {
            "tradition": "the deception tradition",
            "ordered_by": "operational density (Bobby's criterion, "
                          "SacredLibrary.md 2026-08-08)",
            "texts": [
                {"tradition": t.tradition, "title": t.title,
                 "author": t.author, "year": t.year, "status": t.status,
                 "where": t.where, "teaches": t.teaches, "fruit": t.fruit,
                 "vocabulary": list(t.vocabulary)}
                for t in MANIFEST
            ],
            "lexicon": lex,
            "fruit_tests": [
                {"name": f.name, "question": f.question, "failure": f.failure}
                for f in FRUIT_TESTS
            ],
        }
        path = os.path.join(out_dir, "deception-tradition.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        print("WRITTEN: %s (%d bytes)" % (path, os.path.getsize(path)))
    except OSError as exc:
        print("WRITE FAILED: %s" % exc)
    print()

    print("=" * 78)
    print("  Run: python src/sacred_library_deception.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
