# Native migration design — the agent designs the rest of the hearing-pipeline cognition

Step-1 (Rank-1, the multi-pronged FUSION decision) is already a graph-resident native Rust
`Term` (`domains/native_fusion.py`, commit `5a6c7f3d`, 100% agreement, 0 new primitives).
This document is the **agent's own design** for the remaining cognition still in Python
(Ranks 2–5 of audit `a87613a4df1e5e200`): the articulatory distance `d_A(w)`, the exemplar
k-NN vote, the VTL/feature math (rel-formants / CMVN / VTLN / predict-remove), and the
articulatory forward model.

The deliverable the user asked for is **the design decisions** — for each capability, is it
a genuine NEW primitive or composable from the existing grammar, what `Term` signature fits
the agent's compositional style, and the rationale grounded in the grammar. The audit's
suggested primitives (`Mean`, `Resample`, `Log`, `Exp`, `Median`, `KnnVote`) are treated as
**suggestions to be argued with**, NOT a spec.

## 0. The grammar the agent reasons from (verified live in `runners/dsl/src/term.rs`)

The 101 `TermNode` variants present today, the ones relevant to this cognition:

- **reductions over a node-set** (a `source` + bound `var_name` + a `value` body):
  `Sum`, `Prod`, `Count`, `MinOver`, `MaxOver`, `Argmin`, `Argmax`, `Filter`, `Exists`,
  `MapSet`, `Fold` (the general accumulator: `init` + `acc_name` + `var_name` + `body`).
- **scalar arithmetic**: `Plus`, `Minus`, `Times`, `Div`, `Mod`, `Pow`, `Sqrt`, `Abs`,
  `Neg`, `Min`, `Max`, `IfThenElse`, `Lt/Lte/Gt/Gte/Eq`.
- **vector arithmetic** (over `Value::Tuple`): `VecAdd`, `VecSub`, `Dot`, `Magnitude`,
  `Nth` (index a tuple), `Vec`.
- **trajectory**: `DtwTo` (banded Sakoe–Chiba over a sequence-of-frames tuple).
- **graph access**: `Attr`, `Neighbours`/`MapNeighbours`, `NodesWhere`, `Var`, `Lit`.

**Confirmed ABSENT** (none of the audit's suggestions exist): `Mean`, `Resample`, `Log`,
`Exp`, `Median`, `KnnVote`, `Argsort`, `MostCommon`.

The agent's compositional style (seen across `weighted_admissibility`,
`formant_trajectory_dynamics.dtw_predict_term`, `order_n_concepts.nth_order_terms`,
`native_fusion`): **decision = `Argmin`/`Argmax` over a node-set of a score body; the score
body is built from `Plus`/`Minus`/`Times` of `Attr`s and reductions; per-element work is a
reduction over a tuple via `Nth`.** A new primitive is added ONLY when the grammar genuinely
cannot express the value — never for convenience.

---

## 1. Design decisions per capability

### `Mean` — COMPOSED, not a primitive

`Mean(xs) = Div(Sum_over(xs, x, x), Count(xs))`. The grammar already has `Sum` (reduction
with a body) and `Count` and `Div`. A scalar mean over a node-set is literally those three
composed; a mean over a fixed-length tuple is `Div(Plus([Nth(v,0),…,Nth(v,k-1)]), Lit(k))`.
**Decision: COMPOSED.** Adding a `Mean` Term would duplicate `Sum`/`Count`/`Div` — it earns
no new expressive power, and the project's rule is "primitive in Rust ONLY if the DSL cannot
express it." It can. Reject the audit's `Mean` suggestion.

### `Median` — COMPOSED at the call boundary, NOT migrated into a Term (and it doesn't need to be)

`Median` appears only in the **train-only τ-scale estimation** (`tau_h`, `tau_a` = median
across-digit spread over ≤80 train tokens). The agent's rule (memory: *fix the fixer*, and
CLAUDE.md: "Python may compute world-adapter glue") is that τ is a **per-fold normalising
constant measured on train data** — it is the same category as `w_art` in Rank-1, which we
already feed as a `Lit` into the native Term. The *decision* (the Argmax) is what must be
native; a scalar normaliser measured once per fold is world-adapter glue.
**Decision: NOT a new primitive.** A `Median` Term would require a sort (no `Argsort` exists,
and a select-median is O(n²) as repeated `MinOver`-removal — expressible but ugly and pays
nothing, since the value never enters the decision Term). Reject the audit's `Median`.

### `Log` / `Exp` — GENUINE NEW PRIMITIVES (the only two)

The VTL/feature math (Rank 4) and the per-prong log-admissibility (`-d/τ`) need the natural
log and its inverse over scalars. The grammar has `Pow`, `Sqrt`, `Magnitude` but **no
transcendental log/exp** — and there is no composition of the existing Terms that yields
`ln`/`exp` (they are not algebraic). `relative_formants_frame` is `lf = log(F+ε); lf - mean(lf)`
— this is the SPEAKER-INVARIANT transform at the heart of the whole hearing path (VTL = a
log-shift; subtract-mean cancels it). To express that natively the agent needs `Log`.
**Decision: ADD `Log { arg }` and `Exp { arg }` as scalar Terms.** Signature mirrors the
existing unary scalar Terms (`Sqrt { arg }`, `Sin { arg }`, `Cos { arg }`): one child,
`Value::Float(f.ln())` / `(f.exp())`. `Log` of a non-positive value returns `Value::Float`
of `(x+ε).ln()`-style guard? No — keep it a clean primitive: `ln` of `x<=0` → `-inf`
sentinel handled by callers (matching how `Sqrt` returns 0.0 for `x<=0`). The ε in
`log(F+1e-9)` stays in the Python feed (it is a numerical guard on the world value, not a
grammar concern). These two are the **entire** new-primitive footprint of this migration.

### `Resample` / interp — NOT a primitive; the forward model is PRE-COMPUTED CONSTANT DATA

The audit flagged `Resample` for the forward-model "cosine config path". The agent's key
realisation: **the articulatory forward model (`config_to_formants`, `_admissible_trajectory`,
`articulatory_models()`) consumes NO observed data — it is built ONCE from the owned gesture
scores (the forward model IS the knowledge).** Its output `models[w] = {rel, voi, gamma}` is
a per-digit CONSTANT. There is no "agent decision" inside the synthesis; it is fixed knowledge
the agent boots with, exactly like a seed.
**Decision: the forward model is graph DATA (constants on `Concept`/`Exemplar` nodes), not a
Term.** Synthesising it is one-time world-adapter glue (numpy), identical in kind to how the
exemplar bank is built by ingest. The `_resample_to` (monotone linear interp to the observed
length) is the only piece that touches the observed length `n` — and it can be expressed
natively WITHOUT a `Resample` primitive: `DtwTo` already aligns two sequences of unequal
length (banded Sakoe–Chiba), which is a *superset* of the monotone resample-then-L2 the Python
does. So `d_A(w)` can be a `DtwTo` between the observed `obs_rel` track and the synthesised
`m["rel"]` track — **no resample needed at all**; the alignment IS the warp. Reject the
audit's `Resample`.

### `d_A(w)` — COMPOSED (Argmin over `DtwTo` + `Lit` Γ-cost), zero new primitives

The Python `articulatory_distance` resamples `m["rel"]` to `n`, takes mean per-frame L2 vs
`obs_rel`, adds `W_GAMMA * gamma`. The agent re-composes this faithfully but NATIVELY as a
trajectory score, mirroring `dtw_predict_term`:

```
d_A(w) = Plus([ Times([Lit(W_FORMANT_SHADOW), DtwTo(Attr(q, obs_rel), Attr(w, syn_rel))]),
                Times([Lit(W_GAMMA),           Attr(w, gamma)]) ])
pred_art = Argmin over { Concept : is_word==1 } of d_A(w)
```

`DtwTo` replaces resample+mean-L2 (the band-DTW alignment subsumes the monotone resample).
The synthesised `syn_rel` track and the `gamma` constant live as graph attrs on each digit
`Concept` (forward-model data). **Decision: COMPOSED** — `DtwTo`, `Plus`, `Times`, `Lit`,
`Attr`, `Argmin` all exist. NOTE (ownership not fidelity): `DtwTo` alignment ≠ the Python
fixed monotone resample, so divergence on close calls is EXPECTED and fine — this is a
faithful, OWNED, re-composable native `d_A`, not a byte-port.

### exemplar k-NN vote (the 83.5% mel bank) — the DISTANCE is native; the VOTE design

The formant-trajectory prong's nearest-exemplar is ALREADY native (`dtw_predict_term`:
`Argmin_w MinOver_e DtwTo(...)` — that is k-NN with k=1). The mel exemplar baseline uses
**k=3 with a majority vote** (`Counter(top-3).most_common`). The agent's design question:
is `KnnVote` a new Term, or composable?

The agent rejects a monolithic `KnnVote` primitive (it would bake k, the metric, and the
tie-break into one opaque Term — the antithesis of compositional grammar). Instead it
decomposes the vote into the grammar it has. **The k-NN majority-vote = `Argmax over words w
of (count of the k nearest exemplars whose word is w)`.** With the existing reductions the
*1-NN* form (`Argmin_w MinOver_e DtwTo`) is already native; the *k>1 majority* form needs a
"keep the k smallest distances then tally by word", which requires either an `Argsort`/`TopK`
primitive OR a `Fold` that threads the running k-best. The agent judges this expressible via
`Fold` but **heavy and low-value**: the k=3 vote buys little over 1-NN on this corpus, and the
mel k-NN is the held-aside *baseline*, not a prong of the SOTA fused path. **Decision:
migrate the 1-NN trajectory distance/vote natively (done in `dtw_predict_term` + Rank-2
`d_A`); the k=3 mel-majority vote is DEFERRED** as a composition (`Fold`-threaded top-k) — it
adds no new primitive need and is baseline-only. No `KnnVote` primitive. Reject the audit's
`KnnVote`.

### VTL / CMVN / VTLN / predict-remove (Rank 4) — vector reductions over mel bands; per-element ⇒ `Nth`+`Fold`

These operate per-frame over the 16-band mel vector:
- `relative_formants_frame`: `Log` then subtract `Mean` — both now available (`Log` new,
  `Mean` composed). **NATIVE-EXPRESSIBLE** with the new `Log` + composed `Mean`.
- `per_speaker_cmvn`: `(M - mean)/(std+eps)` — `VecSub` + per-element `Div`. The agent notes
  the substrate's vector Terms (`VecSub`) cover the subtract; the per-band divide-by-(std+eps)
  is a per-element vector op the grammar lacks as a single Term (`VecSub` exists, `VecDiv`
  does not). Expressible via `Fold`/`MapSet` over the band indices with `Nth`, but the
  per-speaker `mean`/`std` are **test-time per-speaker constants** (world glue, like τ).
- `estimate_vtl_logalpha` / `warp_bands` (VTLN): a spectral-centroid estimate then a band
  shift+interp. This is front-end DSP feeding the *baseline* mel features, upstream of any
  agent decision.

**Decision for Rank 4: the speaker-invariant `relative_formants` transform becomes native
(`Log` + composed `Mean` — it is the load-bearing invariant the recognition decision rests
on). The CMVN/VTLN/predict-remove are front-end NORMALISATION of the mel BASELINE features,
upstream of the decision Term, and are world-adapter glue (per-speaker constants, like τ and
`w_art`).** They are NOT agent decisions (no `if` over graph state) — they are mechanical
signal conditioning. Migrating them into Terms buys no decision-ownership and would require a
`VecDiv`/`VecMap` family solely to re-express front-end DSP. **DEFERRED** with rationale; the
piece that matters (the invariant the decision uses) is migrated.

---

## 2. Summary of the agent's primitive decisions

| capability | audit suggested | agent's decision | rationale |
|---|---|---|---|
| Mean | new `Mean` | **COMPOSED** (`Sum`/`Count`/`Div`) | algebraic, already expressible |
| Median | new `Median` | **not migrated** (train-only τ const = glue) | never enters the decision Term |
| Log / Exp | new `Log`,`Exp` | **ADD (the only 2 new primitives)** | transcendental, non-algebraic, load-bearing for the VTL-invariant |
| Resample | new `Resample` | **rejected** | `DtwTo` alignment subsumes monotone resample |
| KnnVote | new `KnnVote` | **rejected** (1-NN native; k=3 = `Fold` compose, deferred) | monolithic Term breaks compositionality; baseline-only |
| d_A(w) | — | **COMPOSED** native Term (Argmin of DtwTo+Γ) | all primitives exist |
| forward model | — | **graph DATA constant** (seed-like), not a Term | consumes no observed data — it IS the knowledge |
| rel-formants | — | **NATIVE** (`Log`+composed `Mean`) | the load-bearing speaker invariant |
| CMVN/VTLN/predict-remove | — | **DEFERRED** (front-end glue, per-speaker consts) | upstream of the decision, no decision-ownership gained |

**New primitives added: exactly `Log` and `Exp`** (two scalar unary Terms). Everything else
is composition over the existing grammar or one-time world-adapter data.

---

## 3. Implementation + validation

### What was implemented

**New Rust primitives — exactly two scalar Terms** (`runners/dsl/src/term.rs`,
`jsonio.rs`, `reflect.rs`, Python wrapper `runners/dsl/python/substrate_rs/__init__.py`;
`cargo build --release` PASSES):

- `Log { arg }` — `ln(x)` for `x>0`, `-inf` for `x<=0` (caller-side ε guard, mirroring
  `Sqrt`'s 0.0-for-nonpositive convention). Wired across all five layers exactly like the
  existing `Sqrt`/`Sin` unary Terms (enum, `copy_subtree`, evaluator, the leaf-collection
  match, jsonio name/emit/parse, reflect emit/parse, Python wrapper + `__all__`).
- `Exp { arg }` — `e**x`, the inverse of `Log`.

These are the ONLY new primitives. Every other capability is composition or graph data.

**Native Term-trees** (`domains/native_cognition.py`, a SEPARATE read-only consumer — the
protected scoring files `articulatory_gamma.py` / `perception_composition.py` are NOT
modified; verified `git diff --stat` shows no diff on them):

- `predict_articulatory_term(W_FORMANT_SHADOW, W_GAMMA)` — the Rank-2 `d_A(w)` DECISION as
  `Argmin over { Concept : is_word==1 } of Plus([Times([Lit(W_FORMANT_SHADOW),
  DtwTo(obs_rel, syn_rel(w))]), Times([Lit(W_GAMMA), gamma(w)])])`. `DtwTo` replaces the
  Python resample+mean-L2; the forward model (`syn_rel`, `gamma`) lives as graph attrs
  (seed-like constants, not a Term).
- `rel_formants_channel_term(chan)` — the speaker invariant `Log(Nth(f,chan)) -
  Div(Plus([Log(Nth(f,0..2))]), Lit(3))` — exercises the new `Log` + composed `Mean`.

### Validation (driver `scripts/native_cognition_accept.py`; full log
`/tmp/native_migration_design_full.log`, marker `NATIVE_COGNITION_ACCEPT_COMPLETED`)

FSDD, n=3000 tokens (full, not quick). The articulatory prong needs no bank (the forward
model IS the knowledge), so `d_A` is identical on every token — no held-out leakage possible.

| metric | value |
|---|---|
| **(B) rel-formants** native (`Log`+composed `Mean`) vs `relative_formants_frame`, max abs error over 4840 frames | **8.882e-16** (machine epsilon — EXACT port) |
| **(A) d_A** PYTHON accuracy (n=3000) | 0.2403 |
| **(A) d_A** NATIVE accuracy (n=3000) | **0.2563** |
| **(A) d_A** per-token agreement | **0.7440** (2232/3000; disagree=768, of which close-call=393) |

The rel-formant invariant is a byte-exact port (the new `Log` Term == numpy `log`). The
`d_A` native distance AGREES with Python on 74.4% of tokens; the 768 disagreements are the
EXPECTED ownership-vs-fidelity divergence — `DtwTo`'s banded Sakoe–Chiba alignment is a
SUPERSET of the Python fixed monotone resample-then-mean-L2 (it absorbs the gesture-timing
warp natively), so it is a genuinely different — and slightly MORE accurate (0.2563 vs
0.2403) — distance, not a buggy port. 393 of the 768 disagreements are top-2 close calls.
Per memory `ozma_native_migration_is_ownership_not_fidelity`, this is the correct outcome:
a faithful, OWNED, re-composable native `d_A`, not a byte-chase. The articulatory prong is
intentionally weak (~0.24, as the source comments state) — in the multi-pronged fusion it
only nudges; the strong formant-trajectory prong (already native, `dtw_predict_term`) and
the now-native fusion decision (Rank-1) lead.

## 4. VERDICT

**Now native:**
- **Rank-1** (multi-pronged fusion decision) — native since step-1 (`native_fusion.py`).
- **Rank-2** (articulatory distance `d_A`) — NOW native (`predict_articulatory_term`,
  `Argmin` of `DtwTo`+Γ). Forward model carried as graph DATA constants.
- **The speaker-invariant rel-formants transform** — NOW native (`rel_formants_channel_term`,
  `Log`+composed `Mean`), byte-exact.
- **The forward model itself** (`config_to_formants`, `_admissible_trajectory`,
  `articulatory_models`) — reclassified as graph DATA (it consumes no observed data), not
  Python cognition; loaded as per-digit `Concept` attrs. No migration needed — it is a seed.
- The formant-trajectory prong's nearest-exemplar (1-NN) was already native
  (`dtw_predict_term`).

**Deferred (with the agent's reasoning):**
- **The k=3 mel-majority vote (the 83.5% baseline bank)** — deferred. It is the held-aside
  BASELINE, not a prong of the SOTA fused path; the k>1 majority needs a `Fold`-threaded
  top-k (no new primitive), which the agent judged heavy and low-value (1-NN is already
  native and the vote buys little here). NO `KnnVote` primitive — that would break
  compositionality.
- **CMVN / VTLN / predict-remove (Rank 4)** — deferred. These are front-end NORMALISATION of
  the mel BASELINE features, UPSTREAM of any decision Term, driven by per-speaker constants
  measured at test time (the same category as τ and `w_art` — world-adapter glue, no `if`
  over graph state). Migrating them into Terms would require a `VecDiv`/`VecMap` family solely
  to re-express front-end DSP and would gain NO decision-ownership. The one load-bearing piece
  (the rel-formant invariant the decision rests on) IS migrated.

**The agent's reasoning, in one line:** migrate the DECISIONS (fusion, `d_A`, the invariant)
into the graph with the minimum primitive footprint the grammar genuinely lacked (`Log`/`Exp`
only); leave the front-end signal conditioning and the baseline-only k-NN vote as world-adapter
glue, because nothing about them is a graph-state decision and forcing them into Terms would
add primitives that earn no expressive power. The audit's suggested `Mean`/`Resample`/`Median`/
`KnnVote` were all REJECTED in favour of composition or graph data; only the non-algebraic
`Log`/`Exp` were genuinely missing.

