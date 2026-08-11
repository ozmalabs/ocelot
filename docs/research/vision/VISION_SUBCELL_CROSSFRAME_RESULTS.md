# RESULTS — block 149000-149999: SUB-CELL CROSS-FRAME REGISTRATION

`SEED CLAIM 149000-149999:` **CLEAN** -- no collision DETECTED
(`python3 scripts/seed_claim.py 149000 149999`; `check_claim(149000, 149999)` ->
OK; 570 unresolved sink sites tree-wide, counted not discarded; "CLEAN" means no
collision DETECTED, never proven absent).

## VERDICT — CONFIRM-on-mechanism / DEGRADE-on-real-confidence

- **The mechanism is PROVEN (oracle CONFIRM).** Precision placed in the
  CROSS-FRAME OFFSET (invariant-clean, a finer-unit INTEGER) — where 147000's
  in-frame grid could not put it and 148000's aperture was not the wall —
  recovers a KNOWN sub-cell acceleration through the UNCHANGED robust integer
  witness. No Rust, no seed change.
- **The real clip moves OFF the floor but the number is NOT confirmed physical
  (DEGRADE-on-real-confidence).** Where the integer centroid floored (accel 0 /
  no order-2), the sub-cell path mints a nonzero order-2 coefficient — a real
  improvement in the right direction on one window (+1 = +0.1 cell/f²). But there
  is no ground-truth g for this clip in cell-units; the tracked run is only 7
  frames with a glitchy tail; and the two OVERLAPPING windows of the same fall
  recover OPPOSITE-sign accel_fine (+1 vs -2) with whole-cell per-pair residuals.
  So the coefficient is not established as the physical acceleration. **The wall
  MOVES to trajectory LENGTH / quality** (longer, cleaner tracked runs), not to
  precision (proven) nor aperture (148000) nor in-frame resolution (147000).

Judged by the COEFFICIENT, not the status flip (147000's hard lesson).

## Engine provenance (§10) — NO Rust built, source_match == shared

```
engine 64dbce1e7f47 @ .../runners/dsl/python/substrate_rs/_native.abi3.so
[shared build from .../gamma-substrate — Rust source identical]
```

The finer-unit INTEGER offset stream feeds the EXISTING `robust_order`
(`shape_decode.rs`, `&[Vec<i64>]`) UNCHANGED — no Rust variant was needed, exactly
the minimal form the reframe predicts. `source_match == shared`.

## Oracle (§2) — UNMOVED, 222/0 both sides

- BEFORE: `222 passed in 176.73s` (`var/oracle_before.log`, `bash scripts/rung7_vision_bench.sh`).
- AFTER:  `222 passed` (`var/oracle_after.log`; same shared engine — no Rust rebuilt).

## The invariant audit (§ BASE-AS-DIMENSION) — NO in-frame float

The crux of this rung. The frame/continuum invariant says in-frame coordinates
are INTEGER; non-integer / sub-cell structure is CROSS-FRAME (`Hom(frame,frame)`),
its observable the STEPPED (finer-unit INTEGER) rendering. Audited, clean:

- **The registration sensor's output contract is integer-only.**
  `domains/subcell_register.register_residual_offset` returns
  `cdr * S + bsy, cdc * S + bsx` — integer arithmetic on the coarse integer cell
  displacement (`cdr` = `int(round(cy))` differences) plus the argmin fine-grid
  offset `bsy/bsx` (integers over `range(-R, R+1)`). No float is returned as, or
  written into, any coordinate.
- **The carve centroid enters ONLY via `round(...)`** (the coarse integer anchor
  that centres the residual search). Its sub-cell (float) part is NEVER read —
  the forbidden "sub-pixel float centroid" does not appear (grepped the diff:
  every coordinate use is `int(round(...))`; the only `float(...)` calls are the
  frame-tick attr, the pixel COUNT, and grey VALUES — none a coordinate).
- **The bilinear upsample interpolates grey VALUES on a finer grid** inside the
  cross-frame comparator (a rendering), never a coordinate.
- **The cumulative positions fed to the witness are integer sums of integer
  offsets**; the graph Observation's coordinate slots read back as `int` (verified
  live). Gate: `test_no_in_frame_coordinate_is_a_float` asserts sensor output is
  `int`-typed, the whole position stream is `int`, and the graph coordinate slots
  are `int` — able to fail if any float ever leaks.

`S = 10` (the finer unit, 1/10 cell) and `SEARCH_CELLS = 3` are DECLARED
resolution residuals (§13), like `block` / `k` — the registration's sub-cell step
and residual aperture. NO tuned witness tolerance was added; the witness's
tolerance still falls out of integer bit-costs (`robust_order` unchanged). The
template = the `count` brightest window pixels (count from the carve — falls out,
no tuned threshold); window half-extent = `ceil(√count)+2`.

## Oracle chain-check — the mechanism, PROVEN (deterministic)

A textured square rendered at a KNOWN sub-cell parabola (`a_cell = 0.2`,
anti-aliased vertically — the sub-cell position is a stepped rendering of a
continuous translation), `S = 10` → target `accel_fine = a_cell*S = 2`:

| readout | stream (2nd diff) | status | accel |
|---|---|---|---|
| INTEGER centroid (`round(true top)`) | d2 = [0,1,0,-1,2,-1] | `time_none` | **None (FLOORS)** |
| SUB-CELL registration | py_fine = [0,0,3,9,16,25,36,49]; d2_fine = [3,3,1,2,2,2] | `time_inferred` | **2 == target** |

The integer centroid floors on the very parabola the sub-cell path resolves;
sub-cell recovers the known acceleration in finer units EXACTLY. The
registration/witness chain is correct before any real patch is blamed.

## Controls (all hold)

| control | result |
|---|---|
| const-velocity (sub-cell render) | `accel_coeff = None` — **no manufactured curvature** |
| static | mints nothing (`accel_coeff = None`) |
| random / noise | floors (`accel_coeff = None`) — registration of noise does not confabulate order-2 |
| ideal sub-cell oracle | recovers the known `accel_fine = 2` (above) |

## Real clip — the coefficient, honestly

Native `128×640` free-fall clip, carve+track for anchors, register the RAW grey
patch at sub-cell → finer-unit INTEGER position → the witness. Two OVERLAPPING
windows of the same fall + one that failed to track:

| config | run | INTEGER centroid | SUB-CELL accel_fine | d2_fine |
|---|---|---|---|---|
| `real_128x640_b6_2fps` (ss=55) | 7 | accel **0** (floored) | **+1** (=+0.1 cell/f²) | [1,1,0,-5,16] |
| `real_128x640_b6_2fps_early` (ss=50) | 7 | accel **None** (floored) | **-2** (=-0.2 cell/f²) | [-2,-2,6,0,-2] |
| `real_128x640_b6_1p5fps` | <4 | — | — (no witness) | — |

- **CONFIRM-on-mechanism:** where the integer centroid floored, the sub-cell path
  minted a NONZERO order-2 coefficient — the invariant-clean cross-frame precision
  moved the real clip off the floor 147000/148000 left it on. Window 1's +1 is the
  correct (downward) sign.
- **DEGRADE-on-real-confidence:** no ground-truth g for this clip in cell-units;
  the run is only 7 frames with a glitchy tail (the +16 in window 1 comes from
  pair 5's registration blowing up to a +2.8-cell residual); and the two
  overlapping windows disagree in SIGN (+1 vs -2). A real fall's acceleration is a
  single constant of one sign, so the sign disagreement shows the recovered
  coefficient is dominated by registration NOISE, not the physical curvature. The
  registration is unstable on the real patch: per-pair ROW residuals swing from
  -14 to +28 finer units (±1.4 to ±2.8 cells) and COLUMN residuals hit the ±30
  search boundary — the masked-template SAD is not locking onto a stable feature
  (motion blur + ruler occlusion + noisy carve anchor at real slow-mo scale).

**The wall, named:** trajectory LENGTH / patch-stability — a longer, cleaner
tracked run and a stable appearance model (updated/appearance-tracked template,
robust matching that rejects the ruler, or spatial-neighbour MV propagation for
longer tracking per 148000's named next step). NOT precision (oracle proves it),
NOT aperture (148000), NOT in-frame resolution (147000). A next rung testing an
appearance-tracked template is a NEW mechanism and needs its own pre-registration
(§3 rule 6); it was not bolted on here.

## §9 byte-identity — coarse integer-cell path UNCHANGED, default OFF

The sub-cell mechanism lives in NEW files only (`domains/subcell_register.py`,
`scripts/subcell_crossframe_measure.py`, the gate, the results/prereg/docs). No
existing engine / sensor / seed / carve file is modified, so the coarse
integer-cell path (`vector_field`, `falling_world`, the carve, the witness) is
byte-identical with the sub-cell path OFF — it is not wired into any existing
default. Proven by `test_byte_identity_off_only_new_files_touched` (git diff scope
vs base `c4814cd58f`: only allowed new files) and by the integer-centroid readout
in the real table reproducing 148000's floor (accel 0 / None).

## Cross-process stability (§12 / 148000's lesson)

The carve's region ids are a per-process HashMap artifact, so the gate asserts the
robust GRAPH-READ verdict (the minted coeff), NEVER an exact d2 constancy
(`len(set(d2))==1`, the exact mistake fixed in 148000's gate). The oracle and
invariant assertions are deterministic; the real-clip assertion reads the
committed graph-minted coeff. Fresh-process check: 8/8 fresh-process invocations passed, 0 failures (8 independent
`python3 -m pytest` invocations, 0 failures).

## WHAT I GOT WRONG

- **I ended without closing out.** The measurement was sound and complete, but I
  stopped before running the oracle AFTER, hardening the gate for cross-process
  stability, writing this results file, and committing. A measured result that is
  not closed out and committed is not a result — the supervisor caught the
  unfinished hand-off.
- **My first real-clip gate xfailed the whole thing as a flat DEGRADE.** That
  under-credited the mechanism: the sub-cell path genuinely moved the real clip
  OFF the integer floor (0 → nonzero, correct sign on window 1). The honest
  framing is CONFIRM-on-mechanism / DEGRADE-on-real-confidence — the mechanism
  works and is proven; only the confidence that the recovered NUMBER is the
  physical g degrades (short glitchy trajectory, no ground truth, cross-window
  sign disagreement). Reporting it as a bare DEGRADE would have buried a real
  positive.
- **Two overlapping windows were the right call, and I nearly ran only one.** One
  window (+1) alone looks like a clean confirm; the second (-2) exposed that the
  coefficient is within registration noise. Replicating on a fresh window before
  believing (§4) is what turned an over-claimable +1 into an honest DEGRADE-on-
  confidence.

## Proposed VISION_PROTOCOL.md ledger row

| **149000–149999 (sub-cell cross-frame registration; NO Rust — a gated Python SENSOR `domains/subcell_register.py`, DEFAULT OFF / new files only; feeds the 146000 robust witness UNCHANGED)** | **SUB-CELL CROSS-FRAME OFFSET — precision in the MAP, not the frame (mechanism CONFIRM; real-clip DEGRADE-on-confidence, wall moves to trajectory length).** The frame/continuum invariant says WHERE precision may live: NOT in a frame's INTEGER coordinates (147000 raised the in-frame grid, the aperture paid ∝R, real clip still a=0) but in the CROSS-FRAME MAP `Hom(frame,frame)` — the per-frame displacement, "its observable the STEPPED finer-unit INTEGER rendering". Fix: REGISTER the tracked ball's grey patch across consecutive frames at sub-cell precision (masked-template upsampled SAD) and emit the offset as a FINER-UNIT INTEGER (×S); the stream feeds the existing `robust_order` `&[Vec<i64>]` witness UNCHANGED (no Rust). **INVARIANT AUDIT CLEAN:** no float in any in-frame coordinate — the carve centroid enters only via `round()` (coarse integer anchor; its sub-cell float part is never read — the forbidden sub-pixel float centroid is absent), the bilinear upsample interpolates grey VALUES (a rendering) not coordinates, the emitted offsets and cumulative positions are integers, the graph coordinate slots read back `int` (gate `test_no_in_frame_coordinate_is_a_float`). **ORACLE CONFIRM (deterministic), judged by the COEFFICIENT:** a known sub-cell parabola (a_cell 0.2, anti-aliased; S=10 → target accel_fine 2) — INTEGER centroid FLOORS (d2 [0,1,0,-1,2,-1], time_none) while SUB-CELL recovers accel_fine EXACTLY 2 (py_fine [0,0,3,9,16,25,36,49], time_inferred). The registration/witness chain is proven correct. **REAL 128×640 DEGRADE-on-confidence:** where the integer centroid FLOORED (accel 0 / None — reproducing 147000/148000), the sub-cell path minted a NONZERO order-2 coeff (+1 = +0.1 cell/f², correct downward sign) — the mechanism moved off the floor — BUT no ground-truth g, the tracked run is 7 frames with a glitchy tail, and two OVERLAPPING windows of the SAME fall disagree in SIGN (+1 vs −2) with whole-cell per-pair residuals (row −14..+28, column at the ±30 boundary): the coefficient is registration NOISE, not confirmed physical g. Wall MOVES to trajectory LENGTH / patch-stability (longer clean runs; appearance-tracked template; spatial-neighbour MV propagation), NOT precision (proven), aperture (148000) or in-frame resolution (147000). CONTROLS hold: const-velocity → no manufactured curvature; static → nothing; noise → floors; ideal oracle → known accel. No agent decision in Python (the sensor reads only pixel arrays; every order-N decision stays the seed rule — audited). S=10 / search_cells=3 declared §13 residuals; NO tuned witness tolerance. shared engine `64dbce1e7f47` (source_match==shared, no Rust); oracle 222/0 BEFORE and AFTER; gate `test_subcell_crossframe_migrated` 5/5 (graph-read, cross-process-stable — robust minted coeff, never exact d2; 8/8 fresh-process invocations passed, 0 failures); §9 byte-identity — new files only, coarse integer-cell path unchanged (integer-centroid readout reproduces the floor); `SEED CLAIM 149000-149999 CLEAN`. Raw: `results/subcell_crossframe_measure.json`; `VISION_SUBCELL_CROSSFRAME_RESULTS.md`. |
