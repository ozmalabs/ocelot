# RESULTS — a persistent, graph-native in-graph map of Doom, built from what the agent SEES

Block **161000–161999**. Branch `gamma-substrate/doom-ingraph-map`. Engine
`64dbce1e7f47…` **`source_match = "shared"`** (this rung adds **NO Rust** — the worktree's
Rust source is byte-identical to the canonical tree, so the shared canonical engine is the
one measured; source_fingerprint `3a66c063…`). Prereg: `VISION_DOOM_INGRAPH_MAP_PREREG.md`.

## SEED CLAIM (§3)

```
SEED CLAIM 161000-161999: CLEAN -- no collision DETECTED.
```
`check_claim(161000, 161999)` → `ok = True` (full text in the prereg).

## Oracle (§10) — UNMOVED

`bash scripts/rung7_vision_bench.sh`, canonical shared engine, both sides of the work:

| | passed | skipped | failed |
|---|---|---|---|
| **BEFORE** | 212 | 10 | **0** |
| **AFTER**  | 212 | 10 | **0** |

**222/0 both** (212 pass + 10 optional-dep skips). The new seed is INERT without the ingest
(every dm_* rule guards on `game.map_mode=="doom"`), so every existing world's coarse path is
byte-identical (§9). No Rust changed.

---

## STEP 1 — the machinery I reused (composed, did not reinvent)

| piece | what it gave | how I used it |
|---|---|---|
| `runners/dsl/src/space_quantize.rs` (Rust) | the in-graph map primitive: reads a `has_cell` belief (`Cell{pose,value}`, **unknown = ABSENCE**), decodes it into `SpaceQuantum` `passable` boxes + `portal` edges + `frontier` boxes at the unknown border; body-conditional, per-dim, foveated, incremental | THE map representation. Called from the adapter (`I.space_quantize`), unchanged. |
| `seeds/quanta_navigation.json` (the qf_* rules) | proof that flood/route/frontier over the belief is graph-native; the belief conventions (`has_cell`, `pose`, `value`, `kind`) | the conventions my accumulation writes into; the qf_* nav layer sits on top unchanged. |
| `scripts/doom_world.py` | the marine's pose (x/y/angle, self-motion), the depth/RGB side-channels, the `sees`/`SpatialLocation` topology | the pose source; I wrote my own pose-carrying E1M1 capture (couldn't edit 157000's `capture_e1m1`, which omits pose). |
| `scripts/depth_from_motion_probe.py` (block 158000) | `estimate_foe` / `radial_decompose` / `depth_from_motion` / `expansion_gate` / `flag_movers` / `_flow_field` / `spearman` | the eye SEEING wall depth from RGB flow — the geometry source. |
| efference copy (block 155000) | the agent knows its own forward displacement from its motor command | calibrates depth-from-motion's `r/|flow|` (`Z/speed`) to world units. |

**Added:** `seeds/doom_ingraph_map.json` (8 rules), `domains/doom_map_ingest.py` (mechanical
ingest + display), `scripts/doom_ingraph_map_run.py` (the E1M1 runner + capture),
`scripts/build_doom_map_seed.py` (seed emitter), the gate. **No Rust.**

## The map-build design (what is graph data / rules, what is mechanical)

Three graph-native layers, one persistent map:

1. **Occupancy belief** — `has_cell Cell{pose,value}` on the game node. GROWN by rules:
   - `dm_free_new` / `dm_wall_new`: an observed cell whose pose is not yet known mints a Cell
     (free / wall). Registering an unseen pose IS the explored region growing; an unobserved
     pose has no node = **unknown, first-class absence**.
   - `dm_walk_frees_wall`: the merge POLICY — first-hand walking is authoritative, so a cell the
     agent stood in that a depth ray mis-called a wall is corrected to FREE. This rule (not any
     Python) is what guarantees the map never keeps a wall on a walked cell.
2. **Areas** — the existing `space_quantize` decodes the belief into `SpaceQuantum` boxes.
3. **Human area kinds** — rules type each box by geometry relative to the body width
   (config-space; §13-clean, no aspect-ratio constant): `dm_kind_room` (open in both dims),
   `dm_kind_corridor` (one body wide, longer in the other), `dm_kind_area` (single-body
   junction), `dm_kind_frontier` (the unknown border), `dm_kind_lava` (value-keyed hazard).

**Mechanical (adapter, no decision):** pose → walk-free ObsCell (efference copy); RGB flow →
depth-from-motion → per-azimuth SEEN depth → world points → depth_free/depth_wall ObsCells;
per-frame sensor fusion (one obs/cell); `run_rules` + `space_quantize` cadence; PNG render.

---

## M1 — a graph-native map GROWS (headline)

**Constructed** (`test_M1_*`, deterministic, cross-process): belief grows 1 → N as it is sensed;
the belief IS `has_cell Cell` nodes (one per pose), decode yields `SpaceQuantum` nodes; a known
room+corridor layout registers exactly the expected free/occupied cells (able to fail).

**Real E1M1** (seed 1234, 80 frames, fixed route): the map read FROM the graph grows

| frame | 0 | 20 | 40 | 79 |
|---|---|---|---|---|
| **cells** | 1 | 55 | 101 | **122** |

Final: **122 cells** (35 free, 87 wall), **29 passable** areas, **22 frontier** areas.
Checkpoint PNGs (read from the graph): `results/doom_ingraph_map/map_frame_{010,025,045,065,080}.png`
— the map visibly accumulates (small patch → bounded room/corridor field with the red trajectory
threading free space, black seen-walls around, white unknown beyond).

## M2 — the geometry is SEEN, and correlates with the oracle it is scored against

The walls are **SEEN** (depth-from-motion on RGB flow, efference-calibrated), never read. Two
ground-truth scores:

- **(a) Trajectory-consistency = 1.0** — all 9 walked cells are free in the map; **0 walls on
  walked cells**. Guaranteed by the `dm_walk_frees_wall` rule, and that rule is **load-bearing**
  (the gate shows depth alone calls a cell a wall, then walking it flips it to free — §13.2).
- **(b) SEEN-vs-depth-buffer Spearman** (the depth buffer is the ORACLE ONLY): over 71 forward
  frames, **median ρ = 0.309, mean 0.263, p10 −0.196, p90 0.694, frac_pos = 0.803**. The SEEN
  depth positively correlates with ground truth on 80% of frames — genuine seeing, bounded.

**HONEST DEGRADE (carried, not hidden):** map fidelity is bounded by seen-depth quality. On the
coarse DOWN=2 quantized flow the sensor NULLs (median ρ −0.14, `seen_forward_frames = 0`, map has
no walls); full-resolution raw-luma flow (320×240, block 16) recovers median ρ 0.38 (in 158000's
0.40–0.94 band) at the cost of off-real-time flow (ties the scale wall). So the seen map is real
but NOISIER than a depth-buffer map would be — the correct, disciplined outcome, not a reason to
read the buffer.

## M3 — unknown is first-class ABSENCE

Constructed: after partial exploration, an unexplored cell has **no Cell node** (absent — neither
free nor wall), and a `frontier` `SpaceQuantum` is minted at the border (typed `region_kind =
"frontier"`); it fills only as the agent senses it. Real run: **22 frontier quanta** at the edge
of the explored region.

## Human area map (the user's steer)

The map segments explored space into human kinds that fall out of body-relative box geometry
(graph-native rules, no magic number). Constructed: a 3×3 open box → **room**, a 1-wide passage →
**corridor**, a hazard-valued box → **lava**. Real E1M1 (seed 1234): `{area: 25, corridor: 4,
frontier: 22}` — the start's irregular seen-free region decomposes into junctions/corridors, no
`room` (E1M1's opening is a zigzag, and the noisy seen-free field fragments large boxes — an
honest consequence of the bounded seen depth). `room`/`lava` are proven on the clean constructed
case; `outside`/live-`lava` need a sky/health-damage sense (named residuals).

---

## Architecture audit (the point)

- **Map accumulation is RULES, not Python.** `dm_free_new`/`dm_wall_new`/`dm_walk_frees_wall`
  GROW and MERGE the belief; `dm_kind_*` type the areas. The gate's source-audit asserts the
  ingest module (`domains/doom_map_ingest.py`) **never** writes `has_cell` (it only emits
  `observed` ObsCells + calls `run_rules`/`space_quantize`); every belief write is a rule effect.
- **Both scoring buffers stay oracles.** The map's WHOLE input is the eye (RGB flow → seen depth)
  + self-motion (pose). The VizDoom **depth buffer** is used only for the Spearman score; the
  **labels buffer** is not used at all (objects are a named residual — using labels would smuggle
  the oracle, the same shortcut as reading the depth buffer for geometry).
- **INERT by default (§9).** Every rule guards on `game.map_mode=="doom"`; no existing world sets
  it → coarse path byte-identical, oracle 222/0 unchanged.
- **§13.** cell=64 and body_w=1 are doom_world's grid; FOV=90 is the engine; the flow operating
  point was MEASURED (not tuned-to-oracle); world depth scale is the agent's own displacement.

## Gate

`tests/test_doom_ingraph_map_migrated.py` — 8 tests, **8 passed** (incl. the real E1M1 run;
skips E1M1 if WAD/VizDoom absent). Cross-process-stable (scores by occupancy/position/counts,
never node-id): 3 fresh `python3 -m pytest` processes → 8/8 each.

## WHAT I GOT WRONG

1. **First cut read the DEPTH BUFFER for geometry** — a working map (M2 traj 1.0, room/corridor
   typing) but built on a shortcut that GETS the walls instead of SEEING them, exactly the labels-
   buffer shortcut one level over. Corrected before any commit: geometry is now depth-from-motion
   on RGB flow; the depth buffer is the scoring oracle only.
2. **Coarse flow NULLed the sensor.** My first SEEN config (DOWN=2, quantized, block 8) gave
   `seen_forward_frames = 0` and median ρ −0.14 — a wall-less map. The fix was the sensor's own
   adequate operating point (full-res raw luma), MEASURED and disclosed, not tuned to the score.
3. **`expansion_gate` rejected every forward frame** (block-matched Doom flow is curl-dominated
   even mid-walk — 158000's flow wall). Gated instead on the efference-forward regime (own forward
   action + real translation), which the agent KNOWS; expansion is reported as a diag.
4. **Within-frame duplicate Cells.** The accumulation guard is a pre-pass snapshot, so two obs at
   one new pose in a single batch both minted — caught by the gate's one-Cell-per-pose invariant;
   fixed with mechanical per-frame sensor fusion (one obs/cell), cross-frame merges still the rule.
5. **Objects as a labels scaffold** — first version placed objects from the labels buffer with a
   disclosure. Dropped entirely once the source discipline was made uniform: labels are an oracle,
   so objects are a named residual (the eye's RGB carve), not a smuggled input.

## Proposed VISION_PROTOCOL.md ledger row

- **161000–161999 (the agent builds a persistent, graph-native in-graph MAP of E1M1 from its
  OWN senses + self-motion — SEEN geometry, NO Rust; new seed `doom_ingraph_map` + adapter +
  runner, engine `64dbce1e7f47…` `source_match="shared"`, oracle 212+10s/0 both sides).** The map
  is graph DATA: a `has_cell Cell{pose,value}` occupancy belief (unknown = ABSENCE, first-class),
  GROWN and MERGED by rules (`dm_free_new`/`dm_wall_new`/`dm_walk_frees_wall` — walk-free
  authoritative, the merge is a rule not a Python grid), decoded by the EXISTING `space_quantize`
  into `SpaceQuantum` areas, and TYPED into human kinds (room/corridor/area/frontier/lava) that
  FALL OUT of body-relative box geometry (§13-clean). **The WHOLE map is SEEN:** walls via
  depth-from-motion on RGB flow (block 158000) calibrated by the agent's own forward displacement
  (efference copy, 155000); the VizDoom **depth buffer and labels buffer are SCORING ORACLES
  ONLY**, never inputs (objects = named residual). **M1** map grows 1→122 cells over 80 frames,
  graph-native (read from `has_cell`/`SpaceQuantum`), 5 checkpoint PNGs. **M2** trajectory-
  consistency 1.0 / 0 walls on walked cells (guaranteed by the load-bearing merge rule) AND SEEN
  depth positively correlates with the depth-buffer oracle (Spearman median 0.31, frac_pos 0.80,
  n=71). **M3** unknown = absence (no node) + 22 frontier quanta. **HONEST DEGRADE:** map fidelity
  bounded by seen-depth quality — coarse flow NULLs (ρ −0.14), full-res raw-luma recovers ρ 0.38
  (158000's flow wall), off-real-time (scale wall). Gate `tests/test_doom_ingraph_map_migrated.py`
  8/8, cross-process-stable, E1M1-skips without the WAD. `SEED CLAIM 161000-161999 CLEAN`.
