# VISION — SPLAT OVER TIME: does the eye BUILD a fixed scene? (PREREG)

**Seed block: 179000–179999.** Branch: `worktree-agent-ae1d233877c27f846`
(isolated worktree off `main` HEAD `7b6ded99d4a4d7ade4936b0d092be2482065bacb`).

Seed-claim check (verbatim, run before any number):

```
$ python3 scripts/seed_claim.py 179000 179999
SEED CLAIM 179000-179999: CLEAN -- no collision DETECTED.
  Scope: 877 files with seed sinks; 596 UNRESOLVED sink sites tree-wide (counted, not discarded).
```

This document is committed ALONE, BEFORE any measurement, so the thresholds
below cannot be back-fitted to the numbers. All thresholds are derived from the
KNOWN accumulation mechanism (the EMA analytic `E(t) ≈ (1−r)^t`), not from a run.

---

## The question

The event-native photon eye (`domains/photon_eye.py::GraphEye`, 2-D path) plus
its graph-native accumulation already exist. This rung makes the accumulation
VISIBLE and FALSIFIABLE: hold ONE FIXED scene in front of the eye, tick it over
time, snapshot the held state at intervals, and ask whether it goes coarse GIST
→ full RECONSTRUCTION — and whether per-tick COMPUTE DRAINS as the scene
stabilizes (compute-∝-surprise).

The crux the codebase flagged: **"does the splat build?" ≡ "does the eye
ACCUMULATE?"** If the held state recomputes statelessly each tick, the render is
identical every tick and the build shows nothing — a FLAT outcome is itself a
legitimate finding, not a failure to force.

## What accumulates in THIS eye (established by code audit BEFORE prereg)

The eye persists LOW-LEVEL perceptual state graph-natively across `tick()`:

- **The per-receptor adapting floor `adaptation`** — an EMA over the receptor's
  own history: `next_adaptation = adaptation + adapt_rate·(caught − adaptation)`
  (`runners/dsl/src/cognitive_tasks.rs`, `photon_transduce_onset`), written back
  by the `photon_retina` seed rule (`set_attr_if_different receptor adaptation
  output[1]`) and read into the NEXT frame's payload
  (`photon_eye.py::submit_photons_2d`, `payload[2] = adaptation`). It carries the
  scene forward and converges to the caught luminance.
- **The accumulating onset-event stream** — `RetinalOnsetEvent` nodes minted by
  the `retinal_onset_2d` rule when `output[3] = 20·log10(caught/adaptation)`
  exceeds a DATA threshold; they persist (never deleted) and pile up per
  column/row/epoch. NOTE: onset fires on an INCREASE (caught > adaptation → dB
  positive); a decrease does not cross the positive threshold.
- **Per-column refractory epoch** (`last_onset_epoch`).

There is NO persistent dense "held percept" node beyond these; the raw
`PhotonExposure` is discarded each frame, and `scripts/eyeview_render.py`'s
surface-level "held state" re-carves statelessly. So the honest, genuinely-wired
held reconstruction is **the per-receptor adapting floor `adaptation`**, and the
honest, genuinely-wired compute signal is **the onset-event count per tick**.
Both are read out MECHANICALLY (no Python decision; the accumulation is the
eye's own `photon_retina` EMA rule + `retinal_onset_2d` rule under `run_rules`).

## The measured quantities (mechanical read-out only)

- **Held reconstruction** = the per-cell adapting floor field `adaptation_i(t)`.
- **Ground-truth target** = the per-cell caught field `caught_i` (= the
  receptor's `caught_quanta`, deterministic and constant for a FIXED scene; the
  EMA floor chases it).
- **Normalized reconstruction error** `E(t) = mean_i |adaptation_i(t) −
  caught_i| / mean_i caught_i`. (Analytically `E(t) ≈ (1−r)^t` for a fixed
  scene; `r = adapt_rate`.)
- **Per-tick compute** `C(t)` = number of `RetinalOnsetEvent` nodes minted at
  epoch `t` (the eye's spent "looks" — each onset is one unit of surprise-driven
  settlement work). NO wall-clock; WORK UNITS only.
- **Per-cell look allocation (explicit fovea signal)** = accumulated onset-event
  count per cell over a window (where the eye SPENT its looks).
- **Per-cell error-drop (implicit fovea signal)** = per-cell change in
  `|adaptation_i − caught_i|` over a window (where the reconstruction moves most).

Note (established by the existing gate `test_salience_static_field_is_empty_in_2d`):
the eye's motion-residual `RetinalSalience` map is EMPTY on a static scene, so it
is NOT a usable fovea signal here; the onset-event allocation IS the eye's actual
compute/look allocation and is the explicit signal used for Headline 3.

## Protocol (committed before running)

- 2-D retina, `n_az = n_el = 16` (256 cells), `context={"retina_2d": True}`
  (onset path on by construction), `adapt_rate = 0.15`, `onset_threshold_db = 6.0`.
- **FIXED scene A**: per-cell luminance = a dim background (`L_bg = 20` photon
  units) with a bright block (`L_hi = 200`) over a fixed rectangular region;
  converted to per-cell photon counts, presented IDENTICALLY each tick. Every
  cell catches ≥ `L_bg` → every cell is "lit" (`N_lit = 256`).
- **Build phase**: ticks `1..T1` with `T1 = 20`, scene A each tick (one
  persistent eye: `submit_photons_2d(A); run_cognitive_tasks(1); run_rules()`).
- **Perturb (a BRIGHTENING, so onsets re-fire)**: at tick `T1+1`, switch to
  **scene B** = scene A with one `K×K` sub-patch (`K = 4`, `N_perturbed = 16`,
  ~6% of cells) in a previously-DIM region raised from `L_bg` to `L_hi`; present
  scene B for ticks `T1+1..T2` with `T2 = 40`.
- **Snapshot** each tick: `adaptation_i`, `caught_i`, `C(t)`.
- **STATELESS control** (truly not-persisted-between-ticks): a FRESH eye is
  built each tick and shown scene A ONCE, then read — held state never carries
  forward (`E_stateless ≈ 1−r = 0.85` every tick). Expected FLAT.
- **FROZEN control** (secondary): the same persistent eye with `adapt_rate =
  0.0` — the accumulation coefficient is switched off; the floor cannot
  integrate (`E_frozen ≈ 1.0` every tick). Expected FLAT.
- Deterministic (fixed scene, fixed patch placement). No Rust built (goal);
  canonical `.so` md5 reported unchanged.

## PRE-REGISTERED THRESHOLDS (pass/fail, fixed before any number)

### HEADLINE 1 — the BUILD (fixed scene A, build phase ticks 1..T1)

- **H1a MONOTONE:** accumulating `E(t)` is non-increasing across the build phase
  within numerical slack — `E(t+1) ≤ E(t) + 0.02` for every build tick. PASS iff
  0 violations.
- **H1b ASYMPTOTE:** accumulating `E(T1) < 0.12`. (analytic `0.85^20 = 0.039`)
- **H1c BUILD DROP:** `E(T1) / E(1) < 0.25` (≥ 4× reduction, gist → reconstruction).
- **H1d STATELESS FLAT:** stateless `E(t)` has `std(E) < 0.02` across build ticks
  AND `mean(E) > 0.5` (no build).
- **H1e ACCUMULATION GAP:** accumulating `E(T1) < 0.3 · mean(stateless E)`.

### HEADLINE 2 — the COST-BEND (same run)

- **H2a COST DROP:** accumulating `C(T1) ≤ 0.10 · C(1)` (compute drains ≥ 90% as
  the scene grounds).
- **H2b STATELESS COST FLAT:** stateless `C(t)` stays high and flat —
  `mean(C_stateless) ≥ 0.5 · N_lit` and `std(C_stateless) < 0.10 · mean` across
  build ticks.
- **H2c PERTURB RE-RAISE:** `C(T1+1) ≥ 3 · plateau` where `plateau = mean C over
  the last 3 build ticks`, AND `C(T1+1) ≥ 0.5 · N_perturbed` (surprise returns,
  localized to the changed patch). (If `plateau = 0` the binding clause is the
  second.)
- **H2d CORRELATION:** over the build phase, `Pearson(E(t), C(t)) > 0.6`
  (reconstruction-error-drop and compute-drop track each other). Spearman also
  reported.

### HEADLINE 3 — the build IMPLICITLY shows the FOVEA (post-perturb window)

- **H3a LOCALIZATION:** in the window `[T1+1, T1+4]`, the set of cells that fired
  ≥ 1 onset (explicit spent-looks) overlaps the perturbed patch with
  `IoU(explicit_onset_cells, perturbed_patch) ≥ 0.5`.
- **H3b IMPLICIT≡EXPLICIT:** `IoU(explicit_onset_cells, implicit_top_cells) ≥
  0.5`, where `implicit_top_cells` = the `N_perturbed` cells with the largest
  post-perturb `|Δ adaptation|` in the window.
- **DIVERGENCE is reported, not hidden.** If H3a/H3b miss, the divergence is a
  legitimate diagnostic finding (this is a PREDICTION, not a given). Additionally
  reported (no pass/fail): during the uniform BUILD phase the explicit onset
  allocation is dB-ratio-invariant (roughly uniform among lit cells) while the
  implicit error-drop is magnitude-weighted (bright-cell-heavy) — an expected,
  honest partial divergence.

## Discipline commitments

- SEPARATE prereg commit (this file ALONE) BEFORE any number.
- NEW FILES ONLY / §9 byte-identity: `git diff --stat` shows only new files; all
  existing vision gates stay green (Rung-5/5b/5c/k0 included).
- Oracle `bash scripts/rung7_vision_bench.sh` = 0 failed, BEFORE == AFTER.
- Provenance (§10): `source_match ∈ {own, shared}`, never a pinned hash. No Rust
  built (goal): canonical `.so` md5 `417f667716d71ed7d98bae5df25fe9df` reported
  unchanged BEFORE and AFTER.
- NO TIMING CLAIM; the cost-bend is WORK UNITS (onset-event counts) only.
- Gate `tests/test_splat_over_time_migrated.py` pins the build-curve drop, the
  accumulating-vs-stateless gap, the cost drop, and the perturb re-raise at the
  mechanism grain (reads measured values; able to fail on a true flat curve).
- Splat render sequence saved under `results/splat_over_time/`.
