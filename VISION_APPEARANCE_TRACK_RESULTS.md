# RESULTS — APPEARANCE-TRACKED STABILITY -> REAL-VIDEO FREE-FALL PHYSICS (block 151000-151999)

**Branch:** `gamma-substrate/appearance-track-stability` (worktree off HEAD
`9cc4393c60`). NOT merged to main. Python-only rung; engine SHARED (Rust source
byte-identical, no rebuild).

## SEED CLAIM 151000-151999 CLEAN

`python3 scripts/seed_claim.py 151000 151999` -> CLEAN; `check_claim(151000,
151999)` -> `ok=True`. Verbatim output recorded in
`VISION_APPEARANCE_TRACK_PREREG.md` (committed before the confirmatory run). This
rung draws NO seed (deterministic decode/carve/track/witness; synthetic controls
reuse already-burned 149xxx texture seeds).

## ENGINE (§10)

```
engine 64dbce1e7f47 @ .../runners/dsl/python/substrate_rs/_native.abi3.so
  [shared build from canonical tree — Rust source identical]
```

`diff -rq runners/dsl/src <canonical>/runners/dsl/src` is EMPTY across the whole
rung. No `.rs` touched, so the shared build is legitimate (§10.1 rule 4) and no
`engine_build.sh` was required. Both oracle runs used this engine.

## ORACLE (§2) — UNMOVED

| when | `bash scripts/rung7_vision_bench.sh` |
|---|---|
| BEFORE (HEAD `9cc4393c60`, `data/` symlinked) | **222 passed, 0 failed** (171s) |
| AFTER  (this rung's tree) | **222 passed, 0 failed** (172s) |

Python-only, engine shared — the AFTER run is on the SAME binary; no rebuild.

## THE CLIPS

- **PRIMARY (block-150000's identified clean clip):** `cand2_1yT0hxplVBg.mp4` —
  bright yellow tennis ball on black, static camera, no ruler. Re-acquired fresh
  via `yt-dlp` (1280x720@30fps, 603 frames). Two grey frames saved as PNG
  (`results/appearance_track_frames/cand2_frame_*_grey_160x90.png`; the clip mp4
  itself is under gitignored `naming_corpus_local/`). **It is a slow-motion
  BOUNCE CLOSE-UP** (the ball is a large deforming yellow blob near a surface),
  NOT a sustained vertical drop.
- **SECONDARY (one principled longer-drop clip, per prereg H-DEGRADE-a licence):**
  `cand3_vJEul_K8prU.mp4` — "Slow motion of a falling ball with horizontal
  velocity" (928x720@24fps, 135s). A COMPACT bright ball in PROJECTILE motion
  (gravity only -> the vertical component is genuine free fall) translating
  across a dark background, static camera. Acquired by principled description
  AFTER the primary clip's free-fall phase proved footage-limited; reported
  whether or not it passes (it passes) — no try-until-pass.

## H1 (MECHANISM) — CONFIRMED: appearance holds ONE trajectory far beyond the id tracker

An appearance-tracked template (grey-patch normalized cross-correlation, `argmax`
association — NO threshold) holds the object as ONE trajectory where the current
motion/overlap/velocity tracker (Rust `segment_motion_and_track`, chained by
Region id) fragments it.

**PRIMARY clip (cand2), longest continuous tracked run:**

| framing | RUST-ID run | non-ground ceiling | APPEARANCE run |
|---|---|---|---|
| trial2 160x90 b4 | **3** | 75 | **75** |
| trial2 160x90 b3 | 6 | 69 | **69** |
| hi 214x120 b5 | 3 | 60 | **60** |
| early 160x90 b4 | 3 | 75 | **75** |

The id run fragments to 3-6 frames; appearance holds the FULL non-ground ceiling
(60-75 frames). The id run is also **cross-process UNSTABLE** (a HashMap artifact
the protocol names): my probe measured RUST-ID=3 on trial2 where block-150000
measured 5, on the identical params — because carve Region ids depend on HashMap
iteration order. Appearance chains by pixel appearance, not id, so it is
**cross-process stable** by construction.

**SECONDARY clip (cand3):** appearance run 17-35 vs id run 2-14 across framings
(table under H2). H1 holds on both clips.

## H2 (PAYOFF) — REAL-VIDEO FREE-FALL PHYSICS LANDS on the longer-drop clip

`physics_test` (imported UNCHANGED from 149000/150000) on the longest
strictly-downward monotonic sub-run (the free-fall phase, excluding the bounce
impact): P1 (order-2 + downward sign) & P2 (two overlapping windows agree in
sign — 149000's tolerance-free replication test).

**SECONDARY clip (cand3) — the free-fall phase and its physics verdict:**

| framing | id free-fall | APPEARANCE free-fall | coeff | P1 | P2 | P3 | **PASS** |
|---|---|---|---|---|---|---|---|
| f1 160x124 b4 | 6 | **21** | 2 | ✓ | ✓ | ✓ | **TRUE** |
| f1.5 160x124 b4 | 10 | **22** | 1 | ✓ | ✓ | ✓ | **TRUE** |
| f1.25 160x124 b4 | 11 | **17** | 1 | ✓ | ✓ | ✓ | **TRUE** |
| f1 200x155 b5 | 11 | **16** | 2 | ✓ | ✓ | ✓ | **TRUE** |
| f1 128x99 b4 | 8 | **15** | 1 | ✓ | ✓ | ✓ | **TRUE** |
| f0.75 160x124 b4 | 1 | 4 | — | — | — | — | (free-fall <6) |

**Cross-process stability of the headline (f1 160x124 b4):** 3 fresh processes
(random `PYTHONHASHSEED`) each gave appearance run=23, free-fall phase 17-21
frames, and **physics PASS=True** every time. The verdict is id-independent.

**=> REAL-VIDEO FREE-FALL PHYSICS LANDS (CONFIRM, n=1 longer-drop clip):** the
full pipeline recovers a STABLE single-sign acceleration through the free-fall
phase, passing 149000's replication test, on five independent framings.

**PRIMARY clip (cand2) — H2 DEGRADE-a (footage), precisely named:** appearance
HOLDS the ball (60-75 frames), but its free-fall (monotonic-down) phase is only
4-8 frames, and where it reaches the witness floor (b3, 8 frames) the recovered
coefficient is **0 / None** — the phase is near CONSTANT VELOCITY (a bounce
close-up in extreme slow-mo has a short, low-curvature approach; the acceleration
is below the noise floor). Physics does NOT land on cand2. This is the honest
H-DEGRADE-a of the prereg: the wall on the PRIMARY clip is **clip choice** (need
a genuine drop), which the secondary clip supplies.

## CONTROLS (gate — all pass)

- **const-velocity** -> graph mints order-1, NOT order-2 (no manufactured curvature);
- **static** -> no order-2;
- **noise** -> no order-2 (floors);
- **two disjoint objects** -> `track_multi` keeps two SEPARATE runs (cx=20 and
  cx=68 held throughout — appearance does NOT merge distinct objects);
- all read the GRAPH-minted order (`fw.discover_order` -> `latent:time`), never an
  exact d2.

## BYTE-IDENTITY-OFF (§9) — PROVEN

`appearance_track.longest_run(track, enabled=False)` returns EXACTLY
`subcell_crossframe_measure.longest_run_indexed(track)` — proven two ways:
1. Gate `test_byte_identity_off_equals_existing_longest_run` asserts `off == ref`
   element-for-element on a fixture with id runs, a break, and a None gap.
2. Every real-clip measurement asserts inline that the OFF run equals
   `longest_run_indexed(track)` on the SAME carved regions before proceeding.

The appearance code path never executes when `enabled=False`; the existing
carve+track trajectory reproduces exactly.

## INVARIANT AUDIT (§ frame/continuum) — CLEAN

- Patches are read at the INTEGER centroid `int(round(cy))`, `int(round(cx))`
  (`grey_patch`). Gate `test_invariant_patch_read_at_integer_centroid` proves any
  float centroid within ±0.5 of an integer reads the SAME patch as that integer
  (the in-frame coordinate is stepped).
- NCC is the ONLY continuous quantity and it is a CROSS-FRAME comparison — it
  lives in `Hom(frame, frame)`, the admissible home of the continuum ("bins
  propose, continuous decides").
- The association layer writes NO float into any in-frame coordinate: the run
  carries the carve's OWN `cy/cx` unchanged (gate
  `test_invariant_run_passes_through_carve_coords`), reaching the witness only via
  `round()`, exactly as the existing pipeline.

## MAGIC-NUMBER AUDIT (§13)

- **Association acceptance threshold: NONE.** The association is `argmax NCC` —
  best-correlation FALLS OUT; there is no tuned constant to accept/reject a match.
- **Declared residuals** (like `block`/`S`/`k`): patch half-size `HALF=3`; reused
  `S=10`, `SEARCH_CELLS=3` from the imported 149000 registration; the witness
  tolerance still falls out of integer bit-costs inside the unchanged
  `physics_test`. None was tuned against the answer.

## NO AGENT DECISION IN PYTHON (audit)

`domains/appearance_track.py` reads ONLY pixel patches (`grey_patch`) + the
carve's own centroid/count and returns an `argmax` (association) — no `if`/`else`
over graph state, no rule engine, no agent state. It is the mechanical peer of
the overlap / nearest-centroid / velocity-predictive phases already inside
`segment_motion_and_track`. Every order-N verdict stays the seed rule inside
`graph_mint` / `fw.discover_order`.

## FRESH-PROCESS GATE COUNT

`tests/test_appearance_track_migrated.py` — 8 assertions (H1, four controls,
byte-identity-off, two invariant guards). Run in **5 fresh `python3 -m pytest`
processes** (random `PYTHONHASHSEED`): **5/5 processes, 8/8 each.** (Carve ids are
a cross-process HashMap artifact; the gate's verdicts do not depend on them.)

## WHAT I GOT WRONG

1. **I predicted the PRIMARY clip would most likely DEGRADE-b (perception
   elsewhere). It DEGRADEd, but as DEGRADE-a (footage):** cand2's free-fall phase
   is near CONSTANT VELOCITY (coeff 0/None), so the wall there is the bounce
   close-up's short low-curvature approach, not a perception bug downstream. My
   proviso ("if the monotonic-down phase is <6, DEGRADE-a") was the one that
   fired.
2. **I over-attributed the physics win to appearance alone.** On the WELL-SAMPLED
   cand3 framings the id run ALSO reaches the 6-frame witness floor (id free-fall
   6-11) and 149000's SUB-CELL registration ALSO passes physics on it (its
   integer cy is a constant 4.0/frame — the acceleration is sub-cell). So on
   those framings appearance is NOT the sole enabler. Appearance's MEASURED
   contribution is a **2-6x longer, cross-process-STABLE trajectory**, decisive
   where the id run fragments below the floor (cand2 id=3 vs appearance=75; cand3
   f0.75 id free-fall=1 vs appearance run=17). The clean division of labour: the
   earned appearance/quanta layer PROPOSES a long stable trajectory; the strong
   continuous cross-frame registration DECIDES the acceleration ("bins propose,
   continuous decides"). The headline "real-video free-fall physics lands" is
   solid; "only appearance could land it" is true only on the fragmenting
   framings.
3. **First gate fixture used a sub-cell float acceleration (0.25 cell/f²) that the
   INTEGER-centroid witness cannot resolve into a clean order-2** — the gate reads
   integer centroids (no sub-cell layer), so it needs integer-exact order-N
   positions. Fixed by rendering with integer semi-implicit-Euler physics (`v+=g;
   y+=v`), which gives an exact constant 2nd difference.
4. **Boundary rounding:** `round(40.5)==40` (Python banker's rounding) — a test
   assertion assumed round-half-up. Corrected.

## SCOPE / RESIDUALS (§8)

- **n=1 longer-drop clip.** Synthetic-proven mechanism ≠ benchmark value; both are
  reported. This is a projectile clip — the measured quantity is the VERTICAL
  free-fall acceleration (gravity only acts; horizontal velocity does not enter
  `longest_monotonic_down`, which keys on cy).
- **P3 magnitude is NOT physically calibrated for real footage** — its
  `TARGET_FINE=2` is the synthetic oracle's injected accel; for real video the
  binding criterion is the tolerance-free P1&P2 (order + single-sign
  replication), exactly as 150000 defined it. P3 is reported as corroboration
  only.
- **Not shown:** absolute g in physical units (uncalibrated pixels/frame);
  robustness beyond these framings; any clip with a busy background.

## PROPOSED VISION_PROTOCOL.md LEDGER ROW

```
151000-151999 | APPEARANCE-TRACKED STABILITY LANDS REAL-VIDEO FREE-FALL PHYSICS — grey-patch NCC association (argmax, no threshold) holds the object as ONE trajectory 2-6x longer than the fragmenting/id-unstable motion tracker (cand2 id=3 vs appearance=75; cand3 id=6 vs appearance=23), and the full pipeline recovers order-2 single-sign REPLICATED acceleration through the free-fall phase on a genuine longer-drop clip (cand3 vJEul_K8prU, 5 framings PASS, cross-process stable) — H1 CONFIRM, H2 CONFIRM (n=1 longer-drop; primary bounce-close-up clip is H2 DEGRADE-a, footage). Honest: on well-sampled framings the id run also reaches the 6-frame floor and 149000's sub-cell registration also passes — appearance PROPOSES the long stable trajectory, continuous registration DECIDES g ("bins propose, continuous decides"). Python-only tracker-association sensor (reads pixel patches only, no agent decision); byte-identical when OFF. engine 64dbce1e7f47, source_match=shared (Rust identical, no rebuild); oracle 222/0 BEFORE and 222/0 AFTER; gate tests/test_appearance_track_migrated.py 8/8 in 5/5 fresh processes; SEED CLAIM 151000-151999 CLEAN.
```
