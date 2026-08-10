# SCALE — ATTRIBUTE the per-cell constant, then attack the batchable part (BULK PyO3 INGEST) — PRE-REGISTRATION

*Committed BEFORE any number (PROTOCOL §3). Block 132000–132999. This rung
EXTENDS `VISION_SCALE_WALL_PUSH_RESULTS.md` (131000), which proved the O(N²)
algorithmic wall is SPENT — the committed batched drive is LINEAR (~50×50 @
23.976 fps) and PyO3 was EXONERATED as the EXPONENT driver. What remains between
~50×50 and real resolution is (i) the linear per-cell constant (measured 16.8
µs/cell) and (ii) 11 idle cores. 131000 NAMED but did not measure how much of
that constant a bulk boundary handoff can buy — that is this rung.*

## 0. Provenance (§10)

- This rung **ADDS RUST** (a bulk per-node-value attribute writer, see §3), so
  it MUST build its own engine (`scripts/engine_build.sh`) and measure that
  binary. `domains/engine_provenance.provenance_line()` printed from inside the
  measuring process; `source_match ∈ {own, shared}` asserted, NEVER a literal
  build hash.
- The engine hash + `rust_source_fingerprint` are recorded in the RESULTS doc
  (they are not knowable until the build) with a post-run re-verify.
- **NO new DSL Term.** `set_attr_each` is a `#[pymethods]` method on the
  `Substrate` pyclass — the exact per-node-value complement of the existing
  `set_attr_many` (uniform) and `get_attr_many` (read). NUM_TERM_VARIANTS
  UNCHANGED (181); no Term index allocated; `variant_table_covers_the_enum`
  stays green. If that changes, this line is wrong and the rung stops.

## 1. The gap this fills — WHY it is worth a rung

131000 established, machine ALONE, byte-identical:
- OFF (unbatched drive) wall exponent **1.939** → 17.1² ceiling (re-earns the
  memory's 18×18);
- ON (batched drive, the committed DEFAULT) wall exponent **0.997 — LINEAR** →
  49.9² ceiling; per-cell constant **16.8 µs/cell**;
- **PyO3 exonerated as the EXPONENT driver** (FFI bucket linear 0.997/0.998 on
  both arms); the binding super-linear cost was the drive RE-ENUMERATION, which
  batching removed.

131000 then NAMED the residual as "(i) the linear per-cell constant 16.8 µs/cell
(of which the FFI bucket and the adapter's per-cell luminance write are the
batchable parts) and (ii) 11 idle cores" — **but did not MEASURE the share** of
the constant those batchable parts occupy. Assuming that share is large is
exactly the "wrong-layer" trap that bit rungs 125000–128000. This rung
ATTRIBUTES the 16.8 µs/cell FIRST, and only then attacks the dominant batchable
part, with the Amdahl bound stated up front.

**The concrete hot path (read from `domains/wave_world.py::present`,
`fovea_radius=0`, the default):** every OTHER per-cell quantity in `step()` is
ALREADY bulk (`get_attr_many`/`set_attr_many` for state/driven/bursting). The
ONE surviving per-cell Python→Rust loop is the luminance ingest:

```
for (r, c), n in self.cells.items():
    at = self.s.node(n)["attrs"]             # 1 crossing, materialises FULL attr dict
    self.s.set_attr(n, "lum_prev", ...)      # 1 crossing, builds old+new py objects
    self.s.set_attr(n, "lum_raw",  ...)      # 1 crossing
    self.s.set_attr(n, "lum_seen", ...)      # 1 crossing
```

**4 boundary crossings/cell/tick**, and `node()` materialises the whole
attribute dict (~15 objects) to read nothing. `set_attr_many` (uniform value)
CANNOT replace this because the values DIFFER per cell — which is precisely why
this loop survived the bulk conversion that batched everything else.

## 2. Object measured (SCOPE — up front, §8)

The **assembled-eye RETINAL TICK** — waves + change + lateral — booted
byte-for-byte as `scale_split_measure._boot_eye` /
`batch_apply_measure.build_world` (the object that produced 1.887, 18×18,
16.8 µs/cell). Frame-driven with the committed smooth drifting synthetic field
(`scale_split_measure._frames`, seed 11). The batched drive
(`apply_rule_batch`, the committed default) is ON in EVERY arm — the intervention
is the LUMINANCE INGEST path only, layered on top of the already-committed batch.

**Explicitly OUT of scope:** the per-SCENE discovery/carve ops (`space_quantize`,
`GenInfer`/`TimeInfer`/`DepthInfer`, `slide_flood`) — a separate cost that does
not set the per-tick ceiling; not measured. Multi-core parallelism is NAMED as
the alternative lever if attribution FALSIFIES the boundary hypothesis; it is
NOT built here (a §11.4-style report, not a build).

## 3. What is BUILT — the bulk per-frame PyO3 handoff

**Rust primitive (`runners/dsl/src/py.rs`): `set_attr_each(nodes, key, values)`**
— writes `values[i]` onto `nodes[i][key]` in ONE crossing. It is the per-node-
value complement of `set_attr_many`: same interner-once, same `scale_audit::ffi`
accounting, same `attr_set`-hook fallback to the per-node path (byte-identical
hook semantics), same no-existence-check-when-no-hook contract. **No new
capability, no decision** — a world adapter still chooses WHICH nodes and WHAT
values; only the LOOP moves to the Rust side of the boundary (CLAUDE.md:
"primitive in Rust, composition in graph"). No new DSL Term.

**Adapter (`domains/wave_world.py::present`): a NEW opt-in bulk path**, gated on
`getattr(self, "bulk_ingest", False)` — the exact `detect_cycles` precedent
(an opt-in attribute, DEFAULT FALSE, byte-identical when unset). With it OFF the
committed per-cell loop is UNCHANGED and still runs (§9). With it ON:

```
prev = get_attr_many(cell_ids, "lum_raw")        # bulk read (old lum_raw)
seen = get_attr_many(cell_ids, "lum_seen")        # bulk read
set_attr_each(cell_ids, "lum_prev", [float(p or 0.0) for p in prev])
set_attr_each(cell_ids, "lum_raw",  [float(frame[r,c]) for (r,c) in cell_rc])
set_attr_each(cell_ids, "lum_seen", [float(s or 0.0)+1.0 for s in seen])
```

5 crossings total instead of 4N. **Byte-identity is guaranteed by CONSTRUCTION,
not hoped for:** the SAME `float(...)` conversions produce the SAME f64 values in
the SAME cell order; only the number of crossings changes. The in-bounds guard
(`r < frame.shape[0] and c < frame.shape[1]`) is replicated on the subset. The
`frame_median` write and the `_drive_phase()` call are unchanged.

## 4. Statistics (fixed here, §3.2)

### 4.1 THE ATTRIBUTION — decompose 16.8 µs/cell FIRST (the load-bearing step)

At each grid, on the committed batched drive, I wrap `present` (luminance write +
drive), `_drive_phase`, and `s.tick` with perf-counter timers (measurement-only,
in the script — no committed code path timed), and decompose the per-tick wall:

- **t_lumwrite** = t(present incl. drive) − t(`_drive_phase`) — the per-cell
  luminance ingest (candidate (a) FFI + (b) per-cell write + (d) glue for ingest);
- **t_drive** = t(`_drive_phase`) — the batched rule application (candidate (a)
  FFI-to-batch + (c) irreducible Rust rule compute);
- **t_tick** = t(`s.tick`) — the wave rules (candidate (c) irreducible compute);
- **t_other** = t(step) − t(present incl. drive) − t(`s.tick`) — the bulk
  bookkeeping (`_mark_bursts`, `set_attr_many` — already bulk glue (d)).

Each reported as µs/cell AND as a fraction of the total per-tick wall.

Then the **batchable share** — split t_lumwrite into FFI/object overhead
(batchable) vs irreducible marshalling — by measuring per-cell vs bulk luminance
write: `Δ = t_lumwrite(per-cell) − t_lumwrite(bulk)`. **The Amdahl bound the
attribution implies:** the MAXIMUM the bulk handoff can buy on the whole tick is
`Δ / t_step_total`. If (t_lumwrite batchable) is a small fraction of the tick,
the boundary is NOT the lever, and I say so (see §6 FALSIFY).

### 4.2 THE PER-CELL CONSTANT / CEILING under bulk ingest — same protocol as 131000

Two arms as GRAPH/config DATA (the `bulk_ingest` flag), never a Python code fork:
- **PERCELL (baseline / committed default):** `bulk_ingest=False` ⇒ the current
  per-cell loop.
- **BULK (intervention):** `bulk_ingest=True` ⇒ the one-crossing ingest.

Per grid g ∈ {12, 16, 24, 32, 48, 64} (131000's grids), per arm:
1. **Wall ms/tick** — T timed trials (T = {12:9,16:9,24:9,32:7,48:5,64:5}), each
   the mean over TICKS = 20 ticks after WARMUP = 5 discarded; fresh boot per
   trial; `gc.collect()` before each timed region. Report median, IQR, bootstrap
   95% CI. NO single-shot verdict (§ timing).
2. **Per-cell constant** — median µs/cell at the largest grid, PERCELL vs BULK.
3. **Wall exponent** — log-log OLS of median ms/tick vs cells, r², per arm (both
   expected LINEAR — the batched drive is already linear; this rung moves the
   CONSTANT, not the exponent).
4. **Real-time ceiling** — affordable grid at 41.7 ms/tick (23.976 fps, FALLS
   OUT of the frame rate, §13), per arm: PERCELL re-earns ~50×50; BULK is the new
   ceiling.
5. **QVGA (320×240) / 1080p (1920×1080) per-frame projections**, PERCELL vs BULK.
6. **Byte-identity** — `state_digest` (sha256 over exact per-cell reprs of every
   drive-touchable attribute, `batch_apply_measure.CELL_ATTRS`, NO tolerance) for
   PERCELL and BULK at every grid, PLUS the full per-cell record so a mismatch
   localises to a cell+attr. Required: **0 mismatches, all grids**.

**Liveness is a HARD gate per point** (§1): frozen checksum, zero `cand_enum`, or
a dead witness aborts. Conservation asserts (the imported instrument's) hold.

## 5. Solitude & timing rigor (§ timing)

`os.getloadavg()` recorded at start AND end INSIDE the measuring process, printed.
Solitude is PROVEN by per-point CI WIDTH: sub-0.5% per-point CI95 = solitude; the
1.66× swings prior rungs saw = contention (131000 §1). CPU governor recorded
(`powersave` — depresses absolute ms, common-mode across arms, so the PERCELL/BULK
ratio and both exponents are governor-independent; only the absolute constant is
not). 12 logical cores; single measuring process/thread; NO concurrent load
spawned (I am the only rung running). `determinism_across_trials_ok` per point
(every trial's final graph state byte-identical) is a further contention-free
witness.

## 6. Decision rule — CONFIRM / DEGRADE / FALSIFY (two-sided, §3.5)

Registered BEFORE any number:

- **CONFIRM** iff ALL hold: (i) the attribution shows the batchable luminance
  ingest (a)+(b) is a **MEANINGFUL share** of the 16.8 µs/cell constant
  (≥ 20% of the per-tick wall at the largest grid); (ii) the bulk handoff cuts
  the per-cell constant by a measured factor consistent with the Amdahl bound;
  (iii) the ceiling moves ~50×50 → measurably larger (BULK affordable grid ≥
  1.15× PERCELL); (iv) BYTE-IDENTICAL — 0 per-cell mismatches, all grids; (v)
  oracle `rung7_vision_bench.sh` 222/0 BEFORE and AFTER; (vi) QVGA/1080p move
  toward real-time as the Amdahl bound predicts.
- **DEGRADE** iff byte-identity holds and the bulk handoff HELPS but is
  Amdahl-limited (the batchable share is a MODEST fraction, so the whole-tick
  speedup is < the naive per-cell speedup): report the measured share, the real
  speedup, and how much of the constant is irreducible Rust compute (c).
- **FALSIFY** (first-class, names the next lever) iff the attribution shows the
  16.8 µs/cell is DOMINATED by irreducible Rust per-cell compute (c) — the
  batchable ingest (a)+(b) being a SMALL fraction (< 20% of the per-tick wall) —
  so the boundary handoff buys little. Then the boundary is NOT the scale lever:
  PROVE it (the attribution numbers + a byte-identical bulk arm that moves the
  ceiling < 1.15×), and NAME the real lever — MULTI-CORE parallelism over cells
  (131000's 11 idle cores, Amdahl 2–6×) and/or reducing the Rust per-cell compute
  itself. **Do NOT rescue the boundary lever if attribution kills it; do NOT
  claim a speedup that is not byte-identical.**

## 7. Prediction, with provisos (§3.7)

I predict **DEGRADE, modally** — the bulk ingest is byte-identical and cuts the
luminance-write constant substantially, but the whole-tick speedup is
Amdahl-limited because the irreducible Rust rule/wave compute (t_drive + t_tick)
is a large share of the 16.8 µs/cell. Reasoning: 131000 measured the FFI bucket
as a LINEAR but non-trivial CONSTANT share; the luminance loop is 4N crossings,
the single largest per-cell Python-side cost, but the batched drive + `tick`
still run the actual cell dynamics in Rust each tick. Provisos and what each
would teach:
- If t_lumwrite is ≥ ~40% of the tick, the bulk handoff CONFIRMS with a large
  push (the boundary WAS a major share of the constant). I predict against a
  share this large, given 131000's FFI-linear finding.
- If t_lumwrite is < ~20% of the tick, the attribution FALSIFIES my own boundary
  hypothesis — the constant is dominated by irreducible Rust compute (c), and the
  next lever is multi-core / cheaper Rust per-cell, NOT the boundary. **This is a
  good outcome** (§7 of PROTOCOL: a diagnosed negative that names the next lever
  is worth more than an undiagnosed positive), and I state it plainly if the
  numbers say so.
- Byte-identity is guaranteed by construction (same floats, same order); if it
  FAILS, the fast path does not ship and I report the divergence (cell, attr,
  values) instead of a speedup.

## 8. §3 clause 8 — verbatim `check_claim` for block 132000–132999

```
SEED CLAIM 132000-132999: CLEAN -- no collision DETECTED.
  Scope: 839 files with seed sinks; 560 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

unknown_sinks = 560 (tree-wide, counted not discarded). This rung draws **0
seeds** (deterministic measurement: WaveWorld seed 0, frame seed 11, fixed
grids), so none of the 560 is mine.

## 9. §9 / architecture

The committed per-cell luminance path is UNCHANGED and still runs by default
(`bulk_ingest` unset ⇒ False, the `detect_cycles` precedent). The bulk path is a
NEW option proven byte-identical to it (§4.2 item 6 + a migrated gate
`tests/test_bulk_ingest_migrated.py` comparing BULK==PERCELL digests, 0
mismatches, on a battery of grids). No new Python agent decision — the adapter is
mechanical I/O; the flag is config, dispatched like `detect_cycles`/`fovea_radius`.
Rust adds ONE bulk writer method (no Term, no seed). All committed gates + the
oracle stay green.
