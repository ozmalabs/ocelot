# DEPTH AS AN INFERRED DIMENSION — results (monocular structure-from-motion)

**Pre-registration:** `VISION_DEPTH_PREREG.md`, committed BEFORE the confirmatory
run at **`8c88cbf3`** (with the mechanism, per the time-rung precedent). Runner:
`scripts/depth_measure.py`; pilots `scripts/depth_pilot.py` (premise on the
existing TimeInfer) / `scripts/depth_pilot2.py` (the new Term) /
`scripts/depth_retina_probe.py` (retinal step). Results JSON:
`results/depth_measure.json`.

**Engine:** `41372737a9ae` — **this worktree's OWN build** (the rung adds Rust:
the `DepthInfer` Term). `scripts/engine_build.sh`; `data/` symlinked to canonical.

## The headline

**DEPTH IS AN INFERRED DIMENSION in this substrate, recovered MONOCULARLY from
motion, BOUNDED to the discrete integer-velocity class** — the third dimension,
earned the same way time and the spatial generators were. It is the RESIDUAL of
`TimeInfer`'s single-generator question, read as discrete depth: a scene NO SINGLE
flat generator can explain because near regions sweep faster than far ones (motion
parallax) mints `latent:depth`, the ordinal dimension indexing the regions by
velocity. **And — the whole result — a FLAT scene mints NOTHING.**

## The decisive pair

- **H_flat (the anti-forced control, run FIRST) — PASS.** A flat scene (one
  integer velocity everywhere) AND a multi-COLOUR scene at a SINGLE velocity both
  → `depth_none`, **NO mint**. Depth is minted from VELOCITY VARIATION, never from
  the mere presence of multiple regions. *A flat plane minting depth would be the
  §1.1 dead-arm / §13 magic-dimension disease in the depth domain — DISQUALIFYING.
  It does not.* Reported as the honest MDL floor: "no depth dimension shorter than
  a single generator (provisional)."
- **H_depth — PASS.** A 2-layer scene (red (2,0), blue (1,0), same coord span so no
  shear can fake it) → mint `latent:depth`, `n_layers=2` (read from the data),
  velocities `((2,0),(1,0))`, ordering near→far `(red, blue)`. **MDL 36→13 tokens
  (2.77×)**: one generator cannot carry the scene, so the "without" baseline is
  enumeration; depth compresses it below that.

## The controls (same discipline as gen-mint / time)

- **H_multiheld (§13.1, frozen machinery) — PASS.** Four DIFFERENT structures →
  four correct, DIFFERENT results from one frozen Term: `2-layer[red>blue]`,
  `3-layer[r>b>g]` (n_layers=3), `reversed[blue>red]` (ordering FLIPS to
  `(blue,red)`), and `dedup[3 surfaces, 2 velocities]` (`n_layers=2`, all three
  surfaces indexed). ≥3 distinct orderings ⇒ same-ordering-regardless (forced) is
  ruled out.
- **H_shuffle (the floor at the LONGEST window K=8) — PASS.** 400 random shuffles
  (seeds 27100–27499) of 2- and 3-layer scenes → **0 spurious mints** (per-surface
  velocity is no longer constant under a shuffle). An exact monotone reversal is a
  legitimate depth orbit (negated velocities) and is counted separately; 0 arose.
- **H_downstream (§1.5 / §13.2, LOAD-BEARING) — PASS.** The minted depth predicts
  the UNSEEN view at tick K (each surface advanced by its OWN velocity K times)
  **EXACTLY**: `predicted == withheld`, `D_mint=1`, `D_pred=1`. A single (naive)
  generator CANNOT produce this view — the depth is what makes it predictable. Not
  decoration.
- **H_offday (§9) — PASS.** Flag OFF ⇒ a multi-depth scene does not mint (inert).

**All 6 arms PASS. Every prediction held; no proviso broke.**

## The retinal step — REACHED, POSITIVE (`depth_retina_probe.py`)

Two distinguishable patterns drifting across a 30×30 retina at DIFFERENT integer
velocities (motion parallax), read as their per-tick active-cell footprints:
- **multi-depth** (`a` fast/near, `b` slow/far) at three velocity pairs → depth
  minted, `n_layers=2`, the faster pattern correctly ordered NEARER, and the
  minted depth **predicts the unseen view exactly** in all three;
- **flat control** (both patterns at one velocity) → **no depth**
  (`reason=single_velocity`);
- **shuffle control** → grounds (`reason=non_constant_velocity`).

**Honest scope (prereg P1, the time-rung precedent):** the two patterns are
DISTINGUISHABLE (a two-channel active-cell read — "two patterns"). Recovering the
surfaces from motion ALONE when appearance is uniform (**unlabelled common-fate
segmentation**) is a SEPARATE rung, named not built — as the full center-surround
event pipeline was for time (a moving blob under center-surround + adaptation is
not exact-integer-rigid and would ground at the exact-equality floor).

## The minimal delta

**Reused, not rebuilt:** `DepthInfer` (`shape_decode.rs::eval_depth_infer`) is the
DEPTH sibling of `TimeInfer`, built on the SAME primitives — `infer_translate_offset`
+ exact-equality verification (`TimeInfer`'s per-region rigidity test),
`apply_generator_k` (the downstream prediction), `load_parts` (dim_types). The only
NEW code is the PARTITION-by-surface (`surface_key` / `partition_by_surface`, cells
grouped by their non-coord slots) and the distinct-velocity decision — the residual
`TimeInfer` cannot express because it asks about the WHOLE scene. Wired
`term.rs`/`jsonio.rs`/`reflect.rs`. Seed `depth_axis.json` mirrors `time_axis.json`
field-for-field (`depth_infer_mint`/`depth_infer_floor`, flag-gated, OFF by default).
The mint/floor DECISION is the Rust Term + the seed rule — no Python `if` over graph
state (the architecture rule IS the experiment).

## Every constant — what it falls out of (§13)

- **`n_layers`** = `Count` of distinct per-surface velocities — falls out of the
  DATA. Confirmed by the cardinality audit: 2-layer reads 2, 3-layer reads 3, dedup
  reads 2 — never a literal.
- **`window` (K)** = frames seen — read from the Term, not hardcoded.
- **The depth ordering** falls out of the measured per-surface velocities (L1 norm),
  not a chosen scale.
- **The velocity search bound** is data-derived (inherited from `TimeInfer`); `max_b`
  is only a data-scaled safety cap.
- **No float committed.** Depth is an ordinal (ℕ); the orbit test is EXACT integer
  equality. There is nothing to tune — the strongest §13 outcome after "no number":
  a number (`n_layers`) that is *counted*, not chosen.

## §9 — committed results byte-identical (this rung is additive + OFF by default)

| oracle | result |
|---|---|
| vision bench (with `data/`) | **200 passed / 0** (190/10 without `data/`, the §10.2 condition) |
| sd orbit law `{2:1,3:2,4:2,6:2,12:4}` | UNMOVED (`test_sdloop_vision_migrated` green) |
| genmint 6 H-arms | PASS |
| time gate | 6/6 |
| dimension-inference / gen_infer / provenance | 8/8 · 7/7 · 7/7 (44/44 sibling gates) |
| fm0 vacuity | **VACUOUS**, `D=0.000000e+00` on lum/x/theta/resp |
| fm0b drift-wired | `D_lum = 8.071079e-01` |
| **new gate** `test_depth_infer_migrated.py` | **8/8** |

The new mint path is reachable ONLY via `status=='depth_seq'` + `depth_infer_enabled==1`,
which no committed contract produces — so every committed number reproduces exactly.

## Seed block

**27000–27999.** H_shuffle consumed **27100–27499**; retinal/shuffle probes used
27500 (exploratory). **27000–27099 + 27500–27999 exploratory/clean. 12000–26999
untouched.**

## What I got wrong / did not show

- **Did NOT show** continuous perspective — a real velocity gradient / continuous
  foreshortening is CROSS-FRAME (non-integer) and DEFERRED, exactly as real-angle
  rotation is (prereg P2). This is the DISCRETE, integer-velocity, in-frame core of
  monocular depth — the recoverable third dimension — NOT the full projective
  apparatus.
- **Did NOT show** unlabelled common-fate segmentation (surfaces recovered from
  motion when appearance is uniform) — a separate rung (P1).
- **Did NOT show** rotation-as-depth or accelerating layers — those reach the floor
  (`non_constant_velocity` / `non_rigid_surface`); the linear-generator depth regime
  is a separate extension (P3).
- **A "surface" is grouped by observable appearance.** Depth is inferred from the
  surfaces' differential MOTION, and the multi-colour-single-velocity control proves
  appearance ALONE mints nothing — but the grouping itself is given, not derived.

## Bottom line

**Depth is now an inferred dimension in this substrate — `latent:depth`, minted
from the temporal residual of motion, bounded to the discrete integer-velocity
(N-layer, rigid, in-frame) class, recovered MONOCULARLY.** A multi-depth scene
mints it; a FLAT scene correctly mints NOTHING. It is believed for the same reason
gen-mint and time were: it FAILS where it must (flat → nothing; shuffled → floor;
continuous/rotating → floor), and what it mints PREDICTS an unseen view.
