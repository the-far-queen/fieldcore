"""
mltr_register.py -- THE MACHINE-LANGUAGE TECHNICAL REGISTER. 450 words.

Bobby, 2026-10-28: *"start language sheaf with mltr if not already give
it 450 common words in machine language technica register that u use
constantly in python and with me in chats"*

AND WHY A REGISTER AND NOT A DICTIONARY. The project's own rule, in
`sheaf.rs`: "A source not named here cannot enter. Adding one is a
change to this enum, which is a diff, which is reviewable. A filter in
a config file is a filter somebody edits at 3am." So the register is a
FIXED SET IN CODE, and the count is checked by a test. A register of
"whatever words came to mind" is a bag; a register of 450 named terms
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

THE COUNT IS 450, and a test checks it, because "450 words" is a
specification and a specification that is not checked is a wish.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class Term:
    """One word of the register.

    AND WHY IT IS FROZEN. The register is a fixed set, and a term that
    could be mutated in place would be a filter somebody edits at 3am.
    """
    word: str
    gloss: str
    domain: str
    mmm: float
    snr: float

    def describe(self) -> str:
        return "%-14s %-11s mmm=%.2f snr=%.2f  %s" % (
            self.word, self.domain, self.mmm, self.snr, self.gloss)


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
    Term("index", "the position of a value", "py-builtin", 0.15, 0.90),
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
    Term("index", "a list for finding things", "process", 0.25, 0.90),
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
)


def words() -> List[str]:
    """The register's words, in order."""
    return [t.word for t in REGISTER]


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


def search(text: str) -> List[Term]:
    """The register's terms that occur in a text."""
    low = (text or "").lower()
    out: List[Term] = []
    for t in REGISTER:
        if t.word.lower() in low:
            out.append(t)
    return out
