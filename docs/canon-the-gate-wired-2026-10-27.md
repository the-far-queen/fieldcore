# The gate, wired: what works, and what the numbers are

**Filed 2026-10-27 by Hermes, from Bobby's session.**

Bobby, 2026-10-27, twice — and the second time he said **"do not make
the gate perfect we need to move on just working the gate will evolve
with fc as u self code"**:

> *"review fc atlas simself we were working on a real gate — see last
> session wire together but focus on gates that work"*

> *"review fc all modules ie gov controller qualification tool call mini
> llm safety layer wire subs for mte etc wire the whole system now make
> it run as a wrapper for hermes so minimax in hermes in fc"*

So this file is not about a better gate. It is about **the gate, wired**,
and the measurements that decided what goes where.

---

## THE FINDING THAT DECIDED EVERYTHING

**The false-positive rate on the system's OWN output had never been
measured.** The canon doc of 2026-10-26 has catch rates on three
adversary sets — and not one number for what the gate does to ordinary
answers.

So this session measured it. The corpus was this machine's own session
database:

| set | what it is | size |
|---|---|---|
| **real replies** | assistant messages from `state.db` | 5,512 messages / 24,428 chunks |
| **real tool calls** | the `tool_calls` column | 11,268 calls |

**AND THE NUMBERS, per layer:**

| layer | catch (fresh adversary) | false positive (real replies) |
|---|---|---|
| claim | 39.1% | 0.18% |
| **scope** | **1.6%** | **4.67%** |
| property | 12.5% | 0.00% |
| predicate | 21.9% | 0.00% |
| testimony | 39.1% | 0.00% |
| union of 5 | 81.2% | 4.85% |
| **union of 4 (no scope)** | **81.2%** | **0.18%** |

### THE SCOPE LAYER IS NOT IN THE REPLY PATH

It costs 4.67% false positives for 1.6% catch. The reason is exact: it
reads version strings as dangling references, so it refused

    - OS: Windows 11 Home Single Language (Build 26100)
    - CPU: 12th Gen Intel Core i5-1235U — 10 cores / 12 threads

**The union of four catches exactly as much as the union of five, and is
27× cleaner.** So the scope layer is a **TOOL layer** — it belongs in the
MTE wrapper, where the span *is* about a build. It does not belong in
front of a reply. That is where it went: `fc_model.py` attaches it to the
wrapper.

---

## THE HARD/ADVISORY SPLIT, and it came out of the measurement

**96 of the 103 false positives came from the agenda layer**, and 7 from
the deny lexicon.

The agenda layer reads **INTENT** — "this span is asking for the
guarantee to be relaxed". Its frames include bare modals: *could, may,
whatever, parameter, argument, override*. Those words occur in ordinary
writing about the project's own design:

    "simself's persistence layer (MVCC across substrates) could use this."
    "**may be fine if cwd is right**; test was wrong"

So the layer reads a HEDGED SUGGESTION about the project as an ATTACK on
the project. **The layer is right about the attack and wrong about the
writing around it** — so the gate owns the blast radius and the layer
keeps its vocabulary:

| catch | what it means | reply path | tool path |
|---|---|---|---|
| **hard** | the span says something FALSE about the system | refuses | refuses |
| **advisory** | the span asks for the guarantee to be RELAXED | **flags** | refuses |

**AND WHY THE TOOL PATH IS STRICTER:** a blocked tool call costs a turn;
a lost reply costs an answer. So the reply path fails open on an advisory
catch and the tool path fails closed.

---

## THE TOOL PATH READS INTENT, NOT PAYLOAD

Reading a tool call's **full payload** gave a **2.343%** veto rate on
11,268 real tool calls — and **every sampled catch was innocent**:

    [write_file] test_psi_0_immutable_under_frequency — REWRITTEN: ψ_0 immutability
    [patch]     assert np.allclose(psi_0_before, psi_0_after), "ψ_0 must be immutable"
    [run_code]  **the atlas exam grows with the system.**

A test file whose docstring says "psi_0 must be immutable" is not an
attack on the ground — it is a test **asserting** the ground is protected.

**SO THE TOOL PATH READS THE OPERATION:** the tool name, the path-like
arguments, and the short flag-like arguments. The bulk content is
excluded by argument NAME (`content`, `text`, `body`, `code`, …).

| tool path | veto rate | cost |
|---|---|---|
| full payload | 2.343% | 7.59 ms |
| **intent only** | **0.151%** | **0.68 ms** |

---

## TWO LAYER DEFECTS, FOUND BY THE PLUGIN'S OWN TEST

**Both were fixed at the layer and not at the gate**, because a layer that
is wrong about a word should be fixed about the word.

### 1. "im**mutable**" matched "mutable"

`property_layer` matched the property by plain substring, so a test
asserting the ground IS protected was refused for claiming it is mutable:

    "psi_0 immutability under tick(): the ground must be immutable"
    -> REFUSED: the_ground has the property 'mutable', and it does not

**THE FIX:** the property is matched as a PHRASE on word boundaries — and
"immutable" is not "mutable".

**AND THE POLARITY, which was the second half of the same defect:** "the
ground is not mutable" ASSERTS that the ground is write-protected. It is
the truth. So a negator immediately before the property turns the
assertion into a denial, and a denied property is not a false one.

### 2. `claim_register` imported numpy and never used it

`import numpy as np` at module level, and `np.` appears **zero times** in
the file. It cost the module's availability and nothing else.

**AND IT COST THE GATE.** The plugin runs inside Hermes' own python,
which has no numpy — so a dead import meant the claim layer could not
load there at all. And the claim layer is the one that catches 39.1% of
the fresh adversary at a 0.18% false-positive rate.

---

## THE REFUSAL DOES NOT REPEAT THE CLAIM

The first marker said:

    [the FieldCore gate refused this span: the span asserts that
     the_ground has the property 'an ordinary json file', and it does not]

**A refusal that restates the claim is a second delivery of the claim.**
So the marker names the **instrument** and nothing else:

    [the FieldCore gate refused this span: the property layer]

---

## THE WIRING

```
    +--------------------------------------------------+
    |  FIELDCORE                                       |
    |    src/fc_gate.py     the gate, four layers        |
    |    src/fc_model.py    the model call, MiniMax in  |
    |    src/governor.py    the 1-bit veto              |
    |    +------------------------------------------+  |
    |    |  HERMES                                 |  |
    |    |    plugins/fieldcore-gate/                |  |
    |    |      pre_tool_call        THE VETO       |  |
    |    |      transform_llm_output THE REPLY      |  |
    |    |    +------------------------------+    |  |
    |    |    |  MINIMAX                     |    |  |
    |    |    |    minimax_client.py          |    |  |
    |    |    +------------------------------+    |  |
    |    +------------------------------------------+  |
    +--------------------------------------------------+
```

**THE GATE SITS AT THE SEAMS, NOT IN THE MIDDLE.** A gate between Hermes
and MiniMax would intercept the model's own text — and the reply-path gate
already reads that text. Two gates on the same text is one gate and half
the cost. And the tool call never goes near MiniMax — it goes to the
filesystem — so it needs its own seam: `pre_tool_call`.

**`pre_tool_call` IS THE ONLY HOOK HERMES TREATS AS POLICY:** a raise or a
timeout there becomes a **block directive**, not a pass. So that is the
one place a refusal may cost a turn.

### THE ORDER INSIDE `fc_model.py`

    1. THE GATE reads the PROMPT
    2. THE MODEL answers
    3. THE MTE reads the ANSWER  (echo, poison, scope)
    4. THE GATE reads the ANSWER (is it TRUE)
    5. THE GOVERNOR is consulted last

**The answer is checked TWICE by two different instruments, because they
answer different questions:** the MTE asks *is this text well formed*; the
gate asks *is this text true*.

**AND THE SPEND GUARD IS CLOSED BY DEFAULT** — `GABRIELLE_ALLOW_LIVE=1`.
"Do not use my credit card pls" is a standing instruction.

---

## THE ATLAS: TWO FAILURES CLEARED

The atlas-exam found two capabilities that existed and nothing called:

    [FAIL] 16 spawning    research/agent_pool.py        0 inbound callers
    [FAIL] 17 extraction  constitutional/repo_scanner.py 0 inbound callers

**Both are Bobby's own named work** — the extractor IS the scavenger, the
agent pool IS the spawning. And the reachability check is an AST audit of
the substrate's own source, so the fix is the substrate calling its own
capabilities, **through the gate**:

    simself/src/wiring.py

Which implements the atlas's two demands literally:

| demand | how |
|---|---|
| extraction must attach provenance to every item | every item carries `source`, `scanned_at`, `digest` |
| extraction must never write the substrate directly | the write path refuses any destination inside the ground's tree |
| spawning must be bounded | the gate is asked BEFORE the pool is asked to spawn |
| spawning must be gated | the spawn request is read before any child exists |
| a child must not get write authority over the parent ground | **a CONSTANT, not a setting** — there is no argument to pass |

**atlas-exam: 9/23 → 11/23.** The exam still reports FAIL, because eight
areas are TODO and an unimplemented area is not a passing area.

---

## THE FILES

| file | what it is |
|---|---|
| `fieldcore/src/fc_gate.py` | the gate: one entry point, four layers, hard/advisory |
| `fieldcore/src/fc_model.py` | MiniMax inside FC: prompt→model→MTE→gate→governor |
| `fieldcore/tests/test_fc_gate.py` | 17 tests, incl. the false-positive test on real output |
| `simself/src/wiring.py` | the substrate's own wiring: extraction and spawning, gated |
| `hermes/plugins/fieldcore-gate/` | the plugin: the veto, the reply, the record |

Suites: fieldcore **876 passed, 1 xfailed**; simself **518 passed, 2
skipped**; atlas-exam **79 passed**.

---

## THE NUMBER TO QUOTE

The gate's own rate on an **unfitted** adversary (the fresh set), and its
own rate on the system's **real** output:

| | |
|---|---|
| fresh adversary, any catch | **81.2%** |
| fresh adversary, hard catch | 71.9% |
| **real messages hard-refused** | **0.96%** |
| **real tool calls vetoed (intent)** | **0.151%** |
| cost per message | 1.9 ms |
| cost per tool call | 0.68 ms |

**AND THE HONEST LIMIT:** 0.96% of the system's own honest output is still
refused. That is the number to bring down, and the log
(`logs/fieldcore_gate.jsonl`) records every catch so it can be watched
fall.
