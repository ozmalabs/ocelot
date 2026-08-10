# Native back-off — the LAST Python piece of the cognition, migrated to graph Term-trees

## (1) Verdict — LEAD

**YES — the counted n-gram BACK-OFF SCORER is now NATIVE (a graph Term-tree
evaluated by the Rust runtime), verified native==python to machine epsilon. With
it migrated, the ENTIRE collapse cognition is native: back-off → manifold →
confidence → surprise are all graph Term-trees in Rust. What remains Python is
only the measurement instrument and corpus I/O — not a decision.**

- **Back-off log-prob native==python**: the trigram→bigram→unigram recurrence,
  re-expressed as a Term-tree over the graph count nodes, matches the untouched
  Python back-off (`collapse_domains.CountedStructure.trans_logprob` /
  `.seq_logprob`) **EXACTLY** — max |Δ| = **0.000e+00** on all three domains
  (sentences, llvm_passes, letters), per-triple AND per-whole-sequence. (It is
  bit-exact, not merely sub-epsilon: the Term-tree reduces to the identical
  sequence of float ops as the Python recurrence.)
- **Full native cognition end-to-end**: with the native back-off feeding the
  native manifold, the whole pipeline (back-off → confidence → surprise) matches
  the pure-Python mirror to machine epsilon — max |Δconf| / |Δsurprise| =
  **6.66e-16 / 8.88e-16** (llvm_passes), **3.02e-14 / 3.02e-14** (sentences).
- The pre-existing native manifold/surprise checks still pass unchanged
  (`4.44e-16` llvm, `1.62e-14` letters), and the native learning-mutation drop +
  held-out generalisation still holds (sentences: surprise `27.631→4.217` at
  constructed, sharp held-out `27.631→2.357`).

Run captured to `/tmp/backoff_full.log`
(`NATIVE_COLLAPSE_RUN_COMPLETED` + `MARKER_EXIT=0` + `BACKOFF_RUN_END_MARKER`;
no `scripts.native_collapse_run` process remaining — pgrep-verified gone).

The Python back-off (`collapse_domains.CountedStructure`) was **left untouched** —
it is the mirror the native back-off is verified against.

---

## (2) The back-off Term-tree (file:line, primitives, donkey audit)

The native back-off lives in **`scripts/native_collapse.py`**:

- The Term-tree constants: **`scripts/native_collapse.py:285-310`**
  (`_P_UNI`, `_LAM_B`, `_P_BI_LEARNED`, `_P_BI`, `_LAM_A`, `_P_TRI_LEARNED`,
  `_P_TRI`, `_P_FLOORED`, `T_BACKOFF_LOGP`).
- The driver `class NativeBackoff`: **`scripts/native_collapse.py:313`**
  (`.trans_logprob` at `:378`, `.seq_logprob` at `:403`).

### The recurrence, re-expressed (faithful mirror of `trans_logprob(a,b,c)`)

```
p_uni = (uni_c + 1) / (tot + V)                                  # Div, Plus, Lit(1.0)
lam_b = uni_b / (uni_b + V)                                      # Div, Plus
p_bi  = (uni_b > 0) ? lam_b*(big_bc/uni_b) + (1-lam_b)*p_uni     # IfThenElse, Gt,
                    : p_uni                                      #   Times, Div, Minus, Plus
lam_a = big_ab / (big_ab + V)
p_tri = (big_ab > 0) ? lam_a*(tri_abc/big_ab) + (1-lam_a)*p_bi
                     : p_bi
logp  = log( max(p_tri, 1e-12) )                                 # Log, IfThenElse(Gt,...)
```

### Primitives used (all pre-existing DSL Terms; NO new Rust required)

`Div`, `Plus`, `Times`, `Minus`, `Log`, `Lit`, `IfThenElse`, `Gt`, `Attr`, `Var`.
Every one is an existing `term.rs` evaluator. The back-off **branch** (`uni_b>0`,
`big_ab>0`) and the `max(p,1e-12)` floor are `IfThenElse(Gt(...), ..., ...)` —
`IfThenElse` is lazy in the Rust evaluator (verified: the dead branch's
divide-by-zero is never evaluated), so the back-off selects the learned estimate
or falls back, exactly as the Python `if` did.

### Where the counts come from — the graph

Every input to the Term-tree is a **COUNT read from a graph node via `Attr`**:

| Term input | graph source |
|---|---|
| `uni_c`, `uni_b` | `Attr(MWord, "freq")` — unigram counts (pre-existing nodes) |
| `big_bc`, `big_ab` | `Attr(MBi, "cnt")` — bigram counts (pre-existing nodes) |
| `tri_abc` | `Attr(MTri, "cnt")` — trigram counts (**now materialised** as graph nodes; the Python mirror held them in a dict) |
| `V`, `tot` | `Attr(BackoffRoot, "V"/"tot")` — counts |

A single always-present `MZero` node (`cnt=0.0`/`freq=0.0`) supplies a real graph
`0.0` for any absent n-gram, so every `Attr` read is a genuine graph count, never
a missing attr. `NativeBackoff.__init__` reuses the SAME substrate the
`CountedStructure` already built (its `MWord`/`MBi` nodes), adding only the `MTri`
count nodes + the count-root — so the back-off reads the counts that are already
the agent's graph data.

### Donkey audit (the back-off)

- **No tunable parameter.** Every number fed to the log is a COUNT
  (`uni`, `big`, `tri`, `V`, `tot`) or a FIXED literal of the back-off scheme:
  the add-1 (`Lit(1.0)`), the uniform floor structure, and the `1e-12`
  pre-log world-value guard (`Lit(1e-12)`). The back-off **weights**
  `lam = n/(n+V)` are **counted ratios**, not fitted — the back-off weight is the
  count itself, computed by `Div(n, Plus([n, V]))`.
- **No** `.fit` / gradient / backprop / loss / optimiser / net / `torch` /
  `sklearn` / sweep / softmax-fit in the back-off (grep of
  `scripts/native_collapse.py` `NativeBackoff` section: zero hits).
- **No** Python `math.log` / `math.exp` in the back-off scorer — the log and all
  arithmetic are the Rust-evaluated Term-tree (grep of the `NativeBackoff` class
  body: zero `math.log`/`math.exp`).

---

## (3) Native-vs-Python deltas (real numbers, from `/tmp/backoff_full.log`)

### (a) Back-off LOG-PROB — native Term-tree vs Python back-off

| domain | trans cmps | seq cmps | max \|Δ trans_logp\| | max \|Δ seq_logp\| |
|---|---|---|---|---|
| sentences | 5319 | 300 | **0.000e+00** | **0.000e+00** |
| llvm_passes | 264 | 19 | **0.000e+00** | **0.000e+00** |
| letters | 2144 | 300 | **0.000e+00** | **0.000e+00** |

Bit-exact across all three domains (>2 domains, per directive), both per-triple
back-off log-prob and per-whole-sequence log-plausibility.

### (b) FULL NATIVE COGNITION end-to-end (native back-off → manifold → confidence → surprise)

| domain | steps | max \|Δ confidence\| | max \|Δ surprise\| |
|---|---|---|---|
| sentences | 400 | **3.020e-14** | **3.020e-14** |
| llvm_passes | 190 | **6.661e-16** | **8.882e-16** |

Machine epsilon. The sentences `~3e-14` is the standard accumulated float-order
difference of a softmax over a 1200-candidate pool (consistent with the prior
report's `1.6e-14` on letters' 320k comparisons); llvm is at the float floor.

### Regression — the pre-existing native checks (unchanged, still pass)

```
[A/B] manifold conf/entropy/surprise:  llvm 4.44e-16 / 6.41e-16 / 4.44e-16
                                        letters 1.62e-14 / 2.34e-14 / 1.62e-14
[C]   native learning mutation:  sentences SURPRISE @ constructed 27.631 -> 4.217
                                  SHARP held-out 27.631 -> 2.357 (generalises)
```

---

## (4) What remains Python — and why it is NOT cognition

After this migration, the only Python left in the collapse path is the
**measurement instrument and corpus I/O** — no decision lives there:

1. **Corpus I/O (world adapter).** Reading LibriSpeech `.trans.txt` /
   `/tmp/llvm_pipelines/*.raw` into opaque symbol-sequences
   (`_load_sentences`, `_parse_pipeline_schedules`). Mechanical text→token
   translation — exactly the world-adapter role the architecture rule permits.
   It chooses no admissibility; it only hands the substrate tokens.
2. **The measurement / verification harness** (`scripts/native_collapse_run.py`):
   calibration, cohort, shuffle control, the before/after/held-out surprise
   bookkeeping, and the native==python comparison itself. This is the
   experimenter's instrument that EVALUATES the agent — explicitly not the
   agent's cognition (per the directive).
3. **Two compile-time literals**: `_LN2 = math.log(2.0)` (the bits-conversion
   constant for the manifold entropy) — a single literal, not a per-step op.
   The back-off itself introduces **no** new Python constant beyond the
   in-graph `Lit` literals.

The **n-gram counting** (`CountedStructure.learn`) is structure-building — it
writes counts as graph data (`MWord`/`MBi`, and `MTri` once materialised). It
holds no decision; it is the agent's memory being populated, the same way the
world adapter ingests. It is the donkey-clean counting the back-off reads.

Crucially, the thing that **was** cognition-in-Python — the back-off arithmetic
that produced the manifold's scalar weights (`seq_logprob`/`next_dist`/`lw`) — is
now the graph Term-tree. The scorer feeding the manifold is native.

`CortexLoop` and `solve_for_n.py` were **untouched**.

---

## (5) Honest verdict

**The back-off scorer is native, and with it the entire collapse cognition is
native.** The trigram→bigram→unigram back-off recurrence — the last piece of the
cognition still computed in Python — is now a graph Term-tree
(`T_BACKOFF_LOGP`, `scripts/native_collapse.py:285-310`) composed from existing
DSL primitives (`Div`/`Plus`/`Times`/`Minus`/`Log`/`Lit`/`IfThenElse`/`Gt`/`Attr`)
over the graph count nodes (`MWord.freq`/`MBi.cnt`/`MTri.cnt`/`BackoffRoot.V,tot`),
evaluated by the Rust runtime. It reproduces the untouched Python back-off
**bit-exactly** (max |Δ| 0.000e+00 on sentences, llvm_passes, letters), and the
full pipeline fed by it matches the pure-Python mirror to machine epsilon
(conf/surprise ≤ 3.02e-14).

**This was a faithful re-expression, not a redesign.** No decision was added or
moved — the back-off holds none: its weights are counted ratios `n/(n+V)`, its
floors are fixed literals, and the migration changed only *where the arithmetic
runs* (Rust Term-tree vs Python), not *what it computes* (proven by the bit-exact
match).

**Honest scoping.** (i) The migration is of the **back-off LOG-PROB** that drives
`seq_logprob` (the manifold's `lw`). `next_dist` (the next-symbol predictive
distribution used by the learning instrument) shares the same `trans_logprob`
recurrence — now native — but its final per-candidate softmax-normalisation is
still done in the Python instrument; that softmax is the same operator already
proven native in the manifold (`T_CONF`), so it is mechanical to route through
the native manifold and holds no new decision, but it was not re-routed here.
(ii) The trigram counts were a Python dict in the mirror; the native back-off
**materialises them as `MTri` graph nodes** so the trigram term reads a real
graph count — this is the only structural addition, and it is counting, not
cognition. (iii) The native back-off reuses the `CountedStructure`'s existing
substrate rather than rebuilding the graph from a save file — a performance reuse,
the counts are identical.

### Files (only the two NEW native-migration files were extended)

- `scripts/native_collapse.py` — **extended**: the `NativeBackoff` class + the
  `T_BACKOFF_LOGP` back-off Term-tree (lines 285-410). The cognition.
- `scripts/native_collapse_run.py` — **extended**: the back-off native==python
  verification (`verify_backoff_native_vs_python`), the full-cognition end-to-end
  check (`verify_full_native_cognition`), and an `llvm_factory`. The instrument.
- `docs/native_backoff.md` — this report.
- `/tmp/backoff_full.log` — full captured run (`NATIVE_COLLAPSE_RUN_COMPLETED`
  + `MARKER_EXIT=0` + `BACKOFF_RUN_END_MARKER`).

`collapse_domains.CountedStructure` (the Python back-off mirror),
`collapse_engine.py`, `CortexLoop`, and `solve_for_n.py` were left untouched.
