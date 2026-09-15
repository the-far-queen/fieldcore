"""
stalk_topology.py — braided stalks on a substrate manifold.

The geometry of Bobby's stalk architecture, made concrete:

  - A stalk is a 1D curve embedded in a 2D substrate surface.
  - Stalks attach at TWO points (inner torus + outer torus), per Bobby.
  - Stalks braid (DNA-like), cross-member, nest, resonate, touch, detach.
  - The substrate is parameterised by (theta, phi) on the unit torus T^2.

This is the topology layer. The substrate (modal_field_core.py) is the
dynamics layer. The harness (simself/src/harness/stalk_harness.py) is the
runtime layer.

Spec source: fieldcore/docs/Math/stalk-architecture-2026-09-08.md
             HANDOFF.md #3 (braided stalks, design captured, code not written)

Math:
  Stalk position:  x(s) = (theta(s), phi(s)) for s in [0, 1]
  Curvature:      kappa(s) = |x'(s) x x''(s)| / |x'(s)|^3
  Winding number:  w = (1 / 2 pi) integral_0^1 kappa(s) ds
  Braid crossing:  two stalks cross iff their winding numbers differ by 1
  Resonance:       two stalks resonate iff their arc-lengths match mod 1
  Cross-member:    a third stalk linking two parent stalks at (s1, s2)
  Nested stalk:    a stalk inside the convex hull of another stalk
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PHI = (1 + 5 ** 0.5) / 2          # golden ratio (fractal node aspect)
TWO_PI = 2 * math.pi


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class AttachmentSide(str, Enum):
    """Stalks attach at TWO sides — Bobby's 2026-09-08 framing."""
    INNER = "inner"               # inner solid torus surface
    OUTER = "outer"               # outer processing torus surface


class StalkState(str, Enum):
    """Five states, transitions driven by topology operations."""
    IDLE = "idle"
    EXTENDING = "extending"
    BRAIDED = "braided"
    RESONATING = "resonating"
    DETACHED = "detached"


@dataclass
class StalkAttachment:
    """Where a stalk attaches to the substrate."""
    side: AttachmentSide
    theta: float                  # substrate angle in [0, 2 pi)
    phi: float                    # substrate angle in [0, 2 pi)


@dataclass
class StalkGeometry:
    """The geometric description of a single stalk."""
    length: float                 # arc length in substrate units (>= 0.01)
    girth: float                  # cross-section radius (>= 0.001)
    curvature: float = 0.0        # mean |kappa(s)|; computed from control points
    winding: int = 0              # integer winding number around substrate axis
    control_points: List[Tuple[float, float]] = field(default_factory=list)
    """Substrate-space waypoints; (theta, phi). If empty, default linear arc."""


@dataclass
class Stalk:
    """One stalk: a curve on the substrate, attached at two points."""
    id: str
    inner: StalkAttachment
    outer: StalkAttachment
    geometry: StalkGeometry
    state: StalkState = StalkState.IDLE
    parent_id: Optional[str] = None      # set when this stalk is nested
    children: List[str] = field(default_factory=list)
    braid_partner: Optional[str] = None  # set when braided with another
    cross_members: List[str] = field(default_factory=list)
    resonance_freq: Optional[float] = None
    touched: List[str] = field(default_factory=list)
    """Other stalks currently touching this one (transient contact)."""

    # ------------------------------------------------------------------
    # Geometry helpers
    # ------------------------------------------------------------------
    def arc_length(self) -> float:
        """Total arc length along the substrate waypoints.

        If waypoints are populated, the arc length is computed from them
        and the caller's `geometry.length` is treated as a target.
        Otherwise the geometry length is returned directly.
        """
        pts = self.geometry.control_points
        if len(pts) < 2:
            return self.geometry.length
        total = 0.0
        for a, b in zip(pts, pts[1:]):
            # Toroidal distance — small-angle Euclidean is good enough for
            # local work; callers may substitute geodesic distance if needed.
            d_theta = (b[0] - a[0]) % TWO_PI
            d_phi = (b[1] - a[1]) % TWO_PI
            # unwrap small angles
            if d_theta > math.pi:
                d_theta -= TWO_PI
            if d_phi > math.pi:
                d_phi -= TWO_PI
            total += math.sqrt(d_theta * d_theta + d_phi * d_phi)
        return total

    def is_resonant_with(self, other: "Stalk") -> bool:
        """Two stalks resonate when arc lengths are congruent modulo 1.

        Resonance is the mechanism for cross-stalk coupling on the substrate.
        Same-length stalks at same geometric phase exchange signal coherently.
        """
        return abs((self.arc_length() - other.arc_length()) % 1.0) < 1e-6

    def touches(self, other: "Stalk") -> bool:
        """Two stalks touch if any pair of their waypoints are within `touch_eps`."""
        eps = max(self.geometry.girth, other.geometry.girth) * 2
        for a in self.geometry.control_points:
            for b in other.geometry.control_points:
                dt = abs(a[0] - b[0]) % TWO_PI
                dp = abs(a[1] - b[1]) % TWO_PI
                if dt > math.pi:
                    dt = TWO_PI - dt
                if dp > math.pi:
                    dp = TWO_PI - dp
                if math.sqrt(dt * dt + dp * dp) <= eps:
                    return True
        return False


# ---------------------------------------------------------------------------
# Braid / cross-member / nesting operations
# ---------------------------------------------------------------------------

def braid(a: Stalk, b: Stalk) -> bool:
    """DNA-like braid: bind two stalks by linking their windings.

    Pre:  a, b attached at the same pair of (inner.theta, outer.theta)
           and not already braided.
    Post: a.braid_partner == b.id, b.braid_partner == a.id,
          both states -> BRAIDED.
    Returns True on success, False otherwise.
    """
    if a.state == StalkState.DETACHED or b.state == StalkState.DETACHED:
        return False
    if a.braid_partner is not None or b.braid_partner is not None:
        return False
    if a.inner.theta != b.inner.theta or a.outer.theta != b.outer.theta:
        return False
    # crossing requires |winding diff| == 1
    if abs(a.geometry.winding - b.geometry.winding) != 1:
        return False
    a.braid_partner = b.id
    b.braid_partner = a.id
    a.state = StalkState.BRAIDED
    b.state = StalkState.BRAIDED
    return True


def unbraid(a: Stalk, b: Stalk) -> bool:
    """Reverse a braid; both return to IDLE."""
    if a.braid_partner != b.id or b.braid_partner != a.id:
        return False
    a.braid_partner = None
    b.braid_partner = None
    if a.state == StalkState.BRAIDED:
        a.state = StalkState.IDLE
    if b.state == StalkState.BRAIDED:
        b.state = StalkState.IDLE
    return True


def nest(child: Stalk, parent: Stalk) -> bool:
    """Make `child` a nested stalk inside the convex hull of `parent`.

    Geometric meaning: child's waypoints all lie within `parent`'s
    waypoint-enclosing disk on the substrate.
    """
    if child.parent_id is not None:
        return False
    if not _is_inside(child, parent):
        return False
    child.parent_id = parent.id
    parent.children.append(child.id)
    return True


def add_cross_member(parent_a: Stalk, parent_b: Stalk,
                     member: Stalk) -> bool:
    """Link parent_a and parent_b with a new stalk `member`.

    Cross-members are third stalks that bridge two parent stalks,
    creating the substrate's high-speed routes (per Bobby).
    """
    # member must touch both parents
    if not member.touches(parent_a) or not member.touches(parent_b):
        return False
    parent_a.cross_members.append(member.id)
    parent_b.cross_members.append(member.id)
    return True


def resonate(a: Stalk, b: Stalk) -> bool:
    """Couple two stalks on resonance.

    Pre:  not detached; arc lengths congruent mod 1.
    Post: both states -> RESONATING, both resonance_freq set to common freq.
    """
    if a.state == StalkState.DETACHED or b.state == StalkState.DETACHED:
        return False
    if not a.is_resonant_with(b):
        return False
    # resonance frequency = 1 / arc length (natural mode of the substrate)
    freq = 1.0 / max(a.arc_length(), b.arc_length(), 1e-6)
    a.resonance_freq = freq
    b.resonance_freq = freq
    a.state = StalkState.RESONATING
    b.state = StalkState.RESONATING
    return True


def detach(s: Stalk) -> None:
    """Remove a stalk from all pairings. State -> DETACHED."""
    if s.braid_partner is not None:
        # caller must hold reference; we just clear local pointers
        s.braid_partner = None
    s.cross_members = []
    s.resonance_freq = None
    s.state = StalkState.DETACHED


def attach(s: Stalk, inner: StalkAttachment,
           outer: StalkAttachment) -> None:
    """Re-attach a detached stalk."""
    s.inner = inner
    s.outer = outer
    s.state = StalkState.IDLE


def extend(s: Stalk, new_length: float, new_girth: float) -> None:
    """Variable length / girth: extend or contract a stalk."""
    if new_length < 0.01 or new_girth < 0.001:
        return
    s.geometry.length = new_length
    s.geometry.girth = new_girth
    if s.state == StalkState.IDLE:
        s.state = StalkState.EXTENDING
    # generate default linear waypoints if none provided
    if not s.geometry.control_points:
        s.geometry.control_points = [
            (s.inner.theta, s.inner.phi),
            (s.outer.theta, s.outer.phi),
        ]


# ---------------------------------------------------------------------------
# Topology — the collection of stalks
# ---------------------------------------------------------------------------

class StalkTopology:
    """The collection of all stalks on a single substrate.

    Maintains:
      - A registry of stalks by id.
      - The set of currently-active pairings (braids, resonances).
      - Touch updates: contact pairs are refreshed on each `tick`.
    """

    def __init__(self) -> None:
        self.stalks: Dict[str, Stalk] = {}
        self.tick_count: int = 0

    def add(self, s: Stalk) -> None:
        self.stalks[s.id] = s

    def remove(self, stalk_id: str) -> None:
        s = self.stalks.pop(stalk_id, None)
        if s is None:
            return
        # unlink from any partner
        if s.braid_partner and s.braid_partner in self.stalks:
            self.stalks[s.braid_partner].braid_partner = None
        # remove from parent / children
        if s.parent_id and s.parent_id in self.stalks:
            self.stalks[s.parent_id].children = [
                c for c in self.stalks[s.parent_id].children if c != stalk_id
            ]

    def tick(self) -> None:
        """One topology step: refresh touch contacts."""
        ids = list(self.stalks.keys())
        touched_map: Dict[str, List[str]] = {i: [] for i in ids}
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a = self.stalks[ids[i]]
                b = self.stalks[ids[j]]
                if a.touches(b):
                    touched_map[a.id].append(b.id)
                    touched_map[b.id].append(a.id)
        for sid, partners in touched_map.items():
            self.stalks[sid].touched = partners
        self.tick_count += 1

    def _resonance_pairs(self) -> List[Tuple[str, str, float]]:
        """Pair up resonating stalks (state == RESONATING, not braided)."""
        seen: set = set()
        out: List[Tuple[str, str, float]] = []
        for a, s in self.stalks.items():
            if s.state != StalkState.RESONATING:
                continue
            if s.resonance_freq is None:
                continue
            for b_id, b in self.stalks.items():
                if b_id <= a:
                    continue
                if b.state != StalkState.RESONATING:
                    continue
                if b.resonance_freq != s.resonance_freq:
                    continue
                key = (a, b_id)
                if key in seen:
                    continue
                seen.add(key)
                out.append((a, b_id, s.resonance_freq))
        return out

    def status(self) -> Dict:
        """Snapshot of topology state for the harness to surface."""
        return {
            "tick": self.tick_count,
            "stalk_count": len(self.stalks),
            "states": {
                state.value: sum(
                    1 for s in self.stalks.values() if s.state == state
                )
                for state in StalkState
            },
            "braids": [
                [a, b] for a, s in self.stalks.items()
                if s.braid_partner and a < s.braid_partner
                for b in [s.braid_partner]
            ],
            "resonances": self._resonance_pairs(),
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_inside(child: Stalk, parent: Stalk) -> bool:
    """True iff all child waypoints lie within parent's bounding disk.

    The bounding disk is computed from parent's waypoints on the substrate.
    Euclidean distance in (theta, phi) coordinates with toroidal unwrapping.
    """
    pts = parent.geometry.control_points
    if len(pts) < 2:
        return False
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    r = max(
        math.sqrt(((p[0] - cx) % TWO_PI) ** 2 + ((p[1] - cy) % TWO_PI) ** 2)
        for p in pts
    )
    for c in child.geometry.control_points:
        dt = (c[0] - cx) % TWO_PI
        dp = (c[1] - cy) % TWO_PI
        if math.sqrt(dt * dt + dp * dp) > r:
            return False
    return True


# ---------------------------------------------------------------------------
# Demo — self-test when run directly
# ---------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    topo = StalkTopology()

    s1 = Stalk(
        id="s1",
        inner=StalkAttachment(AttachmentSide.INNER, 0.0, 0.0),
        outer=StalkAttachment(AttachmentSide.OUTER, math.pi / 2, 0.0),
        geometry=StalkGeometry(
            length=1.0, girth=0.05, winding=0,
            control_points=[(0.0, 0.0), (math.pi / 2, 0.0)],
        ),
    )
    s2 = Stalk(
        id="s2",
        inner=StalkAttachment(AttachmentSide.INNER, 0.0, 0.0),
        outer=StalkAttachment(AttachmentSide.OUTER, math.pi / 2, 0.0),
        geometry=StalkGeometry(
            length=1.0, girth=0.05, winding=1,
            control_points=[(0.0, 0.0), (math.pi / 2, 0.0)],
        ),
    )
    s3 = Stalk(
        id="s3",
        inner=StalkAttachment(AttachmentSide.INNER, 0.0, 0.0),
        outer=StalkAttachment(AttachmentSide.OUTER, math.pi / 2, 0.0),
        geometry=StalkGeometry(
            length=1.0, girth=0.04,
            control_points=[(0.0, 0.0), (math.pi / 2, 0.0)],
        ),
    )
    # s1 and s2 share attachments and winding diff == 1 -> braid
    assert braid(s1, s2)
    # s3 has the same arc length as s1 -> resonates
    assert resonate(s1, s3)

    topo.add(s1)
    topo.add(s2)
    topo.add(s3)
    topo.tick()
    print("STATUS:", topo.status())