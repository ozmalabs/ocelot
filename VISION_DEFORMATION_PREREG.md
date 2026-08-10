# NON-RIGID DEFORMATION INVARIANCE (FRONTIER rung T4) — PRE-REGISTRATION

*Written and COMMITTED before the confirmatory run (§3). Runner
`scripts/deformation_measure.py`, gate `tests/test_deformation_migrated.py`, pinned
`results/deformation_measure.json`, seed `seeds/vision_deformation.json`. Confirmatory
seeds **46000–46999** (noise floor **46000–46099**) — never previously used (ledger
checked: 43000–43999 crowding, 44000–44999 category, 48000–48999 agnosia, 49000–49999
face-inversion; 45000–47999 CLEAN). Base `main` HEAD **877937e4**
(`git merge-base --is-ancestor 877937e4 HEAD` verified).*

## 0. THE RUNG AND ITS TENSION

Recognition invariant under SMOOTH NON-RIGID DEFORMATION — and the tension that must be
resolved honestly rather than assumed away:

- A **small, smooth** warp **PRESERVES** identity. This is the Omniglot fact: a letter
  written differently is the SAME letter (`OMNIGLOT_ARC.md`; composition +21pp).
- A **large affine** distortion **CHANGES** identity. This is MEASURED, not assumed:
  `VISION_SIMILARITY_RESULTS.md` established that the identity-preserving nuisance group
  is the **discrete similarity subgroup** (`M·Mᵀ = λI` — rotation, reflection, uniform
  scale) and that the **SHEARS ARE IDENTITY-CHANGING** (`shearY(F) → X`, `shearX(T) → X`
  under `|det|=1`; refused under the similarity restriction).

So the rung is NOT "be invariant to deformation". It is the **IDENTITY-PRESERVATION
BOUND**: recognition invariant under LOW-magnitude smooth deformation, **REFUSING**
deformation large enough to change identity. A mechanism with no bound merges everything
and must FAIL the crux arm.

`VISION_CONTINUOUS_POSE_RESULTS.md` deliberately did NOT use the deformation metrics for
pose, precisely because they free the whole affine group including the shears. This rung
takes them up directly, and asks whether the freed group can be BOUNDED back.

## 1. AUDIT (§12.4) — file:line, and the verdict

**VERDICT: COMPOSE. NO NEW RUST.** The bound is expressible as graph data over held
Terms; the only question is whether it SEPARATES, which is what this rung measures.

**Do the held deformation Terms expose a bending-energy / deformation-magnitude the
recognition can BOUND?** YES — one of them does, explicitly:

- `SmoothDeformComponents { a, b }` — `runners/dsl/src/term.rs:598` (declaration),
  evaluator `term.rs:5651`, implementation `runners/dsl/src/deform_metric.rs:255`
  (`smooth_deform_components`). It fits the SAME multi-level free-form-deformation field
  `SmoothDeformDist` fits (`deform_metric.rs:118` `ffd_fit`, a verbatim duplicate of
  `term.rs::smooth_deform_dist`'s warping loop), then **DECOMPOSES that field into an
  AFFINE part and a NON-AFFINE residual**, returning a `Dict`:
  - `total` — the Term's own fused verdict, **byte-identical to `SmoothDeformDist(a,b)`**
    (`deform_metric.rs:278`, `residual + 1.5*dc`);
  - `residual` — post-warp point-set mismatch (`deform_metric.rs:276`);
  - `dc` — mean squared TOTAL displacement, the deformation MAGNITUDE
    (`deform_metric.rs:277`);
  - **`bending`** — mean squared **NON-AFFINE** residual displacement, "the part of the
    FFD's own displacement field the affine fit does NOT explain"
    (`deform_metric.rs:286–292`) — **this is the bending energy**;
  - `rotation` / `shear` / `log_scale` / `tx` / `ty` — the affine decomposition
    (`deform_metric.rs:222` `decompose_affine`, the Graphics-Gems / CSS-WG QR-style
    split), so **`shear` is directly readable** — the exact quantity the similarity rung
    measured to be identity-changing.
- `DeformDist` (`term.rs`, registered `jsonio.rs:1310`), `TpsDeformDist` (`term.rs:587`,
  `jsonio.rs:1318`), `ScTpsDist` (`term.rs:611`, `jsonio.rs:1330`) return a BARE SCALAR
  only — no bending/affine split. `TpsDeformDist`'s doc (`term.rs:582`) notes it gives the
  affine part an *unconditional free pass*, which is precisely the behaviour that would
  re-merge the shears. **They are therefore NOT usable for a bending bound; only
  `SmoothDeformComponents` is.** This rung uses `SmoothDeformComponents`.

**Can recognition-under-bounded-deformation COMPOSE with no new Rust?** YES. Every Term
needed is held and JSON-serializable for seed rules: `SmoothDeformComponents`
(`jsonio.rs:1322`), `DictGet` (`jsonio.rs:1050`), `Argmin`, `MinOver`, `Abs`, `Lte`,
`Gte`, `Div`, `Sqrt`, `Not`, `And`, `Attr`, `NodesOfType`, `Lit` (all present in
`jsonio.rs`'s parser, verified by grep). The composition is
"**codebook proposes, deformation verdict decides, bounded**" — the same shape as
continuous pose's `Rotate`+`PointSetDist`, with the deformation verdict in place of the
rigid one.

## 2. THE MECHANISM (graph data, flag OFF by default)

Seed `seeds/vision_deformation.json`, two rules gated on `agent.deform` (absent by
default ⇒ §9 byte-identity), firing only on `status == "df_decoded"`:

- `df_recognize` — `covered_by = Attr(Argmin over NodesOfType('ShapeSignature') of
  DictGet(SmoothDeformComponents(c.points, obs.points), 'total'), 'name')`, and
  `status = "recognized_deformed"`, iff the winner satisfies **THE BOUND** (below).
- `df_refuse` — the `Not(...)` branch on the same bound term; `status = "df_refused"`,
  `covered_by` ABSENT.

### THE BOUND — and what it FALLS OUT OF (§13)

One quantity generates all three clauses. The observation is quantized to the integer
lattice, so a point's position is certified only to the **lattice half-diagonal `√2/2`**
— the identical falls-out constant continuous pose used, for the identical reason. Point
sets are normalized to unit RMS radius (a canonical scale, and REQUIRED because uniform
scale is identity-preserving per the similarity rung), so in normalized units that floor is

```
eps = (sqrt(2)/2) / R          R = the codebook's own mean RMS radius, in lattice units
```

`eps` is written onto the agent as graph data by the adapter, exactly as continuous pose
wrote `cp_angles`. It is **measured from the held codebook's own geometry**, not chosen.
The three clauses are the SAME floor applied to each component in ITS OWN UNITS:

| clause | quantity | bound | why this bound |
|---|---|---|---|
| **match/magnitude** | `total` (= `SmoothDeformDist`) | `<= eps` | linear in displacement ⇒ the lattice floor itself |
| **affine identity-preservation** | `Abs(shear)` | `<= eps` | INHERITED from the similarity rung: identity-preserving ⇔ `M·Mᵀ=λI` ⇔ shear 0, identifiable only to observational resolution |
| **bending energy** | `bending` | `<= eps^2` | a mean **SQUARED** displacement ⇒ the floor SQUARED |

No constant is fitted. `eps` shifts if the codebook or the lattice shifts (§13's
distribution-shift test).

## 3. PILOT (burned seeds 0–13 + 0–119 scatter/blob controls, §3.3) — DISCLOSED

A pilot was run on burned seeds to fix the mechanism and the arm sizes BEFORE this
pre-registration. It is disclosed in full because it drives the predictions below:

- **the verdict scalar was chosen at pilot stage and is now FIXED**: `total` (the Term's
  own fused headline scalar, byte-identical to `SmoothDeformDist`) rather than the
  `residual` sub-component. This is a pilot-stage choice, not metric surgery — no
  pre-registered gate existed to rescue. **It will NOT be revisited after this file is
  committed** (§5).
- pilot readings that motivate the predictions: `bending` sits at `1e-5 … 1.8e-3`
  everywhere, versus its bound `eps^2 ≈ 0.0244`; identity-preserving smooth warps reach
  `total ≈ 0.107`; the minimum cross-object (different-identity) `residual` is `≈ 0.0945`;
  random connected 5-cell polyominoes force-mapped at a high rate.

## 4. STIMULI

7 hand-chosen full-rank free pentominoes (`F T U V L N X`) — **the same object set as the
wall / det1 / similarity / continuous-pose rungs**, dense-sampled `s=4` (each unit cell
becomes a 4×4 block of lattice points, ~80 points/object) so the FFD has a field to fit.

- **SMOOTH deformation** — a low-frequency sinusoidal displacement field applied to the
  dense lattice points and **ROUNDED back to the integer lattice** (in-frame integer;
  the warp is a cross-frame map, the observation is stepped): amplitudes
  `a ∈ {0.5, 1.0, 1.5, 2.0, 2.5}` lattice units. This is the handwriting-class warp.
- **LARGE / identity-changing deformation** — `shearY(k=1.0)`, the transform the
  similarity rung MEASURED to change identity.
- **FLOOR** — random connected 5-cell polyominoes (seeds **46000–46099**), dense-sampled
  identically, with any that canonicalize to a held object EXCLUDED.

## 5. ARMS, STATISTICS, DECISION RULES

| arm | statistic | decision rule |
|---|---|---|
| **A1 INVARIANCE** | recognized-as-own-identity / 35 (7 obj × 5 amplitudes) | CROSS iff `>= 30/35` with 0 wrong-id |
| **A2 DISCRIMINATION exact-0** | untransformed: own-identity / 7, wrong-id count | EXACT-0 iff `7/7` and `wrong_id == 0` |
| **A3 THE BOUND CRUX (§1.1, LOAD-BEARING)** | three conjuncts, below | CROSS iff ALL THREE hold |
| **A4 FLOOR** | force-maps / 100 non-held random polyominoes (46000–46099) | FLOOR iff `0/100` |
| **A5 §13.2 BENDING LOAD-BEARING** | `max abs(on − off)` of the bending clause over every stimulus | LOAD-BEARING iff `> 0`; `== 0` ⇒ **INERT/decorative** |
| **A6 §9 OFF-DAY** | flag absent ⇒ no df rule fires; bench 200/0 with `data/`; sd orbit law `{2:1,3:2,4:2,6:2,12:4}`; siblings | all unmoved |

### A3 — the crux, stated so it can FAIL

1. **small smooth warp RECOGNIZED** — `a <= 2.5` recognized as own identity;
2. **large / identity-changing warp REFUSED** — `shearY(1.0)` refused `7/7`;
3. **SEPARABILITY** — `max(total)` over identity-PRESERVING stimuli `<`
   `min(total)` over identity-CHANGING stimuli (different-object pairs ∪ shears).
   **If these bands OVERLAP, then NO bound — falls-out or tuned — can separate them, and
   the crux FAILS as a matter of the verdict's own geometry, not of threshold choice.**

Conjunct 3 is the one that makes this rung falsifiable rather than a threshold search. A
mechanism with NO bound fails conjunct 2; a mechanism whose bands overlap fails conjunct 3
no matter what threshold is chosen.

## 6. PREDICTION, STATED IN ADVANCE (§3.7)

**I predict a MIXED outcome whose headline is a CLEAN DIAGNOSED NEGATIVE on the
identity-preservation bound.** Specifically:

- **A1 INVARIANCE — PASS.** `>= 30/35`. Small smooth warps will be recognized; the FFD
  absorbs them and `total` stays low.
- **A2 DISCRIMINATION — PASS, exact-0.** Untransformed objects are exact matches
  (`total = 0`), so the argmin cannot err.
- **A3 conjunct 2 — PASS.** `shearY(1.0)` refused `7/7`. **The affine `shear` clause is
  the load-bearing part of the bound**, and it is INHERITED from the similarity rung
  rather than invented here.
- **A3 conjunct 3 (SEPARABILITY) — FAIL. This is the predicted negative.** The
  identity-preserving band and the identity-changing band will **OVERLAP**: identity-
  preserving smooth warps reach a `total` ABOVE the minimum `total` between two DIFFERENT
  held identities. **Mechanism, named in advance: the FFD is a FREE-FORM warp, so it
  absorbs not only the nuisance deformation but also part of the structure that
  DISTINGUISHES identities** — it pulls a candidate onto a different object nearly as well
  as onto a warp of itself. The freed non-rigid group is larger than the identity-
  preserving one, and no scalar bound on that verdict can re-restrict it.
- **A4 FLOOR — FAIL (leak > 0).** For the same reason: random non-held polyominoes will
  force-map onto held identities at a substantial rate. I predict a leak well above zero,
  NOT `0/100`.
- **A5 BENDING — INERT (`D == 0`).** The bending clause will never bind: `bending`
  measures `~1e-3` against a bound of `~2.4e-2`. **The "bending energy" the held Term
  exposes does NOT separate identity-preserving from identity-changing deformation — the
  AFFINE SHEAR component does.** Per §13.2 an inert clause is decorative and will be
  reported as such, not quietly retained.
- **A6 OFF-DAY — PASS.**

**Two-sided (§3.1).** If instead the bands SEPARATE (`max_preserving < min_changing`) and
the floor comes in at `0/100`, that is a genuine BOUNDED CROSSING and I will report it as
such — the composition would then be the first non-rigid identity-preservation bound in
this arc. I do not expect it, for the mechanism named above.

**The proviso that would break my prediction:** if `total`'s deformation-magnitude term
(`1.5*dc`) penalizes the free-form warp enough to price identity-dissolving warps out, the
bands could separate after all. The pilot's `min cross-object residual ≈ 0.0945` versus
identity-preserving `total ≈ 0.107` says it does not, but `dc` is measured per-stimulus and
could reorder the bands.

## 7. WHAT A NULL MEANS

A null here is INFORMATIVE and is the expected result: it says the held free-form
deformation verdict **cannot** be bounded back into an identity-preserving group, and
therefore that non-rigid invariance in this substrate needs a mechanism that constrains
the WARP FAMILY itself (as the similarity rung constrained the linear group), not a
scalar threshold on an unconstrained warp's cost. It does NOT retract the Omniglot
composition result, and it does NOT license "deformation invariance is impossible".

## 8. BOUNDS (§8) — declared in advance

INSTANCE-level recognition under BOUNDED SMOOTH DEFORMATION over 7 hand-chosen
pentominoes at one dense sampling. NOT shown regardless of outcome: category-level
deformation invariance; deformation of natural images; the learned axis-codebook at
scale. **NAMED FRONTIER, explicitly NOT this rung: lighting, style, and the learned
axis-codebook at natural-image scale.**

## 9. SEEDS

**46000–46999** allocated; **46000–46099** for the A4 floor. No other confirmatory seed is
consumed (A1/A2/A3 are deterministic geometry). 45000–45999 and 46100–47999 remain CLEAN.
