# VISION — THE ALLOCENTRIC HELD-SURFACE MAP RECONSTRUCTION (PRE-REGISTRATION)

*Committed ALONE, BEFORE any implementation and BEFORE any measurement
(PROTOCOL §3). Branch `worktree-agent-a7da416ac03de11bd`, isolated worktree off
`main` HEAD **`4ea0a4126c`** (LEDGER 201000 — the Doom real-time rung). Engine
canonical shared build `substrate_rs/_native.abi3.so` sha256
**`04c9d28e316d…`** (md5 **`793ce09e`**, `source_fingerprint`
**`7dd6c73692c0…`**), `source_match = "shared"` (Rust source byte-identical to
this worktree — this rung adds **NO Rust**, `term.rs` diff EMPTY). Seed block
**203000–203999**.*

Seed-claim check (verbatim, run before any number):

```
$ python scripts/seed_claim.py 203000 203999
SEED CLAIM 203000-203999: CLEAN -- no collision DETECTED.
  Scope: 901 files with seed sinks; 612 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

`check_claim(203000, 203999)` → `ok = True`.

---

## 0. The claim — the map IS the held surface, in ALLOCENTRIC (world) coordinates

Three lines are already landed and must be UNIFIED here:

- **161000** — a persistent, graph-native OCCUPANCY map of E1M1 (`has_cell
  Cell{pose,value}`, unknown = ABSENCE), grown by `dm_*` rules from geometry
  SEEN via depth-from-motion (158000) placed at world coordinates via the
  marine's pose (155000 efference / `doom_world`). Decoded by the EXISTING
  `space_quantize` (Rust) into `SpaceQuantum` boxes.
- **180000/196000/198000/200000** — the held-surface / staleness-decay /
  demotion loop: a held BELIEF that EMA-accumulates observations (denoises with
  dwell — density climbs), DECAYS by an integer half-life set inversely by
  surprise, DEMOTES `FRESH→GIST→LATENT` when long unseen (never DELETES), and
  PROMOTES back + recovers detail on re-observation. Landed EGOCENTRICALLY (per
  retina cell) and shown to transfer to the real Doom eye (200000).

This rung REGISTERS the held-surface loop into WORLD (allocentric) coordinates
via the marine's pose and ACCUMULATES it into a persistent map. **The map is the
held surface in allocentric coordinates:** as the eye moves through real E1M1,
each SEEN observation (world cell + its observed luminance, placed by pose) is
accumulated into a first-class `AlloCell{pose, value, density, freshness,
last_refresh_epoch, half_life, tier, geom}` on the game node. Regions DWELT on
super-resolve (density climbs, value denoises); regions seen once are gist;
long-unseen regions DEMOTE (retained + promotable, NOT deleted); the
occupancy/geometry stays SEEN (depth-from-motion / the eye's carve), and the
VizDoom **depth + labels buffers are SCORING ORACLES ONLY, never inputs** (the
161000 discipline).

This is NEITHER 161000 (occupancy-only, no decay/dwell/demotion) NOR 200000
(egocentric, retina-frame). It is the held surface accumulated in ALLOCENTRIC
coordinates — a persistent, super-resolving, DECAYING reconstruction of the
level built from what the eye SEES as it moves.

**The accumulation + decay + demotion are all graph RULES** (a new seed
`doom_allocentric_surface.json`, transcribing the SAME 196000/198000/180000
mechanism forms — EMA blend, `freshness = Ashr(C0, IDiv(now − last_refresh,
half_life))`, freshness-thresholded tiers, `Ashr`-coarsened `stored` — onto the
world-cell key, and mirroring 161000's game-node minting/merge pattern). **NO
Rust, NO new Term** (`term.rs` diff EMPTY; every op — `Ashr`/`IDiv`/`Abs`/`Max`/
`IfThenElse`/`Gte`/`Plus`/`Times`/`Minus`/`IndexAt`/`Exists`/`Not` — already
exists). A NEW SEED is graph data, not new engine code; it is authored because
the allocentric cells hang off the game node (like 161000's `has_cell`), which
does not fit the retina/column/rod structure the 196000/198000/200000 rules
match on — the FORMS are reused, transcribed to the world-cell key.

**The wiring is a MECHANICAL world-adapter** (`domains/doom_allo_surface_ingest.py`):
pose + SEEN depth-from-motion + per-azimuth observed luminance → world `ObsCell`
tokens; set the game innovation clock; `run_rules()` (the mint/blend/decay/
demote/promote rules fire); `space_quantize` for areas; read the map back /
render. Every DECISION (mint, EMA blend, density++, residual→half_life,
freshness, tier, demote, promote) is a graph RULE. NO agent decisions in Python
(CLAUDE.md).

## 1. Stimulus — real E1M1, a real pan/walk (ONE persistent allocentric map)

The marine walks a FIXED, seeded, forward-heavy route on real E1M1 (the 161000
`_capture` + `_seen_depth_by_column` path: forward parallax → depth-from-motion
on RGB flow → per-azimuth SEEN world depth, calibrated by the agent's own
forward displacement; the depth/labels buffers are captured as ORACLES only).
Per frame the SEEN free/wall world cells AND their observed luminance are
registered by pose and accumulated into the one persistent allocentric map.

For the deterministic, VizDoom-free GATE: a CONSTRUCTED synthetic run over a
KNOWN level + a scripted pose path (with injected per-observation shot noise on
the luminance) exercises mint / EMA-denoise / density-climb / decay / demote /
promote deterministically and cross-process. The real E1M1 run (behind a WAD
guard) provides the headline numbers + the map FIGURE.

## 2. Gates — ALL count/observable-based, NONE wall-clock (this rung runs concurrently; wall-clock is corrupted by contention, lesson 149)

### G1 — RECONSTRUCTION FIDELITY (headline)

As the eye moves, the accumulated allocentric held surface RECONSTRUCTS the
level geometry, AND the map is a DECAYING reconstruction (super-resolves where
dwelt, demotes where long-unseen), not an ever-growing store.

- **G1a — fidelity GROWS with exploration.** The reconstruction's coverage
  (count of world cells reconstructed) and its structural agreement with the
  depth ORACLE (the SEEN-vs-depth-buffer correlation over the accumulated map /
  geometry-IoU of reconstructed free cells vs the oracle's free cells) GROW
  monotone-ish with frames (`fidelity(last) > fidelity(early)`; coverage strictly
  increases over the walk). Reported as a fidelity-vs-frames curve.
- **G1b — dwelt regions SUPER-RESOLVE (density climbs).** On cells observed
  across multiple frames (dwell), `density` (integer observation count) CLIMBS,
  and the held `value` DENOISES: on the constructed run with a known true
  appearance + injected shot noise, the dwelt-region held-value error vs the true
  appearance DROPS to `< 0.5 ×` its start (accumulation), with ≤ 3 up-steps —
  the 200000 density-climb, now in world coordinates.
- **G1c — long-unseen regions DEMOTE (decaying reconstruction).** Cells not
  re-observed for many frames drop tier `FRESH(2)→GIST(1)→LATENT(0)` as their
  freshness decays; the mean tier of the long-unseen region is STRICTLY LOWER
  than the recently-seen region, AND the `AlloCell` node count is NON-DECREASING
  across the demotion (demote, never delete). Reported as a per-region tier-over-
  time curve.

### G2 — REVISIT / PROMOTE (loop-closure analog)

Revisiting a region that had demoted to gist/latent PROMOTES it back to FRESH
and RECOVERS detail (198000 G2, in world coordinates). Measured as a
demote→revisit→promote cycle: after a region demotes (tier drops, `stored`
coarsened by `Ashr`), a re-observation at that world pose resets the innovation
clock (`last_refresh_epoch = obs_epoch`), tier climbs back to FRESH next tick,
`stored` recovers full detail from the incoming observation, and the node count
is unchanged (recovery, not re-creation). Demonstrated on the constructed run
(deterministic) and, where the real E1M1 route returns near a previously-seen
area, on the real run.

### G3 — GRAPH-NATIVE + ORACLES-ONLY

- **G3a — the map GROWS/DECAYS by RULES, not Python.** The mint / EMA blend /
  density++ / residual→half_life / freshness / tier / demote / promote all live
  in `seeds/doom_allocentric_surface.json` as graph data; the ingest adapter
  makes NO map-building DECISION — it emits `ObsCell` tokens + sets the clock +
  calls `run_rules`/`space_quantize` only, and NEVER writes an `AlloCell` value
  from a conditional (source audit, mirroring 161000's ARCH gate).
- **G3b — depth + labels are SCORING ORACLES, provably not smuggled.** The map's
  WHOLE input is the eye (RGB flow → SEEN depth-from-motion; per-azimuth observed
  luminance) + self-motion (pose). The VizDoom depth buffer is used ONLY for the
  G1a fidelity score; the labels buffer is not used as input at all. Source audit
  asserts the ingest never reads `depth`/`labels_buffer` into a map write.

### G4 — COMPUTE ∝ SURPRISE (deterministic work-count, NOT wall-clock)

Exploring NEW regions costs; revisiting KNOWN regions is cheap.

- **G4a — work spikes on novel geometry.** Per-frame work-count `W(t)` =
  # `AlloCell`s minted this frame + # re-processed (blended) this frame (a
  deterministic integer, the 185000 dirty tie-in; equivalently the
  `space_quantize` `cand_enum` over the frontier). `W(t)` SPIKES on frames that
  reveal novel geometry (many mints).
- **G4b — revisiting is cheap.** On frames that re-observe already-mapped
  regions, `W(t)` (mints ≈ 0, only blends of settled cells) is LOW —
  `revisit-mean W ≤ 0.5 × novel-mean W`. Compute follows surprise. Deterministic
  integer counts, never wall-clock (this rung runs concurrently).

### G5 — INTEGER-NATIVE + DEFAULT-OFF BYTE-IDENTITY

- **G5a — integer-native.** All decay/tier/map bookkeeping attributes (`pose`,
  `density`, `residual`, `half_life`, `freshness`, `last_refresh_epoch`, `tier`,
  `stored`, `geom`) are integer-valued (0 non-integer cells over the run). Only
  the EMA blend gain / held `value` is float (documented; in-frame is integer,
  the continuum lives in the cross-frame blend — the 196000 G5 boundary).
- **G5b — default-OFF / 161000 map + oracle byte-identical when off.** Every new
  rule guards on `game.map_mode == "doom"` AND an opt-in `AlloParams{enabled=1}`
  node the adapter creates only on opt-in. With the seed loaded but NO
  `AlloParams` node, the loop is inert: the 161000 `has_cell` map, its
  `SpaceQuantum` decode, and every existing world's coarse path are BYTE-
  IDENTICAL, and the oracle is UNMOVED.

## 3. Falsifiable failure / honest-negative conditions

Any of these is a reportable measured negative (a valid, valuable landing per
PROTOCOL — e.g. "registration drifts and the map doesn't cohere"):

- G1a fails: pose-registered accumulation does NOT reconstruct coherent geometry
  (fidelity does not grow, or drifts) — registration/seen-depth too noisy.
- G1b fails: dwelt regions do not super-resolve (density does not climb, or the
  held value does not denoise).
- G1c fails: long-unseen regions do not demote (no decaying reconstruction).
- G2 fails: a revisit does not promote/recover a demoted region.
- G4 fails: work does not track surprise (novel and revisit frames cost the same).

A negative is reported straight, with the raw curves and the MAP FIGURE.

## 4. Discipline restated

- Prefer graph-data + EXISTING Terms; REUSE `space_quantize`, the `has_cell`/
  pose conventions, the 196000/198000/180000/200000 mechanism forms,
  depth-from-motion (158000), the pose (155000/`doom_world`). `term.rs` diff
  EMPTY. A new SEED (`doom_allocentric_surface.json`) is graph data — NO new
  Term (if one were needed, STOP and report; none is).
- Python = mechanical world-adapter (ingest / pose-register / display) + measure
  only, NO agent decisions (CLAUDE.md — the map GROWS/DECAYS via rules; the
  adapter is pose-registration I/O).
- Measure module IMPORT-INERT (scoped context manager; `main()`/`run()` guarded).
- Engine-semantics gate set (lesson 12), ONE synchronous session (read-only for
  this rung, but run to prove no perturbation): `test_incremental_match`,
  `test_empty_match_proof`, `test_per_sensor_epoch`, `test_per_area_settlement`,
  `test_eye_binding_projection`, `test_staleness_decay`,
  `test_demotion_hierarchy`, `test_doom_held_prediction`, plus the eye suite +
  `held_surface`; and the 161000 Doom-map gate `test_doom_ingraph_map` kept
  green.
- Canonical `.so` invariant: MAIN canonical is `793ce09e…`; this seed/Python-only
  rung keeps it `793ce09e` (verify md5 untouched). If any Rust — none intended —
  build only in-worktree + note rebuild-on-merge.
- Oracle `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER. `source_match`
  own/shared. Commit before report. Do NOT merge to main or touch
  VISION_PROTOCOL.md.

## 5. Deliverables

Prereg hash; engine/results hashes; the allocentric-held-surface reconstruction
wiring (pose registration + accumulation + decay/demotion, all graph-native:
seed `doom_allocentric_surface.json` + adapter `doom_allo_surface_ingest.py` +
runner/measure `doom_allo_surface_run.py`); gate
`tests/test_doom_allo_surface_migrated.py`; G1 reconstruction-fidelity-vs-frames
+ per-region tier curves; G2 demote→revisit→promote cycle; G3 graph-native +
oracles-only source audit; G4 compute-∝-surprise work-count; integer-native
audit; `term.rs`-empty / no-new-Term audit; full engine-semantics gate results +
eye suite; oracle BEFORE == AFTER; default-OFF byte-identity; canonical-untouched;
`source_match`. Raw numbers + a MAP FIGURE (the reconstructed allocentric map vs
the true level) in `VISION_DOOM_ALLO_SURFACE_RESULTS.md` + `results/doom_allo_surface/`.
