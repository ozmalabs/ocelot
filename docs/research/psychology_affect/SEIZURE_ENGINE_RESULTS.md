# SEIZURE IN THE REAL ENGINE — results

Confirmatory run of `SEIZURE_ENGINE_PREREG.md` on FRESH seeds 5–14, frozen
architecture untouched. Every number here comes from the REAL engine settling a
`CognitiveArea` lattice via `run_rules` + `fold_clock_edge` (no numpy
settlement). Data: `results/seizure_engine.json`; figure:
`results/seizure_engine_figure.png`. Reproduce:
`python3 scripts/seizure_engine_experiments.py`.

## Verdict

**SUPPORTS — the REAL engine reproduces the paper's standing→persist/die→
traveling bifurcation from the give when tuned, and normal cognition is
byte-identical when the dial is off.** Every registered prediction held; the
byte-identity-when-off safety claim is proven. **No new Rust Term** was added
(the settlement is one graph rule of existing DSL Terms).

Honest bound (unchanged from the prereg): this delivers the glass-box TOOL —
the actual cognition engine, tunably seizure-capable, default-off. It does NOT
claim the positive-feedback term is functionally NECESSARY for cognition; we
ADDED it for the capability. That question stays open and separate.

## The engine's settlement, driven by run_rules + fold_clock_edge

One substep = one `(run_rules, fold_clock_edge)` pair. The rule
`sz_settle_next_residual` (seed `seizure_dynamics`) reads each area's current
`residual` (+ neighbours' current `residual` over `projects_to`) and writes
`next_residual` combinationally; the engine's native `fold_clock_edge` commits
`next_residual → residual` at the clock edge (the double-buffered synchronous
substep — the engine's own "tock"). The Python harness is a world adapter only:
it sets the focal onset `drive` and the async per-area `ticking` clock, ticks
the engine, and reads `residual`. Every dynamical term (overload regeneration,
give/shed, dissipation budget, lateral broadcast/recruitment) lives in the graph
rule, evaluated in Rust. This is strictly stronger than the reduced numpy model.

## Results vs registered predictions

| Pred | Claim | Result | Verdict |
|---|---|---|---|
| **P1** | standing onset | rank-1 fraction 0.73–0.87 (dominant); onset-window front propagation ≈ 0 at give=1.0 (0.0 areas), small (≈1 area) elsewhere | HOLDS |
| **P2** | give intact → graceful | give=1.0 DIES at every drive D∈{1,3,6,12,30,60} (final active 0) | HOLDS |
| **P3** | fold in [0.50,0.65] | **median fold = 0.5375**, range [0.5375, 0.55] across fresh seeds 5–14 | HOLDS |
| **P4** | traveling wave emerges | persisting regime: front advances monotonically, **linear r² up to 0.999** | HOLDS |
| **P5** | matched control | interictal (give=0.60) DIES vs seizure (give=0.50) PERSISTS — only `give` differs | HOLDS |
| **P6** | anti-null (vertical boundary) | fold identical across D∈{2,4,8,16} (seeds 5–7) → **persistence tracks give, not drive** | HOLDS |
| **P7** | good null (α necessity) | **alpha=0 never persists at any give**, including give=0 (peak active grows 28→83 then dissipates) | HOLDS |
| **P7b** | desync rescue | restore give=1.0 on a running seizure at t=120 → active 257 → **0** (aborts) | HOLDS |
| **P8** | quantitative contact (bonus) | traveling speed brackets the paper's 0.48 mm/s untuned (give=0.30 → 0.43, give=0.20 → 0.54); standing rank-1 0.73–0.87 (paper 0.94) | PARTIAL-GOOD |

## The bifurcation is carried by the give, independent of drive (the anti-null)

- The give-fold is **give\* = 0.5375** (fresh seeds) and is **the same at
  D∈{2,4,8,16}** — a near-vertical boundary in the (drive, give) plane.
  Persistence is a property of the GIVE, not of how hard the onset drives.
- Give intact (give=1.0) never seizes even at D=60. Too much input does not
  cause the seizure; too little give does.
- So the give-dial carries persistence INDEPENDENT of drive strength — the same
  result the reduced model reported, now on the real engine.

## The anti-plant core: BOTH dials are required, neither alone seizes

- **Positive feedback OFF (alpha=0): never seizes, at any give** — the lattice
  can only dissipate; the standing wave spreads a little then dies (peak active
  28 → 83 as give drops from 1.0 to 0.0, but final active 0 every time). The
  seizure is NOT an artefact of removing the give.
- **Give intact (give=1.0) with alpha ON: never seizes** (P2) — the overload is
  shed before it can recruit.
- The seizure exists only in the interior where alpha>0 AND give<give\*. This is
  the emergence test: standing→traveling is a genuine positive-feedback-vs-
  dissipation instability in the engine's own settlement, not scripted.

## The load-bearing safety check — byte-identity when off (PROVEN)

Adding pathology-capability to the core engine, normal cognition must be
provably unchanged when the dial is off. Proven three ways:

1. **Dedicated byte-identity test** (`test_seizure_dynamics_migrated.py::
   test_scheduler_settlement_byte_identical_with_seed_present_off`): a real
   scheduler scenario (area + two tasks + residual + projection + load, driven
   to `run_rules` fixpoint) reaches a **node-for-node identical graph state**
   whether or not the seizure seed is loaded. The rule matches only areas with a
   `sz_managed_by` edge, which the scheduler graph never has, so it is inert.
   PASSES.
2. **Scheduler / cognitive benches green with the seed present**:
   `test_seizure_dynamics_migrated` (5) + `test_cognitive_tasks_migrated` +
   `test_cognitive_cycle_migrated` + `test_meta_cognitive_migrated` +
   `test_cost_scheduling` = **37 passed**.
3. **Broad conversation/self subset UNCHANGED** by the seed. On this worktree at
   the base commit, `test_gap_awareness_migrated` +
   `test_topic_route_selfheal_migrated` + `test_self_gaps_surfacing_migrated`
   run **14 failed / 13 passed** — and the result is **identical with the
   seizure seed present vs. physically removed** (verified by moving the seed
   file away and rerunning: same 14 failed / 13 passed). Those failures are
   PRE-EXISTING base/environment reds (this worktree is at `7003c9ca23` without
   later conversation fixes / optional data), NOT introduced by this work. That
   the number does not move when the seed is added or removed IS the byte-
   identity demonstration on a partially-red subset.

The seed also declares `self_load_only: true` and is not in any default boot
set, so a normal agent never loads it at all.

## Honest caveats (recorded, not rescued)

- **The positive-feedback term was ADDED, not derived.** The engine as built is
  convergent (the supervisor's finding); we added `alpha` for the capability.
  Functional necessity (does an escalation term the engine needs anyway produce
  the seizure as a side-effect?) is untested and separate. No claim it does.
- **The async clock is harness-driven.** The per-area `ticking` schedule is set
  by the adapter each substep (the async clocks are not yet unified into the
  engine — that is the standing `ozma_global_clock_is_the_lie` work). The
  SETTLEMENT is the engine's; the CLOCK is I/O.
- **Quantitative contact is bracketing, not a fit.** Speed brackets 0.48 mm/s
  with scale pinned from two observations; standing rank-1 (0.73–0.87) is below
  the paper's 0.94. Bonus-level, changes no verdict.
- **`neighbour` recruitment reads current residual**, a same-substep coupling
  (the reduced model buffered one substep). The bifurcation is unaffected.
- **No timing claims.** Everything here is about the bifurcation/dynamics.

## Files

- `seeds/seizure_dynamics.json` — the default-off seed (generated).
- `scripts/seizure_engine_seed.py` — seed generator (authoring tool).
- `scripts/seizure_engine_lattice.py` — engine driver + metrics.
- `scripts/seizure_engine_experiments.py` — confirmatory sweep + figure.
- `scripts/_seizure_pilot.py` — disclosed pilot (seeds 0–4).
- `tests/test_seizure_dynamics_migrated.py` — byte-identity + mechanism gates.
- `results/seizure_engine.json`, `results/seizure_engine_figure.png`.
- `SEIZURE_ENGINE_PREREG.md` — pre-registration (committed before these numbers).
