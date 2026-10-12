# PLAN — Agenthon Track 3 (Simulation), OCELOT

Derived from `T3_PARTS_AUDIT.md`. The audit's verdict drives the scope: the
reusable OCELOT assets (PyO3/maturin/Docker ship path, integer-tick fit, bench
culture) are all PERIPHERAL to the two hardest Track-3 items (a sim-time DES
kernel and — the crux — numpy-`RandomState`-exact reproduction). Therefore the
opening move is NOT a from-scratch engine.

## The governing insight

Tier-A exactness (families 1,3,6,7,8: exact event multiset + fill sequence +
Kendall-τ≥0.999, `semantics.py:265`) is determined by ABIDES's agents drawing
from `np.random.RandomState`. Reproducing that stream bit-for-bit in Rust is the
highest-risk item and OCELOT contributes nothing to it. BUT: **keep the numpy
agents in place and accelerate only the hot loop → Tier-A exactness is inherited
for free**, because the draws that fix the event sequence are unchanged.

## Scope (audit-recommended, in order)

- **PRIMARY — profile-guided in-place acceleration.** Profile `abides.run`
  (baselines/abides_fork), find the hot loop (matching engine / order-book ops /
  message dispatch / agent stepping). Replace ONLY the hottest, RNG-free inner
  machinery with a Rust module in the existing `substrate_rs` crate, exposed via
  `py.rs`, keeping the numpy agents and their exact `RandomState` draws IN PLACE.
  Inherits Tier-A exactness; ships on the proven wheel/Docker pipeline.
- **SECONDARY (only if primary saturates) — Tier-B from-scratch.** A Rust engine
  scoped to the statistical families (2,4,5: return-KS≤0.08, spread±10bps) where
  OCELOT's own deterministic RNG suffices and bit-exactness is not required.
- **AVOID as opening move** — a from-scratch Tier-A-EXACT rewrite.

## Phases

### Phase 0 — Stand up the baseline + pin the exact bar (LOAD-BEARING)
The correctness gate is the whole game; nothing is safe until the baseline runs
green locally. Do:
- Clone ABIDES at the pinned commit (baselines/README.md), install
  abides-core + abides-markets (+ the pomegranate-free patch), install
  qfbench2-common@v2.3.1, build the baseline Docker image.
- `build_reference_cache.py`, then `run_regression.py` over all 65 public
  scenarios against the baseline → confirm 65/65 pass + stylized facts 0.0.
- Measure baseline `events_per_sec` (throughput/timer.py on as06_throughput_fast).
- READ `semantics.py::check_tier_a` fully — pin the exact reproduction contract.
- DELIVERABLE: `T3_PHASE0.md` — baseline green Y/N, the speed floor number, and
  the exact Tier-A contract in our words.

### Phase 1 — Profile: find the hot loop
- Profile `abides.run` on a representative scenario (cProfile / py-spy) → where do
  the events/sec actually go? matching, order-book insert/cancel, message queue,
  agent wakeups? This DECIDES what to accelerate; do not guess.
- Confirm the hot inner ops are RNG-FREE (so replacing them preserves the numpy
  draw stream → Tier-A exactness). Any hot op that CONSUMES an agent's random
  draw must stay in numpy or reproduce the draw exactly — flag these.
- DELIVERABLE: `T3_PHASE1.md` — the profile, the % of wall-clock in each
  component, and the specific RNG-free hot target(s) to port to Rust.

### Phase 2 — Rust hot-loop module in the existing crate
- Add `market_engine.rs` (or the profile-named target) to `runners/dsl/`, exposed
  via `py.rs` one-line handoffs, reusing the whole maturin abi3 wheel path.
- Drop it in behind `abides_fork` for the hot op ONLY; numpy agents untouched.
- Re-run `run_regression.py` after EACH change (audit/README rule: never let
  correctness slip) — 65/65 must stay green, stylized facts must stay passing.
- DELIVERABLE: the Rust module + the wired adapter + a regression-green log.

### Phase 3 — Validate, measure, containerize
- Full regression (65/65) + 4 stylized-fact checks + the `simulate` AND
  `simulate-batch` verbs (batch families need per-sub isolation).
- Measure speedup vs the Phase-0 floor; build the Docker image on the proven
  pipeline (maturin wheel + qfbench2-common@v2.3.1, `--network none`, no
  ENTRYPOINT, `simulate`/`simulate-batch` on PATH).
- DELIVERABLE: `T3_PHASE3.md` — regression-green, stylized-facts-pass, measured
  speedup, admissible image; + a `T3_STATUS.md` with proven vs
  unverifiable-locally (sealed scenarios, SS-BENCH, ranked number) and the
  ordered remaining actions.

## Discipline
PREREG-then-measure per phase; nulls are findings (e.g. "the hot loop is inside
numpy agents' RNG draws, so in-place Rust acceleration can't preserve Tier-A" is
a valid, plan-changing finding — surface it in Phase 1, do not force Phase 2).
No fabricated speed numbers. Reuse the substrate_rs crate + wheel + Docker path;
add a Rust module, never fork the build. If the hot loop turns out to be
RNG-entangled, STOP and re-scope to Tier-B (secondary) rather than breaking
Tier-A exactness.

## The honest risk (stated up front)
The primary scope's payoff depends on Phase 1 finding a HOT, RNG-FREE inner loop
big enough to matter. If ABIDES's time is dominated by numpy agent stepping
(which consumes RNG), a Rust kernel can't touch it without breaking Tier-A, and
the realistic scope collapses to Tier-B statistical families only. Phase 1 is the
go/no-go; Phase 0 is the prerequisite that makes Phase 1 possible.
