# RESULTS — A GENERIC PATTERN-RECOGNITION EYE THAT RECOGNISES DOORS/SWITCHES ON SIGHT (block 209000)

Prereg: `DOOR_SWITCH_RECOGNITION_PREREG.md`, committed ALONE first at
**`301303d443bbe448df7ae6948c81ab034463fa27`**. Off `main` HEAD **`e8105953e4`**.
Seed block **209000–209999** (`scripts/seed_claim.py 209000 209999` → `CLEAN`).

## The build — and two owner steers that shaped it

The competent-man Jabberwock HOLDS the concepts `door` and `switch` and recognises them
on sight, then investigates. Two mid-build steers moved the design to its right form:

1. **"Spotting *a different type of thing* is easy; naming it a switch needs a closer
   look."** → recognition is TWO-TIER: a COARSE family match at distance (robust) and a
   FINE door/switch match up close (harder, and the reason to approach).
2. **"It should be a generic shape/pattern matching system — an eye that happens to work
   in Doom, not a Doom-playing eye"** (and *"floating point and Python decisions are not
   allowed"*). → the mechanism is a **GENERIC, INTEGER-NATIVE, graph-native pattern
   matcher**; `door`/`switch` are just two entries in a held prototype library; every
   decision is a rule; the eye only quantises pixels to integer tokens.

So this block delivers a domain-free mechanism (`seeds/pattern_recognition.json`) plus a
Doom world-adapter eye (`domains/doom_pattern_eye.py`) and a real-E1M1 run
(`scripts/doom_pattern_eye_run.py`). The prereg's Doom-specific, float draft is superseded
by this generic integer realisation; the prereg GATES are unchanged and reported below.

### The generic mechanism (integer, graph-native — no Python decision)

`PatternLibrary` holds `PatternPrototype`s, each an integer descriptor `[geometry_level,
texture_level]` (0..K), a label, a tier, and (optionally) an affordance. Four generic rules:

- **`pattern_salience`** — SALIENCE == generic novelty: integer L1 distance of a region's
  descriptor from the `background` prototype. Background match → 0 → not salient (the
  false-positive control is intrinsic and integer).
- **`pattern_recognise_coarse`** (FAR) — a salient region clearing the family bar IS the
  held `operable_feature` (a candidate door/switch); mints an APPROACH goal.
- **`pattern_recognise_fine`** (NEAR, `R.near==1`) — nearest FINE prototype by integer L1
  distance under its threshold → `recognised_as` door/switch. Scramble a prototype's
  descriptor → distance blows up → no match.
- **`pattern_investigate_operate`** — a fine recognition + its held affordance → OPERATE goal.

`door`/`switch`/`background`/`operable_feature` are graph DATA. All arithmetic is integer
(`Plus`/`Minus`/`Abs`/`Gte`/`Lt`); the float L2 `Magnitude` of the `figure_geometric_shape`
idiom is replaced by integer L1 (`Abs(Minus)+Abs(Minus)`). In-frame observations are integer
by construction; the only continuous step is the cross-frame optical-flow map inside
depth-from-motion, whose output is quantised to an integer level before it reaches the graph.

## G-salient (both channels) — PASS on texture; geometry is the named residual

Controlled scenes on real E1M1 (`results/pattern_eye/gates.json`), eye vs a plain-wall
false-positive control. The texture channel is the calibrated absolute signal: a plain
structural wall has per-column vertical-gradient energy `vgrad` median **0.10**; the
computer/switch panel median **6.28** (≈60×), so an integer quantised `texture_level`
(0..8) reads **0** on plain wall and **6–8** on marked surfaces.

| scene | class | median tex_level | salient fraction | coarse `operable_feature` |
|---|---|---|---|---|
| plain_wall_SE | plain | 0 | **0.000** | 0 |
| plain_wall_W | plain | 0 | **0.000** | 0 |
| plain_wall_SW | plain | 0 | **0.000** | 0 |
| plain_wall_NW | plain | 0 | **0.000** | 0 |
| panel_switch_N | distinct | 7 | 1.000 | 80 |
| courtyard_grille | distinct | 8 | 0.950 | 76 |
| tech_wall_SE | distinct | 4 | 0.963 | 77 |
| tech_wall_NE | distinct | 7 | 0.975 | 78 |

**Mean salient fraction: plain 0.000 vs distinct 0.972.** A plain wall is flagged in ZERO
columns (the false-positive control); every distinct surface is flagged salient AND
coarse-recognised as the held `operable_feature` — "that's a different type of thing."

**Both channels contribute (mechanism, synthetic proof, integer):** a geometry-only region
`[4,1]` and a texture-only region `[0,6]` are each salient; together `[4,6]` higher
(`test_pattern_recognition_migrated`, and the smoke matrix). ON REAL PIXELS, however, the
SEEN geometry channel is unreliable — see the residual below — so the real-scene headline
rests on texture, exactly the **pre-registered narrow condition** ("if depth-from-motion is
too noisy, report the number and lean on texture").

## G-recognise — PASS; concept-scramble control bites

`tests/test_pattern_recognition_migrated.py` (10 passed). Synthetic held descriptors:
`door[4,6]`→door, `switch[0,7]`→switch, `plain[0,0]`→neither. On real E1M1 all four distinct
scenes coarse-recognise as `operable_feature`; the panel resolves to `switch` up close
(marked, ~flush → switch-family).

**Concept-scramble control:** corrupt the held `door` prototype descriptor (`[4,6]→[0,0]`)
and door FINE recognition FAILS (`recognised_as` None) while the COARSE family detection
stays robust and `switch` is unaffected — the held pattern does the work, not a hardcoded
detector. (`test_concept_scramble_breaks_fine_keeps_coarse`.)

## G-no-oracle (load-bearing) — PASS

The eye's appearance path is source-audited by an AST check (runtime, in the run + a test):
the texture eye (`_luma_int`, `col_texture_level`) may NOT access `depth_buffer` /
`labels_buffer` / `labels` / `sectors`, nor index `["depth"]`/`["label"]`/`["texture"]`.
**Exactly what the eye samples for texture:** the rendered RGB screen buffer only — integer
luma via the ITU-R BT.601 approximation `(77·R + 150·G + 29·B) >> 8`, then the integer sum
of `|Δluma|` down each column band, quantised by integer division to a 0..8 level. No WAD
texture NAME, no labels buffer. The VizDoom **depth buffer** and **sectors** are used ONLY
as a SCORING ORACLE (structural-anomaly labels for the geometry AUC below; closed-door /
door-open detection) and never enter the eye.

## G-investigate — coarse→fine over a real approach; live door-OPEN named as residual

Over a real forward approach to the panel wall (`proximity_coarse_to_fine`): **FAR**
(travelled 0.8 units) the salient region is recognised only as the coarse family
`operable_feature` (a different kind of thing → the held affordance mints an APPROACH goal);
**NEAR** (travelled 297.5 units, `near=1` set from the agent's own travelled distance — a
proprioceptive/efference signal) the FINE prototype resolves to **`switch`** and an OPERATE
goal is minted. Recognition → investigation is the graph's decision (the prototype carries
the affordance). Investigations minted: `approach_to_resolve` per salient region + `operate`
per fine recognition.

**Honest residual (pre-declared):** autonomous operation of a live DR door in E1M1 (USE →
sector ceiling rises) was probed and does NOT reliably trigger — **0 door-open events over
600 + 1200 USE-spammed autonomous tics** in the open, pillared start region (the ceiling==
floor sectors near spawn are decorative pillars/windows, not operable doors). So the OPERATE
goal is minted and the orient/approach behaviour is shown, but an actual door OPENING is not
demonstrated autonomously — named, not faked.

## G-discipline — PASS

- **Integer-native:** descriptors, salience (integer L1), and thresholds are all integers
  (`test_descriptors_and_salience_are_integer`); no float `Magnitude`. In-frame values
  integer; the continuum stays in the cross-frame optical-flow map, quantised before the graph.
- **Default-OFF byte-identical:** every rule gates on a `PatternParams{enabled}` node the
  adapter creates only on opt-in; absent it, no rule fires and regions carry no salience/
  recognition attrs (`test_default_off_is_byte_identical`). The seed is `self_load_only`, so
  `load_all_seeds` SKIPS it (`substrate/boot_all.py`) — it never enters any existing boot.
- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (the loaded
  `runners/dsl/python/substrate_rs/_native.abi3.so`).
- **`runners/dsl` diff EMPTY** (incl. `term.rs`) — no Rust. `source_match = "shared"` (the
  loaded engine is the shared canonical `.so`; the worktree Rust source is byte-identical /
  empty diff). `stale_rust = []`.
- **Vision oracle `bash scripts/rung7_vision_bench.sh`:** BEFORE (at the prereg commit)
  **214 passed / 10 skipped / 0 failed**; AFTER identical (the new seed is `self_load_only`,
  the new modules are imported by nothing existing).
- **`bash scripts/per_area_settlement_regression.sh`:** **23 failed / 277 passed / 5 skipped,
  BEFORE == AFTER** — the failing-node-id SET is unchanged. All 23 are pre-existing
  data-less-environment reds (conversation/topic/gap/elaboration/cortices tests that need
  `data/` symlinked or fixture files present); NONE touch this block's modules, and the seed
  is `self_load_only` (provably cannot affect any of them). Failing set enumerated in the run log.

## Honest residuals (named, not patched)

- **SEEN depth-from-motion geometry is unreliable per-column on real frames** — AUC **0.508**
  vs the depth-buffer structural oracle over 31,664 columns (near-chance). This is the
  pre-registered hard part; the real-scene headline leans on the texture channel. Robust SEEN
  geometry (unifying the integer depth/occupancy reconstruction of 205000/161000 with this
  texture channel) is the named next step.
- **Door-vs-switch fine disambiguation is texture-dominated.** Without reliable geometry the
  marked panel resolves to `switch` (marked + ~flush); separating a `door` (framed/recessed
  geometry + marked surface) from a `switch` on geometry is the residual that the robust
  geometry channel would close.
- **Live DR-door OPEN not autonomously demonstrated** (above).
- **Scope:** small controlled scene set (8 scenes), single map (E1M1). The mechanism is
  generic but is exercised here on one world; other worlds/prototypes are untested.

## Reproduce

```
python3 scripts/build_pattern_recognition_seed.py          # emit seeds/pattern_recognition.json
pytest tests/test_pattern_recognition_migrated.py          # 10 passed (mechanism + controls)
PYTHONPATH=. python3 scripts/doom_pattern_eye_run.py       # real-E1M1 numbers -> results/pattern_eye/gates.json
```
