# VISION — THE PER-AREA DIRTY-INDEX: per-tick cost O(SURPRISE), not O(cells) (results)

**Block 185000.** Prereg: `VISION_DIRTY_INDEX_PREREG.md`, committed ALONE
(`055f094c45`) BEFORE any number from the mechanism. `source_match = "own"`.
**This rung BUILDS Rust** — the canonical `.so`
(`…/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so`, md5
`395637824bd541805abcff02ff42ef34`, mtime Jul 25 02:31) is **UNCHANGED**; the
build happened only in this worktree. **THE SUPERVISOR MUST REBUILD CANONICAL ON
MERGE (Rust changed).** Measured SOLO on the committed real `defend_the_line`
fixture (`tests/fixtures/doom_carve_scale/frames_160x120.npz`), VizDoom-free, via
`scripts/dirty_index_measure.py` → `results/dirty_index.json`.

## Headline

184000 linearized the sheet and named its own residual: an **O(cells) FLOOR** —
the batch touches every cell every tick. This rung processes only the CHANGED
cells. The result, in one line: **on the real Doom motion sequence at 160×120 the
adapted sheet runs at 584 fps (1.71 ms/tick) because only ~508 of 19 200 cells
(2.6%) are dirty — 21× the 184000 full sweep on the same machine, byte-identical.**

The rung's intellectual content is the CORRECTNESS argument, not the speed:

- **The float64 EMA reaches an EXACT fixed point.** `a + rate·(caught − a)` rounds
  back to `a` once `rate·|caught−a| < ulp(a)/2`. At `rate = 0.4` that is
  **t\* ≈ 71 ticks** of bit-repeatable input, essentially independent of
  magnitude. After t\* the update is a **genuine no-op**, so **BRANCH A exists**
  and skipping is *provably* byte-identical — measured firing at **tick 73**, and
  **never once before tick 65**.
- **But a photon-COUNTING sensor never repeats.** The committed fixture has no
  dark cells (luma ∈ [7.62, 246.34]) and `photon_packets` draws Poisson shot
  noise, so **under the default sensor the exact predicate fires 0.0% of the time
  at every tick** — measured, not assumed. "Unchanged" is not a property of the
  input; at the photon level everything always changes.
- Therefore **BRANCH B (bounded shedding)** was ALSO built and measured — as a
  **SEMANTIC OPTION, DEFAULT OFF, with NO byte-identity claim** and a full
  divergence curve. It is not a mirror and is never described as one.

## What was built

- **Rust** — `retina_onset_batch` (`runners/dsl/src/cognitive_tasks.rs`) EXTENDED
  with four optional arguments; omitting them is the byte-unchanged 184000 call.
  The arrays passed are now the **WORK LIST**; `cell_idx` maps work items to flat
  cells; `track_settled` evaluates the **exact skippability predicate** and
  returns the flat indices that are NOT settled; `stamp_rod_ids` stamps
  `input_epoch` across the sheet; `naive_skip` is the wrong-predicate falsifier.
  **NO new Term enum variant** (`term.rs` untouched) — a batch graph op + PyO3
  entrypoint, exactly as 184000.
- **The exact predicate** (all comparisons BITWISE, on `f64::to_bits`):
  `bits(next_adapt)==bits(adaptation_in)` ∧ `bits(caught)==bits(caught_quanta)` ∧
  `bits(response)==bits(activation)` ∧ `¬(onset_db > threshold_db)`. The third
  clause is what makes `prev_activation` safe (after such a tick
  `prev_activation == activation`, exactly what a further processed tick writes).
- **Adapter** — `GraphEye.submit_photons_2d(packets, dirty=None)`
  (`domains/photon_eye.py`), `context['retina_dirty']` (default **OFF**).
  `dirty` is the SENSOR'S OWN change report; `dirty=None` is the full sweep.
  Absence of a packet INSIDE the report still means DARK — the two semantics are
  never conflated. The eye's work list is **report ∪ its own not-yet-settled
  set**, and it retains each cell's last submitted input so an unsettled but
  unreported cell is re-presented with exactly the input a full sweep would give
  it. Pure mechanical I/O.
- **World** — `photon_counts` / `changed_cells` / `packets_from_counts`
  (`domains/doom_photon_world.py`): the vectorized, event-native form of the
  existing sensor. Building packets only for changed cells is what keeps the
  WORLD side O(surprise) too.
- **Droppable:** `retina_dirty` OFF → 184000 full-sweep accel → `retina_accel`
  OFF → graph/`run_rules` path. All three agree (below).

## C0 — the branch decision, MEASURED — PASS

| sensor | max skipped fraction | first tick > 50% | fraction before tick 65 | at tick 90 |
|---|---|---|---|---|
| noiseless (`rng=None`, held frame) | **1.000** | **73** | **0.000** | **1.000** |
| Poisson shot noise (default) | **0.000** | never | 0.000 | 0.000 |

The transition lands exactly where the float arithmetic says it must (predicted
t\* ≈ 71–73). **C0a** (<1% before tick 65, ≥90% by tick 90) ✅. **C0b** (<1%
under Poisson) ✅ — measured **exactly 0**.

## C1 — BRANCH A CORRECTNESS: byte-identity — PASS

Full carve protocol (80-tick hold past t\*, event flush, 13 real motion frames,
carve settle), noiseless sensor. ON = dirty-index; OFF = 184000 full-sweep accel;
GRAPH = `retina_accel=False` (the `run_rules` oracle, affordable ≤ 4800).

| grid | cells | polygons | onset stream | iou / precision | rod state (4 attrs) | `input_epoch` | 3-way vs graph | skipped, final tick |
|---|---|---|---|---|---|---|---|---|
| 20×15   | 300   | 0 == 0  | ✅ (1)   | ✅ 0.0 / 0.0        | ✅ | ✅ | ✅ | 90.0% |
| 40×30   | 1200  | 0 == 0  | ✅ (4)   | ✅ 0.0 / 0.0        | ✅ | ✅ | ✅ | 92.0% |
| 80×60   | 4800  | 2 == 2  | ✅ (41)  | ✅ 0.0433 / 0.9167  | ✅ | ✅ | ✅ | 92.9% |
| 160×120 | 19200 | 10 == 10| ✅ (304) | ✅ 0.1030 / 0.9914  | ✅ | ✅ | (too slow) | **93.5%** |

"rod state" = the FULL-PRECISION per-cell `adaptation`, `activation`,
`prev_activation`, `caught_quanta` vectors — the state that persists across
ticks. **C1a ✅, C1b ✅** (three-way droppable at 300/1200/4800).

**C1c — the LANDED 160×120 Doom carve reproduced EXACTLY under the dirty index.**
Re-running the 182000 protocol at seed 182000 with the VERBATIM Poisson photon
stream: **4 VisionPolygons, union_iou 0.1215, carve_precision 0.9784,
false_poly_rate 0.0** — identical to the landed 182000/183000/184000 headline,
and ON≡184000-accel on polygons + onset stream + rod state. **Skipped cell-ticks
under Poisson: 0 of 364 800** — the dirty index is SAFE BY CONSTRUCTION here: it
skips nothing because nothing is exactly skippable, and the numbers are the
landed ones. ✅

**C1d — NON-VACUITY, both directions.** (i) The identity is not bought by never
skipping: 90–93.5% of cells are skipped on the final tick of every grid. (ii) The
**naive** predicate — skip on "input unchanged" ALONE, ignoring the still-moving
EMA floor, i.e. exactly the bug the mission warned about — **BREAKS the
identity**: at 40×30 it skips 108 443 cell-ticks (vs the exact predicate's
24 816) and diverges on `adaptation`, `activation`, `prev_activation` AND the
onset stream. ✅

**C1e — `input_epoch`, the one attribute a skip would leave stale. DECLARED AND
MEASURED, not waved away.**

| mode | `input_epoch` identical | all other rod state | onset stream |
|---|---|---|---|
| `stamp_epoch=True` (used in every C1 row above) | **✅ identical** | ✅ | ✅ |
| `stamp_epoch=False` | ❌ **differs** (skipped rods lag) | ✅ identical | ✅ identical |

Stamping is pure bookkeeping (no kernel, no payload, no mint) and restores exact
whole-graph identity — but it is itself **O(cells)**, and that is the honest
residual floor (quantified in C2). With it off, the rod's `input_epoch` becomes
the rod's OWN per-sensor time, everything observable stays bit-identical, and the
cost becomes truly O(dirty). **Both arms are reported everywhere below.**

## C2 — O(SURPRISE): cost tracks the DIRTY COUNT — PASS (stamp-off), PASS-with-caveat (stamp-on)

**C2a — per-tick vs dirty count at a FIXED 19 200 cells** (median of 7; the
reported cells are re-presented so the work is real and the sheet stays settled):

| dirty cells k | 0 | 1 | 16 | 64 | 256 | 1024 | 4096 | 19200 |
|---|---|---|---|---|---|---|---|---|
| stamp ON (ms) | 0.419 | 0.440 | 0.461 | 0.564 | 0.920 | 2.424 | 7.825 | 31.646 |
| stamp OFF (ms)| **0.003** | 0.007 | **0.039** | 0.130 | 0.477 | 1.844 | 6.440 | 32.441 |

Affine fit `t = c₀ + c₁·k`: **R² = 0.9994 (stamp on) / 0.9997 (stamp off)** ≥ 0.95
✅. **cost(k=16)/cost(k=19200) = 0.0146 (on) / 0.0012 (off)** ≤ 0.05 ✅. The
intercept IS the stamp: **0.42 ms with it, 0.003 ms without**.
A REAL 4×4 perturbation (16 cells genuinely change, nothing else does) costs
**0.443 ms (stamp on) / 0.022 ms (stamp off)** — i.e. the cost tracks ~16 cells,
not 19 200.

**C2b — per-tick vs TOTAL cells at a FIXED dirty count of 16:**

| cells | dirty-16, stamp ON (ms) | dirty-16, stamp OFF (ms) | full work (ms) |
|---|---|---|---|
| 300   | 0.0277 | 0.0255 | 0.272 |
| 1200  | 0.0501 | 0.0235 | 1.255 |
| 4800  | 0.1230 | 0.0274 | 5.644 |
| 19200 | 0.4815 | 0.0365 | 32.782 |

Fitted log-log exponent at fixed dirty count: **0.089 with the stamp OFF**
(≤ 0.35 ✅ — essentially FLAT in resolution) and **0.683 with the stamp ON**
(**> 0.35, the prereg threshold FAILS in this arm** — and the cause is named
exactly: the O(cells) `input_epoch` stamp, nothing else). The full-work arm
reproduces 184000's linear behaviour (**1.116** vs 1.072). **Per-tick cost is
flat in RESOLUTION at fixed surprise; the only resolution-dependent term left is
the exactness bookkeeping.**

**C2c — THE DRAIN.** Per-tick cost over a 120-tick hold on a frozen scene
(160×120): **tick 3 → tick 120 falls 54× (stamp on) / 6353× (stamp off)** ≥ 10× ✅.
At 240×180: **24× / 13973×** ✅. The cliff is at tick 71–73, where the sheet's
EMAs reach their exact fixed point together.

## C3 — the floor is broken (facts, vs 184000)

| condition | 184000 full sweep (measured, same machine) | dirty index, stamp ON | dirty index, stamp OFF |
|---|---|---|---|
| 160×120, **real Doom motion** (~508/19200 dirty) | 36.07 ms — **27.7 fps** | **1.71 ms — 584 fps (21×)** | — |
| 160×120, frozen adapted scene | 31.37 ms — 31.9 fps | 0.480 ms — 2085 fps (65×) | 0.0035 ms — 287 000 fps |
| 240×180 (43 200 cells), frozen adapted | 84.64 ms — 11.8 fps | 2.33 ms — 429 fps (36×) | 0.0039 ms — 256 000 fps |

Against 184000's PUBLISHED 32.82 ms @19200: the real-motion number is **19×**.

**What "real-time" now means for the sheet, honestly.** 184000 delivered 30.5 fps
at 160×120 by paying for every cell. This rung delivers **584 fps at 160×120 on
the real motion sequence** and **429 fps at 240×180** on an adapted scene, by
paying only for what changed — the sheet is no longer the bottleneck at video
rate, and resolution is nearly free once the scene is grounded. The frozen-scene
numbers (2085 / 287 000 fps) are a DEGENERATE endpoint — a perfectly frozen input
has an EMPTY work list, so the "cost" is just the change-detect; they are
reported as the floor, not as the operating point. **The operating point is the
584 fps real-motion row.** And it remains the SHEET only: the common-fate
carve/motion/salience settle ops are unchanged and unmeasured here.

## C4 — FALSIFIER: no free lunch when everything is genuinely surprising — PASS

| scene | dirty index (ms) | 184000 full sweep (ms) | ratio |
|---|---|---|---|
| fresh uniform-random frame every tick (noiseless — every cell changes) | 41.47 | 37.72 | **1.099** |
| Poisson shot noise on a HELD frame (every count changes) | 40.49 | 35.00 | **1.157** |

Both inside the pre-registered **[0.80, 1.25]** ✅, and both **above 1.0** — the
index costs slightly MORE when nothing is skippable (it pays for the change
detect and the settled bookkeeping and skips nothing). **There is no free lunch:
the speedup is bought from surprise, and where there is no surplus surprise there
is no speedup.** The gate additionally asserts that ZERO cells are skipped in
this condition.

## C5 — BRANCH B: the shedding curve — SEMANTIC OPTION, DEFAULT OFF

Adapter defaults verified in-run: `retina_dirty=False`, `retina_dirty_shed=False`,
`retina_dirty_naive=False`. **NO byte-identity is claimed for any row below.**
Real Poisson Doom carve protocol @160×120, seed 182000 (the landed protocol);
divergence measured against the EXACT (Branch A) arm.

| δ (counts) | skipped | per-tick (ms) | polys | union_iou | precision | onset Δ | max \|Δadaptation\| |
|---|---|---|---|---|---|---|---|
| exact (A) | 0.000 | 39.0 | **4** | **0.1215** | **0.9784** | 0 | 0 |
| 0 (shed)  | 0.030 | 39.0 | 4 | 0.1215 | 0.9784 | 223 | 26.1 |
| 1  | 0.091 | 36.9 | 4 | 0.1314 | 0.9800 | 512 | 25.1 |
| 2  | 0.151 | 35.1 | 4 | 0.1314 | 0.9800 | 602 | 25.1 |
| 4  | 0.266 | 30.9 | 3 | 0.1150 | 0.9556 | 822 | 36.5 |
| 8  | 0.475 | 22.0 | **45** | 0.0504 | **0.2143** | 2110 | 51.3 |
| 16 | 0.765 | 9.29 | **168** | **0.0** | **0.0** | 5771 | 63.0 |
| 32 | 0.932 | 1.87 | 15 | 0.0201 | 0.2353 | 2228 | 83.5 |

**Findings, stated as they are.**
1. **Shedding is NOT byte-identical at ANY δ, including δ = 0** — the polygon
   internals already differ at δ=0 (`first_delta_changing_landed_carve = 0`).
   That is the whole point of calling it Branch B: with shedding on, the eye
   stops carrying its own unsettled residual, so a still-moving floor freezes.
2. **The speed is real** (39 → 1.9 ms, 21×) **and so is the damage.** Fidelity
   survives to about δ ≈ 2 (4 polys, precision 0.98) and then COLLAPSES: at δ=8
   the carve mints **45** polygons at precision 0.21, at δ=16 **168** polygons and
   iou 0. The mechanism is legible: a shed cell's departure from its frozen floor
   ACCUMULATES, so when it is finally processed it fires a spurious onset —
   shedding manufactures surprise downstream. **The onset stream is exactly what
   the carve reads, so shedding trades sheet cost for false structure.**
3. Therefore, on this scene, **BRANCH B buys nothing worth having**: Branch A
   already gives 21× on real motion for free, and B's extra speed costs the
   carve. It stays DEFAULT OFF and is reported as a measured negative.

## Per-criterion table

| id | criterion | measured | pass |
|---|---|---|---|
| C0a | exact predicate <1% before tick 65, ≥90% by tick 90 (noiseless) | 0.000 / 1.000, first >50% at tick 73 | ✅ |
| C0b | exact predicate <1% under Poisson shot noise | **0.000 at every tick** | ✅ |
| C1a | dirty-ON ≡ 184000 accel: polygons + onsets + iou/precision + 4 rod state vectors, 300/1200/4800/19200 | identical (all) | ✅ |
| C1b | three-way ON ≡ accel ≡ graph path (≤4800) | identical | ✅ |
| C1c | landed 160×120 carve under dirty index | 4 / 0.1215 / 0.9784 / 0.0, ==accel, ==landed | ✅ |
| C1d | non-vacuity: ≥90% skipped final tick, AND naive predicate breaks identity | 90.0–93.5%; naive breaks 3 state vectors + onsets | ✅ |
| C1e | `input_epoch` declared + restored exactly by the stamp | stamp on identical; stamp off differs only there | ✅ (declared) |
| C2a | affine in dirty count, R² ≥ 0.95; cost(16) ≤ 5% of cost(19200) | R² 0.9994/0.9997; 1.46% / 0.12% | ✅ |
| C2b | exponent vs total cells at fixed dirty 16 ≤ 0.35 | **0.089 stamp OFF** ✅ / **0.683 stamp ON** ❌ | ✅ / ❌ |
| C2c | drain ≥ 10× over a 120-tick hold | 54× (on) / 6353× (off) @160×120 | ✅ |
| C3 | ≥ 10× per-tick improvement at 19200 on the adapted sheet | 65× frozen, **21× on real motion** | ✅ |
| C4 | full-field change ∈ [0.80, 1.25] of the full sweep | 1.099 and 1.157 | ✅ |
| C5 | Branch B default OFF, divergence measured, no identity claimed | defaults False; full curve; first divergence at δ=0 | ✅ |

**The one prereg threshold breached: C2b with the epoch stamp ON (0.683 > 0.35).**
It is not a surprise absorbed after the fact — it is a decomposed result: exact
whole-graph identity costs an O(cells) `input_epoch` write, 0.42 ms at 19 200.
Everything OBSERVABLE is byte-identical without it, at exponent 0.089.

## Provenance & discipline

- **Oracle** `bash scripts/rung7_vision_bench.sh`: **BEFORE 214 passed, 10
  skipped, 0 failed** (base sources + base engine rebuilt, md5 `7acf75f3…`) and
  **AFTER 214 passed, 10 skipped, 0 failed** — BEFORE == AFTER. (This worktree
  has no `data/` symlink, so the tree-wide condition is the documented
  "worktree-without-data" one; main reports 224/0 with data present.)
- **Gate** `tests/test_dirty_index_migrated.py`: **8 passed** — byte-identity
  3-way at 300 + on a FIRING 4800 carve, the naive-predicate falsifier, the
  fixed-point timing law, the Poisson no-skip boundary, cost-tracks-dirty-count
  at the mechanism grain, the full-field no-free-lunch falsifier, and Branch B
  default-OFF + bounded divergence. `tests/test_eye_accel_migrated.py` (184000)
  still **5 passed** — 13 together.
- **Rust built in this worktree ONLY.** Canonical `.so` md5
  `395637824bd541805abcff02ff42ef34` **UNCHANGED** (verified before and after).
  Worktree engine md5 `7572a616c6b83d5b8d3078acfa9efa88`.
  **CANONICAL NEEDS REBUILD ON MERGE.**
- `source_match = own`. **NO new Term enum variant** — `term.rs` untouched; a
  batch graph op + PyO3 entrypoint only. Seed block **185000–185999**;
  `scripts/seed_claim.py 185000 185999` → CLEAN.
- Curves + raw: `results/dirty_index.json`, `results/dirty_index/dirty_index.png`.

## Honest residuals

- **The exactness bookkeeping is the last O(cells) term.** With `stamp_epoch` on,
  every rod still gets an `input_epoch` write each tick (0.42 ms @19 200,
  exponent 0.683). Removing it makes the sheet truly O(dirty) (exponent 0.089)
  and leaves every OBSERVABLE byte-identical — but a rod's `input_epoch` then
  means "when this rod last changed", i.e. **per-sensor time**. That is arguably
  the architecturally correct reading rather than a compromise, but it is a
  SEMANTIC choice and is therefore not the default here.
- **Branch A's domain is a bit-repeatable input.** Under the default Poisson
  photon sensor it fires ZERO times, and the dirty index degenerates (safely,
  byte-identically) to the 184000 full sweep at a ~10-16% overhead. The 21×
  real-motion win is measured with the noiseless sensor. Whether a real
  event-camera front end (which reports changes above its own contrast threshold,
  i.e. a physical Branch B) recovers the win on noisy light is UNTESTED and is
  the obvious next question.
- **Branch B is a measured negative on this scene** (see C5): it manufactures
  false onsets and destroys the carve beyond δ≈2. A shed residual that is carried
  in the RECEPTOR (so the departure does not accumulate into a spurious onset)
  might behave differently; that was not built.
- **This is still the SHEET, not the whole eye.** The common-fate carve/motion/
  salience settle ops (one task each, per motion window) are untouched and
  unmeasured by this rung; a full "see + carve + name" loop at video rate is not
  claimed. With the per-cell sheet now O(surprise), **those settle ops are the
  next bottleneck** — and since they are per-AREA rather than per-cell, the
  natural next lever is exactly the named direction: **per-area ASYNC settlement**
  (each area on its own clock, spending compute in proportion to its own
  residual). The per-area dirty set built here is that mechanism's seed.
- The 240×180 frames are a nearest-neighbour upscale of the 160×120 fixture
  (there is no higher-resolution committed capture); it is a RESOLUTION scaling
  fact, not new visual content.

## Proposed VISION_PROTOCOL ledger row

`185000 | THE PER-AREA DIRTY-INDEX: per-tick cost O(SURPRISE) not O(cells) (retina_onset_batch work-list + exact bitwise settled predicate, adapter flag retina_dirty) | 184000 left an O(cells) FLOOR (batch touches every cell every tick) though an adapted scene is mostly silent; skip cells whose re-processing is a BITWISE no-op | the EMA reaches an EXACT float64 fixed point (t*≈71 @rate 0.4) — measured firing at tick 73, never before 65 — so BRANCH A skipping is PROVABLY byte-identical: ON≡184000-accel≡graph on polygons+onsets+iou/precision+adaptation/activation/prev_activation/caught_quanta @300/1200/4800/19200, landed 160×120 carve EXACT (4/0.1215/0.9784/0), 90-93.5% cells skipped; cost affine in dirty count R²=0.9994/0.9997, cost(16)=1.5%/0.12% of cost(19200), exponent vs cells at fixed surprise 0.089 (stamp off); REAL Doom motion @160×120 = 1.71ms/584 fps on ~508/19200 dirty cells = 21× the full sweep; drain 54×/6353×; 240×180 429 fps | FALSIFIERS BOTH HELD: full-field change costs 1.099×/1.157× the full sweep (no free lunch, 0 cells skipped) and the NAIVE "skip quiet cells" predicate BREAKS byte-identity (108443 vs 24816 skips, 3 state vectors + onsets diverge). Under the Poisson photon sensor the exact predicate fires 0.000 — a photon-COUNTING input is never bit-identical — so BRANCH B (bounded shedding) was built too: DEFAULT OFF, NO byte-identity claimed, and measured as a NEGATIVE (δ≥8 mints 45-168 spurious polygons, precision 0.98→0.21→0.0) | Rust built (canonical .so md5 395637… UNCHANGED, REBUILD ON MERGE); NO new Term enum (term.rs untouched); gate test_dirty_index_migrated 8/8 + eye_accel 5/5; oracle rung7 BEFORE==AFTER 214/10/0 (worktree-without-data); source_match own | the last O(cells) term is the input_epoch STAMP that buys exact whole-graph identity (0.42ms@19200, exponent 0.683 — the one breached prereg threshold, decomposed not excused); dropping it is exact on everything observable and means PER-SENSOR time; Branch A's domain is a bit-repeatable input; still the SHEET not the whole eye — the carve/motion/salience settle ops are now the bottleneck and per-area ASYNC settlement is the next lever`
