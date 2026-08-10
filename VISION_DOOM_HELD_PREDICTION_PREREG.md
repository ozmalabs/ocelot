# VISION — THE HELD-PREDICTION / DECAY / DEMOTION LOOP ON THE REAL DOOM EYE (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Branch `worktree-agent-a40adf9647378c168`, isolated worktree off
`main` HEAD **`53d2467c0d`** (LEDGER 198000 — THE DEMOTION HIERARCHY). Engine
canonical shared build `substrate_rs/_native.abi3.so` sha256
**`04c9d28e316d…`**, `source_match = "shared"` (Rust source byte-identical to
this worktree — this rung adds **NO Rust**, `term.rs` diff EMPTY, **NO new
seed**). Seed block **200000–200999**.*

Seed-claim check (verbatim, run before any number):

```
$ python scripts/seed_claim.py 200000 200999
SEED CLAIM 200000-200999: CLEAN -- no collision DETECTED.
  Scope: 898 files with seed sinks; 609 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

---

## 0. The claim — wire the loop we just landed onto the REAL Doom eye

The held-prediction / decay / demotion loop was landed and gated on a SYNTHETIC
scene (196000 `staleness_decay`, 198000 `demotion_hierarchy`, over 180000
`held_surface`). This rung wires that SAME loop onto the REAL Doom path — the
event-native 2-D photon eye (`domains/photon_eye.py` `GraphEye`) over real
VizDoom E1M1 frames (`domains/doom_photon_world.py`, the 181000 path) — and
measures the density/latency DECOUPLING **on real Doom frames**:

- The **held surface that has not decayed IS the accumulated prediction**
  (196000 freshness + the held `value`).
- The **new Doom frame is read at ORDER-0 as the residual** against that
  prediction (`sd_residual` — the fast, low-latency read).
- **`decay ∝ surprise` + demotion manage the held field**: STATIC level
  geometry (low residual) keeps a long half-life → freshness persists → gain
  stays low → it DENOISES and density accrues with dwell; MOVING content (high
  residual) collapses freshness → gain rises → it ADOPTS the new frame
  (refreshed, not smeared) at flat integer-tick latency; content that goes stale
  DEMOTES `FRESH→GIST` (198000, `dh_demote`, detail coarsened by `Ashr`) and is
  NEVER deleted.

**The loop wiring is a MECHANICAL MEASURE-ADAPTER**, not new agent logic: it
loads the EXISTING `staleness_decay` + `demotion_hierarchy` + `held_surface`
seed manifests onto the real Doom eye, creates the opt-in `HeldDecayParams` /
`HeldTierParams` config nodes + per-cell `HeldSurfaceCell` / `HierTrace` nodes,
submits real Doom photon flux, ticks under `run_rules()`, and READS graph
attributes. Every DECISION (residual, half-life, freshness, blend gain, tier,
demote) is an existing graph RULE. NO Rust, NO Term, NO new seed. Python is
mechanical world-I/O + measurement only (CLAUDE.md).

## 1. Stimulus — real E1M1, static hold + real pan + re-hold (ONE persistent eye)

Real VizDoom E1M1 frames captured via `doom_photon_world.capture_e1m1`, fed as
per-receptor Poisson photon flux (shot-noise every tick — so denoising is a real
task). One persistent decay-loop eye over the ordered sequence:

```
luma_seq = [f0]*T1  +  [f1 .. fM]  +  [fM]*T3
           static hold   real PAN     re-hold
           (camera fixed) (turn_right) (camera fixed)
```

`N_AZ×N_EL = 20×15` retina (the 181000 Doom-eye grid). Committed VizDoom-free
fixture (`tests/fixtures/doom_held_prediction/frames.npz`: downsampled luma
frames + depth + labels) so the gate is self-contained and deterministic.

**Region classification is EMPIRICAL, from the stimulus itself** (not
hand-placed): per retinal cell, the temporal variance of its NOISELESS true
luminance across `luma_seq`. STATIC region = the low-variance cells (level
geometry that persists); MOVING region = the high-variance cells (content the
pan sweeps through). This is the synthetic gate's static-rows/moving-rows split,
now DERIVED from real Doom pixels.

## 2. Gates — ALL count/observable-based, NONE wall-clock (this rung runs concurrently; wall-clock is corrupted by contention, lesson 149)

### G1 — THE DECOUPLING ON REAL DOOM (headline)

The two curves come apart on real Doom frames, over ONE held belief with ONE
decay-loop parameter set:

- **G1a — STATIC density CLIMBS with dwell.** On STATIC cells, the held
  reconstruction's normalized error vs the true field DROPS across the
  static-hold ticks (shot-noise averaged out — accumulation / super-resolution).
  Pass: static-region asymptote error `< 0.5 ×` its start error (density
  = 1/error climbs), and monotone-ish (≤ 3 up-steps > 0.03).
- **G1b — MOVING latency stays FLAT and LOW, as an INTEGER tick-count.** On
  MOVING content, after each frame change measure `ticks-to-adopt` = the INTEGER
  number of ticks for the held value to track the new true field within
  tolerance (0.15 normalized). Pass: mean ticks-to-adopt is small (`≤ 3`), FLAT
  across the motion phase (CV `< 0.5` and |slope| `< 0.5` over the transitions —
  the 196000 discipline, which measured `[1,1,1,1,1]`), i.e. latency does NOT
  grow with dwell.
- **G1c — the decoupling DOMINATES the fixed-rate trade.** vs two fixed-`lr`
  `held_surface` controls (the CURRENT eye): the decay loop achieves BOTH a
  static asymptote `≤ 1.5 ×` the low-`lr` control's AND a moving latency
  `≤ high-lr control + 2` ticks, while each control fails one arm (low-`lr`
  denoises but adopts slowly: latency `> 2×` the loop's; high-`lr` adopts fast
  but never denoises: static asymptote `> 2×` the loop's). The two timescales
  are COUPLED for a single rate and DECOUPLED by `decay ∝ surprise` — on real
  Doom.

### G2 — SCENE RECOVERY PRESERVED (byte-observable)

The eye's carve/onset recovery on the Doom pan is preserved (or improved) with
the held-prediction loop vs the current eye — the loop does not degrade what the
eye recovers. The decay/demotion rules read the SAME rod / onset stream and
write only their own bookkeeping nodes; they must not perturb the onset or carve
path.

- **G2a — onset signature identical.** Per-epoch `RetinalOnsetEvent` count over
  the whole sequence is BYTE-IDENTICAL with the loop ON vs the current
  fixed-`lr` eye (same photon seed).
- **G2b — carve set preserved.** The 2-D common-fate carve `VisionPolygon` set
  (`carve_polygons_2d`) over the motion phase is IDENTICAL (same polygon
  bounds), or the carve-vs-labels IoU is `≥` the current eye's. No degradation.

### G3 — COMPUTE ∝ SURPRISE (deterministic work-count, NOT wall-clock)

On a stabilising Doom scene the held-prediction path RE-PROCESSES FEWER CELLS
than the current every-frame eye; the work-count TRACKS SURPRISE (185000
dirty-index tie-in).

- **G3a — work drains on stabilising scene.** Per-tick surprise-gated work-count
  `W(t)` = # cells that are actually surprising at tick `t` (a cell with a
  `RetinalOnsetEvent` this epoch, i.e. change exceeded the dB threshold). `W(t)`
  DRAINS across the static-hold (plateau `≤ 0.15 ×` its start), SPIKES on the
  real pan (motion peak `≥ 20`, motion-mean `≥ 2.5 ×` plateau), then RE-DRAINS
  in the second hold. Deterministic integer counts.
- **G3b — held-prediction re-processes FEWER cells than every-frame.** The
  every-frame eye re-touches all `N = N_AZ×N_EL` cells each tick; the
  held-prediction work-count `W(t)` is `≪ N` on stable ticks. Pass: static-hold
  plateau `W ≤ 0.25 × N` and motion/static ratio `≥ 3`.

### G4 — DEMOTION (demote, never delete) — supporting observable

Stale STATIC content that stops being refreshed DEMOTES `FRESH→GIST` (tier drops
2→1, `stored` detail coarsened by `Ashr(detail, k_gist)`) — but the trace node
is NEVER deleted (`dh_demote` contains no `del_node`; deletion is the separate
order-9 `dh_delete_latent`, kept OFF). Pass: after a hold with no refresh, ≥ 1
`HierTrace` demotes to a lower tier AND the `HierTrace` node count is CONSTANT
(no deletion); a re-observation promotes it back to FRESH (`dh_promote`) and
recovers full detail.

### G5 — INTEGER-NATIVE + DEFAULT-OFF BYTE-IDENTITY

- **G5a — integer-native.** All decay/tier bookkeeping attributes (`residual`,
  `half_life`, `freshness`, `last_refresh_epoch`, `tier`, `stored`) are
  integer-valued (0 non-integer cells); `ticks-to-adopt` is an integer. Only the
  blend gain is float (documented; the decision is graph-resident).
- **G5b — default-OFF / eye byte-identical when off.** With the loop flag off
  (no `HeldDecayParams` / `HeldTierParams` node), every existing Doom-eye path is
  byte-identical to the current eye — onset events, carve polygons, and the
  fixed-`lr` `held_surface` value field all unchanged. Opt-in only.

## 3. Falsifiable failure / honest-negative conditions

Any of these is a reportable measured negative (a valid landing per PROTOCOL):

- G1 fails: on REAL Doom the static density does not climb, OR the moving latency
  is not flat/low, OR the decoupling does not dominate the fixed-rate trade (the
  synthetic result does not transfer to real frames).
- G2 fails: the loop perturbs the onset or carve output (scene recovery
  degrades). This would be a hard veto — the loop must be additive.
- G3 fails: the work-count does not track surprise on real Doom (no drain, or no
  motion spike).

A negative is reported straight, with the raw curves.

## 4. Discipline restated

- Prefer graph-data + EXISTING Terms; reuse 196000 / 198000 / 180000 rules, the
  191000/195000 event path, the settlement axiom. `term.rs` diff EMPTY; NO new
  seed (the loop already exists as rules — this rung is the ADAPTER that opts the
  Doom eye into them + the measurement).
- Python = mechanical world-adapter / measure only, NO agent decisions.
- Measure module IMPORT-INERT (scoped; `main()` guarded).
- Engine-semantics gate set (lesson 12), ONE synchronous session (read-only for
  this rung, but run to prove no perturbation): `test_incremental_match`,
  `test_empty_match_proof`, `test_dirty_precision`, `test_per_sensor_epoch`,
  `test_per_area_settlement`, `test_predicate_retraction`,
  `test_eye_binding_projection`, `test_staleness_decay`,
  `test_dissipation_inference`, `test_demotion_hierarchy`, plus the eye suite
  (`test_2d_retina`, `test_retinal_onset`, `test_async_carve`,
  `test_eye_graphnative_event`, `test_2d_motion_salience`,
  `test_photon_grapheye`) + `held_surface`.
- Oracle `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER (the current Doom
  eye output UNCHANGED with the flag off). `source_match` own/shared. Commit
  before report. Do NOT merge to main or touch VISION_PROTOCOL.md.

## 5. Deliverables

Prereg hash; results hashes; the loop wiring on the Doom path
(`scripts/doom_held_prediction_measure.py` + gate
`tests/test_doom_held_prediction_migrated.py`); G1 decoupling curves on real Doom
(density-vs-dwell on static, integer-tick latency on moving); G2
scene-recovery-preserved comparison; G3 compute-∝-surprise work-count curve; G4
demote-not-delete observable; integer-native audit; term.rs-empty / no-new-seed
audit; full engine-semantics gate results + eye suite; oracle BEFORE == AFTER;
default-OFF byte-identity; canonical-untouched; `source_match`. Raw numbers in
`VISION_DOOM_HELD_PREDICTION_RESULTS.md` + `results/doom_held_prediction/`.
