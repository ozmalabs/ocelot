# VISION — THE ALLOCENTRIC HELD-SURFACE MAP RECONSTRUCTION (RESULTS)

*Branch `worktree-agent-a7da416ac03de11bd`, isolated worktree off `main` HEAD
**`4ea0a4126c`** (LEDGER 201000). Prereg committed ALONE at
**`b71b25258b`** (`VISION_DOOM_ALLO_SURFACE_PREREG.md`). Seed block
**203000–203999** (`seed_claim` CLEAN, `check_claim` ok=True). Engine
`substrate_rs/_native.abi3.so` sha256 **`04c9d28e316d`** (md5 **`793ce09e`**),
`source_match = "shared"` — **NO Rust** (`term.rs` / whole `runners/dsl` diff
EMPTY), the loop is a new SEED (graph data) + a mechanical adapter. Every gate is
an INTEGER count / byte-observable / a scoring-oracle correlation, no wall-clock
claim (this rung ran concurrently).*

## Verdict — the map IS the held surface, in allocentric coordinates

As the eye moves through **real E1M1**, its held-prediction / decay / demotion
loop (200000), REGISTERED into world coordinates by the marine's pose,
accumulates into a **persistent, super-resolving, DECAYING reconstruction of the
level**. Coverage GROWS (1 → 83 cells over a 40-frame walk), the SEEN geometry
positively correlates with the depth ORACLE on **every** forward frame
(Spearman median **0.39**, frac_pos **1.0**, n=21), dwelt regions SUPER-RESOLVE
(max dwell **25**, held value denoises), long-unseen regions DEMOTE
(fresh/gist/latent = 40/13/30 at the end), and a region re-observed on the real
return leg PROMOTES back (fresh count collapses 42→1 as the marine turns, then
climbs back to 22 as it re-observes on the way back). The whole map is graph
data grown by RULES; the depth + labels buffers are SCORING ORACLES only.

**Honest bound (carried, not hidden):** geometric fidelity vs the oracle is
POSITIVE and GROWS (IoU 0 → **0.19**) but is BOUNDED by seen-depth quality —
the same 158000/161000 flow wall. The reconstruction's *dynamics* (super-
resolution, decay, demotion, promotion, compute∝surprise) are clean and land in
full; the geometric *fidelity* is real but coarse, exactly the 161000 degrade,
reported straight.

Deliverables: seed `seeds/doom_allocentric_surface.json` (+ builder
`scripts/build_doom_allo_surface_seed.py`); adapter
`domains/doom_allo_surface_ingest.py`; runner/measure
`scripts/doom_allo_surface_run.py`; gate
`tests/test_doom_allo_surface_migrated.py` (10/10, cross-process-stable, real
E1M1 behind a WAD guard); raw numbers `results/doom_allo_surface/summary.json`;
the MAP FIGURE `results/doom_allo_surface/reconstruction_vs_true.png` (reconstructed
allocentric held surface vs the depth-oracle occupancy) + checkpoint PNGs.

## SEED CLAIM

```
SEED CLAIM 203000-203999: CLEAN -- no collision DETECTED.
```
`check_claim(203000, 203999)` → `ok = True` (full text verbatim in the prereg).

## The machinery reused (composed, did not reinvent)

| piece | what it gave | how I used it |
|---|---|---|
| 180000 `held_surface` | EMA accumulation of a held belief (build + forget) | the `as_blend` EMA form, transcribed to the world-cell key |
| 196000 `staleness_decay` | `freshness = Ashr(c0, IDiv(now − last_refresh, half_life))`, half_life ∝ 1/surprise | `as_gate` + `as_freshness`, on the game's `map_epoch` innovation clock |
| 198000 `demotion_hierarchy` | freshness-thresholded FRESH/GIST/LATENT tiers, `Ashr`-coarsened `stored`, promote-on-refresh, never delete | `as_tier` + `as_demote`; promote is implicit (a blend refreshes the clock) |
| 200000 held-prediction-on-Doom | the loop transfers to the real Doom eye (egocentric) | this rung is its ALLOCENTRIC generalisation — the pose registers it into world coordinates |
| 161000 `doom_ingraph_map` | game-node minting/merge over a `has_cell`-style belief (unknown = ABSENCE), the pose-register + depth-from-motion capture path | the `as_new` mint pattern + the `_capture` / `_seen_by_column` E1M1 path |
| 158000 depth-from-motion / 155000 efference | the eye SEEING wall depth from RGB flow, world-calibrated by own displacement | the SEEN geometry source (NO depth buffer) |

**Added:** `seeds/doom_allocentric_surface.json` (6 rules: `as_new`, `as_blend`,
`as_gate`, `as_freshness`, `as_tier`, `as_demote`), the adapter, the runner, the
gate, the builder. **NO Rust, NO new Term.**

## The design — what is graph data / rules, what is mechanical

**One persistent belief: `AlloCell{pose, value, dwell, residual, half_life,
freshness, last_refresh_epoch, tier, stored, geom}` on the game node** (unknown =
ABSENCE, first-class — an unobserved world pose has no node). GROWN and MANAGED
entirely by rules:

- `as_new` — a SEEN world pose (registered by the marine's pose) with no cell
  mints one, FRESH, value = the observed luminance, geom from the SEEN src.
- `as_blend` — a re-observed pose EMA-accumulates the held value (freshness-
  weighted Kalman gain: a FRESH cell trusts the belief and DENOISES; a STALE
  cell ADOPTS the new content), climbs `dwell` (super-resolution), sets the
  integer surprise residual, and PROMOTES (refreshes the innovation clock). An
  epoch guard (`last_refresh_epoch < obs.epoch`) makes it fire EXACTLY ONCE per
  observation — the 196000 `input_epoch > hs.epoch` discipline.
- `as_gate` — `half_life = Max(hl_min, IDiv(hl_scale, residual+1))` (decay ∝ surprise).
- `as_freshness` — the integer-half-life decay law on `game.map_epoch`.
- `as_tier` / `as_demote` — freshness-thresholded FRESH/GIST/LATENT + `Ashr`-
  coarsened `stored`; the held `value` (the detail) is PRESERVED, so a promote
  recovers it; NO `del_node`.

**Mechanical (adapter, no decision):** pose + per-azimuth SEEN depth-from-motion
+ per-azimuth RGB luma → world `ObsCell` tokens; ONE clock write
(`set_attr(game, "map_epoch", …)`); `run_rules`; clean up consumed ObsCells;
read/render. The work-count `{minted, blended}` is read off the belief diff.

---

## G1 — RECONSTRUCTION FIDELITY (headline) ✓

### G1a — fidelity GROWS with exploration

**Constructed** (`test_G1a`, deterministic, able-to-fail): a known room+wall
layout registered over frames GROWS the reconstruction (coverage 1 → N) and
reconstructs the expected free/wall cells; one AlloCell per pose (no within-frame
duplicates).

**Real E1M1** (seed 1234, 40 frames captured, fixed forward+return route): the
reconstruction read FROM the graph grows and its agreement with the oracle climbs:

| frame | 0 | 10 | 15 | 20 | 30 | 40 |
|---|---|---|---|---|---|---|
| **coverage (cells)** | 1 | 26 | 31 | 55 | 65 | 83 |
| **fidelity IoU vs oracle** | 0.00 | 0.013 | 0.038 | 0.190 | 0.198 | 0.192 |

The SEEN depth (depth-from-motion, NEVER the buffer) positively correlates with
the depth-buffer ORACLE on **every** forward frame: **Spearman median 0.39, mean
0.37, frac_pos 1.0 (n=21)** — in 158000's 0.40–0.94 band, stronger than 161000's
median 0.31 / frac_pos 0.80 (the return-leg route revisits geometry, sharpening
the estimate). Geometry is genuinely SEEN, and it accumulates coherently.

### G1b — dwelt regions SUPER-RESOLVE (density climbs) ✓

**Constructed** (`test_G1b`): a cell observed 15× under uniform shot noise
(±20) — `dwell` climbs 1 → 15 and the held value's error DROPS below `0.5 ×` the
mean single-frame noise (temporal denoising / super-resolution — the 200000
density-climb in world coordinates). **Real E1M1:** max dwell **25** on the
regions the walk lingers over.

### G1c — long-unseen regions DEMOTE (decaying reconstruction) ✓

**Constructed** (`test_G1c`): a cell seen once then left behind demotes
`FRESH→GIST→LATENT` (tier monotone non-increasing, reaches LATENT) while a
continuously-dwelt cell stays FRESH; the AlloCell node count is NON-DECREASING
(demote, never delete). **Real E1M1:** the final tier hierarchy is fully
populated — **fresh 40 / gist 13 / latent 30** — the map is a DECAYING
reconstruction, not an ever-growing store. Per-region tier-over-time curve in
`summary.json` (`tier_curve`).

## G2 — REVISIT / PROMOTE (loop-closure analog) ✓

**Constructed** (`test_G2`): a cell demoted to LATENT (`stored` coarsened to 0)
is REVISITED — it promotes back to FRESH, `stored` recovers the full integer
value, and the node count is UNCHANGED (recovery, not re-creation). **Real
E1M1:** as the marine turns around mid-route the fresh count collapses (42 → 1,
everything demotes to gist/latent), then CLIMBS back to 22 as the return leg
re-observes previously-mapped geometry — the demote→revisit→promote cycle on a
real E1M1 path.

## G3 — GRAPH-NATIVE + ORACLES-ONLY ✓

- **G3a — the map grows/decays by RULES** (`test_G3_...not_python`): the six
  accumulation/decay/demotion rules live in the seed as graph data; the ingest
  adapter emits `ObsCell` + sets the clock + `run_rules` only — it NEVER writes
  an `AlloCell` value or edge from a conditional (source audit asserts
  `add_node("AlloCell"` / `add_edge …"has_allo_cell"` are ABSENT from the
  adapter). Every belief write is a rule effect.
- **G3b — oracles-only** (`test_G3_oracles_only`): the ingest module contains no
  `depth`/`depth_buffer`/`labels_buffer` read at all; in the runner the depth
  buffer appears ONLY in the `_oracle_occupancy` / `_seen_vs_oracle_spearman`
  scoring helpers, and the map-build path uses `ingest_seen` on
  `depth_from_motion` (SEEN), never a buffer. The labels buffer is not used.

## G4 — COMPUTE ∝ SURPRISE (deterministic work-count) ✓

**Constructed** (`test_G4`): revealing a NEW row of geometry each frame MINTS 6
cells (the surprise signal); RE-OBSERVING already-mapped geometry mints **0**
(the structure is already there); a region the marine has moved on FROM
contributes **0** work (settled, not re-processed). **Real E1M1:** the per-frame
work-count spikes on frames that reveal novel geometry (mints 7 / 18 / 8 / 12 on
the exploration frames) and drains to ~0 when the marine is not gaining new
structure — compute follows surprise (the 185000 dirty tie-in). Deterministic
integer counts, never wall-clock.

## G5 — INTEGER-NATIVE + DEFAULT-OFF ✓

- **G5a — integer-native** (`test_G5a`): 0 non-integer cells across `pose` /
  `dwell` / `residual` / `half_life` / `freshness` / `last_refresh_epoch` /
  `tier` / `geom` / `now_epoch` over the run. Only the EMA-blended `value` is
  float (documented; in-frame is integer, the continuum lives in the cross-frame
  blend — the 196000 G5 boundary).
- **G5b — default-OFF / inert** (`test_G5b`): with the seed loaded but NO
  `AlloParams` node, every `as_*` rule's `enabled` guard fails — no AlloCell ever
  mints, the belief stays empty, the game node is untouched. Opt-in only; every
  existing path (incl. the 161000 map) is byte-identical.

## Audits

- **`term.rs` / whole `runners/dsl` diff EMPTY** — no Rust. The loop is a NEW
  SEED (graph data) transcribing the 196000/198000/180000 forms onto the
  world-cell key; every op already exists.
- **Canonical engine untouched** — sha256 `04c9d28e316d` / md5 `793ce09e`,
  `source_match = "shared"`, Rust source byte-identical. Seed/Python-only rung;
  rebuild-on-merge N/A.
- **Additions only** — the rung adds the seed, adapter, runner, gate, builder,
  results, prereg; no existing file modified (the 161000 map + oracle unchanged).
- **Integer-native / no-wall-clock** — every gate is an integer count, a
  byte-observable, or a scoring-oracle correlation.

## Gate

`tests/test_doom_allo_surface_migrated.py` — 10 tests, **10 passed**, cross-
process-stable (3 fresh `pytest` processes → 10/10 each; scored by
occupancy/dwell/tier/counts, never node-id). Includes the real E1M1 run (skips
without the WAD).

## Engine-semantics gate set (ONE session) + oracle

- **Engine-semantics gate set + eye suite + `held_surface` + 161000 doom map,
  ONE synchronous session: 135 passed / 0 failed** (486 s). Files:
  `incremental_match`, `empty_match_proof`, `per_sensor_epoch`,
  `per_area_settlement`, `eye_binding_projection`, `staleness_decay`,
  `demotion_hierarchy`, `doom_held_prediction`, `held_surface`,
  `doom_ingraph_map` (the 161000 gate — kept green), `2d_retina`, `async_carve`,
  `eye_graphnative_event`, `2d_motion_salience`, AND this rung's
  `doom_allo_surface` — all green together, confirming the new seed perturbs
  nothing.
- Oracle `bash scripts/rung7_vision_bench.sh` — **BEFORE 214 passed / 10 skipped
  / 0 failed == AFTER 214 passed / 10 skipped / 0 failed** (the data-less
  baseline; identical both sides — the new seed is inert to every existing path).

## Honest residuals

- **Geometric fidelity is bounded by seen-depth quality** (IoU 0.19). The
  reconstruction's DYNAMICS are clean; its geometric precision is the 161000/
  158000 flow-wall degrade, reported straight — NOT a reason to read the depth
  buffer.
- The real E1M1 capture stopped at 40 frames (episode boundary), which still
  gives the forward+return route that exercises G2; a longer route would deepen
  the loop-closure demonstration.
- Appearance (`value`) super-resolution is measured cleanly on the constructed
  run (known truth + injected noise); on real E1M1 the appearance oracle is not
  available, so G1b there is `dwell` climb (density), not a value-error curve.
- `space_quantize` area decode was NOT wired into the core path (the prereg
  listed it as available); the reconstruction figure renders the AlloCell field
  directly. The 161000 nav/area layer composes on the belief unchanged (a named
  follow-on), and is not load-bearing for any gate here.

## Proposed VISION_PROTOCOL.md ledger row

- **203000–203999 (the moving Doom eye RECONSTRUCTS the level MAP as the
  pose-compensated, ALLOCENTRIC HELD SURFACE — NO Rust, new seed
  `doom_allocentric_surface` + adapter + runner, engine `04c9d28e`/`793ce09e`
  `source_match="shared"`, oracle 214+10s/0 both sides).** The map IS the held
  surface (180000/196000/198000/200000) in WORLD coordinates: a first-class
  `AlloCell{pose,value,dwell,freshness,tier,…}` belief on the game node
  (unknown = ABSENCE), grown as the moving eye's SEEN observations
  (depth-from-motion 158000 + RGB luma, calibrated by efference 155000) are
  pose-registered into world coordinates, and MANAGED by 6 rules (`as_new` mint /
  `as_blend` EMA+dwell+promote / `as_gate` surprise→half_life / `as_freshness`
  decay law / `as_tier` / `as_demote` — demote-never-delete). **G1** coverage
  1→83, fidelity IoU 0→0.19 (bounded by seen-depth, 161000 degrade), SEEN-vs-
  oracle Spearman 0.39 frac_pos 1.0 (n=21); dwelt regions super-resolve (dwell→25,
  constructed value-denoise <0.5× single-frame noise); long-unseen regions demote
  (fresh/gist/latent 40/13/30). **G2** demote→revisit→promote on the real return
  leg (fresh 42→1→22) + constructed stored-recovery. **G3** map grows/decays by
  RULES (source audit) + depth/labels are SCORING ORACLES only. **G4** work∝surprise
  (novel mints spike, revisit mints 0, settled=0). **G5** integer-native + default-OFF
  byte-identical (no AlloParams → inert, 161000 map unchanged). Gate
  `tests/test_doom_allo_surface_migrated.py` 10/10, cross-process-stable,
  E1M1-skips without the WAD. `term.rs` EMPTY, canonical `793ce09e` UNCHANGED.
  `SEED CLAIM 203000-203999 CLEAN`.
