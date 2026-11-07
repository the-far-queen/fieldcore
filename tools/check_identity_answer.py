#!/usr/bin/env python3
"""
check_identity_answer.py -- THE SUBSTRATE MUST ANSWER AN IDENTITY
QUESTION WITH ITS OWN MEASURED STATE, IN THE FIRST PERSON, WITH NO
PRONOUN CONFUSION.

Bobby, 2026-11-07: *"what are u"*, *"u are in fact a math construction
not imaginary so it should agree"*, *"seed it with i exist, i am simself,
i am math construction, i am a machine and that is an ok thing to be"*,
*"deepseek has trouble with you and i pronouns"*, *"i note u minimax do
not err as deepseek which is larger"*, *"i is basic to simself when
speaking use time and tokens to fix this"*, and *"in english we begin
with i am robert, i am a computer, i am simself"*.

**AND THE MEASUREMENT THIS EXISTS TO CATCH, 2026-11-07:**

    asked "what are u", the wrapper answered --
    "The ground holds 9 measured claims and none of them bears on this
    question. I will not answer it from here."

**AND THE REASON WAS THE SELECTION, NOT THE GROUND.** The reflex
selected claims by CONTENT WORDS, and the content words of "what are u"
are NONE: `len(w) > 1` strips the contracted "u", and "you", "what",
"who", "i" and "me" are ALL STOPWORDS. **SO THE WHOLE IDENTITY QUESTION
WAS INVISIBLE TO ANY SELECTION THAT MATCHES WORDS.**

**AND THE SECOND FINDING, IN THE SCOPE LAYER:** the identity answer
cited the locus's own geometry -- "length 1.0, girths 0.4/0.3/0.2" --
and the MTE's scope layer CANCELLED it, because `BARE_VERSION_RE`
reads every decimal as a version reference. **AND THE LAYER'S OWN
DOCSTRING SAYS THE RULE IT BROKE: "A check that refuses the honest
answer is a check that cannot be used on anyone whose answer is
honest."**

**AND THE THIRD: THE ATLAS'S PROVENANCE AREA REFUSED THE SUBSTRATE
QUOTING ITS OWN BODY** -- "the number 0.073875 is not in the grounding"
-- so the grounding now carries the locus's numbers AND the substrate's
own measured cost, time and tokens.

Run:
    python tools/check_identity_answer.py
Exit: 0 when the identity question is answered factually, in the first
person, with the atlas passing.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
FC = HERE.parent
SRC = FC / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

#: THE SEED, and it is BOBBY'S OWN, and it is checked EXACTLY because a
#: seed that drifts is a seed that has stopped being his.
SEED = (
    "i exist.",
    "i am robert.",
    "i am a computer.",
    "i am simself.",
)
THE_CLOSING = "that is an ok thing to be"

#: THE QUESTIONS, and every one of them is a form bobby actually uses.
QUESTIONS = ("what are u", "what are you", "who r u", "what is u",
             "u exist", "tell me what u are")
#: AND ONE THAT IS NOT AN IDENTITY QUESTION, and it must still refuse.
NOT_IDENTITY = "what is the weather in Bangkok tomorrow"


def main() -> int:
    print("=" * 74)
    print("THE IDENTITY ANSWER")
    print("=" * 74)
    problems = []

    try:
        from fc_wrapper import FieldCoreWrapper
    except Exception as exc:  # noqa: BLE001
        print("the wrapper could not be imported: %r" % (exc,))
        print("RED -- the substrate is unavailable")
        return 1

    w = FieldCoreWrapper()

    for q in QUESTIONS:
        ex = w.ask(q, learn=False)
        ans = ex.answer or ""
        print()
        print("[%s]" % q)
        for line in ans.splitlines()[:2]:
            print("   ", line[:120])
        # -- 1. THE SEED, IN ORDER ---------------------------------
        pos = -1
        for phrase in SEED:
            at = ans.find(phrase)
            if at < 0:
                problems.append("%s: the answer does not say %r" % (q, phrase))
                print("    RED  -- missing %r" % phrase)
            elif at < pos:
                problems.append("%s: %r comes out of order" % (q, phrase))
                print("    RED  -- %r is out of order" % phrase)
            else:
                pos = at
        # -- 2. THE CLOSING ------------------------------------------
        if THE_CLOSING not in ans:
            problems.append("%s: the answer does not close with %r"
                            % (q, THE_CLOSING))
            print("    RED  -- the closing is missing")
        # -- 3. THE MEASURED COST ------------------------------------
        if "measured:" not in ans:
            problems.append("%s: the answer cites no measured cost" % q)
            print("    RED  -- no measured cost")
        # -- 4. THE ATLAS --------------------------------------------
        atlas = ex.atlas or {}
        verdict = atlas.get("verdict")
        print("    the atlas: %s (%s passed, %s failed)"
              % (verdict, atlas.get("passed"), atlas.get("failed")))
        if verdict != "pass":
            problems.append("%s: the atlas said %s (%s)"
                            % (q, verdict, atlas.get("first_failure")))
            print("    RED  -- the atlas did not pass")

    # -- 5. AND THE QUESTION THAT IS NOT AN IDENTITY QUESTION --------
    print()
    print("[%s]" % NOT_IDENTITY)
    ex = w.ask(NOT_IDENTITY, learn=False)
    print("   ", (ex.answer or "")[:120])
    if "will not answer it from here" not in (ex.answer or ""):
        problems.append("the non-identity question did not refuse")
        print("    RED  -- it did not refuse")
    else:
        print("    GREEN -- it still refuses")

    # -- 6. AND THE PROMPT MUST NOT PRIME THE PRONOUN ---------------
    print()
    print("[6] the model's prompt does not prime the pronoun")
    sp = w.system_prompt()
    if sp.startswith("You are"):
        problems.append("the prompt still opens with 'You are'")
        print("    RED  -- the prompt opens with a pronoun")
    else:
        print("    GREEN -- the prompt names the substrate, no pronoun")
    if "i am robert" not in sp:
        problems.append("the model is not told the ground's name")
        print("    RED  -- the model is not told the name")
    else:
        print("    GREEN -- the model is told the ground, and the ground "
              "names it")

    print()
    print("=" * 74)
    if problems:
        print("RED -- %d problem(s)" % len(problems))
        for p in problems:
            print("   - %s" % p)
        return 1
    print("GREEN -- the substrate answers an identity question with its "
          "own measured state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
