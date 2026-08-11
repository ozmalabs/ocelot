# STEREO — DEPTH FROM N SIMULTANEOUS EYES — results

**Pre-registration:** `VISION_STEREO_PREREG.md`, committed BEFORE the run at
`e634ed6c` (§3). **Runner:** `scripts/stereo_measure.py` (→ `results/stereo_measure.json`);
retinal probe `scripts/stereo_retina_probe.py`. **Gate:** `tests/test_stereo_infer_migrated.py`.
**Engine:** `62d8fbbb23b8` — `[shared build from …/gamma-substrate — Rust source
identical]` (§10.1 rule 4: this rung adds NO Rust and NO seed, so the shared,
source-identical canonical build is the correct and legitimate engine; the
provenance gate passes in both trees). **Bench condition:** `data/` symlinked to
canonical → **200/0** (would be 190/10 without, §10.2).

## HEADLINE — `DepthInfer` GENERALIZED across frame-source. No `StereoInfer`.

**The prediction held exactly.** The mechanism was read first (§12.4):
`eval_depth_infer` consumes a `sequence` of frames and requires each surface to be
a rigid constant-velocity translate ACROSS THE SEQUENCE — it has **no notion of
time**; the axis is whatever the adapter puts in the sequence. Fed **N-EYE frames
at one instant** (each eye's view = every surface shifted by `baseline × disparity`),
the **UNCHANGED `DepthInfer` Term + the UNCHANGED `depth_axis` seed rules** mint the
**SAME `latent:depth`** they mint from N-tick frames:

```
N=3 eyes, RED disp 2 (near) + BLU disp 1 (far)
  -> latent:depth { n_layers: 2, velocities: ((0,-2),(0,-1)), ordering: (red, blue) }
```

**Frame-source (eyes vs ticks) is the ONLY difference.** No new Rust, no new seed
rule, no `StereoInfer` sibling. This is the unification proof in code: **eyes and
ticks are the same resource** — disparity is the inter-eye translate exactly as
velocity is the inter-tick translate, and the SAME residual-of-a-single-generator
decision recovers depth from either.

## The decisive pair (run FIRST)

- **H_single — a SINGLE-depth scene mints NOTHING.** Multi-colour at ONE disparity
  (N=2 and N=3) AND a scene at infinity (zero disparity, N=3) → `depth_none`, no
  `latent:depth`. One inter-eye generator carries every eye ⇒ residual ZERO ⇒ no
  mint. Depth from disparity VARIATION, never from having multiple eyes/surfaces.
  *A single-depth scene minting depth would be the §1.1/§13 disease — it does not.*
- **H_stereo — ≥2 depths mint + COMPRESS.** 2 layers (disparities 2,1) at N=3 →
  `latent:depth{n_layers:2}`, ordering near→far (larger disparity = nearer),
  **MDL 18→13 (1.38×)** — the depth dimension pays vs enumerating every eye's every
  cell. (The ratio grows with eye count; N=3 is reported to keep the cardinality
  point.) Eye count read from the graph = 3.

## The cardinality demonstration — BUILD FOR N (the point)

- **H_cardinality — SAME frozen machinery at N=2 AND N=3, count from the graph.**
  The runner instantiates N `Eye` hub nodes and reads them BACK via `Count(Eye
  hubs)` (`len(eyes_in_graph(s))`); `frames.len() == Count(Eye hubs)` for every arm.
  Clean 2-depth scene: N=2 (eyes_from_graph=2) and N=3 (eyes_from_graph=3) mint the
  **same ordering** `(red, blue)`. **No literal eye count in any decision path.**
- **N=3 is MORE PRECISE than N=2.** On an INCONSISTENT-disparity surface (BLU
  shifts −1 then −2 across eyes — not a rigid single depth), **N=2 has ZERO
  verification pairs and MINTS the unreliable layering (`depth_inferred`); N=3's
  extra baseline is a verification pair that REJECTS it (`depth_none`).** More
  baselines ground the same depth tighter — fewer false layers. On a CLEAN scene
  N=2 and N=3 agree.
- **The honest bound (proviso 1 held):** the precision gain is a
  VERIFICATION-REJECTION (N=3 refuses a false layering N=2 accepts), NOT a positive
  split of a clean scene — because equal baselines make integer disparity constant,
  so N=2 already resolves any clean depth. Finer/continuous-disparity resolution
  (sub-integer parallax, accumulating over a longer baseline) is **CROSS-FRAME and
  DEFERRED**, exactly as real-angle rotation is (the frame/continuum invariant).

## The other confirmatory arms

- **H_multiheld (§13.1):** 4 structures → 4 correct DIFFERENT results from one
  frozen Term (2-layer / 3-layer / a REVERSED ordering `(blue, red)` / a dedup
  3-surface→2-layer), ≥3 distinct orderings. Not same-regardless.
- **H_shuffle (mismatched eyes):** eye-ORDER shuffles at the LONGEST config **N=8**,
  **n=400** (seeds 28000–28399) → **0 spurious mints** (per-surface disparity no
  longer constant under a scramble; original/reversal counted separately — at N=8 a
  random shuffle reproduces neither, so both were 0).
- **H_downstream (§1.5/§13.2):** hold out the LAST eye, feed eyes 0…N−2 → the
  minted depth's `predicted` field (each surface advanced by its OWN disparity to
  eye-index N−1) EQUALS the held-out eye's actual view. **D_mint=1, D_pred=1** —
  load-bearing, not decoration (a single generator cannot produce this view).
- **H_offday (§9):** flag OFF → multi-depth eye-frames do not mint (inert).

## The ADDITIVE arm — the stereo payoff, measured

1. **SAME dimension:** the SAME depth structure, grounded once as N-eye-at-one-tick
   (stereo) and once as one-eye-over-K-ticks (motion) with the same depth→speed
   map, mints `latent:depth` with the **IDENTICAL ordering** `(red, blue)`.
2. **QUICKER:** stereo grounds depth at a **SINGLE tick** (N=3 simultaneous eyes,
   no temporal orbit); motion needs **K=6 ticks** to accumulate. The predator's
   "depth NOW, before the prey moves." Reported: `stereo_ticks_to_ground=1`,
   `motion_ticks_to_ground=6`.
3. **MORE PRECISE:** N=3 resolves (rejects) an ambiguous layering N=2 accepts
   (H_cardinality). N=3 > N=2.

## The RETINAL step — reached, positive

`stereo_retina_probe.py`: two DISTINGUISHABLE patterns at different disparities
across a 30×30 retina, viewed by N Eye hubs at baselines 0…N−1 at ONE instant:

- N=2 and N=3 (eyes_from_graph read = 2, 3) → depth minted, `n_layers=2`, near = the
  larger-disparity pattern, **predicts the UNSEEN eye at baseline N** exactly.
- Single-depth retina (uniform disparity) → NO depth (`single_velocity`).
- Eye-order shuffle (N=8) → floor (`non_constant_velocity`).

**Honest scope (§11.4, §8):** the two patterns are DISTINGUISHABLE (a labelled
two-channel active-cell read). Recovering surfaces from disparity ALONE when
appearance is uniform (unlabelled binocular correspondence — the classic stereo
matching problem) is a SEPARATE rung, exactly as unlabelled common-fate
segmentation was for the motion-depth retina. This is the labelled active-cell
level, integer/in-frame only.

## §9 — nothing moved (this rung adds nothing off by default)

- **Bench 200/0** with `data/` (190/10 without, §10.2).
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved** (`test_sdloop_vision_migrated.py`
  15/15).
- `test_depth_infer_migrated.py` **8/8**, `test_time_infer_migrated.py` 6/6,
  `test_dimension_inference_migrated.py` 8/8, `test_engine_provenance_migrated.py`
  7/7, gen_infer 7/7; **fm0 VACUOUS D=0.0 exactly** (`fm0_vacuity_audit.py`).
- New gate `tests/test_stereo_infer_migrated.py` **9/9**.
- No `.rs` and no seed changed ⇒ engine byte-identical to the committed depth rung's
  engine (source-identical shared build); every committed contract reproduces.

## Cardinality audit (no hardcoded eye count)

- Eye count read via `len(eyes_in_graph(s)) == Count(Eye hubs)` (hub traversal), at
  N=2 (→2), N=3 (→3), N=4 (downstream), N=8 (shuffle). `frames.len() == Count(Eye
  hubs)` for every arm (frames built by iterating the hubs). The mint/floor DECISION
  is the Rust `DepthInfer` Term + the `depth_axis` seed rule — no Python `if` over
  graph state. **No literal `2` in any decision path.**

## Zero magic numbers (§13)

Disparities/baselines READ from the data (per-eye column offsets); depth ordinal ℕ
(rank by L1 speed); orbit/rigidity test EXACT INTEGER equality (no tolerance); eye
count from the graph; n=400 fixed in advance. No float committed.

## What I got wrong (recorded, §7)

- **Frame-order shuffle is degenerate at N=2** and cannot be the precision
  discriminator: with 2 eyes the only sequence permutations are original and
  reversal, both legitimate depth orbits. The real precision difference is
  VERIFICATION-baseline count (N=2 has zero verification pairs; N=3 has one), so the
  precision case had to be an INCONSISTENT-disparity surface, not a shuffle. Fixed
  before the confirmatory run; the shuffle arm is the floor control (eye-order
  scramble → 0 spurious), and the precision arm is the inconsistent-disparity scene.
- A first attempt linked each Eye hub to the agent with a `has_eye` edge; **Γ
  rejects that edge type (not in vocabulary)**. The cardinality never needed the
  edge — `Count(Eye hubs)` is `s.nodes("Eye")` — so the edge was dropped.

## Plain statement

**Depth is now grounded from N SIMULTANEOUS eyes as well as from motion — the SAME
`latent:depth` dimension, additively — bounded to the DISCRETE, integer-disparity,
in-frame class** (N depth layers each at a different integer inter-eye translate;
distinguishable/labelled surfaces). It is grounded by the **UNCHANGED** `DepthInfer`
Term and `depth_axis` seed rules, with the frame-source (N eyes at one tick vs one
eye over N ticks) the ONLY difference — so `DepthInfer` GENERALIZED and no
`StereoInfer` delta was needed. Stereo grounds depth at a single instant (quicker
than motion's K ticks); the eye count falls out of `Count(Eye hubs)` (N=2 and N=3
demonstrated, N=3 more precise), never a literal. **NOT shown / deferred
(cross-frame):** continuous/sub-integer disparity and finer-baseline resolution;
unlabelled binocular correspondence (surfaces recovered from disparity alone under
uniform appearance); any map topography or biological OD/vergence claim.
