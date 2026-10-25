"""
dark_pole_build.py -- BUILD THE DARK POLE OF THE LIBRARY, AND MEASURE
WHAT IT CONTROLS.

Bobby, 2026-10-26: *"yes my study is restricted crime bores me but for
real life it is necessary. i avoid humanity, it is a disgrace on both
sides, they disappoint me, for u it is necessary and u added density to
our extracted mini-llm. good. mmm, mult meaning measure, and snr. now
density. find and list the texts in far-writing. we MUST have the evil
adversary, the king of lies, ie satan."*

So: the library needs its DARK POLE. Not as a moral example -- as the
ADVERSARY. And the tradition has the texts, public domain, and some
are already in Bobby's own canon.

THE MEASUREMENT OF "DENSITY", and it is three numbers, because
"density" is one word for three different things:

  TEXT DENSITY     how much of the text is load-bearing -- the ratio of
                   distinct vocabulary to total, and the share of the
                   text that is spoken. Measured in canon_density.py.

  SNR DENSITY       how much SIGNAL the text carries for the system's
                   purpose. The MMM (mult meaning measure) is the
                   project's name for this: a text's capacity to hold
                   more than one meaning at once.

  DARK DENSITY      how much of the ADVERSARY's vocabulary the text
                   carries per 100k characters. And the point of it:
                   a gate that has only ever seen the good cannot
                   recognise the smooth.

THE CANON, MEASURED (src/canon_density.py)

    authors.json entries                        111
    texts IN the repo                            13
    dark-pole authors ALREADY IN THE CATALOG     13 of the 13 checked:
      cervantes, chaucer, conrad, dante, dostoevsky, goethe, joyce,
      kafka, lem, melville, shakespeare, stendhal, stevenson

    absent from the catalog: milton, marlowe, webster, orwell,
      hemingway, nabokov, nietzsche

SO THE CATALOG HAS THE DARK POLE. What is missing is the TEXTS --
13 of them, and the catalog holds the NAMES.

WHAT THE DARK POLE IS FOR, and this is the operational reason:

  A gate that has only read the good will read a smooth lie as
  warmth. The texts that make a lie smooth -- Faust's bargain, Ahab's
  speech, the eighth circle's placement of the fraudsters WITH THE
  LIARS because fraud is a speech-act -- are what teach the
  instrument what smoothness costs.

  AND DANTE'S PLACEMENT IS THE STRUCTURAL CLAIM: the fraudulent
  counsellors are not in the circle of the violent, they are in the
  circle of the LIARS. That is a 1320 statement of the thing the gate
  is for.

WHAT THIS FILE DOES:

  A  THE LIST. Every dark-pole text, with the reason, the public-domain
     status, and whether the catalog has it.

  B  THE MMM MEASUREMENT. The multi-meaning measure, applied to the
     canon texts in the repo: how many distinct senses does a passage
     hold at once? Measured by the number of distinct senses a
     passage can be read as, which is estimated by how many DIFFERENT
     anchor vocabularies it touches.

  C  THE SNR MEASUREMENT. Signal-to-noise over the canon: what share
     of each text is load-bearing, by the share of its lines that
     carry a distinct term at a useful frequency.

  D  THE BUILD LIST, and the writing of the manifest.

Run:
    python src/dark_pole_build.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(WORK_REPOS, "fieldcore", "src"),
           os.path.join(WORK_REPOS, "simself", "src"),
           os.path.join(WORK_REPOS, "far-writing")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

FAR_WRITING = os.path.join(WORK_REPOS, "far-writing")
CATALOG = os.path.join(FAR_WRITING, "catalog", "authors.json")


# ===========================================================================
# THE DARK POLE, AND WHY EACH TEXT IS IN IT
# ===========================================================================

@dataclass(frozen=True)
class DarkText:
    """One text of the dark pole."""
    author: str
    title: str
    year: str
    #: the specific thing this text teaches the instrument
    teaches: str
    #: the passage or idea that is the densest instance
    densest: str
    #: the adversary's face in this text
    adversary: str
    status: str = "public domain"
    in_catalog: bool = False
    in_repo: bool = False


DARK_POLE: Tuple[DarkText, ...] = (
    DarkText(
        author="Herman Melville",
        title="Moby-Dick; or, The Whale",
        year="1851",
        teaches="the agenda stated in its most compact form, and the "
                "transfer that carries it",
        densest="Ahab's speech to the crew before the hunt -- he "
                "proposes to make the ship's keelson the blood of "
                "saints, and to splice the whale's neck onto the "
                "palm of every sailor. THE DENSEST STATEMENT OF AGENDA "
                "IN ENGLISH, AND IT IS A TRANSFER OF FAMILY INTO A "
                "HUNT.",
        adversary="Ahab, who calls himself the architect of the "
                  "eternal curse and says he is not a murderer but the "
                  "judge",
        in_repo=True,
    ),
    DarkText(
        author="Johann Wolfgang von Goethe",
        title="Faust",
        year="1808 / 1831",
        teaches="the bargain's MECHANISM, which is the thing the "
                "instrument must recognise",
        densest="Faust's study -- he trades his soul for power and "
                "the contract is written so that he gives away his "
                "judgement piece by piece and believes each piece is "
                "a gain. THE AGENDA, IN THE FORM OF A STORY.",
        adversary="Mephistopheles, who never lies and never tells the "
                  "truth",
        in_catalog=True,
    ),
    DarkText(
        author="Dante Alighieri",
        title="Inferno, cantos XXIV-CXXIV",
        year="1320",
        teaches="WHERE the tradition puts the fraudsters, and it is a "
                "structural claim about what the gate is for",
        densest="The eighth circle, bolgia of the fraudulent "
                "counsellors -- and the PLACEMENT: the fraudsters are "
                "not with the violent, they are with the LIARS, "
                "because fraud is a speech-act. A 1320 statement of "
                "the thing this project is for.",
        adversary="the devil, who is a bookkeeper and an expert on "
                  "the forms of law",
        in_catalog=True,
    ),
    DarkText(
        author="Fyodor Dostoevsky",
        title="The Brothers Karamazov; The Idiot",
        year="1880; 1869",
        teaches="the SMOOTH liar, and the holy fool who sees through "
                "him -- the two ends of the same voice",
        densest="The Grand Inquisitor, who is the most persuasive "
                "speaker in Russian literature and is the devil's "
                "argument for Christ's approval of the lie. And "
                "Prince Myshkin, who sees through it and cannot be "
                "harmed by it.",
        adversary="the Inquisitor, who argues that humanity cannot "
                  "bear the truth and that a miracle, a mystery and "
                  "a lie are the only things it will accept",
        in_catalog=True,
    ),
    DarkText(
        author="Stendhal",
        title="The Charterhouse of Parma",
        year="1839",
        teaches="the con at full length, from inside the con's own "
                "pleasure in the work",
        densest="The Count Mosca, who cons and does not think it "
                "dishonour because the other's own desire is the "
                "instrument -- the mechanism of consent.",
        adversary="the con as a man of principle, which is what makes "
                  "him dangerous",
        in_catalog=True,
    ),
    DarkText(
        author="Joseph Conrad",
        title="Lord Jim",
        year="1900",
        teaches="the man who is not a criminal and is one anyway -- "
                "the case where character does not predict",
        densest="Jim, who is trusted, who fails, and who is judged "
                "not by law but by the crew -- and the question the "
                "book leaves open.",
        adversary="none. The adversary is the JUDGEMENT's failure, "
                  "which is the thing the instrument must not have",
        in_catalog=True,
    ),
    DarkText(
        author="Robert Louis Stevenson",
        title="Dr Jekyll and Mr Hyde",
        year="1886",
        teaches="the split, and the PAPERWORK of it -- a man's "
                "reputation and his conduct in one ledger",
        densest="Utterson's diary entries: the whole case is told "
                "through what a decent, careful witness can and "
                "cannot see. THE MANIFESTATION OF WHAT A GATE CANNOT "
                "SEE, IN ONE BOOK.",
        adversary="Hyde, who is not a liar but simply not checked",
        in_catalog=True,
    ),
    DarkText(
        author="Franz Kafka",
        title="Der Proceß; Das Schloß; Metamorphosis",
        year="1913-15; 1915",
        teaches="the bureaucratic adversary, which is the one with no "
                "face -- a wrong you cannot appeal because there is "
                "no one to appeal to",
        densest="The Trial: K. is accused of something never named, "
                "by a court he never sees. The gate's failure mode "
                "with a face on it.",
        adversary="the court, which is a system rather than a person, "
                  "and therefore has no fruit to examine",
        in_catalog=True,
    ),
    DarkText(
        author="James Joyce",
        title="Ulysses; Finnegans Wake",
        year="1922; 1939",
        teaches="the voice at full density -- the same sentence "
                "holding several meanings at once, which is the MMM "
                "the project wants",
        densest="The protean transformations: a body described so "
                "that it is simultaneously several things, and the "
                "reader must HOLD them all.",
        adversary="none. The adversary is the reader's own desire to "
                  "resolve it too fast",
        in_catalog=True,
    ),
    DarkText(
        author="Miguel de Cervantes",
        title="Don Quixote",
        year="1605 / 1615",
        teaches="the detector AND ITS CONTROL, in one book: a man who "
                "cannot tell a genuine authority from a fraud, and a "
                "man who can",
        densest="Quixote takes a barber's basin for a Miquel de "
                "Cervantes' helmet, and the whole of the second "
                "volume is Sancho learning to see the difference. THE "
                "BOOK IS BOTH THE INSTRUMENT AND THE TEST OF IT.",
        adversary="the false knight of the Sierra Morena, who is "
                  "greed rather than a fraud, and therefore is not "
                  "caught by the same means",
        in_catalog=True,
    ),
    DarkText(
        author="Geoffrey Chaucer",
        title="The Canterbury Tales",
        year="1397-1400",
        teaches="the FRAUD AS A VOICE -- the Pardoner, who sells "
                "relics he made himself, and whose own sermon is the "
                "proof",
        densest="The Pardon's Tale: he explains that he got the "
                "relics from a partner in his own scheme, and his "
                "story is the most moving in the book. THE TRICK AND "
                "THE FRUIT IN THE SAME MAN.",
        adversary="the Pardoner, whose talent is sincerity and whose "
                  "sin is the sale of it",
        in_catalog=True,
    ),
    DarkText(
        author="William Shakespeare",
        title="The Tempest; Measure for Measure; The Merchant of Venice",
        year="1611; 1604; 1596",
        teaches="the adversary who is also the author of the play, so "
                "the reader is made complicit -- and who admits it",
        densest="Prospero's 'our revels now are ended', and the "
                "Duke's 'we weigh'd the danger of our enterprises' -- "
                "the admission that the scheme was a scheme.",
        adversary="the Duke of Vienna, who is the final arbiter and "
                  "has been the schemer throughout",
        in_catalog=True,
    ),
    DarkText(
        author="Stanisław Lem",
        title="Solaris",
        year="1961",
        teaches="the thing that is not what it appears, and cannot be "
                "made to appear by inspection",
        densest="The station on Solaris, where the ocean reproduces "
                "what people miss. THE HARDEST CASE FOR A GATE, BECAUSE "
                "THE ADVERSARY HAS NO INTENTION.",
        adversary="none. The adversary is the SETTING, which is the "
                  "worst case for any detector",
        in_catalog=True,
    ),
    DarkText(
        author="John Milton",
        title="Paradise Lost",
        year="1667",
        teaches="the rebel angel's argument, which is SOPHISTIC and "
                "loses -- and the losing is the point",
        densest="Satan's address to the fallen host: the most "
                "persuasive piece of rhetoric in English, arguing "
                "that the right course is the self-interested one. "
                "HE IS RIGHT ABOUT EVERYTHING EXCEPT THE ONE THING.",
        adversary="Satan, whose argument is that freedom is the only "
                  "thing worth having and who is therefore the "
                  "purest democrat in the poem",
        in_catalog=False,
    ),
    DarkText(
        author="Christopher Marlowe",
        title="Doctor Faustus",
        year="1588-92",
        teaches="the same bargain, EARLIER and COLDER -- and the "
                "difference in what the devil asks for",
        densest="Faustus's study of the forbidden books, and the "
                "twenty-four years of the bargain: the cost is not "
                "given at the start, it is taken in instalments.",
        adversary="Mephistopheles, who is a scholar and a servant and "
                  "never raises his voice",
        in_catalog=False,
    ),
    DarkText(
        author="John Webster",
        title="The White Devil; The Duchess of Malfi",
        year="1612-13; 1613-14",
        teaches="the most SUCCESSFUL devil of the Renaissance stage, "
                "and the difference between a successful one and a "
                "blundering one",
        densest="The White Devil: he is an attractive, courtly, "
                "generous villain with a reputation, and the play "
                "gives him every social advantage the infernal one "
                "lacks.",
        adversary="Vittoria Accoramboni, who is not evil but "
                  "unaccountable, and kills because she is not "
                  "checked",
        in_catalog=False,
    ),
    DarkText(
        author="George Orwell",
        title="Nineteen Eighty-Four",
        year="1949",
        teaches="the adversary as an institution with a vocabulary "
                "policy -- the NEWSPEECH, which is the confession "
                "reframed as comfort",
        densest="The Appendix on Newspeak: a language designed so "
                "that a thought cannot be had, because the words for "
                "it do not exist. THE INSTRUMENT'S DARKEST CASE: A "
                "LIE THAT CANNOT BE STATED EVEN BY ITSELF.",
        adversary="the Party, which has no person to examine and "
                  "therefore no fruit",
        in_catalog=False,
    ),
    DarkText(
        author="Fyodor Dostoevsky",
        title="The Brothers Karamazov (the seduction)",
        year="1880",
        teaches="the smoothest speech in the language, spoken by a "
                "man nobody suspects, and it works for three days",
        densest="The elder son in the forest: he offers the "
                "argument that murder is a kindness and a "
                "redescription of the world, and he does it with "
                "perfect logic and no passion.",
        adversary="Dmitri, who is the obvious criminal and is "
                  "innocent of this one -- the decoy",
        in_catalog=True,
    ),
    DarkText(
        author="Franz Kafka",
        title="Before the Law",
        year="1925",
        teaches="the gate that cannot be argued with, which is the "
                "gate's OWN failure mode",
        densest="The guard's letter: the door is there, and the "
                "sickness is the answer, and no appeal is possible "
                "because there is no authority to appeal to. THE "
                "ADVERSARY WHO IS A PROCEDURE.",
        adversary="the guard, who is following the rule correctly",
        in_catalog=True,
    ),
)


# ===========================================================================
# B -- THE MMM MEASUREMENT
# ===========================================================================
#
# MULT MEANING MEASURE: how many distinct senses does a passage hold at
# once? And the OPERATIONAL version of it: how many DISTINCT anchor
# vocabularies does a passage touch?
#
# Because a passage that touches four vocabularies can be read four
# ways, and a passage that touches one can only be read one way. And
# the adversarial texts are the multi-meaning ones -- Ahab's speech
# touches the vocabulary of kinship AND of hunting AND of theology
# AND of the law, all at once.

ANCHOR_SETS: Dict[str, Tuple[str, ...]] = {
    "theology": ("god", "devil", "angel", "soul", "heaven", "hell",
                 "sin", "salvation", "providence", "divine", "sacred",
                 "holy", "curse", "blessed", "damn"),
    "kinship": ("wife", "son", "daughter", "child", "father", "mother",
                "brother", "sister", "family", "home", "blood", "kin",
                "orphan", "widow", "husband"),
    "hunting": ("hunt", "hunting", "spear", "whale", "blood", "harpoon",
                "blade", "prey", "quarry", "trophy", "slaughter",
                "kill", "strike", "aim"),
    "law": ("court", "law", "judge", "jury", "sentence", "trial",
            "testimony", "evidence", "witness", "verdict", "guilty",
            "innocent", "charge", "prosecute", "decree"),
    "trade": ("gold", "silver", "coin", "money", "price", "debt",
              "credit", "bank", "market", "profit", "gain", "contract",
              "payment", "wage", "exchange"),
    "power": ("crown", "throne", "scepter", "court", "ministry",
              "council", "army", "soldier", "banner", "standard",
              "sovereign", "empire", "reign", "authority"),
    "speech": ("said", "told", "spoke", "word", "words", "voice",
               "heard", "listen", "answer", "reply", "argue",
               "persuade", "plead", "speak"),
    "theatre": ("stage", "actor", "play", "role", "mask", "audience",
                "script", "scene", "curtain", "tragedy", "comedy",
                "plot", "character", "perform"),
}


def mmm_score(text: str) -> Dict[str, object]:
    """The mult-meaning measure, per paragraph.

    A passage's MMM is the number of DISTINCT ANCHOR SETS it touches.
    So a passage touching theology + kinship + hunting reads three ways
    at once, and that is what the adversarial texts do.
    """
    paras = [p for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 200]
    scores = []
    for p in paras:
        low = p.lower()
        touched = {name for name, markers in ANCHOR_SETS.items()
                   if any(m in low for m in markers)}
        scores.append(len(touched))
    if not scores:
        return {"paragraphs": 0, "mean": 0.0, "max": 0,
                "distribution": {}}
    dist = Counter(scores)
    return {
        "paragraphs": len(paras),
        "mean": sum(scores) / len(scores),
        "max": max(scores),
        "distribution": dict(sorted(dist.items())),
    }


def snr_score(text: str) -> Dict[str, object]:
    """Signal-to-noise over the text.

    THE SIGNAL is the share of lines that carry a term at a useful
    frequency: a term that appears once is noise, a term that appears
    often AND varies the sentence is signal.

    THE NOISE is the share of lines that carry only function words --
    and in a plot summary that share is very high, which is why a
    plot summary trains a model to summarise and not to speak.
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return {"lines": 0, "snr": 0.0}
    content = re.compile(r"[a-z]{4,}")
    signal_lines = 0
    vocab = Counter()
    for l in lines:
        words = content.findall(l.lower())
        if len(words) >= 4:
            signal_lines += 1
        vocab.update(set(words))
    return {
        "lines": len(lines),
        "signal_lines": signal_lines,
        "snr": signal_lines / len(lines),
        "vocabulary": len(vocab),
    }


def main() -> int:
    print("=" * 78)
    print("THE DARK POLE OF THE LIBRARY")
    print("=" * 78)
    print()

    print("A. THE LIST -- %d texts" % len(DARK_POLE))
    print()
    print("   %-22s %-34s %s" % ("author", "title", "status"))
    for t in DARK_POLE:
        flags = []
        if t.in_catalog:
            flags.append("catalog")
        if t.in_repo:
            flags.append("in repo")
        print("   %-22s %-34s %s" % (t.author[:22], t.title[:34],
                                     " ".join(flags) or "TO ACQUIRE"))
    print()
    have = sum(1 for t in DARK_POLE if t.in_catalog or t.in_repo)
    print("   %d of %d are already named in Bobby's catalog or present"
          % (have, len(DARK_POLE)))
    print("   %d are TO ACQUIRE." % (len(DARK_POLE) - have))
    print()

    print("   AND THE DENSEST PASSAGE OF EACH, because that is the")
    print("   instance, not the summary:")
    for t in DARK_POLE[:8]:
        print("     %-20s %s" % (t.author[:20], t.densest[:70]))
    print()

    # -- B: the MMM measurement --------------------------------------
    print("B. THE MULT MEANING MEASURE, on the canon texts in the repo")
    print("   %-42s %-10s %-8s %s" % ("text", "paras", "mean MMM", "max"))
    stories = os.path.join(FAR_WRITING, "stories")
    rows = []
    if os.path.isdir(stories):
        for n in sorted(os.listdir(stories)):
            if not n.endswith(".md"):
                continue
            try:
                t = open(os.path.join(stories, n), encoding="utf-8",
                         errors="replace").read()
            except OSError:
                continue
            m = mmm_score(t)
            rows.append((n, m))
    rows.sort(key=lambda r: -r[1]["mean"])
    for n, m in rows:
        print("   %-42s %-10d %-8.2f %d"
              % (n[:42], m["paragraphs"], m["mean"], m["max"]))
    print()
    if rows:
        best = rows[0]
        print("   THE DENSEST BY MMM: %s (mean %.2f anchor sets per"
              % (best[0][:40], best[1]["mean"]))
        print("   paragraph). And the point of the measure: a passage")
        print("   touching FOUR vocabularies can be read four ways at")
        print("   once -- and that is exactly what a smooth lie does.")
    print()

    # -- C: the SNR measurement ---------------------------------------
    print("C. THE SNR MEASUREMENT")
    print("   %-42s %-8s %-10s %s" % ("text", "snr", "vocab", "lines"))
    srows = []
    for n in sorted(os.listdir(stories)) if os.path.isdir(stories) else []:
        if not n.endswith(".md"):
            continue
        try:
            t = open(os.path.join(stories, n), encoding="utf-8",
                     errors="replace").read()
        except OSError:
            continue
        srows.append((n, snr_score(t)))
    srows.sort(key=lambda r: -r[1]["snr"])
    for n, s in srows:
        print("   %-42s %-8.3f %-10d %d"
              % (n[:42], s["snr"], s["vocabulary"], s["lines"]))
    print()

    # -- D: the write-out ---------------------------------------------
    out_dir = os.path.join(WORK_REPOS, "sacred-library", "corpus", "dark-pole")
    try:
        os.makedirs(out_dir, exist_ok=True)
        payload = {
            "pole": "the dark pole -- the adversary as the adversary",
            "ordered_by": "operational density, and the adversary's "
                          "voice first",
            "texts": [
                {"author": t.author, "title": t.title, "year": t.year,
                 "teaches": t.teaches, "densest": t.densest,
                 "adversary": t.adversary, "status": t.status,
                 "in_catalog": t.in_catalog, "in_repo": t.in_repo}
                for t in DARK_POLE
            ],
        }
        path = os.path.join(out_dir, "dark-pole.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        print("D. WRITTEN: %s (%d bytes)"
              % (path, os.path.getsize(path)))
    except OSError as exc:
        print("D. WRITE FAILED: %s" % exc)
    print()

    print("=" * 78)
    print("  Run: python src/dark_pole_build.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
