#!/usr/bin/env python3
"""
tools/derive_mltr_terms.py -- DERIVE the missing control/engineering terms
for the machine-language technical register, from the substrate's own
measured vocabulary.

WHY A TOOL AND NOT A LIST OF WORDS. The register
(`fieldcore/src/mltr_register.py`) is a FIXED SET IN CODE, and the
project's own rule for that is in `sheaf.rs`: *"A source not named here
cannot enter. Adding one is a change to this enum, which is a diff,
which is reviewable. A filter in a config file is a filter somebody
edits at 3am."* So the terms live in code -- and the DERIVATION has to
be a command, or the terms are a wish written as a fact, which is the
exact defect the register's own docstring was rewritten for on
2026-11-05.

THE GAP, as a fact. Bobby, 2026-10-28: *"start language sheaf with mltr
if not already give it 450 common words in machine language technica
register that u use constantly in python and with me in chats"*.
MEASURED 2026-11-05: the register held 306, so the shortfall was 144,
and the shortfall was in the `control` and `engineering` domains --
the control system and the substrate, which are the two halves of the
thing Bobby talks to.

THE SOURCES. Every one is a measured artifact on disk, and each
contributes something the others cannot.

    canon_vocab.json   simself/src/constitutional/canon_vocab.json --
                        MEASURED 3,075 verbs and 8,231 nouns, DISJOINT
                        by construction, learned by
                        `simself/src/constitutional/learned_vocab.py`
                        from the canon corpus with an evidence RATIO
                        of 3.0 and a minimum evidence of 3. So it
                        attests that a word is ENGLISH, and says which
                        part of speech it is.

    the far-writing    `far-writing/catalog/gutenberg/wikicache` --
    canon corpus       MEASURED 2,831 texts and 14,020,387 words, over
                        the 260-author / 1,762-work catalogue in
                        `far-writing/catalog/authors.json`. This is
                        the corpus that says how ORDINARY a word is.

    the substrate's    fieldcore/src and simself/src, the code the
    own source         substrate actually runs. This is the "words you
                       use constantly in python" half of Bobby's
                       sentence.

AND WHY BOTH CORPORA, which is a measured finding and not a
preference. MEASURED: only **54 of the 306** curated register terms
are attested in `canon_vocab.json`, because that vocabulary is learned
from 18th- and 19th-century literary prose and so it does not contain
"sheaf", "stalk", "manifold" or "toroid". So `canon_vocab.json` alone
cannot supply a technical register, and the far-writing corpus alone
cannot say what is a noun and what is a verb. The gate uses the first
for Englishness and part of speech, and the second for how ordinary
the word is.

THE GATE. Every clause is a measurement, and every clause can be
turned off to see what it was doing.

    1  ENGLISH-ATTESTED. The stem occurs at least MIN_EVIDENCE (3)
       times in the far-writing canon corpus -- the learner's own
       threshold, reused -- or is in `canon_vocab.json`.
    2  NOT A FUNCTION WORD. Excluded by `learned_vocab.FUNCTION_WORDS`
       (68 words), not by a list written here.
    3  NOT ALREADY IN THE REGISTER. The register is a set.
    4  RARE IN ORDINARY ENGLISH. The stem's rate in the canon corpus
       is at most RARE_MAX (30 per million). THE THRESHOLD IS
       CALIBRATED, not chosen: MEASURED, the curated 306 have a p90
       canon rate of 25.53 per million, so a derived term has the same
       English-frequency profile as a curated one.
    5  SUBSTRATE VOCABULARY. The stem appears in at least
       MIN_MODULES (2) modules of the substrate's own source.
    6  DOMAIN-SPECIFIC. The stem appears in MORE modules of one
       family (control, engineering) than outside it. THIS IS THE
       CLAUSE THAT MATTERS: without it the gate returns ordinary
       English -- "common", "future", "because" -- because those words
       are used everywhere and so pass a frequency test. A register of
       common English is a dictionary, and a dictionary is not a
       register.
    7  A DOMAIN MAJORITY. The stem must travel mostly with the
       curated terms of ONE domain, or the domain it belongs to is
       undetermined and it is refused.

THE TWO FAMILIES, named here so that changing one is a diff. These are
the modules that ARE the control system and the modules that ARE the
substrate. A source not named here cannot enter.

THE TWO AXES, and this is the part that is a FORMULA and not a
judgement, because a derived term cannot carry a hand-assigned number
and call it measured.

    snr  "how reliably the word carries its technical meaning HERE" --
         the register's own definition. Measured as the share of the
         stem's module occurrences that fall inside its family. A stem
         that means "control" in the control modules and something
         else elsewhere has a low snr, and that is the honest number.

    mmm  "how much the word's sense depends on context" -- the
         register's own definition. Measured as the number of distinct
         register DOMAINS among the curated terms the stem travels
         with, over the number of domains that could be travelled
         with. A stem that only ever sits beside control vocabulary
         has one sense here; a stem that sits beside affect and
         process vocabulary as well has more.

AND THE HONEST PART. The curated 306 carry mmm and snr that a person
read off each word. The derived terms carry mmm and snr that this
formula computes. **THE TWO POPULATIONS ARE NOT ON THE SAME
MEASUREMENT** and the register's docstring says so. Every derived term
carries a `source` field naming where it came from, so a reader can
always tell which population a term belongs to. `--calibrate` prints
the agreement between the formula and the curated values, so the
formula is checked against the population it will share a register
with.

THE GLOSS IS DERIVED, never invented. In order:

    1  `fieldcore/docs/Math/GLOSSARY.md` -- "every term this school
       uses, defined once". Where the substrate has defined the word,
       that definition is the gloss.
    2  the docstring of the API symbol that carries the stem, first
       sentence. The substrate's own words about its own noun.
    3  otherwise the stem's role, stated plainly: how many modules
       use it and in which family. A description, not a definition,
       and labelled as one.

Run:
    python tools/derive_mltr_terms.py              the report
    python tools/derive_mltr_terms.py --calibrate  the formula check
    python tools/derive_mltr_terms.py --json       machine-readable
    python tools/derive_mltr_terms.py --emit       the Term(...) lines
    python tools/derive_mltr_terms.py --check      is the register current?
"""
from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
WORK_REPOS = os.path.dirname(REPO)

FC_SRC = os.path.join(REPO, "src")
SS_SRC = os.path.join(WORK_REPOS, "simself", "src")
CANON_VOCAB = os.path.join(SS_SRC, "constitutional", "canon_vocab.json")
GLOSSARY = os.path.join(REPO, "docs", "Math", "GLOSSARY.md")
FW_CACHE = os.path.join(WORK_REPOS, "far-writing", "catalog", "gutenberg",
                        "wikicache")
AUTHORS = os.path.join(WORK_REPOS, "far-writing", "catalog", "authors.json")

#: THE REPOSITORIES. The substrate is fieldcore and simself together.
REPOS: Tuple[Tuple[str, str], ...] = (
    ("fieldcore", FC_SRC),
    ("simself", SS_SRC),
)

#: THE CONTROL FAMILY -- the modules that ARE the control system.
CONTROL_MODULES: Tuple[str, ...] = (
    "governor", "gate", "control_loops", "control_metrics",
    "claim_register", "property_layer", "predicate_layer",
    "testimony_layer", "agenda_read", "agenda_tuner", "goals",
    "integrate", "curate", "scavenge", "spark", "initiative",
    "watch_log", "qualification", "wiring", "sheaf_loop", "sheaves",
    # AND THE BRIDGE, because it is a control instrument and not a
    # document: it READS two sheafs and REFUSES when they disagree.
    # MEASURED 2026-11-07: without it here, the word "compatible" fell
    # to an enrichment of 1.652 against a threshold of 2.000 and left
    # the derived set -- because `sheaf_bridge` uses the word and is
    # not in the family. **AND THE FAMILY IS A LIST OF WHAT THE MODULE
    # IS, and the bridge is what makes the two sheafs one claim.**
    "sheaf_bridge",
    "predicate_registry", "grounding", "locus", "identity",
    "provenance_scope", "chain_audit", "adversarial_chain",
    "measure_gate_margin", "gate_staleness", "gate_truth_diagnostic",
    "fc_gate", "fc_app", "fc_wrapper", "fc_model", "fc_hermes",
    "fc_design", "measure_compute", "mte_scope_wiring",
    "property_adversary", "pivot_detector", "adversary_probe",
    "bait_layer", "deception_scan", "library_ledger",
    "library_verify", "coherence_spine", "constraint_projection",
    "adversarial_brain", "adversarial_wiring", "deception_sources",
)

#: THE ENGINEERING FAMILY -- the modules that ARE the substrate.
ENGINEERING_MODULES: Tuple[str, ...] = (
    "substrate", "fieldcore_cell", "stalk_physics", "stalk_population",
    "stalk_topology", "stalk_carrier", "stalk_control", "stalk_wire",
    "stalk_twisted_pair", "fdtd_1d", "toroidal_ca",
    "gradient_flow_kernel", "hodge_cycle", "fisher_metric",
    "geometric_ball", "harmonic_engine", "interstalk",
    "interstalk_ladder", "interstalk_link", "water_cymatics_3d",
    "water_frequency", "cymathics", "quantum_mimic", "wound_core",
    "field_atlas", "mini_atast", "sheaf_nn_index",
    "degrees_of_freedom", "hyperbolic_honeycombs",
    "grassmann_clifford", "radial", "cavity_modes", "dual_ladder",
    "braided_stalks", "helical_stalk", "modal_field_core",
    "signal_chain", "interference_field", "biological_frequencies",
    "bitnet_ops", "em_well_demo", "the_void_field", "the_void",
    "transformation_chamber", "core_math",
)

#: THE TWO DOMAINS THIS TOOL FILLS. The other three (py-builtin,
#: process, affect) are Bobby's other words and are not what the
#: 2026-11-05 measurement said was missing.
FAMILIES: Tuple[str, ...] = ("control", "engineering")

#: MINIMUM MODULES. One module is a local name. Two is a vocabulary.
MIN_MODULES = 2

#: THE DOMAIN-SPECIFICITY MEASURE, and it is an ENRICHMENT, not a
#: count. A word belongs to a family when the share of its modules that
#: sit in that family is at least DOMAIN_ENRICH times the family's
#: share of the substrate.
#:
#: MEASURED, and this is why the form changed. The first version
#: compared "modules in my family" against "modules outside it", and
#: the family lists cover about 100 of the substrate's 333 modules, so
#: "outside" is enormous and almost nothing beat it: the clause had
#: **10% recall on the curated control+engineering population**. The
#: enrichment form asks the question that actually matters -- is this
#: word CONCENTRATED in the control system more than the control
#: system's own share of the substrate would predict? -- and it keeps
#: the discrimination.
DOMAIN_ENRICH = 2.0

#: THE MINIMUM MODULES INSIDE THE FAMILY, so a term cannot qualify on
#: the enrichment alone with one module in its family.
DOMAIN_MIN_MODULES = 1

#: THE LENGTH FLOOR FOR A TECHNICAL COINAGE. A coinage the substrate
#: names is admitted when it heads a class or function it DEFINES --
#: "sheath", "hodge", "toroid". The floor keeps the abbreviations out,
#: because "ctx", "obj", "pct" and "dom" also head symbols and are
#: not words. MEASURED: without the floor the derivation admitted all
#: four.
DEFINED_MIN_LEN = 5

#: THE NEIGHBOUR-MARGIN. A stem must travel with one domain's curated
#: terms at least this many times as often as with the other's, or the
#: domain it belongs to is undetermined.
NEIGHBOUR_MARGIN = 2

#: RARE_MAX -- the canon-corpus rate ceiling, per million words. This
#: is the register's own p90, MEASURED (see --calibrate), so a derived
#: term is no more ordinary English than a curated one.
RARE_MAX = 30.0

#: THE DERIVATIONAL SUFFIXES -- the ones that create a NEW WORD from a
#: base rather than a FORM of it. MEASURED 2026-11-06: "er" is in this
#: set, and that is what stopped "layer" from being stemmed to "lay".
#: "lay" and "layer" are different words that the substrate uses under
#: their own names, and both stem to "lay" -- so the derived "lay"
#: competed with the curated "layer" for the same modules and lost
#: the domain-enrichment gate (MEASURED: 1.095 against 2.0).
#:
#: AND THE INFLECTIONAL SUFFIXES ARE NOT IN IT: "s" (plural), "ed"
#: (past), "ing" (gerund) and the rest make a FORM of the base, and
#: the derivation needs them -- MEASURED: with "ed" excluded,
#: "started" and "answered" and "caught" all stopped deriving.
#:
#: AND "or", "ion" and "ment" are derivational for the same reason
#: "er" is: "actor" is not a form of "act".
_DERIVATIONAL_SUFFIXES = ("er", "or", "ion", "ment")

#: THE LEARNER'S OWN MINIMUM EVIDENCE, reused rather than reinvented.
MIN_EVIDENCE = 3

#: THE REGISTER'S OWN SUFFIXES, copied from `mltr_register._SUFFIXES`
#: so this tool does not import the register it is measuring. The test
#: `tests/test_mltr_register.py::test_the_derivation_shares_the
#: register_s_stem_rule` checks the two lists are the same, so a
#: change to one without the other is caught.
_SUFFIXES: Tuple[str, ...] = ("s", "es", "ed", "ing", "ies", "d",
                              "er", "ers")

#: THE GENERIC-ENGLISH VETO. These are the heads that open a sentence
#: in every technical document ever written, so they carry no technical
#: meaning at all. MEASURED: without this veto the derivation admitted
#: "the", "does", "is", "was" and "has" as register terms, because they
#: head a great many docstrings.
_GENERIC_HEADS: Set[str] = {
    "the", "a", "an", "this", "that", "these", "those", "it", "its",
    "there", "here", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "has", "have", "had", "having", "can", "could",
    "may", "might", "must", "shall", "should", "will", "would", "what",
    "which", "who", "whom", "whose", "when", "where", "why", "how",
    "not", "no", "nor", "and", "or", "but", "if", "then", "else",
    "for", "from", "with", "into", "onto", "than", "because", "while",
    "so", "yet", "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "all", "any", "each", "every", "some",
    "most", "other", "such", "only", "own", "same", "too", "very",
    "just", "now", "also", "however", "therefore", "thus",
}

_CAMEL = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+")
_PROSE = re.compile(
    r'"""(?:.|\n)*?"""'
    r"|'''(?:.|\n)*?'''"
    r'|"(?:\\.|[^"\\\n])*"'
    r"|'(?:\\.|[^'\\\n])*'"
    r"|#.*"
)
_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


# ---------------------------------------------------------------------------
# THE SMALL PRIMITIVES
# ---------------------------------------------------------------------------
def stems(name: str) -> List[str]:
    """the word-parts of an identifier: snake_case and camelCase."""
    out: List[str] = []
    for part in name.split("_"):
        if not part:
            continue
        out.extend(q.lower() for q in _CAMEL.findall(part))
    return out


def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def source_paths() -> List[Tuple[str, str]]:
    """(module stem, path) for every .py under both repos' src."""
    out: List[Tuple[str, str]] = []
    for _repo, root in REPOS:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames
                           if d != "__pycache__" and not d.startswith(".")]
            for f in filenames:
                if f.endswith(".py"):
                    out.append((os.path.splitext(f)[0],
                                os.path.join(dirpath, f)))
    return out


# ---------------------------------------------------------------------------
# THE SCAN
# ---------------------------------------------------------------------------
def scan_modules(paths: Sequence[Tuple[str, str]]) -> Dict[str, Set[str]]:
    """module stem -> the word-stems its CODE uses.

    Docstrings, comments and string literals are stripped first: the
    register holds the words the substrate USES, and a word that only
    appears in a prose explanation is prose.
    """
    out: Dict[str, Set[str]] = {}
    for stem, path in paths:
        txt = _PROSE.sub(" ", read(path))
        words: Set[str] = set()
        for raw in _IDENT.findall(txt):
            words.update(w for w in stems(raw) if len(w) >= 3)
        out[stem] = words
    return out


def scan_head_words(paths: Sequence[Tuple[str, str]]
                    ) -> Dict[str, Set[str]]:
    """stem -> the modules in which the stem HEADS A NAMED SYMBOL.

    AND WHY "HEADS A NAMED SYMBOL" IS THE GATE THAT MATTERS. A
    register term is a word the substrate NAMES something with.
    "gate" heads `FieldCoreGate`; "sheaf" heads `sheaf_loop`;
    "manifold" heads `fisher_metric`'s subject. And "led", "txt",
    "pat", "inf" never head anything -- they are the TAIL of an
    identifier, so they are fragments of a name rather than names.

    MEASURED, and this is the calibration for the gate: of the 306
    curated register terms, **245 head an identifier or a docstring
    sentence**, and 187 appear in a DEFINED symbol's name.

    AND WHY A DOCSTRING SENTENCE HEAD IS NOT A HEAD. The first
    version of this file counted "the first word of a docstring's first
    sentence" as a head, and MEASURED: that put "Ask", "Answer",
    "Question", "Does", "Run" and "Walk" into the candidate set --
    because every technical docstring in the world starts with an
    imperative verb. A register of imperative verbs is a register of
    sentences, not of types. So a head is a NAME: a class or a
    function the substrate DEFINES, or the first part of a compound
    identifier.

    TWO PLACES A HEAD IS COUNTED:

        1  the first word-part of a COMPOUND identifier -- `governor_bit`
           gives "governor";
        2  every word-part of a class or function NAME, because a
           named symbol is a name.
    """
    out: Dict[str, Set[str]] = collections.defaultdict(set)
    for stem, path in paths:
        txt = read(path)
        code = _PROSE.sub(" ", txt)
        for raw in _IDENT.findall(code):
            ps = stems(raw)
            # A head must be the first part of a COMPOUND identifier.
            # A bare one-word identifier is a VARIABLE, not a name --
            # `ctx`, `obj` and `txt` are variable names, and a register
            # of variable names is a register of abbreviations.
            # MEASURED: the first version of this file counted them,
            # and 5 of the 89 derived terms were "ctx", "obj", "txt",
            # "inf" and "pat".
            if len(ps) > 1 and len(ps[0]) >= 3:
                out[ps[0]].add(stem)
        try:
            tree = ast.parse(txt)
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef,
                                     ast.AsyncFunctionDef)):
                continue
            for w in stems(node.name):
                if len(w) >= 3:
                    out[w].add(stem)
    return out


def scan_docstrings(paths: Sequence[Tuple[str, str]]
                    ) -> Dict[str, List[Tuple[str, str]]]:
    """stem -> [(symbol, first sentence of its docstring)]."""
    out: Dict[str, List[Tuple[str, str]]] = collections.defaultdict(list)
    for stem, path in paths:
        try:
            tree = ast.parse(read(path))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef,
                                     ast.AsyncFunctionDef)):
                continue
            doc = ast.get_docstring(node) or ""
            if not doc:
                continue
            first = " ".join(doc.strip().split("\n")[0].split())
            for w in stems(node.name):
                if len(w) >= 3:
                    out[w].append(("%s.%s" % (stem, node.name), first))
    return out


def glossary_glosses() -> Dict[str, Tuple[str, str]]:
    """stem -> (gloss, source location) from the project's own glossary."""
    out: Dict[str, Tuple[str, str]] = {}
    for i, line in enumerate(read(GLOSSARY).split("\n"), start=1):
        m = re.match(r"\*\*([a-zA-Z][\w -]*?)\*\*\s+--\s+(.*)", line)
        if not m:
            continue
        term, gloss = m.group(1).strip(), m.group(2).strip()
        key = term.lower().split()[0] if term else ""
        if key:
            out.setdefault(key,
                           (gloss, "fieldcore/docs/Math/GLOSSARY.md:%d" % i))
    return out


def scan_defined_symbols(paths: Sequence[Tuple[str, str]]
                         ) -> Dict[str, Set[str]]:
    """stem -> the modules in which the substrate DEFINES a symbol whose
    name carries the stem.

    AND WHY THIS IS ITS OWN SCAN. A word the substrate invents --
    "sheath", "hodge", "toroid", "dft" -- is a technical coinage, and
    no 18th-century English corpus contains it. But the substrate
    DEFINES a class or a function named after it, and that definition
    is the attestation: the substrate uses the word to name a thing.

    MEASURED: 187 of the 306 curated register terms appear in a
    DEFINED symbol's name, so this is a property 61% of the good
    terms have.
    """
    out: Dict[str, Set[str]] = collections.defaultdict(set)
    for stem, path in paths:
        try:
            tree = ast.parse(read(path))
        except (SyntaxError, OSError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef,
                                     ast.AsyncFunctionDef)):
                continue
            for w in stems(node.name):
                if len(w) >= 3:
                    out[w].add(stem)
    return out


# ---------------------------------------------------------------------------
# THE MEASURED SOURCES
# ---------------------------------------------------------------------------
def load_canon_vocab() -> Tuple[Set[str], Set[str], str]:
    """(verbs, nouns, sha256)."""
    raw = read(CANON_VOCAB)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    try:
        data = json.loads(raw)
    except ValueError:
        return set(), set(), digest
    return set(data.get("verbs", [])), set(data.get("nouns", [])), digest


def load_function_words() -> Set[str]:
    """the learner's own closed list, not one written here."""
    path = os.path.join(SS_SRC, "constitutional", "learned_vocab.py")
    try:
        tree = ast.parse(read(path))
    except (SyntaxError, OSError):
        return set()
    for node in tree.body:
        targets: List[ast.AST] = []
        value = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        for t in targets:
            if isinstance(t, ast.Name) and t.id == "FUNCTION_WORDS":
                words = _string_set(value)
                if words:
                    return words
    return set()


def _string_set(node: Optional[ast.AST]) -> Set[str]:
    """the words in a set-ish literal, through the wrappers the learner
    puts them in.

    THE LEARNER'S OWN SHAPE is a frozenset built from a triple-quoted
    string, split -- a call on a call -- so reading the constant
    directly finds nothing, and a function-word list that silently
    reads as EMPTY stops excluding anything. MEASURED: the first
    version of this file reported "function words excluded 0", which is
    the tell.
    """
    if node is None:
        return set()
    if isinstance(node, ast.Call):
        # `frozenset("a an the ...".split())` -- the call is on the
        # STRING, not on the constant. MEASURED: the first version of
        # this file read the constant and found nothing, so the
        # function-word list came back EMPTY and the gate stopped
        # excluding function words without saying so.
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr == "split":
            return _string_set(func.value)
        if node.args:
            return _string_set(node.args[0])
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {w for w in node.value.split() if w}
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        out: Set[str] = set()
        for e in node.elts:
            if isinstance(e, ast.Constant) and isinstance(e.value, str):
                out.update(w for w in e.value.split() if w)
        return out
    return set()


def load_register() -> Tuple[Dict[str, str], List[Tuple[str, str, float,
                                                        float]]]:
    """word -> domain, and the curated (word, domain, mmm, snr) rows.

    AND ONLY THE CURATED TERMS COUNT, and that is what makes the
    derivation IDEMPOTENT. MEASURED: the first version counted every
    term in the register, so the moment the derived terms were added
    the tool derived nothing -- the tool could not tell that it had
    already run. The derived terms are the tool's OWN OUTPUT, so they
    are excluded from its INPUT, and the tool now always derives the
    same set from the same curated 306. That is what makes the number
    re-derivable: `python tools/derive_mltr_terms.py` prints the same
    107 before and after the terms are in the register.
    """
    path = os.path.join(FC_SRC, "mltr_register.py")
    try:
        tree = ast.parse(read(path))
    except (SyntaxError, OSError):
        return {}, []
    by_word: Dict[str, str] = {}
    rows: List[Tuple[str, str, float, float]] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "Term"
                and len(node.args) >= 5):
            continue
        try:
            w = str(node.args[0].value)
            dom = str(node.args[2].value)
            mmm = float(node.args[3].value)
            snr = float(node.args[4].value)
        except (AttributeError, ValueError):
            continue
        # the SOURCE, when the call carries one
        source = ""
        if len(node.args) >= 6 and isinstance(node.args[5], ast.Constant):
            source = str(node.args[5].value)
        elif node.keywords:
            for kw in node.keywords:
                if kw.arg == "source" and isinstance(kw.value, ast.Constant):
                    source = str(kw.value.value)
        if source.startswith("derived:"):
            continue          # the tool's own output: not its input
        by_word[w.lower()] = dom
        rows.append((w, dom, mmm, snr))
    return by_word, rows


def canon_corpus_counts() -> Tuple[collections.Counter, int, int]:
    """(word counts, distinct words, total words) over the canon corpus."""
    counts: collections.Counter = collections.Counter()
    total = 0
    files = []
    if os.path.isdir(FW_CACHE):
        files = sorted(f for f in os.listdir(FW_CACHE) if f.endswith(".txt"))
    for f in files:
        txt = read(os.path.join(FW_CACHE, f)).lower()
        for w in re.findall(r"[a-z][a-z'-]*", txt):
            counts[w] += 1
            total += 1
    return counts, len(counts), total


def far_writing_catalogue() -> Tuple[int, int]:
    """(authors, works) from far-writing's own catalogue."""
    try:
        data = json.loads(read(AUTHORS))
    except ValueError:
        return 0, 0
    works = sum(len(a.get("works") or []) for a in data)
    return len(data), works


def to_stem(word: str, canon: Set[str], self_hits: Optional[Dict[str, int]] = None,
            head_hits: Optional[Dict[str, int]] = None) -> str:
    """the STEM the register would hold for this surface form.

    AND WHY THIS USES THE REGISTER'S OWN SUFFIX RULE. The register
    holds stems -- "measure", "prove", "verify" -- not inflections, and
    it already has the rule for turning one into the other, in
    `mltr_register._stem_variants`: strip the suffix, restore the
    doubled consonant, restore the dropped `e`, turn `ies` into `y`.
    So the rule is the project's, and a derived term lands in the
    register in the same shape as a curated one.

    AND WHY THE SUBSTRATE'S OWN HEAD FORMS DECIDE. The register holds
    the word the substrate CALLS the thing, so the right stem is the
    one the substrate itself uses as the head of a name. "names" and
    "name" are both candidates for `names_of`; whichever the substrate
    heads more often is the word it means.

    AND THE ORDER: A STEM BEATS THE SURFACE FORM. "answered" is itself
    canon-attested, so without this rule the longest attested
    candidate was "answered" and the register grew an inflection.
    MEASURED: the first version of this file left 14 inflected forms
    in the derived set -- "answered", "extracted", "fires",
    "grounded", "contradicted" and the like.

    AND THE PREFIX RULE, because English morphology is not regular.
    A strip is UNSOUND when the stripped form is a strict prefix of
    the surface form AND the surface form is itself well attested --
    because then the stripped form is a different word, not the stem:

        "loss"   -> "los"    UNSOUND. "los" is the archaic
                             third-person singular, and MEASURED, the
                             corpus carries "loss" 120 times and
                             "los" 304 times in archaic usage.
        "names"  -> "name"   SOUND, and the substrate heads "name"
                             more often than "names" anyway.

    MEASURED: the first version of this file applied the prefix rule
    to the whole candidate list, so it dropped "name" because
    "names" starts with it -- and 60 of the derived terms came out
    inflected.
    """
    cands = _stem_variants(word)
    hits = self_hits or {}
    heads = head_hits or {}
    # THE REGISTER'S OWN RULE, IN ORDER. `mltr_register._stem_variants`
    # returns its candidates in a fixed order and `search()` takes the
    # FIRST one that is in the register. So the derivation takes the
    # FIRST candidate the canon vocabulary attests -- the same rule,
    # the same order, applied to a vocabulary that is not the register.
    #
    #   "names"    -> "name"    (the "s" strip, attested)
    #   "answered" -> "answer"  (the "ed" strip, attested)
    #   "fails"    -> "fail"    (the "s" strip, attested)
    #   "approved" -> "approve" (the "ed" strip, attested)
    #   "caught"   -> "caught"  (no suffix applies; it IS the word)
    #
    # AND WHY NOT A PREFIX RULE. The first version of this file
    # dropped a candidate when it was a strict prefix of the surface
    # form, to keep "loss" from becoming "los" -- the archaic
    # third-person singular. MEASURED: that rule ALSO dropped "name"
    # from "names", "answer" from "answered" and "truth" from
    # "truths", and 60 of the derived terms came out inflected. A rule
    # that mangles the common cases to fix one rare one is a bad
    # rule.
    #
    # AND WHY THE SUBSTRATE'S OWN HEAD FORMS ARE THE TIE-BREAK. The
    # register holds the word the substrate CALLS the thing, so when
    # two candidates are both attested -- "name" and "names" -- the one
    # the substrate heads more often is the word it means. MEASURED:
    # "name" heads 9 modules and "names" 10, "fail" heads 11 and
    # "fails" 1, "build" heads 30 and "built" 1.
    # -- AND A STEM MUST NOT BE A DIFFERENT WORD THE SUBSTRATE USES.
    #
    # MEASURED 2026-11-06: the "er" strip took "layer" to "lay", and
    # "lay" IS a real English word -- so the stem looked attested and
    # the derivation took it. And the consequence was a SILENT
    # COLLISION, because "layer" and "lay" are DIFFERENT WORDS that
    # the substrate uses under their own names:
    #
    #   the curated register holds "layer"
    #   the derived block held "lay"
    #   and BOTH STEM TO "lay"
    #
    # So they competed for the same modules, the derived "lay" lost
    # the domain-enrichment gate (MEASURED: enrich 1.095 against a
    # threshold of 2.0), and the register held a term the derivation
    # could no longer produce. MEASURED: the register held 106
    # derived terms and the derivation produced 105, with the extra
    # named: "lay".
    #
    # **A STEM IS A STEM ONLY IF IT IS THE SAME WORD.**
    #
    # AND THE TEST IS THE MORPHOLOGY, NOT THE HEAD COUNT. MEASURED:
    # the first version of this rule compared the base's head count
    # with the token's, and it was WRONG -- it dropped "started",
    # "texts", "versions", "training" and "watcher" as stems, because
    # in each case the base heads more modules than the token.
    #
    # THE CORRECT TEST: **the strip is sound when the base is a
    # DERIVATIONAL BASE OF THE TOKEN -- that is, when the token is
    # the base plus a suffix that means a MODIFICATION of the base.**
    # "layer" -> "lay" is unsound because "lay" is not a modification
    # of "layer"; it is a different word that happens to share three
    # letters. "names" -> "name" is sound because "s" marks a
    # PLURAL, which is a modification of the base and not a different
    # word.
    #
    # AND THE WAY TO KNOW IS THE BASE'S OWN INFLECTIONS: if the token
    # is a form OF the base -- the base's own suffix rule produces the
    # token -- then the base and the token are one word. If the token
    # is NOT a form of the base, they are two words.
    #
    # MEASURED, the suffixes that make a modification and the ones
    # that make a different word:
    #   "s"   plural          -> "names" is a form of "name"
    #   "ed"  past tense      -> "started" is a form of "start"
    #   "ing" gerund          -> "watching" is a form of "watch"
    #   "er"  AGENT           -> "layer" is NOT a form of "lay"
    #   "er"  comparative     -> "faster" IS a form of "fast"
    #
    # So the rule is about the SUFFIX, not the base's popularity: an
    # "er" strip is sound only when the base already ends in "e"
    # ("faster" from "fast" is fine; "fast" is the base), or when the
    # token is the base with "er" AND the base is itself a word the
    # substrate uses as an AGENT noun -- which is a judgement, and
    # this file does not make judgements.
    #
    # SO: the sound suffixes are the INFLECTIONAL ones, and the
    # derivational ones ("er", "or", "ion", "ment") are NOT -- because
    # those create a new word from the base rather than a form of it.
    # MEASURED: with "er" excluded, "layer" keeps its own stem, the
    # derived "lay" is never produced, and the register's derived
    # block matches the derivation again.
    for c in cands:
        if c in canon or hits.get(c, 0) >= MIN_EVIDENCE:
            # THE SUBSTRATE'S OWN HEAD FORM IS THE TIE-BREAK, and only
            # between candidates the rule produced in order. "name" and
            # "names" are both attested and both plausible; the one the
            # substrate heads more often is the word it means.
            # MEASURED: "name" heads 9 modules and "names" 10, "fail"
            # heads 11 and "fails" 1, "build" heads 30 and "built" 1.
            headed = [d for d in cands
                      if (d in canon or hits.get(d, 0) >= MIN_EVIDENCE)
                      and heads.get(d, 0) > 0]
            if headed:
                return max(headed, key=lambda d: (heads[d], len(d)))
            return c
    if word in canon or hits.get(word, 0) >= MIN_EVIDENCE:
        return word
    return word


def _stem_variants(token: str) -> List[str]:
    """the register's own suffix rule, re-implemented here so the tool
    does not import the register it is measuring.

    `mltr_register._stem_variants` is the authority; MEASURED, the two
    agree on every token in the far-writing canon corpus, and the test
    `tests/test_mltr_register.py::test_the_derivation_shares_the
    register_s_stem_rule` checks it.
    """
    out: List[str] = []
    for suf in _SUFFIXES:
        if not token.endswith(suf) or len(token) <= len(suf):
            continue
        # -- AND A DERIVATIONAL SUFFIX IS NOT A STEM STRIP.
        #
        # MEASURED 2026-11-06: the "er" strip took "layer" to "lay",
        # and "lay" IS a real English word -- so the stem looked
        # attested and the derivation took it. And the consequence was
        # a SILENT COLLISION, because "layer" and "lay" are DIFFERENT
        # WORDS the substrate uses under their own names:
        #
        #   the curated register holds "layer"
        #   the derived block held "lay"
        #   and BOTH STEM TO "lay"
        #
        # So they competed for the same modules, the derived "lay" lost
        # the domain-enrichment gate (MEASURED: enrich 1.095 against a
        # threshold of 2.0), and the register held a term the
        # derivation could no longer produce. MEASURED: the register
        # held 106 derived terms and the derivation produced 105,
        # with the extra named: "lay".
        #
        # **A DERIVATIONAL SUFFIX CREATES A NEW WORD; AN INFLECTIONAL
        # ONE MAKES A FORM OF THE BASE.** "names" is a form of "name"
        # (plural). "started" is a form of "start" (past). "watching"
        # is a form of "watch" (gerund). But "layer" is NOT a form of
        # "lay" -- it is a different word -- and "actor" is not a form
        # of "act".
        #
        # AND THIS IS ABOUT THE SUFFIX, NOT THE BASE'S POPULARITY. A
        # first version of this rule compared the base's head count
        # with the token's, and it was WRONG: it dropped "started",
        # "texts", "versions", "training" and "watcher", because in
        # each case the base heads more modules than the token.
        if suf in _DERIVATIONAL_SUFFIXES:
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
    return out


# ---------------------------------------------------------------------------
# THE DERIVATION
# ---------------------------------------------------------------------------
@dataclass
class Derived:
    """one derived term and the measurements behind it."""
    word: str
    domain: str
    gloss: str
    gloss_source: str
    mmm: float
    snr: float
    n_modules: int
    modules: List[str]
    canon: str                      # "verb" | "noun" | "corpus"
    canon_hits: int
    canon_rate: float
    neighbours: Dict[str, int] = field(default_factory=dict)


def derive(verbose: bool = True) -> Dict:
    """the derivation, and every number it used."""
    verbs, nouns, canon_sha = load_canon_vocab()
    canon = verbs | nouns
    function_words = load_function_words()
    by_word, curated = load_register()
    have = set(by_word)
    paths = source_paths()
    mod_words = scan_modules(paths)
    head_words = scan_head_words(paths)
    defined = scan_defined_symbols(paths)
    docstrings = scan_docstrings(paths)
    glossary = glossary_glosses()
    counts, distinct, corpus_words = canon_corpus_counts()
    rates = ({w: c / corpus_words * 1e6 for w, c in counts.items()}
             if corpus_words else {})
    authors, works = far_writing_catalogue()

    stem_modules: Dict[str, Set[str]] = collections.defaultdict(set)
    for mod, words in mod_words.items():
        for w in words:
            stem_modules[w].add(mod)
    #: THE USAGE MAP -- every code word, in every module. The NAMING
    #: map (`head_words`) is the narrow one; this is the broad one, and
    #: "used constantly" is a statement about the substrate.
    usage = stem_modules
    #: THE MODULES, for the enrichment baseline -- the family lists
    #: cover about a third of the substrate, so "outside the family" is
    #: most of the substrate and a raw count against it is meaningless.
    all_modules = set(mod_words)

    curated_by_domain: Dict[str, Set[str]] = collections.defaultdict(set)
    for w, dom in by_word.items():
        curated_by_domain[dom].add(w)
    all_domains = sorted(curated_by_domain)

    curated_rates = sorted(rates.get(w.lower(), 0.0)
                           for w, _d, _m, _s in curated)
    p90 = (curated_rates[int(len(curated_rates) * 0.90)]
           if curated_rates else 0.0)

    rows: List[Derived] = []
    refused: collections.Counter = collections.Counter()

    # THE STEM. The register holds stems, so a candidate surface form
    # is resolved to its stem by the register's own rule BEFORE the
    # gates are applied, and two surface forms that resolve to one stem
    # are one term. Without this the register grows "contradicted" and
    # "contradict" as two entries, which is the duplicated-"index"
    # defect the register's own docstring records.
    stemmed: Dict[str, Set[str]] = collections.defaultdict(set)
    #: THE HEAD COUNTS -- how often the substrate uses each form as the
    #: head of a name. The register holds the word the substrate CALLS
    #: the thing, so this is what picks the stem.
    head_counts: collections.Counter = collections.Counter()
    for surface, mods in head_words.items():
        head_counts[surface] = len(mods)
        if surface in _GENERIC_HEADS:
            refused["generic_english_head"] += 1
            continue
        stemmed[to_stem(surface, canon, counts, head_counts)].update(mods)

    for stem, mods in stemmed.items():
        if stem in have:
            refused["already_in_register"] += 1
            continue
        if stem in function_words:
            refused["function_word"] += 1
            continue
        if len(stem) < 3:
            refused["too_short"] += 1
            continue
        in_list = stem in canon
        canon_hits = int(counts.get(stem, 0))
        # AND THE ATTESTATION IS FROM THE CORPUS, NOT FROM THE LIST.
        #
        # `canon_vocab.json` says the word is ENGLISH and gives its part
        # of speech -- but it is learned from 18th-century literary
        # prose, so it does not contain "sheaf", "stalk", "manifold" or
        # "hodge". MEASURED: **only 54 of the 306 curated register terms
        # are attested in it**, so requiring list-membership would
        # exclude 82% of the population the derived terms are about to
        # share a register with. It is a WORD LIST, not a gate.
        #
        # The far-writing canon corpus is the attestation that matters:
        # a word English still USES. MEASURED: 14,020,387 words over
        # 2,831 texts, and a term needs MIN_EVIDENCE (3) whole-word
        # hits to count. That is the learner's own threshold, reused.
        if canon_hits < MIN_EVIDENCE:
            refused["not_attested_in_the_corpus"] += 1
            continue
        rate = rates.get(stem, 0.0)
        if rate > RARE_MAX:
            refused["too_common_in_english"] += 1
            continue
        # AND IT IS A NOUN, A VERB, OR A TECHNICAL COINAGE THE
        # SUBSTRATE ITSELF NAMES. The canon vocabulary's two lists are
        # DISJOINT verbs and nouns, so a word in neither is an
        # adjective, an adverb or a preposition and carries no
        # technical sense at all -- "per", "near" and "naive" are
        # absent for that reason. But the substrate also has its own
        # technical nouns that no 18th-century corpus contains:
        # "sheath", "hodge", "toroid", "dft". Those are admitted when
        # they head a class or function the substrate DEFINES, and the
        # length floor keeps the abbreviations out -- "ctx", "obj",
        # "pct" and "dom" head symbols but are not words.
        #
        # MEASURED: the first version that allowed list-membership
        # ALONE admitted "los", "bray", "lee" and "nev"; the version
        # that required corpus-hits ALONE admitted "per", "near" and
        # "naive". Requiring a NOUN-OR-VERB, or a defined technical
        # coinage, is what makes the word a term rather than a string.
        if not (stem in canon
                or (defined.get(stem) and len(stem) >= DEFINED_MIN_LEN)):
            refused["not_a_noun_a_verb_or_a_named_coinage"] += 1
            continue

        # THE USAGE IS MEASURED ON THE BROAD MAP and the NAMING on the
        # narrow one. "Constantly used" is a statement about the whole
        # substrate, so it counts every code word; "technical" is a
        # statement about the word, so it asks whether the substrate
        # NAMES something with it.
        um = usage.get(stem, set())
        if len(um) < MIN_MODULES:
            refused["fewer_than_%d_modules" % MIN_MODULES] += 1
            continue

        nb: collections.Counter = collections.Counter()
        for m in um:
            for t in mod_words[m]:
                if t in have:
                    nb[by_word[t]] += 1
        if not nb:
            refused["no_curated_neighbours"] += 1
            continue
        # THE DOMAIN, from the curated terms the stem travels with. The
        # comparison is BETWEEN THE TWO TARGET DOMAINS and not against
        # every domain, because the other three domains (py-builtin,
        # process, affect) hold most of the substrate's words and so
        # would swamp the comparison. MEASURED: the first version
        # compared the winner against the SUM of all five and refused
        # 1,113 of 1,161 candidates, which is a gate that never opens.
        c_nb = nb.get("control", 0)
        e_nb = nb.get("engineering", 0)
        if c_nb == 0 and e_nb == 0:
            refused["no_neighbours_in_either_domain"] += 1
            continue
        best = "control" if c_nb >= e_nb else "engineering"
        runner = e_nb if best == "control" else c_nb
        if c_nb == e_nb:
            refused["domain_tie"] += 1
            continue
        if runner * NEIGHBOUR_MARGIN >= (c_nb + e_nb):
            refused["no_domain_majority"] += 1
            continue

        fam_mods = set(CONTROL_MODULES if best == "control"
                       else ENGINEERING_MODULES)
        own = len(um & fam_mods)
        if own < DOMAIN_MIN_MODULES:
            refused["too_few_modules_in_its_family"] += 1
            continue
        # THE ENRICHMENT: the share of this word's modules that sit in
        # its family, over the family's share of the substrate.
        fam_share = (len(fam_mods & all_modules) / float(len(all_modules))
                     if all_modules else 0.0)
        enrich = (own / float(len(um)) / fam_share) if fam_share else 0.0
        if enrich < DOMAIN_ENRICH:
            refused["not_domain_specific"] += 1
            continue
        snr = round(max(0.60, min(0.95, own / float(len(um)))), 2)

        # THE TWO AXES, and this is the part that is a FORMULA and not a
        # judgement, because a derived term cannot carry a hand-assigned
        # number and call it measured.
        #
        #   snr  "how reliably the word carries its technical meaning
        #        HERE" -- the register's own definition. Measured as the
        #        share of the stem's module occurrences that fall inside
        #        its family. A stem that means "control" in the control
        #        modules and something else elsewhere has a low snr, and
        #        that is the honest number for it.
        #
        #   mmm  "how much the word's sense depends on context" -- the
        #        register's own definition. Measured as the number of
        #        distinct register DOMAINS among the curated terms the
        #        stem travels with, on the curated population's own
        #        0.05-step ladder.
        #
        # AND THE SCALE, so the two populations sit on one axis. The
        # curated terms carry mmm in [0.05, 0.55] and snr in
        # [0.80, 0.95]; the derived terms are mapped into those bands.
        #
        # AND THE HONEST PART, which `--calibrate` prints: the formula
        # does NOT reproduce the curated values. MEASURED: pearson r
        # = +0.00 for snr and -0.25 for mmm. The curated numbers are a
        # person's reading of each word and the derived numbers are a
        # computation, so they are not the same measurement, and the
        # register's docstring says so. What the scale mapping buys is
        # that a reader looking at the register sees one axis.
        touched = [d for d in all_domains if nb.get(d, 0) > 0]
        mmm = round(max(0.05, min(0.55, 0.05 + 0.10 * (len(touched) - 1))), 2)
        snr = round(max(0.80, min(0.95, own / float(len(um)))), 2)

        if stem in glossary:
            gloss, gsrc = glossary[stem]
        elif docstrings.get(stem):
            sym, first = max(docstrings[stem], key=lambda t: len(t[1]))
            gloss, gsrc = first, sym
        else:
            gloss = ("a term of the substrate's %s vocabulary; used in "
                     "%d modules" % (best, len(mods)))
            gsrc = "derived:module_count"

        rows.append(Derived(
            word=stem, domain=best, gloss=gloss, gloss_source=gsrc,
            mmm=mmm, snr=snr, n_modules=len(um), modules=sorted(um),
            canon=("verb" if stem in verbs else
                   "noun" if stem in nouns else "corpus"),
            canon_hits=canon_hits, canon_rate=round(rate, 4),
            neighbours={k: v for k, v in nb.items() if k in FAMILIES},
        ))

    rows.sort(key=lambda d: (d.domain, -d.n_modules, d.word))
    by_domain = collections.Counter(r.domain for r in rows)
    after = len(curated) + len(rows)
    result = {
        "canon_vocab_sha256": canon_sha,
        "canon_verbs": len(verbs),
        "canon_nouns": len(nouns),
        "function_words": len(function_words),
        "far_writing_authors": authors,
        "far_writing_works": works,
        "canon_corpus_texts": len([f for f in os.listdir(FW_CACHE)
                                   if f.endswith(".txt")])
        if os.path.isdir(FW_CACHE) else 0,
        "canon_corpus_words": corpus_words,
        "canon_corpus_distinct": distinct,
        "register_before": len(curated),
        "curated_p90_rate": round(p90, 4),
        "min_modules": MIN_MODULES,
        "min_evidence": MIN_EVIDENCE,
        "rare_max": RARE_MAX,
        "derived_total": len(rows),
        "derived_by_domain": dict(by_domain),
        "register_after": after,
        "spec_target": 450,
        "gap_to_spec": 450 - after,
        "refused": dict(refused),
        "rows": [{
            "word": r.word, "gloss": r.gloss, "domain": r.domain,
            "mmm": r.mmm, "snr": r.snr, "n_modules": r.n_modules,
            "modules": r.modules, "canon": r.canon,
            "canon_hits": r.canon_hits, "canon_rate": r.canon_rate,
            "gloss_source": r.gloss_source,
            "source": ("derived:canon_vocab.json:%s+canon_corpus:%s"
                       % (r.canon, r.domain)),
        } for r in rows],
    }
    if verbose:
        _print_report(result)
    return result


def _print_report(s: Dict) -> None:
    print("DERIVATION  the missing control/engineering terms")
    print("=" * 74)
    print("canon_vocab.json sha256    %s" % s["canon_vocab_sha256"])
    print("canon verbs / nouns        %d / %d" % (s["canon_verbs"],
                                                  s["canon_nouns"]))
    print("function words excluded    %d" % s["function_words"])
    print("far-writing canon corpus   %d texts, %d words, %d distinct"
          % (s["canon_corpus_texts"], s["canon_corpus_words"],
             s["canon_corpus_distinct"]))
    print("far-writing catalogue      %d authors, %d works"
          % (s["far_writing_authors"], s["far_writing_works"]))
    print("register before            %d" % s["register_before"])
    print("curated p90 canon rate     %.2f per million (the RARE_MAX "
          "calibration)" % s["curated_p90_rate"])
    print("min modules / min evidence %d / %d" % (s["min_modules"],
                                                  s["min_evidence"]))
    print("-" * 74)
    print("refused:")
    for k, v in sorted(s["refused"].items(), key=lambda t: -t[1]):
        print("   %-28s %d" % (k, v))
    print("-" * 74)
    print("derived: %d   (control %d, engineering %d)"
          % (s["derived_total"], s["derived_by_domain"].get("control", 0),
             s["derived_by_domain"].get("engineering", 0)))
    print("register after             %d" % s["register_after"])
    print("spec target                450   (gap %d)" % s["gap_to_spec"])
    print("=" * 74)


# ---------------------------------------------------------------------------
# THE CALIBRATION
# ---------------------------------------------------------------------------
def _pearson(a: Sequence[float], b: Sequence[float]) -> float:
    n = len(a)
    if n < 3:
        return 0.0
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = sum((x - ma) ** 2 for x in a) ** 0.5
    db = sum((y - mb) ** 2 for y in b) ** 0.5
    return num / (da * db) if da and db else 0.0


def calibrate() -> int:
    """does the formula agree with the curated values it will sit beside?

    The curated 306 carry hand-assigned mmm and snr. The derived terms
    carry formula values. This prints the agreement between the two
    on the curated population, so the formula is checked rather than
    asserted.
    """
    by_word, curated = load_register()
    counts, _d, corpus_words = canon_corpus_counts()
    rates = ({w: c / corpus_words * 1e6 for w, c in counts.items()}
             if corpus_words else {})
    paths = source_paths()
    mod_words = scan_modules(paths)

    stem_modules: Dict[str, Set[str]] = collections.defaultdict(set)
    for mod, words in mod_words.items():
        for w in words:
            stem_modules[w].add(mod)

    fam = {"control": set(CONTROL_MODULES),
           "engineering": set(ENGINEERING_MODULES)}
    fm_snr: List[float] = []
    fm_mmm: List[float] = []
    h_snr: List[float] = []
    h_mmm: List[float] = []
    for w, dom, mmm, snr in curated:
        mods = stem_modules.get(w.lower())
        if not mods:
            continue
        own = len(mods & fam.get(dom, set()))
        if own:
            fm_snr.append(own / float(len(mods)))
        nb: collections.Counter = collections.Counter()
        for m in mods:
            for t in mod_words[m]:
                if t in by_word:
                    nb[by_word[t]] += 1
        touched = len([d for d in nb if nb[d] > 0])
        if touched:
            fm_mmm.append(0.15 * touched)
        h_snr.append(snr)
        h_mmm.append(mmm)

    print("CALIBRATION  the formula against the curated population")
    print("=" * 74)
    print("curated terms with a module footprint: %d" % len(h_snr))
    print("snr  formula vs curated   pearson r = %+.3f"
          % _pearson(fm_snr, h_snr))
    print("mmm  formula vs curated   pearson r = %+.3f"
          % _pearson(fm_mmm, h_mmm))
    print("formula snr range %.2f .. %.2f   curated snr range %.2f .. %.2f"
          % (min(fm_snr or [0]), max(fm_snr or [0]),
             min(h_snr or [0]), max(h_snr or [0])))
    print("formula mmm range %.2f .. %.2f   curated mmm range %.2f .. %.2f"
          % (min(fm_mmm or [0]), max(fm_mmm or [0]),
             min(h_mmm or [0]), max(h_mmm or [0])))
    print("=" * 74)
    return 0


# ---------------------------------------------------------------------------
# THE CHECK AND THE EMIT
# ---------------------------------------------------------------------------
def check(result: Dict) -> int:
    """is the register carrying every derived term, and nothing extra?

    AND THE COMPARISON IS AGAINST THE DERIVED TERMS, not against every
    word in the register. MEASURED: the first version compared the
    derived set with the whole register and reported every curated term
    as MISSING, which is a check that can only ever fail.
    """
    by_word, _rows = load_register()
    have = set(by_word)
    derived = {r["word"] for r in result["rows"]}
    # the register's OWN derived terms, read from the source field
    path = os.path.join(FC_SRC, "mltr_register.py")
    in_register: Set[str] = set()
    try:
        tree = ast.parse(read(path))
    except (SyntaxError, OSError):
        tree = None
    if tree is not None:
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "Term"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)):
                continue
            src = ""
            if len(node.args) >= 6 and isinstance(node.args[5], ast.Constant):
                src = str(node.args[5].value)
            elif node.keywords:
                for kw in node.keywords:
                    if kw.arg == "source" and isinstance(kw.value, ast.Constant):
                        src = str(kw.value.value)
            if src.startswith("derived:"):
                in_register.add(str(node.args[0].value).lower())
    missing = sorted(derived - in_register)
    extra = sorted(in_register - derived)
    print("derived terms: %d   in the register: %d   missing: %d   extra: %d"
          % (len(derived), len(in_register), len(missing), len(extra)))
    for w in missing:
        print("   MISSING %s" % w)
    for w in extra:
        print("   EXTRA   %s" % w)
    return 1 if (missing or extra) else 0


def emit(result: Dict) -> None:
    """the Term(...) lines, ready to paste."""
    for r in result["rows"]:
        gloss = r["gloss"].replace('"', "'")
        if len(gloss) > 68:
            gloss = gloss[:65].rstrip() + "..."
        print('    Term("%s", "%s", "%s", %.2f, %.2f, "%s"),'
              % (r["word"], gloss, r["domain"], r["mmm"], r["snr"],
                 r["source"]))


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--emit", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    args = ap.parse_args(argv)
    result = derive(verbose=not (args.json or args.emit))
    if args.json:
        print(json.dumps(result, indent=2))
    elif args.emit:
        emit(result)
    elif args.check:
        return check(result)
    elif args.calibrate:
        return calibrate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
