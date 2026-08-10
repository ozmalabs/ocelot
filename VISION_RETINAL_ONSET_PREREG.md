# ASYNC VISUAL ONSET EVENTS — PRE-REGISTRATION

**Written and committed BEFORE any confirmatory number.** Vision is brought onto
the same event-native, asynchronous footing audition already has: the cochlear
nucleus (`runners/dsl/src/cochlear_nucleus.rs::detect_onsets`) fires a discrete
`OnsetEvent` when a per-band envelope rises `threshold_db` above an
asymmetrically-adapting local floor, with a refractory. This rung builds the
one-to-one visual analog: a discrete **`RetinalOnsetEvent`** per column, fired
when the rod receptor's transduced drive departs its OWN adapting floor.

- **branch (as observed):** `gamma-substrate/retinal-onset` (isolated worktree
  `.claude/worktrees/agent-retinal-onset`).
- **base SHA (as observed):** `5e6ae1c7b2af15d7f0aa22e4d5c332f24c904372` (main).
- **engine:** `own` build via `scripts/engine_build.sh` in THIS worktree.
  Provenance gate as its own step: `tests/test_engine_provenance_migrated.py`
  **7 passed** (recorded before any measurement).
- **oracle baseline:** `bash scripts/rung7_vision_bench.sh` → recorded in
  RESULTS both sides (before with the flag off, after). `data/` symlinked
  (§10.2, with-corpus case).
- **seeds:** 135000–135999.

## §0 — `check_claim`, VERBATIM (§3 clause 8)

```
SEED CLAIM 135000-135999: CLEAN -- no collision DETECTED.
  Scope: 860 files with seed sinks; 582 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

The 582 unresolved sinks are PRICED, not waved past. This rung draws its RNG
ONCE at `default_rng(135000)` (photon shot-noise on the stimulus); every drawn
seed is a direct element of the declared block.

## §1 — THE MECHANISM

The atom already exists: `cognitive_tasks.rs::execute_kernel` `photon_transduce`
computes a Naka-Rushton `response = caught/(caught+half+adaptation)` and carries
per-receptor light adaptation across frames:
`next_adaptation = adaptation + adapt_rate*(caught - adaptation)`. The receptor's
`adaptation` is its OWN async history — the visual analog of the auditory
adapting floor; `caught` is the instantaneous drive (the analog of the
envelope).

**Rust (the DECISION primitive):** a new task kind `photon_transduce_onset`, a
byte-identical PEER of `photon_transduce` in its first three outputs (so the
shared `photon_apply_receptor_transduction` rule folds it unchanged), that
appends a FOURTH output:

```
onset_db = 20 * log10( (caught + 1e-10) / (adaptation + 1e-10) )
```

This is the exact analog of `detect_onsets`' "dB above the local floor" line
(eps = 1e-10, 20·log10 of the ratio). The floor is the receptor's held
`adaptation` (the value BEFORE this observation updated it).

**Graph (the mint):** seed `seeds/retinal_onset.json`, rule `retinal_mint_onset`
(area retina, order 2). For a column whose rod's fresh onset-task reports
`output[3] > threshold_db` AND the refractory is satisfied
(`rod.input_epoch − column.last_onset_epoch > refractory_epochs`), it MINTS a
`RetinalOnsetEvent{column_index, magnitude_db, epoch, logical_time}` — carrying
the receptor's OWN `input_epoch` (its own clock, NOT a shared frame index) — and
advances `column.last_onset_epoch`. A per-task `onset_seen` guard makes it fire
at most once per task (one transient → one event).

**Default OFF / byte-identity (§9):** the onset path is additive. The retina
emits `photon_transduce_onset` and loads `retinal_onset.json` ONLY when the world
sets `context["visual_onset"]`; the mint rule cannot even match without a
`RetinaOnsetParams` node the adapter creates in that mode. With the flag off the
plain `photon_transduce` kind and the whole existing retina are byte-unchanged.
Proven by the oracle (222/0 before and after, flag off) plus the Rust unit test
that the first three outputs of the two kernels are byte-identical.

## §2 — THE CONFIRMATORY CONFIG (fixed here, before any number)

One synthetic retina, `n_az = 16` rod columns, threshold_db = 6.0, refractory =
0 epochs, `adapt_rate = 0.12` (ON) / `0.0` (OFF). Drive: a bright column =
Poisson(2000) photons @ 500 nm (rods, centre 498 nm); dark = 0. RNG
`default_rng(135000)`. Driven synchronously: `submit → run_cognitive_tasks(1) →
run_rules()` per frame. Every scene is preceded by **8 dark warm-up frames** so
each column's floor adapts to the dark baseline before measurement (the
cold-start `adaptation = 0` fires on the first observation by construction — a
warm-up, exactly as `detect_onsets` initialises its floor to `envelope[0]`).

- **MOVING:** 16 sweep frames; frame *t* lights column *t* only. Count all
  `RetinalOnsetEvent`s minted during the sweep = `moving_count`.
- **STATIC (adapt ON):** all 16 columns bright, held 16 frames; count events in
  the **last 8** frames = `static_adapted_count`.
- **OFF CONTROL (adapt_rate = 0):** the SAME static bright scene, held 16
  frames; count events in the last 8 = `off_count`.

## §3 — THE HEADLINE QUANTITY + INTERVAL (design-derived, able-to-fail)

Headline: the moving : static-adapted contrast

```
R = moving_count / (static_adapted_count + 1)
```

**Design prediction.** Post-warm-up, each column's floor sits at the dark
baseline. In MOVING, the arriving bar drives `caught` ≈ 2000 against a floor ≈
0.15 → `onset_db` ≈ 82 dB ≫ 6 → the column fires exactly once as the bar
arrives; a column going dark again departs NEGATIVE and stays silent. So
`moving_count` ≈ N = 16 (one per column). In STATIC (adapt ON), the floor rises
to the drive within ~6 frames (`onset_db → 0`), so the last 8 frames are SILENT:
`static_adapted_count` ≈ 0. Hence R ≈ 16/1 = 16.

**PRE-REGISTERED INTERVAL: `R ∈ [6, 40]`.** Able to fail LOW if the bar fails to
fire per column, or if the adapted scene does NOT go silent (both tank the
ratio); able to fail HIGH if the moving path over-fires beyond design (> 40).

## §4 — THE COMPUTE-∝-SURPRISE GATE (able-to-fail, with the required OFF control)

Three conditions, each a MEASURED count (never a re-derived constant):

1. **MOVING FIRES + LOCALISES:** `moving_count ≥ 12`, and every minted event's
   `column_index` equals the bright column at that event's epoch.
2. **STATIC-ADAPTED FALLS SILENT:** `static_adapted_count ≤ 2`.
3. **ADAPTATION-OFF STAYS NOISY (the load-bearing control):** with the ONLY
   change being `adapt_rate = 0`, the SAME static bright scene must NOT go
   silent: `off_count ≥ 16` (≥ N). If the OFF control also fell silent, the
   silence in (2) would not be from adaptation and the gate would be
   meaningless. The frozen floor never rises, so the sustained bright drive
   departs it every frame.

## §5 — WHAT THIS RUNG DOES NOT DO

No motion, no carve, no depth. It mints the discrete onset substrate that later
rungs read. `detect_onsets`' asymmetric windowed floor is approximated here by
the receptor's existing symmetric `adapt_rate` low-pass (the atom the project
already ships); an asymmetric visual floor is a named successor, not built here.
