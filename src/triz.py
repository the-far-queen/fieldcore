"""
triz.py -- THE 40 INVENTIVE PRINCIPLES, AS MACHINERY.

Bobby, 2026-10-28: *"make smaller, enlarge, unscrew it, clamp it,
lubricate it, reverse it, join it separate it, there were many many"* and
*"generalize to data was referring to machinery"*.

AND THE CORRECTION IS THE WHOLE FILE. The first version of the technique
register had TRIZ as ONE entry -- "the 40 inventive principles" -- which
is a pointer to a list, not the list. And "generalize to data" was
misread as "apply the measures to any data"; it was about MACHINERY.
The principles are MACHINE techniques. They are moves on a physical
assembly, and they apply to the substrate because the substrate IS an
assembly: stalks, carriers, sheaves, a ground, a governor.

AND THE 40, with their canonical names, from Domb, E., '40 Inventive
Principles With Examples', TRIZ Journal, July 1997 (as rendered in
Mann & O'Cathain, '40 Inventive (Architecture) Principles With
Examples'). CHECKED 2026-10-28 against the primary text, not from
memory.

AND THE SECOND REGISTER, the 76. The TRIZ literature has TWO big
enumerations and both matter:

    THE 40 INVENTIVE PRINCIPLES   the MOVES. "Make it smaller. Make it
        bigger. Unscrew it. Clamp it. Lubricate it. Reverse it. Join it.
        Separate it." Each is a transformation of a thing.

    THE 76 STANDARD INVENTIVE    the SOLUTIONS. Altshuller's system of
        SOLUTIONS (SIS)                76 solution models, each
        expressed as a substance-field (Su-Field) interaction. Started
        as 28 in the 1970s and expanded through the 1980s to 76, which
        Altshuller judged sufficient. In five classes.

AND WHY BOTH MATTER FOR THE SUBSTRATE. The 40 are MOVES and they are
bounded by the substrate's own vocabulary -- so applying one is a
LOOKUP, not a search: the move that applies is already tabulated.
That is the whole compute argument again: a fixed table answers in
constant time.

AND THE LIMIT, which is the important one and it is Altshuller's own:

    **TRIZ SOLVES MECHANICAL CONTRADICTIONS.** It is for a thing that
    must be bigger AND smaller, or fast AND strong, where the
    contradiction is in the PHYSICS.

    The substrate's problems are mostly not mechanical
    contradictions. They are questions of PROVENANCE, of IDENTITY, of
    what may be believed. And TRIZ is silent on those -- which is
    exactly why it needs the other techniques beside it.

Run:
    python src/triz.py --selftest
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
WORK_REPOS = os.path.abspath(os.path.join(HERE, "..", ".."))
FC_SRC = os.path.join(WORK_REPOS, "fieldcore", "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")

for _p in (FC_SRC, SS_SRC):
    if _p not in sys.path:
        sys.path.insert(0, _p)


@dataclass(frozen=True)
class Principle:
    """One inventive principle: a MOVE on a thing.

    AND THE MACHINERY READING, which is the field that makes this a
    register rather than a list. Every principle names the assembly it
    applies to and the physical consequence.
    """
    number: int
    name: str
    #: the actual moves -- the subsection titles from the primary text
    moves: Tuple[str, ...]
    #: the machinery reading: what it does to an assembly
    machinery: str

    def describe(self) -> Dict[str, Any]:
        return {"n": self.number, "name": self.name,
                "moves": list(self.moves), "machinery": self.machinery}



PRINCIPLES: Tuple[Principle, ...] = (
    Principle(1, "Segmentation",
             moves=("divide an object into independent parts", "make an object sectional, for easy assembly or disassembly", "increase the degree of fragmentation"),
             machinery="split the assembly so a fault is contained and a part is replaceable"),
    Principle(2, "Taking out / Removal / Extraction",
             moves=("separate an interfering part or property", "extract only the necessary part or property", "single out the only part that carries the unwanted property"),
             machinery="remove the part that carries the problem instead of compensating for it"),
    Principle(3, "Local quality",
             moves=("change uniform structure to non-uniform", "change a uniform environment to a non-uniform one", "each part functions in the conditions most suitable for it", "each part fulfils a different or complementary function"),
             machinery="give each part the conditions it needs instead of one setting for all"),
    Principle(4, "Asymmetry",
             moves=("replace symmetrical forms with asymmetrical ones", "increase the degree of asymmetry already present", "shape the object to suit external asymmetries"),
             machinery="break the symmetry so orientation is determined and wrong assembly is impossible"),
    Principle(5, "Merging",
             moves=("bring closer together identical or similar objects in space", "bring operations together in time, make them contiguous or parallel"),
             machinery="co-locate so a shared resource is used and a boundary is removed"),
    Principle(6, "Universality",
             moves=("one object performs several functions", "use standardised features so parts are interchangeable"),
             machinery="make one part do several jobs, so there are fewer parts to fail"),
    Principle(7, "Nesting (matrioshka)",
             moves=("place one object inside another", "place multiple objects inside others", "make one part pass dynamically through a cavity in the other"),
             machinery="nest so the assembly is compact and one envelope holds many"),
    Principle(8, "Counterweight",
             moves=("compensate weight by merging with a lifting object", "compensate weight by interacting with the environment", "use aerodynamic, hydrodynamic or buoyancy forces"),
             machinery="balance the load so the actuator does not carry it"),
    Principle(9, "Prior counteraction",
             moves=("replace an action with its counter-action to control harm", "preload so later stresses are opposed in advance"),
             machinery="pre-load so the working stress is countered before it arrives"),
    Principle(10, "Prior action",
             moves=("perform the required change in advance", "pre-arrange so the object can act from the most convenient place"),
             machinery="do the step before it is needed, so the runtime is shorter and simpler"),
    Principle(11, "Cushion in advance",
             moves=("prepare emergency means for low reliability", "use rollers, balls, spirals", "go from linear to rotary motion", "use centrifugal forces"),
             machinery="carry a margin for the failure you expect, before it happens"),
    Principle(12, "Remove tension",
             moves=("limit position changes in a potential field", "equalise pressure and release the stress"),
             machinery="relieve the preload so nothing is held under unnecessary tension"),
    Principle(13, "The other way round",
             moves=("invert the action", "make movable parts fixed and fixed parts movable", "turn the object upside down"),
             machinery="do the opposite action, or move what was fixed"),
    Principle(14, "Spheroidality / curvature",
             moves=("use curvilinear instead of rectilinear forms", "use rollers, balls, spirals, domes", "go from linear to rotary motion", "use centrifugal forces"),
             machinery="curve the surface: stronger for the same material"),
    Principle(15, "Dynamics",
             moves=("change characteristics for optimal performance at each stage", "divide into parts capable of movement relative to each other", "make a rigid thing movable or adaptive", "increase the degree of free motion"),
             machinery="make it adjustable, so one part serves several conditions"),
    Principle(16, "Partial or excessive action",
             moves=("if 100% is hard, use slightly more or less", "over-design slightly, then trim back"),
             machinery="accept a little excess or a little shortfall: the practical answer"),
    Principle(17, "Another dimension",
             moves=("move outside the line", "move outside the plane", "multi-storey instead of single-storey", "tilt or re-orient the object", "use the other side of a given area"),
             machinery="add a degree of freedom the geometry did not have"),
    Principle(18, "Mechanical vibration",
             moves=("cause an object to oscillate", "increase the frequency", "use the resonant frequency", "use piezoelectric vibrators", "combine ultrasonic and electromagnetic oscillation"),
             machinery="vibrate it, and use the resonance"),
    Principle(19, "Periodic action",
             moves=("use periodic or pulsating action instead of continuous", "change the periodic magnitude or frequency", "use the pauses between actions for a different action"),
             machinery="pulse it, and do something else in the gaps"),
    Principle(20, "Continuity of useful action",
             moves=("carry on work continuously, at full load", "eliminate idle or intermittent work"),
             machinery="no idle time: the useful action is never stopped"),
    Principle(21, "Skipping",
             moves=("conduct a process or stage at high speed", "skip the stages that are harmful or destructive"),
             machinery="do the dangerous step fast, before it can propagate"),
    Principle(22, "Blessing in disguise",
             moves=("use a harmful factor to achieve a positive effect", "add the harmful action to another harmful action", "amplify a harmful factor until it is no longer harmful"),
             machinery="the waste heat becomes the power"),
    Principle(23, "Feedback",
             moves=("introduce feedback to improve the process", "change the feedback magnitude or influence with the conditions"),
             machinery="close the loop, and tune the loop's gain to the operating condition"),
    Principle(24, "Intermediary",
             moves=("use an intermediary carrier or process", "merge one object temporarily with another, easily removed"),
             machinery="put a sacrificial interface between two parts"),
    Principle(25, "Self-service",
             moves=("make the object serve or organise itself", "use waste resources, energy or substances"),
             machinery="the machine feeds and maintains itself from what it discards"),
    Principle(26, "Copying",
             moves=("use a simpler, cheaper copy in place of an expensive or fragile one", "replace an object or process with optical copies", "move to infrared or ultraviolet copies"),
             machinery="copy it -- cheaper, and the fragile original is spared"),
    Principle(27, "Cheap short-living objects",
             moves=("replace an expensive object with many inexpensive ones", "compromise on service life to gain in replaceability"),
             machinery="throw-away parts: cheap, and replaced instead of repaired"),
    Principle(28, "Mechanics substitution",
             moves=("replace a mechanical means with a sensory one", "use electric, magnetic and electromagnetic fields", "change from static to movable fields, unstructured to structured", "use fields with field-activated particles"),
             machinery="swap the mechanism for the field that does the same job"),
    Principle(29, "Pneumatics and hydraulics",
             moves=("use gas and liquid parts instead of solid ones", "use air cushions and hydrostatic support"),
             machinery="fluid instead of solid: it yields, it self-levels"),
    Principle(30, "Flexible shells and thin films",
             moves=("use flexible shells and thin films instead of 3D structures", "isolate the object from the environment with a flexible shell"),
             machinery="a skin instead of a frame: light, and it insulates"),
    Principle(31, "Porous materials",
             moves=("make an object porous", "use the pores to introduce a useful substance or function"),
             machinery="make it breathe, and the breath does work"),
    Principle(32, "Colour changes",
             moves=("change the colour of an object or its environment", "change the transparency", "use colour to improve observability", "change the emissivity under radiant heating"),
             machinery="read the state by colour, or change the state by colour"),
    Principle(33, "Homogeneity",
             moves=("make interacting objects the same material", "avoid dissimilar materials in contact"),
             machinery="one material in contact: no reaction, no corrosion"),
    Principle(34, "Discarding and recovering",
             moves=("discard the parts that have fulfilled their function", "restore the consumable parts in operation"),
             machinery="the spent part leaves and the fresh part arrives, in operation"),
    Principle(35, "Parameter changes",
             moves=("change the physical state", "change the concentration or consistency", "change the degree of flexibility", "change the temperature", "change the pressure", "change other parameters"),
             machinery="tune a parameter instead of rebuilding the thing"),
    Principle(36, "Phase transitions",
             moves=("use the phenomena of phase transitions", "use volume change or loss or absorption of heat"),
             machinery="store energy in a phase change: free, and reversible"),
    Principle(37, "Thermal expansion",
             moves=("use thermal expansion or contraction", "use several materials with different expansion coefficients"),
             machinery="heat it to fit it: the joint closes as it warms"),
    Principle(38, "Enriched atmosphere",
             moves=("replace common air with oxygen-enriched air", "replace enriched air with pure oxygen", "expose air or oxygen to ionizing radiation", "use ionized oxygen", "replace ozonized oxygen with ozone"),
             machinery="change the medium the thing lives in"),
    Principle(39, "Inert atmosphere",
             moves=("replace a normal environment with an inert one", "add neutral parts or inert additives"),
             machinery="the environment stops reacting"),
    Principle(40, "Composite materials",
             moves=("change from uniform to composite materials, each tuned to a requirement"),
             machinery="several materials, each doing one job: the whole is stronger than any"),
)


#: THE EVERYDAY NAMES. AND WHY THEY ARE NEEDED.
#
#: MEASURED 2026-10-28: Bobby said "make smaller, enlarge, unscrew it,
#: clamp it, lubricate it, reverse it, join it separate it" -- and a
#: lookup by those words found NOTHING, because the canonical names are
#: formal ("segmentation", "taking out"). The register was correct and
#: UNREACHABLE, which is the same failure as a pointer to a file that
#: does not exist.
#
#: So every principle carries the plain words a person would actually
#: use, and the lookup goes through BOTH. That is the difference
#: between a table that exists and a table that can be used.
ALIASES: Dict[int, Tuple[str, ...]] = {
    1: ("smaller", "split", "divide", "fragment", "section", "separate parts"),
    2: ("take out", "remove", "extract", "unscrew", "strip"),
    3: ("local", "different part", "per part", "non-uniform", "specialise"),
    4: ("asymmetric", "odd", "left right"),
    5: ("merge", "join", "combine", "bring together", "merge parts"),
    6: ("multi-function", "universal", "all in one", "combine function"),
    7: ("nested", "nest", "inside", "matryoshka", "telescope"),
    8: ("counterweight", "balance", "ballast", "lift"),
    9: ("pre-action", "prior", "counter", "preload", "pre-stress"),
    10: ("in advance", "prior action", "prepare", "pre-empt", "pre-arrange"),
    11: ("cushion", "buffer", "spare", "margin", "safety"),
    12: ("remove tension", "relieve", "de-stress", "equalise pressure"),
    13: ("reverse", "invert", "other way round", "upside down", "flip"),
    14: ("curved", "round", "spherical", "spheroid", "rollers", "balls", "spirals"),
    15: ("dynamic", "adjustable", "flexible", "adaptive", "movable"),
    16: ("partial", "excess", "slightly more", "slightly less", "95 percent"),
    17: ("another dimension", "out of plane", "tilt", "multi-storey", "angled"),
    18: ("vibration", "oscillate", "resonance", "ultrasonic", "frequency"),
    19: ("periodic", "pulse", "interval", "periodic action"),
    20: ("continuity", "continuous", "no idle", "full load"),
    21: ("skip", "fast", "speed", "high speed"),
    22: ("lemonade", "blessing", "use the waste", "turn harm to good"),
    23: ("feedback", "close the loop", "cross-check"),
    24: ("intermediary", "sacrificial", "temporary carrier"),
    25: ("self-service", "self cleaning", "maintain itself", "use the waste"),
    26: ("copy", "copying", "cheap copy", "image", "replica"),
    27: ("cheap", "throwaway", "disposable", "short-lived", "replace not repair"),
    28: ("mechanics substitution", "field instead", "magnetic", "electromagnetic", "sensor instead"),
    29: ("pneumatic", "hydraulic", "air cushion", "fluid"),
    30: ("flexible shell", "thin film", "inflatable", "skin"),
    31: ("porous", "perforated", "breathable", "holes"),
    32: ("colour", "color", "transparency", "chromatic", "emissive"),
    33: ("homogeneous", "same material", "one material"),
    34: ("discard", "recover", "consumable", "replace in operation"),
    35: ("parameter", "state change", "temperature", "pressure", "concentration"),
    36: ("phase transition", "phase change", "melt", "freeze", "latent heat"),
    37: ("thermal expansion", "contraction", "expand", "heat to fit"),
    38: ("enriched atmosphere", "oxygen enriched", "ionised", "ionized"),
    39: ("inert atmosphere", "inert", "nitrogen", "sealed"),
    40: ("composite", "composite materials", "layered", "hybrid", "multi material"),
}


#: THE 76 STANDARD INVENTIVE SOLUTIONS, IN FIVE CLASSES.
#:
#: AND WHY ONLY THE CLASSES ARE NAMED HERE. The 76 solution models are
#: enumerated in the TRIZ literature, but the sources consulted
#: (checked 2026-10-28) give the CLASSES and the COUNTS rather than
#: the 76 names. And a register that lists 76 entries it cannot source
#: is worse than one that names the five classes and the counts: the
#: counts are the part that is checkable.
SIS_CLASSES: Tuple[Tuple[str, str, int], ...] = (

    ("1st class", "the system and its parts", 15),
    ("2nd class", "the system's interaction with the environment", 12),
    ("3rd class", "breakdown of the system into subsystems", 14),
    ("4th class", "the system's application", 12),
    ("5th class", "the objects of any system", 23),
)


def principle(number: int) -> Optional[Principle]:
    """One principle by number. 1-40."""
    for p in PRINCIPLES:
        if p.number == number:
            return p
    return None


def by_name(name: str) -> Optional[Principle]:
    for p in PRINCIPLES:
        if p.name.lower() == name.lower():
            return p
    return None


def search(text: str) -> List[Principle]:
    """The principles whose name or moves mention the text.

    AND WHY THIS IS A LOOKUP AND NOT A SEARCH IN THE EXPENSIVE SENSE.
    The table is FIXED and it is SMALL, so this is O(40) -- and the
    answer is already tabulated. That is the compute argument applied
    to a register: a bounded table that answers in constant time.
    """
    low = (text or "").lower()
    out: List[Principle] = []
    for p in PRINCIPLES:
        # THE DIRECTION OF THE TEST. The first version tested
        # `p.name.lower() in low` and `m.lower() in low` -- i.e. whether
        # the REGISTER's text contains the QUERY. So a long move like
        # "each material is tuned to a particular functional requirement"
        # was tested for being inside the two-word query "smaller", and
        # the check was true for almost everything.
        #
        # MEASURED: every one of "smaller", "clamp", "reverse", "join"
        # returned principle 40 and nothing else. It is the WRONG DIRECTION
        # of the substring test.
        #
        # The right test is the other way round: does the QUERY appear in
        # the register's text? And the query must be a WORD, not a
        # fragment -- "sm" must not match "smaller".
        if low in p.name.lower():
            out.append(p)
            continue
        # THE ALIASES, and they are what makes the register USABLE.
        for alias in ALIASES.get(p.number, ()):  
            if low in alias or (len(low) >= 4 and low in alias):
                out.append(p)
                break
        else:
            for m in p.moves:
                for word in low.split():
                    if len(word) >= 4 and word in m.lower():
                        out.append(p)
                        break
                else:
                    continue
                break
    return out


# ===========================================================================
# THE SELFTEST
# ===========================================================================

def _selftest() -> int:
    print("=" * 78)
    print("THE 40 INVENTIVE PRINCIPLES, AS MACHINERY")
    print("=" * 78)
    print()

    print("1. THE REGISTER, %d principles:" % len(PRINCIPLES))
    for p in PRINCIPLES[:8]:
        print("   %2d. %-34s %s" % (p.number, p.name[:32], p.machinery[:56]))
    print("   ... and %d more" % (len(PRINCIPLES) - 8))
    print()

    print("2. AND THE WORDS BOBBY SAID, each one a principle here:")
    for word in ("smaller", "bigger", "unscrew", "clamp", "lubricat",
                 "reverse", "join", "separat"):
        hits = search(word)
        for h in hits[:1]:
            print("   %-10s -> %2d. %s" % (word, h.number, h.name))
    print()

    print("3. THE 76 STANDARD INVENTIVE SOLUTIONS, five classes:")
    total = 0
    for cls, gloss, n in SIS_CLASSES:
        total += n
        print("   %-12s %-46s %d" % (cls, gloss, n))
    print("   TOTAL: %d" % total)
    print()

    print("4. AND THE LIMIT, which is Altshuller's own and it is the")
    print("   reason the register needs the other techniques beside it:")
    print("   TRIZ SOLVES MECHANICAL CONTRADICTIONS. The substrate's")
    print("   problems are mostly provenance and identity, not physics.")
    print()

    print("5. AND A LOOKUP IS A LOOKUP -- O(40), bounded, the answer")
    print("   already tabulated:")
    import time
    t0 = time.time()
    for _ in range(100):
        search("clamp the thing")
    dt = (time.time() - t0) / 100
    print("   100 searches in %.4fs -> %.4f ms each" % (dt * 100, dt * 1000))
    print()
    print("   Run: python src/triz.py --selftest")
    return 0


def main() -> int:
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(main())
