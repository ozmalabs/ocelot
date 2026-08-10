# Native collapse core — the cognition migrated to the Rust/graph runtime

## (1) Verdict — LEAD

**YES — the collapse cognition is now NATIVE (Rust/graph), verified
native==python, surprise wired as a native Term, and learning as a native graph
mutation that DROPS surprise and GENERALISES.**

- **The collapse decision (manifold + confidence + entropy)** runs as graph
  Term-trees evaluated by the Rust runtime (`substrate.evaluate`) — softmax over
  candidate log-weights held as graph data. Verified identical to the Python
  prototype to **machine epsilon** (max |Δconf| `4.4e-16` on llvm_passes,
  `1.6e-14` on letters).
- **Surprise** is the native Term `Neg(Log(conf))` evaluated in Rust. Verified
  per-step identical to the Python surprise (max |Δsurprise| `4.4e-16`).
- **Learning** is a native **graph mutation** — both a direct
  `add_node`/`add_edge_unchecked` and a `tick()`-fired graph-resident **Rule**
  whose `add_edge` effects the Rust rewrite engine applies. After native
  construction, surprise **drops** at the constructed points (sentences:
  `27.631 -> 4.217`) and **drops on held-out data** wherever the constructed
  structure genuinely recurs (the sharp held-out set: `27.631 -> 2.357`,
  −25.3) — generalisation, not memorisation.

Run captured to `/tmp/nativecore_full.log` (`NATIVE_COLLAPSE_RUN_COMPLETED` +
`END MARKER`, `MARKER_EXIT=0`; process pgrep-verified gone).

The Python prototype `scripts/collapse_engine.py` was **left untouched** — it is
the mirror the native cognition is verified against.

---

## (2) The native primitives — what the cognition is built from

No new Rust primitive was required: the DSL already carries every operator the
collapse cognition needs (`Log`/`Exp`/`Neg` were added earlier tonight; `Sum` /
`MaxOver` / `Attr` / `Neighbours` / `Div` / `Minus` / `Times` pre-existed). The
migration is therefore **graph Term-trees composed from existing primitives** +
a thin native driver — the donkey-clean accretion path (agent composes; Rust
evaluates). The Term variants and their Rust evaluators:

| native op | Rust evaluator (`runners/dsl/src/term.rs`) |
|---|---|
| `Neg`     | `term.rs:2522` |
| `Log` (ln; x≤0 → −inf) | `term.rs:2572` |
| `Exp`     | `term.rs:2577` |
| `Sum` (fold over a node-set) | `term.rs:1741` |
| `MaxOver` | `term.rs:1823` |
| `Div` / `Minus` / `Times` / `Attr` / `Neighbours` | (pre-existing arithmetic/graph evaluators) |

The cognition Term-trees (module constants in `scripts/native_collapse.py`,
naming no domain, holding no state):

```
T_MAX_LW  = MaxOver_c  Attr(c,"lw")                      # max log-weight
T_Z       = Sum_c      Exp(Attr(c,"lw") - mx)            # softmax denominator
T_CONF    = Exp(Attr(c,"lw") - mx) / Z                   # candidate confidence
T_ENTROPY = -Sum_c  [p · Log(p)] / ln2,  p = Exp(lw-mx)/Z   # manifold H (bits)
T_SURPRISE = Neg(Log(conf))                              # surprise = -log(conf)
```

The **learning-mutation primitive** is the substrate's native graph mutation —
exercised two ways, both in `scripts/native_collapse.py`:

- `construct_gap_direct` (`native_collapse.py:176`): host calls
  `add_node`/`add_edge_unchecked` — the same native mutation Rust applies for an
  `add_edge` rule effect — to grow the `MBi(b -> missing)` counted transition.
- `construct_gap_via_rule` (`native_collapse.py:193`): installs a graph-resident
  **Rule** node (`match` staging edges, `effect: add_edge … / del_edge …`) and
  calls `substrate.tick()`; the **Rust rewrite engine** (`graph_rules.rs` +
  `rewrite.rs`) matches and applies the effects. The structure-addition (the
  admissibility link the surprise localised) is decided by a graph-resident Rule
  and executed in Rust — the agent flexing its own Γ natively, not Python
  control flow. (Smoke-verified: `P(z|ab) 0.0 → 0.175`; the `bi`/`to` edges
  exist after `tick()`; the staging edges were `del_edge`'d away.)

No new term.rs/py.rs code was needed; the spec-and-emit accretion path was on
standby but the existing grammar already expressed the cognition.

---

## (3) Numbers — native==python, surprise drop, held-out generalisation

### (a/b) NATIVE == PYTHON  (`scripts/native_collapse_run.py`, the instrument)

The native manifold confidence, entropy, and surprise are compared per candidate
/ per fraction / per step against the untouched `collapse_engine.py`:

```
domain= llvm_passes  steps=190  conf_cmps=  3610
  max |conf_native - conf_python|     = 4.441e-16
  max |entropy_native - entropy_py|   = 6.407e-16
  max |surprise_native - surprise_py| = 4.441e-16   →  NATIVE==PYTHON: YES
domain=     letters  steps=400  conf_cmps=320000
  max |conf_native - conf_python|     = 1.621e-14
  max |entropy_native - entropy_py|   = 2.338e-14
  max |surprise_native - surprise_py| = 1.621e-14   →  NATIVE==PYTHON: YES
```

Machine epsilon on llvm; ~1e-14 on letters (320k confidence comparisons,
accumulated float order differences) — the project's standard native-mirror
verification, passed.

### (c) NATIVE LEARNING MUTATION — surprise drop + held-out generalisation

```
domain=sentences
  construct gaps localised : 369  (via tick()-Rule: 185, via direct native: 184)
  held-out gaps (disjoint) : 410
  SURPRISE @ constructed   : 27.631 -> 4.217   (drop +23.414)
  SURPRISE @ HELD-OUT      : 27.631 -> 27.323  (drop +0.308; 5 of 410 closed)
  SHARP held-out (the 5 held-out gaps whose transition was constructed
                  from the DISJOINT construct set):
    SURPRISE @ shared      : 27.631 -> 2.357   (drop +25.274)
  drops at constructed: YES   GENERALISES to held-out: YES
```

- **Drops at constructed points**: surprise `27.631 -> 4.217` (the constructed
  admissibility now admits the previously-zero-mass transition).
- **Generalises (the binary-vs-fit test)**: of 410 held-out gaps (from targets
  **disjoint** from the construct set), exactly **5** share a `(context-symbol,
  missing-symbol)` transition that was constructed. On precisely those 5, native
  surprise drops `27.631 -> 2.357` (−25.3). The structure transfers **where it
  genuinely recurs and nowhere else** — no smeared fit. That sharpness is the
  admissibility signature: the constructed transition is the same object whether
  it appears in the construct set or the held-out set.

Surprise here is the **native Term** evaluated in Rust on the counted next-symbol
probability (`-log P(true_next | ctx)`); the construction is the **native graph
mutation**. Both halves of the loop are native.

---

## (4) What is native vs justifiably-still-Python

**Native (the cognition):**
- The collapse decision — manifold log-weights as graph data; confidence,
  entropy, max, softmax denominator as graph Term-trees evaluated by Rust.
- Surprise — `Neg(Log(conf))`, a native Term.
- The learning step — a native graph mutation (direct, and a `tick()`-fired
  graph-resident Rule applied by the Rust rewrite engine).

**Still Python (the instrument, not cognition):**
- Reading the corpus into opaque symbol-sequences (world-adapter I/O).
- The counted n-gram structure's back-off arithmetic (`seq_logprob` /
  `next_dist`) — this is the **scorer the manifold consumes**, donkey-clean
  counts; its graph-resident equivalent already exists and is donkey-audited in
  `collapse_domains.CountedStructure.graph_bi_support` (graph-`Sum` == python
  count). It feeds the native manifold as a scalar `lw`; migrating the full
  back-off recurrence into Term-trees is mechanical but not where the cognition
  lives.
- The measurement / verification harness — calibration, cohort, shuffle control,
  the before/after/held-out surprise bookkeeping. Explicitly the experimenter's
  instrument for evaluating the agent (per the directive), not the agent's
  cognition. Not migrated, by design.
- One compile-time constant `_LN2 = math.log(2.0)` (ln 2 for the bits
  conversion) — a literal, not a per-step operation.

---

## (5) Donkey audit

- **No** gradient, backprop, `.fit`, loss, optimiser, net, `torch`/`sklearn`,
  weight-update — grep of `scripts/native_collapse.py` (the cognition): the only
  hits are the docstring saying these are absent.
- **No** Python `math.exp`/`math.log` in the per-step cognition — the manifold,
  confidence, entropy and surprise are native Term-trees (`Exp`/`Log`/`Neg`/
  `Sum`/`MaxOver`/`Div`) evaluated by the Rust runtime. The only `math.log` is
  the `_LN2` constant.
- The learning is **structure-ADDITION**: a counted `MBi` transition edge (the
  admissibility the surprise localised), count-incremented — exactly what the
  Python `on_gap` did, now as a native graph mutation. Not a fitted parameter.
- The shuffle/structure controls (in the instrument) and the counted-back-off
  scorers are unchanged and donkey-clean (graph-`Sum` == python count, proven in
  `collapse_domains.donkey_audit`).

**ALL PASS.**

---

## (6) Honest verdict

**The cognition is native.** The three things the directive named as cognition —
the collapse decision, surprise, and the learning mutation — now run in the
Rust/graph runtime: confidence/entropy/surprise as graph Term-trees evaluated by
`substrate.evaluate`, verified equal to the Python prototype to machine epsilon;
the learning step as a native graph mutation (including a `tick()`-fired
graph-resident Rule the Rust rewrite engine applies), which drops surprise at the
constructed points and generalises to held-out data exactly where the structure
recurs.

**What remains Python is justifiably the instrument**, not the cognition: corpus
I/O, the measurement harness, and the counted-back-off scorer that supplies the
manifold's scalar `lw` (its graph-resident `Sum` form already exists and is
donkey-audited; the residual is the mechanical migration of the back-off
recurrence into Term-trees — no decision lives there).

**Honest scoping of (c):** the generalisation was proven on **sentences** (369
constructs, 410 disjoint held-out gaps, sharp held-out drop −25.3 on the 5 shared
transitions). On **letters** the test is degenerate — the dense 26-symbol
alphabet trained on held-out words leaves only **1** construct gap and **0**
held-out gaps, so there is nothing to generalise across; letters serves only as a
second native==python check (which it passes), not as a generalisation domain.
The native==python identity is shown on **two** domains (llvm_passes, letters);
the learning-mutation drop + held-out generalisation is shown on the domain that
actually has held-out gaps (sentences). That is the honest extent of the proof.

### Files (all NEW; nothing pre-existing modified)

- `scripts/native_collapse.py` — the native cognition: the manifold/confidence/
  entropy/surprise Term-trees + the native learning-mutation paths (direct +
  tick()-Rule). Names no domain.
- `scripts/native_collapse_run.py` — the instrument: native==python verification
  + the learning-mutation drop + held-out generalisation measurement.
- `docs/native_collapse_core.md` — this report.
- `/tmp/nativecore_full.log` — full captured run (`NATIVE_COLLAPSE_RUN_COMPLETED`
  + `END MARKER`).

`scripts/collapse_engine.py` (the Python mirror), `CortexLoop` and `solve_for_n.py`
were left untouched.
