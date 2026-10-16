"""The Layer A/B/C rule, enforced in code so a doc cannot drift past it.

Every math claim in this project carries a layer. Layer C material is
preserved, never dropped, and never silently promoted to Layer A. This
module is the gate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class Layer(str, Enum):
    A = "A"  # standard textbook math, cited correctly, used as a tool
    B = "B"  # real math glued onto toy code; held until the discrete operator exists
    C = "C"  # speculative; preserved with reasoning + falsifiability; off every runtime path


@dataclass
class Claim:
    name: str
    layer: Layer
    statement: str
    check: str | None = None
    falsifier: str | None = None
    engineering_value: str = "n/a"
    tags: list[str] = field(default_factory=list)


_LAYER_RE = re.compile(r"\bLayer\s+([ABC])\b")


def scan_layers(text: str) -> set[Layer]:
    """Return every layer named in a document."""
    return {Layer(m) for m in _LAYER_RE.findall(text)}


def untagged_c_suspects(text: str) -> list[str]:
    """Lines that read as a Layer C claim (unfalsifiable framing) but carry
    no layer marker. A list to read, not an automatic demotion.
    """
    markers = ("per bobby", "likely", "the universe", "fractal offset", "sacred", "correspondence")
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        low = line.lower()
        if any(m in low for m in markers) and not _LAYER_RE.search(line):
            hits.append(f"{i}: {line.strip()[:110]}")
    return hits


def audit(text: str) -> dict:
    """The audit a document must pass before it is called mathematics here."""
    layers = scan_layers(text)
    return {
        "layers_present": sorted(l.value for l in layers),
        "has_layer_marker": Layer.A in layers or Layer.B in layers,
        "untagged_c_suspects": untagged_c_suspects(text),
        "ok": bool(layers) and Layer.C not in layers or Layer.A in layers,
    }