# PRE-REGISTRATION — APPEARANCE-TRACKED STABILITY (block 151000-151999)

**Branch:** `gamma-substrate/appearance-track-stability` (worktree, off HEAD `9cc4393c60`).
Written and committed BEFORE the confirmatory H2 run (§3). NOT merged to main.

## SEED CLAIM 151000-151999: CLEAN

`python3 scripts/seed_claim.py 151000 151999` and `check_claim(151000, 151999)`
both return CLEAN. Recorded verbatim (§3 clause 8):

```
SEED CLAIM 151000-151999: CLEAN -- no collision DETECTED.
  Scope: 852 files with seed sinks; 571 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

This rung draws NO seed (deterministic decode/carve/track/witness; the only RNG
uses are in the imported synthetic controls, which draw already-burned
149xxx/150xxx texture/jitter seeds unchanged).

## ENGINE

```
engine 64dbce1e7f47 @ .../runners/dsl/python/substrate_rs/_native.abi3.so
  [shared build from canonical tree — Rust source identical]
```

Python-only rung. No Rust change is planned (the mechanism is a mechanical
Python tracker-association sensor reading pixel patches). The engine is therefore
SHARED with the canonical tree, legitimately, because the Rust source is
byte-identical (`diff -rq runners/dsl/src` empty). If any `.rs` is touched, the
provenance gate blocks the measurement until `scripts/engine_build.sh` runs.

## HYPOTHESES (two-sided)

- **H1 (mechanism).** An appearance-tracked template (grey-patch normalized
  cross-correlation, `argmax` association) holds the clean tennis-ball clip as
  ONE trajectory **>=6 consecutive frames** where the current motion/overlap/
  velocity tracker (Rust `segment_motion_and_track`, chained by Region id)
  fragments it into short runs. Two-sided null: appearance tracking does NOT
  extend the run beyond the Rust-id run (fragmentation is deeper than
  appearance).
- **H2 (payoff).** With the object held >=6 frames, the full pipeline recovers a
  STABLE single-sign acceleration through the FREE-FALL PHASE (the longest
  strictly-downward monotonic sub-run, excluding the bounce impact), passing
  149000's tolerance-free single-sign replication test. Two-sided null: it holds
  the trajectory but the recovered acceleration fails P1&P2.

## THE STATISTIC (exactly)

- H1: `len(appearance_run)` vs `len(rust_id_run)` — the longest consecutive
  tracked run under each association, on the same per-frame largest-non-ground
  carved regions. H1 passes iff `len(appearance_run) >= 6` AND
  `len(appearance_run) > len(rust_id_run)`.
- H2: the **graph-minted** verdict of `realism_ladder_measure.physics_test`
  on `longest_monotonic_down(appearance_run)`:
  - **P1** (order+sign): full free-fall run mints order-2 with nonzero coeff of
    the DOWNWARD sign (target_fine > 0).
  - **P2** (replication): two overlapping windows (offset by 1 frame) each mint
    order-2 with nonzero coeff and AGREE IN SIGN (the exact tolerance-free test
    that killed 149000).
  - **PASS = P1 & P2.** P3 (magnitude within the falls-out rounding envelope
    TOL_FINE=2) is reported as corroboration only.
  The acceleration coefficient is read from the graph's minted `latent:time`
  LatentDimension — never an exact-d2 assertion (148000's flaky-gate lesson).

## n, FIXED IN ADVANCE

n = 1 clip (the block-150000-identified clean clip `1yT0hxplVBg`), swept over a
small FIXED set of decode framings (150000's trial2 `160x90 b4` + three
neighbours: `160x90 b3`, `214x120 b5`, early-window `160x90 b4`). Framing is
decode choice, not a pass filter — every framing's verdict is reported. This is
n=1 real footage; the mechanism's synthetic gate (H1 on a synthetic
fragmentation-inducing fixture) is the powered, able-to-fail test.

## DECISION RULE

- **CONFIRM (headline: real-video free-fall physics LANDS):** H1 holds AND on at
  least one reported framing H2's PASS (P1&P2) is true through the free-fall
  phase. Reported soberly, n=1 clip.
- **DEGRADE-a (clip choice):** H1 holds (appearance >=6) but the free-fall phase
  (monotonic-down sub-run) is <6 frames on every framing -> the wall is footage
  (need a longer drop). May acquire ONE longer-drop clip by principled
  description and report it whether or not it passes.
- **DEGRADE-b (perception elsewhere):** appearance holds >=6 free-fall frames but
  the recovered accel fails P1&P2 -> isolate where.
- **FALSIFY H1:** appearance tracking does NOT hold >=6 frames -> report why
  (what breaks the template match: scale change / blur / rotation).

## CONTROLS (must all hold)

1. **Const-velocity** synthetic object -> appearance association recovers the
   run but order-1, NOT order-2 (must not manufacture curvature).
2. **Static** -> nothing (no order-2).
3. **Noise** -> floors (no confabulated order-2).
4. **Two disjoint objects** -> two stable trajectories; appearance
   (greedy one-to-one) must NOT merge them.
5. **Byte-identity-off (§9):** `appearance_track.longest_run(track, enabled=False)`
   is byte-identical to the existing `longest_run_indexed(carve_track_indexed())`
   region trajectory on a fixture. (Asserted inline in the measurement too.)
6. **Invariant guard (§ frame/continuum):** no float is written into any in-frame
   coordinate — patches are read at `int(round(cy/cx))`; NCC is the only
   continuous quantity and it is a CROSS-FRAME comparison (Hom(frame,frame)).

## MAGIC-NUMBER AUDIT (§13)

- **Association threshold:** NONE. The association is `argmax NCC` — it FALLS
  OUT (best-correlation). There is no tuned acceptance constant.
- **Declared residuals** (like `block`/`S`/`k`): patch half-size `HALF=3`
  (appearance-template grain); reused `S=10`, `SEARCH_CELLS=3` from the imported
  149000 sub-cell registration; the witness tolerance still falls out of integer
  bit-costs inside `physics_test` (unchanged).

## NO AGENT DECISION IN PYTHON (audit)

The association reads ONLY pixel patches (`grey_patch`) + the carve's own
centroid/count and returns an argmax — no `if`/`else` over graph state, no rule
engine, no agent state. Every order-N verdict stays the seed rule inside
`graph_mint` (`fw.discover_order` / `physics_test`). The tracker-association
sensor is the mechanical peer of the overlap/nearest-centroid/velocity phases
already inside `segment_motion_and_track`.

## PREDICTION (stated in advance, with provisos)

I predict **H1 CONFIRMS strongly** — the pilot probe already showed the Rust-id
run fragmenting to 3-6 frames while appearance holds 60-75 (the full
non-ground-region ceiling); the id-run length is itself cross-process-unstable
(a HashMap artifact), which appearance sidesteps by construction.

For **H2 I am genuinely uncertain** and predict DEGRADE-b is most likely: this
clip is a slow-motion tennis-ball BOUNCE close-up (a large deforming yellow blob
near a surface), not a long clean vertical drop. The free-fall (monotonic-down)
phase may be short, and impact deformation + the ball nearly filling the frame
may inject centroid noise that breaks the single-sign replication test even with
the trajectory held. Proviso that would break: if the monotonic-down phase is
>=6 and smooth, H2 could CONFIRM; if it is <6, DEGRADE-a (footage) and I acquire
one longer-drop clip. Being wrong about which DEGRADE tells me where the real
wall is.

## GATE

`tests/test_appearance_track_migrated.py` — H1 on a synthetic fragmentation
fixture (able to fail: the plain id-tracker fragments, appearance holds >=6),
the five controls, byte-identity-off, and the invariant guard. Reads the
GRAPH-minted verdict, never exact-d2. Run in several fresh `python3 -m pytest`
processes (carve ids are a cross-process HashMap artifact) — fresh-process pass
count reported.
