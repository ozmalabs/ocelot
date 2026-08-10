# SCALE WALL — the WALL-CLOCK truth of the batched drive, machine ALONE — PRE-REGISTRATION

*Committed BEFORE any number (PROTOCOL §3). Block 131000–131999.*

## 0. Provenance (§10)

- Engine: `own` `67add13387fa` @ this worktree's
  `runners/dsl/python/substrate_rs/_native.abi3.so` (built by
  `scripts/engine_build.sh`; `tests/test_engine_provenance_migrated.py` 7/7).
- Rust source fingerprint `324b73d745df566dc8d34e09008c9310e9be2b86989a22e00c7cf0e6679d687a`.
- **This rung adds NO Rust and NO seed.** It is a MEASURING INSTRUMENT over the
  already-committed batched drive. NUM_TERM_VARIANTS unchanged (181); no Term
  index allocated. If that changes, this line is wrong and the rung stops.
- Base worktree HEAD `1279387a45` (branch `worktree-agent-a542f4134fe2a2823`).

## 1. The gap this fills — WHY it is worth a rung

The scale wall was measured and attributed by three prior rungs, ALL in COUNTS,
because the machine was always contended and every one correctly refused
wall-clock (`VISION_VIDEO_PROBE_RESULTS.md` §0.1; `ENGINE_WINNER_VALUE` 1.66×
on load alone):

1. **Video probe** (`VISION_VIDEO_PROBE_RESULTS.md` §S5): wall exponent **1.887**
   (r² 0.997, n=4) on real frames ⇒ **1920×1080 = 164 h/frame**, and at a
   23.976 fps budget (41.7 ms/tick) the affordable field is **336 cells = 18×18**.
   Measured with the drive UNBATCHED (`apply_rule_once`, before batch landed).
2. **Scale split** (`VISION_SCALE_SPLIT_RESULTS.md`): counted-op exponent **1.955**
   (r² 0.99992); of F(FFI)/C(comparison-enumeration)/R(redundancy), **only C is
   superlinear (1.980)**; **FFI is LINEAR at 0.998** — *"an FFI term at exponent
   0.998 cannot produce a wall at 1.955 at any N; removing FFI entirely shifts
   the 1080p projection by 0.3%."* **PyO3 is EXONERATED as the scaling cause.**
   Taking the drive re-enumeration out drops the exponent **1.955 → 0.982**.
3. **Batch-apply** (`VISION_BATCH_APPLY_RESULTS.md`): BUILT the fix — `batch:true`
   on the five `vision_change` rules (v1.1.0) + `Substrate::apply_rule_batch` +
   one adapter line; the counted exponent fell to **linear, constant in N** over
   a 28× cell range, **byte-identical** (a byte-identity hazard in the eval cache
   was found and fixed; gated by `tests/test_batch_apply_migrated.py`). **This is
   the committed DEFAULT today** (`_drive_phase` calls `apply_rule_batch`; the
   five rules all carry `batch:true`).

**What NO rung has done: measure the batch fix in WALL-CLOCK, or state the NEW
real-time resolution ceiling.** The 18×18/1.887 memory is the PRE-batch number.
I have the machine to myself (loadavg recorded, solitude proven). I convert the
counted attribution into the wall-clock truth and the new ceiling, byte-identity
re-proven at the wall.

## 2. Object measured (SCOPE — stated up front, §8)

The **assembled-eye RETINAL TICK** — waves + change + lateral — booted
byte-for-byte as `scale_split_measure._boot_eye` / `video_probe_measure.boot_eye`
(the object that produced 1.887 and the 18×18 ceiling). Frame-driven with the
committed smooth drifting synthetic field (`scale_split_measure._frames`, seed 11)
— the object `VISION_SCALE_SPLIT_RESULTS.md` established reproduces the workload
(counted 1.955 ≈ wall 1.887).

**Explicitly OUT of scope:** the per-SCENE discovery/carve ops (`space_quantize`,
`GenInfer`/`TimeInfer`/`DepthInfer`, `slide_flood`) are a separate cost (regime B
in `assembled_eye_scale.py`); they do NOT set the 18×18 per-tick ceiling and are
not measured here. This rung is the PER-TICK retinal cost that sets the ceiling.

## 3. Statistics (fixed here, §3.2)

Two arms, expressed as GRAPH DATA (the batch flag), never a Python code fork —
inherited verbatim from `batch_apply_measure`:
- **OFF (slow / baseline):** the five `ch_*` rules with `batch` STRIPPED from the
  seed ⇒ `apply_rule_batch` delegates to `apply_rule_once` (M re-derivations, the
  pre-batch O(N²) drive).
- **ON (fast / committed default):** `batch:true` live ⇒ `batch_apply_rule`
  (one enumeration/drive-rule/pass).

Per grid g ∈ {12, 16, 24, 32, 48, 64} (the video probe's four + two larger),
per arm:
1. **Wall ms/tick** — `T = 9` timed trials, each the mean over `TICKS = 20`
   ticks after `WARMUP = 5` discarded ticks; a fresh boot per trial; `gc.collect()`
   before each timed region. Report **median, IQR, and a bootstrap 95% CI** of the
   per-trial ms/tick. (Multi-trial + CI — NO single-shot verdict, §timing.)
2. **Wall exponent** — log-log OLS of median ms/tick vs cells, with r². One per arm.
3. **Real-time ceiling** — affordable grid at the **41.7 ms/tick** budget
   (23.976 fps, the video probe's own budget — it FALLS OUT of the frame rate,
   §13, nothing chosen): `cells* = (41.7/e^intercept)^(1/exponent)`, `grid* =
   √cells*`. One per arm. The OFF arm re-earns 18×18; the ON arm is the new ceiling.
4. **Speedup** — median ms(OFF)/median ms(ON) per grid, headline at the largest grid.
5. **Byte-identity** — `state_digest` (sha256 over exact per-cell reprs of every
   drive-touchable attribute, NO tolerance — `batch_apply_measure.CELL_ATTRS`) for
   ON and OFF at every grid; PLUS the full per-cell record so a mismatch localises
   to a cell+attr. Required: **0 mismatches, all grids**.
6. **Attribution (wall + count)** — the F/C/R counted buckets per arm (the audited
   Rust counters), confirming at the wall level that (a) FFI stays linear and is
   not the binding cost, (b) C collapses from superlinear→linear under batch.

**Liveness is a HARD gate per point** (§1): frozen checksum, zero `cand_enum`, or
a dead witness aborts. Conservation asserts (the imported instrument's) must hold.

## 4. Solitude & timing rigor

`os.getloadavg()` recorded at start and end of the measurement, INSIDE the
measuring process, and printed. A timing number is void if loadavg rose
materially during it. CPU governor: `powersave` (recorded; noted as a caveat —
it depresses absolute ms but is common-mode across arms, which is what the OFF/ON
comparison rests on). 12 logical cores; single measuring process, single thread of
timed work. No concurrent load spawned (I am the only rung running).

## 5. n / seeds (§3.3, §3.4)

The measurement is fully DETERMINISTIC (WaveWorld seed 0, frame seed 11, fixed
grids) — like `scale_split_measure` and `batch_apply_measure`, it consumes **NO
seed** from block 131000–131999. The block is allocated defensively; the results
doc will record exactly which (if any) integers are drawn (expected: none) and
disclose any out-of-block draw. The "n" for the wall claim is T=9 trials/point ×
6 grids; the exponent claim's unit is the 6-point fit per arm.

## 6. Decision rule — CONFIRM / DEGRADE / FALSIFY (two-sided, §3.5)

Registered BEFORE any number:

- **CONFIRM** iff ALL hold: (i) byte-identity — 0 per-cell mismatches, all grids;
  (ii) ON wall exponent ≤ OFF wall exponent − 0.5 **and** ON exponent < 1.3
  (batching linearises the WALL as the counts predicted); (iii) the ON real-time
  ceiling grid ≥ **2×** the OFF ceiling grid (a measured push — stated 18×18 → N×N);
  (iv) oracle `rung7_vision_bench.sh` 222/0 BEFORE and AFTER; (v) FFI attributed
  linear (F-bucket exponent < 1.3), confirming PyO3 is not the binding cost.
- **DEGRADE** iff byte-identity holds and ON is faster (ceiling pushed) but
  sub-target: exponent falls but stays ≥ 1.3 (a residual superlinearity survives —
  NAME it), OR the ceiling push is real but < 2×, OR the push is real yet a residual
  O(N) constant/FFI still keeps real-resolution out of reach. Report the measured
  push and what remains.
- **FALSIFY** (first-class) iff the batch fix does NOT move the WALL ceiling within
  noise (ON exponent and ceiling ≈ OFF) DESPITE moving the counts — i.e. the wall
  binding cost is something batching does not touch. Then PROVE it (show the count
  speedup with no wall speedup) and NAME the next lever. **OR** byte-identity FAILS
  (any per-cell mismatch) — then the fast path DOES NOT SHIP; report the divergence
  (cell, attr, values) instead of a speedup.

## 7. Prediction, with provisos (§3.7)

I predict **CONFIRM on exponent and byte-identity, with a real DEGRADE risk on
"real-resolution reachable".** Reasoning: the counts strongly imply the wall
follows (C was 98–99% of enumeration and it is the drive re-enum that batching
removes); byte-identity is already gated. Provisos that would break, and what each
would teach:
- If the ON exponent lands ~1.0 but the per-cell CONSTANT (µs/cell) keeps 1080p
  (2.07 M cells) far above 41.7 ms even linearly, the ceiling jumps HUGELY (18×18 →
  hundreds-of-cells-a-side) yet 1080p stays unreachable at real-time on one core ⇒
  CONFIRM on the push, honest DEGRADE on "native video". **This is my modal call.**
- If FFI + adapter glue (both O(N)/tick) DOMINATE the batched eye (the
  `assembled_eye_scale` Amdahl suggested FFI is a large share of the BATCHED eye),
  the ON exponent may sit ABOVE 1.0 while still ≪ OFF — the quadratic→linear story
  then rests on the drive-reenum removal and the residual is a linear FFI/glue
  constant, the named next lever (bulk per-frame handoff).
- If the ON exponent is NOT ~1.0 but still ~1.9, that FALSIFIES "batch moves the
  wall": the wall O(N²) would be elsewhere (wave fixpoint depth? lateral pooling?),
  and I would have to find and name it. I predict AGAINST this.

## 8. §3 clause 8 — verbatim `check_claim` for block 131000–131999

```
SEED CLAIM 131000-131999: CLEAN -- no collision DETECTED.
  Scope: 838 files with seed sinks; 559 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

unknown_sinks = 559 (tree-wide, counted not discarded). This rung draws 0 seeds
(deterministic measurement), so none of the 559 is mine.

## 9. §9 / architecture

No default changes (the batched drive is ALREADY the committed default; the OFF
arm is a measurement-only stripped-seed control, exactly as `batch_apply_measure`).
No new Python agent decision — the instrument is mechanical I/O + timing over the
committed seeds. No Rust, no Term, no seed edit.
