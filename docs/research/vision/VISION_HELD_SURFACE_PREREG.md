# VISION — HELD SURFACE: does the SURFACE-level reconstruction BUILD, graph-natively? (PREREG)

**Seed block: 180000–180999.** Branch: `worktree-agent-abe2bf48c1c0c0a16`
(isolated worktree off `main` HEAD `e7bb4c684901bb8331859607b27f5f49dffc6943`).

Seed-claim check (verbatim, run before any number):

```
$ python3 scripts/seed_claim.py 180000 180999
SEED CLAIM 180000-180999: CLEAN -- no collision DETECTED.
  Scope: 877 files with seed sinks; 591 UNRESOLVED sink sites tree-wide (counted, not discarded).
```

This document is committed ALONE, BEFORE any measurement, so the thresholds
below cannot be back-fitted. All thresholds are derived from the KNOWN
EMA-accumulation mechanism (analytic `E_lag(t) ≈ (1−r)^t` for the build lag and
`residual_noise ≈ σ_obs·√(r/(2−r))` for the denoised asymptote), not from a run.

---

## The question — close residual #1 of block 179000

Block 179000 (`VISION_SPLAT_OVER_TIME_PREREG.md`) proved the eye BUILDS a fixed
scene, but the genuinely-accumulating layer was only the LOW-LEVEL per-receptor
adapting floor (`adaptation`, an EMA written back by the `photon_retina` rule).
The HIGH-LEVEL surface/percept reconstruction (`scripts/eyeview_render.py`)
**re-derives STATELESSLY each call** — there is no persistent held surface.

This rung lifts the SAME proven EMA-accumulation mechanism ONE LEVEL UP: a
**persistent dense held-surface node** (`HeldSurfaceCell`, one per retina cell)
updated by a **graph-native accumulation/decay RULE** (`held_surface_accumulate`,
seed `held_surface.json`), firing under `run_rules()`. The surface-level
reconstruction itself then BUILDS over ticks — the surface twin of the receptor
adapting floor — and FORGETS (the same EMA decays stale content toward changed
content when the scene moves): object-permanence-WITH-forgetting.

## Why accumulation genuinely helps at the surface grain (not a strawman)

A single tick's surface observation is the eye's noisy per-cell catch
(`caught_quanta` carries photon **shot noise** — the counts are Poisson). A
STATELESS surface carve re-derived each call is therefore a *complete but
un-integrated, noisy* reconstruction whose error is a flat shot-noise floor. The
held surface EMA-integrates the observation over ticks and **temporally
denoises** it — its error converges BELOW the single-tick floor. The gap is a
real reconstruction benefit (temporal integration), not an EMA-lag artifact.

## The mechanism (graph-native; NO Rust, NO new Term)

- **`HeldSurfaceCell`** node per retina cell: `value` (the held EMA), `obs` (last
  observation), `row`/`col`/`cell_index`, `epoch`.
- **`HeldSurfaceParams`** config node: `enabled`, `lr` (surface learning rate).
- **`held_surface_accumulate`** rule (`seeds/held_surface.json`, order 5):
  matches `retina -has_held_surface_params-> params`,
  `retina -has_column-> column`, `column -rod_receptor-> rod`,
  `column -has_held_surface_cell-> hs`; guard
  `params.enabled == 1 AND column.input_epoch > hs.epoch AND
  rod.input_epoch == column.input_epoch` (the last clause is the FRESH-guard:
  fire only after this epoch's transduction has written `caught_quanta`).
  Effect (standard DSL Terms only — `Plus`/`Times`/`Minus`/`Attr`):
  `hs.value ← value + lr·(rod.caught_quanta − value)`; `hs.obs ← caught_quanta`;
  `hs.epoch ← column.input_epoch`.
- **DEFAULT OFF / §9:** the rule cannot fire unless a `HeldSurfaceParams` node
  exists AND is enabled (created by the measure adapter only on opt-in). The seed
  is not in any existing eye's seed list, so every existing path is
  byte-identical. Same default-off precedent as `retinal_superres.json`.

## Protocol (committed before running)

- 2-D retina, `n_az = n_el = 16` (256 cells), `context={"retina_2d": True}`,
  `adapt_rate = 0.15` (the floor, irrelevant to the surface), surface
  `lr = 0.15`, `onset_threshold_db = 6.0`. Deterministic RNG seeded at `180000`.
- **Photon shot noise:** each tick every cell's photon count is sampled
  `count ~ Poisson(λ_cell)` where `λ_cell` is the scene luminance.
- **Scene A** (build): dim background `L_bg = 20`, a bright block `L_hi = 200`
  over rows 4..11, cols 2..7 (48 cells).
- **Scene B** (perturb — the block MOVES): background `L_bg`, the bright block
  relocated to rows 4..11, cols 9..14 (48 cells; disjoint from A's block). The
  held surface must FADE the old block AND ADOPT the new one.
- **Build phase**: ticks `1..T1` with `T1 = 30`, scene A each tick
  (`submit_photons_2d(A); run_cognitive_tasks(1); run_rules()`).
- **Perturb phase**: ticks `T1+1..T2` with `T2 = 60`, scene B each tick.
- **Ground truth**: `true_A`, `true_B` = the NOISELESS caught fields for A, B
  (each cell's `λ + dark_current`), captured once by a noiseless pass.
- **Error** `E(est, true) = mean_i |est_i − true_i| / mean_i true_i`.

### Arms

1. **ACC** — one persistent eye, held surface, `lr = 0.15` throughout. Snapshot
   `held_acc(t)` each tick.
2. **STATELESS** (Control 1) — the un-accumulated single-tick surface: the eye's
   raw per-tick observation `obs(t)` (noisy `caught_quanta`) read off, never
   integrated. This is exactly what a stateless carve produces each call.
3. **FROZEN** (Control 2) — one persistent eye, `lr = 0.15` during build (so it
   BUILDS scene A), then `lr = 0` from tick `T1+1` (a mechanical ablation of the
   accumulation coefficient at perturb onset, the analogue of 179000's
   `adapt_rate = 0`). Held stays stuck at A; it cannot forget/adopt.

## PRE-REGISTERED THRESHOLDS (pass/fail, fixed before any number)

Let `asymptote = mean(E_acc_A over ticks T1−2..T1)` (the built surface error) and
`E_sl = mean(E_stateless over build ticks)`.

### HEADLINE 1 — the SURFACE BUILDS (fixed scene A, build phase)

- **H1a BUILD DROP:** `asymptote < 0.15 · E_acc_A(1)` (≥ ~6× reduction, gist →
  reconstruction). (analytic: `E_acc_A(1) ≈ 1−r = 0.85`, `asymptote ≈ 0.03`.)
- **H1b ASYMPTOTE:** `asymptote < 0.06`.
- **H1c MONOTONE (noise slack):** the number of build ticks with
  `E_acc_A(t+1) > E_acc_A(t) + 0.03` is `≤ 3`.
- **H1d STATELESS FLAT:** `std(E_stateless)/mean(E_stateless) < 0.15` across build
  ticks AND `E_sl > 2 · asymptote` (the single-tick carve does not build and sits
  above the denoised asymptote). (analytic `E_sl ≈ 0.093`.)
- **H1e ACCUMULATION GAP:** `asymptote < 0.5 · E_sl` (the held surface denoises
  clearly below the stateless single-tick floor).

### HEADLINE 2 — DECAY IS REAL (perturb phase; object-permanence-WITH-forgetting)

Let `E_acc_B(t)`, `E_frozen_B(t)` = error vs `true_B`; `tail = mean over ticks
T2−2..T2`.

- **H2a ACC FOLLOWS:** `tail(E_acc_B) < 0.10` (held converges to the moved scene).
- **H2b ACC DECREASES:** `tail(E_acc_B) < 0.4 · E_acc_B(T1+1)` (the first perturb
  tick, held still ≈ A → high error on the moved block → then decays).
- **H2c FROZEN STUCK:** `tail(E_frozen_B) > 0.5` (frozen held cannot fade/adopt;
  the block mismatch keeps it high — analytic `≈ 1.25`).
- **H2d DECAY GAP:** `tail(E_acc_B) < 0.2 · tail(E_frozen_B)` (accumulating follows
  the change; frozen is stuck — the gap IS the decay signal).

## Discipline commitments

- SEPARATE prereg commit (this file ALONE) BEFORE any number.
- NEW FILES ONLY / §9 byte-identity: `git diff --stat` shows only new files
  (`seeds/held_surface.json`, `scripts/held_surface_measure.py`,
  `tests/test_held_surface_migrated.py`, this prereg, the results doc, renders).
  The held-surface seed is additive and default-off. All existing vision gates
  stay green (`test_splat_over_time_migrated`, `test_two_eyes*`).
- Oracle `bash scripts/rung7_vision_bench.sh` = 0 failed, BEFORE == AFTER.
- Provenance (§10): `source_match ∈ {own, shared}`, never a pinned hash. No Rust
  built (goal): canonical `.so` md5 `417f667716d71ed7d98bae5df25fe9df` reported
  unchanged BEFORE and AFTER.
- NO TIMING CLAIM; if cost is measured it is WORK UNITS only.
- Gate `tests/test_held_surface_migrated.py` pins the surface build-curve drop,
  the accumulating-vs-stateless gap, and the decay/perturb-update at the mechanism
  grain (reads measured values; able to fail on a flat curve or a frozen surface).
- Surface splat render sequence saved under `results/held_surface/`.
