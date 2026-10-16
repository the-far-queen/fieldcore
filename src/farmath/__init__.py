"""farmath: Layer A mathematics for the far-* schools, with checks.

Layer A = standard math used as tools.
Layer B = real math glued onto code, held until the discrete operator exists.
Layer C = speculative, preserved with reasoning + falsifiability, never
          on a runtime path.

FOLDED IN 2026-10-16 (Bobby: "del far-math fold into fieldcore"). This was
the far-math repo. The CODE moved here because fieldcore is where mathematics
that touches the substrate belongs -- one place to run it, one place to break
it.

Two things did NOT move with it, on purpose:

  - the CLAIMS REGISTER (docs/04-claims-register.md in far-math) is the most
    valuable artifact in the whole school -- it is what keeps a Layer C claim
    from quietly becoming a Layer A one. It stayed a document, because a
    register is a thing you READ, and putting it under src/ would imply it is
    enforced. It is enforced by `layers.py`, which is why that module came.
  - the school framing ("a school for humans and AI, no price") is not a code
    property and does not belong in a library either.

Nothing here imports the substrate repos. This package is mathematics; it has
no opinion about fieldcore or simself, and fieldcore does not import it back.
That direction is deliberate and load-bearing: the math is usable without the
substrate, so a broken substrate cannot invalidate a working proof.
"""

__all__ = ["geometry", "number_theory"]
__version__ = "0.1.0"