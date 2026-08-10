# RESULTS — the Doom real-time rung (seed block 201000-201999)

**Prereg:** `VISION_DOOM_REALTIME_CEILING_PREREG.md` (committed alone at `992d022f5d`).
**Base:** `0f2eb74a41` (LEDGER 200000). **Seed used:** 201000.
**Engine:** `04c9d28e316d` (`source_match: shared` — shared build, Rust source
identical, NO Rust change); canonical `.so`
md5 `793ce09ed498a749abb79aeaea44b92e` — **UNTOUCHED** BEFORE==AFTER (pure
measurement + spec: no Rust, no Term, no seed edit, no eye code change;
`git diff runners/dsl/src/term.rs` EMPTY).
**Runner:** `scripts/doom_realtime_ceiling_measure.py` (import-inert) over the
SHIPPED photon-eye `_tick` (`doom_carve_scale_measure._tick`: submit_photons_2d →
run_cognitive_tasks(1) → run_rules() → prune_settled_tasks). Feed = **real
VizDoom frames** (`defend_the_line`, still camera + moving DoomImp/Demon, seed
201000). SOLO, median + spread over 12 per-tick reps (distinct real frames).
Raw: `results/doom_realtime_ceiling.json`, `results/foveated_layout_spec.json`.

---

## PART A — the uniform real-time ceiling (measured, solo)

Two paths of the shipped eye: the **graph** path (correctness oracle, the full
run_cognitive_tasks + run_rules fixpoint — where the 195000 linearisation lives)
and the **184000 accelerator** (`retina_accel`, the vectorized byte-identical
mirror — the shipped real-time fast path: transduce settled in one FFI crossing,
no CognitiveTask nodes).

### End-to-end ms/frame vs uniform cells (median [min–max])

| cells | grid | GRAPH ms | ACCEL ms | cand_enum/tick (graph) | cand_enum/tick (accel) |
|------:|------|---------:|---------:|-----------------------:|-----------------------:|
|   300 | 20×15  |   3.93 [3.90–4.07]   |  0.515 [0.51–0.61] |   7,504 |  1,501 |
|   588 | 28×21  |   7.91 [7.84–8.96]   |  0.995 [0.98–1.08] |  14,704 |  2,941 |
| 1,200 | 40×30  |  17.94 [17.38–19.11] |  2.048 [2.01–2.20] |  30,004 |  6,001 |
| 2,352 | 56×42  |  41.34 [38.65–44.99] |  4.044 [3.90–4.53] |  61,156 | 11,761 |
| 4,800 | 80×60  | 102.63 [97.92–109.68]|  8.407 [8.00–9.37] | 124,804 | 24,001 |
| 9,605 | 113×85 | 285.79 [277.73–290.80]| 18.038 [17.75–19.26]| 278,544 | 48,026 |
|19,200 | 160×120| 881.17 [845.47–893.94]| 41.671 [40.67–43.14]| 556,799 | 96,001 |

Liveness held at every point (cand_enum > 0 and scaling; onset events fired —
591…37,817 over the eye's life).

### G1 — LINEARITY AT SCALE (the real gate) — **PASS**, with the honest decomposition

Log-log exponents over the 64× cell span (300→19,200):

| quantity | GRAPH exponent (r²) | ACCEL exponent (r²) |
|---|---|---|
| **work-count `cand_enum`** | **1.040** (0.9996) | **1.000** (1.000) |
| **work-count `term_evals_total`** | **1.036** (0.9997) | **1.000** (1.000) |
| wall ms/frame | 1.294 (0.9945) | 1.048 (0.9989) |

**The deterministic run_rules work-count is essentially EXACTLY LINEAR (1.04 /
1.00) — 195000's scheduler linearisation HOLDS at the scales that matter**
(pre-195000 run_rules was ~2.0). The gate (exponent ≤ ~1.3) passes on every
counter, and on the wall too (1.294 graph, 1.048 accel).

**The wall/work-count exponent gap (graph 1.29 vs counter 1.04) is NOT run_rules
— it is located, per the prereg's incomplete-counter cross-check.** The per-tick
decomposition (submit / fixpoint / prune, ms at 300 → 19,200 cells):

- `run_rules` **fixpoint**: 1.28 → 146.3 ms → exponent **≈1.14** (agrees with the
  counter's 1.04 — the fixpoint is linear);
- `submit_photons_2d` (Python per-cell CognitiveTask ingest, O(cells)): 2.10 →
  262.2 ms → exponent **≈1.16**;
- `prune_settled_tasks` (Python graph housekeeping): 0.59 → **479.4 ms** →
  exponent **≈1.6**, and it becomes the DOMINANT term at high resolution
  (479 of 881 ms at 19,200).

So the graph wall's mild super-linearity is a **super-linear (~1.6) residual in
`prune_settled_tasks`**, a Python-side settled-task cleanup — **not** the
run_rules fixpoint. The **184000 accelerator removes it entirely** (prune ≈ 0 ms,
no CognitiveTask nodes), and the accel wall collapses to **1.05**, matching its
work-count 1.00. Named finding, reported straight: the perception fixpoint is
linear; the only super-linear term is graph housekeeping that the shipped fast
path already bypasses.

### G2 — THE CEILING (uniform cells at budget)

Ceiling = the cell count at the budget, by log-log piecewise interpolation on the
measured medians (and, for cross-check, the power-law fit):

| path | @ 28.5 ms (35 fps) | @ 33 ms (30 fps) | vs ~700 pre-195000 |
|---|---:|---:|---|
| **GRAPH** (oracle, full run_rules + Python housekeeping) | **~1,743 cells** (powerfit 1,592) | **~1,961 cells** (1,783) | **~2.8×** |
| **ACCEL** (184000, the SHIPPED real-time path) | **~14,023 cells** (powerfit 14,526) | **~15,830 cells** (16,706) | **~23×** |

The headline: on the **shipped accelerated eye the uniform real-time ceiling is
~14,000–16,000 receptors** — close to the **full 160×120 = 19,200** Doom-native
grid (19,200 cells run at 41.7 ms = ~24 fps; ~15,800 cells fit the 33 ms / 30 fps
budget). The graph oracle sits at ~1,700–1,960. **Both are well above the
pre-195000 ~700**; the linearisation + accelerator together bought ~2.8× (graph)
to ~23× (accel).

### Secondary — held-scene uplift (compute ∝ surprise, 185000 dirty path)

Changing (full change-report) vs a held/static scene, per grid:

- **Byte-identical dirty path (branch A):** uplift **~1.02–1.08×**, **0 cells
  skipped** at every grid. The onset/carve fixpoint keeps cells *unsettled*, so
  nothing is bitwise-skippable — **compute ∝ surprise does NOT materialise on the
  byte-identical path** for a held Doom scene. Honest null.
- **Shed branch (B, `retina_dirty_shed` — declared NOT byte-identical):** uplift
  **~1.69–2.0×**, all cells skipped on the held frame (it sheds the unsettled
  residual of unreported cells). The uplift is *real but only realised by the
  non-identical shed variant* — so on the conservative shipped eye the every-frame
  uniform ceiling above IS the honest ceiling; the ~2× held uplift is available
  only if one accepts the shed branch's residual-shedding.

---

## PART B — the foveated layout (G3): eye is uniform-only → SPEC + SIMULATION

**Does the eye admit non-uniform receptor layouts? NO** (source-verified).
`photon_eye.py::_build_2d_retina` mints receptors on a strictly uniform az×el
lattice (nested `for row in range(n_el): for col in range(n_az)`, evenly-spaced
az/el, no per-receptor position table); `submit_photons_2d` indexes cells by
`flat = row*n_az + col` with a uniform-grid bounds check. So a live foveated eye
is not buildable without an eye change. Part B is therefore an honest
**compute-model + simulation** (`scripts/foveated_layout_spec.py`,
`results/foveated_layout_spec.json`), faking no live foveated eye.

**Model:** a dense **1:1 foveal patch** (one receptor per Doom pixel — no
sub-pixel detail to recover) at the screen centre (the aim point where Doom
enemies render) + a **log-polar periphery** (isotropic: constant angular
samples/ring, rings geometric in eccentricity, density ~1/ecc) covering the full
frame to the 200 px corner radius, the whole sized to the Part-A budget.

| budget (receptors) | uniform | foveated | central acuity gain | frame at 1:1 |
|---|---|---|---:|---|
| 1,743 (graph @28.5ms) | 48×36, 6.67 px/cell everywhere | 30×30 1:1 fovea + 42×19 log-polar = 1,698 | **6.67×** | 0.012 |
| 1,961 (graph @33ms) | 51×38, 6.28 px/cell | 34×34 1:1 fovea + 42×19 = 1,954 | **6.28×** | 0.016 |
| 14,023 (accel @28.5ms) | 137×102, 2.34 px/cell | 114×114 1:1 fovea + periphery = 13,794 | **2.34×** | 0.226 |
| 15,830 (accel @33ms) | 145×109, 2.21 px/cell | 122×122 1:1 fovea + periphery = 15,682 | **2.21×** | 0.259 |

**The foveation payoff (equal receptor count, equal real-time cost, full-frame
coverage preserved):** the central aim region is resolved at **Doom-native 1:1**
while the equal-count uniform grid blurs it to the uniform px/cell. The gain
EQUALS the uniform px/cell by construction, so it is **largest at the tight graph
budget (~6.3–6.7×** — lifting the sub-grid enemy wall the 152000/153000 probes
hit: a ~30 px enemy is ~4.5–4.8 uniform cells vs full 30 at the fovea) and
**modest at the accel budget (~2.2–2.3×**, because uniform there already nearly
resolves Doom at ~2.2 px/cell). Foveation's marginal value shrinks as the budget
approaches the scene's pixel count — reported straight.

**The named build gap (exactly what a live foveated eye needs):**
1. a per-receptor `(az, el)` position TABLE replacing the uniform nested loop in
   `_build_2d_retina` (fovea 1:1 + log-polar spokes/rings as explicit positions);
2. a matching SCATTER in `submit_photons_2d` (pixel→nearest-receptor assignment
   instead of `flat = row*n_az + col`);
3. explicit neighbour adjacency on the non-uniform sheet for the common-fate
   carve neighbourhood.
**No new DSL Term expected** — this is receptor construction + a scatter
(world-adapter / seed-builder work); the onset/carve Terms are position-agnostic.

---

## GATES SUMMARY

- **G1 (linearity):** PASS. Work-count exponents 1.04 (graph) / 1.00 (accel) —
  run_rules linear, 195000 confirmed. Wall 1.29 (graph) / 1.05 (accel); the graph
  wall's excess over 1.04 is a ~1.6 residual in `prune_settled_tasks` (Python
  housekeeping, not run_rules), which the accelerator removes.
- **G2 (ceiling):** ~1,743/1,961 uniform cells @ 28.5/33 ms on the graph oracle;
  **~14,023/15,830 on the shipped accelerator** — ~2.8× to ~23× the pre-195000
  ~700, near the full 19,200 Doom-native grid.
- **G3 (foveated):** eye is uniform-only → SPEC+SIMULATION delivered; central
  acuity gain ~6.3–6.7× (graph budget) / ~2.2–2.3× (accel budget) at equal count
  and cost; build gap named. (Simulation, not a live build, per the honest boundary.)
- **G4 (byte-identity):** pure measurement + spec, no eye change; `term.rs`
  empty; `.so` md5 `793ce09e…` untouched BEFORE==AFTER. Trivially holds.

## GATE / REGRESSION RESULTS

- **Eye suite + engine-semantics gate set:** `99 passed, 0 failed`
  (`test_doom_carve_scale`, `test_photon_grapheye`, `test_doom_held_prediction`,
  `test_held_surface`, `test_incremental_match`, `test_empty_match_proof`,
  `test_per_sensor_epoch`, `test_per_area_settlement`, `test_eye_binding_projection`,
  `test_staleness_decay`, `test_demotion_hierarchy`, `test_dissipation_inference`
  — all `_migrated`). No engine change, so this confirms no regression.
- **Oracle `bash scripts/rung7_vision_bench.sh`:** `214 passed, 10 skipped, 0
  failed` (the data-less baseline `214/10/0`; `data/` not symlinked in this
  worktree). BEFORE==AFTER by construction — no existing file, seed, or engine
  touched; only new measurement scripts + prereg/results/JSON added.
- **`source_match`: shared** (engine `04c9d28e316d`, Rust source identical, no
  Rust change). **`term.rs` diff EMPTY. Canonical `.so` md5 `793ce09e…`
  unchanged.**
- **Seed:** block 201000–201999 claimed CLEAN at prereg; seed 201000 the single
  measured draw. VISION_PROTOCOL.md untouched; not merged to main.
