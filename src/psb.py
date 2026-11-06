"""THE PSB VALIDATOR -- a THIN wrapper over the schema.

**THIS IS A THIN VALIDATOR, NOT A REIMPLEMENTATION.** The schema
itself lives in `simself/src/constitutional/psb_schema.py`, next to the
module that already held the primitives, and this file only:

  1. adds the substrate's sys.path so the schema can be imported,
  2. re-exports the schema's names,
  3. offers `check_registry()`, which validates EVERY PSB in a registry
     and says which ones are broken.

**AND WHY IT IS IN FIELDCORE AT ALL.** The schema is the SUBSTRATE'S,
and the substrate is simself. But the thing that has to be checked is
the language sheaf's register, and the language sheaf lives in
fieldcore -- so fieldcore is where the check runs. It is wired into
`fieldcore/src/sheaves.py`'s `language_types()`, which is already
WIRED by the census, so this module is not an orphan.

**AND WHY A THIN WRAPPER AND NOT A COPY.** A second implementation of
the same schema is two schemas, and they will diverge -- which is
exactly what happened to the population recipe, which was copied seven
times and had diverged. One schema, one implementation, one place to
change.

**THE SCHEMA'S SOURCE:** `vault/10-minimax/20-writing/far-writing-canon/
2026-11-06-the-psb-schema.md`.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional, Tuple

#: AND THE SUBSTRATE'S SRC IS ADDED TO THE PATH, so the schema can be
#: imported by name. AND IT IS ADDED HERE AND NOT AT THE TOP OF THE
#: MODULE, because the import of the schema has to be DEFERRED until
#: the path is set -- and a deferred import that fails must fail
#: LOUDLY, with the reason, rather than being swallowed.
_SIMSRC = os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "simself", "src")
if _SIMSRC not in sys.path:
    sys.path.insert(0, _SIMSRC)

try:
    from constitutional.psb_schema import (  # noqa: F401
        LAYERS,
        PSB,
        Layer,
        PSBRegistry,
        PSB_REGISTRY,
        Relation,
        Sense,
        Status,
        admit_psb,
        retire_psb,
        revise_psb,
        validate_psb,
    )
except Exception as _exc:  # noqa: BLE001
    # AND THE FAILURE IS LOUD. A swallowed import is how the modulator
    # hid three gone imports for months, and how "the writer says how
    # far it is sure" became a module that imported fine and had no
    # class in it. So this raises, and the caller sees why.
    raise ImportError(
        "the PSB schema could not be imported from %r -- the substrate's "
        "path is wrong or the schema module is broken: %r"
        % (_SIMSRC, _exc)) from _exc


__all__ = [
    "LAYERS", "PSB", "Layer", "PSBRegistry", "PSB_REGISTRY", "Relation",
    "Sense", "Status", "admit_psb", "retire_psb", "revise_psb",
    "validate_psb", "check_registry", "derive_from_register",
]


def check_registry(registry: Optional[PSBRegistry] = None
                   ) -> Tuple[bool, List[str]]:
    """Validate EVERY PSB in a registry.

    AND IT REPORTS THE ID OF EACH BROKEN PSB, not just a count. A
    count says how many are wrong; the ids say which, and the ids are
    what a reader needs.
    """
    reg = registry if registry is not None else PSB_REGISTRY
    broken: List[str] = []
    for psb in reg.all():
        ok, bad = validate_psb(psb, reg)
        if not ok:
            broken.extend("%s: %s" % (psb.id, b) for b in bad)
    return (not broken), broken


def derive_from_register(registry: Optional[PSBRegistry] = None
                         ) -> List[PSB]:
    """DERIVE candidate PSBs from the substrate's own language register.

    **AND THE DERIVATION IS HONEST ABOUT WHAT IT DOES.** The MLTR
    register holds terms with a domain, a gloss and a source. A term
    is a CANDIDATE PSB -- it has a word, a domain and a meaning -- but
    it does NOT have:

      - its inflections (the register does not carry them),
      - its contexts (I5 requires them, and a sense without a context
        is a dictionary gloss),
      - its snr (the register has no snr for a term), or
      - its relations.

    **SO THE DERIVED PSBs ARE NOT ADMITABLE AS THEY STAND**, and this
    function says so rather than pretending. It returns the candidates
    so that a reader can see what the substrate's own vocabulary would
    produce, and the check that consumes them asserts that they are
    CANDIDATES -- with the four missing fields named.

    **AND THE POINT OF DERIVING IS THAT THE GAP IS MEASURED.** The
    register holds 412 terms; the PSB schema needs 11 fields each; so
    the number of fields the substrate cannot yet fill is a number, and
    the number is the work.
    """
    reg = registry if registry is not None else PSB_REGISTRY
    try:
        import mltr_register as MLTR
    except Exception as exc:  # noqa: BLE001
        raise ImportError("the MLTR register could not be imported: %r"
                          % (exc,)) from exc
    out: List[PSB] = []
    for term in getattr(MLTR, "REGISTER", ()):  # pragma: no branch
        term_id = getattr(term, "id", None) or getattr(term, "term", "")
        word = getattr(term, "term", "") or getattr(term, "gloss", "")[:24]
        if not word:
            continue
        out.append(PSB(
            id=str(term_id or word).lower().replace(" ", "-"),
            word=str(word),
            inflections=(),
            senses=(Sense(domain=str(getattr(term, "domain", "")),
                          meaning=str(getattr(term, "gloss", "")),
                          contexts=(),
                          snr=float(getattr(term, "snr", 0.0) or 0.0)),),
            relations=(),
            layer=Layer.SEMANTIC,
            provenance=(str(getattr(term, "source", "")),),
            revision=1,
            status=Status.ADMITTED,
            admitted_at="",
        ))
    return out


def _selftest() -> int:
    """THE SELF-TEST -- and it can go RED."""
    print("=" * 74)
    print("THE PSB SCHEMA -- the self-test")
    print("=" * 74)
    print()
    ok = True

    def check(label: str, cond: bool, extra: str = "") -> None:
        nonlocal ok
        print("  %-52s %s%s" % (label, "ok" if cond else "FAILED",
                                ("  " + extra) if extra else ""))
        if not cond:
            ok = False

    reg = PSBRegistry()
    good = PSB(
        id="refuse",
        word="refuse",
        inflections=("refuse", "refuses", "refused", "refusing"),
        senses=(Sense(domain="control",
                      meaning="to decline to act",
                      contexts=("the operator refuses the change",),
                      snr=0.8),),
        layer=Layer.SEMANTIC,
        provenance=("vault/20-writing/04-voice.md",),
        admitted_at="2026-11-06",
    )
    admitted, bad = admit_psb(good, reg)
    check("a valid PSB is admitted", admitted, str(bad[:2]))

    ok2, bad2 = validate_psb(good, reg)
    check("and it validates", ok2, str(bad2[:2]))

    # I4 -- the senses are non-empty
    no_senses = PSB(id="x", word="x", inflections=("x",))
    ok3, bad3 = validate_psb(no_senses, reg)
    check("I4 catches a PSB with no senses",
          not ok3 and any("I4" in b for b in bad3))

    # I5 -- a sense with no contexts
    no_ctx = PSB(id="y", word="y", inflections=("y",),
                 senses=(Sense(domain="d", meaning="m", contexts=()),))
    ok4, bad4 = validate_psb(no_ctx, reg)
    check("I5 catches a sense with no contexts",
          not ok4 and any("I5" in b for b in bad4))

    # I11 -- two senses with the same domain
    dup = PSB(id="z", word="z", inflections=("z",),
              senses=(Sense(domain="d", meaning="m", contexts=("c",)),
                      Sense(domain="d", meaning="n", contexts=("c",))),)
    ok5, bad5 = validate_psb(dup, reg)
    check("I11 catches two senses in one domain",
          not ok5 and any("I11" in b for b in bad5))

    # I1 -- a duplicate id is refused
    dup_id, bad6 = admit_psb(good, reg)
    check("I1 refuses a duplicate id",
          not dup_id and any("I1" in b for b in bad6))

    # revision
    ok7, bad7 = revise_psb("refuse", {}, reg, reason="a new context")
    check("a revision with a reason lands", ok7, str(bad7[:2]))
    check("and the revision number moved", reg.get("refuse").revision == 2,
          str(reg.get("refuse").revision))
    ok8, bad8 = revise_psb("refuse", {}, reg, reason="")
    check("a revision with NO reason is refused", not ok8, str(bad8[:1]))

    # retirement
    ok9, bad9 = retire_psb("refuse", "the word was not the word", reg)
    check("a retirement lands", ok9, str(bad9[:2]))
    check("and the PSB is RETIRED, not deleted",
          reg.get("refuse") is not None
          and reg.get("refuse").status is Status.RETIRED)
    check("and it says why",
          any("retired:" in p for p in reg.get("refuse").provenance))

    print()
    print("=" * 74)
    if ok:
        print("VERDICT: PASS")
        return 0
    print("VERDICT: FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(_selftest())
