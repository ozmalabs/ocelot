# RESULTS — GENUINE texture recognition (pattern + colour-as-sign), block 214000

Prereg: `TEXTURE_RECOGNITION_PREREG.md`, committed ALONE first at
**`e15362bdfb6411968c692c40e087e195c7f613d6`**. Off `main` HEAD **`e4cf1dc239`**.
Seed block **214000–214999** (`python scripts/seed_claim.py 214000 214999` → `CLEAN -- no
collision DETECTED`, verbatim in the prereg).

**Lead:** this replaces the 209000 edge-DENSITY salience scalar with genuine texture recognition
against the held door concept, over a richer INTEGER descriptor with two new SEEN, RGB-only
dimensions — COLOUR-as-a-sign (chroma contrast from the ambient wall) and PATTERN-as-arrangement
(the ORIENTATION of the gradient, not just its magnitude). **The honest headline: the ARRANGEMENT
dimension RECOVERS the texture-FAINT doors (sec83/sec85) the energy scalar threw away, and
DOMINATES the old scalar on both recognition AND false-positive. COLOUR is a validated independent
sign for doors whose material differs from their wall — but it is CHANCE on these particular faint
doors, because E1M1's faint doors share their wall's brown palette. The recovering mechanism is
pattern, reported straight; colour is honest signal that does not happen to fire here.**

## The null attacked (blocks 209000 / 210000)

The 209000 texture channel (`col_texture_level`) is one ENERGY scalar: per-column vertical
luma-gradient `Σ|Δluma|`, quantised 0..8. 210000 measured its residual: doors sec83/sec85 read
level ~2 on their openable faces → never recognised → **`n_use=0`, 0 opens / 10**, while a human
reads them easily. One energy number discards (a) the ARRANGEMENT of edges and (b) COLOUR entirely
(the channel is luma-only). This block adds both, integer-native and graph-native.

## The descriptor (SEEN, single-frame, integer, RGB pixels only)

`domains/doom_pattern_eye.py` (additive — `col_texture_level`, `region_descriptor`, the 209000 seed
and the 211000 geometry channel are UNTOUCHED):

- **`col_colour_level`** — per-column chroma-L1 contrast from the frame's ambient wall chroma
  (per-column mean RGB → integer luma → chroma vector → minus the per-channel median chroma). A
  region whose material/hue differs from its wall reads high even at matched luma-gradient; a plain
  wall IS the ambient → ~0.
- **`col_orientation_hist` / `col_pattern_level`** — per-column 4-bin gradient-orientation
  histogram; the shipped `pattern_level` is the quantised HORIZONTAL-GRADIENT share (= the fraction
  of edge energy forming VERTICAL image contours — door jambs / panel lines). A RATIO that
  normalises out total energy, so it sees a faint door where the magnitude scalar cannot.

The held concept lives in a NEW self-contained seed `seeds/pattern_texture_signature.json`
(`self_load_only`, default-OFF on a `TextureParams` gate): a `TextureLibrary` with a `door`
prototype carrying `tex_sig=6, colour_sig=0, pattern_sig=7, arr_thresh=1, colour_min=4`, and three
rules — `texture_salience` (novelty over all three dims), `texture_recognise_arrangement` (recognise
by the ARRANGEMENT match — the faint-door recovery), `texture_recognise_colour` (recognise by a
strong COLOUR sign — a colour-distinct region the luma channel can't see). The adapter only
quantises pixels and reads recognition back; no Python decision picks the recognition.

## SCORING ORACLE

Doors located by 210000's WAD-derived `DOORS` table (sec26/69 strong, sec83/85 faint). Door frames
captured by warping the agent to fixed distances along each door's openable face-normal and
orienting at it; plain-wall frames by facing plain E1M1 walls. Door-vs-wall separation is scored on
central-band columns; pose-distance (geometric) selects mid-distance frames. **The depth buffer is
never read by any descriptor** (source-audited); it only labels/filters. `scripts/
texture_signature_measure.py` → `results/pattern_eye/texture_signature.json`.

## G-faint (HEADLINE) — RECOVERED, via PATTERN

Door-vs-wall AUC (central columns, mid-distance; RAW pre-quantisation features; frame-bootstrap 95%
CI; n_door=20 per class, n_wall=46):

| channel (SEEN, RGB) | FAINT doors AUC | 95% CI | STRONG doors AUC | 95% CI |
|---|---|---|---|---|
| `tex_energy` (209000 scalar) | 0.685 | [0.558, 0.806] | 0.970 | [0.921, 1.000] |
| `colour_contrast` (new sign) | **0.471** | [0.333, 0.605] | 0.726 | [0.598, 0.845] |
| **`pattern` arrangement (new)** | **0.943** | **[0.884, 0.985]** | 0.985 | [0.957, 1.000] |

**On the faint doors the arrangement AUC 0.943 [0.884, 0.985] beats the energy scalar's 0.685
[0.558, 0.806] — CI-separated (0.884 > 0.806).** The scalar was throwing the arrangement away.
Colour is chance on the faint doors (0.471, CI spans 0.5).

**End-to-end through the held graph** (the eye's real quantised descriptor → the seed rules; same
frames; operating point `pattern_sig=7, arr_thresh=1, salience_floor=2`):

| | faint recognition | strong recognition | plain-wall FALSE-POSITIVE |
|---|---|---|---|
| **richer descriptor (214000)** | **0.60** | 0.95 | **0.13** |
| old scalar (209000) | 0.10 | 1.00 | 0.30 |

**The richer descriptor DOMINATES on both axes — 6× the faint-door recovery (0.60 vs 0.10) at less
than half the plain-wall false-positive (0.13 vs 0.30).** Every faint-door recognition fired via
`arrangement` (0 via colour). The mechanism: doors devote ~30 % of their gradient energy to
vertical contours (jambs/panel lines) vs walls' ~13 % (median hshare doors 219–322 ‰ vs walls
132 ‰), a RATIO independent of the faint total energy — which also REJECTS the busy textured wall
that fools the energy scalar (the 0.30 → 0.13 FP drop).

**Honest outcome:** OUTCOME 1 (recovered) — via PATTERN. Not via colour.

## G-colour — colour is a real INDEPENDENT sign, but not the recovering one HERE

- **Independent signal (real pixels):** colour separates the STRONG doors from wall at AUC **0.726
  [0.598, 0.845]** (CI excludes 0.5) — a genuine door-vs-wall material contrast the luma-only
  channel cannot represent.
- **The luma channel is blind to it (synthetic control, `test_colour_sign_sees_what_luma_cannot`):**
  a central patch LUMA-matched to its grey surround but red-tinted reads the SAME `col_texture_level`
  (±1) yet lights up `col_colour_level` (+≥4); the graph recognises such a colour-only door via the
  `colour` path (`test_colour_only_door_recognised_and_independent_of_luma`), invisible to the scalar.
- **Honest limit:** on the *faint doors* colour is CHANCE (0.471) — sec83/sec85 are chromatically
  near-identical to their wall (measured cen−edge chroma ≈ 0–4 units; E1M1 doors and walls share the
  brown palette). Colour-as-a-sign is real and independently validated; it simply does not fire on
  these particular doors. The recovery is pattern's.

## G-pattern — arrangement carries signal BEYOND energy

`test_pattern_carries_signal_beyond_energy`: a HIGH-energy horizontal grating (wall-course-like) has
`pattern_level` 0 while a LOW-energy vertical grating (door-jamb-like) reads 8 — energy and
arrangement are DECOUPLED (the wall-like grating has ~5× the total gradient energy yet a LOWER
pattern level), and the level is a RATIO (invariant to amplitude scaling). On real pixels the same
ratio is what separates faint doors (hshare 219–322 ‰) from walls (132 ‰) at MATCHED-or-lower energy.

## G-no-oracle — the descriptor reads ONLY rendered RGB

AST audit (`test_new_descriptor_reads_only_rendered_pixels_source_audit`) over `_mean_rgb_band`,
`col_colour_level`, `col_orientation_hist`, `col_pattern_level`: no `depth_buffer` / `labels` /
`sectors` attribute, no `["depth"]`/`["label"]`/`["texture"]` subscript, no texture NAME. **Exactly
what the descriptor samples:** the rendered RGB screen buffer only — integer luma
`(77R+150G+29B)>>8` for the pattern/energy dimensions, and the integer colour channels `rgb[...,0/1/2]`
for the chroma-contrast sign. Depth is a SCORING oracle for AUC/labels, never fed to the eye.

## G-no-regression — PASS

- **10/10 `test_pattern_recognition_migrated`** (the 209000 gate) green under the shared-file change
  (`col_texture_level`, `region_descriptor`, the 209000 seed all untouched; new code is additive).
- **16/16 sibling tests** — `test_robust_geometry_migrated` (211000) + `test_doom_operate_migrated`
  (210000, the strong-door opens) green.
- **`rung7_vision_bench` oracle: 214 passed / 10 skipped BEFORE == 214 passed / 10 skipped AFTER.**
- **`per_area_settlement_regression`: 23 failed / 277 passed / 5 skipped AFTER — identical to the
  210000/211000 documented baseline** (the pre-existing `test_topic_route_selfheal_migrated`
  fixture/`data/` failures). BEFORE == AFTER by construction — no test in either bench imports the
  changed module; the only 4 tests importing `doom_pattern_eye` are pattern/robust-geometry/operate/
  texture, none listed in these benches.
- **9/9 `test_texture_recognition_migrated`** (the new gate) green.

## G-discipline — PASS

- **Integer-native:** every descriptor dimension and all rule arithmetic (`Abs`/`Minus`/`Plus`/
  `Gte`/`Lte`) are integers; no float reaches the graph
  (`test_descriptor_levels_and_salience_are_integer`, `test_integer_descriptors_from_synthetic_pixels`).
- **Default-OFF byte-identical:** the seed is `self_load_only` (skipped by `load_all_seeds`); every
  rule gates on an enabled `TextureParams`; absent it no rule fires and no attr is written
  (`test_default_off_is_byte_identical`). The new module functions are imported by nothing existing.
- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED** (no Rust).
- **`runners/dsl` diff EMPTY; `term.rs` diff EMPTY.** `source_match`: the engine-provenance gate
  (`test_engine_provenance_migrated`) passes inside `rung7_vision_bench` — the worktree engine is the
  canonical tree's, byte-for-byte.
- Only one tracked file changed (`domains/doom_pattern_eye.py`, additive); new seed/test/scripts.

## Honest residuals / named follow-ons

- **Colour doesn't recover THESE faint doors** — E1M1's faint doors share the wall palette. A world
  with materially-distinct doors would exercise the colour path; **full colour-CATEGORY grounding**
  (naming hues as signs, not just contrast) is the next step for colour.
- **Operating-point trade-off:** at `arr_thresh=1` faint recovery is 0.60 at 0.13 FP; `arr_thresh=2`
  lifts faint recovery to 0.90 at 0.17 FP (still below the scalar's 0.30). The threshold-free AUC
  0.943 is the headline; the shipped default is the conservative low-FP cut.
- **Learned texture prototypes** — the door signature is calibrated (competent-man), not learned; the
  sd-loop could grow `TexturePrototype`s from observation.
- **The context/memory channel** — a human also uses expectation (knowing a door is there). Pattern
  suffices for sec83/sec85, but a single-frame eye has no priors; a memory/context channel is the
  named path for doors below even the arrangement floor.
