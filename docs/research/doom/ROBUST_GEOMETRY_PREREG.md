# PRE-REGISTRATION — a SEEN geometry channel that beats chance on real E1M1 (block 211000)

Committed ALONE, before any measurement. Off `main` HEAD **`6952055056`**.
Seed block **211000–211999** (`python scripts/seed_claim.py 211000 211999` → verbatim below).

## The honest null this attacks (block 209000)

209000 recognises doors/switches by TEXTURE (vertical-gradient luma energy, ~60× plain-vs-marked,
AUC-clean). Its GEOMETRY channel is CHANCE on real frames: SEEN depth-from-motion per-column
deviation scored **AUC 0.508** over 31,664 columns vs the depth-buffer structural oracle. So the
pre-registered "differing GEOMETRY" contributed nothing; texture carried the whole result. This
block looks for a **SEEN geometry feature that beats chance with a real margin** feeding the same
`PatternLibrary` geometry-level (`col_geometry_level` in `domains/doom_pattern_eye.py`).

## HARD CONSTRAINT (unchanged from 209000) — no oracle

The geometry signal comes ONLY from SEEN rendered pixels (integer luma) + the agent's OWN motion.
The VizDoom **depth buffer / sectors / labels buffer / texture names are NEVER read by the eye** —
they are a SCORING ORACLE only (for computing AUC). AST-audited (below).

## Candidate SEEN geometry features (measured, not assumed)

A door's "differing geometry" is a framed/recessed sector — a **depth discontinuity / occluding
contour** (the "edges are grounded contours" line). A depth edge is a VERTICAL contour in the image
(depth steps left→right along a column). Its natural SEEN signature is the **horizontal** luma
gradient — orthogonal to the texture channel's **vertical** gradient. Candidates, each measured:

1. **`hgrad_energy` (primary)** — per-column integer sum of `|Δluma|` ACROSS columns (horizontal
   gradient) in the central band. A vertical structural edge (door frame / recess boundary / corner)
   reads high; a flat wall reads ~0. Pixels only, single frame, no motion needed.
2. **`dfm_grad` / `dfm_depth` (baseline family)** — the 209000 SEEN depth-from-motion per column
   (its |gradient| and raw deviation), scored on the SAME oracle for an apples-to-apples comparison.
3. **`vgrad_texture` (control)** — the existing texture channel, to prove geometry is SEPARABLE from
   texture (texture is a confound because marked surfaces cluster near structural features).
4. Multi-frame parallax accumulation of depth-from-motion (temporal median over a dwell window) —
   probed as a diagnostic (expected to degrade under view shift; reported straight).

## SCORING ORACLE (depth buffer — SCORING ONLY, never fed to the eye)

The 209000 `_struct_oracle` = `(depth-deviation ≥ p85) OR (depth-gradient ≥ p92)` marks ~42 % of
columns positive and is DOMINATED by depth DEVIATION (flat surfaces at non-modal depth — a distant
corridor wall), which a per-column EDGE feature cannot and should not detect. It is a poor target
for a geometry-EDGE channel. We report it for continuity, but the PRINCIPLED geometry target — the
thing a door's framing IS — is the **occluding contour / depth EDGE**:

> **`depth_edge_oracle(pct)`**: per column, the median depth over the central band (rows GH/3..2GH/3);
> a column is POSITIVE iff `|horizontal gradient| of that per-column depth ≥ max(percentile(grad,pct),
> 1.0)`. Computed PURELY from the depth buffer (no luma). Reported at `pct ∈ {90,95,97}` (robustness).

## GATES (pre-registered bars)

- **G-geometry (headline).** On the `depth_edge_oracle` (pct=95), the primary SEEN feature
  `hgrad_energy` reaches **AUC ≥ 0.65 with the 95 % CI (frame-level bootstrap) excluding 0.5**, over
  **N ≥ 3000 scored columns with ≥ 1000 positives**, and BEATS both the 209000 depth-from-motion
  baseline (on the same oracle) and chance by a real margin. Reported: AUC + CI + N for EVERY feature
  (hgrad, dfm family, texture) on BOTH the `depth_edge_oracle` AND the 209000 `_struct_oracle`
  (apples-to-apples), across two independent walks + combined. **If the best SEEN feature stays near
  chance, that is an HONEST NULL reported straight with the number — no faked AUC.**
- **G-both-channels.** With the improved geometry, geometry AND texture EACH contribute: (a) on real
  pixels, `hgrad_energy` still separates depth-edges WITHIN texture-quantile strata (a geometry-only
  signal at matched texture); (b) a geometry-only recognition difference — two regions with IDENTICAL
  `tex_level` but different `geom_level` (one from a real door-frame column, one from a real flush
  column) recognise/salience differently — the thing 209000 could NOT do. Report the number.
- **G-no-oracle (load-bearing).** AST + runtime audit: `col_geometry_level` (and its helper) may NOT
  access `depth_buffer`/`labels_buffer`/`labels`/`sectors`, nor index `["depth"]`/`["label"]`/
  `["texture"]`/`["linedef"]`. State exactly what it samples: rendered RGB → integer luma
  `(77R+150G+29B)>>8` → integer sum of `|Δluma|` across columns → integer-divide to a 0..K level.
- **G-discipline.** Integer-native (the descriptor level is integer division of an integer gradient
  sum; the eye touches no float that reaches the graph). Default-OFF byte-identical (the geometry
  feature is only consumed when the opt-in `PatternParams` gate exists; the seed stays
  `self_load_only`; no existing boot imports the eye). Canonical `.so` md5 stays
  **`793ce09ed498a749abb79aeaea44b92e`**; `runners/dsl` diff EMPTY incl. `term.rs` (NO Rust — if Rust
  is needed, STOP and report). Oracle `bash scripts/rung7_vision_bench.sh` BEFORE == AFTER; 34-file
  `bash scripts/per_area_settlement_regression.sh` failing-node-id SET BEFORE == AFTER;
  `source_match` reported.

## Reproduce

```
python scripts/robust_geometry_measure.py        # AUC per feature × oracle × walk -> results/pattern_eye/robust_geometry.json
pytest tests/test_robust_geometry_migrated.py     # integer / no-oracle / default-off / both-channels
```

## seed_claim (verbatim)

Filled in the commit body below.
