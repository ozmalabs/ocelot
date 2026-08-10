# PREREG — ASYNC MOTION FROM THE EVENT STREAM (Rung 2 of the photon-eye migration)

**Seed block: 136000–136999** (`check_claim(136000, 136999)` CLEAN — no
collision detected; drawn once at `default_rng(136000)`). Committed BEFORE any
confirmatory number.

## The claim

Motion (direction + speed) is recovered from the ASYNCHRONOUS onset-event stream
(`RetinalOnsetEvent` nodes minted by Rung 1, `seeds/retinal_onset.json` +
`photon_transduce_onset`), NOT from a two-frame `vector_field` /
`retinal_flow_depth` difference and NOT from the coarse `retinal_field` raster.

A moving edge is onset events firing in ADJACENT columns at SUCCESSIVE
per-receptor epochs. Each event carries its OWN epoch (its own clock). Correlate
column position against per-event epoch across the accumulated events: the SLOPE
of that space-time relation IS the velocity (columns per epoch). Direction =
sign(slope). Speed = |slope|. The fit is SETTLED from the events available this
tick, always leaving a residual (the unexplained column variance) — not a
snapshot difference.

## The mechanism (fixed before the confirmatory run)

- **Rust kernel `retinal_event_motion`** (pure peer of `photon_transduce` /
  `retinal_flow_depth`): payload `[n, c_0, e_0, …, c_{n-1}, e_{n-1}]` of onset
  events (column index `c_i`, own epoch `e_i`). Least-squares slope of column on
  epoch:
  - `slope = Σ(e-ē)(c-c̄) / Σ(e-ē)²`  (velocity, columns per epoch)
  - `r = Σ(e-ē)(c-c̄) / √(Σ(e-ē)²·Σ(c-c̄)²)`  (Pearson coherence, |r|∈[0,1])
  - `residual = Σ(c-c̄)² − slope·Σ(e-ē)(c-c̄)`  (SSE — the settlement residual)
  - Returns `(direction=sign(slope), speed=|slope|, residual, coherence=|r|, n)`.
  - `n<2`, or zero temporal spread `Σ(e-ē)²=0`, or zero spatial spread → `(0,0,…)`.
- **Seed `seeds/retinal_motion.json`** rule `retinal_mint_motion`: mints a
  `RetinalMotionPercept{direction, speed, residual, coherence, epoch}` iff the
  done `retinal_event_motion` task has `coherence > min_coherence` AND
  `n > min_events` (both thresholds are DATA on a `RetinaMotionParams` node),
  once per task via a `motion_seen` guard.
- **OFF by default (§9):** engages only under `context["visual_motion"]`, which
  creates the `RetinaMotionParams` node; absent it the rule cannot match and no
  motion task is ever created. Coarse / onset-only paths byte-identical.
- **Python is mechanical only:** the adapter reads `RetinalOnsetEvent` attrs
  (`column_index`, `epoch`) — the EVENT STREAM, nothing from the raster — packs
  them into the task payload, and reads the percept back. No decision in Python.

## Headline QUANTITY + pre-registered interval

On a controlled synthetic sweep (a single bright column swept across the retina
at a range of true speeds, L→R and R→L), the recovered speed tracks the true
sweep speed:

> **ρ = Pearson correlation between recovered speed and true sweep speed, over
> the speed sweep, ∈ [0.90, 1.00].**

Interval justified from the mechanism: on a noiseless synthetic diagonal the
least-squares slope EQUALS the true step exactly, so ρ→1.0; [0.90, 1.00] leaves
headroom for column quantization / event-count differences across speeds without
admitting a null (ρ≈0) result.

## Able-to-fail controls (read MEASURED values; no constant re-derived in Python)

1. **MOVING → correct motion recovered:** L→R sweep gives `direction=+1`, R→L
   gives `direction=-1` (sign-correct), coherence high; speed tracks GT (the
   headline ρ).
2. **STATIC → no motion:** a held/dark scene mints no onset events → the motion
   task sees `n<2` → coherence 0 → NO `RetinalMotionPercept` (silent in, silent
   out).
3. **SCRAMBLED-event-times control → no coherent motion:** the SAME event column
   multiset with epochs shuffled destroys the space-time diagonal → coherence
   collapses below `min_coherence` → no coherent motion. Proves the signal is the
   space-time STRUCTURE, not a static column bias.

## Oracle + provenance

- `bash scripts/rung7_vision_bench.sh` = 0 failed, BEFORE == AFTER (flag off).
- Gate `tests/test_async_motion_migrated.py`; provenance asserts
  `source_match in ("own","shared")`.

## Merge-block statement

Motion is derived from the async EVENT STREAM (`RetinalOnsetEvent` + per-receptor
epochs), never from the `retinal_field` raster and never from a two-frame
`vector_field` / `retinal_flow_depth` diff. Source-audited in the gate.
