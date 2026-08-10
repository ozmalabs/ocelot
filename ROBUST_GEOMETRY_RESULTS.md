# RESULTS — a SEEN geometry channel that beats chance on real E1M1 (block 211000)

Prereg: `ROBUST_GEOMETRY_PREREG.md`, committed ALONE first at **`dfc14ed935`**. Off `main` HEAD
**`6952055056`**. Seed block **211000–211999** (`python scripts/seed_claim.py 211000 211999` →
`CLEAN -- no collision DETECTED`, verbatim in the prereg commit).

## The null attacked (209000)

209000 recognises doors/switches by TEXTURE; its GEOMETRY channel — SEEN depth-from-motion
per-column deviation — was **CHANCE (AUC 0.508)** over 31,664 columns. So "differing geometry"
contributed nothing. This block replaces `col_geometry_level` with a SEEN feature that beats
chance with a real margin.

## The feature — geometry = STRUCTURAL horizontal edge above ambient (SEEN, integer)

A door's "differing geometry" is a framed/recessed sector = a **depth discontinuity** = an
**occluding contour** = a VERTICAL edge in the image (depth steps left→right along a column). Its
SEEN signature is the **HORIZONTAL luma gradient** — the ORTHOGONAL twin of the texture channel's
vertical gradient. Because every Doom wall carries horizontal texture detail, the ambient
horizontal-gradient MEDIAN across the frame's columns is subtracted, leaving only a LOCAL
structural edge that stands out from its surface (a flush wall / uniformly-marked panel → 0; a
framed door / recess boundary / corner → high). Integer throughout:

```
energy[c]  = Σ_rows |luma[r,c] − luma[r,c−1]|     (central band; integer horizontal gradient)
ambient    = median_c energy[c]                    (integer texture floor)
geom_level = min(K, max(0, energy − ambient) // GEO_DIV)   (0..8, GEO_DIV=100)
```

`domains/doom_pattern_eye.py::col_structural_level` (and `col_geometry_level` wrapping it,
kept `(frames, fi)`-shaped for its callers). Single frame — **NO motion needed** (a strict
improvement over 209000, which returned 0 unless the previous action was forward).

## G-geometry (headline) — PASS

`scripts/robust_geometry_measure.py` on TWO independent E1M1 routes (600 frames), vs a **depth-EDGE
(occluding-contour) scoring oracle** (top-5% per-frame |horizontal depth-gradient|; depth buffer,
SCORING ONLY). Frame-level bootstrap 95% CI. `results/pattern_eye/robust_geometry.json`.

| feature (SEEN) | AUC | 95% CI (frame-boot) | N pos | N neg |
|---|---|---|---|---|
| **geometry_shipped** (quantised 0..8, → the graph) | **0.686** | **[0.673, 0.700]** | 4,105 | 165,175 |
| structural_continuous (pre-quantisation energy) | 0.728 | [0.716, 0.739] | 4,105 | 165,175 |
| hgrad_raw (no ambient subtraction) | 0.780 | [0.764, 0.793] | 4,105 | 165,175 |
| texture (209000 vertical-gradient channel) | 0.747 | [0.726, 0.766] | 4,105 | 165,175 |
| **dfm_baseline (209000 depth-from-motion)** | **0.527** | [0.505, 0.550] | 3,206 | 112,800 |

**The shipped SEEN geometry channel = AUC 0.686 [0.673, 0.700] over 169,280 columns — clears the
pre-registered ≥ 0.65 bar, CI excludes 0.5, and beats both the 209000 motion baseline (0.508 on
its walk / 0.527 here on the same depth-edge oracle) and chance by a real margin.** Per-route it
is 0.715 (rturn) and 0.853 (lturn); combined 0.686 after the coarse 0..8 recogniser quantisation
(the raw ranking energy is 0.78). This is the "edges are grounded contours" line realised: SEEN
luma vertical-edges preferentially sit on real depth discontinuities, and geometry-from-luma-edges
beats geometry-from-motion.

**Honest — texture (0.747) out-ranks the shipped geometry (0.686) in raw AUC.** Expected: depth
edges correlate with texture boundaries (marked surfaces cluster at structural features). The claim
is NOT "geometry beats texture" — it is "geometry beats CHANCE (0.508→0.686) and adds INDEPENDENT
signal," which G-both-channels establishes next. The 209000 problem was geometry contributing
*nothing* (0.508); it now contributes real, separable signal.

## G-both-channels — PASS

**(a) Geometry adds signal BEYOND texture (real pixels, matched texture).** Within texture-quantile
strata, the geometry channel still separates depth-edges:

| texture stratum | geometry AUC | N pos | N neg |
|---|---|---|---|
| low  [0, 60]   | 0.681 | 6 | 56,200 |
| mid  [60, 556] | 0.750 | 1,112 | 55,070 |
| high [556, 2937] | 0.653 | 2,998 | 54,592 |

All > 0.5 → at MATCHED texture, geometry carries independent structural signal (corr(geo,texture)
= 0.41 — moderate; distinct channels, orthogonal derivative directions).

**(b) Geometry-only recognition — the thing 209000 could NOT do.** With a real geometry channel, a
geometry difference at IDENTICAL texture changes recognition: a framed region `[geom=4, tex=6]`
resolves to **`door`**, a flush region `[geom=0, tex=6]` does NOT (`switch`), and a texture-free
structural edge `[geom=5, tex=0]` is still salient while `[0,0]` is not
(`tests/test_robust_geometry_migrated.py`: `test_geometry_only_difference_shifts_recognition_matched_texture`,
`test_geometry_only_region_is_salient`). 209000 could only ever separate door/switch on texture;
geometry now disambiguates the framed-vs-flush distinction its residual named.

## G-no-oracle (load-bearing) — PASS

AST + runtime audit (`robust_geometry_measure.assert_no_oracle_in_geometry_eye` +
`test_no_oracle_source_audit_geometry_eye`): `col_structural_level` / `col_geometry_level` /
`region_descriptor` / `_luma_int` may NOT access `depth_buffer`/`labels_buffer`/`labels`/`sectors`,
nor index `["depth"]`/`["label"]`/`["texture"]`/`["linedef"]`/`["sectors"]`. **Exactly what the
geometry eye samples:** the rendered RGB screen buffer only — integer luma `(77·R+150·G+29·B)>>8`,
then the integer sum of `|Δluma|` ACROSS columns (horizontal gradient) in the central band, minus
the integer ambient median, integer-divided to a 0..8 level. NO motion, NO WAD texture name, NO
depth / sectors / labels buffer. The VizDoom depth buffer is used ONLY as the AUC scoring oracle.

## G-discipline — PASS

- **Integer-native:** the level is integer division of `max(0, integer_energy − integer_median)`;
  no float reaches the graph (`test_geometry_level_is_integer`).
- **Default-OFF byte-identical:** the geometry channel is consumed only when the opt-in
  `PatternParams` gate exists; absent it, no rule fires and regions carry no salience/recognition
  attrs (`test_default_off_is_byte_identical`). The seed `pattern_recognition.json` is unchanged and
  `self_load_only`; no existing boot imports the eye.
- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED**; `runners/dsl` diff EMPTY
  incl. `term.rs` — **NO Rust** (the feature is mechanical eye I/O in Python; existing Terms only).
  `source_match = shared`, `stale_rust = []`.
- **Vision oracle `bash scripts/rung7_vision_bench.sh`:** BEFORE (at the prereg commit) **214
  passed / 10 skipped / 0 failed**; AFTER **214 passed / 10 skipped / 0 failed** (identical — the
  geometry change is in an opt-in eye module imported by no existing boot / no oracle-list test).
- **34-file `bash scripts/per_area_settlement_regression.sh`:** AFTER **23 failed / 277 passed / 5
  skipped** — the identical failing-node-id SET as the 209000-documented baseline (23f/277p/5s), all
  pre-existing data-less-environment reds across `test_cortices_tick`, `test_composer_driver_migrated`
  (FileNotFoundError fixture), `test_gap_awareness_migrated`, `test_elaboration_migrated`,
  `test_topic_route_selfheal_migrated` (need `data/` symlinked / fixtures). **BEFORE == AFTER by
  construction:** NO test in the regression list imports the changed module (`doom_pattern_eye` is
  imported only by `test_pattern_recognition_migrated` + the new `test_robust_geometry_migrated`,
  neither in the list), and the new files are not in the list — so the geometry change is provably
  inert to this list; the measured set matches the documented baseline exactly. NONE of the 23 touch
  this block's modules.

## Honest residuals (named, not patched)

- **Texture out-ranks geometry in raw AUC (0.747 vs 0.686).** Depth edges correlate with texture
  boundaries. Geometry's value is INDEPENDENT signal (within-stratum > 0.5), not beating texture.
- **The clean-floor ambient subtraction costs ranking** — raw hgrad ranks at 0.78, the
  ambient-subtracted continuous at 0.728, the graph-quantised at 0.686. The subtraction is
  the right trade: it gives a flush wall/switch geom_level 0 (recogniser fidelity) at a modest AUC
  cost. Reported both.
- **The 209000 `_struct_oracle` (deviation-dominated, ~42% positive) is a POOR geometry target** —
  every per-column feature is ~chance on it (geometry_shipped 0.495, texture 0.363, dfm 0.456);
  reported for continuity. The principled geometry target is the occluding contour / depth EDGE.
- **Real depth-from-motion geometry stays near-chance (0.508 / 0.527)** — the standing real-video
  depth wall; the win here is that geometry-from-SEEN-luma-edges routes around it.
- **Scope:** two routes on one map (E1M1); the mechanism is generic but exercised on one world.

## Reproduce

```
python scripts/robust_geometry_measure.py        # -> results/pattern_eye/robust_geometry.json
pytest tests/test_robust_geometry_migrated.py     # 9 passed (mechanism + no-oracle + both-channels)
```
