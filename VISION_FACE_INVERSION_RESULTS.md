# FACE-INVERSION / THATCHER (T10) — RESULTS

*Confirmatory run of `VISION_FACE_INVERSION_PREREG.md` (committed at `e407429f`, BEFORE
this run, §3). A VALIDATION gate on the EXISTING composition machinery. Nothing below was
measured before the pre-registration was committed; the instrument was calibrated first
(§1) on deterministic constructions + the fixed noise block.*

## HEADLINE — a CLEAN DIAGNOSED NEGATIVE (§7)

**The substrate's composition is reference-frame-INVARIANT, NOT holistic-configural in the
human way.** Every pre-registered prediction held:

- **NO inversion cost.** A uniform 180° inversion of a configural arrangement is recognised
  as the SAME identity (4/4), exactly as a part-based object is (4/4). `cost_config = 0.0`,
  `cost_part = 0.0`, **differential = 0.0**. The transform channel folds the inversion into
  `rotation90 k=2`.
- **NO Thatcher frame-gating.** A locally-inverted part is a non-uniform residual no single
  generator folds, so it is UNRECOGNISED **upright AND inverted identically** — 0 of 12
  configural Thatcher cases are frame-gated; 12/12 unrecognised in BOTH orientations.
- **The reference-frame structure it DOES have is the OPPOSITE of the human bias:** the
  transform channel COLLAPSES inversion-related pairs (a pattern and its 180°-twin are ONE
  identity, 4/4) — it UNDER-distinguishes orientation, where humans OVER-attend the upright.

**The substrate has no privileged (upright) reference frame.** Its identity is the
generator-ORBIT (identity_untangling), and an orbit is orientation-invariant by definition
under the held `rotation90`/`reflection` generators. A holistic inversion effect is
therefore **not expressible** under the default ladder — as predicted from the audit. This
is reported, not forced (§7): building the human effect would require BREAKING the D4
symmetry with a learned upright prior, which is §13.1 architecture-forcing if done by hand.

## Provenance (§10)

- **Engine:** `engine 7d5f50c18673 @ …/runners/dsl/python/substrate_rs/_native.abi3.so
  [shared build, Rust source identical]` — **NO new Rust** (§10.1 rule 4: `git diff
  301ae161..HEAD -- runners/dsl/src runners/dsl/Cargo.toml` is EMPTY). Same engine as the
  crowding / McCollough / identity-untangling / similarity sibling gates.
- **Base:** branch `gamma-substrate/vision-face-inversion` off `main` HEAD **`301ae161`**
  (verified `git merge-base --is-ancestor 301ae161 HEAD`). Prereg commit `e407429f`.
- **Runner:** `scripts/face_inversion_measure.py` → `results/face_inversion_measure.json`.
  **Lib:** `scripts/face_inversion_lib.py`. **Gate:** `tests/test_face_inversion_migrated.py`
  (7/7). **NO new seed; NO new Rust.** Seeds **49000–49099** (noise floor) consumed;
  **49100–49999 CLEAN; 12000–48999 untouched.**

## AUDIT (§12.4, file:line) — the composition machinery is reference-frame-DUAL

The sd loop offers two recognition channels of OPPOSITE frame-behaviour:

| channel | rule | guard | frame-behaviour |
|---|---|---|---|
| LITERAL decode | `sd_recognize` (`shape_decode_loop.json:1465`) | `Count(residual)==0` (1475–1511) | **DEPENDENT** — exact canonical-frame match |
| TRANSFORM (uniform) | `sd_transform_decode` (`:245`) | residual>0, ONE per-dim delta | **INVARIANT** |
| TRANSFORM (generator) | `sd_infer_dimension` (`:360`) | residual>0, a held generator on the shape's coords | **INVARIANT** |

- The two transform rungs run for **any** residual with **no flag** (only the general-linear
  `GenInfer` is flag-gated, `agent.gen_infer_enabled`, `:889`) ⇒ the DEFAULT is invariant.
- **Point-inversion is free:** `rotate90_once` (`runners/dsl/src/shape_decode.rs:581`) at
  **k=2** = 180°, enumerated from the seed generator's `params=[1,2,3]`
  (`shape_decode_loop.json:24`; DimInfer iterates `for &k in &gen.params`, `:1849`).
- **The stroke arrangement code is split** (`runners/dsl/src/strokes.rs:1-31`): `seg`
  relative-turn quanta are rotation/translation/scale-INVARIANT by construction (test
  `invariance_under_rotation_translation_scale:959`); `pose_o` is a SEPARATE absolute-
  orientation relation, OMITTED under `invariant_only` (`:395`). But a UNIFORM rotation
  still surfaces as ONE `pose_o` delta (rung-1 tier-1, `:1447-1500`) ⇒ folded ⇒ invariant
  EVEN with `pose_o` present. (Reasoned from the *measured* strokes.rs folding mechanism —
  not re-measured here through `StrokeQuantize`; flagged as such, §12.4.)

**Verdict:** identity = generator-orbit ⇒ orientation-invariant by design. A frame-
DEPENDENT channel exists (`sd_recognize` literal, `pose_o` absolute) but is SUBORDINATE —
the transform channel overrides it (ARM 3 below shows it overriding even an exact literal
twin). So a holistic inversion cost is predicted NOT expressible. Confirmed.

## Per-arm results (engine `7d5f50c18673`, `gen_infer` OFF)

| arm | prereg prediction | result | verdict |
|---|---|---|---|
| **ARM 1 — INVERSION COST (headline differential)** | NEGATIVE: both costs ≈ 0 | config inverted 4/4 own-id, part inverted 4/4 own-id; `cost_config=0.0`, `cost_part=0.0`, **differential=0.0** | **NEGATIVE — no disproportionate cost** |
| **ARM 2 — THATCHER (frame-gating)** | NEGATIVE: no gating | **0/12** configural cases frame-gated; **12/12** unrecognised in BOTH orientations; part-based 0 gated | **NEGATIVE — no frame-gating** |
| **ARM 3 — REFERENCE-FRAME (dual channel)** | pairs COLLAPSE (orbit-invariance) | **4/4** inversion-pairs collapse (present-upright and present-inverted both → the upright identity); part-based non-rotation-related control discriminable (both up & inverted own-id) | orbit-invariant — OPPOSITE of the human upright bias |
| **ARM 4 — FLOOR / §1.1** | alive + noise 0 | upright 4/4 & inverted 4/4 recognised, Thatcher probe unrecognised (both states reached → ALIVE); noise **0/100** (seeds 49000–49099) | **PASS** |

**4/4 confirmatory arms pass; every pre-registered prediction held (the NEGATIVE was
predicted in advance — §3.7).**

## Why the negative (the diagnosis)

Human holistic-configural coding is reference-frame-dependent because it **PRIVILEGES the
upright** — an experience-dependent prior (grounding-doc: category/face domains emerge
~200 days; face-deprived macaques develop no face patches). The substrate has **no such
privileged frame**: its held generators (`rotation90`, `reflection`) form the D4 group and
treat every orientation as equivalent, so:

1. it CANNOT show an inversion RECOGNITION cost (all orientations fold to one orbit);
2. it CANNOT show Thatcher frame-gating (no upright-privileged anomaly detector — a local
   inconsistency is a residual in *every* frame, symmetrically);
3. it actually UNDER-distinguishes orientation — collapsing a pattern with its 180°-twin —
   the mirror-image failure of the human over-attention to upright.

**config and part-based are representation-BLIND-identical** here (both 4/4 invariant, both
0-gated): the sd loop matches cell-sets, it does not carry a "holistic vs featural" split.
That split, in humans, IS the upright privilege — which the substrate lacks.

## Magic numbers (§13) — none

No threshold is tuned. The verdicts are counts (4/4, 0/12, 12/12, 4/4, 0/100) off the sd
loop's own `status`/`covered_by`; every coordinate is an in-frame integer (frame/continuum
invariant); the point-inversion `rotation90 k=2` is enumerated from the seed generator's
existing `params`, not added. The decision thresholds in the pre-registration (cost ≤ 0.1,
differential ≥ 0.5) are the pre-declared PASS bands, not fitted — and the result is at the
extreme (0.0), not near a band edge.

## §9 — committed results preserved

This gate adds **NO seed and NO Rust** — it is a read-only measurement of the existing sd
loop with `gen_infer` OFF (the default). There is no flag to toggle; `test_no_face_inversion
_seed_is_added` pins that no `vision_face_inversion.json` exists. The sd orbit law
`{2:1,3:2,4:2,6:2,12:4}` is unmoved (no seed touches the sd loop). Sibling gates green
(sdloop / identity_untangling / dimension_inference / gen_infer: 38 passed; provenance 7/7).
Broad `scripts/rung7_vision_bench.sh`: 200/0 (190/10 without `data/`, §10.2) — recorded in
the commit.

## BOUNDS (§8) — stated, not overclaimed

- A VALIDATION gate on the EXISTING composition's **reference-frame behaviour**, on abstract
  cell-arrangement stimuli. **NOT** face-specific processing, **NOT** grown face-selectivity
  (the diagnosed Hebbian dead-end), **NOT** a claim about which biological mechanism is
  right. The parts and arrangements are SUPPLIED.
- The negative is about the **DEFAULT ladder** (`gen_infer` OFF). The literal channel
  (`sd_recognize`, residual==0) IS frame-dependent, but the transform channel overrides it
  (ARM 3 shows collapse even with the exact literal twin held).
- **Reasoned-not-measured (§12.4):** that `pose_o`/`StrokeQuantize` (`invariant_only=False`)
  does not rescue the effect is reasoned from the *measured* strokes.rs single-delta folding
  (`:1447-1500`, tested at `:959`), not re-measured through `StrokeQuantize` here. Flagged
  as a claim, not a fresh measurement.
- **NAMED FRONTIER (not this rung):** the D4-symmetry-breaking **upright prior** — an
  experience-dependent frame privilege (down-weighting the rotation/reflection generators
  or learning a canonical-orientation bias) — that a human-like inversion cost + Thatcher
  frame-gating would require. Building it by hand would be §13.1 architecture-forcing; it is
  the experience-dependent-frame line, adjacent to the diagnosed Hebbian dead-end. The
  remaining ventral gate (cerebral achromatopsia, #5) and the generator-track extensions
  are the other named frontiers.

**The result:** the substrate's arrangement code is a generator-orbit — reference-frame-
INVARIANT — so a uniform inversion pays no cost, Thatcher does not frame-gate, and a pattern
collapses with its own inversion. It is **not holistic-configural in the human way, and the
reason is precise**: no privileged upright frame. A clean diagnosed negative, gated.
