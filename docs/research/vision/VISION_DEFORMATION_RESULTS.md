# NON-RIGID DEFORMATION INVARIANCE (FRONTIER rung T4) — the IDENTITY-PRESERVATION BOUND — RESULTS

*Pre-registered in `VISION_DEFORMATION_PREREG.md` (committed `f96199d1`, BEFORE this run,
§3). Runner `scripts/deformation_measure.py`, seed `seeds/vision_deformation.json`, gate
`tests/test_deformation_migrated.py`, pinned `results/deformation_measure.json`.
Confirmatory floor seeds **46000–46099** (never previously used; ledger checked —
43000–43999 crowding, 44000–44999 category, 48000–48999 agnosia, 49000–49999
face-inversion; 45000–47999 was CLEAN). Base `main` HEAD **877937e4**
(`git merge-base --is-ancestor 877937e4 HEAD` verified).*

**Provenance (§10):**
`engine 7d5f50c18673 @ …/runners/dsl/python/substrate_rs/_native.abi3.so
[shared build from …/gamma-substrate — Rust source identical]`. This rung adds **NO
Rust** — recognition-under-bounded-deformation is a COMPOSITION over existing Terms
(`SmoothDeformComponents` + `DictGet` + `Argmin` + `Abs` + `Lte` + `Times` + `Attr` +
`NodesOfType`) driven by two new SEED rules (`seeds/vision_deformation.json`, gated on
`agent.deform`, OFF by default). The shared canonical engine is a legitimate build of this
tree's source (`test_engine_provenance_migrated` green, source `shared` — byte-identical
`.rs`). **No new engine hash: shared-legit, because there is truly no `.rs` change.**

## HEADLINE — a CLEAN DIAGNOSED NEGATIVE on the bound, with the mechanism named and measured

**The identity-preservation bound is EXPRESSIBLE and its affine clause WORKS — but the
bound CANNOT SEPARATE identity-preserving from identity-changing deformation, because the
two bands OVERLAP in the verdict's own scalar. This is not a threshold that was set badly;
it is a fact about the geometry of a free-form warp, and no bound — falls-out or tuned —
can fix it.**

Measured, on the SAME 7 pentominoes the wall / det1 / similarity / continuous-pose rungs
used:

```
max(total) over identity-PRESERVING stimuli   =  0.10659   (X, smooth warp a=2.0)
min(total) over identity-CHANGING  stimuli   =  0.10299   (the pair N ↔ L)
                                                 ^^^^^^^  PRESERVING > CHANGING
```

An identity-preserving smooth warp of `X` costs MORE deformation than the entire distance
between two DIFFERENT held identities, `N` and `L`. Any threshold that admits the warp
admits the confusion; any threshold that refuses the confusion refuses the warp. **The
bands overlap ⇒ the crux fails as a matter of the verdict's own geometry.**

**Every pre-registered prediction held, including the predicted negative** (§3.7 —
the prediction was committed before the run and is reproduced verbatim in the prereg).

## AUDIT verdict (§12.4) — COMPOSE, no new Rust

**Do the held deformation Terms expose a bending energy the recognition can BOUND?
Exactly one does.**

- **`SmoothDeformComponents { a, b }`** — `runners/dsl/src/term.rs:598` (decl), evaluator
  `term.rs:5651`, impl `runners/dsl/src/deform_metric.rs:255`. It fits the SAME
  free-form-deformation field `SmoothDeformDist` fits (`deform_metric.rs:118` `ffd_fit`, a
  verbatim duplicate of `term.rs::smooth_deform_dist`'s warping loop) and **decomposes it
  into an AFFINE part and a NON-AFFINE residual**, returning a `Dict` with `total`
  (`:278`, byte-identical to `SmoothDeformDist`), `residual` (`:276`), `dc` (`:277`, the
  deformation MAGNITUDE), **`bending`** (`:286–292`, the mean-squared NON-AFFINE
  displacement — the bending energy), and `rotation`/`shear`/`log_scale`/`tx`/`ty`
  (`:222` `decompose_affine`).
- **`DeformDist`** (`jsonio.rs:1310`), **`TpsDeformDist`** (`term.rs:587`), **`ScTpsDist`**
  (`term.rs:611`) return a **bare scalar** — no bending/affine split, so **they cannot
  express the bound at all**. `TpsDeformDist`'s own doc records that it gives the affine
  part an *unconditional free pass*, which is precisely the behaviour that would re-merge
  the shears `VISION_SIMILARITY_RESULTS.md` measured to be identity-changing. This is why
  `VISION_CONTINUOUS_POSE_RESULTS.md` refused these metrics for pose, and the refusal is
  vindicated here.

**Does recognition-under-bounded-deformation COMPOSE with no new Rust? YES.** Every Term
is held and JSON-serializable for seed rules (`jsonio.rs`: `SmoothDeformComponents:1322`,
`DictGet:1050`, plus `Argmin`/`Abs`/`Lte`/`Times`/`Attr`/`NodesOfType`). Two seed rules
(`df_recognize` / `df_refuse`) do the whole job: **codebook proposes, deformation verdict
decides, bounded**.

## THE BOUND — what it falls out of (§13)

One quantity generates all three clauses. The observation is quantized to the integer
lattice, so a point's position is certified only to the **lattice half-diagonal `√2/2`** —
the identical falls-out constant continuous pose used, for the identical reason. Point sets
are normalized to unit RMS radius (canonical scale, and REQUIRED because uniform scale is
identity-preserving per the similarity rung), so in normalized units the floor is

```
eps = (sqrt(2)/2) / R  =  0.15637        R = 4.5220 = the codebook's OWN mean RMS radius
```

| clause | quantity | bound | derivation | **measured verdict** |
|---|---|---|---|---|
| match / magnitude | `total` | `<= eps` | linear in displacement ⇒ the floor itself | load-bearing |
| **affine identity-preservation** | `Abs(shear)` | `<= eps` | INHERITED from the similarity rung (`M·Mᵀ=λI` ⇔ shear 0), identifiable only to observational resolution | **load-bearing (D=1)** |
| **bending energy** | `bending` | `<= eps^2 = 0.02445` | a mean SQUARED displacement ⇒ the floor squared | **INERT (D=0)** |

No constant is fitted; `eps` is measured from the held codebook's own geometry and shifts
with it (§13's distribution-shift test). It is graph data on the agent (`df_eps`), written
by the adapter exactly as continuous pose wrote `cp_angles`.

## RESULTS (mode: `deform=1`, all arms)

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A1 INVARIANCE** | recognized-as-own / 35 (7 obj × 5 amplitudes) | **35/35**, 0 wrong, 0 refused | ≥30/35 ✓ (PASS, as predicted) |
| **A2 DISCRIMINATION exact-0** | untransformed own-identity, wrong_id | **7/7, wrong_id=0 → exact0=TRUE** | exact-0 ✓ (PASS, as predicted) |
| **A3 c1 small smooth recognized** | / 7 | **7/7** | PASS ✓ |
| **A3 c2 strong shear REFUSED** | / 7 | **7/7 refused** | PASS ✓ (the inherited affine clause working) |
| **A3 c3 SEPARABILITY (THE CRUX)** | max_preserving vs min_changing | **0.10659 > 0.10299 → separable = FALSE** | **FAIL — the predicted NEGATIVE** ✓ |
| **A4 FLOOR** | force-maps / 61 non-held (46000–46099) | **16/61 force-mapped** | leak > 0 ✓ (FAIL, as predicted) |
| **A5 §13.2 bending clause** | `max abs(on − off)` | **D = 0.0 → INERT**; max bending 0.00141 vs bound 0.02445 (17× below) | INERT ✓ (as predicted) |
| **A5b §13.2 shear clause** | `max abs(on − off)` | **D = 1.0 → load-bearing** | load-bearing ✓ |
| **A5c NO-BOUND positive control** | shears admitted / merges | **7/7 admitted, 5 WRONG-ID merges** (F→N, T→X, L→V, N→V, X→U) | the crux is RISKED ✓ |
| **A6 §9 OFF-DAY** | flag absent | **inert** (`status` stays `df_decoded`, `covered_by` None) | ✓ |

## The questions the task demanded, ANSWERED by measurement

**1. Is the bending-energy bound expressible?** **YES for exactly one Term, and it is
INERT.** `SmoothDeformComponents` exposes `bending` explicitly and the clause composes
graph-natively with no new Rust — but toggling it changes **ZERO** verdicts across every
stimulus class (`D = 0.0`, §13.2). The reason is measured, not guessed: **`bending` never
rises above `0.00141` while its falls-out bound is `0.02445` — 17× below, everywhere.**
The FFD is fit on a coarse `[2,4]` control-grid schedule with ridge regularisation
(`deform_metric.rs:152–154`), so **the displacement field it produces is very nearly
affine BY CONSTRUCTION**; the non-affine residual it can report is structurally tiny. Per
§13.2 an inert clause is decorative and is reported as such, not quietly retained.

**So the honest answer to Step 1's question is: the "bending energy" the held Terms expose
does NOT separate identity-preserving from identity-changing deformation. The AFFINE SHEAR
component does** — and it is the clause inherited from the similarity rung, not one
invented here.

**2. Can identity-preserving smooth warps be separated from identity-changing ones?**
**NO — and this is the headline negative, established as a band-overlap rather than a
threshold failure.** `max(total)` over identity-preserving stimuli is `0.10659`; `min(total)`
over identity-changing stimuli is `0.10299`. Since **preserving > changing**, no scalar
threshold on this verdict — falls-out, tuned, or oracle — can admit every identity-
preserving warp while refusing every identity-changing one. The floor arm shows the same
fact from the other side: **16 of 61 random non-held polyominoes force-map onto a held
identity** (mostly onto `U` and `F`).

**MECHANISM, named in advance and confirmed:** the FFD is a **FREE-FORM** warp. It absorbs
not only the nuisance deformation but **also part of the structure that DISTINGUISHES
identities** — it can pull a candidate onto a different object nearly as well as onto a
warped version of itself. The freed non-rigid group is strictly larger than the identity-
preserving one, and a scalar bound on the warp's COST cannot re-restrict a group that has
already been freed. This is the deformation-domain restatement of exactly what
`VISION_CONTINUOUS_POSE_RESULTS.md` refused these metrics for.

**3. Is the crux RISKED, or forced by construction (§13.1)?** RISKED, and the positive
control proves it. Removing the bound from the SAME graph (`df_eps` set huge) makes the
mechanism **admit all 7 shears and WRONG-MERGE 5 of them** (F→N, T→X, L→V, N→V, X→U) —
reproducing the similarity rung's `shearY(F) → X` failure in the deformation setting. The
bound is doing real work; a mechanism without one merges everything, exactly as the
pre-registration said it must.

## What SURVIVES this rung (the positive residue, stated conservatively)

- **Invariance under BOUNDED smooth deformation is real: 35/35, wrong_id 0.** Within the
  band where it applies, the composition does recognize a smoothly-warped object as
  itself — the Omniglot fact ("a letter written differently is the same letter") holds
  graph-natively over a held continuous verdict, no new Rust.
- **Discrimination on untransformed objects is exact-0** (7/7, wrong_id 0).
- **The strong shear is refused 7/7**, by the affine clause INHERITED from the similarity
  rung. The similarity rung's group characterization transfers intact into the non-rigid
  setting — a sheared glyph remains a novel shape, not a viewing transform.
- **The composition itself is sound and cheap** — two seed rules, no Rust, flag OFF by
  default.

What does NOT survive: the claim that this constitutes *deformation-invariant recognition*.
It does not, and the overlap number says by how much.

## The honest boundary — what this negative does and does NOT license

- It does **NOT** retract the Omniglot composition result (`OMNIGLOT_ARC.md`, +21pp from
  arrangement; the 73.5% SC+TPS verdict transplant of RUN 16).
- It does **NOT** say "non-rigid invariance is impossible in this substrate."
- It **DOES** say: **a scalar bound on an UNCONSTRAINED warp's cost is the wrong shape of
  mechanism.** The similarity rung succeeded because it constrained the **GROUP** (a
  graph-data test on the inferred matrix: orthogonal columns, equal lengths, non-degenerate)
  — not because it thresholded a cost. The deformation analogue must therefore constrain
  the **WARP FAMILY ITSELF** — a smoothness/curvature admissibility test on the fitted
  field, applied *before* a cost is read — rather than pricing an already-free warp. That
  is the named next mechanism, and it needs its own pre-registration with its own
  mechanism-level hypothesis (§3.6), not a parameter search on this one.

## BOUNDS (§8) — what is NOT shown

INSTANCE-level recognition under BOUNDED SMOOTH DEFORMATION, over 7 hand-chosen full-rank
free pentominoes at one dense sampling (`s=4`, ~80 points/object), one smooth warp family
(low-frequency sinusoidal), one identity-changing transform family (`shearY`). The
band-overlap claim is over those stimuli and that verdict scalar (`total`), not over all
shapes or all deformation metrics. The floor is 61 non-held random connected polyominoes
from seeds 46000–46099 (39 of the 100 canonicalized to a held object and were excluded).
This licenses nothing about biological deformation tolerance. **NAMED FRONTIER, UNCHANGED
and explicitly NOT this rung: lighting, style, and the learned axis-codebook at
natural-image scale** — plus, now added by this rung's diagnosis, the warp-family
admissibility test named above.

## §9 off-day / sibling gates

`deform` absent by default ⇒ committed bench unmoved. At engine `7d5f50c18673`:
- new gate `tests/test_deformation_migrated.py` **13/13** (incl. off-by-default inertness;
  the no-new-Rust source audit; the no-Python-decision audit; the pinned-results
  reproduction; **and the pre-registered NEGATIVE itself gated**, so it cannot silently
  drift into an unexamined pass);
- sibling gates **54 passed / 0 failed together** (`test_sdloop_vision_migrated` — orbit law
  `{2:1,3:2,4:2,6:2,12:4}` unmoved, `test_identity_untangling_migrated`,
  `test_dimension_inference_migrated`, `test_similarity_migrated`,
  `test_continuous_pose_migrated`, `test_engine_provenance_migrated` source `shared`);
- broad vision bench `scripts/rung7_vision_bench.sh` (`data/` symlinked into this worktree
  only, §10.2): **200 passed / 0 failed** — identical to the documented with-`data/`
  baseline, and its no-Python-thresholds scan reports *"(none — every knob is graph data)"*
  (the `deform` flag and the `df_eps` bound are both graph data).
