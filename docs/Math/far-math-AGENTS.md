# far-math — the claim-layer rules

> MOVED 2026-10-24. The far-math repo was deleted; its code and documents
> were already folded into fieldcore on 2026-10-16 (`src/farmath/`,
> `docs/Math/`). This file carried the rules for ADDING a claim, and the
> layer contract itself. fieldcore's own math docs stay Layer A only; the
> far-math school carries the full A/B/C layer system.

## Before you add a claim

1. **Name its layer.** A / B / C. If you cannot, it is C.
2. **Give it a check.** A function that returns a number another function
   can disagree with. If the check cannot go red, it is not a check.
3. **Give a Layer C claim a falsifier** and an engineering value. If the
   engineering value is "none", say so plainly. That is allowed; hiding it
   is not.
4. **Never promote a layer silently.** Moving C to A is the one edit that
   needs Bobby's word, because it is the one edit that puts a guess into a
   runtime path.

## The rules of the house

These are the same seven rules that govern the substrate repos
(`C:/Users/HP/AppData/Local/hermes/CENTRAL-RULES.md`). They are short
because they are load-bearing.

1. **Diagnose before adjusting.** If you are about to change a number to
   make something work, run it as-is first and read the output.
2. **Instrument before adjusting.** When something surprises you, print the
   trace before you touch a parameter.
3. **No number without the command that produced it**, run *after* the
   change.
4. **A surprising result means your code is wrong first**, and the physical
   claim is the second hypothesis.
5. **Two derivations must agree.** Derive it twice, independently. If they
   disagree, one is wrong — find out which before reporting either.
6. **Stability is a basin, not a knife edge.** Sweep the parameter. If it
   works at exactly one setting, the model is wrong.
7. **A test that cannot fail is not a test.** Show it going red.

## Honesty about voice

Bobby's framings stay in the repo, in his words, marked as his. Do not
soften them into vagueness and do not inflate them into claims. When Grok or
another collaborator is right and Bobby is wrong about a fact of topology,
the correction goes in beside the original, dated, with both names on it —
never over the top of it.

## Style

Lowercase for prose. Code and math in normal case. No marketing register.
No word from the poisoned-speech list; the scanner is in
`fieldcore/docs/PRODUCTS/poisoned_speech_lint.py` and it is not optional.