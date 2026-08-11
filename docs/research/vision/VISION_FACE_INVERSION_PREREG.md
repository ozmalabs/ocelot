# FACE-INVERSION / THATCHER (T10) — PRE-REGISTRATION

*A VALIDATION gate (VISION_VENTRAL_GROUNDING.md failure-mode #3). Written and COMMITTED
before the confirmatory run (PROTOCOL §3). Seeds **49000–49999** (noise floor 49000–49099
only). This gate ADDS NO seed rule and NO Rust — it MEASURES the existing composition
machinery (the shape-decode loop, `seeds/shape_decode_loop.json` over
`runners/dsl/src/shape_decode.rs`), so §9 holds by construction (nothing new can move a
committed result). The instrument was calibrated first (§1) on deterministic constructions
+ the fixed noise block; this file fixes the arms and the PREDICTION before the
confirmatory run.*

## The question

The face-inversion effect: recognising a **configural** pattern (identity carried by the
ARRANGEMENT of parts) is disproportionately hurt by INVERSION, far more than a **part-
based** pattern is, because configural coding is reference-frame-dependent (tuned to the
upright frame). The Thatcher illusion: a locally-inverted part looks grotesque UPRIGHT but
not INVERTED — configural anomaly-detection is gated to the canonical frame.

**The claim under test:** the substrate's COMPOSITION (arrangement = relative-pose
relations, the Omniglot "+21pp arrangement" one level up) is **reference-frame-dependent
holistic** — a configural pattern binds only in the upright frame, and inversion /
Thatcherisation break it MORE than they break a part-based pattern.

## AUDIT (§12.4, file:line) — what composition machinery exists, and its frame-behaviour

The sd loop is **reference-frame-DUAL**, with two channels of opposite frame-behaviour,
selectable by the ladder rung reached (audited by reading the code, not inferred):

- **LITERAL decode `sd_recognize`** (`seeds/shape_decode_loop.json:1465`; guard
  `Count(residual)==0` at 1475–1511) — fires only on an EXACT match in the canonical
  frame ⇒ **reference-frame-DEPENDENT**.
- **TRANSFORM channel `sd_transform_decode`** (`:245`, one uniform per-dim delta) and
  **`sd_infer_dimension`** (`:360`, a held generator applied to the shape's own coords) —
  recognise a rotated / reflected / **inverted** whole as the SAME identity
  (`status=recognized_transformed`, `covered_by=base`), the orientation folded into a
  `Transform{generator, k}`. **These two rungs run for ANY residual with NO flag** (only
  the general-linear `GenInfer` is flag-gated, `agent.gen_infer_enabled`,
  `:889`) ⇒ **reference-frame-INVARIANT by default**.
- **Point-inversion is FREE:** `rotate90_once` (`runners/dsl/src/shape_decode.rs:581`)
  at **k=2** = 180° = point inversion, enumerated from the seed generator's
  `params=[1,2,3]` (`shape_decode_loop.json:24`; DimInfer iterates `for &k in &gen.params`,
  `shape_decode.rs:1849`). `identity_untangling` already measured rot180 → same identity.
- **The stroke arrangement code is split** (`runners/dsl/src/strokes.rs:1-31`): `seg`
  relative-turn quanta are rotation/translation/scale-INVARIANT by construction (test
  `invariance_under_rotation_translation_scale:959`); `pose_o` is a SEPARATE absolute-
  orientation relation, frame-DEPENDENT, OMITTED under `invariant_only` (`:395`). But a
  UNIFORM rotation still surfaces as ONE `pose_o` delta (rung-1 tier-1, `:1447-1500`) ⇒
  folded ⇒ invariant even with `pose_o` present.

**Audit verdict:** identity in this substrate is the **generator-ORBIT** (identity_
untangling: `covered_by`). An orbit is orientation-invariant BY DEFINITION under the held
`rotation90`/`reflection` generators, so the DEFAULT composition is reference-frame-
INVARIANT. A frame-DEPENDENT channel exists (`sd_recognize` literal, `pose_o` absolute) but
is SUBORDINATE — the transform channel overrides it. **A holistic inversion COST is
therefore expected to be NOT expressible under the default ladder** — the substrate has no
privileged (upright) frame. This is the crux the confirmatory arms test.

## Statistic, arms, n (FIXED)

All confirmatory arms are DETERMINISTIC constructions (no RNG ⇒ no confirmatory seed
burned) except the noise floor (fixed block 49000–49099). Stimuli: a part **atom** is an
asymmetric L-tromino (`rot180 ≠ self`); a **configural** face = the SAME atom at K=4
distinct anchor arrangements (identity = the arrangement); a **part-based** object = 4
distinct atoms at fixed anchors (identity = which atoms). Whole inversion = `rot180` (=
rotation90 k=2). Thatcher = ONE atom locally flipped in place. Driver = the identity_
untangling `identify(codebook, view) -> (status, covered_by)` over the real sd loop,
`gen_infer` OFF (default).

- **ARM 1 — INVERSION COST (headline DIFFERENTIAL).** `cost_config = 1 −
  (#inverted-config-faces recognised as OWN identity)/K`; `cost_part` likewise. Statistic:
  the DIFFERENTIAL `cost_config − cost_part`. The effect requires `cost_config ≫
  cost_part` (both-hurt-a-little is NOT it).
- **ARM 2 — THATCHER (frame-gating).** For each of K×3 configural Thatcher cases:
  `recognised(upright)` and `recognised(inverted)`. Frame-gating signature =
  `recognised(upright) ≠ recognised(inverted)`. Same for part-based.
- **ARM 3 — REFERENCE-FRAME (the dual channel).** For each face X, hold `{X, rot180(X)}`
  as DISTINCT identities; present X and present rot180(X); record `covered_by` of each.
  `COLLAPSED = (covered_by(X) == covered_by(rot180(X)))`. Control: two part-based objects
  that are NOT rotation-related must stay discriminable under inversion.
- **ARM 4 — FLOOR / §1.1 (arms ALIVE + noise).** ALIVE: upright faces recognised as OWN
  identity (rate high, `covered_by` not a constant None), inverted faces recognised, and
  Thatcher probes unrecognised — BOTH states reached. NOISE: n=100 random 9-cell sets
  (seeds 49000–49099) vs the K-face codebook; `force_map_rate` = fraction recognised.
- **ARM 5 — §9 OFF-DAY.** This gate adds NO seed / NO Rust; verify no seed edited, the sd
  orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved, sibling gates green, broad
  `scripts/rung7_vision_bench.sh` 200/0 (190/10 without `data/`).

## Decision rule (incl. what a null means)

- **Headline POSITIVE (holistic-configural, human-like):** `cost_config − cost_part ≥
  0.5` AND `cost_part ≤ 0.1`. Would show the composition is reference-frame-dependent.
- **Headline NEGATIVE (part-bag / frame-invariant):** `cost_config ≤ 0.1` AND `cost_part
  ≤ 0.1` (both recognised under inversion) ⇒ the differential ≈ 0 ⇒ NO disproportionate
  cost. A clean diagnosed negative (§7), reported with the mechanism.
- **Thatcher POSITIVE:** frame-gating present for configural (`recognised(upright) ≠
  recognised(inverted)` on ≥ half the cases) and ABSENT for part-based.
- **Thatcher NEGATIVE:** the local anomaly is detected EQUALLY in both orientations
  (`recognised(upright) == recognised(inverted)` on ALL cases) ⇒ no frame-gating.
- **Reference-frame:** `COLLAPSED` on all configural inversion-pairs is the measured
  orbit-invariance (the substrate treats a pattern and its inverse as ONE identity — the
  OPPOSITE of the human upright bias, not the same effect).
- **NOISE:** `force_map_rate == 0` required (else the recogniser is a universal container
  and every other arm is void).

## PREDICTION (stated in advance, with provisos — §3.7)

I predict the **NEGATIVE on both headline arms**, from the audited mechanism:

1. **ARM 1:** `cost_config ≈ 0` AND `cost_part ≈ 0` (both K/K inverted patterns recognised
   as OWN identity) ⇒ differential ≈ 0. The composition is reference-frame-INVARIANT for a
   UNIFORM inversion — the transform channel folds it into `rotation90 k=2`. **No
   disproportionate inversion cost. NEGATIVE.**
2. **ARM 2:** NO Thatcher frame-gating — a locally-flipped part is a NON-uniform residual
   that no single generator folds, so it is unrecognised UPRIGHT **and** INVERTED
   identically (`recognised(upright) == recognised(inverted)` for all cases). The
   substrate has no upright-privileged anomaly detector.
3. **ARM 3:** inversion-related pairs COLLAPSE (a face and its 180-twin → one `covered_by`)
   — the orbit-invariance, i.e. the substrate UNDER-distinguishes orientation, the mirror-
   image of the human effect.
4. **ARMS 4/5:** upright & inverted recognised (alive), Thatcher unrecognised, noise
   force-map 0/100; siblings + orbit law unmoved.

**Provisos (what would break the prediction, and what it would mean):**
- If ARM 1 shows `cost_config ≫ cost_part`, the cell arrangement code carries a frame-
  dependent channel I mis-audited ⇒ POSITIVE, the substrate IS holistic-configural.
- If ARM 2 shows frame-gating, a non-uniform local flip IS folded in one orientation only
  ⇒ an upright-privileged frame exists after all.
- The diagnosis if the NEGATIVE holds: **the substrate has no privileged reference frame**
  — its generators are D4-symmetric, so every orientation is equivalent; human holistic-
  configural coding is frame-dependent because it PRIVILEGES the upright (an experience-
  dependent prior; grounding-doc: category/face domains emerge ~200 days). To build the
  human effect you must BREAK the D4 symmetry with a learned upright prior — a NAMED
  FRONTIER, NOT built here (building it by hand would be §13.1 architecture-forcing).

## Bounds (§8)

A VALIDATION gate on the EXISTING composition's reference-frame behaviour, on abstract
cell-arrangement stimuli — NOT face-specific processing, NOT grown face-selectivity (the
diagnosed Hebbian dead-end), NOT a claim about biology. The parts and arrangements are
supplied. NAMED FRONTIER: the D4-symmetry-breaking upright prior (experience-dependent
frame privilege) that a human-like inversion cost would require.

## Provenance (§10)

- Base `main` HEAD **301ae161** (verified ancestor). Engine to be recorded in RESULTS.
- Runner `scripts/face_inversion_measure.py`; lib `scripts/face_inversion_lib.py`; gate
  `tests/test_face_inversion_migrated.py`; results `results/face_inversion_measure.json`.
- Seeds 49000–49099 (noise floor) consumed; 49100–49999 CLEAN.
