# RESULTS — ASYNC MOTION FROM THE EVENT STREAM (Rung 2, block 136000–136999)

Prereg: `VISION_ASYNC_MOTION_PREREG.md` (committed `b4649cabae`, before any
confirmatory number). Seed block `136000–136999` `check_claim` CLEAN before the
draw; after the draw the only occupier is this rung's own
`tests/test_async_motion_migrated.py` (136000, 136001), no ledger overlap.

## What landed

- **Rust kernel `retinal_event_motion`** (`runners/dsl/src/cognitive_tasks.rs`,
  a pure peer of `photon_transduce` / `retinal_flow_depth`): takes the async
  onset-event cloud `[n, c_0, e_0, …]` (column index + the event's OWN epoch) and
  returns `(direction=sign(slope), speed=|slope|, residual=SSE, coherence=|r|, n)`
  from the least-squares slope of column on epoch — the space-time STRUCTURE of
  the events, settled from what is available this tick, leaving the residual.
- **Seed `seeds/retinal_motion.json`** rule `retinal_mint_motion`: mints
  `RetinalMotionPercept{direction, speed, residual, coherence, epoch}` iff
  `coherence > min_coherence` AND `n > min_events` (thresholds are DATA on a
  `RetinaMotionParams` node). OFF by default (no params node, no motion task).
- **Adapter (`domains/photon_eye.py`)**: `settle_motion(since_epoch)` reads ONLY
  `RetinalOnsetEvent` attrs (`column_index`, `epoch`) — the event stream — packs
  the payload, links the task to the retina; `motion_percepts()` reads back.
  Mechanical I/O only, no decision. `visual_motion` context implies the onset
  path (motion is derived FROM onset events).

## Measured (gate `tests/test_async_motion_migrated.py`, 7/7 passed)

### Headline (pre-registered ρ ∈ [0.90, 1.00])

| true sweep speed | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| recovered speed  | 1.0 | 2.0 | 3.0 | 4.0 |

**ρ = Pearson(recovered, true) = 1.0000 ∈ [0.90, 1.00] → PASS.** On the noiseless
synthetic diagonal the least-squares slope equals the sweep step exactly.

### Able-to-fail controls (MEASURED, not re-derived)

| control | measured | verdict |
|---|---|---|
| MOVING L→R (kernel + eye) | direction **+1**, speed tracks step, coherence 1.000 | motion recovered |
| MOVING R→L | direction **−1** | sign flips correctly |
| STATIC (dark window) | **0** motion percepts | silent in → silent out |
| SCRAMBLED epochs (kernel, n=6) | coherence **0.486** vs clean **1.000** | structure is load-bearing |
| SCRAMBLED epochs through the MINT RULE (n=32) | coherence **0.154**, **0** percepts minted | rule declines incoherent set |
| DEFAULT OFF (`visual_motion` absent) | no params node, `settle_motion()→None`, 0 percepts, plain kind | byte-unchanged |

All three pre-registered controls fire: moving → correct motion; static → none;
scrambled → no coherent motion (coherence collapses below `min_coherence`=0.5).

### Merge-block source audit (in-gate)

`test_motion_is_derived_from_the_event_stream_not_a_raster_or_frame_diff`:
`settle_motion`'s source references `RetinalOnsetEvent` / `column_index` / `epoch`
and contains NONE of `retinal_field`, `vector_field`, `retinal_flow_depth`,
`_previous_field`, `PhotonExposure`. **Motion is derived from the async EVENT
STREAM, never a raster or two-frame diff.**

## Oracle (`scripts/rung7_vision_bench.sh`) — flag off

| | passed | skipped | failed |
|---|---|---|---|
| BEFORE (pristine 6a6d5ea066 engine) | 214 | 10 | **0** |
| AFTER (this rung's engine, flag off) | 214 | 10 | **0** |

**BEFORE == AFTER, 0 failed.** (10 skipped = optional-dep skips with `data/`
absent; the 214+10=224 total matches Rung 1's "224" under `data/` present where
those 10 pass instead of skip.)

## Provenance (§10)

`engine_provenance()["source_match"] == "own"` — the engine is a build of this
tree's Rust (source == binary; the gate asserts `in ("own","shared")`).

## Honest residuals (owned)

1. **Windowed settle.** `settle_motion(since_epoch)` reads a host-supplied epoch
   window, excluding the Rung-1 cold-start warm-up events (adaptation=0 fires for
   ~6 dark epochs before the floor primes — a known Rung 1 residual). The window
   is I/O framing (the async twin of an on-clock frame window), not a decision;
   with `since_epoch=None` it settles the whole held cloud. A persistent agent
   would window by "events since last settle"; not built here.
2. **Least-squares slope is a single rigid-velocity fit.** One coherent motion
   per settle; multiple simultaneous motions / transparent motion would need a
   per-cluster fit (the events already carry the structure; the estimator does
   not yet segment). Named, not built.
3. **Coherence threshold is a DATA default (0.5), not learned.** The gate reads
   MEASURED coherences (clean 1.0 vs scrambled 0.15/0.49) and only checks they
   straddle the default; the threshold itself is not tuned to pass.
4. **Synthetic sweep, integer steps.** Speed tracking is exact because the
   stimulus is noiseless and column-quantized; real ink/video will introduce
   event jitter (the fit degrades gracefully via coherence, untested here).
5. **Still on one shared clock at settle time** (inherited Rung 1 residual): each
   event already carries its per-receptor epoch, so the fit is async-correct; the
   host just settles them together until per-area ticks decouple.

## Files touched

- `runners/dsl/src/cognitive_tasks.rs` — `retinal_event_motion` kernel + unit test.
- `seeds/retinal_motion.json` — `retinal_mint_motion` rule + params/percept productions.
- `domains/photon_eye.py` — `_motion_enabled`, params node, `settle_motion`,
  `motion_percepts` (all gated on `visual_motion`).
- `tests/test_async_motion_migrated.py` — the gate (7 tests).
- `VISION_ASYNC_MOTION_PREREG.md` / `VISION_ASYNC_MOTION_RESULTS.md`.

Instance 2 of the photon-eye migration (async motion off the event stream,
replacing the frame-diff). Next = async carve / depth off the event stream.
