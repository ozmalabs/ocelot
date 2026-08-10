# PRE-REGISTRATION — block 149000-149999: SUB-CELL CROSS-FRAME REGISTRATION

`SEED CLAIM 149000-149999:` CLEAN -- no collision DETECTED (`python3
scripts/seed_claim.py 149000 149999`; `check_claim(149000,149999)` -> OK).
Written before the REAL-CLIP measurement (the oracle/control chain was validated
as a deterministic pilot; the real-clip coefficient is prospective).

## The reframe (the crux — the frame/continuum invariant)

147000 added precision to the IN-FRAME grid (where the block aperture pays for
it ∝ R) and the real clip still floored at a=0. 148000 decoupled the aperture
but the small real per-frame curvature stayed below the integer-CENTROID noise
floor (((4,0),(0,0)) — velocity recovered, accel 0). The invariant
(`BASE-AS-DIMENSION + the frame/continuum invariant`) says WHERE precision may
live: NOT in a frame's coordinates (in-frame is INTEGER; `coord_ints` refusing a
float is CORRECT), but in the CROSS-FRAME MAP `Hom(frame,frame)`. The per-frame
displacement (velocity) IS such a map; a continuous parameter is admissible
there, "its observable always the STEPPED (integer-k) rendering". So we add
precision to the CROSS-FRAME OFFSET as a FINER-UNIT INTEGER (offset × S).

## Hypothesis (two-sided)

- **H-CONFIRM:** sub-cell cross-frame registration of the tracked ball's grey
  patch recovers a nonzero ∝-correct (positive/downward, constant-to-dispersion)
  acceleration on the real clip — in the finer unit — where the integer-cell
  centroid floored (148000's a=0). Precision in the cross-frame offset
  (invariant-clean) succeeds where in-frame resolution (147000) and aperture
  (148000) could not.
- **H-DEGRADE:** the ball's real patch is too unstable across frames (appearance
  change / motion blur / ruler occlusion) or the true curvature over the short
  trackable window is below registration precision, so the finer-unit curvature
  still floors. Then: isolate WHY with an IDEAL sub-cell oracle (a real parabola
  rendered at KNOWN sub-cell displacement), separating "registration can't" from
  "the real patch is too poor", and name the next wall.

## The statistic, exactly

`accel_coeff = coeffs[1][0]` (the constant 2nd-difference, the acceleration) read
from the minted `latent:time` `LatentDimension` on the GRAPH, after ingesting the
finer-unit INTEGER position stream as a `motion_seq_robust` Observation and
running the seeded `run_rules` fixpoint. Read in FINER units (1/S cell). Judged
by the COEFFICIENT, not the status flip (147000's hard lesson).

## Declared resolution residuals (§13 — fall out, not tuned)

- `S = 10` — the finer unit (1/10 cell): the registration's sub-cell step. A
  DECLARED residual like `block`/`k`, NOT a tuned witness tolerance. The witness's
  tolerance still falls out of integer bit-costs unchanged (no tolerance added).
- `SEARCH_CELLS = 3` — residual half-window (±cells), absorbing carve-anchor
  noise; the registration total is independent of the coarse anchor's noise so
  long as the true residual is within ±SEARCH_CELLS.
- The registration template = the `count` brightest window pixels (count from the
  carve — falls out, no tuned threshold); the window half-extent = ceil(√count)+2.

## Decision rule

- CONFIRM iff ≥1 real config recovers `accel_coeff` that is nonzero and positive
  (downward) with `status==time_inferred`, AND the integer-centroid readout
  floors on ≥1 config (the wall exists). A null (no positive real accel on any
  config) is a DEGRADE, recorded as such (xfail with the measured reason), and
  the ideal oracle must still recover the known accel_fine (chain is correct).
- The ORACLE control (deterministic) MUST recover `accel_fine == a_cell*S`
  while the integer centroid on the same parabola floors — else the chain is
  wrong and no real verdict is trustworthy.

## Controls (must all hold)

- const-velocity (sub-cell) → order-1 not 2 (no manufactured curvature).
- static → mints nothing; random/noise → floors (no confabulated order-2).
- ideal sub-cell oracle → recovers the known accel_fine.
- §9 byte-identity: the coarse integer-cell path is UNCHANGED (new mechanism in
  NEW files only, default OFF); existing carve/physics outputs byte-identical.

## Invariant discipline (a violation FAILS the rung)

NO float in any in-frame coordinate. The carve centroid enters only via
`round(...)` (coarse integer anchor). The bilinear upsample interpolates grey
VALUES inside the cross-frame comparator (not a coordinate). The emitted offsets
and cumulative positions are INTEGERS in finer units. Audited by grep of the diff
and by a graph-read gate assertion (`test_no_in_frame_coordinate_is_a_float`).

## Prediction, in advance (with provisos)

I predict the ORACLE chain confirms (a large clean textured ball, anti-aliased
sub-cell render → registration → witness must recover `accel_fine=2`). For the
REAL clip I predict a MODEST-probability CONFIRM: the ball is large (~25 cells,
~500 px) so registration has ample texture, and the float-centroid 2nd-difference
mean over the workable window was ≈0.4 cell/f² (≈4 finer units) — above the ~1
finer-unit registration noise, so a positive accel_fine is plausible. **Proviso
that would break it (and what it would teach):** if the ball's appearance changes
frame-to-frame (motion blur as it accelerates, ruler markings crossing it), the
masked-template SAD registers on the WRONG feature and the finer-unit d2 scatters
→ DEGRADE, and the wall is patch-stability at real slow-mo, not registration
precision (the oracle would still confirm). If the DEGRADE is instead because the
window is genuinely near-constant-velocity (curvature ≈ 0 over ~6 frames), the
wall is trackable-window length, pointing at the aperture-safe-resolution route
to hold a longer run.

## Engine provenance

`engine 64dbce1e7f47 @ .../runners/dsl/python/substrate_rs/_native.abi3.so
[shared build — Rust source identical]`. NO Rust built (the finer-unit integer
stream feeds the existing `robust_order` `&[Vec<i64>]` witness unchanged);
`source_match == shared`. Oracle 222/0 BEFORE (recorded in RESULTS).
