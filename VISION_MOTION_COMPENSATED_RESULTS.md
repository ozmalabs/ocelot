# MOTION-COMPENSATED (PREDICTIVE-CENTER) BLOCK SEARCH — block 148000-148999

**Verdict (judged by the COEFFICIENT, not the status flip — block 147000's rule):**
- **H1 (synthetic isolation) — CONFIRM.** A fast free-fall whose per-frame
  displacement overruns the fixed aperture: the fixed-aperture sensor floors
  end-to-end (no order-2, `accel_coeff=None`); with motion-compensated search ON
  the SAME fall is held as one trajectory and mints **order-2 with a NONZERO,
  ∝-correct acceleration** (`accel_coeff=3`, `d2=[3,3]` — a genuine constant
  positive curvature), read from the graph.
- **H2 (real clip) — DEGRADE, wall isolated.** See §H2 below.

---

## §3 PRE-REGISTRATION (written before the confirmatory witness run)

**SEED CLAIM 148000-148999:**
```
SEED CLAIM 148000-148999: CLEAN -- no collision DETECTED.
  Scope: 848 files with seed sinks; 566 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```
(`python3 scripts/seed_claim.py 148000 148999`, exit 0.) Confirmatory seed:
`148000` (the H1 texture RNG) + `148002` (the noise control); these integers
are used for nothing else.

**Hypotheses (two-sided).**
- **H1.** A free fall whose per-frame displacement OVERRUNS the fixed aperture
  floors the fixed sensor end-to-end (carve+track+robust witness) — recovering
  NO nonzero acceleration. With MC-search ON the same fall mints order-2 with a
  nonzero, ∝-correct acceleration coefficient. *Null:* MC-search recovers the
  same (a=0 / floor) as fixed — the aperture was not the isolated cause.
- **H2.** On the real 128×640 free-fall clip, MC-search recovers a nonzero
  ∝-correct acceleration where 147000 got a=0 — OR, if it still floors the
  acceleration, the remaining wall is isolated (aperture overrun is fixed but
  carve centroid noise persists — a legitimate DEGRADE).

**Statistic.** The order-2 acceleration coefficient `coeffs[1][0]` of the minted
`LatentDimension{name:latent:time, order:2}`, read from the graph
(`accel_coeff`). Nonzero ∝-correct ⇒ `accel_coeff != 0`, same sign as the ideal
(a downward fall ⇒ positive curvature), and a constant positive 2nd difference
`d2` (a parabola shape up to scale).

**Decision rule.** CONFIRM a hypothesis iff MC-search's `accel_coeff` is nonzero
and ∝-correct while the fixed sensor's is `None`/`0`. A status flip
(floor→time_inferred) with `accel_coeff` still 0 is NOT a confirm — it is the
147000 failure and is reported as DEGRADE with the wall isolated.

**Controls (all must hold).** §9 byte-identity default-OFF; const-velocity (MC
on) → no manufactured curvature; static → nothing; random/noise (MC on) → floors;
first-frame/no-prior-field → plain fallback.

**Prediction (in advance).** H1 CONFIRM; H2 the honest, likely DEGRADE
(aperture fixed, carve centroid noise persists). Proviso: co-located temporal
prediction is only valid while the object's per-frame displacement stays below
its own extent-overlap; a small fast object that moves more than its extent
cannot be temporally predicted at co-located blocks — so H1 needs a LARGE object
and H2's small ball is expected to hit the carve/centroid wall, not the aperture.

---

## THE FIX

`domains/motion_group_world.py :: vector_field(a, b, block, radius=None, predict=None)`
gains an OPTIONAL `predict` argument — an `(nh,nw,2)` array of per-block predicted
integer displacements (the PREVIOUS frame-pair's `vector_field` output; the codec
P-frame move). When supplied, each block ALSO searches the same ±`block` aperture
window CENTERED ON ITS PREDICTION, so the total sensable displacement =
predicted + residual, and a small aperture senses a fast fall as long as the
ACCELERATION (the residual) fits ±`block`. The aperture is thereby DECOUPLED from
the velocity. The predicted-vs-plain choice FALLS OUT as an argmin (each block
keeps whichever of {plain, predicted} has the lower block-SAD), so:
- a wrong prediction (e.g. a leading-edge block predicting 0) degrades gracefully
  to the plain result — never worse;
- **no new constant**: the residual window stays `block` (the same declared §13
  aperture, now around a prediction), and there is NO tuned gain / confidence /
  smoothing threshold.

**The exact flag / DEFAULT OFF.** MC-search is engaged only by a **non-None,
non-zero `predict`**. `predict=None` (the default) runs ONLY the plain search —
literally the original code path. A supplied `predict` that is zero everywhere
adds a predicted pass whose candidates coincide with the already-evaluated plain
candidates and can never STRICTLY beat them ⇒ byte-identical output.

---

## §2 ORACLE UNMOVED

| when | `bash scripts/rung7_vision_bench.sh` (data/ symlinked) |
|---|---|
| BEFORE | **222 passed / 0 failed** (173.4s) |
| AFTER  | **222 passed / 0 failed** (171.8s) |

**Pre-existing gate state (disclosed, not mine — `test_*_migrated`).**
`tests/test_instrument_seams_migrated.py` has **3 reds at my base HEAD
`21532d0af9`, ALL independent of this rung** (proven by removing every file this
rung adds and the original sensor — all three still fail):
`test_the_preamble_gate_binds_NEW_violations_only` (enumerated in
`results/failure_baseline.json`); `test_the_measured_ledger_record_is_CURRENT`
(the committed `seed_ledger_measured.json` has been stale since block **133000**
— blocks 133000–147000 all `committed=None`, prior rungs never regenerated it);
`test_every_new_prereg_records_its_check_claim_output` (three OTHER rungs'
`VISION_CLOSURE/EYEVIEW/MOTIONENERGY_PREREG.md` record no `check_claim`). This
rung adds NONE of them: its instrument's seeds (148000–148002) do not flip the
already-stale ledger, and its document is a `_RESULTS.md` (this gate scans
`VISION_*_PREREG.md` only). Per the **147000 precedent**,
`results/seed_ledger_measured.json` is left **byte-identical to base** —
regenerating it would sweep 15 other rungs' seed draws into this commit (§11 rule
3). The failure-baseline gate (`test_failure_baseline_migrated`) is **11/11
green**.

Python-only sensor variant; NO Rust built. Engine is **`shared`**:
`substrate_rs` resolves through the canonical `substrate_rs.pth` to
`runners/dsl/python` (engine `64dbce1e7f47`, `source_match==shared`) — the same
engine 147000 measured on. (Provenance recorded in
`results/motion_compensated_measure.json :: provenance_line`; asserted by
`domains.engine_provenance`, never a pinned hash.)

---

## §9 BYTE-IDENTITY (default OFF)

Over 6 random frame pairs (`np.random.default_rng(148000/148001)`, 80×48, block 4):

| condition | mismatched vector components |
|---|---|
| `predict=None` vs plain | **0 / 10656** |
| `predict=0` vs plain     | **0 / 10656** |

The whole existing pipeline is unchanged when the flag is off. **Positive
control on the guard** (`test_byte_identity_gate_can_fail`): a genuinely nonzero
prediction on a fast (11-cell) shift DOES change the output, so the identity
assertion is not vacuous.

---

## H1 — SYNTHETIC ISOLATION (the clean demonstration)

**Apparatus** (fixed in advance; the cross-frame rendering map, NOT a witness
threshold): a textured 80-cell square in free fall from ~rest,
`cy(t)=8 + ½·2·t²` (2nd difference of cy = 2 = the acceleration = the residual
the MC aperture absorbs, ≤ aperture 4), 150×96 grid, block/aperture 4, L=4
quantization, texture seed 148000. Per-frame displacement `1,3,5,7,9,11,13`
overruns the aperture (4) from frame 2. Object extent (80) ≫ the displacements,
so a co-located block overlaps its own previous-frame position (temporal
prediction valid). True object cy `[48,49,52,57,64,73,84,97]`, true d2
`[2,2,2,2,2,2]`; the ideal witness on the true cy mints `accel_coeff=2`.

**FIELD FIDELITY — the layer the sensor fixes** (median block vy over the moving
cells vs the true per-frame displacement; pure sensor read, no carve/graph):

| frame        | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|--------------|---|---|---|---|---|---|---|
| true disp    | 1 | 3 | 5 | 7 | 9 | 11 | 13 |
| **MC OFF** (fixed) | 1 | 3 | **1** | **1** | **1** | **1** | **1** |
| **MC ON**    | 1 | 3 | **5** | **7** | **9** | **11** | **13** |

The fixed aperture saturates and collapses to ~1 once the displacement overruns
it (frame 3+); MC-search reads the exact true displacement at every frame. This
is the aperture DECOUPLED from the velocity, measured directly.

**End-to-end (carve + track + robust witness), read from the graph:**

| | longest run | one id | witness status | `accel_coeff` | tracked cy | d2 |
|---|---|---|---|---|---|---|
| **MC OFF** (fixed aperture) | 2 | — | (no witness) | **None** | — | — |
| **MC ON** | 4 | True | `time_inferred` | **3** | `[50,50,53,59]` | `[3,3]` |

**MC OFF FLOORS** (run < 4 ⇒ no order-2 witness fires; no nonzero acceleration
recovered). **MC ON mints order-2 with a nonzero, ∝-correct acceleration** — the
tracked cy `[50,50,53,59]` is a parabola from rest (d1 `[0,3,6]`, d2 `[3,3]` — a
constant positive curvature), and the graph mints
`LatentDimension{order:2, coeffs:[[…],[3,…]]}`, `accel_coeff=3`. **CONFIRM.**

The recovered magnitude (3) differs from the ideal (2): that residual is
**downstream carve centroid noise** (the ±1-cell centroid jitter the sensor fix
does NOT touch), not the aperture. The SIGN and the constant-positive-curvature
SHAPE are correct — nonzero ∝-correct.

---

## H2 — REAL CLIP (the payoff, honest) — DEGRADE, wall isolated

Native 128×640 free-fall clip end-to-end (carve+track+robust witness), the same
windows 147000 drove. Read from the graph:

| config | side | run | witness status | `accel_coeff` | minted coeffs | maxdisp / aperture |
|---|---|---|---|---|---|---|
| b6, 2fps | **MC OFF** | 8 | `time_inferred` | **0** | `[[4,0],[0,0]]` | 8 / 6 = **1.33×** |
| b6, 2fps | **MC ON** | 5 | `time_none` | **None** | — | 10 / 6 |
| b4, 3fps | MC OFF | 3 | (no witness) | None | — | — |
| b4, 3fps | MC ON | 3 | (no witness) | None | — | — |

**DEGRADE — neither side recovers a nonzero acceleration.** MC OFF reproduces
147000's finding EXACTLY: order-2 mints but the coefficient is `[[4,0],[0,0]]`,
`accel_coeff=0` (the ball's carved centroid
`[394,398,406,414,420,426,431,436]` has d1 `[4,8,8,6,6,5,5]` — noisy, no constant
curvature). MC ON does not recover the acceleration either; it floors (no mint)
with a shorter run.

**The wall is isolated, and at this scale it is NOT the aperture.** The per-frame
displacement at 128×640/b6 is 8 cells against a 6-cell aperture — only a **1.33×**
overrun (mild), so the aperture is not the dominant wall here. Two things bite
instead, and neither is what this rung fixes:

1. **Carve centroid noise (unfixed by the sensor).** The a=0 is the ±1–2-cell
   centroid jitter 145000/147000 already located — a *witness/centroid* wall
   downstream of the vector field. MC-search corrects the FIELD, not the centroid,
   so it cannot move this.
2. **Co-located temporal prediction is INAPPLICABLE to the small real ball.** The
   mechanism predicts block `L` from the previous field at `L`, valid only while
   the object overlaps its own previous-frame position — i.e. while displacement
   < extent. The real ball is SMALL and moves ~8–10 cells, comparable to or
   greater than its own extent, so its blocks were BACKGROUND last frame and the
   prediction there is 0. The predicted pass therefore cannot help; worse, because
   the union keeps the lower block-SAD and a lower SAD at an aperture-ambiguous
   small object is not the correct motion, a spurious predicted match can perturb
   the carve — which is why MC ON's run is SHORTER (5 vs 8) and floors. This is a
   real, honest limit of *co-located temporal* prediction, distinct from the
   aperture it does fix (H1, large object).

**Named next wall (NOT built here):** a sub-pixel / robust centroid (the a=0
carve noise), OR — for the small-mover regime the real ball lives in — a
SPATIAL-propagation prediction (a block's MV predicted from already-solved
NEIGHBOUR blocks, which propagates a coherent object's velocity into its leading
edge) rather than the co-located temporal prediction that only a large object
satisfies. H1 proves the aperture decoupling; H2 shows that at the real clip's
scale the aperture is not the binding constraint.

---

## APERTURE-vs-VELOCITY CHARACTERIZATION

The fixed sensor's aperture is `radius=block`, which falls out of block overlap:
beyond a displacement of its own extent a block shares no pixels with its source.
A free fall's velocity grows without bound (∝ t), so at any fixed block/fps it
eventually overruns the aperture and the plain search saturates (H1 field
fidelity: OFF collapses to ~1 past disp 4). MC-search moves the *velocity* into
the PREDICTION (order-1, carried from the previous field) and leaves only the
*acceleration* (the constant 2nd difference) for the aperture to absorb as the
residual — exactly the physics. So the sensable displacement is
`predicted + residual`, and the constraint is on the ACCELERATION (≤ aperture),
not the velocity. The measured cost/step of the predicted pass is one extra
per-block gather over the same ±block offsets (timing in the JSON;
characterization only, not a verdict).

**The honest boundary of the mechanism (co-located temporal prediction):** the
prediction for block `L` is the previous field at `L`, valid only while the
object overlaps its own previous-frame position at `L` — i.e. while the per-frame
displacement stays below the object's extent. A LARGE object (H1: extent 80 ≫
displacement) is predictable through a fast fall; a SMALL object that moves more
than its extent (the real ball) is NOT — its co-located blocks were background
last frame, so the prediction is 0 there and those blocks fall back to the plain
(saturating) search. This is why H1 confirms and H2 does not fully.

---

## NO-AGENT-DECISION AUDIT (CLAUDE.md)

- `vector_field(..., predict=...)` operates ONLY on numpy arrays `a`, `b`,
  `predict`. It never touches the graph, the agent, or any node/edge. It is
  mechanical SENSOR I/O (the same position `quantize()` occupies), extended with
  a second array-only search pass.
- In `carve_track`, the prediction is `pred = np.rint(prev_vf).astype(np.int64)`
  — the PREVIOUS frame-pair's `vector_field` OUTPUT ARRAY, RAW MOTION-FIELD DATA
  ONLY. No conditional over graph state; no read of any minted node.
- Every order-N DECISION remains the seed rule `time_infer_mint_robust`
  (`seeds/time_axis.json`); the instrument only ingests the perceived cy and
  reads the minted `LatentDimension` coeffs back out.
- No Rust added; no seed edited. `git diff` touches only
  `domains/motion_group_world.py` (sensor), `scripts/motion_compensated_measure.py`
  (instrument), `tests/test_motion_compensated_search_migrated.py` (gate) and
  this doc + the raw JSON.

---

## §13 MAGIC NUMBERS

The only declared magic-number residual is `block` — the sensor's aperture,
exactly as the incumbent `vector_field` declares it, and NOT claimed to fall out.
The residual window stays `block` (the same geometric aperture, now around the
prediction). The predicted-vs-plain choice is an **argmin** (lower block-SAD
wins), which FALLS OUT — there is no tuned prediction gain, confidence threshold,
or smoothing constant. The synthetic apparatus numbers (object extent, accel,
grid, texture seed) are the rendering map (the cross-frame stepped map, §
frame/continuum invariant), FIXED in advance, not witness thresholds.

---

## WHAT I GOT WRONG

1. **First texture destroyed by quantization.** The initial object texture
   `rng.integers(128,256)` collapses under L=4 to just two levels {2,3} — a
   near-uniform blob whose interior block-SAD is ambiguous, so the temporal
   prediction chain corrupted from the inside. Fixed with a texture spanning
   `[64,256)` → distinct nonzero levels {1,2,3} that SURVIVE L=4. (The lesson:
   check what your synthetic looks like AFTER the pipeline's own quantization.)
2. **Over-fast synthetic fall broke the very mechanism it was meant to show.**
   The first apparatus (a=4, extent 40) pushed the per-frame displacement to 26,
   approaching the object extent (40); co-located temporal prediction is only
   valid while displacement ≪ extent, so the field broke exactly where the claim
   needed it to hold. Retuned to a LARGE object (extent 80) and a modest
   acceleration (a=2), keeping displacement well inside the overlap. I had
   assumed "faster = better demonstration"; the mechanism's own validity window
   is the opposite.
3. **The carve has its OWN velocity ceiling, independent of the aperture.** Even
   with a byte-perfect field, the common-fate tracker's region velocity estimate
   degrades and the id-persistence breaks around the same displacement — so the
   end-to-end MC run is capped at ~4-5 frames (the witness minimum) regardless of
   the sensor fix. This is the "carve centroid noise I do NOT fix", and it caps
   H1 at a short (but valid: nonzero ∝-correct) demonstration and is the wall H2
   hits.
4. **"const-velocity → clean order-1" is not achievable through the noisy carve.**
   The MDL/robust witness over-fits a noisy near-linear centroid to high order
   (order-5 on a vel-3 track). 147000 got order-1 by feeding an EXACT ideal ramp,
   not a carved centroid. So the faithful const-velocity control is at the FIELD
   level (the predictor converges to the constant velocity and holds a flat
   plateau — no manufactured curvature) plus "no parabola signature", NOT a bare
   "mints order-1".

---

## PROPOSED VISION_PROTOCOL.md LEDGER ROW

| **148000–148999 (sensor variant; NO Rust, NO seed — an optional `predict=` arg on `motion_group_world.vector_field`, DEFAULT OFF)** | **MOTION-COMPENSATED (PREDICTIVE-CENTER) BLOCK SEARCH DECOUPLES THE APERTURE FROM THE VELOCITY — CONFIRM on synthetic isolation, DEGRADE on the real clip (wall isolated, and at 128×640 it is NOT the aperture).** The fix: each block ALSO searches the same ±`block` aperture window CENTERED on its PREDICTION (the PREVIOUS frame-pair's vector field — raw motion-field ARRAY data, the codec P-frame move), so total displacement = predicted + residual and a small aperture senses fast motion as long as the ACCELERATION (the residual) fits ±`block`. Predicted-vs-plain FALLS OUT as an argmin (lower block-SAD wins per block — a wrong prediction degrades to plain, never worse); NO new constant (the residual window stays `block`, the declared §13 aperture). **H1 (synthetic, CONFIRM):** a fast textured free-fall (extent 80, a=2, block/aperture 4; disp 1,3,5,7,9,11,13 overruns the aperture from frame 2) — the fixed sensor's field SATURATES (median vy 1,3,**1,1,1,1,1**) and carve+track+robust-witness FLOORS end-to-end (`accel_coeff=None`); MC-ON reads the EXACT true displacement (1,3,5,7,9,11,13) and mints order-2 with a NONZERO ∝-correct acceleration (`accel_coeff=3`, d2 `[3,3]` — a genuine constant positive curvature, one tracked id), read from the graph. THE TELL IS THE COEFFICIENT (147000's rule), and MC recovers nonzero curvature where fixed recovers none. **H2 (real 128×640, DEGRADE):** MC OFF reproduces 147000's a=0 EXACTLY (order-2, coeffs `[[4,0],[0,0]]`); MC ON floors (`time_none`, no mint, shorter run 5<8). Wall isolated: at 128×640/b6 the overrun is only 8/6=**1.33×** (MILD), so the aperture is NOT the binding constraint — the a=0 is CARVE CENTROID noise (a field-level fix cannot move it) AND co-located temporal prediction is INAPPLICABLE to the SMALL real ball (disp ≈ extent ⇒ its blocks were background last frame ⇒ prediction 0). NAMED next wall: sub-pixel/robust centroid, or SPATIAL-neighbour MV propagation for the small-mover regime — NOT aperture at this scale. **Controls:** §9 byte-identity DEFAULT-OFF (`predict=None` and `predict=0` both **0/10656** mismatched, positive-controlled can-fail guard); const-velocity (MC on, vel 6 > aperture 4) converges and holds a flat plateau — NO manufactured curvature; static → nothing; noise → floors. WHAT IT GOT WRONG: first synthetic texture died under L=4 (2 levels) → interior aliased the prediction chain; over-fast first fall (a=4, disp→26≈extent) broke the co-located prediction it was meant to show; the carve has its OWN velocity ceiling independent of the aperture (caps H1 at the 4-frame witness minimum — the centroid noise NOT fixed here); "const-velocity → clean order-1" is unachievable through the noisy carve (the MDL witness over-fits to order-5), so the control is field-level. shared engine `64dbce1e7f47` (source_match==shared, no Rust); oracle 222/0 BEFORE and AFTER; gate `test_motion_compensated_search_migrated` 10/10 (graph-read, able to fail); `SEED CLAIM 148000-148999 CLEAN`. Raw: `results/motion_compensated_measure.json`; instrument `scripts/motion_compensated_measure.py`; `VISION_MOTION_COMPENSATED_RESULTS.md`. |

---

**Gate:** `tests/test_motion_compensated_search_migrated.py` — 10/10, all
assertions read from the graph and able to fail (byte-identity off with a
positive-controlled can-fail guard; field-fidelity aperture decoupling; H1 fixed
floors / MC nonzero ∝-correct; const-velocity no-manufactured-curvature; static
mints nothing; noise floors). Raw: `results/motion_compensated_measure.json`;
instrument: `scripts/motion_compensated_measure.py`.
