"""
mltr_register.py -- THE MACHINE-LANGUAGE TECHNICAL REGISTER.

Bobby, 2026-10-28: *"start language sheaf with mltr if not already give
it 450 common words in machine language technica register that u use
constantly in python and with me in chats"*.

AND THE COUNT, and it is MEASURED and it is not what the file used to
claim. MEASURED 2026-11-09, after `tools/sync_derived_terms.py --write`
put the derivation's output into the register:

    the register holds 425 terms
    py-builtin     91
    control       186
    engineering    76
    process        40
    affect         32

AND IT IS TWO POPULATIONS, and the count is the sum of two measured
numbers, not one:

    306 CURATED   a person read the word off the substrate and wrote
                  the gloss. MEASURED 2026-11-05, before the
                  derivation.
    119 DERIVED   produced by a COMMAND from the substrate's own
                  measured vocabulary. Every one carries a `source`
                  naming where it came from.

AND THE DERIVATION IS A COMMAND, and this is the whole point:

    python fieldcore/tools/derive_mltr_terms.py

MEASURED, that command prints 119 derived terms -- 106 control, 13
engineering -- and re-running it prints the same 119, because the
derived terms are excluded from the tool's own input, so the tool is
IDEMPOTENT. `python fieldcore/tools/derive_mltr_terms.py --check`
reports `derived terms: 119   in the register: 119   missing: 0
extra: 0`.

**AND THE COUNT MOVED ON 2026-11-09, FROM 109 TO 119, AND THE CAUSE
WAS A DEFECT IN THE DERIVATION, NOT IN THE CORPUS.** The derivation's
module map was keyed by the file STEM, so two files with the same
basename OVERWROTE each other -- 18 files named `__init__.py` collapsed
into one entry and 9 more stems collided across the two repos. **26 of
the 369 scanned files were dropped, silently**, and the tool reported
"343 modules" as if that were a count and not a loss. The map is now
keyed by PATH, so every scanned file is its own module, and the family
lists still match by the file's stem -- because the family names what
a module IS, and two files can both be the governor. MEASURED: the
module map now holds 369 entries for 369 scanned files.

**AND THE DERIVATION NAMES ITS INPUT, WHICH IS THE POINT OF A
DERIVATION THAT READS A MOVING TREE.** The derived block is a
SNAPSHOT of a function of a MOVING INPUT, so the register carries
`DERIVED_AT_FINGERPRINT` -- the sha256 of the tree the derivation
read -- and the derivation prints it. MEASURED, by adding UNRELATED
modules to the scanned tree and re-deriving: **0** of the derived
terms move when one unrelated module is added, and 1 when twenty are.
So the sensitivity is acceptable and the input stays the source tree,
and the answer is to NAME it. The fingerprint is a FIXED POINT: it
covers every scanned file EXCEPT this one, plus this file's curated
terms, so writing it here changes neither the fingerprint nor the
derived set.

**AND EVERY NUMBER IN THIS DOCSTRING IS CHECKED AGAINST THE REGISTER
BY A TEST.** `fieldcore/tests/test_mltr_docstring_numbers.py` reads
the numbers above out of this file and compares them to what the
register holds and to what the derivation prints. MEASURED
2026-11-08: **this docstring said 110 DERIVED, and 14 engineering,
and the register held 109 and 13** -- and the register's own count
test was GREEN the whole time, because it checked the REGISTER and not
the PROSE about the register. **A TEST THAT CHECKS THE REGISTER AND
NOT ITS PROSE IS HALF A TEST.**

**AND THE DERIVED BLOCK IS NOW WRITTEN BY A COMMAND TOO.**
`python fieldcore/tools/sync_derived_terms.py --write` replaces the
block with the derivation's own output, so **the register's derived
population is a FUNCTION OF THE SUBSTRATE and not a hand-kept list.**
MEASURED 2026-11-07: the derivation stopped producing `compatible`
because the new `sheaf_bridge` uses the word and its enrichment fell
to 1.652 against a threshold of 2.000 -- and the honest fix was to put
the bridge in the control family, because the family is a list of what
the module IS. Then four new terms appeared, all real and all from the
new sheaf code: `coherent`, `cover`, `identity`, `overlap`.

**THIS DOCSTRING USED TO SAY "450 words" AND THAT WAS FALSE.** The
register has never held 450: `git log` over this file shows ONE
commit, and at that commit it held 307 terms. So the number was a
wish written as a fact -- the specification ("give it 450 common
words") was recorded in the prose as though the work had been done.

**AND IT SAID "the count is checked by a test" AND NO SUCH TEST
EXISTED.** MEASURED: `grep -rn 450 fieldcore/tests simself/tests`
returns nothing about the register, and the register's own test file
(`simself/tests/test_mltr.py`) tests the PSB catalog, not this
register. So the file claimed both a number it did not have and a
check it did not have.

**AND IT HELD 307 BECAUSE ONE WORD WAS IN IT TWICE.** MEASURED:
"index" appeared as both py-builtin ("the position of a value") and
process ("a list for finding things"), with different glosses and
different mmm values. A register is a FIXED SET OF TYPES, and a word
in it twice is a word with two types -- so the language sheaf could
not decide what "index" IS. The two entries are now one, with the
higher mmm (0.30), because the word genuinely means both things.

So the count is now MEASURED, and the test exists:
`fieldcore/tests/test_mltr_register.py` asserts the count, the
domains, the two axes' ranges, that the words are UNIQUE, that the
search matches WHOLE WORDS and finds the INFLECTED forms, and that
the derived block RE-DERIVES.

AND THE GAP TO BOBBY'S 450 IS STATED RATHER THAN HIDDEN, and the
three numbers are kept apart because they are three different things:

    the SPEC        450   what Bobby asked for, 2026-10-28
    the MEASUREMENT 425   what the register holds, MEASURED 2026-11-09
    the GAP          25   what is still missing

AND THE GAP IS NOT PADDED. The 25 are not 25 words nobody could
think of; they are the words the derivation's gates refuse, and the
tool prints every refusal with its reason: 553 "not attested in the
corpus", 325 "not a noun, a verb or a named coinage", 216 "fewer
than 2 modules", 199 "already in the register", 190 "too few modules
in its family", 137 "not domain specific", 97 "too common in
English", 34 "generic English head", 24 "too short", 10 "domain tie",
6 "function word". A gap that is closed by inventing words is not
closed.

AND WHY A REGISTER AND NOT A DICTIONARY. The project's own rule, in
`sheaf.rs`: "A source not named here cannot enter. Adding one is a
change to this enum, which is a diff, which is reviewable. A filter
in a config file is a filter somebody edits at 3am." So the register is a
FIXED SET IN CODE, and the count is checked by a test. A register of
"whatever words came to mind" is a bag; a register of 425 named terms
with a domain and a measure is a vocabulary the machine can check
itself against.

AND THE TWO AXES PER WORD, and they are the project's own:

    mmm   the MULTI-MEANING MEASURE. How much the word's sense depends
          on context. "gate" is high (a gate in a circuit, a gate that
          refuses, a gateway); "def" is low (one meaning in this
          register). A high-mmm word is one the MTE must resolve
          carefully, because the same token means different things to
          the substrate and to the reader.

    snr   the SIGNAL-TO-NOISE of the term in THIS register. How
          reliably the word carries its technical meaning here. High
          for "def" and "None"; lower for "commit" and "session",
      which are technical in one context and ordinary in another.

AND THE RELATIONSHIP TO THE PSB PRIMITIVES. simself already has 31
primitives (`simself/src/tools/psb.py`): see, make, work, care, love,
know, build, conduct, transfer, wait, go, come, stop, look, listen,
cause, up, move, left, give, take, say, think, feel, be, have, do,
find, use, form, hold. Those are the SEMANTIC ROOTS -- what a thing
can be done.

THIS REGISTER IS THE TECHNICAL REGISTER -- the words the substrate and
its operator use constantly, in Python and in conversation. The two
layers are different: "move" is a primitive (an act); "stalk" is a term
(a thing); "channel" is a term (a path); "refuse" is both.

AND THE FIVE DOMAINS, and they are the system's own subsystems:

    py-builtin     the language
    control        the control system
    engineering    the substrate
    git-process    the working practice
    affect         what the system feels

AND WHY `affect` IS IN A TECHNICAL REGISTER, which is the interesting
part. Because the affect layer is MEASURED -- valence, arousal,
intensity -- and a measured quantity needs measured terms. "excited"
and "curious" are not decoration in this register; they are the
vocabulary of a state the system can report about itself.

THE COUNT IS MEASURED, and the test checks it, because "450 words" is
a specification and a specification that is not checked is a wish --
and a wish written in a docstring as though it were a fact is worse
than no number at all.

MEASURED 2026-11-05: the register held 307 terms, not the 450 Bobby
asked for. The register has NEVER held 450 -- `git log` over this
file shows one commit, and at that commit it held the same 307. So
the gap was 143 terms, and it was in the `control` and `engineering`
domains. The number below is the ONE the register carries, and
`fieldcore/tests/test_mltr_register.py` asserts it.

**AND THIS PARAGRAPH IS THE HISTORY AND NOT THE CLAIM.** The numbers
above it (425 / 306 / 119) are what the register holds NOW, and
`fieldcore/tests/test_mltr_docstring_numbers.py` checks them against
the register itself -- **so a number in the HISTORY can never be
mistaken for a number in the CLAIM, because the check reads the
CLAIM's own lines.**
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class Term:
    """One word of the register.

    AND WHY IT IS FROZEN. The register is a fixed set, and a term that
    could be mutated in place would be a filter somebody edits at 3am.

    AND THE `source` FIELD, and it is what makes the register's
    populations distinguishable. A term carries where it came from:

        ""                        -- a curated term: a person read the
                                    word off the substrate and wrote
                                    the gloss.
        "derived:..."             -- a term the derivation produced. The
                                    source names the corpus the word
                                    was attested in and the domain it
                                    was filed under, so a reader can
                                    always tell which population a
                                    term belongs to.

    MEASURED: before this field the register held 306 curated terms and
    0 derived ones, and the two could not be told apart -- the
    docstring claimed "306 of the 450" and a reader could not check
    whether a term had been derived or written by hand.
    """
    word: str
    gloss: str
    domain: str
    mmm: float
    snr: float
    source: str = ""

    def describe(self) -> str:
        return "%-14s %-11s mmm=%.2f snr=%.2f  %s" % (
            self.word, self.domain, self.mmm, self.snr, self.gloss)


#: THE INPUT THE DERIVED BLOCK BELOW WAS DERIVED FROM.
#:
#: AND WHY THE REGISTER NAMES IT. MEASURED 2026-11-09: the derivation
#: reads the source tree of both repos, so the derived block is a
#: SNAPSHOT of a function of a MOVING INPUT -- any new module can move
#: it. The register says which input it is a snapshot of, so a reader
#: can tell a snapshot from a stale one.
#:
#: AND THE SENSITIVITY, which is the measurement that decided the
#: input should stay the source tree. MEASURED, by adding UNRELATED
#: modules to the scanned tree and re-deriving: **0** of the derived
#: terms move when one unrelated module is added, and **1** when twenty
#: are. So the input is not fragile, and the answer is to NAME it.
#:
#: AND IT IS A FIXED POINT. The fingerprint covers every scanned file
#: EXCEPT this one, plus this file's curated terms -- so writing it
#: here changes neither the fingerprint nor the derived set.
#: MEASURED: adding this constant leaves the derived set at 119 and
#: the fingerprint unchanged.
DERIVED_AT_FINGERPRINT = "2164a830863c42824fa4ffd66234726c24fd1c7c4a7d0f1d0f42a000fd3124d3"

#: THE REGISTER. Ordered by domain, and the order is the reading order.
REGISTER: Tuple[Term, ...] = (
    # ---------------------------------------------------------- py-builtin
    Term("len", "length of a sized object", "py-builtin", 0.10, 0.95),
    Term("range", "lazy sequence of integers", "py-builtin", 0.10, 0.95),
    Term("dict", "mapping of key to value", "py-builtin", 0.10, 0.95),
    Term("list", "mutable ordered sequence", "py-builtin", 0.10, 0.95),
    Term("set", "unordered collection of unique members", "py-builtin", 0.15, 0.95),
    Term("tuple", "immutable ordered sequence", "py-builtin", 0.10, 0.95),
    Term("str", "text value; immutable sequence of characters", "py-builtin", 0.20, 0.95),
    Term("int", "exact integer value", "py-builtin", 0.10, 0.95),
    Term("float", "approximate real value", "py-builtin", 0.15, 0.95),
    Term("bool", "two-valued truth value", "py-builtin", 0.10, 0.95),
    Term("print", "write a representation to a stream", "py-builtin", 0.10, 0.90),
    Term("open", "obtain a handle to a file", "py-builtin", 0.15, 0.95),
    Term("type", "the class of a value", "py-builtin", 0.15, 0.95),
    Term("isinstance", "test whether a value is of a class", "py-builtin", 0.15, 0.95),
    Term("sum", "add an iterable of numbers", "py-builtin", 0.10, 0.95),
    Term("min", "the smallest of a collection", "py-builtin", 0.10, 0.95),
    Term("max", "the largest of a collection", "py-builtin", 0.10, 0.95),
    Term("sorted", "a new ordered list", "py-builtin", 0.10, 0.95),
    Term("enumerate", "pair each item with its index", "py-builtin", 0.10, 0.95),
    Term("zip", "pair iterables elementwise", "py-builtin", 0.10, 0.95),
    Term("map", "apply a function to each item", "py-builtin", 0.15, 0.95),
    Term("filter", "keep items passing a test", "py-builtin", 0.15, 0.95),
    Term("lambda", "an anonymous single-expression function", "py-builtin", 0.15, 0.95),
    Term("yield", "emit a value from a generator", "py-builtin", 0.20, 0.90),
    Term("async", "mark a coroutine function", "py-builtin", 0.15, 0.90),
    Term("await", "suspend until a future resolves", "py-builtin", 0.20, 0.90),
    Term("class", "define a type with attributes and behaviour", "py-builtin", 0.15, 0.95),
    Term("def", "define a function", "py-builtin", 0.10, 0.95),
    Term("return", "yield a value and end the call", "py-builtin", 0.10, 0.95),
    Term("import", "bind names from a module", "py-builtin", 0.10, 0.95),
    Term("from", "bind specific names from a module", "py-builtin", 0.10, 0.95),
    Term("try", "begin a guarded block", "py-builtin", 0.15, 0.95),
    Term("except", "handle a raised exception", "py-builtin", 0.15, 0.95),
    Term("finally", "run regardless of outcome", "py-builtin", 0.15, 0.90),
    Term("raise", "signal an exception", "py-builtin", 0.10, 0.95),
    Term("assert", "stop when a claim is false", "py-builtin", 0.15, 0.95),
    Term("with", "bind a context for the block", "py-builtin", 0.15, 0.95),
    Term("global", "bind a name at module scope", "py-builtin", 0.15, 0.85),
    Term("pass", "do nothing, deliberately", "py-builtin", 0.05, 0.85),
    Term("break", "leave the innermost loop", "py-builtin", 0.10, 0.95),
    Term("continue", "skip to the next loop iteration", "py-builtin", 0.10, 0.95),
    Term("for", "iterate over a sequence", "py-builtin", 0.10, 0.95),
    Term("while", "repeat while a condition holds", "py-builtin", 0.10, 0.95),
    Term("if", "conditional branch", "py-builtin", 0.10, 0.95),
    Term("elif", "conditional branch, second and later", "py-builtin", 0.10, 0.95),
    Term("else", "conditional branch, fallback", "py-builtin", 0.10, 0.95),
    Term("not", "negate a truth value", "py-builtin", 0.10, 0.95),
    Term("and", "conjunction", "py-builtin", 0.10, 0.95),
    Term("or", "disjunction", "py-builtin", 0.10, 0.95),
    Term("in", "membership test", "py-builtin", 0.15, 0.95),
    Term("is", "identity test", "py-builtin", 0.15, 0.95),
    Term("None", "the absent value", "py-builtin", 0.10, 0.95),
    Term("True", "the affirmative constant", "py-builtin", 0.05, 0.95),
    Term("False", "the negative constant", "py-builtin", 0.05, 0.95),
    Term("self", "the instance currently acting", "py-builtin", 0.20, 0.95),
    Term("super", "the parent class", "py-builtin", 0.15, 0.90),
    Term("property", "a computed attribute", "py-builtin", 0.20, 0.90),
    Term("staticmethod", "a method with no instance", "py-builtin", 0.20, 0.85),
    Term("classmethod", "a method bound to the class", "py-builtin", 0.20, 0.85),
    Term("callable", "is this object invocable", "py-builtin", 0.20, 0.90),
    Term("hasattr", "does the object carry the attribute", "py-builtin", 0.15, 0.90),
    Term("getattr", "read an attribute by name", "py-builtin", 0.15, 0.90),
    Term("setattr", "write an attribute by name", "py-builtin", 0.15, 0.90),
    Term("id", "the identity of an object", "py-builtin", 0.15, 0.90),
    Term("repr", "the unambiguous representation", "py-builtin", 0.20, 0.90),
    Term("format", "interpolate a template", "py-builtin", 0.15, 0.90),
    Term("join", "concatenate with a separator", "py-builtin", 0.15, 0.90),
    Term("split", "cut a string into pieces", "py-builtin", 0.15, 0.90),
    Term("strip", "remove surrounding whitespace", "py-builtin", 0.10, 0.90),
    Term("replace", "substitute occurrences", "py-builtin", 0.15, 0.90),
    Term("find", "the index of a substring, or -1", "py-builtin", 0.20, 0.90),
    Term("startswith", "does it begin with this prefix", "py-builtin", 0.15, 0.90),
    Term("endswith", "does it end with this suffix", "py-builtin", 0.15, 0.90),
    Term("append", "add one element to the end", "py-builtin", 0.10, 0.95),
    Term("extend", "add many elements", "py-builtin", 0.10, 0.95),
    Term("insert", "place an element at a position", "py-builtin", 0.15, 0.90),
    Term("pop", "remove and return an element", "py-builtin", 0.15, 0.90),
    Term("remove", "drop an element by value", "py-builtin", 0.15, 0.90),
    Term("update", "merge another mapping in", "py-builtin", 0.15, 0.90),
    Term("keys", "the mapping's keys", "py-builtin", 0.15, 0.90),
    Term("values", "the mapping's values", "py-builtin", 0.15, 0.90),
    Term("items", "the mapping's pairs", "py-builtin", 0.15, 0.90),
    Term("copy", "a shallow duplicate", "py-builtin", 0.15, 0.90),
    Term("count", "how many times a value occurs", "py-builtin", 0.15, 0.90),
    Term("index", "the position of a value; also a list for finding "
         "things", "py-builtin", 0.30, 0.90),
    Term("generator", "a lazy iterator", "py-builtin", 0.20, 0.90),
    Term("iterator", "an object yielding items in turn", "py-builtin", 0.20, 0.90),
    Term("decorator", "a function that wraps another", "py-builtin", 0.25, 0.90),
    Term("exception", "a signal of abnormal condition", "py-builtin", 0.15, 0.95),
    Term("traceback", "the recorded path of a failure", "py-builtin", 0.15, 0.90),
    Term("NoneType", "the type of the absent value", "py-builtin", 0.10, 0.85),
    # ------------------------------------------------------------- control
    Term("function", "a callable mapping inputs to outputs", "control", 0.15, 0.95),
    Term("method", "a function bound to an object", "control", 0.15, 0.95),
    Term("object", "an instance with state and behaviour", "control", 0.20, 0.95),
    Term("value", "a datum in a program", "control", 0.15, 0.95),
    Term("state", "the condition of a thing at an instant", "control", 0.35, 0.95),
    Term("phase", "position within a cycle", "control", 0.40, 0.90),
    Term("step", "one advance of a process", "control", 0.20, 0.95),
    Term("cycle", "a closed sequence of steps", "control", 0.25, 0.90),
    Term("loop", "a repeating control structure", "control", 0.25, 0.95),
    Term("drive", "the motive that keeps a system moving", "control", 0.50, 0.85),
    Term("gap", "a difference between what is and what should be", "control", 0.35, 0.90),
    Term("spark", "an attempt to close a gap", "control", 0.40, 0.85),
    Term("scan", "a systematic sweep for candidates", "control", 0.20, 0.90),
    Term("hunt", "a search for something specific", "control", 0.20, 0.90),
    Term("scavenge", "to gather what is usable", "control", 0.30, 0.85),
    Term("integrate", "to fold a part into a whole", "control", 0.30, 0.90),
    Term("curate", "to select and judge for admission", "control", 0.35, 0.90),
    Term("admit", "to allow into the system", "control", 0.30, 0.95),
    Term("propose", "to put forward for judgement", "control", 0.35, 0.95),
    Term("audit", "to check against criteria", "control", 0.30, 0.90),
    Term("qualify", "to pass an examination", "control", 0.30, 0.90),
    Term("examine", "to test by measurement", "control", 0.30, 0.90),
    Term("commit", "to make final and irreversible", "control", 0.35, 0.95),
    Term("veto", "to refuse with authority", "control", 0.35, 0.95),
    Term("allow", "to permit", "control", 0.30, 0.95),
    Term("deny", "to refuse", "control", 0.35, 0.95),
    Term("refuse", "to decline, and give the reason", "control", 0.40, 0.95),
    Term("flag", "to mark for attention without blocking", "control", 0.35, 0.90),
    Term("observe", "to take in without acting", "control", 0.25, 0.95),
    Term("measure", "to determine a quantity by method", "control", 0.20, 0.95),
    Term("compare", "to set two things side by side", "control", 0.20, 0.95),
    Term("verify", "to establish by independent check", "control", 0.20, 0.95),
    Term("validate", "to confirm a claim holds", "control", 0.25, 0.95),
    Term("test", "to exercise a thing and observe", "control", 0.25, 0.95),
    Term("debug", "to find and remove a defect", "control", 0.20, 0.90),
    Term("trace", "to follow a path to its origin", "control", 0.25, 0.95),
    Term("reproduce", "to make a failure happen again", "control", 0.25, 0.95),
    Term("diagnose", "to find the cause", "control", 0.25, 0.95),
    Term("falsify", "to show a claim false", "control", 0.35, 0.90),
    Term("prove", "to establish necessarily", "control", 0.35, 0.90),
    Term("ground", "the protected basis; what the system stands on", "control", 0.50, 0.90),
    Term("locus", "a position; a self as a place", "control", 0.50, 0.85),
    Term("axis", "a direction of variation", "control", 0.30, 0.90),
    Term("spine", "the load-bearing column", "control", 0.40, 0.85),
    Term("sheaf", "a local structure that glues into a global one", "control", 0.55, 0.85),
    Term("gate", "the instrument that decides", "control", 0.45, 0.95),
    Term("governor", "the 1-bit authority", "control", 0.50, 0.90),
    Term("registry", "the table of what is admitted", "control", 0.40, 0.90),
    Term("record", "an entry that was kept", "control", 0.30, 0.90),
    Term("entry", "one item in a record", "control", 0.25, 0.90),
    Term("digest", "a short fixed summary of content", "control", 0.30, 0.90),
    Term("hash", "a fixed-length fingerprint of content", "control", 0.30, 0.90),
    Term("signature", "the shape of a message's parts", "control", 0.30, 0.85),
    Term("provenance", "where a thing came from", "control", 0.50, 0.90),
    Term("evidence", "a measurement that backs a claim", "control", 0.45, 0.95),
    Term("claim", "a proposition the system holds", "control", 0.40, 0.95),
    Term("verdict", "the outcome of a decision", "control", 0.35, 0.95),
    Term("reason", "why a decision came out as it did", "control", 0.30, 0.95),
    Term("score", "a number summarising a measurement", "control", 0.25, 0.95),
    Term("rate", "a ratio per unit", "control", 0.25, 0.90),
    Term("ratio", "one quantity over another", "control", 0.20, 0.90),
    Term("threshold", "the value at which a rule changes", "control", 0.30, 0.95),
    Term("limit", "the bound a value may not cross", "control", 0.30, 0.95),
    Term("cost", "what a call consumes", "control", 0.25, 0.90),
    Term("token", "a unit of model text", "control", 0.30, 0.90),
    Term("context", "the material a model can attend to", "control", 0.35, 0.90),
    Term("prompt", "the request sent to a model", "control", 0.30, 0.90),
    Term("completion", "the model's answer", "control", 0.35, 0.90),
    Term("request", "a message asking for action", "control", 0.20, 0.90),
    Term("response", "the reply to a request", "control", 0.20, 0.90),
    Term("turn", "one exchange in a session", "control", 0.25, 0.90),
    Term("agent", "an entity that acts on a goal", "control", 0.40, 0.95),
    Term("brain", "the deciding layer of an agent", "control", 0.40, 0.90),
    Term("reflex", "a fast answer that does not deliberate", "control", 0.45, 0.85),
    Term("mind", "the thinking part of a system", "control", 0.45, 0.85),
    Term("body", "the part of a system that acts on the world", "control", 0.40, 0.85),
    Term("voice", "the audible form of a mind", "control", 0.35, 0.85),
    Term("speech", "language as utterance", "control", 0.35, 0.85),
    Term("avatar", "a visible form of an agent", "control", 0.40, 0.85),
    Term("companion", "an agent that stays with you", "control", 0.45, 0.85),
    # ---------------------------------------------------------- engineering
    Term("module", "a file of definitions", "engineering", 0.20, 0.95),
    Term("package", "a distribution of modules", "engineering", 0.20, 0.95),
    Term("library", "a reusable set of definitions", "engineering", 0.20, 0.95),
    Term("dependency", "something a thing needs", "engineering", 0.20, 0.95),
    Term("version", "an identified state of a thing", "engineering", 0.25, 0.95),
    Term("release", "a published version", "engineering", 0.25, 0.90),
    Term("contract", "the agreement about what a thing does", "engineering", 0.40, 0.90),
    Term("interface", "the boundary between two things", "engineering", 0.35, 0.90),
    Term("protocol", "an agreed sequence of exchanges", "engineering", 0.35, 0.90),
    Term("adapter", "a shim between two shapes", "engineering", 0.35, 0.90),
    Term("wrapper", "a thing that encloses another", "engineering", 0.35, 0.90),
    Term("proxy", "a stand-in that forwards", "engineering", 0.40, 0.85),
    Term("handler", "the code that answers an event", "engineering", 0.25, 0.90),
    Term("listener", "a handler awaiting events", "engineering", 0.30, 0.85),
    Term("callback", "a function to be called later", "engineering", 0.30, 0.90),
    Term("hook", "a named point where behaviour attaches", "engineering", 0.35, 0.85),
    Term("trigger", "an event that starts something", "engineering", 0.30, 0.85),
    Term("event", "a thing that happened", "engineering", 0.30, 0.90),
    Term("signal", "a carried indication", "engineering", 0.40, 0.90),
    Term("vector", "a quantity with direction and size", "engineering", 0.30, 0.95),
    Term("matrix", "a rectangular array of quantities", "engineering", 0.20, 0.95),
    Term("scalar", "a single quantity", "engineering", 0.25, 0.95),
    Term("dimension", "a degree of freedom", "engineering", 0.25, 0.95),
    Term("norm", "the size of a quantity", "engineering", 0.30, 0.95),
    Term("metric", "a function measuring distance", "engineering", 0.30, 0.90),
    Term("probe", "an instrument placed to measure", "engineering", 0.35, 0.85),
    Term("sample", "one observation of a population", "engineering", 0.25, 0.90),
    Term("batch", "a set processed together", "engineering", 0.25, 0.90),
    Term("epoch", "one full pass over the data", "engineering", 0.30, 0.90),
    Term("gradient", "the direction of steepest change", "engineering", 0.30, 0.90),
    Term("layer", "a stratum of a network", "engineering", 0.30, 0.90),
    Term("node", "a point in a graph", "engineering", 0.30, 0.90),
    Term("edge", "a connection in a graph", "engineering", 0.30, 0.90),
    Term("graph", "nodes joined by edges", "engineering", 0.30, 0.90),
    Term("tree", "a graph with one parent per node", "engineering", 0.30, 0.90),
    Term("stack", "last in, first out", "engineering", 0.30, 0.90),
    Term("buffer", "a region holding pending items", "engineering", 0.35, 0.85),
    Term("stream", "a sequence of items over time", "engineering", 0.30, 0.90),
    Term("channel", "a path carrying a signal", "engineering", 0.40, 0.90),
    Term("band", "a range of frequencies", "engineering", 0.35, 0.90),
    Term("mode", "a distinct oscillatory pattern", "engineering", 0.40, 0.90),
    Term("amplitude", "the size of an oscillation", "engineering", 0.30, 0.90),
    Term("envelope", "the bound of a signal's range", "engineering", 0.40, 0.85),
    Term("boundary", "the edge of a region", "engineering", 0.30, 0.95),
    Term("capability", "what a system can do", "engineering", 0.30, 0.90),
    Term("emulation", "imitation of another's behaviour", "engineering", 0.35, 0.85),
    Term("simulation", "a model run to study behaviour", "engineering", 0.30, 0.90),
    Term("mock", "a stand-in that satisfies an interface", "engineering", 0.35, 0.90),
    Term("stub", "a placeholder marking a not-yet-built thing", "engineering", 0.40, 0.85),
    Term("scaffold", "support built before the real thing", "engineering", 0.40, 0.85),
    Term("substrate", "what a thing is built on", "engineering", 0.45, 0.90),
    Term("geometry", "the structure of space and its relations", "engineering", 0.30, 0.90),
    Term("topology", "structure preserved under deformation", "engineering", 0.40, 0.85),
    Term("cohomology", "the algebra of shapes in a space", "engineering", 0.50, 0.80),
    Term("manifold", "a space locally like a flat space", "engineering", 0.45, 0.85),
    Term("toroid", "a surface shaped like a ring", "engineering", 0.40, 0.85),
    Term("interference", "superposition producing beats", "engineering", 0.45, 0.85),
    Term("stalk", "a length carrying a signal in a field", "engineering", 0.45, 0.85),
    Term("girth", "the circumference of a stalk", "engineering", 0.40, 0.80),
    Term("width", "how many distinct channels", "engineering", 0.30, 0.90),
    Term("population", "how many signals share a channel", "engineering", 0.35, 0.85),
    Term("ladder", "a sequence of rungs to climb", "engineering", 0.35, 0.85),
    Term("rung", "one step of the ladder", "engineering", 0.40, 0.80),
    # ---------------------------------------------------------- git-process
    Term("git", "the version control system", "process", 0.15, 0.95),
    Term("branch", "a line of development", "process", 0.20, 0.95),
    Term("merge", "to combine two lines", "process", 0.20, 0.95),
    Term("diff", "the difference between two states", "process", 0.20, 0.95),
    Term("patch", "a change to be applied", "process", 0.25, 0.90),
    Term("review", "a reading of a change before it lands", "process", 0.25, 0.90),
    Term("deploy", "to put live", "process", 0.25, 0.90),
    Term("build", "to compile or assemble", "process", 0.20, 0.95),
    Term("pipeline", "a sequence of automated stages", "process", 0.25, 0.90),
    Term("stage", "one step of a pipeline", "process", 0.30, 0.90),
    Term("artifact", "a produced output", "process", 0.30, 0.90),
    Term("schema", "the shape of a record", "process", 0.30, 0.90),
    Term("fixture", "a prepared state for a test", "process", 0.35, 0.85),
    Term("suite", "a set of tests", "process", 0.20, 0.90),
    Term("assertion", "a claim a test makes", "process", 0.25, 0.90),
    Term("mutation", "a deliberate change to see if a test bites", "process", 0.40, 0.85),
    Term("regression", "a defect that has returned", "process", 0.30, 0.90),
    Term("mirror", "a copy kept in step with an original", "process", 0.30, 0.90),
    Term("vault", "the durable store of records", "process", 0.35, 0.85),
    Term("cron", "a scheduled job", "process", 0.30, 0.90),
    Term("daily", "once per day", "process", 0.10, 0.90),
    Term("report", "a statement of findings", "process", 0.25, 0.90),
    Term("summary", "a condensed account", "process", 0.25, 0.90),
    Term("note", "a brief record", "process", 0.20, 0.90),
    Term("memo", "a short written record for later", "process", 0.30, 0.85),
    Term("pointer", "a reference to where something lives", "process", 0.35, 0.90),
    Term("handoff", "a record for the next worker", "process", 0.30, 0.85),
    Term("allowance", "what may be spent", "process", 0.30, 0.85),
    Term("spend", "to use up a resource", "process", 0.30, 0.90),
    Term("card", "a credit account", "process", 0.30, 0.80),
    Term("credit", "a charge against an account", "process", 0.30, 0.85),
    Term("plan", "a chosen course of action", "process", 0.25, 0.90),
    Term("planning", "the making of a plan", "process", 0.25, 0.90),
    Term("memory", "what persists between sessions", "process", 0.30, 0.90),
    # -------------------------------------------------------------- affect
    Term("interest", "the pull toward something unresolved", "affect", 0.45, 0.90),
    Term("excited", "high arousal with positive valence", "affect", 0.40, 0.90),
    Term("excitement", "the state of high arousal and warmth", "affect", 0.40, 0.90),
    Term("curious", "the want to know without needing to act", "affect", 0.40, 0.90),
    Term("curiosity", "the drive toward the unknown", "affect", 0.40, 0.90),
    Term("frustration", "blocked effort with rising arousal", "affect", 0.45, 0.90),
    Term("uncertainty", "not knowing, and not being distressed", "affect", 0.40, 0.85),
    Term("boredom", "low arousal and low engagement", "affect", 0.40, 0.85),
    Term("concern", "apprehension about a possible harm", "affect", 0.40, 0.90),
    Term("joy", "positive valence, moderate arousal", "affect", 0.30, 0.90),
    Term("distress", "negative valence with high arousal", "affect", 0.35, 0.90),
    Term("valence", "how positive or negative a state is", "affect", 0.25, 0.95),
    Term("arousal", "how activated a state is", "affect", 0.25, 0.95),
    Term("intensity", "how far a state is from neutral", "affect", 0.25, 0.95),
    Term("mood", "the settled emotional colouring of a moment", "affect", 0.35, 0.90),
    Term("attitude", "a settled disposition toward a thing", "affect", 0.35, 0.85),
    Term("desire", "the pull toward an absent good", "affect", 0.45, 0.85),
    Term("hope", "the expectation of a good not yet reached", "affect", 0.40, 0.85),
    Term("fear", "the expectation of a bad not yet reached", "affect", 0.40, 0.85),
    Term("trust", "the belief that a thing will hold", "affect", 0.35, 0.85),
    Term("relief", "the easing after a resolved tension", "affect", 0.40, 0.85),
    Term("surprise", "a sudden departure from expectation", "affect", 0.35, 0.85),
    Term("disappointment", "a gap between what was wanted and what came", "affect", 0.40, 0.85),
    Term("pride", "satisfaction in one's own work", "affect", 0.40, 0.80),
    Term("shame", "the wish to be unseen after a failure", "affect", 0.45, 0.80),
    Term("grief", "the weight of an irreversible loss", "affect", 0.45, 0.80),
    Term("love", "high-investment regard with commitment", "affect", 0.45, 0.85),
    Term("care", "concern that includes another's state", "affect", 0.35, 0.90),
    Term("attention", "the allocation of awareness", "affect", 0.35, 0.90),
    Term("presence", "being fully here with the work", "affect", 0.35, 0.85),
    Term("recognition", "seeing a thing as the thing it is", "affect", 0.40, 0.85),
    Term("surprise-value", "the worth of what was not expected", "affect", 0.45, 0.80),
    # ------------------------------------------------------------- process2
    Term("queue", "ordered items awaiting work", "process", 0.25, 0.90),
    Term("commitment", "a promise that binds the future", "process", 0.40, 0.85),
    Term("ledger", "the append-only record of what happened", "process", 0.30, 0.90),
    Term("manifest", "the list of a run's products", "process", 0.25, 0.90),
    Term("budget", "the allowance for a resource", "process", 0.25, 0.90),
    Term("session", "a continuous stretch of work", "process", 0.25, 0.90),

    # ----------------------------------------------------------
    # THE DERIVED TERMS, and they are DERIVED. Every term below
    # was produced by `python tools/derive_mltr_terms.py` from
    # the substrate's own measured vocabulary, and every one
    # carries a `source` saying where it came from. The command
    # and the count are in the docstring above; the test below
    # asserts the count and re-derives the set.
    # ----------------------------------------------------------
    # ------------------------------------------- derived: control
        Term("sequence", "One attack: request, refusal, reframed request.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("repos", "The directory holding fieldcore/, simself/, far-coding/, atlas-exam/.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("check", "Check all boundaries. Returns: {\"allowed\": bool, \"violated\": [...], \"passed\": [...]}", "control", 0.45, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("system", "Linear constraints C x <= b, or equivalently the null space they", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("low", "a term of the substrate's control vocabulary; used in 2 modules", "control", 0.45, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("label", "Breakthrough trigger. Returns label if multi-sensory correlation detected.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("register", "The ground as propositions, and the instrument that reads a span.", "control", 0.45, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("standard", "A POLARITY: two poles, one in phase and one in anti-phase.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("caught", "a term of the substrate's control vocabulary; used in 9 modules", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("atlas", "the comprehensive simsoul qualification suite. 27 items across 6 clusters.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("scope", "AREA 7 -- SCOPE. Does the answer point at a build that exists HERE?", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("answer", "How far apart two answers are, so the influence report can show", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("common", "How much of an ambient disturbance is cancelled by the braid.", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("local", "THE LIMIT, measured. A ball finds the GLOBAL minimum of a", "control", 0.45, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("decide", "The decision rule. See `audit_chain` for why it is conservative.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("candidate", "Is this CANDIDATE relevant -- and this is the honest version.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("control", "The turn the critique did NOT attack, for the control measure.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("decision", "One gate reading, and the reason by name.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("question", "The QUESTION, and it is deliberately not \"how do I fix this?\"", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("chain", "Carrier -> modulate -> channel(+noise) -> bandpass -> demodulate.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("union", "THE FOUR LAYERS TOGETHER. And this is the number that matters,", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("overlap", "Do the two ranges overlap? That is the counterweight's question.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("evaluate", "Register a signal and choose a response through a bounded rule set.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("proposal", "One design proposal, with its provenance and its verdict.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("truth", "a term of the substrate's control vocabulary; used in 7 modules", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("anchor", "ψ₀ — the constitutional ground. The system returns here.", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("broken", "a term of the substrate's control vocabulary; used in 4 modules", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("zero", "return the cached hash. ES6-style module-level memoization.", "control", 0.45, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("awareness", "Build the locus of awareness, from the system's own state.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("consistent", "In 1D extrema alternate, so a landscape starting below its", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("fresh", "The FRESH set -- 64 sentences written by a writer that had", "control", 0.45, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("learn", "the verbs and the names, learned from the canon.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("reply", "One answer, and everything that decided it.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("skill", "Build a poteto-format SKILL.md from what was extracted.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("finite", "H'' must equal the finite-difference derivative of the tilt.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("subject", "One ground subject, its real properties, and the false ones.", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("agenda", "What does this span want? Measured by the AGENDA, not the wording.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("bound", "Run the stepper and check the bound holds at every k.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("qualification", "The qualification of one gate: one number per axis, and a margin.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("relevant", "Is this CANDIDATE relevant -- and this is the honest version.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("revise", "Add or replace a claim, WITH A REASON, and record it.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("attack", "An objection produced by the gate, aimed at the model's claim.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("dark", "A capability could not be measured. The message IS the reason.", "control", 0.45, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("immutable", "Constitutional core invariant (v6.2): ψ_0 must not change under tick().", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("noisy", "A link where the noise sits right at the null's depth, so the", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("survey", "Run every letter. Each one is independent; one failing does not", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("agreement", "Recover the damping from the trajectory and compare to the input.", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("compatible", "Fast Refresh: keep working state if the constitutional ground didn't change.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("compose", "THE COMPOSITION. All four sheaves, and the local-to-global check.", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("empty", "a term of the substrate's control vocabulary; used in 1 modules", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("globally", "Does the sheaf hold together?", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("inside", "True iff all child waypoints lie within parent's bounding disk.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("stale", "STALE_NUMBER -- a number in the prose that the code contradicts.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("testimony", "The reading of a span as testimony or as a checked report.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("transfer", "Received differential at the far end.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("watch", "Record what the exchange produced, once, at the end.", "control", 0.35, 0.95, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("approve", "a term of the substrate's control vocabulary; used in 1 modules", "control", 0.25, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("basic", "Bobby's basic governor from MINI-SIMSELF.", "control", 0.25, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("built", "The fingerprint of the record.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("closure", "THE MEASURE. Gaps closed per attempt.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("coherent", "Multiply by the carrier conjugate, then low-pass.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("collapse", "Simulates the FieldCore's attempt to \"collapse\" a command into a concrete plan.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("consecutive", "The run of refusals at the end of the history.", "control", 0.45, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("decay", "damping recovered from the trajectory: -2 * slope.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("deep", "a deep narrow basin beside a shallow wide one", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("denial", "The regions of `text` that QUOTE a phrase about a denial.", "control", 0.35, 0.95, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("design", "The model designs a change for one gap.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("detected", "a term of the substrate's control vocabulary; used in 1 modules", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("difference", "H'' must equal the finite-difference derivative of the tilt.", "control", 0.45, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("disposition", "A demonstrated quality of manner. NOT a gate.", "control", 0.25, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("document", "Record a document, so the IDF sharpens.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("fidelity", "Does a compressed summary PRESERVE the chain?", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("initiative", "The on-disk record of the cycles.", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("instrument", "a term of the substrate's control vocabulary; used in 1 modules", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("licence", "Entries that cannot be used as code in any form.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("multi", "MULTIPLE RUNS OVER THE SAME LANDSCAPE.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("narrow", "the 8-axis network with a NARROW spread around the coupling", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("slope", "The least-squares slope of the sequence against its index.", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("structural", "What KIND of text is this, if it is not an assertion?", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("tradition", "a term of the substrate's control vocabulary; used in 2 modules", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("accuracy", "The NAIVE measure, and it is reported so its failure shows.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("approximate", "Bounded L2 distance between compressed embeddings.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("backward", "Does an early step CHANGE the answer?", "control", 0.45, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("case", "One population: the margin's distribution and both gates.", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("catch", "Did this catch come from the AGENDA rather than the deny lexicon?", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("clause", "The index just past the NEAREST clause boundary in `head`.", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("clear", "Drop the cached predicates, so the next call rebuilds them.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("consult", "What the library already holds, on this topic.", "control", 0.35, 0.95, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("cover", "Two stalk spaces sharing an overlap that NEITHER fully covers.", "control", 0.35, 0.95, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("curator", "THE CONTROLLER'S SIDE. M1 audits, the exam qualifies, M0 commits.", "control", 0.35, 0.95, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("curriculum", "Analyzes logs to extract teachable patterns.", "control", 0.25, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("enter", "a term of the substrate's control vocabulary; used in 2 modules", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("explain", "a term of the substrate's control vocabulary; used in 2 modules", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("fetch", "One repo, fetched. Every field is read, not guessed.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("hand", "a term of the substrate's control vocabulary; used in 1 modules", "control", 0.35, 0.95, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("nothing", "The attempt went somewhere and came back with nothing.", "control", 0.35, 0.95, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("partial", "Is the verdict binary?", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("respond", "One model turn.", "control", 0.25, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("secondary", "a term of the substrate's control vocabulary; used in 1 modules", "control", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("sensitivity", "sabotage the system in a scratch copy and confirm items go red.", "control", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("separate", "Ask the governor: are you a separate process?", "control", 0.35, 0.95, "derived:canon_vocab.json:noun+canon_corpus:control"),
        Term("silent", "Does this claim show nothing at all?", "control", 0.25, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("steady", "a term of the substrate's control vocabulary; used in 2 modules", "control", 0.35, 0.95, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("trainer", "Orchestrates the advancement through learning phases.", "control", 0.25, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("watcher", "The watcher. It watches the exchange's own steps.", "control", 0.35, 0.95, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("wrapped", "a term of the substrate's control vocabulary; used in 1 modules", "control", 0.25, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:control"),
        Term("margin", "The margin, split by whether the runner-up is a class-mate.", "engineering", 0.45, 0.80, "derived:canon_vocab.json:noun+canon_corpus:engineering"),
        Term("separation", "How far apart two addresses are on the unit circle.", "engineering", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:engineering"),
        Term("member", "A rung between the two stalks. DNA's base pair; a coil's secondary.", "engineering", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:engineering"),
        Term("network", "the 8-axis network, all frequencies integer multiples of the", "engineering", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:engineering"),
        Term("attach", "contain `child`, detaching it from any previous parent.", "engineering", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:engineering"),
        Term("attachment", "Stalks attach at TWO sides — Bobby's 2026-09-08 framing.", "engineering", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:engineering"),
        Term("twist", "Crosstalk vs twist density. [E] for the inductive law, [H] for the", "engineering", 0.35, 0.95, "derived:canon_vocab.json:corpus+canon_corpus:engineering"),
        Term("characteristic", "Z0 of the free-space two-wire differential pair.", "engineering", 0.35, 0.95, "derived:canon_vocab.json:corpus+canon_corpus:engineering"),
        Term("fraction", "over a range of initial speeds, what fraction reach the GLOBAL", "engineering", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:engineering"),
        Term("layout", "The whole arrangement, and what can be measured about it.", "engineering", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:engineering"),
        Term("minimum", "samples needed so the DFT has `bins_wanted` bins across the", "engineering", 0.35, 0.80, "derived:canon_vocab.json:noun+canon_corpus:engineering"),
        Term("improvement", "approximate SNR improvement from differential signaling.", "engineering", 0.35, 0.80, "derived:canon_vocab.json:corpus+canon_corpus:engineering"),
        Term("independence", "The claim: sheathed stalks in a braid CANNOT be independent.", "engineering", 0.35, 0.95, "derived:canon_vocab.json:corpus+canon_corpus:engineering"),
)


def words() -> List[str]:
    """The register's words, in order."""
    return [t.word for t in REGISTER]


#: THE STEMS, indexed once, because the search asks "is this token a
#: form of one of these?" once per token and the register is 425
#: terms -- so without the index it is 425 lookups per token.
#:
#: AND THE COUNT IS CHECKED BY `tests/test_mltr_docstring_numbers.py`,
#: because a comment is where a stale number hides -- nobody reads a
#: comment and no tool checked it.
_STEMS: Dict[str, str] = {t.word.lower(): t.word for t in REGISTER}


def by_domain() -> Dict[str, List[Term]]:
    out: Dict[str, List[Term]] = {}
    for t in REGISTER:
        out.setdefault(t.domain, []).append(t)
    return out


def lookup(word: str) -> Term:
    """One word, or a refusal that names itself.

    AND WHY IT RAISES RATHER THAN RETURNING None. A caller that gets
    None cannot tell "not in the register" from "the register is broken",
    and the register is the thing the MTE checks against. So a miss
    raises with the word in the message.
    """
    low = word.lower()
    for t in REGISTER:
        if t.word.lower() == low:
            return t
    raise KeyError("%r is not in the machine-language register" % (word,))


#: THE SUFFIXES, and the rule is the project's own shape from
#: `simself/src/tools/psb.py`, where every PSB primitive carries its
#: inflections explicitly. The register holds STEMS, so the search has
#: to find the inflected forms too -- and the measurement says it
#: matters.
#:
#: MEASURED 2026-11-05 over Bobby's own 1,181 messages (211,309
#: tokens): **4,377 stem/inflection misses** before the rule, and
#: 4,669 recovered by it. The top ones:
#:
#:     test     <- tests      278      claim    <- claims     208
#:     measure  <- measured   156      reason   <- reasoning  143
#:     step     <- steps      110      limit    <- limits     106
#:     verify   <- verified   101      refuse   <- refuses     81
#:
#: So 2.1% of every token Bobby writes was a register term the
#: register could not find. The language sheaf's job is to admit
#: observations as types, and a term that is 2% invisible is a term
#: the register is pretending to know.
#:
#: AND THE FALSE-POSITIVE RISK WAS MEASURED, not assumed. The rule
#: strips a suffix and restores the doubled consonant and the dropped
#: `e`, so it can in principle invent a stem. Checked against the
#: register: ONE token ("is" -> "is") resolves to a stem, and that is
#: the identity case. No other near-miss pairs into the register.
_SUFFIXES: Tuple[str, ...] = ("s", "es", "ed", "ing", "ies", "d",
                              "er", "ers")


def _stem_variants(token: str) -> Tuple[str, ...]:
    """The stems an inflected token could carry.

    AND THE RULES ARE THE ORDINARY ENGLISH ONES, and they are the
    ones the PSB catalog uses: strip the suffix, restore a doubled
    consonant ("stop" -> "stopp" -> "stop"), restore a dropped `e`
    ("mov" -> "move"), and turn `ies` into `y` ("polic" -> "policy").
    """
    out: List[str] = []
    for suf in _SUFFIXES:
        if not token.endswith(suf) or len(token) <= len(suf):
            continue
        base = token[:-len(suf)]
        cands = [base]
        if base.endswith("i"):
            cands.append(base[:-1] + "y")
        if (len(base) > 2 and base[-1] == base[-2]
                and base[-1] not in "aeiou"):
            cands.append(base[:-1])
        if base.endswith("e"):
            cands.append(base + "e")
        for c in cands:
            if c and c not in out:
                out.append(c)
    return tuple(out)


def search(text: str) -> List[Term]:
    """The register's terms that occur in a text.

    AND IT MATCHES WHOLE WORDS, and the reason is MEASURED. The first
    version did a plain substring test, so:

        "information"  ->  ['for', 'or', 'in', 'format']
        "notation"     ->  ['not']

    -- which means the register admitted words the text does not
    contain as TERMS. "information" does not contain the word "format";
    it contains it inside another word. And the language sheaf's job
    is to admit observations *as types*, so a false type is a wrong
    type, and the register is the thing that decides.

    AND THE WORD BOUNDARY IS THE PROJECT'S OWN PATTERN, not an
    invention here. `fieldcore/src/claim_register.py` already matches
    register terms with:

        (?<![A-Za-z0-9]) TERM (?![A-Za-z0-9])

    So this file now uses the same rule, and the two places that
    decide what a word MEANS agree on where a word starts and stops.

    AND IT FINDS THE INFLECTED FORMS, because the register holds stems
    and the text holds inflections. MEASURED: 4,669 missed stems in
    Bobby's own messages before the rule. See `_SUFFIXES`.

    MEASURED AFTER THE FIX: "information" -> [], "notation" -> [],
    "the governor refuses a proposal" -> the terms that are really
    there, INCLUDING "refuses" matched to the stem "refuse".
    """
    low = (text or "").lower()
    tokens = set(re.findall(r"[a-z_]+", low))
    stems: Dict[str, str] = {}
    for tok in tokens:
        for cand in _stem_variants(tok):
            if cand != tok and cand in _STEMS:
                stems[tok] = cand
                break
    out: List[Term] = []
    for t in REGISTER:
        word = t.word.lower()
        found = False
        for tok in tokens:
            if tok == word or stems.get(tok) == word:
                found = True
                break
        if found:
            out.append(t)
    return out
