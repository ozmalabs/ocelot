# PREREG — the integer-observable log-quantum emitter

**Committed BEFORE any number.** Expands a FUNDAMENTAL substrate capability. It is
the shared machinery the reasoning-layer RatioInduce assessment
(`RATIO_IN_REASONING_LOG.md`) identified as the single unlock: read a continuous
log-domain quantity (log-odds, log-weight, log-prior) at observational resolution
as a STEPPED INTEGER coordinate on a log axis, with the continuous base/resolution
held in `Hom` (intensional, applied on read), so `coord_ints` sees an integer and
the frame/continuum invariant is satisfied BY CONSTRUCTION. Build one; CAN
grounding marginals, `frame.py` log-weights, and Bayes log-priors all become
RatioInduce populations at once.

## The warrant is the substrate's own declared law (not an imposition)

`seeds/log_graph_law.json` already states this worldview as held knowledge:
- `log_axis_law`: "Quantities are COORDINATES ON A LOG AXIS, not values on a
  linear one. Information (−log p), description length, perception (Weber-Fechner),
  scale, growth are all natively log."
- `log_scaled_proprioception` (the named LEVER): "proprioceptive gauges should be
  LOG-scaled (a log sensor on a log world reads linearly = efficient); hot-counters
  log-binned; thresholds log-spaced. Align the instrumentation with the axis the
  system runs on."
- `compute_in_log_space`: "represent quantities as logs so multiplication becomes
  addition."

The emitter is `log_scaled_proprioception` made into a primitive. This is the
substrate applying its OWN stated law to its OWN continuous internal quantities.

## The precedent is exact: `scale2` already treats log₂ as an integer axis

`shape_decode.rs::scale_pow2_once` (:736) makes log₂ a DimensionGenerator: a ×2^k
scale family collapses to one held shape + one `latent:scale2` dimension, the
quantum `k` is the ADDITIVE integer step in log₂, and `coord_ints` keeps it
integer-lattice-only. The emitter GENERALISES this from the fixed base-2 spatial
case to ANY continuous log-domain quantity at a chosen resolution: the log-quantum
is `round(log_a(x) / Δ)`, the same integer-step-on-a-log-axis shape `scale2`
already proves well-formed.

## The contract (well-formed by construction)

`LogQuantum` — a Rust DSL op (wired like `scale2`/`RatioInduce`). Given a
continuous log-domain quantity `x` (or a raw value to be logged) and a resolution
policy, it emits the INTEGER log-coordinate `q = round(log_a(x) / Δ)`:
- `q` is the ONLY thing that lands in-frame — an Int, so `coord_ints` accepts it.
- the base `a` and resolution `Δ` are held in `Hom` (params on the emitter /
  a `LatentDimension` descriptor), APPLIED on read, NEVER stored as an in-frame
  coordinate — exactly the invariant's "continuity is intensional; the observable
  is the stepped integer rendering; a continuous parameter pinned only to
  observational resolution (MDL)."
- a DIFFERENCE of two log-quanta `q_i − q_j` is a log-ratio (= `log_a(x_i/x_j)/Δ`)
  in integer units — precisely the shape `RatioInduce`/`scale2` consume. So the
  emitter's output feeds the ratio-induction ladder directly.

Resolution `Δ` is pinned to OBSERVATIONAL resolution (MDL: never encode precision
the source can't support) — the invariant's identifiability guard. Weber-scaled by
default (equal log steps = equal perceptual/ratio steps), matching
`log_scaled_proprioception`.

## Hypotheses (falsifiable, pre-declared)

- **H-L1 (well-formedness — THE crux):** the emitter puts ONLY an integer in-frame;
  base+resolution live in `Hom` applied-on-read; `coord_ints` still refuses floats;
  no continuous coordinate is stored in-frame. CONFIRMED iff the emitted quantum is
  Int, the emitter round-trips as a Term with base/Δ as intensional params, and a
  float is never written to a coord slot. FAIL (needs to store the continuous value
  in-frame) → the emitter cannot be well-formed and that is the finding (a real
  boundary). This is the whole point: the price must be zero against the invariant.

- **H-L2 (log-ratio composition):** a DIFFERENCE of two log-quanta is an
  integer log-ratio that `RatioInduce` consumes — i.e. quantities related by a
  multiplicative factor `f` emit log-quanta differing by the constant integer
  `round(log_a(f)/Δ)`, so a population of frames differing by a per-frame
  multiplicative scale becomes a population of integer-coordinate frames differing
  by a per-frame additive log-offset that RatioInduce factors. CONFIRMED iff, on a
  synthetic population with planted per-frame multiplicative scales, emitting
  log-quanta then running RatioInduce recovers the invariant and factors the
  per-frame scale (the reasoning-layer analogue of RATIO_INVARIANCE H-R1, now via
  the emitter instead of raw integer extents).

- **H-L3 (reasoning-layer unlock — at least one real site):** on ONE of the
  identified log-domain sites, the emitter makes a continuous log-quantity
  RatioInduce-consumable. Target the CLEANEST: `domains/frame.py`'s log-weights
  (`relative_weight = log_weight(a) − log_weight(b) = log(a/b)`, frame.py:171-179 —
  already a log-ratio, just stored as float). Emit integer log-quanta of the
  per-dimension weights across a POPULATION of frames differing by a per-frame
  importance scale; run RatioInduce; recover the invariant relative-weight
  structure with the per-frame scale factored out. CONFIRMED iff the frame
  population's per-frame scale is factored and the invariant relative-weight ratios
  recovered — WITHOUT storing a continuous weight in-frame (the emitter quantises
  it). A secondary demonstration on the CAN log-odds marginal
  (`can_ops.rs` tanh/energy) is a stretch goal; frame.py is the headline because it
  is already a log-ratio by construction.

## What each outcome MEANS (pre-committed)

- **H-L1 ∧ H-L2 ∧ H-L3** → the reasoning layer's continuous log-domain quantities
  are now RatioInduce-consumable via a single well-formed primitive; the substrate
  applies its own `log_axis_law` to its own internal state. General across sites
  (CAN, Frame, Bayes-prior) because they share the emitter.
- **H-L1 fails** → an integer-observable log-quantum cannot be emitted without
  storing continuous in-frame state; the invariant forbids the reasoning-layer
  application; report the boundary (the log-quantum is not well-formedly
  representable) — a real finding, not a workaround target.
- **H-L2 or H-L3 null** → the emitter is well-formed but does not compose with
  RatioInduce / does not factor a real site's scale (e.g. the frame population's
  scale is not purely multiplicative in log). Report the residual.

## Method / discipline

- Build on the REAL machinery: model the emitter on `scale_pow2_once`/the
  `latent:scale2` mint path (the existing log-axis-as-integer precedent); wire the
  Term through the full set (`term.rs`/`term_variants.rs`/`jsonio.rs`/`reflect.rs`,
  `py.rs` generic handoff), like `RatioInduce`. Reuse the crate/wheel path; do NOT
  fork. Existing shape_decode/dim_infer/ratio tests stay green.
- The invariant is the GATE, checked FIRST (H-L1): integer in-frame, base+Δ in
  `Hom`, `coord_ints` untouched, resolution pinned to observation (MDL). A build
  that must store continuous in-frame state to work is a FAILURE reported as the
  boundary, not forced.
- Synthetic body first (H-L2, planted multiplicative scales through the emitter),
  then the frame.py reasoning site (H-L3, real log-ratio weights). CAN marginal is
  a stretch demo, not required.
- PREREG-then-measure; nulls are findings; usefulness-at-a-price reported IN SHAPE
  (what it unlocks + what it costs the invariant), not a benchmark.

## Deliverables

- `LOG_QUANTUM_RESULTS.md` — H-L1 (invariant-respected/price), H-L2 (log-ratio
  composition with RatioInduce), H-L3 (frame.py reasoning-site unlock), and the
  usefulness-at-a-price-in-shape ledger + which further sites (CAN, Bayes-prior)
  the same emitter now unlocks.
- the Rust `LogQuantum` op + Term wiring + the synthetic and frame.py exercise
  harnesses. Reuse the crate/wheel path; invariant respected by construction.

---
MEASUREMENT GATE — nothing above this line is edited once numbers exist.
