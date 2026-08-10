# VISION — THE PER-AREA DIRTY-INDEX: make per-tick cost O(SURPRISE), not O(cells) (pre-registration)

**Block 185000.** Written and committed ALONE, BEFORE any measurement of the
mechanism. Seed claim `python3 scripts/seed_claim.py 185000 185999` → CLEAN.
Base: `main` @ `5ae765165a` (the 184000 ACCELERATION).

## What 184000 left standing

184000 vectorized the uniform retina sheet — cells exponent 1.838 → **1.072**,
109× @4800, 335× @19200, **30.5 fps @160×120** — and named its own residual: an
**O(cells) FLOOR**. `retina_onset_batch` touches EVERY cell EVERY tick, whether
or not anything about that cell changed. On an adapted scene most cells are
silent (179000 measured onset counts draining 300→0; 181000 measured a Doom
static plateau of 0 onsets spiking to exactly the 16 changed cells), so the sheet
is paying full price for a mostly-settled world.

This rung tests the named next lever: process only the CHANGED cells — a
**per-area DIRTY-INDEX** — so per-tick cost tracks SURPRISE, not resolution.

## THE CENTRAL DESIGN TENSION — and the analysis that decides the branch

"Skip unchanged cells" is **NOT trivially byte-identical.** The per-receptor
adapting floor is an EMA, `next = a + rate·(caught − a)`. Even with a FROZEN
input the floor keeps moving toward `caught`, so a naively-skipped cell takes a
DIFFERENT trajectory — a silent correctness bug of exactly the kind the
byte-identity gate exists to catch.

### PRE-REGISTRATION INPUTS (arithmetic + committed-fixture properties, NOT measurements of the mechanism)

Two facts were established BEFORE this prereg because the mission requires the
branch decision up front. Neither is a measurement of the mechanism under test.

**(i) The float64 EMA DOES reach an EXACT fixed point, in finite ticks.** For a
bit-repeatable input, `d_t = caught − a_t` shrinks by `(1−rate)` per tick and
`fl(a + rate·d)` **rounds to `a` exactly** once `rate·|d| < ulp(a)/2`. Solving
`(1−rate)^t < 2⁻⁵³/rate` gives, at `rate = 0.4` (this tree's `ADAPT_RATE`),
**t\* ≈ 71 ticks, essentially independent of magnitude** (verified by direct
float iteration at `caught ∈ {0.15, 7.62, 77.0, 246.0}` — the fixture's dark
current and luma range: 71, 72, 71, 72 ticks). After t\* the update is a
**genuine no-op** and skipping is PROVABLY bit-identical. So **Branch A exists.**

**(ii) But the committed Doom fixture has NO exactly-repeatable input under the
photon sensor.** `frames_160x120.npz` luma ∈ [7.62, 246.34] — **zero cells with
luma 0** — and `doom_photon_world.photon_packets(luma, rng)` draws a **Poisson**
count per cell per tick (photon shot noise, physically correct). So under the
shot-noise sensor **every cell's input changes every tick** and the exact
predicate can essentially never fire. Under the codebase's OTHER, already-
existing sensor mode — `photon_packets(luma)` with `rng=None`, the noiseless
"read the true field" mode — a held frame IS bit-repeatable and Branch A applies
in full.

**Calibration (declared).** The 184000 accel tick at 19200 cells decomposes
roughly as: world packet generation ~9 ms, adapter packet grouping ~4 ms,
payload build + id marshalling + FFI + Rust ~18 ms (≈32 ms total, reproducing
184000's 32.82 ms). All three are O(cells) and all three must fall for an
O(surprise) claim; a residual O(cells) memory-bandwidth change-detect (numpy,
~50 µs) and optional per-rod epoch stamp are the only permitted leftovers.

### Consequence — WE MEASURE BOTH BRANCHES, and label them honestly

- **BRANCH A — EXACT dirty predicate.** A cell is skipped ONLY when processing it
  would be BIT-IDENTICAL to skipping it. The predicate is checked in Rust on the
  last processed tick and is the conjunction of four BITWISE equalities plus a
  no-mint condition:
  `bits(next_adapt)==bits(adaptation_in)` ∧ `bits(caught)==bits(caught_quanta_prev)`
  ∧ `bits(response)==bits(activation_prev)` ∧ `¬(onset_db > threshold_db)`,
  AND the sensor reports the cell's input unchanged. (The `response==activation`
  clause is what makes `prev_activation` safe: after that tick
  `prev_activation == activation`, which is exactly what a further processed tick
  would write.) **Byte-identity is then PROVABLE, and the speedup is free.**
- **BRANCH B — BOUNDED SHEDDING.** Skip cells whose input moved by ≤ δ photon
  counts from the last PROCESSED input (a dead-band / send-on-delta; the residual
  is CARRIED, not lost — the comparison is always against the last processed
  value, so a slow drift eventually exceeds δ and fires). This is **a SEMANTIC
  OPTION, DEFAULT OFF, and NO byte-identity is claimed for it.** It is measured
  as a speed↔fidelity CURVE.

`δ = 0` ⟹ Branch A exactly. The two branches are one mechanism at two settings;
they are reported separately and never conflated.

## Architecture (what gets built)

- **Rust** — `retina_onset_batch` (`runners/dsl/src/cognitive_tasks.rs`) EXTENDED
  with optional arguments; the 184000 call shape keeps 184000 behaviour
  byte-unchanged. New: the arrays passed are the WORK LIST (dirty cells only),
  an optional `cell_idx` maps work items back to flat cell indices, the function
  computes the exact-settled predicate per processed cell and RETURNS the
  work-list indices that are NOT settled, and an optional `stamp_rod_ids` writes
  `input_epoch` on every rod (the one attribute a skip would otherwise leave
  stale). **NO new Term enum variant** — a batch graph op + PyO3 entrypoint only,
  exactly as 184000.
- **Adapter** — `GraphEye.submit_photons_2d(packets, dirty=None)`
  (`domains/photon_eye.py`), `context['retina_dirty']`. `dirty` is the SENSOR'S
  OWN change report (a list of flat cell indices whose input may have changed);
  `dirty=None` is the full sweep (byte-unchanged 184000/graph behaviour). Absence
  of a packet for a cell INSIDE the dirty set still means DARK — the two
  semantics are never conflated. The eye's per-tick WORK LIST is
  `reported_dirty ∪ not_yet_settled` (the latter returned by the previous Rust
  call), and it retains the last submitted input per cell so an unsettled,
  unreported cell is re-presented with the SAME input a full sweep would give it.
  Pure mechanical I/O; no decision.
- **The dirty set is the eye's own state** (the settled set) unioned with the
  sensor's change report — the seed of the per-area async settlement direction.
- **Droppable:** `retina_dirty` OFF → 184000 full-sweep accel → `retina_accel`
  OFF → graph path. All three must agree in Branch A.

## Criteria (thresholds fixed NOW)

### C0 — the branch decision, measured
- **C0a** exactly-skippable fraction on a HELD frame, NOISELESS sensor, 19200
  cells: **< 1% before tick 65**, **≥ 90% by tick 90** (predicted transition at
  t\* ≈ 71–73).
- **C0b** exactly-skippable fraction under the **Poisson shot-noise** sensor on
  the SAME held frame: **< 1% at every tick** (prediction: ≈ 0). A photon-counting
  sensor's input is never bit-identical; "unchanged" is not a property of the
  input.

### C1 — BRANCH A CORRECTNESS: byte-identity (the primary gate)
- **C1a** dirty-ON (δ=0) ≡ dirty-OFF (=184000 accel) at 300 / 1200 / 4800 / 19200
  on: VisionPolygons, the onset-event stream, `union_iou` / `carve_precision`,
  and the FULL-PRECISION per-cell rod state vectors **`adaptation`, `activation`,
  `prev_activation`, `caught_quanta`** — under BOTH sensors (noiseless long-hold
  protocol, where skipping actually fires; and the standard Poisson protocol).
- **C1b** three-way droppability: dirty-ON ≡ accel-ON/dirty-OFF ≡ GRAPH path
  (`retina_accel=False`) at ≤ 4800.
- **C1c** the LANDED 160×120 Doom carve (182000 protocol, seed 182000) under
  dirty-ON reproduces **4 polygons / union_iou 0.1215 / precision 0.9784 /
  false_poly_rate 0.0** EXACTLY.
- **C1d NON-VACUITY** — the identity must not be achieved by never skipping: on
  the 120-tick noiseless hold at 19200, the **skipped fraction on the final tick
  ≥ 90%**, and a deliberately WRONG skip predicate (skip a settled cell one tick
  EARLY, i.e. before its bitwise no-op holds) must **BREAK** C1a.
- **C1e DECLARED, MEASURED DIVERGENCE** — a skipped rod's `input_epoch` is the
  ONE attribute that lags a full sweep. Reported explicitly, with (i) proof that
  nothing observable reads it on the accel path (C1a covers every other rod attr
  and every output), and (ii) `stamp_epoch=True` restoring it EXACTLY, with its
  measured cost. No claim is made that a stale `input_epoch` "doesn't count".

### C2 — O(SURPRISE): cost tracks dirty count, not total cells
- **C2a** at 19200 cells on a SETTLED noiseless scene, per-tick vs perturbed-cell
  count k ∈ {0, 1, 16, 64, 256, 1024, 4096, 19200}: an affine fit
  `t = c₀ + c₁·k` with **R² ≥ 0.95**, and **cost(k=16) ≤ 5% of cost(k=19200)**.
- **C2b** at a FIXED dirty count of 16, per-tick vs TOTAL cells (300 / 1200 /
  4800 / 19200): fitted log-log **exponent ≤ 0.35** (≈ flat), against 184000's
  **1.072**.
- **C2c DRAIN** — per-tick cost over a 120-tick noiseless hold at 19200 falls by
  **≥ 10×** between tick 3 and tick 120, and the settled fraction reaches ≥ 90%.

### C3 — the floor is broken (facts, reported against 184000)
Adapted-scene per-tick + fps at **160×120** (vs 184000's 32.82 ms / 30.5 fps) and
at **240×180** (43200 cells, a resolution 184000 never reached in its sweep).
Gate: **≥ 10× per-tick improvement at 19200** on the fully-settled hold. What
"real-time" now means for the sheet is stated honestly, including what the WHOLE
eye (carve / motion / salience settle) still costs.

### C4 — FALSIFIER: no free lunch when everything is genuinely surprising
A scene where EVERY cell changes EVERY tick (a fresh uniform-random frame per
tick under the noiseless sensor; and the Poisson sensor on a held frame) must
cost **≈ the 184000 full sweep**: dirty-ON per-tick ∈ **[0.80×, 1.25×]** of
dirty-OFF. **If dirty-ON is < 0.80× on full-field change, the index is wrongly
skipping work and the rung FAILS.**

### C5 — BRANCH B: the shedding curve (semantic option, DEFAULT OFF)
δ ∈ {0, 1, 2, 4, 8, 16, 32} photon counts, real Poisson Doom carve protocol
@160×120. Reported: skip fraction, per-tick, fps, onset-stream size + set-diff vs
the δ=0 exact arm, n_polygons, union_iou, carve_precision, false_poly_rate, and
max/mean |Δadaptation|. **Pass/fail is ONLY on:** (i) δ=0 is byte-identical to
the exact arm, (ii) the default is OFF, (iii) the divergence is MEASURED and
reported as a curve, never as a byte-identity claim. The δ at which the landed
carve output first changes is reported as the headline fidelity fact.

## Discipline

- Prereg committed ALONE before any number. `source_match ∈ {own, shared}`
  reported. Seed block **185000–185999** only.
- Oracle `bash scripts/rung7_vision_bench.sh`: **0 failed, BEFORE == AFTER**
  (both sides reported, with the worktree's data condition stated).
- Gate `tests/test_dirty_index_migrated.py` pins (a) Branch A byte-identity
  across dirty-ON / dirty-OFF / graph + the wrong-predicate falsifier,
  (b) cost tracks dirty count not total cells, (c) the full-field-change
  falsifier, (d) Branch B defaults OFF and its divergence is bounded/reported.
  Self-contained committed fixture (`tests/fixtures/doom_carve_scale/`).
- **This rung BUILDS Rust** → the canonical `.so` md5 is verified UNCHANGED and
  **CANONICAL NEEDS REBUILD ON MERGE** is stated loudly.
- Timing measured SOLO, multiple trials, median + spread. Curves saved under
  `results/dirty_index/`.

## What would make this rung a FAILURE

- Branch B smuggled in under a byte-identity claim, or ON by default.
- C4 breached low (a "speedup" on full-field change = wrongly skipped work).
- C1d vacuous (identity achieved by never skipping).
- A skip predicate that changes any rod state vector or the carve output at δ=0.
