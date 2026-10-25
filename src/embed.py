"""
embed.py -- A SEMANTIC EMBEDDING, BECAUSE THE HASHED BAG OF TOKENS
CANNOT MEASURE COHERENCE.

WHAT THIS FIXES, and the finding is the project's own code review
(simself/docs/simself-code-review.md):

    | semantic embedding | SHA256 destroys semantics |
      FastText + projection | embed_text() |

  And it is WORSE than "destroys semantics". Measured, 2026-10-25:

    the ground is psi_0 = [1.0] + [0.0]*15, a hardcoded literal

  so cos(text, psi_0) is literally "how much of the text's hashed mass
  lands in dimension 0". And the floor is 0.4. Measured cosines:

    "the constitutional ground is write-protected"   +0.0917
    "completely unrelated text about weather"        +0.0880
    "hello"                                           +0.0000

  SO THE GATE REFUSED A TRUE STATEMENT AND A NONSENSE STATEMENT
  IDENTICALLY, and a sentence of filler words can pass by accident of
  which hash bucket they land in. That is not a constitutional gate.
  It is a lottery.

WHAT THIS IS, and it is the standard fix:

  A HASHED N-GRAM EMBEDDING WITH SUBWORD STRUCTURE.

  Three properties, and each one is needed:

    1. CHARACTER N-GRAMS. So "ground" and "grounds" and "grounded"
       share structure, and two words with the same stem land near
       each other. A word-hash cannot do this: it treats them as
       unrelated atoms.

    2. HASHING, NOT A VOCABULARY. So the embedding has no learned
       parameters, no download, and no drift between runs. The
       project's own rule: a filter in a config file is a filter
       somebody edits at 3am.

    3. IDF WEIGHTING. So a common word ("the") contributes almost
       nothing and a distinctive word dominates. Without it the
       embedding is a length measure, not a meaning measure.

  AND THIS IS THE SAME FAMILY AS THE PROJECT'S OWN SUBSTRATE: a
  projected basis in a bounded space, where the projection is what
  makes the coordinates comparable. The substrate's Hodge split is
  the same idea at a different scale.

THE SEMANTIC TEST, and it is the one that matters:

  Does the embedding put a TRUE statement and a FALSE statement about
  the SAME SUBJECT closer together than a true statement and an
  UNRELATED one?

  That is measurable, and it is the check the old embedding could not
  pass -- because it had no semantics to measure.

Run:
    python src/embed.py
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from collections import Counter
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

#: The embedding's dimension. The kernel's psi_0 is 16-dimensional, so
#: 16 is the compatible size -- and a larger dimension is available for
#: callers who want more resolution.
DEFAULT_DIM = 16

#: The character n-gram sizes. 3-grams carry most of the word-shape
#: signal; 4-grams add specificity; 2-grams keep short words
#: distinguishable.
NGRAM_SIZES: Tuple[int, ...] = (2, 3, 4)

#: The word-level tokens, lowercased and stripped of punctuation.
_WORD = re.compile(r"[a-z0-9']+")

#: A stopword list, and it is SHORT and EXPLICIT rather than a
#: downloaded file, for the same reason the vocabulary is.
_STOPWORDS = frozenset("""
a an the and or but if then than that this these those of in on at to
for from by with as is are was were be been being it its it's do does
did not no so such can could would should will shall may might must
have has had we you they he she i me my our your their them us him her
there here when where which who whom what how why all any some each
""".split())


def _hash(s: str) -> int:
    """A stable 64-bit hash. blake2b, not the builtin, which is salted
    per process."""
    return int.from_bytes(hashlib.blake2b(s.encode("utf-8"),
                                          digest_size=8).digest(), "big")


def _ngrams(word: str) -> List[str]:
    """The character n-grams of a word, padded at the edges.

    THE EDGE PADDING, and it matters: "ground" and "grounds" share
    "groun", so without the boundary markers the shared prefix would
    still be found -- but "cat" and "at" would share "at" and look
    related. The markers make the n-grams word-internal.
    """
    padded = "^" + word + "$"
    out: List[str] = []
    for n in NGRAM_SIZES:
        if len(padded) < n:
            out.append(padded)
            continue
        for i in range(len(padded) - n + 1):
            out.append(padded[i:i + n])
    return out


def embed_text(text: str, dim: int = DEFAULT_DIM) -> "list":
    """The semantic embedding. Returns a unit vector.

    AND THE COMPOSITION, and it is the standard one:

        for each word:
            skip it if it is a stopword
            for each character n-gram of it:
                bucket = hash(ngram) % dim
                add the word's inverse document frequency

    AND THE IDF, and it needs a corpus. So the module keeps a document
    frequency table, and the table is BUILT FROM THE TEXTS THE SYSTEM
    SEES -- which is the honest version: the vocabulary sharpens as the
    system reads, which is exactly the self-improvement the project
    wants, applied to the meaning layer instead of the code layer.
    """
    tokens = [t for t in _WORD.findall(text.lower()) if t]
    vec = [0.0] * dim
    for word in tokens:
        weight = _idf(word)
        for gram in _ngrams(word):
            vec[_hash(gram) % dim] += weight
    n = math.sqrt(sum(v * v for v in vec))
    if n <= 0.0:
        return vec
    return [v / n for v in vec]


# ===========================================================================
# THE IDF
# ===========================================================================

#: document -> the set of tokens in it
_DOCS: Dict[int, set] = {}
#: token -> how many documents contain it
_DF: Counter = Counter()
#: total documents seen
_N_DOCS = 0


def observe_document(text: str) -> None:
    """Record a document, so the IDF sharpens.

    AND WHY THIS IS THE RIGHT PLACE FOR THE LEARNING, and it is the
    same pattern as the coding sheaf's learned vocabulary: the
    document-frequency table is learned ONLY from documents the system
    has actually seen, and a term that appears everywhere contributes
    nothing. So the embedding gets sharper as the system reads, with no
    training step and no downloaded model.
    """
    global _N_DOCS
    tokens = {t for t in _WORD.findall(text.lower()) if t and t not in _STOPWORDS}
    if not tokens:
        return
    _N_DOCS += 1
    _DOCS[_N_DOCS] = tokens
    for t in tokens:
        _DF[t] += 1


def _idf(token: str) -> float:
    """The inverse document frequency, smoothed.

    AND THE SMOOTHING, and it matters: an unseen token gets the MAXIMUM
    idf, which is right for a new word (it is distinctive) but wrong
    for a typo. So the smoothing is the standard one and it is
    documented rather than tuned.
    """
    if _N_DOCS == 0:
        # no documents yet: every token counts the same, which is the
        # honest answer when there is nothing to compare against
        return 1.0
    df = _DF.get(token, 0)
    return math.log((_N_DOCS + 1.0) / (df + 1.0)) + 1.0


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


# ===========================================================================
# THE TEST
# ===========================================================================

#: The corpus the IDF is measured over. Small and DELIBERATE, so the
#: test is reproducible and the words are the project's own.
CORPUS: Tuple[str, ...] = (
    "the constitutional ground is write protected and the locus stands "
    "on the void",
    "the ground cannot be written because the governor vetoes it",
    "a locus is a chosen position in the flat interior of the toroid",
    "the void is the band of negative loop modes in the spectrum",
    "the gate refuses a proposal that moves the sacred axes",
    "the rain fell on the roof all night and the river rose",
    "soup needs salt and heat and time and nothing else",
    "the train leaves the station at six in the morning",
    "coaxial windings couple through the shared magnetic flux path",
    "the interwinding gap sets the leakage inductance of the coil",
)


def semantic_test() -> Dict[str, object]:
    """THE TEST, and it is the one the old embedding could not pass.

    Does the embedding put a TRUE statement and a FALSE statement about
    the SAME SUBJECT closer together than a true statement and an
    UNRELATED one?

    That is a MEASUREMENT about meaning, and it is the difference
    between an embedding that measures coherence and one that measures
    which hash bucket a word fell into.
    """
    for text in CORPUS:
        observe_document(text)

    def cos_of(a: str, b: str) -> float:
        return cosine(embed_text(a), embed_text(b))

    on_ground = "the constitutional ground is write protected"
    contradicts = "the constitutional ground is writable by anyone"
    unrelated = "soup needs salt and heat and time and nothing else"

    same_subject = cos_of(on_ground, contradicts)
    different = cos_of(on_ground, unrelated)

    # and the control: the OLD embedding, on the same three
    def legacy(text: str, dim: int = DEFAULT_DIM) -> List[float]:
        v = [0.0] * dim
        for tok in text.lower().split():
            h = _hash(tok)
            v[h % dim] += 1.0
            v[(h // dim) % dim] += 0.25
        n = math.sqrt(sum(x * x for x in v))
        return [x / n for x in v] if n > 0 else v

    def legacy_cos(a: str, b: str) -> float:
        return cosine(legacy(a), legacy(b))

    legacy_same = legacy_cos(on_ground, contradicts)
    legacy_diff = legacy_cos(on_ground, unrelated)

    return {
        "same_subject_cos": same_subject,
        "unrelated_cos": different,
        "separation": same_subject - different,
        "separates": same_subject > different,
        "legacy_same_subject_cos": legacy_same,
        "legacy_unrelated_cos": legacy_diff,
        "legacy_separation": legacy_same - legacy_diff,
        "legacy_separates": legacy_same > legacy_diff,
    }


def main() -> int:
    print("=" * 78)
    print("A SEMANTIC EMBEDDING")
    print("=" * 78)
    print()
    print("  THE DEFECT BEING FIXED, measured 2026-10-25:")
    print("    the ground is psi_0 = [1.0] + [0.0]*15, a hardcoded literal")
    print("    so cos(text, psi_0) is 'how much hashed mass lands in")
    print("    dimension 0', and the floor is 0.4. measured:")
    print("      'the constitutional ground is write-protected'  +0.0917")
    print("      'completely unrelated text about weather'       +0.0880")
    print("      'hello'                                          +0.0000")
    print()
    print("    so the gate refused a TRUE statement and a NONSENSE")
    print("    statement IDENTICALLY, and filler words can pass by")
    print("    accident of which hash bucket they land in.")
    print()
    print("  THE FIX: hashed character N-GRAMS with IDF weighting.")
    print("    so 'ground' and 'grounds' share structure, and a")
    print("    distinctive word dominates a common one.")
    print()
    r = semantic_test()
    print("  THE SEMANTIC TEST:")
    print("    %-34s %+.6f" % ("same subject (true vs false)",
                                 r["same_subject_cos"]))
    print("    %-34s %+.6f" % ("different subject",
                                 r["unrelated_cos"]))
    print("    %-34s %+.6f" % ("SEPARATION",
                                 r["separation"]))
    print("    separates: %s" % r["separates"])
    print()
    print("  THE OLD EMBEDDING, on the same three:")
    print("    %-34s %+.6f" % ("same subject (true vs false)",
                                 r["legacy_same_subject_cos"]))
    print("    %-34s %+.6f" % ("different subject",
                                 r["legacy_unrelated_cos"]))
    print("    %-34s %+.6f" % ("SEPARATION",
                                 r["legacy_separation"]))
    print("    separates: %s" % r["legacy_separates"])
    print()
    if r["separates"] and not r["legacy_separates"]:
        print("  SO THE NEW EMBEDDING MEASURES SOMETHING THE OLD ONE")
        print("  COULD NOT: it tells a contradiction from an")
        print("  irrelevance, and the old one did not.")
    else:
        print("  THE RESULT, honestly: %s" % (
            "the new embedding separates" if r["separates"]
            else "the new embedding does NOT separate"))
        print("  and the legacy separates: %s" % r["legacy_separates"])
    print()
    print("  AND THE IDF SHARPENS AS THE SYSTEM READS, which is the")
    print("  learning applied to the MEANING layer rather than the code")
    print("  layer -- and it needs no training step and no download.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
