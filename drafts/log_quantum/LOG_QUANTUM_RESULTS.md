# RESULTS — the integer-observable log-quantum emitter (`LogQuantum`)

Measured against `LOG_QUANTUM_PREREG.md` (committed before any number). The
gate is the frame/continuum invariant (H-L1), checked FIRST. Engine built via
`scripts/engine_build.sh` (`engine af09f38e0336`, the same crate — not a fork).
All numbers reproduced below are from the harnesses under `drafts/log_quantum/`.

Nulls are findings; no number is fabricated. Every verdict here is a live
harness print, re-runnable with `PYTHONPATH=. python3 drafts/log_quantum/<h>.py`.

---

## What was built

`LogQuantum` — a Rust DSL Term (`runners/dsl/src/shape_decode.rs::eval_log_quantum`,
471 lines incl. doc), wired through the SAME full file set as `RatioInduce`/`scale2`:

| file | touch-points |
|------|--------------|
| `term.rs` | enum variant + doc, `evaluate` dispatch arm, `copy_subtree` arm, child-collect arm |
| `term_variants.rs` | name + discriminant `236` — **regenerated** via `tools/gen_term_variants.py` (237 variants total; no existing discriminant renumbered — appended at the enum tail) |
| `jsonio.rs` | type-name, `to_json`, `from_json` |
| `reflect.rs` | `encode`, `reconstruct` |
| `py.rs` | **no change** — generic `term_from_json` handoff, exactly as the trace stage predicted |

**Params (all `i64`/`bool`, held intensionally on the Term — in `Hom`):**
`population` (child), `value_slot`, `base_num`/`base_den` (base `a = num/den`;
`base_num == 0` = natural-log sentinel), `delta_num`/`delta_den` (resolution
`Δ = num/den`), `raw` (true = `x` is a raw linear value to be logged; false =
`x` is already a natural-log quantity — the `frame.py` case — rebased +
requantized), `field` (diagnostic-Dict selector, else returns the quantized
population).

**The operation:** for every relation in every frame, the slot `value_slot`
holding a continuous quantity `x` is REPLACED by the integer log-quantum
`q = round(log_a(x) / Δ)`, written through the kind-preserving `set_coord` as a
`Value::Int`. The single transient float — `ln(x)/(ln(a)·Δ)` — is computed in
the cross-frame map and immediately rounded; it is never stored. This is the
exact generalization of `scale_pow2_once` (fixed base-2, additive-`k`-in-log₂)
to arbitrary base `a` + step `Δ`.

---

## H-L1 — WELL-FORMEDNESS / PRICE CHECK (the crux, reported FIRST)

**Harness:** `drafts/log_quantum/hl1_price.py`

**VERDICT: H-L1 PASSED — the integer-observable log-quantum is well-formed BY
CONSTRUCTION; the price against the frame/continuum invariant is ZERO.**

Five falsifiable price facts, all `True`:

| # | fact | result |
|---|------|--------|
| P1 | emitted quantum is an **Int**, in-frame (input was `float`) | `PASS` — raw floats `[1.7, 2.9, 5.5, 11.1, 20.0]` (base e, Δ=1) → quanta `[1, 1, 2, 2, 3]` = `round(ln x)`, every value a Python `int` |
| P2 | base + Δ are **intensional params on the Term** (in `Hom`), applied on read | `PASS` — same input, Δ=0.25 → `[2,4,7,10,12]` vs Δ=1 → `[1,1,2,2,3]` (param applied on read); re-eval reproduces; the term wire form carries only params, no coordinate payload |
| P3 | `coord_ints` **still refuses floats** — the downstream gate is untouched | `PASS` — emitter's integer output → `RatioInduce explained=True` (consumable); a RAW FLOAT population → `RatioInduce explained=False, n_frames=0` (refused) |
| P4 | a float is **never written to a coord slot** (applicable OR skip) | `PASS` — applicable path all-int; Δ≤0 / invalid base / out-of-range slot are graceful skips returning the population UNCHANGED |
| P5 | resolution **pinned to observation (MDL)** | `PASS` — inputs ≈100, 106: fine Δ=0.01 separates (`461` vs `466`), coarse Δ=1 merges (`5` == `5`); the observable IS the step |

**Reading (in shape).** The emitter's price against the invariant is *zero* —
not "small," zero. It puts ONLY an integer in-frame (P1), the continuum lives
entirely in `Hom` as Term params applied on read (P2), the Int-only gate is
intact and the emitter is the *legitimate bridge* that turns a continuous
reading into an admissible integer coordinate (P3), no float ever reaches a
coord slot on any path (P4), and Δ is the MDL identifiability guard (P5). This
is `scale_pow2_once`'s discipline generalized: continuity is intensional, the
observable is the stepped integer rendering. H-L1 is the whole point, and it
holds by construction.

---

## H-L2 — LOG-RATIO COMPOSITION (synthetic)

**Harness:** `drafts/log_quantum/hl2_synthetic.py`

**VERDICT: H-L2 CONFIRMED.**

**(A) The literal statement — a difference of two log-quanta is the constant
integer `round(log_a f / Δ)`, per-frame scale cancelled.** Factor `f = 8`,
base 2, Δ = 1 ⇒ expected diff `3`:

| per-frame scale | quanta | diff | expected |
|---|---|---|---|
| 1.3 | (2, 5) | **3** | 3 |
| 2.7 | (3, 6) | **3** | 3 |
| 5.1 | (4, 7) | **3** | 3 |
| 9.9 | (5, 8) | **3** | 3 |
| 100.0 | (8, 11) | **3** | 3 |

The per-frame multiplicative scale is a common additive log-offset that cancels
in the difference — exactly the shape `RatioInduce` consumes.

**(B) Population recovery via emitter → `RatioInduce`: 5/5.** Planted cross-axis
log-extent ratios recovered with the per-frame multiplicative scale factored:

| base | planted y:x log-extent | induced | latent |
|---|---|---|---|
| 2 | (3, 1) | (3, 1) | `latent:ratio` |
| 2 | (1, 1) | (1, 1) | `latent:scale2` |
| 2 | (4, 1) | (4, 1) | `latent:scale2` |
| 3 | (2, 1) | (2, 1) | `latent:scale2` |
| 2 | (3, 2) | (3, 2) | `latent:ratio` |

(Ratios whose num/den are powers of two mint `latent:scale2`; the rest mint
`latent:ratio` — both correct, the same dispatch `RatioInduce` already used.)

**(C) Negative control — independent per-axis stretch FALSIFIES after emission:**
`explained=False` (`OK, floored`). The honest MDL floor survives the emitter —
a genuinely non-common-scale population is not falsely explained.

**Reading (in shape).** A whole multiplicative-scale family collapses, through
the emitter, to one held ratio recovered by `RatioInduce` — the reasoning-layer
analogue of `RATIO_INVARIANCE` H-R1, now sourced from a continuous reading
rather than hand-planted integer extents.

---

## H-L3 — FRAME.PY UNLOCK (the headline reasoning site)

**Harness:** `drafts/log_quantum/hl3_frame.py` — uses the **REAL** `domains/frame.py`
machinery (`build_frame` / `dimension_weight` / `relative_weight` / `frame_dims`)
over a real `boot_core` substrate. Not a synthetic stand-in.

**VERDICT: H-L3 CONFIRMED (all four parts).**

Setup: four dimensions with LINEAR importance weights `{topic:1, speaker:4,
affect:16, time:64}` (log₂ → 0, 2, 4, 6). A population of four real Frame nodes
(`ctx_A..D`) differing by a per-frame importance SCALE `{1, 4, 16, 64}` — a
multiplicative factor on every linear weight, i.e. a common additive log-offset
(`build_frame` stores `math.log`).

| # | claim | result |
|---|---|---|
| 0 | frame.py `relative_weight` is scale-invariant (ground truth) | `PASS` — `relative_weight(speaker,topic)=1.3863`, `(affect,topic)=2.7726`, `(time,topic)=4.1589`, **identical across all four frames** (the per-frame importance scale cancels — frame.py's own stated property) |
| 1 | no continuous weight stored in-frame (the emitter quantized it) | `PASS` — the raw **float** log-weight population is REFUSED by `RatioInduce`; after `LogQuantum` (raw=False, base 2) every in-frame coordinate is an `Int` |
| 2 | `RatioInduce` recovers the invariant, per-frame scale factored | `PASS` — recovers the non-degenerate ratio **2:1** (logw-extent 6 : idx-extent 3), `latent:scale2`, constant across all 4 frames |
| 3 | emitted quanta == frame.py `relative_weight` in integer units | `PASS` — quantum-diffs `{topic:0, speaker:2, affect:4, time:6}` == `round(relative_weight(d, topic)/ln 2)` exactly |

**Reading (in shape).** `frame.py`'s `relative_weight = log_weight(a) −
log_weight(b) = log(a/b)` was already a log-ratio — but stored as a `math.log`
float, invisible to the integer-lattice reasoning ladder. The emitter quantizes
those real log-weights to integer log-quanta whose differences ARE the
relative-weight structure in exact integer units (part 3), so a whole population
of frames differing by an importance scale collapses onto one invariant
relative-weight structure that `RatioInduce` recovers with the scale factored
(part 2) — WITHOUT ever storing a continuous weight in-frame (part 1). The
continuous log-weight stays where the invariant says it belongs: on the real
Frame node (frame.py's own store) and in the transient emitter read, never in a
coordinate slot handed to the reasoning ladder.

---

## Regression — existing machinery stays green

| suite | result |
|---|---|
| `tests/test_dimension_inference_migrated.py` + `tests/test_engine_provenance_migrated.py` | 25 passed, 1 skipped |
| `drafts/ratio_invariance/hr1_synthetic.py` (RatioInduce recovery) | `H-R1 CONFIRMED: True` (5/5 + all floors) |
| `drafts/ratio_invariance/hr2_price.py` (RatioInduce price) | `H-R2 PASSED — ratio in Hom` |

The `LogQuantum` addition disturbed nothing: `RatioInduce`, `DimInfer`, and
provenance all stay green on the rebuilt engine.

---

## Usefulness-at-a-price ledger — IN SHAPE (not a benchmark)

| what it buys (usefulness) | what it costs (price, in shape) |
|---|---|
| Any continuous log-domain quantity (log-odds, log-weight, log-prior) becomes an **integer coordinate on a log axis** — admissible to `coord_ints` and thus to the whole rung-1/rung-2 ladder (`RatioInduce`, `scale2`, `DimInfer`). | **Zero against the frame/continuum invariant.** The emitted value is an `Int`; base+Δ live in `Hom`; `coord_ints` untouched; no float ever in a coord slot (H-L1 P1–P4). |
| A per-frame **multiplicative** nuisance (impedance / gain / importance / prior mass) becomes a per-frame **additive** log-offset that a difference/extent cancels — the emitter is the bridge that makes ratio-cancellation reach continuous readings (H-L2, H-L3). | **Resolution Δ is a real, declared cost.** Δ pins the emitter to observational resolution (MDL): distinctions finer than Δ are merged by construction (H-L1 P5). This is a *guard*, not a leak — but it means the emitter never encodes precision the source cannot support, and a caller must choose Δ honestly. |
| **One primitive, many sites.** The emitter is `log_scaled_proprioception` (`seeds/log_graph_law.json`) made a primitive — the substrate applying its OWN declared `log_axis_law` to its OWN internal quantities. | **A modelling commitment:** the input must genuinely be a log-domain (or log-able) quantity related across frames by a *multiplicative* scale. Where the per-frame structure is NOT purely multiplicative, `RatioInduce` correctly returns `explained=false` (H-L2 control C) — the emitter is well-formed but the *site* does not compose, which would be the honest null. None of the three sites tested here hit that. |

## Further sites the SAME emitter now unlocks

The emitter is site-agnostic (it quantizes any continuous log-domain slot), so
each of these becomes a `RatioInduce` population at no additional invariant cost:

- **`domains/context_prior_speaker.py`** — the Bayesian listener's message
  PRIOR / posterior (log-odds, bits of MI): a peaked-vs-flat prior across a
  population of shared-context frames is a log-domain quantity differing by a
  per-frame scale; emit log-quanta → `RatioInduce` the invariant prior structure
  with the per-speaker peakedness factored. (Named in the prereg; not run here —
  frame.py was the headline because it is already a log-ratio by construction.)
- **`runners/dsl/src/can_ops.rs`** — the CAN mean-field marginal (`tanh`
  self-consistency) and energy `H(σ)`: log-odds / log-probability quantities.
  The prereg's stretch demo; the emitter makes them integer-observable the same
  way. Not run (optional, and CAN's marginals are not yet framed as a
  cross-frame multiplicative population — the honest scoping note).

---

## Files

- **Rust op:** `runners/dsl/src/shape_decode.rs::eval_log_quantum` (+ wiring in
  `term.rs`, `term_variants.rs`, `jsonio.rs`, `reflect.rs`).
- **Harnesses:** `drafts/log_quantum/hl1_price.py`, `hl2_synthetic.py`,
  `hl3_frame.py`.
- **Engine:** rebuilt + installed via `scripts/engine_build.sh` (reused crate,
  not forked); existing `shape_decode` / `dim_infer` / `gen_infer` / ratio tests
  stay green.

---

## One-line finding

**An integer-observable log-quantum emitter is well-formed against the
frame/continuum invariant at ZERO price (H-L1), composes with `RatioInduce` as a
log-ratio (H-L2), and turns `frame.py`'s real `math.log` log-weights into a
scale-factored, integer-observable relative-weight structure the reasoning ladder
can induce (H-L3) — the substrate applying its own `log_axis_law` to its own
internal state, via one primitive that generalizes `scale2` from base-2 to any
base + resolution.**
