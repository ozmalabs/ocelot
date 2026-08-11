# SCALE — ATTRIBUTE the per-cell constant, then attack the batchable part — RESULTS

*Pre-registration: `VISION_SCALE_BULK_INGEST_PREREG.md`, committed at `3036583946`
BEFORE any number. Block 132000–132999. Extends 131000
(`VISION_SCALE_WALL_PUSH_RESULTS.md`).*

## VERDICT: **DEGRADE** — the bulk handoff is byte-identical and captures ~75% of its target, but the target is only **~21% of the tick**; the constant is DOMINATED by irreducible Rust per-cell compute (**~77%**). The boundary was NOT the scale lever.

131000 proved the O(N²) algorithmic wall is SPENT (batched drive LINEAR, ~50×50)
and NAMED the residual as the linear per-cell constant (16.8 µs/cell) + 11 idle
cores, WITHOUT measuring how much a bulk boundary handoff can buy. This rung
did the load-bearing step FIRST — **attributed the constant** — and only then
built the lever. The attribution answers the open question and, honestly, mostly
DEFLATES my own boundary hypothesis:

- **The 16.8 µs/cell constant decomposes (largest grid, 64², the REAL unaudited
  tick = 13.94 µs/cell) into: luminance ingest (a)+(b) 20.97 % · batched drive
  (c) 25.98 % · wave tick (c) 50.89 % · bookkeeping glue (d) 2.03 %.** So
  **irreducible Rust per-cell compute (drive + wave relaxation) is 76.88 %** of
  the constant; the batchable boundary work is a MODEST 21 %.
- **Amdahl bound the attribution implies: the bulk handoff can buy at most
  ×1.185 on the whole tick** (removing the entire luminance ingest saves 15.6 %).
- **The bulk handoff (`set_attr_each`) delivers ~75 % of that target** — it cuts
  the luminance write 2.923 → 0.744 µs/cell — for a measured whole-tick speedup
  of **×1.143–1.152, constant across a 28× cell range** (both arms LINEAR), a
  per-cell constant **17.05 → 14.91 µs/cell**, and a ceiling **49.7² → 53.2²**
  (×1.071/side, ×1.145 in cells).
- **BYTE-IDENTICAL, exactly** — 0 mismatched cells at all six grids, digests
  identical per grid; gated by `tests/test_bulk_ingest_migrated.py` (8/8).
- **Oracle `rung7_vision_bench.sh` 222/0 BEFORE and AFTER** on my own rebuilt
  engine.

**This is a DEGRADE, not a CONFIRM**, on the pre-registered rule (§6): the
handoff HELPS, is byte-identical, but is Amdahl-limited by a modest batchable
share. It borders FALSIFY — the luminance share (20.97 %) sits right at the
20 % floor, and the constant is clearly dominated by irreducible Rust (77 %).
**The next lever is NOT the boundary** — it is MULTI-CORE parallelism over the
per-cell Rust compute (drive + wave tick = 77 %, the parallelizable work; 11 idle
cores; 131000's Amdahl 2–6×) and/or reducing that Rust per-cell compute itself.
QVGA moved 1307 → 1138 ms and 1080p 35.5 → 30.9 s — real, but a constant-factor
nudge, not the order-of-magnitude the boundary hypothesis hoped for.

## 0. Provenance / engine / oracle

| item | value |
|---|---|
| engine | `own` `8c5f49e34e84` @ this worktree's `runners/dsl/python/substrate_rs/_native.abi3.so` |
| rust source fingerprint | `b1894331c7ac744e0cb7ae661a5b90ff18547a076ae1b04a887ce6c7df3b416e` |
| re-verify after run | `source_match = own`, sha `8c5f49e34e84`, fingerprint unchanged |
| Rust added | **`set_attr_each`** — a `#[pymethods]` bulk per-node-VALUE writer on the `Substrate` pyclass (`runners/dsl/src/py.rs`), the complement of `set_attr_many`; + one-line wrapper delegation in `runners/dsl/python/substrate_rs/__init__.py`. **NO new DSL Term; NUM_TERM_VARIANTS 181 unchanged; `variant_table_covers_the_enum` green.** |
| adapter | `domains/wave_world.py::drive` — a NEW opt-in bulk path gated on `getattr(self, "bulk_ingest", False)` (DEFAULT OFF, the `detect_cycles` precedent; committed per-cell path UNCHANGED) |
| oracle BEFORE | **222 passed, 0 failed** (`rung7_vision_bench.sh`, 174.3 s, engine `67add13387fa` = unchanged-source build of my tree) |
| oracle AFTER | **222 passed, 0 failed** (`rung7_vision_bench.sh`, 184.6 s, engine `8c5f49e34e84`) |
| byte-identity gate | `tests/test_bulk_ingest_migrated.py` **8 passed** |
| provenance gate | `tests/test_engine_provenance_migrated.py` **7 passed** |
| branch / base | `worktree-agent-ab2908ac50cad010f`, prereg commit `3036583946` |

## 1. Solitude & timing rigor — PROVEN

| item | value |
|---|---|
| machine | AMD Ryzen 5 9600X, 6-core / 12 logical |
| CPU governor | **powersave** (depresses absolute ms; **common-mode across arms**, so the PERCELL/BULK ratio and both exponents are governor-independent; only the absolute constant is not) |
| loadavg at start | **[0.184, 0.532, 0.488]** |
| loadavg at end | **[0.676, 0.613, 0.521]** |
| trials/grid | 12²–24²: 9; 32²: 7; 48²–64²: 5 (fixed in prereg) + 3 phase-trials/grid |
| block seeds drawn | **0** (deterministic: WaveWorld seed 0, frame seed 11) |

**Solitude proof — the per-point CI WIDTH.** Every per-point CI95 sits within
**±0.16 % to ±1.15 %** of its median; at the load-bearing large grids it is
**±0.16 % (64² BULK), ±0.18 % (32² PC), ±0.75 % (64² PC)**. The small grids (2 ms
ticks, jitter-sensitive) are the widest at ±0.93–1.15 %. **All are one to two
orders of magnitude below the 1.66× (66 %) swings prior rungs recorded under
contention** (`ENGINE_WINNER_VALUE`, `VIDEO_PROBE §0.1`) and refused wall-clock
over. The end-loadavg 0.68 is the single measuring thread itself (< 1.0 — even
lighter than 131000); no competing job was launched.
`determinism_across_trials_ok = True` at every point (every trial's final graph
state byte-identical) is a further contention-free witness.

## 2. The measured sweep (median ms/tick, machine alone)

| grid | cells | **PERCELL** ms/tick (CI95 %) | µs/cell | **BULK** ms/tick (CI95 %) | µs/cell | **speedup** |
|---|---|---|---|---|---|---|
| 12 | 144 | 2.4334 (±0.93 %) | 16.90 | 2.1270 (±1.15 %) | 14.77 | ×1.144 |
| 16 | 256 | 4.3157 (±0.58 %) | 16.86 | 3.7485 (±0.22 %) | 14.64 | ×1.151 |
| 24 | 576 | 9.6134 (±0.48 %) | 16.69 | 8.3664 (±0.41 %) | 14.52 | ×1.149 |
| 32 | 1024 | 17.1909 (±0.18 %) | 16.79 | 14.9499 (±0.37 %) | 14.60 | ×1.150 |
| 48 | 2304 | 38.8604 (±0.57 %) | 16.87 | 33.7201 (±0.68 %) | 14.64 | ×1.152 |
| 64 | 4096 | 69.8185 (±0.75 %) | 17.05 | 61.0696 (±0.16 %) | 14.91 | ×1.143 |

The speedup is **CONSTANT ~×1.15 across a 28× cell range** — the signature of a
constant-factor reduction, not an exponent change (both arms are already linear).
The PERCELL 16.7–17.05 µs/cell **re-earns 131000's 16.8 µs/cell** (same object,
same audit). Under BULK it is 14.5–14.9 µs/cell.

## 3. THE CONSTANT ATTRIBUTION — 16.8 µs/cell decomposed (the load-bearing step)

Per-tick phase decomposition at 64² (the REAL, unaudited retinal tick = **13.94
µs/cell**; the 16.8/17.05 µs/cell headline carries ~3 µs/cell of scale-audit
counting instrumentation that is NOT part of the workload — 131000's 16.8 is the
audited figure, disclosed here so the two are reconciled):

| phase | prereg candidate | share of tick | µs/cell (PERCELL) | µs/cell (BULK) |
|---|---|---|---|---|
| **luminance ingest** (`drive` − `_drive_phase`) | **(a) PyO3 FFI + (b) per-cell write** | **20.97 %** | **2.923** | **0.744** |
| **batched drive** (`_drive_phase`) | **(c) irreducible Rust rule compute** | 25.98 % | 3.622 | 3.622 |
| **wave tick** (`s.tick(200_000)`) | **(c) irreducible Rust relaxation** | 50.89 % | 7.095 | 7.095 |
| bookkeeping (`_mark_bursts`) | (d) bulk glue | 1.21 % | 0.169 | 0.169 |
| recruit/driven (`step` remainder) | (d) bulk glue | 0.82 % | 0.114 | 0.114 |

- **(a)+(b) the batchable boundary work = 20.97 %** of the constant.
- **(c) irreducible Rust per-cell compute = 76.88 %** (drive 25.98 % + wave tick
  50.89 %). **The wave relaxation ALONE is 51 %.**
- **(d) glue = 2.03 %** (already bulk).

**THE AMDAHL BOUND THIS IMPLIES:** removing the ENTIRE luminance ingest caps the
whole-tick speedup at **×1.185** (saves 15.6 %). The bulk handoff cuts the
luminance write **2.923 → 0.744 µs/cell** — it removes **74.5 %** of its target
(the residual 0.744 is the irreducible marshalling of N values across ONE
crossing: the per-value `py_to_value` conversion that must still happen). So the
handoff is EFFICIENT at what it targets; the target is just small.

**This EXTENDS 131000's PyO3 exoneration from the EXPONENT to the CONSTANT.**
131000 proved PyO3 is not the scaling exponent (FFI bucket linear). This rung
proves the boundary is not even the dominant share of the linear CONSTANT — it
is ~21 %, and 77 % is Rust the boundary handoff cannot touch. The "wrong-layer"
trap the prereg named (rungs 125000–128000) is avoided by MEASURING this rather
than assuming the boundary was large.

## 4. Exponent, ceiling, projections

| quantity | PERCELL (committed default) | BULK (new opt-in) |
|---|---|---|
| wall exponent vs cells | **1.002** (r² 0.99997) | **1.002** (r² 0.99995) |
| real-time ceiling @ 41.7 ms | **49.7²** (2467 cells) | **53.2²** (2830 cells) |
| per-cell constant (largest grid) | 17.05 µs/cell | **14.91 µs/cell** |
| QVGA (320×240) | 1306.9 ms | **1138.0 ms** |
| 1080p (1920×1080) | 35.5 s | **30.9 s** |

**Both arms are dead LINEAR** (exponent 1.002) — this rung moves the CONSTANT,
not the exponent, exactly as expected (131000 already linearised the tick). The
ceiling push is **49.7² → 53.2² = ×1.071/side, ×1.145 in cells** — real but
modest, and it MATCHES the ×1.15 speedup (for a linear tick, cells-ceiling ∝
speedup). 1080p is still ×740 over the 41.7 ms budget single-core; the bulk
handoff took a 15 % bite out of a constant that needs an order of magnitude.

## 5. Byte-identity — the bulk path == the per-cell path, bit-for-bit

`state_digest` = sha256 over exact `repr` of every drive-touchable attribute per
cell (14 attributes × N cells, no rounding, no tolerance — `CELL_ATTRS`). BULK vs
PERCELL, per grid:

| grid | 12 | 16 | 24 | 32 | 48 | 64 |
|---|---|---|---|---|---|---|
| mismatched cells | 0 | 0 | 0 | 0 | 0 | 0 |
| digests equal | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**The speedup changes no output.** Byte-identity is guaranteed by construction
(the SAME `float(...)` conversions, SAME cell order; only the crossing count
changes) and MEASURED here. Independently gated by
`tests/test_bulk_ingest_migrated.py` (8/8): bitwise-identical state on grids
{8,12,16}, the luminance carry exact, **a cropped (10×13) frame on a 16×16 grid**
(the in-bounds subset path a square frame never exercises), and the §9 default
(an un-opted world takes the per-cell path).

## 6. What I got WRONG (every prior rung found a real self-error; here is mine)

1. **My pre-registered CONFIRM band was SELF-CONTRADICTORY.** CONFIRM required
   BOTH (i) luminance share ≥ 20 % AND (iii) ceiling ≥ 1.15×/side. But for a
   LINEAR tick, a batchable share `f` caps the ceiling push at `√(1/(1−f))` per
   side, so ceiling ≥ 1.15×/side REQUIRES `f ≥ 24.4 %` — strictly ABOVE my own
   20 % floor. Any result in [20 %, 24.4 %) — which is exactly where the truth
   landed (20.97 %) — satisfies (i) and fails (iii) BY ARITHMETIC, forcing
   DEGRADE. **I mis-calibrated two thresholds against each other; the honest
   reading is the ATTRIBUTION itself, which is DEGRADE.** (This is a threshold
   error, not metric surgery: I am reporting it against myself, not rescuing a
   failure.)
2. **My boundary hypothesis was on the LOW end of even my own prediction, and
   131000 had already implied it.** I predicted DEGRADE modally (correct) but
   floated 20–40 % as the plausible luminance share; it is exactly 21 %, the
   floor. 131000's finding that FFI is a LINEAR CONSTANT (not the exponent)
   already pointed here — I under-weighted my own predecessor's evidence that the
   boundary is a small share. The attribution's real value is CONFIRMING the
   exoneration extends from exponent to constant.
3. **The 16.8 µs/cell "constant" is partly INSTRUMENT.** My headline per-cell
   figure (17.05 µs/cell) reproduces 131000's 16.8 because BOTH run with
   `scale_audit` enabled during timing; the TRUE unaudited retinal tick is
   **13.94 µs/cell** (~3 µs/cell is the op-counting instrumentation). I decompose
   the real 13.94; the shares transfer approximately. Neither number is wrong,
   but "16.8 µs/cell" should be quoted as *audited*, and the workload it
   decomposes is 13.94. I nearly reported the attribution against the audited
   figure without flagging this.

## 6b. Bench state — my gate green; 3 instrument-seams reds are PRE-EXISTING, none mine

`tests/test_bulk_ingest_migrated.py` **8/8**; `test_engine_provenance_migrated.py`
**7/7**; `test_batch_apply_migrated.py` green (my `drive` edit did not touch the
per-cell path); oracle **222/0** both sides. `tests/test_instrument_seams_migrated.py`
reports **3 failed / 27 passed** — ALL THREE PRE-EXISTING, verified NOT mine:

1. `test_the_preamble_gate_binds_NEW_violations_only` → `pa.new_violations()` ==
   `['scripts/codec_decision_probe.py']` — **the task's NAMED baseline red.** My
   measure script is NOT in the list (it calls `engine_preamble()`, not merely
   imports it). **I introduced NO new preamble violation.**
2. `test_the_measured_ledger_record_is_CURRENT` → the committed seed-record is
   stale w.r.t. 24 non-mine blocks (116000–131000; `committed=140 live=164`).
   The diff **never mentions block 132000** — my rung draws 0 seeds and is not
   implicated. Regenerating (`domains.seed_record --write`) would sweep 24 OTHER
   rungs' changes into a commit — **§11 forbids me touching a shared ledger I do
   not own; the supervisor sequences it.**
3. `test_every_new_prereg_records_its_check_claim_output` →
   `preregs_missing_claim()` == `['VISION_CLOSURE_PREREG.md',
   'VISION_EYEVIEW_PREREG.md', 'VISION_MOTIONENERGY_PREREG.md']` — three OTHER
   rungs' preregs. **`VISION_SCALE_BULK_INGEST_PREREG.md` is NOT in the list** —
   my prereg records its `check_claim` verbatim (§8).

None of the three reference any file I added or edited (verified: my diff vs base
is my prereg + `py.rs` + `wave_world.py` + the wrapper `__init__.py` + the new
gate + results/JSON; I touched no ledger, floor, or record file).

## 7. Scope — what is NOT shown (§8)

- **Multi-core is NAMED, not built.** The 77 % irreducible Rust (drive + wave
  relaxation) is the per-cell work that parallelises over 11 idle cores; this
  rung is single-thread and does not measure it (a §11.4-style report, per the
  prereg).
- **Out of scope:** the per-SCENE discovery/carve ops (`space_quantize`,
  `GenInfer`/`TimeInfer`/`DepthInfer`, `slide_flood`) — a separate cost that does
  not set the per-tick ceiling; not measured.
- **The absolute constant is governor/synthetic-frame specific** (powersave;
  synthetic drifting field) — the same disclosure 131000 made. The
  governor-independent claims are the SHARES, the exponent (1.002), and the
  PERCELL/BULK ratio on ONE instrument.
- **`set_attr_each` is a general bulk primitive**, but only the retina's
  luminance ingest is wired to it here. Other per-cell-different-value writes
  (e.g. rung 3's `prev_burst`, still a per-node loop) are candidates but were not
  changed (not in scope; §9 keeps them untouched).

## 8. Ledger row

| block | outcome |
|---|---|
| **132000–132999 (0 block seeds drawn — deterministic measurement, WaveWorld seed 0 + frame seed 11; `check_claim` CLEAN, unknown_sinks 560; Rust `set_attr_each` added — a bulk per-node-VALUE writer, NO new Term, NUM_TERM_VARIANTS 181 unchanged, variant-table green; adapter opt-in `bulk_ingest` path DEFAULT OFF)** | **ATTRIBUTE THE CONSTANT, THEN ATTACK THE BATCHABLE PART — DEGRADE. The 16.8 µs/cell constant (real unaudited tick 13.94) decomposes at 64² into luminance ingest (a)+(b) 20.97 % · batched drive (c) 25.98 % · wave tick (c) 50.89 % · glue (d) 2.03 % ⇒ irreducible Rust per-cell compute is 76.88 %; the batchable boundary work is a MODEST 21 %. Amdahl caps the bulk handoff at ×1.185; the built handoff (`set_attr_each`, one whole-field crossing replacing the 4N per-cell luminance loop) delivers ~75 % of that — cuts the luminance write 2.923 → 0.744 µs/cell — for a whole-tick ×1.143–1.152 CONSTANT across a 28× cell range (both arms LINEAR, exp 1.002), per-cell constant 17.05 → 14.91 µs/cell, ceiling 49.7² → 53.2² (×1.071/side, ×1.145 cells), BYTE-IDENTICAL (0 mismatched cells all six grids; `test_bulk_ingest_migrated` 8/8 incl. cropped-frame subset + §9 default). QVGA 1307 → 1138 ms; 1080p 35.5 → 30.9 s — a constant-factor nudge, not the order of magnitude. THE BOUNDARY IS NOT THE SCALE LEVER: 131000's PyO3 exoneration extends from the EXPONENT to the CONSTANT — the boundary is ~21 % of even the linear constant. NEXT LEVER NAMED, not built: MULTI-CORE over the 77 % per-cell Rust compute (drive + wave relaxation; 11 idle cores; Amdahl 2–6×) and/or reducing that Rust compute. WHAT I GOT WRONG: (1) my CONFIRM band was self-contradictory — ceiling ≥1.15×/side needs share ≥24.4 % but I set the share floor at 20 %, so [20 %,24.4 %) forces DEGRADE by arithmetic, and the truth (20.97 %) landed there; (2) I floated 20–40 % for the boundary share when 131000's FFI-linear finding already implied the low end (21 %); (3) the 16.8 µs/cell is AUDITED — the real workload is 13.94 µs/cell, ~3 µs/cell is op-counting instrumentation. Engine `own` `8c5f49e34e84`, re-verified stable after the run (fingerprint `b1894331c7ac…`); oracle `rung7_vision_bench` 222/0 BEFORE and AFTER; `check_claim` verbatim in prereg §8; loadavg [0.184]→[0.676], per-point CI ±0.16–1.15 % (vs the 1.66× contention swings) PROVING solitude; governor powersave (disclosed). NO new preamble-gate violation (the measure script calls `engine_preamble()`, not just imports it). Raw: `results/scale_bulk_ingest.json`; instrument `scripts/scale_bulk_ingest_measure.py`; gate `tests/test_bulk_ingest_migrated.py`. |
